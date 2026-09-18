#!/usr/bin/env python3
"""Focused Guild login greeting checks.

Run directly from the module root:
  python tools/tests/test_guild_login_greetings.py
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

import chatter_guild_login  # noqa: E402
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402


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
        'id': 91,
        'extra_data': json.dumps({
            'guild_id': 9,
            'guild_name': 'Keepers',
            'session_id': 41,
            'turn_id': 0,
            'player_guid': 7,
            'player_name': 'Calwen',
            'team': 'Alliance',
            'candidates': [
                _candidate(101, 'Aliss'),
                _candidate(102, 'Rytsen'),
                _candidate(103, 'Calia'),
            ],
        }),
    }


def test_registry_routes_login_greeting():
    spec = EVENT_REGISTRY['guild_login_greeting']
    assert spec.handler_module == 'chatter_guild_login'
    assert spec.handler_func == (
        'process_guild_login_greeting_event'
    )
    assert spec.priority == 'high'


def test_single_is_common_and_multi_is_bounded():
    config = {
        'LLMChatter.GuildChatter.'
        'LoginGreeting.MultiReplyChance': 20,
        'LLMChatter.GuildChatter.'
        'LoginGreeting.MaxResponders': 3,
    }

    with patch.object(
        chatter_guild_login.random,
        'randint',
        return_value=21,
    ):
        assert (
            chatter_guild_login
            ._choose_responder_count(config, 3)
            == 1
        )

    with patch.object(
        chatter_guild_login.random,
        'randint',
        side_effect=[20, 3],
    ):
        assert (
            chatter_guild_login
            ._choose_responder_count(config, 3)
            == 3
        )

    assert (
        chatter_guild_login
        ._choose_responder_count(config, 1)
        == 1
    )


def test_first_message_has_no_second_delay():
    messages = [
        {'name': 'Aliss', 'message': 'Welcome, Calwen.'},
        {'name': 'Rytsen', 'message': 'Good hunting.'},
        {'name': 'Calia', 'message': 'Light guide you.'},
    ]
    with patch.object(
        chatter_guild_login,
        'calculate_dynamic_delay',
        side_effect=[7.0, 8.0],
    ) as pacing:
        delays = (
            chatter_guild_login._greeting_delays(
                messages, {}
            )
        )

    assert delays == [0.0, 7.0, 15.0]
    assert pacing.call_count == 2
    assert all(
        call.kwargs['responsive'] is False
        for call in pacing.call_args_list
    )


def test_multi_prompt_requires_distinct_short_lines():
    prompt, names = (
        chatter_guild_login._build_multi_prompt(
            [
                _candidate(101, 'Aliss'),
                _candidate(102, 'Rytsen'),
            ],
            'Keepers',
            'Alliance',
            'Calwen',
            True,
            100,
        )
    )

    assert names == ['Aliss', 'Rytsen']
    assert "clearly different" in prompt.user_prompt
    assert "3 to 12 words" in prompt.user_prompt
    assert "Hard limit: 100" in prompt.user_prompt
    assert "do not repeat the player's name" in (
        prompt.user_prompt
    )


def test_stale_session_skips_before_generation():
    statuses = []
    with (
        patch.object(
            chatter_guild_login,
            '_session_is_current',
            return_value=False,
        ),
        patch.object(
            chatter_guild_login,
            '_mark_event',
            side_effect=lambda db, event_id, status:
                statuses.append((event_id, status)),
        ),
        patch.object(
            chatter_guild_login,
            'call_llm',
        ) as call,
    ):
        result = (
            chatter_guild_login
            .process_guild_login_greeting_event(
                object(),
                object(),
                {},
                _event(),
            )
        )

    assert result is False
    assert statuses == [(91, 'skipped')]
    call.assert_not_called()


class _CompletionCursor:
    def __init__(self, db):
        self.db = db
        self.rowcount = 0

    def execute(self, query, params=None):
        if "SET status = 'completed'" in query:
            self.rowcount = 1 if self.db.current else 0
        elif "UPDATE llm_chatter_messages" in query:
            self.db.consumed = True


class _CompletionDb:
    def __init__(self, current: bool):
        self.current = current
        self.consumed = False
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return _CompletionCursor(self)

    def commit(self):
        self.commits += 1


def test_cancelled_event_consumes_racing_output():
    current = _CompletionDb(True)
    assert chatter_guild_login._complete_event_if_current(
        current, 91
    ) is True
    assert current.consumed is False

    cancelled = _CompletionDb(False)
    assert chatter_guild_login._complete_event_if_current(
        cancelled, 91
    ) is False
    assert cancelled.consumed is True
    assert cancelled.commits == 1


def test_multi_greeting_inserts_native_guild_rows():
    db = object()
    inserted = []
    statuses = []
    responders = [
        _candidate(101, 'Aliss'),
        _candidate(102, 'Rytsen'),
    ]
    messages = [
        {
            'name': 'Aliss',
            'message': 'Welcome, Calwen.',
        },
        {
            'name': 'Rytsen',
            'message': 'Good hunting today.',
        },
    ]

    with (
        patch.object(
            chatter_guild_login,
            '_session_is_current',
            return_value=True,
        ) as session_check,
        patch.object(
            chatter_guild_login,
            '_choose_responder_count',
            return_value=2,
        ),
        patch.object(
            chatter_guild_login,
            '_select_responders',
            return_value=responders,
        ),
        patch.object(
            chatter_guild_login,
            '_generate_multi',
            return_value=messages,
        ),
        patch.object(
            chatter_guild_login,
            '_greeting_delays',
            return_value=[0.0, 9.0],
        ),
        patch.object(
            chatter_guild_login,
            'insert_chat_message',
            side_effect=lambda db, **kwargs:
                inserted.append(kwargs),
        ),
        patch.object(
            chatter_guild_login,
            '_mark_event',
            side_effect=lambda db, event_id, status:
                statuses.append((event_id, status)),
        ),
        patch.object(
            chatter_guild_login,
            '_complete_event_if_current',
            return_value=True,
        ) as complete,
        patch.object(
            chatter_guild_login.random,
            'randint',
            return_value=100,
        ),
    ):
        result = (
            chatter_guild_login
            .process_guild_login_greeting_event(
                db,
                object(),
                {},
                _event(),
            )
        )

    assert result is True
    assert session_check.call_count == 2
    assert len(inserted) == 2
    assert [row['delay_seconds'] for row in inserted] == [
        0.0,
        9.0,
    ]
    assert [row['sequence'] for row in inserted] == [
        0,
        1,
    ]
    assert all(
        row['channel'] == 'guild'
        and row['owner_subsystem'] == 'guild'
        and row['player_guid'] == 7
        for row in inserted
    )
    assert statuses == []
    complete.assert_called_once_with(db, 91)


def test_long_greeting_is_trimmed_at_word_boundary():
    text = (
        "Welcome back to the guild, Calwen, may your "
        "travels across distant lands bring honor and "
        "many remarkable stories to us all."
    )
    trimmed = chatter_guild_login._trim_greeting(
        text,
        60,
    )

    assert len(trimmed) <= 60
    assert trimmed.endswith('.')
    assert "travels" in trimmed


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(
        f"{len(tests)} guild login greeting tests passed"
    )
