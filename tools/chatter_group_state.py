"""Group state helpers extracted from chatter_group (N4).

This module owns:
- session mood drift state
- personality trait assignment/fetch helpers
- pre-generated farewell storage
"""

import logging
import random
import threading
import time

from chatter_shared import (
    build_race_class_context,
    call_llm,
    cleanup_message,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)

# Keep in sync from chatter_group.init_group_config
_chat_history_limit = 10


def set_group_chat_history_limit(value: int):
    """Set shared chat-history limit used by group helpers."""
    global _chat_history_limit
    _chat_history_limit = max(1, min(int(value), 50))


# ============================================================
# SESSION MOOD DRIFT
# ============================================================
# Per-bot mood scores: (group_id, bot_guid) -> (float, float)
# Value = (score, last_update_time). Positive = happy,
# negative = gloomy. Drifts toward 0.
_bot_mood_scores: dict = {}
_bot_mood_scores_lock = threading.RLock()
_MOOD_STALE_SECONDS = 7200  # 2 hours

MOOD_LABELS = [
    (-999, -4, 'miserable'),
    (-4, -2, 'gloomy'),
    (-2, -0.5, 'tired'),
    (-0.5, 0.5, 'neutral'),
    (0.5, 2, 'content'),
    (2, 4, 'cheerful'),
    (4, 999, 'ecstatic'),
]

MOOD_DELTAS = {
    'kill': 1.0,
    'boss_kill': 2.0,
    'death': -2.0,
    'wipe': -3.0,
    'loot': 1.0,
    'epic_loot': 2.0,
    'resurrect': 1.0,
    'quest': 1.0,
    'levelup': 2.0,
    'achievement': 1.5,
}

# Drift toward neutral each event
MOOD_DRIFT_RATE = 0.5


def _evict_stale_moods():
    """Remove mood entries older than 2 hours."""
    with _bot_mood_scores_lock:
        now = time.time()
        stale = [
            k for k, (_, ts)
            in _bot_mood_scores.items()
            if now - ts > _MOOD_STALE_SECONDS
        ]
        for k in stale:
            del _bot_mood_scores[k]


def update_bot_mood(
    group_id: int, bot_guid: int,
    event_type: str,
):
    """Shift a bot's mood score based on an event.

    Also applies a slow drift toward neutral (0).
    """
    with _bot_mood_scores_lock:
        # Periodic eviction of stale entries
        if len(_bot_mood_scores) > 50:
            _evict_stale_moods()

        key = (group_id, bot_guid)
        entry = _bot_mood_scores.get(key)
        current = entry[0] if entry else 0.0

        # Drift toward neutral
        if current > 0:
            current = max(
                0, current - MOOD_DRIFT_RATE
            )
        elif current < 0:
            current = min(
                0, current + MOOD_DRIFT_RATE
            )

        # Apply event delta
        delta = MOOD_DELTAS.get(event_type, 0.0)
        current += delta

        # Clamp to [-6, 6]
        current = max(-6.0, min(6.0, current))
        _bot_mood_scores[key] = (
            current, time.time()
        )

        label = get_bot_mood_label(
            group_id, bot_guid
        )


def get_bot_mood_label(
    group_id: int, bot_guid: int,
) -> str:
    """Get human-readable mood label for a bot."""
    with _bot_mood_scores_lock:
        entry = _bot_mood_scores.get(
            (group_id, bot_guid)
        )
        score = entry[0] if entry else 0.0
        for low, high, label in MOOD_LABELS:
            if low <= score < high:
                return label
        return 'neutral'


def cleanup_group_moods(group_id: int):
    """Remove mood data for a disbanded group."""
    with _bot_mood_scores_lock:
        keys_to_remove = [
            k for k in _bot_mood_scores
            if k[0] == group_id
        ]
        for k in keys_to_remove:
            del _bot_mood_scores[k]


# ============================================================
# PERSONALITY TRAITS
# ============================================================
PERSONALITY_TRAITS = {
    'social': [
        'friendly', 'reserved', 'talkative',
        'shy', 'thoughtful', 'polite',
    ],
    'attitude': [
        'optimistic', 'cynical', 'cautious',
        'easygoing', 'stoic',
    ],
    'focus': [
        'combat-focused', 'loot-driven',
        'explorer', 'quest-obsessed',
        'socializer',
    ],
    'humor': [
        'sarcastic', 'deadpan', 'cheerful',
        'dry wit', 'warmhearted',
    ],
    'energy': [
        'eager', 'laid-back', 'steady',
        'drowsy', 'relaxed',
    ],
}


