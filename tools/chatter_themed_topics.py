"""Themed topics for Guild, General and party chat.

Faction, race, class and race+class topics are keyed to the first
speaker. Rumors are keyed to the ``audience`` (the real player who will
read the line): their level, faction, earned achievements and
mod-individual-progression tier decide what may be mentioned.
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from chatter_lore_data import (
    CLASS_TOPICS,
    FACTION_CRITICISM,
    FACTION_WAR_FRONTS,
    LOCAL_CONFLICTS,
    RACE_CLASS_TOPICS,
    RACE_CRITICISM,
    RACE_TOPICS,
)
from chatter_progression import (
    class_style,
    content_unlocked,
    has_completed,
    level_in_range,
)
from chatter_rumor_data import (
    CAVERNS_OF_TIME_INTRO,
    DUNGEON_RUMORS,
    EXPANSION_RUMORS,
    LOCATION_RUMORS,
    RAID_RUMORS,
    REGION_RUMORS,
)
from chatter_shared import get_zone_flavor, get_zone_name
from chatter_trainer_rumor_data import (
    CLASS_ABILITIES,
    CLASS_TRAINER_RUMOR_LEVELS,
    CLASS_TRAINERS,
    PROFESSION_ABILITIES,
    PROFESSION_RUMOR_LEVELS,
    PROFESSION_TRAINERS,
)

logger = logging.getLogger(__name__)

ALLIANCE_RACES = ('Human', 'Dwarf', 'Night Elf', 'Gnome', 'Draenei')
HORDE_RACES = ('Orc', 'Undead', 'Tauren', 'Troll', 'Blood Elf')
RACE_NAMES_BY_ID = {
    1: 'Human', 2: 'Orc', 3: 'Dwarf', 4: 'Night Elf', 5: 'Undead',
    6: 'Tauren', 7: 'Gnome', 8: 'Troll', 10: 'Blood Elf', 11: 'Draenei',
}
CLASS_NAMES_BY_ID = {
    1: 'Warrior', 2: 'Paladin', 3: 'Hunter', 4: 'Rogue', 5: 'Priest',
    6: 'Death Knight', 7: 'Shaman', 8: 'Mage', 9: 'Warlock', 11: 'Druid',
}

CHANNEL_KINDS = {
    'guild': ('faction', 'race', 'class', 'race_class', 'expansion',
              'dungeon', 'raid', 'location', 'region', 'profession',
              'trainer'),
    'general': ('faction', 'race', 'class', 'race_class', 'expansion',
                'dungeon', 'raid', 'location', 'region', 'profession',
                'trainer'),
    'party': ('class', 'race_class'),
}
CHANNEL_CHANCE = {
    'guild': ('LLMChatter.ThemedTopics.GuildChance', 60),
    'general': ('LLMChatter.ThemedTopics.GeneralChance', 60),
    'party': ('LLMChatter.ThemedTopics.PartyChance', 5),
}
KIND_WEIGHT = {
    'faction': ('LLMChatter.ThemedTopics.FactionWeight', 12),
    'race': ('LLMChatter.ThemedTopics.RaceWeight', 18),
    'class': ('LLMChatter.ThemedTopics.ClassWeight', 18),
    'race_class': ('LLMChatter.ThemedTopics.RaceClassWeight', 7),
    'expansion': ('LLMChatter.ThemedTopics.ExpansionRumorWeight', 8),
    'dungeon': ('LLMChatter.ThemedTopics.DungeonRumorWeight', 12),
    'raid': ('LLMChatter.ThemedTopics.RaidRumorWeight', 6),
    'location': ('LLMChatter.ThemedTopics.LocationRumorWeight', 10),
    'region': ('LLMChatter.ThemedTopics.RegionRumorWeight', 9),
    'profession': ('LLMChatter.ThemedTopics.ProfessionRumorWeight', 12),
    'trainer': ('LLMChatter.ThemedTopics.ClassTrainerRumorWeight', 12),
}
RUMOR_KINDS = ('expansion', 'dungeon', 'raid', 'location', 'region',
               'profession', 'trainer')
LEVEL_BANDS = {
    'profession': PROFESSION_RUMOR_LEVELS,
    'trainer': CLASS_TRAINER_RUMOR_LEVELS,
}


@dataclass
class ThemedTopic:
    kind: str
    subject: str
    lines: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    name_zone: bool = False

    def render(self) -> str:
        return " ".join([self.subject.rstrip('.') + '.'] + self.lines)


def cfg_int(config, key, default):
    try:
        return int((config or {}).get(key, default))
    except (TypeError, ValueError):
        return default


def chance_hit(config, key, default):
    chance = max(0, min(100, cfg_int(config, key, default)))
    return random.randint(1, 100) <= chance


def _race_name(value):
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return RACE_NAMES_BY_ID.get(int(value), '')
    return str(value or '')


def _class_name(value):
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return CLASS_NAMES_BY_ID.get(int(value), '')
    return str(value or '')


def race_faction(race):
    if race in ALLIANCE_RACES:
        return 'Alliance'
    if race in HORDE_RACES:
        return 'Horde'
    return ''


def speaker_profile(db, bot: Dict, faction: str = '') -> Dict:
    """Normalize a bot dict (names or ids) into what the builders need."""
    race = _race_name(bot.get('race'))
    klass = _class_name(bot.get('class'))
    guid = bot.get('guid') or 0
    return {
        'guid': guid,
        'name': bot.get('name') or '',
        'race': race,
        'class': klass,
        'class_style': class_style(db, guid, klass),
        'level': int(bot.get('level') or 0),
        'faction': faction or race_faction(race),
    }


def _enemy(faction):
    return 'Horde' if faction == 'Alliance' else 'Alliance'


def _faction_line(speaker):
    return (f"{speaker['name']} is {_a(speaker['race'])} {speaker['race']} "
            f"{speaker['class_style'] or speaker['class']} who fights for "
            f"the {speaker['faction']}.")


def _a(word):
    return 'an' if word[:1].upper() in 'AEIOU' else 'a'


def _mode_lines(mode, rumor=False, place_kind=''):
    if mode == 'roleplay':
        lines = []
        if place_kind == 'raid':
            lines.append(
                "Never use the word \"raid\": speak as someone who lives in "
                "this world.")
        if place_kind == 'dungeon':
            lines.append(
                "\"Dungeon\" is adventurer slang; the place may really be a "
                "fortress, village, city, mine or temple, so describe it as "
                "what it is.")
        return lines
    return ["Frame it the way a player would chat about their character "
            "and the world of the game."]


# --------------------------------------------------------------------------
# Speaker-keyed topics
# --------------------------------------------------------------------------

def _faction_topic(speaker, mode):
    faction = speaker['faction']
    if faction not in ('Alliance', 'Horde'):
        return None
    enemy = _enemy(faction)
    choice = random.choice(('war_front', 'criticism', 'race', 'conflict'))
    lines = [_faction_line(speaker)]
    if choice == 'war_front':
        zone, text = random.choice(list(FACTION_WAR_FRONTS.items()))
        subject = (f"rumors that the war between the Horde and the Alliance "
                   f"has flared up again in {zone}")
        lines += [f"Background: {text}",
                  f"Side with the {faction} and show contempt or hatred for "
                  f"the {enemy}."]
        meta = {'faction_topic': choice, 'faction_zone': zone}
    elif choice == 'criticism':
        subject = f"contempt for the {enemy}"
        lines += [f"Typical {faction} criticism of the {enemy}: "
                  f"{FACTION_CRITICISM[faction]}"]
        meta = {'faction_topic': choice}
    elif choice == 'race':
        race, text = random.choice(list(RACE_CRITICISM[faction].items()))
        subject = (f"criticism, contempt or mockery of the {race}, a race of "
                   f"the {enemy}")
        lines += [f"What the {faction} holds against the {race}: {text}",
                  f"Talk about the {race} only, no other race."]
        meta = {'faction_topic': choice, 'faction_target_race': race}
    else:
        text = random.choice(LOCAL_CONFLICTS[faction])
        subject = "a recent local clash with the " + enemy
        lines += [f"What happened: {text}",
                  f"Condemn the {enemy} and stand by the {faction}; new "
                  "details may be invented."]
        meta = {'faction_topic': choice}
    lines += _mode_lines(mode)
    return ThemedTopic('faction', subject, lines, meta)


def _race_topic(speaker, mode):
    topics = RACE_TOPICS.get(speaker['race'])
    if not topics:
        return None
    topic = random.choice(topics)
    lines = [
        _faction_line(speaker),
        f"This topic belongs to {speaker['name']}'s own {speaker['race']} "
        "identity. Others may be of other races and answer from their own "
        "point of view.",
    ] + _mode_lines(mode)
    return ThemedTopic('race', topic, lines, {'themed_race': speaker['race']})


def _class_topic(speaker, mode):
    style = speaker['class_style']
    topics = CLASS_TOPICS.get(style)
    if not topics:
        return None
    topic = random.choice(topics)
    lines = [
        _faction_line(speaker),
        f"This topic comes from {speaker['name']}'s calling as "
        f"{_a(style)} {style}. Others may follow other callings and answer "
        "from their own point of view.",
    ] + _mode_lines(mode)
    return ThemedTopic('class', topic, lines, {'themed_class': style})


def _race_class_topic(speaker, mode):
    style = speaker['class_style']
    topics = RACE_CLASS_TOPICS.get((speaker['race'], style))
    if not topics:
        return None
    topic = random.choice(topics)
    lines = [
        _faction_line(speaker),
        f"This topic comes from being {_a(speaker['race'])} "
        f"{speaker['race']} {style}, both race and calling. Others may "
        "answer from their own race and calling.",
    ] + _mode_lines(mode)
    return ThemedTopic('race_class', topic, lines,
                       {'themed_race': speaker['race'],
                        'themed_class': style})


# --------------------------------------------------------------------------
# Audience-keyed rumors
# --------------------------------------------------------------------------

def _rumor_lines(speaker):
    return [
        _faction_line(speaker),
        "Tell it to everyone listening; do not address anyone directly.",
    ]


def _expansion_rumor(db, speaker, audience, mode):
    options = [e for e in EXPANSION_RUMORS.values()
               if level_in_range(audience, e) and content_unlocked(audience, e)]
    if not options:
        return None
    entry = random.choice(options)
    facts = random.sample(entry['facts'], min(3, len(entry['facts'])))
    seen = speaker['level'] > audience['level']
    land = entry['name']
    hint = ("the lands beyond the Dark Portal" if land == 'Outland'
            else "the frozen continent in the north")
    subject = (f"what {speaker['name']} has seen with their own eyes in {land}"
               if seen else f"rumors about {land}")
    lines = _rumor_lines(speaker) + [
        f"Name {land} or call it something like \"{hint}\" so it is clear "
        "which land is meant.",
        "Ideas to retell in your own words (you may invent or expand): "
        + "; ".join(facts) + ".",
        ("Speak as someone who has been there." if seen
         else "Frame it as a rumor you have heard."),
        "Others may show interest in going, or unease and a wish to stay "
        "away.",
    ] + _mode_lines(mode, rumor=True)
    return ThemedTopic('expansion', subject, lines,
                       {'rumor': land, 'rumor_seen': seen})


def _place_rumor(db, speaker, audience, mode, pool, kind):
    options = [
        e for e in pool
        if level_in_range(audience, e)
        and content_unlocked(audience, e)
        and not has_completed(db, audience['guid'], e.get('achievements'))
    ]
    if not options:
        return None
    entry = random.choice(options)
    lines = _rumor_lines(speaker) + [f"What is known: {entry['text']}"]
    if entry.get('caverns_of_time') and CAVERNS_OF_TIME_INTRO:
        lines.append(f"Where it is: {CAVERNS_OF_TIME_INTRO}")
    lines += [
        "Try to spark interest in going there, or warn of the threat and "
        "the need to end it.",
        "Others may show interest, wish the place cleansed and the threat "
        "ended, or voice fear.",
    ] + _mode_lines(mode, rumor=True, place_kind=kind)
    return ThemedTopic(kind, f"rumors about {entry['name']}", lines,
                       {'rumor': entry['name']})


def _location_rumor(db, speaker, audience, mode):
    team = audience.get('team')
    options = [
        e for e in LOCATION_RUMORS
        if team in e['factions'] and team in e['text']
        and level_in_range(audience, e) and content_unlocked(audience, e)
    ]
    if not options:
        return None
    entry = random.choice(options)
    lines = _rumor_lines(speaker) + [
        f"What is known about {entry['name']}: {entry['text'][team]}",
        f"Name {entry['name']} and try to spark interest in it, or report "
        "its threats and the need to deal with them.",
        "Others may show interest, hope things there improve, want to "
        "visit, or voice fear.",
    ] + _mode_lines(mode, rumor=True)
    return ThemedTopic('location', f"news about {entry['name']}", lines,
                       {'rumor': entry['name']})


def _region_rumor(db, speaker, audience, mode):
    team = audience.get('team')
    options = [
        e for e in REGION_RUMORS
        if team in e['factions'] and e['rumors']
        and level_in_range(audience, e) and content_unlocked(audience, e)
    ]
    if not options:
        return None
    entry = random.choice(options)
    rumor = random.choice(entry['rumors'])
    place = entry.get('general_region') or entry['name']
    lines = _rumor_lines(speaker) + [
        f"The rumor to retell in your own words (details may be added): "
        f"{rumor}",
        f"Say that it happens in {place}. Keep it vague and mysterious, a "
        "rumor rather than hard fact.",
        "Others may say they heard the same, want to check it, or doubt "
        "it.",
    ] + _mode_lines(mode, rumor=True)
    return ThemedTopic('region', f"a strange rumor from {place}", lines,
                       {'rumor': entry['name']})


def _own_or_other(own, other):
    """Half the time the player's own group, falling back when one is empty."""
    first, second = (own, other) if random.random() < 0.5 else (other, own)
    return first or second


