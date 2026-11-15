#!/usr/bin/env python3
"""World reactivity checks: the content tables, once-only letters,
level pacing, gift choice, text limits and rumor rules.

Run directly from the module root:
  python tools/tests/test_reactivity.py
"""

import importlib
import json
import random
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_non_strict_stubs() -> None:
    for module_name, class_name in (
        ("anthropic", "Anthropic"), ("openai", "OpenAI"),
    ):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            setattr(
                _ensure_module(module_name),
                class_name,
                type(class_name, (), {}),
            )
    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        setattr(
            _ensure_module("mysql"),
            "connector",
            _ensure_module("mysql.connector"),
        )


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

_install_non_strict_stubs()

import chatter_letters as letters  # noqa: E402
import chatter_reactive_rumors as rumors  # noqa: E402
import chatter_reactivity_data as data  # noqa: E402
from chatter_letter_prompts import (  # noqa: E402
    deed_letter_prompt,
    memory_letter_prompt,
    profession_letter_prompt,
    starter_letter_prompt,
)
from chatter_structured import (  # noqa: E402
    ResponseContract,
    _build_schema,
)

LIMITS = {'body_chars': 900, 'target_words': 112, 'subject_chars': 60}
RECIPIENT = {
    'guid': 1, 'name': 'Ana', 'gender': 'female', 'race': 'Human',
    'class': 'Mage', 'level': 30,
}


class FakeCursor:
    """Answers by the first registered phrase found in the query."""

    def __init__(self, db):
        self.db = db
        self.rows = []
        self.rowcount = 0

    def execute(self, sql, params=()):
        self.db.log.append((sql, params))
        self.rows = []
        self.rowcount = 1
        for phrase, rows in self.db.answers.items():
            if phrase in sql:
                self.rows = rows() if callable(rows) else rows
                break
        if sql.startswith('INSERT IGNORE'):
            key = (sql.split()[3], params[:3])
            self.rowcount = 0 if key in self.db.seen else 1
            self.db.seen.add(key)

    def executemany(self, sql, rows):
        for row in rows:
            self.db.log.append((sql, row))

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeDb:
    def __init__(self, answers=None):
        self.answers = answers or {}
        self.log = []
        self.seen = set()

    def cursor(self, dictionary=False):
        return FakeCursor(self)

    def commit(self):
        pass

    def inserted(self, table):
        return [
            params for sql, params in self.log
            if sql.startswith('INSERT') and table in sql
        ]


class ContentTables(unittest.TestCase):
    def test_every_table_row_is_present(self):
        self.assertEqual(len(data.letters()['dungeons']), 52)
        self.assertEqual(len(data.letters()['raids']), 25)
        self.assertEqual(len(data.letters()['quests']), 70)
        self.assertEqual(len(data.rumors()['quests']), 70)
        self.assertEqual(len(data.rumors()['dungeons']), 77)

    def test_any_achievement_of_a_dungeon_finds_one_letter(self):
        first = data.letter_for_achievement(647)
        heroic = data.letter_for_achievement(667)
        self.assertEqual(first[1]['key'], heroic[1]['key'])
        self.assertEqual(first[0], 'dungeon')

    def test_every_letter_has_a_sender_for_who_can_earn_it(self):
        tables = data.letters()
        for table in tables.values():
            for row in table:
                teams = (
                    ['Alliance', 'Horde']
                    if row['faction'] == 'Both' else [row['faction']]
                )
                for team in teams:
                    for quest in row.get('quests', [0]):
                        sender = data.sender_for(row, team, quest)
                        self.assertTrue(sender, row['key'])
                        self.assertGreater(sender['entry'], 0)

    def test_faction_sender_and_clan_sender(self):
        row = data.letter_by_key('dungeon', 'deadmines')
        self.assertEqual(
            data.sender_for(row, 'Alliance')['name'],
            'Gryan Stoutmantle',
        )
        self.assertEqual(
            data.sender_for(row, 'Horde')['name'], 'Baron Revilgaz',
        )
        clans = data.letter_by_key('quest', 'q1380')
        self.assertEqual(
            data.sender_for(clans, 'Horde', 1381)['name'], 'Warug',
        )

    def test_rumors_have_full_sets(self):
        tables = data.rumors()
        for row in tables['quests']:
            self.assertEqual(len(row['addressed']), 3)
            self.assertEqual(len(row['recounted']), 3)
            self.assertTrue(row['zones'])
        for row in tables['dungeons']:
            self.assertEqual(len(row['addressed']), 5)
            self.assertEqual(len(row['recounted']), 5)
        for row in tables['achievements']:
            self.assertTrue(1 <= row['frequency'] <= 10)

    def test_gatherers_have_no_gift_table(self):
        for name in ('Mining', 'Herbalism', 'Skinning'):
            self.assertNotIn(name, data.gifts()['professions'])
            self.assertIn(name, data.gifts()['starters'])


