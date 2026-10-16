#!/usr/bin/env python3
"""The bridge must be responsive when busy and quiet when idle.

Two failures pull in opposite directions here. A fixed fast poll keeps
the bridge spinning on an empty server, which is the idle CPU burn this
branch set out to fix. Applying the configured interval unconditionally
fixes that but adds the whole interval to every direct player reply,
which is what review of this PR caught.

So the cadence is a decision, not a constant, and these tests pin the
decision: fast while anyone is online or work is still running, slow only
when nothing is happening at all.

Run directly from the module root:
  python tools/tests/test_bridge_poll_cadence.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm_chatter_bridge as bridge  # noqa: E402

MODULE_ROOT = Path(bridge.__file__).resolve().parent.parent
ACTIVE = 0.2
IDLE = 3.0


def test_players_online_keeps_the_fast_cadence():
    """Someone is playing, so a reply could arrive at any moment."""
    assert bridge._poll_delay(True, False, ACTIVE, IDLE) == ACTIVE


def test_work_in_flight_keeps_the_fast_cadence():
    """No one online, but a background task is still finishing."""
    assert bridge._poll_delay(False, True, ACTIVE, IDLE) == ACTIVE


def test_idle_server_uses_the_configured_interval():
    """Nobody online and nothing running: this is the CPU-burn case."""
    assert bridge._poll_delay(False, False, ACTIVE, IDLE) == IDLE


def test_the_two_signals_are_independent():
    """Either signal alone is enough to stay responsive."""
    for players, work in ((True, False), (False, True), (True, True)):
        assert bridge._poll_delay(
            players, work, ACTIVE, IDLE) == ACTIVE, (
            'players=%r work=%r should poll fast' % (players, work))


def test_loop_asks_for_the_delay_rather_than_hardcoding_one():
    """The main loop must route through the decision, not a constant.

    Guards the regression directly: a bare time.sleep(poll_interval) in
    the loop is what made replies wait, and a bare time.sleep(0.2) is
    what burned CPU when idle.
    """
    source = Path(bridge.__file__).read_text(encoding='utf-8')
    assert 'time.sleep(_poll_delay(' in source, (
        'main loop no longer routes its cadence through _poll_delay')


def test_active_interval_is_documented_and_defaulted():
    """The setting has to be discoverable, not just readable in code."""
    dist = (MODULE_ROOT / 'conf' / 'mod_llm_chatter.conf.dist').read_text(
        encoding='utf-8')
    assert 'LLMChatter.Bridge.ActivePollIntervalSeconds' in dist, (
        'new interval is undocumented in the distributed config')


def main() -> int:
    test_players_online_keeps_the_fast_cadence()
    test_work_in_flight_keeps_the_fast_cadence()
    test_idle_server_uses_the_configured_interval()
    test_the_two_signals_are_independent()
    test_loop_asks_for_the_delay_rather_than_hardcoding_one()
    test_active_interval_is_documented_and_defaulted()
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
