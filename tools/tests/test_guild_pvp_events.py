#!/usr/bin/env python3
"""Open-world PvP reactions: Guild kill comments, Guild and General death
reactions, battleground kill context, and the C++, SQL and conf wiring.

Run directly from the module root:
  python tools/tests/test_guild_pvp_events.py
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
import chatter_guild_pvp_events as pvp  # noqa: E402
from chatter_bg_prompts import build_bg_pvp_kill_prompt  # noqa: E402
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402

NEW_EVENTS = ('guild_pvp_kill', 'guild_pvp_death', 'zone_pvp_death')
SPEAKER = {
    'race': 'Orc', 'class': 'Warrior', 'gender': 'male', 'level': 40,
    'traits': ['blunt'], 'tone': 'cold and curt', 'backstory': '',
}
RP = {'LLMChatter.ChatterMode': 'roleplay'}


def _event(event_type, extra):
    return {'id': 42, 'event_type': event_type,
            'extra_data': json.dumps(extra)}


def _kill_extra(**fields):
    base = {
        'guild_id': 3, 'guild_name': 'Iron Wolves', 'team': 'Horde',
        'bot_guid': 10, 'bot_name': 'Grom', 'bot_race': 'Orc',
        'bot_class': 'Warrior', 'bot_gender': 'male', 'bot_level': 40,
        'bot_team': 'Horde',
        'victim_guid': 20, 'victim_name': 'Aldric', 'victim_race': 'Human',
        'victim_class': 'Paladin', 'victim_gender': 'male',
        'victim_level': 39, 'victim_team': 'Alliance',
        'zone_id': 17, 'area_id': 380,
    }
    base.update(fields)
    return base


def _death_extra(**fields):
    base = {
        'guild_id': 3, 'guild_name': 'Iron Wolves', 'team': 'Horde',
        'bot_guid': 10, 'bot_name': 'Grom', 'bot_race': 'Orc',
        'bot_class': 'Warrior', 'bot_gender': 'male', 'bot_level': 40,
        'bot_team': 'Horde',
        'killer_guid': 20, 'killer_name': 'Aldric', 'killer_race': 'Human',
        'killer_class': 'Paladin', 'killer_gender': 'male',
        'killer_level': 47, 'killer_team': 'Alliance',
        'zone_id': 17, 'area_id': 380,
    }
    base.update(fields)
    return base


def _text(prompt) -> str:
    return getattr(prompt, 'user_prompt', prompt)


class _Capture:
    def __init__(self):
        self.inserted = []
        self.marked = []
        self.prompts = []
        self.prepared = []

    def prepare(self, db, client, config, participants, prepared=None,
                channel='guild'):
        self.prepared.append((channel, [p['name'] for p in participants]))
        return [dict(p, speaker=dict(p['speaker'])) for p in participants]

    def insert(self, db, **kwargs):
        self.inserted.append(kwargs)
        return len(self.inserted)

    def mark(self, db, event_id, status):
        self.marked.append(status)


def _run(handler, event, capture, config=RP, zone_delay=0.0):
    def single(client, config, prompt, name, *args, **kwargs):
        capture.prompts.append(_text(prompt))
        return [{'name': name, 'message': 'Watch the road north.'}]

    patches = [
        patch.object(pvp, '_query_speaker', return_value=dict(SPEAKER)),
        patch.object(pvp, 'prepare_guild_speakers',
                     side_effect=capture.prepare),
        patch.object(pvp, 'insert_chat_message', side_effect=capture.insert),
        patch.object(common, 'insert_chat_message',
                     side_effect=capture.insert),
        patch.object(pvp, '_mark_event', side_effect=capture.mark),
        patch.object(pvp, 'run_single_prompt', side_effect=single),
        patch.object(common, 'run_single_prompt', side_effect=single),
        patch.object(pvp, 'get_guild_profile', return_value={}),
        patch.object(pvp, '_zone_delivery_delay', return_value=zone_delay),
        patch.object(common, 'calculate_dynamic_delay', return_value=5.0),
    ]
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
                return source[brace:index + 1]
    raise AssertionError(signature)


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

def test_registry_routes_pvp_events():
    for event_type in NEW_EVENTS:
        spec = EVENT_REGISTRY[event_type]
        assert spec.handler_module == 'chatter_guild_pvp_events'
        assert spec.producer == 'LLMChatterGuildPvP.cpp'
        assert spec.priority == 'normal'
        assert callable(getattr(pvp, spec.handler_func))
    assert 'bot_group_pvp_kill' not in EVENT_REGISTRY


# --------------------------------------------------------------------------
# Guild kill and death
# --------------------------------------------------------------------------

def test_guild_kill_goes_to_guild_as_filler():
    capture = _Capture()
    assert _run(pvp.process_guild_pvp_kill_event,
                _event('guild_pvp_kill', _kill_extra()), capture)
    assert capture.marked == ['completed']
    assert len(capture.inserted) == 1
    row = capture.inserted[0]
    assert row['channel'] == 'guild'
    assert row['owner_subsystem'] == 'guild'
    assert row['delivery_policy'] == 'filler'
    prompt = capture.prompts[0]
    assert "Grom has just killed an enemy of the opposing faction" in prompt
    assert ("Grom fights for the Horde; Aldric fights for the Alliance."
            in prompt)
    assert "a shrug or a dry remark" in prompt
    assert "contempt for the enemy" not in prompt


def test_guild_death_is_personality_led():
    capture = _Capture()
    assert _run(pvp.process_guild_pvp_death_event,
                _event('guild_pvp_death', _death_extra()), capture)
    assert capture.inserted[0]['delivery_policy'] == 'filler'
    prompt = capture.prompts[0]
    assert "Anger, grief, a shrug, a dry joke" in prompt
    assert "React the way Grom naturally would" in prompt
    assert "cold and curt" in prompt
    lowered = prompt.lower()
    for phrase in ('full of contempt', 'resentment', 'humiliating'):
        assert phrase not in lowered, phrase
    assert "The killer was far more seasoned than Grom." in prompt
    assert "respawning" in prompt


def test_disabled_guild_events_are_skipped():
    for handler, event_type, key, extra in (
        (pvp.process_guild_pvp_kill_event, 'guild_pvp_kill',
         'LLMChatter.GuildChatter.PvpKill.Enable', _kill_extra()),
        (pvp.process_guild_pvp_death_event, 'guild_pvp_death',
         'LLMChatter.GuildChatter.PvpDeath.Enable', _death_extra()),
        (pvp.process_zone_pvp_death_event, 'zone_pvp_death',
         'LLMChatter.GeneralChat.PvpDeath.Enable', _death_extra()),
    ):
        capture = _Capture()
        config = dict(RP, **{key: '0'})
        assert not _run(handler, _event(event_type, extra), capture, config)
        assert capture.marked == ['skipped']
        assert not capture.inserted and not capture.prompts


# --------------------------------------------------------------------------
# Zone General death
# --------------------------------------------------------------------------

def test_zone_death_uses_general_persona_and_zone_pacing():
    capture = _Capture()
    extra = _death_extra()
    extra.pop('guild_id')
    assert _run(pvp.process_zone_pvp_death_event,
                _event('zone_pvp_death', extra), capture, zone_delay=12.0)
    assert capture.prepared == [('general', ['Grom'])]
    row = capture.inserted[0]
    assert row['channel'] == 'general'
    assert 'owner_subsystem' not in row
    assert row['delay_seconds'] == pvp.ZONE_LINE_DELAY + 12.0
    prompt = capture.prompts[0]
    assert "on General chat" in prompt
    assert "Never insult or mock the Horde" in prompt
    assert "React the way Grom naturally would" in prompt
    assert "full of contempt" not in prompt.lower()


def test_zone_pacing_is_reserved_per_zone():
    calls = []

    def delay(zone_id, config):
        calls.append(zone_id)
        return 0.0

    capture = _Capture()
    extra = _death_extra(zone_id=331)
    with patch.object(pvp, '_zone_delivery_delay', side_effect=delay):
        def single(client, config, prompt, name, *args, **kwargs):
            return [{'name': name, 'message': 'Careful out there.'}]
        with patch.object(pvp, '_query_speaker',
                          return_value=dict(SPEAKER)), \
                patch.object(pvp, 'prepare_guild_speakers',
                             side_effect=capture.prepare), \
                patch.object(pvp, 'insert_chat_message',
                             side_effect=capture.insert), \
                patch.object(pvp, '_mark_event', side_effect=capture.mark), \
                patch.object(pvp, 'run_single_prompt', side_effect=single):
            assert pvp.process_zone_pvp_death_event(
                None, None, RP, _event('zone_pvp_death', extra))
    assert calls == [331]


# --------------------------------------------------------------------------
# Battleground kill context
# --------------------------------------------------------------------------

def test_bg_kill_names_race_and_factions_without_massive_battle():
    extra = {
        'victim_name': 'Aldric', 'victim_class': 2,
        'victim_race': 'Human', 'victim_gender': 'male',
        'victim_level': 70, 'killer_name': 'Grom',
        'killer_team': 'Horde', 'victim_team': 'Alliance',
        'killer_is_real_player': False, 'team': 'Horde',
        'bg_type_id': 2,
    }
    prompt = _text(build_bg_pvp_kill_prompt(
        extra, {'bot_name': 'Thrall', 'race': 'Orc', 'class': 'Shaman'},
    ))
    assert "The fallen enemy was a male Human." in prompt
    assert ("You and your side fight for the Horde; Aldric fights for the "
            "Alliance.") in prompt
    assert "massive" not in prompt.lower()

    old = {key: value for key, value in extra.items()
           if key not in ('victim_race', 'victim_gender', 'killer_team',
                          'victim_team')}
    prompt = _text(build_bg_pvp_kill_prompt(
        old, {'bot_name': 'Thrall', 'race': 'Orc', 'class': 'Shaman'},
    ))
    assert "The fallen enemy was" not in prompt
    assert "fights for the Alliance" not in prompt


# --------------------------------------------------------------------------
# C++ wiring
# --------------------------------------------------------------------------

def test_cpp_queues_only_readable_and_quiet_guild_posts():
    source = _src('LLMChatterGuildPvP.cpp')
    kill = _function_body(source, 'void QueueGuildPvpKill(')
    death = _function_body(source, 'void QueuePvpDeathComplaint(')
    assert 'GuildConversationActive(guildId)' in kill
    assert 'PickRealGuildMember(guildId)' in kill
    assert 'IsGroupedWithRealPlayer(killer)' in kill
    assert '!GuildConversationActive(guildId)' in death
    assert 'PickRealGuildMember(guildId)' in death
    assert 'PickRealPlayerInZone(zoneId, team)' in death
    assert 'CanSpeakInGeneralChannel(killed)' in death
    assert 'sPvpCooldownMutex' in kill and 'sPvpCooldownMutex' in death

    handler = _function_body(source, 'void HandleOpenWorldPvpKill(')
    assert 'InBattleground()' in handler and 'InArena()' in handler
    assert 'QueueGroupPvpKill' not in source
    for name in ('LLMChatterGuildPvP.cpp', 'LLMChatterPlayer.cpp',
                 'LLMChatterShared.cpp', 'LLMChatterConfig.cpp',
                 'LLMChatterConfig.h'):
        text = _src(name)
        assert 'bot_group_pvp_kill' not in text, name
        assert 'massive' not in text.lower(), name
        assert 'BattlegroundChance' not in text, name


def test_cpp_pvp_kill_hook_keeps_bg_reaction_chance():
    source = _src('LLMChatterPlayer.cpp')
    body = _function_body(source, 'void OnPlayerPVPKill(')
    open_world = body.index('HandleOpenWorldPvpKill(killer, killed)')
    bg_gate = body.index('_bgChatterEnable')
    assert open_world < bg_gate
    assert '_eventReactionChance' in body
    for field in ('victim_race', 'victim_gender', 'victim_level',
                  'killer_team', 'victim_team'):
        assert f'\\"{field}\\"' in body, field
    assert '#include "LLMChatterGuildPvP.h"' in source


def test_cpp_priorities_and_delivery_gate():
    shared = _src('LLMChatterShared.cpp')
    match = re.search(
        r'std::array<EventPriorityRule, (\d+)>\s+kTierPriorityRules = '
        r'\{\{(.*?)\}\};', shared, re.S)
    assert match
    entries = re.findall(r'\{"([a-z_]+)",', match.group(2))
    assert int(match.group(1)) == len(entries)
    for event_type in NEW_EVENTS:
        assert f'{{"{event_type}",' in match.group(2)
        line = next(line for line in match.group(2).splitlines()
                    if f'"{event_type}"' in line)
        assert 'PRIORITY_NORMAL' in line

    delivery = _src('LLMChatterDelivery.cpp')
    assert 'deliveryPolicy == "filler"' in delivery
    assert '"guild_conversation_active"' in delivery
    gate = delivery[delivery.index('deliveryPolicy == "filler"'):][:300]
    assert 'WasGuildPlayerConversationRecent(' in gate

    active = _function_body(
        _src('LLMChatterGuildPvP.cpp'), 'bool GuildConversationActive(')
    assert 'WasGuildPlayerConversationRecent(' in active
    record = _function_body(
        _src('LLMChatterGuild.cpp'), 'void RecordDeliveredGuildLine(')
    assert ('if (eventType == "guild_player_message")\n'
            '            NoteGuildPlayerConversation(guildId);') in record


# --------------------------------------------------------------------------
# SQL and conf
# --------------------------------------------------------------------------

def test_sql_adds_event_types_additively():
    base = (MODULE_DIR / 'data/sql/characters/base/'
            '00000000_llm_chatter_tables.sql').read_text(encoding='utf-8')
    enum = base[base.index('`event_type` ENUM('):]
    enum = enum[:enum.index(') NOT NULL')]
    update = (MODULE_DIR / 'data/sql/characters/updates/'
              '20261002_guild_pvp_events.sql').read_text(encoding='utf-8')
    for event_type in NEW_EVENTS:
        assert f"'{event_type}'" in enum
        assert f"LIKE '%''{event_type}''%'" in update
    assert 'information_schema.COLUMNS' in update
    assert 'MODIFY COLUMN `event_type` ' in update
    assert "LEFT(@event_type, CHAR_LENGTH(@event_type) - 1)" in update
    readme = (MODULE_DIR / 'README.md').read_text(encoding='utf-8')
    assert readme.count('20261002_guild_pvp_events.sql') == 2


def test_conf_keys_are_documented_and_loaded():
    keys = {
        'LLMChatter.GuildChatter.PvpKill.Enable': ('1', '1'),
        'LLMChatter.GuildChatter.PvpKill.Chance': ('25', '15'),
        'LLMChatter.GuildChatter.PvpKill.Cooldown': ('300', '300'),
        'LLMChatter.GuildChatter.PvpDeath.Enable': ('1', '1'),
        'LLMChatter.GuildChatter.PvpDeath.Chance': ('30', '20'),
        'LLMChatter.GuildChatter.PvpDeath.GuildCooldown': ('600', '1200'),
        'LLMChatter.GeneralChat.PvpDeath.Enable': ('1', '1'),
        'LLMChatter.GeneralChat.PvpDeath.Chance': ('15', '10'),
        'LLMChatter.GeneralChat.PvpDeath.ZoneCooldown': ('600', '1200'),
        'LLMChatter.PvpDeath.VictimCooldown': ('1800', '2700'),
    }
    main = (MODULE_DIR / 'conf/mod_llm_chatter.conf.dist').read_text(
        encoding='utf-8')
    quieter = (MODULE_DIR / 'conf/presets/'
               'mod_ll_chatter_quieter.conf.dist').read_text(
        encoding='utf-8')
    loads = _src('LLMChatterConfig.cpp')
    for key, (default, quiet) in keys.items():
        assert re.search(rf'^{re.escape(key)} = {default}$', main, re.M), key
        assert re.search(rf'^{re.escape(key)} = {quiet}$', quieter,
                         re.M), key
        short = key[len('LLMChatter.'):]
        assert f'"LLMChatter.{short}"' in loads, key
    for text in (main, quieter):
        assert 'GroupChatter.PvpKill' not in text
        assert 'contempt, resentment' not in text


def main() -> int:
    test_registry_routes_pvp_events()
    test_guild_kill_goes_to_guild_as_filler()
    test_guild_death_is_personality_led()
    test_disabled_guild_events_are_skipped()
    test_zone_death_uses_general_persona_and_zone_pacing()
    test_zone_pacing_is_reserved_per_zone()
    test_bg_kill_names_race_and_factions_without_massive_battle()
    test_cpp_queues_only_readable_and_quiet_guild_posts()
    test_cpp_pvp_kill_hook_keeps_bg_reaction_chance()
    test_cpp_priorities_and_delivery_gate()
    test_sql_adds_event_types_additively()
    test_conf_keys_are_documented_and_loaded()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
