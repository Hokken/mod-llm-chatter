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
import chatter_db  # noqa: E402
import chatter_general  # noqa: E402
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


def test_brief_single_addressee_suppresses_conversation():
    with (
        patch.object(
            chatter_general,
            'find_addressed_bot',
            return_value={
                'bot': 'Karguhr',
                'multi_addressed': False,
                'brief_casual': True,
                'reply_optional': True,
            },
        ),
        patch.object(
            chatter_general,
            '_get_bot_info',
            return_value={
                'name': 'Karguhr',
                'race': 1,
                'class': 1,
                'level': 30,
                'gender': 0,
            },
        ),
        patch.object(
            chatter_general.random,
            'randint',
            return_value=1,
        ),
    ):
        result = chatter_general._select_primary_bot(
            object(),
            object(),
            {'LLMChatter.GeneralChat.ConversationChance': 100},
            [101, 102],
            ['Karguhr', 'Oscario'],
            'Calwen',
            'That means a lot.',
            'roleplay',
            chat_hist='Karguhr: Welcome back.',
        )

    assert result['bot1_name'] == 'Karguhr'
    assert result['brief_casual'] is True
    assert result['reply_optional'] is True
    assert result['is_conversation'] is False


def test_player_general_candidates_match_player_faction():
    class Cursor:
        query_count = 0

        def execute(self, _query, _params):
            self.query_count += 1

        def fetchall(self):
            return [
                {'guid': 101, 'race': 2},
                {'guid': 102, 'race': 7},
                {'guid': 103, 'race': 8},
                {'guid': 104, 'race': 1},
            ]

        def close(self):
            pass

    class DB:
        cursor_value = Cursor()

        def cursor(self, **_kwargs):
            return self.cursor_value

    db = DB()
    guids, names = (
        chatter_general._filter_player_general_candidates(
            db,
            'Alliance',
            [101, 102, 103, 104],
            ['OrcBot', 'GnomeBot', 'TrollBot', 'HumanBot'],
        )
    )

    assert guids == [102, 104]
    assert names == ['GnomeBot', 'HumanBot']
    assert db.cursor_value.query_count == 1


def test_player_general_recent_context_matches_faction():
    class Cursor:
        query = ''

        def execute(self, query, _params):
            self.query = query

        def fetchall(self):
            return []

    class DB:
        cursor_value = Cursor()

        def cursor(self, **_kwargs):
            return self.cursor_value

    db = DB()
    chatter_db.get_recent_zone_messages(
        db, 12, faction='Alliance'
    )
    assert 'c.race IN (1, 3, 4, 7, 11)' in (
        db.cursor_value.query
    )


def test_cpp_general_roster_matches_player_team():
    source = (
        TOOLS_DIR.parent / 'src' / 'LLMChatterPlayer.cpp'
    ).read_text(encoding='utf-8')
    assert source.count(
        '!= player->GetTeamId()'
    ) >= 2


def test_cpp_player_reply_delivery_rechecks_faction():
    source = (
        TOOLS_DIR.parent / 'src' / 'LLMChatterDelivery.cpp'
    ).read_text(encoding='utf-8')
    for event_type in (
        'player_general_msg',
        'bot_group_player_msg',
        'guild_player_message',
        'guild_login_greeting',
    ):
        assert f'eventType == "{event_type}"' in source
    assert 'eventType == "bot_group_general_reaction"' not in source
    assert 'e.subject_guid' in source
    assert 'subject->GetTeamId()' in source
    assert '!= bot->GetTeamId()' in source
    assert '"faction_mismatch"' in source
    assert 'if (subject' in source
    assert '!subject ||' not in source


def test_cpp_party_player_route_requires_same_team_bot():
    source = (
        TOOLS_DIR.parent / 'src' /
        'LLMChatterGroupCombat.cpp'
    ).read_text(encoding='utf-8')
    handler = source.split(
        'void HandleGroupPlayerBeforeSendChatMessageImpl(', 1
    )[1].split(
        'void HandleGroupPlayerLevelChangedImpl(', 1
    )[0]
    assert 'member->GetTeamId()' in handler
    assert '== player->GetTeamId()' in handler


if __name__ == '__main__':
    tests = [
        test_full_windows_are_serialized,
        test_extending_never_shortens_a_reservation,
        test_automated_conversations_reserve_full_windows,
        test_world_event_conversation_uses_reserved_window,
        test_single_reaction_resolves_delay_after_generation,
        test_brief_single_addressee_suppresses_conversation,
        test_player_general_candidates_match_player_faction,
        test_player_general_recent_context_matches_faction,
        test_cpp_general_roster_matches_player_team,
        test_cpp_player_reply_delivery_rechecks_faction,
        test_cpp_party_player_route_requires_same_team_bot,
    ]
    for test in tests:
        test()
    print(f'{len(tests)}/{len(tests)} tests passed')
