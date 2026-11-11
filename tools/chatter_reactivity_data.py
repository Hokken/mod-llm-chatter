"""World reactivity content: letters, gifts and rumors.

The tables are JSON beside this file and are read once. Lookups are by
the game IDs the worldserver reports, so a deed with no letter or rumor
costs one dictionary miss.
"""

import json
import logging
import os
import random
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))

PROFESSION_SKILLS = {
    171: 'Alchemy',
    164: 'Blacksmithing',
    333: 'Enchanting',
    202: 'Engineering',
    182: 'Herbalism',
    773: 'Inscription',
    755: 'Jewelcrafting',
    165: 'Leatherworking',
    186: 'Mining',
    393: 'Skinning',
    197: 'Tailoring',
    185: 'Cooking',
    129: 'First Aid',
    356: 'Fishing',
}


@lru_cache(maxsize=None)
def _load(name: str) -> Dict:
    with open(
        os.path.join(_HERE, name), encoding='utf-8'
    ) as handle:
        return json.load(handle)


def letters() -> Dict:
    return _load('reactivity_letters.json')


def gifts() -> Dict:
    return _load('reactivity_gifts.json')


def rumors() -> Dict:
    return _load('reactivity_rumors.json')


@lru_cache(maxsize=None)
def _letter_index() -> Tuple[Dict, Dict, Dict]:
    by_achievement = {}
    by_quest = {}
    by_key = {}
    tables = letters()
    for kind, table in (('dungeon', 'dungeons'), ('raid', 'raids')):
        for row in tables[table]:
            by_key[(kind, row['key'])] = row
            for achievement in row['achievements']:
                by_achievement[achievement] = (kind, row)
    for row in tables['quests']:
        by_key[('quest', row['key'])] = row
        for quest in row['quests']:
            by_quest[quest] = ('quest', row)
    return by_achievement, by_quest, by_key


@lru_cache(maxsize=None)
def _rumor_index() -> Tuple[Dict, Dict, Dict]:
    by_achievement = {}
    by_quest = {}
    by_key = {}
    tables = rumors()
    for row in tables['achievements']:
        by_key[('achievement', row['key'])] = row
        for achievement in row['ids']:
            by_achievement[achievement] = ('achievement', row)
    for row in tables['dungeons']:
        by_key[('dungeon', row['key'])] = row
        for achievement in row['achievements']:
            by_achievement[achievement] = ('dungeon', row)
    for row in tables['quests']:
        by_key[('quest', row['key'])] = row
        for quest in row['quests']:
            by_quest[quest] = ('quest', row)
    return by_achievement, by_quest, by_key


def letter_for_achievement(achievement_id: int):
    return _letter_index()[0].get(achievement_id)


def letter_for_quest(quest_id: int):
    return _letter_index()[1].get(quest_id)


def letter_by_key(kind: str, key: str) -> Optional[Dict]:
    return _letter_index()[2].get((kind, key))


def rumor_for_achievement(achievement_id: int):
    return _rumor_index()[0].get(achievement_id)


def rumor_for_quest(quest_id: int):
    return _rumor_index()[1].get(quest_id)


def rumor_by_key(kind: str, key: str) -> Optional[Dict]:
    return _rumor_index()[2].get((kind, key))


def faction_allows(row: Dict, team: str) -> bool:
    return row.get('faction', 'Both') in ('Both', team)


def sender_for(
    row: Dict, team: str, quest_id: int = 0
) -> Optional[Dict]:
    """The row's sender for this deed: by quest for the Desolace clans,
    otherwise by faction, otherwise the one shared sender."""
    senders = row['senders']
    return (
        senders.get(str(quest_id))
        or senders.get(team.lower())
        or senders.get('any')
    )


def trainer_entry(name: str) -> int:
    return int(gifts()['trainers'].get(name, 0))


def weighted_choice(options: List[Tuple[object, int]]):
    """One option by weight; None when there is nothing to choose."""
    if not options:
        return None
    values = [option for option, _ in options]
    weights = [max(1, weight) for _, weight in options]
    return random.choices(values, weights=weights, k=1)[0]
