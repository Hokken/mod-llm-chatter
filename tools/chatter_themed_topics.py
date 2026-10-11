"""Themed topics for Guild, General and party chat.

Faction, race, class and race+class topics are keyed to the first
speaker. Rumors are keyed to the ``audience``: every real player who can
read the line. Each pick aims progression rumors at one target listener,
rotating through the audience (``next_rumor_target()``): a rumor must
fit the target's level band and uncompleted content, and among those
the rumors fitting the most listeners win. Faction-bound rumors still
need one faction.

A themed topic is a subject the speakers may take up, never a script.
With conversation threads on it is one more fresh-subject source of the
thread planner (``LLMChatter.Threads.ThemedTopicWeight``); with threads
off the per-channel ``ThemedTopics.*Chance`` applies.
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List

from chatter_lore_data import (
    CLASS_TOPICS,
    FACTION_CRITICISM,
    FACTION_WAR_FRONTS,
    LOCAL_CONFLICTS,
    RACE_CLASS_TOPICS,
    RACE_CRITICISM,
    RACE_TOPICS,
)
from chatter_class_style import class_style
from chatter_constants import CLASS_NAMES, RACE_NAMES
from chatter_guild_profile import indefinite_article as _a
from chatter_progression import (
    audience_team,
    best_covered,
    next_rumor_target,
)
from chatter_rumor_data import (
    CAVERNS_OF_TIME_INTRO,
    DUNGEON_RUMORS,
    EXPANSION_RUMORS,
    LOCATION_RUMORS,
    RAID_RUMORS,
    REGION_RUMORS,
)
from chatter_shared import get_race_faction, get_race_name
from chatter_threads import themed_topic_weight, threads_enabled
from chatter_trainer_rumor_data import (
    CLASS_ABILITIES,
    CLASS_TRAINER_RUMOR_LEVELS,
    CLASS_TRAINERS,
    PROFESSION_ABILITIES,
    PROFESSION_RUMOR_LEVELS,
    PROFESSION_TRAINERS,
)

logger = logging.getLogger(__name__)

_RACE_IDS = {name: race_id for race_id, name in RACE_NAMES.items()}

CHANNEL_KINDS = {
    'guild': ('faction', 'race', 'class', 'race_class', 'expansion',
              'dungeon', 'raid', 'location', 'region', 'profession',
              'trainer'),
    'general': ('faction', 'race', 'class', 'race_class', 'expansion',
                'dungeon', 'raid', 'location', 'region', 'profession',
                'trainer'),
    'party': ('class', 'race_class'),
}
# Used only while conversation threads are off for the channel.
CHANNEL_CHANCE = {
    'guild': ('LLMChatter.ThemedTopics.GuildChance', 30),
    'general': ('LLMChatter.ThemedTopics.GeneralChance', 30),
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
# (last level at full weight, last level at reduced weight)
LEVEL_BANDS = {
    'profession': (
        ('LLMChatter.ThemedTopics.ProfessionRumorFullLevel',
         PROFESSION_RUMOR_LEVELS[0]),
        ('LLMChatter.ThemedTopics.ProfessionRumorMaxLevel',
         PROFESSION_RUMOR_LEVELS[1]),
    ),
    'trainer': (
        ('LLMChatter.ThemedTopics.ClassTrainerRumorFullLevel',
         CLASS_TRAINER_RUMOR_LEVELS[0]),
        ('LLMChatter.ThemedTopics.ClassTrainerRumorMaxLevel',
         CLASS_TRAINER_RUMOR_LEVELS[1]),
    ),
}


@dataclass
class ThemedTopic:
    kind: str
    subject: str
    lines: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

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
        return get_race_name(int(value), '')
    return str(value or '')


def _class_name(value):
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return CLASS_NAMES.get(int(value), '')
    return str(value or '')


def race_faction(race):
    return get_race_faction(_RACE_IDS.get(race, 0))


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


def _shares_view(speaker):
    return (f"How far {speaker['name']} shares these views is up to "
            "their own personality.")


def _enemy(faction):
    return 'Horde' if faction == 'Alliance' else 'Alliance'


def _faction_line(speaker):
    return (f"{speaker['name']} is {_a(speaker['race'])} {speaker['race']} "
            f"{speaker['class_style'] or speaker['class']} who fights for "
            f"the {speaker['faction']}.")


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
        subject = (f"the long struggle between the Horde and the Alliance "
                   f"in {zone}")
        lines += [f"Background: {text}",
                  "Talk about it as an old, ongoing conflict, not as news "
                  "of a fresh battle."]
        meta = {'faction_topic': choice, 'faction_zone': zone}
    elif choice == 'criticism':
        subject = f"what the {faction} thinks of the {enemy}"
        lines += [f"Views often heard in the {faction} about the "
                  f"{enemy}: {FACTION_CRITICISM[faction]}",
                  _shares_view(speaker)]
        meta = {'faction_topic': choice}
    elif choice == 'race':
        race, text = random.choice(list(RACE_CRITICISM[faction].items()))
        subject = (f"the {race}, a race of the {enemy}, as the {faction} "
                   "sees them")
        lines += [f"Views often heard in the {faction} about the "
                  f"{race}: {text}",
                  _shares_view(speaker),
                  f"Talk about the {race} only, no other race."]
        meta = {'faction_topic': choice, 'faction_target_race': race}
    else:
        text = random.choice(LOCAL_CONFLICTS[faction])
        subject = "a story going around about a clash with the " + enemy
        lines += [f"The story as it is told: {text}",
                  "Tell it as hearsay, not as something that just "
                  "happened, and add no new details."]
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


def _target(audience, target):
    return target or (audience[0] if audience else None)


def _expansion_rumor(db, speaker, audience, mode, target=None):
    options = best_covered(db, audience, _target(audience, target),
                           EXPANSION_RUMORS.values())
    if not options:
        return None
    entry = random.choice(options)
    facts = random.sample(entry['facts'], min(3, len(entry['facts'])))
    land = entry['name']
    hint = ("the lands beyond the Dark Portal" if land == 'Outland'
            else "the frozen continent in the north")
    subject = f"rumors about {land}"
    lines = _rumor_lines(speaker) + [
        f"Name {land} or call it something like \"{hint}\" so it is clear "
        "which land is meant.",
        "Ideas to retell in your own words: " + "; ".join(facts) + ".",
        "Frame it as a rumor you have heard.",
        "Others may show interest in going, or unease and a wish to stay "
        "away.",
    ] + _mode_lines(mode, rumor=True)
    return ThemedTopic('expansion', subject, lines,
                       {'rumor': land})


def _place_rumor(db, speaker, audience, mode, pool, kind, target=None):
    options = best_covered(db, audience, _target(audience, target), pool)
    if not options:
        return None
    entry = random.choice(options)
    lines = _rumor_lines(speaker) + [f"What is known: {entry['text']}"]
    if entry.get('caverns_of_time') and CAVERNS_OF_TIME_INTRO:
        lines.append(f"Where it is: {CAVERNS_OF_TIME_INTRO}")
    lines += [
        "Others may show interest, wish the place cleansed and the threat "
        "ended, or voice fear.",
    ] + _mode_lines(mode, rumor=True, place_kind=kind)
    return ThemedTopic(kind, f"rumors about {entry['name']}", lines,
                       {'rumor': entry['name']})


def _location_rumor(db, speaker, audience, mode, target=None):
    team = audience_team(audience)
    if not team:
        return None
    options = best_covered(db, audience, _target(audience, target), [
        e for e in LOCATION_RUMORS
        if team in e['factions'] and team in e['text']
    ])
    if not options:
        return None
    entry = random.choice(options)
    lines = _rumor_lines(speaker) + [
        f"What is known about {entry['name']}: {entry['text'][team]}",
        f"Name {entry['name']} so it is clear which place is meant.",
        "Others may show interest, hope things there improve, want to "
        "visit, or voice fear.",
    ] + _mode_lines(mode, rumor=True)
    return ThemedTopic('location', f"news about {entry['name']}", lines,
                       {'rumor': entry['name']})


def _region_rumor(db, speaker, audience, mode, target=None):
    team = audience_team(audience)
    if not team:
        return None
    options = best_covered(db, audience, _target(audience, target), [
        e for e in REGION_RUMORS
        if team in e['factions'] and e['rumors']
    ])
    if not options:
        return None
    entry = random.choice(options)
    rumor = random.choice(entry['rumors'])
    place = entry.get('general_region') or entry['name']
    lines = _rumor_lines(speaker) + [
        f"The rumor to retell in your own words: {rumor}",
        f"It is said to happen in {place}. Tell it as a rumor, not as "
        "hard fact, and add no new details.",
        "Others may want to check it, doubt it, or wonder what is behind "
        "it.",
    ] + _mode_lines(mode, rumor=True)
    return ThemedTopic('region', f"a strange rumor from {place}", lines,
                       {'rumor': entry['name']})


def _own_or_other(config, own, other):
    """The listener's own race or class at OwnTrainerChance, otherwise
    another one; falls back when one side is empty."""
    own_first = chance_hit(
        config, 'LLMChatter.ThemedTopics.OwnTrainerChance', 50)
    first, second = (own, other) if own_first else (other, own)
    return first or second


def _trainer_lines(speaker, trainer, pupils, ability):
    return _rumor_lines(speaker) + [
        f"The speaker has heard of {trainer['name']}, found at "
        f"{trainer['place']}, who teaches {pupils}.",
        f"Something this trainer is said to teach, to retell in your own "
        f"words: {ability}.",
        "Tell it as a rumor. Name the trainer and the place.",
        "Others may admire it, want to learn it too, or doubt it.",
    ]


def _profession_rumor(db, config, speaker, audience, mode,
                      target=None):
    races = PROFESSION_TRAINERS.get(audience_team(audience))
    if not races:
        return None
    own_race = _target(audience, target).get('race')
    own = [(own_race, t) for t in races.get(own_race, ())]
    other = [(race, t) for race, trainers in races.items()
             if race != own_race for t in trainers]
    pool = _own_or_other(config, own, other)
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


def _class_trainer_rumor(db, config, speaker, audience, mode,
                         target=None):
    races = CLASS_TRAINERS.get(audience_team(audience))
    if not races:
        return None
    own_class = _target(audience, target).get('class')
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
    pool = _own_or_other(config, own, other)
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


def _kind_weight(config, kind, audience, target=None):
    weight = max(0, cfg_int(config, *KIND_WEIGHT[kind]))
    band = LEVEL_BANDS.get(kind)
    if not band or not weight:
        return weight
    level = (_target(audience, target) or {}).get('level', 0)
    # The maximum always wins: a FullLevel above it is capped to it.
    reduced = cfg_int(config, *band[1])
    full = min(cfg_int(config, *band[0]), reduced)
    if level > reduced:
        return 0
    if level <= full:
        return weight
    percent = max(0, min(100, cfg_int(
        config, 'LLMChatter.ThemedTopics.TrainerRumorReducedPercent', 33)))
    return weight * percent / 100


# --------------------------------------------------------------------------
# Picker
# --------------------------------------------------------------------------

def _build(kind, db, config, speaker, audience, mode, target=None):
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
        return _expansion_rumor(db, speaker, audience, mode, target)
    if kind == 'dungeon':
        return _place_rumor(db, speaker, audience, mode, DUNGEON_RUMORS,
                            'dungeon', target)
    if kind == 'raid':
        return _place_rumor(db, speaker, audience, mode, RAID_RUMORS, 'raid',
                            target)
    if kind == 'location':
        return _location_rumor(db, speaker, audience, mode, target)
    if kind == 'region':
        return _region_rumor(db, speaker, audience, mode, target)
    if kind == 'profession':
        return _profession_rumor(db, config, speaker, audience, mode,
                                 target)
    if kind == 'trainer':
        return _class_trainer_rumor(db, config, speaker, audience, mode,
                                    target)
    return None


def pick_themed_topic(db, config, channel, bot, audience=None,
                      mode='roleplay', faction='', roll=True):
    """Return a ThemedTopic for the channel, or None to use generic topics.

    ``audience`` is the list of listeners from ``parse_audience()``;
    rumors need at least one, and each call aims them at the next
    listener in the rotation.
    """
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
    target = next_rumor_target(audience or [])
    remaining = []
    for kind in kinds:
        weight = _kind_weight(config, kind, audience, target)
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
            topic = _build(kind, db, config, speaker, audience, mode,
                           target)
        except Exception:
            logger.exception("themed topic %s failed", kind)
            topic = None
        if topic:
            topic.metadata.update({'themed_kind': kind,
                                   'themed_channel': channel})
            if kind in RUMOR_KINDS and target:
                topic.metadata['rumor_target'] = target['name']
            return topic
    return None


def themed_candidate(db, config, channel, bot, thread_key=None,
                     audience=None, mode='roleplay', faction=''):
    """The themed subject for one idle turn, or None.

    Callers compute it before ``plan_idle_turn()`` so the guild, talent
    and achievement lookups never run under the thread lock. While
    threads are on for ``thread_key``, ``ThemedTopicWeight`` decides in
    the planner whether it is used, so no channel chance is rolled here.
    """
    threaded = thread_key is not None and threads_enabled(thread_key)
    if threaded and not themed_topic_weight():
        return None
    return pick_themed_topic(
        db, config, channel, bot, audience=audience, mode=mode,
        faction=faction, roll=not threaded,
    )


def themed_used(themed, thread_turn) -> bool:
    """Whether this turn's subject is the themed candidate."""
    if not themed:
        return False
    return thread_turn is None or thread_turn.source == 'themed'


def themed_metadata(themed) -> Dict:
    """Request-log fields for the themed subject (empty kind when none)."""
    if not themed:
        return {'themed_kind': ''}
    return dict(themed.metadata)
