#!/usr/bin/env python3
"""
LLM Chatter Bridge - Generates dynamic bot
conversations via LLM

Supports Anthropic (Claude), OpenAI (GPT), and
Ollama models.

This script:
1. Polls the database for pending chatter requests
2. Sends prompts to LLM API based on bot
   personalities and zone context
3. Supports diverse message types: plain, quest
   links, item drops, quest+rewards
4. Parses responses and inserts messages with
   dynamic timing delays
"""

import argparse
import json
import logging
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

import anthropic
import openai

import chatter_ambient

from chatter_constants import (
    MSG_TYPE_PLAIN, MSG_TYPE_QUEST,
    MSG_TYPE_LOOT, MSG_TYPE_QUEST_REWARD,
    MSG_TYPE_TRADE, MSG_TYPE_SPELL,
)
from chatter_db import (
    get_group_location,
    any_real_players_online,
    cleanup_stale_groups,
    cleanup_all_session_data,
)
from chatter_shared import (
    format_location_label,
    get_class_name, get_race_name,
    get_chatter_mode,
    set_race_lore_chance,
    set_race_vocab_chance,
    set_action_chance,
    set_emote_chance,
    parse_config, get_db_connection,
    parse_extra_data,
    wait_for_database,
    stagger_if_needed,
)
from chatter_events import (
    cleanup_expired_events,
    reset_stuck_processing_events,
)
from chatter_group import (
    init_group_config,
    check_idle_group_chatter,
    check_bot_questions,
)
from chatter_general import (
    init_general_config,
    process_general_player_msg_event,
)
from chatter_cache import refill_precache_pool
from chatter_event_registry import (
    build_handler_map,
    validate_registry,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress noisy HTTP request logging from OpenAI/httpx
# (fires on every Ollama API call)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


# =============================================================================
# REQUEST PROCESSING
# =============================================================================
def process_statement(
    db, cursor, client, config, request, bot: dict
):
    """Process a single statement request."""
    return chatter_ambient.process_statement(
        db, cursor, client, config, request, bot
    )


def process_conversation(
    db, cursor, client, config,
    request, bots: List[dict]
):
    """Process a conversation request with 2-4 bots.

    Args:
        db: Database connection
        cursor: Database cursor
        client: LLM client (Anthropic or OpenAI)
        config: Configuration dict
        request: Queue request row
        bots: List of 2-4 bot dicts with guid, name,
              class, race, level, zone
    """
    return chatter_ambient.process_conversation(
        db, cursor, client, config, request, bots
    )


def process_pending_requests(
    db, client: anthropic.Anthropic, config: dict
):
    """Process all pending chatter requests."""
    cursor = db.cursor(dictionary=True)

    # Cancel stale pending requests (older than 5 minutes)
    cursor.execute("""
        UPDATE llm_chatter_queue
        SET status = 'cancelled'
        WHERE status = 'pending'
          AND created_at < NOW() - INTERVAL 5 MINUTE
    """)
    # Mark stale undelivered messages as delivered so
    # C++ never picks them up (e.g. from a previous
    # session before the player logged out).
    cursor.execute("""
        UPDATE llm_chatter_messages
        SET delivered = 1
        WHERE delivered = 0
          AND deliver_at < NOW() - INTERVAL 5 MINUTE
    """)
    db.commit()

    # Get pending requests
    cursor.execute("""
        SELECT * FROM llm_chatter_queue
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT 1
    """)
    request = cursor.fetchone()

    if not request:
        return False

    request_id = request['id']
    request_type = request['request_type']

    # Mark as processing
    cursor.execute(
        "UPDATE llm_chatter_queue "
        "SET status = 'processing' WHERE id = %s",
        (request_id,)
    )
    db.commit()

    try:
        # Stagger if another system already submitted
        # an LLM call this poll cycle (avoids two
        # systems delivering in the same bucket).
        poll_iv = int(config.get(
            'LLMChatter.Bridge.PollIntervalSeconds', 3
        ))
        stagger_min = float(config.get(
            'LLMChatter.Bridge.InterSystemStaggerMin',
            3
        ))
        stagger_max = float(config.get(
            'LLMChatter.Bridge.InterSystemStaggerMax',
            6
        ))
        stagger_if_needed(
            poll_iv, stagger_min, stagger_max
        )

        # Get zone_id from the request
        zone_id = request.get('zone_id', 0)
        request['zone_id'] = zone_id if zone_id else 0

        if request_type == 'statement':
            raw_class = request['bot1_class']
            raw_race = request['bot1_race']
            bot = {
                'guid': request['bot1_guid'],
                'name': request['bot1_name'],
                'class': (
                    get_class_name(raw_class)
                    if isinstance(raw_class, int)
                    else raw_class
                ),
                'race': (
                    get_race_name(raw_race)
                    if isinstance(raw_race, int)
                    else raw_race
                ),
                'level': request['bot1_level'],
                'zone': request['bot1_zone']
            }
            success = process_statement(
                db, cursor, client,
                config, request, bot
            )
        else:
            # Build list of 2-4 bots from request
            bots = []

            # Helper to build a bot dict with
            # text race/class
            def _make_bot(
                prefix, zone_override=None
            ):
                rc = request[f'{prefix}_class']
                rr = request[f'{prefix}_race']
                zone_key = f'{prefix}_zone'
                if zone_override:
                    zone = zone_override
                elif zone_key in request:
                    zone = request[zone_key]
                else:
                    zone = request['bot1_zone']
                return {
                    'guid': request[
                        f'{prefix}_guid'
                    ],
                    'name': request[
                        f'{prefix}_name'
                    ],
                    'class': (
                        get_class_name(rc)
                        if isinstance(rc, int)
                        else rc
                    ),
                    'race': (
                        get_race_name(rr)
                        if isinstance(rr, int)
                        else rr
                    ),
                    'level': request[
                        f'{prefix}_level'
                    ],
                    'zone': zone,
                }

            # Bot 1 (always present)
            bots.append(_make_bot('bot1'))

            # Bot 2 (always present for conversations)
            if request.get('bot2_guid'):
                bots.append(_make_bot(
                    'bot2', request['bot1_zone']
                ))

            # Bot 3 (optional)
            if request.get('bot3_guid'):
                bots.append(_make_bot(
                    'bot3', request['bot1_zone']
                ))

            # Bot 4 (optional)
            if request.get('bot4_guid'):
                bots.append(_make_bot(
                    'bot4', request['bot1_zone']
                ))

            success = process_conversation(
                db, cursor, client,
                config, request, bots
            )

        # Mark as completed only if processing
        # succeeded
        if success:
            cursor.execute(
                "UPDATE llm_chatter_queue "
                "SET status = 'completed', "
                "processed_at = NOW() "
                "WHERE id = %s",
                (request_id,)
            )
            db.commit()
            return True
        else:
            cursor.execute(
                "UPDATE llm_chatter_queue "
                "SET status = 'failed' "
                "WHERE id = %s",
                (request_id,)
            )
            db.commit()
            return False

    except Exception:
        logger.error(
            "Legacy request %d failed",
            request_id, exc_info=True,
        )
        cursor.execute(
            "UPDATE llm_chatter_queue "
            "SET status = 'failed' WHERE id = %s",
            (request_id,)
        )
        db.commit()
        return False


# =============================================================================
# EVENT PROCESSING
# =============================================================================
def fetch_pending_events(db, config, max_count):
    """Fetch and atomically claim up to max_count
    pending events for parallel processing.

    Returns list of claimed event dicts, each with
    an added '_group_id' key for group serialization.
    """
    cursor = db.cursor(dictionary=True)

    # Single unified query — parallel processing
    # makes transport-specific priority redundant
    cursor.execute("""
        SELECT e.*
        FROM llm_chatter_events e
        WHERE e.status = 'pending'
          AND (e.react_after IS NULL
               OR e.react_after <= NOW())
          AND (e.expires_at IS NULL
               OR e.expires_at > NOW())
          AND (
              e.zone_id IS NULL
              OR e.zone_id = 0
              OR e.event_type LIKE 'bot_group%%'
              OR e.event_type LIKE 'bg_%%'
              OR e.event_type LIKE 'raid_%%'
              OR e.event_type = 'player_general_msg'
              OR e.event_type = 'player_enters_zone'
              OR (
                  EXISTS (
                      SELECT 1 FROM characters c
                      JOIN acore_auth.account a
                          ON c.account = a.id
                      WHERE c.online = 1
                        AND c.zone = e.zone_id
                        AND a.username
                            LIKE 'RNDBOT%%%%'
                  )
                  AND EXISTS (
                      SELECT 1 FROM characters rp
                      JOIN acore_auth.account a
                          ON rp.account = a.id
                      WHERE rp.online = 1
                        AND rp.zone = e.zone_id
                        AND a.username
                            NOT LIKE 'RNDBOT%%%%'
                  )
              )
          )
        ORDER BY e.priority DESC,
                 e.created_at ASC
        LIMIT %s
    """, (max_count,))
    candidates = cursor.fetchall()

    claimed = []
    for event in candidates:
        # Atomic claim via CAS
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = 'processing', "
            "processed_at = NOW() "
            "WHERE id = %s AND status = 'pending'",
            (event['id'],)
        )
        db.commit()
        if cursor.rowcount == 1:
            # Extract group_id for serialization
            group_id = None
            et = event.get('event_type', '')
            if et.startswith('bot_group') or \
               et.startswith('bg_') or \
               et.startswith('raid_'):
                try:
                    extra = event.get('extra_data')
                    if isinstance(extra, str):
                        extra = json.loads(extra)
                    if isinstance(extra, dict):
                        group_id = extra.get(
                            'group_id'
                        )
                except Exception:
                    logger.error(
                        "Failed to parse group_id "
                        "from extra_data for "
                        "event_type=%s",
                        et, exc_info=True,
                    )
            event['_group_id'] = group_id
            claimed.append(event)

    return claimed


