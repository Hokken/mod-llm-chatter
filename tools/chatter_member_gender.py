"""Genders of the other characters a prompt names, so the LLM refers to
party members, the real player and battleground players with matching
pronouns instead of defaulting to he/him.

Only characters are looked up: party rosters, and battleground payload keys
that always name players. Creature, pet and enemy-unit names (kill,
spell and callout targets) are never matched against character rows.
"""

import logging
import re
from typing import Dict, Iterable, Optional

from chatter_shared import get_gender_label

logger = logging.getLogger(__name__)

# Battleground payload keys that only ever hold player names: flags are
# carried, dropped and returned by players, nodes are claimed by players,
# and spell casters, the fallen teammate and achievers are group members.
# achiever_name may be a batched "A, B and C" list (format_name_list).
# Entries of the payload's real_players roster are checked as well.
BG_PLAYER_NAME_KEYS = (
    'carrier_name',
    'scorer_name',
    'dropper_name',
    'returner_name',
    'claimer_name',
    'actor_name',
    'friendly_flag_carrier',
    'enemy_flag_carrier',
    'caster_name',
    'dead_name',
    'achiever_name',
)


def gender_from_id(value) -> str:
    """'female'/'male' for a payload gender id (0 or 1, int or str);
    '' for anything else, so a missing value never becomes male."""
    if isinstance(value, bool):
        return ''
    try:
        gender_id = int(str(value).strip())
    except (TypeError, ValueError):
        return ''
    if gender_id not in (0, 1):
        return ''
    return get_gender_label(gender_id)


def gender_prefix(bot) -> str:
    """'female ' / 'male ' for a speaker header; '' when unknown."""
    gender = (bot or {}).get('gender') or ''
    return f"{gender} " if gender else ''


def get_character_genders(db, names: Iterable[str]) -> Dict[str, str]:
    """Map character names to 'female'/'male'.

    Names without a character row or with a NULL gender are left out, so
    an unknown gender stays unknown. Returns {} on any query error.
    """
    wanted = sorted({str(n).strip() for n in names or () if n})
    wanted = [n for n in wanted if n]
    if db is None or not wanted:
        return {}
    genders = {}
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        placeholders = ', '.join(['%s'] * len(wanted))
        cursor.execute(
            "SELECT name, gender FROM characters "
            f"WHERE name IN ({placeholders})",
            tuple(wanted),
        )
        for row in cursor.fetchall():
            gender = row.get('gender')
            if row.get('name') and gender is not None:
                genders[row['name']] = get_gender_label(int(gender))
    except Exception:
        logger.debug("character gender lookup failed", exc_info=True)
        return {}
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
    return genders


def format_gender_line(
    genders: Dict[str, str],
    player_name: Optional[str] = None,
    exclude: Iterable[str] = (),
) -> str:
    """One prompt line stating who is female or male; '' when none known."""
    skip = {n for n in exclude if n}
    parts = []
    for name in sorted(genders):
        if name in skip or genders[name] not in ('female', 'male'):
            continue
        tag = " (the player)" if player_name and name == player_name else ""
        parts.append(f"{name}{tag} is {genders[name]}")
    if not parts:
        return ''
    return (
        f"Genders: {', '.join(parts)}. "
        "Use matching pronouns when referring to them."
    )


def _group_member_names(db, group_id) -> list:
    """Names of everyone currently in the group; [] on any error."""
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT c.name FROM group_member gm "
            "JOIN characters c ON c.guid = gm.memberGuid "
            "WHERE gm.guid = %s",
            (group_id,),
        )
        return [r['name'] for r in cursor.fetchall() if r.get('name')]
    except Exception:
        logger.debug("group member lookup failed", exc_info=True)
        return []
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass


def get_genders_by_guid(db, guids: Iterable) -> Dict[int, str]:
    """Map character guids to 'female'/'male'; same contract as
    get_character_genders (unknown left out, {} on error)."""
    wanted = set()
    for guid in guids or ():
        try:
            if int(guid) > 0:
                wanted.add(int(guid))
        except (TypeError, ValueError):
            continue
    if db is None or not wanted:
        return {}
    genders = {}
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        placeholders = ', '.join(['%s'] * len(wanted))
        cursor.execute(
            "SELECT guid, gender FROM characters "
            f"WHERE guid IN ({placeholders})",
            tuple(sorted(wanted)),
        )
        for row in cursor.fetchall():
            gender = row.get('gender')
            if row.get('guid') is not None and gender is not None:
                genders[int(row['guid'])] = get_gender_label(int(gender))
    except Exception:
        logger.debug("character gender lookup failed", exc_info=True)
        return {}
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
    return genders


