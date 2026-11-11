#!/usr/bin/env python3
"""Checks for the party player-message guards (issue #93).

Covers the one-line-per-speaker / copied-line guard on player-message
conversations and the null-addressee fallback that skips the bot that
spoke last.

Run directly from the module root:
  python tools/tests/test_party_player_msg_guards.py
"""

import importlib
import json
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
        attribute = 'Anthropic' if dependency == 'anthropic' else 'OpenAI'
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

import chatter_group  # noqa: E402
import chatter_group_handlers as handlers  # noqa: E402


# ---------------------------------------------------------------------
# Conversation guard: helpers
# ---------------------------------------------------------------------

def _names(messages):
    return [m['name'] for m in messages]


def test_first_line_per_speaker_keeps_first_occurrence():
    messages = [
        {'name': 'Avrii', 'message': 'Ready when you are.'},
        {'name': 'Eleney', 'message': 'Blades sharp.'},
        {'name': 'Avrii', 'message': 'Really, I am ready.'},
    ]
    kept = handlers._first_line_per_speaker(messages)
    assert _names(kept) == ['Avrii', 'Eleney'], kept
    assert kept[0]['message'] == 'Ready when you are.'
    assert handlers._first_line_per_speaker([]) == []


def test_speech_key_ignores_case_punctuation_and_action():
    key = handlers._delivered_speech_key
    assert key('Prête, allons-y !') == key('prête  allons-y')
    assert key('*nods* Ready.') == key('Ready.')
    assert key('Ready.') != key('Ready too.')
    assert key('') == ''


# ---------------------------------------------------------------------
# Conversation guard: handler level
# ---------------------------------------------------------------------

class _Cursor:
    def execute(self, *args, **kwargs):
        pass

    def fetchone(self):
        return {'class': 1, 'race': 1, 'level': 20, 'gender': 1}


class _DB:
    def cursor(self, *args, **kwargs):
        return _Cursor()


ADDRESSED = {
    'guid': 1, 'name': 'Avrii', 'class': 'Warrior', 'race': 'Human',
    'level': 20, 'trait1': 'a', 'trait2': 'b', 'trait3': 'c',
    'tone': None, 'backstory': '', 'travel_mode': '',
    'travel_context': 'on foot', 'travel_state': {},
}

ROWS = [
    {'bot_guid': 1, 'bot_name': 'Avrii'},
    {'bot_guid': 2, 'bot_name': 'Eleney'},
    {'bot_guid': 3, 'bot_name': 'Ateema'},
]


def _run_conversation(lines, brief_casual=False, fits=True,
                      repair_lines=None):
    inserted = []
    replies = [json.dumps(lines)]
    if repair_lines is not None:
        replies.append(json.dumps(repair_lines))

    def fake_call_llm(*args, **kwargs):
        return replies.pop(0)

    def fake_insert(db, guid, name, text, **kwargs):
        inserted.append((name, text, kwargs.get('emote')))

    passthrough = {
        'build_travel_state_from_row': lambda row: {},
        'format_travel_context': lambda state: '',
        'get_class_name': lambda value: 'Warrior',
        'get_race_name': lambda value: 'Human',
        'get_gender_label': lambda value: 'female',
        'get_character_guild_name': lambda db, guid: '',
        '_gate_conversation_backstories': lambda *a, **k: None,
        'attach_speaker_gear': lambda *a, **k: None,
        '_maybe_talent_context': lambda *a, **k: None,
        'get_character_info_by_name': lambda *a, **k: None,
        'build_player_msg_conversation_prompt': lambda **k: 'prompt',
        'same_guild_note': lambda *a, **k: '',
        'player_context_text': lambda *a, **k: '',
        'render_for_player_reply': lambda *a, **k: '',
        'with_party_genders': lambda prompt, *a, **k: prompt,
        'get_dungeon_flavor': lambda map_id: '',
        'build_zone_metadata': lambda **k: {},
        'get_zone_name': lambda *a: '',
        'get_zone_flavor': lambda *a: '',
        'get_subzone_name': lambda *a: '',
        'get_subzone_lore': lambda *a: '',
        'build_group_travel_metadata': lambda bots: {},
        'call_llm': fake_call_llm,
        'brief_casual_response_fits': lambda *a, **k: fits,
        'build_brief_casual_repair_prompt': lambda prompt: prompt,
        'strip_conversation_actions': lambda *a, **k: None,
        'calculate_dynamic_delay': lambda *a, **k: 1.0,
        'insert_chat_message': fake_insert,
        '_store_chat': lambda *a, **k: None,
    }
    with patch.multiple(handlers, **passthrough), \
            patch.object(handlers.random, 'randint', lambda a, b: 3), \
            patch.object(handlers.random, 'shuffle', lambda seq: None):
        ok = handlers.execute_player_msg_conversation(
            _DB(), object(), {}, 1, 7,
            dict(ADDRESSED), ROWS,
            'Minhalie', 'Les autres, prêts aussi ?', 'roleplay',
            '', [],
            brief_casual=brief_casual,
        )
    return ok, inserted


