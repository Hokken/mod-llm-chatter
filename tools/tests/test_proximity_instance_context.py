#!/usr/bin/env python3
"""Focused regression checks for instance proximity chatter."""

import importlib
import json
import sys
import types
from pathlib import Path


def _ensure_module(name):
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


for dependency in ('anthropic', 'openai'):
    try:
        importlib.import_module(dependency)
    except ModuleNotFoundError:
        module = _ensure_module(dependency)
        attribute = (
            'Anthropic' if dependency == 'anthropic'
            else 'OpenAI'
        )
        setattr(module, attribute, type(attribute, (), {}))

try:
    importlib.import_module('mysql.connector')
except ModuleNotFoundError:
    mysql_module = _ensure_module('mysql')
    connector_module = _ensure_module('mysql.connector')
    setattr(mysql_module, 'connector', connector_module)

TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from chatter_instance_context import (  # noqa: E402
    build_instance_context,
    build_location_prompt_lines,
)
import chatter_boss_dialogue  # noqa: E402
from chatter_boss_dialogue import (  # noqa: E402
    _build_prompt as build_boss_prompt,
)
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402
from chatter_proximity import (  # noqa: E402
    _conversation_prompt,
    _fetch_proximity_history,
    _player_say_conversation_prompt,
    _player_say_single_prompt,
    _single_prompt,
)


NORMAL_CONFIG = {'LLMChatter.ChatterMode': 'normal'}
NPC = {
    'name': 'Deathstalker Adamant',
    'is_npc': True,
    'npc_entry': 3849,
    'npc_spawn_id': 9001,
    'role': 'Guard',
    'sub_name': 'Imprisoned scout',
    'disposition': 'unfriendly',
    'rank': 'elite',
}
BOT = {
    'name': 'Aliss',
    'is_npc': False,
    'bot_guid': 77,
    'race': 'Human',
    'class': 'Mage',
    'level': 30,
    'gender': 'female',
}
INSTANCE_EXTRA = {
    'player_guid': 42,
    'player_name': 'Calwen',
    'zone_id': 209,
    'zone_name': 'Shadowfang Keep',
    'subzone_name': 'The Courtyard',
    'map_id': 33,
    'instance_id': 12,
    'map_name': 'Shadowfang Keep',
    'is_dungeon': True,
    'is_raid': False,
    'participants': [NPC],
    'nearby_names': [],
    'max_lines': 2,
}
BOSS_EXTRA = {
    **INSTANCE_EXTRA,
    'trigger': 'proximity_boss_player_say',
    'encounter_state': 'pre_aggro',
    'player_message': 'Baron, your keep is falling.',
    'distance': 55,
    'aggro_distance': 35,
    'safety_margin': 10,
    'safe_distance': 45,
    'boss': {
        'name': 'Baron Silverlaine',
        'entry': 3887,
        'spawn_id': 9010,
        'role': 'Undead noble',
        'sub_name': 'Master of the Keep',
        'disposition': 'hostile',
        'rank': 'boss',
    },
}


class _Cursor:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows = list(self.rows)
        self.rows.clear()
        return rows


class _DB:
    def __init__(self, rows=None):
        self.cursor_value = _Cursor(rows)

    def cursor(self, *args, **kwargs):
        return self.cursor_value

    def commit(self):
        return None


def test_known_instance_uses_canonical_name_and_existing_lore():
    context = build_instance_context(INSTANCE_EXTRA)
    assert context['instance_name'] == 'Shadowfang Keep'
    assert context['current_area'] == 'The Courtyard'
    assert 'haunted fortress' in context['instance_flavor'].lower()

    text = '\n'.join(build_location_prompt_lines(INSTANCE_EXTRA))
    assert 'Instance: Shadowfang Keep' in text
    assert 'Current area: The Courtyard' in text
    assert 'grounding only; do not recite' in text


