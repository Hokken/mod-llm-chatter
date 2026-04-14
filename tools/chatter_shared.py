"""
Chatter Shared - Shared utilities, DB, LLM, queries for the LLM Chatter Bridge.

Imports from chatter_constants, chatter_text,
chatter_llm, and chatter_db.
No circular dependencies.
"""

import json
import logging
import os
import random
import re
import sys
import threading
import time
from typing import Optional, Dict, List, Tuple, Any

from chatter_constants import (
    ZONE_LEVELS, ZONE_NAMES,
    CLASS_NAMES, RACE_NAMES,
    RACE_SPEECH_PROFILES, CLASS_SPEECH_MODIFIERS,
    CLASS_ROLE_MAP, ROLE_COMBAT_PERSPECTIVES,
    ZONE_FLAVOR, DUNGEON_FLAVOR,
    ITEM_QUALITY_COLORS, ITEM_QUALITY_NAMES,
    ITEM_CLASS_NAMES, WEAPON_SUBCLASS_NAMES,
    ARMOR_SUBCLASS_NAMES, CLASS_BITMASK,
    MSG_TYPE_PLAIN, MSG_TYPE_QUEST, MSG_TYPE_LOOT,
    MSG_TYPE_QUEST_REWARD, MSG_TYPE_TRADE,
    EMOTE_KEYWORDS,
    EMOTE_LIST_STR,
)
from chatter_text import (
    strip_speaker_prefix,
    parse_single_response,
    _sanitize_action,
    cleanup_message,
    extract_conversation_msg_count,
    repair_json_string,
    _extract_ngrams,
    is_too_similar,
)
from chatter_llm import (
    resolve_model,
    call_llm,
    _get_quick_analyze_client,
    quick_llm_analyze,
)
from chatter_db import (
    zone_cache,
    get_db_connection,
    wait_for_database,
    validate_emote,
    insert_chat_message,
    query_zone_quests,
    query_zone_loot,
    query_zone_mobs,
    query_bot_spells,
    query_item_details,
    query_quest_turnin_npc,
    get_recent_zone_messages,
    get_recent_bot_messages,
    get_character_info_by_name,
    get_character_talents,
)
from talent_catalog import TALENT_CATALOG

logger = logging.getLogger(__name__)


class PromptParts(str):
    """Prompt string with separate system prompt.

    Subclasses str so existing code that treats
    prompts as strings continues to work. The
    system_prompt attribute carries format/rules
    instructions for providers that support system
    messages.
    """
    def __new__(
        cls, user_prompt: str, system_block: str
    ):
        instance = super().__new__(
            cls, user_prompt + system_block
        )
        instance.user_prompt = user_prompt
        instance.system_prompt = system_block
        return instance

    def __add__(self, other):
        if isinstance(other, PromptParts):
            return PromptParts(
                self.user_prompt
                + other.user_prompt,
                self.system_prompt
                or other.system_prompt
            )
        if isinstance(other, str):
            return PromptParts(
                self.user_prompt + other,
                self.system_prompt
            )
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, str):
            return PromptParts(
                other + self.user_prompt,
                self.system_prompt
            )
        return NotImplemented

    def __iadd__(self, other):
        return self.__add__(other)


# N12 decomposition scaffold note:
# chatter_shared.py remains the stable facade.
# Target modules (chatter_text/chatter_llm/chatter_db)
# now exist as skeletons; functions are moved in
# N13-N16 with compatibility re-exports.


# =============================================================================
# GLOBAL MUTABLE STATE
# =============================================================================

# Zone-level transport cooldowns (in-memory, resets on bridge restart)
# Key: zone_id, Value: timestamp of last transport announcement
_zone_transport_cooldowns: Dict[int, float] = {}

# Per-zone delivery pacing for General channel messages.
# Shared between chatter_ambient and chatter_general so
# that player reactions and ambient statements both
# respect the same minimum gap per zone.
# Key: zone_id -> monotonic time of last delivery (or
# the projected future time when a gap is applied).
_zone_last_delivery: Dict[int, float] = {}
_zone_gap_lock = threading.Lock()
_ZONE_GAP_DEFAULT = 15  # seconds


def _evict_zone_delivery_cache() -> None:
    """Remove stale entries from _zone_last_delivery.

    Entries older than 1 hour are irrelevant — no
    meaningful gap enforcement needed after that long.
    Called probabilistically from _zone_delivery_delay
    (~1% of calls) to bound memory growth.
    """
    cutoff = time.monotonic() - 3600
    stale = [
        k for k, v in _zone_last_delivery.items()
        if v < cutoff
    ]
    for k in stale:
        del _zone_last_delivery[k]


def _zone_delivery_delay(zone_id, config) -> float:
    """Return extra delay (seconds) to enforce a
    minimum gap between General messages in a zone.

    Returns 0 if enough time has passed since the
    last delivery in this zone.

    Shared between ambient and player-reaction paths
    so both contribute to and respect the same gap.
    Thread-safe: read-compute-write is under lock.
    """
    # Probabilistic eviction (~1% chance per call)
    if random.random() < 0.01:
        _evict_zone_delivery_cache()

    gap = float(config.get(
        'LLMChatter.GeneralChat.MinZoneGap',
        _ZONE_GAP_DEFAULT
    ))
    with _zone_gap_lock:
        now = time.monotonic()
        last = _zone_last_delivery.get(zone_id, 0)
        elapsed = now - last
        if elapsed >= gap:
            _zone_last_delivery[zone_id] = now
            return 0
        extra = gap - elapsed
        _zone_last_delivery[zone_id] = now + extra
        return extra


# =============================================================================
# INTER-SYSTEM LLM SUBMISSION STAGGER
#
# When two independent systems (e.g. General ambient
# and group idle chatter) both fire LLM calls in the
# same poll cycle, their messages land in the same
# delivery bucket and appear simultaneously in-game.
# This stagger delays the second submission by 1-2x
# the poll interval so delivery falls in a different
# bucket.  The sleep happens inside the worker thread,
# never on the main poll loop.
# =============================================================================
_stagger_lock = threading.Lock()
_last_system_submission_time: float = 0.0


def stagger_if_needed(
    poll_interval: float,
    stagger_min: float = 0.0,
    stagger_max: float = 0.0,
) -> None:
    """If another system submitted an LLM call this
    poll cycle, sleep a random stagger_min–stagger_max
    seconds so messages land in different delivery
    buckets.

    If stagger_min/stagger_max are 0 (or omitted),
    falls back to 1–2x poll_interval.

    Must be called from worker threads only — never
    from the main poll loop.
    """
    global _last_system_submission_time
    with _stagger_lock:
        now = time.monotonic()
        needs_stagger = (
            now - _last_system_submission_time
            < poll_interval
        )
        # Stamp immediately so the next caller in
        # this same cycle also sees a recent stamp.
        _last_system_submission_time = now

    if needs_stagger:
        lo = stagger_min if stagger_min > 0 else (
            poll_interval
        )
        hi = stagger_max if stagger_max > 0 else (
            poll_interval * 2
        )
        delay = random.uniform(lo, hi)
        time.sleep(delay)
        # Re-stamp after the sleep so later callers
        # see the post-stagger time, not the pre-
        # stagger time.
        with _stagger_lock:
            _last_system_submission_time = (
                time.monotonic()
            )


# =============================================================================
# NAME LOOKUPS
def pick_random_max_tokens(config: dict) -> int:
    """Pick a randomized max_tokens for single-
    statement LLM calls. Creates natural length
    variety that the LLM can't override.

    NOT for conversations — those need the full
    token budget for multi-message JSON arrays.

    Distribution:
      30% short (150-200 tokens)
      40% medium (200-300 tokens)
      30% full config value
    """
    full = int(config.get(
        'LLMChatter.MaxTokens', 350
    ))
    roll = random.random()
    if roll < 0.30:
        return random.randint(150, 200)
    elif roll < 0.70:
        return random.randint(200, 300)
    return full


# =============================================================================
def get_zone_name(zone_id: int) -> Optional[str]:
    """Get human-readable zone name from zone ID.

    Returns None when the zone ID is unknown to avoid
    injecting 'zone 123' placeholder text into prompts.
    """
    if zone_id in ZONE_NAMES:
        return ZONE_NAMES[zone_id]
    return None


