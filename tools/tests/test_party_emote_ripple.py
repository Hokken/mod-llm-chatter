#!/usr/bin/env python3
"""Party emote ripple checks (Python side).

When the player emotes at a party bot, another nearby party bot may
chime in (target_type 'party_bot') as a single comment or a two-line
exchange with the targeted bot, and both emote handlers note their
delivered line in the party conversation thread. Other observer
targets are unchanged.

The C++ routing (observer call, proximity witnesses, mood spread) is
not exercised here; it needs a server build.

Run directly from the module root:
  python tools/tests/test_party_emote_ripple.py
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

import chatter_emote_observer as obs  # noqa: E402
import chatter_emote_reaction as react  # noqa: E402
import chatter_threads as th  # noqa: E402

GID = 7
CONFIG = {'LLMChatter.ChatterMode': 'roleplay'}


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


def _event(target_type='party_bot', **extra):
    data = {
        'bot_guid': 102, 'bot_name': 'Mira', 'bot_class': 8,
        'bot_race': 1, 'bot_gender': 1, 'bot_level': 40,
        'emote_name': 'hug', 'player_name': 'Calwen',
        'target_type': target_type, 'target_name': 'Gruk',
        'target_guid': 101, 'npc_rank': 0, 'npc_type': 0,
        'npc_subname': '', 'custom_emote': 0, 'group_id': GID,
    }
    data.update(extra)
    return {'id': 55, 'extra_data': json.dumps(data)}


def _traits(db, group_id, bot_guid):
    return {
        101: {'traits': ['gruff', 'loyal', 'dry'], 'tone': 'terse'},
        102: {'traits': ['warm', 'bookish', 'curious'],
              'tone': 'bright'},
    }.get(bot_guid)


class _Run:
    """Patch the observer handler's collaborators and record calls."""

    def __init__(self, exchange_chance, llm_response=None,
                 traits=_traits):
        self.config = dict(CONFIG, **{
            'LLMChatter.EmoteReactions.PartyObserverExchangeChance':
                exchange_chance,
        })
        self.single_prompts = []
        self.inserts = []
        self.llm_response = llm_response
        self.patches = [
            patch.object(obs, 'should_defer_party_generation',
                         return_value=False),
            patch.object(obs, 'get_bot_traits', side_effect=traits),
            patch.object(obs, 'build_gear_context', return_value=''),
            patch.object(obs, 'build_party_context', return_value=''),
            patch.object(obs, '_store_chat'),
            patch.object(obs, '_mark_event'),
            patch.object(obs, 'run_single_reaction',
                         side_effect=self._single),
            patch.object(obs, 'call_llm',
                         side_effect=lambda *a, **k: self.llm_response),
            patch.object(obs, 'insert_chat_message',
                         side_effect=self._insert),
            patch.object(obs, 'calculate_dynamic_delay',
                         return_value=1),
        ]

    def _single(self, db, client, config, prompt, **kwargs):
        self.single_prompts.append(_text(prompt))
        return {'ok': True, 'message': 'Aww.', 'message_id': 9}

    def _insert(self, db, guid, name, text, **kwargs):
        self.inserts.append((guid, name, text, kwargs['sequence']))
        return 100 + len(self.inserts)

    def run(self, event):
        for p in self.patches:
            p.start()
        try:
            return obs.handle_emote_observer(
                None, None, self.config, event,
            )
        finally:
            for p in self.patches:
                p.stop()


def test_party_bot_observer_single_comment():
    th.clear_all()
    run = _Run(exchange_chance=0)
    assert run.run(_event()) is True
    assert not run.inserts
    prompt = run.single_prompts[0]
    assert 'at your party member Gruk' in prompt
    assert '/hug' in prompt
    event = th.snapshot(GID).interruptions[-1]
    assert event['label'] == 'emote observer'
    assert event['message_id'] == 9


def test_party_bot_observer_two_line_exchange():
    th.clear_all()
    reply = json.dumps([
        {'speaker': 'Mira', 'message': 'Gruk, you are blushing.'},
        {'speaker': 'Gruk', 'message': 'I do not blush.'},
    ])
    run = _Run(exchange_chance=100, llm_response=reply)
    assert run.run(_event()) is True
    assert not run.single_prompts
    assert [(g, n, s) for g, n, _, s in run.inserts] == [
        (102, 'Mira', 0), (101, 'Gruk', 1),
    ]
    notes = th.snapshot(GID).interruptions
    assert [n['speaker'] for n in notes] == ['Mira', 'Gruk']
    assert [n['message_id'] for n in notes] == [101, 102]


def test_exchange_falls_back_to_single_comment():
    for response in ('', 'not json',
                     '[{"speaker":"Stranger","message":"x"}]'):
        th.clear_all()
        run = _Run(exchange_chance=100, llm_response=response)
        assert run.run(_event()) is True
        assert not run.inserts, response
        assert len(run.single_prompts) == 1
    # No traits row for the targeted bot: single comment too.
    run = _Run(exchange_chance=100, llm_response='[]',
               traits=lambda db, g, guid: (
                   None if guid == 101 else _traits(db, g, guid)))
    assert run.run(_event()) is True
    assert len(run.single_prompts) == 1


