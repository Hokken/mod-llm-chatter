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
    build_bot_identity,
    call_llm,
    cleanup_message,
    get_class_name,
    get_race_name,
    strip_speaker_prefix,
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



def check_or_create_bot_identity(
    db, config, bot_guid, bot_name,
):
    """Check for a stored persistent identity.

    If a row exists in llm_bot_identities with a
    matching identity_version, return stored values.
    Otherwise generate fresh traits, store them, and
    return.

    Returns dict with trait1-3, role, farewell_msg
    or None if identity system is disabled.
    """
    if not config:
        return None
    target_version = int(config.get(
        'LLMChatter.Memory.IdentityVersion', 1
    ))

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT trait1, trait2, trait3, role,"
            "   tone, farewell_msg, backstory,"
            "   identity_version"
            " FROM llm_bot_identities"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        row = cursor.fetchone()
        if row and int(
            row.get('identity_version', 0)
        ) == target_version:
            logger.debug(
                "Identity reused for %s"
                " (v%s)",
                bot_name, target_version,
            )
            return {
                'trait1': row['trait1'],
                'trait2': row['trait2'],
                'trait3': row['trait3'],
                'role': row.get('role'),
                'tone': row.get('tone'),
                'farewell_msg': row.get(
                    'farewell_msg'
                ),
                'backstory': row.get('backstory'),
            }
        had_row = row is not None
    except Exception:
        had_row = False

    # No stored identity or version mismatch:
    # generate fresh traits
    categories = random.sample(
        list(PERSONALITY_TRAITS.keys()), 3
    )
    traits = [
        random.choice(PERSONALITY_TRAITS[cat])
        for cat in categories
    ]

    try:
        cursor = db.cursor()
        # Clear farewell_msg and backstory on version
        # bump so they regenerate for the new
        # personality instead of reusing stale values
        cursor.execute("""
            INSERT INTO llm_bot_identities
            (bot_guid, bot_name,
             trait1, trait2, trait3,
             tone,
             farewell_msg,
             backstory,
             identity_version)
            VALUES (%s, %s, %s, %s, %s, NULL,
                    NULL, NULL, %s)
            ON DUPLICATE KEY UPDATE
                bot_name = VALUES(bot_name),
                trait1 = VALUES(trait1),
                trait2 = VALUES(trait2),
                trait3 = VALUES(trait3),
                tone = NULL,
                farewell_msg = NULL,
                backstory = NULL,
                identity_version =
                    VALUES(identity_version),
                created_at = CURRENT_TIMESTAMP
        """, (
            bot_guid, bot_name,
            traits[0], traits[1], traits[2],
            target_version,
        ))
        db.commit()
        logger.debug(
            "Identity %s for %s"
            " (v%s): %s, %s, %s",
            'bumped' if had_row else 'created',
            bot_name, target_version,
            traits[0], traits[1], traits[2],
        )
    except Exception:
        pass

    return {
        'trait1': traits[0],
        'trait2': traits[1],
        'trait3': traits[2],
        'role': None,
        'tone': None,
        'farewell_msg': None,
        'backstory': None,
        'reason': (
            'version_bump' if had_row else 'new'
        ),
    }


