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


for dependency in ('openai',):
    try:
        importlib.import_module(dependency)
    except ModuleNotFoundError:
        module = _ensure_module(dependency)
        attribute = 'OpenAI'
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
import chatter_proximity  # noqa: E402
from chatter_db import insert_chat_message  # noqa: E402
from chatter_boss_dialogue import (  # noqa: E402
    _build_prompt as build_boss_prompt,
    _fetch_previous_boss_lines,
)
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402
from chatter_shared import parse_conversation_response  # noqa: E402
from chatter_proximity import (  # noqa: E402
    _conversation_prompt,
    _fetch_proximity_history,
    _player_emote_conversation_prompt,
    _player_emote_single_prompt,
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
    'presence_id': 1725796800,
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
        _player_emote_single_prompt(
            db, INSTANCE_EXTRA, NPC, 'wave', NORMAL_CONFIG,
        ).user_prompt,
        _player_emote_conversation_prompt(
            db,
            {
                **INSTANCE_EXTRA,
                'participants': [NPC, {**NPC, 'name': 'Thar'}],
                'addressed_name': NPC['name'],
                'player_emote': 'wave',
                'interaction_mode': 'npc_aside',
            },
            [NPC, {**NPC, 'name': 'Thar'}],
            'wave',
            NORMAL_CONFIG,
        ).user_prompt,
    ]
    for prompt in prompts:
        assert 'Instance: Shadowfang Keep' in prompt
        assert 'haunted fortress' in prompt.lower()


def test_directed_emote_registry_and_player_agency_contract():
    spec = EVENT_REGISTRY['proximity_player_emote']
    assert spec.handler_module == 'chatter_proximity'
    assert spec.handler_func == 'handle_proximity_player_emote'
    assert spec.priority == 'high'
    assert spec.payload_fields['player_emote'] == (str, True)
    assert spec.payload_fields['mirror_emote'] == (str, False)
    assert spec.payload_fields['participants'] == (list, True)

    participants = [NPC, {**NPC, 'name': 'Thar'}]
    aside = _player_emote_conversation_prompt(
        _DB(),
        {
            **INSTANCE_EXTRA,
            'participants': participants,
            'addressed_name': NPC['name'],
            'interaction_mode': 'npc_aside',
        },
        participants,
        'wave',
        NORMAL_CONFIG,
    ).user_prompt
    assert 'FIRST message MUST be spoken by Deathstalker Adamant' in aside
    assert "discuss the player's real action" in aside
    assert 'Do not address the player' in aside
    assert 'address only each other' in aside
    assert 'Never invent dialogue, thoughts, or actions' in aside

    mirrored = _player_emote_single_prompt(
        _DB(),
        {
            **INSTANCE_EXTRA,
            'mirror_emote': 'wave',
        },
        NPC,
        'wave',
        NORMAL_CONFIG,
    ).user_prompt
    assert 'also scheduled to perform /wave' in mirrored
    assert 'must not contradict that animation' in mirrored


def test_all_player_proximity_replies_use_responsive_timing():
    assert EVENT_REGISTRY['proximity_reply'].priority == 'high'
    assert EVENT_REGISTRY['proximity_player_say'].priority == 'high'
    assert (
        EVENT_REGISTRY['proximity_player_conversation'].priority
        == 'high'
    )
    assert EVENT_REGISTRY['proximity_player_emote'].priority == 'high'

    source = (
        MODULE_DIR / 'src' / 'LLMChatterProximity.cpp'
    ).read_text(encoding='utf-8')
    active_reply = source.split(
        'void HandleProximityPlayerSay(', 1
    )[1].split('void HandleProximityPlayerEmote(', 1)[0]
    assert '"proximity_reply"' in active_reply
    assert '->_proxDirectedExpirySeconds' in active_reply

    shared = (
        MODULE_DIR / 'src' / 'LLMChatterShared.cpp'
    ).read_text(encoding='utf-8')
    assert '{"proximity_reply",         PRIORITY_HIGH}' in shared
    assert '{"proximity_reply",         2}' in shared
    assert '{"proximity_reply", 1}' in shared


