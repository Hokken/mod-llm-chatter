"""Races outside the original ten get the name the worldserver knows."""

import unittest

import test_persona_coherence  # dependency stubs and tools path
import chatter_db
import chatter_guild
import chatter_shared
import chatter_themed_topics
from chatter_db import get_race_name, load_race_names


class _Cursor:
    def __init__(self, rows, error=None):
        self.rows = rows
        self.error = error
        self.query = ''

    def execute(self, sql, params=()):
        if self.error:
            raise self.error
        self.query = sql

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class _DB:
    def __init__(self, rows=(), error=None):
        self.cursor_obj = _Cursor(list(rows), error)

    def cursor(self, *args, **kwargs):
        return self.cursor_obj


# What SaveRaceNames() writes on a server whose ChrRaces names race 20
# and 21 "Pandaren", one per faction.
_SERVER_ROWS = [
    {'race_id': 1, 'name': 'Human'},
    {'race_id': 9, 'name': 'Goblin'},
    {'race_id': 20, 'name': 'Pandaren'},
    {'race_id': 21, 'name': 'Pandaren'},
]


class RaceNameTests(unittest.TestCase):
    def tearDown(self):
        chatter_db._server_race_names = {}

    def test_without_server_names_only_the_ten_are_known(self):
        self.assertEqual(get_race_name(10), 'Blood Elf')
        self.assertEqual(get_race_name(20), 'Unknown')
        self.assertEqual(get_race_name(20, ''), '')
        self.assertEqual(get_race_name(None), 'Unknown')

    def test_server_names_fill_in_other_races(self):
        db = _DB(_SERVER_ROWS)
        load_race_names(db)
        self.assertIn('llm_chatter_race_names', db.cursor_obj.query)
        self.assertEqual(get_race_name(9), 'Goblin')
        self.assertEqual(get_race_name(21), 'Pandaren')
        self.assertEqual(get_race_name(22), 'Unknown')
        # The bridge's own names keep the original ten.
        self.assertEqual(get_race_name(5), 'Undead')

    def test_unreadable_table_keeps_the_previous_names(self):
        load_race_names(_DB(_SERVER_ROWS))
        load_race_names(_DB(error=RuntimeError('no such table')))
        self.assertEqual(get_race_name(20), 'Pandaren')

    def test_callers_share_the_one_lookup(self):
        load_race_names(_DB(_SERVER_ROWS))
        self.assertIs(chatter_shared.get_race_name, get_race_name)
        self.assertEqual(chatter_themed_topics._race_name(20), 'Pandaren')
        self.assertEqual(chatter_themed_topics._race_name('9'), 'Goblin')

    def test_shared_name_never_decides_a_faction(self):
        # Race 20 and 21 share a name, so only the race ID can tell
        # their factions apart; the name alone stays without one.
        load_race_names(_DB(_SERVER_ROWS))
        self.assertEqual(
            chatter_guild._speaker_faction({'race': 'Pandaren'}), ''
        )
        self.assertEqual(
            chatter_themed_topics.race_faction('Pandaren'), ''
        )


if __name__ == '__main__':
    unittest.main()
