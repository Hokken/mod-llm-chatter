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
    build_travel_state_from_row,
    call_llm,
    cleanup_message,
    format_travel_context,
    get_class_name,
    get_gender_label,
    get_race_name,
    shorten_chat_message,
    strip_speaker_prefix,
)
from chatter_mode import (
    build_player_prompt_header,
    is_roleplay,
    normalize_chatter_mode,
    resolve_player_personality,
)
from chatter_constants import PERSONALITY_TRAITS
from chatter_db import mark_event

logger = logging.getLogger(__name__)



# Keep in sync from chatter_group.init_group_config
_chat_history_limit = 10


def set_group_chat_history_limit(value: int):
    """Set shared chat-history limit used by group helpers."""
    global _chat_history_limit
    _chat_history_limit = max(1, min(int(value), 50))


def normalize_active_group_personalities(db, config) -> int:
    """Replace legacy RP metadata in active normal-mode group rows.

    Persistent identities remain unchanged for roleplay mode. Only the
    session-scoped group rows are normalized so existing groups immediately
    receive ordinary player styles after a bridge restart.
    """
    mode = normalize_chatter_mode(
        (config or {}).get('LLMChatter.ChatterMode', 'normal')
    )
    if is_roleplay(mode):
        return 0

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT group_id, bot_guid, bot_name "
        "FROM llm_group_bot_traits"
    )
    rows = cursor.fetchall()
    if not rows:
        return 0

    update_cursor = db.cursor()
    for row in rows:
        traits, tone = resolve_player_personality(
            row.get('bot_name', ''), mode=mode
        )
        update_cursor.execute(
            "UPDATE llm_group_bot_traits "
            "SET trait1 = %s, trait2 = %s, trait3 = %s, "
            "tone = %s, backstory = NULL "
            "WHERE group_id = %s AND bot_guid = %s",
            (
                traits[0], traits[1], traits[2], tone,
                row.get('group_id'), row.get('bot_guid'),
            ),
        )
    db.commit()
    logger.info(
        "Normalized %d active group personality row(s) for normal mode",
        len(rows),
    )
    return len(rows)


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


def _label_for_score(score: float) -> str:
    """Map a mood score onto its MOOD_LABELS bucket."""
    for low, high, label in MOOD_LABELS:
        if low <= score < high:
            return label
    return 'neutral'


def get_bot_mood_label(
    group_id: int, bot_guid: int,
) -> str:
    """Get human-readable mood label for a bot."""
    with _bot_mood_scores_lock:
        entry = _bot_mood_scores.get(
            (group_id, bot_guid)
        )
        score = entry[0] if entry else 0.0
        return _label_for_score(score)


def get_bot_mood_label_by_guid(bot_guid: int) -> str:
    """Get a bot's mood label regardless of channel.

    Uses the most recently updated live entry for this bot across
    groups, so guild and General prompts see the same event mood as
    party chat. Entries past the stale window count as neutral,
    matching the lifetime enforced by _evict_stale_moods.
    """
    with _bot_mood_scores_lock:
        now = time.time()
        latest = None
        for (_, guid), (score, ts) in _bot_mood_scores.items():
            if guid != bot_guid:
                continue
            if now - ts > _MOOD_STALE_SECONDS:
                continue
            if latest is None or ts > latest[1]:
                latest = (score, ts)
        return _label_for_score(latest[0] if latest else 0.0)


def cleanup_group_moods(group_id: int):
    """Remove mood data for a disbanded group."""
    with _bot_mood_scores_lock:
        keys_to_remove = [
            k for k in _bot_mood_scores
            if k[0] == group_id
        ]
        for k in keys_to_remove:
            del _bot_mood_scores[k]



from chatter_identity import (
    check_or_create_bot_identity,
    _generate_bot_tone, _generate_bot_backstory,
    regenerate_missing_identity_tones,
    regenerate_bot_backstory, regenerate_bot_tone,
    handle_backstory_regen_event, handle_tone_regen_event,
)