def genders_by_named_guid(db, named_guids) -> Dict[str, str]:
    """{name: guid} -> {name: 'female'/'male'} for names whose guid is
    known; unknown genders are left out."""
    named = {}
    for name, guid in (named_guids or {}).items():
        try:
            named[name] = int(guid)
        except (TypeError, ValueError):
            continue
    by_guid = get_genders_by_guid(db, named.values())
    return {
        name: by_guid[guid] for name, guid in named.items()
        if guid in by_guid
    }


def attach_bot_genders(db, bots) -> None:
    """Fill an empty bot['gender'] from bot['guid'] (one query)."""
    missing = [b for b in bots or () if not b.get('gender')]
    if not missing:
        return
    genders = get_genders_by_guid(db, (b.get('guid') for b in missing))
    for bot in missing:
        try:
            gender = genders.get(int(bot.get('guid') or 0))
        except (TypeError, ValueError):
            gender = None
        if gender:
            bot['gender'] = gender


def speaker_gender_line(bots) -> str:
    """Gender line for the speakers of a multi-bot prompt (no DB)."""
    return format_gender_line({
        b['name']: b.get('gender')
        for b in bots or ()
        if b.get('name') and b.get('gender')
    })


def with_character_genders(
    prompt, db, names, player_name=None, exclude=(),
):
    """prompt with a gender line for named player characters appended.

    Only for names that are always player characters (General chat
    speakers, the real player); never for NPC or creature names.
    """
    names = list(names or ())
    if player_name:
        names.append(player_name)
    line = format_gender_line(
        get_character_genders(db, names),
        player_name=player_name, exclude=exclude,
    )
    return prompt + f"\n{line}" if line else prompt


def party_gender_line(db, group_id, speaker_name: str = '') -> str:
    """Gender line for the speaker's party: fellow bots and the player."""
    if not group_id:
        return ''
    # Local import: chatter_group_state imports this module.
    from chatter_group_state import (
        get_group_members,
        get_group_player_name,
    )
    try:
        members = list(get_group_members(db, group_id))
    except Exception:
        members = []
    try:
        player_name = get_group_player_name(db, group_id)
    except Exception:
        player_name = None
    # Current membership adds every other human in the group (and bots
    # whose trait rows are not written yet); only the player is tagged.
    names = (
        members + _group_member_names(db, group_id)
        + ([player_name] if player_name else [])
    )
    return format_gender_line(
        get_character_genders(db, names),
        player_name=player_name,
        exclude=(speaker_name,),
    )


def with_party_genders(prompt: str, db, group_id, speaker_name='') -> str:
    """prompt with the party gender line appended, when one is known."""
    line = party_gender_line(db, group_id, speaker_name)
    # prompt + str keeps PromptParts system prompt and contract metadata.
    return prompt + f"\n{line}" if line else prompt


def name_mentioned(name: str, prompt: str) -> bool:
    """Whole-name match: "Ana" inside "Banana" is not a mention."""
    return bool(re.search(
        rf"(?<!\w){re.escape(name)}(?!\w)", prompt
    ))


def bg_subject_gender_line(
    db, extra_data, prompt: str, speaker_name: str = '',
) -> str:
    """Gender line for players a battleground prompt names.

    Only names the prompt already shows are included, so visibility gates
    that withhold a name from the prompt also withhold its gender.
    """
    if not isinstance(extra_data, dict) or not prompt:
        return ''
    candidates = []
    for key in BG_PLAYER_NAME_KEYS:
        candidates.extend(split_name_list(extra_data.get(key)))
    # Real players on the speaker's team, printed by _bg_base_context.
    for entry in extra_data.get('real_players') or ():
        if isinstance(entry, dict):
            candidates.extend(split_name_list(entry.get('name')))
    # Batched Arathi Basin node changes keep their actor per change.
    for change in extra_data.get('node_changes') or ():
        if isinstance(change, dict):
            candidates.extend(split_name_list(change.get('actor_name')))
    names = [
        n for n in candidates
        if n != speaker_name and name_mentioned(n, prompt)
    ]
    return format_gender_line(get_character_genders(db, names))


def split_name_list(value):
    """Names in a payload value: one name, a list, or "A, B and C"."""
    if isinstance(value, (list, tuple)):
        items = value
    elif isinstance(value, str):
        items = re.split(r", | and ", value)
    else:
        return []
    return [n.strip() for n in items if isinstance(n, str) and n.strip()]
