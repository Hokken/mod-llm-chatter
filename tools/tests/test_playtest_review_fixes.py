#!/usr/bin/env python3
"""Checks for fixes made after live playtesting.

Covers the General roster extension (a bot the player is talking to
but outside the capped zone sample must be resolvable), the kill/pull
burst guards (reserve, commit on success, release on failure), and
open-air instance environment lines (time and season, never weather).

Run directly from the module root:
  python tools/tests/test_playtest_review_fixes.py
"""

import importlib
import json
import sys
import threading
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

import chatter_general  # noqa: E402
import chatter_group_handlers as handlers  # noqa: E402
import chatter_prompts  # noqa: E402
import chatter_proximity  # noqa: E402
import chatter_shared  # noqa: E402


# ---------------------------------------------------------------------
# General roster extension
# ---------------------------------------------------------------------

class _CharactersCursor:
    """Evaluates the roster query against an in-memory characters
    table: name IN (...), online = 1, zone = %s."""

    def __init__(self, table):
        self.table = table
        self.rows = []

    def execute(self, sql, params=()):
        *names, zone = params
        self.rows = [
            row for row in self.table
            if row['name'] in names
            and row['online'] == 1
            and row['zone'] == zone
        ]

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class _CharactersDB:
    def __init__(self, table):
        self.table = table
        self.queries = 0

    def cursor(self, dictionary=False):
        self.queries += 1
        return _CharactersCursor(self.table)


_ZONE = 148
_CHARACTERS = [
    # Recent General speaker, online, here, Alliance: must be added.
    {'guid': 3001, 'name': 'Zulrakka', 'race': 1,
     'online': 1, 'zone': _ZONE},
    # Bot that spoke here but is now in another zone.
    {'guid': 3002, 'name': 'Farwander', 'race': 1,
     'online': 1, 'zone': 1},
    # Bot of the other faction.
    {'guid': 3003, 'name': 'Grukk', 'race': 2,
     'online': 1, 'zone': _ZONE},
    # Offline bot.
    {'guid': 3004, 'name': 'Sleepy', 'race': 1,
     'online': 0, 'zone': _ZONE},
    # The real player: online and here, but never a candidate.
    {'guid': 5, 'name': 'Karaez', 'race': 4,
     'online': 1, 'zone': _ZONE},
]
_HISTORY = [
    {'speaker_name': 'Sleepy', 'is_bot': 1, 'message': 'hm'},
    {'speaker_name': 'Grukk', 'is_bot': 1, 'message': 'lok'},
    {'speaker_name': 'Farwander', 'is_bot': 1, 'message': 'off'},
    {'speaker_name': 'Karaez', 'is_bot': 0, 'message': 'hi'},
    {'speaker_name': 'Zulrakka', 'is_bot': 1, 'message': 'Beaches.'},
]


def _resolve(bot_names, analyzer_bot):
    reply = json.dumps({
        'bot': analyzer_bot, 'multi_addressed': False,
        'brief_casual': False, 'requires_reply': True,
    })
    with patch.object(chatter_shared, 'quick_llm_analyze',
                      return_value=reply):
        return chatter_shared.find_addressed_bot(
            'where are you from?', bot_names,
            # A non-empty config: an empty one skips the analyzer.
            client=object(), config={'LLMChatter.Provider': 'test'},
        )


def test_resolver_discards_names_outside_the_sample():
    # The reviewer's reproduction: without the roster extension the
    # addressed bot cannot be chosen at all.
    assert _resolve(['Mira'], 'Zulrakka')['bot'] is None


def test_roster_extension_makes_recent_speaker_addressable():
    guids, names = [2001], ['Mira']
    db = _CharactersDB(_CHARACTERS)
    chatter_general._add_recent_general_speakers(
        db, _HISTORY, guids, names, _ZONE, 'Alliance',
    )
    assert names == ['Mira', 'Zulrakka'], names
    assert guids == [2001, 3001], guids
    assert _resolve(names, 'Zulrakka')['bot'] == 'Zulrakka'


