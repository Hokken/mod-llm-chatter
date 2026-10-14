"""Replies to the player wait within the configured responsive range."""

import unittest
from unittest.mock import patch

import test_persona_coherence  # dependency stubs and tools path
from chatter_shared import calculate_dynamic_delay


def _bounds(config):
    """The (low, high) range handed to random.uniform."""
    with patch('chatter_shared.random.uniform',
               side_effect=lambda low, high: (low, high)):
        return calculate_dynamic_delay(40, config, responsive=True)


class ResponsiveDelayTests(unittest.TestCase):
    def test_defaults_keep_four_to_eight_seconds(self):
        self.assertEqual(_bounds({}), (4.0, 8.0))

    def test_configured_range_is_used(self):
        config = {
            'LLMChatter.ResponsiveDelayMin': '1500',
            'LLMChatter.ResponsiveDelayMax': '3000',
        }
        self.assertEqual(_bounds(config), (1.5, 3.0))

    def test_zero_allows_an_immediate_reply(self):
        config = {
            'LLMChatter.ResponsiveDelayMin': '0',
            'LLMChatter.ResponsiveDelayMax': '0',
        }
        self.assertEqual(_bounds(config), (0.0, 0.0))

    def test_swapped_negative_and_invalid_values(self):
        swapped = {
            'LLMChatter.ResponsiveDelayMin': '6000',
            'LLMChatter.ResponsiveDelayMax': '2000',
        }
        self.assertEqual(_bounds(swapped), (2.0, 6.0))
        negative = {'LLMChatter.ResponsiveDelayMin': '-500'}
        self.assertEqual(_bounds(negative), (0.0, 8.0))
        invalid = {'LLMChatter.ResponsiveDelayMax': 'fast'}
        self.assertEqual(_bounds(invalid), (4.0, 8.0))

    def test_ambient_delay_ignores_responsive_range(self):
        config = {
            'LLMChatter.ResponsiveDelayMin': '0',
            'LLMChatter.ResponsiveDelayMax': '0',
        }
        # The ambient floor is 4 s before the final 0.85-1.20 jitter.
        for _ in range(20):
            self.assertGreaterEqual(
                calculate_dynamic_delay(40, config), 3.4
            )


if __name__ == '__main__':
    unittest.main()
