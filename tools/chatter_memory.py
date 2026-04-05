"""Bot persistent memory system.

Owns:
- Session tracking (which bots are grouped with
  which player)
- Background memory generation via dedicated
  ThreadPoolExecutor
- Memory flush on farewell (activate or discard)
- Orphan recovery and session rehydration on
  bridge restart
- Memory retrieval for reunion greetings
"""

import json
import logging
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

from chatter_db import (
    get_db_connection, get_group_location,
)
from chatter_shared import (
    get_zone_name, get_dungeon_flavor,
    format_location_label,
)
from chatter_llm import call_llm, get_llm_client

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

MEMORY_MOODS = {
    'ambient': [
        'curious', 'nostalgic', 'wistful',
        'playful', 'contemplative',
    ],
    'boss_kill': [
        'triumphant', 'exhilarated', 'proud',
        'breathless', 'relieved',
    ],
    'wipe': [
        'grimly_amused', 'humbled', 'resilient',
        'rueful', 'determined',
    ],
    'rare_kill': [
        'delighted', 'surprised', 'pleased',
        'excited', 'satisfied',
    ],
    'dungeon': [
        'adventurous', 'focused', 'alert',
        'eager', 'cautious',
    ],
    'party_member': [
        'warm', 'fond', 'grateful',
        'affectionate', 'respectful',
    ],
    'player_message': [
        'thoughtful', 'engaged', 'amused',
        'intrigued', 'moved',
    ],
    'quest_complete': [
        'proud', 'satisfied', 'relieved',
        'accomplished', 'glad',
    ],
    'achievement': [
        'proud', 'excited', 'delighted',
        'impressed', 'cheerful',
    ],
    'level_up': [
        'proud', 'elated', 'inspired',
        'jubilant', 'nostalgic',
    ],
    'bg_win': [
        'triumphant', 'exhilarated', 'proud',
        'victorious', 'gleeful',
    ],
    'bg_loss': [
        'rueful', 'determined', 'humbled',
        'stoic', 'resilient',
    ],
    'discovery': [
        'awed', 'curious', 'wistful',
        'adventurous', 'reflective',
    ],
    'pvp_kill': [
        'fierce', 'satisfied', 'exhilarated',
        'proud', 'ruthless',
    ],
}

MEMORY_EXPRESSION_STYLES = [
    'poetic', 'understated', 'vivid',
    'wry', 'sincere',
]

# ============================================================
# BACKGROUND EXECUTOR
# ============================================================

memory_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="memory",
)

# ============================================================
# THREAD-SAFE SESSION TRACKER
# ============================================================

_active_sessions: Dict[int, dict] = {}
# {group_id: {
#   "start": float,        # set ONCE at first bot
#   "player_guid": int,
#   "bots": set(),         # bot_guids still in session
#   "members": dict,       # {guid: {name, class, race}}
#   "msg_count": int,      # player_message count
#   "party_memories_generated": bool,
# }}

_group_locks: Dict[int, threading.Lock] = {}
_group_locks_meta = threading.Lock()


def _get_group_lock(
    group_id: int, create: bool = True
) -> Optional[threading.Lock]:
    """Get the per-group lock for session operations.

    create=False returns None if no lock exists
    (session already cleaned up).
    """
    with _group_locks_meta:
        if group_id not in _group_locks:
            if not create:
                return None
            _group_locks[group_id] = threading.Lock()
        return _group_locks[group_id]


# ============================================================
# SESSION MANAGEMENT
# ============================================================

def start_session(
    group_id, bot_guid, player_guid,
    session_start, members,
):
    """Register a bot in the active session tracker.

    First bot in a group initializes the session with
    session_start timestamp. Late joiners inherit the
    existing clock.

    Args:
        group_id: group identifier
        bot_guid: bot character guid
        player_guid: real player guid
        session_start: time.time() float
        members: dict {guid: {name, class, race}}
    """
    lock = _get_group_lock(group_id)
    with lock:
        if group_id not in _active_sessions:
            _active_sessions[group_id] = {
                "start": session_start,
                "player_guid": player_guid,
                "bots": set(),
                "members": members or {},
                "msg_count": 0,
                "party_memories_generated": False,
            }
        _active_sessions[group_id]["bots"].add(
            bot_guid
        )
        # Merge new member data for late joiners
        if members:
            _active_sessions[group_id][
                "members"
            ].update(members)