def test_newer_ineligible_speakers_do_not_hide_the_partner():
    # Zulrakka spoke first; three ineligible bots spoke after. The
    # partner must still be added (no pre-validation cap).
    history = [
        {'speaker_name': 'Zulrakka', 'is_bot': 1, 'message': 'Beaches.'},
        {'speaker_name': 'Farwander', 'is_bot': 1, 'message': 'a'},
        {'speaker_name': 'Grukk', 'is_bot': 1, 'message': 'b'},
        {'speaker_name': 'Sleepy', 'is_bot': 1, 'message': 'c'},
    ]
    guids, names = [2001], ['Mira']
    chatter_general._add_recent_general_speakers(
        _CharactersDB(_CHARACTERS), history, guids, names,
        _ZONE, 'Alliance',
    )
    assert names == ['Mira', 'Zulrakka'], names
    assert _resolve(names, 'Zulrakka')['bot'] == 'Zulrakka'


def test_roster_excludes_out_of_zone_faction_offline_and_players():
    guids, names = [], []
    chatter_general._add_recent_general_speakers(
        _CharactersDB(_CHARACTERS), _HISTORY, guids, names,
        _ZONE, 'Alliance',
    )
    for excluded in ('Farwander', 'Grukk', 'Sleepy', 'Karaez'):
        assert excluded not in names, (excluded, names)


def test_roster_skips_names_already_sampled_and_needs_faction():
    db = _CharactersDB(_CHARACTERS)
    names = ['Zulrakka']
    chatter_general._add_recent_general_speakers(
        db, _HISTORY, [3001], names, _ZONE, 'Alliance',
    )
    assert names == ['Zulrakka']
    chatter_general._add_recent_general_speakers(
        db, _HISTORY, [], [], _ZONE, '',
    )
    assert db.queries == 1  # no faction: no query at all


# ---------------------------------------------------------------------
# Burst guards
# ---------------------------------------------------------------------

def _event(event_id, bot_guid, is_boss=False, group_id=7):
    return {'id': event_id, 'extra_data': json.dumps({
        'group_id': group_id, 'bot_guid': bot_guid,
        'bot_name': f'Bot{bot_guid}', 'is_boss': int(is_boss),
        'creature_name': 'Quilboar',
    })}


def _run(handler, events, results, config=None):
    """Run events through `handler` with the pipeline returning (or
    raising) the given results in order. Returns handler results and
    the number of pipeline calls."""
    calls = []
    outcomes = iter(results)

    def fake_pipeline(*args, **kwargs):
        calls.append(kwargs.get('event_type_label'))
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    config = config if config is not None else {}
    got = []
    with patch.object(handlers, 'run_group_handler',
                      side_effect=fake_pipeline), \
            patch.object(handlers, '_mark_event'), \
            patch.object(handlers, '_has_recent_event',
                         return_value=False), \
            patch.object(handlers, '_maybe_raid_battle_cry'):
        for event in events:
            try:
                got.append(handler(None, None, config, event))
            except RuntimeError:
                got.append('raised')
    return got, len(calls)


def _reset():
    with handlers._burst_lock:
        handlers._burst_voiced_at.clear()
        handlers._burst_inflight.clear()


def test_pull_success_holds_the_window():
    _reset()
    got, calls = _run(handlers.process_group_combat_event,
                      [_event(1, 11), _event(2, 12)], [True, True])
    assert got == [True, False] and calls == 1, (got, calls)


def test_failed_pull_releases_the_window():
    # Reviewer's reproduction: [False, True] must let the second
    # bot speak.
    _reset()
    got, calls = _run(handlers.process_group_combat_event,
                      [_event(1, 11), _event(2, 12)], [False, True])
    assert got == [False, True] and calls == 2, (got, calls)


def test_exception_releases_the_window():
    _reset()
    got, calls = _run(handlers.process_group_kill_event,
                      [_event(1, 11), _event(2, 12)],
                      [RuntimeError('llm down'), True])
    assert got == ['raised', True] and calls == 2, (got, calls)


def test_boss_kill_bypasses_and_restarts_the_window():
    _reset()
    got, calls = _run(
        handlers.process_group_kill_event,
        [_event(1, 11, is_boss=True), _event(2, 12),
         _event(3, 13, is_boss=True)],
        [True, True, True],
    )
    assert got == [True, False, True] and calls == 2, (got, calls)


