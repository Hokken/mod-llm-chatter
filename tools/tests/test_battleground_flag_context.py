#!/usr/bin/env python3
"""Battleground flag timeline and BG prompt context checks.

Run directly from the module root:
  python tools/tests/test_battleground_flag_context.py
"""

import sys
import types
from datetime import datetime, timedelta
from pathlib import Path


def _install_non_strict_stubs() -> None:
    for module_name, class_name in (
        ('anthropic', 'Anthropic'),
        ('openai', 'OpenAI'),
    ):
        try:
            __import__(module_name)
        except ModuleNotFoundError:
            module = types.ModuleType(module_name)
            setattr(module, class_name, type(class_name, (), {}))
            sys.modules[module_name] = module

    try:
        __import__('mysql.connector')
    except ModuleNotFoundError:
        mysql_module = types.ModuleType('mysql')
        connector_module = types.ModuleType('mysql.connector')
        mysql_module.connector = connector_module
        sys.modules['mysql'] = mysql_module
        sys.modules['mysql.connector'] = connector_module


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_bg_flag_timeline as timeline  # noqa: E402
from chatter_bg_prompts import (  # noqa: E402
    build_bg_arrival_prompt,
    build_bg_flag_carry_prompt,
)

T0 = datetime(2026, 9, 30, 20, 0, 0)


class _FakeCursor:
    """Applies the subject/instance scoping that the real
    query does, over an in-memory event table."""

    def __init__(self, table):
        self._table = table
        self._rows = []

    def execute(self, sql, params):
        subject = params[0]
        instance = params[1 + len(timeline.FLAG_EVENT_TYPES)]
        self._rows = [
            dict(r) for r in self._table
            if r['subject_guid'] == subject
            and r['bg_instance_id'] == instance
            and r['event_type'] in timeline.FLAG_EVENT_TYPES
        ]

    def fetchall(self):
        return sorted(self._rows, key=lambda r: r['id'])

    def close(self):
        pass


class _FakeDb:
    def __init__(self, table):
        self._table = table

    def cursor(self, dictionary=False):
        return _FakeCursor(self._table)


def _row(event_id, event_type, flag_team, subject=1,
         instance=10, seconds=0, **extra):
    row = {
        'id': event_id,
        'event_type': event_type,
        'flag_team': flag_team,
        'subject_guid': subject,
        'bg_instance_id': instance,
        'created_at': T0 + timedelta(seconds=seconds),
        'carrier_name': None,
        'dropper_name': None,
    }
    row.update(extra)
    return row


def test_two_simultaneous_matches_do_not_mix():
    table = [
        # Match A (player 1, instance 10)
        _row(1, 'bg_flag_picked_up', 'Horde',
             carrier_name='Gnenci'),
        _row(3, 'bg_flag_dropped', 'Horde', seconds=20,
             dropper_name='Gnenci'),
        # Match B (player 2, instance 20): a Horde return
        # queued between A's pickup and drop.
        _row(2, 'bg_flag_returned', 'Horde', subject=2,
             instance=20, seconds=10),
        _row(4, 'bg_flag_picked_up', 'Horde', subject=2,
             instance=20, seconds=30),
    ]
    db = _FakeDb(table)
    rows_a = timeline.fetch_match_flag_events(
        db, {'id': 3, 'subject_guid': 1},
        {'bg_instance_id': 10})
    assert [r['id'] for r in rows_a] == [1, 3]
    # B's return must not make A's drop look returned.
    assert not timeline.drop_already_returned(rows_a, 3, 'Horde')
    # B's later pickup must not mark A's carry as stale.
    assert not timeline.changed_since(rows_a, 3)


