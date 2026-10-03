"""Nearby conversations stay readable without long, mechanical pauses."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chatter_proximity_pacing import proximity_line_delays

PREFIX = 'LLMChatter.ProximityChatter.DynamicPacing.'


class ProximityPacingTests(unittest.TestCase):
    def test_length_and_previous_line_affect_delay(self):
        config = {PREFIX + 'JitterPercent': 0}
        short = {'message': 'Hi!'}
        long = {'message': 'A longer thought. ' * 10}
        short_gap = proximity_line_delays([short, short], config, 8)[1]
        long_gap = proximity_line_delays([short, long], config, 8)[1]
        reading_gap = proximity_line_delays([long, short], config, 8)[1]
        self.assertLess(short_gap, long_gap)
        self.assertEqual(long_gap, reading_gap)

    def test_jitter_survives_length_cap(self):
        lines = [{'message': 'A long thought. ' * 20}] * 2
        with patch('chatter_proximity_pacing.random.uniform',
                   side_effect=lambda low, high: low):
            fast = proximity_line_delays(lines, {}, 8)
        with patch('chatter_proximity_pacing.random.uniform',
                   side_effect=lambda low, high: high):
            slow = proximity_line_delays(lines, {}, 8)
        self.assertLess(fast[1], slow[1])

    def test_gap_bounds_and_scene_duration(self):
        for length in (0, 10, 50, 100, 250):
            lines = [{'message': 'x' * length}] * 4
            for _ in range(30):
                delays = proximity_line_delays(lines, {}, 8)
                self.assertEqual(delays[0], 0)
                gaps = [b - a for a, b in zip(delays, delays[1:])]
                self.assertTrue(all(3 <= gap <= 8 for gap in gaps))
                self.assertLessEqual(delays[-1], 24)

    def test_disabled_preserves_fixed_setting(self):
        self.assertEqual(proximity_line_delays(
            [{}] * 4, {PREFIX + 'Enable': 0}, 8,
        ), [0, 8, 16, 24])
        self.assertEqual(proximity_line_delays([], {}, 8), [])

    def test_config_bounds_and_invalid_values(self):
        config = {PREFIX + key: 'invalid' for key in (
            'MinSeconds', 'MaxSeconds', 'CharsPerSecond', 'JitterPercent',
        )}
        config[PREFIX + 'MaxSeconds'] = float('nan')
        delays = proximity_line_delays([{}, {}], config, 8)
        self.assertEqual(delays[0], 0)
        self.assertTrue(3 <= delays[1] <= 4)
        config = {PREFIX + 'MinSeconds': 5, PREFIX + 'MaxSeconds': 2}
        self.assertEqual(proximity_line_delays([{}, {}], config, 8), [0, 5])


if __name__ == '__main__':
    unittest.main()
