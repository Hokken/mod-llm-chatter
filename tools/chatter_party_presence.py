"""Group awareness for bots speaking outside party chat.

A grouped bot that speaks in /say, General, Guild or a yell is told
about its own group, so it never meets its companions as strangers
(issue #94). Only facts are passed:

- the roster and who is actually nearby, from the C++ ``group``
  object (live when the line was written);
- the speaker's own location (``group.self``);
- for a party with a real player: party lines that were actually
  delivered, and recent quest / dungeon / boss / zone events, both
  strictly after the speaker joined (``member_since``).

Raid speakers get the roster plus raid-channel lines only: party
lines reach one subgroup, which is not recorded. The conversation
thread topic is never used: its start time is the bridge's adoption
time, not delivery time.

The activity ring is in-memory and bounded; it is lost on restart,
and an unknown fact is simply left out.
"""

import logging
import threading
import time
from collections import deque
from typing import Dict, Iterable, List, Optional, Tuple

from chatter_member_gender import (
    format_gender_line,
    get_character_genders,
)

logger = logging.getLogger(__name__)

_CONFIG_PREFIX = 'LLMChatter.GroupAwareness.'

_RING_EVENT_TYPES = frozenset((
    'bot_group_quest_accept',
    'bot_group_quest_accept_batch',
    'bot_group_quest_complete',
    'bot_group_dungeon_entry',
    'bot_group_zone_transition',
    'bot_group_kill',
))