def _trainer_lines(speaker, trainer, pupils, ability):
    return _rumor_lines(speaker) + [
        f"The speaker knows of {trainer['name']}, found at "
        f"{trainer['place']}, who can do amazing things and is willing to "
        f"teach {pupils}.",
        f"The amazing skill to retell in your own words: {ability}.",
        "Tell, as a rumor, how this master has mastered it. Name the master "
        "and the place.",
        "Others may admire it, want to learn it too, or doubt it.",
    ]


def _profession_rumor(db, speaker, audience, mode):
    races = PROFESSION_TRAINERS.get(audience.get('team'))
    if not races:
        return None
    own_race = audience.get('race')
    own = [(own_race, t) for t in races.get(own_race, ())]
    other = [(race, t) for race, trainers in races.items()
             if race != own_race for t in trainers]
    pool = _own_or_other(own, other)
    if not pool:
        return None
    race, trainer = random.choice(pool)
    skill = trainer['skill']
    ability = random.choice(PROFESSION_ABILITIES[skill])
    lines = _trainer_lines(speaker, trainer,
                           f"{skill} to anyone who wants to learn", ability)
    return ThemedTopic(
        'profession', f"rumors about {trainer['name']}, who teaches {skill}",
        lines + _mode_lines(mode, rumor=True),
        {'rumor': trainer['name'], 'trainer_profession': skill,
         'trainer_race_list': race})


