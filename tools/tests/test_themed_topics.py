#!/usr/bin/env python3
"""Themed topics, rumor gating and race+class notes.

Run directly from the module root:
  python tools/tests/test_themed_topics.py
"""

import importlib
import random
import re
import sys
import types
from pathlib import Path
from unittest.mock import patch


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_non_strict_stubs() -> None:
    for module_name in ("anthropic", "openai"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            module = _ensure_module(module_name)
            class_name = (
                "Anthropic" if module_name == "anthropic" else "OpenAI"
            )
            setattr(module, class_name, type(class_name, (), {}))
    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module("mysql.connector")
        setattr(mysql_module, "connector", connector_module)


TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_guild  # noqa: E402
import chatter_progression as progression  # noqa: E402
import chatter_themed_topics as themed  # noqa: E402
import chatter_threads as th  # noqa: E402
from chatter_constants import RACE_NAMES  # noqa: E402
from chatter_lore_data import (  # noqa: E402
    CLASS_TOPICS,
    FACTION_CRITICISM,
    RACE_CLASS_NOTES,
    RACE_CLASS_TOPICS,
    RACE_CRITICISM,
    RACE_TOPICS,
)
from chatter_rumor_data import (  # noqa: E402
    DUNGEON_RUMORS,
    EXPANSION_RUMORS,
    LOCATION_RUMORS,
    RAID_RUMORS,
    REGION_RUMORS,
)
from chatter_shared import (  # noqa: E402
    build_race_class_context,
    race_class_note,
)
from chatter_trainer_rumor_data import (  # noqa: E402
    CLASS_ABILITIES,
    CLASS_TRAINERS,
    PROFESSION_ABILITIES,
    PROFESSION_TRAINERS,
)


PLAYABLE = {
    'Human': ('Warrior', 'Paladin', 'Rogue', 'Priest', 'Mage', 'Warlock',
              'Death Knight'),
    'Dwarf': ('Warrior', 'Paladin', 'Hunter', 'Rogue', 'Priest',
              'Death Knight'),
    'Night Elf': ('Warrior', 'Hunter', 'Rogue', 'Priest', 'Druid',
                  'Death Knight'),
    'Gnome': ('Warrior', 'Rogue', 'Mage', 'Warlock', 'Death Knight'),
    'Draenei': ('Warrior', 'Paladin', 'Hunter', 'Priest', 'Shaman', 'Mage',
                'Death Knight'),
    'Orc': ('Warrior', 'Hunter', 'Rogue', 'Shaman', 'Warlock',
            'Death Knight'),
    'Undead': ('Warrior', 'Rogue', 'Priest', 'Mage', 'Warlock',
               'Death Knight'),
    'Tauren': ('Warrior', 'Hunter', 'Shaman', 'Druid', 'Death Knight'),
    'Troll': ('Warrior', 'Hunter', 'Rogue', 'Priest', 'Shaman', 'Mage',
              'Death Knight'),
    'Blood Elf': ('Paladin', 'Hunter', 'Rogue', 'Priest', 'Mage', 'Warlock',
                  'Death Knight'),
}


def _styles(klass):
    return ('Light Priest', 'Shadow Priest') if klass == 'Priest' else (klass,)


class _NoDb:
    def cursor(self, *args, **kwargs):
        raise RuntimeError("no database in this test")


class _AchievementDb:
    """Achievements per guid; a plain list applies to every guid."""

    def __init__(self, earned):
        self.earned = earned

    def cursor(self, *args, **kwargs):
        db = self

        class _Cursor:
            def execute(self, query, params=None):
                earned = db.earned
                if isinstance(earned, dict):
                    earned = earned.get(params[0], ())
                self.rows = [(a,) for a in earned]

            def fetchall(self):
                return self.rows

        return _Cursor()


def _player(level=60, team='Horde', race='Orc', guid=7, klass='Warrior'):
    return {
        'guid': guid, 'name': f'Player{guid}', 'level': level,
        'team': team, 'race': race, 'class': klass,
    }


def _audience(**kwargs):
    return progression.parse_audience([_player(**kwargs)])


def _listener(**kwargs):
    return _audience(**kwargs)[0]


BOT = {'guid': 5, 'name': 'Grom', 'race': 'Orc', 'class': 'Warrior',
       'level': 60}

PUSHY_WORDING = ('Open with it', 'leave it behind', 'build the line around',
                 'raises the subject', 'spark interest', 'amazing',
                 'They see it from', 'may be invented', 'invent or expand',
                 'has been there', 'own eyes', 'need to end it')


def test_every_playable_combination_has_topics_and_notes():
    for race, classes in PLAYABLE.items():
        assert RACE_TOPICS.get(race), race
        for klass in classes:
            for style in _styles(klass):
                assert CLASS_TOPICS.get(style), style
                assert RACE_CLASS_TOPICS.get((race, style)), (race, style)
                assert RACE_CLASS_NOTES.get((race, style)), (race, style)


def test_parse_audience_accepts_lists_objects_and_rejects_garbage():
    parsed = progression.parse_audience(
        '[{"guid": 3, "level": 20, "team": "Alliance"},'
        ' {"guid": 3, "level": 20}, {"guid": 4, "level": 30}]')
    assert [p['guid'] for p in parsed] == [3, 4]
    assert parsed[0]['team'] == 'Alliance'
    assert set(parsed[0]) == {'guid', 'name', 'level', 'team', 'race',
                              'class'}
    single = progression.parse_audience('{"guid": 9, "level": 11}')
    assert [p['guid'] for p in single] == [9]
    assert progression.parse_audience('not json') == []
    assert progression.parse_audience({'guid': 0, 'level': 5}) == []
    assert progression.parse_audience(None) == []
    many = [_player(guid=g) for g in range(1, 30)]
    assert len(progression.parse_audience(many)) == progression.MAX_AUDIENCE










def test_fits_checks_level_and_completion_per_listener():
    progression.clear_caches()
    northrend = EXPANSION_RUMORS['Northrend']
    ready = _listener(guid=1, level=northrend['min_level'])
    low = _listener(guid=3, level=12)
    assert progression.fits(_NoDb(), ready, northrend)
    assert not progression.fits(_NoDb(), low, northrend)
    entry = next(d for d in DUNGEON_RUMORS if d['achievements'])
    ach = entry['achievements'][0]
    db = _AchievementDb({99: [ach]})
    assert progression.has_completed(db, 99, entry['achievements'])
    assert not progression.has_completed(db, 99, ())
    done = _listener(guid=99, level=entry['min_level'])
    fresh = _listener(guid=98, level=entry['min_level'])
    assert not progression.fits(db, done, entry)
    assert progression.fits(db, fresh, entry)
    progression.clear_caches()


def test_best_covered_prefers_rumors_for_more_listeners():
    progression.clear_caches()
    wide = {'name': 'wide', 'min_level': 10, 'max_level': 30}
    narrow = {'name': 'narrow', 'min_level': 10, 'max_level': 15}
    miss = {'name': 'miss', 'min_level': 40, 'max_level': 50}
    audience = progression.parse_audience([
        _player(guid=1, level=12), _player(guid=2, level=25)])
    target = audience[0]
    assert progression.best_covered(
        _NoDb(), audience, target, [narrow, wide, miss]) == [wide]
    assert progression.best_covered(
        _NoDb(), audience, target, [narrow, miss]) == [narrow]
    assert progression.best_covered(
        _NoDb(), audience, audience[1], [narrow, miss]) == []
    assert progression.best_covered(_NoDb(), audience, None, [wide]) == []


def test_rotation_serves_each_listener_before_repeating():
    progression.clear_caches()
    audience = progression.parse_audience(
        [_player(guid=g) for g in (1, 2, 3)])
    with patch.object(progression.time, 'time', side_effect=range(1, 7)):
        order = [progression.next_rumor_target(audience)['guid']
                 for _ in range(6)]
    assert sorted(order[:3]) == [1, 2, 3]
    assert order[3:] == order[:3]
    assert progression.next_rumor_target([]) is None
    progression.clear_caches()


def test_one_listener_is_always_the_target():
    progression.clear_caches()
    random.seed(11)
    alone = _audience(guid=21, level=25)
    for _ in range(5):
        assert progression.next_rumor_target(alone)['guid'] == 21
    for pool in (DUNGEON_RUMORS, RAID_RUMORS,
                 list(EXPANSION_RUMORS.values())):
        old_rule = [e for e in pool
                    if progression.level_in_range(alone[0], e)]
        assert progression.best_covered(
            _NoDb(), alone, alone[0], pool) == old_rule
    only_dungeons = {f'LLMChatter.ThemedTopics.{k}Weight': 0 for k in (
        'Faction', 'Race', 'Class', 'RaceClass', 'ExpansionRumor',
        'RaidRumor', 'LocationRumor', 'RegionRumor', 'ProfessionRumor',
        'ClassTrainerRumor')}
    for _ in range(30):
        topic = themed.pick_themed_topic(
            _NoDb(), only_dungeons, 'guild', BOT, alone, roll=False)
        assert topic and topic.kind == 'dungeon'
        assert topic.metadata['rumor_target'] == 'Player21'
    progression.clear_caches()


def test_mixed_levels_get_rumors_for_each_listener_in_turn():
    progression.clear_caches()
    random.seed(13)
    audience = progression.parse_audience([
        _player(guid=31, level=15), _player(guid=32, level=25)])
    only_places = {f'LLMChatter.ThemedTopics.{k}Weight': 0 for k in (
        'Faction', 'Race', 'Class', 'RaceClass', 'ExpansionRumor',
        'RaidRumor', 'LocationRumor', 'ProfessionRumor', 'ClassTrainerRumor')}
    pools = {'dungeon': DUNGEON_RUMORS, 'region': REGION_RUMORS}
    by_name = {p['name']: p for p in audience}
    targets = set()
    for _ in range(20):
        topic = themed.pick_themed_topic(
            _NoDb(), only_places, 'guild', BOT, audience, roll=False)
        assert topic and topic.kind in pools
        target = by_name[topic.metadata['rumor_target']]
        targets.add(target['guid'])
        entry = next(e for e in pools[topic.kind]
                     if e['name'] == topic.metadata['rumor'])
        assert progression.level_in_range(target, entry)
    assert targets == {31, 32}
    progression.clear_caches()


def test_a_listener_with_nothing_left_does_not_stall_the_others():
    progression.clear_caches()
    random.seed(17)
    earned = [a for d in DUNGEON_RUMORS for a in d['achievements']]
    db = _AchievementDb({41: earned})
    audience = progression.parse_audience([
        _player(guid=41, level=80), _player(guid=42, level=20)])
    only_dungeons = {f'LLMChatter.ThemedTopics.{k}Weight': 0 for k in (
        'Faction', 'Race', 'Class', 'RaceClass', 'ExpansionRumor',
        'RaidRumor', 'LocationRumor', 'RegionRumor', 'ProfessionRumor',
        'ClassTrainerRumor')}
    served = 0
    for _ in range(6):
        topic = themed.pick_themed_topic(
            db, only_dungeons, 'guild', BOT, audience, roll=False)
        if topic:
            assert topic.metadata['rumor_target'] == 'Player42'
            served += 1
    assert served == 3
    progression.clear_caches()


def test_dungeon_rumor_respects_level_and_completion():
    progression.clear_caches()
    level = 25
    eligible = [d for d in DUNGEON_RUMORS
                if d['min_level'] <= level <= d['max_level']]
    assert eligible
    earned = [a for d in eligible for a in d['achievements']]
    speaker = themed.speaker_profile(_NoDb(), BOT)
    blocked = themed._place_rumor(
        _AchievementDb(earned), speaker, _audience(level=level, guid=11),
        'roleplay', DUNGEON_RUMORS, 'dungeon',
    )
    assert blocked is None or all(not d['achievements'] for d in eligible)
    progression.clear_caches()
    topic = themed._place_rumor(
        _AchievementDb([]), speaker, _audience(level=level, guid=12),
        'roleplay', DUNGEON_RUMORS, 'dungeon',
    )
    assert topic and topic.metadata['rumor'] in {d['name'] for d in eligible}
    assert 'Dungeon' in topic.render() or 'dungeon' in topic.render()
    progression.clear_caches()


def test_location_and_region_rumors_follow_audience_faction():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    for _ in range(30):
        topic = themed._location_rumor(
            _NoDb(), speaker, _audience(level=30, team='Horde'), 'roleplay')
        if topic:
            entry = next(e for e in LOCATION_RUMORS
                         if e['name'] == topic.metadata['rumor'])
            assert 'Horde' in entry['factions']
        topic = themed._region_rumor(
            _NoDb(), speaker, _audience(level=30, team='Horde'), 'roleplay')
        if topic:
            entry = next(e for e in REGION_RUMORS
                         if e['name'] == topic.metadata['rumor'])
            assert 'Horde' in entry['factions']


def test_mixed_faction_listeners_get_no_faction_rumors():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    mixed = progression.parse_audience([
        _player(guid=1, level=30, team='Horde'),
        _player(guid=2, level=30, team='Alliance', race='Human'),
    ])
    assert progression.audience_team(mixed) == ''
    for build in (themed._location_rumor, themed._region_rumor):
        assert build(_NoDb(), speaker, mixed, 'roleplay') is None
    for build in (themed._profession_rumor, themed._class_trainer_rumor):
        assert build(_NoDb(), {}, speaker, mixed, 'roleplay') is None


def test_expansion_rumors_are_always_hearsay():
    low = themed.speaker_profile(_NoDb(), dict(BOT, level=60))
    high = themed.speaker_profile(_NoDb(), dict(BOT, level=80))
    audience = _audience(level=68)
    for speaker in (low, high):
        topic = themed._expansion_rumor(_NoDb(), speaker, audience,
                                        'roleplay')
        text = topic.render()
        assert topic.subject == 'rumors about Northrend'
        assert 'rumor you have heard' in text
        assert 'has been there' not in text
        assert 'own eyes' not in text
        assert 'invent' not in text
        assert 'rumor_seen' not in topic.metadata
    mixed = progression.parse_audience([
        _player(guid=1, level=68), _player(guid=2, level=80)])
    topic = themed._expansion_rumor(_NoDb(), high, mixed, 'roleplay',
                                    target=mixed[0])
    assert topic.metadata['rumor'] == 'Northrend'
    assert themed._expansion_rumor(_NoDb(), high, mixed, 'roleplay',
                                   target=mixed[1]) is None
    assert themed._expansion_rumor(
        _NoDb(), low, _audience(level=40), 'roleplay') is None


def test_pick_states_speaker_faction_and_channel_kinds():
    random.seed(1)
    for _ in range(40):
        topic = themed.pick_themed_topic(
            _NoDb(), {}, 'guild', BOT, _audience(level=60), roll=False)
        assert topic is not None
        assert 'fights for the Horde' in topic.render()
        assert topic.metadata['themed_kind'] in themed.CHANNEL_KINDS['guild']
    for _ in range(20):
        topic = themed.pick_themed_topic(
            _NoDb(), {}, 'party', BOT, roll=False)
        assert topic.kind in ('class', 'race_class')


def test_faction_topics_offer_views_without_orders():
    random.seed(2)
    seen = set()
    for _ in range(120):
        topic = themed._faction_topic(
            themed.speaker_profile(_NoDb(), BOT), 'roleplay')
        text = topic.render()
        kind = topic.metadata['faction_topic']
        seen.add(kind)
        assert 'Horde' in text
        assert 'They see it from' not in text
        assert 'criticism' not in text.lower()
        assert 'holds against' not in text
        if kind == 'criticism':
            assert topic.subject == 'what the Horde thinks of the Alliance'
        if kind == 'race':
            assert 'as the Horde sees them' in topic.subject
        if kind in ('criticism', 'race'):
            assert 'Views often heard in the Horde' in text
            assert ('How far Grom shares these views is up to their own '
                    'personality.') in text
        if kind == 'conflict':
            assert 'recent' not in topic.subject
            assert 'What happened' not in text
            assert 'add no new details' in text
            assert 'may be invented' not in text
    assert seen == {'war_front', 'criticism', 'race', 'conflict'}


def test_themed_wording_is_a_suggestion_not_an_order():
    random.seed(4)
    speaker = themed.speaker_profile(_NoDb(), BOT)
    progression.clear_caches()
    texts = []
    for _ in range(60):
        for channel in ('guild', 'general', 'party'):
            topic = themed.pick_themed_topic(
                _AchievementDb([]), {}, channel, BOT,
                _audience(level=random.choice((10, 30, 60, 75))),
                roll=False)
            if topic:
                texts.append(topic.render())
    texts.append(themed._faction_topic(speaker, 'normal').render())
    for text in texts:
        for phrase in PUSHY_WORDING:
            assert phrase not in text, (phrase, text)
    progression.clear_caches()


def test_rumors_need_an_audience():
    config = {f'LLMChatter.ThemedTopics.{k}Weight': 0 for k in (
        'Faction', 'Race', 'Class', 'RaceClass')}
    assert themed.pick_themed_topic(
        _NoDb(), config, 'general', BOT, [], roll=False) is None
    assert themed.pick_themed_topic(
        _NoDb(), config, 'general', BOT, None, roll=False) is None


def test_channel_chance_and_enable_switch():
    with patch.object(themed.random, 'randint', return_value=31):
        assert themed.pick_themed_topic(
            _NoDb(), {}, 'guild', BOT, _audience()) is None
    with patch.object(themed.random, 'randint', return_value=30):
        assert themed.pick_themed_topic(
            _NoDb(), {}, 'guild', BOT, _audience()) is not None
    with patch.object(themed.random, 'randint', return_value=6):
        assert themed.pick_themed_topic(
            _NoDb(), {}, 'party', BOT) is None
    assert themed.pick_themed_topic(
        _NoDb(), {'LLMChatter.ThemedTopics.Enable': '0'}, 'guild', BOT,
        _audience(), roll=False) is None


def test_candidate_skips_the_channel_chance_while_threads_are_on():
    th.reset_settings()
    th.configure_threads({})
    key = th.guild_key(1)
    try:
        with patch.object(themed.random, 'randint', return_value=100):
            assert themed.themed_candidate(
                _NoDb(), {}, 'guild', BOT, thread_key=key,
                audience=_audience()) is not None
            th.configure_threads({'LLMChatter.Threads.GuildEnable': 0})
            assert themed.themed_candidate(
                _NoDb(), {}, 'guild', BOT, thread_key=key,
                audience=_audience()) is None
        th.configure_threads({'LLMChatter.Threads.ThemedTopicWeight': 0})
        assert themed.themed_candidate(
            _NoDb(), {}, 'guild', BOT, thread_key=key,
            audience=_audience()) is None
    finally:
        th.reset_settings()
        th.clear_all()


def test_themed_used_follows_the_planned_source():
    topic = themed.ThemedTopic('race', 'subject')
    turn = types.SimpleNamespace(source='themed')
    assert themed.themed_used(topic, None)
    assert themed.themed_used(topic, turn)
    assert not themed.themed_used(topic, types.SimpleNamespace(source='pool'))
    assert not themed.themed_used(None, turn)
    assert themed.themed_metadata(None) == {'themed_kind': ''}


def test_candidates_are_prepared_before_the_thread_lock():
    """The candidate's DB lookups must never run inside plan_idle_turn:
    every caller prepares it first and passes plain text."""
    for name in ('chatter_guild.py', 'chatter_ambient.py',
                 'chatter_group.py'):
        source = (TOOLS_DIR / name).read_text(encoding='utf-8')
        calls = [m.start() for m in re.finditer(r'plan_idle_turn\(', source)
                 if 'themed_topic=' in source[m.start():m.start() + 400]]
        assert calls, name
        for start in calls:
            before = source[max(0, start - 900):start]
            assert ('themed_candidate(' in before
                    or '_guild_themed_candidate(' in before), name
    th.reset_settings()
    th.configure_threads({
        'LLMChatter.Threads.PersonaTopicWeight': 0,
        'LLMChatter.Threads.SurroundingsTopicWeight': 0,
        'LLMChatter.Threads.PoolTopicWeight': 0,
    })
    th.clear_all()
    try:
        turn = th.plan_idle_turn(th.guild_key(7), ['Grom'], db=_NoDb(),
                                 themed_topic='rumors about Zul\'Farrak.')
        assert turn.source == 'themed'
        assert not th._lock._is_owned()
    finally:
        th.reset_settings()
        th.clear_all()


def test_roleplay_raid_rumor_avoids_the_word_raid():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    progression.clear_caches()
    topic = themed._place_rumor(
        _AchievementDb([]), speaker, _audience(level=60, guid=21),
        'roleplay', RAID_RUMORS, 'raid')
    assert topic and 'Never use the word "raid"' in topic.render()
    normal = themed._place_rumor(
        _AchievementDb([]), speaker, _audience(level=60, guid=21),
        'normal', RAID_RUMORS, 'raid')
    assert 'Never use the word' not in normal.render()
    progression.clear_caches()


def test_race_class_notes_split_priests():
    light = race_class_note('Undead', 'Priest')
    shadow = race_class_note('Undead', 'Priest', actual_role='ranged_dps')
    assert 'Light Priest' in light and 'Shadow Priest' in shadow
    assert race_class_note('Undead', 'Priest',
                           class_style='Shadow Priest') == shadow
    assert 'people and calling' not in build_race_class_context(
        'Orc', 'Warrior')
    identity = chatter_guild._guild_identity(
        'Grom', {'race': 'Orc', 'class': 'Warrior'})
    assert "Grom's people and calling (Orc Warrior)" in identity


def _trainer_names(tree):
    return {race: {t['name'] for t in trainers}
            for race, trainers in tree.items()}


def test_trainer_data_covers_every_race_and_skill():
    for tree, abilities in ((PROFESSION_TRAINERS, PROFESSION_ABILITIES),
                            (CLASS_TRAINERS, CLASS_ABILITIES)):
        races = RACE_NAMES.values()
        assert set(tree['Alliance']) == {
            r for r in races if themed.race_faction(r) == 'Alliance'}
        assert set(tree['Horde']) == {
            r for r in races if themed.race_faction(r) == 'Horde'}
        for races in tree.values():
            for trainers in races.values():
                for trainer in trainers:
                    assert abilities.get(trainer['skill']), trainer
                    assert trainer['name'] and trainer['place'], trainer
    for races in PROFESSION_TRAINERS.values():
        for trainers in races.values():
            assert {t['skill'] for t in trainers} == set(PROFESSION_ABILITIES)
    assert 'Death Knight' not in CLASS_ABILITIES
    for abilities in (PROFESSION_ABILITIES, CLASS_ABILITIES):
        for skill, lines in abilities.items():
            assert len(lines) == len(set(lines)), skill


def test_trainer_rumor_level_bands_follow_the_target():
    for kind, full, reduced, gone in (('profession', 20, 21, 31),
                                      ('trainer', 15, 16, 26)):
        base = themed._kind_weight({}, kind, _audience(level=1))
        assert base == 12
        assert themed._kind_weight({}, kind, _audience(level=full)) == 12
        assert 0 < themed._kind_weight(
            {}, kind, _audience(level=reduced)) < 12
        assert themed._kind_weight({}, kind, _audience(level=gone)) == 0
        mixed = progression.parse_audience([
            _player(guid=1, level=1), _player(guid=2, level=gone)])
        assert themed._kind_weight({}, kind, mixed, mixed[0]) == 12
        assert themed._kind_weight({}, kind, mixed, mixed[1]) == 0
    config = {'LLMChatter.ThemedTopics.TrainerRumorReducedPercent': '50'}
    assert themed._kind_weight(config, 'trainer', _audience(level=20)) == 6
    assert themed._kind_weight({}, 'dungeon', _audience(level=80)) == 12
    bands = {'LLMChatter.ThemedTopics.ClassTrainerRumorFullLevel': '30',
             'LLMChatter.ThemedTopics.ClassTrainerRumorMaxLevel': '40',
             'LLMChatter.ThemedTopics.ProfessionRumorMaxLevel': '20'}
    assert themed._kind_weight(bands, 'trainer', _audience(level=30)) == 12
    assert 0 < themed._kind_weight(bands, 'trainer',
                                   _audience(level=40)) < 12
    assert themed._kind_weight(bands, 'profession', _audience(level=21)) == 0
    # A MaxLevel below the FullLevel still caps every level above it.
    low_max = {'LLMChatter.ThemedTopics.ProfessionRumorMaxLevel': '10',
               'LLMChatter.ThemedTopics.ClassTrainerRumorMaxLevel': '10'}
    for kind in ('profession', 'trainer'):
        assert themed._kind_weight(low_max, kind, _audience(level=10)) == 12
        for level in (11, 15, 18, 20, 60):
            assert themed._kind_weight(
                low_max, kind, _audience(level=level)) == 0, (kind, level)


def test_trainer_rumors_never_cross_factions():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    alliance = set().union(*_trainer_names(PROFESSION_TRAINERS['Alliance'])
                           .values(),
                           *_trainer_names(CLASS_TRAINERS['Alliance'])
                           .values())
    horde = set().union(*_trainer_names(PROFESSION_TRAINERS['Horde'])
                        .values(),
                        *_trainer_names(CLASS_TRAINERS['Horde']).values())
    random.seed(3)
    for _ in range(200):
        for build in (themed._profession_rumor, themed._class_trainer_rumor):
            topic = build(_NoDb(), {}, speaker,
                          _audience(level=10, team='Horde', race='Tauren'),
                          'roleplay')
            assert topic.metadata['rumor'] in horde
            topic = build(_NoDb(), {}, speaker,
                          _audience(level=10, team='Alliance', race='Gnome'),
                          'normal')
            assert topic.metadata['rumor'] in alliance


def test_trainer_rumors_own_or_other_follows_the_config():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    audience = _audience(level=8, team='Alliance', race='Night Elf',
                         klass='Druid')
    always = {'LLMChatter.ThemedTopics.OwnTrainerChance': '100'}
    never = {'LLMChatter.ThemedTopics.OwnTrainerChance': '0'}
    own = themed._profession_rumor(_NoDb(), always, speaker, audience,
                                   'roleplay')
    assert own.metadata['trainer_race_list'] == 'Night Elf'
    other = themed._class_trainer_rumor(_NoDb(), never, speaker, audience,
                                        'roleplay')
    assert other.metadata['trainer_class'] != 'Druid'
    with patch.object(themed.random, 'randint', return_value=50):
        own = themed._profession_rumor(_NoDb(), {}, speaker, audience,
                                       'roleplay')
        assert own.metadata['trainer_race_list'] == 'Night Elf'
        own = themed._class_trainer_rumor(_NoDb(), {}, speaker, audience,
                                          'roleplay')
        assert own.metadata['trainer_class'] == 'Druid'
    with patch.object(themed.random, 'randint', return_value=51):
        other = themed._profession_rumor(_NoDb(), {}, speaker, audience,
                                         'roleplay')
        assert other.metadata['trainer_race_list'] != 'Night Elf'
        other = themed._class_trainer_rumor(_NoDb(), {}, speaker, audience,
                                            'roleplay')
        assert other.metadata['trainer_class'] != 'Druid'




def test_death_knight_audience_gets_other_class_trainers():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    audience = _audience(level=10, team='Horde', race='Orc',
                         klass='Death Knight')
    with patch.object(themed.random, 'randint', return_value=1):
        topic = themed._class_trainer_rumor(_NoDb(), {}, speaker, audience,
                                            'roleplay')
    assert topic and topic.metadata['trainer_class'] != 'Death Knight'


def test_trainer_rumor_prompt_and_channels():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    topic = themed._class_trainer_rumor(
        _NoDb(), {}, speaker, _audience(level=5), 'normal')
    text = topic.render()
    assert topic.metadata['rumor'] in text
    assert 'Name the trainer and the place' in text
    assert 'amazing' not in text and 'master' not in text
    assert 'Frame it the way a player would chat' in text
    assert 'profession' not in themed.CHANNEL_KINDS['party']
    assert 'trainer' not in themed.CHANNEL_KINDS['party']
    only_trainers = {f'LLMChatter.ThemedTopics.{k}Weight': 0 for k in (
        'Faction', 'Race', 'Class', 'RaceClass', 'ExpansionRumor',
        'DungeonRumor', 'RaidRumor', 'LocationRumor', 'RegionRumor')}
    kinds = {themed.pick_themed_topic(
        _NoDb(), only_trainers, 'general', BOT, _audience(level=12),
        roll=False).kind for _ in range(40)}
    assert kinds == {'profession', 'trainer'}
    assert themed.pick_themed_topic(
        _NoDb(), only_trainers, 'guild', BOT, _audience(level=40),
        roll=False) is None


def test_dungeon_rumors_last_until_the_dungeon_finder_drops_them():
    progression.clear_caches()
    # The Dungeon Finder upper limit (the last wing's for multi-wing
    # dungeons), capped at the expansion's level cap.
    expected_max = {'Ragefire Chasm': 21, 'The Deadmines': 25,
                    'Scarlet Monastery': 45, 'Maraudon': 53,
                    'Blackrock Depths': 60, 'Dire Maul': 60,
                    'Upper Blackrock Spire': 60, 'Hellfire Ramparts': 67,
                    'Old Hillsbrad Foothills': 70, 'The Black Morass': 70,
                    'Utgarde Keep': 80}
    by_name = {d['name']: d for d in DUNGEON_RUMORS}
    for name, top in expected_max.items():
        entry = by_name[name]
        assert entry['max_level'] == top, name
        assert progression.fits(_NoDb(), _listener(level=top), entry), name
        assert not progression.fits(
            _NoDb(), _listener(level=top + 1), entry), name
    level_cap = {'classic': 60, 'tbc': 70, 'wotlk': 80}
    for entry in DUNGEON_RUMORS:
        assert entry['min_level'] < entry['max_level'], entry['name']
        assert entry['max_level'] <= level_cap[entry['expansion']], \
            entry['name']
        if entry['expansion'] == 'wotlk':
            assert entry['max_level'] == 80, entry['name']
    progression.clear_caches()



def test_no_external_progression_module_support():
    for pool in (DUNGEON_RUMORS, RAID_RUMORS, LOCATION_RUMORS,
                 REGION_RUMORS, list(EXPANSION_RUMORS.values())):
        for entry in pool:
            assert 'required_tier' not in entry, entry['name']
            assert 'max_tier' not in entry, entry['name']
    # Classic Onyxia and classic Naxxramas do not exist on 3.3.5; only the
    # level-80 versions remain.
    for name in ("Onyxia's Lair", 'Naxxramas'):
        levels = [(r['min_level'], r['max_level']) for r in RAID_RUMORS
                  if r['name'] == name]
        assert levels == [(78, 80)], (name, levels)
    for name in ('LLMChatterThemedAudience.cpp', 'LLMChatterThemedAudience.h'):
        text = (MODULE_DIR / 'src' / name).read_text(encoding='utf-8')
        for word in ('IndividualProgression', 'ModuleMgr', 'ip_active',
                     'progression', 'is_gm'):
            assert word not in text, (name, word)
    source = (TOOLS_DIR / 'chatter_progression.py').read_text(
        encoding='utf-8')
    assert 'content_unlocked' not in source and 'tier' not in source


def test_trainer_rumors_never_name_gossip_only_npcs():
    names = {t['name'] for tree in (PROFESSION_TRAINERS, CLASS_TRAINERS)
             for races in tree.values() for trainers in races.values()
             for t in trainers}
    for apprentice in ('Graham Van Talen', 'Lalina Summermoon',
                       'Malcomb Wynn', 'Mot Dawnstrider', 'Thund',
                       'Trianna', 'Victor Ward'):
        assert apprentice not in names, apprentice


def test_a_turn_never_carries_a_guild_topic_and_a_themed_subject():
    """#67's guild topics and the themed source share plan_idle_turn():
    the guild topic is offered through the pool, the themed subject
    through its own source, and a used guild topic drops the themed one
    (with threads off it comes first)."""
    ambient = (TOOLS_DIR / 'chatter_ambient.py').read_text(encoding='utf-8')
    for helper in ('= _guild_praise_topic(', '= _guild_discussion_topic('):
        start = ambient.index(helper)
        block = ambient[start:start + 1600]
        assert ('topic_pool=[guild_topic] if guild_topic else topic_pool'
                in block)
        assert 'themed_topic=themed.render() if themed else None' in block
        assert ('if guild_used or not themed_used(themed, thread_turn):'
                in block)
        assert 'guild_topic or (themed.render() if themed' in block
    guild = (TOOLS_DIR / 'chatter_guild.py').read_text(encoding='utf-8')
    plans = [m.start() for m in re.finditer(r'plan_idle_turn\(', guild)]
    assert len(plans) == 2
    for start in plans:
        block = guild[start:start + 900]
        assert '_guild_topic_pool(special, topic_pool)' in block
        assert 'themed_topic=themed.render() if themed else None' in block
        assert ('if special or not themed_used(themed, thread_turn):'
                in block)
        assert (block.index('special.subject if special')
                < block.index('else themed.render() if themed'))
    for needle in ('special_override=special,\n        themed_override=themed,',
                   'special=special,\n        themed=themed,'):
        assert needle in guild, needle


STANCE_OPENINGS = re.compile(
    r'^(Express|Mock|Complain|Boast|Brag|Scoff|Sneer|Grumble|Lament|'
    r'Mourn|Miss|Rant|Wistfully|Bitterly|Regret|Marvel|Tease|Condemn|'
    r'Praise|Say|Share|Feel|Be|Worry|Criticize|Question|Remind|Rave|'
    r'Rapturously|Ironically|Sympathize)\b')
STANCE_WORDS = re.compile(
    r'\b(contempt|proud|pride|despise|mock|hatred|scorn|disgust\w*|'
    r'bitter\w*|resent\w*|condemn|endorse)\b', re.I)
SCRIPTED_PAST = re.compile(
    r'\b(they once|you once|once had|they were once|they recently|'
    r'recently|how they (once|managed|tried|fought|tracked|used)|'
    r'they managed to|they had to|they used to|who was (your|their) '
    r'mentor|your own invention|of your life)\b', re.I)

# Representative entries the semantic review found; each must be gone.
REMOVED_STANCES_AND_PASTS = (
    'admire the Alliance', 'Feel ashamed of, or justify',
    'Rommath is a madman', 'dangerous idiots',
    "he was right in many ways", 'Teldrassil before its destruction',
    'several weeks to heal', 'breakdown of your own invention',
    'old hunter who was your mentor', 'during a rest stop',
    'tried to enter the Cathedral', 'vast, empty library where',
    'the souls of ancestors. The tormented', 'stole a valuable magical',
    'demon worshippers by their very nature',
    'hunting humans and dwarves is not much different',
)


def _all_topics():
    for table in (RACE_TOPICS, CLASS_TOPICS, RACE_CLASS_TOPICS):
        for key, topics in table.items():
            for topic in topics:
                yield key, topic


def test_topics_leave_the_mood_to_the_persona():
    for key, topic in _all_topics():
        assert not STANCE_OPENINGS.match(topic), (key, topic)
        assert not STANCE_WORDS.search(topic), (key, topic)


def test_topics_never_script_the_speakers_past():
    for key, topic in _all_topics():
        assert not SCRIPTED_PAST.search(topic), (key, topic)


def test_reviewed_stances_and_scripted_pasts_are_gone():
    texts = [topic for _, topic in _all_topics()]
    for phrase in REMOVED_STANCES_AND_PASTS:
        assert not any(phrase in text for text in texts), phrase
    assert any('Teldrassil and life beneath its great branches' in text
               for text in texts)
    assert any('recovering from serious battle wounds' in text
               for text in texts)


def test_faction_views_have_no_dehumanising_terms():
    texts = list(FACTION_CRITICISM.values()) + [
        text for races in RACE_CRITICISM.values() for text in races.values()]
    for text in texts:
        for term in ('half-animals', 'filth', 'stupidity', 'called cows',
                     'called goats', 'Disgusting'):
            assert term not in text, (term, text)


def test_rumor_texts_never_order_a_stance():
    texts = [e['text'] for e in DUNGEON_RUMORS + RAID_RUMORS]
    texts += [t for e in LOCATION_RUMORS for t in e['text'].values()]
    texts += [t for e in REGION_RUMORS for t in e['rumors']]
    for text in texts:
        assert 'If the speaker' not in text, text
        assert not re.search(r'\b(condemn|mock|express hope)\b', text,
                             re.I), text


def test_region_and_war_front_wording_is_grounded():
    random.seed(9)
    speaker = themed.speaker_profile(_NoDb(), BOT)
    progression.clear_caches()
    for _ in range(40):
        topic = themed._region_rumor(_NoDb(), speaker,
                                     _audience(level=30), 'roleplay')
        if topic:
            text = topic.render()
            for phrase in ('details may be added', 'vague and mysterious',
                           'heard the same'):
                assert phrase not in text, phrase
            assert 'add no new details' in text
    for _ in range(60):
        topic = themed._faction_topic(speaker, 'roleplay')
        if topic.metadata['faction_topic'] == 'war_front':
            assert 'flared up' not in topic.render()
            assert 'not as news of a fresh battle' in topic.render()
    progression.clear_caches()


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} themed topic tests passed")