def _dispatch_player_general_msg(
    db, client, config, event
):
    """Adapter for general player-message handler
    signature.
    """
    return process_general_player_msg_event(
        event, db, client, config
    )


# Events exempt from the orphaned-group guard.
# Lifecycle events must bypass the llm_group_bot_traits
# existence check because:
# - farewell: C++ deletes traits before Python processes it
# - join/join_batch: traits don't exist yet when they fire
# bot_greeting is included defensively; it doesn't start
# with 'bot_group_' so the guard would never match it
# anyway, but listing it here documents intent.
_ORPHAN_GUARD_EXEMPT = frozenset({
    'bot_group_farewell',
    'bot_group_join',
    'bot_group_join_batch',
    'bot_greeting',  # defensive; doesn't match bot_group_*
    # Emote events carry all bot data in extra_data;
    # they don't need a traits row to produce a response.
    'bot_group_emote_observer',
    'bot_group_emote_reaction',
})

# Handler map built from central event registry.
# player_general_msg uses a local adapter, so we
# inject it after registry-driven generation.
EVENT_HANDLERS = build_handler_map()
EVENT_HANDLERS['player_general_msg'] = (
    _dispatch_player_general_msg
)


EVENT_LOG_OVERRIDES = {
    'bot_group_screenshot_observation': 'Screenshot vision',
    'player_general_msg': 'General chat event',
    'player_enters_zone': 'Zone intrusion',
    'bot_group_low_health': 'State callout',
    'bot_group_oom': 'State callout',
    'bot_group_aggro_loss': 'State callout',
    'bg_match_start': 'BG event',
    'bg_match_end': 'BG event',
    'bg_flag_picked_up': 'BG event',
    'bg_flag_dropped': 'BG event',
    'bg_flag_captured': 'BG event',
    'bg_flag_returned': 'BG event',
    'bg_node_contested': 'BG event',
    'bg_node_captured': 'BG event',
    'bg_pvp_kill': 'BG event',
    'bg_score_milestone': 'BG event',
    'bg_idle_chatter': 'BG event',
    'raid_boss_pull': 'Raid event',
    'raid_boss_kill': 'Raid event',
    'raid_boss_wipe': 'Raid event',
    'raid_idle_morale': 'Raid event',
}


