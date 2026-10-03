"""Class key for prompts that treat Light and Shadow priests apart.

Talents come from chatter_db.get_character_talents(), which reads the
active spec on every call and caches per (guid, active spec), so the
style follows a dual-spec switch without a cache of its own.
"""

import logging

logger = logging.getLogger(__name__)


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def priest_style(db, guid) -> str:
    """'Shadow Priest' when Shadow has strictly the most points, else
    'Light Priest'."""
    if db is None or not guid:
        return 'Light Priest'
    try:
        from chatter_db import get_character_talents
        totals = (get_character_talents(db, int(guid)) or {}).get(
            'tree_totals') or {}
    except Exception:
        logger.debug("talent lookup failed for %s", guid, exc_info=True)
        return 'Light Priest'
    shadow = _int(totals.get('Shadow'))
    others = max(_int(totals.get('Discipline')), _int(totals.get('Holy')))
    return 'Shadow Priest' if shadow > others else 'Light Priest'


def class_style(db, guid, class_name) -> str:
    """Class name, with priests split into 'Light Priest' and
    'Shadow Priest' by their talents."""
    if class_name == 'Priest':
        return priest_style(db, guid)
    return class_name or ''
