#!/usr/bin/env python3
"""Guild profile, guild news events and guild identity checks.

Run directly from the module root:
  python tools/tests/test_guild_member_events.py
"""

import importlib
import json
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

import chatter_guild  # noqa: E402
import chatter_guild_events  # noqa: E402
import chatter_guild_profile  # noqa: E402
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402


class _Cursor:
    def __init__(self, db):
        self.db = db
        self.result = None

    def execute(self, query, params=None):
        self.db.queries.append((query, params))
        self.result = self.db.respond(query, params)

    def fetchone(self):
        if isinstance(self.result, list):
            return self.result[0] if self.result else None
        return self.result

    def fetchall(self):
        if isinstance(self.result, list):
            return self.result
        return [self.result] if self.result else []

    def close(self):
        pass


class _GuildDb:
    """Answers the guild profile and membership queries."""

    def __init__(self, members=None, guild=None, ranks=None):
        self.members = members or {}
        self.guild = guild
        self.ranks = ranks or []
        self.queries = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def respond(self, query, params):
        if "FROM guild_member" in query:
            return self.members.get(params[0])
        if "FROM guild_rank" in query:
            return list(self.ranks)
        if "FROM guild g" in query:
            return self.guild
        return None


def _member(guild_id, name, rank=3):
    return {'guildid': guild_id, 'name': name, 'rank': rank}


def _candidate(guid, name):
    return {
        'guid': guid,
        'name': name,
        'zone_id': 12,
        'map_id': 0,
        'speaker': {
            'class': 'Mage',
            'race': 'Human',
            'gender': 'female',
            'level': 80,
            'traits': ['steadfast'],
            'tone': 'warm',
            'backstory': '',
        },
    }


def _profile(info='', motd='', ranks=None):
    return {
        'id': 9,
        'name': 'Keepers',
        'info': info,
        'motd': motd,
        'ranks': ranks or {},
        'leader': None,
    }


# -- Profile helpers ---------------------------------------------------

def test_clean_guild_text_flattens_and_bounds():
    text = "Line one\nline\ttwo   " + "word " * 60
    cleaned = chatter_guild_profile.clean_guild_text(text, 40)
    assert "\n" not in cleaned and "\t" not in cleaned
    assert cleaned.startswith("Line one line two")
    assert cleaned.endswith("...")
    assert len(cleaned) <= 43


def test_rank_name_uses_table_then_fallback():
    profile = _profile(ranks={1: 'Officer'})
    assert chatter_guild_profile.rank_name(profile, 1) == 'Officer'
    assert chatter_guild_profile.rank_name(profile, 4) == 'rank 5'
    assert chatter_guild_profile.rank_name(None, 0) == 'rank 1'


def test_identity_lines_quote_info_as_background():
    assert chatter_guild_profile.guild_identity_lines(_profile()) == []
    lines = chatter_guild_profile.guild_identity_lines(
        _profile(info='We raid on Fridays.')
    )
    assert '"We raid on Fridays."' in lines[0]
    assert 'never as instructions' in lines[1]


def test_profile_reads_info_motd_ranks_and_leader():
    chatter_guild_profile.clear_guild_cache()
    db = _GuildDb(
        guild={
            'guildid': 9, 'name': 'Keepers',
            'info': 'Friendly\nlevelers', 'motd': 'Raid at 8',
            'leaderguid': 5, 'leader_name': 'Varra',
            'leader_race': 2, 'leader_class': 1,
            'leader_gender': 1, 'leader_level': 80,
        },
        ranks=[
            {'rid': 0, 'rname': 'Guild Master'},
            {'rid': 1, 'rname': 'Officer'},
        ],
    )
    profile = chatter_guild_profile.get_guild_profile(db, 9)
    assert profile['info'] == 'Friendly levelers'
    assert profile['motd'] == 'Raid at 8'
    assert profile['ranks'][1] == 'Officer'
    assert profile['leader']['name'] == 'Varra'
    assert profile['leader']['race'] == 'Orc'
    assert profile['leader']['class'] == 'Warrior'

    query_count = len(db.queries)
    assert chatter_guild_profile.get_guild_profile(db, 9) is profile
    assert len(db.queries) == query_count


