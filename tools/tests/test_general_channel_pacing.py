#!/usr/bin/env python3
"""Focused checks for cross-producer General pacing."""

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import patch


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
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_shared  # noqa: E402
import chatter_world_events  # noqa: E402


CONFIG = {'LLMChatter.GeneralChat.MinZoneGap': 15}


def test_full_windows_are_serialized():
    chatter_shared._zone_last_delivery.clear()
    with (
        patch(
            'chatter_shared.time.monotonic',
            return_value=100.0,
        ),
        patch(
            'chatter_shared.random.random',
            return_value=1.0,
        ),
    ):
        first = chatter_shared._reserve_zone_delivery_window(
            12, CONFIG, duration_seconds=20,
        )
        second = chatter_shared._reserve_zone_delivery_window(
            12, CONFIG, duration_seconds=10,
        )

    assert first == 0
    assert second == 35
    assert chatter_shared._zone_last_delivery[12] == 145


def test_extending_never_shortens_a_reservation():
    chatter_shared._zone_last_delivery.clear()
    chatter_shared._zone_last_delivery[12] = 145.0
    with patch(
        'chatter_shared.time.monotonic',
        return_value=100.0,
    ):
        chatter_shared._extend_zone_delivery_window(12, 5)
        assert chatter_shared._zone_last_delivery[12] == 145

        chatter_shared._extend_zone_delivery_window(12, 60)
        assert chatter_shared._zone_last_delivery[12] == 160


def test_automated_conversations_reserve_full_windows():
    ambient = (
        TOOLS_DIR / 'chatter_ambient.py'
    ).read_text(encoding='utf-8')
    events = (
        TOOLS_DIR / 'chatter_world_events.py'
    ).read_text(encoding='utf-8')
    general = (
        TOOLS_DIR / 'chatter_general.py'
    ).read_text(encoding='utf-8')

    assert '_reserve_zone_delivery_window(' in ambient
    assert '_reserve_zone_delivery_window(' in events
    assert 'duration_seconds=relative_delay' in ambient
    assert 'duration_seconds=relative_delay' in events
    assert '_zone_last_delivery[zone_id] =' not in ambient
    assert '_zone_last_delivery[zone_id] =' not in general


def test_world_event_conversation_uses_reserved_window():
    inserted = []
    reservation = []
    bots = [
        {
            'bot1_guid': index,
            'bot1_name': f'Bot{index}',
            'bot1_class': 'Mage',
            'bot1_race': 'Human',
            'bot1_level': 20,
            'zone_id': 12,
        }
        for index in range(1, 4)
    ]
    messages = [
        {
            'name': f'Bot{index}',
            'message': f'Line {index}',
            'action': None,
        }
        for index in range(1, 4)
    ]

    def reserve(zone_id, _config, duration_seconds):
        reservation.append((zone_id, duration_seconds))
        return 5.0

    with (
        patch.object(
            chatter_world_events,
            'get_zone_name', return_value='Zone',
        ),
        patch.object(
            chatter_world_events,
            'get_recent_zone_messages', return_value=[],
        ),
        patch.object(
            chatter_world_events,
            'build_event_context', return_value='Event',
        ),
        patch.object(
            chatter_world_events,
            'build_event_conversation_prompt',
            return_value='Prompt',
        ),
        patch.object(
            chatter_world_events,
            'call_llm', return_value='Generated',
        ),
        patch.object(
            chatter_world_events,
            'parse_conversation_response',
            return_value=messages,
        ),
        patch.object(
            chatter_world_events,
            'strip_conversation_actions',
        ),
        patch.object(
            chatter_world_events,
            'calculate_dynamic_delay', return_value=10.0,
        ),
        patch.object(
            chatter_world_events,
            '_reserve_zone_delivery_window',
            side_effect=reserve,
        ),
        patch.object(
            chatter_world_events,
            'insert_chat_message',
            side_effect=lambda *args, **kwargs: inserted.append(
                kwargs['delay_seconds']
            ),
        ),
        patch.object(
            chatter_world_events,
            'maybe_queue_group_general_reaction',
        ),
        patch.object(
            chatter_world_events, 'mark_event',
        ),
    ):
        assert chatter_world_events._deliver_conversation(
            object(), object(), {},
            {'id': 9, 'map_id': 0},
            bots, {}, 12,
        )

    assert reservation == [(12, 20.0)]
    assert inserted == [5.0, 15.0, 25.0]


def test_single_reaction_resolves_delay_after_generation():
    with (
        patch.object(
            chatter_shared, 'call_llm',
            return_value='generated',
        ),
        patch.object(
            chatter_shared, 'parse_single_response',
            return_value={
                'message': 'hello',
                'emote': None,
                'action': None,
            },
        ),
        patch.object(
            chatter_shared, 'insert_chat_message'
        ) as insert,
    ):
        result = chatter_shared.run_single_reaction(
            object(), object(), {},
            prompt='prompt',
            speaker_name='Bot',
            bot_guid=1,
            channel='general',
            delay_seconds=5,
            delay_resolver=lambda _message: 42,
        )

    assert result['ok'] is True
    assert result['delay_seconds'] == 42
    assert insert.call_args.kwargs['delay_seconds'] == 42


if __name__ == '__main__':
    tests = [
        test_full_windows_are_serialized,
        test_extending_never_shortens_a_reservation,
        test_automated_conversations_reserve_full_windows,
        test_world_event_conversation_uses_reserved_window,
        test_single_reaction_resolves_delay_after_generation,
    ]
    for test in tests:
        test()
    print(f'{len(tests)}/{len(tests)} tests passed')