class LetterText(unittest.TestCase):
    def test_pipes_are_removed(self):
        self.assertNotIn('|', letters.clean_text('a | | b|'))

    def test_body_is_delivered_whole(self):
        body = ('One sentence. ' * 120 + '\n\nFrom the Isle,\nMolthor')
        response = json.dumps({'subject': 'News', 'body': body})
        with patch.object(letters, 'call_llm', return_value=response):
            subject, text = letters._query_letter(
                None, {'LLMChatter.Letters.MaxChars': 300}, 'prompt', 'x',
            )
        self.assertEqual(text, letters.clean_text(body))
        self.assertTrue(text.endswith('Molthor'))

    def test_long_subject_is_cut_only_at_its_column_on_a_word(self):
        subject = letters.clamp_subject('word ' * 40)
        self.assertLessEqual(len(subject), letters.SUBJECT_STORAGE_CHARS)
        self.assertTrue(subject.endswith('word'))
        self.assertEqual(letters.clamp_subject('A' * 70), 'A' * 70)

    def test_subject_never_overflows_its_column(self):
        limit = letters.SUBJECT_STORAGE_CHARS
        for end in (limit - 2, limit - 1, limit, 60):
            text = 'a' * end + 'b. tail words here'
            subject = letters.clamp_subject(text)
            self.assertLessEqual(len(subject), limit, end)
        # A sentence ending inside the column is kept whole.
        whole = letters.clamp_subject('a' * 120 + '. ' + 'b' * 40)
        self.assertEqual(whole, 'a' * 120 + '.')

    def test_length_is_asked_for_in_words_from_the_limit(self):
        limits = letters._limits({'LLMChatter.Letters.MaxChars': 700})
        self.assertEqual(limits['target_words'], 87)

    def test_subject_is_one_line(self):
        self.assertEqual(
            letters.clamp_subject('News\nfrom  Elwynn'), 'News from Elwynn',
        )

    def test_items_spec(self):
        self.assertEqual(
            letters.items_spec([
                {'entry': 1, 'count': 2}, {'entry': 3, 'count': 4},
            ]),
            '1:2,3:4',
        )

    def test_letter_contract(self):
        schema = _build_schema(ResponseContract('letter').schema_key)
        self.assertEqual(
            set(schema['properties']), {'subject', 'body'},
        )


class Prompts(unittest.TestCase):
    def setUp(self):
        self.items = [{'name': 'Moon Pearl', 'count': 2}]

    def test_deed_letter_keeps_facts_and_order(self):
        row = data.letter_by_key('raid', 'molten_core')
        sender = data.sender_for(row, 'Horde')
        prompt = deed_letter_prompt(
            sender, RECIPIENT, row, row['gift']['items'], LIMITS,
        )
        self.assertIn(row['letter'], prompt)
        self.assertIn('at most 112 words', prompt)
        self.assertIn(row['origin'], prompt)
        self.assertIn('"subject"', prompt)

    def test_generic_sender_writes_as_their_role(self):
        row = data.letter_by_key('dungeon', 'deadmines')
        prompt = deed_letter_prompt(
            data.sender_for(row, 'Horde'), RECIPIENT, row,
            row['gift']['items'], LIMITS,
        )
        self.assertIn('You are a shipping agent', prompt)
        self.assertNotIn('You are Baron', prompt)

    def test_quest_letter_fixes_the_subject(self):
        row = data.letter_by_key('quest', 'q14')
        prompt = deed_letter_prompt(
            data.sender_for(row, 'Alliance'), RECIPIENT, row,
            row['gift']['items'], LIMITS,
            subject_hint='News from Westfall',
        )
        self.assertIn('News from Westfall', prompt)

    def test_memory_letter_mentions_a_pet_only_for_a_pet(self):
        args = ('You are Bo.', RECIPIENT, 'We fished.', self.items, '')
        self.assertIn(
            'give it a name',
            memory_letter_prompt(*args, True, True, LIMITS),
        )
        self.assertNotIn(
            'give it a name',
            memory_letter_prompt(*args, False, True, LIMITS),
        )

    def test_starter_letter_has_invitation_and_place(self):
        starter = data.gifts()['starters']['Mining']
        prompt = starter_letter_prompt(
            {'name': 'Tor', 'place': 'Goldshire'}, 'Mining', RECIPIENT,
            starter, LIMITS,
        )
        self.assertIn('Goldshire', prompt)
        self.assertIn(starter['why'], prompt)
        self.assertIn('apprentice', prompt)

    def test_profession_letter_names_the_bundle(self):
        bundle = {'items': self.items, 'what': 'For rings.'}
        prompt = profession_letter_prompt(
            {'name': 'Tor', 'place': 'x'}, 'Jewelcrafting', RECIPIENT,
            bundle, LIMITS,
        )
        self.assertIn('Moon Pearl x2', prompt)

    def test_profession_letters_do_not_all_open_alike(self):
        bundle = {'items': self.items, 'what': 'For rings.'}
        prompts = {
            profession_letter_prompt(
                {'name': 'Tor', 'place': 'x'}, 'Mining', RECIPIENT,
                bundle, LIMITS,
            )
            for _ in range(50)
        }
        self.assertGreater(len(prompts), 1)
        self.assertFalse(any('coming along' in text for text in prompts))

    def test_profession_praise_rests_on_what_could_reach_the_writer(self):
        bundle = {'items': self.items, 'what': 'For rings.'}
        prompts = [
            profession_letter_prompt(
                {'name': 'Tor', 'place': 'x'}, 'Mining', RECIPIENT,
                bundle, LIMITS,
            )
            for _ in range(50)
        ]
        self.assertTrue(all(
            'never say you watched them' in text for text in prompts
        ))
        self.assertTrue(any('what people say' in text for text in prompts))
        self.assertTrue(any('finished piece' in text for text in prompts))

    def test_profession_gift_comes_with_the_letter(self):
        prompt = profession_letter_prompt(
            {'name': 'Tor', 'place': 'x'}, 'Mining', RECIPIENT,
            {'items': self.items, 'what': 'For rings.'}, LIMITS,
        )
        self.assertIn('in with this letter', prompt)
        self.assertIn('never ask them to come for them', prompt)

    def test_subject_leaves_out_the_reader(self):
        starter = data.gifts()['starters']['Mining']
        prompt = starter_letter_prompt(
            {'name': 'Tor', 'place': 'Goldshire'}, 'Mining', RECIPIENT,
            starter, LIMITS,
        )
        self.assertIn("Never put the reader's name in it", prompt)


