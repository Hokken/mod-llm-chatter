"""Bot persistent memory system.

Owns:
- Session tracking (which bots are grouped with
  which player)
- Background memory generation via dedicated
  ThreadPoolExecutor
- Memory flush on farewell (activate or discard)
- Orphan recovery and session rehydration on
  bridge restart
- Memory retrieval and relevance scoring for
  greetings, replies, idle chatter and bot questions
- The shared notes that frame recalled memories
"""

import json
import logging
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional

from chatter_db import (
    get_db_connection, get_group_location,
)
from chatter_shared import (
    get_zone_name, get_dungeon_flavor,
    format_location_label,
    build_bot_identity,
    get_chatter_mode,
)
from chatter_llm import call_llm, get_llm_client
from chatter_member_gender import (
    get_character_genders,
    get_genders_by_guid,
)
from chatter_structured import ResponseContract

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
    'pvp_kill': [
        'fierce', 'satisfied', 'exhilarated',
        'proud', 'ruthless',
    ],
    'discovery': [
        'awed', 'curious', 'wistful',
        'adventurous', 'reflective',
    ],
    'duel': [
        'playful', 'competitive', 'good_humoured',
        'determined', 'respectful',
    ],
}

MEMORY_EXPRESSION_STYLES = [
    'plain', 'understated', 'matter_of_fact',
    'wry', 'observational',
]

MEMORY_TARGET_CHARS = 250
MEMORY_HARD_CHARS = 400

# How much a memory type weighs in recall scoring: shared
# milestones over passing moments.
MEMORY_TYPE_WEIGHTS = {
    'boss_kill': 3.0, 'dungeon': 2.5, 'wipe': 2.5,
    'rare_kill': 2.0, 'quest_complete': 2.0,
    'achievement': 2.0, 'bg_win': 2.0, 'bg_loss': 2.0,
    'pvp_kill': 1.5, 'level_up': 1.5,
    'discovery': 2.0, 'duel': 1.5,
    'player_message': 1.5, 'party_member': 1.5,
    'first_meeting': 1.0, 'ambient': 1.0,
}

# A memory shown in a prompt this recently is held back, so
# the same few do not come back in a row.
RECENTLY_SHOWN_SECONDS = 30 * 60

# Achievements that only count or mark a level ("Level 30",
# "50 Quests Completed", "100 Mounts") carry a number and no
# deed; in roleplay they are skipped before the LLM call.
_MILESTONE_ACHIEVEMENT = re.compile(r'\d')


def is_milestone_achievement(name: str) -> bool:
    """True for achievements that only count or mark a
    level, with no deed behind them."""
    return bool(_MILESTONE_ACHIEVEMENT.search(str(name or '')))


def memory_age_label(created_at, now=None) -> str:
    """How long ago a memory was made, in plain words, so
    recall never presents an old moment as new."""
    if not isinstance(created_at, datetime):
        return ''
    now = now or datetime.now()
    seconds = max(0.0, (now - created_at).total_seconds())
    hours = seconds / 3600
    days = hours / 24
    if hours < 1:
        return 'less than an hour ago'
    if hours < 24:
        return 'earlier today'
    if days < 2:
        return 'yesterday'
    if days < 7:
        return 'a few days ago'
    if days < 14:
        return 'about a week ago'
    if days < 30:
        return 'a few weeks ago'
    if days < 60:
        return 'about a month ago'
    if days < 365:
        return 'a few months ago'
    return 'over a year ago'


def pick_event_bots(config, bots):
    """At most LLMChatter.Memory.MaxBotsPerEvent bots write
    a memory of one group event (boss, rare, achievement),
    so a party does not store five copies of it."""
    try:
        limit = int(config.get(
            'LLMChatter.Memory.MaxBotsPerEvent', 2))
    except (TypeError, ValueError):
        limit = 2
    bots = list(bots or [])
    if limit <= 0:
        return []
    if len(bots) <= limit:
        return bots
    return random.sample(bots, limit)


