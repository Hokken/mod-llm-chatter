#!/usr/bin/env python3
"""Location topics and the universal topic pools.

Checks location_topics.json, how a topic tied to a place is drawn and
worded, where it reaches the prompts (party, threads, General,
proximity, raid), the party same-zone rule, and that the universal
roleplay pools no longer assume weather, places or the speaker's life.

Run directly from the module root:
  python tools/tests/test_location_topics.py
"""

import importlib
import json
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
                "Anthropic"
                if module_name == "anthropic"
                else "OpenAI"
            )
            setattr(module, class_name, type(class_name, (), {}))

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module("mysql.connector")
        setattr(mysql_module, "connector", connector_module)


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_constants as constants  # noqa: E402
import chatter_group_prompts as group_prompts  # noqa: E402
import chatter_location_topics as lt  # noqa: E402
import chatter_threads as threads  # noqa: E402

DATA = json.loads(
    (TOOLS_DIR / 'location_topics.json').read_text(encoding='utf-8')
)
ALWAYS = {'LLMChatter.LocationTopics.Chance': '100'}
NEVER = {'LLMChatter.LocationTopics.Chance': '0'}
# Zone 330 has a description but no topic list.
ELWYNN, DEADMINES, ICC, WSG, NO_TOPICS = 12, 36, 631, 489, 330
BOT = {'name': 'Aliss', 'class': 'Mage', 'race': 'Human',
       'level': 10, 'gender': 'female'}


def _reset():
    lt.configure_location_topics({})
    threads.configure_threads({})


# -- Data contracts ----------------------------------------------------

def test_every_entry_maps_to_a_described_place():
    assert len(DATA['zones']) >= 70 and len(DATA['maps']) >= 70
    for zone_id, entry in DATA['zones'].items():
        assert int(zone_id) in constants.ZONE_FLAVOR, zone_id
        assert entry['name'] and len(entry['topics']) >= 15, zone_id
    for map_id, entry in DATA['maps'].items():
        assert int(map_id) in constants.DUNGEON_FLAVOR, map_id
        assert entry['kind'] in ('dungeon', 'raid'), map_id
        assert entry['name'] and len(entry['topics']) >= 15, map_id
    assert DATA['maps'][str(ICC)]['kind'] == 'raid'
    assert DATA['maps'][str(DEADMINES)]['kind'] == 'dungeon'


def test_topics_are_clean_subjects():
    # A topic names a subject; it does not cast the speaker as someone
    # arguing or complaining, claim a current moment, or use game terms.
    framed = re.compile(
        r"^(Heroes|Some [a-z ]+?) (arguing|debating|discussing|"
        r"complaining|wondering|boasting|telling|comparing)\b")
    moment = re.compile(r"\b(currently|right now|this season)\b", re.I)
    # "Loot" (plunder) and "quest" (a mission) are in-world words.
    jargon = re.compile(
        r"\b(players?|respawn\w*|questline|aggro|raid boss|instance)\b",
        re.I)
    for table in DATA.values():
        for entry in table.values():
            topics = entry['topics']
            assert len(set(topics)) == len(topics), entry['name']
            for topic in topics:
                assert topic and topic == topic.strip(), entry['name']
                assert not framed.search(topic), topic
                assert not moment.search(topic), topic
                assert not jargon.search(topic), topic


def test_scarlet_enclave_has_name_and_description():
    assert constants.ZONE_NAMES[4298] == 'Plaguelands: The Scarlet Enclave'
    assert constants.ZONE_FLAVOR[4298].startswith('The Scarlet Enclave:')
    assert '4298' in DATA['zones']
    from locales import deDE, esES, frFR, ruRU
    for module in (ruRU, deDE, frFR, esES):
        assert 4298 in module.ZONE_NAMES and 4298 in module.ZONE_FLAVOR


# -- Drawing a topic ---------------------------------------------------

def test_zone_topic_carries_place_and_description():
    _reset()
    topic = lt.location_topic_for(ELWYNN, 0)
    assert topic.place == 'Elwynn Forest' and topic.kind == 'zone'
    assert topic.topic in DATA['zones'][str(ELWYNN)]['topics']
    assert topic.description == constants.ZONE_FLAVOR[ELWYNN]
    lines = topic.lines()
    assert lines[0].startswith('A subject tied to Elwynn Forest')
    assert 'belongs to Elwynn Forest itself' in lines[0]
    assert lines[1] == (
        f"Location description: {constants.ZONE_FLAVOR[ELWYNN]}")
    assert topic.lines(with_description=False) == lines[:1]


def test_instances_use_their_own_list():
    _reset()
    dungeon = lt.location_topic_for(ELWYNN, DEADMINES)
    assert dungeon.kind == 'dungeon'
    assert dungeon.topic in DATA['maps'][str(DEADMINES)]['topics']
    assert dungeon.description == constants.DUNGEON_FLAVOR[DEADMINES]
    assert lt.location_topic_for(0, ICC).kind == 'raid'