def test_directed_parser_accepts_only_exact_or_unique_name_tokens():
    names = ['Mountaineer Rharen', 'Mountaineer Thar']
    shortened = parse_conversation_response(
        '[{"speaker":"Rharen","message":"Aye."}]',
        names,
        unique_tokens_only=True,
    )
    assert shortened[0]['name'] == 'Mountaineer Rharen'

    ambiguous = parse_conversation_response(
        '[{"speaker":"Mountaineer","message":"Aye."}]',
        names,
        unique_tokens_only=True,
    )
    assert ambiguous == []

    typo = parse_conversation_response(
        '[{"speaker":"Rharex","message":"Aye."}]',
        names,
        unique_tokens_only=True,
    )
    assert typo == []

    addressed = parse_conversation_response(
        '[{"speaker":"Rharen","message":"Aye.",'
        '"addressee":"Calwen"}]',
        names,
        unique_tokens_only=True,
        addressee_names=['Calwen', *names],
    )
    assert addressed[0]['addressee'] == 'Calwen'


def test_directed_addressee_never_falls_back_to_speaker():
    rharen = {
        **NPC,
        'name': 'Mountaineer Rharen',
        'npc_spawn_id': 101,
    }
    thar = {
        **NPC,
        'name': 'Mountaineer Thar',
        'npc_spawn_id': 102,
    }
    line = {
        'name': rharen['name'],
        'addressee': rharen['name'],
    }
    chatter_proximity._set_line_addressee(
        line,
        {
            **INSTANCE_EXTRA,
            'interaction_mode': 'npc_aside',
        },
        [rharen, thar],
        rharen['name'],
    )
    assert line['_addressee_npc_spawn_id'] == 102


def test_scripted_emote_ownership_matches_core_semantics():
    emote_source = (
        MODULE_DIR / 'src' / 'LLMChatterGroupEmote.cpp'
    ).read_text(encoding='utf-8')
    world_source = (
        MODULE_DIR / 'src' / 'LLMChatterWorld.cpp'
    ).read_text(encoding='utf-8')
    assert "ss.event_type = 22" in emote_source
    assert "direct_ct.AIName = 'SmartAI'" in emote_source
    assert "spawn_ct.AIName = 'SmartAI'" in emote_source
    assert 'ss.entryorguid < 0' in emote_source
    assert 'textEmote == 0' in emote_source
    assert 'IsCreatureEmoteScripted(creature, textEmote)' in emote_source
    assert '_emoteCooldownMutex' in emote_source
    assert 'TryStampEmoteCooldown(' in emote_source
    assert 'GetCreatureEntryColumn()' in emote_source
    assert 'LoadScriptedEmoteExclusions();' in world_source


def test_delivery_records_drops_and_explicit_addressees():
    delivery_source = (
        MODULE_DIR / 'src' / 'LLMChatterDelivery.cpp'
    ).read_text(encoding='utf-8')
    schema = (
        MODULE_DIR / 'data' / 'sql' / 'characters' / 'base'
        / '00000000_llm_chatter_tables.sql'
    ).read_text(encoding='utf-8')
    migration = (
        MODULE_DIR / 'data' / 'sql' / 'characters' / 'updates'
        / '20260914_npc_multidirectional_interactions.sql'
    ).read_text(encoding='utf-8')
    assert 'FinalizeDroppedMessage(' in delivery_source
    assert 'cancelled_after_directed_drop' in delivery_source
    assert 'drop_reason = NULL' in delivery_source
    assert 'm.addressee_player_guid' in delivery_source
    assert 'm.addressee_npc_spawn_id' in delivery_source
    assert '`drop_reason` VARCHAR(64)' in schema
    assert '`addressee_player_guid` INT UNSIGNED' in schema
    assert '`addressee_npc_spawn_id` INT UNSIGNED' in schema
    assert 'ADD COLUMN IF NOT EXISTS' not in migration
    assert '@has_addressee_player_guid' in migration
    assert '@has_addressee_bot_guid' in migration
    assert '@has_addressee_npc_spawn_id' in migration