def memory_block_notes(mode) -> str:
    """Notes that frame any block of recalled memories."""
    notes = (
        "The time in brackets is how long ago it happened. "
        "People named in a memory may not be with you now; "
        "never speak as if they are here unless they are.\n"
    )
    if mode != 'roleplay':
        notes += (
            "Treat these as remembered gameplay events. "
            "Paraphrase them as a player and never copy "
            "in-character journal wording.\n"
        )
    return notes


def _clamp_memory_text(text: str) -> str:
    """Trim an over-long memory at a sentence boundary.

    Bounding length here rather than at prompt build
    time lets prompts carry the stored memory whole.
    """
    if len(text) <= MEMORY_HARD_CHARS:
        return text
    head = text[:MEMORY_HARD_CHARS]
    cut = max(
        head.rfind('. '), head.rfind('! '),
        head.rfind('? '),
    )
    if cut > 60:
        return head[:cut + 1]
    # No usable sentence break — fall back to the last
    # word boundary so the memory never ends mid-word.
    word = head.rfind(' ')
    if word > 60:
        head = head[:word]
    return head.rstrip(' ,;:-') + '.'


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
#   "members": dict,       # {guid: {name, class, race, gender}}
#   "msg_count": int,      # player_message count
#   "party_memories_generated": bool,
#   "dungeons": set(),     # (bot_guid, map_id) remembered
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
                "dungeons": set(),
            }
        _active_sessions[group_id]["bots"].add(
            bot_guid
        )
        # Merge new member data for late joiners
        if members:
            _active_sessions[group_id][
                "members"
            ].update(members)


def claim_dungeon_memory(group_id, bot_guid, map_id) -> bool:
    """True the first time this bot may remember entering
    this instance in the current session. Joining inside a
    dungeon and the dungeon-entry event can both fire."""
    lock = _get_group_lock(group_id, create=False)
    if lock is None:
        return False
    with lock:
        session = _active_sessions.get(group_id)
        if not session:
            return False
        key = (int(bot_guid), int(map_id or 0))
        dungeons = session.setdefault("dungeons", set())
        if key in dungeons:
            return False
        dungeons.add(key)
        return True


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
    bot_gender="",
    player_name="",
    db=None,
    background=None,
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
        background: short labelled lines of fact
            (zone and subzone descriptions, what a
            quest-giver said) that keep the memory
            accurate; never events of their own
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

    # Resolve place, persona and companions NOW, while
    # the group's trait rows still exist.
    context = _resolve_memory_context(
        db, config, group_id, bot_guid
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
        bot_gender=bot_gender,
        player_name=player_name,
        context=context,
        background=background,
        session_start=session_start,
        insert_active=False,
    )


# ============================================================
# MEMORY GENERATION (runs in background thread)
# ============================================================

def _location_label(zone_id, area_id, map_id):
    """ "Teldrassil > Dolanaar", "The Deadmines", or ''."""
    dungeon = get_dungeon_flavor(map_id)
    if dungeon:
        return dungeon.split(':')[0]
    if zone_id:
        return format_location_label(zone_id, area_id)
    return ""


def _read_persona(cursor, group_id, bot_guid):
    """The bot's traits, tone and backstory: this session's
    row first, then the persistent identity."""
    cursor.execute(
        "SELECT trait1, trait2, trait3, tone, backstory"
        " FROM llm_group_bot_traits"
        " WHERE group_id = %s AND bot_guid = %s",
        (group_id, bot_guid),
    )
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "SELECT trait1, trait2, trait3, tone, backstory"
            " FROM llm_bot_identities WHERE bot_guid = %s",
            (bot_guid,),
        )
        row = cursor.fetchone()
    if not row:
        return {}
    return {
        'traits': [t for t in (
            row.get('trait1'), row.get('trait2'),
            row.get('trait3'),
        ) if t],
        'tone': row.get('tone') or '',
        'backstory': row.get('backstory') or '',
    }