def test_other_observer_targets_are_unchanged():
    th.clear_all()
    run = _Run(exchange_chance=100)
    run.run(_event(target_type='creature', target_name='Hogger',
                   target_guid=0))
    assert not run.inserts
    assert 'party member' not in run.single_prompts[0]
    assert 'Hogger' in run.single_prompts[0]
    run = _Run(exchange_chance=100)
    run.run(_event(target_type='none', target_name=''))
    assert not run.inserts and len(run.single_prompts) == 1


def test_directed_reaction_notes_the_thread():
    th.clear_all()
    event = {'id': 56, 'extra_data': json.dumps({
        'bot_guid': 101, 'bot_name': 'Gruk', 'bot_class': 1,
        'bot_race': 2, 'bot_gender': 0, 'bot_level': 40,
        'emote_name': 'hug', 'mirror_emote': '',
        'player_name': 'Calwen', 'directed': True,
        'custom_emote': 0, 'group_id': GID,
    })}
    patches = [
        patch.object(react, 'get_bot_traits', side_effect=_traits),
        patch.object(react, 'build_gear_context', return_value=''),
        patch.object(react, 'build_party_context', return_value=''),
        patch.object(react, '_store_chat'),
        patch.object(react, '_mark_event'),
        patch.object(react, 'run_single_reaction', return_value={
            'ok': True, 'message': 'Hmph. Fine.', 'message_id': 77,
        }),
    ]
    extra = [
        patch.object(react, name, return_value=False)
        for name in ('should_defer_party_generation',)
        if hasattr(react, name)
    ]
    for p in patches + extra:
        p.start()
    try:
        assert react.handle_emote_reaction(
            None, None, CONFIG, event) is True
    finally:
        for p in patches + extra:
            p.stop()
    note = th.snapshot(GID).interruptions[-1]
    assert note['label'] == 'emote reaction'
    assert note['message_id'] == 77


def test_exchange_chance_bounds():
    assert obs._party_exchange_roll({
        'LLMChatter.EmoteReactions.PartyObserverExchangeChance': 0,
    }) is False
    assert obs._party_exchange_roll({
        'LLMChatter.EmoteReactions.PartyObserverExchangeChance': 100,
    }) is True
    assert obs._party_exchange_roll({
        'LLMChatter.EmoteReactions.PartyObserverExchangeChance': 'x',
    }) is False


def test_party_bot_prompt_uses_persona_boundary():
    """Normal mode never sees stored roleplay identity; a missing
    tone falls back to the bot's deterministic tone."""
    from chatter_persona import fallback_tone
    normal = _text(obs._build_party_bot_prompt(
        'Mira', 'Human', 'Mage', 'female', 'Calwen', 'hug',
        'Gruk', 'affection',
        traits=['WARSONG_ROLEPLAY_TRAIT'],
        stored_tone='ANCIENT_ORC_TONE', mode='normal', bot_guid=102,
    ))
    assert 'WARSONG_ROLEPLAY_TRAIT' not in normal
    assert 'ANCIENT_ORC_TONE' not in normal
    rp = _text(obs._build_party_bot_prompt(
        'Mira', 'Human', 'Mage', 'female', 'Calwen', 'hug',
        'Gruk', 'affection',
        traits=['warm', 'bookish', 'curious'], stored_tone=None,
        mode='roleplay', bot_guid=102,
    ))
    expected = fallback_tone(102, 'Mira', 'roleplay')
    assert f'Your tone: {expected}' in rp
    again = _text(obs._build_party_bot_prompt(
        'Mira', 'Human', 'Mage', 'female', 'Calwen', 'wave',
        'Gruk', 'greeting',
        traits=['warm', 'bookish', 'curious'], stored_tone=None,
        mode='roleplay', bot_guid=102,
    ))
    assert f'Your tone: {expected}' in again


def test_malformed_exchanges_fall_back_to_one_comment():
    cases = {
        'target only': [
            {'speaker': 'Gruk', 'message': 'I do not blush.'},
        ],
        'reversed': [
            {'speaker': 'Gruk', 'message': 'I do not blush.'},
            {'speaker': 'Mira', 'message': 'You are blushing.'},
        ],
        'duplicate': [
            {'speaker': 'Mira', 'message': 'Look at him.'},
            {'speaker': 'Mira', 'message': 'So red.'},
        ],
        'empty after cleanup': [
            {'speaker': 'Mira', 'message': '*waves*'},
            {'speaker': 'Gruk', 'message': 'I do not blush.'},
        ],
        'too many': [
            {'speaker': 'Mira', 'message': 'Look at him.'},
            {'speaker': 'Gruk', 'message': 'Hmph.'},
            {'speaker': 'Mira', 'message': 'So red.'},
        ],
    }
    for label, reply in cases.items():
        th.clear_all()
        run = _Run(exchange_chance=100, llm_response=json.dumps(reply))
        assert run.run(_event()) is True, label
        assert not run.inserts, label
        assert len(run.single_prompts) == 1, label


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    th.clear_all()
    print(f"{len(tests)} party emote ripple checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