def test_handler_first_occurrence_consumed_even_when_copied():
    ok, inserted = _run_conversation([
        {'speaker': 'Avrii', 'message': 'Ready.'},
        {'speaker': 'Eleney', 'message': 'Ready.'},
        {'speaker': 'Eleney', 'message': 'Blades sharp.'},
    ])
    assert ok
    assert [(n, t) for n, t, _ in inserted] == [('Avrii', 'Ready.')], (
        inserted)


def test_handler_drops_copy_hidden_behind_action():
    ok, inserted = _run_conversation([
        {'speaker': 'Avrii', 'message': 'Ready.', 'action': 'nods'},
        {'speaker': 'Ateema', 'message': 'Ready.'},
        {'speaker': 'Eleney', 'message': 'Toujours prête.'},
    ])
    assert ok
    assert [(n, t) for n, t, _ in inserted] == [
        ('Avrii', '*nods* Ready.'), ('Eleney', 'Toujours prête.'),
    ], inserted


def test_handler_keeps_distinct_lines_and_text_whole():
    long_line = ('A long line that must stay whole, every single '
                 'word of it, all the way to the end.')
    ok, inserted = _run_conversation([
        {'speaker': 'Avrii', 'message': long_line},
        {'speaker': 'Eleney', 'message': 'Ready too.'},
        {'speaker': 'Ateema', 'message': 'Aye.'},
    ])
    assert ok
    assert [(n, t) for n, t, _ in inserted] == [
        ('Avrii', long_line), ('Eleney', 'Ready too.'),
        ('Ateema', 'Aye.'),
    ], inserted


def test_handler_emote_only_lines_are_not_compared():
    ok, inserted = _run_conversation([
        {'speaker': 'Avrii', 'message': '', 'emote': 'nod'},
        {'speaker': 'Eleney', 'message': '', 'emote': 'nod'},
    ], brief_casual=True)
    assert ok
    assert [n for n, _, _ in inserted] == ['Avrii', 'Eleney'], inserted


def test_handler_brief_path_keeps_first_line():
    ok, inserted = _run_conversation([
        {'speaker': 'Avrii', 'message': 'Ready.'},
        {'speaker': 'Eleney', 'message': 'Blades sharp.'},
        {'speaker': 'Avrii', 'message': 'Let us leave.'},
    ], brief_casual=True)
    assert ok
    assert [(n, t) for n, t, _ in inserted] == [
        ('Avrii', 'Ready.'), ('Eleney', 'Blades sharp.'),
    ], inserted


def test_handler_brief_repair_keeps_first_line():
    ok, inserted = _run_conversation(
        [
            {'speaker': 'Avrii', 'message': 'Ready.'},
            {'speaker': 'Eleney', 'message': 'Blades sharp.'},
        ],
        brief_casual=True, fits=False,
        repair_lines=[
            {'speaker': 'Avrii', 'message': 'Set.'},
            {'speaker': 'Eleney', 'message': 'Aye.'},
            {'speaker': 'Avrii', 'message': 'Let us leave.'},
        ],
    )
    assert ok
    assert [(n, t) for n, t, _ in inserted] == [
        ('Avrii', 'Set.'), ('Eleney', 'Aye.'),
    ], inserted


# ---------------------------------------------------------------------
# Null-addressee fallback
# ---------------------------------------------------------------------

BOTS = [
    {'bot_guid': 1, 'bot_name': 'Avrii'},
    {'bot_guid': 2, 'bot_name': 'Eleney'},
    {'bot_guid': 3, 'bot_name': 'Ateema'},
]


def test_fallback_skips_last_bot_speaker():
    history = [
        {'speaker_name': 'Minhalie', 'is_bot': 0,
         'message': 'Avrii, ready?'},
        {'speaker_name': 'Avrii', 'is_bot': 1, 'message': 'Ready.'},
        {'speaker_name': 'Minhalie', 'is_bot': 0,
         'message': 'Les autres, prêts aussi ?'},
    ]
    pool = chatter_group._fallback_responder_pool(BOTS, history)
    assert [b['bot_name'] for b in pool] == ['Eleney', 'Ateema'], pool


def test_fallback_keeps_all_without_bot_history():
    history = [
        {'speaker_name': 'Minhalie', 'is_bot': 0, 'message': 'hi'},
    ]
    assert chatter_group._fallback_responder_pool(BOTS, history) == BOTS
    assert chatter_group._fallback_responder_pool(BOTS, []) == BOTS
    assert chatter_group._fallback_responder_pool(BOTS, None) == BOTS


def test_fallback_keeps_single_bot():
    history = [{'speaker_name': 'Avrii', 'is_bot': 1, 'message': 'x'}]
    solo = BOTS[:1]
    assert chatter_group._fallback_responder_pool(solo, history) == solo


def test_fallback_ignores_departed_last_speaker():
    history = [{'speaker_name': 'Gone', 'is_bot': 1, 'message': 'x'}]
    assert chatter_group._fallback_responder_pool(BOTS, history) == BOTS


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} party player-message guard checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
