"""Content gating for rumors: level, faction, achievements and
mod-individual-progression tiers.

The worldserver sends an ``audience``: the online real players who can
read the line (every real guild member for Guild chat, every real
player of the speaker's faction in the zone for General), at most
``MAX_AUDIENCE``. A rumor that depends on progression must suit all of
them. When mod-individual-progression is absent or disabled,
``ip_active`` is false and every tier check passes.
"""

import json
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_ZUL_GURUB_TIER = 3
DEFAULT_ZUL_AMAN_TIER = 12
MAX_AUDIENCE = 10

_ACHIEVEMENT_TTL = 60
_achievement_cache = {}


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
        'is_gm': bool(raw.get('is_gm')),
        'ip_active': bool(raw.get('ip_active')),
        'progression_tier': _int(raw.get('progression_tier')),
        'progression_limit': _int(raw.get('progression_limit')),
        'ip_zg_tier': _int(raw.get('ip_zg_tier'), DEFAULT_ZUL_GURUB_TIER),
        'ip_za_tier': _int(raw.get('ip_za_tier'), DEFAULT_ZUL_AMAN_TIER),
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


def resolve_required_tier(required, listener):
    if required == 'zul_gurub':
        return listener.get('ip_zg_tier', DEFAULT_ZUL_GURUB_TIER)
    if required == 'zul_aman':
        return listener.get('ip_za_tier', DEFAULT_ZUL_AMAN_TIER)
    return _int(required)


def content_unlocked(listener, entry):
    """True when mod-individual-progression lets the listener reach
    entry."""
    if not listener or not listener.get('ip_active') or listener.get('is_gm'):
        return True
    tier = listener.get('progression_tier', 0)
    required = resolve_required_tier(entry.get('required_tier', 0), listener)
    limit = listener.get('progression_limit', 0)
    if limit and required > limit:
        return False
    if tier < required:
        return False
    max_tier = entry.get('max_tier')
    if max_tier is not None and tier > max_tier:
        return False
    return True


def level_in_range(listener, entry):
    level = (listener or {}).get('level', 0)
    return entry.get('min_level', 0) <= level <= entry.get('max_level', 255)


def suits_all(listeners: List[Dict], entry) -> bool:
    """The entry's level band and unlock tier fit every listener."""
    return bool(listeners) and all(
        level_in_range(listener, entry) and content_unlocked(listener, entry)
        for listener in listeners
    )


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


def completed_by_all(db, listeners: List[Dict], achievement_ids) -> bool:
    """True only when every listener has completed the content."""
    if not listeners or not achievement_ids:
        return False
    return all(
        has_completed(db, listener['guid'], achievement_ids)
        for listener in listeners
    )


def clear_caches():
    _achievement_cache.clear()