def test_directed_emote_handler_persists_addressee_ids():
    rharen = {
        **NPC,
        'name': 'Mountaineer Rharen',
        'npc_spawn_id': 101,
    }
    thar = {
        **NPC,
        'name': 'Mountaineer Thar',
        'npc_spawn_id': 102,
    }
    extra = {
        **INSTANCE_EXTRA,
        'participants': [rharen, thar],
        'addressed_name': rharen['name'],
        'player_emote': 'wave',
        'interaction_mode': 'npc_aside',
        'max_lines': 2,
    }
    event = {'id': 77, 'extra_data': json.dumps(extra)}
    captured = []
    original_call = chatter_proximity.call_llm
    original_insert = chatter_proximity.insert_chat_message
    try:
        chatter_proximity.call_llm = lambda *args, **kwargs: json.dumps([
            {
                'speaker': 'Rharen',
                'message': 'That was unexpectedly friendly.',
                'addressee': 'Calwen',
            },
            {
                'speaker': 'Thar',
                'message': 'Perhaps they need directions.',
                'addressee': 'Rharen',
            },
        ])
        chatter_proximity.insert_chat_message = (
            lambda db, **kwargs: captured.append(kwargs)
        )
        assert chatter_proximity.handle_proximity_player_emote(
            _DB(), None, NORMAL_CONFIG, event
        )
    finally:
        chatter_proximity.call_llm = original_call
        chatter_proximity.insert_chat_message = original_insert

    assert len(captured) == 2
    assert captured[0]['npc_spawn_id'] == 101
    assert captured[0]['addressee_npc_spawn_id'] == 102
    assert captured[1]['npc_spawn_id'] == 102
    assert captured[1]['addressee_npc_spawn_id'] == 101


def test_message_insert_addressee_parameters_match_placeholders():
    db = _DB()
    insert_chat_message(
        db,
        event_id=77,
        bot_guid=0,
        bot_name='Mountaineer Rharen',
        message='Aye.',
        channel='msay',
        npc_spawn_id=101,
        player_guid=42,
        addressee_npc_spawn_id=102,
    )
    query, params = db.cursor_value.queries[0]
    assert query.count('%s') == len(params) == 18
    assert params[-3:] == (None, None, 102)


def test_directed_validation_uses_only_insertable_lines():
    rharen = {
        **NPC,
        'name': 'Mountaineer Rharen',
        'npc_spawn_id': 101,
    }
    thar = {
        **NPC,
        'name': 'Mountaineer Thar',
        'npc_spawn_id': 102,
    }
    extra = {
        **INSTANCE_EXTRA,
        'participants': [rharen, thar],
        'addressed_name': rharen['name'],
        'player_message': 'How fares the road?',
        'interaction_mode': 'player_inclusive',
        'max_lines': 2,
    }
    responses = iter([
        json.dumps([
            {'speaker': 'Rharen', 'message': 'Long enough.'},
            {'speaker': 'Rharen', 'message': 'Still raining.'},
            {'speaker': 'Thar', 'message': 'Aye.'},
        ]),
        json.dumps({'message': 'The road is passable.'}),
    ])
    captured = []
    original_call = chatter_proximity.call_llm
    original_insert = chatter_proximity.insert_chat_message
    try:
        chatter_proximity.call_llm = (
            lambda *args, **kwargs: next(responses)
        )
        chatter_proximity.insert_chat_message = (
            lambda db, **kwargs: captured.append(kwargs)
        )
        assert chatter_proximity.handle_proximity_player_conversation(
            _DB(), None, NORMAL_CONFIG,
            {'id': 78, 'extra_data': json.dumps(extra)},
        )
    finally:
        chatter_proximity.call_llm = original_call
        chatter_proximity.insert_chat_message = original_insert

    assert len(captured) == 1
    assert captured[0]['npc_spawn_id'] == 101


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