class Scheduling(unittest.TestCase):
    def test_a_dungeon_gets_one_letter_for_two_achievements(self):
        db = FakeDb()
        config = {'LLMChatter.Letters.Dungeons.Chance': '100'}
        first = data.letter_for_achievement(647)
        second = data.letter_for_achievement(667)
        self.assertTrue(letters._schedule_deed_letter(
            db, config, 1, 'Alliance', first, 647,
        ))
        self.assertFalse(letters._schedule_deed_letter(
            db, config, 1, 'Alliance', second, 667,
        ))

    def test_a_failed_roll_is_final_too(self):
        db = FakeDb()
        found = data.letter_for_achievement(647)
        config = {'LLMChatter.Letters.Dungeons.Chance': '0'}
        self.assertFalse(letters._schedule_deed_letter(
            db, config, 1, 'Alliance', found, 647,
        ))
        row = db.inserted('llm_reactivity_letters')[0]
        self.assertEqual(row[3], 'skipped')
        config['LLMChatter.Letters.Dungeons.Chance'] = '100'
        self.assertFalse(letters._schedule_deed_letter(
            db, config, 1, 'Alliance', found, 667,
        ))

    def test_other_faction_gets_no_letter(self):
        db = FakeDb()
        found = data.letter_for_achievement(629)
        self.assertEqual(found[1]['faction'], 'Horde')
        self.assertFalse(letters._schedule_deed_letter(
            db, {}, 1, 'Alliance', found, 629,
        ))
        self.assertEqual(db.inserted('llm_reactivity_letters'), [])

    def test_disabled_kind_is_silent(self):
        db = FakeDb()
        config = {'LLMChatter.Letters.Raids.Enable': '0'}
        self.assertFalse(letters._schedule_deed_letter(
            db, config, 1, 'Horde',
            data.letter_for_achievement(686), 686,
        ))

    def test_delay_stays_in_range(self):
        for _ in range(200):
            seconds = letters._roll_delay_seconds({}, 'Raids', 4, 6)
            self.assertTrue(4 * 86400 <= seconds <= 6 * 86400)

    def test_starter_level_is_ahead_and_in_window(self):
        for _ in range(100):
            self.assertTrue(
                5 <= letters._roll_starter_level(1, 5, 15) <= 15
            )
            self.assertTrue(
                11 <= letters._roll_starter_level(10, 5, 15) <= 15
            )
        self.assertEqual(letters._roll_starter_level(15, 5, 15), 0)
        self.assertEqual(letters._roll_starter_level(40, 5, 15), 0)

    def test_profession_pacing(self):
        self.assertEqual(letters._next_profession_level({}, 10), 25)
        for _ in range(100):
            level = letters._next_profession_level({}, 30)
            self.assertTrue(40 <= level <= 46)

    def test_no_free_slot_no_starter_letter(self):
        db = FakeDb()
        state = {'team': 'Alliance', 'starter_one_skill': None}
        self.assertIsNone(letters._schedule_starter(
            db, {}, 1, state, {'free_professions': 0}, 'first',
        ))
        self.assertEqual(db.inserted('llm_reactivity_letters'), [])

    def _starter(self, state, known=None):
        db = FakeDb({'FROM characters': [{
            'name': 'Ana', 'race': 1, 'class': 8, 'gender': 1,
            'level': 12, 'online': 1,
        }]})
        facts = {'free_professions': 1, 'skills': known or {}}
        with patch('chatter_letters.get_race_name',
                   return_value='Human'):
            offered = letters._schedule_starter(
                db, {}, 1, state, facts, 'second',
            )
        return offered, db

    def test_second_starter_differs_from_the_first(self):
        for _ in range(50):
            offered, _db = self._starter({
                'team': 'Alliance', 'starter_one_skill': 'Mining',
            })
            self.assertNotEqual(offered, 'Mining')

    def test_starter_skips_known_professions(self):
        known = {
            str(skill): 1 for skill, name
            in data.PROFESSION_SKILLS.items() if name != 'Tailoring'
        }
        offered, _db = self._starter(
            {'team': 'Horde', 'starter_one_skill': None}, known,
        )
        self.assertEqual(offered, 'Tailoring')

    def test_custom_race_falls_back_to_the_faction(self):
        trainer = letters._trainer_for('Mining', 'Horde', 'Goblin')
        self.assertTrue(trainer)
        self.assertEqual(trainer['skill'], 'Mining')

    def test_bundle_follows_skill(self):
        low = letters.eligible_bundle('Tailoring', 40, 20)
        self.assertEqual(low['min_skill'], 1)
        self.assertIsNone(letters.eligible_bundle('Mining', 300, 60))
        self.assertIsNone(letters.eligible_bundle('Tailoring', 400, 60))