def test_pulls_do_not_bypass_for_bosses():
    _reset()
    got, calls = _run(
        handlers.process_group_combat_event,
        [_event(1, 11, is_boss=True), _event(2, 12, is_boss=True)],
        [True, True],
    )
    assert got == [True, False] and calls == 1, (got, calls)


def test_window_zero_disables_the_guard():
    _reset()
    config = {'LLMChatter.GroupChatter.KillBurstWindow': '0',
              'LLMChatter.GroupChatter.PullBurstWindow': '0'}
    got, calls = _run(handlers.process_group_kill_event,
                      [_event(1, 11), _event(2, 12)], [True, True],
                      config=config)
    assert got == [True, True] and calls == 2, (got, calls)
    assert not handlers._burst_voiced_at
    assert not handlers._burst_inflight


def test_concurrent_reservations_only_one_wins():
    _reset()
    extra = {'group_id': 7}
    winners = []
    barrier = threading.Barrier(8)

    def worker():
        barrier.wait()
        reservation = handlers._burst_reserve(
            'pull', {}, extra, 'LLMChatter.GroupChatter.PullBurstWindow',
            15, boss_passes=False,
        )
        if reservation is not None:
            winners.append(reservation)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(winners) == 1, len(winners)


def _reserve(extra):
    return handlers._burst_reserve(
        'kill', {}, extra, 'LLMChatter.GroupChatter.KillBurstWindow',
        30, boss_passes=True,
    )


_NORMAL = {'group_id': 7}
_BOSS = {'group_id': 7, 'is_boss': 1}


def test_failed_normal_then_failed_boss_leaves_group_free():
    # Reviewer's ordering: A (normal) reserved, boss B bypasses it,
    # A fails, then B fails. Nothing was voiced: no window may remain.
    _reset()
    a = _reserve(_NORMAL)
    b = _reserve(_BOSS)
    assert a and b
    handlers._burst_finish(a, voiced=False)
    handlers._burst_finish(b, voiced=False)
    assert _reserve(_NORMAL) is not None


def test_failed_boss_then_failed_normal_leaves_group_free():
    _reset()
    a = _reserve(_NORMAL)
    b = _reserve(_BOSS)
    handlers._burst_finish(b, voiced=False)
    handlers._burst_finish(a, voiced=False)
    assert _reserve(_NORMAL) is not None


def test_failed_boss_keeps_an_earlier_voiced_window():
    # A genuinely voiced reaction still holds the window even when a
    # later boss attempt fails.
    _reset()
    a = _reserve(_NORMAL)
    handlers._burst_finish(a, voiced=True)
    b = _reserve(_BOSS)
    handlers._burst_finish(b, voiced=False)
    assert _reserve(_NORMAL) is None


def test_in_flight_reaction_suppresses_until_finished():
    _reset()
    a = _reserve(_NORMAL)
    assert _reserve(_NORMAL) is None  # a is still being generated
    handlers._burst_finish(a, voiced=False)
    assert _reserve(_NORMAL) is not None


# ---------------------------------------------------------------------
# Environment lines
# ---------------------------------------------------------------------

def _env(map_id, is_instance):
    extra = {'map_id': map_id, 'zone_id': 491}
    import chatter_group
    with patch.object(chatter_group, 'get_recent_weather',
                      return_value='heavy rain') as weather, \
            patch.object(chatter_prompts.random, 'random',
                         return_value=0.0):
        lines = chatter_proximity._environment_lines(
            object(), extra, is_instance,
        )
    return lines, weather.called


def test_indoor_instance_has_no_environment():
    lines, looked_up = _env(34, True)  # Stormwind Stockade
    assert lines == [] and not looked_up, lines


def test_open_air_instance_has_time_but_never_weather():
    lines, looked_up = _env(47, True)  # Razorfen Kraul
    assert any(line.startswith('Time of day') for line in lines), lines
    assert not any('weather' in line.lower() for line in lines), lines
    assert not looked_up


def test_open_world_keeps_live_weather():
    lines, looked_up = _env(1, False)
    assert looked_up
    assert 'Current weather: heavy rain' in lines, lines


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} playtest review checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