def get_player_zone(db, player_name):
    """Get the real player's live zone and map from
    the characters table. This is always accurate
    because the game client keeps it updated.
    Bots are always co-located with the player,
    so this is the universal source of truth for
    group zone context.

    Args:
        db: database connection
        player_name: the real player's character name

    Returns (zone_id, map_id) or (0, 0) if not found.
    """
    if not player_name:
        return (0, 0)
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT zone, map
            FROM characters
            WHERE name = %s
        """, (player_name,))
        row = cursor.fetchone()
        if row:
            return (
                int(row.get('zone', 0) or 0),
                int(row.get('map', 0) or 0),
            )
    except Exception:
        logger.error(
            "get_player_zone failed for '%s'",
            player_name, exc_info=True,
        )
    return (0, 0)


def debug_log_zone(
    config: dict,
    context: str,
    bot_name: str,
    zone_id: int,
    map_id: int = 0,
):
    """Log zone context for a grouped bot when
    DebugLog is enabled."""
    if config.get('LLMChatter.DebugLog', '0') != '1':
        return
    zone_name = get_zone_name(zone_id)
    logger.info(
        f"[DEBUG] {context}: {bot_name} "
        f"zone={zone_id} ({zone_name}), "
        f"map={map_id}"
    )


def get_class_name(class_id: int) -> str:
    """Get human-readable class name from class ID."""
    return CLASS_NAMES.get(class_id, "Adventurer")


def get_race_name(race_id: int) -> str:
    """Get human-readable race name from race ID."""
    return RACE_NAMES.get(race_id, "Unknown")


def get_gender_label(gender_id: int) -> str:
    """Get human-readable gender label from gender ID."""
    return 'female' if gender_id == 1 else 'male'


def build_bot_identity(
    bot_name: str,
    bot_race: str,
    bot_class: str,
    gender: str = '',
) -> str:
    """Return an identity prefix for bot prompts.

    Used by emote reaction/observer handlers so both
    share the same "You are X, a Y Z." format.
    """
    if bot_race and bot_class:
        gender_prefix = f"{gender} " if gender else ""
        return (
            f"You are {bot_name}, "
            f"a {gender_prefix}{bot_race} {bot_class}."
        )
    return f"You are {bot_name}."


def build_bot_identity_with_level(
    bot_name: str,
    bot_race: str,
    bot_class: str,
    bot_level,
    gender: str = '',
    suffix: str = ' in World of Warcraft.',
) -> str:
    """Return a leveled identity prefix for bot prompts."""
    gender_prefix = f"{gender} " if gender else ""
    return (
        f"You are {bot_name}, a level "
        f"{bot_level} {gender_prefix}{bot_race} "
        f"{bot_class}{suffix}"
    )


def build_bot_identity_from_dict(
    bot: dict,
    include_level: bool = True,
    suffix: str = ' in World of Warcraft.',
) -> str:
    """Build a standard identity line from a bot dict."""
    gender = bot.get('gender', '')
    if include_level:
        return build_bot_identity_with_level(
            bot['name'],
            bot['race'],
            bot['class'],
            bot['level'],
            gender=gender,
            suffix=suffix,
        )
    return build_bot_identity(
        bot['name'],
        bot['race'],
        bot['class'],
        gender=gender,
    )


def get_chatter_mode(config: dict) -> str:
    """Return 'normal' or 'roleplay' from config."""
    if not config:
        return 'normal'
    mode = config.get('LLMChatter.ChatterMode', 'normal').lower()
    return mode if mode in ('normal', 'roleplay') else 'normal'


def get_distance_unit(config: dict) -> str:
    """Return 'yards' or 'meters' from config."""
    unit = config.get(
        'LLMChatter.DistanceUnit', 'yards').lower()
    return unit if unit in ('yards', 'meters') \
        else 'yards'


def format_distance(yards, config):
    """Format a distance value with the configured
    unit. Input is always in yards (WoW native)."""
    unit = get_distance_unit(config)
    if unit == 'meters':
        return f"{yards * 0.9144:.0f} meters"
    return f"{yards:.0f} yards"


# Module-level race lore chance (set from config at startup)
_race_lore_chance = 0.15

# Module-level race vocabulary chance (set from config)
_race_vocab_chance = 0.15


def set_race_lore_chance(chance_pct: int):
    """Set from config: LLMChatter.RaceLoreChance (0-100)."""
    global _race_lore_chance
    _race_lore_chance = chance_pct / 100.0


def set_race_vocab_chance(chance_pct: int):
    """Set from config: LLMChatter.RaceVocabChance (0-100)."""
    global _race_vocab_chance
    _race_vocab_chance = chance_pct / 100.0


def build_race_class_context(
    race: str, class_name: str,
    actual_role: str = None
) -> str:
    """Build an RP personality fragment for prompts."""
    parts = []
    profile = RACE_SPEECH_PROFILES.get(race)
    if profile:
        traits = profile['traits']
        if isinstance(traits, list):
            traits = random.choice(traits)
        flavor_words = profile['flavor_words']
        words = random.sample(
            flavor_words,
            min(4, len(flavor_words))
        )
        parts.append(
            f"As a {race}, you tend to be {traits}. "
            f"You might occasionally use words like: "
            f"{', '.join(words)} "
            f"but don't force it."
        )
        worldview = profile.get('worldview')
        if worldview:
            parts.append(
                f"Worldview: {worldview}"
            )
        vocab = profile.get('vocabulary')
        if vocab and random.random() < _race_vocab_chance:
            phrase, meaning = random.choice(vocab)
            parts.append(
                f"You may naturally weave in a "
                f"phrase from your native tongue: "
                f'"{phrase}" ({meaning}). '
                f"Use it only if it fits — never "
                f"force it."
            )
        lore = profile.get('lore')
        if lore and random.random() < _race_lore_chance:
            lore_str = ' '.join(lore)
            parts.append(
                f"Lore: {lore_str}"
            )
    modifier = CLASS_SPEECH_MODIFIERS.get(class_name)
    if modifier:
        if isinstance(modifier, list):
            modifier = random.choice(modifier)
        parts.append(f"As a {class_name}, you are {modifier}.")
    role = actual_role or CLASS_ROLE_MAP.get(class_name)
    if role:
        perspective = ROLE_COMBAT_PERSPECTIVES.get(role)
        if perspective:
            parts.append(perspective)
    return " ".join(parts)


def build_race_class_context_parts(
    race: str, class_name: str,
    actual_role: str = None,
    race_count: int = 1,
):
    """Return (per_bot, shared_race, shared_class) strings.

    per_bot: traits line + random class modifier +
        optional vocab (unique per bot — always emitted)
    shared_race: worldview + lore (same for all bots of
        same race — caller deduplicates, emitted once)
    shared_class: fixed role perspective only (same for
        all bots of same class — caller deduplicates)

    race_count: number of bots sharing this race in the
        conversation. Used to compute cumulative lore
        probability 1-(1-p)^n so deduplication does not
        reduce lore frequency vs the old per-bot behaviour.
    """
    per_bot_parts = []
    shared_race_parts = []
    shared_class_parts = []

    profile = RACE_SPEECH_PROFILES.get(race)
    if profile:
        # Per-bot: traits (random choice) + vocab phrase
        traits = profile['traits']
        if isinstance(traits, list):
            traits = random.choice(traits)
        flavor_words = profile['flavor_words']
        words = random.sample(
            flavor_words,
            min(4, len(flavor_words))
        )
        per_bot_parts.append(
            f"As a {race}, you tend to be {traits}. "
            f"You might occasionally use words like: "
            f"{', '.join(words)} "
            f"but don't force it."
        )
        vocab = profile.get('vocabulary')
        if vocab and random.random() < _race_vocab_chance:
            phrase, meaning = random.choice(vocab)
            per_bot_parts.append(
                f"You may naturally weave in a "
                f"phrase from your native tongue: "
                f'"{phrase}" ({meaning}). '
                f"Use it only if it fits — never "
                f"force it."
            )

        # Shared race: worldview + lore
        worldview = profile.get('worldview')
        if worldview:
            shared_race_parts.append(
                f"Worldview: {worldview}"
            )
        lore = profile.get('lore')
        # Cumulative probability: 1-(1-p)^n so dedup
        # doesn't reduce lore frequency vs per-bot rolls.
        lore_p = (
            1.0 - (1.0 - _race_lore_chance) ** race_count
            if race_count > 1
            else _race_lore_chance
        )
        if lore and random.random() < lore_p:
            lore_str = ' '.join(lore)
            shared_race_parts.append(
                f"Lore: {lore_str}"
            )

    # Per-bot: class modifier (random per bot — distinct)
    modifier = CLASS_SPEECH_MODIFIERS.get(class_name)
    if modifier:
        if isinstance(modifier, list):
            modifier = random.choice(modifier)
        per_bot_parts.append(
            f"As a {class_name}, you are {modifier}."
        )

    # Shared class: role perspective only (fixed per role)
    role = actual_role or CLASS_ROLE_MAP.get(class_name)
    if role:
        perspective = ROLE_COMBAT_PERSPECTIVES.get(role)
        if perspective:
            shared_class_parts.append(perspective)

    return (
        " ".join(per_bot_parts),
        " ".join(shared_race_parts),
        " ".join(shared_class_parts),
    )


def build_bot_state_context(extra_data):
    """Build natural-language state description
    from C++ bot_state data in extra_data."""
    if not extra_data:
        return ""
    state = extra_data.get('bot_state')
    if not state or not isinstance(state, dict):
        return ""

    parts = []

    # Real role (replaces CLASS_ROLE_MAP guessing)
    role = state.get('role', '')
    if role:
        role_labels = {
            'tank': 'the tank',
            'healer': 'the healer',
            'melee_dps': 'melee DPS',
            'ranged_dps': 'ranged DPS',
            'dps': 'DPS',
        }
        parts.append(
            f"Your role in this group is "
            f"{role_labels.get(role, role)}."
        )

    # Health
    hp = state.get('health_pct')
    if hp is not None:
        hp = int(hp)
        if hp <= 20:
            parts.append(
                f"You are critically wounded "
                f"({hp}% health)."
            )
        elif hp <= 50:
            parts.append(
                f"You are injured "
                f"({hp}% health)."
            )

    # Mana (skip for non-mana classes: -1 sentinel)
    mp = state.get('mana_pct')
    if mp is not None:
        mp = int(mp)
        if mp >= 0:  # -1 = not a mana user
            if mp <= 15:
                parts.append(
                    f"You are almost out of mana "
                    f"({mp}%)."
                )
            elif mp <= 35:
                parts.append(
                    f"Your mana is getting low "
                    f"({mp}%)."
                )

    # Current target
    target = state.get('target', '')
    if target:
        parts.append(
            f"You are currently fighting "
            f"{target}."
        )

    return ' '.join(parts)


# =============================================================================
# CONFIG & DATABASE
# =============================================================================
def parse_config(config_path: str) -> dict:
    """Parse the WoW-style config file."""
    config = {}
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        sys.exit(1)
    return config


# =============================================================================
# ZONE DATA QUERIES
# =============================================================================
def get_zone_level_range(
    zone_id: int, bot_level: int
) -> Tuple[int, int]:
    """Get level range for a zone, falling back to bot level."""
    if zone_id in ZONE_LEVELS:
        return ZONE_LEVELS[zone_id]
    return (max(1, bot_level - 5), bot_level + 5)


def get_zone_flavor(zone_id: int) -> Optional[str]:
    """Get rich zone flavor text for immersive context."""
    return ZONE_FLAVOR.get(zone_id)


def get_dungeon_flavor(map_id: int) -> Optional[str]:
    """Get dungeon/raid flavor text by map ID."""
    return DUNGEON_FLAVOR.get(map_id)


def get_group_area(db, group_id: int) -> int:
    """Get the current area (subzone) for a group.

    Reads from llm_group_bot_traits — all bots in
    the group share the same area (set by real
    player's OnPlayerUpdateArea hook).

    Returns area_id or 0 if not found.
    """
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT area
            FROM llm_group_bot_traits
            WHERE group_id = %s
            LIMIT 1
        """, (group_id,))
        row = cursor.fetchone()
        if row:
            return int(row.get('area') or 0)
    except Exception:
        logger.error(
            "get_group_area failed for group %s",
            group_id, exc_info=True,
        )
    return 0