class Gifts(unittest.TestCase):
    def test_class_fit(self):
        mana = {'cat': 'mana', 'name': 'Mana Potion', 'note': ''}
        self.assertTrue(letters.fits_class(mana, 'Mage'))
        self.assertFalse(letters.fits_class(mana, 'Warrior'))
        scroll = {'cat': 'scroll', 'name': 'Scroll', 'stat': 'strength'}
        self.assertFalse(letters.fits_class(scroll, 'Mage'))
        self.assertTrue(letters.fits_class(scroll, 'Warrior'))
        stone = {'cat': 'weapon', 'name': 'Stone', 'stat': 'physical'}
        self.assertFalse(letters.fits_class(stone, 'Mage'))
        oil = {'cat': 'weapon', 'name': 'Oil', 'stat': 'caster'}
        self.assertTrue(letters.fits_class(oil, 'Mage'))
        self.assertFalse(letters.fits_class(oil, 'Rogue'))

    def test_fit_reads_the_stat_field_not_the_name(self):
        # The name is free text; only the explicit field decides.
        scroll = {'cat': 'scroll', 'name': 'Scroll of Strength'}
        self.assertTrue(letters.fits_class(scroll, 'Mage'))
        stats = {g.get('stat', '') for g in data.gifts()['common']}
        self.assertLessEqual(
            stats, {'', 'strength', 'agility', 'caster', 'physical'},
        )

    def test_precious_gifts_follow_their_chance(self):
        table = {'common': [
            {'cat': 'food', 'id': 1, 'name': 'Bread', 'note': '',
             'min': 1, 'until': 80},
            {'cat': 'food', 'id': 2, 'name': 'Cake',
             'note': 'a generous gift', 'min': 1, 'until': 80},
        ]}
        db = FakeDb({'SELECT RequiredLevel': [(1,)]})
        with patch.object(letters, 'gifts', return_value=table), \
                patch.object(letters, '_pick_green', return_value=None):
            never = {
                letters.pick_common_gift(db, 1, 30, 'Mage', 0)[0]['entry']
                for _ in range(100)
            }
        self.assertEqual(never, {1})

    def test_gift_suits_level_and_class(self):
        by_id = {g['id']: g for g in data.gifts()['common']}
        db = FakeDb({'SELECT RequiredLevel': [(1,)]})
        with patch.object(letters, '_pick_green', return_value=None):
            for _ in range(200):
                item, _note, _pet = letters.pick_common_gift(
                    db, 1, 30, 'Warrior',
                )
                entry = by_id[item['entry']]
                self.assertTrue(entry['min'] <= 30 <= entry['until'])
                self.assertNotEqual(entry['cat'], 'mana')

    def test_item_raised_by_a_mod_is_not_given_early(self):
        db = FakeDb({'SELECT RequiredLevel': [(60,)]})
        with patch.object(letters, '_pick_green', return_value=None):
            item, _note, _pet = letters.pick_common_gift(
                db, 1, 20, 'Warrior',
            )
        self.assertIsNone(item)

    def test_a_known_pet_is_not_given_again(self):
        pets = {
            g['id'] for g in data.gifts()['common']
            if g['cat'] == 'pet'
        }
        db = FakeDb({'SELECT RequiredLevel': [(1,)]})
        with patch.object(letters, '_knows_pet', return_value=True), \
                patch.object(letters, '_pick_green', return_value=None):
            for _ in range(100):
                item, _note, is_pet = letters.pick_common_gift(
                    db, 1, 30, 'Mage',
                )
                self.assertFalse(is_pet)
                self.assertNotIn(item['entry'], pets)