def assign_bot_traits(
    db, group_id, bot_guid, bot_name,
    role=None, zone=0, map_id=0
):
    """Pick 3 random traits and store them.

    Selects 3 random categories, picks 1 trait from
    each. Uses INSERT ... ON DUPLICATE KEY UPDATE
    so re-invites get fresh traits.
    Optionally stores the bot's detected role
    (tank/healer/melee_dps/ranged_dps) and current
    zone/map from C++ extra_data.
    """
    categories = random.sample(
        list(PERSONALITY_TRAITS.keys()), 3
    )
    traits = [
        random.choice(PERSONALITY_TRAITS[cat])
        for cat in categories
    ]

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO llm_group_bot_traits
        (group_id, bot_guid, bot_name,
         trait1, trait2, trait3, role,
         zone, map)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            trait1 = VALUES(trait1),
            trait2 = VALUES(trait2),
            trait3 = VALUES(trait3),
            role = VALUES(role),
            zone = VALUES(zone),
            map = VALUES(map),
            assigned_at = CURRENT_TIMESTAMP
    """, (
        group_id, bot_guid, bot_name,
        traits[0], traits[1], traits[2],
        role, zone, map_id
    ))
    db.commit()

    return traits


def get_bot_traits(
    db, group_id, bot_guid, config=None
):
    """Retrieve assigned traits for a bot."""
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT trait1, trait2, trait3,
            bot_name, role, zone, area, map
        FROM llm_group_bot_traits
        WHERE group_id = %s AND bot_guid = %s
    """, (group_id, bot_guid))
    row = cursor.fetchone()
    if row:
        zone = int(row.get('zone', 0) or 0)
        map_id = int(row.get('map', 0) or 0)
        name = row.get('bot_name', '')

        area = int(row.get('area', 0) or 0)

        # Debug: log zone+area for every trait lookup
        if (config
                and config.get(
                    'LLMChatter.DebugLog', '0'
                ) == '1'):
            from chatter_shared import (
                format_location_label
            )
            loc = format_location_label(zone, area)
            logger.info(
                f"[DEBUG] get_bot_traits: "
                f"{name} (group={group_id}) "
                f"{loc}, map={map_id}"
            )
        return {
            'traits': [
                row['trait1'], row['trait2'],
                row['trait3'],
            ],
            'bot_name': name,
            'role': row.get('role'),
            'zone': zone,
            'area': area,
            'map': map_id,
        }
    return None


def get_other_group_bot(db, group_id, exclude_guid):
    """Find another bot in the group (not the excluded
    one). Returns dict with guid, name, traits or None.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT bot_guid, bot_name,
               trait1, trait2, trait3, role
        FROM llm_group_bot_traits
        WHERE group_id = %s AND bot_guid != %s
        ORDER BY RAND()
        LIMIT 1
    """, (group_id, exclude_guid))
    row = cursor.fetchone()
    if row:
        return {
            'guid': row['bot_guid'],
            'name': row['bot_name'],
            'traits': [
                row['trait1'], row['trait2'],
                row['trait3'],
            ],
            'role': row.get('role'),
        }
    return None


def _generate_farewell(
    db, client, config,
    bot_name, bot_race, bot_class,
    traits, mode, group_id, bot_guid,
):
    """Generate and store a farewell message for later
    use when the bot leaves the group.

    Called after the greeting is generated. Uses a
    small LLM call to pre-generate the farewell.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    if is_rp:
        style = (
            "Stay in-character. Brief, natural "
            "farewell fitting your race and class."
        )
    else:
        style = (
            "Casual, brief farewell like a real "
            "player leaving a group."
        )

    rp_ctx = ""
    if is_rp:
        rp_ctx = build_race_class_context(
            bot_race, bot_class
        )
        if rp_ctx:
            rp_ctx = f"\n{rp_ctx}"

    prompt = (
        f"You are {bot_name}, a {bot_race} "
        f"{bot_class}.\n"
        f"Personality: {trait_str}{rp_ctx}\n\n"
        f"Write a short farewell message for when "
        f"you leave a party. One sentence, under "
        f"80 characters.\n"
        f"{style}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Just the farewell text, nothing else"
    )

    try:
        response = call_llm(
            client, prompt, config,
            max_tokens_override=60,
            context=f"farewell:{bot_name}"
        )
        if not response:
            return

        farewell = response.strip().strip('"').strip()
        farewell = cleanup_message(farewell)
        farewell = strip_speaker_prefix(
            farewell, bot_name
        )
        if not farewell or len(farewell) > 255:
            return

        cursor = db.cursor()
        cursor.execute("""
            UPDATE llm_group_bot_traits
            SET farewell_msg = %s
            WHERE group_id = %s AND bot_guid = %s
        """, (farewell, group_id, bot_guid))
        db.commit()

    except Exception:
        pass

def _has_recent_event(
    db, event_type, subject_guid, seconds=60,
    exclude_id=None
):
    """Check if a recent event exists for this bot.
    Prevents duplicate greetings from rapid
    invite/leave/reinvite. Use exclude_id to skip
    the event currently being processed.
    """
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT 1 FROM llm_chatter_events
        WHERE event_type = %s
          AND subject_guid = %s
          AND status IN (
              'pending', 'processing', 'completed'
          )
          AND created_at > DATE_SUB(
              NOW(), INTERVAL %s SECOND
          )
    """
    params = [event_type, subject_guid, seconds]
    if exclude_id:
        query += "  AND id != %s"
        params.append(exclude_id)
    query += " LIMIT 1"
    cursor.execute(query, params)
    return cursor.fetchone() is not None