def _class_trainer_rumor(db, speaker, audience, mode):
    races = CLASS_TRAINERS.get(audience.get('team'))
    if not races:
        return None
    own_class = audience.get('class')
    own = [(race, t) for race, trainers in races.items()
           for t in trainers if t['skill'] == own_class]
    race_order = list(races)
    random.shuffle(race_order)
    other = []
    for race in race_order:
        other = [(race, t) for t in races[race] if t['skill'] != own_class]
        if other:
            break
    if own:
        own_race = random.choice(sorted({race for race, _ in own}))
        own = [pair for pair in own if pair[0] == own_race]
    pool = _own_or_other(own, other)
    if not pool:
        return None
    race, trainer = random.choice(pool)
    klass = trainer['skill']
    ability = random.choice(CLASS_ABILITIES[klass])
    lines = _trainer_lines(
        speaker, trainer,
        f"{klass.lower()}s (only those of that calling can learn from "
        "them)", ability)
    return ThemedTopic(
        'trainer', f"rumors about {trainer['name']}, {_a(klass)} {klass} "
        "trainer", lines + _mode_lines(mode, rumor=True),
        {'rumor': trainer['name'], 'trainer_class': klass,
         'trainer_race_list': race})


def _kind_weight(config, kind, audience):
    weight = max(0, cfg_int(config, *KIND_WEIGHT[kind]))
    band = LEVEL_BANDS.get(kind)
    if not band or not weight:
        return weight
    level = (audience or {}).get('level', 0)
    full, reduced = band
    if level <= full:
        return weight
    if level <= reduced:
        percent = max(0, min(100, cfg_int(
            config, 'LLMChatter.ThemedTopics.TrainerRumorReducedPercent',
            33)))
        return weight * percent / 100
    return 0