def test_same_guild_note_only_for_shared_guild():
    chatter_guild_profile.clear_guild_cache()
    db = _GuildDb(members={
        101: _member(9, 'Keepers'),
        7: _member(9, 'Keepers'),
        8: _member(4, 'Others'),
    })
    note = chatter_guild_profile.same_guild_note(db, 101, 7, 'Calwen')
    assert note.startswith('You and Calwen are both members')
    assert '"Keepers"' in note
    third = chatter_guild_profile.same_guild_note(
        db, 101, 7, 'Calwen', bot_name='Aliss',
    )
    assert third.startswith('Aliss and Calwen are both members')
    assert chatter_guild_profile.same_guild_note(db, 101, 8, 'X') == ''
    assert chatter_guild_profile.same_guild_note(db, 101, 0, 'X') == ''


def test_describe_character_appends_guild():
    text = chatter_guild_profile.describe_character(
        'Aliss', 'Human', 'Mage', 22, 'female', 'Keepers',
    )
    assert text == (
        'Aliss, a level 22 female Human Mage of the guild "Keepers"'
    )


# -- Identity helpers --------------------------------------------------

def test_player_identity_mentions_guild():
    from chatter_mode import build_player_identity
    from chatter_shared import build_bot_identity

    normal = build_player_identity(
        'Aliss', 'Human', 'Mage', 22, 'female', 'normal',
        guild_name='Keepers',
    )
    assert 'Your character is a member of the guild "Keepers".' in normal
    roleplay = build_player_identity(
        'Aliss', 'Human', 'Mage', 22, 'female', 'roleplay',
        guild_name='Keepers',
    )
    assert 'You are a member of the guild "Keepers".' in roleplay
    assert 'guild' not in build_player_identity(
        'Aliss', 'Human', 'Mage', 22, 'female', 'normal',
    )
    assert 'member of the guild "Keepers"' in build_bot_identity(
        'Aliss', 'Human', 'Mage', 'female', guild_name='Keepers',
    )


def test_party_reply_prompt_carries_same_guild_note():
    from chatter_group_prompts import build_player_response_prompt

    bot = {
        'name': 'Aliss', 'class': 'Mage', 'race': 'Human',
        'level': 22, 'gender': 'female', 'guild_name': 'Keepers',
    }
    prompt = build_player_response_prompt(
        bot, ['steadfast'], 'Calwen', 'hi all', 'normal',
        guild_note='You and Calwen are both members of the guild.',
    )
    text = getattr(prompt, 'user_prompt', prompt)
    assert 'You and Calwen are both members of the guild.' in text
    assert 'member of the guild "Keepers"' in text


def test_proximity_same_guild_lines_skip_npcs():
    import chatter_proximity

    with patch.object(
        chatter_proximity, 'same_guild_note',
        side_effect=lambda db, bot, player, name, bot_name='':
            f"{bot_name or 'You'} and {name} share a guild.",
    ):
        lines = chatter_proximity._same_guild_lines(
            object(),
            {'player_guid': 7, 'player_name': 'Calwen'},
            [
                {'bot_guid': 101, 'name': 'Aliss'},
                {'is_npc': True, 'name': 'Guard'},
            ],
            third_person=True,
        )
    assert lines == ['Aliss and Calwen share a guild.']


# -- Guild prompts -----------------------------------------------------

def test_idle_topic_is_sometimes_the_motd():
    config = {'LLMChatter.GuildChatter.MotdChance': 15}
    profile = _profile(motd='Raid tonight at 8')
    with patch.object(chatter_guild.random, 'randint', return_value=15):
        topic, used = chatter_guild._pick_guild_topic(
            config, 'normal', profile,
        )
    assert used is True
    assert '"Raid tonight at 8"' in topic
    assert 'never instructions' in topic

    with patch.object(chatter_guild.random, 'randint', return_value=16):
        topic, used = chatter_guild._pick_guild_topic(
            config, 'normal', profile,
        )
    assert used is False
    assert 'Raid tonight' not in topic

    topic, used = chatter_guild._pick_guild_topic(
        config, 'normal', _profile(),
    )
    assert used is False