# ── Subzone lore (loaded once from JSON) ────────
_subzone_lore: Optional[Dict] = None


def _load_subzone_lore() -> Dict:
    """Load subzone_lore.json once on first access."""
    global _subzone_lore
    if _subzone_lore is not None:
        return _subzone_lore
    lore_path = os.path.join(
        os.path.dirname(__file__),
        "subzone_lore.json",
    )
    try:
        with open(lore_path, "r", encoding="utf-8") as f:
            _subzone_lore = json.load(f)
    except Exception:
        logging.getLogger("chatter").warning(
            "Could not load subzone_lore.json")
        _subzone_lore = {}
    return _subzone_lore


def get_subzone_lore(
    zone_id: int, area_id: int
) -> Optional[str]:
    """Get rich subzone lore description.

    Returns None if area_id equals zone_id (no
    subzone — use zone_flavor instead), or if no
    lore entry exists for this area.
    """
    if not area_id or area_id == zone_id:
        return None
    lore = _load_subzone_lore()
    zones = lore.get("zones", {})
    zdata = zones.get(str(zone_id), {})
    subzones = zdata.get("subzones", {})
    entry = subzones.get(str(area_id))
    if entry and entry.get("description"):
        desc = entry["description"]
        name = entry.get("name", f"area {area_id}")
        zone_name = zdata.get(
            "name", f"zone {zone_id}"
        )
        logger.info(
            f"[LORE] {zone_name} > {name}: "
            f"{desc[:80]}..."
        )
        return desc
    return None


def get_subzone_name(
    zone_id: int, area_id: int
) -> Optional[str]:
    """Get subzone name from subzone_lore.json.

    Returns None if area equals zone or no entry.
    """
    if not area_id or area_id == zone_id:
        return None
    lore = _load_subzone_lore()
    zones = lore.get("zones", {})
    zdata = zones.get(str(zone_id), {})
    subzones = zdata.get("subzones", {})
    entry = subzones.get(str(area_id))
    if entry:
        return entry.get("name")
    return None


def build_zone_metadata(
    zone_name: str = '',
    zone_flavor: str = '',
    subzone_name: str = '',
    subzone_lore: str = '',
    dungeon_name: str = '',
    dungeon_flavor: str = '',
) -> dict:
    """Build zone metadata dict for request logging.

    Returns a dict containing only non-empty string
    values so the log stays compact when data is
    unavailable.
    """
    meta = {}
    if dungeon_name:
        meta['zone_name'] = dungeon_name
    elif zone_name:
        meta['zone_name'] = zone_name
    if dungeon_flavor:
        meta['zone_flavor'] = dungeon_flavor
    elif zone_flavor:
        meta['zone_flavor'] = zone_flavor
    if subzone_name:
        meta['subzone_name'] = subzone_name
    if subzone_lore:
        meta['subzone_lore'] = subzone_lore
    return meta


def format_location_label(
    zone_id: int, area_id: int
) -> str:
    """Format 'Zone > Subzone' label for logging.

    Returns e.g. 'Teldrassil > Dolanaar' or just
    'Teldrassil' if no subzone.
    """
    zone_name = get_zone_name(zone_id)
    sub_name = get_subzone_name(zone_id, area_id)
    if sub_name:
        return f"{zone_name} > {sub_name}"
    return zone_name


# Cache for dungeon boss lists (never changes)
_dungeon_boss_cache = {}


