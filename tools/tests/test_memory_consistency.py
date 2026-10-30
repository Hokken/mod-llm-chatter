#!/usr/bin/env python3
"""Bot memories stay factual, in character and recalled sensibly.

Covers the memory prompt (persona, companions, facts-only and mode
rules), event contexts (achievement earner, milestones, ambient facts,
player messages), recall scoring and age labels, the cap and eviction,
session handling (dungeon dedupe, rehydration), the identity reset, the
schema migration and the optional cleanup script.

Run directly from the module root:
  python tools/tests/test_memory_consistency.py
"""

import re
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import test_persona_coherence  # noqa: F401  dependency stubs, tools path

import chatter_duel
import chatter_group
import chatter_group_handlers as handlers
import chatter_memory as memory
import chatter_shared
from chatter_event_registry import DEAD_EVENTS, EVENT_REGISTRY

TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent


def _read(rel):
    return (MODULE_DIR / rel).read_text(encoding='utf-8')


class _Cursor:
    """Records SQL; answers SELECTs from a queue of results."""

    def __init__(self, db):
        self.db = db
        self.rowcount = 1

    def execute(self, sql, params=()):
        self.db.statements.append((' '.join(sql.split()), params))
        self._result = self.db.results.pop(0) if self.db.results else []

    def fetchall(self):
        return list(self._result) if isinstance(self._result, list) else []

    def fetchone(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result

    def close(self):
        pass


class _DB:
    def __init__(self, results=()):
        self.results = list(results)
        self.statements = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def commit(self):
        pass


PERSONA = {
    'traits': ['stern', 'loyal', 'curious'],
    'tone': 'clipped and formal',
    'backstory': (
        'Born beneath the spires of Silvermoon, she was raised by '
        'magistrates. She swore her oaths alone. ' + 'More. ' * 80
    ),
}


def _prompt(mode, **kw):
    args = dict(
        bot_name='Deryna', bot_class='Paladin', bot_race='Blood Elf',
        bot_gender='female', player_name='Melindra',
        player_gender='female', memory_type='boss_kill',
        event_context='Killed Arcanist Doan', location='Scarlet Monastery',
        mode=mode, persona=PERSONA, companions=['Zaneon', 'Kealvie'],
    )
    args.update(kw)
    return memory.build_memory_prompt(**args)


class MemoryPromptTests(unittest.TestCase):
    def test_roleplay_prompt_carries_persona_and_party(self):
        text = _prompt('roleplay')
        self.assertIn('Your personality: stern, loyal, curious', text)
        self.assertIn('Your voice: clipped and formal', text)
        self.assertIn('Your background (never contradict it): Born', text)
        # Only an excerpt of the backstory.
        background = text.split('Your background')[1].split('\n')[0]
        self.assertLess(len(background), 360)
        self.assertIn('Also in the party: Zaneon, Kealvie', text)
        self.assertIn('never mention levels, achievements, quests', text)
        self.assertIn('in your own in-world voice', text)

    def test_facts_only_rules_in_every_mode(self):
        for mode in ('roleplay', 'normal'):
            text = _prompt(mode)
            for rule in (
                'Record only what "What happened" states',
                "Never describe the player's feelings, motives, words",
                'No outcomes or decisions that are not stated',
                'name them or say "the party"',
                'invent no childhood, family or past events',
                'Never write today, yesterday, just now',
                'return an empty memory',
            ):
                self.assertIn(rule, text, (mode, rule))

    def test_normal_mode_is_a_player_log(self):
        text = _prompt('normal')
        self.assertIn('as a player keeping a log', text)
        self.assertNotIn('Your background', text)
        self.assertNotIn('never mention levels', text)

    def test_new_types_have_moods_and_descriptions(self):
        for kind in ('discovery', 'duel'):
            self.assertIn(kind, memory.MEMORY_MOODS)
            self.assertIn(kind, memory._MEMORY_TYPE_DESC)
            self.assertIn(kind, memory.MEMORY_TYPE_WEIGHTS)
        self.assertEqual(
            memory._MEMORY_TYPE_DESC['duel'], 'a friendly training spar')

    def test_length_is_about_250(self):
        self.assertEqual(memory.MEMORY_TARGET_CHARS, 250)
        self.assertEqual(memory.MEMORY_HARD_CHARS, 400)
        text = _prompt('roleplay')
        self.assertIn('one or two sentences', text)
        self.assertIn('about 250 characters', text)
        self.assertNotIn('One sentence, at most', text)
        clamped = memory._clamp_memory_text('Word ' * 120)
        self.assertLessEqual(len(clamped), 400)

    def test_background_is_facts_not_events(self):
        text = _prompt('roleplay', background=['About X: a ruined keep'])
        self.assertIn('Background (facts to keep the memory accurate; '
                      'not events that happened now):', text)
        self.assertIn('- About X: a ruined keep', text)
        self.assertIn('never retell them as something that happened '
                      'now', text)
        self.assertNotIn('Background (facts', _prompt('roleplay'))

    def test_empty_memory_is_not_stored(self):
        with patch.object(memory, 'get_llm_client'), \
                patch.object(memory, 'call_llm',
                             return_value='{"memory": "", "emote": null}'):
            self.assertEqual(
                memory._call_llm_for_memory({}, mode='roleplay'),
                (None, None))


class EventContextTests(unittest.TestCase):
    def _levelup(self, mode, leveler_class='Paladin', style='Paladin'):
        # Reactor Veliana (guid 5); leveler Erodora (guid 6), a bot.
        ctx = {
            'config': {}, 'group_id': 1, 'bot_guid': 5,
            'bot_name': 'Veliana',
            'bot': {'class': 'Priest', 'race': 'Blood Elf',
                    'gender': 'female'},
            'leveler_name': 'Erodora', 'leveler_guid': 6,
            'new_level': 36, 'is_bot': True, 'mode': mode,
            'leveler_race': 'Blood Elf', 'leveler_class': leveler_class,
        }
        db = _DB(results=[{'class': 2, 'race': 10, 'gender': 1}])
        with patch.object(handlers, 'genders_by_named_guid',
                          return_value={'Erodora': 'female'}), \
                patch.object(handlers, 'class_style',
                             return_value=style), \
                patch.object(handlers.random, 'random', return_value=0), \
                patch.object(handlers, 'queue_memory') as queued:
            handlers._levelup_post_success(db, ctx, 'Well done.')
        return {c.args[2]: c.kwargs['event_context']
                for c in queued.call_args_list}

    def test_levelup_memory_names_class_growth(self):
        contexts = self._levelup('roleplay')
        growth = handlers.levelup_growth('', 'Paladin')[1]
        self.assertEqual(
            contexts[5],
            'Erodora (female), a Blood Elf Paladin, grew noticeably '
            f'stronger in {growth}')
        self.assertEqual(
            contexts[6], f'I felt myself grow noticeably stronger in {growth}')
        shadow = self._levelup('roleplay', 'Priest', 'Shadow Priest')
        self.assertIn("a priest's command of shadow magic", shadow[6])
        self.assertIn('a Blood Elf Shadow Priest,', shadow[5])
        # Unknown class: no growth phrase, as in the party reaction.
        unknown = self._levelup('roleplay', '', '')
        self.assertEqual(unknown[5], 'Erodora (female), a Blood Elf, grew '
                         'noticeably stronger')
        self.assertEqual(unknown[6], 'I felt myself grow noticeably stronger')
        normal = self._levelup('normal')
        self.assertEqual(normal[6], 'I reached level 36')

    def test_milestones_are_recognised(self):
        for name in ('Level 30', '50 Quests Completed', '100 Mounts'):
            self.assertTrue(memory.is_milestone_achievement(name), name)
        for name in ('Lunch Lady', 'Wailing Caverns', 'Giddy Up!'):
            self.assertFalse(memory.is_milestone_achievement(name), name)

    def _achievement(self, mode, name, achiever_guid=7):
        db = _DB(results=[[
            {'bot_guid': 7, 'bot_name': 'Zaneon', 'class': 4,
             'race': 10, 'gender': 0},
            {'bot_guid': 8, 'bot_name': 'Kealvie', 'class': 1,
             'race': 2, 'gender': 1},
        ]])
        ctx = {
            'config': {'LLMChatter.Memory.AchievementGenerationChance': 100,
                       'LLMChatter.Memory.MaxBotsPerEvent': 5},
            'group_id': 3, 'mode': mode, 'extra_data': {},
            'achievement_name': name, 'achiever_name': 'Zaneon',
            'achiever_guid': achiever_guid,
        }
        calls = []
        with patch.object(handlers, 'queue_memory',
                          side_effect=lambda *a, **k: calls.append(k)):
            handlers._achievement_post_success(db, ctx, 'msg')
        return calls

    def test_achievement_names_the_earner(self):
        calls = self._achievement('roleplay', 'Wailing Caverns')
        contexts = {c['bot_name']: c['event_context'] for c in calls}
        self.assertEqual(
            contexts['Zaneon'],
            'I earned recognition for: Wailing Caverns')
        self.assertEqual(
            contexts['Kealvie'],
            'Zaneon earned recognition for: Wailing Caverns')

    def test_roleplay_milestone_skipped_before_llm(self):
        self.assertEqual(self._achievement('roleplay', 'Level 30'), [])
        self.assertEqual(len(self._achievement('normal', 'Level 30')), 2)

    def test_event_bots_are_capped(self):
        bots = list(range(5))
        self.assertEqual(
            len(memory.pick_event_bots({}, bots)), 2)
        self.assertEqual(
            len(memory.pick_event_bots(
                {'LLMChatter.Memory.MaxBotsPerEvent': '1'}, bots)), 1)
        self.assertEqual(
            memory.pick_event_bots(
                {'LLMChatter.Memory.MaxBotsPerEvent': '0'}, bots), [])

    def test_ambient_context_holds_only_facts(self):
        with patch.object(chatter_group, 'get_recent_weather',
                          return_value='light rain'):
            outdoor = handlers._ambient_memory_context(
                None, 12, 87, 0, 'Elwynn Forest')
            indoor = handlers._ambient_memory_context(
                None, 1581, 0, 36, 'The Deadmines')
        self.assertIn('Elwynn Forest', outdoor)
        self.assertIn('nothing else happened', outdoor)
        self.assertIn('Time of day:', outdoor)
        self.assertIn('Current weather: light rain', outdoor)
        # Indoor instance: no sky, so no time, season or weather.
        self.assertNotIn('Time of day', indoor)
        self.assertNotIn('weather', indoor)

    def test_travel_memory_carries_place_background(self):
        outdoor = handlers._place_background(12, 87, 0, 'Elwynn Forest')
        self.assertTrue(outdoor[0].startswith('About Elwynn Forest: '))
        self.assertTrue(outdoor[1].startswith('About Goldshire: '))
        self.assertEqual(
            len(handlers._place_background(12, 12, 0)), 1)
        indoor = handlers._place_background(1581, 0, 36, 'The Deadmines')
        self.assertEqual(len(indoor), 1)
        self.assertIn(handlers.get_dungeon_flavor(36), indoor[0])
        # No description at all: the travel memory is not queued.
        self.assertEqual(handlers._place_background(99999, 0, 0), [])
        source = _read('tools/chatter_group_handlers.py')
        self.assertIn('and place_background\n', source)
        self.assertIn('background=place_background,', source)

    def test_quest_context_avoids_the_word_quest(self):
        source = _read('tools/chatter_group_handlers.py')
        self.assertNotIn('Completed quest:', source)
        self.assertIn('Finished the task', source)


class DiscoveryTests(unittest.TestCase):
    BOTS = [
        {'bot_guid': 101, 'bot_name': 'Aliss', 'zone': 33,
         'class': 8, 'race': 10, 'gender': 1, 'level': 30},
        {'bot_guid': 102, 'bot_name': 'Brom', 'zone': 33,
         'class': 1, 'race': 3, 'gender': 0, 'level': 12},
        {'bot_guid': 103, 'bot_name': 'Caro', 'zone': 12,
         'class': 5, 'race': 1, 'gender': 1, 'level': 40},
    ]

    def _run(self, **payload):
        data = {'group_id': 4, 'player_guid': 900,
                'player_name': 'Melindra', 'player_level': 30,
                'zone_id': 33, 'area_id': 99, 'map_id': 0,
                'nearby_bot_guids': [101, 102]}
        data.update(payload)
        config = {'LLMChatter.Memory.DiscoveryGenerationChance': 100,
                  'LLMChatter.Memory.MaxBotsPerEvent': 5}
        calls = []
        with patch.object(handlers, 'get_subzone_lore',
                          side_effect=lambda z, a: (
                              'Old troll ruins.' if a == 99 else None)), \
                patch.object(handlers, 'get_subzone_name',
                             return_value='Zul\'Kunda'), \
                patch.object(handlers, 'get_zone_name',
                             return_value='Stranglethorn Vale'), \
                patch.object(handlers, 'get_zone_flavor',
                             return_value='A jungle.'), \
                patch.object(handlers, 'queue_memory',
                             side_effect=lambda *a, **k: calls.append(
                                 (a, k))):
            handlers.queue_discovery_memories(
                _DB(results=[list(self.BOTS)]), config, data)
        return calls

    def test_nearby_bots_of_level_remember_together(self):
        # 102 is near but below level 15; 103 is far away.
        calls = self._run()
        self.assertEqual([c[0][2] for c in calls], [101])
        kw = calls[0][1]
        self.assertEqual(kw['memory_type'], 'discovery')
        self.assertIn("Melindra and I discovered Zul'Kunda in "
                      "Stranglethorn Vale together", kw['event_context'])
        self.assertEqual(kw['background'], [
            'About Stranglethorn Vale: A jungle.',
            "About Zul'Kunda: Old troll ruins.",
        ])

    def test_only_bots_near_the_player(self):
        self.assertEqual(
            [c[0][2] for c in self._run(nearby_bot_guids=[103])], [103])
        self.assertEqual(self._run(nearby_bot_guids=[]), [])
        self.assertEqual(self._run(nearby_bot_guids=None), [])

    def test_skips(self):
        self.assertEqual(self._run(player_level=14), [])
        self.assertEqual(self._run(zone_id=1519), [])  # Stormwind
        self.assertEqual(self._run(area_id=5), [])     # no description

    def test_event_is_live_and_memory_only(self):
        self.assertNotIn('bot_group_discovery', DEAD_EVENTS)
        spec = EVENT_REGISTRY['bot_group_discovery']
        self.assertEqual(spec.handler_func, 'process_group_discovery_event')
        self.assertEqual(spec.producer, 'LLMChatterGroupDiscovery.cpp')

    def test_cpp_watches_explored_flags(self):
        source = _read('src/LLMChatterGroupDiscovery.cpp')
        self.assertIn('PLAYER_EXPLORED_ZONES_1 + i', source)
        self.assertIn('current[i] & ~it->second[i]', source)
        self.assertIn('area->zone && area->area_level > 0', source)
        self.assertIn('// First sight (login, new group): baseline only.',
                      source)
        self.assertIn('IsBattlegroundOrArena()', source)
        self.assertIn('"bot_group_discovery"', source)
        self.assertIn('constexpr float kDiscoveryBotRange = 100.0f;', source)
        self.assertIn('IsWithinDistInMap(member, kDiscoveryBotRange)',
                      source)
        self.assertIn('if (nearby.empty())\n        return;', source)
        self.assertIn('nearby_bot_guids', source)
        self.assertIn('nearby_bot_guids',
                      EVENT_REGISTRY['bot_group_discovery'].payload_fields)
        world = _read('src/LLMChatterWorld.cpp')
        self.assertIn('CheckGroupDiscoveries();', world)
        self.assertIn('"LLMChatter.Memory.DiscoveryEnable", true',
                      _read('src/LLMChatterConfig.cpp'))


class DuelTests(unittest.TestCase):
    DUEL = {
        'group_id': 4, 'outcome': 'won',
        'winner_guid': 101, 'winner_in_group': True,
        'winner_is_real_player': False, 'winner_identity_known': True,
        'winner_name': 'Aliss',
        'loser_guid': 900, 'loser_in_group': True,
        'loser_is_real_player': True, 'loser_identity_known': True,
        'loser_name': 'Melindra',
    }

    def test_perspectives_are_friendly_spars(self):
        ctx = chatter_duel.duel_memory_context
        self.assertEqual(
            ctx(self.DUEL, 101),
            'I won a friendly training spar against Melindra')
        lost = dict(self.DUEL, winner_guid=900, winner_is_real_player=True,
                    winner_name='Melindra', loser_guid=101,
                    loser_is_real_player=False, loser_name='Aliss')
        self.assertEqual(
            ctx(lost, 101),
            'Melindra won a friendly training spar against me')
        self.assertEqual(
            ctx(self.DUEL, 102),
            'Aliss won a friendly training spar against Melindra; '
            'I watched')
        fled = dict(self.DUEL, outcome='fled')
        self.assertIn('after Melindra left the sparring ground',
                      ctx(fled, 101))
        self.assertIsNone(ctx(dict(self.DUEL, outcome='interrupted'), 101))

    def _memories(self, duel, bots):
        ctx = {'config': {'LLMChatter.Memory.DuelGenerationChance': 100,
                          'LLMChatter.Memory.MaxBotsPerEvent': 1},
               'group_id': 4, 'extra_data': duel}
        calls = []

        def genders(db, named):
            return {p: 'male' for p in named}

        with patch.object(chatter_duel, 'queue_memory',
                          side_effect=lambda *a, **k: calls.append(
                              (a, k))), \
                patch.object(chatter_duel, 'genders_by_named_guid',
                             side_effect=genders):
            chatter_duel._duel_end_memory(_DB(results=[bots]), ctx, 'm')
        return calls

    def test_duellist_and_capped_watchers_remember(self):
        bots = [{'bot_guid': g, 'bot_name': n, 'class': 1, 'race': 1,
                 'gender': 0} for g, n in
                ((101, 'Aliss'), (102, 'Brom'), (103, 'Caro'))]
        calls = self._memories(self.DUEL, bots)
        guids = [c[0][2] for c in calls]
        self.assertEqual(guids[0], 101)
        self.assertEqual(len(guids), 2)  # duellist + one watcher
        self.assertTrue(all(c[1]['memory_type'] == 'duel' for c in calls))

    OUTSIDER_DUEL = {
        'group_id': 4, 'outcome': 'won',
        'winner_guid': 900, 'winner_in_group': True,
        'winner_is_real_player': True, 'winner_identity_known': True,
        'winner_name': 'Melindra',
        'loser_guid': 555, 'loser_in_group': False,
        'loser_is_real_player': False, 'loser_identity_known': True,
        'loser_name': 'Torvald', 'loser_race': 3, 'loser_class': 1,
        'loser_level': 30,
    }

    def test_players_duel_with_an_outsider_is_remembered(self):
        bots = [{'bot_guid': 102, 'bot_name': 'Brom', 'class': 1,
                 'race': 1, 'gender': 0}]
        calls = self._memories(dict(self.OUTSIDER_DUEL), bots)
        self.assertEqual([c[0][2] for c in calls], [102])
        self.assertEqual(
            calls[0][1]['event_context'],
            'Melindra won a friendly training spar against Torvald, '
            'a male Dwarf Warrior from outside the party; I watched')

    def test_unidentified_outsider_is_a_stranger(self):
        duel = dict(self.OUTSIDER_DUEL, loser_identity_known=False)
        self.assertEqual(
            chatter_duel.duel_memory_context(duel, 102),
            'Melindra won a friendly training spar against a stranger; '
            'I watched')

    def test_duel_without_the_party_is_skipped(self):
        outsiders = dict(self.OUTSIDER_DUEL, winner_in_group=False,
                         winner_is_real_player=False)
        bots = [{'bot_guid': 102, 'bot_name': 'Brom', 'class': 1,
                 'race': 1, 'gender': 0}]
        self.assertEqual(self._memories(outsiders, bots), [])
        self.assertEqual(
            self._memories(dict(self.DUEL, outcome='interrupted'), bots),
            [])


class QuestTextTests(unittest.TestCase):
    def test_placeholders_are_filled(self):
        text = chatter_shared.clean_quest_text(
            'Greetings, $N the $R $C.$B$BThank you, $Gsir:madam;!',
            'Melindra', 'Blood Elf', 'Hunter', 'female')
        self.assertEqual(
            text, 'Greetings, Melindra the Blood Elf Hunter. '
                  'Thank you, madam!')
        self.assertIn('sir', chatter_shared.clean_quest_text(
            '$Gsir:madam;', player_gender='male'))
        long = chatter_shared.clean_quest_text(
            'First part. ' * 60, limit=100)
        self.assertLessEqual(len(long), 100)
        self.assertTrue(long.endswith('.'))

    def test_texts_use_the_locale_and_all_three_labels(self):
        db = _DB(results=[
            {'brief': 'Kill trolls.', 'full': 'Hello $N.',
             'completion': 'Well done.'},
            {'brief': 'Töte Trolle.', 'full': None, 'completion': None},
        ])
        with patch.object(chatter_shared, 'get_language_locale_code',
                          return_value='deDE'):
            texts = chatter_shared.get_quest_memory_texts(
                db, 42, 'Melindra')
        self.assertEqual(texts, {'brief': 'Töte Trolle.',
                                 'full': 'Hello Melindra.',
                                 'completion': 'Well done.'})
        lines = chatter_shared.quest_memory_background(texts)
        self.assertEqual(lines, [
            'How the quest-giver summed up the task: Töte Trolle.',
            'How the quest-giver described the task: Hello Melindra.',
            'What the quest-giver said when it was done: Well done.',
        ])

    def test_quest_memories_pass_the_background(self):
        source = _read('tools/chatter_group_handlers.py')
        self.assertEqual(source.count('background=_quest_background('), 2)


class PlayerMessageTests(unittest.TestCase):
    def setUp(self):
        memory.clear_all_sessions()
        memory.start_session(5, 101, 900, time.time(), {})
        memory._active_sessions[5]['bots'].add(102)

    def tearDown(self):
        memory.clear_all_sessions()

    def _queue(self, msg, responders=(101,), brief=False):
        calls = []
        with patch.object(chatter_group, 'queue_memory',
                          side_effect=lambda *a, **k: calls.append(a)):
            chatter_group._maybe_queue_player_msg_memory(
                {}, 5, msg,
                [{'bot_guid': 101, 'bot_name': 'Aliss'},
                 {'bot_guid': 102, 'bot_name': 'Brom'}],
                player_name='Melindra',
                responders=list(responders), brief_casual=brief,
            )
        return calls

    def test_only_the_responder_remembers(self):
        calls = self._queue('Where should we head after the mine?')
        self.assertEqual([c[2] for c in calls], [101])

    def test_trivial_lines_are_skipped(self):
        self.assertEqual(self._queue('hello', brief=True), [])
        for line in ('((brb))', 'ooc: lag', 'test', '???'):
            self.assertEqual(self._queue(line), [], line)
        self.assertEqual(self._queue('A real question?', responders=()), [])


def _row(i, **kw):
    row = {'id': i, 'memory': f'memory {i}', 'memory_type': 'ambient',
           'zone_id': None, 'map_id': None, 'companions': None,
           'created_at': datetime.now() - timedelta(days=20),
           'last_used_at': None}
    row.update(kw)
    return row


class RecallTests(unittest.TestCase):
    def _recall(self, rows, **kw):
        db = _DB(results=[rows])
        with patch.object(memory.random, 'uniform', return_value=0.0):
            result = memory.get_bot_memories(db, 1, 2, **kw)
        return result, db

    def test_age_labels(self):
        now = datetime(2026, 10, 28, 12, 0)
        cases = {
            timedelta(minutes=10): 'less than an hour ago',
            timedelta(hours=5): 'earlier today',
            timedelta(days=1, hours=2): 'yesterday',
            timedelta(days=10): 'about a week ago',
            timedelta(days=20): 'a few weeks ago',
            timedelta(days=45): 'about a month ago',
            timedelta(days=200): 'a few months ago',
        }
        for delta, label in cases.items():
            self.assertEqual(
                memory.memory_age_label(now - delta, now), label)

    def test_memories_carry_their_age(self):
        result, _ = self._recall([_row(1)], count=1)
        self.assertEqual(result[0], '(a few weeks ago) memory 1')
        self.assertEqual(result[0].memory_id, 1)

    def test_same_place_and_present_companions_come_first(self):
        rows = [
            _row(1),
            _row(2, zone_id=40),
            _row(3, companions='Zaneon'),
            _row(4, companions='Erodora'),
        ]
        result, _ = self._recall(
            rows, count=4, zone_id=40, present=['Zaneon'])
        ids = [r.memory_id for r in result]
        self.assertEqual(ids[0], 2)
        self.assertLess(ids.index(3), ids.index(1))
        self.assertEqual(ids[-1], 4)

    def test_recently_shown_waits(self):
        rows = [
            _row(1, memory_type='boss_kill',
                 last_used_at=datetime.now() - timedelta(minutes=5)),
            _row(2),
        ]
        result, _ = self._recall(rows, count=1)
        self.assertEqual(result[0].memory_id, 2)

    def test_reply_gets_only_relevant_memories(self):
        rows = [
            _row(1, memory='We cleared the Deadmines foundry'),
            _row(2, memory='Rested at Sun Rock Retreat'),
        ]
        result, _ = self._recall(
            rows, count=3, relevant_to='Remember the foundry fight?')
        self.assertEqual([r.memory_id for r in result], [1])

    def test_shown_is_not_used(self):
        _, db = self._recall([_row(1)], count=1)
        update = db.statements[-1][0]
        self.assertIn('last_used_at = NOW()', update)
        self.assertNotIn('used = 1', update)
        _, db = self._recall([_row(1)], count=1, mark_used=True)
        self.assertIn('used = 1', db.statements[-1][0])

    def test_block_notes_follow_the_mode(self):
        self.assertIn('how long ago', memory.memory_block_notes('roleplay'))
        self.assertIn('may not be with you now',
                      memory.memory_block_notes('roleplay'))
        self.assertNotIn('Paraphrase', memory.memory_block_notes('roleplay'))
        self.assertIn('Paraphrase', memory.memory_block_notes('normal'))

    def test_no_forced_callbacks_in_prompts(self):
        for rel in ('tools/chatter_group.py',
                    'tools/chatter_group_prompts.py'):
            source = _read(rel)
            self.assertNotIn('Reference one of these memories', source)
            self.assertNotIn('recognise the callback', source)
        self.assertIn('ignore them and simply answer',
                      _read('tools/chatter_group_prompts.py'))


class CapTests(unittest.TestCase):
    def test_eviction_order_spares_first_meeting(self):
        db = _DB()
        memory._evict_one(db.cursor(), db, 1, 2)
        sql = db.statements[0][0]
        self.assertIn("memory_type != 'first_meeting'", sql)
        self.assertIn(
            'ORDER BY used DESC, COALESCE(last_used_at, created_at) ASC',
            sql)
        self.assertNotIn('RAND()', sql)

    def test_active_insert_keeps_the_cap(self):
        # COUNT returns the cap: one eviction before the insert.
        db = _DB(results=[(30,), []])
        memory._ensure_cap_and_insert(
            db, 1, 2, 3, 'party_member', 'text', 'warm', None,
            1.0, active=1, max_per=30,
            context={'zone_id': 40, 'map_id': 1,
                     'companions': ['Zaneon']},
        )
        kinds = [s[0].split()[0] for s in db.statements]
        self.assertEqual(kinds, ['SELECT', 'DELETE', 'INSERT'])
        insert = db.statements[-1]
        self.assertIn('zone_id, map_id, companions', insert[0])
        self.assertEqual(insert[1][-3:], (40, 1, 'Zaneon'))


class SessionTests(unittest.TestCase):
    def tearDown(self):
        memory.clear_all_sessions()

    def test_dungeon_memory_once_per_session(self):
        memory.start_session(9, 101, 900, time.time(), {})
        self.assertTrue(memory.claim_dungeon_memory(9, 101, 36))
        self.assertFalse(memory.claim_dungeon_memory(9, 101, 36))
        self.assertTrue(memory.claim_dungeon_memory(9, 101, 43))
        self.assertFalse(memory.claim_dungeon_memory(99, 101, 36))

    def test_rehydration_resumes_player_and_clock(self):
        db = _DB(results=[
            [{'group_id': 4, 'bot_guid': 101, 'bot_name': 'Aliss',
              'assigned': 1000.0, 'class': 8, 'race': 10, 'gender': 1}],
            {'start': 900.5},
        ])
        with patch('chatter_db.get_real_player_guid_for_group',
                   return_value=1002):
            memory.rehydrate_active_sessions(db)
        session = memory._active_sessions[4]
        self.assertEqual(session['start'], 900.5)
        self.assertEqual(session['player_guid'], 1002)
        self.assertFalse(session['party_memories_generated'])
        self.assertEqual(session['members'][101]['name'], 'Aliss')

    def test_orphan_recovery_runs_on_the_cleanup_tick(self):
        bridge = _read('tools/llm_chatter_bridge.py')
        tick = bridge[bridge.index('cleanup_stale_groups(db)\n'):]
        self.assertIn('activate_orphaned_memories(', tick[:900])


class IdentityResetTests(unittest.TestCase):
    def test_reset_spares_first_meeting(self):
        db = _DB()
        memory.reset_bot_memories(db, 55)
        sql, params = db.statements[0]
        self.assertIn("memory_type != 'first_meeting'", sql)
        self.assertEqual(params, (55,))

    def test_reset_is_opt_in_on_version_bump(self):
        source = _read('tools/chatter_identity.py')
        self.assertIn("'LLMChatter.Memory.ResetOnIdentityChange'", source)
        self.assertIn('reset_bot_memories(db, bot_guid)', source)


class SqlAndConfTests(unittest.TestCase):
    def test_migration_and_base_schema(self):
        migration = _read(
            'data/sql/characters/updates/20261028_memory_context.sql')
        base = _read('data/sql/characters/base/00000000_llm_chatter_tables.sql')
        table = base[base.index('CREATE TABLE IF NOT EXISTS `llm_bot_memories`'):]
        table = table[:table.index(') ENGINE')]
        for column in ('zone_id', 'map_id', 'companions'):
            self.assertIn(f"COLUMN_NAME  = '{column}'", migration)
            self.assertIn(f'`{column}`', table)
        self.assertIn('20261028_memory_context.sql', _read('README.md'))

    def test_cleanup_script_never_touches_first_meeting(self):
        script = _read('data/sql/characters/optional/memory_cleanup.sql')
        statements = [s for s in script.split(';') if re.search(
            r'\b(SELECT|DELETE)\b', s)]
        self.assertEqual(len(statements), 2)
        for statement in statements:
            self.assertIn("memory_type != 'first_meeting'", statement)

    def test_new_keys_are_documented(self):
        for rel, maxbots in (('conf/mod_llm_chatter.conf.dist', 2),
                             ('conf/presets/mod_ll_chatter_quieter.conf.dist',
                              1)):
            text = _read(rel)
            self.assertIn(
                f'LLMChatter.Memory.MaxBotsPerEvent = {maxbots}', text)
            self.assertIn('LLMChatter.Memory.ResetOnIdentityChange = 0', text)
            self.assertIn('LLMChatter.Memory.DiscoveryEnable = 1', text)
            self.assertIn('LLMChatter.Memory.DiscoveryMinLevel = 15', text)
            for key in ('DiscoveryGenerationChance', 'DuelGenerationChance'):
                self.assertRegex(
                    text, rf'LLMChatter.Memory.{key} = (60|40)')

    def test_enum_updates(self):
        base = _read('data/sql/characters/base/00000000_llm_chatter_tables.sql')
        self.assertIn("'bot_group_discovery'", base)
        self.assertIn("'discovery', 'pvp_kill', 'duel'", base)
        update = _read(
            'data/sql/characters/updates/20261028_memory_events.sql')
        self.assertIn("'''bot_group_discovery'''", update)
        self.assertIn("'''duel'''", update)
        self.assertIn('20261028_memory_events.sql', _read('README.md'))


if __name__ == '__main__':
    unittest.main()