def test_repeat_boss_prompt_continues_without_repeating():
    prompt = build_boss_prompt({
        **BOSS_EXTRA,
        'trigger': 'proximity_boss_approach',
        'player_message': '',
        'automatic_line_number': 2,
        'previous_boss_lines': [
            'You have wandered far from the surface.',
        ],
    }).user_prompt
    assert 'automatic line 2' in prompt
    assert 'later observation, not another introduction' in prompt
    assert 'You have wandered far from the surface.' in prompt
    assert 'Do not repeat, paraphrase, or contradict' in prompt


def test_boss_events_have_separate_registry_ownership():
    approach = EVENT_REGISTRY['proximity_boss_approach']
    directed = EVENT_REGISTRY['proximity_boss_player_say']
    assert approach.handler_module == 'chatter_boss_dialogue'
    assert directed.handler_module == 'chatter_boss_dialogue'
    assert directed.priority == 'high'
    assert 'automatic_line_number' in approach.payload_fields
    assert 'automatic_line_number' not in directed.payload_fields
    assert 'presence_id' in approach.payload_fields
    assert 'presence_id' in directed.payload_fields


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
            'event_id': 2,
            'extra_data': (
                '{"instance_id":13,"addressed_name":"RightCopy"}'
            ),
        },
        {
            'bot_name': 'RightCopy',
            'message': 'this one',
            'event_id': 1,
            'extra_data': (
                '{"instance_id":12,"addressed_name":"RightCopy",'
                '"player_name":"Calwen",'
                '"player_message":"How are you?"}'
            ),
        },
    ]
    db = _DB(rows)
    history = _fetch_proximity_history(
        db, 42, 209, 33, 12, 'RightCopy'
    )
    query, params = db.cursor_value.queries[0]
    assert 'e.zone_id = %s' in query
    assert 'e.map_id = %s' in query
    assert 'm.drop_reason IS NULL' in query
    assert params[:3] == (209, 33, 42)
    assert history == [
        {'name': 'Calwen', 'message': 'How are you?'},
        {'name': 'RightCopy', 'message': 'this one'},
    ]


def test_history_accepts_eastern_kingdoms_map_zero():
    db = _DB([{
        'bot_name': 'Marshal Dughan',
        'message': 'Keep your eyes open.',
        'event_id': 1,
        'extra_data': (
            '{"instance_id":0,'
            '"addressed_name":"Marshal Dughan"}'
        ),
    }])
    history = _fetch_proximity_history(
        db, 42, 12, 0, 0, 'Marshal Dughan'
    )
    assert history == [{
        'name': 'Marshal Dughan',
        'message': 'Keep your eyes open.',
    }]
    assert db.cursor_value.queries[0][1][:2] == (12, 0)


def test_history_uses_addressed_spawn_not_duplicate_name():
    db = _DB([
        {
            'bot_name': 'Mountaineer Rharen',
            'message': 'Wrong Rharen.',
            'event_id': 2,
            'extra_data': json.dumps({
                'instance_id': 0,
                'addressed_name': 'Mountaineer Rharen',
                'participants': [{
                    'name': 'Mountaineer Rharen',
                    'is_npc': True,
                    'npc_spawn_id': 202,
                }],
            }),
        },
        {
            'bot_name': 'Mountaineer Rharen',
            'message': 'Right Rharen.',
            'event_id': 1,
            'extra_data': json.dumps({
                'instance_id': 0,
                'addressed_name': 'Mountaineer Rharen',
                'participants': [{
                    'name': 'Mountaineer Rharen',
                    'is_npc': True,
                    'npc_spawn_id': 101,
                }],
            }),
        },
    ])
    history = _fetch_proximity_history(
        db, 42, 12, 0, 0,
        'Mountaineer Rharen', 101,
    )
    assert history == [{
        'name': 'Mountaineer Rharen',
        'message': 'Right Rharen.',
    }]
    query = db.cursor_value.queries[0][0]
    assert 'JSON_CONTAINS' in query
    assert "JSON_OBJECT('npc_spawn_id', %s)" in query


