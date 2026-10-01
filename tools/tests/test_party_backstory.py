#!/usr/bin/env python3
"""Party backstory checks (roleplay only, config-gated).

Covers the shared renderer and gate, party event reactions through
the handler pipeline, replies to the player, and multi-bot party
conversations (gating per speaker and rendering through the cast).

Run directly from the module root:
  python tools/tests/test_party_backstory.py
"""

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

import chatter_group_handlers as handlers  # noqa: E402
import chatter_handler_pipeline as pipeline  # noqa: E402
import chatter_threads  # noqa: E402
from chatter_group_prompts import (  # noqa: E402
    build_player_msg_conversation_prompt,
    build_player_response_prompt,
)
from chatter_persona import (  # noqa: E402
    Persona,
    build_persona_block,
    format_backstory_block,
    party_reaction_backstory,
)

STORY = 'Deserted the Warsong after Ashenvale; still carries the guilt.'
RP = {'LLMChatter.ChatterMode': 'roleplay',
      'LLMChatter.Backstory.PartyReactionChance': 100}
NORMAL = {'LLMChatter.ChatterMode': 'normal',
          'LLMChatter.Backstory.PartyReactionChance': 100}
GRUK = {'guid': 101, 'name': 'Gruk', 'race': 'Orc',
        'class': 'Warrior', 'level': 40, 'gender': 'male'}
MIRA = {'guid': 102, 'name': 'Mira', 'race': 'Human',
        'class': 'Mage', 'level': 40, 'gender': 'female'}


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


# ------------------------------------------------------------
# Renderer and gate
# ------------------------------------------------------------
def test_gate_boundaries():
    assert party_reaction_backstory(RP, STORY, 'roleplay') == STORY
    assert party_reaction_backstory(RP, STORY, 'normal') == ''
    assert party_reaction_backstory(RP, '', 'roleplay') == ''
    assert party_reaction_backstory(RP, None, 'roleplay') == ''
    off = dict(RP, **{'LLMChatter.Backstory.Enable': 0})
    assert party_reaction_backstory(off, STORY, 'roleplay') == ''
    zero = dict(RP, **{'LLMChatter.Backstory.PartyReactionChance': 0})
    assert party_reaction_backstory(zero, STORY, 'roleplay') == ''
    bad = dict(RP, **{'LLMChatter.Backstory.PartyReactionChance': 'x'})
    assert party_reaction_backstory(bad, STORY, 'roleplay') == ''
    half = dict(RP, **{'LLMChatter.Backstory.PartyReactionChance': 50})
    with patch('chatter_persona.random.randint', return_value=50):
        assert party_reaction_backstory(half, STORY, 'roleplay') == STORY
    with patch('chatter_persona.random.randint', return_value=51):
        assert party_reaction_backstory(half, STORY, 'roleplay') == ''


def test_one_backstory_wording_everywhere():
    block = format_backstory_block(STORY, 'roleplay')
    assert STORY in block and block.startswith('<backstory>')
    assert format_backstory_block(STORY, 'normal') == ''
    persona = build_persona_block(
        Persona('Gruk', ('gruff',), 'terse', STORY), 'roleplay',
    )
    assert block in persona


# ------------------------------------------------------------
# Event reactions through the pipeline
# ------------------------------------------------------------
def _run_event(config, backstory=STORY):
    captured = {}

    def fake_reaction(db, client, cfg, prompt, **kwargs):
        captured['prompt'] = _text(prompt)
        return {'ok': True, 'message': 'Hm.', 'message_id': None}

    patches = [
        patch.object(pipeline, 'get_bot_traits', return_value={
            'traits': ['gruff'], 'tone': 'terse',
            'backstory': backstory,
        }),
        patch.object(pipeline, 'build_gear_context', return_value=''),
        patch.object(pipeline, '_get_recent_chat', return_value=[]),
        patch.object(pipeline, '_maybe_talent_context',
                     return_value=None),
        patch.object(pipeline, 'run_single_reaction',
                     side_effect=fake_reaction),
        patch.object(pipeline, '_store_chat'),
        patch.object(pipeline, '_mark_event'),
        patch.object(pipeline, 'update_bot_mood'),
    ]
    for p in patches:
        p.start()
    try:
        pipeline.run_group_handler(
            None, None, config, {'id': 1},
            event_type_label='bot_group_kill',
            extract_fields=lambda ed: {},
            build_prompt=lambda ctx: 'Say something about the kill.',
            pre_parsed_extra={
                'bot_guid': 101, 'bot_name': 'Gruk', 'group_id': 7,
                'bot_class': 1, 'bot_race': 2,
            },
        )
    finally:
        for p in patches:
            p.stop()
        chatter_threads.clear_all()
    return captured['prompt']