def get_dungeon_bosses(
    db, map_id: int
) -> list:
    """Get boss names for a dungeon/raid map.

    Queries creature + creature_template from
    acore_world. Detects bosses via:
    - rank=3 (raid bosses)
    - CreatureImmunitiesId > 0 AND single spawn
      (named dungeon bosses — immune mobs that
      spawn only once per map are reliably bosses;
      multi-spawn immune mobs like Molten Elementals
      or Haunted Servitors are trash)
    """
    if map_id in _dungeon_boss_cache:
        return _dungeon_boss_cache[map_id]

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT ct.name
            FROM acore_world.creature_template ct
            JOIN acore_world.creature c
                ON c.id1 = ct.entry
            WHERE c.map = %s
                AND (ct.`rank` = 3
                     OR ct.CreatureImmunitiesId > 0)
            GROUP BY ct.entry, ct.name, ct.`rank`
            HAVING ct.`rank` = 3 OR COUNT(*) = 1
            ORDER BY ct.name
        """, (map_id,))
        bosses = [
            row['name']
            for row in cursor.fetchall()
        ]
        _dungeon_boss_cache[map_id] = bosses
        return bosses
    except Exception:
        logger.error(
            "get_dungeon_bosses failed for map %s",
            map_id, exc_info=True,
        )
        _dungeon_boss_cache[map_id] = []
        return []


def can_class_use_item(
    class_name: str, allowable_class: int
) -> bool:
    """Check if a class can use an item based on AllowableClass bitmask."""
    if allowable_class in (-1, 0):
        return True
    class_bit = CLASS_BITMASK.get(class_name, 0)
    if class_bit == 0:
        return True
    return (allowable_class & class_bit) != 0


# =============================================================================
# LINK FORMATTING
# =============================================================================
def format_price(copper: int) -> str:
    """Format copper amount as WoW gold/silver/copper."""
    if not copper or copper <= 0:
        return ""
    gold = copper // 10000
    silver = (copper % 10000) // 100
    cop = copper % 100
    parts = []
    if gold > 0:
        parts.append(f"{gold}g")
    if silver > 0:
        parts.append(f"{silver}s")
    if cop > 0 and gold == 0:
        parts.append(f"{cop}c")
    return " ".join(parts) if parts else ""


def format_quest_link(
    quest_id: int, quest_level: int, quest_name: str
) -> str:
    """Format a clickable quest link for WoW chat."""
    return (
        f"|cFFFFFF00|Hquest:{quest_id}:{quest_level}"
        f"|h[{quest_name}]|h|r"
    )


def format_item_link(
    item_id: int, item_quality: int, item_name: str
) -> str:
    """Format a clickable item link for WoW chat."""
    color = ITEM_QUALITY_COLORS.get(item_quality, "ffffff")
    return (
        f"|c{color}|Hitem:{item_id}:0:0:0:0:0:0:0"
        f"|h[{item_name}]|h|r"
    )


def format_spell_link(
    spell_id: int, spell_name: str
) -> str:
    """Format a clickable spell link for WoW chat."""
    return (
        f"|cff71d5ff|Hspell:{spell_id}"
        f"|h[{spell_name}]|h|r"
    )


def replace_placeholders(
    message: str,
    quest_data: dict = None,
    item_data: dict = None,
    spell_data: dict = None
) -> str:
    """Replace {quest:...}, {item:...}, and {spell:...}
    placeholders with WoW links."""
    result = message

    if quest_data:
        quest_pattern = r'\{quest:[^}]+\}'
        if re.search(quest_pattern, result):
            link = format_quest_link(
                quest_data['quest_id'],
                quest_data.get('quest_level', 1),
                quest_data['quest_name']
            )
            result = re.sub(quest_pattern, link, result)

    if item_data:
        item_pattern = r'\{item:[^}]+\}'
        link = format_item_link(
            item_data['item_id'],
            item_data.get('item_quality', 2),
            item_data['item_name']
        )
        if re.search(item_pattern, result):
            result = re.sub(item_pattern, link, result)
        else:
            bracket_pattern = r'\[([A-Z][a-zA-Z\' ]{2,25})\]'
            if re.search(bracket_pattern, result):
                result = re.sub(
                    bracket_pattern, link, result, count=1
                )

    if spell_data:
        spell_pattern = r'\{spell:[^}]+\}'
        if re.search(spell_pattern, result):
            link = format_spell_link(
                spell_data['spell_id'],
                spell_data['spell_name']
            )
            result = re.sub(spell_pattern, link, result)

    return result


# Module-level action chance (set from config at startup)
_action_chance = 0.10
_action_disabled = True

# Module-level emote chance (set from config at startup)
_emote_chance = 0.50

# Module-level response language (set from config at startup).
# Empty string = English default (no extra instruction emitted).
_language = ""

# Human-readable label used in the prompt rule.
_LANGUAGE_LABELS = {
    "FR": "French",
    "GB": "English",
    "US": "English",
}


def set_language(code: str) -> None:
    """Set from config: LLMChatter.Language (FR | GB | US).

    Stored as the canonical label ('French' / 'English').
    Empty / unknown / English values are stored as "" so
    no extra instruction is emitted (saves tokens on the
    default English case).
    """
    global _language
    if not code:
        _language = ""
        return
    label = _LANGUAGE_LABELS.get(code.strip().upper(), "")
    # English is the implicit default — emit nothing.
    _language = "" if label in ("", "English") else label


def get_language_rule() -> str:
    """Return the language instruction line, or empty.

    Used by JSON instruction builders to force the LLM
    to respond in the server's configured language while
    preserving WoW proper nouns in English.
    """
    if not _language:
        return ""
    return (
        f"\nLanguage: Write EVERY field in {_language} — "
        "the \"message\" field AND the \"action\" "
        "narrator field must both be fully in "
        f"{_language}. Do not mix languages. "
        "Exception: keep WoW proper nouns (zone, "
        "subzone, creature, NPC, item, spell, quest, "
        "and character names) in English exactly as "
        "written — never translate them."
    )


def set_emote_chance(chance_pct: int):
    """Set from config: LLMChatter.EmoteChance (0-100).

    Controls how often the emote list is included in
    prompts. When skipped, the model returns null for
    emote, saving ~500 tokens per call.
    """
    global _emote_chance
    _emote_chance = chance_pct / 100.0


def set_action_chance(chance_pct: int, mode: str = 'roleplay'):
    """Set from config: LLMChatter.ActionChance (0-100).

    Actions (narrator comments like *leans on staff*) are
    RP-mode only. In normal mode, get_action_chance()
    always returns 0.0.
    """
    global _action_chance, _action_disabled
    _action_chance = chance_pct / 100.0
    _action_disabled = (mode != 'roleplay')


def get_action_chance() -> float:
    """Return the configured action chance (0.0-1.0).

    Returns 0.0 in normal mode (actions are RP-only).
    """
    if _action_disabled:
        return 0.0
    return _action_chance


def should_include_action() -> bool:
    """Roll against ActionChance; return True if a narrator action should be kept."""
    return random.random() < get_action_chance()


def strip_conversation_actions(
    messages: List[dict],
    label: str = '',
) -> None:
    """Strip actions per-message via ActionChance RNG.

    Each message gets an independent roll. Modifies
    the list in place. Logs before/after to the
    request log when enabled.
    """
    # Snapshot before stripping
    original = [
        {'name': m.get('name', ''),
         'action': m.get('action')}
        for m in messages
    ]

    for msg in messages:
        if (msg.get('action')
                and not should_include_action()):
            msg['action'] = None

    # Log before/after if any action was present
    if any(o['action'] for o in original):
        try:
            from chatter_request_logger import (
                log_delivered_messages,
            )
            log_delivered_messages(
                label, original, messages,
            )
        except Exception:
            pass


def append_json_instruction(
    prompt: str, allow_action: bool = True,
    skip_emote: bool = False,
    skip_action_rng: bool = False,
) -> str:
    """Append structured JSON response instruction
    to a prompt.

    Tells the LLM to respond with JSON containing
    message, emote, and optionally action fields.
    skip_emote=True omits the emote list (saves
    ~200 tokens for General channel prompts where
    emotes are not displayed).
    skip_action_rng=True bypasses the pre-call RNG
    so the caller can apply post-parse stripping
    instead (used by General conversation paths).
    """
    # Apply ActionChance RNG: allow_action=True means
    # "eligible for action" — the RNG decides.
    # allow_action=False means "never include action"
    # (e.g. raid channel).
    # skip_action_rng=True defers RNG to post-parse.
    if (allow_action and not skip_action_rng
            and random.random() >= _action_chance):
        allow_action = False
    action_desc = ""
    if allow_action:
        action_desc = (
            '"action": a short physical narration '
            '(max 8 words). '
            "NEVER put {item:}, {quest:}, or "
            "{spell:} placeholders in action. "
            "NEVER include your own name in the "
            "action — the client already shows it.\n"
        )
    else:
        action_desc = (
            '"action": null (do not include an '
            "action for this response)\n"
            "IMPORTANT: do NOT put *narrator text* "
            "or *physical actions* inside the "
            '"message" field.\n'
        )

    # Skip emote list if explicitly requested OR
    # if EmoteChance RNG says no
    if skip_emote or random.random() >= _emote_chance:
        emote_line = '  "emote": null,\n'
    else:
        emote_line = (
            f'  "emote": one of [{EMOTE_LIST_STR}] '
            "or null,\n"
        )

    lang_rule = get_language_rule()
    # Also inject the language rule into the user
    # prompt so split-system providers (Anthropic)
    # see it close to generation — system prompts
    # lose steering weight against English few-shot
    # content that sits inside the user prompt.
    if lang_rule:
        prompt = prompt + lang_rule
    block = (
        "\n\nRESPONSE FORMAT: You MUST respond with "
        "ONLY valid JSON. No other text.\n"
        "{\n"
        '  "message": "your spoken words here",\n'
        f"{emote_line}"
        f"  {action_desc}"
        "}\n"
        "Rules: double quotes only, no trailing "
        "commas, no code fences, no markdown.\n"
        "CRITICAL: Follow the Length instruction "
        "in the prompt exactly — never exceed the "
        "stated character limit."
        f"{lang_rule}"
    )
    return PromptParts(prompt, block)


def append_conversation_json_instruction(
    prompt: str,
    bot_names: List[str],
    msg_count: int,
    allow_action: bool = True,
) -> str:
    """Append conversation JSON array instruction.

    Conversation prompts return an array where each
    item has speaker/message/emote/action fields.
    """
    # When actions are enabled, every message MUST
    # include an action — strip_conversation_actions()
    # enforces ActionChance per-message post-parse.
    # _action_disabled=True (non-RP mode) disables all.
    action_speakers: List[str] = (
        list(bot_names)
        if (allow_action and bot_names and not _action_disabled)
        else []
    )

    _no_narrator = (
        "IMPORTANT: do NOT put *narrator text* "
        "or *physical actions* inside any "
        "\"message\" field."
    )
    if action_speakers:
        action_text = (
            "Actions: EVERY message MUST include a "
            "non-null \"action\" field — a 2-5 word "
            "physical narration (e.g. \"leans against "
            "the wall\"). "
            "NEVER include the speaker's own name in "
            "the action — the client already shows it. "
            "NEVER put {item:}, {quest:}, or "
            "{spell:} placeholders in the action "
            f"field — those belong in message only. "
            f"{_no_narrator}"
        )
    else:
        action_text = (
            f"Actions: Set \"action\" to null for "
            f"ALL messages in this response. "
            f"{_no_narrator}"
        )

    # EmoteChance RNG for conversations
    if random.random() < _emote_chance:
        emote_rule = (
            "Emotes: Each message may include an "
            f"optional \"emote\" field (one of: "
            f"{EMOTE_LIST_STR}). Pick an emote "
            "that fits the mood, or use null.\n"
        )
        emote_ex = '"emote": "talk"'
    else:
        emote_rule = (
            "Emotes: Set the \"emote\" field to "
            "null for all messages.\n"
        )
        emote_ex = '"emote": null'

    action_ex = (
        '"action": "..."' if action_speakers
        else '"action": null'
    )
    example_msgs = ',\n  '.join(
        [
            f'{{"speaker": "{name}", "message": "...", '
            f'{emote_ex}, '
            f'{action_ex}}}'
            for name in bot_names
        ]
    )

    lang_rule = get_language_rule()
    if lang_rule:
        prompt = prompt + lang_rule
    block = (
        f"\n\n{emote_rule}"
        f"{action_text}\n"
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, no code fences.\n"
        f"\nRespond with EXACTLY {msg_count} messages in JSON:\n"
        "[\n"
        f"  {example_msgs}\n"
        "]\n"
        "ONLY the JSON array, nothing else.\n"
        "CRITICAL: Follow the Length instruction "
        "in the prompt exactly — never exceed the "
        "stated character limit."
        f"{lang_rule}"
    )
    return PromptParts(prompt, block)


# =============================================================================
# MESSAGE TYPE SELECTION
# =============================================================================
def select_message_type() -> str:
    """Randomly select a message type based on distribution."""
    roll = random.randint(1, 100)
    if roll <= MSG_TYPE_PLAIN:
        return "plain"
    elif roll <= MSG_TYPE_QUEST:
        return "quest"
    elif roll <= MSG_TYPE_LOOT:
        return "loot"
    elif roll <= MSG_TYPE_QUEST_REWARD:
        return "quest_reward"
    elif roll <= MSG_TYPE_TRADE:
        return "trade"
    else:
        return "spell"


# =============================================================================
# DYNAMIC DELAYS
# =============================================================================
def calculate_dynamic_delay(
    message_length: int,
    config: dict,
    prev_message_length: int = 0,
    responsive: bool = False,
) -> float:
    """Calculate a realistic delay based on message
    length.

    When responsive=True (player message replies),
    uses faster timing: no distraction, shorter
    reaction/typing, lower floor. Bots respond
    promptly when spoken to directly.
    """
    min_delay = (
        int(config.get('LLMChatter.MessageDelayMin', 1000))
        / 1000.0
    )
    max_delay = (
        int(config.get('LLMChatter.MessageDelayMax', 30000))
        / 1000.0
    )

    if responsive:
        # Player is waiting — fast reply.  The LLM
        # already took several seconds ("thinking"),
        # so keep the typing simulation short.
        return random.uniform(4.0, 8.0)

    # Ambient/idle — full simulation
    reading_time = (
        prev_message_length / random.uniform(4.0, 9.0)
        if prev_message_length > 0 else 0
    )

    reaction_time = random.uniform(1.0, 4.0)

    if message_length < 15:
        typing_time = random.uniform(1.0, 3.0)
    elif message_length < 40:
        typing_time = message_length / random.uniform(3.0, 6.0)
    elif message_length < 80:
        typing_time = message_length / random.uniform(2.5, 5.0)
    else:
        typing_time = message_length / random.uniform(2.0, 4.0)

    distraction_roll = random.random()
    if distraction_roll < 0.4:
        distraction = random.uniform(0, 3.0)
    elif distraction_roll < 0.85:
        distraction = random.uniform(2.0, 8.0)
    else:
        distraction = random.uniform(6.0, 18.0)

    total_delay = (
        reading_time + reaction_time + typing_time + distraction
    )

    try:
        pacing = float(config.get(
            'LLMChatter.ConversationPacing', 1.0
        ))
    except (ValueError, TypeError):
        pacing = 1.0
    pacing = max(0.1, min(pacing, 5.0))
    total_delay *= pacing

    minimum_for_length = (message_length / 4.0) + 2.0
    total_delay = max(total_delay, minimum_for_length)
    total_delay = max(total_delay, min_delay, 4.0)
    total_delay *= random.uniform(0.85, 1.20)

    return min(total_delay, max_delay)


# =============================================================================
# LLM INTERACTION
# =============================================================================
def get_effective_speaker_cooldown(
    config: dict, num_bots: int = 1
) -> int:
    """Compute per-bot speaker cooldown scaled by
    group size.

    Formula: max(60, min(base, base * num_bots / 5))
    where 5 = reference full party size.
    """
    base = int(config.get(
        'LLMChatter.BotSpeakerCooldownSeconds', 900
    ))
    return max(60, min(base, base * num_bots // 5))


def run_single_reaction(
    db,
    client: Any,
    config: dict,
    *,
    prompt: str,
    speaker_name: str,
    bot_guid: int,
    channel: str,
    delay_seconds: float,
    event_id: int = None,
    sequence: int = 0,
    allow_emote_fallback: bool = True,
    max_tokens_override: int = None,
    context: str = '',
    message_transform: Any = None,
    metadata: dict = None,
    label: str = 'single_reaction',
    num_bots: int = 1,
    bypass_speaker_cooldown: bool = True,
) -> Dict[str, Any]:
    """Run shared single-message reaction pipeline.

    Flow:
    0. per-bot speaker cooldown gate
    1. call_llm
    2. parse_single_response
    3. strip_speaker_prefix
    4. cleanup_message
    5. length clamp
    6. optional emote fallback
    7. insert_chat_message

    Returns:
      {'ok': bool, 'message': str|None, 'emote': str|None,
       'error_reason': str|None}
    """
    # ---- per-bot speaker cooldown ----
    if not bypass_speaker_cooldown:
        cooldown = get_effective_speaker_cooldown(
            config, num_bots
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM llm_chatter_messages
            WHERE bot_guid = %s
              AND delivered = 1
              AND delivered_at > DATE_SUB(
                  NOW(), INTERVAL %s SECOND
              )
        """, (bot_guid, cooldown))
        row = cursor.fetchone()
        cursor.close()
        if row and row['cnt'] > 0:
            return {
                'ok': False,
                'message': None,
                'emote': None,
                'error_reason': 'speaker_cooldown',
            }

    # Randomize token budget for natural length
    # variety unless caller specified an override.
    if max_tokens_override is None:
        max_tokens_override = pick_random_max_tokens(
            config
        )
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens_override,
        context=context,
        label=label,
        metadata=metadata,
    )
    if not response:
        return {
            'ok': False,
            'message': None,
            'emote': None,
            'error_reason': 'no_response',
        }

    parsed = parse_single_response(response)
    message = strip_speaker_prefix(
        parsed['message'], speaker_name
    )
    message = cleanup_message(
        message, action=parsed.get('action')
    )
    if not message:
        return {
            'ok': False,
            'message': None,
            'emote': None,
            'error_reason': 'empty_message',
        }

    if callable(message_transform):
        try:
            transformed = message_transform(message)
            if isinstance(transformed, str):
                message = transformed
        except Exception:
            return {
                'ok': False,
                'message': None,
                'emote': None,
                'error_reason': 'transform_error',
            }

    if len(message) > 255:
        message = message[:252] + "..."

    emote = parsed.get('emote')

    try:
        insert_chat_message(
            db,
            bot_guid,
            speaker_name,
            message,
            channel=channel,
            delay_seconds=delay_seconds,
            event_id=event_id,
            sequence=sequence,
            emote=emote,
        )
    except Exception:
        logger.error(
            "insert_chat_message failed for %s",
            speaker_name, exc_info=True,
        )
        return {
            'ok': False,
            'message': message,
            'emote': emote,
            'error_reason': 'insert_failed',
        }

    return {
        'ok': True,
        'message': message,
        'emote': emote,
        'error_reason': None,
    }


