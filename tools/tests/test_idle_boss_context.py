#!/usr/bin/env python3
"""Idle party chatter lists a dungeon's bosses only some of the time.

Every idle prompt in a dungeon used to carry the same "Bosses here:"
line with the alphabetically first six names, which invites bots to
name-drop the same bosses again and again, and in a large instance
(Blackrock Depths has 18) always shows the same six. Now one roll per
idle request (LLMChatter.GroupChatter.IdleBossContextChance) decides
whether the list joins the prompt, as a random sample of up to six.
The dungeon itself always stays in the prompt, and the dungeon-entry
and spell-reaction prompts are unchanged.

Run directly from the module root:
  python tools/tests/test_idle_boss_context.py
"""

import importlib
import random
import re
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
from chatter_group import (  # noqa: E402
    build_idle_chatter_prompt,
    build_idle_conversation_prompt,
    pick_idle_boss_context,
)

MODULE_ROOT = TOOLS_DIR.parent
KEY = 'LLMChatter.GroupChatter.IdleBossContextChance'
DEADMINES = 36

BRD = [
    'Ambassador Flamelash', "Anger'rel", "Bael'Gar",
    'Emperor Dagran Thaurissan', 'Fineous Darkvire',
    'General Angerforge', 'Golem Lord Argelmach',
    'High Interrogator Gerstahn', 'Houndmaster Grebmar',
    'Hurley Blackbreath', 'Lord Incendius', 'Lord Roccor', 'Magmus',
    'Phalanx', 'Plugger Spazzring', 'Pyromancer Loregrain',
    'Ribbly Screwspigot', 'Warder Stilgiss',
]
DEADMINES_BOSSES = [
    'Captain Greenskin', 'Cookie', 'Edwin VanCleef', 'Gilnid',
    'Mr. Smite', "Rhahk'Zor",
]

GRUK = {
    'guid': 101, 'name': 'Gruk', 'race': 'Orc',
    'class': 'Warrior', 'level': 20, 'gender': 'male',
    'tone': 'gruff and terse',
}
MIRA = {
    'guid': 102, 'name': 'Mira', 'race': 'Human',
    'class': 'Mage', 'level': 20, 'gender': 'female',
    'tone': 'bookish and warm',
}
TRAITS = {
    'Gruk': ['brooding', 'loyal', 'sardonic'],
    'Mira': ['wide-eyed', 'bookish', 'gentle'],
}


class _KeepRandomState:
    """Seeded tests must not disturb other tests' randomness."""

    def __enter__(self):
        self._state = random.getstate()
        return self

    def __exit__(self, *exc):
        random.setstate(self._state)
        return False


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


# ------------------------------------------------------------
# The roll and the sample
# ------------------------------------------------------------
def test_chance_zero_never_and_hundred_always():
    with _KeepRandomState():
        random.seed(1)
        for _ in range(200):
            assert pick_idle_boss_context(BRD, {KEY: '0'}) == []
            assert pick_idle_boss_context(BRD, {KEY: '100'})


def test_sample_is_six_unique_names_and_varies():
    seen = set()
    with _KeepRandomState():
        for seed in range(20):
            random.seed(seed)
            picked = pick_idle_boss_context(BRD, {KEY: '100'})
            assert len(picked) == 6
            assert len(set(picked)) == 6
            assert set(picked) <= set(BRD)
            seen.update(picked)
    assert len(seen) > 6, 'not always the same six'
    assert seen != set(sorted(BRD)[:6])


def test_small_instance_shows_every_boss():
    with _KeepRandomState():
        random.seed(3)
        picked = pick_idle_boss_context(DEADMINES_BOSSES, {KEY: '100'})
    assert sorted(picked) == sorted(DEADMINES_BOSSES)


def test_cached_list_is_never_mutated():
    bosses = list(BRD)
    with _KeepRandomState():
        for seed in range(10):
            random.seed(seed)
            pick_idle_boss_context(bosses, {KEY: '100'})
    assert bosses == BRD


def test_no_bosses_means_no_roll():
    with patch.object(chatter_group.random, 'randint') as roll:
        assert pick_idle_boss_context([], {KEY: '100'}) == []
        assert pick_idle_boss_context(None, {KEY: '100'}) == []
    assert not roll.called