def test_history_restores_real_player_emote_context():
    db = _DB([{
        'bot_name': 'Mountaineer Rharen',
        'message': 'Well met!',
        'event_id': 1,
        'extra_data': json.dumps({
            'instance_id': 0,
            'addressed_name': 'Mountaineer Rharen',
            'player_name': 'Calwen',
            'player_emote': 'wave',
            'participants': [{
                'name': 'Mountaineer Rharen',
                'is_npc': True,
                'npc_spawn_id': 101,
            }],
        }),
    }])
    history = _fetch_proximity_history(
        db, 42, 12, 0, 0,
        'Mountaineer Rharen', 101,
    )
    assert history == [
        {
            'name': 'Calwen',
            'message': (
                '[performed /wave at Mountaineer Rharen]'
            ),
        },
        {
            'name': 'Mountaineer Rharen',
            'message': 'Well met!',
        },
    ]


def test_boss_history_is_scoped_in_sql_to_presence():
    db = _DB([
        {
            'message': 'Second warning.',
        },
        {
            'message': 'First warning.',
        },
    ])
    history = _fetch_previous_boss_lines(
        db, 9010, 33, 12, 1725796800
    )
    query, params = db.cursor_value.queries[0]
    assert "m.owner_subsystem = 'boss_dialogue'" in query
    assert "e.event_type IN (" in query
    assert "'$.instance_id'" in query
    assert "'$.presence_id'" in query
    assert params == (9010, 33, 12, 1725796800, 3)
    assert history == ['First warning.', 'Second warning.']


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
    assert '_proximityCooldownMutex' in source
    assert 'TryReserveProximityCooldown(' in source
    assert 'IsExplicitVocativeNameUse(' in source
    assert 'selected_npc_ineligible' in source
    selected_target = source.split(
        'SelectedCandidateMatch FindSelectedCandidate(', 1
    )[1].split('NamedCandidateMatch FindNamedCandidate(', 1)[0]
    assert 'if (!IsPlayerBot(selectedPlayer))' in selected_target
    assert 'selected_party_bot' in selected_target
    assert 'candidate.bot->GetGUID() == selGuid' in selected_target
    directed_say = source.split(
        'DirectedSayResult QueueDirectedPlayerSayProximityEvent(', 1
    )[1].split('void HandleProximityPlayerSayNewScene(', 1)[0]
    assert directed_say.index('FindNamedCandidate(') < (
        directed_say.index('if (selectedMatch.suppress')
    )
    assert '&& !explicitNamedOverride' in directed_say
    assert directed_say.count(
        'sLLMChatterConfig->IsDebugLog()'
    ) >= 2
    assert 'uint32 instanceId = 0;' in source
    assert 'scene.instanceId != instanceId' in source
    assert 'IsLLMChatterBoss(creature)' in source
    assert 'IsProximitySpeakerAllowed(entry)' in source
    assert 'IsProximitySpeakerDenied(entry)' in source
    assert '_proxChatterEnableInDungeons' in header
    assert '_proxChatterEnableInRaids' in header
    assert '_proxChatterOutdoorScanInterval' in header
    assert '_proxChatterInstanceScanInterval' in header
    assert '_proxChatterOutdoorChance' in header
    assert '_proxChatterInstanceChance' in header
    scoped_scan = source.split(
        'void CheckProximityChatter(bool instanceMaps)', 1
    )[1].split('void HandleProximityPlayerSay(', 1)[0]
    assert 'playerInInstance != instanceMaps' in scoped_scan
    effective_chance = source.split(
        'uint32 ComputeEffectiveChance(', 1
    )[1].split('void NoteZoneTrigger(', 1)[0]
    assert '_proxChatterInstanceChance' in effective_chance
    assert '_proxChatterOutdoorChance' in effective_chance
    assert '_proxChatterInstanceScanInterval' in effective_chance
    assert '_proxChatterOutdoorScanInterval' in effective_chance
    assert 'bool IsLLMChatterBoss' in shared
    assert 'FROM instance_encounters' in shared
    assert 'creditType = 0' in shared
    assert 'CreatureImmunitiesId > 0' in shared
    assert 'GetAggroRange(player)' in boss
    assert '_proxBossAggroSafetyMargin' in boss
    assert 'IsBossDialogueEntryDenied' in boss
    assert 'creature->IsHostileTo(player)' in boss
    boss_eligibility = boss.split(
        'bool IsBossDialogueSpeakerEligible(', 1
    )[1].split('void CheckBossProximityDialogue()', 1)[0]
    assert 'HasUnsafeChatterFacingMotion(creature)' not in boss_eligibility
    assert 'IsLLMChatterInternalCreature(creature)' in boss_eligibility
    assert 'creature->HasUnitState(UNIT_STATE_DIED)' in boss_eligibility
    assert 'creature->HasDynamicFlag(UNIT_DYNFLAG_DEAD)' in boss_eligibility
    assert 'player->CanSeeOrDetect(creature)' in boss_eligibility
    assert 'TryReserveBossDialogue' in boss
    assert 'TryScheduleBossApproach' in boss
    repeat_chance = boss.split(
        'uint32 GetBossRepeatChance(', 1
    )[1].split('void ResetBossPresenceState(', 1)[0]
    assert '_proxBossRepeatChanceFloor' in repeat_chance
    assert 'minimumChance' in repeat_chance
    assert 'std::max(' in repeat_chance
    scheduling = boss.split(
        'bool TryScheduleBossApproach(', 1
    )[1].split('uint64 PostponeBossApproach(', 1)[0]
    assert '_proxBossUnlimitedAutomaticLines' in scheduling
    assert 'maximumLines == 0' in scheduling
    assert 'state.linesQueued >= maximumLines' in scheduling
    assert 'reachedConfiguredLimit' in scheduling
    assert 'GetBossPresenceKey(Creature* creature)' in boss
    assert '_bossPresenceStates' in boss
    assert '_bossApproachCooldowns' not in boss
    assert 'automatic_line_number' in boss
    assert 'presence_id' in boss
    assert 'PostponeBossApproach(' in boss
    assert 'directedBoss);' in boss
    assert '_bossDialogueStateMutex' in boss
    assert 'TryBeginBossPlayerScan' in boss
    assert 'TryBeginBossDirectedScan' in boss
    assert 'return messageNamesSelectedBoss;' in boss
    assert 'ambiguousFirstToken = true' in boss
    assert 'ContainsCreatureEntry(' in config
    assert '_proxBossSpeakerDenyEntries, creatureEntry' in config
    assert '#include <memory>' in header
    assert (
        'std::shared_ptr<std::unordered_set<uint32> const>'
        in header
    )
    assert 'std::atomic<std::shared_ptr<' not in header
    assert 'std::atomic_load(&configured)' in config
    assert (
        'std::atomic_store(&_proxBossSpeakerDenyEntries,'
        in config
    )
    group_kill = group_combat.split(
        'void HandleGroupCreatureKillImpl(', 1
    )[1].split('\nvoid ', 1)[0]
    assert 'IsLLMChatterBoss(killed)' in group_kill
    enter_combat = group_combat.split(
        'void HandleGroupPlayerEnterCombatImpl(', 1
    )[1].split('\nvoid ', 1)[0]
    assert 'IsLLMChatterBoss(creature)' not in enter_combat
    assert 'CREATURE_TYPE_FLAG_BOSS_MOB' in enter_combat
    assert '_lastBossDialogueCheckTime' in world
    assert 'CheckBossProximityDialogue();' in world
    assert '_lastOutdoorProximityScanTime' in world
    assert '_lastInstanceProximityScanTime' in world
    assert 'CheckProximityChatter(false);' in world
    assert 'CheckProximityChatter(true);' in world

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
    assert 'IsSafeForChatterFacing(bot)' in delivery
    assert 'IsSafeForChatterFacing(speaker)' in delivery

    directed = source.index(
        'QueueDirectedPlayerSayProximityEvent('
    )
    active_scene = source.index(
        'ProximityScene* scene = FindBestScene(player);'
    )
    assert directed < active_scene