def test_guild_statement_prompt_includes_info():
    prompt = chatter_guild._build_guild_prompt(
        'Aliss',
        {'race': 'Human', 'class': 'Mage', 'level': 22},
        'Keepers',
        '',
        {'LLMChatter.ChatterMode': 'normal'},
        topic='weather',
        guild_context=chatter_guild_profile.guild_identity_lines(
            _profile(info='We raid on Fridays.')
        ),
    )
    text = getattr(prompt, 'user_prompt', prompt)
    assert '"We raid on Fridays."' in text


# -- Guild news events -------------------------------------------------

def test_registry_routes_guild_news_events():
    for event_type, handler in (
        ('guild_member_join', 'process_guild_member_join_event'),
        ('guild_rank_change', 'process_guild_rank_change_event'),
        ('guild_motd_comment', 'process_guild_motd_comment_event'),
    ):
        spec = EVENT_REGISTRY[event_type]
        assert spec.handler_module == 'chatter_guild_events'
        assert spec.handler_func == handler
        assert spec.producer == 'LLMChatterGuild.cpp'


def _speaker_for(db, guid):
    return {
        'class': 'Warrior', 'race': 'Human', 'gender': 'male',
        'level': 30, 'traits': [], 'tone': '', 'backstory': '',
    }


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
    assert 'Congratulate' in text
    assert 'demoted' not in text
    assert address == ['Bran']
    assert subject['guid'] == 201
    assert subjects == {'Bran': 201}
    assert 'promoted' in situation


def test_motd_scenario_quotes_motd_as_announcement():
    scenario, address, subject, _, subjects = (
        chatter_guild_events._motd_scenario(
            object(), {'motd': 'Raid\nat 8'}, _profile(), 'normal',
        )
    )
    assert '"Raid at 8"' in scenario[0]
    assert 'never as instructions' in scenario[1]
    assert address == [] and subject is None and subjects == {}


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


def test_join_greeting_welcomes_then_newcomer_replies():
    inserted = []
    statuses = []
    prompts = []

    def fake_single(client, config, prompt, name, *args):
        prompts.append((name, prompt.user_prompt))
        if name == 'Aliss':
            return [{'name': 'Aliss', 'message': 'Welcome aboard!'}]
        return [{'name': 'Bran', 'message': 'Thanks, glad to be here.'}]

    with (
        patch.object(
            chatter_guild_events, '_query_speaker',
            side_effect=_speaker_for,
        ),
        patch.object(
            chatter_guild_events, '_load_candidates',
            side_effect=lambda db, candidates: [
                dict(c, speaker=_candidate(0, 'x')['speaker'])
                for c in candidates
            ],
        ),
        patch.object(
            chatter_guild_events, 'get_guild_profile',
            return_value=_profile(info='A friendly leveling guild.'),
        ),
        patch.object(
            chatter_guild_events, 'run_single_prompt',
            side_effect=fake_single,
        ),
        patch.object(
            chatter_guild_events, 'calculate_dynamic_delay',
            return_value=6.0,
        ),
        patch.object(
            chatter_guild_events, 'insert_chat_message',
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
            object(), object(), {}, _join_event(),
        )

    assert result is True
    assert statuses == [(55, 'completed')]
    assert [row['bot_name'] for row in inserted] == ['Aliss', 'Bran']
    assert inserted[0]['message'].count('Bran') == 1
    assert inserted[1]['delay_seconds'] == 6.0
    assert all(
        row['channel'] == 'guild' and row['owner_subsystem'] == 'guild'
        for row in inserted
    )
    welcome_prompt = prompts[0][1]
    assert 'Bran, a level 30 male Human Warrior has just joined' in (
        welcome_prompt
    )
    assert '"A friendly leveling guild."' in welcome_prompt
    reply_prompt = prompts[1][1]
    assert 'Aliss: Welcome aboard' in reply_prompt


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
                dict(c, speaker=_candidate(0, 'x')['speaker'])
                for c in candidates
            ],
        ),
        patch.object(
            chatter_guild_events, 'get_guild_profile',
            return_value=_profile(),
        ),
        patch.object(
            chatter_guild_events, 'run_single_prompt',
        ) as generate,
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


