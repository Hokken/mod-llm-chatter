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

    def test_body_ends_on_a_sentence(self):
        text = 'First sentence here. Second one is rather long indeed.'
        self.assertEqual(
            letters.clamp_body(text, 30), 'First sentence here.',
        )

    def test_cut_keeps_the_sign_off(self):
        text = 'One sentence. Two sentence. Three.\n\nFrom the Isle,\nMolthor'
        self.assertEqual(
            letters.clamp_body(text, 45),
            'One sentence.\n\nFrom the Isle,\nMolthor',
        )

    def test_long_last_paragraph_is_not_a_sign_off(self):
        tail = 'word ' * 30 + 'end.'
        text = f'Opening line here.\n\n{tail}'
        clamped = letters.clamp_body(text, 60)
        self.assertLessEqual(len(clamped), 60)
        self.assertTrue(clamped.startswith('Opening line here.'))

    def test_length_is_asked_for_in_words_from_the_limit(self):
        limits = letters._limits({'LLMChatter.Letters.MaxChars': 700})
        self.assertEqual(limits['target_words'], 87)

    def test_short_body_is_untouched(self):
        self.assertEqual(letters.clamp_body('Hi.', 30), 'Hi.')

    def test_subject_is_one_short_line(self):
        self.assertEqual(
            letters.clamp_subject('News\nfrom  Elwynn', 9), 'News from',
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

    def test_locked_profession_is_not_offered(self):
        with patch(
            'chatter_letters.chatter_progression.profession_available',
            lambda db, guid, name: name == 'Cooking',
        ):
            offered, _db = self._starter(
                {'team': 'Alliance', 'starter_one_skill': None},
            )
        self.assertEqual(offered, 'Cooking')

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
        scroll = {'cat': 'scroll', 'name': 'Scroll of Strength'}
        self.assertFalse(letters.fits_class(scroll, 'Mage'))
        stone = {'cat': 'weapon', 'name': 'Stone', 'note': 'Blade'}
        self.assertFalse(letters.fits_class(stone, 'Mage'))

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
