"""Third-person description of the real player for prompts that address
them: race outlook, class calling and the race+class note in roleplay, a
single short line in normal mode."""

import logging
import time
from typing import Dict, List

from chatter_constants import RACE_SPEECH_PROFILES
from chatter_lore_data import CLASS_CALLINGS
from chatter_mode import is_roleplay
from chatter_progression import class_style
from chatter_shared import (
    get_class_name,
    get_gender_label,
    get_race_name,
    race_class_note,
)

logger = logging.getLogger(__name__)

_TTL = 300
_cache: Dict[int, tuple] = {}


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _load_character(db, guid: int) -> Dict[str, str]:
    now = time.time()
    cached = _cache.get(guid)
    if cached and now - cached[0] < _TTL:
        return cached[1]
    info: Dict[str, str] = {}
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT race, class, gender FROM characters WHERE guid = %s",
            (guid,),
        )
        row = cursor.fetchone()
        if row:
            info = {
                'race': get_race_name(_safe_int(row.get('race'))),
                'class': get_class_name(_safe_int(row.get('class'))),
                'gender': get_gender_label(_safe_int(row.get('gender'))),
            }
    except Exception:
        logger.debug("player lookup failed guid=%s", guid, exc_info=True)
    _cache[guid] = (now, info)
    return info


def _calling_style(db, guid: int, class_name: str) -> str:
    if class_name != 'Priest':
        return class_name
    return (class_style(db, guid, class_name)
            if db is not None and guid else 'Light Priest')


def _lore_lines(db, guid: int, name: str, race: str, class_name: str,
                style: str) -> List[str]:
    lines = []
    worldview = (RACE_SPEECH_PROFILES.get(race) or {}).get('worldview')
    if worldview:
        lines.append(f"{race} outlook: {worldview}")
    calling = CLASS_CALLINGS.get(style)
    if calling:
        lines.append(f"{style} calling: {calling}")
    note = race_class_note(race, class_name, style, subject=f"{name}'s")
    if note:
        lines.append(note)
    return lines


def character_lore_lines(
    db, guid, name: str, race: str, class_name: str,
) -> List[str]:
    """Race outlook, class calling and race+class note for any character;
    empty when the race or class is unknown."""
    name = str(name or '').strip() or 'They'
    race = '' if race == 'Unknown' else str(race or '')
    class_name = '' if class_name == 'Adventurer' else str(class_name or '')
    if not race or not class_name:
        return []
    guid = _safe_int(guid)
    return _lore_lines(db, guid, name, race, class_name,
                       _calling_style(db, guid, class_name))


def player_character_lines(
    db, guid, name: str, mode: str,
    race: str = '', class_name: str = '', gender: str = '',
) -> List[str]:
    """Describe the real player; empty when nothing is known."""
    name = str(name or '').strip()
    guid = _safe_int(guid)
    if not name:
        return []
    if (not race or not class_name) and db is not None and guid:
        info = _load_character(db, guid)
        race = race or info.get('race', '')
        class_name = class_name or info.get('class', '')
        gender = gender or info.get('gender', '')
    race = '' if race == 'Unknown' else str(race or '')
    class_name = '' if class_name == 'Adventurer' else str(class_name or '')
    if not race or not class_name:
        return []

    who = " ".join(p for p in (gender, race) if p)
    a = _article(who)
    if not is_roleplay(mode):
        return [f"{name} (the real player) plays {a} {who} {class_name}."]

    style = _calling_style(db, guid, class_name)
    lines = [
        f"About {name}, the real player you are talking to: {a} {who} "
        f"{style}."
    ]
    lines.extend(_lore_lines(db, guid, name, race, class_name, style))
    lines.append(
        "Let this colour your words (a fitting greeting, a nod to their "
        "people or calling); never recite it or explain it back to them."
    )
    return lines


def player_context_text(db, guid, name: str, mode: str, **kwargs) -> str:
    """player_character_lines joined as one block for string prompts."""
    return "\n".join(player_character_lines(db, guid, name, mode, **kwargs))


def clear_cache():
    _cache.clear()