def _mark_event(db, event_id, status):
    """Mark an event with given status."""
    cursor = db.cursor()
    if status == 'completed':
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = 'completed', "
            "processed_at = NOW() "
            "WHERE id = %s",
            (event_id,)
        )
    else:
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = %s WHERE id = %s",
            (status, event_id)
        )
    db.commit()

def _store_chat(
    db, group_id, speaker_guid,
    speaker_name, is_bot, message
):
    """Store a message in group chat history."""
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO llm_group_chat_history
        (group_id, speaker_guid, speaker_name,
         is_bot, message)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        group_id, speaker_guid, speaker_name,
        1 if is_bot else 0, message[:255]
    ))
    db.commit()

def _get_recent_chat(db, group_id, limit=None):
    """Get recent chat messages for a group.

    Returns list of dicts with speaker_name, is_bot,
    message — ordered oldest-first for natural
    reading in prompts.
    """
    if limit is None:
        limit = _chat_history_limit
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT speaker_name, is_bot, message
        FROM llm_group_chat_history
        WHERE group_id = %s
        ORDER BY id DESC
        LIMIT %s
    """, (group_id, limit))
    rows = cursor.fetchall()
    return list(reversed(rows))

def format_chat_history(history):
    """Format chat history as a readable string
    for inclusion in prompts.
    Returns empty string if no history.
    """
    if not history:
        return ""
    lines = []
    for msg in history:
        name = msg['speaker_name']
        text = msg['message']
        if msg['is_bot']:
            lines.append(f"  {name}: {text}")
        else:
            lines.append(
                f"  {name} (player): {text}"
            )
    return (
        "\nRecent party chat:\n"
        + '\n'.join(lines)
    )

def get_group_members(db, group_id):
    """Get all bot names in a group.
    Returns list of bot_name strings.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT bot_name
        FROM llm_group_bot_traits
        WHERE group_id = %s
    """, (group_id,))
    return [
        row['bot_name']
        for row in cursor.fetchall()
    ]


def get_group_player_name(db, group_id):
    """Get the real player's name from chat history
    or player_msg events. Returns name or None.
    """
    cursor = db.cursor(dictionary=True)
    # Check chat history first (most reliable)
    cursor.execute("""
        SELECT speaker_name
        FROM llm_group_chat_history
        WHERE group_id = %s AND is_bot = 0
        ORDER BY id DESC
        LIMIT 1
    """, (group_id,))
    row = cursor.fetchone()
    if row:
        return row['speaker_name']

    # Fallback: check join events first (most recent
    # join captures current player name reliably),
    # then player_msg events
    cursor.execute("""
        SELECT JSON_EXTRACT(
            extra_data, '$.player_name'
        ) as pname
        FROM llm_chatter_events
        WHERE event_type IN (
              'bot_group_join',
              'bot_group_join_batch',
              'bot_group_player_msg'
          )
          AND CAST(
              JSON_EXTRACT(
                  extra_data, '$.group_id'
              ) AS UNSIGNED
          ) = %s
        ORDER BY id DESC
        LIMIT 1
    """, (group_id,))
    row = cursor.fetchone()
    if row and row['pname']:
        # JSON_EXTRACT returns quoted string
        name = row['pname'].strip('"')
        if name:
            return name

    return None