def test_no_topic_without_data_in_battlegrounds_or_when_disabled():
    _reset()
    assert lt.location_topic_for(0, WSG) is None
    assert lt.location_topic_for(NO_TOPICS, 0) is None
    assert lt.location_topic_for(0, 0) is None
    lt.configure_location_topics({'LLMChatter.LocationTopics.Enable': '0'})
    assert lt.location_topic_for(ELWYNN, 0) is None
    _reset()


def test_chance_is_honored_and_clamped():
    lt.configure_location_topics(NEVER)
    assert all(lt.roll_location_topic(ELWYNN, 0) is None
               for _ in range(50))
    lt.configure_location_topics(ALWAYS)
    assert all(lt.roll_location_topic(ELWYNN, 0) for _ in range(50))
    lt.configure_location_topics(
        {'LLMChatter.LocationTopics.Chance': '250'})
    assert lt._settings['chance'] == 100
    _reset()
    assert lt._settings == {'enable': True, 'chance': 70}


# -- Party -------------------------------------------------------------

def _rows(*zones):
    return [{'zone': zone, 'map': map_id} for zone, map_id in zones]


def test_party_needs_player_and_bots_in_the_same_place():
    import chatter_group as group

    _reset()
    with patch.object(group, 'get_character_location',
                      return_value=(ELWYNN, 0)):
        same = group._party_location_topic(
            None, 'roleplay', 'Lyn', _rows((ELWYNN, 0), (ELWYNN, 0)),
            ELWYNN, 0)
        assert same is not None and same.place == 'Elwynn Forest'
        # One bot in another zone: nobody gets the topic.
        assert group._party_location_topic(
            None, 'roleplay', 'Lyn', _rows((ELWYNN, 0), (40, 0)),
            ELWYNN, 0) is None
        assert group._party_location_topic(
            None, 'normal', 'Lyn', _rows((ELWYNN, 0)), ELWYNN, 0) is None
        assert group._party_location_topic(
            None, 'roleplay', None, _rows((ELWYNN, 0)), ELWYNN, 0) is None
    with patch.object(group, 'get_character_location',
                      return_value=(40, 0)):
        assert group._party_location_topic(
            None, 'roleplay', 'Lyn', _rows((ELWYNN, 0)), ELWYNN, 0) is None
    with patch.object(group, 'get_character_location',
                      return_value=(1581, DEADMINES)):
        inside = group._party_location_topic(
            None, 'roleplay', 'Lyn', _rows((1581, DEADMINES)),
            1581, DEADMINES)
        assert inside.kind == 'dungeon'


def test_party_statement_uses_the_location_topic():
    import chatter_group as group

    _reset()
    topic = lt.location_topic_for(ELWYNN, 0)
    prompt = str(group.build_idle_chatter_prompt(
        BOT, ['curious'], 'roleplay', zone_id=ELWYNN, map_id=0,
        location_topic=topic,
    ))
    assert topic.subject_line() in prompt
    assert prompt.count(constants.ZONE_FLAVOR[ELWYNN]) == 1
    assert "You're in a party, currently" not in prompt
    # In a dungeon the topic now gives the idle line a subject.
    inside = lt.location_topic_for(1581, DEADMINES)
    prompt = str(group.build_idle_chatter_prompt(
        BOT, ['curious'], 'roleplay', zone_id=1581, map_id=DEADMINES,
        location_topic=inside,
    ))
    assert inside.subject_line() in prompt
    assert prompt.count(constants.DUNGEON_FLAVOR[DEADMINES]) == 1


def test_bot_question_can_ask_about_the_place():
    _reset()
    topic = lt.location_topic_for(ELWYNN, 0)
    prompt = str(group_prompts.build_bot_question_prompt(
        BOT, ['curious'], 'roleplay', 'Lyn', 'Warrior', 'Dwarf',
        'male', 12, zone_id=ELWYNN, map_id=0, location_topic=topic,
    ))
    assert (f"about {topic.topic} (a subject tied to Elwynn Forest, "
            "where you both are now)") in prompt


# -- Conversation threads ----------------------------------------------

def test_thread_location_source_needs_a_topic_and_weight():
    _reset()
    assert 'location' not in {
        threads._pick_source(False, True, True) for _ in range(2000)}
    picked = {threads._pick_source(True, True, False, True)
              for _ in range(2000)}
    assert 'location' in picked and 'pool' not in picked
    threads.configure_threads(
        {'LLMChatter.Threads.LocationTopicWeight': '0'})
    assert 'location' not in {
        threads._pick_source(False, True, False, True)
        for _ in range(2000)}
    _reset()


def test_thread_nudge_names_the_place():
    _reset()
    topic = lt.location_topic_for(ELWYNN, 0)
    with patch.object(threads, '_pick_source', return_value='location'):
        turn = threads.plan_idle_turn(
            ('party', 9101), ['Aliss', 'Borin'],
            topic_pool=constants.AMBIENT_CHAT_TOPICS_RP,
            location_topic=topic,
        )
    assert turn.kind == 'new' and turn.source == 'location'
    assert turn.pool_topic == topic.topic
    assert turn.location_place == 'Elwynn Forest'
    assert (f"A possible fresh subject tied to Elwynn Forest, where the "
            f"speakers are now: {topic.topic}.") in turn.prompt_block
    threads.clear_all()


