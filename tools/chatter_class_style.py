"""Class keys and spec roles derived from a character's active talents.

- class_style(): class key that treats Light and Shadow priests apart.
- talent_spec_role(): the group role a character's talent spec points
  to, or None when the talents cannot tell (issue #97).

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


# Dominant talent tree -> spec role, per class. Trees that cannot tell
# the role are absent on purpose and resolve to None: every Death
# Knight tree (any can tank in 3.3.5a; presence is not a talent) and
# Druid Feral Combat (bear or cat).
_SPEC_ROLES = {
    'Warrior': {'Arms': 'dps', 'Fury': 'dps', 'Protection': 'tank'},
    'Paladin': {
        'Holy': 'healer', 'Protection': 'tank', 'Retribution': 'dps',
    },
    'Priest': {
        'Discipline': 'healer', 'Holy': 'healer', 'Shadow': 'dps',
    },
    'Shaman': {
        'Elemental': 'dps', 'Enhancement': 'dps',
        'Restoration': 'healer',
    },
    'Druid': {'Balance': 'dps', 'Restoration': 'healer'},
    'Rogue': {'Assassination': 'dps', 'Combat': 'dps', 'Subtlety': 'dps'},
    'Mage': {'Arcane': 'dps', 'Fire': 'dps', 'Frost': 'dps'},
    'Warlock': {
        'Affliction': 'dps', 'Demonology': 'dps', 'Destruction': 'dps',
    },
    'Hunter': {
        'Beast Mastery': 'dps', 'Marksmanship': 'dps', 'Survival': 'dps',
    },
}


def talent_spec_role(db, guid, class_name):
    """'tank', 'healer' or 'dps' from the tree holding strictly the
    most points of the active spec, or None when unknown: no talents,
    a failed lookup, a tie, or a tree that does not tell the role."""
    roles = _SPEC_ROLES.get(class_name or '')
    if not roles or db is None or not guid:
        return None
    try:
        from chatter_db import get_character_talents
        totals = (get_character_talents(db, int(guid)) or {}).get(
            'tree_totals') or {}
    except Exception:
        logger.debug("talent lookup failed for %s", guid, exc_info=True)
        return None
    points = {tree: _int(pts) for tree, pts in totals.items()}
    top = max(points.values(), default=0)
    if top <= 0:
        return None
    leaders = [tree for tree, pts in points.items() if pts == top]
    if len(leaders) != 1:
        return None
    return roles.get(leaders[0])