def test_default_and_invalid_config():
    """Missing or unparsable = 40; out of range is clamped."""
    def included(config, roll):
        with patch.object(chatter_group.random, 'randint',
                          return_value=roll):
            return bool(pick_idle_boss_context(BRD, config))

    for config in ({}, {KEY: 'abc'}, {KEY: None}):
        assert included(config, 40), config
        assert not included(config, 41), config
    assert not included({KEY: '-5'}, 1), 'clamped to 0: never'
    assert included({KEY: '500'}, 100), 'clamped to 100: always'


# ------------------------------------------------------------
# What reaches the prompt
# ------------------------------------------------------------
def _prompts(bosses, mode):
    single = _text(build_idle_chatter_prompt(
        GRUK, TRAITS['Gruk'], mode, map_id=DEADMINES,
        stored_tone=GRUK['tone'], dungeon_bosses=bosses,
    ))
    conv = _text(build_idle_conversation_prompt(
        [GRUK, MIRA], TRAITS, mode, None, map_id=DEADMINES,
        dungeon_bosses=bosses,
    ))
    return single, conv


def test_failed_roll_keeps_the_dungeon_and_drops_only_bosses():
    for mode in ('roleplay', 'normal'):
        for prompt in _prompts([], mode):
            # Normal mode names the instance ("inside The Deadmines").
            assert ('Dungeon context:' in prompt
                    or 'inside The Deadmines' in prompt), mode
            assert 'Bosses here' not in prompt, mode
            assert '\n\n\n' not in prompt, mode


def test_included_sample_is_listed_as_given():
    picked = ['Edwin VanCleef', 'Cookie', "Rhahk'Zor"]
    for mode in ('roleplay', 'normal'):
        for prompt in _prompts(picked, mode):
            assert 'Bosses here: ' + ', '.join(picked) in prompt, mode


# ------------------------------------------------------------
# Wiring and configuration
# ------------------------------------------------------------
def _source(name):
    return (TOOLS_DIR / name).read_text(encoding='utf-8')


def test_idle_path_rolls_and_other_prompts_do_not():
    group = _source('chatter_group.py')
    idle = group[group.index('def check_idle_group_chatter('):]
    idle = idle[:idle.index('\ndef ')]
    assert re.search(
        r'pick_idle_boss_context\(\s*get_dungeon_bosses\(db, map_id\),'
        r'\s*config,\s*\)', idle), 'idle path must roll'
    assert idle.count('get_dungeon_bosses(') == 1
    assert group.count('pick_idle_boss_context(') == 2, (
        'defined once, used once')

    prompts = _source('chatter_group_prompts.py')
    handlers = _source('chatter_group_handlers.py')
    assert 'dungeon_bosses = get_dungeon_bosses(db, map_id)' in prompts
    assert 'pick_idle_boss_context' not in prompts
    assert 'pick_idle_boss_context' not in handlers
    assert re.search(r'get_dungeon_bosses\(\s*ctx\[\'db\'\]', handlers)


def test_config_files_carry_the_key():
    def value(path):
        text = path.read_text(encoding='utf-8')
        found = re.findall(
            r'^LLMChatter\.GroupChatter\.IdleBossContextChance = (\d+)$',
            text, re.M)
        assert len(found) == 1, path
        return int(found[0])

    conf = MODULE_ROOT / 'conf'
    assert value(conf / 'mod_llm_chatter.conf.dist') == 40
    assert value(conf / 'presets' / 'mod_ll_chatter_quieter.conf.dist') == 25
    with patch.object(chatter_group.random, 'randint', return_value=40):
        assert pick_idle_boss_context(BRD, {}), 'code default is 40'


def main():
    tests = [
        test_chance_zero_never_and_hundred_always,
        test_sample_is_six_unique_names_and_varies,
        test_small_instance_shows_every_boss,
        test_cached_list_is_never_mutated,
        test_no_bosses_means_no_roll,
        test_default_and_invalid_config,
        test_failed_roll_keeps_the_dungeon_and_drops_only_bosses,
        test_included_sample_is_listed_as_given,
        test_idle_path_rolls_and_other_prompts_do_not,
        test_config_files_carry_the_key,
    ]
    for test in tests:
        test()
    print('%d idle boss context tests passed' % len(tests))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