# -- General, proximity, raid ------------------------------------------

def test_general_topics_are_roleplay_only():
    import chatter_ambient as ambient

    _reset()
    assert ambient._general_location_topic('normal', ELWYNN) is None
    assert ambient._general_location_topic('roleplay', ELWYNN).place == (
        'Elwynn Forest')
    lt.configure_location_topics(ALWAYS)
    rolled = ambient._rolled_location(
        lt.location_topic_for(ELWYNN, 0), None, None, ELWYNN)
    assert rolled is not None
    # A thread, or a guild or themed subject, keeps the turn.
    assert ambient._rolled_location(rolled, object(), None, ELWYNN) is None
    assert ambient._rolled_location(rolled, None, 'guild', ELWYNN) is None
    assert ambient._location_or_pool(rolled, ['x']) == rolled.subject_line()
    assert ambient._location_or_pool(None, ['x']) == 'x'
    _reset()


def test_proximity_in_world_speakers_get_location_topics():
    import chatter_proximity as prox

    extra = {'zone_id': ELWYNN, 'map_id': 0}
    lt.configure_location_topics(ALWAYS)
    assert prox._in_world_topic(extra).startswith(
        'A subject tied to Elwynn Forest')
    assert prox._playerbot_topic(
        {'LLMChatter.ChatterMode': 'roleplay'}, extra
    ).startswith('A subject tied to')
    # Normal-mode playerbots keep their player-talk pool.
    assert prox._playerbot_topic(
        {'LLMChatter.ChatterMode': 'normal'}, extra
    ) in constants.PROXIMITY_PLAYER_CHAT_TOPICS
    lt.configure_location_topics(NEVER)
    assert prox._in_world_topic(extra) in constants.PROXIMITY_CHAT_TOPICS
    _reset()


def test_raid_idle_location_lines():
    import chatter_raid_prompts as raid

    lt.configure_location_topics(ALWAYS)
    rp = {'_config': {'LLMChatter.ChatterMode': 'roleplay'},
          'map_id': ICC, 'zone_id': 4812, 'raid_name': 'Icecrown Citadel'}
    lines = raid._raid_location_lines(rp)
    # Icecrown Citadel's Lore line already describes the raid.
    assert len(lines) == 1 and 'Icecrown Citadel' in lines[0]
    lines = raid._raid_location_lines(dict(rp, raid_name='Unknown'))
    assert len(lines) == 2
    assert raid._raid_location_lines(
        dict(rp, _config={'LLMChatter.ChatterMode': 'normal'})) == []
    assert raid._raid_location_lines(dict(rp, map_id=0)) == []
    prompt = str(raid.build_raid_banter_prompt(rp, {'bot_name': 'Aliss'}))
    assert 'A subject tied to Icecrown Citadel' in prompt
    assert 'Topic hint:' not in prompt
    _reset()


# -- Universal pools ---------------------------------------------------

def test_roleplay_pools_assume_nothing_untracked():
    banned = re.compile(
        r"\b(weather|rain|snow|frost|thaw|storm|sunshine|sunset|"
        r"season|autumn|harvest|garden|fence|roof|curtains|chimney|"
        r"market|bakery|port|canal|town hall|mayor|tannery|well water|"
        r"pond|graveyard|ruins|this place|this area|this region|nearby|"
        r"brewfest|hallow's end|winter veil|lunar festival|patrol|"
        r"shift|bio break|keys|leveling|profession|mount)\b", re.I)
    pools = {
        'ambient rp': constants.AMBIENT_CHAT_TOPICS_RP,
        'proximity': constants.PROXIMITY_CHAT_TOPICS,
        'guild rp': constants.GUILD_CHAT_TOPICS_RP,
        'bot questions': group_prompts.BOT_QUESTION_TOPICS,
    }
    for label, pool in pools.items():
        assert len(set(pool)) == len(pool), label
        for topic in pool:
            assert not banned.search(topic), (label, topic)
    assert len(constants.AMBIENT_CHAT_TOPICS_RP) >= 90
    assert len(constants.PROXIMITY_CHAT_TOPICS) >= 140
    assert not hasattr(constants, 'PROXIMITY_WEATHER_TOPICS')
    rp_categories = ' '.join(constants.RP_MESSAGE_CATEGORIES).lower()
    for phrase in ('weather', 'time of day', 'ruins', 'next town',
                   'fight you just had'):
        assert phrase not in rp_categories, phrase


def test_normal_pool_keeps_its_player_subjects():
    for topic in ('commenting on the weather', 'talking about their mount',
                  'joking about needing a bio break'):
        assert topic in constants.AMBIENT_CHAT_TOPICS
        assert topic not in constants.AMBIENT_CHAT_TOPICS_RP


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} location topic tests passed")