def teardown_group_session(group_id):
    """Clear in-memory session state for one group.

    Called by cleanup_stale_groups() when a single
    group's player goes offline while others remain.
    """
    with _group_locks_meta:
        _active_sessions.pop(group_id, None)
        _group_locks.pop(group_id, None)


def clear_all_sessions():
    """Clear all in-memory session state.

    Called when all players go offline to prevent
    stale _active_sessions from surviving a full
    DB wipe.
    """
    with _group_locks_meta:
        _active_sessions.clear()
        _group_locks.clear()


# ============================================================
# QUEUE MEMORY
# ============================================================

def queue_memory(
    config, group_id, bot_guid, player_guid,
    memory_type, event_context,
    bot_name="", bot_class="", bot_race="",
    db=None,
):
    """Validate eligibility and submit a memory
    generation task to the background executor.

    Location is resolved here at queue time from
    get_group_location() while traits still exist.

    Args:
        config: bridge config dict
        group_id: group identifier
        bot_guid: bot character guid
        player_guid: real player guid
        memory_type: one of MEMORY_MOODS keys
        event_context: brief description of the
            moment for the LLM prompt
        bot_name: bot's character name
        bot_class: bot's class name
        bot_race: bot's race name
        db: optional DB connection for location
            lookup (avoids opening a new one)
    """
    if not int(config.get(
        'LLMChatter.Memory.Enable', 1
    )):
        return

    lock = _get_group_lock(group_id, create=False)
    if lock is None:
        return
    with lock:
        session = _active_sessions.get(group_id)
        if not session:
            return
        if bot_guid not in session["bots"]:
            return
        session_start = session["start"]
        p_guid = session["player_guid"]

    # Use the session's player_guid if caller
    # didn't provide one
    if not player_guid:
        player_guid = p_guid

    # Last resort: resolve from group members
    # (handles bridge restart mid-session where
    # session player_guid was lost)
    if not player_guid:
        try:
            from chatter_db import (
                get_real_player_guid_for_group,
            )
            player_guid = (
                get_real_player_guid_for_group(
                    db, group_id
                )
            )
        except Exception:
            logger.error(
                "player_guid DB fallback failed "
                "for group %s", group_id,
                exc_info=True,
            )

    if not player_guid:
        return  # can't create orphaned memory

    # Resolve location NOW while traits exist
    location = _resolve_location(
        db, config, group_id
    )

    memory_executor.submit(
        _execute_generate_memory,
        config=config,
        group_id=group_id,
        bot_guid=bot_guid,
        player_guid=player_guid,
        memory_type=memory_type,
        event_context=event_context,
        bot_name=bot_name,
        bot_class=bot_class,
        bot_race=bot_race,
        location=location,
        session_start=session_start,
        insert_active=False,
    )


# ============================================================
# MEMORY GENERATION (runs in background thread)
# ============================================================

def _resolve_location(db, config, group_id):
    """Resolve player-centric location label.

    Uses get_group_location() for zone/area/map,
    then get_dungeon_flavor() for instances or
    format_location_label() for open world.

    Must be called while llm_group_bot_traits
    rows still exist (before group cleanup).

    Args:
        db: DB connection (None = open one)
        config: bridge config dict
        group_id: group identifier

    Returns a human-readable string like
    "Teldrassil > Dolanaar" or "The Deadmines",
    or empty string on failure.
    """
    own_db = False
    try:
        if db is None:
            db = get_db_connection(config)
            own_db = True
        z, a, m = get_group_location(db, group_id)
        if not z and not m:
            return ""
        # Dungeons/raids: use flavour name
        df = get_dungeon_flavor(m)
        if df:
            return df.split(':')[0]
        # Open world: "Zone > Subzone" or "Zone"
        if z:
            return format_location_label(z, a)
        return ""
    except Exception:
        return ""
    finally:
        if own_db and db:
            try:
                db.close()
            except Exception:
                pass


def _count_active_memories(cursor, bot_guid, player_guid):
    """Count active memories for a bot-player pair."""
    cursor.execute(
        "SELECT COUNT(*) FROM llm_bot_memories"
        " WHERE bot_guid = %s"
        "   AND player_guid = %s"
        "   AND active = 1",
        (bot_guid, player_guid),
    )
    row = cursor.fetchone()
    return row[0] if row else 0