def _event_summary(event):
    """Build compact summary of key extra_data
    fields for diagnostic log lines.
    Returns string like '(killer=X, victim=Y)'
    or '' if no relevant data.
    """
    try:
        ed = event.get('extra_data')
        if isinstance(ed, str):
            ed = json.loads(ed)
        if not isinstance(ed, dict):
            ed = {}
    except Exception:
        ed = {}

    et = event.get('event_type', '')
    subj = event.get('subject_name', '')
    tgt = event.get('target_name', '')
    parts = []

    if et == 'bg_pvp_kill':
        parts = [
            ('killer', ed.get('killer_name', '')),
            ('victim', ed.get('victim_name', '')),
        ]
    elif et == 'bg_flag_picked_up':
        parts = [
            ('carrier',
             ed.get('carrier_name', '')),
            ('flag_team',
             ed.get('flag_team', '')),
        ]
    elif et == 'bg_flag_captured':
        parts = [
            ('scorer',
             ed.get('scorer_name', '')),
            ('flag_team',
             ed.get('flag_team', '')),
        ]
    elif et == 'bg_flag_returned':
        parts = [
            ('returner',
             ed.get('returner_name', '')),
            ('flag_team',
             ed.get('flag_team', '')),
        ]
    elif et == 'bg_flag_dropped':
        parts = [
            ('dropper',
             ed.get('dropper_name', '')),
            ('flag_team',
             ed.get('flag_team', '')),
        ]
    elif et == 'bg_player_death':
        parts = [
            ('dead',
             ed.get('dead_name', '')),
            ('killer',
             ed.get('killer_name', '')),
        ]
    elif et == 'bg_match_end':
        parts = [
            ('winner',
             ed.get('winner', '')),
        ]
    elif et == 'bg_score_milestone':
        parts = [
            ('alliance',
             ed.get('alliance_score', '')),
            ('horde',
             ed.get('horde_score', '')),
        ]
    elif et.startswith('bg_node_'):
        parts = [
            ('node',
             ed.get('node_name', '')),
            ('claimer',
             ed.get('claimer_name', '')),
        ]
    elif et == 'bot_group_kill':
        parts = [
            ('killer', subj),
            ('target',
             ed.get('creature_name', tgt)),
        ]
    elif et == 'bot_group_death':
        parts = [
            ('dead',
             ed.get('dead_name', '')),
            ('reactor', subj),
        ]
    elif et == 'bot_group_loot':
        parts = [
            ('looter', subj),
            ('item',
             ed.get('item_name', '')),
        ]
    elif et == 'bot_group_spell_cast':
        parts = [
            ('caster', subj),
            ('spell',
             ed.get('spell_name', '')),
            ('target',
             ed.get('target', tgt)),
        ]
    elif et == 'bot_group_player_msg':
        pname = ed.get('player_name', '')
        pmsg = ed.get('player_message', '')
        if isinstance(pmsg, str) and len(pmsg) > 40:
            pmsg = pmsg[:40] + '...'
        parts = [
            ('player', pname),
            ('msg', pmsg),
        ]
    elif et == 'bot_group_combat':
        parts = [
            ('bot', subj),
            ('creature',
             ed.get('creature_name', '')),
        ]
    elif et.startswith('bot_group_quest_'):
        parts = [
            ('bot', subj),
            ('quest',
             ed.get('quest_name', '')),
        ]
    elif et in (
        'bot_group_low_health',
        'bot_group_oom',
        'bot_group_aggro_loss',
        'bot_group_resurrect',
        'bot_group_corpse_run',
    ):
        parts = [('bot', subj)]
    elif et == 'bot_group_levelup':
        parts = [
            ('bot', subj),
            ('level',
             ed.get('new_level', '')),
        ]
    elif et == 'bot_group_achievement':
        parts = [
            ('bot', subj),
            ('achievement',
             ed.get('achievement_name', '')),
        ]
    elif et == 'bot_group_wipe':
        parts = [
            ('zone',
             ed.get('zone_name', '')),
        ]
    elif et == 'bot_group_dungeon_entry':
        parts = [
            ('dungeon',
             ed.get('dungeon_name', '')),
        ]
    elif et == 'bot_group_zone_transition':
        parts = [
            ('bot', subj),
            ('zone',
             ed.get('new_zone_name',
                     ed.get('zone_name', ''))),
        ]
    elif et == 'bot_group_nearby_object':
        parts = [
            ('bot', subj),
            ('object',
             ed.get('object_name', '')),
        ]
    elif et == 'bot_group_join':
        parts = [
            ('bot',
             ed.get('bot_name', subj)),
        ]
    elif et == 'bot_group_join_batch':
        names = ed.get('bot_names', [])
        if isinstance(names, list) and names:
            parts = [
                ('bots', ', '.join(
                    str(n) for n in names[:4]
                )),
            ]

    # Filter out empty values and build string
    filled = [
        (k, v) for k, v in parts
        if v not in (None, '', 0)
    ]
    if not filled:
        return ''
    summary = ', '.join(
        f"{k}={v}" for k, v in filled
    )
    return f" ({summary})"


def _log_event_location(db, event, config):
    """Log zone > subzone label for a group event.

    Uses get_group_location (bot traits) as the
    single source of truth for location data.
    """
    try:
        extra = event.get('extra_data')
        if isinstance(extra, str):
            extra = json.loads(extra)
        if not isinstance(extra, dict):
            return
        gid = int(extra.get('group_id', 0) or 0)
        if not gid:
            return
        zone_id, area_id, _ = get_group_location(
            db, gid
        )
        if not zone_id:
            return
        loc = format_location_label(
            zone_id, area_id
        )
        et = event['event_type']
        short = et.replace('bot_group_', '')
        logger.info(
            f"[DEBUG] {short}: {loc}"
        )
    except Exception:
        logger.error(
            "_log_event_location failed",
            exc_info=True,
        )