def _resolve_memory_context(db, config, group_id, bot_guid):
    """Everything a memory prompt needs from the live group,
    resolved at queue time while llm_group_bot_traits rows
    still exist: place, mode, the bot's persona and the
    other bots present.

    Returns a dict; missing parts are empty, never raised.
    """
    context = {
        'location': '', 'zone_id': 0, 'map_id': 0,
        'mode': get_chatter_mode(config or {}),
        'persona': {}, 'companions': [],
    }
    own_db = False
    try:
        if db is None:
            db = get_db_connection(config)
            own_db = True
        z, a, m = get_group_location(db, group_id)
        context['zone_id'] = int(z or 0)
        context['map_id'] = int(m or 0)
        context['location'] = _location_label(z, a, m)
        cursor = db.cursor(dictionary=True)
        context['persona'] = _read_persona(
            cursor, group_id, bot_guid)
        cursor.execute(
            "SELECT bot_name FROM llm_group_bot_traits"
            " WHERE group_id = %s AND bot_guid != %s",
            (group_id, bot_guid),
        )
        context['companions'] = [
            r['bot_name'] for r in cursor.fetchall()
            if r.get('bot_name')
        ]
        cursor.close()
    except Exception:
        logger.debug(
            "memory context lookup failed for group %s",
            group_id, exc_info=True,
        )
    finally:
        if own_db and db:
            try:
                db.close()
            except Exception:
                pass
    return context


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


def _evict_one(cursor, conn, bot_guid, player_guid):
    """Evict the least valuable active memory: a referenced
    one first, the longest unseen first, then the oldest.

    first_meeting rows are never evicted: they are the
    templated "Met X in Zone" anchor of the whole
    remembers-you premise. When only first_meeting rows
    remain, this deletes nothing and returns False.

    Returns True if a row was deleted.
    """
    cursor.execute(
        "DELETE FROM llm_bot_memories"
        " WHERE bot_guid = %s"
        "   AND player_guid = %s"
        "   AND active = 1"
        "   AND memory_type != 'first_meeting'"
        " ORDER BY used DESC,"
        "   COALESCE(last_used_at, created_at) ASC"
        " LIMIT 1",
        (bot_guid, player_guid),
    )
    conn.commit()
    return cursor.rowcount > 0


def _prune_to_cap(cursor, conn, bot_guid, player_guid, max_per):
    """Evict until the pair holds at most max_per active
    memories (first_meeting rows aside)."""
    cnt = _count_active_memories(cursor, bot_guid, player_guid)
    while cnt > max_per:
        if not _evict_one(cursor, conn, bot_guid, player_guid):
            break
        cnt -= 1


def _ensure_cap_and_insert(
    conn, bot_guid, player_guid, group_id,
    memory_type, memory_text, mood, emote,
    session_start, active, max_per, context=None,
):
    """Insert a memory, keeping the pair within its cap on
    every path (pending rows are pruned at activation).

    Returns True if inserted.
    """
    context = context or {}
    cursor = conn.cursor()
    if active:
        _prune_to_cap(
            cursor, conn, bot_guid, player_guid,
            max(0, max_per - 1),
        )
    companions = ', '.join(context.get('companions') or [])
    cursor.execute(
        "INSERT INTO llm_bot_memories"
        " (bot_guid, player_guid,"
        "  group_id, memory_type,"
        "  memory, mood, emote,"
        "  active, session_start,"
        "  zone_id, map_id, companions)"
        " VALUES"
        " (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            bot_guid, player_guid,
            group_id, memory_type,
            memory_text, mood, emote,
            active, session_start,
            context.get('zone_id') or None,
            context.get('map_id') or None,
            companions[:255] or None,
        ),
    )
    conn.commit()
    return True


def _session_alive(group_id, bot_guid, session_start):
    lock = _get_group_lock(group_id, create=False)
    if lock is None:
        return False
    with lock:
        session = _active_sessions.get(group_id)
        return bool(
            session is not None
            and session["start"] == session_start
            and bot_guid in session["bots"]
        )