def test_custom_instance_uses_map_name_without_invented_lore():
    extra = {
        'map_id': 99999,
        'instance_id': 8,
        'map_name': 'The Test Vault',
        'zone_name': 'Fallback Zone',
        'is_dungeon': True,
    }
    context = build_instance_context(extra)
    assert context['instance_name'] == 'The Test Vault'
    assert context['instance_flavor'] == ''
    text = '\n'.join(build_location_prompt_lines(extra))
    assert 'Instance: The Test Vault' in text
    assert 'Instance context:' not in text


def test_outdoor_context_retains_zone_and_subzone():
    text = '\n'.join(build_location_prompt_lines({
        'map_id': 0,
        'zone_name': 'Elwynn Forest',
        'subzone_name': 'Goldshire',
    }))
    assert text == 'Zone: Elwynn Forest\nSubzone: Goldshire'


def test_all_proximity_prompt_shapes_receive_instance_context():
    db = _DB()
    prompts = [
        _single_prompt(
            db, INSTANCE_EXTRA, NPC, 'local concern',
            config=NORMAL_CONFIG,
        ).user_prompt,
        _conversation_prompt(
            db,
            {**INSTANCE_EXTRA, 'participants': [NPC, BOT]},
            [NPC, BOT],
            config=NORMAL_CONFIG,
        ).user_prompt,
        _player_say_single_prompt(
            db, INSTANCE_EXTRA, NPC, 'hello', [],
            NORMAL_CONFIG,
        ).user_prompt,
        _player_say_conversation_prompt(
            db,
            {**INSTANCE_EXTRA, 'participants': [NPC, BOT]},
            [NPC, BOT], 'hello', [], NORMAL_CONFIG,
        ).user_prompt,
    ]
    for prompt in prompts:
        assert 'Instance: Shadowfang Keep' in prompt
        assert 'haunted fortress' in prompt.lower()


def test_normal_playerbot_treats_lore_as_game_knowledge():
    prompt = _single_prompt(
        _DB(), INSTANCE_EXTRA, BOT, 'route choice',
        config=NORMAL_CONFIG,
    ).user_prompt
    assert 'CHAT MODE: NORMAL' in prompt
    assert 'treat the instance context as game knowledge' in prompt
    assert 'must not claim to physically sense its lore' in prompt


def test_npc_disposition_and_rank_reach_prompt():
    prompt = _single_prompt(
        _DB(), INSTANCE_EXTRA, NPC, 'local concern',
        config=NORMAL_CONFIG,
    ).user_prompt
    assert 'disposition: unfriendly' in prompt
    assert 'rank: elite' in prompt
    assert 'unfriendly rather than openly hostile' in prompt


def test_boss_prompt_is_grounded_directed_and_action_free():
    prompt = build_boss_prompt(BOSS_EXTRA).user_prompt
    assert 'Baron Silverlaine' in prompt
    assert 'Instance: Shadowfang Keep' in prompt
    assert 'haunted fortress' in prompt.lower()
    assert 'your keep is falling' in prompt
    assert 'respond to their meaning' in prompt.lower()
    assert 'never reproduce or paraphrase known scripted' in prompt.lower()
    assert 'do not narrate an attack' in prompt.lower()


def test_boss_events_have_separate_registry_ownership():
    approach = EVENT_REGISTRY['proximity_boss_approach']
    directed = EVENT_REGISTRY['proximity_boss_player_say']
    assert approach.handler_module == 'chatter_boss_dialogue'
    assert directed.handler_module == 'chatter_boss_dialogue'
    assert directed.priority == 'high'


def test_boss_handler_fails_closed_without_safety_metadata():
    event = {
        'id': 501,
        'event_type': 'proximity_boss_approach',
        'extra_data': json.dumps({
            key: value for key, value in BOSS_EXTRA.items()
            if key != 'safe_distance'
        }),
    }
    called = []
    original_call = chatter_boss_dialogue.call_llm
    chatter_boss_dialogue.call_llm = (
        lambda *args, **kwargs: called.append(True)
    )
    try:
        assert not chatter_boss_dialogue.handle_boss_dialogue(
            _DB(), object(), {}, event
        )
    finally:
        chatter_boss_dialogue.call_llm = original_call
    assert not called