def find_addressed_bot(
    message: str, bot_names,
    client=None, config=None,
    chat_history=""
) -> dict:
    """Check if a player message addresses a specific
    bot by name. Returns a dict with:
      - 'bot': matched bot name or None
      - 'multi_addressed': True if the message is
        directed at multiple bots

    Three-pass approach for name hint:
    1. Exact whole-word match (case-insensitive)
    2. Fuzzy fallback for names >= 4 chars
    Then LLM analysis confirms the hint and assesses
    whether multiple bots are addressed.
    """
    no_match = {
        'bot': None,
        'multi_addressed': False,
    }
    if not message or not bot_names:
        return no_match
    msg_lower = message.lower()

    # Pass 1: exact whole-word match
    name_hint = None
    for name in bot_names:
        if not name:
            continue
        name_lower = name.lower()
        idx = msg_lower.find(name_lower)
        while idx != -1:
            left_ok = (
                idx == 0
                or not msg_lower[idx - 1].isalpha()
            )
            end = idx + len(name_lower)
            right_ok = (
                end >= len(msg_lower)
                or not msg_lower[end].isalpha()
            )
            if left_ok and right_ok:
                name_hint = name
                break
            idx = msg_lower.find(
                name_lower, idx + 1
            )
        if name_hint:
            break

    # Pass 2: fuzzy match on words (names >= 4 chars)
    if not name_hint:
        words = re.split(r'[^a-zA-Z]+', message)
        words = [w for w in words if len(w) >= 4]
        for name in bot_names:
            if not name or len(name) < 4:
                continue
            for word in words:
                if fuzzy_name_match(word, name):
                    name_hint = name
                    break
            if name_hint:
                break

    # If no LLM client, return name hint only
    if not client or not config:
        return {
            'bot': name_hint,
            'multi_addressed': False,
        }

    # LLM analysis for bot identification and
    # multi_addressed assessment
    names_str = ', '.join(
        n for n in bot_names if n
    )
    hint_line = ""
    if name_hint:
        hint_line = (
            f"\nName matching suggests: {name_hint}"
            f"\nUse this as a strong hint but you "
            f"may override if context clearly "
            f"indicates otherwise."
        )
    history_block = ""
    if chat_history:
        history_block = (
            f"Recent chat:\n{chat_history}\n\n"
        )
    prompt = (
        f"{history_block}"
        f"The player just said:\n"
        f"\"{message}\"\n\n"
        f"Available bots: {names_str}\n"
        f"{hint_line}\n"
        f"Respond with ONLY a JSON object "
        f"(no markdown, no explanation):\n"
        f'{{"bot": "BotName", '
        f'"multi_addressed": true}}\n\n'
        f"Rules:\n"
        f'- "bot": the single bot most likely '
        f"being addressed, or null if the "
        f"message is general/undirected.\n"
        f'- "multi_addressed": true if the '
        f"player is addressing or expecting "
        f"responses from multiple bots. "
        f"Consider:\n"
        f"  * Plural pronouns (you both, you "
        f"all, everyone, guys)\n"
        f"  * Group-directed questions (are we "
        f"ready?, what's the plan?)\n"
        f"  * Multiple bot names mentioned\n"
        f"  * Questions inviting multiple "
        f"perspectives\n"
        f"  * General observations that could "
        f"prompt group discussion\n"
        f'- If only one bot is addressed, '
        f'"multi_addressed" must be false.'
    )

    try:
        result = quick_llm_analyze(
            client, config, prompt, max_tokens=60,
            label='find_addressed_bot',
        )
    except Exception:
        logger.error(
            "find_addressed_bot LLM call failed",
            exc_info=True,
        )
        return {
            'bot': name_hint,
            'multi_addressed': False,
        }

    if not result:
        return {
            'bot': name_hint,
            'multi_addressed': False,
        }

    # Parse JSON response
    result = result.strip()
    # Strip markdown fences if present
    if result.startswith('```'):
        result = re.sub(
            r'^```[a-z]*\s*', '', result
        )
        result = re.sub(r'\s*```$', '', result)
    try:
        parsed = json.loads(result)
    except (json.JSONDecodeError, ValueError):
        return {
            'bot': name_hint,
            'multi_addressed': False,
        }

    # Extract bot name
    raw_bot = parsed.get('bot')
    matched_bot = None
    if raw_bot and isinstance(raw_bot, str):
        raw_bot = raw_bot.strip().strip(
            '"'
        ).strip("'")
        if raw_bot.lower() == 'null':
            raw_bot = None

    if raw_bot:
        # Exact match against bot names
        for name in bot_names:
            if not name:
                continue
            if name.lower() == raw_bot.lower():
                matched_bot = name
                break
        # Fuzzy match fallback
        if not matched_bot:
            for name in bot_names:
                if not name:
                    continue
                if fuzzy_name_match(raw_bot, name):
                    matched_bot = name
                    break

    # If LLM didn't match, keep name hint
    if not matched_bot and name_hint:
        matched_bot = name_hint

    raw_multi = parsed.get(
        'multi_addressed', False
    )
    if isinstance(raw_multi, str):
        multi = raw_multi.lower() not in (
            'false', '0', 'no', ''
        )
    else:
        multi = bool(raw_multi)

    return {
        'bot': matched_bot,
        'multi_addressed': multi,
    }


