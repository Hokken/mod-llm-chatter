#!/usr/bin/env python3
"""Focused player-driven Guild Chat checks.

Run directly from the module root:
  python tools/tests/test_guild_player_replies.py
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

import chatter_guild_player  # noqa: E402


def _candidate(guid: int, name: str) -> dict:
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


def _event() -> dict:
    return {
        'id': 77,
        'extra_data': json.dumps({
            'guild_id': 9,
            'guild_name': 'Keepers',
            'session_id': 41,
            'turn_id': 3,
            'player_guid': 7,
            'player_name': 'Calwen',
            'player_message': 'What became of that caravan?',
            'team': 'Alliance',
            'candidates': [
                _candidate(101, 'Aliss'),
                _candidate(102, 'Rytsen'),
            ],
        }),
    }


def test_topology_supports_all_three_shapes():
    config = {
        'LLMChatter.GuildChatter.'
        'PlayerReplies.MaxResponders': 3,
    }

    conversation = dict(config)
    conversation[
        'LLMChatter.GuildChatter.'
        'PlayerReplies.ConversationChance'
    ] = 100
    with patch.object(
        chatter_guild_player.random,
        'randint',
        side_effect=[1, 3],
    ):
        assert chatter_guild_player._choose_topology(
            conversation, 3, False
        ) == ('conversation', 3)

    multiple = dict(config)
    multiple[
        'LLMChatter.GuildChatter.'
        'PlayerReplies.ConversationChance'
    ] = 0
    multiple[
        'LLMChatter.GuildChatter.'
        'PlayerReplies.MultiReplyChance'
    ] = 100
    with patch.object(
        chatter_guild_player.random,
        'randint',
        side_effect=[1, 1, 2],
    ):
        assert chatter_guild_player._choose_topology(
            multiple, 3, False
        ) == ('multi_reply', 2)

    single = dict(multiple)
    single[
        'LLMChatter.GuildChatter.'
        'PlayerReplies.MultiReplyChance'
    ] = 0
    with patch.object(
        chatter_guild_player.random,
        'randint',
        side_effect=[1, 1],
    ):
        assert chatter_guild_player._choose_topology(
            single, 3, False
        ) == ('single', 1)

    assert chatter_guild_player._choose_topology(
        conversation, 1, False
    ) == ('single', 1)


def test_group_addressing_boosts_but_does_not_force_multi():
    config = {
        'LLMChatter.GuildChatter.'
        'PlayerReplies.ConversationChance': 0,
        'LLMChatter.GuildChatter.'
        'PlayerReplies.MultiReplyChance': 15,
        'LLMChatter.GuildChatter.'
        'PlayerReplies.MultiAddressedBonus': 15,
    }

    with patch.object(
        chatter_guild_player.random,
        'randint',
        side_effect=[100, 31],
    ):
        assert chatter_guild_player._choose_topology(
            config, 3, True
        ) == ('single', 1)

    with patch.object(
        chatter_guild_player.random,
        'randint',
        side_effect=[100, 30, 2],
    ):
        assert chatter_guild_player._choose_topology(
            config, 3, True
        ) == ('multi_reply', 2)


def test_reply_delays_use_full_shared_pacing():
    messages = [
        {'name': 'Aliss', 'message': 'First reply.'},
        {'name': 'Rytsen', 'message': 'Second reply.'},
        {'name': 'Aliss', 'message': 'Third reply.'},
    ]
    config = {
        'LLMChatter.GuildChatter.'
        'PlayerReplies.FirstDelayMin': 8,
        'LLMChatter.GuildChatter.'
        'PlayerReplies.FirstDelayMax': 20,
    }
    with (
        patch.object(
            chatter_guild_player.random,
            'randint',
            return_value=12,
        ),
        patch.object(
            chatter_guild_player,
            'calculate_dynamic_delay',
            return_value=17.0,
        ) as pacing,
    ):
        delays = chatter_guild_player._reply_delays(
            messages,
            'Hello guild.',
            config,
        )

    assert delays == [12.0, 29.0, 46.0]
    assert pacing.call_count == 2
    assert all(
        call.kwargs['responsive'] is False
        for call in pacing.call_args_list
    )


def test_addressed_bot_is_primary_responder():
    candidates = [
        _candidate(101, 'Aliss'),
        _candidate(102, 'Rytsen'),
        _candidate(103, 'Calia'),
    ]
    with patch.object(
        chatter_guild_player,
        '_weighted_pick',
        return_value=candidates[0],
    ):
        selected = (
            chatter_guild_player._select_responders(
                candidates,
                'Rytsen',
                2,
                ['Rytsen'],
                60,
            )
        )

    assert [
        responder['name'] for responder in selected
    ] == ['Rytsen', 'Aliss']


def test_context_separates_memory_and_visible_lines():
    context = chatter_guild_player._format_session_context(
        "Calwen promised to escort a caravan.",
        [
            {
                'speaker_name': 'Calwen',
                'is_bot': 0,
                'source_kind': 'player',
                'message': 'I will meet them at dawn.',
            },
            {
                'speaker_name': 'Aliss',
                'is_bot': 1,
                'source_kind': 'ambient',
                'message': 'Storm clouds gather.',
            },
        ],
    )

    assert "Compact memory" in context
    assert "Calwen (player)" in context
    assert "Aliss [ambient]" in context
    assert "escort a caravan" in context


def test_repeated_speaker_is_in_json_contract():
    participants = [
        _candidate(101, 'Aliss'),
        _candidate(102, 'Rytsen'),
    ]
    with (
        patch.object(
            chatter_guild_player,
            'select_conversation_message_count',
            return_value=3,
        ),
        patch.object(
            chatter_guild_player,
            '_select_participant_references',
            return_value=[],
        ),
    ):
        prompt, _, message_count = (
            chatter_guild_player._build_multi_prompt(
                participants,
                'conversation',
                'Keepers',
                'Alliance',
                'Calwen',
                'What do you think?',
                '',
                False,
                False,
                False,
                {},
            )
        )

    assert message_count == 3
    assert prompt.system_prompt.count(
        '"speaker": "Aliss"'
    ) == 2
    assert prompt.system_prompt.count(
        '"speaker": "Rytsen"'
    ) == 1


def test_single_reply_retries_empty_output_once():
    calls = []

    def fake_call(client, prompt, config, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return '{"message": ""}'
        return '{"message": "I remember it, Calwen."}'

    with (
        patch.object(
            chatter_guild_player,
            '_build_single_prompt',
            return_value='prompt',
        ),
        patch.object(
            chatter_guild_player,
            'call_llm',
            side_effect=fake_call,
        ),
    ):
        messages = (
            chatter_guild_player._generate_single_reply(
                None,
                object(),
                {},
                77,
                _candidate(101, 'Aliss'),
                'Keepers',
                'Alliance',
                'Calwen',
                'Do you remember?',
                '',
                False,
                True,
                False,
                {'guild_repair': False},
            )
        )

    assert messages == [{
        'name': 'Aliss',
        'message': 'I remember it, Calwen.',
    }]
    assert len(calls) == 2
    assert calls[1]['metadata']['guild_repair'] is True


def test_disabled_memory_is_not_sent_to_model():
    histories = []
    inserted = []
    statuses = []

    def addressed(
        message,
        bot_names,
        client=None,
        config=None,
        chat_history='',
    ):
        histories.append(chat_history)
        return {'bot': None, 'multi_addressed': False}

    with (
        patch.object(
            chatter_guild_player,
            '_session_is_current',
            return_value=True,
        ),
        patch.object(
            chatter_guild_player,
            '_fetch_session_context',
            return_value=(
                'Older private memory',
                [{
                    'speaker_name': 'Aliss',
                    'is_bot': 1,
                    'source_kind': 'reply',
                    'message': 'Earlier reply',
                }],
            ),
        ) as fetch_context,
        patch.object(
            chatter_guild_player,
            'find_addressed_bot',
            side_effect=addressed,
        ),
        patch.object(
            chatter_guild_player,
            '_choose_topology',
            return_value=('single', 1),
        ),
        patch.object(
            chatter_guild_player,
            '_select_responders',
            side_effect=lambda bots, *args: [bots[0]],
        ),
        patch.object(
            chatter_guild_player,
            '_generate_single_reply',
            return_value=[{
                'name': 'Aliss',
                'message': 'The caravan reached safety.',
            }],
        ) as generate,
        patch.object(
            chatter_guild_player,
            'insert_chat_message',
            side_effect=lambda db, **kwargs:
                inserted.append(kwargs),
        ),
        patch.object(
            chatter_guild_player,
            '_mark_event',
            side_effect=lambda db, event_id, status:
                statuses.append((event_id, status)),
        ),
        patch.object(
            chatter_guild_player,
            '_maybe_summarize_session',
            return_value=False,
        ),
        patch.object(
            chatter_guild_player.random,
            'randint',
            return_value=100,
        ),
    ):
        result = (
            chatter_guild_player
            .process_guild_player_message_event(
                object(),
                object(),
                {
                    'LLMChatter.GuildChatter.'
                    'SessionMemory.Enable': '0',
                },
                _event(),
            )
        )

    assert result is True
    assert histories == ['']
    assert fetch_context.call_args.args[2] == 15
    assert generate.call_args.args[9] == ''
    assert inserted[0]['channel'] == 'guild'
    assert statuses[-1] == (77, 'completed')


def test_stale_turn_is_skipped_before_generation():
    statuses = []
    with (
        patch.object(
            chatter_guild_player,
            '_session_is_current',
            return_value=False,
        ),
        patch.object(
            chatter_guild_player,
            '_mark_event',
            side_effect=lambda db, event_id, status:
                statuses.append((event_id, status)),
        ),
        patch.object(
            chatter_guild_player,
            'call_llm',
        ) as call,
    ):
        result = (
            chatter_guild_player
            .process_guild_player_message_event(
                object(), object(), {}, _event()
            )
        )

    assert result is False
    assert statuses == [(77, 'skipped')]
    call.assert_not_called()


class _SummaryCursor:
    def __init__(self, db):
        self.db = db
        self.one = None
        self.all = []

    def execute(self, query, params=None):
        if "SELECT summary" in query:
            self.one = {
                'summary': 'The caravan was delayed.',
                'summarized_through_id': 0,
            }
        elif (
            "SELECT id " in query
            and "SELECT id, speaker_name" not in query
        ):
            self.all = self.db.recent_rows
        elif "SELECT id, speaker_name" in query:
            self.all = self.db.rows
        elif "UPDATE llm_guild_chat_sessions" in query:
            self.db.update_params = params

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.all


class _SummaryDb:
    def __init__(self):
        long_line = "A" * 300
        self.rows = [
            {
                'id': index,
                'speaker_name': (
                    'Calwen' if index % 2 else 'Aliss'
                ),
                'is_bot': index % 2 == 0,
                'message': long_line,
            }
            for index in range(1, 7)
        ]
        self.recent_rows = [
            {'id': index}
            for index in range(6, 2, -1)
        ]
        self.update_params = None
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return _SummaryCursor(self)

    def commit(self):
        self.commits += 1


def test_summary_reuses_configured_client_and_model():
    db = _SummaryDb()
    client = object()
    config = {
        'LLMChatter.Provider': 'ollama',
        'LLMChatter.Model': 'qwen-local',
        'LLMChatter.GuildChatter.'
        'SessionMemory.Enable': '1',
        'LLMChatter.GuildChatter.'
        'SessionMemory.KeepRecentMessages': 4,
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryThresholdChars': 500,
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryMaxInputChars': 500,
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryMaxTokens': 300,
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryMaxChars': 1200,
    }
    calls = []

    def fake_call(
        passed_client,
        prompt,
        passed_config,
        **kwargs,
    ):
        calls.append((
            passed_client,
            passed_config,
            prompt,
            kwargs,
        ))
        return json.dumps({
            'message': (
                'Calwen promised to help the delayed '
                'caravan; Aliss remains concerned.'
            ),
        })

    with patch.object(
        chatter_guild_player,
        'call_llm',
        side_effect=fake_call,
    ):
        result = (
            chatter_guild_player._maybe_summarize_session(
                db, client, config, 41
            )
        )

    assert result is True
    assert calls[0][0] is client
    assert calls[0][1] is config
    assert calls[0][3]['label'] == (
        'guild_session_summary'
    )
    assert db.update_params[1:] == (1, 41)
    assert db.commits == 1


def test_summary_boundary_uses_all_visible_guild_lines():
    db = _SummaryDb()
    db.rows = [
        {
            'id': 1,
            'speaker_name': 'Calwen',
            'is_bot': False,
            'message': 'A' * 600,
        },
        {
            'id': 2,
            'speaker_name': 'Aliss',
            'is_bot': True,
            'message': 'B' * 600,
        },
    ]
    db.recent_rows = [
        {'id': index}
        for index in range(20, 5, -1)
    ]
    config = {
        'LLMChatter.GuildChatter.'
        'SessionMemory.Enable': '1',
        'LLMChatter.GuildChatter.'
        'SessionMemory.KeepRecentMessages': 15,
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryThresholdChars': 500,
    }

    with patch.object(
        chatter_guild_player,
        'call_llm',
        return_value=json.dumps({
            'message': 'Calwen and Aliss discussed a promise.',
        }),
    ):
        assert chatter_guild_player._maybe_summarize_session(
            db,
            object(),
            config,
            41,
        ) is True

    assert db.update_params[1] == 2


if __name__ == '__main__':
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed")