class GiftItems(unittest.TestCase):
    ALL_CLASSES = {'-1', '0', '1535', '2047', '4095', '32767', '262143'}
    # The client takes bag icons from its own Item.dbc, which ends here:
    # an item past it shows a question mark once it leaves the mailbox.
    LAST_CLIENT_ITEM = 56806
    STOCK_ITEMS = (
        TOOLS_DIR.parents[2] / 'data' / 'sql' / 'base' / 'db_world'
        / 'item_template.sql'
    )

    def letter_gifts(self):
        return [
            item
            for table in data.letters().values()
            for row in table
            for item in row['gift']['items']
        ]

    def test_every_gift_is_an_item_the_client_knows(self):
        for item in self.letter_gifts():
            self.assertLessEqual(
                item['entry'], self.LAST_CLIENT_ITEM, item['name']
            )

    def test_every_gift_matches_the_stock_item(self):
        if not self.STOCK_ITEMS.exists():
            self.skipTest('core item_template.sql not available')
        names = {}
        sql = self.STOCK_ITEMS.read_text(encoding='utf-8', errors='replace')
        for entry, name in re.findall(
            r"^\((\d+),\d+,\d+,-?\d+,'((?:[^'\\]|\\.)*)'", sql,
            flags=re.MULTILINE,
        ):
            names[int(entry)] = name.replace("\\'", "'")
        for item in self.letter_gifts():
            self.assertEqual(
                names.get(item['entry']), item['name'], item['entry']
            )

    def test_every_gift_can_be_taken_and_used_by_anyone(self):
        """No gift is unique, class-locked or needs a profession to use:
        trade goods need one only to be worked, and the profession
        tables go to players who have it."""
        if not self.STOCK_ITEMS.exists():
            self.skipTest('core item_template.sql not available')
        sql = self.STOCK_ITEMS.read_text(encoding='utf-8', errors='replace')
        cols = re.findall(
            r'^  `(\w+)`', sql[:sql.index('PRIMARY KEY')], re.MULTILINE,
        )
        at = {c: cols.index(c) for c in (
            'class', 'AllowableClass', 'RequiredSkill', 'maxcount',
        )}
        items = {}
        for line in re.findall(r'^\((.*)\),?;?$', sql, re.MULTILINE):
            vals = re.findall(r"'(?:[^'\\]|\\.)*'|NULL|-?[\d.e+-]+", line)
            if len(vals) == len(cols):
                items[int(vals[0])] = {c: vals[i] for c, i in at.items()}
        tables = data.gifts()
        gifts = [(g['id'], 'common') for g in tables['common']]
        gifts += [(item['entry'], 'letter') for item in self.letter_gifts()]
        for entry, source in gifts:
            item = items[entry]
            self.assertIn(item['AllowableClass'], self.ALL_CLASSES, entry)
            self.assertEqual(item['maxcount'], '0', entry)
            if item['class'] != '7':
                self.assertEqual(item['RequiredSkill'], '0', (entry, source))

    def test_prompt_names_are_localized_and_stored_ones_kept(self):
        items = [{'entry': 2454, 'name': "Elixir of Lion's Strength",
                  'count': 3}]
        with patch.object(
            letters, 'localize_item_name',
            side_effect=lambda db, name, entry: f'{name}/{entry}',
        ):
            named = letters._localized_gifts(FakeDb(), items)
        self.assertEqual(
            named[0]['name'], "Elixir of Lion's Strength/2454"
        )
        self.assertEqual(named[0]['count'], 3)
        self.assertEqual(items[0]['name'], "Elixir of Lion's Strength")