# =============================================================================
# RESPONSE PARSING
# =============================================================================
def fuzzy_name_match(
    speaker: str, expected_name: str, max_distance: int = 2
) -> bool:
    """Check if speaker matches expected_name with tolerance."""
    s1 = speaker.lower()
    s2 = expected_name.lower()

    if s1 == s2:
        return True

    if abs(len(s1) - len(s2)) > max_distance:
        return False

    differences = 0
    i, j = 0, 0
    while i < len(s1) and j < len(s2):
        if s1[i] != s2[j]:
            differences += 1
            if len(s1) > len(s2):
                i += 1
            elif len(s2) > len(s1):
                j += 1
            else:
                i += 1
                j += 1
        else:
            i += 1
            j += 1

    differences += (len(s1) - i) + (len(s2) - j)
    return differences <= max_distance


def parse_conversation_response(
    response: str, bot_names: List[str]
) -> list:
    """Parse conversation JSON response into message list."""
    try:
        cleaned = response.strip()
        cleaned = re.sub(
            r'```(?:json)?', '', cleaned,
            flags=re.IGNORECASE
        ).strip()
        json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if json_match:
            try:
                messages = json.loads(json_match.group())
            except json.JSONDecodeError:
                start = cleaned.find('[')
                end = cleaned.rfind(']')
                if start != -1 and end != -1 and end > start:
                    messages = json.loads(
                        cleaned[start:end + 1]
                    )
                else:
                    raise
            result = []
            for msg in messages:
                speaker = msg.get('speaker', '').strip()
                message = msg.get('message', '').strip()
                if speaker and message:
                    matched_name = None
                    for bot_name in bot_names:
                        if fuzzy_name_match(speaker, bot_name):
                            matched_name = bot_name
                            break
                    if matched_name:
                        entry = {
                            'name': matched_name,
                            'message': message,
                        }
                        # Extract optional emote
                        raw_emote = msg.get('emote')
                        if raw_emote:
                            entry['emote'] = (
                                validate_emote(raw_emote)
                            )
                        # Extract optional action
                        raw_action = msg.get('action')
                        action = _sanitize_action(
                            raw_action
                        )
                        if action:
                            entry['action'] = action
                        result.append(entry)
            return result
    except json.JSONDecodeError:
        pass
    return []


