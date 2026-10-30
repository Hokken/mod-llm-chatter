#!/usr/bin/env python3
"""Multi-bot party replies to a real player carry a response contract.

Regression: build_player_msg_conversation_prompt() returned a bare string,
so structured dispatch refused it (contract_error) and the player's party
message got no reply.
"""

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

from chatter_group_prompts import (  # noqa: E402
    build_player_msg_conversation_prompt,
)
from chatter_shared import (  # noqa: E402
    PromptParts,
    build_brief_casual_repair_prompt,
)
from chatter_structured import validate_and_normalize  # noqa: E402

GRUK = {'guid': 101, 'name': 'Gruk', 'race': 'Orc',
        'class': 'Warrior', 'level': 40, 'gender': 'male'}
MIRA = {'guid': 102, 'name': 'Mira', 'race': 'Human',
        'class': 'Mage', 'level': 40, 'gender': 'female'}
TRAITS = {'Gruk': ['gruff'], 'Mira': ['curious']}


def _build(mode='normal', **kwargs):
    return build_player_msg_conversation_prompt(
        [GRUK, MIRA], TRAITS, 'Calwen',
        'Fancy doing anything interesting today guys?', mode, **kwargs,
    )


def test_prompt_carries_a_conversation_contract():
    for mode in ('normal', 'roleplay'):
        prompt = _build(mode)
        assert isinstance(prompt, PromptParts)
        assert not prompt.contract_conflict
        contract = prompt.response_contract
        assert contract.kind == 'conversation'
        assert contract.speaker_names == ('Gruk', 'Mira')
        assert contract.message_count == 2
        assert contract.emote
        assert contract.action == 'optional'
        assert not contract.emote_only
        assert prompt.structured_system_prompt


def test_action_and_brief_casual_options_shape_the_contract():
    no_action = _build(allow_action=False).response_contract
    assert no_action.action == 'none'
    brief = _build(allow_action=False, brief_casual=True).response_contract
    assert brief.emote_only and brief.action == 'none'


def test_contract_survives_gender_line_and_brief_repair():
    prompt = _build(allow_action=False, brief_casual=True)
    # with_party_genders() appends a plain line.
    gendered = prompt + '\nGenders: Gruk is male, Mira is female.'
    repaired = build_brief_casual_repair_prompt(gendered)
    for wrapped in (gendered, repaired):
        assert wrapped.response_contract == prompt.response_contract
        assert not wrapped.contract_conflict


def test_legacy_text_keeps_the_party_json_block():
    prompt = _build()
    assert 'Respond with EXACTLY 2 messages in JSON' in str(prompt)
    assert 'Respond with EXACTLY' in prompt.system_prompt
    assert 'Respond with EXACTLY' not in prompt.user_prompt


def test_optional_action_may_be_null_in_a_structured_reply():
    contract = _build().response_contract
    raw = json.dumps({'messages': [
        {'speaker': 'Gruk', 'message': 'Hunt something big.',
         'emote': 'nod', 'action': None},
        {'speaker': 'Mira', 'message': 'Or read something old.',
         'emote': None, 'action': 'adjusts her robe'},
    ]})
    assert validate_and_normalize(raw, contract)
