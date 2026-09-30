"""Content gating for rumors: level, faction, achievements and
mod-individual-progression tiers, plus the priest Light/Shadow style.

The worldserver sends an ``audience`` object describing the real player
who will read the line. When mod-individual-progression is absent or
disabled, ``ip_active`` is false and every tier check passes.
"""

import json
import logging
import time

logger = logging.getLogger(__name__)

DEFAULT_ZUL_GURUB_TIER = 3
DEFAULT_ZUL_AMAN_TIER = 12

_ACHIEVEMENT_TTL = 60
_achievement_cache = {}
_STYLE_TTL = 300
_style_cache = {}


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_audience(raw):
    """Normalize an audience payload (dict or JSON text) or return None."""
    if not raw:
        return None
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode('utf-8', 'replace')
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return None
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


def resolve_required_tier(required, audience):
    if required == 'zul_gurub':
        return audience.get('ip_zg_tier', DEFAULT_ZUL_GURUB_TIER)
    if required == 'zul_aman':
        return audience.get('ip_za_tier', DEFAULT_ZUL_AMAN_TIER)
    return _int(required)


def content_unlocked(audience, entry):
    """True when mod-individual-progression lets the audience reach entry."""
    if not audience or not audience.get('ip_active') or audience.get('is_gm'):
        return True
    tier = audience.get('progression_tier', 0)
    required = resolve_required_tier(entry.get('required_tier', 0), audience)
    limit = audience.get('progression_limit', 0)
    if limit and required > limit:
        return False
    if tier < required:
        return False
    max_tier = entry.get('max_tier')
    if max_tier is not None and tier > max_tier:
        return False
    return True


def level_in_range(audience, entry):
    level = (audience or {}).get('level', 0)
    return entry.get('min_level', 0) <= level <= entry.get('max_level', 255)


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


def priest_style(db, guid):
    """'Shadow Priest' when Shadow has strictly the most points, else 'Light Priest'."""
    now = time.time()
    cached = _style_cache.get(guid)
    if cached and now - cached[0] < _STYLE_TTL:
        return cached[1]
    style = 'Light Priest'
    if db is not None and guid:
        try:
            from chatter_db import get_character_talents
            totals = (get_character_talents(db, int(guid)) or {}).get(
                'tree_totals') or {}
            shadow = _int(totals.get('Shadow'))
            others = max(_int(totals.get('Discipline')),
                         _int(totals.get('Holy')))
            if shadow > others:
                style = 'Shadow Priest'
        except Exception:
            logger.debug("talent lookup failed for %s", guid, exc_info=True)
    _style_cache[guid] = (now, style)
    return style


def class_style(db, guid, class_name):
    """Class key used by the topic and race+class data."""
    if class_name == 'Priest':
        return priest_style(db, guid)
    return class_name or ''


def clear_caches():
    _achievement_cache.clear()
    _style_cache.clear()