def process_single_event(event, client, config):
    """Process a single claimed event with its own
    DB connection. Designed for concurrent execution
    in a ThreadPoolExecutor.
    """
    event_id = event['id']
    event_type = event['event_type']
    zone_id = event.get('zone_id')
    db = None
    try:
        db = get_db_connection(config)
        cursor = db.cursor(dictionary=True)

        # Route known events via map.
        handler = EVENT_HANDLERS.get(event_type)
        if handler is not None:
            # Skip orphaned group events: if the
            # group has no traits rows (already
            # cleaned up after player logout /
            # group disband), mark expired and skip.
            # Lifecycle events are exempt — see
            # _ORPHAN_GUARD_EXEMPT at module scope.
            if (event_type.startswith('bot_group_')
                    and event_type
                    not in _ORPHAN_GUARD_EXEMPT):
                gid = event.get('_group_id')
                if gid:
                    cursor.execute(
                        "SELECT 1"
                        " FROM llm_group_bot_traits"
                        " WHERE group_id = %s"
                        " LIMIT 1",
                        (gid,)
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            "UPDATE llm_chatter_events"
                            " SET status = 'expired'"
                            " WHERE id = %s",
                            (event_id,)
                        )
                        db.commit()
                        return False
                else:
                    logger.warning(
                        "bot_group_* event %s has"
                        " no _group_id — orphan"
                        " guard skipped",
                        event_type,
                    )
            # Log location context for group events
            if (event_type.startswith('bot_group_')
                    and config.get(
                        'LLMChatter.DebugLog', '0'
                    ) == '1'):
                _log_event_location(
                    db, event, config
                )
            return handler(db, client, config, event)

        # Unknown event type — no handler registered.
        # Mark as skipped so it doesn't block the
        # queue indefinitely.
        logger.warning(
            "Unknown event_type '%s' (id=%s)"
            " — skipping",
            event_type, event_id,
        )
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = 'skipped' "
            "WHERE id = %s",
            (event_id,)
        )
        db.commit()
        return False

    except Exception:
        logger.error(
            "Event %d (%s) unhandled error",
            event_id, event_type,
            exc_info=True,
        )
        # Try to mark as skipped
        try:
            if db:
                c = db.cursor()
                c.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
        except Exception:
            logger.error(
                "Fallback skip for event %d also"
                " failed", event_id,
                exc_info=True,
            )
        return False
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass


def _run_with_group_lock(lock, fn, *args, **kwargs):
    """Execute fn while holding a per-group lock.
    Serializes events for the same group."""
    with lock:
        return fn(*args, **kwargs)


def _run_in_worker(fn_name, fn, client, config):
    """Run a function in a worker thread with its
    own DB connection. Follows process_single_event
    pattern."""
    db = None
    try:
        db = get_db_connection(config)
        fn(db, client, config)
    except Exception:
        logger.error(
            "Worker '%s' failed", fn_name,
            exc_info=True,
        )
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass


# Keep this aligned with the High-tier band in
# modules/mod-llm-chatter/src/LLMChatterShared.cpp.
_PRIORITY_URGENT_FLOOR = 20


def _config_enabled(config, key, default='1'):
    """Parse a boolean-like 0/1 config flag."""
    return str(config.get(key, default)).strip() == '1'


def _config_int(config, key, default, minimum=None):
    """Parse an integer config value with optional clamp."""
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError):
        value = default

    if minimum is not None:
        value = max(minimum, value)

    return value


def _priority_bridge_yield_enabled(config):
    """Phase 2 gate for bridge-side backlog yielding."""
    return (
        _config_enabled(
            config,
            'LLMChatter.PrioritySystem.Enable'
        )
        and _config_enabled(
            config,
            'LLMChatter.PrioritySystem.BridgeYieldEnable',
            '1'
        )
    )


def _priority_safety_enabled(config):
    """Phase 4 gate for emergency provider-safety mode."""
    return (
        _config_enabled(
            config,
            'LLMChatter.PrioritySystem.Enable'
        )
        and _config_enabled(
            config,
            'LLMChatter.PrioritySystem.SafetyEnable',
            '1'
        )
    )


def _has_ready_event_backlog(db, priority_floor=None):
    """Check for any ready pending event, optionally by floor."""
    cursor = db.cursor()
    sql = [
        "SELECT 1",
        "FROM llm_chatter_events",
        "WHERE status = 'pending'",
    ]
    params = []
    if priority_floor is not None:
        sql.append("AND priority >= %s")
        params.append(int(priority_floor))
    sql.extend([
        "AND (react_after IS NULL",
        "     OR react_after <= NOW())",
        "AND (expires_at IS NULL",
        "     OR expires_at > NOW())",
        "LIMIT 1",
    ])
    cursor.execute("\n".join(sql), tuple(params))
    return cursor.fetchone() is not None


def _has_urgent_event_backlog(db, urgent_floor):
    """Check whether any ready T1/T2 event is pending."""
    return _has_ready_event_backlog(
        db, priority_floor=urgent_floor
    )


def _has_pending_legacy_requests(db):
    """Check whether the legacy ambient queue has pending work."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT 1
        FROM llm_chatter_queue
        WHERE status = 'pending'
        LIMIT 1
    """)
    return cursor.fetchone() is not None


def _event_is_urgent(event, urgent_floor):
    """Return True when the claimed event belongs to T1/T2."""
    try:
        return int(event.get('priority') or 0) >= int(
            urgent_floor
        )
    except (TypeError, ValueError):
        return False


def _get_group_lock(
    group_locks,
    group_locks_lock,
    group_id,
    *,
    priority_banded,
    urgent,
):
    """Return the correct per-group lock for the event lane."""
    with group_locks_lock:
        if group_id not in group_locks:
            if priority_banded:
                group_locks[group_id] = {
                    'urgent': threading.Lock(),
                    'filler': threading.Lock(),
                }
            else:
                group_locks[group_id] = threading.Lock()

        entry = group_locks[group_id]
        if priority_banded:
            if not isinstance(entry, dict):
                entry = {
                    'urgent': threading.Lock(),
                    'filler': threading.Lock(),
                }
                group_locks[group_id] = entry
            lane = 'urgent' if urgent else 'filler'
            return entry[lane]
        return entry


def _evict_unused_group_locks(
    group_locks,
    group_locks_lock,
    active_group_ids,
):
    """Drop stale per-group locks with no active event futures."""
    with group_locks_lock:
        stale = [
            gid for gid in group_locks.keys()
            if gid not in active_group_ids
        ]
        for gid in stale:
            del group_locks[gid]
        return len(stale)


def _count_in_flight_jobs(*futures):
    """Count active worker tasks for provider-safety heuristics."""
    return sum(
        1 for future in futures
        if future is not None
    )