def test_delayed_drop_and_return_ordering():
    # Return queued after the drop (processing delay).
    rows = [
        _row(1, 'bg_flag_picked_up', 'Horde'),
        _row(2, 'bg_flag_dropped', 'Horde', seconds=30),
        _row(3, 'bg_flag_returned', 'Horde', seconds=31),
    ]
    assert timeline.drop_already_returned(rows, 2, 'Horde')
    # Return queued before the drop (3s poll lag).
    rows = [
        _row(1, 'bg_flag_picked_up', 'Horde'),
        _row(2, 'bg_flag_returned', 'Horde', seconds=30),
        _row(3, 'bg_flag_dropped', 'Horde', seconds=32),
    ]
    assert timeline.drop_already_returned(rows, 3, 'Horde')
    # A return from a PREVIOUS carry doesn't count.
    rows = [
        _row(1, 'bg_flag_returned', 'Horde'),
        _row(2, 'bg_flag_picked_up', 'Horde', seconds=60),
        _row(3, 'bg_flag_dropped', 'Horde', seconds=90),
    ]
    assert not timeline.drop_already_returned(rows, 3, 'Horde')
    # A return after the NEXT pickup belongs to that carry.
    rows = [
        _row(1, 'bg_flag_picked_up', 'Horde'),
        _row(2, 'bg_flag_dropped', 'Horde', seconds=30),
        _row(3, 'bg_flag_picked_up', 'Horde', seconds=35),
        _row(4, 'bg_flag_returned', 'Horde', seconds=80),
    ]
    assert not timeline.drop_already_returned(rows, 2, 'Horde')
    # The other team's flag is independent.
    rows = [
        _row(1, 'bg_flag_picked_up', 'Horde'),
        _row(2, 'bg_flag_returned', 'Alliance', seconds=10),
        _row(3, 'bg_flag_dropped', 'Horde', seconds=20),
    ]
    assert not timeline.drop_already_returned(rows, 3, 'Horde')


def test_regrab_is_event_relative():
    rows = [
        _row(1, 'bg_flag_picked_up', 'Horde',
             carrier_name='Hitti'),
        _row(2, 'bg_flag_dropped', 'Horde', seconds=40,
             dropper_name='Hitti'),
    ]
    at = T0 + timedelta(seconds=43)
    assert timeline.is_regrab(
        rows, 3, at, 'Horde', 'Hitti', 15)
    # Outside the window, relative to the events (not NOW).
    late = T0 + timedelta(seconds=70)
    assert not timeline.is_regrab(
        rows, 3, late, 'Horde', 'Hitti', 15)
    # A different carrier is a real pickup.
    assert not timeline.is_regrab(
        rows, 3, at, 'Horde', 'Zaranis', 15)
    # A return in between starts a new carry.
    rows.append(_row(3, 'bg_flag_returned', 'Horde',
                     seconds=41))
    assert not timeline.is_regrab(
        rows, 4, at, 'Horde', 'Hitti', 15)
    # Window 0 disables the filter.
    assert not timeline.is_regrab(
        rows[:2], 3, at, 'Horde', 'Hitti', 0)


def _carry_extra(**overrides):
    extra = {
        'bg_type_id': 2, 'team': 'Alliance',
        'score_alliance': 1, 'score_horde': 1,
        'friendly_flag_carrier': 'Karaez',
        'horde_flag_carry_sec': 60,
        'real_players': [{'name': 'Karaez', 'race': 'Night Elf'}],
        '_config': {},
    }
    extra.update(overrides)
    return extra


def test_carry_prompt_only_claims_safety_at_base():
    bot = {'bot_name': 'Grogum'}
    at_base = build_bg_flag_carry_prompt(
        _carry_extra(own_flag_state='base'), bot)
    assert 'safe at base' in at_base
    on_ground = build_bg_flag_carry_prompt(
        _carry_extra(own_flag_state='ground'), bot)
    assert 'safe' not in on_ground
    assert 'on the ground' in on_ground
    unknown = build_bg_flag_carry_prompt(_carry_extra(), bot)
    assert 'safe' not in unknown
    assert 'scores' not in unknown


def _arrival_extra(**overrides):
    extra = {
        'bg_type_id': 2, 'team': 'Alliance',
        'player_name': 'Karaez', '_config': {},
    }
    extra.update(overrides)
    return extra


def test_arrival_prompt_pre_start_and_late_join():
    bot = {'bot_name': 'Osco'}
    pre = build_bg_arrival_prompt(_arrival_extra(
        match_in_progress=False,
        score_alliance=0, score_horde=0), bot)
    assert 'gathering before the fight' in pre
    late = build_bg_arrival_prompt(_arrival_extra(
        match_in_progress=True,
        score_alliance=2, score_horde=1), bot)
    assert 'already in progress' in late
    assert 'Alliance 2' in late and 'Horde 1' in late
    assert 'before the fight' not in late
    # No status/score supplied: assert neither phase
    # nor a made-up 0-0 score.
    unknown = build_bg_arrival_prompt(_arrival_extra(), bot)
    assert 'before the fight' not in unknown
    assert 'already in progress' not in unknown
    assert 'Score:' not in unknown


if __name__ == '__main__':
    test_two_simultaneous_matches_do_not_mix()
    test_delayed_drop_and_return_ordering()
    test_regrab_is_event_relative()
    test_carry_prompt_only_claims_safety_at_base()
    test_arrival_prompt_pre_start_and_late_join()
    print('Battleground flag context checks passed.')