class Rumors(unittest.TestCase):
    NPC = {'is_npc': True, 'disposition': 'friendly'}
    EXTRA = {
        'player_guid': 1, 'zone_id': 40, 'player_name': 'Ana',
        'map_id': 0, 'is_dungeon': False, 'is_raid': False,
    }

    def test_only_friendly_or_neutral_npcs_tell_rumors(self):
        tell = rumors._speakers_may_tell
        self.assertTrue(tell([self.NPC]))
        self.assertTrue(tell([{'is_npc': True, 'disposition': 'neutral'}]))
        self.assertFalse(tell([{'is_npc': True, 'disposition': 'hostile'}]))
        self.assertFalse(
            tell([{'is_npc': True, 'disposition': 'unfriendly'}])
        )
        self.assertFalse(tell([{'is_npc': False}]))
        self.assertFalse(tell([self.NPC, {'is_npc': False}]))
        self.assertFalse(tell([]))

    def test_hero_becomes_the_players_name(self):
        self.assertEqual(
            rumors._name_hero('The hero won. Ask the hero.', 'Ana'),
            'Ana won. Ask Ana.',
        )

    def test_a_faction_without_a_region_has_no_rumor(self):
        row = data.rumor_by_key('dungeon', 'ragefire_chasm')
        self.assertEqual(rumors.rumor_zones(row, 'dungeon', 'Alliance'), [])
        self.assertTrue(rumors.rumor_zones(row, 'dungeon', 'Horde'))
        db = FakeDb()
        self.assertFalse(rumors.unlock_rumor(
            db, {}, 1, 'Alliance', ('dungeon', row),
        ))

    def test_unlock_is_fresh_once(self):
        db = FakeDb()
        found = data.rumor_for_quest(14)
        self.assertTrue(rumors.unlock_rumor(
            db, {}, 1, 'Alliance', found,
        ))
        self.assertFalse(rumors.unlock_rumor(
            db, {}, 1, 'Alliance', found,
        ))
        zones = db.inserted('llm_reactivity_fresh_rumor_zones')
        self.assertEqual([z[1] for z in zones], found[1]['zones'])

    def test_home_ground_dungeons_stay_with_their_faction(self):
        for key, silent in (
            ('deadmines', 'Horde'), ('gnomeregan', 'Horde'),
            ('shadowfang_keep', 'Alliance'),
            ('scarlet_monastery', 'Alliance'), ('zulaman', 'Alliance'),
        ):
            row = data.rumor_by_key('dungeon', key)
            speaking = 'Alliance' if silent == 'Horde' else 'Horde'
            self.assertEqual(rumors.rumor_zones(row, 'dungeon', silent), [])
            self.assertTrue(rumors.rumor_zones(row, 'dungeon', speaking))

    def test_achievement_rumor_is_told_anywhere(self):
        kind, row = data.rumor_for_achievement(1681)
        self.assertEqual(rumors.rumor_zones(row, kind, 'Alliance'), [0])

    def _pick(self, answers, speakers=None, config=None):
        answers = {
            'FROM llm_reactivity_player_state': [('Alliance',)],
            **answers,
        }
        return rumors.pick_rumor(
            FakeDb(answers), config or {}, self.EXTRA,
            speakers or [self.NPC],
        )

    def test_fresh_rumor_ignores_the_chance(self):
        topic = self._pick(
            {'llm_reactivity_fresh_rumor_zones': [('quest', 'q14')]},
            config={'LLMChatter.Rumors.Chance': '0'},
        )
        self.assertEqual(topic.key, 'q14')

    def test_no_fresh_rumor_and_no_chance_is_silent(self):
        self.assertIsNone(self._pick(
            {}, config={'LLMChatter.Rumors.Chance': '0'},
        ))

    def test_hostile_speaker_blocks_a_fresh_rumor(self):
        self.assertIsNone(self._pick(
            {'llm_reactivity_fresh_rumor_zones': [('quest', 'q14')]},
            speakers=[{'is_npc': True, 'disposition': 'hostile'}],
        ))

    def test_old_deed_is_told_only_in_its_region(self):
        answers = {
            'FROM character_queststatus_rewarded': [(14,)],
        }
        config = {'LLMChatter.Rumors.Chance': '100'}
        topic = self._pick(answers, config=config)
        self.assertEqual(topic.key, 'q14')
        elsewhere = dict(self.EXTRA, zone_id=12)
        db = FakeDb({
            'FROM llm_reactivity_player_state': [('Alliance',)],
            **answers,
        })
        self.assertIsNone(rumors.pick_rumor(
            db, config, elsewhere, [self.NPC],
        ))

    def test_recently_told_rumor_rests(self):
        topic = self._pick(
            {
                'FROM character_queststatus_rewarded': [(14,)],
                'last_voiced_at >': [('quest', 'q14')],
            },
            config={'LLMChatter.Rumors.Chance': '100'},
        )
        self.assertIsNone(topic)

    def test_recounted_keeps_the_player_out_of_it(self):
        random.seed(3)
        for _ in range(40):
            topic = self._pick(
                {'llm_reactivity_fresh_rumor_zones': [('quest', 'q14')]},
            )
            lines = ' '.join(rumors.rumor_prompt_lines(topic, 'Ana'))
            if topic.addressed:
                self.assertIn('Ana', lines)
                self.assertIn(str(topic), lines)
            else:
                self.assertNotIn('Ana', lines)

    def test_notes_are_filled_in(self):
        db = FakeDb({
            'FROM character_achievement': [(2780,)],
            'FROM character_reputation': [(932, 100), (934, 5)],
        })
        champion = data.rumor_by_key('achievement', 'champion_of_a_city')
        self.assertIn('Ironforge', rumors._achievement_notes(
            db, champion, 1, 'Alliance',
        ))
        divided = data.rumor_by_key('achievement', 'shattrath_divided')
        self.assertIn('Aldor', rumors._achievement_notes(
            db, divided, 1, 'Alliance',
        ))
        winds = data.rumor_by_key(
            'achievement', 'the_winds_of_the_north'
        )
        self.assertIn('Horde Expedition', rumors._achievement_notes(
            db, winds, 1, 'Horde',
        ))

    def test_a_claimed_but_unsent_line_is_not_heard(self):
        db = FakeDb({'FROM llm_reactivity_rumor_voicings v': []})
        rumors.settle_voicings(db, {})
        query = db.log[0][0]
        self.assertIn('m.delivered_at IS NOT NULL', query)
        self.assertIn('m.drop_reason IS NULL', query)

    def test_addressed_share_comes_from_config(self):
        row = data.rumor_by_key('quest', 'q14')
        for chance, addressed in ((0, False), (100, True)):
            for _ in range(20):
                topic = rumors._render(
                    None, 'quest', row, 1, 'Alliance', 'Ana', chance,
                )
                self.assertEqual(topic.addressed, addressed)

    def _settle(self, row, config=None):
        db = FakeDb({'FROM llm_reactivity_rumor_voicings v': [row]})
        rumors.settle_voicings(db, config or {})
        return [sql for sql, _ in db.log]

    def test_undelivered_line_does_not_count(self):
        sql = self._settle({
            'id': 1, 'player_guid': 1, 'kind': 'quest',
            'rumor_key': 'q14', 'expired': 0, 'heard': 0,
        })
        self.assertFalse(any('voiced_count' in s for s in sql))
        self.assertFalse(any(s.startswith('DELETE') for s in sql))

    def test_expired_unheard_voicing_is_dropped_uncounted(self):
        sql = self._settle({
            'id': 1, 'player_guid': 1, 'kind': 'quest',
            'rumor_key': 'q14', 'expired': 1, 'heard': 0,
        })
        self.assertFalse(any('voiced_count' in s for s in sql))
        self.assertTrue(any(
            'DELETE FROM llm_reactivity_rumor_voicings' in s for s in sql
        ))

    def test_delivered_line_counts_and_ends_freshness(self):
        sql = self._settle({
            'id': 1, 'player_guid': 1, 'kind': 'quest',
            'rumor_key': 'q14', 'expired': 0, 'heard': 1,
        })
        self.assertTrue(any('voiced_count + 1' in s for s in sql))
        self.assertTrue(any(
            'DELETE FROM llm_reactivity_fresh_rumor_zones' in s
            for s in sql
        ))