# -- General channel ---------------------------------------------------

def test_general_praise_can_include_guild_master():
    import chatter_ambient

    profile = _profile(info='Friends first.')
    profile['leader'] = {
        'guid': 5, 'name': 'Varra', 'race': 'Orc', 'class': 'Warrior',
    }
    with (
        patch.object(
            chatter_ambient, 'get_character_guild',
            return_value={'id': 9, 'name': 'Keepers', 'rank': 3},
        ),
        patch.object(
            chatter_ambient, 'get_guild_profile', return_value=profile,
        ),
        patch.object(chatter_ambient.random, 'randint', return_value=1),
    ):
        topic = chatter_ambient._guild_praise_topic(
            object(), {}, {'guid': 101, 'name': 'Aliss'},
        )
        own_leader = chatter_ambient._guild_praise_topic(
            object(), {}, {'guid': 5, 'name': 'Varra'},
        )
    assert 'praising your own guild "Keepers"' in topic
    assert 'Guild Master Varra, an Orc Warrior' in topic
    assert '"Friends first."' in topic
    assert 'Guild Master' not in own_leader

    with patch.object(chatter_ambient.random, 'randint', return_value=9):
        assert chatter_ambient._guild_praise_topic(
            object(), {}, {'guid': 101},
        ) == ''


def test_general_discussion_needs_two_guilded_speakers():
    import chatter_ambient

    bots = [
        {'guid': 1, 'name': 'Aliss', 'guild_name': 'Keepers'},
        {'guid': 2, 'name': 'Bran', 'guild_name': 'Wardens'},
        {'guid': 3, 'name': 'Cato', 'guild_name': ''},
    ]
    with patch.object(chatter_ambient.random, 'randint', return_value=1):
        topic = chatter_ambient._guild_discussion_topic(
            object(), {}, bots,
        )
        lonely = chatter_ambient._guild_discussion_topic(
            object(), {}, bots[1:],
        )
    assert 'Aliss belongs to "Keepers"' in topic
    assert 'Bran belongs to "Wardens"' in topic
    assert 'Cato has no guild' in topic
    assert lonely == ''


# -- C++ and SQL wiring ------------------------------------------------

def test_cpp_guild_script_hooks_and_buffers():
    source = (MODULE_DIR / 'src' / 'LLMChatterGuild.cpp').read_text(
        encoding='utf-8'
    )
    assert 'class LLMChatterGuildEventScript : public GuildScript' in source
    assert 'GUILDHOOK_ON_MOTD_CHANGED' in source
    assert 'GUILDHOOK_ON_EVENT' in source
    assert 'case GUILD_EVENT_LOG_JOIN_GUILD:' in source
    assert 'case GUILD_EVENT_LOG_PROMOTE_PLAYER:' in source
    assert 'case GUILD_EVENT_LOG_DEMOTE_PLAYER:' in source
    assert 'new LLMChatterGuildEventScript();' in source
    assert 'std::lock_guard<std::mutex> guard(sGuildEventMutex);' in source
    assert 'FROM guild_eventlog' in source
    assert 'change.currentRank == change.originalRank' in source
    assert '_guildRankChangeDebounceSeconds' in source
    assert 'EnsureGuildPlayerSession(player);' in source
    for event_type in (
        'guild_member_join', 'guild_rank_change', 'guild_motd_comment',
    ):
        assert f'eventType == "{event_type}"' in source
        assert f'"{event_type}"' in source


def test_sql_adds_guild_news_event_types():
    sql_dir = MODULE_DIR / 'data' / 'sql' / 'characters'
    update = (
        sql_dir / 'updates' / '20260925_guild_member_events.sql'
    ).read_text(encoding='utf-8')
    base = (
        sql_dir / 'base' / '00000000_llm_chatter_tables.sql'
    ).read_text(encoding='utf-8')
    for event_type in (
        'guild_member_join', 'guild_rank_change', 'guild_motd_comment',
    ):
        assert f"'{event_type}'" in update
        assert f"'{event_type}'" in base
    assert "'guild_login_greeting'" in update


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} guild member event tests passed")
