"""Content gating for rumors: level, faction and achievements.

The worldserver sends an ``audience``: the online real players who can
read the line (every real guild member for Guild chat, every real
player of the speaker's faction in the zone for General), at most
``MAX_AUDIENCE``. Levels in one guild or zone can be far apart, so a
rumor that depends on progression is aimed at one target listener at a
time, rotating to the one served least recently, and among the rumors
that fit the target the ones fitting the most listeners win. With one
listener that listener is always the target.
"""

import json
import logging
import random
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_AUDIENCE = 10

_ACHIEVEMENT_TTL = 60
_achievement_cache = {}

_ROTATION_LIMIT = 1000
_rumor_served = {}


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _listener(raw) -> Optional[Dict]:
    if not isinstance(raw, dict):
        return None
    guid = _int(raw.get('guid'))
    level = _int(raw.get('level'))
    if not guid or not level:
        return None
    return {
        'guid': guid,
        'name': str(raw.get('name') or ''),
        'level': level,
        'team': str(raw.get('team') or ''),
        'race': str(raw.get('race') or ''),
        'class': str(raw.get('class') or ''),
    }


def parse_audience(raw) -> List[Dict]:
    """Listeners from an audience payload (a JSON array of players, or a
    single player object), as dicts or JSON text. Empty when unknown."""
    if not raw:
        return []
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode('utf-8', 'replace')
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return []
    items = [raw] if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    listeners = []
    seen = set()
    for item in items:
        listener = _listener(item)
        if listener and listener['guid'] not in seen:
            seen.add(listener['guid'])
            listeners.append(listener)
    return listeners[:MAX_AUDIENCE]


def level_in_range(listener, entry):
    level = (listener or {}).get('level', 0)
    return entry.get('min_level', 0) <= level <= entry.get('max_level', 255)


def audience_team(listeners: List[Dict]) -> str:
    """The listeners' faction, or '' when it is unknown or mixed."""
    teams = {listener.get('team') for listener in listeners}
    if len(teams) != 1:
        return ''
    return next(iter(teams)) or ''


def audience_max_level(listeners: List[Dict]) -> int:
    return max((listener.get('level', 0) for listener in listeners),
               default=0)


def has_completed(db, guid, achievement_ids):
    """True when the character earned any of the given achievements."""
    ids = tuple(int(a) for a in (achievement_ids or ()) if a)
    if not ids or not guid:
        return False
    now = time.time()
    cached = _achievement_cache.get(guid)
    if cached and now - cached[0] < _ACHIEVEMENT_TTL:
        earned = cached[1]
    else:
        earned = set()
        try:
            cursor = db.cursor()
            cursor.execute(
                "SELECT achievement FROM character_achievement "
                "WHERE guid = %s", (guid,))
            earned = {int(row[0]) for row in cursor.fetchall()}
        except Exception:
            logger.debug("achievement lookup failed for %s", guid,
                         exc_info=True)
        _achievement_cache[guid] = (now, earned)
    return any(a in earned for a in ids)


def fits(db, listener, entry) -> bool:
    """The entry suits the listener: level band, and a dungeon or raid
    they have not completed yet."""
    achievements = entry.get('achievements')
    return (
        level_in_range(listener, entry)
        and not (achievements
                 and has_completed(db, listener['guid'], achievements))
    )


def next_rumor_target(listeners: List[Dict]) -> Optional[Dict]:
    """The listener served least recently, marked as served now.

    Marking happens even when no rumor comes of it, so a listener with
    nothing left to hear cannot hold the rotation."""
    if not listeners:
        return None
    if len(_rumor_served) > _ROTATION_LIMIT:
        _rumor_served.clear()
    target = min(listeners, key=lambda listener: (
        _rumor_served.get(listener['guid'], 0), random.random()))
    _rumor_served[target['guid']] = time.time()
    return target


def best_covered(db, listeners: List[Dict], target, entries) -> List:
    """The entries that fit the target, keeping those that fit the most
    listeners."""
    if not target:
        return []
    best = 0
    options = []
    for entry in entries:
        if not fits(db, target, entry):
            continue
        covered = sum(1 for listener in listeners
                      if fits(db, listener, entry))
        if covered > best:
            best = covered
            options = [entry]
        elif covered == best:
            options.append(entry)
    return options


def clear_caches():
    _achievement_cache.clear()
    _rumor_served.clear()
