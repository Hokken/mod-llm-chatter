"""
Chatter Cache - Background refill logic for
pre-cached group reactions.

Generates cached LLM responses for combat-time
events (pull cries, state callouts, spell support)
so C++ can deliver them instantly without waiting
for a live LLM call.

Imports from chatter_group, chatter_shared,
and chatter_constants.
"""

import logging

from chatter_group_prompts import (
    build_precache_combat_pull_prompt,
    build_precache_state_prompt,
    build_precache_spell_support_prompt,
    build_precache_spell_offensive_prompt,
)
from chatter_group_state import get_bot_mood_label
from chatter_shared import (
    call_llm, cleanup_message,
    strip_speaker_prefix,
    pick_emote_for_statement,
    parse_single_response,
)
from chatter_constants import CLASS_NAMES, RACE_NAMES

logger = logging.getLogger(__name__)


# Category definitions with priority order.
# Each tuple: (category_key, config_depth_key,
#               config_enable_key, prompt_type)
_CATEGORIES = [
    (
        'state_low_health',
        'LLMChatter.GroupChatter.PreCacheDepthState',
        'LLMChatter.GroupChatter.PreCacheStateEnable',
        'state',
    ),
    (
        'state_oom',
        'LLMChatter.GroupChatter.PreCacheDepthState',
        'LLMChatter.GroupChatter.PreCacheStateEnable',
        'state',
    ),
    (
        'state_aggro_loss',
        'LLMChatter.GroupChatter.PreCacheDepthState',
        'LLMChatter.GroupChatter.PreCacheStateEnable',
        'state',
    ),
    (
        'combat_pull',
        'LLMChatter.GroupChatter.PreCacheDepthCombat',
        'LLMChatter.GroupChatter.PreCacheCombatEnable',
        'combat',
    ),
    (
        'spell_support',
        'LLMChatter.GroupChatter.PreCacheDepthSpell',
        'LLMChatter.GroupChatter.PreCacheSpellEnable',
        'spell',
    ),
    (
        'spell_offensive',
        'LLMChatter.GroupChatter.PreCacheDepthSpell',
        'LLMChatter.GroupChatter.PreCacheSpellEnable',
        'spell_offensive',
    ),
]

# Classes that don't use mana — Warrior (1),
# Rogue (4), Death Knight (6).  OOM callouts
# make no sense for these classes.
_NON_MANA_CLASS_IDS = {1, 4, 6}

# Map category to state_type for state prompts
_STATE_TYPE_MAP = {
    'state_low_health': 'low_health',
    'state_oom': 'oom',
    'state_aggro_loss': 'aggro_loss',
}


def _run_cache_hygiene(db):
    """Expire stale rows and purge old used/expired
    rows. Cheap -- three simple queries."""
    cursor = db.cursor()

    # Expire stale ready rows
    cursor.execute(
        "UPDATE llm_group_cached_responses "
        "SET status = 'expired' "
        "WHERE status = 'ready' "
        "AND expires_at IS NOT NULL "
        "AND expires_at < NOW()"
    )

    # Purge used rows older than 1 hour
    cursor.execute(
        "DELETE FROM llm_group_cached_responses "
        "WHERE status = 'used' "
        "AND used_at < DATE_SUB(NOW(), "
        "INTERVAL 1 HOUR)"
    )

    # Purge expired rows older than 1 hour
    cursor.execute(
        "DELETE FROM llm_group_cached_responses "
        "WHERE status = 'expired' "
        "AND created_at < DATE_SUB(NOW(), "
        "INTERVAL 1 HOUR)"
    )

    db.commit()


def _get_active_bots(db):
    """Get all bots with active group traits.

    Returns list of dicts with group_id, bot_guid,
    bot_name, trait1, trait2, trait3, role.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT DISTINCT group_id, bot_guid, "
        "bot_name, trait1, trait2, trait3, role "
        "FROM llm_group_bot_traits"
    )
    return cursor.fetchall()


def _get_bot_race_class(db, bot_guid):
    """Look up race and class names for a bot.

    Returns (race_name, class_name, level, class_id)
    or None if not found.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT race, class, level "
        "FROM characters WHERE guid = %s",
        (int(bot_guid),)
    )
    row = cursor.fetchone()
    if not row:
        return None

    class_id = int(row['class'])
    race_name = RACE_NAMES.get(
        int(row['race']), 'Unknown'
    )
    class_name = CLASS_NAMES.get(
        class_id, 'Adventurer'
    )
    level = int(row['level'])
    return (race_name, class_name, level, class_id)


def _get_ready_count(db, group_id, bot_guid, cat):
    """Count ready (non-expired) cached responses
    for a specific bot+category."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) "
        "FROM llm_group_cached_responses "
        "WHERE group_id = %s "
        "AND bot_guid = %s "
        "AND event_category = %s "
        "AND status = 'ready' "
        "AND (expires_at IS NULL "
        "     OR expires_at > NOW())",
        (int(group_id), int(bot_guid), cat)
    )
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def _get_recent_cached(db, group_id, bot_guid, cat):
    """Fetch last 3 cached messages for
    anti-repetition context."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT message "
        "FROM llm_group_cached_responses "
        "WHERE group_id = %s "
        "AND bot_guid = %s "
        "AND event_category = %s "
        "ORDER BY created_at DESC LIMIT 3",
        (int(group_id), int(bot_guid), cat)
    )
    rows = cursor.fetchall()
    return [r[0] for r in rows if r[0]]