class LetterSaving(unittest.TestCase):
    LETTER = {'id': 4, 'kind': 'quest', 'player_guid': 1, 'attempts': 0}

    def test_a_failed_save_counts_as_a_failed_attempt(self):
        class SaveFails(FakeDb):
            def cursor(self, dictionary=False):
                cursor = FakeCursor(self)
                plain = cursor.execute

                def execute(sql, params=()):
                    if "SET status = 'ready'" in sql:
                        raise RuntimeError('Data too long for subject')
                    plain(sql, params)
                cursor.execute = execute
                return cursor

        db = SaveFails({
            'FROM llm_reactivity_letters': [dict(self.LETTER)],
            'FROM characters': [{
                'name': 'Ana', 'race': 1, 'class': 8, 'gender': 1,
                'level': 30, 'online': 0,
            }],
        })
        written = ('Subject', 'Body', 'creature', 7, [
            {'entry': 2454, 'name': 'Elixir', 'count': 1},
        ])
        with patch.dict(letters._WRITERS,
                        {'quest': lambda *a: written}), \
                patch.object(letters, '_letter_failed') as failed:
            letters._write_due_letters(db, None, {})
        failed.assert_called_once()

    def test_recovery_fails_a_row_out_of_attempts(self):
        db = FakeDb()
        letters._recover_stuck_letters(db)
        sql = [(q, p) for q, p in db.log]
        self.assertIn("SET status = 'failed'", sql[0][0])
        self.assertIn("status = 'generating' AND attempts >= %s", sql[0][0])
        self.assertEqual(sql[0][1], (letters.MAX_ATTEMPTS,))
        self.assertIn("SET status = 'scheduled'", sql[1][0])