_lock = threading.Lock()
# group_id -> deque of (occurred_at, kind, label, quest_id)
_rings: Dict[int, deque] = {}
# group_id -> time the group's state was cleared
_tombstones: Dict[int, float] = {}
# Events from before every session ended are ignored.
_all_ended_at = 0.0


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
def _int_config(config, name: str, default: int, low: int,
                high: int) -> int:
    try:
        value = int(str((config or {}).get(
            _CONFIG_PREFIX + name, default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(low, min(high, value))


def enabled(config) -> bool:
    return _int_config(config, 'Enable', 1, 0, 1) == 1


def _history_lines(config) -> int:
    return _int_config(config, 'HistoryLines', 4, 0, 8)


def _window_seconds(config) -> int:
    return _int_config(config, 'WindowSeconds', 600, 30, 7200)


def _max_entries(config) -> int:
    return _int_config(config, 'ActivityMaxEntries', 5, 1, 10)


# ------------------------------------------------------------------
# Activity ring
# ------------------------------------------------------------------
def _event_occurred_at(db, event: Dict) -> Optional[float]:
    """Unix time the in-game event was queued (event row
    created_at), never the time the bridge processed it."""
    event_id = event.get('id')
    if db is None or not event_id:
        return None
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT UNIX_TIMESTAMP(created_at) AS ts "
            "FROM llm_chatter_events WHERE id = %s",
            (event_id,),
        )
        row = cursor.fetchone()
        if row and row.get('ts') is not None:
            return float(row['ts'])
    except Exception:
        logger.error("group awareness: event time lookup failed",
                     exc_info=True)
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
    return None


def _ring_entries_for(event_type: str, extra: Dict) -> List[Tuple]:
    """(kind, label, quest_id) facts carried by one group event."""
    if event_type == 'bot_group_quest_accept':
        name = str(extra.get('quest_name') or '').strip()
        return [('accept', name, int(extra.get('quest_id') or 0))] \
            if name else []
    if event_type == 'bot_group_quest_accept_batch':
        names = extra.get('quest_names') or []
        if not isinstance(names, list):
            return []
        return [('accept', str(n).strip(), 0)
                for n in names if str(n).strip()]
    if event_type == 'bot_group_quest_complete':
        name = str(extra.get('quest_name') or '').strip()
        return [('complete', name, int(extra.get('quest_id') or 0))] \
            if name else []
    if event_type == 'bot_group_dungeon_entry':
        name = str(extra.get('map_name') or '').strip()
        return [('dungeon', name, 0)] if name else []
    if event_type == 'bot_group_zone_transition':
        name = str(extra.get('zone_name') or '').strip()
        return [('zone', name, 0)] if name else []
    if event_type == 'bot_group_kill':
        name = str(extra.get('creature_name') or '').strip()
        if name and int(extra.get('is_boss') or 0):
            return [('boss', name, 0)]
    return []


def _evict_locked(now: float, window: int) -> None:
    for gid in [g for g, ring in _rings.items()
                if not ring or ring[-1][0] < now - window]:
        del _rings[gid]
    for gid in [g for g, t in _tombstones.items()
                if t < now - window]:
        del _tombstones[gid]


def note_group_event(db, event: Dict, extra: Optional[Dict],
                     config) -> None:
    """Record the facts of one group event in the activity ring.

    Called before the event's handler runs; the event already
    happened in game, so nothing depends on any LLM output.
    """
    if not enabled(config):
        return
    event_type = str(event.get('event_type') or '')
    if event_type not in _RING_EVENT_TYPES or not isinstance(
            extra, dict):
        return
    try:
        group_id = int(event.get('_group_id')
                       or extra.get('group_id') or 0)
    except (TypeError, ValueError):
        return
    if group_id <= 0:
        return
    facts = _ring_entries_for(event_type, extra)
    if not facts:
        return
    occurred_at = _event_occurred_at(db, event)
    if occurred_at is None:
        return

    window = _window_seconds(config)
    now = time.time()
    with _lock:
        tomb = _tombstones.get(group_id)
        if ((tomb is not None and occurred_at <= tomb)
                or occurred_at <= _all_ended_at):
            return
        ring = _rings.get(group_id)
        max_entries = _max_entries(config)
        if ring is None or ring.maxlen != max_entries:
            ring = deque(ring or (), maxlen=max_entries)
            _rings[group_id] = ring
        merged = sorted(
            list(ring) + [(occurred_at, kind, label, quest_id)
                          for kind, label, quest_id in facts],
            key=lambda entry: entry[0],
        )
        ring.clear()
        ring.extend(merged)
        _evict_locked(now, window)


def clear_group(group_id) -> None:
    """Forget a group's activity; late events from before this
    moment are ignored."""
    try:
        gid = int(group_id or 0)
    except (TypeError, ValueError):
        return
    if gid <= 0:
        return
    with _lock:
        _rings.pop(gid, None)
        _tombstones[gid] = time.time()


def reconcile_active_groups(active_group_ids: Iterable) -> None:
    """Forget every group that no longer has a session (ended by
    any path: last bot removed, disband, logout, C++ cleanup)."""
    active = set()
    for gid in active_group_ids or ():
        try:
            active.add(int(gid))
        except (TypeError, ValueError):
            continue
    now = time.time()
    with _lock:
        for gid in [g for g in _rings if g not in active]:
            del _rings[gid]
            _tombstones[gid] = now


def end_all_sessions() -> None:
    """Every session ended (last real player offline): forget all
    activity and ignore late events from before this moment."""
    global _all_ended_at
    with _lock:
        _rings.clear()
        _tombstones.clear()
        _all_ended_at = time.time()


def reset_state() -> None:
    """Testing hook: forget everything, including cutoffs."""
    global _all_ended_at
    with _lock:
        _rings.clear()
        _tombstones.clear()
        _all_ended_at = 0.0


def _activity_facts(group_id: int, member_since: float,
                    window: int) -> List[str]:
    now = time.time()
    with _lock:
        entries = list(_rings.get(group_id) or ())
    entries = [e for e in entries
               if e[0] > member_since and e[0] > now - window]
    if not entries:
        return []

    quests: Dict[str, Dict[str, float]] = {}
    order: List[Tuple[float, str, str]] = []
    for occurred_at, kind, label, quest_id in entries:
        if kind in ('accept', 'complete'):
            # Batched accepts carry names only, so every quest fact
            # is keyed by its name: an accept and a completion of the
            # same quest always meet.
            key = label.casefold()
            state = quests.setdefault(key, {'label': label})
            state[kind] = max(state.get(kind, 0.0), occurred_at)
            continue
        order.append((occurred_at, kind, label))
    for state in quests.values():
        completed = state.get('complete', 0.0)
        accepted = state.get('accept', 0.0)
        if completed and completed > accepted:
            order.append((completed, 'turned_in', state['label']))
        else:
            order.append((accepted, 'picked_up', state['label']))
    order.sort(key=lambda item: item[0])

    phrases = {
        'picked_up': 'picked up the quest "{}"',
        'turned_in': 'turned in the quest "{}"',
        'dungeon': 'entered {}',
        'zone': 'arrived in {}',
        'boss': 'defeated {}',
    }
    return [phrases[kind].format(label)
            for _, kind, label in order if kind in phrases]


# ------------------------------------------------------------------
# Delivered party lines
# ------------------------------------------------------------------
def _delivered_lines(db, group_id: int, member_since: int,
                     is_raid: bool, limit: int,
                     window: int) -> List[Tuple[str, str, bool]]:
    """(speaker, text, is_player) for lines the group actually heard,
    strictly after the speaker joined, oldest first."""
    if db is None or limit <= 0:
        return []
    # (time heard, source, id, speaker, text, is_player)
    rows: List[Tuple[float, int, int, str, str, bool]] = []
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, bot_name AS name, message, "
            "UNIX_TIMESTAMP(delivered_at) AS ts "
            "FROM llm_chatter_messages "
            "WHERE channel = %s AND group_id = %s "
            "AND delivered = 1 AND delivered_at IS NOT NULL "
            "AND drop_reason IS NULL "
            "AND UNIX_TIMESTAMP(delivered_at) > "
            "GREATEST(%s, UNIX_TIMESTAMP() - %s) "
            "ORDER BY delivered_at DESC, id DESC LIMIT %s",
            ('raid' if is_raid else 'party', group_id,
             member_since, window, limit),
        )
        for row in cursor.fetchall() or []:
            rows.append((float(row.get('ts') or 0), 0,
                         int(row.get('id') or 0),
                         str(row.get('name') or ''),
                         str(row.get('message') or ''), False))
        if not is_raid:
            cursor.execute(
                "SELECT id, speaker_name AS name, message, "
                "UNIX_TIMESTAMP(created_at) AS ts "
                "FROM llm_group_chat_history "
                "WHERE group_id = %s AND is_bot = 0 "
                "AND UNIX_TIMESTAMP(created_at) > "
                "GREATEST(%s, UNIX_TIMESTAMP() - %s) "
                "ORDER BY created_at DESC, id DESC LIMIT %s",
                (group_id, member_since, window, limit),
            )
            for row in cursor.fetchall() or []:
                rows.append((float(row.get('ts') or 0), 1,
                             int(row.get('id') or 0),
                             str(row.get('name') or ''),
                             str(row.get('message') or ''), True))
    except Exception:
        logger.error("group awareness: party line lookup failed",
                     exc_info=True)
        return []
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
    # The SQL already applies the bounds; the strict join-second
    # boundary is re-checked here so it holds whatever the query.
    rows = [r for r in rows
            if r[3] and r[4] and r[0] > member_since]
    # Chronological by when each line was heard; the id breaks ties
    # within one second.
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    return [(name, text, is_player)
            for _, _, _, name, text, is_player in rows[-limit:]]


# ------------------------------------------------------------------
# Rendering
# ------------------------------------------------------------------
def speaker_group(speaker: Dict) -> Dict:
    group = speaker.get('group') if isinstance(speaker, dict) else None
    if not isinstance(group, dict):
        return {}
    try:
        if int(group.get('group_id') or 0) <= 0:
            return {}
    except (TypeError, ValueError):
        return {}
    return group


def _member_phrase(member: Dict) -> str:
    name = str(member.get('name') or '').strip()
    if not name:
        return ''
    tags = []
    if member.get('is_player'):
        tags.append('the player')
    if member.get('near'):
        tags.append('here')
    elif member.get('same_zone'):
        tags.append('elsewhere in this zone')
    else:
        tags.append('elsewhere')
    return f"{name} ({', '.join(tags)})"


def _self_place(group: Dict) -> str:
    place = group.get('self') if isinstance(group.get('self'),
                                            dict) else {}
    area = str(place.get('area_name') or '').strip()
    zone = str(place.get('zone_name') or '').strip()
    parts = [p for p in (area, zone) if p]
    if len(parts) == 2 and parts[0] == parts[1]:
        parts = parts[:1]
    text = ', '.join(parts)
    map_name = str(place.get('map_name') or '').strip()
    if place.get('is_instance') and map_name:
        text = f"inside {map_name}" + (f" ({text})" if text else '')
    return text


def near_companions(speakers: Iterable[Dict]) -> Dict[str, str]:
    """name -> speaker for group members marked near a speaker."""
    tagged: Dict[str, str] = {}
    for speaker in speakers or ():
        group = speaker_group(speaker)
        for member in group.get('members') or ():
            if isinstance(member, dict) and member.get('near'):
                name = str(member.get('name') or '').strip()
                if name and name not in tagged:
                    tagged[name] = str(speaker.get('name') or '')
    return tagged


def tag_companions(names: Iterable[str],
                   speakers: Iterable[Dict],
                   config=None) -> List[str]:
    """Mark nearby names that travel with one of the speakers.
    Names are returned unchanged when group awareness is off."""
    if not enabled(config):
        return list(names or ())
    tagged = near_companions(speakers)
    out = []
    for name in names or ():
        owner = tagged.get(name)
        out.append(f"{name} (travelling with {owner})"
                   if owner else name)
    return out


# Channel name used by the presence block for guild speakers.
GUILD_PRESENCE_CHANNEL = 'guild chat'


def candidate_group(extra: Optional[Dict], guid) -> Dict:
    """The group object C++ sent for one candidate bot in
    `bot_groups` (General replies, transport arrivals); {} when
    the bot is ungrouped or the payload predates it."""
    groups = extra.get('bot_groups') if isinstance(extra, dict) else None
    if not isinstance(groups, dict):
        return {}
    try:
        key = str(int(guid))
    except (TypeError, ValueError):
        return {}
    group = groups.get(key)
    return group if isinstance(group, dict) else {}


def with_group_presence(prompt: str, db, config,
                        extra: Optional[Dict],
                        speakers: Iterable[Tuple],
                        channel_label: str,
                        player_name: str = '') -> str:
    """prompt with the presence block appended for the given
    (guid, name) speakers; unchanged when none of them is
    grouped."""
    lines = build_presence_lines(
        db,
        [{'name': name, 'group': candidate_group(extra, guid)}
         for guid, name in speakers or ()],
        config, channel_label, player_name=player_name,
    )
    return prompt + "\n" + "\n".join(lines) if lines else prompt


def build_presence_lines(
    db,
    speakers: List[Dict],
    config,
    channel_label: str,
    player_name: str = '',
) -> List[str]:
    """Per-speaker group knowledge block; [] when no speaker is
    grouped (the prompt then stays exactly as before)."""
    if not enabled(config):
        return []
    grouped = [s for s in speakers or () if speaker_group(s)]
    if not grouped:
        return []

    window = _window_seconds(config)
    history_limit = _history_lines(config)
    lines = ["What each speaker knows about their own group "
             "(no one else knows it):"]
    gender_names: List[str] = []
    line_cache: Dict[Tuple[int, int, bool], List] = {}

    for speaker in grouped:
        group = speaker_group(speaker)
        name = str(speaker.get('name') or 'Someone')
        group_id = int(group.get('group_id') or 0)
        is_raid = bool(group.get('is_raid'))
        members = [m for m in group.get('members') or ()
                   if isinstance(m, dict)]
        member_names = [str(m.get('name') or '') for m in members]
        gender_names.extend(n for n in member_names if n)

        kind = 'raid' if is_raid else 'party'
        phrases = [p for p in (_member_phrase(m) for m in members) if p]
        place = _self_place(group)
        head = f"- {name}" + (f" ({place})" if place else '') + ": "
        # The member list is only the online part of the speaker's
        # party (or of its raid subgroup), so nobody's absence from it
        # is stated as a fact.
        if is_raid:
            head += ("in a raid" + (
                f"; in their subgroup: {', '.join(phrases)}."
                if phrases else "."))
        elif phrases:
            head += f"in a party with {', '.join(phrases)}."
        else:
            head += "in a party."
        if phrases:
            head += (" They already know each other: never offers to "
                     "group with them or greets them as strangers.")

        private: List[str] = []
        try:
            member_since = int(group.get('member_since') or 0)
        except (TypeError, ValueError):
            member_since = 0
        has_provenance = (member_since > 0
                          and bool(group.get('with_real_player')))
        if has_provenance and not is_raid:
            facts = _activity_facts(group_id, member_since, window)
            if facts:
                private.append(
                    "The party recently " + '; '.join(facts) + '.')
        if has_provenance and history_limit > 0:
            key = (group_id, member_since, is_raid)
            if key not in line_cache:
                line_cache[key] = _delivered_lines(
                    db, group_id, member_since, is_raid,
                    history_limit, window)
            heard = line_cache[key]
            if heard:
                rendered = ' / '.join(
                    f"{who}{' (player)' if is_player else ''}: {text}"
                    for who, text, is_player in heard)
                private.append(
                    f"Lately in {kind} chat (not said here): "
                    f"{rendered}")
        lines.append(head + (' ' + ' '.join(private) if private else ''))

    outsiders = [str(s.get('name') or '') for s in speakers or ()
                 if not speaker_group(s) and s.get('name')]
    if outsiders:
        lines.append(f"{', '.join(outsiders)} "
                     f"{'knows' if len(outsiders) == 1 else 'know'} "
                     "none of this.")
    if gender_names:
        gender_line = format_gender_line(
            get_character_genders(db, gender_names),
            player_name=player_name or None,
            exclude=[str(s.get('name') or '') for s in grouped],
        )
        if gender_line:
            lines.append(gender_line)
    lines.append(
        f"This is {channel_label}: others can hear. Group matters may "
        "come up if it fits, but need not. Mention only plans that "
        "appear above.")
    return lines