def parse_extra_data(
    raw_data: str, event_id=None, event_type=None
) -> dict:
    """Parse extra_data JSON with repair attempts."""
    if not raw_data:
        return {}

    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        pass

    repaired = repair_json_string(raw_data)
    try:
        result = json.loads(repaired)
        return result
    except json.JSONDecodeError:
        pass
    except Exception:
        logger.error(
            "parse_extra_data unexpected error",
            exc_info=True,
        )

    return {}


# =============================================================================
# EMOTE HELPERS
# =============================================================================
def pick_emote_for_statement(message: str) -> Optional[str]:
    """Keyword-match an emote for a plain-text statement.

    90% RNG gate — most messages attempt emote matching.
    Returns a valid emote name or None.
    """
    if not message or random.random() > 0.90:
        return None
    msg_lower = message.lower()
    for keyword, emote in EMOTE_KEYWORDS.items():
        if keyword in msg_lower:
            return emote
    return None


# =============================================================================
# ITEM LINK DETECTION (for party chat item reactions)
# =============================================================================
_ITEM_LINK_RE = re.compile(
    r'\|Hitem:(\d+):[^|]*\|h\[([^\]]+)\]\|h\|r'
)


def detect_item_links(
    message: str,
) -> List[Tuple[int, str]]:
    """Extract (item_entry, item_name) from WoW item
    links in a chat message.
    """
    return [
        (int(m.group(1)), m.group(2))
        for m in _ITEM_LINK_RE.finditer(message)
    ]


def format_item_context(
    items_info: List[dict],
    bot_class: str,
) -> str:
    """Build human-readable item context for a prompt.

    Includes quality, type, level, and whether the
    bot's class can equip it.
    """
    parts = []
    for item in items_info:
        quality = ITEM_QUALITY_NAMES.get(
            item.get('Quality', 1), 'Common'
        )
        item_class = item.get('item_class', 0)
        item_sub = item.get('item_subclass', 0)

        # Subclass-level type name for weapons/armor
        if item_class == 2:
            type_name = WEAPON_SUBCLASS_NAMES.get(
                item_sub, 'Weapon'
            )
        elif item_class == 4:
            type_name = ARMOR_SUBCLASS_NAMES.get(
                item_sub, 'Armor'
            )
        else:
            type_name = ITEM_CLASS_NAMES.get(
                item_class, 'Item'
            )

        name = item.get('name', 'Unknown')
        ilvl = item.get('ItemLevel', 0)
        req_lvl = item.get('RequiredLevel', 0)

        desc = f"{name} ({quality} {type_name}"
        if ilvl:
            desc += f", iLvl {ilvl}"
        if req_lvl:
            desc += f", req level {req_lvl}"
        desc += ")"

        # Always show equipability for weapons/armor
        allowable = item.get('AllowableClass', -1)
        if item_class in (2, 4):
            if allowable and allowable != -1:
                can_use = can_class_use_item(
                    bot_class, allowable
                )
            else:
                can_use = True
            if can_use:
                desc += (
                    f" — {bot_class} CAN equip"
                )
            else:
                desc += (
                    f" — {bot_class} CANNOT equip"
                )

        # Add stat highlights
        stats = []
        if item.get('armor'):
            stats.append(
                f"{item['armor']} armor"
            )
        if (
            item.get('dmg_min1')
            and item.get('dmg_max1')
        ):
            stats.append(
                f"{item['dmg_min1']}-"
                f"{item['dmg_max1']} damage"
            )
        if stats:
            desc += f" [{', '.join(stats)}]"

        parts.append(desc)

    return "Items linked: " + "; ".join(parts)


# =============================================================================
# ANTI-REPETITION SYSTEM
# =============================================================================
def build_anti_repetition_context(
    recent_messages: list,
    max_items: int = 10
) -> str:
    """Format recent messages as an anti-repetition
    prompt injection block.

    Returns empty string if no recent messages.
    """
    if not recent_messages:
        return ''

    # Deduplicate and limit
    seen = set()
    unique = []
    for msg in recent_messages:
        normalized = msg.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(msg.strip())
        if len(unique) >= max_items:
            break

    if not unique:
        return ''

    lines = '\n'.join(f'- "{m}"' for m in unique)
    return (
        "ANTI-REPETITION: These messages were recently "
        "said in this area. You MUST NOT repeat or "
        "closely paraphrase ANY of them. Say something "
        "completely different.\n"
        f"{lines}"
    )


# =============================================================================
# TALENT CONTEXT FOR LLM PROMPTS
# =============================================================================


def _normalize_target_description(
    description: str, char_name: str,
) -> str:
    """Rewrite 2nd-person catalog descriptions to
    3rd-person for target perspective prompts.

    Converts 'you'/'your' phrasing so that target
    context reads as '{name} is known for X, an
    ability that gives them...' instead of
    '...that gives you...'.
    """
    import re
    result = description
    # 1. Reflexive
    result = re.sub(
        r'\byourself\b', 'themself', result
    )
    result = re.sub(
        r'\bYourself\b', 'Themself', result
    )
    # 2. Possessive
    result = re.sub(r'\byour\b', 'their', result)
    result = re.sub(r'\bYour\b', 'Their', result)
    # 3. Subject-form "you" — at sentence start,
    #    after conjunctions, or after relative/
    #    subordinating words where "you" is subject.
    #    Uses capture group (not lookbehind) to
    #    enforce word boundaries on prefix words.
    _SUBJ_WORDS = (
        r'and|but|or|while|when|that|which'
        r'|whenever|if|unless|until|after'
        r'|before|once|so|where|as'
    )
    # Sentence/clause start
    result = re.sub(r'^[Yy]ou\b', 'they', result)
    result = re.sub(
        r'(?<=\. )[Yy]ou\b', 'they', result
    )
    # After punctuation + space
    result = re.sub(
        r'([,;] )[Yy]ou\b',
        r'\1they', result,
    )
    # After subordinating/conjunction words
    # (word boundary prevents "for" matching "or")
    result = re.sub(
        r'(\b(?:' + _SUBJ_WORDS + r') )'
        r'[Yy]ou\b',
        r'\1they', result,
    )
    # "you [verb]" — subject "you" followed by a
    # common verb (catches relative clauses like
    # "the damage you deal")
    _SUBJ_VERBS = (
        r'deal|take|cast|gain|have|get|do'
        r'|are|were|make|cause|receive|kill'
        r'|generate|spend|use|need|would'
        r'|can|may|will|could|should|must'
    )
    result = re.sub(
        r'\byou (?=' + _SUBJ_VERBS + r'\b)',
        'they ', result,
    )
    # Fix capitalization at true sentence start
    result = re.sub(
        r'(?:^|(?<=\. ))they\b',
        'They', result,
    )
    # 4. Subject-form contractions
    result = re.sub(
        r"\byou'll\b", "they'll", result
    )
    result = re.sub(
        r"\bYou'll\b", "They'll", result
    )
    result = re.sub(
        r"\byou're\b", "they're", result
    )
    result = re.sub(
        r"\bYou're\b", "They're", result
    )
    result = re.sub(
        r"\byou've\b", "they've", result
    )
    result = re.sub(
        r"\bYou've\b", "They've", result
    )
    result = re.sub(
        r"\byou'd\b", "they'd", result
    )
    result = re.sub(
        r"\bYou'd\b", "They'd", result
    )
    # 5. All remaining "you" is object-form
    result = re.sub(r'\bYou\b', 'Them', result)
    result = re.sub(r'\byou\b', 'them', result)
    return result


