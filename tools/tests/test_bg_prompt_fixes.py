#!/usr/bin/env python3
"""BG prompt fixes from the AB live test (sides, vows, caveats, repetition).

Run from the module root:
  python tools/tests/test_bg_prompt_fixes.py
"""

import unittest
from unittest.mock import patch

import test_battleground_flag_context  # noqa: F401 - dependency stubs
import chatter_bg_prompts as prompts
from chatter_shared import format_name_list


BOT = {'bot_name': 'Rudrun'}


def base(**extra):
    data = {'bg_type_id': 3, 'team': 'Alliance', 'score_alliance': 300,
            'score_horde': 420}
    data.update(extra)
    return data


class PromptFixTests(unittest.TestCase):
    def setUp(self):
        self.stack = [
            patch('chatter_bg_prompts.pick_personality_spices', return_value=[]),
            patch('chatter_bg_prompts.build_environmental_context_lines',
                  return_value=[]),
        ]
        for p in self.stack:
            p.start()

    def tearDown(self):
        for p in self.stack:
            p.stop()

    def test_spell_target_side_is_explicit(self):
        # Live regression: a friendly Dispel Magic on teammate Grogum was
        # spoken as attacking an enemy Forsaken.
        cases = (
            ('dispel', 'your teammate Grogum',
             'cleansing harmful effects off a teammate'),
            ('heal', 'your teammate Grogum', 'heal'),
            ('buff', 'your teammate Grogum', 'buff'),
            ('resurrect', 'your teammate Grogum', 'resurrect'),
            ('offensive', 'the enemy Grogum', 'offensive'),
            ('cc', 'the enemy Grogum', 'cc'),
        )
        for category, target, label in cases:
            for caster in ('Rudrun', 'Kilco'):
                text = prompts.build_bg_spell_cast_prompt(base(
                    caster_name=caster, spell_name='Dispel Magic',
                    target_name='Grogum', spell_category=category), BOT)
                self.assertIn(f'on {target} ({label})', text, (category, caster))

    def test_death_reaction_has_no_orders_or_vows(self):
        for mode in ('normal', 'roleplay'):
            for killer in ('Sydori', ''):
                text = prompts.build_bg_death_prompt(base(
                    dead_name='Grogum', killer_name=killer,
                    _config={'LLMChatter.ChatterMode': mode}), BOT)
                self.assertNotIn('vow revenge', text)
                self.assertNotIn('rally the team', text)
                # The shared normal-mode header mentions tactical chat; the
                # death instruction itself must not ask for tactics.
                instruction = text.split('Grogum', 1)[1].split('\n', 1)[0]
                self.assertNotIn('tactical', instruction)
                self.assertIn('no orders, target calls or vows', text)
                self.assertIn('your teammate grogum', text.lower())
                if killer:
                    self.assertIn('the enemy sydori', text.lower())
        text = prompts.build_bg_death_prompt(base(), BOT)
        self.assertNotIn('teammate a teammate', text)

    def test_match_end_has_no_snapshot_caveat(self):
        text = prompts.build_bg_match_end_prompt(base(
            won=False, final_score_alliance=1100, final_score_horde=1600), BOT)
        self.assertIn('Final score: Alliance 1100 - Horde 1600', text)
        self.assertNotIn('do not claim an exact current score', text)
        # Live prompts keep the caveat.
        live = prompts.build_bg_low_health_prompt(base(), BOT)
        self.assertIn('do not claim an exact current score', live)

    def test_kill_prompt_states_both_sides(self):
        for real in (True, False):
            text = prompts.build_bg_pvp_kill_prompt(base(
                killer_name='Grogum', killer_is_real_player=real,
                victim_name='Lelolastor', victim_class=5), BOT)
            self.assertIn('Your teammate Grogum', text)
            self.assertIn('the enemy Lelolastor (Priest)', text)
        text = prompts.build_bg_pvp_kill_prompt(base(victim_name='Lajmo'), BOT)
        self.assertIn('A teammate killed the enemy Lajmo', text)

    def test_batched_achievement_is_a_natural_list(self):
        self.assertEqual(format_name_list([]), '')
        self.assertEqual(format_name_list(['A']), 'A')
        self.assertEqual(format_name_list(['A', 'B']), 'A and B')
        self.assertEqual(format_name_list(['A', 'B', 'C']), 'A, B and C')
        text = prompts.build_bg_achievement_prompt(base(
            achiever_name='Jaelkua and Arallius', achiever_count=2,
            achievement_name='The Grim Reaper'), BOT)
        self.assertIn('Jaelkua and Arallius each just earned "The Grim Reaper"',
                      text)
        text = prompts.build_bg_achievement_prompt(base(
            achiever_name='Kilco', achievement_name='Know Thy Enemy'), BOT)
        self.assertIn('Kilco just earned "Know Thy Enemy"', text)

    def test_callouts_do_not_invent_a_location(self):
        builders = (
            (prompts.build_bg_low_health_prompt, base(target_name='Sydori')),
            (prompts.build_bg_low_health_prompt, base()),
            (prompts.build_bg_oom_prompt, base()),
            (prompts.build_bg_combat_prompt, base(creature_name='Sydori')),
        )
        for mode in ('normal', 'roleplay'):
            for builder, data in builders:
                data = dict(data, _config={'LLMChatter.ChatterMode': mode})
                self.assertIn('Do not name a place', builder(data, BOT),
                              builder.__name__)

    def test_spell_target_payload_shapes(self):
        # Shapes LLMChatterGroupCombat.cpp emits: area auras use the
        # collective "the group"; shield/support are friendly; a missing
        # target or unknown category gets no invented allegiance.
        cases = (
            ('buff', 'the group', 'Kilco', 'your group'),
            ('shield', 'the group', 'Kilco', 'your group'),
            ('shield', 'Grogum', 'Kilco', 'your teammate Grogum'),
            ('support', 'Grogum', 'Kilco', 'your teammate Grogum'),
            ('heal', 'Rudrun', 'Rudrun', 'yourself'),
            ('heal', 'Kilco', 'Kilco', 'themselves'),
            ('offensive', '', 'Kilco', 'someone'),
            ('heal', None, 'Kilco', 'someone'),
            ('mystery', 'Grogum', 'Kilco', 'Grogum'),
        )
        for category, target, caster, expected in cases:
            data = base(caster_name=caster, spell_name='Power Word: Shield',
                        spell_category=category)
            if target is not None:
                data['target_name'] = target
            text = prompts.build_bg_spell_cast_prompt(data, BOT)
            self.assertIn(f'on {expected} ({category})', text,
                          (category, target, caster))
            self.assertNotIn('teammate the group', text)
            self.assertNotIn('enemy someone', text)
            self.assertNotIn('teammate someone', text)

    def test_bg_anti_repetition_is_scoped_to_match_and_group(self):
        recent = [f'line {i}' for i in range(20)]
        with patch('chatter_bg_prompts.get_recent_bg_messages',
                   return_value=recent) as scoped, \
                patch('chatter_bg_prompts.get_recent_zone_messages',
                      return_value=['zone line']) as zone:
            text = prompts.build_bg_oom_prompt(base(
                zone_id=3358, _db=object(), bg_match_token='tok-1',
                group_id=91), BOT)
        scoped.assert_called_once()
        zone.assert_not_called()
        self.assertEqual(scoped.call_args.args[1:3], ('tok-1', 91))
        self.assertEqual(scoped.call_args.kwargs, {'limit': 20, 'minutes': 20})
        self.assertIn('line 11', text)
        self.assertNotIn('line 12', text)
        self.assertNotIn('zone line', text)
        # Legacy rows without an envelope keep the original zone window.
        with patch('chatter_bg_prompts.get_recent_bg_messages') as scoped, \
                patch('chatter_bg_prompts.get_recent_zone_messages',
                      return_value=['zone line']) as zone:
            text = prompts.build_bg_oom_prompt(
                base(zone_id=3358, _db=object()), BOT)
        scoped.assert_not_called()
        self.assertEqual(zone.call_args.kwargs, {'limit': 8, 'minutes': 10})
        self.assertIn('zone line', text)

    def test_scoped_query_excludes_other_matches_groups_and_drops(self):
        import chatter_db

        class Cursor:
            def __init__(self):
                self.sql, self.params = '', ()

            def execute(self, sql, params):
                self.sql, self.params = sql, params

            def fetchall(self):
                return [{'message': 'spoken'}, {'message': ''}]

        class DB:
            def __init__(self):
                self.cur = Cursor()

            def cursor(self, dictionary=False):
                return self.cur

        db = DB()
        self.assertEqual(chatter_db.get_recent_bg_messages(db, 'tok-1', 91),
                         ['spoken'])
        sql = ' '.join(db.cur.sql.split())
        for clause in (
            'm.delivered = 1',
            'm.drop_reason IS NULL',  # dropped rows were never spoken
            "m.channel IN ('party', 'battleground')",
            "JSON_UNQUOTE(JSON_EXTRACT( e.extra_data, '$.bg_match_token')) = %s",
            "JSON_EXTRACT(e.extra_data, '$.group_id') = %s",
        ):
            self.assertIn(clause, sql)
        self.assertNotIn('zone_id', sql)
        self.assertEqual(db.cur.params, (20, 'tok-1', 91, 20))
        # No token or group: nothing is fetched rather than a wider scope.
        for token, group in (('', 91), ('tok-1', 0), (None, None)):
            db = DB()
            self.assertEqual(
                chatter_db.get_recent_bg_messages(db, token, group), [])
            self.assertEqual(db.cur.sql, '')


if __name__ == '__main__':
    unittest.main()