# --------------------------------------------------------------------------
# Picker
# --------------------------------------------------------------------------

def _build(kind, db, speaker, audience, mode):
    if kind == 'faction':
        return _faction_topic(speaker, mode)
    if kind == 'race':
        return _race_topic(speaker, mode)
    if kind == 'class':
        return _class_topic(speaker, mode)
    if kind == 'race_class':
        return _race_class_topic(speaker, mode)
    if not audience:
        return None
    if kind == 'expansion':
        return _expansion_rumor(db, speaker, audience, mode)
    if kind == 'dungeon':
        return _place_rumor(db, speaker, audience, mode, DUNGEON_RUMORS,
                            'dungeon')
    if kind == 'raid':
        return _place_rumor(db, speaker, audience, mode, RAID_RUMORS, 'raid')
    if kind == 'location':
        return _location_rumor(db, speaker, audience, mode)
    if kind == 'region':
        return _region_rumor(db, speaker, audience, mode)
    if kind == 'profession':
        return _profession_rumor(db, speaker, audience, mode)
    if kind == 'trainer':
        return _class_trainer_rumor(db, speaker, audience, mode)
    return None


def pick_themed_topic(db, config, channel, bot, audience=None,
                      mode='roleplay', faction='', roll=True):
    """Return a ThemedTopic for the channel, or None to use generic topics."""
    if not cfg_int(config, 'LLMChatter.ThemedTopics.Enable', 1):
        return None
    kinds = CHANNEL_KINDS.get(channel)
    if not kinds or not bot:
        return None
    if roll:
        key, default = CHANNEL_CHANCE[channel]
        if not chance_hit(config, key, default):
            return None
    speaker = speaker_profile(db, bot, faction)
    remaining = []
    for kind in kinds:
        weight = _kind_weight(config, kind, audience)
        if weight and (kind not in RUMOR_KINDS or audience):
            remaining.append([kind, weight])
    while remaining:
        total = sum(w for _, w in remaining)
        pick = random.uniform(0, total)
        for index, (kind, weight) in enumerate(remaining):
            pick -= weight
            if pick <= 0:
                break
        remaining.pop(index)
        try:
            topic = _build(kind, db, speaker, audience, mode)
        except Exception:
            logger.exception("themed topic %s failed", kind)
            topic = None
        if topic:
            topic.metadata.update({'themed_kind': kind,
                                   'themed_channel': channel})
            return topic
    return None