def _generate_bot_tone(
    db, config, bot_guid, group_id,
    bot_name, bot_class, bot_race, traits,
):
    """Generate a short tone description via LLM.

    Checks if tone is already stored for this
    bot+group. If not, calls LLM to generate one
    based on the bot's personality traits.

    Returns the tone string, or a fallback on
    failure.
    """
    fallback = "thoughtful and measured"

    def _sync_group_rows(cursor, tone_value):
        if group_id:
            cursor.execute(
                "UPDATE llm_group_bot_traits"
                " SET tone = %s"
                " WHERE group_id = %s"
                "   AND bot_guid = %s"
                "   AND tone IS NULL",
                (tone_value, group_id, bot_guid),
            )
        else:
            cursor.execute(
                "UPDATE llm_group_bot_traits"
                " SET tone = %s"
                " WHERE bot_guid = %s"
                "   AND tone IS NULL",
                (tone_value, bot_guid),
            )

    # Check if tone already stored
    try:
        cursor = db.cursor(dictionary=True)
        if group_id:
            cursor.execute(
                "SELECT tone FROM llm_group_bot_traits"
                " WHERE group_id = %s"
                "   AND bot_guid = %s",
                (group_id, bot_guid),
            )
            row = cursor.fetchone()
            if row and row.get('tone'):
                return row['tone']

        cursor.execute(
            "SELECT tone FROM llm_bot_identities"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        row = cursor.fetchone()
        if row and row.get('tone'):
            tone = row['tone']
            cursor = db.cursor()
            _sync_group_rows(cursor, tone)
            db.commit()
            return tone
    except Exception:
        pass

    # Build LLM prompt
    trait_str = ', '.join(traits)
    prompt = (
        "You are helping define the communication "
        "style of a WoW bot character.\n\n"
        f"Bot: {bot_name} ({bot_race} {bot_class})\n"
        f"Personality traits: {trait_str}\n\n"
        "Write a short tone description (5-8 words) "
        "that captures how this character speaks.\n"
        "It must be consistent with ALL three traits "
        "— do not contradict any of them.\n"
        "Examples: \"wry, guarded, with quiet "
        "curiosity\" / \"bold and warm, prone to "
        "rambling\" / \"earnest and blunt, "
        "occasionally self-deprecating\"\n\n"
        "Respond with ONLY the tone description, "
        "no quotes, no punctuation at the end."
    )

    # Plain-string prompt — inject language rule
    # directly since this path doesn't go through
    # append_json_instruction.
    from chatter_shared import get_language_rule
    lang_rule = get_language_rule()
    if lang_rule:
        prompt += lang_rule

    # Build LLM client inline (same pattern as
    # _call_llm_for_memory in chatter_memory.py)
    client = None
    try:
        provider = config.get(
            'LLMChatter.Provider', 'anthropic'
        ).lower()
        if provider == 'ollama':
            import openai as _openai
            base = config.get(
                'LLMChatter.Ollama.BaseUrl',
                'http://localhost:11434',
            )
            client = _openai.OpenAI(
                base_url=f"{base.rstrip('/')}/v1",
                api_key='ollama',
            )
        elif provider == 'openai':
            import openai as _openai
            client = _openai.OpenAI(
                api_key=config.get(
                    'LLMChatter.OpenAI.ApiKey', ''
                )
            )
        else:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(
                api_key=config.get(
                    'LLMChatter.Anthropic.ApiKey', ''
                )
            )
    except Exception:
        pass

    try:
        response = call_llm(
            client, prompt, config,
            max_tokens_override=30,
            context=f"tone:{bot_name}",
            label='bot_tone',
        )
        if not response:
            raise ValueError("empty response")

        tone = response.strip().strip('"').strip()
        tone = tone.rstrip('.')
        if not tone:
            raise ValueError("blank tone")
        # Cap at 100 chars
        tone = tone[:100]

        # Store in DB
        cursor = db.cursor()
        _sync_group_rows(cursor, tone)
        cursor.execute(
            "UPDATE llm_bot_identities"
            " SET tone = %s"
            " WHERE bot_guid = %s",
            (tone, bot_guid),
        )
        db.commit()

        logger.debug(
            "Tone generated for %s: %s",
            bot_name, tone,
        )

        return tone

    except Exception:
        # Store fallback so we don't retry LLM on
        # every subsequent call for this bot+group
        try:
            cursor = db.cursor()
            _sync_group_rows(cursor, fallback)
            cursor.execute(
                "UPDATE llm_bot_identities"
                " SET tone = %s"
                " WHERE bot_guid = %s"
                "   AND tone IS NULL",
                (fallback, bot_guid),
            )
            db.commit()
        except Exception:
            pass
        return fallback


def _generate_bot_backstory(
    db, config, bot_guid, group_id,
    bot_name, bot_class, bot_race, traits, tone,
):
    """Generate a short background story via LLM.

    Checks if backstory is already stored for this
    bot. If not, calls LLM to generate one based on
    the bot's race, class, traits, and tone.

    Returns the backstory string, or None on failure.
    """
    if not int(config.get(
        'LLMChatter.Backstory.Enable', 1
    )):
        return None

    def _sync_group_rows(cursor, value):
        if group_id:
            cursor.execute(
                "UPDATE llm_group_bot_traits"
                " SET backstory = %s"
                " WHERE group_id = %s"
                "   AND bot_guid = %s"
                "   AND backstory IS NULL",
                (value, group_id, bot_guid),
            )
        else:
            cursor.execute(
                "UPDATE llm_group_bot_traits"
                " SET backstory = %s"
                " WHERE bot_guid = %s"
                "   AND backstory IS NULL",
                (value, bot_guid),
            )

    # Check if backstory already stored
    try:
        cursor = db.cursor(dictionary=True)
        if group_id:
            cursor.execute(
                "SELECT backstory"
                " FROM llm_group_bot_traits"
                " WHERE group_id = %s"
                "   AND bot_guid = %s",
                (group_id, bot_guid),
            )
            row = cursor.fetchone()
            if row and row.get('backstory'):
                return row['backstory']

        cursor.execute(
            "SELECT backstory"
            " FROM llm_bot_identities"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        row = cursor.fetchone()
        if row and row.get('backstory'):
            bs = row['backstory']
            cursor = db.cursor()
            _sync_group_rows(cursor, bs)
            db.commit()
            return bs
    except Exception:
        pass

    # Build LLM prompt
    trait_str = ', '.join(traits)
    tone_line = (
        f"\nSpeaking tone: {tone}"
        if tone else ""
    )
    prompt = (
        "You are a World of Warcraft lore writer.\n\n"
        f"Character: {bot_name}, a {bot_race} "
        f"{bot_class}.\n"
        f"Personality traits: {trait_str}\n"
        f"{tone_line}\n\n"
        "Write a 3-4 sentence background story for "
        "this character. Include:\n"
        "- A birthplace appropriate to their race "
        "and Warcraft lore\n"
        "- A brief mention of their parents or "
        "upbringing\n"
        "- 1-2 formative events that shaped them\n\n"
        "The story should hint at their current "
        "personality but not rigidly explain every "
        "trait. Stay consistent with Warcraft lore "
        "and the character's race/class "
        "combination.\n\n"
        "Respond with ONLY the backstory paragraph, "
        "no quotes, no character name prefix."
    )

    # Inject language rule
    from chatter_shared import get_language_rule
    lang_rule = get_language_rule()
    if lang_rule:
        prompt += lang_rule

    # Build LLM client inline
    client = None
    try:
        provider = config.get(
            'LLMChatter.Provider', 'anthropic'
        ).lower()
        if provider == 'ollama':
            import openai as _openai
            base = config.get(
                'LLMChatter.Ollama.BaseUrl',
                'http://localhost:11434',
            )
            client = _openai.OpenAI(
                base_url=f"{base.rstrip('/')}/v1",
                api_key='ollama',
            )
        elif provider == 'openai':
            import openai as _openai
            client = _openai.OpenAI(
                api_key=config.get(
                    'LLMChatter.OpenAI.ApiKey', ''
                )
            )
        else:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(
                api_key=config.get(
                    'LLMChatter.Anthropic.ApiKey', ''
                )
            )
    except Exception:
        pass

    try:
        response = call_llm(
            client, prompt, config,
            max_tokens_override=200,
            context=f"backstory:{bot_name}",
            label='bot_backstory',
        )
        if not response:
            raise ValueError("empty response")

        backstory = response.strip().strip('"').strip()
        if not backstory:
            raise ValueError("blank backstory")
        # Cap at 1000 chars
        backstory = backstory[:1000]

        # Store in DB — upsert identity so backstory
        # persists even if no identity row existed
        cursor = db.cursor()
        _sync_group_rows(cursor, backstory)
        target_version = int(config.get(
            'LLMChatter.Memory.IdentityVersion', 1
        ))
        cursor.execute(
            "INSERT INTO llm_bot_identities"
            " (bot_guid, bot_name,"
            "  trait1, trait2, trait3,"
            "  backstory, identity_version)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s)"
            " ON DUPLICATE KEY UPDATE"
            "  backstory = VALUES(backstory)",
            (bot_guid, bot_name,
             traits[0], traits[1], traits[2],
             backstory, target_version),
        )
        db.commit()

        logger.debug(
            "Backstory generated for %s: %s",
            bot_name, backstory[:80],
        )

        return backstory

    except Exception:
        return None


def regenerate_missing_identity_tones(
    db, client, config, limit=3,
):
    """Backfill derived tones for bots whose traits are
    set but whose stored tone is currently NULL.

    This supports addon-driven trait edits where the
    traits are the user's input and tone is a derived
    output generated asynchronously.
    """
    if not config or int(config.get(
        'LLMChatter.Memory.Enable', 1
    )) != 1:
        return 0

    try:
        limit = max(1, int(limit))
    except (TypeError, ValueError):
        limit = 1

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.bot_guid,
               COALESCE(i.bot_name, c.name) AS bot_name,
               i.trait1, i.trait2, i.trait3,
               c.class, c.race
        FROM llm_bot_identities i
        JOIN characters c
          ON c.guid = i.bot_guid
        WHERE i.tone IS NULL
          AND i.trait1 IS NOT NULL
          AND i.trait1 != ''
          AND i.trait2 IS NOT NULL
          AND i.trait2 != ''
          AND i.trait3 IS NOT NULL
          AND i.trait3 != ''
        ORDER BY i.created_at DESC, i.bot_guid DESC
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()

    generated = 0
    for row in rows:
        bot_guid = int(row.get('bot_guid') or 0)
        if not bot_guid:
            continue

        bot_name = row.get('bot_name', '') or ''
        bot_class = get_class_name(
            int(row.get('class') or 0)
        )
        bot_race = get_race_name(
            int(row.get('race') or 0)
        )
        if not bot_name or not bot_class or not bot_race:
            continue

        traits = [
            row.get('trait1', '') or '',
            row.get('trait2', '') or '',
            row.get('trait3', '') or '',
        ]
        if not all(traits):
            continue

        tone = _generate_bot_tone(
            db, config, bot_guid, None,
            bot_name, bot_class, bot_race,
            traits,
        )
        if tone:
            generated += 1
            logger.info(
                "Regenerated tone for %s (%s): %s",
                bot_name, bot_guid, tone,
            )

    return generated


def regenerate_bot_backstory(
    db, config, bot_guid,
):
    """Clear and regenerate backstory for a bot.

    Called by the bot_backstory_regen event handler
    when the player requests a new backstory via addon.
    """
    # Clear existing backstory
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE llm_bot_identities"
            " SET backstory = NULL"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        cursor.execute(
            "UPDATE llm_group_bot_traits"
            " SET backstory = NULL"
            " WHERE bot_guid = %s",
            (bot_guid,),
        )
        db.commit()
    except Exception:
        pass

    # Fetch bot info for generation — try identity
    # table first, fall back to session traits
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.bot_guid,
               COALESCE(i.bot_name, c.name)
                   AS bot_name,
               i.trait1, i.trait2, i.trait3,
               i.tone,
               c.class, c.race
        FROM llm_bot_identities i
        JOIN characters c
          ON c.guid = i.bot_guid
        WHERE i.bot_guid = %s
    """, (bot_guid,))
    row = cursor.fetchone()
    if not row:
        # Fall back to session traits
        cursor.execute("""
            SELECT t.bot_guid,
                   COALESCE(t.bot_name, c.name)
                       AS bot_name,
                   t.trait1, t.trait2, t.trait3,
                   t.tone,
                   c.class, c.race
            FROM llm_group_bot_traits t
            JOIN characters c
              ON c.guid = t.bot_guid
            WHERE t.bot_guid = %s
            ORDER BY t.assigned_at DESC
            LIMIT 1
        """, (bot_guid,))
        row = cursor.fetchone()
    if not row:
        return None

    bot_name = row.get('bot_name', '') or ''
    bot_class = get_class_name(
        int(row.get('class') or 0)
    )
    bot_race = get_race_name(
        int(row.get('race') or 0)
    )
    traits = [
        row.get('trait1', ''),
        row.get('trait2', ''),
        row.get('trait3', ''),
    ]
    tone = row.get('tone', '')

    if not bot_name or not bot_class or not bot_race:
        return None
    if not all(traits):
        return None

    backstory = _generate_bot_backstory(
        db, config, bot_guid, None,
        bot_name, bot_class, bot_race,
        traits, tone,
    )
    if backstory:
        logger.info(
            "Regenerated backstory for %s (%s)",
            bot_name, bot_guid,
        )
    return backstory


def handle_backstory_regen_event(
    db, client, config, event,
):
    """Event handler for bot_backstory_regen.

    Called when a player requests backstory
    regeneration via the addon. Clears and
    regenerates the backstory, then marks the
    event completed.
    """
    import json
    extra = event.get('extra_data')
    if isinstance(extra, str):
        extra = json.loads(extra)

    bot_guid = int(extra.get('bot_guid') or 0)
    if not bot_guid:
        return True

    backstory = regenerate_bot_backstory(
        db, config, bot_guid,
    )
    return True


def assign_bot_traits(
    db, group_id, bot_guid, bot_name,
    role=None, zone=0, area_id=0, map_id=0,
    config=None,
    bot_class='', bot_race='',
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

    # Clear stored tone and backstory on fresh identity
    # (new or version bump) so they get regenerated
    if identity and identity.get('reason'):
        try:
            cursor.execute(
                "UPDATE llm_group_bot_traits"
                " SET tone = NULL,"
                "     backstory = NULL"
                " WHERE group_id = %s"
                "   AND bot_guid = %s",
                (group_id, bot_guid),
            )
            db.commit()
        except Exception:
            pass

    # Generate LLM-derived tone if not already set
    tone = None
    if config and bot_class and bot_race:
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
    if config and bot_class and bot_race:
        try:
            backstory = _generate_bot_backstory(
                db, config, bot_guid, group_id,
                bot_name, bot_class, bot_race,
                traits, tone,
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
            zone, area, map
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
        }
    return None


def get_other_group_bot(db, group_id, exclude_guid):
    """Find another bot in the group (not the excluded
    one). Returns dict with guid, name, traits or None.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT bot_guid, bot_name,
               trait1, trait2, trait3, role, tone
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
            'tone': row.get('tone'),
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
    if config and int(config.get(
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

    identity = build_bot_identity(
        bot_name, bot_race, bot_class, bot_gender,
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

    try:
        response = call_llm(
            client, prompt, config,
            max_tokens_override=60,
            context=f"farewell:{bot_name}",
            label='group_farewell',
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
        if config and int(config.get(
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
