"""
Chatter Links - WoW link parser and description
resolver for player chat messages.

Parses quest/item/spell links from raw WoW markup,
resolves descriptions from the world database,
and formats enriched context for LLM prompts.
"""

import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

# Regex for WoW chat links (quest, item, spell)
_WOW_LINK_RE = re.compile(
    r'\|c[0-9a-fA-F]{8}'
    r'\|H(quest|item|spell):(\d+)'
    r'[^|]*\|h\[([^\]]+)\]\|h\|r'
)

ITEM_QUALITY_NAMES = {
    0: 'Poor', 1: 'Common', 2: 'Uncommon',
    3: 'Rare', 4: 'Epic', 5: 'Legendary',
    6: 'Artifact', 7: 'Heirloom',
}

_ITEM_CLASS_NAMES = {
    0: "Consumable", 1: "Container",
    2: "Weapon", 3: "Gem", 4: "Armor",
    5: "Reagent", 6: "Projectile",
    7: "Trade Goods", 9: "Recipe",
    12: "Quest Item", 15: "Miscellaneous",
}

_WEAPON_SUBCLASS = {
    0: "One-Handed Axe", 1: "Two-Handed Axe",
    2: "Bow", 3: "Gun", 4: "One-Handed Mace",
    5: "Two-Handed Mace", 6: "Polearm",
    7: "One-Handed Sword", 8: "Two-Handed Sword",
    10: "Staff", 13: "Fist Weapon",
    15: "Dagger", 16: "Thrown",
    17: "Spear", 18: "Crossbow",
    19: "Wand", 20: "Fishing Pole",
}

_ARMOR_SUBCLASS = {
    0: "Miscellaneous", 1: "Cloth",
    2: "Leather", 3: "Mail", 4: "Plate",
    6: "Shield",
}


def parse_wow_links(message: str) -> list:
    """Parse all quest/item/spell links from a
    WoW chat message.

    Returns list of dicts:
      [{'type': 'quest'|'item'|'spell',
        'id': int, 'name': str}]
    """
    if not message:
        return []
    results = []
    for m in _WOW_LINK_RE.finditer(message):
        results.append({
            'type': m.group(1),
            'id': int(m.group(2)),
            'name': m.group(3),
        })
    return results


def clean_link_markup(message: str) -> str:
    """Replace WoW link markup with just [Name].

    The LLM sees clean text like:
      "anyone done [Gaffer Jacks]?"
    instead of raw color/link codes.
    """
    if not message:
        return message
    return _WOW_LINK_RE.sub(
        lambda m: f"[{m.group(3)}]", message
    )


def resolve_link_descriptions(
    config, links: list
) -> list:
    """Resolve descriptions for parsed links by
    querying the world database.

    Adds a 'description' key to each link dict.
    Uses a temporary acore_world connection.
    Gracefully degrades if DB is unavailable.
    """
    if not links:
        return links

    # Resolve spells first (no DB needed)
    for link in links:
        link['description'] = ''
        if link['type'] == 'spell':
            try:
                _resolve_spell(link)
            except Exception:
                pass

    # Only open world DB if quest/item links exist
    needs_db = any(
        l['type'] in ('quest', 'item')
        for l in links
    )
    if not needs_db:
        return links

    from chatter_db import get_db_connection

    world_db = None
    try:
        world_db = get_db_connection(
            config, 'acore_world'
        )
        cursor = world_db.cursor(dictionary=True)

        for link in links:
            try:
                if link['type'] == 'quest':
                    _resolve_quest(
                        cursor, link
                    )
                elif link['type'] == 'item':
                    _resolve_item(
                        cursor, link
                    )
            except Exception:
                pass
    except Exception:
        for link in links:
            if 'description' not in link:
                link['description'] = ''
    finally:
        if world_db:
            try:
                world_db.close()
            except Exception:
                pass

    return links


def _resolve_quest(cursor, link: dict):
    """Resolve quest description from world DB."""
    cursor.execute(
        "SELECT LogDescription "
        "FROM quest_template "
        "WHERE ID = %s",
        (link['id'],)
    )
    row = cursor.fetchone()
    if row and row.get('LogDescription'):
        desc = row['LogDescription'].strip()
        if desc:
            link['description'] = desc


def _resolve_item(cursor, link: dict):
    """Resolve item description from world DB."""
    cursor.execute(
        "SELECT class, subclass, Quality, "
        "ItemLevel, description "
        "FROM item_template "
        "WHERE entry = %s",
        (link['id'],)
    )
    row = cursor.fetchone()
    if not row:
        return

    raw_q = row.get('Quality')
    quality = int(raw_q) if raw_q is not None else 1
    quality_name = ITEM_QUALITY_NAMES.get(
        quality, 'Common'
    )
    raw_c = row.get('class')
    item_class = int(raw_c) if raw_c is not None else 0
    raw_s = row.get('subclass')
    item_sub = int(raw_s) if raw_s is not None else 0

    if item_class == 2:
        type_name = _WEAPON_SUBCLASS.get(
            item_sub, 'Weapon'
        )
    elif item_class == 4:
        type_name = _ARMOR_SUBCLASS.get(
            item_sub, 'Armor'
        )
    else:
        type_name = _ITEM_CLASS_NAMES.get(
            item_class, 'Item'
        )

    raw_i = row.get('ItemLevel')
    ilvl = int(raw_i) if raw_i is not None else 0
    parts = [f"{quality_name} {type_name}"]
    if ilvl:
        parts.append(f"iLvl {ilvl}")

    item_desc = row.get('description', '')
    if item_desc and isinstance(item_desc, str):
        item_desc = item_desc.strip()
        if item_desc:
            parts.append(item_desc)

    link['description'] = ', '.join(parts)


def _resolve_spell(link: dict):
    """Resolve spell info. Uses spell_names cache
    if available, otherwise just the link name.
    No DB query (spell_dbc descriptions have
    ugly template placeholders).
    """
    try:
        from spell_names import SPELL_NAMES
        cached_name = SPELL_NAMES.get(link['id'])
        if cached_name:
            link['description'] = cached_name
    except ImportError:
        pass


def format_link_context(
    resolved_links: list
) -> str:
    """Format resolved links into a prompt-friendly
    context string.

    Returns empty string if no links.
    """
    if not resolved_links:
        return ""

    lines = []
    for link in resolved_links:
        type_label = link['type'].capitalize()
        name = link['name']
        desc = link.get('description', '')

        if desc and desc != name:
            lines.append(
                f"- [{type_label}] {name}: {desc}"
            )
        else:
            lines.append(
                f"- [{type_label}] {name}"
            )

    return (
        "The player referenced these in-game "
        "links:\n" + "\n".join(lines)
    )


def resolve_and_format_links(
    config, message: str
) -> tuple:
    """Convenience function: parse, resolve, format.

    Returns (clean_message, link_context).
    Both are strings. link_context is empty if
    no links found.
    """
    links = parse_wow_links(message)
    if not links:
        return message, ""

    resolved = resolve_link_descriptions(
        config, links
    )
    context = format_link_context(resolved)
    clean_msg = clean_link_markup(message)

    link_summary = ", ".join(
        f"{l['type']}:{l['id']} [{l['name']}]"
        for l in links
    )

    return clean_msg, context
