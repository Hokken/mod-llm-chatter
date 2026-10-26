"""Conversation topics tied to the place where the speakers are.

Each open-world zone, dungeon and raid in ``location_topics.json`` has its
own topic list. A prompt that uses one names the place, states that the
subject belongs to it, and carries the place's description, so the model
talks about something that is really there instead of inventing ruins, a
market or the weather.

Used by roleplay-mode bots and by NPC speakers (always in-world). Party
callers also check that every speaker and the real player share the zone
(see ``chatter_group``). Guild chat does not use these topics: its
speakers are elsewhere.
"""

import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from chatter_constants import BG_MAP_NAMES
from chatter_shared import (
    get_dungeon_flavor,
    get_zone_flavor,
    get_zone_name,
)

logger = logging.getLogger(__name__)

_settings = {'enable': True, 'chance': 40}
_topics: Optional[Dict] = None


def _clamped_int(config, key, default, low, high) -> int:
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError, AttributeError):
        logger.error("Failed to parse %s", key)
        value = default
    return max(low, min(value, high))


def configure_location_topics(config) -> None:
    """Load the location topic settings from the bridge config."""
    config = config or {}
    _settings['enable'] = _clamped_int(
        config, 'LLMChatter.LocationTopics.Enable', 1, 0, 1
    ) == 1
    _settings['chance'] = _clamped_int(
        config, 'LLMChatter.LocationTopics.Chance', 40, 0, 100
    )


def _load_topics() -> Dict:
    """Load location_topics.json once on first access."""
    global _topics
    if _topics is not None:
        return _topics
    path = os.path.join(
        os.path.dirname(__file__), 'location_topics.json'
    )
    try:
        with open(path, 'r', encoding='utf-8') as f:
            _topics = json.load(f)
    except Exception:
        logger.warning("Could not load location_topics.json")
        _topics = {}
    return _topics


@dataclass(frozen=True)
class LocationTopic:
    """One topic drawn for a place, with the place's description."""

    place: str
    kind: str           # zone|dungeon|raid
    topic: str
    description: str

    def subject_line(self) -> str:
        return (
            f"A subject tied to {self.place}, where the speakers are "
            f"now: {self.topic}. It belongs to {self.place} itself; "
            "talk about it as people who are there."
        )

    def description_line(self) -> str:
        return f"Location description: {self.description}"

    def lines(self, with_description: bool = True) -> List[str]:
        """Prompt lines; leave the description out when the prompt
        already carries the same zone or instance description."""
        lines = [self.subject_line()]
        if with_description:
            lines.append(self.description_line())
        return lines


def location_topic_for(zone_id, map_id) -> Optional[LocationTopic]:
    """A random topic for this place, or None.

    Inside a dungeon or raid the instance's own list is used, never the
    zone's. Battlegrounds, arenas and places without a list or a
    description get nothing. No chance roll: callers that weigh
    sources themselves (conversation threads) use this directly.
    """
    if not _settings['enable']:
        return None
    try:
        zone_id, map_id = int(zone_id or 0), int(map_id or 0)
    except (TypeError, ValueError):
        return None
    if map_id in BG_MAP_NAMES:
        return None
    data = _load_topics()
    instance_flavor = get_dungeon_flavor(map_id)
    if instance_flavor is not None:
        entry = data.get('maps', {}).get(str(map_id))
        description = instance_flavor
        kind = (entry or {}).get('kind', 'dungeon')
        place = (entry or {}).get('name')
    else:
        entry = data.get('zones', {}).get(str(zone_id))
        description = get_zone_flavor(zone_id) if zone_id else None
        kind = 'zone'
        place = get_zone_name(zone_id) or (entry or {}).get('name')
    if not entry or not entry.get('topics') or not description:
        return None
    return LocationTopic(
        place=place,
        kind=kind,
        topic=random.choice(entry['topics']),
        description=description,
    )


def roll_location_topic(zone_id, map_id) -> Optional[LocationTopic]:
    """A topic for this place at LocationTopics.Chance, or None, in
    which case the caller keeps its universal topic."""
    if random.randint(1, 100) > _settings['chance']:
        return None
    return location_topic_for(zone_id, map_id)
