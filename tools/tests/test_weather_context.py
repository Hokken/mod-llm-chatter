#!/usr/bin/env python3
"""A player's weather context follows the zone they are in.

The core sends fine weather on entering a zone with no weather
data (Durotar, Orgrimmar); the module must not keep the previous
zone's rain for that zone's prompts.

Run directly from the module root:
  python tools/tests/test_weather_context.py
"""

import re
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[2]


def _zone_update_body():
    source = (MODULE_DIR / 'src/LLMChatterAmbient.cpp').read_text(
        encoding='utf-8')
    match = re.search(
        r'void HandleAmbientPlayerUpdateZone\(.*?\n}\n', source, re.S)
    assert match, 'HandleAmbientPlayerUpdateZone not found'
    return match.group(0)


class WeatherContextTests(unittest.TestCase):
    def test_zone_change_never_carries_the_previous_weather(self):
        body = _zone_update_body()
        self.assertNotIn('currentZoneId = newZone', body)
        # No weather data: fine, as the core sends; weather data but
        # no state seen yet: no context rather than a guess.
        self.assertIn('WeatherMgr::GetWeatherData(newZone)', body)
        self.assertIn('WEATHER_STATE_FINE', body)
        self.assertIn('CONFIG_WEATHER', body)
        self.assertIn('_playerWeatherContext.erase(', body)


if __name__ == '__main__':
    unittest.main()
