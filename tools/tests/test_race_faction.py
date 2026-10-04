"""Faction comes from the race ID, decided in one place."""

import unittest
from unittest.mock import DEFAULT, patch

import test_persona_coherence  # dependency stubs and tools path
import chatter_battlegrounds
import chatter_constants
import chatter_db
import chatter_guild
from chatter_constants import ALLIANCE_RACE_IDS, HORDE_RACE_IDS, RACE_NAMES
from chatter_shared import get_race_faction


class _Cursor:
    query = ''

    def execute(self, sql, params=()):
        _Cursor.query = sql

    def fetchall(self):
        return []

    def close(self):
        pass


class _DB:
    def cursor(self, *args, **kwargs):
        return _Cursor()


def _carrier_speaks(race_id, team):
    with patch.multiple(
        chatter_battlegrounds,
        get_lightweight_bot_data=DEFAULT,
        _maybe_talent_context=DEFAULT,
        build_bg_flag_carrier_prompt=DEFAULT,
        run_single_reaction=DEFAULT,
    ) as mocks:
        mocks['get_lightweight_bot_data'].return_value = {
            'class': 'Warrior',
            'race': RACE_NAMES.get(race_id, 'Unknown'),
            'race_id': race_id,
        }
        mocks['_maybe_talent_context'].return_value = None
        mocks['build_bg_flag_carrier_prompt'].return_value = 'prompt'
        chatter_battlegrounds._try_carrier_self_message(
            None, None, {}, 123, 'bg_flag_picked_up',
            {'carrier_name': 'Aliss', 'carrier_guid': 101,
             'carrier_is_real_player': False, 'team': team,
             'party_bot_guids': [101]},
        )
        return mocks['run_single_reaction'].call_count == 1


class RaceFactionTests(unittest.TestCase):
    def test_every_named_race_has_exactly_one_faction(self):
        self.assertFalse(set(ALLIANCE_RACE_IDS) & set(HORDE_RACE_IDS))
        self.assertEqual(
            set(RACE_NAMES), set(ALLIANCE_RACE_IDS) | set(HORDE_RACE_IDS)
        )
        self.assertEqual(get_race_faction(11), 'Alliance')
        self.assertEqual(get_race_faction('10'), 'Horde')
        self.assertEqual(get_race_faction(13), '')
        self.assertEqual(get_race_faction(None), '')

    def test_carrier_message_follows_race_id(self):
        self.assertTrue(_carrier_speaks(11, 'Alliance'))
        self.assertFalse(_carrier_speaks(11, 'Horde'))
        self.assertTrue(_carrier_speaks(10, 'Horde'))
        self.assertFalse(_carrier_speaks(None, 'Horde'))

    def test_guild_speaker_faction(self):
        self.assertEqual(
            chatter_guild._speaker_faction({'race_id': 5}), 'Horde'
        )
        # Without an ID the race name still answers.
        self.assertEqual(
            chatter_guild._speaker_faction({'race': 'Draenei'}), 'Alliance'
        )
        self.assertEqual(
            chatter_guild._speaker_faction({'race': 'Scourge'}), 'Horde'
        )
        self.assertEqual(chatter_guild._speaker_faction({}), '')

    def test_added_race_reaches_faction_and_sql_filter(self):
        added = ALLIANCE_RACE_IDS + (22,)
        with patch.object(chatter_constants, 'ALLIANCE_RACE_IDS', added),                 patch('chatter_shared.ALLIANCE_RACE_IDS', added),                 patch('chatter_db.ALLIANCE_RACE_IDS', added):
            self.assertEqual(get_race_faction(22), 'Alliance')
            self.assertTrue(_carrier_speaks(22, 'Alliance'))
            chatter_db.get_recent_zone_messages(
                _DB(), 12, faction='Alliance'
            )
            expected = ', '.join(str(i) for i in added)
            self.assertIn(f'c.race IN ({expected})', _Cursor.query)


if __name__ == '__main__':
    unittest.main()
