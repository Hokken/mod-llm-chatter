#!/usr/bin/env python3
"""Guild world events: meet greeting and its held Guild follow-up, the
General join announcement and NPC encounters, plus the C++ and SQL
wiring.

Run directly from the module root:
  python tools/tests/test_guild_world_events.py
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
                "Anthropic" if module_name == "anthropic" else "OpenAI"
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
import chatter_guild_world_events as world  # noqa: E402
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402

NEW_EVENTS = (
    'guild_meet_greeting', 'guild_join_zone_announce', 'guild_npc_encounter',
)
MOOD_WORDS = ('glad', 'warm', 'happily', 'proud', 'cheerful',
              'enthusiastic', 'boast')
SPEAKER = {
    'race': 'Orc', 'class': 'Warrior', 'gender': 'male', 'level': 40,
    'traits': ['blunt'], 'tone': 'cold and curt', 'backstory': '',
}
RP = {'LLMChatter.ChatterMode': 'roleplay'}


def _event(event_type, extra):
    return {'id': 42, 'event_type': event_type,
            'extra_data': json.dumps(extra)}


def _guild_extra(**fields):
    base = {
        'guild_id': 3, 'guild_name': 'Iron Wolves', 'team': 'Horde',
        'bot_guid': 10, 'bot_name': 'Grom', 'bot_race': 'Orc',
        'bot_class': 'Warrior', 'bot_gender': 'male', 'bot_level': 40,
        'zone_id': 17,
    }
    base.update(fields)
    return base


def _meet_extra(**fields):
    return _guild_extra(player_guid=77, player_name='Vlad',
                        player_race='Troll', player_class='Mage',
                        player_gender='male', player_level=38,
                        area_id=380, **fields)


def _text(prompt) -> str:
    return getattr(prompt, 'user_prompt', prompt)


def _assert_no_mood(text: str):
    lowered = text.lower().replace('from warm to dry', '')
    for word in MOOD_WORDS:
        assert word not in lowered, word


class _Capture:
    def __init__(self):
        self.inserted = []
        self.marked = []
        self.prompts = []
        self.prepared = []
        self.held = []

    def prepare(self, db, client, config, participants, prepared=None,
                channel='guild'):
        self.prepared.append((channel, [p['name'] for p in participants]))
        return [dict(p, speaker=dict(p['speaker'])) for p in participants]

    def insert(self, db, **kwargs):
        self.inserted.append(kwargs)
        return len(self.inserted)

    def mark(self, db, event_id, status):
        self.marked.append(status)

    def hold(self, db, follow_up_id, greeting_id):
        self.held.append((follow_up_id, greeting_id))
        return 'pending'


def _patches(capture, messages):
    def single(client, config, prompt, name, *args, **kwargs):
        capture.prompts.append(_text(prompt))
        return [{'name': name, 'message': messages[len(capture.prompts) - 1]}]

    return [
        patch.object(world, '_query_speaker', return_value=dict(SPEAKER)),
        patch.object(world, 'prepare_guild_speakers',
                     side_effect=capture.prepare),
        patch.object(world, 'insert_chat_message', side_effect=capture.insert),
        patch.object(common, 'insert_chat_message', side_effect=capture.insert),
        patch.object(world, '_mark_event', side_effect=capture.mark),
        patch.object(world, 'run_single_prompt', side_effect=single),
        patch.object(common, 'run_single_prompt', side_effect=single),
        patch.object(world, 'hold_follow_up', side_effect=capture.hold),
        patch.object(world, 'get_guild_profile', return_value={}),
        patch.object(world, 'get_character_guild_name',
                     return_value='Ember Court'),
        patch.object(world, 'player_character_lines', return_value=[]),
        patch.object(world, '_reserve_zone_delivery_window',
                     return_value=0.0),
        patch.object(common, 'calculate_dynamic_delay', return_value=5.0),
    ]


def _run(handler, event, capture, messages, config=RP):
    patches = _patches(capture, messages)
    for item in patches:
        item.start()
    try:
        return handler(None, None, config, event)
    finally:
        for item in reversed(patches):
            item.stop()


def _src(name: str) -> str:
    return (MODULE_DIR / 'src' / name).read_text(encoding='utf-8')


def _function_body(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
            if depth == 0:
                return source[brace:index]
    raise AssertionError(signature)


# -- Registry --------------------------------------------------------------

def test_registry_routes_new_events():
    for event_type in NEW_EVENTS:
        spec = EVENT_REGISTRY[event_type]
        assert spec.handler_module == 'chatter_guild_world_events'
        assert spec.producer == 'LLMChatterGuildWorld.cpp'
        assert hasattr(world, spec.handler_func), spec.handler_func
    assert 'bot_group_pvp_kill' not in EVENT_REGISTRY
    for event_type in ('guild_pvp_kill', 'guild_pvp_death',
                       'zone_pvp_death'):
        spec = EVENT_REGISTRY.get(event_type)
        assert spec is None or (
            spec.handler_module != 'chatter_guild_world_events'
        ), event_type


# -- Meet greeting -----------------------------------------------------------

def test_meet_greeting_says_hello_to_the_player():
    capture = _Capture()
    ok = _run(world.process_guild_meet_greeting_event,
              _event('guild_meet_greeting', _meet_extra()), capture,
              ['Vlad. Mind the raptors.'],
              config=dict(RP, **{
                  'LLMChatter.GuildChatter.MeetGreeting.GuildPostChance':
                  '0'}))
    assert ok and capture.marked == ['completed']
    assert len(capture.inserted) == 1 and not capture.held
    row = capture.inserted[0]
    assert row['channel'] == 'say' and row['emote'] == 'hello'
    assert row['player_guid'] == 77 and row['addressee_player_guid'] == 77
    assert row['owner_subsystem'] == 'guild'
    assert capture.prepared == [('guild', ['Grom'])]


def test_meet_greeting_prompt_lets_a_cold_persona_be_cold():
    capture = _Capture()
    _run(world.process_guild_meet_greeting_event,
         _event('guild_meet_greeting', _meet_extra()), capture,
         ['Vlad.'],
         config=dict(RP, **{
             'LLMChatter.GuildChatter.MeetGreeting.GuildPostChance': '0'}))
    prompt = capture.prompts[0]
    assert 'Grom speaking tone: cold and curt.' in prompt
    assert ('React to meeting Vlad the way Grom naturally would, given '
            'their personality and tone.') in prompt
    assert 'a dry remark' in prompt
    _assert_no_mood(prompt)


def test_meet_follow_up_is_held_until_the_greeting_is_spoken():
    capture = _Capture()
    ok = _run(world.process_guild_meet_greeting_event,
              _event('guild_meet_greeting', _meet_extra()), capture,
              ['Vlad. Mind the raptors.', 'Ran into Vlad at the Crossroads.'],
              config=dict(RP, **{
                  'LLMChatter.GuildChatter.MeetGreeting.GuildPostChance':
                  '100'}))
    assert ok
    say, post = capture.inserted
    assert say['channel'] == 'say'
    assert post['channel'] == 'guild' and post['sequence'] == 1
    assert post['owner_subsystem'] == 'guild'
    assert post['delivery_policy'] == 'filler'
    assert capture.held == [(2, 1)]
    guild_prompt = capture.prompts[1]
    assert 'The Crossroads in The Barrens' in guild_prompt
    assert '"Vlad. Mind the raptors."' in guild_prompt
    assert 'React the way Grom naturally would' in guild_prompt
    _assert_no_mood(guild_prompt)


def test_meet_follow_up_skipped_during_player_conversation():
    capture = _Capture()
    _run(world.process_guild_meet_greeting_event,
         _event('guild_meet_greeting',
                _meet_extra(guild_post_allowed=False)),
         capture, ['Vlad.'],
         config=dict(RP, **{
             'LLMChatter.GuildChatter.MeetGreeting.GuildPostChance': '100'}))
    assert [row['channel'] for row in capture.inserted] == ['say']
    assert not capture.held


class _FakeCursor:
    def __init__(self, db):
        self.db = db

    def execute(self, sql, params=()):
        self.db.statements.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.db.greeting_row


class _FakeDb:
    def __init__(self, greeting_row):
        self.greeting_row = greeting_row
        self.statements = []

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        pass


def test_hold_follow_up_settles_by_greeting_state():
    db = _FakeDb((0, None, None))
    assert world.hold_follow_up(db, 9, 8) == 'pending'
    assert db.statements[0][0].startswith(
        'UPDATE llm_chatter_messages SET deliver_at = NULL')
    assert db.statements[0][1] == (9,)
    assert len(db.statements) == 2

    db = _FakeDb((1, None, None))
    assert world.hold_follow_up(db, 9, 8) == 'pending'

    db = _FakeDb((1, '2026-10-02 10:00:00', None))
    assert world.hold_follow_up(db, 9, 8) == 'spoken'
    release, params = db.statements[-1]
    assert 'SET deliver_at = DATE_ADD(NOW()' in release
    assert 'deliver_at IS NULL' in release
    assert 8 <= params[0] <= 15 and params[1] == 9

    db = _FakeDb((1, '2026-10-02 10:00:00', 'meet_out_of_range'))
    assert world.hold_follow_up(db, 9, 8) == 'dropped'
    cancel, params = db.statements[-1]
    assert 'SET delivered = 1' in cancel and 'deliver_at IS NULL' in cancel
    assert params == ('meet_greeting_not_delivered', 9)


def test_cpp_meet_greeting_is_rechecked_at_delivery():
    world_src = _src('LLMChatterGuildWorld.cpp')
    check = _function_body(
        world_src, 'char const* CheckMeetGreetingDelivery(')
    for needle in ('bot->GetMap() != player->GetMap()',
                   'IsWithinDistInMap(player, radius)',
                   '_guildMeetGreetingRadius',
                   'player->CanSeeOrDetect(bot)',
                   'player->IsWithinLOSInMap(bot)',
                   '"meet_out_of_range"', '"meet_player_gone"'):
        assert needle in check, needle

    delivery = _src('LLMChatterDelivery.cpp')
    body = _function_body(delivery, 'void DeliverPendingMessagesImpl(')
    gate = body.index('CheckMeetGreetingDelivery(bot, playerGuid)')
    assert gate < body.index('ai->Say(processedMessage)')
    drop = body[gate:gate + 700]
    defer = drop.index('if (DeferMeetGreeting(messageId, meetDrop))')
    keep = drop.index('replyHold.Keep();')
    assert defer < keep < drop.index('FinalizeDroppedMessage(')
    assert 'SettleMeetGreetingFollowUp(eventId, false);' in drop
    # The delivery scope ends the hold on this terminal drop.
    assert 'ReleaseBotReplyHold' not in drop
    assert body.index('ReplyHoldDeliveryScope replyHold(botGuid, eventType);') \
        < gate
    settle = body.rindex('SettleMeetGreetingFollowUp(eventId, sent);')
    assert settle > body.rindex('"SET delivered = 0, "')
    assert settle > body.rindex('FinalizeDroppedMessage(')


def test_cpp_meet_greeting_retries_passing_failures():
    source = _src('LLMChatterGuildWorld.cpp')
    defer = _function_body(source, 'bool DeferMeetGreeting(')
    for reason in ('"meet_out_of_range"', '"meet_not_visible"',
                   '"meet_no_line_of_sight"'):
        assert reason in defer, reason
    for reason in ('meet_player_gone', 'meet_other_map',
                   'meet_bot_unavailable'):
        assert reason not in defer, reason
    assert 'kMeetDeliveryGraceSeconds' in defer
    assert 'SET delivered = 0' in defer
    assert 'INTERVAL {} SECOND' in defer
    assert 'kMeetDeliveryRetrySeconds' in defer
    assert 'constexpr time_t kMeetDeliveryGraceSeconds = 8;' in source


def test_cpp_follow_up_release_and_cancel():
    source = _src('LLMChatterGuildWorld.cpp')
    settle = _function_body(source, 'void SettleMeetGreetingFollowUp(')
    assert settle.count('deliver_at IS NULL') == 2
    assert 'meet_greeting_not_delivered' in settle
    assert 'urand(kMeetFollowUpMinDelay, kMeetFollowUpMaxDelay)' in settle
    sweep = _function_body(source, 'void SweepHeldFollowUps(')
    assert "e.event_type = 'guild_meet_greeting'" in sweep


def test_cpp_meet_scan_uses_short_reply_hold():
    source = _src('LLMChatterGuildWorld.cpp')
    scan = _function_body(source, 'void ScanMeetGreetings(')
    assert 'HoldBotForReply(bot, player, "guild_meet_greeting")' in scan
    assert '"guild_post_allowed":{}' in scan
    assert 'GuildConversationActive(guildId)' in scan
    assert 'IsPersistedEventOnCooldown(key, cooldown)' in scan
    assert 'InSameGroup(bot, player)' in scan
    assert 'GetMotionMaster' not in source


# -- NPC encounter ----------------------------------------------------------

def test_npc_encounter_names_npc_without_inventing_history():
    scenario = " ".join(world._npc_scenario(
        _guild_extra(npc_name='Innkeeper Grosk', npc_subname='Innkeeper',
                     npc_role='Innkeeper'), 'roleplay'))
    assert 'Innkeeper Grosk <Innkeeper>' in scenario
    assert 'opinion' in scenario
    assert 'had not met' not in scenario and 'met before' not in scenario


def test_npc_encounter_posts_filler_guild_line():
    capture = _Capture()
    ok = _run(world.process_guild_npc_encounter_event,
              _event('guild_npc_encounter',
                     _guild_extra(npc_name='Innkeeper Grosk',
                                  npc_role='Innkeeper')),
              capture, ['Grosk waters the ale in Orgrimmar.'])
    assert ok and capture.marked == ['completed']
    row = capture.inserted[0]
    assert row['channel'] == 'guild' and row['owner_subsystem'] == 'guild'
    assert row['delivery_policy'] == 'filler'
    assert 'React the way Grom naturally would' in capture.prompts[0]


def test_cpp_npc_encounter_visibility_and_flags():
    source = _src('LLMChatterGuildWorld.cpp')
    check = _function_body(source, 'bool IsFriendlyServiceNpc(')
    assert 'creature->HasNpcFlag(kServiceNpcFlags)' in check
    assert 'bot->CanSeeOrDetect(creature)' in check
    assert 'bot->IsWithinLOSInMap(creature)' in check
    assert 'UNIT_NPC_FLAGS' not in source
    encounter = _function_body(source, 'bool TryNpcEncounter(')
    assert 'GuildConversationActive(guild->GetId())' in encounter


# -- Guild conversation suppression at delivery ------------------------------

def test_cpp_delivery_drops_guild_filler_during_player_conversation():
    body = _function_body(
        _src('LLMChatterDelivery.cpp'), 'void DeliverPendingMessagesImpl(')
    gate = body[body.index('deliveryPolicy == "filler"') - 200:]
    gate = gate[:600]
    assert 'ownerSubsystem == "guild"' in gate
    assert 'WasGuildPlayerConversationRecent(' in gate
    assert '_guildPlayerIdleSuppressionSeconds' in gate
    assert '"guild_conversation_active"' in gate


def test_cpp_login_welcome_is_not_a_player_conversation():
    guild = _src('LLMChatterGuild.cpp')
    handle = _function_body(guild, 'void HandleGuildPlayerMessage(')
    assert 'NoteGuildPlayerConversation(player->GetGuildId());' in handle
    record = _function_body(guild, 'void RecordDeliveredGuildLine(')
    assert ('if (eventType == "guild_player_message")\n'
            '            NoteGuildPlayerConversation(guildId);') in record
    assert record.count('NoteGuildPlayerConversation(') == 1
    active = _function_body(
        _src('LLMChatterGuildWorld.cpp'), 'bool GuildConversationActive(')
    assert 'WasGuildPlayerConversationRecent(' in active
    assert 'WasGuildPlayerInteractionRecent' not in active


# -- Join announcement -------------------------------------------------------

def _announce_event():
    return _event('guild_join_zone_announce', _guild_extra(
        candidates=[{'guid': 11, 'name': 'Zul'}, {'guid': 12, 'name': 'Mok'}],
    ))


def _announce_config():
    return dict(RP, **{
        'LLMChatter.GuildChatter.JoinZoneAnnounce.MaxResponders': 2})


def _run_announce(llm_replies, capture, pacing=0.0):
    replies = iter(llm_replies)
    paced = []

    def reserve(zone_id, config, duration_seconds=0.0):
        paced.append((zone_id, duration_seconds))
        return pacing

    def fake_llm(client, prompt, config, **kwargs):
        capture.prompts.append(_text(prompt))
        return next(replies)

    patches = [
        patch.object(world, '_query_speaker', return_value=dict(SPEAKER)),
        patch.object(world, 'prepare_guild_speakers',
                     side_effect=capture.prepare),
        patch.object(world, 'insert_chat_message', side_effect=capture.insert),
        patch.object(world, '_mark_event', side_effect=capture.mark),
        patch.object(world, 'get_character_guild_name',
                     return_value='Ember Court'),
        patch.object(world, '_reserve_zone_delivery_window',
                     side_effect=reserve),
        patch.object(world.random, 'randint', return_value=2),
        patch.object(world.random, 'shuffle', side_effect=lambda items: None),
        patch.object(common, 'call_llm', side_effect=fake_llm),
        patch.object(common, 'calculate_dynamic_delay', return_value=5.0),
    ]
    for item in patches:
        item.start()
    try:
        ok = world.process_guild_join_zone_announce_event(
            None, None, _announce_config(), _announce_event(),
        )
    finally:
        for item in reversed(patches):
            item.stop()
    return ok, paced


def _conversation(*pairs):
    return json.dumps([
        {'speaker': name, 'message': message} for name, message in pairs
    ])


def test_join_announce_goes_to_general_with_reactions():
    capture = _Capture()
    ok, _ = _run_announce([_conversation(
        ('Grom', 'I ride with the Iron Wolves now.'),
        ('Zul', 'Good for you.'),
        ('Mok', 'Never heard of them.'),
    )], capture)
    assert ok
    assert [row['bot_name'] for row in capture.inserted] == [
        'Grom', 'Zul', 'Mok']
    assert all(row['channel'] == 'general' for row in capture.inserted)
    assert all('owner_subsystem' not in row for row in capture.inserted)
    prompt = capture.prompts[0]
    assert 'Iron Wolves' in prompt and 'Ember Court' in prompt
    assert 'Each speaker reacts the way they naturally would' in prompt
    _assert_no_mood(prompt)
    assert capture.prepared == [('general', ['Grom', 'Zul', 'Mok'])]


def test_join_announce_repairs_announcer_order():
    capture = _Capture()
    ok, _ = _run_announce([_conversation(
        ('Zul', 'Good for you.'),
        ('Grom', 'I ride with the Iron Wolves now.'),
        ('Mok', 'Never heard of them.'),
    )], capture)
    assert ok
    assert [row['bot_name'] for row in capture.inserted] == [
        'Grom', 'Zul', 'Mok']
    assert [row['sequence'] for row in capture.inserted] == [0, 1, 2]


def test_join_announce_rejects_duplicate_speakers_and_falls_back():
    capture = _Capture()
    duplicate = _conversation(
        ('Grom', 'I ride with the Iron Wolves now.'),
        ('Zul', 'Good for you.'),
        ('Zul', 'Really good.'),
    )
    ok, _ = _run_announce([
        duplicate, duplicate,
        json.dumps({'message': 'I ride with the Iron Wolves now.'}),
    ], capture)
    assert ok
    assert [row['bot_name'] for row in capture.inserted] == ['Grom']
    assert len(capture.prompts) == 3
    fallback = capture.prompts[2]
    assert 'Zul' not in fallback and 'Mok' not in fallback


def test_join_announce_rejects_unexpected_speaker():
    names = ['Grom', 'Zul']
    stranger = [{'name': 'Grom', 'message': 'a'},
                {'name': 'Thrall', 'message': 'b'}]
    assert common.checked_order(stranger, names, 'Grom') is None


def test_join_announce_uses_zone_pacing():
    capture = _Capture()
    ok, paced = _run_announce([_conversation(
        ('Grom', 'I ride with the Iron Wolves now.'),
        ('Zul', 'Good for you.'),
        ('Mok', 'Never heard of them.'),
    )], capture, pacing=12.0)
    assert ok
    assert paced == [(17, 10.0)]
    assert [row['delay_seconds'] for row in capture.inserted] == [
        13.0, 18.0, 23.0]


def test_cpp_join_announce_has_its_own_guild_hook():
    source = _src('LLMChatterGuildWorld.cpp')
    assert 'class LLMChatterGuildWorldGuildScript : public GuildScript' \
        in source
    assert 'GUILDHOOK_ON_ADD_MEMBER' in source
    assert 'NoteGuildJoinForZoneAnnounce(' in _function_body(
        source, 'void OnAddMember(')
    assert 'WORLDHOOK_ON_UPDATE' in source
    assert 'PickRealPlayerInZone(zoneId, team)' in source
    assert 'AddLLMChatterGuildWorldScripts();' in _src('LLMChatterScript.cpp')
    assert 'NoteGuildJoinForZoneAnnounce' not in _src('LLMChatterGuild.cpp')


# -- Wiring ------------------------------------------------------------------

def test_priorities_are_registered_in_cpp():
    source = _src('LLMChatterShared.cpp')
    table = source[source.index('kTierPriorityRules'):]
    table = table[:table.index('}};')]
    declared = int(re.search(
        r'std::array<EventPriorityRule, (\d+)>\s+kTierPriorityRules',
        source).group(1))
    assert declared == len(re.findall(r'\{"[a-z_]+",', table))
    for event_type in NEW_EVENTS:
        assert f'"{event_type}"' in table


def test_sql_adds_event_types():
    sql_dir = MODULE_DIR / 'data' / 'sql' / 'characters'
    update = (sql_dir / 'updates' / '20261002_guild_world_events.sql'
              ).read_text(encoding='utf-8')
    base = (sql_dir / 'base' / '00000000_llm_chatter_tables.sql'
            ).read_text(encoding='utf-8')
    assert 'information_schema.COLUMNS' in update
    assert 'LEFT(@event_type, CHAR_LENGTH(@event_type) - 1)' in update
    for event_type in NEW_EVENTS:
        assert f"'''{event_type}'''" in update
        assert f"'{event_type}'" in base


def test_session_cleanup_keeps_meet_cooldown_rows():
    source = (TOOLS_DIR / 'chatter_db.py').read_text(encoding='utf-8')
    body = source[source.index('def cleanup_all_session_data('):]
    assert "WHERE event_type <> 'guild_meet_greeting'" in body
    assert "OR status IN ('pending', 'processing')" in body


def test_config_keys_in_both_confs():
    conf = MODULE_DIR / 'conf'
    for path in (conf / 'mod_llm_chatter.conf.dist',
                 conf / 'presets' / 'mod_ll_chatter_quieter.conf.dist'):
        text = path.read_text(encoding='utf-8')
        for key in (
            'MeetGreeting.Enable', 'MeetGreeting.Radius',
            'MeetGreeting.CooldownHours', 'MeetGreeting.GuildPostChance',
            'WorldScanInterval', 'JoinZoneAnnounce.Enable',
            'JoinZoneAnnounce.Chance', 'JoinZoneAnnounce.MaxResponders',
            'NpcEncounter.Enable', 'NpcEncounter.Chance',
            'NpcEncounter.Radius', 'NpcEncounter.Cooldown',
        ):
            assert re.search(
                rf'^LLMChatter\.GuildChatter\.{re.escape(key)} = \d+',
                text, re.M), (path.name, key)


def test_structured_event_repairs_keep_the_contract():
    config = {'LLMChatter.StructuredOutput.Enable': '1'}
    speaker = {'class': 'Mage', 'race': 'Human', 'gender': 'female',
               'level': 80, 'traits': [], 'tone': '', 'backstory': ''}
    prompts = []

    def record(client, prompt, config, **kwargs):
        prompts.append(prompt)
        return ''

    for names in (['Aliss'], ['Aliss', 'Bran']):
        prompts.clear()
        prompt, _ = common.build_prompt(
            [{'name': name, 'speaker': speaker, 'zone_id': 12,
              'map_id': 0} for name in names],
            'Keepers', 'Alliance', 'normal', [],
            ['A dragon was slain.'], 120,
        )
        assert prompt.response_contract.message_only
        with patch.object(common, 'call_llm', side_effect=record):
            common.generate(None, config, 7, 'guild_world_event', prompt,
                            names, 120, {})
        assert len(prompts) == 2
        assert all(p.response_contract == prompt.response_contract
                   for p in prompts)


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} guild world event tests passed")