def _evict_one_used(cursor, conn, bot_guid, player_guid):
    """Evict one random used memory.

    Returns True if a row was deleted.
    """
    cursor.execute(
        "DELETE FROM llm_bot_memories"
        " WHERE bot_guid = %s"
        "   AND player_guid = %s"
        "   AND active = 1"
        "   AND used = 1"
        " ORDER BY RAND() LIMIT 1",
        (bot_guid, player_guid),
    )
    conn.commit()
    return cursor.rowcount > 0


def _ensure_cap_and_insert(
    conn, bot_guid, player_guid, group_id,
    memory_type, memory_text, mood, emote,
    session_start, active, max_per,
):
    """Check memory cap, evict if needed, insert.

    Returns True if inserted, False if pool full.
    """
    cursor = conn.cursor()
    cnt = _count_active_memories(
        cursor, bot_guid, player_guid
    )
    if cnt >= max_per:
        if not _evict_one_used(
            cursor, conn, bot_guid, player_guid
        ):
            logger.debug(
                "Memory pool full, no used"
                " memories to evict for"
                " bot %s", bot_guid,
            )
            return False
    cursor.execute(
        "INSERT INTO llm_bot_memories"
        " (bot_guid, player_guid,"
        "  group_id, memory_type,"
        "  memory, mood, emote,"
        "  active, session_start)"
        " VALUES"
        " (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            bot_guid, player_guid,
            group_id, memory_type,
            memory_text, mood, emote,
            active, session_start,
        ),
    )
    conn.commit()
    return True