def _write_db_snapshot(db, snapshot_dir):
    """Write DB state JSON snapshots to the logs dir
    so the log viewer's DB State tab can read them.
    Uses atomic replace to avoid partial reads.
    """
    import os
    import json as _json
    from datetime import datetime, timezone

    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT m.bot_guid,"
            " c.name AS bot_name,"
            " m.player_guid, m.group_id,"
            " m.memory_type, m.memory,"
            " m.mood, m.emote, m.active,"
            " m.used, m.last_used_at,"
            " m.created_at,"
            " m.session_start"
            " FROM llm_bot_memories m"
            " LEFT JOIN characters c"
            "   ON c.guid = m.bot_guid"
            " ORDER BY m.created_at DESC"
            " LIMIT 200"
        )
        memories = cursor.fetchall()

        cursor.execute(
            "SELECT id, status, request_type,"
            " bot1_guid, bot2_guid, bot3_guid,"
            " bot4_guid, created_at"
            " FROM llm_chatter_queue"
            " ORDER BY created_at DESC"
            " LIMIT 100"
        )
        queue = cursor.fetchall()

        cursor.execute(
            "SELECT id, bot_guid, bot_name,"
            " message, channel, delivered,"
            " deliver_at"
            " FROM llm_chatter_messages"
            " ORDER BY deliver_at DESC"
            " LIMIT 100"
        )
        messages = cursor.fetchall()

        cursor.close()

        # Convert datetime/decimal objects
        def _serialise(rows):
            out = []
            for row in rows:
                r = {}
                for k, v in row.items():
                    if hasattr(v, 'isoformat'):
                        r[k] = v.isoformat()
                    else:
                        r[k] = v
                out.append(r)
            return out

        ts = datetime.now(
            timezone.utc
        ).isoformat()

        for fname, rows in [
            ('db_memories.json', memories),
            ('db_queue.json', queue),
            ('db_messages.json', messages),
        ]:
            data = {
                'rows': _serialise(rows),
                'updated': ts,
            }
            path = os.path.join(
                snapshot_dir, fname
            )
            tmp = path + '.tmp'
            with open(
                tmp, 'w', encoding='utf-8'
            ) as f:
                _json.dump(
                    data, f,
                    ensure_ascii=False
                )
            os.replace(tmp, path)

    except Exception:
        logger.error(
            "_write_db_snapshot failed",
            exc_info=True,
        )


# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description='LLM Chatter Bridge'
    )
    parser.add_argument(
        '--config', required=True,
        help='Path to config file'
    )
    args = parser.parse_args()

    # Load config
    config = parse_config(args.config)

    # Check if enabled - if disabled, wait and check
    # periodically
    while config.get('LLMChatter.Enable', '0') != '1':
        time.sleep(60)
        config = parse_config(args.config)

    # Apply config-driven settings to shared module
    set_race_lore_chance(int(config.get(
        'LLMChatter.RaceLoreChance', 15
    )))
    set_race_vocab_chance(int(config.get(
        'LLMChatter.RaceVocabChance', 15
    )))
    set_action_chance(int(config.get(
        'LLMChatter.ActionChance', 10
    )), mode=config.get(
        'LLMChatter.ChatterMode', 'normal'
    ).lower())
    set_emote_chance(int(config.get(
        'LLMChatter.EmoteChance', 50
    )))
    init_group_config(config)
    init_general_config(config)

    # Initialize request logger (no-op if disabled)
    from chatter_request_logger import (
        init_request_logger,
    )
    init_request_logger(config)

    # Derive snapshot dir from log path
    import os as _os
    _log_path = config.get(
        'LLMChatter.RequestLog.Path',
        '/logs/llm_requests.jsonl'
    )
    snapshot_dir = (
        _os.path.dirname(_log_path) or '/logs'
    )

    # Get provider and initialize appropriate client
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()
    model = config.get(
        'LLMChatter.Model',
        'claude-haiku-4-5-20251001'
    )

    if provider == 'ollama':
        # Ollama runs locally - no API key needed
        # Uses OpenAI-compatible API endpoint
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://localhost:11434'
        )
        # Ollama's OpenAI-compatible endpoint is
        # at /v1
        ollama_api_url = (
            f"{base_url.rstrip('/')}/v1"
        )
        client = openai.OpenAI(
            base_url=ollama_api_url,
            api_key="ollama"
        )
    elif provider == 'openai':
        api_key = config.get(
            'LLMChatter.OpenAI.ApiKey', ''
        )
        if not api_key:
            sys.exit(1)
        client = openai.OpenAI(api_key=api_key)
    else:
        # Anthropic (default)
        api_key = config.get(
            'LLMChatter.Anthropic.ApiKey', ''
        )
        if not api_key:
            sys.exit(1)
        client = anthropic.Anthropic(api_key=api_key)

    # Get poll interval
    poll_interval = int(config.get(
        'LLMChatter.Bridge.PollIntervalSeconds', 3
    ))

    # Max concurrent event workers
    try:
        max_concurrent = max(1, min(int(
            config.get(
                'LLMChatter.Bridge.MaxConcurrent',
                '3'
            )
        ), 10))
    except (ValueError, TypeError):
        max_concurrent = 3

    # Check event system config
    use_event_system = (
        config.get(
            'LLMChatter.UseEventSystem', '1'
        ) == '1'
    )
    priority_bridge_yield = _priority_bridge_yield_enabled(
        config
    )
    urgent_floor = _PRIORITY_URGENT_FLOOR

    # Inter-system stagger range (seconds)
    inter_stagger_min = float(config.get(
        'LLMChatter.Bridge.InterSystemStaggerMin', 3
    ))
    inter_stagger_max = float(config.get(
        'LLMChatter.Bridge.InterSystemStaggerMax', 6
    ))

    chatter_mode = get_chatter_mode(config)

    logger.info("=" * 60)
    logger.info("LLM Chatter Bridge v4.0")
    logger.info("=" * 60)
    logger.info(f"ChatterMode: {chatter_mode}")
    logger.info(f"Provider: {provider}")
    logger.info(
        f"Model: {model}"
    )
    if provider == 'ollama':
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://localhost:11434'
        )
        context_size = config.get(
            'LLMChatter.Ollama.ContextSize', 2048
        )
        disable_thinking = (
            config.get(
                'LLMChatter.Ollama.DisableThinking',
                '1'
            ) == '1'
        )
        logger.info(f"Ollama URL: {base_url}")
        logger.info(f"Context size: {context_size}")
        logger.info(
            f"Thinking mode: "
            f"{'disabled (/no_think)' if disable_thinking else 'enabled'}"
        )
    logger.info(f"Poll interval: {poll_interval}s")
    logger.info(
        f"Max concurrent: {max_concurrent}"
    )
    base_max = config.get(
        'LLMChatter.MaxTokens', 200
    )
    convo_max = config.get(
        'LLMChatter.ConversationMaxTokens', base_max
    )
    logger.info(
        f"Max tokens (statements): {base_max}"
    )
    logger.info(
        f"Max tokens (conversations): {convo_max}"
    )
    logger.info(
        f"Event system: "
        f"{'enabled' if use_event_system else 'disabled'}"
    )
    logger.info(
        f"Message type distribution: "
        f"{MSG_TYPE_PLAIN}% plain, "
        f"{MSG_TYPE_QUEST - MSG_TYPE_PLAIN}% quest, "
        f"{MSG_TYPE_LOOT - MSG_TYPE_QUEST}% loot, "
        f"{MSG_TYPE_QUEST_REWARD - MSG_TYPE_LOOT}% "
        f"quest+reward, "
        f"{MSG_TYPE_TRADE - MSG_TYPE_QUEST_REWARD}% "
        f"trade, "
        f"{MSG_TYPE_SPELL - MSG_TYPE_TRADE}% spell"
    )
    precache_enabled = config.get(
        'LLMChatter.GroupChatter.PreCacheEnable',
        '1'
    ) == '1'
    logger.info("-" * 60)
    logger.info("Setup:")
    logger.info(
        f"  Provider: "
        f"{config.get('LLMChatter.Provider', 'anthropic')}"
        f"  Model: "
        f"{config.get('LLMChatter.Model', '(default)')}"
    )
    logger.info(
        f"  ChatterMode: "
        f"{config.get('LLMChatter.ChatterMode', 'roleplay')}"
    )
    logger.info(
        f"  Ollama.BaseUrl: "
        f"{config.get('LLMChatter.Ollama.BaseUrl', 'http://localhost:11434')}"
        f"  ContextSize: "
        f"{config.get('LLMChatter.Ollama.ContextSize', 2048)}"
        f"  DisableThinking: "
        f"{config.get('LLMChatter.Ollama.DisableThinking', 1)}"
    )
    logger.info("-" * 60)
    logger.info("Feature toggles:")
    logger.info(
        f"  GroupChatter: "
        f"{config.get('LLMChatter.GroupChatter.Enable', 1)}"
        f"  GeneralChat: "
        f"{config.get('LLMChatter.GeneralChat.Enable', 1)}"
        f"  BGChatter: "
        f"{config.get('LLMChatter.BGChatter.Enable', 1)}"
        f"  RaidChatter: "
        f"{config.get('LLMChatter.RaidChatter.Enable', 1)}"
    )
    logger.info(
        f"  ZoneIntrusion: "
        f"{config.get('LLMChatter.ZoneIntrusion.Enable', 1)}"
        f"  PreCache: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheEnable', 1)}"
    )
    logger.info("-" * 60)
    logger.info("Ambient / world events:")
    logger.info(
        f"  TriggerChance: "
        f"{config.get('LLMChatter.TriggerChance', 15)}%"
        f"  EventReactionChance: "
        f"{config.get('LLMChatter.EventReactionChance', 15)}%"
    )
    logger.info(
        f"  WeatherAmbientChance: "
        f"{config.get('LLMChatter.WeatherAmbientChance', 0)}%"
        f"  TransportEventChance: "
        f"{config.get('LLMChatter.TransportEventChance', 0)}%"
    )
    logger.info(
        f"  TransportCooldown: "
        f"{config.get('LLMChatter.TransportCooldownSeconds', 600)}s"
        f"  WeatherCooldown: "
        f"{config.get('LLMChatter.WeatherCooldownSeconds', 1800)}s"
        f"  WeatherAmbientCooldown: "
        f"{config.get('LLMChatter.WeatherAmbientCooldownSeconds', 120)}s"
    )
    logger.info(
        f"  DayNightCooldown: "
        f"{config.get('LLMChatter.DayNightCooldownSeconds', 7200)}s"
        f"  HolidayCooldown: "
        f"{config.get('LLMChatter.HolidayCooldownSeconds', 1800)}s"
    )
    logger.info(
        f"  HolidayCityChance: "
        f"{config.get('LLMChatter.HolidayCityChance', 10)}%"
        f"  HolidayZoneChance: "
        f"{config.get('LLMChatter.HolidayZoneChance', 5)}%"
        f"  MinorEventChance: "
        f"{config.get('LLMChatter.Events.MinorEventChance', 20)}%"
    )
    logger.info("-" * 60)
    logger.info("Group chatter:")
    logger.info(
        f"  IdleChance: "
        f"{config.get('LLMChatter.GroupChatter.IdleChance', 10)}%"
        f"  IdleCooldown: "
        f"{config.get('LLMChatter.GroupChatter.IdleCooldown', 30)}s"
    )
    logger.info(
        f"  KillChanceNormal: "
        f"{config.get('LLMChatter.GroupChatter.KillChanceNormal', 20)}%"
        f"  DeathChance: "
        f"{config.get('LLMChatter.GroupChatter.DeathChance', 40)}%"
    )
    logger.info(
        f"  LootChanceGreen: "
        f"{config.get('LLMChatter.GroupChatter.LootChanceGreen', 20)}%"
        f"  LootChanceBlue: "
        f"{config.get('LLMChatter.GroupChatter.LootChanceBlue', 50)}%"
    )
    logger.info(
        f"  SpellCastChance: "
        f"{config.get('LLMChatter.GroupChatter.SpellCastChance', 10)}%"
    )
    logger.info(
        f"  NearbyObjectEnable: "
        f"{config.get('LLMChatter.GroupChatter.NearbyObjectEnable', 1)}"
        f"  NearbyObjectChance: "
        f"{config.get('LLMChatter.GroupChatter.NearbyObjectChance', 10)}%"
    )
    logger.info(
        f"  BotQuestionEnable: "
        f"{config.get('LLMChatter.GroupChatter.BotQuestionEnable', 1)}"
        f"  BotQuestionChance: "
        f"{config.get('LLMChatter.GroupChatter.BotQuestionChance', 1)}%"
    )
    logger.info(
        f"  QuestConversationChance: "
        f"{config.get('LLMChatter.GroupChatter.QuestConversationChance', 30)}%"
    )
    logger.info(
        f"  PlayerMsgConversationChance: "
        f"{config.get('LLMChatter.GroupChatter.PlayerMsgConversationChance', 30)}%"
        f"  SecondBotChance: "
        f"{config.get('LLMChatter.GroupChatter.PlayerMsgSecondBotChance', 25)}%"
    )
    logger.info("-" * 60)
    logger.info("General chat:")
    logger.info(
        f"  ReactionChance: "
        f"{config.get('LLMChatter.GeneralChat.ReactionChance', 40)}%"
        f"  QuestionChance: "
        f"{config.get('LLMChatter.GeneralChat.QuestionChance', 80)}%"
        f"  Cooldown: "
        f"{config.get('LLMChatter.GeneralChat.Cooldown', 30)}s"
    )
    logger.info("-" * 60)
    logger.info("Raid chatter:")
    logger.info(
        f"  MoraleEnable: "
        f"{config.get('LLMChatter.RaidChatter.MoraleEnable', 1)}"
    )
    logger.info("-" * 60)
    logger.info("Prompt / output:")
    logger.info(
        f"  ActionChance: "
        f"{config.get('LLMChatter.ActionChance', 10)}%"
        f"  EmoteChance: "
        f"{config.get('LLMChatter.EmoteChance', 50)}%"
        f"  RaceLoreChance: "
        f"{config.get('LLMChatter.RaceLoreChance', 15)}%"
    )
    logger.info("-" * 60)
    logger.info("Safety / performance:")
    logger.info(
        f"  MaxTokens: "
        f"{config.get('LLMChatter.MaxTokens', 350)}"
        f"  ConversationMaxTokens: "
        f"{config.get('LLMChatter.ConversationMaxTokens', 700)}"
        f"  Temperature: "
        f"{config.get('LLMChatter.Temperature', 0.8)}"
    )
    logger.info(
        f"  MaxMessageLength: "
        f"{config.get('LLMChatter.MaxMessageLength', 250)}"
        f"  MaxPendingRequests: "
        f"{config.get('LLMChatter.MaxPendingRequests', 5)}"
        f"  MaxBotsPerZone: "
        f"{config.get('LLMChatter.MaxBotsPerZone', 8)}"
    )
    logger.info(
        f"  Bridge.PollInterval: "
        f"{config.get('LLMChatter.Bridge.PollIntervalSeconds', 3)}s"
        f"  Bridge.MaxConcurrent: "
        f"{config.get('LLMChatter.Bridge.MaxConcurrent', 3)}"
        f"  InterSystemStagger: "
        f"{inter_stagger_min}s\u2013{inter_stagger_max}s"
    )
    logger.info(
        f"  MessageDelayMin: "
        f"{config.get('LLMChatter.MessageDelayMin', 1000)}ms"
        f"  MessageDelayMax: "
        f"{config.get('LLMChatter.MessageDelayMax', 30000)}ms"
    )
    logger.info(
        f"  DistanceUnit: "
        f"{config.get('LLMChatter.DistanceUnit', 'yards')}"
        f"  BotSpeakerCooldown: "
        f"{config.get('LLMChatter.BotSpeakerCooldownSeconds', 900)}s"
    )
    logger.info(
        f"  EventExpiration: "
        f"{config.get('LLMChatter.EventExpirationSeconds', 600)}s"
        f"  LootRecentCooldown: "
        f"{config.get('LLMChatter.LootRecentCooldownSeconds', 1200)}s"
    )
    logger.info(
        f"  BGChatter.MaxTokens: "
        f"{config.get('LLMChatter.BGChatter.MaxTokens', 32)}"
        f"  PrioritySystem.SafetyEnable: "
        f"{config.get('LLMChatter.PrioritySystem.SafetyEnable', 1)}"
    )
    logger.info("=" * 60)

    # Validate event registry at startup
    validate_registry()

    # Wait for database to be ready
    # (handles Docker startup order)
    if not wait_for_database(config):
        sys.exit(1)

    # Startup cleanup: reset any events stuck in
    # 'processing' from previous crash
    if use_event_system:
        db = None
        try:
            db = get_db_connection(config)
            reset_stuck_processing_events(db)

            # Memory system startup recovery
            if int(config.get(
                'LLMChatter.Memory.Enable', 1
            )):
                from chatter_memory import (
                    activate_orphaned_memories,
                    rehydrate_active_sessions,
                )
                session_min = int(config.get(
                    'LLMChatter.Memory'
                    '.SessionMinutes', 15
                ))
                activate_orphaned_memories(
                    db, session_min
                )
                rehydrate_active_sessions(db)
        except Exception:
            logger.error(
                "Startup memory rehydration failed",
                exc_info=True,
            )
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass

    # Main loop
    last_cleanup = 0
    cleanup_interval = 60  # every 60 seconds
    last_db_snapshot = 0
    db_snapshot_interval = 10  # every 10 seconds
    last_idle_check = 0
    idle_check_interval = int(config.get(
        'LLMChatter.GroupChatter.IdleCheckInterval',
        60
    ))
    last_cache_refill = 0
    cache_refill_interval = 30  # every 30 seconds
    last_question_check = 0
    question_check_interval = int(config.get(
        'LLMChatter.GroupChatter.'
        'BotQuestionCheckInterval',
        30
    ))

    executor = ThreadPoolExecutor(
        max_workers=max_concurrent + 4
    )
    active_futures = []
    active_event_ids = set()
    group_locks = {}
    group_locks_lock = threading.Lock()
    # Background task futures
    precache_future = None
    idle_chatter_future = None
    bot_question_future = None
    legacy_future = None
    # Track online→offline transition for full wipe
    was_players_online = True

    def _harvest_future(f, name):
        """Consume any unexpected worker failure."""
        try:
            f.result()
        except Exception:
            logger.error(
                "Background worker '%s' failed",
                name, exc_info=True,
            )

    while True:
        try:
            # Prune completed event futures
            still_active = []
            for f in active_futures:
                if f.done():
                    active_event_ids.discard(
                        f.event_id
                    )
                    try:
                        f.result()
                    except Exception:
                        logger.error(
                            "Event future failed",
                            exc_info=True,
                        )
                else:
                    still_active.append(f)
            active_futures = still_active
            active_group_ids = {
                future.group_id
                for future in active_futures
                if getattr(future, 'group_id', None)
            }

            # Prune background task futures
            if (
                precache_future
                and precache_future.done()
            ):
                _harvest_future(
                    precache_future, "pre-cache"
                )
                precache_future = None
            if (
                idle_chatter_future
                and idle_chatter_future.done()
            ):
                _harvest_future(
                    idle_chatter_future,
                    "idle-chatter"
                )
                idle_chatter_future = None
            if (
                bot_question_future
                and bot_question_future.done()
            ):
                _harvest_future(
                    bot_question_future,
                    "bot-question"
                )
                bot_question_future = None
            if (
                legacy_future
                and legacy_future.done()
            ):
                _harvest_future(
                    legacy_future,
                    "legacy-requests"
                )
                legacy_future = None

            # DB connection with proper lifecycle
            db = None
            try:
                db = get_db_connection(config)
                current_time = time.time()

                # Global gate: skip all work if no
                # real players are online. Handles
                # clean logout, crash, and alt-F4.
                players_online = (
                    any_real_players_online(db)
                )

                # Transition online → offline: wipe
                # all ephemeral session data once
                if (
                    was_players_online
                    and not players_online
                ):
                    cleanup_all_session_data(db)
                    try:
                        from chatter_memory import (
                            clear_all_sessions,
                        )
                        clear_all_sessions()
                    except Exception:
                        logger.error(
                            "clear_all_sessions failed",
                            exc_info=True,
                        )
                was_players_online = players_online

                # Periodic cleanup (fast SQL,
                # stays on main thread)
                if (
                    current_time
                    - last_cleanup
                    >= cleanup_interval
                ):
                    if use_event_system:
                        cleanup_expired_events(
                            db, active_event_ids
                        )
                        evicted_group_locks = (
                            _evict_unused_group_locks(
                                group_locks,
                                group_locks_lock,
                                active_group_ids,
                            )
                        )
                    # Purge stale groups whose
                    # player went offline (runs
                    # regardless of UseEventSystem)
                    cleanup_stale_groups(db)
                    last_cleanup = current_time

                # DB state snapshot for log viewer
                if (
                    current_time
                    - last_db_snapshot
                    >= db_snapshot_interval
                ):
                    _write_db_snapshot(
                        db, snapshot_dir
                    )
                    last_db_snapshot = current_time

                # Legacy requests (General ambient chatter)
                # Runs freely every cycle — no deferral
                if players_online and not legacy_future:
                    legacy_future = (
                        executor.submit(
                            _run_in_worker,
                            "legacy-requests",
                            process_pending_requests,
                            client, config
                        )
                    )

                # Fetch + dispatch events
                dispatched = 0
                if use_event_system and players_online:
                    available = (
                        max_concurrent
                        - len(active_futures)
                    )
                    if available > 0:
                        events = (
                            fetch_pending_events(
                                db, config,
                                available
                            )
                        )
                        for event in events:
                            gid = event.get(
                                '_group_id'
                            )
                            if gid:
                                glock = _get_group_lock(
                                    group_locks,
                                    group_locks_lock,
                                    gid,
                                    priority_banded=(
                                        priority_bridge_yield
                                    ),
                                    urgent=_event_is_urgent(
                                        event,
                                        urgent_floor
                                    ),
                                )
                                future = (
                                    executor
                                    .submit(
                                        _run_with_group_lock,
                                        glock,
                                        process_single_event,
                                        event,
                                        client,
                                        config
                                    )
                                )
                            else:
                                future = (
                                    executor
                                    .submit(
                                        process_single_event,
                                        event,
                                        client,
                                        config
                                    )
                                )
                            future.event_id = (
                                event['id']
                            )
                            future.group_id = gid
                            active_event_ids.add(
                                event['id']
                            )
                            active_futures.append(
                                future
                            )
                            dispatched += 1

                # Idle chatter -> worker pool
                if (
                    players_online
                    and use_event_system
                    and not idle_chatter_future
                    and current_time
                    - last_idle_check
                    >= idle_check_interval
                ):
                    last_idle_check = current_time
                    idle_chatter_future = (
                        executor.submit(
                            _run_in_worker,
                            "idle-chatter",
                            check_idle_group_chatter,
                            client, config
                        )
                    )

                # Bot questions -> worker pool
                if (
                    players_online
                    and use_event_system
                    and not bot_question_future
                    and current_time
                    - last_question_check
                    >= question_check_interval
                ):
                    last_question_check = current_time
                    bot_question_future = (
                        executor.submit(
                            _run_in_worker,
                            "bot-question",
                            check_bot_questions,
                            client, config
                        )
                    )

                # Pre-cache -> worker pool
                if (
                    players_online
                    and precache_enabled
                    and not precache_future
                    and current_time
                    - last_cache_refill
                    >= cache_refill_interval
                ):
                    last_cache_refill = current_time
                    precache_future = (
                            executor.submit(
                                _run_in_worker,
                                "pre-cache",
                                refill_precache_pool,
                                client, config
                            )
                        )

            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass

            # Fast poll so player messages are
            # picked up quickly. Background tasks
            # self-rate-limit via their own
            # last_X / interval checks.
            time.sleep(0.2)

        except KeyboardInterrupt:
            executor.shutdown(wait=False)
            # Drain memory executor
            try:
                from chatter_memory import (
                    memory_executor,
                )
                memory_executor.shutdown(wait=True)
            except Exception:
                logger.error(
                    "Memory executor shutdown failed",
                    exc_info=True,
                )
            break
        except Exception:
            logger.error(
                "Main loop iteration failed",
                exc_info=True,
            )
            time.sleep(poll_interval)


if __name__ == '__main__':
    main()