def test_boss_handler_queues_monster_yell_with_separate_owner():
    event = {
        'id': 502,
        'event_type': 'proximity_boss_player_say',
        'extra_data': json.dumps(BOSS_EXTRA),
    }
    inserted = []
    original_call = chatter_boss_dialogue.call_llm
    original_insert = chatter_boss_dialogue.insert_chat_message
    chatter_boss_dialogue.call_llm = (
        lambda *args, **kwargs: '{"message":"Your confidence amuses me."}'
    )
    chatter_boss_dialogue.insert_chat_message = (
        lambda *args, **kwargs: inserted.append(kwargs)
    )
    try:
        assert chatter_boss_dialogue.handle_boss_dialogue(
            _DB(), object(), {}, event
        )
    finally:
        chatter_boss_dialogue.call_llm = original_call
        chatter_boss_dialogue.insert_chat_message = original_insert
    assert inserted[0]['channel'] == 'myell'
    assert inserted[0]['owner_subsystem'] == 'boss_dialogue'
    assert inserted[0]['npc_spawn_id'] == 9010


def test_history_is_scoped_by_zone_map_and_instance():
    rows = [
        {
            'bot_name': 'WrongCopy',
            'message': 'not this one',
            'extra_data': '{"instance_id":13}',
        },
        {
            'bot_name': 'RightCopy',
            'message': 'this one',
            'extra_data': '{"instance_id":12}',
        },
    ]
    db = _DB(rows)
    history = _fetch_proximity_history(
        db, 42, 209, 33, 12
    )
    query, params = db.cursor_value.queries[0]
    assert 'e.zone_id = %s' in query
    assert 'e.map_id = %s' in query
    assert params[:3] == (209, 33, 42)
    assert history == [{
        'name': 'RightCopy',
        'message': 'this one',
    }]


def test_history_accepts_eastern_kingdoms_map_zero():
    db = _DB([{
        'bot_name': 'Marshal Dughan',
        'message': 'Keep your eyes open.',
        'extra_data': '{"instance_id":0}',
    }])
    history = _fetch_proximity_history(
        db, 42, 12, 0, 0
    )
    assert history == [{
        'name': 'Marshal Dughan',
        'message': 'Keep your eyes open.',
    }]
    assert db.cursor_value.queries[0][1][:2] == (12, 0)


