#!/usr/bin/env python3
"""Focused Guild statement/conversation checks.

Run directly from the module root:
  python tools/tests/test_guild_conversations.py
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
    for module_name in ("openai",):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            module = _ensure_module(module_name)
            class_name = "OpenAI"
            setattr(
                module,
                class_name,
                type(class_name, (), {}),
            )

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module(
            "mysql.connector"
        )
        setattr(
            mysql_module,
            "connector",
            connector_module,
        )


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_guild  # noqa: E402


class _Cursor:
    def __init__(self, db):
        self.db = db
        self.results = []

    def execute(self, query, params=None):
        if "UPDATE llm_chatter_events" in query:
            self.db.statuses.append(params)
        elif (
            "SELECT id FROM llm_guild_chat_sessions"
            in query
        ):
            self.db.history_queries += 1
            self.results = (
                [{'id': self.db.history_session_id}]
                if self.db.history_session_id
                else []
            )
        elif (
            "FROM llm_guild_session_history"
            in query
        ):
            self.db.history_queries += 1
            limit = int(params[1])
            self.results = list(
                reversed(self.db.history_rows[-limit:])
            )

    def fetchone(self):
        return self.results[0] if self.results else None

    def fetchall(self):
        return list(self.results)


class _DB:
    def __init__(self):
        self.statuses = []
        self.history_queries = 0
        self.history_session_id = 0
        self.history_rows = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def commit(self):
        pass


def _speaker(guid: int) -> dict:
    return {
        'class': 'Mage' if guid % 2 else 'Warrior',
        'race': 'Human',
        'gender': 'female',
        'level': 80,
        'traits': ['steadfast'],
        'tone': 'warm',
        'backstory': '',
    }


def _event(names) -> dict:
    participants = [
        {
            'guid': 100 + index,
            'name': name,
            'zone_id': 12 + index,
            'map_id': 0,
        }
        for index, name in enumerate(names)
    ]
    return {
        'id': 77,
        'subject_guid': participants[0]['guid'],
        'subject_name': participants[0]['name'],
        'zone_id': participants[0]['zone_id'],
        'map_id': participants[0]['map_id'],
        'extra_data': json.dumps({
            'guild_id': 9,
            'guild_name': 'Keepers',
            'speaker_name': participants[0]['name'],
            'mode': 'conversation',
            'participants': participants,
            'guildmates': 'Calia',
            'team': 'Alliance',
            'zone_id': participants[0]['zone_id'],
        }),
    }


def _config() -> dict:
    return {
        'LLMChatter.GuildChatter.MaxTokens': 200,
        'LLMChatter.GuildChatter.MaxConversationLines': 4,
        'LLMChatter.GuildChatter.HistoryContextChance': 35,
        'LLMChatter.GuildChatter.HistoryContextMessages': 15,
        'LLMChatter.GuildChatter.'
        'ParticipantReferenceChance': 25,
        'LLMChatter.GuildChatter.'
        'MultiReferenceChance': 15,
        'LLMChatter.GuildChatter.MaxReferenceLines': 2,
        'LLMChatter.GuildChatter.ZoneNameChance': 20,
        'LLMChatter.MessageDelayMin': 1000,
        'LLMChatter.MessageDelayMax': 30000,
    }


def _conversation_response(names) -> str:
    messages = [
        {
            'speaker': name,
            'message': f"{name} answers the guild.",
        }
        for name in names
    ]
    if len(messages) == 2:
        messages.extend([
            {
                'speaker': names[0],
                'message': "The road has taught me patience.",
            },
            {
                'speaker': names[1],
                'message': "Patience and a dry cloak.",
            },
        ])
    else:
        messages.append({
            'speaker': names[0],
            'message': "Then we are agreed.",
        })
    return json.dumps(messages)


def test_legacy_payload_normalizes_to_statement():
    event = {
        'subject_guid': 101,
        'subject_name': 'Aliss',
        'map_id': 0,
    }
    extra = {
        'speaker_name': 'Aliss',
        'zone_id': 12,
    }
    participants, mode = (
        chatter_guild._normalize_guild_participants(
            event, extra
        )
    )

    assert mode == 'statement'
    assert participants == [{
        'guid': 101,
        'name': 'Aliss',
        'zone_id': 12,
        'map_id': 0,
    }]


def test_legacy_payload_processes_statement():
    db = _DB()
    inserted = []
    event = {
        'id': 17,
        'subject_guid': 101,
        'subject_name': 'Aliss',
        'zone_id': 12,
        'map_id': 0,
        'extra_data': json.dumps({
            'guild_name': 'Keepers',
            'speaker_name': 'Aliss',
            'guildmates': 'Rytsen',
            'team': 'Alliance',
            'zone_id': 12,
        }),
    }

    with (
        patch.object(
            chatter_guild,
            '_query_speaker',
            return_value=_speaker(101),
        ),
        patch.object(
            chatter_guild,
            'call_llm',
            return_value=json.dumps({
                'message': 'The guild has my greeting.',
            }),
        ),
        patch.object(
            chatter_guild,
            'insert_chat_message',
            side_effect=lambda db_arg, **kwargs:
                inserted.append(kwargs),
        ),
        patch.object(
            chatter_guild.random,
            'choice',
            return_value='guild fellowship',
        ),
        patch.object(
            chatter_guild.random,
            'randint',
            return_value=100,
        ),
        patch.object(
            chatter_guild,
            '_pick_length_hint',
            return_value='HARD LIMIT: 150 characters.',
        ),
    ):
        result = (
            chatter_guild.process_guild_idle_chatter_event(
                db, None, _config(), event
            )
        )

    assert result is True
    assert len(inserted) == 1
    assert inserted[0]['bot_name'] == 'Aliss'
    assert inserted[0]['channel'] == 'guild'
    assert db.statuses[-1] == ('completed', 17)


def test_structured_payload_caps_three_participants():
    event = _event([
        'Aliss', 'Rytsen', 'Calia', 'Dorn'
    ])
    extra = json.loads(event['extra_data'])
    participants, mode = (
        chatter_guild._normalize_guild_participants(
            event, extra
        )
    )

    assert mode == 'conversation'
    assert [
        participant['name']
        for participant in participants
    ] == ['Aliss', 'Rytsen', 'Calia']


def test_history_context_miss_avoids_database_query():
    db = _DB()
    with patch.object(
        chatter_guild.random,
        'randint',
        return_value=90,
    ):
        context, metadata = (
            chatter_guild
            ._select_guild_history_context(
                db,
                _config(),
                9,
            )
        )

    assert context == ''
    assert db.history_queries == 0
    assert (
        metadata['guild_history_context_roll']
        == 90
    )
    assert (
        metadata['guild_history_context_selected']
        is False
    )


def test_history_context_hit_loads_latest_visible_lines():
    db = _DB()
    db.history_session_id = 41
    db.history_rows = [
        {
            'id': 10,
            'speaker_name': 'Karaez',
            'is_bot': 0,
            'source_kind': 'player',
            'message': 'Anyone seen the old shrine?',
        },
        {
            'id': 11,
            'speaker_name': 'Aliss',
            'is_bot': 1,
            'source_kind': 'reply',
            'message': 'Not since the last moon.',
        },
        {
            'id': 12,
            'speaker_name': 'Rytsen',
            'is_bot': 1,
            'source_kind': 'ambient',
            'message': 'The road east is quiet.',
        },
    ]
    with patch.object(
        chatter_guild.random,
        'randint',
        return_value=1,
    ):
        context, metadata = (
            chatter_guild
            ._select_guild_history_context(
                db,
                _config(),
                9,
            )
        )

    assert (
        'Karaez (player): Anyone seen the old shrine?'
        in context
    )
    assert (
        'Rytsen [ambient]: The road east is quiet.'
        in context
    )
    assert db.history_queries == 2
    assert (
        metadata['guild_history_context_selected']
        is True
    )
    assert metadata['guild_history_context_lines'] == 3
    assert metadata['guild_history_session_id'] == 41
    assert metadata['guild_history_oldest_id'] == 10
    assert metadata['guild_history_newest_id'] == 12


def test_reference_selection_supports_mixed_patterns():
    with patch.object(
        chatter_guild.random,
        'randint',
        side_effect=[1, 1, 1, 100],
    ):
        plans = (
            chatter_guild
            ._select_participant_references(
                ['Aliss', 'Rytsen', 'Calia'],
                4,
                chance=25,
                multi_chance=15,
                max_reference_lines=2,
            )
        )

    assert plans == [
        {
            'message_index': 1,
            'speaker': 'Rytsen',
            'candidates': ['Aliss'],
            'target_count': 1,
        },
        {
            'message_index': 2,
            'speaker': 'Calia',
            'candidates': ['Aliss', 'Rytsen'],
            'target_count': 2,
        },
    ]


def test_reference_accepts_model_selected_earlier_speaker():
    messages = [
        {
            'name': 'Aliss',
            'message': 'The road is dangerous.',
        },
        {
            'name': 'Rytsen',
            'message': 'We should travel carefully.',
        },
        {
            'name': 'Calia',
            'message': 'You are right, Aliss!',
        },
    ]
    original = messages[2]['message']
    results = chatter_guild._apply_participant_references(
        messages,
        [{
            'message_index': 2,
            'speaker': 'Calia',
            'candidates': ['Aliss', 'Rytsen'],
            'target_count': 1,
        }],
    )

    assert messages[2]['message'] == original
    assert results[0]['targets'] == ['Aliss']
    assert results[0]['fallback'] is False


def test_reference_fallback_guarantees_requested_names():
    messages = [
        {
            'name': 'Aliss',
            'message': 'The road is dangerous.',
        },
        {
            'name': 'Rytsen',
            'message': 'We should travel carefully.',
        },
        {
            'name': 'Calia',
            'message': 'You are right!',
        },
    ]
    with patch.object(
        chatter_guild.random,
        'sample',
        return_value=['Aliss', 'Rytsen'],
    ):
        results = (
            chatter_guild
            ._apply_participant_references(
                messages,
                [{
                    'message_index': 2,
                    'speaker': 'Calia',
                    'candidates': [
                        'Aliss', 'Rytsen',
                    ],
                    'target_count': 2,
                }],
            )
        )

    assert (
        messages[2]['message']
        == 'You are right, Aliss and Rytsen!'
    )
    assert results[0]['targets'] == [
        'Aliss', 'Rytsen',
    ]
    assert results[0]['fallback'] is True


def _run_valid_conversation(names) -> None:
    db = _DB()
    inserted = []
    llm_calls = []

    def fake_call_llm(
        client, prompt, config, **kwargs
    ):
        llm_calls.append((prompt, kwargs))
        return _conversation_response(names)

    def fake_insert(db_arg, **kwargs):
        inserted.append(kwargs)

    with (
        patch.object(
            chatter_guild,
            '_query_speaker',
            side_effect=lambda db_arg, guid: _speaker(guid),
        ),
        patch.object(
            chatter_guild,
            'call_llm',
            side_effect=fake_call_llm,
        ),
        patch.object(
            chatter_guild,
            'insert_chat_message',
            side_effect=fake_insert,
        ),
        patch.object(
            chatter_guild,
            'select_conversation_message_count',
            return_value=4,
        ),
        patch.object(
            chatter_guild,
            'calculate_dynamic_delay',
            return_value=5.0,
        ),
        patch.object(
            chatter_guild.random,
            'choice',
            return_value='the long road home',
        ),
        patch.object(
            chatter_guild.random,
            'randint',
            return_value=100,
        ),
    ):
        result = (
            chatter_guild.process_guild_idle_chatter_event(
                db, None, _config(), _event(names)
            )
        )

    assert result is True
    assert len(llm_calls) == 1
    assert len(inserted) == 4
    assert {
        row['bot_name'] for row in inserted
    } == set(names)
    assert [
        row['sequence'] for row in inserted
    ] == [0, 1, 2, 3]
    assert [
        row['delay_seconds'] for row in inserted
    ] == [2.0, 7.0, 12.0, 17.0]
    assert all(
        row['channel'] == 'guild'
        and row['owner_subsystem'] == 'guild'
        and row['event_id'] == 77
        for row in inserted
    )
    prompt, kwargs = llm_calls[0]
    assert '"emote"' not in prompt.system_prompt
    assert '"action"' not in prompt.system_prompt
    assert kwargs['max_tokens_override'] == min(
        200 * (1 + len(names)), 1000
    )
    assert db.statuses[-1] == ('completed', 77)


def test_two_participant_conversation():
    _run_valid_conversation(['Aliss', 'Rytsen'])


def test_three_participant_conversation():
    _run_valid_conversation([
        'Aliss', 'Rytsen', 'Calia'
    ])


def test_invalid_conversation_repairs_once():
    names = ['Aliss', 'Rytsen']
    db = _DB()
    inserted = []
    calls = []
    responses = iter([
        json.dumps([
            {
                'speaker': 'Aliss',
                'message': 'Only one selected speaker answers.',
            },
            {
                'speaker': 'Stranger',
                'message': 'An unknown speaker intrudes.',
            },
        ]),
        _conversation_response(names),
    ])

    def fake_call_llm(
        client, prompt, config, **kwargs
    ):
        calls.append(kwargs)
        return next(responses)

    with (
        patch.object(
            chatter_guild,
            '_query_speaker',
            side_effect=lambda db_arg, guid: _speaker(guid),
        ),
        patch.object(
            chatter_guild,
            'call_llm',
            side_effect=fake_call_llm,
        ),
        patch.object(
            chatter_guild,
            'insert_chat_message',
            side_effect=lambda db_arg, **kwargs:
                inserted.append(kwargs),
        ),
        patch.object(
            chatter_guild,
            'select_conversation_message_count',
            return_value=4,
        ),
        patch.object(
            chatter_guild,
            'calculate_dynamic_delay',
            return_value=1.0,
        ),
        patch.object(
            chatter_guild.random,
            'choice',
            return_value='old victories',
        ),
        patch.object(
            chatter_guild.random,
            'randint',
            return_value=100,
        ),
    ):
        result = (
            chatter_guild.process_guild_idle_chatter_event(
                db, None, _config(), _event(names)
            )
        )

    assert result is True
    assert len(calls) == 2
    assert calls[0]['metadata']['guild_repair'] is False
    assert calls[1]['metadata']['guild_repair'] is True
    assert len(inserted) == 4
    assert db.statuses[-1] == ('completed', 77)


def test_failed_repair_falls_back_to_statement():
    names = ['Aliss', 'Rytsen']
    db = _DB()
    inserted = []
    calls = []
    responses = iter([
        'not json',
        'still not json',
        json.dumps({
            'message': 'The guild still has my word.',
        }),
    ])

    def fake_call_llm(
        client, prompt, config, **kwargs
    ):
        calls.append((prompt, kwargs))
        return next(responses)

    with (
        patch.object(
            chatter_guild,
            '_query_speaker',
            side_effect=lambda db_arg, guid: _speaker(guid),
        ),
        patch.object(
            chatter_guild,
            'call_llm',
            side_effect=fake_call_llm,
        ),
        patch.object(
            chatter_guild,
            'insert_chat_message',
            side_effect=lambda db_arg, **kwargs:
                inserted.append(kwargs),
        ),
        patch.object(
            chatter_guild,
            'select_conversation_message_count',
            return_value=4,
        ),
        patch.object(
            chatter_guild.random,
            'choice',
            return_value='keeping faith',
        ),
        patch.object(
            chatter_guild.random,
            'randint',
            return_value=100,
        ),
        patch.object(
            chatter_guild,
            '_pick_length_hint',
            return_value='HARD LIMIT: 150 characters.',
        ),
        patch.object(
            chatter_guild,
            '_select_guild_history_context',
            return_value=(
                '  Karaez (player): Keep watch east.',
                {
                    'guild_history_context_chance': 35,
                    'guild_history_context_roll': 7,
                    'guild_history_context_roll_hit': True,
                    'guild_history_context_selected': True,
                    'guild_history_context_limit': 15,
                    'guild_history_context_lines': 1,
                    'guild_history_session_id': 41,
                    'guild_history_oldest_id': 10,
                    'guild_history_newest_id': 10,
                    'guild_history_player_lines': 1,
                    'guild_history_reply_lines': 0,
                    'guild_history_ambient_lines': 0,
                },
            ),
        ) as history_select,
    ):
        result = (
            chatter_guild.process_guild_idle_chatter_event(
                db, None, _config(), _event(names)
            )
        )

    assert result is True
    assert len(calls) == 3
    assert history_select.call_count == 1
    assert all(
        'Karaez (player): Keep watch east.'
        in str(prompt)
        for prompt, _kwargs in calls
    )
    assert (
        calls[-1][1]['metadata']
        ['guild_statement_fallback']
        is True
    )
    assert all(
        kwargs['metadata']
        ['guild_history_context_roll'] == 7
        for _prompt, kwargs in calls
    )
    assert len(inserted) == 1
    assert inserted[0]['bot_name'] == 'Aliss'
    assert inserted[0].get('sequence', 0) == 0
    assert db.statuses[-1] == ('completed', 77)


def main() -> int:
    tests = [
        test_legacy_payload_normalizes_to_statement,
        test_legacy_payload_processes_statement,
        test_structured_payload_caps_three_participants,
        test_history_context_miss_avoids_database_query,
        test_history_context_hit_loads_latest_visible_lines,
        test_reference_selection_supports_mixed_patterns,
        test_reference_accepts_model_selected_earlier_speaker,
        test_reference_fallback_guarantees_requested_names,
        test_two_participant_conversation,
        test_three_participant_conversation,
        test_invalid_conversation_repairs_once,
        test_failed_repair_falls_back_to_statement,
    ]
    for test in tests:
        test()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