# --------------------------------------------------------------------------
# Guild-only zone topics
# --------------------------------------------------------------------------

def guild_zone_topic(zone_id, mode):
    zone = get_zone_name(zone_id) if zone_id else ''
    if not zone:
        return None
    lines = []
    flavor = get_zone_flavor(zone_id)
    if flavor and mode == 'roleplay':
        lines.append(f"What {zone} is like: {flavor}")
    lines.append("Others may agree or argue, drawing on their own time "
                 "there.")
    lines += _mode_lines(mode) if mode != 'roleplay' else []
    return ThemedTopic('zone', f"the speaker's opinion of {zone}, where they "
                       "are right now", lines, {'themed_zone': zone},
                       name_zone=True)


def guild_zone_weather_topic(zone_id, weather, mode):
    zone = get_zone_name(zone_id) if zone_id else ''
    if not zone:
        return None
    from chatter_prompts import get_time_of_day_context
    _, time_desc = get_time_of_day_context()
    weather = (weather or 'clear').strip() or 'clear'
    lines = [
        f"Right now in {zone}: {time_desc.lower()}, and the weather is "
        f"{weather}.",
        "Describe the impression the place, the hour and the weather make "
        "together. Others may agree or argue.",
    ]
    lines += _mode_lines(mode) if mode != 'roleplay' else []
    return ThemedTopic('zone_weather', f"{zone} at this hour and in this "
                       "weather", lines,
                       {'themed_zone': zone, 'themed_weather': weather},
                       name_zone=True)
