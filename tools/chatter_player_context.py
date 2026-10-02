"""Third-person description of the real player for prompts that address
them: race outlook and class calling in roleplay, a single short line in
normal mode."""

import logging
import time
from typing import Dict, List

from chatter_class_style import class_style
from chatter_constants import RACE_SPEECH_PROFILES
from chatter_mode import is_roleplay
from chatter_shared import (
    get_class_name,
    get_gender_label,
    get_race_name,
)

logger = logging.getLogger(__name__)

# Neutral, in-world descriptions of each calling, used to describe the
# real player (never temperament: that belongs to the speaker). Priests
# use "Light Priest" or "Shadow Priest".
CLASS_CALLINGS = {
    'Warrior': 'Warriors are trained fighters of arms and armour who hold '
               'the front line and turn battle into a matter of steel and '
               'nerve.',
    'Paladin': 'Paladins are holy warriors who carry the Light into '
               'battle, shielding allies, mending wounds and smiting the '
               'wicked in heavy armour.',
    'Hunter': 'Hunters are trackers and marksmen of the wild, fighting at '
              'range beside a loyal beast companion.',
    'Rogue': 'Rogues work from the shadows with blades, poisons and '
             'cunning, striking where a guard is weakest.',
    'Light Priest': 'Light Priests serve the Holy Light, mending the '
                    'wounded, shielding the faithful and tending the '
                    'spirits of those around them.',
    'Shadow Priest': 'Shadow Priests have turned from the Light to the '
                     'shadow and the Void, bending darkness and the '
                     'mind itself against their foes.',
    'Death Knight': 'Death Knights are warriors raised by the Scourge and '
                    'freed from the Lich King, wielding runeblades and '
                    'the cold magic of death.',
    'Shaman': 'Shamans commune with the spirits and elements, calling on '
              'earth, fire, water and air to heal allies and strike foes.',
    'Mage': 'Mages are scholars of the arcane who shape fire, frost and '
            'raw arcane power through study and discipline.',
    'Warlock': 'Warlocks draw on fel and shadow magic, binding demons to '
               'their will and laying curses on their enemies.',
    'Druid': 'Druids are guardians of nature who take the shapes of '
             'beasts and wield the power of the wild and the moon.',
}

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
    return lines


def character_lore_lines(
    db, guid, name: str, race: str, class_name: str,
) -> List[str]:
    """Race outlook and class calling for any character; empty when the
    race or class is unknown."""
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
