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
from typing import Dict, List, Optional

from chatter_db import get_db_connection
from chatter_llm import call_llm
from chatter_text import cleanup_message

logger = logging.getLogger(__name__)


def _log_memory_event(entry: dict) -> None:
    """Log a memory event to the request logger.

    Lazy import to avoid circular dependencies.
    No-op if the logger is not available or disabled.
    """
    try:
        from chatter_request_logger import log_request
    except ImportError:
        return
    log_request(
        label=entry.get('label', 'memory_event'),
        prompt='',
        response=None,
        model='',
        provider='',
        duration_ms=0,
        metadata=entry,
    )

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


# ============================================================
# QUEUE MEMORY
# ============================================================

def queue_memory(
    config, group_id, bot_guid, player_guid,
    memory_type, event_context,
    bot_name="", bot_class="", bot_race="",
):
    """Validate eligibility and submit a memory
    generation task to the background executor.

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
        session_start=session_start,
        insert_active=False,
    )


# ============================================================
# MEMORY GENERATION (runs in background thread)
# ============================================================

def _execute_generate_memory(
    config, group_id, bot_guid, player_guid,
    memory_type, event_context,
    bot_name="", bot_class="", bot_race="",
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
            conn, config,
            bot_name=bot_name,
            bot_class=bot_class,
            bot_race=bot_race,
            memory_type=memory_type,
            event_context=event_context,
            mood=mood,
            style=style,
        )

        if not memory_text:
            return

        max_per = int(config.get(
            'LLMChatter.Memory.MaxPerBotPlayer', 50
        ))

        if not insert_active:
            # Re-check under per-group lock
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
                # INSERT while holding lock
                cursor = conn.cursor()
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
                        0, session_start,
                    ),
                )
                conn.commit()
                _log_memory_event({
                    'label': 'memory_generated',
                    'bot_name': bot_name,
                    'bot_guid': bot_guid,
                    'player_guid': player_guid,
                    'group_id': group_id,
                    'memory_type': memory_type,
                    'memory': memory_text,
                    'emote': emote or '',
                    'mood': mood,
                    'active': 0,
                })
        else:
            # party_member: insert as active=1
            cursor = conn.cursor()
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
                    1, session_start,
                ),
            )
            conn.commit()
            _log_memory_event({
                'label': 'memory_generated',
                'bot_name': bot_name,
                'bot_guid': bot_guid,
                'player_guid': player_guid,
                'group_id': group_id,
                'memory_type': memory_type,
                'memory': memory_text,
                'emote': emote or '',
                'mood': mood,
                'active': 1,
            })

            # Self-prune to MaxPerBotPlayer.
            # flush_session_memories also prunes
            # for the departing bot — both paths
            # prune to the same cap so concurrent
            # pruning is idempotent (no data loss,
            # only redundant deletes of the oldest)
            cursor.execute(
                "SELECT COUNT(*) AS cnt"
                " FROM llm_bot_memories"
                " WHERE bot_guid = %s"
                "   AND player_guid = %s"
                "   AND active = 1",
                (bot_guid, player_guid),
            )
            row = cursor.fetchone()
            cnt = row[0] if row else 0
            excess = max(0, cnt - max_per)
            if excess > 0:
                cursor.execute(
                    "DELETE FROM llm_bot_memories"
                    " WHERE bot_guid = %s"
                    "   AND player_guid = %s"
                    "   AND active = 1"
                    " ORDER BY created_at ASC"
                    " LIMIT %s",
                    (bot_guid, player_guid, excess),
                )
                conn.commit()

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
    db, config,
    bot_name="", bot_class="", bot_race="",
    memory_type="ambient", event_context="",
    mood="contemplative", style="sincere",
):
    """Call LLM to generate a memory entry.

    Returns (memory_text, emote) or (None, None).
    """
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()
    if provider == 'ollama':
        try:
            import openai as _openai
        except ImportError:
            logger.error(
                "openai package required for "
                "ollama provider"
            )
            return None, None
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://localhost:11434'
        )
        client = _openai.OpenAI(
            base_url=f"{base_url.rstrip('/')}/v1",
            api_key="ollama",
        )
    elif provider == 'openai':
        try:
            import openai as _openai
        except ImportError:
            logger.error(
                "openai package required for "
                "openai provider"
            )
            return None, None
        client = _openai.OpenAI(
            api_key=config.get(
                'LLMChatter.OpenAI.ApiKey', ''
            ),
        )
    else:
        try:
            import anthropic as _anthropic
        except ImportError:
            logger.error(
                "anthropic package required for "
                "anthropic provider"
            )
            return None, None
        client = _anthropic.Anthropic(
            api_key=config.get(
                'LLMChatter.Anthropic.ApiKey', ''
            ),
        )

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
    }.get(memory_type, "a shared moment")

    prompt = (
        f"You are {bot_name}, a {bot_race} "
        f"{bot_class} in World of Warcraft.\n\n"
        f"Context: {type_desc}\n"
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
        'LLMChatter.Memory.MaxPerBotPlayer', 50
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
            for target_guid in all_bots_snapshot:
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
                _log_memory_event({
                    'label': 'memory_activated',
                    'bot_guid': bot_guid,
                    'player_guid': player_guid,
                    'group_id': group_id,
                    'session_start': session_start,
                    'rows_activated': rows_activated,
                })

            # Prune to cap
            cursor.execute(
                "SELECT COUNT(*) AS cnt"
                " FROM llm_bot_memories"
                " WHERE bot_guid = %s"
                "   AND player_guid = %s"
                "   AND active = 1",
                (bot_guid, player_guid),
            )
            row = cursor.fetchone()
            cnt = row[0] if row else 0
            excess = max(0, cnt - max_per)
            if excess > 0:
                cursor.execute(
                    "DELETE FROM llm_bot_memories"
                    " WHERE bot_guid = %s"
                    "   AND player_guid = %s"
                    "   AND active = 1"
                    "   AND memory_type"
                    "     != 'first_meeting'"
                    " ORDER BY created_at ASC"
                    " LIMIT %s",
                    (
                        bot_guid, player_guid,
                        excess,
                    ),
                )
                db.commit()
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
                _log_memory_event({
                    'label': 'memory_discarded',
                    'bot_guid': bot_guid,
                    'group_id': group_id,
                    'session_start': session_start,
                    'rows_discarded': rows_discarded,
                    'reason': 'session_too_short',
                })
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
):
    """Retrieve random active memories for a
    bot-player pair.

    Returns list of memory strings (may be empty).
    """
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT memory FROM llm_bot_memories"
            " WHERE bot_guid = %s"
            "   AND player_guid = %s"
            "   AND active = 1"
            " ORDER BY RAND()"
            " LIMIT %s",
            (bot_guid, player_guid, count),
        )
        return [
            row['memory'] for row in cursor.fetchall()
        ]
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
