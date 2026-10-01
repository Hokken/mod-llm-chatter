#!/usr/bin/env python3
"""Brief casual length tiers vary reply size without losing brevity."""

import importlib
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

from chatter_general import (  # noqa: E402
    _build_general_followup_prompt,
    _build_general_response_prompt,
)
from chatter_shared import (  # noqa: E402
    BRIEF_CASUAL_TIERS,
    bound_brief_casual_response,
    brief_casual_response_fits,
    build_brief_casual_repair_prompt,
    build_conversational_scale_guidance,
    pick_brief_casual_tier,
)

WEIGHTS_KEY = 'LLMChatter.PlayerChat.BriefCasualLengthWeights'


def test_default_weights_pick_every_tier():
    picked = {pick_brief_casual_tier({}) for _ in range(500)}
    assert picked == set(BRIEF_CASUAL_TIERS)


def test_avoid_skips_previous_tier_when_possible():
    config = {WEIGHTS_KEY: '35,45,20'}
    for _ in range(200):
        assert pick_brief_casual_tier(config, avoid='short') != 'short'
    only_short = {WEIGHTS_KEY: '0,100,0'}
    assert pick_brief_casual_tier(only_short, avoid='short') == 'short'


def test_invalid_weights_fall_back_to_short():
    assert pick_brief_casual_tier({WEIGHTS_KEY: 'junk'}) == 'short'
    assert pick_brief_casual_tier({WEIGHTS_KEY: '0,0,0'}) == 'short'


def test_fits_and_bound_follow_the_tier():
    line = 'Auberdine has decent beds down by the docks, friend'
    assert not brief_casual_response_fits(line, tier='tiny')
    assert not brief_casual_response_fits(line)
    assert brief_casual_response_fits(line, tier='relaxed')
    bounded, _ = bound_brief_casual_response(line, tier='tiny')
    assert brief_casual_response_fits(bounded, tier='tiny')


def test_untiered_callers_keep_the_original_contract():
    guidance = build_conversational_scale_guidance(force_brief=True)
    assert 'Use 2-8 words and no more than 50 characters.' in guidance
    assert 'question' in guidance
    repair = build_brief_casual_repair_prompt('base')
    assert '2-8 words and no more than 50' in repair


def test_relaxed_tier_allows_a_light_question_back():
    guidance = build_conversational_scale_guidance(
        force_brief=True, brief_tier='relaxed',
    )
    assert 'Use 5-14 words and no more than 85 characters.' in guidance
    assert 'light question back' in guidance


def test_general_prompts_use_the_picked_tier():
    reply = str(_build_general_response_prompt(
        'Azu', 'Dwarf', 'Warrior', 20, 'male', None,
        'Karaez', 'evening friends', 'Darkshore', '', 'normal',
        brief_casual=True, brief_tier='tiny',
    ))
    assert 'Length: 1-4 words, no more than 30 characters.' in reply
    followup = str(_build_general_followup_prompt(
        'Binrii', 'Dwarf', 'Shaman', 20, 'male', None,
        'Azu', 'Aye.', 'Karaez', 'evening friends',
        'Darkshore', '', 'roleplay',
        brief_casual=True, brief_tier='relaxed',
    ))
    assert 'Length: 5-14 words, no more than 85 characters.' in followup
