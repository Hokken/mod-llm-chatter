#!/usr/bin/env python3
"""Themed topics, rumor gating and race+class notes.

Run directly from the module root:
  python tools/tests/test_themed_topics.py
"""

import importlib
import random
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

import chatter_progression as progression  # noqa: E402
import chatter_themed_topics as themed  # noqa: E402
from chatter_lore_data import (  # noqa: E402
    CLASS_TOPICS,
    RACE_CLASS_NOTES,
    RACE_CLASS_TOPICS,
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
    def __init__(self, earned):
        self.earned = earned

    def cursor(self, *args, **kwargs):
        db = self

        class _Cursor:
            def execute(self, query, params=None):
                self.rows = [(a,) for a in db.earned]

            def fetchall(self):
                return self.rows

        return _Cursor()


def _audience(level=60, team='Horde', race='Orc', ip=False, tier=0,
              limit=0, gm=False, guid=7, klass='Warrior'):
    return progression.parse_audience({
        'guid': guid, 'name': 'Player', 'level': level, 'team': team,
        'race': race, 'class': klass, 'is_gm': gm,
        'ip_active': ip, 'progression_tier': tier,
        'progression_limit': limit, 'ip_zg_tier': 3, 'ip_za_tier': 12,
    })


BOT = {'guid': 5, 'name': 'Grom', 'race': 'Orc', 'class': 'Warrior',
       'level': 60}


def test_every_playable_combination_has_topics_and_notes():
    for race, classes in PLAYABLE.items():
        assert RACE_TOPICS.get(race), race
        for klass in classes:
            for style in _styles(klass):
                assert CLASS_TOPICS.get(style), style
                assert RACE_CLASS_TOPICS.get((race, style)), (race, style)
                assert RACE_CLASS_NOTES.get((race, style)), (race, style)


def test_parse_audience_accepts_json_and_rejects_garbage():
    parsed = progression.parse_audience(
        '{"guid": 3, "level": 20, "team": "Alliance"}')
    assert parsed['guid'] == 3 and parsed['team'] == 'Alliance'
    assert parsed['ip_active'] is False
    assert progression.parse_audience('not json') is None
    assert progression.parse_audience({'guid': 0, 'level': 5}) is None
    assert progression.parse_audience(None) is None


def test_content_unlocked_without_ip_and_for_gms():
    northrend = EXPANSION_RUMORS['Northrend']
    assert progression.content_unlocked(_audience(ip=False), northrend)
    assert progression.content_unlocked(_audience(ip=True, gm=True),
                                        northrend)
    assert not progression.content_unlocked(_audience(ip=True, tier=12),
                                            northrend)
    assert progression.content_unlocked(_audience(ip=True, tier=13),
                                        northrend)


def test_progression_limit_and_max_tier():
    outland = EXPANSION_RUMORS['Outland']
    assert not progression.content_unlocked(
        _audience(ip=True, tier=8, limit=7), outland)
    classic_naxx = next(r for r in RAID_RUMORS
                        if r.get('max_tier') is not None
                        and r['name'] == 'Naxxramas')
    assert progression.content_unlocked(
        _audience(ip=True, tier=classic_naxx['max_tier']), classic_naxx)
    assert not progression.content_unlocked(
        _audience(ip=True, tier=classic_naxx['max_tier'] + 1), classic_naxx)


def test_zul_gurub_tier_follows_ip_config():
    zg = next(r for r in RAID_RUMORS if r['required_tier'] == 'zul_gurub')
    audience = _audience(ip=True, tier=2)
    assert not progression.content_unlocked(audience, zg)
    audience['ip_zg_tier'] = 2
    assert progression.content_unlocked(audience, zg)


def test_tbc_race_zones_are_open_in_classic_tiers():
    for name in ('Ghostlands', 'Bloodmyst Isle'):
        zone = next(r for r in REGION_RUMORS if r['name'] == name)
        assert progression.content_unlocked(
            _audience(ip=True, tier=0, race='Orc'), zone)
        assert progression.content_unlocked(
            _audience(ip=True, tier=0, race='Human'), zone)


def test_achievement_blocks_completed_dungeons():
    progression.clear_caches()
    entry = next(d for d in DUNGEON_RUMORS if d['achievements'])
    db = _AchievementDb([entry['achievements'][0]])
    assert progression.has_completed(db, 99, entry['achievements'])
    assert not progression.has_completed(db, 99, ())
    progression.clear_caches()
    assert not progression.has_completed(_AchievementDb([]), 98,
                                         entry['achievements'])


def test_dungeon_rumor_respects_level_and_completion():
    progression.clear_caches()
    level = 25
    eligible = [d for d in DUNGEON_RUMORS
                if d['min_level'] <= level <= d['max_level']]
    assert eligible
    earned = [a for d in eligible for a in d['achievements']]
    speaker = themed.speaker_profile(_NoDb(), BOT)
    assert themed._place_rumor(
        _AchievementDb(earned), speaker, _audience(level=level, guid=11),
        'roleplay', DUNGEON_RUMORS, 'dungeon',
    ) is None or all(not d['achievements'] for d in eligible)
    progression.clear_caches()
    topic = themed._place_rumor(
        _AchievementDb([]), speaker, _audience(level=level, guid=12),
        'roleplay', DUNGEON_RUMORS, 'dungeon',
    )
    assert topic and topic.metadata['rumor'] in {d['name'] for d in eligible}
    assert 'Dungeon' in topic.render() or 'dungeon' in topic.render()


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


def test_expansion_rumor_framing_depends_on_bot_level():
    audience = _audience(level=68)
    low = themed.speaker_profile(_NoDb(), dict(BOT, level=60))
    high = themed.speaker_profile(_NoDb(), dict(BOT, level=80))
    heard = themed._expansion_rumor(_NoDb(), low, audience, 'roleplay')
    seen = themed._expansion_rumor(_NoDb(), high, audience, 'roleplay')
    assert heard.metadata['rumor_seen'] is False
    assert 'rumor you have heard' in heard.render()
    assert seen.metadata['rumor_seen'] is True
    assert 'has been there' in seen.render()
    assert themed._expansion_rumor(
        _NoDb(), low, _audience(level=40), 'roleplay') is None


def test_ip_gating_hides_locked_expansion():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    locked = _audience(level=58, ip=True, tier=7)
    assert themed._expansion_rumor(_NoDb(), speaker, locked,
                                   'roleplay') is None
    open_ = _audience(level=58, ip=True, tier=8)
    assert themed._expansion_rumor(_NoDb(), speaker, open_,
                                   'roleplay') is not None


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


def test_rumors_need_an_audience():
    config = {f'LLMChatter.ThemedTopics.{k}Weight': 0 for k in (
        'Faction', 'Race', 'Class', 'RaceClass')}
    assert themed.pick_themed_topic(
        _NoDb(), config, 'general', BOT, None, roll=False) is None


def test_channel_chance_and_enable_switch():
    with patch.object(themed.random, 'randint', return_value=61):
        assert themed.pick_themed_topic(
            _NoDb(), {}, 'guild', BOT, _audience()) is None
    assert themed.pick_themed_topic(
        _NoDb(), {'LLMChatter.ThemedTopics.Enable': '0'}, 'guild', BOT,
        _audience(), roll=False) is None


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


def test_zone_topics_force_zone_naming():
    zone = themed.guild_zone_topic(1519, 'roleplay')
    assert zone.name_zone and 'Stormwind' in zone.subject
    weather = themed.guild_zone_weather_topic(1519, 'light rain', 'normal')
    assert weather.name_zone and 'light rain' in weather.render()
    assert themed.guild_zone_topic(0, 'roleplay') is None


def test_race_class_notes_split_priests():
    light = race_class_note('Undead', 'Priest')
    shadow = race_class_note('Undead', 'Priest', actual_role='ranged_dps')
    assert 'Light Priest' in light and 'Shadow Priest' in shadow
    assert race_class_note('Undead', 'Priest',
                           class_style='Shadow Priest') == shadow
    assert 'Your people and calling' in build_race_class_context(
        'Orc', 'Warrior')


def _trainer_names(tree):
    return {race: {t['name'] for t in trainers}
            for race, trainers in tree.items()}


def test_trainer_data_covers_every_race_and_skill():
    for tree, abilities in ((PROFESSION_TRAINERS, PROFESSION_ABILITIES),
                            (CLASS_TRAINERS, CLASS_ABILITIES)):
        assert set(tree['Alliance']) == set(themed.ALLIANCE_RACES)
        assert set(tree['Horde']) == set(themed.HORDE_RACES)
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


def test_trainer_rumor_level_bands():
    for kind, full, reduced, gone in (('profession', 20, 21, 31),
                                      ('trainer', 15, 16, 26)):
        base = themed._kind_weight({}, kind, _audience(level=1))
        assert base == 12
        assert themed._kind_weight({}, kind, _audience(level=full)) == 12
        assert 0 < themed._kind_weight(
            {}, kind, _audience(level=reduced)) < 12
        assert themed._kind_weight({}, kind, _audience(level=gone)) == 0
    config = {'LLMChatter.ThemedTopics.TrainerRumorReducedPercent': '50'}
    assert themed._kind_weight(config, 'trainer', _audience(level=20)) == 6
    assert themed._kind_weight({}, 'dungeon', _audience(level=80)) == 12


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
            topic = build(_NoDb(), speaker,
                          _audience(level=10, team='Horde', race='Tauren'),
                          'roleplay')
            assert topic.metadata['rumor'] in horde
            topic = build(_NoDb(), speaker,
                          _audience(level=10, team='Alliance', race='Gnome'),
                          'normal')
            assert topic.metadata['rumor'] in alliance


def test_trainer_rumors_split_own_and_other_half_and_half():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    audience = _audience(level=8, team='Alliance', race='Night Elf',
                         klass='Druid')
    with patch.object(themed.random, 'random', return_value=0.1):
        own = themed._profession_rumor(_NoDb(), speaker, audience, 'roleplay')
        assert own.metadata['trainer_race_list'] == 'Night Elf'
        own = themed._class_trainer_rumor(_NoDb(), speaker, audience,
                                          'roleplay')
        assert own.metadata['trainer_class'] == 'Druid'
    with patch.object(themed.random, 'random', return_value=0.9):
        other = themed._profession_rumor(_NoDb(), speaker, audience,
                                         'roleplay')
        assert other.metadata['trainer_race_list'] != 'Night Elf'
        other = themed._class_trainer_rumor(_NoDb(), speaker, audience,
                                            'roleplay')
        assert other.metadata['trainer_class'] != 'Druid'


def test_trainer_rumors_ignore_individual_progression():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    audience = _audience(level=5, team='Alliance', race='Human', ip=True,
                         tier=0, limit=1)
    places = set()
    random.seed(5)
    for _ in range(300):
        places.add(themed._profession_rumor(
            _NoDb(), speaker, audience, 'roleplay').metadata['rumor'])
    assert 'Farii' in places


def test_death_knight_audience_gets_other_class_trainers():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    audience = _audience(level=10, team='Horde', race='Orc',
                         klass='Death Knight')
    with patch.object(themed.random, 'random', return_value=0.1):
        topic = themed._class_trainer_rumor(_NoDb(), speaker, audience,
                                            'roleplay')
    assert topic and topic.metadata['trainer_class'] != 'Death Knight'


def test_trainer_rumor_prompt_and_channels():
    speaker = themed.speaker_profile(_NoDb(), BOT)
    topic = themed._class_trainer_rumor(
        _NoDb(), speaker, _audience(level=5), 'normal')
    text = topic.render()
    assert topic.metadata['rumor'] in text
    assert 'Name the master and the place' in text
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


def test_priest_style_reads_talent_totals():
    progression.clear_caches()
    with patch('chatter_db.get_character_talents',
               return_value={'tree_totals': {'Shadow': 40, 'Holy': 5}}):
        assert progression.priest_style(object(), 77) == 'Shadow Priest'
    progression.clear_caches()
    with patch('chatter_db.get_character_talents',
               return_value={'tree_totals': {'Shadow': 10, 'Holy': 10}}):
        assert progression.priest_style(object(), 78) == 'Light Priest'
    assert progression.priest_style(None, 0) == 'Light Priest'


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} themed topic tests passed")
