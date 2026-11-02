#!/usr/bin/env python3
"""A player's weather context is what their client was sent.

The worldserver records the SMSG_WEATHER packet sent to each real
player (on a zone change the core sends the zone's weather, or fine
weather where the zone has none, e.g. Durotar), so a prompt never
keeps the previous zone's rain.

Run directly from the module root:
  python tools/tests/test_weather_context.py
"""

import re
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[2]


def _read(rel):
    return (MODULE_DIR / rel).read_text(encoding='utf-8')


class WeatherContextTests(unittest.TestCase):
    def test_weather_packet_sets_the_player_context(self):
        source = _read('src/LLMChatterAmbient.cpp')
        hook = re.search(
            r'bool CanPacketSend\(.*?\n    }\n', source, re.S)
        self.assertIsNotNone(hook)
        body = hook.group(0)
        self.assertIn('SMSG_WEATHER', body)
        self.assertIn('packet.read<uint32>(0)', body)
        self.assertIn('SetPlayerWeatherContext(', body)
        self.assertIn('return true;', body)
        self.assertIn('{SERVERHOOK_CAN_PACKET_SEND}', source)
        self.assertIn('AddLLMChatterAmbientScripts();',
                      _read('src/LLMChatterScript.cpp'))

    def test_zone_change_no_longer_guesses(self):
        self.assertNotIn('HandleAmbientPlayerUpdateZone',
                         _read('src/LLMChatterAmbient.cpp'))
        self.assertNotIn('HandleAmbientPlayerUpdateZone',
                         _read('src/LLMChatterPlayer.cpp'))

    def test_player_weather_comes_before_the_zone_cache(self):
        source = _read('src/LLMChatterAmbient.cpp')
        body = re.search(
            r'static std::string GetCachedWeatherName\(.*?\n}\n',
            source, re.S).group(0)
        self.assertLess(body.index('foundPlayerWeather = true'),
                        body.index('GetCachedWeatherState(zoneId'))


if __name__ == '__main__':
    unittest.main()