class Inbox(unittest.TestCase):
    ROW = {'id': 9, 'kind': 'quest', 'player_guid': 1, 'trigger_id': 14,
           'extra_data': '{}', 'attempts': 0}

    def _drain(self, handler):
        db = FakeDb({'FROM llm_reactivity_inbox': [dict(self.ROW)]})
        with patch.object(letters, '_handle_deed', side_effect=handler):
            letters._drain_inbox(db, {})
        return [(sql, params) for sql, params in db.log]

    def test_a_failed_deed_is_kept_and_counted(self):
        def fail(*_):
            raise RuntimeError('db away')
        log = self._drain(fail)
        self.assertFalse(any(sql.startswith('DELETE') for sql, _ in log))
        self.assertIn(
            (1, 9),
            [p for sql, p in log if 'SET attempts' in sql],
        )

    def test_a_handled_deed_is_deleted(self):
        log = self._drain(lambda *_: None)
        self.assertTrue(any(
            sql.startswith('DELETE FROM llm_reactivity_inbox')
            for sql, _ in log
        ))

    def test_rows_past_the_limit_are_not_picked_up(self):
        log = self._drain(lambda *_: None)
        select, params = log[0]
        self.assertIn('attempts < %s', select)
        self.assertEqual(params[0], letters.INBOX_MAX_ATTEMPTS)

    def test_a_faction_change_follows_the_deed(self):
        db = FakeDb({'FROM llm_reactivity_player_state': [
            {'player_guid': 1, 'team': 'Alliance'},
        ]})
        state = letters._ensure_state(db, {}, 1, {'team': 'Horde'})
        self.assertEqual(state['team'], 'Horde')
        self.assertTrue(any(
            'SET team' in sql for sql, _ in db.log
        ))


class SenderIdentity(unittest.TestCase):
    RACES = {
        'Human', 'Dwarf', 'Night Elf', 'Gnome', 'Draenei', 'Orc',
        'Undead', 'Tauren', 'Troll', 'Blood Elf', 'Goblin', 'Broken',
        'Taunka',
    }

    def identities(self):
        for table in data.letters().values():
            for row in table:
                yield from row['senders'].values()
        yield from data.gifts()['trainers'].values()

    def test_values_are_curated_or_absent(self):
        for who in self.identities():
            self.assertIn(who.get('gender', 'male'), ('male', 'female'))
            self.assertIn(who.get('race', 'Human'), self.RACES)
            self.assertNotIn('unknown', str(who).lower())

    def test_proxy_writers_do_not_take_the_named_npcs_identity(self):
        proxies = [
            sender for table in data.letters().values()
            for row in table for sender in row['senders'].values()
            if sender.get('role', '').startswith((
                'a shipping agent of Booty Bay', 'a scout of Garadar',
            ))
        ]
        self.assertEqual(len(proxies), 2)
        for sender in proxies:
            self.assertNotIn('gender', sender)
            self.assertNotIn('race', sender)

    def test_known_values_render_and_missing_ones_are_left_out(self):
        from chatter_letter_prompts import identity_line
        self.assertEqual(
            identity_line({'gender': 'female', 'race': 'Night Elf',
                           'faction': 'Darnassus'}),
            'About you: gender: female | race: Night Elf | '
            'affiliation: Darnassus.',
        )
        self.assertEqual(identity_line({'race': 'Orc'}),
                         'About you: race: Orc.')
        self.assertEqual(identity_line({}), '')

    def test_trainer_letters_carry_the_trainer_identity(self):
        trainer = letters._with_identity(
            {'name': 'Eladriel', 'place': 'x', 'skill': 'Skinning'},
        )
        prompt = profession_letter_prompt(
            trainer, 'Skinning', RECIPIENT,
            {'items': [{'name': 'Light Leather', 'count': 5}],
             'what': 'Armor.'},
            LIMITS,
        )
        self.assertIn('race: Night Elf', prompt)
        self.assertNotIn('warm', prompt)


class QuieterPreset(unittest.TestCase):
    def test_flow_keys_are_lower(self):
        text = (
            TOOLS_DIR.parent / 'conf' / 'presets'
            / 'mod_ll_chatter_quieter.conf.dist'
        ).read_text(encoding='utf-8')
        self.assertIn('LLMChatter.Rumors.FreshVoicings = 1', text)
        raids = re.search(
            r'^LLMChatter.Letters.Raids.Chance = (\d+)', text, re.MULTILINE,
        )
        self.assertLess(int(raids.group(1)), 100)


class Json(unittest.TestCase):
    def test_tables_are_valid_json_files(self):
        for name in (
            'reactivity_letters', 'reactivity_gifts',
            'reactivity_rumors',
        ):
            with open(TOOLS_DIR / f'{name}.json',
                      encoding='utf-8') as handle:
                self.assertTrue(json.load(handle))


if __name__ == '__main__':
    unittest.main()