def assign_bot_traits(
    db, group_id, bot_guid, bot_name,
    role=None, zone=0, area_id=0, map_id=0,
    config=None,
    bot_class='', bot_race='', bot_gender='',
):
    """Pick 3 random traits and store them.

    If persistent identities are enabled (config
    provided), checks llm_bot_identities first and
    reuses stored traits. Otherwise generates fresh
    random traits.

    Uses INSERT ... ON DUPLICATE KEY UPDATE for
    the session-scoped llm_group_bot_traits table.
    """
    identity = None
    if config and int(config.get(
        'LLMChatter.Memory.Enable', 1
    )):
        identity = check_or_create_bot_identity(
            db, config, bot_guid, bot_name,
        )

    if identity:
        traits = [
            identity['trait1'],
            identity['trait2'],
            identity['trait3'],
        ]
        persistent_tone = identity.get('tone')
        persistent_backstory = identity.get(
            'backstory'
        )
        # Use stored role if caller didn't provide
        if not role and identity.get('role'):
            role = identity['role']
    else:
        categories = random.sample(
            list(PERSONALITY_TRAITS.keys()), 3
        )
        traits = [
            random.choice(PERSONALITY_TRAITS[cat])
            for cat in categories
        ]
        persistent_tone = None
        persistent_backstory = None

    mode = normalize_chatter_mode(
        (config or {}).get('LLMChatter.ChatterMode', 'normal')
    )
    traits, persistent_tone = resolve_player_personality(
        bot_name, traits, persistent_tone, mode
    )
    if not is_roleplay(mode):
        persistent_backstory = None

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO llm_group_bot_traits
        (group_id, bot_guid, bot_name,
         trait1, trait2, trait3, role, tone,
         backstory, zone, area, map)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            trait1 = VALUES(trait1),
            trait2 = VALUES(trait2),
            trait3 = VALUES(trait3),
            role = VALUES(role),
            tone = COALESCE(VALUES(tone), tone),
            backstory = COALESCE(
                VALUES(backstory), backstory
            ),
            zone = VALUES(zone),
            area = VALUES(area),
            map = VALUES(map),
            assigned_at = CURRENT_TIMESTAMP
    """, (
        group_id, bot_guid, bot_name,
        traits[0], traits[1], traits[2],
        role, persistent_tone,
        persistent_backstory,
        zone, int(area_id or 0), map_id
    ))
    db.commit()

    # Persist role back to llm_bot_identities so
    # future sessions for this bot inherit it
    if role and identity is not None:
        try:
            cursor.execute(
                "UPDATE llm_bot_identities"
                " SET role = %s"
                " WHERE bot_guid = %s",
                (role, bot_guid),
            )
            db.commit()
        except Exception:
            pass

    # Generate LLM-derived tone if not already set
    tone = (
        None if is_roleplay(mode)
        else persistent_tone
    )
    if is_roleplay(mode) and config and bot_class and bot_race:
        try:
            tone = _generate_bot_tone(
                db, config, bot_guid, group_id,
                bot_name, bot_class, bot_race,
                traits,
            )
        except Exception:
            pass

    # Generate LLM-derived backstory if not already set
    backstory = None
    if is_roleplay(mode) and config and bot_class and bot_race:
        try:
            backstory = _generate_bot_backstory(
                db, config, bot_guid, group_id,
                bot_name, bot_class, bot_race,
                traits, tone,
                bot_gender=bot_gender,
            )
        except Exception:
            pass

    return {
        'traits': traits,
        'tone': tone,
        'backstory': backstory,
    }


def get_bot_traits(
    db, group_id, bot_guid, config=None
):
    """Retrieve assigned traits for a bot."""
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT trait1, trait2, trait3,
            bot_name, role, tone, backstory,
            zone, area, map,
            travel_mode, travel_context,
            is_mounted, is_flying,
            is_taxi_flying, is_on_transport,
            mount_display_id, transport_name
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
            'tone': row.get('tone'),
            'backstory': row.get('backstory'),
            'zone': zone,
            'area': area,
            'map': map_id,
            'travel_state': {
                'mode': row.get('travel_mode') or '',
                'context': row.get('travel_context') or '',
                'mounted': bool(row.get('is_mounted')),
                'flying': bool(row.get('is_flying')),
                'taxi_flight': bool(
                    row.get('is_taxi_flying')),
                'on_transport': bool(
                    row.get('is_on_transport')),
                'mount_display_id': int(
                    row.get('mount_display_id') or 0),
                'transport_name': row.get(
                    'transport_name') or '',
            },
        }
    return None


def get_other_group_bot(db, group_id, exclude_guid):
    """Find another bot in the group (not the excluded
    one). Returns dict with guid, name, traits or None.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT bot_guid, bot_name,
               trait1, trait2, trait3, role, tone,
               backstory,
               travel_mode, travel_context,
               is_mounted, is_flying,
               is_taxi_flying, is_on_transport,
               mount_display_id, transport_name
        FROM llm_group_bot_traits
        WHERE group_id = %s AND bot_guid != %s
        ORDER BY RAND()
        LIMIT 1
    """, (group_id, exclude_guid))
    row = cursor.fetchone()
    if row:
        travel_state = build_travel_state_from_row(row)
        return {
            'guid': row['bot_guid'],
            'name': row['bot_name'],
            'traits': [
                row['trait1'], row['trait2'],
                row['trait3'],
            ],
            'role': row.get('role'),
            'tone': row.get('tone'),
            'backstory': row.get('backstory'),
            'travel_mode': travel_state.get('mode') or '',
            'travel_context': format_travel_context(
                travel_state),
            'travel_state': travel_state,
        }
    return None


def _generate_farewell(
    db, client, config,
    bot_name, bot_race, bot_class, bot_gender,
    traits, mode, group_id, bot_guid,
):
    """Generate and store a farewell message for later
    use when the bot leaves the group.

    Called after the greeting is generated. If a
    persistent identity already has a farewell, reuse
    it instead of generating a new one.
    """
    # Check for stored farewell in identity table,
    # but only reuse it if it matches the current
    # identity_version (version bumps clear it)
    if mode == 'roleplay' and config and int(config.get(
        'LLMChatter.Memory.Enable', 1
    )):
        target_version = int(config.get(
            'LLMChatter.Memory.IdentityVersion', 1
        ))
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT farewell_msg"
                " FROM llm_bot_identities"
                " WHERE bot_guid = %s"
                "   AND identity_version = %s",
                (bot_guid, target_version),
            )
            row = cursor.fetchone()
            if row and row.get('farewell_msg'):
                # Reuse stored farewell
                cursor2 = db.cursor()
                cursor2.execute(
                    "UPDATE llm_group_bot_traits"
                    " SET farewell_msg = %s"
                    " WHERE group_id = %s"
                    "   AND bot_guid = %s",
                    (
                        row['farewell_msg'],
                        group_id, bot_guid,
                    ),
                )
                db.commit()
                return
        except Exception:
            pass

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

    identity = build_player_prompt_header(
        bot_name,
        bot_race,
        bot_class,
        gender=bot_gender,
        mode=mode,
        channel='party',
    )
    prompt = (
        f"{identity}\n"
        f"Personality: {trait_str}{rp_ctx}\n\n"
        f"Write a short farewell message for when "
        f"you leave a party. One sentence, under "
        f"80 characters.\n"
        f"{style}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Just the farewell text, nothing else"
    )
    from chatter_shared import get_language_rule
    lang_rule = get_language_rule()
    if lang_rule:
        prompt += lang_rule

    try:
        response = call_llm(
            client, prompt, config,
            max_tokens_override=60,
            context=f"farewell:{bot_name}",
            label='group_farewell',
            free_text=True,
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

        # Also store in persistent identity table
        if is_rp and config and int(config.get(
            'LLMChatter.Memory.Enable', 1
        )):
            try:
                cursor.execute(
                    "UPDATE llm_bot_identities"
                    " SET farewell_msg = %s"
                    " WHERE bot_guid = %s",
                    (farewell, bot_guid),
                )
                db.commit()
            except Exception:
                pass

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

# Re-export for downstream modules that import
# _mark_event from chatter_group_state.
_mark_event = mark_event

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
        1 if is_bot else 0, shorten_chat_message(message)
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

    # Current group membership is more reliable
    # than historical join events. Same-account alt
    # bots do not have RNDBOT accounts, so exclude
    # GUIDs registered as bots in trait state too.
    cursor.execute("""
        SELECT c.name
        FROM group_member gm
        JOIN `groups` g
          ON g.guid = gm.guid
        JOIN characters c
          ON c.guid = gm.memberGuid
        JOIN acore_auth.account a
          ON a.id = c.account
        LEFT JOIN llm_group_bot_traits t
          ON t.group_id = gm.guid
         AND t.bot_guid = gm.memberGuid
        WHERE gm.guid = %s
          AND a.username NOT LIKE 'RNDBOT%%'
          AND t.bot_guid IS NULL
        ORDER BY (gm.memberGuid = g.leaderGuid) DESC
        LIMIT 1
    """, (group_id,))
    row = cursor.fetchone()
    if row and row.get('name'):
        return row['name']

    # Last fallback: check join/player_msg events.
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


def build_party_context(
    db, group_id, speaker_name='',
    include_history=True,
):
    """Roster and recent party chat for a prompt.

    Gives a reacting bot the same awareness the party
    conversation prompts already have: who else is here
    and what was just said. Returns '' when the group has
    neither.
    """
    if not group_id:
        return ''

    parts = []

    try:
        members = get_group_members(db, group_id)
    except Exception:
        members = []

    others = [
        name for name in members
        if name and name != speaker_name
    ]

    try:
        player_name = get_group_player_name(db, group_id)
    except Exception:
        player_name = None
    if player_name and player_name not in others:
        others.append(f"{player_name} (player)")

    if others:
        parts.append(
            f"Party members: {', '.join(others)}"
        )

    if include_history:
        try:
            history = format_chat_history(
                _get_recent_chat(db, group_id)
            )
        except Exception:
            history = ''
        if history:
            parts.append(history.strip('\n'))

    return '\n'.join(parts)
