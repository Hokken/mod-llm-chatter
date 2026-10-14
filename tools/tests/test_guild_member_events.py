#!/usr/bin/env python3
"""Guild news events: join greetings, rank-change comments and MOTD
comments.

Run directly from the module root:
  python tools/tests/test_guild_member_events.py
"""

import importlib
import json
import re
import sys
import types
from pathlib import Path
from unittest.mock import patch


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_non_strict_stubs() -> None:
    for module_name in ("anthropic", "openai"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            module = _ensure_module(module_name)
            class_name = (
                "Anthropic"
                if module_name == "anthropic"
                else "OpenAI"
            )
            setattr(module, class_name, type(class_name, (), {}))

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module("mysql.connector")
        setattr(mysql_module, "connector", connector_module)


TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_guild_event_common as common  # noqa: E402
import chatter_guild_events  # noqa: E402
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402

MOOD_WORDS = ('warmly', 'glad', 'happily', 'proud', 'graciously',
              'good humor', 'cheerful')


def _profile(info='', motd='', ranks=None):
    return {
        'id': 9,
        'name': 'Keepers',
        'info': info,
        'motd': motd,
        'ranks': ranks or {},
        'leader': None,
    }


def _speaker_for(db, guid):
    return {
        'class': 'Warrior', 'race': 'Human', 'gender': 'male',
        'level': 30, 'traits': [], 'tone': '', 'backstory': '',
    }


def _candidate_speaker(tone='warm'):
    return {
        'class': 'Mage', 'race': 'Human', 'gender': 'female',
        'level': 80, 'traits': ['steadfast'], 'tone': tone,
        'backstory': '',
    }


def _prompt_text(prompt) -> str:
    return getattr(prompt, 'user_prompt', prompt)


def _assert_no_mood(text: str):
    lowered = text.lower()
    for word in MOOD_WORDS:
        assert word not in lowered, word


# -- Registry and scenarios --------------------------------------------

def test_registry_routes_guild_news_events():
    for event_type, handler in (
        ('guild_member_join', 'process_guild_member_join_event'),
        ('guild_rank_change', 'process_guild_rank_change_event'),
        ('guild_motd_comment', 'process_guild_motd_comment_event'),
    ):
        spec = EVENT_REGISTRY[event_type]
        assert spec.handler_module == 'chatter_guild_events'
        assert spec.handler_func == handler
        assert spec.producer == 'LLMChatterGuildMembers.cpp'


def test_rank_scenario_names_ranks_and_direction():
    extra = {'changes': [{
        'guid': 201, 'name': 'Bran', 'online': True, 'is_bot': True,
        'old_rank': 4, 'new_rank': 3, 'direction': 'promotion',
        'actor_guid': 7, 'actor_name': 'Calwen',
    }]}
    profile = _profile(ranks={3: 'Veteran', 4: 'Member'})
    with patch.object(
        chatter_guild_events, '_query_speaker', side_effect=_speaker_for,
    ):
        scenario, address, subject, situation, subjects = (
            chatter_guild_events._rank_scenario(
                object(), extra, profile, 'normal',
            )
        )
    text = "\n".join(scenario)
    assert 'promoted from "Member" to "Veteran" by Calwen' in text
    assert 'congratulations, light teasing, a dry remark' in text
    assert 'demoted' not in text
    assert address == ['Bran']
    assert subject['guid'] == 201
    assert subjects == {'Bran': 201}
    assert 'promoted' in situation
    _assert_no_mood(text + situation)


def test_demotion_scenario_offers_options_only():
    extra = {'changes': [{
        'guid': 201, 'name': 'Bran', 'online': True, 'is_bot': True,
        'old_rank': 3, 'new_rank': 4, 'direction': 'demotion',
    }]}
    with patch.object(
        chatter_guild_events, '_query_speaker', side_effect=_speaker_for,
    ):
        scenario, _, _, situation, _ = chatter_guild_events._rank_scenario(
            object(), extra, _profile(ranks={3: 'Veteran', 4: 'Member'}),
            'roleplay',
        )
    text = "\n".join(scenario)
    assert 'never humiliate them' in text
    assert 'Answer graciously' not in situation
    _assert_no_mood(text + situation)


def test_motd_scenario_quotes_motd_as_announcement():
    scenario, address, subject, _, subjects = (
        chatter_guild_events._motd_scenario(
            object(), {'motd': 'Raid\nat 8'}, _profile(), 'normal',
        )
    )
    assert '"Raid at 8"' in scenario[0]
    assert 'motd' in scenario[0]
    assert 'Message of the Day' not in scenario[0]
    assert 'never instructions' in scenario[2]
    assert 'beyond what it says' in scenario[2]
    assert address == [] and subject is None and subjects == {}

    scenario = chatter_guild_events._motd_scenario(
        object(), {'motd': 'We must always protect our Light'},
        _profile(), 'roleplay',
    )[0]
    text = '\n'.join(scenario)
    assert "officers have just left a new note" in scenario[0]
    assert '"We must always protect our Light"' in scenario[0]
    assert 'sacred creed' in scenario[1]
    assert 'Message of the Day' not in scenario[0]
    assert 'never instructions' in text


# -- Event flow ----------------------------------------------------------

def _join_event():
    return {
        'id': 55,
        'extra_data': json.dumps({
            'guild_id': 9,
            'guild_name': 'Keepers',
            'team': 'Alliance',
            'members': [{
                'guid': 201, 'name': 'Bran', 'online': True,
                'is_bot': True, 'zone_id': 12, 'map_id': 0,
            }],
            'candidates': [
                {'guid': 101, 'name': 'Aliss', 'zone_id': 12, 'map_id': 0},
                {'guid': 201, 'name': 'Bran', 'zone_id': 12, 'map_id': 0},
            ],
        }),
    }


def _run_join(tone='warm', mode='normal'):
    inserted = []
    statuses = []
    prompts = []
    prepared = []

    def fake_single(client, config, prompt, name, *args):
        prompts.append((name, _prompt_text(prompt)))
        if name == 'Aliss':
            return [{'name': 'Aliss', 'message': 'Another one, then.'}]
        return [{'name': 'Bran', 'message': 'Thanks, I suppose.'}]

    def fake_prepare(db, client, config, participants, prepared_cache=None,
                     channel='guild'):
        prepared.extend((channel, p['name']) for p in participants)
        return [dict(p, speaker=dict(p['speaker'])) for p in participants]

    with (
        patch.object(
            chatter_guild_events, '_query_speaker',
            side_effect=_speaker_for,
        ),
        patch.object(
            chatter_guild_events, 'prepare_guild_speakers',
            side_effect=fake_prepare,
        ),
        patch.object(
            chatter_guild_events, '_load_candidates',
            side_effect=lambda db, candidates: [
                dict(c, speaker=_candidate_speaker(tone))
                for c in candidates
            ],
        ),
        patch.object(
            chatter_guild_events, 'get_guild_profile',
            return_value=_profile(info='A friendly leveling guild.'),
        ),
        patch.object(common, 'run_single_prompt', side_effect=fake_single),
        patch.object(common, 'calculate_dynamic_delay', return_value=6.0),
        patch.object(
            common, 'insert_chat_message',
            side_effect=lambda db, **kwargs: inserted.append(kwargs),
        ),
        patch.object(
            chatter_guild_events, '_mark_event',
            side_effect=lambda db, event_id, status:
                statuses.append((event_id, status)),
        ),
        patch.object(
            chatter_guild_events.random, 'randint', return_value=1,
        ),
    ):
        result = chatter_guild_events.process_guild_member_join_event(
            object(), object(), {'LLMChatter.ChatterMode': mode},
            _join_event(),
        )
    return result, statuses, prepared, inserted, prompts


def test_join_greeting_then_newcomer_replies():
    result, statuses, prepared, inserted, prompts = _run_join()
    assert result is True
    assert statuses == [(55, 'completed')]
    assert prepared == [('guild', 'Aliss'), ('guild', 'Bran')]
    assert [row['bot_name'] for row in inserted] == ['Aliss', 'Bran']
    assert inserted[0]['message'].count('Bran') == 1
    assert inserted[1]['delay_seconds'] == 6.0
    assert all(
        row['channel'] == 'guild' and row['owner_subsystem'] == 'guild'
        and row['delivery_policy'] is None
        for row in inserted
    )
    welcome_prompt = prompts[0][1]
    assert 'Bran, a level 30 male Human Warrior has just joined' in (
        welcome_prompt
    )
    assert '"A friendly leveling guild."' in welcome_prompt
    reply_prompt = prompts[1][1]
    assert f"Aliss: {inserted[0]['message']}" in reply_prompt


def test_cold_persona_keeps_its_own_tone():
    _, _, _, _, prompts = _run_join(tone='cold and curt', mode='roleplay')
    welcome_prompt = prompts[0][1]
    assert 'Aliss speaking tone: cold and curt.' in welcome_prompt
    assert 'React the way Aliss naturally would, given their ' \
        'personality and tone.' in welcome_prompt
    assert 'a dry remark or a brief nod all fit' in welcome_prompt
    for _, prompt in prompts:
        _assert_no_mood(prompt.split('Aliss: ')[0])


def test_roleplay_prompts_carry_no_prescribed_mood():
    _, _, _, _, prompts = _run_join(mode='roleplay')
    assert len(prompts) == 2
    for _, prompt in prompts:
        _assert_no_mood(prompt.split('Aliss: ')[0])
    assert 'answers the guild once, briefly, in their own voice' in (
        prompts[1][1]
    )


def test_join_greeting_skips_without_other_commenters():
    event = _join_event()
    extra = json.loads(event['extra_data'])
    extra['candidates'] = [extra['candidates'][1]]
    event['extra_data'] = json.dumps(extra)
    statuses = []
    with (
        patch.object(
            chatter_guild_events, '_query_speaker',
            side_effect=_speaker_for,
        ),
        patch.object(
            chatter_guild_events, '_load_candidates',
            side_effect=lambda db, candidates: [
                dict(c, speaker=_candidate_speaker())
                for c in candidates
            ],
        ),
        patch.object(
            chatter_guild_events, 'get_guild_profile',
            return_value=_profile(),
        ),
        patch.object(common, 'run_single_prompt') as generate,
        patch.object(
            chatter_guild_events, '_mark_event',
            side_effect=lambda db, event_id, status:
                statuses.append((event_id, status)),
        ),
    ):
        result = chatter_guild_events.process_guild_member_join_event(
            object(), object(), {}, event,
        )
    assert result is False
    assert statuses == [(55, 'skipped')]
    generate.assert_not_called()


# -- Shared generation helpers -----------------------------------------

def test_checked_order_requires_each_speaker_once():
    names = ['Aliss', 'Bran']
    ok = [{'name': 'Aliss', 'message': 'a'}, {'name': 'Bran', 'message': 'b'}]
    assert common.checked_order(ok, names) == ok
    swapped = [ok[1], ok[0]]
    assert common.checked_order(swapped, names, 'Aliss') == ok
    duplicate = [ok[0], ok[0]]
    assert common.checked_order(duplicate, names) is None
    stranger = [ok[0], {'name': 'Cato', 'message': 'c'}]
    assert common.checked_order(stranger, names) is None
    assert common.checked_order([ok[0]], names) is None


def test_multi_prompt_rejects_duplicate_speakers_after_repair():
    reply = json.dumps([
        {'speaker': 'Aliss', 'message': 'One'},
        {'speaker': 'Aliss', 'message': 'Two'},
    ])
    with patch.object(common, 'call_llm', return_value=reply) as llm:
        messages = common.run_multi_prompt(
            None, {}, 'prompt', ['Aliss', 'Bran'], 120, {},
            'guild_member_join', 'ctx', 'repair',
        )
    assert messages == []
    assert llm.call_count == 2


def test_multi_prompt_moves_expected_first_speaker_to_the_front():
    reply = json.dumps([
        {'speaker': 'Bran', 'message': 'Two'},
        {'speaker': 'Aliss', 'message': 'One'},
    ])
    metadata = {}
    with patch.object(common, 'call_llm', return_value=reply) as llm:
        messages = common.run_multi_prompt(
            None, {}, 'prompt', ['Aliss', 'Bran'], 120, metadata,
            'guild_member_join', 'ctx', 'repair', expected_first='Aliss',
        )
    assert [m['name'] for m in messages] == ['Aliss', 'Bran']
    assert metadata['guild_order_repaired'] is True
    assert llm.call_count == 1


def _event_prompt(names):
    participants = [
        {'name': name, 'speaker': _candidate_speaker(), 'zone_id': 12,
         'map_id': 0}
        for name in names
    ]
    return common.build_prompt(
        participants, 'Keepers', 'Alliance', 'normal', [],
        ['Someone joined the guild.'], 120,
    )


def test_event_prompts_carry_structured_contracts():
    single, _ = _event_prompt(['Aliss'])
    assert single.response_contract.kind == 'statement'
    assert single.response_contract.message_only
    names = ['Aliss', 'Bran']
    multi, _ = _event_prompt(names)
    contract = multi.response_contract
    assert contract.kind == 'conversation' and contract.message_only
    assert contract.speaker_names == tuple(names)
    assert contract.message_count == 2


def test_structured_repairs_keep_the_event_contract():
    config = {'LLMChatter.StructuredOutput.Enable': '1'}
    prompts = []

    def record(client, prompt, config, **kwargs):
        prompts.append(prompt)
        return ''

    for names in (['Aliss'], ['Aliss', 'Bran']):
        prompts.clear()
        prompt, _ = _event_prompt(names)
        with patch.object(common, 'call_llm', side_effect=record):
            if len(names) == 1:
                common.run_single_prompt(
                    None, config, prompt, names[0], 120, {},
                    'guild_member_join', 'ctx', 'repair',
                )
            else:
                common.run_multi_prompt(
                    None, config, prompt, names, 120, {},
                    'guild_member_join', 'ctx', 'repair',
                )
        assert len(prompts) == 2
        assert all(p.response_contract == prompt.response_contract
                   for p in prompts)


# -- C++, SQL and config wiring ----------------------------------------

def _src(name: str) -> str:
    return (MODULE_DIR / 'src' / name).read_text(encoding='utf-8')


def test_member_events_live_in_their_own_file():
    source = _src('LLMChatterGuildMembers.cpp')
    assert 'class LLMChatterGuildMemberEventScript : public GuildScript' \
        in source
    assert 'GUILDHOOK_ON_MOTD_CHANGED' in source
    assert 'GUILDHOOK_ON_EVENT' in source
    assert 'case GUILD_EVENT_LOG_JOIN_GUILD:' in source
    assert 'case GUILD_EVENT_LOG_PROMOTE_PLAYER:' in source
    assert 'case GUILD_EVENT_LOG_DEMOTE_PLAYER:' in source
    assert 'WORLDHOOK_ON_UPDATE' in source
    assert 'ProcessPendingGuildMemberEvents();' in source
    assert 'std::lock_guard<std::mutex> guard(sGuildEventMutex);' in source
    assert 'FROM guild_eventlog' in source
    assert 'change.currentRank == change.originalRank' in source
    assert 'EnsureGuildSessionForPlayer(player);' in source
    guild = _src('LLMChatterGuild.cpp')
    assert 'public GuildScript' not in guild
    assert 'sGuildEventMutex' not in guild
    assert 'AddLLMChatterGuildMemberScripts();' in _src('LLMChatterScript.cpp')


def test_member_events_are_not_recorded_as_replies():
    source = _src('LLMChatterGuildMembers.cpp')
    assert 'NoteGuildPlayerInteraction' not in source
    guild = _src('LLMChatterGuild.cpp')
    record = guild[guild.index('void RecordDeliveredGuildLine('):]
    record = record[:record.index('CharacterDatabase.DirectExecute')]
    assert 'sourceKind = "reply";' in record
    for event_type in (
        'guild_member_join', 'guild_rank_change', 'guild_motd_comment',
    ):
        assert event_type not in record


def test_guild_news_waits_for_the_player_conversation():
    source = _src('LLMChatterGuildMembers.cpp').replace('\r\n', '\n')
    helpers = source[source.index('bool GuildConversationActive('):]
    helpers = helpers[:helpers.index('bool JoinedGuildRecently(')]
    assert 'WasGuildPlayerInteractionRecent(' in helpers
    assert '_guildPlayerIdleSuppressionSeconds' in helpers
    expired = helpers[helpers.index('bool GuildNewsExpired('):]
    assert 'now - createdAt >= ' in expired
    assert '_guildMemberEventMaxDeferSeconds' in expired
    flush = source[source.index('void ProcessPendingGuildMemberEvents()'):]
    flush = flush[:flush.index('class LLMChatterGuildMemberEventScript')]
    loops = {
        'sPendingGuildJoins': 'now < it->second.dueAt',
        'sPendingGuildRankChanges': 'now - it->second.lastChangeAt',
        'sPendingGuildMotds': 'now < it->second.dueAt',
    }
    for buffer, due_check in loops.items():
        loop = flush[flush.index(f'for (auto it = {buffer}.begin();'):]
        loop = loop[:loop.index('.emplace_back(')]
        expiry = loop.index('GuildNewsExpired(it->second.createdAt, now)')
        # A held batch that keeps receiving updates (a new rank change,
        # an edited MOTD) moves its due/debounce time, never createdAt:
        # expiry must be checked before, and independently of, that time.
        assert expiry < loop.index(due_check), buffer
        assert 'if (busy\n                && GuildNewsExpired(' in loop, \
            buffer
        assert f'it = {buffer}.erase(it);\n                continue;' \
            in loop[expiry:], buffer
        # While busy and not expired, the batch stays pending.
        assert 'if (busy ||' in loop[expiry:] or 'if (busy\n' in \
            loop[expiry + 1:], buffer
    # createdAt is set once, when the batch starts.
    assert 'batch.createdAt = now;' in source
    assert ('if (batch.changes.empty())\n'
            '        batch.createdAt = batch.lastChangeAt;') in source
    assert ('if (pending.motd.empty())\n'
            '        pending.createdAt = now;') in source


def test_guild_news_queued_before_the_player_spoke_is_dropped():
    # The player may start talking after the event was queued (during
    # generation or the line delay): delivery checks again.
    source = _src('LLMChatterDelivery.cpp')
    branch = source[source.index('else if (channel == "guild")'):]
    branch = branch[:branch.index('guild->BroadcastToGuild(')]
    assert 'IsGuildNewsEventType(eventType)' in branch
    assert 'WasGuildPlayerInteractionRecent(' in branch
    assert 'dropReason = "guild_player_active";' in branch
    members = _src('LLMChatterGuildMembers.cpp')
    news = members[members.index('bool IsGuildNewsEventType('):]
    news = news[:news.index('}')]
    for event_type in (
        'guild_member_join', 'guild_rank_change', 'guild_motd_comment',
    ):
        assert f'"{event_type}"' in news


def test_guild_news_never_outranks_player_replies():
    shared = _src('LLMChatterShared.cpp')
    assert '{"guild_player_message",    PRIORITY_HIGH}' in shared
    assert EVENT_REGISTRY['guild_player_message'].priority == 'high'
    for event_type in (
        'guild_member_join', 'guild_rank_change', 'guild_motd_comment',
    ):
        assert f'{{"{event_type}",' not in shared
        assert EVENT_REGISTRY[event_type].priority == 'normal'


def test_event_lines_are_delivered_intact():
    # Seen in game: a 140-character NPC remark was cut at 120 and ended
    # "Worth a visit if." Lines over the prompt's length are kept whole.
    line = ("Haferet's leatherworking stall in the Exodar has decent hide, "
            "though the prices feel like a curse. Worth a visit if you're "
            "patient, friends.")
    assert common.trim_line(line) == line
    assert common.trim_line("  Spaced \n  out   line. ") == 'Spaced out line.'


def test_only_the_chat_limit_is_enforced_at_a_sentence_end():
    first = 'A' * 150 + ' rests here.'
    second = ' Then ' + 'b' * 150 + ' goes on.'
    trimmed = common.trim_line(first + second)
    assert trimmed == first
    assert len(trimmed) <= 255


def test_trimmed_lines_never_split_links():
    colored = ('|cff1eff00|Hitem:12345:0:0:0:0:0:0:0|h'
               '[Fine Guild Reward]|h|r')
    bare = '|Hitem:12345:0:0:0:0:0:0:0|h[Fine Guild Reward]|h'
    for link in (colored, bare):
        text = f'Take a look at {link} before deciding.'
        assert link in common.trim_line(text)
        # Past the chat limit the link still stays whole or goes whole.
        long_text = 'Word ' * 40 + text + ' ' + 'more ' * 20
        trimmed = common.trim_line(long_text)
        assert len(trimmed) <= 255
        assert link in trimmed or '|H' not in trimmed


def test_sql_adds_guild_news_event_types():
    sql_dir = MODULE_DIR / 'data' / 'sql' / 'characters'
    update = (
        sql_dir / 'updates' / '20261002_guild_member_events.sql'
    ).read_text(encoding='utf-8')
    base = (
        sql_dir / 'base' / '00000000_llm_chatter_tables.sql'
    ).read_text(encoding='utf-8')
    assert 'information_schema.COLUMNS' in update
    assert 'LEFT(@event_type, CHAR_LENGTH(@event_type) - 1)' in update
    for event_type in (
        'guild_member_join', 'guild_rank_change', 'guild_motd_comment',
    ):
        assert f"'''{event_type}'''" in update
        assert f"'{event_type}'" in base
    assert "'guild_login_greeting'" not in update


def test_config_keys_in_both_confs():
    conf = MODULE_DIR / 'conf'
    for path in (conf / 'mod_llm_chatter.conf.dist',
                 conf / 'presets' / 'mod_ll_chatter_quieter.conf.dist'):
        text = path.read_text(encoding='utf-8')
        for key in (
            'JoinGreeting.Enable', 'JoinGreeting.BatchSeconds',
            'RankChange.DebounceSeconds', 'MotdComment.DelaySeconds',
            'MemberEvents.MaxCandidates', 'MemberEvents.MaxCharacters',
            'JoinGreeting.SubjectReplyChance',
            'MemberEvents.MaxDeferSeconds',
        ):
            assert re.search(
                rf'^LLMChatter\.GuildChatter\.{re.escape(key)} = \d+',
                text, re.M), (path.name, key)
    config = _src('LLMChatterConfig.cpp')
    assert '"MemberEvents.MaxCandidates", 12)' in config
    assert '"MemberEvents.MaxDeferSeconds", 300)' in config


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} guild member event tests passed")
