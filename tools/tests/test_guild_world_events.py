#!/usr/bin/env python3
"""Guild world events: meet greeting, join announcement, PvP kills and
NPC encounters, plus the C++ and SQL wiring.

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

import chatter_guild_world_events as world  # noqa: E402
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402

NEW_EVENTS = (
    'guild_meet_greeting', 'guild_join_zone_announce', 'guild_pvp_kill',
    'bot_group_pvp_kill', 'guild_npc_encounter',
)
SPEAKER = {
    'race': 'Orc', 'class': 'Warrior', 'class_style': 'Warrior',
    'gender': 'male', 'level': 40, 'traits': ['blunt'], 'tone': '',
    'backstory': '',
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


class _Capture:
    def __init__(self):
        self.inserted = []
        self.marked = []
        self.prompts = []

    def insert(self, db, **kwargs):
        self.inserted.append(kwargs)

    def mark(self, db, event_id, status):
        self.marked.append(status)


def _patches(capture, messages):
    def single(client, config, prompt, name, *args, **kwargs):
        capture.prompts.append(getattr(prompt, 'user_prompt', prompt))
        return [{'name': name, 'message': messages[0]}]

    def multi(client, config, prompt, names, *args, **kwargs):
        capture.prompts.append(getattr(prompt, 'user_prompt', prompt))
        return [{'name': n, 'message': m} for n, m in zip(names, messages)]

    return [
        patch.object(world, '_query_speaker', return_value=dict(SPEAKER)),
        patch.object(world, 'insert_chat_message', side_effect=capture.insert),
        patch.object(world, '_mark_event', side_effect=capture.mark),
        patch.object(world, 'run_single_prompt', side_effect=single),
        patch.object(world, 'run_multi_prompt', side_effect=multi),
        patch.object(world, 'get_guild_profile', return_value={}),
        patch.object(world, 'get_character_guild_name',
                     return_value='Ember Court'),
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


def test_registry_routes_new_events():
    for event_type in NEW_EVENTS:
        spec = EVENT_REGISTRY[event_type]
        assert spec.handler_module == 'chatter_guild_world_events'
        assert hasattr(world, spec.handler_func), spec.handler_func


def test_meet_greeting_says_hello_to_the_player():
    capture = _Capture()
    extra = _guild_extra(player_guid=77, player_name='Vlad',
                         player_race='Troll', player_class='Mage',
                         player_gender='male', player_level=38)
    ok = _run(world.process_guild_meet_greeting_event,
              _event('guild_meet_greeting', extra), capture,
              ['Vlad! Good hunting, brother.'])
    assert ok and capture.marked == ['completed']
    row = capture.inserted[0]
    assert row['channel'] == 'say' and row['emote'] == 'hello'
    assert row['player_guid'] == 77 and row['addressee_player_guid'] == 77
    assert row['owner_subsystem'] == 'guild'
    assert 'Iron Wolves' in capture.prompts[0]
    assert 'Vlad' in capture.prompts[0]


def test_meet_greeting_may_tell_the_guild_where_they_met():
    extra = _guild_extra(player_guid=77, player_name='Vlad',
                         player_race='Troll', player_class='Mage',
                         area_id=380)
    capture = _Capture()
    ok = _run(world.process_guild_meet_greeting_event,
              _event('guild_meet_greeting', extra), capture,
              ['Vlad! Good hunting, brother.'],
              config=dict(RP, **{
                  'LLMChatter.GuildChatter.MeetGreeting.GuildPostChance':
                  '100'}))
    assert ok and capture.marked == ['completed']
    say, post = capture.inserted
    assert say['channel'] == 'say'
    assert post['channel'] == 'guild' and post['sequence'] == 1
    assert post['owner_subsystem'] == 'guild'
    assert post['delay_seconds'] > say['delay_seconds']
    guild_prompt = capture.prompts[1]
    assert 'The Crossroads in The Barrens' in guild_prompt
    assert 'Vlad' in guild_prompt and 'Iron Wolves' in guild_prompt

    capture = _Capture()
    _run(world.process_guild_meet_greeting_event,
         _event('guild_meet_greeting', extra), capture, ['Vlad!'],
         config=dict(RP, **{
             'LLMChatter.GuildChatter.MeetGreeting.GuildPostChance': '0'}))
    assert [row['channel'] for row in capture.inserted] == ['say']


def test_meet_greeting_can_be_disabled():
    capture = _Capture()
    ok = _run(world.process_guild_meet_greeting_event,
              _event('guild_meet_greeting', _guild_extra(player_guid=1)),
              capture, ['hi'],
              config={'LLMChatter.GuildChatter.MeetGreeting.Enable': '0'})
    assert not ok and capture.marked == ['skipped']


def test_join_announce_goes_to_general_with_reactions():
    capture = _Capture()
    extra = _guild_extra(candidates=[{'guid': 11, 'name': 'Zul'},
                                     {'guid': 12, 'name': 'Mok'}])
    config = dict(RP, **{
        'LLMChatter.GuildChatter.JoinZoneAnnounce.MaxResponders': 2})
    with patch.object(world.random, 'randint', return_value=2):
        ok = _run(world.process_guild_join_zone_announce_event,
                  _event('guild_join_zone_announce', extra), capture,
                  ['I joined the Iron Wolves!', 'Well done.', 'Pathetic.'],
                  config=config)
    assert ok
    assert [row['channel'] for row in capture.inserted] == ['general'] * 3
    assert capture.inserted[0]['bot_name'] == 'Grom'
    prompt = capture.prompts[0]
    assert 'Iron Wolves' in prompt and 'disdain' in prompt
    assert 'Ember Court' in prompt


def test_guild_pvp_kill_is_first_person_with_victim_details():
    capture = _Capture()
    extra = _guild_extra(victim_name='Aldric', victim_race='Human',
                         victim_class='Paladin', victim_gender='male',
                         victim_level=39)
    with patch('chatter_guild_events.insert_chat_message',
               side_effect=capture.insert), \
            patch('chatter_guild_events.run_single_prompt',
                  side_effect=lambda c, cfg, p, name, *a, **k: (
                      capture.prompts.append(
                          getattr(p, 'user_prompt', p))
                      or [{'name': name, 'message': 'Aldric fell.'}])):
        ok = _run(world.process_guild_pvp_kill_event,
                  _event('guild_pvp_kill', extra), capture, ['x'])
    assert ok
    prompt = capture.prompts[-1]
    assert 'Human Paladin' in prompt and 'Aldric' in prompt
    assert 'first person' in prompt
    assert capture.inserted[0]['channel'] == 'guild'


def test_npc_encounter_names_npc_and_role():
    scenario = " ".join(world._npc_scenario(
        _guild_extra(npc_name='Innkeeper Grosk', npc_subname='Innkeeper',
                     npc_role='Innkeeper'), 'roleplay'))
    assert 'Innkeeper Grosk <Innkeeper>' in scenario
    assert 'opinion' in scenario


def test_group_pvp_kill_prompt_is_we_perspective():
    ctx = {
        'bot': {'name': 'Grom', 'race': 'Orc', 'class': 'Warrior',
                'level': 40, 'gender': 'male'},
        'traits': ['blunt'], 'stored_tone': 'dry', 'mode': 'roleplay',
        'chat_hist': '',
        'extra_data': {
            'victim_name': 'Aldric', 'victim_race': 'Human',
            'victim_class': 'Paladin', 'victim_gender': 'male',
            'victim_level': 30, 'killer_name': 'Vlad',
            'killer_is_reactor': False, 'zone_id': 17,
        },
    }
    prompt = world.build_group_pvp_kill_prompt(ctx)
    text = getattr(prompt, 'user_prompt', prompt)
    assert '"we"' in text and 'Vlad struck the killing blow' in text
    assert 'far less seasoned' in text
    assert 'guild' not in text.lower()


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


def test_cpp_group_pvp_kill_has_no_guild_checks():
    source = (MODULE_DIR / 'src' / 'LLMChatterGuildWorld.cpp').read_text(
        encoding='utf-8')
    body = _function_body(source, 'bool QueueGroupPvpKill(')
    assert 'Guild' not in body and 'guild' not in body
    assert '_groupPvpKillChance' in body
    entry = _function_body(source, 'void HandleOpenWorldPvpKill(')
    assert 'Guild' not in entry.split('QueueGuildPvpKill')[0]
    assert entry.index('QueueGroupPvpKill') < entry.index(
        'QueueGuildPvpKill')
    guild_body = _function_body(source, 'void QueueGuildPvpKill(')
    assert 'IsGroupedWithRealPlayer(killer)' in guild_body


def test_cpp_bg_kill_uses_rare_massive_battle_chance():
    source = (MODULE_DIR / 'src' / 'LLMChatterPlayer.cpp').read_text(
        encoding='utf-8')
    body = _function_body(source, 'void OnPlayerPVPKill(')
    assert 'HandleOpenWorldPvpKill(killer, killed)' in body
    assert '_groupPvpKillBattlegroundChance' in body
    assert 'massive_battle' in body
    assert 'Guild' not in body


def test_cpp_meet_greeting_cooldown_and_join_hook():
    source = (MODULE_DIR / 'src' / 'LLMChatterGuildWorld.cpp').read_text(
        encoding='utf-8')
    assert '_guildMeetGreetingCooldownHours * 3600' in source
    assert 'InSameGroup(bot, player)' in source
    assert 'IsPersistedEventOnCooldown(key, cooldown)' in source
    guild = (MODULE_DIR / 'src' / 'LLMChatterGuild.cpp').read_text(
        encoding='utf-8')
    assert 'NoteGuildJoinForZoneAnnounce(' in guild
    assert 'UpdateGuildWorldEvents();' in guild


def test_priorities_are_registered_in_cpp():
    source = (MODULE_DIR / 'src' / 'LLMChatterShared.cpp').read_text(
        encoding='utf-8')
    table = source[source.index('kTierPriorityRules'):]
    table = table[:table.index('}};')]
    declared = int(re.search(
        r'std::array<EventPriorityRule, (\d+)>\s+kTierPriorityRules',
        source).group(1))
    assert declared == len(re.findall(r'\{"[a-z_]+",', table))
    for event_type in NEW_EVENTS:
        assert f'"{event_type}"' in table


def test_sql_adds_event_types_and_audience_column():
    sql_dir = MODULE_DIR / 'data' / 'sql' / 'characters'
    update = (sql_dir / 'updates' / '20260927_guild_world_events.sql'
              ).read_text(encoding='utf-8')
    base = (sql_dir / 'base' / '00000000_llm_chatter_tables.sql'
            ).read_text(encoding='utf-8')
    for event_type in NEW_EVENTS:
        assert f"'{event_type}'" in update
        assert f"'{event_type}'" in base
    assert 'audience_context' in update
    assert '`audience_context` JSON DEFAULT NULL' in base


DEATH_EVENTS = ('guild_pvp_death', 'zone_pvp_death')


def _death_extra(**fields):
    return _guild_extra(killer_guid=20, killer_name='Aldric',
                        killer_race='Human', killer_class='Paladin',
                        killer_gender='female', killer_level=48,
                        killer_is_bot=True, **fields)


def test_registry_routes_death_events():
    for event_type in DEATH_EVENTS:
        spec = EVENT_REGISTRY[event_type]
        assert spec.handler_module == 'chatter_guild_world_events'
        assert hasattr(world, spec.handler_func), spec.handler_func
        assert 'killer_name' in spec.payload_fields


def test_death_scenario_names_killer_and_follows_mode():
    rp = " ".join(world._pvp_death_scenario(
        _death_extra(), 'roleplay', 'the guild'))
    assert 'Aldric' in rp and 'female Human Paladin' in rp
    assert 'far more seasoned than Grom' in rp
    assert 'contempt, resentment or anger' in rp
    assert 'not as a player' in rp and 'ganking' in rp
    normal = " ".join(world._pvp_death_scenario(
        _death_extra(), 'normal', 'the guild'))
    assert 'grumbling' in normal and 'not as a player' not in normal
    assert '48' in normal


def test_guild_death_complaint_goes_to_guild_chat():
    capture = _Capture()
    with patch('chatter_guild_events.insert_chat_message',
               side_effect=capture.insert), \
            patch('chatter_guild_events.run_single_prompt',
                  side_effect=lambda c, cfg, p, name, *a, **k: (
                      capture.prompts.append(
                          getattr(p, 'user_prompt', p))
                      or [{'name': name, 'message': 'Curse you, Aldric.'}])):
        ok = _run(world.process_guild_pvp_death_event,
                  _event('guild_pvp_death', _death_extra()), capture, ['x'])
    assert ok and capture.inserted[0]['channel'] == 'guild'
    prompt = capture.prompts[-1]
    assert 'Iron Wolves' in prompt and 'Aldric' in prompt
    assert 'tells the guild' in prompt


def test_zone_death_complaint_goes_to_general():
    capture = _Capture()
    extra = _death_extra()
    extra.pop('guild_id')
    extra.pop('guild_name')
    ok = _run(world.process_zone_pvp_death_event,
              _event('zone_pvp_death', extra), capture,
              ['Aldric the Paladin still lurks here. Beware!'])
    assert ok and capture.marked == ['completed']
    row = capture.inserted[0]
    assert row['channel'] == 'general' and row['bot_name'] == 'Grom'
    assert 'owner_subsystem' not in row
    prompt = capture.prompts[0]
    assert 'General chat' in prompt and 'Aldric' in prompt
    assert 'Never insult or mock the Horde' in prompt
    assert 'still be around' in prompt


def test_death_complaints_can_be_disabled():
    capture = _Capture()
    ok = _run(world.process_zone_pvp_death_event,
              _event('zone_pvp_death', _death_extra()), capture, ['x'],
              config={'LLMChatter.GeneralChat.PvpDeath.Enable': '0'})
    assert not ok and capture.marked == ['skipped']
    capture = _Capture()
    ok = _run(world.process_guild_pvp_death_event,
              _event('guild_pvp_death', _death_extra()), capture, ['x'],
              config={'LLMChatter.GuildChatter.PvpDeath.Enable': '0'})
    assert not ok and capture.marked == ['skipped']


def test_cpp_death_complaint_gating_and_cooldowns():
    source = (MODULE_DIR / 'src' / 'LLMChatterGuildWorld.cpp').read_text(
        encoding='utf-8')
    body = _function_body(source, 'void QueuePvpDeathComplaint(')
    assert '!IsPlayerBot(killer) || !IsPlayerBot(killed)' in body
    assert 'IsGroupedWithRealPlayer(killed)' in body
    assert 'PickRealGuildMember(guildId)' in body
    assert 'PickRealPlayerInZone(zoneId, team)' in body
    assert '_generalChannelEnable' in body
    locked = body[body.index('std::lock_guard<std::mutex> guard('
                             'sPvpCooldownMutex)'):]
    for name in ('sPvpDeathVictimCooldowns', 'sGuildPvpDeathCooldowns',
                 'sZonePvpDeathCooldowns'):
        assert name in locked
    kill = _function_body(source, 'void QueueGuildPvpKill(')
    assert kill.index('sPvpCooldownMutex') < kill.index(
        'sGuildPvpKillCooldowns')
    entry = _function_body(source, 'void HandleOpenWorldPvpKill(')
    assert 'InBattleground()' in entry
    assert entry.index('QueueGuildPvpKill') < entry.index(
        'QueuePvpDeathComplaint')


def _enum_values(text):
    return re.findall(r"'([a-z_]+)'", text)


def test_death_sql_matches_base_enum():
    sql_dir = MODULE_DIR / 'data' / 'sql' / 'characters'
    update = (sql_dir / 'updates' / '20260930_pvp_death_complaints.sql'
              ).read_text(encoding='utf-8')
    base = (sql_dir / 'base' / '00000000_llm_chatter_tables.sql'
            ).read_text(encoding='utf-8')
    update_enum = update[update.index('enum('):update.index(') NOT NULL')]
    start = base.index('`event_type` ENUM(')
    base_enum = base[start:base.index(') NOT NULL', start)]
    assert _enum_values(update_enum) == _enum_values(base_enum)
    for event_type in DEATH_EVENTS:
        assert f"'{event_type}'" in update_enum


def test_death_priorities_are_registered():
    source = (MODULE_DIR / 'src' / 'LLMChatterShared.cpp').read_text(
        encoding='utf-8')
    table = source[source.index('kTierPriorityRules'):]
    table = table[:table.index('}};')]
    for event_type in DEATH_EVENTS:
        assert f'{{"{event_type}",' in table


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} guild world event tests passed")