def _build_prompt(
    cat, prompt_type, bot_name, race, class_name,
    level, traits, mood, role, recent_cached,
):
    """Dispatch to the correct prompt builder."""
    if prompt_type == 'state':
        state_type = _STATE_TYPE_MAP.get(cat)
        return build_precache_state_prompt(
            state_type, bot_name, race,
            class_name, level, traits, mood,
            role=role, recent_cached=recent_cached,
        )
    elif prompt_type == 'combat':
        return build_precache_combat_pull_prompt(
            bot_name, race, class_name, level,
            traits, mood,
            role=role, recent_cached=recent_cached,
        )
    elif prompt_type == 'spell':
        return build_precache_spell_support_prompt(
            bot_name, race, class_name, level,
            traits, mood,
            role=role, recent_cached=recent_cached,
        )
    elif prompt_type == 'spell_offensive':
        return build_precache_spell_offensive_prompt(
            bot_name, race, class_name, level,
            traits, mood,
            role=role, recent_cached=recent_cached,
        )
    return None


def _insert_cached_response(
    db, group_id, bot_guid, cat,
    message, emote, ttl_seconds,
):
    """Insert a generated response into the cache."""
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO llm_group_cached_responses "
        "(group_id, bot_guid, event_category, "
        "message, emote, status, expires_at) "
        "VALUES (%s, %s, %s, %s, %s, 'ready', "
        "DATE_ADD(NOW(), INTERVAL %s SECOND))",
        (
            int(group_id), int(bot_guid), cat,
            message, emote, int(ttl_seconds),
        )
    )
    db.commit()


def refill_precache_pool(db, client, config):
    """Background refill of pre-cached responses.

    Called periodically from the bridge main loop.
    Generates LLM responses for combat-time events
    so C++ can consume them instantly.
    """
    # Step 1: Cache hygiene
    _run_cache_hygiene(db)

    # Step 2: Read config
    max_per_loop = int(config.get(
        'LLMChatter.GroupChatter.'
        'PreCacheGeneratePerLoop', 3
    ))
    ttl_seconds = int(config.get(
        'LLMChatter.GroupChatter.'
        'PreCacheTTLSeconds', 3600
    ))

    # Step 3: Get active bots
    bots = _get_active_bots(db)
    if not bots:
        return

    generated = 0

    # Step 4: Iterate bots and categories
    for bot_row in bots:
        if generated >= max_per_loop:
            break

        group_id = int(bot_row['group_id'])
        bot_guid = int(bot_row['bot_guid'])
        bot_name = bot_row['bot_name']

        # Build traits list
        traits = []
        for key in ('trait1', 'trait2', 'trait3'):
            val = bot_row.get(key)
            if val:
                traits.append(val)

        role = bot_row.get('role')

        # Look up race/class/level/class_id
        char_info = _get_bot_race_class(
            db, bot_guid
        )
        if not char_info:
            continue
        race, class_name, level, class_id = char_info

        # Get mood
        mood = get_bot_mood_label(
            group_id, bot_guid
        )

        # Check each category in priority order
        for (
            cat, depth_key, enable_key, prompt_type
        ) in _CATEGORIES:
            if generated >= max_per_loop:
                break

            # Check if category is enabled
            enabled = config.get(
                enable_key, '1'
            ) == '1'
            if not enabled:
                continue

            # Skip OOM for non-mana classes
            # (Warrior, Rogue, Death Knight).
            # C++ already filters live OOM events
            # via GetMaxPower(POWER_MANA) > 0, but
            # pre-cache runs without that context.
            if (
                cat == 'state_oom'
                and class_id in _NON_MANA_CLASS_IDS
            ):
                continue

            # Check depth
            target_depth = int(
                config.get(depth_key, 2)
            )
            current = _get_ready_count(
                db, group_id, bot_guid, cat
            )
            if current >= target_depth:
                continue

            # Get anti-repetition context
            recent_cached = _get_recent_cached(
                db, group_id, bot_guid, cat
            )

            # Build prompt
            prompt = _build_prompt(
                cat, prompt_type, bot_name,
                race, class_name, level, traits,
                mood, role, recent_cached,
            )
            if not prompt:
                continue

            # Call LLM
            response = call_llm(
                client, prompt, config,
                max_tokens_override=60,
                context=(
                    f"precache:{cat}"
                    f":{bot_name}"
                ),
                label='precache',
            )
            if not response:
                continue

            # Parse structured JSON response
            parsed = parse_single_response(response)
            message = strip_speaker_prefix(
                parsed['message'], bot_name
            )
            message = cleanup_message(
                message,
                action=parsed.get('action'),
            )
            if not message:
                continue
            if len(message) > 255:
                message = message[:252] + "..."

            # Pick emote
            emote = (
                parsed.get('emote')
                or pick_emote_for_statement(message)
            )

            # Insert into cache
            _insert_cached_response(
                db, group_id, bot_guid, cat,
                message, emote, ttl_seconds,
            )

            generated += 1