def _execute_generate_memory(
    config, group_id, bot_guid, player_guid,
    memory_type, event_context,
    bot_name="", bot_class="", bot_race="",
    location="",
    session_start=0.0, insert_active=False,
):
    """Generate a memory via LLM and insert it.

    For insert_active=False (normal path):
      - Fast bailout before LLM call
      - Re-check + INSERT under per-group lock
    For insert_active=True (party_member at flush):
      - INSERT as active=1, then self-prune
    """
    # Fast bailout before expensive LLM call
    if not insert_active:
        lock = _get_group_lock(
            group_id, create=False
        )
        if lock is None:
            return
        with lock:
            session = _active_sessions.get(group_id)
            if (
                session is None
                or session["start"] != session_start
                or bot_guid not in session["bots"]
            ):
                return

    conn = None
    try:
        conn = get_db_connection(config)

        # Pick mood and expression style
        moods = MEMORY_MOODS.get(
            memory_type,
            ['contemplative'],
        )
        mood = random.choice(moods)
        style = random.choice(
            MEMORY_EXPRESSION_STYLES
        )

        # Generate via LLM
        memory_text, emote = _call_llm_for_memory(
            config,
            bot_name=bot_name,
            bot_class=bot_class,
            bot_race=bot_race,
            memory_type=memory_type,
            event_context=event_context,
            mood=mood,
            style=style,
            location=location,
        )

        if not memory_text:
            return

        max_per = int(config.get(
            'LLMChatter.Memory.MaxPerBotPlayer', 30
        ))

        if not insert_active:
            # Re-check session under per-group lock
            lock = _get_group_lock(
                group_id, create=False
            )
            if lock is None:
                return
            with lock:
                session = _active_sessions.get(
                    group_id
                )
                if (
                    session is None
                    or session["start"]
                        != session_start
                    or bot_guid
                        not in session["bots"]
                ):
                    return
                _ensure_cap_and_insert(
                    conn, bot_guid, player_guid,
                    group_id, memory_type,
                    memory_text, mood, emote,
                    session_start, active=0,
                    max_per=max_per,
                )
        else:
            _ensure_cap_and_insert(
                conn, bot_guid, player_guid,
                group_id, memory_type,
                memory_text, mood, emote,
                session_start, active=1,
                max_per=max_per,
            )

    except Exception:
        logger.error(
            "Memory generation failed for "
            f"bot={bot_guid} group={group_id} "
            f"type={memory_type}",
            exc_info=True,
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _call_llm_for_memory(
    config,
    bot_name="", bot_class="", bot_race="",
    memory_type="ambient", event_context="",
    mood="contemplative", style="sincere",
    location="",
):
    """Call LLM to generate a memory entry.

    Returns (memory_text, emote) or (None, None).
    """
    client = get_llm_client(config)

    type_desc = {
        'ambient': (
            "a quiet moment during travel"
        ),
        'boss_kill': (
            "defeating a powerful enemy together"
        ),
        'wipe': (
            "a total party wipe"
        ),
        'rare_kill': (
            "finding and slaying a rare creature"
        ),
        'dungeon': (
            "entering a dungeon or raid"
        ),
        'party_member': (
            "adventuring alongside a companion"
        ),
        'player_message': (
            "something the player said in chat"
        ),
        'quest_complete': (
            "completing a quest together"
        ),
        'achievement': (
            "earning an achievement"
        ),
        'level_up': (
            "reaching a new level"
        ),
        'bg_win': (
            "winning a battleground"
        ),
        'bg_loss': (
            "losing a battleground"
        ),
        'discovery': (
            "discovering a new area"
        ),
        'pvp_kill': (
            "defeating an enemy player in combat"
        ),
    }.get(memory_type, "a shared moment")

    prompt = (
        f"You are {bot_name}, a {bot_race} "
        f"{bot_class} in World of Warcraft.\n"
    )
    if location:
        prompt += f"Location: {location}\n"
    prompt += (
        f"\nContext: {type_desc}\n"
    )
    if event_context:
        prompt += f"What happened: {event_context}\n"
    prompt += (
        f"Mood: {mood}\n"
        f"Expression style: {style}\n\n"
        f"Write a 1-2 sentence first-person memory "
        f"from your perspective about this moment. "
        f"This is a private journal entry, not "
        f"spoken aloud. Be specific about what "
        f"happened.\n\n"
        f"Respond in JSON:\n"
        f'{{"memory": "your memory text", '
        f'"emote": "one_word_emote"}}\n\n'
        f"Rules:\n"
        f"- Memory must be 1-2 sentences\n"
        f"- First person perspective\n"
        f"- No quotes inside the memory text\n"
        f"- Only reference the location given above"
        f" — never invent or guess a location\n"
        f"- Emote is optional (null if none)\n"
        f"- Just the JSON, nothing else"
    )

    try:
        response = call_llm(
            client, prompt, config,
            max_tokens_override=120,
            context=f"memory:{bot_name}:{memory_type}",
            label='memory_generation',
        )
        if not response:
            return None, None

        # Parse JSON response
        response = response.strip()
        # Try to find JSON object in response
        start = response.find('{')
        end = response.rfind('}')
        if start >= 0 and end > start:
            response = response[start:end + 1]

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            return None, None

        memory = data.get('memory', '')
        if isinstance(memory, str):
            memory = memory.strip()
        else:
            return None, None

        if not memory or len(memory) > 500:
            return None, None

        emote = data.get('emote')
        if isinstance(emote, str):
            emote = emote.strip()[:32] or None
        else:
            emote = None

        return memory, emote

    except Exception:
        logger.error(
            f"LLM memory call failed for "
            f"{bot_name}:{memory_type}",
            exc_info=True,
        )
        return None, None


# ============================================================
# FLUSH SESSION MEMORIES
# ============================================================

def flush_session_memories(
    db, group_id, player_guid, bot_guid, config,
):
    """Flush memories for a departing bot.

    Called from process_group_farewell_event.

    Steps:
    1. Under lock: capture session_start, snapshot
       bots for party_member, discard bot
    2. If qualifying: submit party_member for all
    3. UPDATE active=1 for this bot's session rows
    4. Prune to MaxPerBotPlayer cap
    5. If too short: DELETE inactive rows
    6. If last bot: clean up session
    """
    if not int(config.get(
        'LLMChatter.Memory.Enable', 1
    )):
        return

    session_minutes = int(config.get(
        'LLMChatter.Memory.SessionMinutes', 15
    ))
    max_per = int(config.get(
        'LLMChatter.Memory.MaxPerBotPlayer', 30
    ))

    do_commit = False
    do_party = False
    all_bots_snapshot = set()
    members_snapshot = {}
    session_start = 0.0

    lock = _get_group_lock(group_id, create=False)
    if lock is None:
        return

    with lock:
        session = _active_sessions.get(group_id)
        if not session:
            return

        session_start = session["start"]
        elapsed = time.time() - session_start
        do_commit = (
            elapsed >= session_minutes * 60
        )
        do_party = (
            do_commit
            and not session[
                "party_memories_generated"
            ]
        )

        if do_party:
            session[
                "party_memories_generated"
            ] = True
            # Snapshot ALL bots including departing;
            # only generate party_member memories
            # when 2+ bots were present (solo bots
            # cannot reflect on inter-bot bonding)
            all_bots_snapshot = (
                session["bots"] | {bot_guid}
            )
            if len(all_bots_snapshot) < 2:
                do_party = False
                all_bots_snapshot = set()
            members_snapshot = dict(
                session["members"]
            )

        # Remove bot BEFORE UPDATE
        session["bots"].discard(bot_guid)
        last_bot = len(session["bots"]) == 0

        if last_bot:
            del _active_sessions[group_id]
            # Clean up per-group lock entry
            with _group_locks_meta:
                _group_locks.pop(group_id, None)

    if do_commit:
        # Submit party_member memories for all bots
        if do_party:
            party_chance = int(config.get(
                'LLMChatter.Memory'
                '.PartyMemberGenerationChance',
                50
            ))
            flush_loc = _resolve_location(
                db, config, group_id
            )
            for target_guid in all_bots_snapshot:
                if (random.random() * 100
                        >= party_chance):
                    continue
                member = members_snapshot.get(
                    target_guid, {}
                )
                context = (
                    "Reflecting on time spent with "
                    "party companions"
                )
                memory_executor.submit(
                    _execute_generate_memory,
                    config=config,
                    group_id=group_id,
                    bot_guid=target_guid,
                    player_guid=player_guid,
                    memory_type="party_member",
                    event_context=context,
                    bot_name=member.get('name', ''),
                    bot_class=member.get('class', ''),
                    bot_race=member.get('race', ''),
                    location=flush_loc,
                    session_start=session_start,
                    insert_active=True,
                )

        # Activate rows from THIS session
        try:
            cursor = db.cursor()
            cursor.execute(
                "UPDATE llm_bot_memories"
                " SET active = 1"
                " WHERE group_id = %s"
                "   AND bot_guid = %s"
                "   AND active = 0"
                "   AND session_start = %s",
                (group_id, bot_guid, session_start),
            )
            rows_activated = cursor.rowcount
            db.commit()
            if rows_activated > 0:
                logger.debug(
                    "Activated %d memories for"
                    " bot %s / player %s",
                    rows_activated, bot_guid,
                    player_guid,
                )

            # Prune to cap
            cnt = _count_active_memories(
                cursor, bot_guid, player_guid
            )
            while cnt > max_per:
                if not _evict_one_used(
                    cursor, db,
                    bot_guid, player_guid,
                ):
                    break  # no used left
                cnt -= 1
        except Exception:
            logger.error(
                "Memory activation failed for "
                f"bot={bot_guid} group={group_id}",
                exc_info=True,
            )
    else:
        # Session too short: discard inactive rows
        try:
            cursor = db.cursor()
            cursor.execute(
                "DELETE FROM llm_bot_memories"
                " WHERE group_id = %s"
                "   AND bot_guid = %s"
                "   AND active = 0"
                "   AND session_start = %s",
                (group_id, bot_guid, session_start),
            )
            rows_discarded = cursor.rowcount
            db.commit()
            if rows_discarded > 0:
                logger.debug(
                    "Discarded %d memories for"
                    " bot %s (session too short)",
                    rows_discarded, bot_guid,
                )
        except Exception:
            logger.error(
                "Memory discard failed for "
                f"bot={bot_guid} group={group_id}",
                exc_info=True,
            )


# ============================================================
# STARTUP RECOVERY
# ============================================================

def activate_orphaned_memories(
    db, session_minutes,
):
    """Promote orphaned inactive memories from
    sessions that ended without a clean farewell
    (bridge crash, server restart).

    Skips group_ids that still exist in
    llm_group_bot_traits — those are live sessions
    that will be rehydrated and should not be
    touched here.

    Uses UNIX_TIMESTAMP arithmetic since
    session_start is DOUBLE (not TIMESTAMP).
    """
    session_seconds = int(session_minutes) * 60
    try:
        cursor = db.cursor(dictionary=True)
        # Identify live groups — skip them so we
        # don't prematurely promote or discard rows
        # belonging to sessions still in progress
        cursor.execute(
            "SELECT DISTINCT group_id"
            " FROM llm_group_bot_traits"
        )
        live_groups = {
            int(r['group_id'])
            for r in cursor.fetchall()
        }

        # Find truly dead groups with inactive rows
        cursor.execute("""
            SELECT group_id, bot_guid, player_guid,
                MIN(session_start) AS min_start,
                UNIX_TIMESTAMP(MAX(created_at))
                    AS max_created
            FROM llm_bot_memories
            WHERE active = 0
            GROUP BY group_id, bot_guid, player_guid
        """)
        rows = cursor.fetchall()
        promoted = 0
        discarded = 0
        for row in rows:
            g_id = int(row['group_id'])
            # Skip live sessions — rehydration
            # will handle their pending rows
            if g_id in live_groups:
                continue
            b_guid = int(row['bot_guid'])
            p_guid = int(row['player_guid'])
            min_start = float(
                row['min_start'] or 0
            )
            max_created = float(
                row['max_created'] or 0
            )
            elapsed = max_created - min_start
            if elapsed >= session_seconds:
                cursor.execute(
                    "UPDATE llm_bot_memories"
                    " SET active = 1"
                    " WHERE group_id = %s"
                    "   AND bot_guid = %s"
                    "   AND player_guid = %s"
                    "   AND active = 0",
                    (g_id, b_guid, p_guid),
                )
                promoted += cursor.rowcount
            else:
                cursor.execute(
                    "DELETE FROM llm_bot_memories"
                    " WHERE group_id = %s"
                    "   AND bot_guid = %s"
                    "   AND player_guid = %s"
                    "   AND active = 0",
                    (g_id, b_guid, p_guid),
                )
                discarded += cursor.rowcount
        db.commit()
        if promoted or discarded:
            logger.info(
                f"Orphaned memories: promoted="
                f"{promoted}, discarded={discarded}"
            )
    except Exception:
        logger.error(
            "Orphan memory recovery failed",
            exc_info=True,
        )


def rehydrate_active_sessions(db):
    """Rebuild _active_sessions from live groups
    after a bridge restart.

    No lock needed: runs synchronously at startup
    before event loop and background executor.
    """
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT group_id, bot_guid
            FROM llm_group_bot_traits
        """)
        rows = cursor.fetchall()
        if not rows:
            return

        for row in rows:
            g_id = int(row['group_id'])
            b_guid = int(row['bot_guid'])
            if g_id not in _active_sessions:
                _active_sessions[g_id] = {
                    "start": time.time(),
                    "player_guid": 0,
                    "bots": set(),
                    "members": {},
                    "msg_count": 0,
                    "party_memories_generated": True,
                }
                # Create the per-group lock so that
                # queue_memory() and flush_session_memories()
                # (which use create=False) can find it
                # immediately after restart
                _get_group_lock(g_id, create=True)
            _active_sessions[g_id]["bots"].add(
                b_guid
            )

        if _active_sessions:
            logger.info(
                f"Rehydrated {len(_active_sessions)}"
                f" active sessions"
            )
    except Exception:
        logger.error(
            "Session rehydration failed",
            exc_info=True,
        )


# ============================================================
# MEMORY RETRIEVAL
# ============================================================

def get_bot_memories(
    db, bot_guid, player_guid, count=3,
    exclude_first_meeting=False,
):
    """Retrieve random active memories for a
    bot-player pair.

    Returns list of memory strings (may be empty).
    """
    try:
        extra = (
            " AND memory_type != 'first_meeting'"
            if exclude_first_meeting else ""
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, memory"
            " FROM llm_bot_memories"
            " WHERE bot_guid = %s"
            "   AND player_guid = %s"
            "   AND active = 1"
            + extra +
            " ORDER BY RAND()"
            " LIMIT %s",
            (bot_guid, player_guid, count),
        )
        rows = cursor.fetchall()
        if rows:
            ids = [row['id'] for row in rows]
            placeholders = ','.join(
                ['%s'] * len(ids)
            )
            cursor.execute(
                "UPDATE llm_bot_memories"
                " SET used = 1,"
                " last_used_at = NOW()"
                " WHERE id IN (%s)"
                % placeholders,
                tuple(ids),
            )
            db.commit()
        return [row['memory'] for row in rows]
    except Exception:
        logger.error(
            f"Memory retrieval failed for "
            f"bot={bot_guid} player={player_guid}",
            exc_info=True,
        )
        return []


# ============================================================
# SANITIZATION
# ============================================================

def sanitize_memory_for_prompt(memory: str) -> str:
    """Sanitize a memory string for safe inclusion
    in an LLM prompt.

    Strips control characters, normalizes whitespace,
    caps at 200 characters.
    """
    if not memory or not isinstance(memory, str):
        return ""
    # Strip control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', memory)
    # Normalize whitespace
    text = ' '.join(text.split())
    # Cap length
    if len(text) > 200:
        text = text[:197] + "..."
    return text