def test_event_reactions_carry_backstory_in_roleplay_only():
    assert STORY in _run_event(RP)
    assert STORY not in _run_event(NORMAL)
    zero = dict(RP, **{'LLMChatter.Backstory.PartyReactionChance': 0})
    assert STORY not in _run_event(zero)
    assert '<backstory>' not in _run_event(RP, backstory=None)


# ------------------------------------------------------------
# Replies to the player
# ------------------------------------------------------------
def test_player_replies_carry_backstory_except_brief_casual():
    reply = _text(build_player_response_prompt(
        GRUK, ['gruff'], 'Calwen', 'where are you from?', 'roleplay',
        backstory=STORY,
    ))
    assert STORY in reply
    brief = _text(build_player_response_prompt(
        GRUK, ['gruff'], 'Calwen', 'lol', 'roleplay',
        backstory=STORY, brief_casual=True,
    ))
    assert STORY not in brief
    normal = _text(build_player_response_prompt(
        GRUK, ['gruff'], 'Calwen', 'hi', 'normal', backstory=STORY,
    ))
    assert STORY not in normal


# ------------------------------------------------------------
# Multi-bot party conversations
# ------------------------------------------------------------
def test_conversation_speakers_are_gated_and_rendered():
    bots = [dict(GRUK, backstory=STORY),
            dict(MIRA, backstory='A Dalaran apprentice.')]
    handlers._gate_conversation_backstories(bots, RP, 'roleplay')
    prompt = _text(build_player_msg_conversation_prompt(
        bots, {'Gruk': ['gruff'], 'Mira': ['curious']}, 'Calwen',
        'tell me about yourselves', 'roleplay',
    ))
    assert '<backstories>' in prompt
    assert STORY in prompt and 'A Dalaran apprentice.' in prompt

    skipped = [dict(GRUK, backstory=STORY)]
    handlers._gate_conversation_backstories(
        skipped, RP, 'roleplay', skip=True,
    )
    assert skipped[0]['backstory'] == ''
    normal = [dict(GRUK, backstory=STORY)]
    handlers._gate_conversation_backstories(normal, RP, 'normal')
    assert normal[0]['backstory'] == ''


class _Cursor:
    def __init__(self):
        self.row = None

    def execute(self, query, params=None):
        if 'FROM llm_group_bot_traits' in query:
            assert 'backstory' in query
            name = params[1]
            self.row = {
                'bot_guid': 101 if name == 'Gruk' else 102,
                'trait1': 'a', 'trait2': 'b', 'trait3': 'c',
                'tone': 'x',
                'backstory': STORY if name == 'Gruk' else '',
            }
        elif 'FROM characters' in query:
            self.row = {'class': 1, 'race': 2, 'level': 40,
                        'gender': 0}

    def fetchone(self):
        return self.row


class _DB:
    def cursor(self, *args, **kwargs):
        return _Cursor()


def test_quest_conversation_picker_gates_backstory():
    with patch.object(handlers, 'attach_speaker_gear'):
        bots, _, _ = handlers._quest_conversation_pick_bots(
            _DB(), 7, 'Gruk', ['Gruk', 'Mira'], RP,
        )
        by_name = {b['name']: b['backstory'] for b in bots}
        assert by_name == {'Gruk': STORY, 'Mira': ''}
        bots, _, _ = handlers._quest_conversation_pick_bots(
            _DB(), 7, 'Gruk', ['Gruk', 'Mira'], NORMAL,
        )
        assert all(b['backstory'] == '' for b in bots)


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} party backstory checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