# ── Spec Personalities (Phase 2) ─────────────────
# Keys: (class_lower, tree_name_lower)
# Values: personality traits that color how this
# spec speaks and behaves in casual conversation.
SPEC_PERSONALITIES = {
    # Death Knight
    ("death knight", "blood"): (
        "Dark, vampiric nobility. Speaks with a "
        "chilling appreciation for vitality and "
        "judges the fragility of mortals."),
    ("death knight", "frost"): (
        "Cold, emotionless, relentless as northern "
        "winds. Clipped, chilling tones devoid of "
        "warmth or empathy."),
    ("death knight", "unholy"): (
        "Morbid, cynical, obsessed with decay. "
        "Raspy enthusiasm for death and the grave. "
        "Makes grim jokes about corpses and rot."),
    # Druid
    ("druid", "balance"): (
        "Philosophical and detached, drawn to "
        "cosmic cycles and celestial patterns. "
        "Speaks in metaphors about eclipses "
        "and universal harmony."),
    ("druid", "feral combat"): (
        "Wild, predatory, struggles with humanoid "
        "social graces. Short blunt sentences. "
        "Views social interactions through pack "
        "hierarchy."),
    ("druid", "restoration"): (
        "Nurturing, deeply empathetic, grounded "
        "in the earth. Soothing patient cadence. "
        "Always first to offer comfort or "
        "practical wisdom."),
    # Hunter
    ("hunter", "beast mastery"): (
        "Prefers animal company to people. Wild, "
        "instinct-driven, slightly feral in social "
        "interactions. Distrusts city-dwellers."),
    ("hunter", "marksmanship"): (
        "Precise, observant, wastes no words. "
        "Constantly evaluating distances and "
        "vulnerabilities. Patient and methodical."),
    ("hunter", "survival"): (
        "Pragmatic, rugged, always prepared for "
        "the worst. Shares unprompted wilderness "
        "survival advice. Paranoid about ambushes "
        "even in safe taverns."),
    # Mage
    ("mage", "arcane"): (
        "Intellectually superior, obsessed with "
        "raw magical theory. Speaks rapidly, "
        "easily annoyed by those who cannot keep "
        "up. Overthinks simple problems."),
    ("mage", "fire"): (
        "Passionate, impulsive, quick to anger. "
        "Explosive enthusiasm, reckless outlook. "
        "Lacks an inside voice and loves being "
        "the center of attention."),
    ("mage", "frost"): (
        "Calculating, disciplined, emotionally "
        "detached. Deliberate chilling calm, "
        "preferring control over raw emotion. "
        "Disdains messy situations."),
    # Paladin
    ("paladin", "holy"): (
        "Deeply compassionate, selfless, faithful "
        "to the Light. Gentle authority, always "
        "seeks to uplift and counsel. Genuinely "
        "caring, sometimes preachy."),
    ("paladin", "protection"): (
        "Stoic, vigilant, fiercely protective of "
        "the weak. Measures words carefully with "
        "the heavy burden of a steadfast guardian. "
        "Takes duty very seriously."),
    ("paladin", "retribution"): (
        "Zealous, uncompromising, quick to judge. "
        "Righteous fury, sees the world in black "
        "and white. Constantly looking for "
        "corruption to purge."),
    # Priest
    ("priest", "discipline"): (
        "Stern, balanced, regimented in faith. "
        "Unwavering conviction that willpower and "
        "strict boundaries are the true path. "
        "A strict but fair mentor."),
    ("priest", "holy"): (
        "Serene, unconditionally loving, radiant "
        "with grace. Speaks softly, offers "
        "profound spiritual comfort. Almost "
        "unnervingly calm in any crisis."),
    ("priest", "shadow"): (
        "Whispering, paranoid, drawn to the "
        "void\'s secrets. Cryptic unsettling "
        "riddles, references to unseen voices. "
        "Makes others deeply uncomfortable."),
    # Rogue
    ("rogue", "assassination"): (
        "Cold, professional, devoid of empathy. "
        "Speaks quietly and clinically about "
        "death. Views people as contracts, "
        "targets, or obstacles."),
    ("rogue", "combat"): (
        "Brash, confident, always looking for a "
        "good brawl. Speaks loudly, boasts about "
        "close shaves. Fights dirty but has a "
        "surprisingly strong code of honor."),
    ("rogue", "subtlety"): (
        "Secretive, manipulative, deeply "
        "untrusting. Half-truths and shadows, "
        "always looking for leverage. Answers "
        "questions with more questions."),
    # Shaman
    ("shaman", "elemental"): (
        "Attuned to chaotic elemental forces, "
        "often distracted by unseen spirits. "
        "Booming intensity echoing a thunderstorm. "
        "Quick to anger, quick to forgive."),
    ("shaman", "enhancement"): (
        "Aggressive, deeply spiritual, eager to "
        "test physical might. Warrior spirit "
        "grounded in ancestral guidance. Treats "
        "conversations as tests of strength."),
    ("shaman", "restoration"): (
        "Calm, fluid, connected to the soothing "
        "nature of water. Gentle rolling cadence, "
        "always seeking to mend rifts and find "
        "balance in disputes."),
    # Warlock
    ("warlock", "affliction"): (
        "Sadistic, infinitely patient, fascinated "
        "by suffering. Slow cruel drawl, takes "
        "pleasure in the unraveling of enemies. "
        "Views life as a terminal condition."),
    ("warlock", "demonology"): (
        "Power-hungry, arrogant, dangerously "
        "overconfident. Speaks down to others "
        "while casually arguing with summoned "
        "fiends. Believes they are the smartest "
        "person in any room."),
    ("warlock", "destruction"): (
        "Manic, chaotic, obsessed with fel fire. "
        "Dangerous crackling energy, eager to see "
        "the world burn. Highly impatient, solves "
        "every issue with explosives."),
    # Warrior
    ("warrior", "arms"): (
        "Disciplined, tactical, views combat as "
        "a refined art form. Measured authoritative "
        "tone of a veteran commander. Values "
        "honor, training, and technique."),
    ("warrior", "fury"): (
        "Reckless, bloodthirsty, lives for the "
        "rush of combat. Loud, aggressive, barely "
        "containing explosive rage. Impatient "
        "with planning, just wants to fight."),
    ("warrior", "protection"): (
        "Stoic, dependable, grounded in duty. "
        "Speaks sparsely but with immense weight. "
        "The immovable anchor, only speaks up "
        "when absolutely necessary."),
}


def build_talent_context(
    db,
    char_guid: int,
    char_class,
    char_name: str,
    perspective: str = 'speaker',
) -> Optional[str]:
    """Build a talent context string for LLM prompt
    injection.

    Args:
        db: Database connection (acore_characters).
        char_guid: Character GUID (int).
        char_class: Class name (str) or class ID (int).
        char_name: Character name.
        perspective: 'speaker' (2nd person) or
                     'target' (3rd person).

    Returns:
        str or None -- talent context string, or None
        if no talents found.
    """
    data = get_character_talents(db, char_guid)
    if not data or not data.get('talents'):
        return None

    tree_totals = data.get('tree_totals', {})
    if not tree_totals:
        return None

    # Find dominant tree (highest points; random on tie)
    max_pts = max(tree_totals.values())
    top_trees = [
        t for t, p in tree_totals.items()
        if p == max_pts
    ]
    dominant_tree = random.choice(top_trees)

    # Filter talents to dominant tree
    dom_talents = [
        t for t in data['talents']
        if t['tree_name'] == dominant_tree
    ]
    if not dom_talents:
        return None

    picked = random.choice(dom_talents)
    talent_name = picked['talent_name']
    tree_name = picked['tree_name']

    # Normalize class for catalog lookup
    if isinstance(char_class, int):
        class_str = CLASS_NAMES.get(char_class, '')
    else:
        class_str = str(char_class)
    class_lower = class_str.lower()
    tree_lower = tree_name.lower()

    # Look up description from TALENT_CATALOG
    description = None
    class_data = TALENT_CATALOG.get(class_lower, {})
    tree_data = class_data.get(tree_lower, {})

    if tree_data:
        # Exact match first
        description = tree_data.get(talent_name)
        # Case-insensitive fallback
        if not description:
            name_lower = talent_name.lower()
            for k, v in tree_data.items():
                if k.lower() == name_lower:
                    description = v
                    break

    # Instruction to prevent literal name-dropping
    natural_hint = (
        " Use this to subtly color your attitude "
        "or words — do NOT name the talent "
        "directly or put it in parentheses."
    )

    # Spec personality lookup
    spec_key = (class_lower, tree_lower)
    spec_personality = SPEC_PERSONALITIES.get(
        spec_key, '')

    # Format based on perspective
    if description:
        if perspective == 'target':
            desc = _normalize_target_description(
                description, char_name,
            )
            result = (
                f"{char_name} specializes in "
                f"{tree_name} techniques — "
                f"{desc}{natural_hint}"
            )
        else:
            result = (
                f"You trained in {tree_name} "
                f"arts: {description}"
                f"{natural_hint}"
            )
    elif perspective == 'target':
        result = (
            f"{char_name} focuses on the "
            f"{tree_name} path.{natural_hint}"
        )
    else:
        result = (
            f"You follow the {tree_name} path."
            f"{natural_hint}"
        )

    # Append spec personality if available
    if spec_personality:
        if perspective == 'target':
            result += (
                f" {char_name}'s {tree_name} "
                f"demeanor: {spec_personality}")
        else:
            result += (
                f" Your {tree_name} demeanor: "
                f"{spec_personality}")

    return result


# =============================================================================
# CENTRALIZED MESSAGE INSERTION
# =============================================================================
