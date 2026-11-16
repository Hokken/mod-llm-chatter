#!/usr/bin/env python3
"""Group composition comments read real roles (issue #97).

A bot said "careful without a main healer" while the player was a Holy
Priest: the composition summary counted only bots, guessed their roles
from class, and the prompt then stated "There is no dedicated healer."
Now every current group member counts: bots by their stored playerbot
role, everyone else by talent spec. A missing tank or healer is stated
only when the roster is complete and every role is known.

Run directly from the module root:
  python tools/tests/test_group_composition_roles.py
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

import chatter_db  # noqa: E402
import chatter_group  # noqa: E402
from chatter_class_style import talent_spec_role  # noqa: E402
from chatter_group import (  # noqa: E402
    _build_composition_comment_prompt,
    _get_group_role_summary,
    _maybe_comment_on_composition,
)
from chatter_group_state import get_group_roster  # noqa: E402

WARRIOR, PALADIN, PRIEST, DK, SHAMAN, MAGE, DRUID = 1, 2, 5, 6, 7, 8, 11
PLAYER = 100
NO_HEALER = "There is no dedicated healer."
NO_TANK = "There is no dedicated tank."


# -- fakes ---------------------------------------------------------------

class _Cursor:
    def __init__(self, db):
        self._db = db
        self._rows = []

    def execute(self, sql, params=None):
        if self._db.fail:
            raise RuntimeError("db down")
        if 'FROM group_member gm' in sql:
            self._rows = [
                {
                    'guid': m['guid'], 'name': m['name'],
                    'class_id': m['class_id'], 'level': 80,
                    'traits_guid': (
                        m['guid'] if m.get('tracked') else None
                    ),
                    'role': m.get('role'),
                }
                for m in self._db.members
            ]
        elif 'gm.memberGuid IS NULL' in sql:
            self._rows = [
                {'bot_guid': guid} for guid in self._db.unconfirmed
            ]
        else:
            self._rows = []

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _Db:
    def __init__(self, members, unconfirmed=(), fail=False):
        self.members = members
        self.unconfirmed = list(unconfirmed)
        self.fail = fail

    def cursor(self, dictionary=False):
        return _Cursor(self)


def _bot(guid, name, class_id, role):
    return {'guid': guid, 'name': name, 'class_id': class_id,
            'tracked': True, 'role': role}


def _human(guid, name, class_id):
    return {'guid': guid, 'name': name, 'class_id': class_id,
            'tracked': False}


def _talents(by_guid):
    """Patch the talent reader with {guid: tree_totals}."""
    return patch.object(
        chatter_db, 'get_character_talents',
        lambda db, guid: {'talents': [],
                          'tree_totals': by_guid.get(guid, {})},
    )


def _summary(db, talents, player_guid=PLAYER, bot_guids=()):
    with _talents(talents):
        return _get_group_role_summary(
            db, 1, player_guid, bot_guids
        )


def _prompt(role_summary, role_info, mode='normal', speaker_role=None):
    bot = {'guid': 11, 'name': 'Lyra', 'class': 'Mage',
           'race': 'Human', 'level': 30, 'gender': 'female'}
    return _build_composition_comment_prompt(
        bot, ['calm', 'witty', 'curious'], mode, role_summary,
        role_info, player_name='Rob', stored_tone='dry',
        speaker_role=speaker_role,
    )


DPS_BOTS = [
    _bot(11, 'Lyra', MAGE, 'ranged_dps'),
    _bot(12, 'Thrag', WARRIOR, 'melee_dps'),
]


# -- talent_spec_role ----------------------------------------------------

def test_spec_role_healing_and_tank_trees():
    cases = [
        ('Priest', 'Holy', 'healer'), ('Priest', 'Discipline', 'healer'),
        ('Priest', 'Shadow', 'dps'), ('Paladin', 'Holy', 'healer'),
        ('Paladin', 'Protection', 'tank'),
        ('Paladin', 'Retribution', 'dps'),
        ('Shaman', 'Restoration', 'healer'),
        ('Druid', 'Restoration', 'healer'), ('Druid', 'Balance', 'dps'),
        ('Warrior', 'Protection', 'tank'), ('Warrior', 'Fury', 'dps'),
        ('Mage', 'Frost', 'dps'),
    ]
    for class_name, tree, expected in cases:
        with _talents({7: {tree: 31, 'Other': 5}}):
            assert talent_spec_role(object(), 7, class_name) == expected, (
                class_name, tree)


def test_spec_role_unknown_cases():
    unknown = [
        ('Death Knight', {'Frost': 51}),     # DK tank via presence
        ('Death Knight', {'Blood': 51}),
        ('Druid', {'Feral Combat': 51}),     # bear or cat
        ('Priest', {}),                      # no talents (under 10)
        ('Priest', {'Holy': 20, 'Shadow': 20}),  # tie
        ('Mage', {'Holy': 31}),              # tree not of this class
        ('Warrior', {'Unknown': 31}),        # unsupported name
    ]
    for class_name, totals in unknown:
        with _talents({7: totals}):
            assert talent_spec_role(object(), 7, class_name) is None, (
                class_name, totals)
    with _talents({7: {'Holy': 31}}):
        assert talent_spec_role(None, 7, 'Priest') is None
        assert talent_spec_role(object(), 7, '') is None


def test_spec_role_failed_lookup_is_unknown():
    def boom(db, guid):
        raise RuntimeError("lookup failed")
    with patch.object(chatter_db, 'get_character_talents', boom):
        assert talent_spec_role(object(), 7, 'Priest') is None


# -- the reported case and roles -------------------------------------------

def test_holy_priest_player_counts_as_healer():
    db = _Db([_human(PLAYER, 'Rob', PRIEST)] + DPS_BOTS)
    summary, info = _summary(db, {PLAYER: {'Holy': 41}}, bot_guids=[12])
    assert info['has_healer'] and info['roles_known']
    assert 'Rob (Light Priest, healing spec)' in summary
    assert NO_HEALER not in _prompt(summary, info)
    assert NO_TANK in _prompt(summary, info)


def test_protection_warrior_player_counts_as_tank():
    db = _Db([_human(PLAYER, 'Rob', WARRIOR)] + DPS_BOTS)
    summary, info = _summary(db, {PLAYER: {'Protection': 41}})
    assert info['has_tank'] and info['roles_known']
    assert NO_TANK not in _prompt(summary, info)
    assert NO_HEALER in _prompt(summary, info)


def test_bots_use_their_stored_role_not_class():
    db = _Db([
        _human(PLAYER, 'Rob', MAGE),
        _bot(11, 'Aldric', PALADIN, 'tank'),
        _bot(12, 'Fern', DRUID, 'healer'),
    ])
    summary, info = _summary(db, {PLAYER: {'Fire': 41}})
    assert info['has_tank'] and info['has_healer']
    assert 'Aldric (Paladin, tank)' in summary
    assert 'hybrid' not in summary

    db = _Db([
        _human(PLAYER, 'Rob', MAGE),
        _bot(11, 'Thrag', WARRIOR, 'melee_dps'),
        _bot(12, 'Vex', PRIEST, 'dps'),
    ])
    summary, info = _summary(db, {PLAYER: {'Fire': 41}})
    assert not info['has_tank'] and not info['has_healer']
    assert info['roles_known']
    prompt = _prompt(summary, info)
    assert NO_TANK in prompt and NO_HEALER in prompt


def test_unknown_bot_role_blocks_absence_claims():
    db = _Db([_human(PLAYER, 'Rob', MAGE),
              _bot(11, 'Lyra', MAGE, 'ranged_dps'),
              _bot(12, 'Odd', WARRIOR, None)])
    summary, info = _summary(db, {PLAYER: {'Fire': 41}})
    assert not info['roles_known']
    assert 'Odd (Warrior, role unknown)' in summary
    prompt = _prompt(summary, info)
    assert NO_TANK not in prompt and NO_HEALER not in prompt
    assert "do not claim the group has or lacks" in prompt


def test_death_knight_and_feral_players_are_unknown():
    for class_id, totals in ((DK, {'Frost': 51}), (DRUID,
                             {'Feral Combat': 51})):
        db = _Db([_human(PLAYER, 'Rob', class_id)] + DPS_BOTS)
        summary, info = _summary(db, {PLAYER: totals})
        assert not info['roles_known']
        assert 'spec unknown' in summary
        prompt = _prompt(summary, info)
        assert NO_TANK not in prompt and NO_HEALER not in prompt


def test_low_level_player_without_talents_is_unknown():
    db = _Db([_human(PLAYER, 'Rob', PRIEST)] + DPS_BOTS)
    summary, info = _summary(db, {})
    assert not info['roles_known']
    assert NO_HEALER not in _prompt(summary, info)


# -- roster completeness ---------------------------------------------------

def test_two_humans_one_unknown_is_incomplete():
    db = _Db([_human(PLAYER, 'Rob', PRIEST),
              _human(101, 'Kim', DK)] + DPS_BOTS)
    _, info = _summary(db, {PLAYER: {'Holy': 41}, 101: {'Blood': 51}})
    assert not info['roles_known']

    db = _Db([_human(PLAYER, 'Rob', MAGE),
              _human(101, 'Kim', SHAMAN)] + DPS_BOTS)
    summary, info = _summary(
        db, {PLAYER: {'Fire': 41}, 101: {'Restoration': 41}})
    assert info['roles_known'] and info['has_healer']
    assert 'Kim (Shaman, healing spec)' in summary


def test_member_without_traits_row_uses_spec():
    db = _Db([_human(PLAYER, 'Rob', MAGE),
              _human(13, 'Altbot', PALADIN)] + DPS_BOTS)
    _, info = _summary(db, {PLAYER: {'Fire': 41},
                            13: {'Protection': 41}})
    assert info['has_tank'] and info['roles_known']
    _, info = _summary(db, {PLAYER: {'Fire': 41}})
    assert not info['roles_known']


def test_departed_healer_with_lingering_traits_row_is_not_counted():
    db = _Db([_human(PLAYER, 'Rob', MAGE)] + DPS_BOTS, unconfirmed=[14])
    summary, info = _summary(db, {PLAYER: {'Fire': 41}})
    assert not info['has_healer']
    assert not info['roles_known']
    assert NO_HEALER not in _prompt(summary, info)
    assert info['total'] == 3


def test_just_joined_bot_missing_from_group_member_is_incomplete():
    db = _Db([_human(PLAYER, 'Rob', MAGE)] + DPS_BOTS)
    _, info = _summary(db, {PLAYER: {'Fire': 41}}, bot_guids=[15])
    assert not info['roles_known']


def test_roster_missing_the_expected_player_is_incomplete():
    db = _Db([_human(101, 'Kim', MAGE)] + DPS_BOTS)
    _, info = _summary(db, {101: {'Fire': 41}})
    assert not info['roles_known']
    # No player guid in the event: cannot confirm the player.
    db = _Db([_human(PLAYER, 'Rob', MAGE)] + DPS_BOTS)
    _, info = _summary(db, {PLAYER: {'Fire': 41}}, player_guid=0)
    assert not info['roles_known']
    _, info = _summary(db, {PLAYER: {'Fire': 41}}, player_guid='bad')
    assert not info['roles_known']


def test_roster_without_any_human_is_incomplete():
    db = _Db([_bot(PLAYER, 'Rob', MAGE, 'ranged_dps')] + DPS_BOTS)
    _, info = _summary(db, {})
    assert not info['roles_known']


def test_failed_roster_lookup_gives_no_summary():
    db = _Db([], fail=True)
    assert get_group_roster(db, 1) is None
    assert _summary(db, {}) == (None, None)
    assert get_group_roster(_Db([]), 0) is None


# -- comment gate and speaker role -----------------------------------------

def test_two_bot_gate_is_kept():
    config = {'LLMChatter.GroupChatter.CompositionCommentChance': 100}
    bot = {'guid': 11, 'name': 'Lyra', 'class': 'Mage',
           'race': 'Human', 'level': 30, 'gender': 'female'}
    calls = []
    for members, expected_calls in (
        ([_human(PLAYER, 'Rob', PRIEST), DPS_BOTS[0]], 0),
        ([_human(PLAYER, 'Rob', PRIEST)] + DPS_BOTS, 1),
    ):
        calls.clear()
        with _talents({PLAYER: {'Holy': 41}}), \
                patch.object(chatter_group, '_maybe_talent_context',
                             lambda *a, **k: None), \
                patch.object(chatter_group, 'call_llm',
                             lambda *a, **k: calls.append(a[1])):
            _maybe_comment_on_composition(
                _Db(members), None, config, 1, bot,
                ['calm', 'witty', 'curious'], 'normal', 1,
                player_name='Rob', player_guid=PLAYER,
                bot_guids=[11],
            )
        assert len(calls) == expected_calls
    assert NO_HEALER not in calls[0]
    assert 'Rob (Light Priest, healing spec)' in calls[0]


def test_speaker_role_reaches_roleplay_context():
    seen = []

    def fake_context(race, class_name, actual_role=None):
        seen.append(actual_role)
        return ''
    with patch.object(chatter_group, 'build_race_class_context',
                      fake_context):
        _prompt('Rob (Mage, damage spec)', {'roles_known': False},
                mode='roleplay', speaker_role='ranged_dps')
        _prompt('Rob (Mage, damage spec)', {'roles_known': False},
                mode='roleplay')
    assert seen == ['ranged_dps', None]


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} group composition role tests passed")