def test_cpp_source_contracts_cover_instance_safety():
    source = (
        MODULE_DIR / 'src' / 'LLMChatterProximity.cpp'
    ).read_text(encoding='utf-8')
    header = (
        MODULE_DIR / 'src' / 'LLMChatterConfig.h'
    ).read_text(encoding='utf-8')
    shared = (
        MODULE_DIR / 'src' / 'LLMChatterShared.cpp'
    ).read_text(encoding='utf-8')
    boss = (
        MODULE_DIR / 'src' / 'LLMChatterBossDialogue.cpp'
    ).read_text(encoding='utf-8')
    delivery = (
        MODULE_DIR / 'src' / 'LLMChatterDelivery.cpp'
    ).read_text(encoding='utf-8')
    config = (
        MODULE_DIR / 'src' / 'LLMChatterConfig.cpp'
    ).read_text(encoding='utf-8')
    group_combat = (
        MODULE_DIR / 'src' / 'LLMChatterGroupCombat.cpp'
    ).read_text(encoding='utf-8')
    world = (
        MODULE_DIR / 'src' / 'LLMChatterWorld.cpp'
    ).read_text(encoding='utf-8')

    assert 'player->IsAlive()' in source
    assert 'map->IsBattlegroundOrArena()' in source
    assert 'player->IsWithinLOSInMap(cr)' in source
    assert 'player->IsWithinLOSInMap(bot)' in source
    assert 'uint32 instanceId = 0;' in source
    assert 'scene.instanceId != instanceId' in source
    assert 'IsLLMChatterBoss(creature)' in source
    assert 'IsProximitySpeakerAllowed(entry)' in source
    assert 'IsProximitySpeakerDenied(entry)' in source
    assert '_proxChatterEnableInDungeons' in header
    assert '_proxChatterEnableInRaids' in header
    assert 'bool IsLLMChatterBoss' in shared
    assert 'GetAggroRange(player)' in boss
    assert '_proxBossAggroSafetyMargin' in boss
    assert 'IsBossDialogueEntryDenied' in boss
    assert 'creature->IsHostileTo(player)' in boss
    assert 'TryReserveBossDialogue' in boss
    assert '_bossDialogueStateMutex' in boss
    assert 'TryBeginBossPlayerScan' in boss
    assert 'TryBeginBossDirectedScan' in boss
    assert 'return messageNamesSelectedBoss;' in boss
    assert 'ambiguousFirstToken = true' in boss
    assert 'ContainsCreatureEntry(' in config
    assert '_proxBossSpeakerDenyEntries, creatureEntry' in config
    assert '_proxBossSpeakerDenyEntries.store(' in config
    enter_combat = group_combat.split(
        'void HandleGroupPlayerEnterCombatImpl(', 1
    )[1].split('\nvoid ', 1)[0]
    assert 'IsLLMChatterBoss(creature)' not in enter_combat
    assert 'CREATURE_TYPE_FLAG_BOSS_MOB' in enter_combat
    assert '_lastBossDialogueCheckTime' in world
    assert 'CheckBossProximityDialogue();' in world

    reservation = boss.split(
        'bool TryReserveBossDialogue(', 1
    )[1].split('} // namespace', 1)[0]
    persisted = reservation.index(
        'IsPersistedEventOnCooldown('
    )
    assert reservation.index(
        'std::lock_guard<std::mutex>'
    ) < persisted
    assert persisted < reservation.rindex(
        'std::lock_guard<std::mutex>'
    )
    assert 'GetBossAggroDistance' in boss
    assert 'ownerSubsystem == "boss_dialogue"' in delivery
    assert 'channel == "myell"' in delivery

    directed = source.index(
        'QueueDirectedPlayerSayProximityEvent('
    )
    active_scene = source.index(
        'ProximityScene* scene = FindBestScene(player);'
    )
    assert directed < active_scene


def test_boss_event_types_are_persistable():
    base = (
        MODULE_DIR / 'data' / 'sql' / 'characters' / 'base'
        / '00000000_llm_chatter_tables.sql'
    ).read_text(encoding='utf-8')
    migration = (
        MODULE_DIR / 'data' / 'sql' / 'characters' / 'updates'
        / '20260908_instance_proximity_boss_events.sql'
    ).read_text(encoding='utf-8')
    for event_type in (
        'proximity_boss_approach',
        'proximity_boss_player_say',
    ):
        assert event_type in base
        assert event_type in migration


def test_config_fallbacks_match_distributed_values():
    source = (
        MODULE_DIR / 'src' / 'LLMChatterConfig.cpp'
    ).read_text(encoding='utf-8')
    assert '"ScanRadius", 40)' in source
    assert '"Chance", 30)' in source
    assert '"EntityCooldown", 60)' in source
    assert '"ConversationLineDelay", 2)' in source
    assert '"MaxTokensPerLine", 120)' in source
    assert '"EnableBossDialogue", false)' in source
    assert '"BossApproachMaxRadius", 80)' in source
    assert '"BossAggroSafetyMargin", 10)' in source
    assert '"BossDirectedScanCooldownSeconds", 1)' in source


def main():
    tests = [
        value for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f'{len(tests)} instance-proximity tests passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
