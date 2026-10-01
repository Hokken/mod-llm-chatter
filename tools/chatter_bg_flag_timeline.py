"""
chatter_bg_flag_timeline.py — per-match WSG flag event
timeline for mod-llm-chatter.

Flag events are queued once per real player (the event's
subject) and carry the BG instance id, so one query scoped
to (subject_guid, bg_instance_id) yields the flag history of
exactly one match as that player saw it. The decisions below
are pure functions over that ordered history (event id order
is queue order), so they don't depend on processing time.
"""

import logging

LOG = logging.getLogger("chatter_bg_flag_timeline")

FLAG_EVENT_TYPES = (
    'bg_flag_picked_up',
    'bg_flag_dropped',
    'bg_flag_captured',
    'bg_flag_returned',
)

# Only this much history is fetched; a WSG match is shorter.
LOOKBACK_SECONDS = 3600


def fetch_match_flag_events(db, event, extra_data):
    """Flag events for the same recipient and BG instance
    as `event`, oldest first. [] when unscoped."""
    subject_guid = event.get('subject_guid')
    if not subject_guid:
        return []
    instance_id = extra_data.get('bg_instance_id')
    placeholders = ', '.join(['%s'] * len(FLAG_EVENT_TYPES))
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, event_type, created_at, "
            "JSON_UNQUOTE(JSON_EXTRACT(extra_data, "
            "'$.flag_team')) AS flag_team, "
            "JSON_UNQUOTE(JSON_EXTRACT(extra_data, "
            "'$.carrier_name')) AS carrier_name, "
            "JSON_UNQUOTE(JSON_EXTRACT(extra_data, "
            "'$.dropper_name')) AS dropper_name "
            "FROM llm_chatter_events "
            "WHERE subject_guid = %s "
            f"AND event_type IN ({placeholders}) "
            "AND JSON_EXTRACT(extra_data, "
            "'$.bg_instance_id') <=> %s "
            "AND created_at >= DATE_SUB("
            "(SELECT created_at FROM llm_chatter_events "
            "WHERE id = %s), INTERVAL %s SECOND) "
            "ORDER BY id",
            (subject_guid, *FLAG_EVENT_TYPES,
             instance_id, event['id'], LOOKBACK_SECONDS),
        )
        return list(cursor.fetchall())
    finally:
        cursor.close()


def _same_flag(row, event_type, flag_team):
    return (
        row.get('event_type') == event_type
        and row.get('flag_team') == flag_team
    )


def drop_already_returned(rows, drop_id, flag_team):
    """True when the flag this drop belongs to was (or is
    now) returned within the same carry lifecycle: after the
    pickup that preceded the drop and before the next
    pickup. Covers a return queued before the drop (poll
    lag) and one queued after it (processing delay)."""
    start = max(
        (r['id'] for r in rows
         if _same_flag(r, 'bg_flag_picked_up', flag_team)
         and r['id'] < drop_id),
        default=0,
    )
    end = min(
        (r['id'] for r in rows
         if _same_flag(r, 'bg_flag_picked_up', flag_team)
         and r['id'] > drop_id),
        default=float('inf'),
    )
    return any(
        _same_flag(r, 'bg_flag_returned', flag_team)
        and start < r['id'] < end
        for r in rows
    )


def is_regrab(rows, pickup_id, pickup_time, flag_team,
              carrier, window_seconds):
    """True when `carrier` dropped this same flag shortly
    before this pickup and nothing else happened to the
    flag in between (no other pickup, return or capture)."""
    if not carrier or window_seconds <= 0:
        return False
    drops = [
        r for r in rows
        if _same_flag(r, 'bg_flag_dropped', flag_team)
        and r.get('dropper_name') == carrier
        and r['id'] < pickup_id
    ]
    if not drops:
        return False
    last_drop = max(drops, key=lambda r: r['id'])
    for r in rows:
        if (last_drop['id'] < r['id'] < pickup_id
                and r.get('flag_team') == flag_team
                and r.get('event_type') != 'bg_flag_dropped'):
            return False
    elapsed = (pickup_time - last_drop['created_at'])
    return elapsed.total_seconds() <= window_seconds


def changed_since(rows, event_id):
    """True when any flag event was queued after
    `event_id` in this match."""
    return any(r['id'] > event_id for r in rows)