def test_mounted_players_remain_eligible_for_direct_interactions():
    source = (
        MODULE_DIR / 'src' / 'LLMChatterProximity.cpp'
    ).read_text(encoding='utf-8')
    anchor = source.split(
        'bool IsEligibleProximityAnchor(Player* player)', 1
    )[1].split(
        'bool IsEligibleAmbientProximityAnchor(Player* player)', 1
    )[0]
    ambient = source.split(
        'bool IsEligibleAmbientProximityAnchor(Player* player)', 1
    )[1].split('std::string GetNPCDisposition(', 1)[0]
    directed_say = source.split(
        'DirectedSayResult QueueDirectedPlayerSayProximityEvent(', 1
    )[1].split('void HandleProximityPlayerSayNewScene(', 1)[0]
    directed_emote = source.split(
        'void HandleProximityPlayerEmote(', 1
    )[1].split('void RecordDeliveredProximityLine(', 1)[0]

    assert '!player->IsMounted()' not in anchor
    assert '!player->IsMounted()' in ambient
    assert 'IsEligibleProximityAnchor(player)' in directed_say
    assert 'IsEligibleProximityAnchor(player)' in directed_emote
    assert source.count(
        'IsEligibleAmbientProximityAnchor(player)'
    ) == 3


def test_dungeon_boss_lookup_uses_registered_encounters():
    shared = (
        MODULE_DIR / 'tools' / 'chatter_shared.py'
    ).read_text(encoding='utf-8')
    lookup = shared.split(
        'def get_dungeon_bosses(', 1
    )[1].split('\ndef can_class_use_item(', 1)[0]
    assert 'instance_encounters' in lookup
    assert 'ie.creditType = 0' in lookup
    assert 'CreatureImmunitiesId > 0' in lookup
    assert '(map_id, map_id)' in lookup


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
    distributed = (
        MODULE_DIR / 'conf' / 'mod_llm_chatter.conf.dist'
    ).read_text(encoding='utf-8')
    assert '"ScanRadius", 40)' in source
    assert '"Chance", 30)' in source
    assert '"OutdoorScanIntervalSeconds",' in source
    assert '"InstanceScanIntervalSeconds",' in source
    assert '"OutdoorChance", _proxChatterChance)' in source
    assert '"InstanceChance", _proxChatterChance)' in source
    assert 'OutdoorScanIntervalSeconds = 30' in distributed
    assert 'InstanceScanIntervalSeconds = 30' in distributed
    assert 'OutdoorChance = 30' in distributed
    assert 'InstanceChance = 100' in distributed
    assert '"EntityCooldown", 3)' in source
    assert 'EntityCooldown = 3' in distributed
    assert '"ConversationLineDelay", 2)' in source
    assert '"MaxTokensPerLine", 120)' in source
    assert '"EnableBossDialogue", false)' in source
    assert '"BossApproachMaxRadius", 80)' in source
    assert '"BossAggroSafetyMargin", 0)' in source
    assert '"BossInitialDelayMinSeconds", 2)' in source
    assert '"BossInitialDelayMaxSeconds", 6)' in source
    assert '"BossRepeatDelayMinSeconds", 20)' in source
    assert '"BossRepeatDelayMaxSeconds", 60)' in source
    assert '"BossRepeatChance", 80)' in source
    assert '"BossRepeatChanceDecayPercent", 50)' in source
    assert '"BossRepeatChanceFloor", 10)' in source
    assert '"BossUnlimitedAutomaticLines", true)' in source
    assert '"BossMaxAutomaticLines", 3)' in source
    assert 'BossRepeatChanceFloor = 10' in distributed
    assert 'BossUnlimitedAutomaticLines = 1' in distributed
    assert 'BossMaxAutomaticLines = 3' in distributed
    assert 'Set to 0 to disable automatic lines' in distributed
    assert '"BossPresenceResetSeconds", 90)' in source
    assert 'BossDialogueCooldownSeconds' not in source
    assert '"BossDirectedScanCooldownSeconds", 1)' in source
    assert '"BossDirectedReplyCooldownSeconds", 3)' in source
    assert '"NPCVerbalCooldown", 3)' in source
    assert source.count('            3u);') >= 3
    assert 'BossDirectedReplyCooldownSeconds = 3' in distributed
    assert 'NPCVerbalCooldown = 3' in distributed


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