def _execute_generate_memory(
    config, group_id, bot_guid, player_guid,
    memory_type, event_context,
    bot_name="", bot_class="", bot_race="",
    bot_gender="",
    player_name="",
    context=None,
    background=None,
    session_start=0.0, insert_active=False,
):
    """Generate a memory via LLM and insert it.

    For insert_active=False (normal path):
      - Fast bailout before LLM call
      - Re-check + INSERT under per-group lock
    For insert_active=True (party_member at flush):
      - INSERT as active=1 within the cap
    """
    context = context or {}
    # Fast bailout before expensive LLM call
    if not insert_active and not _session_alive(
            group_id, bot_guid, session_start):
        return

    conn = None
    try:
        conn = get_db_connection(config)

        # Resolve player_name from DB if not
        # provided but player_guid is known
        if not player_name and player_guid:
            try:
                pc = conn.cursor(dictionary=True)
                pc.execute(
                    "SELECT name FROM characters"
                    " WHERE guid = %s",
                    (player_guid,),
                )
                pr = pc.fetchone()
                if pr:
                    player_name = pr['name']
                pc.close()
            except Exception:
                logger.debug(
                    "Could not resolve player_name"
                    " for guid=%s", player_guid,
                )

        # Memories are stored and replayed, so the player's
        # pronouns must be right from the start.
        player_gender = ''
        if player_guid:
            player_gender = get_genders_by_guid(
                conn, [player_guid]
            ).get(int(player_guid), '')
        elif player_name:
            player_gender = get_character_genders(
                conn, [player_name]
            ).get(player_name, '')

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
            bot_gender=bot_gender,
            player_name=player_name,
            player_gender=player_gender,
            memory_type=memory_type,
            event_context=event_context,
            mood=mood,
            style=style,
            location=context.get('location', ''),
            mode=context.get('mode', 'normal'),
            persona=context.get('persona'),
            companions=context.get('companions'),
            background=background,
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
                    max_per=max_per, context=context,
                )
        else:
            _ensure_cap_and_insert(
                conn, bot_guid, player_guid,
                group_id, memory_type,
                memory_text, mood, emote,
                session_start, active=1,
                max_per=max_per, context=context,
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


_MEMORY_TYPE_DESC = {
    'ambient': "a quiet moment during travel",
    'boss_kill': "defeating a powerful enemy together",
    'wipe': "the whole party falling in battle",
    'rare_kill': "finding and slaying a rare creature",
    'dungeon': "entering a dungeon or raid",
    'party_member': "adventuring alongside companions",
    'player_message': "something the player told you",
    'quest_complete': "finishing a task together",
    'achievement': "a notable deed",
    'level_up': "growing noticeably stronger",
    'bg_win': "winning a battle",
    'bg_loss': "losing a battle",
    'pvp_kill': "defeating an enemy in combat",
    'discovery': "discovering a new place together",
    'duel': "a friendly training spar",
}

# Short background excerpt: enough to keep the memory true
# to the character without spending the whole backstory.
_BACKSTORY_EXCERPT_CHARS = 300


def _backstory_excerpt(backstory: str) -> str:
    text = ' '.join(str(backstory or '').split())
    if len(text) <= _BACKSTORY_EXCERPT_CHARS:
        return text
    head = text[:_BACKSTORY_EXCERPT_CHARS]
    cut = max(head.rfind('. '), head.rfind('! '), head.rfind('? '))
    return head[:cut + 1] if cut > 80 else head.rsplit(' ', 1)[0] + '...'


def build_memory_prompt(
    bot_name="", bot_class="", bot_race="",
    bot_gender="",
    player_name="", player_gender="",
    memory_type="ambient", event_context="",
    mood="contemplative", style="plain",
    location="", mode="normal",
    persona=None, companions=None,
    background=None,
):
    """The memory-writing prompt: facts only, in the bot's
    voice and the chat mode's register.

    background: labelled lines of fact (place descriptions,
    a quest-giver's words) that keep the memory accurate;
    "What happened" stays the only source of events."""
    is_rp = mode == 'roleplay'
    persona = persona or {}
    companions = [c for c in (companions or []) if c]
    type_desc = _MEMORY_TYPE_DESC.get(memory_type, "a shared moment")

    identity = build_bot_identity(
        bot_name, bot_race, bot_class, bot_gender,
        suffix=' in World of Warcraft.',
    )
    prompt = f"{identity}\n"
    if persona.get('traits'):
        prompt += f"Your personality: {', '.join(persona['traits'])}\n"
    if persona.get('tone'):
        prompt += f"Your voice: {persona['tone']}\n"
    if is_rp and persona.get('backstory'):
        prompt += (
            "Your background (never contradict it): "
            f"{_backstory_excerpt(persona['backstory'])}\n"
        )
    if player_name:
        gender_note = (
            f" ({player_gender})" if player_gender else ""
        )
        prompt += (
            f"Player companion: {player_name}{gender_note}\n"
        )
    if companions:
        prompt += f"Also in the party: {', '.join(companions)}\n"
    if location:
        prompt += f"Location: {location}\n"
    prompt += f"\nContext: {type_desc}\n"
    if event_context:
        prompt += f"What happened: {event_context}\n"
    background = [b for b in (background or []) if b]
    if background:
        prompt += (
            "Background (facts to keep the memory accurate; "
            "not events that happened now):\n"
            + ''.join(f"- {b}\n" for b in background)
        )
    prompt += (
        f"Underlying feeling, keep it subtle: {mood}\n"
        f"Register: {style}\n\n"
    )
    if is_rp:
        prompt += (
            "Write a first-person note of one or two sentences "
            "recording this moment, in your own in-world voice. "
            "This is a private log entry, not spoken aloud, not "
            "a story.\n\n"
        )
    else:
        prompt += (
            "Write a first-person note of one or two sentences "
            "recording this moment, as a player keeping a log "
            "of the session. Not spoken aloud, not a story.\n\n"
        )
    prompt += (
        "Respond in JSON:\n"
        '{"memory": "your memory text", '
        '"emote": "one_word_emote"}\n\n'
        "Rules:\n"
        f"- One or two sentences, about {MEMORY_TARGET_CHARS} "
        "characters\n"
        "- Record only what \"What happened\" states; add no "
        "incidents, conversations or details of your own\n"
        "- Background facts may shape your wording, but never "
        "retell them as something that happened now\n"
        "- Never describe the player's feelings, motives, words "
        "or actions beyond what is given\n"
        "- No outcomes or decisions that are not stated\n"
        "- If others took part, name them or say \"the party\"; "
        "never make it sound like only you and the player were "
        "there\n"
        "- Never contradict your background; invent no "
        "childhood, family or past events\n"
        "- Never write today, yesterday, just now or other words "
        "tied to when you write it\n"
        "- Plain concrete language; no metaphors or flowery "
        "wording\n"
        "- At most a short clause about how you felt\n"
        "- First person perspective\n"
        "- No quotes inside the memory text\n"
        "- Only reference the location given above; never "
        "invent or guess a location\n"
        "- Emote is optional (null if none)\n"
        "- If there is nothing true to record, return an empty "
        "memory (\"\")\n"
    )
    if is_rp:
        prompt += (
            "- Stay in the world: never mention levels, "
            "achievements, quests, experience, loot rarity or "
            "anything from the game interface; describe the deed "
            "itself, or return an empty memory if you cannot\n"
        )
    if player_name:
        prompt += (
            f"- When the memory involves the player,"
            f" refer to them by name"
            f" ({player_name}); never use generic"
            f" terms like 'a traveler' or 'someone'"
            f" or 'a stranger'\n"
        )
    prompt += "- Just the JSON, nothing else"

    # Plain-string prompt path, not routed through
    # append_json_instruction, so inject the language
    # rule directly.
    from chatter_shared import get_language_rule
    lang_rule = get_language_rule()
    if lang_rule:
        prompt += lang_rule
    return prompt


def _call_llm_for_memory(
    config,
    bot_name="", bot_class="", bot_race="",
    bot_gender="",
    player_name="",
    memory_type="ambient", event_context="",
    player_gender="",
    mood="contemplative", style="plain",
    location="", mode="normal",
    persona=None, companions=None,
    background=None,
):
    """Call LLM to generate a memory entry.

    Returns (memory_text, emote) or (None, None); an empty
    memory means the model found nothing true to record.
    """
    client = get_llm_client(config)
    prompt = build_memory_prompt(
        bot_name=bot_name, bot_class=bot_class,
        bot_race=bot_race, bot_gender=bot_gender,
        player_name=player_name,
        player_gender=player_gender,
        memory_type=memory_type,
        event_context=event_context,
        mood=mood, style=style, location=location,
        mode=mode, persona=persona, companions=companions,
        background=background,
    )

    try:
        response = call_llm(
            client, prompt, config,
            max_tokens_override=200,
            context=f"memory:{bot_name}:{memory_type}",
            label='memory_generation',
            response_contract=ResponseContract('memory'),
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

        memory = _clamp_memory_text(memory)

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
        'LLMChatter.Memory.SessionMinutes', 3
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
            minutes = max(1, int(elapsed // 60))
            names = {
                guid: members_snapshot.get(guid, {}).get('name', '')
                for guid in all_bots_snapshot
            }
            for target_guid in all_bots_snapshot:
                if (random.random() * 100
                        >= party_chance):
                    continue
                member = members_snapshot.get(
                    target_guid, {}
                )
                mem_context = _resolve_memory_context(
                    db, config, group_id, target_guid
                )
                mem_context['companions'] = [
                    n for g, n in names.items()
                    if n and g != target_guid
                ]
                context = (
                    f"Spent about {minutes} minutes adventuring "
                    "together as a party"
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
                    bot_gender=member.get(
                        'gender', ''
                    ),
                    context=mem_context,
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

            _prune_to_cap(
                cursor, db, bot_guid, player_guid, max_per,
            )
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
    db, session_minutes, max_per=30,
):
    """Promote orphaned inactive memories from
    sessions that ended without a clean farewell
    (bridge crash, server restart, player logout).
    Runs at startup and on every bridge cleanup tick.

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
                _prune_to_cap(
                    db.cursor(), db, b_guid, p_guid,
                    int(max_per),
                )
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

    The session clock resumes from the group's pending
    memories (or its trait rows), so rows written before
    the restart still activate at farewell. The player and
    the members are resolved again, so player messages and
    party memories keep working.

    No lock needed: runs synchronously at startup
    before event loop and background executor.
    """
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.group_id, t.bot_guid, t.bot_name,
                UNIX_TIMESTAMP(t.assigned_at) AS assigned,
                c.class, c.race, c.gender
            FROM llm_group_bot_traits t
            LEFT JOIN characters c ON c.guid = t.bot_guid
        """)
        rows = cursor.fetchall()
        if not rows:
            return

        from chatter_db import get_real_player_guid_for_group
        from chatter_shared import (
            get_class_name, get_race_name, get_gender_label,
        )

        groups = {}
        for row in rows:
            groups.setdefault(int(row['group_id']), []).append(row)

        for g_id, bots in groups.items():
            cursor.execute(
                "SELECT MIN(session_start) AS start"
                " FROM llm_bot_memories"
                " WHERE group_id = %s AND active = 0",
                (g_id,),
            )
            pending = cursor.fetchone() or {}
            assigned = [
                float(b['assigned']) for b in bots
                if b.get('assigned')
            ]
            start = (
                float(pending['start'])
                if pending.get('start')
                else (min(assigned) if assigned else time.time())
            )
            player_guid = get_real_player_guid_for_group(db, g_id)
            members = {}
            for b in bots:
                members[int(b['bot_guid'])] = {
                    'name': b.get('bot_name') or '',
                    'class': get_class_name(b['class'])
                    if b.get('class') is not None else '',
                    'race': get_race_name(b['race'])
                    if b.get('race') is not None else '',
                    'gender': get_gender_label(b.get('gender') or 0),
                }
            _active_sessions[g_id] = {
                "start": start,
                "player_guid": int(player_guid or 0),
                "bots": set(members),
                "members": members,
                "msg_count": 0,
                "party_memories_generated": not player_guid,
                "dungeons": set(),
            }
            # Create the per-group lock so that
            # queue_memory() and flush_session_memories()
            # (which use create=False) can find it
            # immediately after restart
            _get_group_lock(g_id, create=True)

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


def insert_first_meeting(
    db, bot_guid, player_guid, group_id, player_name,
    zone_id=0, map_id=0,
):
    """Write the templated first_meeting memory once per
    bot-player pair, with where it happened. It is active
    at once and never pruned or discarded."""
    zone_name = get_zone_name(zone_id) if zone_id else None
    where = f" in {zone_name}" if zone_name else ""
    text = f"Met {player_name} and began adventuring together{where}."
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO llm_bot_memories"
            " (bot_guid, player_guid, group_id, memory_type,"
            "  memory, mood, emote, active, session_start,"
            "  zone_id, map_id)"
            " SELECT %s,%s,%s,'first_meeting',%s,'warm',NULL,1,%s,"
            "  %s,%s"
            " WHERE NOT EXISTS ("
            "  SELECT 1 FROM llm_bot_memories"
            "  WHERE bot_guid=%s AND player_guid=%s"
            "    AND memory_type='first_meeting')",
            (
                bot_guid, player_guid, group_id, text, time.time(),
                zone_id or None, map_id or None,
                bot_guid, player_guid,
            ),
        )
        db.commit()
    finally:
        cursor.close()


def reset_bot_memories(db, bot_guid) -> int:
    """Delete a bot's memories except first_meeting, for
    LLMChatter.Memory.ResetOnIdentityChange: a bot with a
    new personality should not keep a journal written in
    its old voice. Returns the number of rows deleted."""
    cursor = db.cursor()
    try:
        cursor.execute(
            "DELETE FROM llm_bot_memories"
            " WHERE bot_guid = %s"
            "   AND memory_type != 'first_meeting'",
            (bot_guid,),
        )
        deleted = cursor.rowcount
        db.commit()
        return deleted
    finally:
        cursor.close()


# ============================================================
# MEMORY RETRIEVAL
# ============================================================

def memory_recall_count(config, idle=False):
    """How many memories one prompt retrieves.

    LLMChatter.Memory.RecallCount covers greetings, replies to the
    player and bot questions; IdleRecallCount covers idle chatter.
    Clamped to 1-10.
    """
    key, default = (
        ('LLMChatter.Memory.IdleRecallCount', 2) if idle
        else ('LLMChatter.Memory.RecallCount', 3)
    )
    try:
        count = int(config.get(key, default))
    except (TypeError, ValueError):
        count = default
    return max(1, min(10, count))


class RecalledMemory(str):
    """A memory as shown in a prompt ("(about a week ago)
    text"), carrying its row id so a caller that really
    used it can mark it with mark_memories_used()."""

    memory_id = 0


# Short words that say nothing about a topic.
_STOPWORDS = frozenset(
    "that this with have your what were they there about would "
    "from just then them when will been into more some than "
    "only also very over here like well back want need know "
    "going still even much make sure dont cant youre thats "
    "where which while again could should after before".split()
)


def _topic_words(text: str) -> set:
    words = re.findall(r"[^\W\d_]{4,}", str(text or '').lower())
    return {w for w in words if w not in _STOPWORDS}


def _relevant(row, zone_id, map_id, words) -> bool:
    """A memory fits a reply when it happened in the same
    place or shares a topic word with the message."""
    if map_id and row.get('map_id') == map_id and (
            get_dungeon_flavor(map_id)):
        return True
    if zone_id and row.get('zone_id') == zone_id:
        return True
    return bool(words & _topic_words(row.get('memory')))


def _score_memory(row, zone_id, map_id, present, now):
    score = MEMORY_TYPE_WEIGHTS.get(row.get('memory_type'), 1.0)
    if map_id and row.get('map_id') == map_id and (
            get_dungeon_flavor(map_id)):
        score += 2.0
    elif zone_id and row.get('zone_id') == zone_id:
        score += 1.5
    companions = [
        c.strip() for c in str(row.get('companions') or '').split(',')
        if c.strip()
    ]
    if companions and present is not None:
        if all(c in present for c in companions):
            score += 1.0
        else:
            score -= 1.0
    created = row.get('created_at')
    if isinstance(created, datetime):
        age_days = max(0.0, (now - created).total_seconds() / 86400)
        score += 1.5 / (1.0 + age_days / 14.0)
    shown = row.get('last_used_at')
    if isinstance(shown, datetime) and (
            (now - shown).total_seconds() < RECENTLY_SHOWN_SECONDS):
        score -= 3.0
    return score + random.uniform(0, 1.5)


def get_bot_memories(
    db, bot_guid, player_guid, count=3,
    exclude_first_meeting=False,
    mark_used=False,
    zone_id=0, map_id=0,
    present=None,
    relevant_to=None,
):
    """Retrieve the active memories that best fit the
    moment for a bot-player pair.

    Scoring prefers the current place (map_id, zone_id),
    memories whose companions are present (present: names
    of the bots in the party now), recent memories and
    weighty types, and holds back ones shown in the last
    30 minutes. relevant_to (a player message) keeps only
    memories of the same place or topic, so a reply is not
    handed unrelated memories.

    Every returned row gets last_used_at (last shown);
    mark_used=True also marks it as referenced, for callers
    whose prompt is about the memory.

    Returns RecalledMemory strings with the age in front
    (may be empty).
    """
    try:
        zone_id = int(zone_id or 0)
        map_id = int(map_id or 0)
        extra = (
            " AND memory_type != 'first_meeting'"
            if exclude_first_meeting else ""
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, memory, memory_type, zone_id, map_id,"
            " companions, created_at, last_used_at"
            " FROM llm_bot_memories"
            " WHERE bot_guid = %s"
            "   AND player_guid = %s"
            "   AND active = 1"
            + extra,
            (bot_guid, player_guid),
        )
        rows = cursor.fetchall()
        if relevant_to is not None:
            words = _topic_words(relevant_to)
            rows = [
                r for r in rows
                if _relevant(r, zone_id, map_id, words)
            ]
        if not rows:
            return []
        present_set = (
            {str(n) for n in present if n}
            if present is not None else None
        )
        now = datetime.now()
        rows.sort(
            key=lambda r: _score_memory(
                r, zone_id, map_id, present_set, now),
            reverse=True,
        )
        rows = rows[:max(0, int(count))]
        if rows:
            ids = [row['id'] for row in rows]
            placeholders = ','.join(['%s'] * len(ids))
            cursor.execute(
                "UPDATE llm_bot_memories"
                " SET last_used_at = NOW()"
                + (", used = 1" if mark_used else "")
                + " WHERE id IN (%s)" % placeholders,
                tuple(ids),
            )
            db.commit()
        result = []
        for row in rows:
            age = memory_age_label(row.get('created_at'), now)
            text = str(row.get('memory') or '')
            item = RecalledMemory(f"({age}) {text}" if age else text)
            item.memory_id = int(row['id'])
            result.append(item)
        return result
    except Exception:
        logger.error(
            f"Memory retrieval failed for "
            f"bot={bot_guid} player={player_guid}",
            exc_info=True,
        )
        return []


def mark_memories_used(db, memories) -> None:
    """Mark recalled memories as referenced (used = 1)."""
    ids = [
        int(getattr(m, 'memory_id', 0) or 0)
        for m in (memories or [])
    ]
    ids = [i for i in ids if i]
    if not ids:
        return
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE llm_bot_memories SET used = 1"
            " WHERE id IN (%s)" % ','.join(['%s'] * len(ids)),
            tuple(ids),
        )
        db.commit()
    except Exception:
        logger.error("mark_memories_used failed", exc_info=True)


# ============================================================
# SANITIZATION
# ============================================================

def sanitize_memory_for_prompt(memory: str) -> str:
    """Sanitize a memory string for safe inclusion
    in an LLM prompt.

    Strips control characters and normalizes
    whitespace. Length is bounded at write time by
    _clamp_memory_text, so the full memory is sent.
    """
    if not memory or not isinstance(memory, str):
        return ""
    # Strip control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', memory)
    # Normalize whitespace
    return ' '.join(text.split())
