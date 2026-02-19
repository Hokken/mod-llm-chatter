"""
Chatter Shared - Shared utilities, DB, LLM, queries for the LLM Chatter Bridge.

Imports from chatter_constants, chatter_text,
chatter_llm, and chatter_db.
No circular dependencies.
"""

import json
import logging
import random
import re
import sys
from typing import Optional, Dict, List, Tuple, Any

from chatter_constants import (
    ZONE_LEVELS, ZONE_NAMES,
    CLASS_NAMES, RACE_NAMES,
    RACE_SPEECH_PROFILES, CLASS_SPEECH_MODIFIERS,
    CLASS_ROLE_MAP, ROLE_COMBAT_PERSPECTIVES,
    ZONE_FLAVOR, DUNGEON_FLAVOR,
    ITEM_QUALITY_COLORS, CLASS_BITMASK,
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
)

logger = logging.getLogger(__name__)

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



# =============================================================================
# NAME LOOKUPS
# =============================================================================
def get_zone_name(zone_id: int) -> str:
    """Get human-readable zone name from zone ID."""
    if zone_id in ZONE_NAMES:
        return ZONE_NAMES[zone_id]
    return f"zone {zone_id}"


def get_class_name(class_id: int) -> str:
    """Get human-readable class name from class ID."""
    return CLASS_NAMES.get(class_id, "Adventurer")


def get_race_name(race_id: int) -> str:
    """Get human-readable race name from race ID."""
    return RACE_NAMES.get(race_id, "Unknown")


def get_chatter_mode(config: dict) -> str:
    """Return 'normal' or 'roleplay' from config."""
    mode = config.get('LLMChatter.ChatterMode', 'normal').lower()
    return mode if mode in ('normal', 'roleplay') else 'normal'


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
        logger.error(f"Failed to parse config: {e}")
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


# Cache for dungeon boss lists (never changes)
_dungeon_boss_cache = {}


def get_dungeon_bosses(
    db, map_id: int
) -> list:
    """Get boss names for a dungeon/raid map.

    Queries creature + creature_template from
    acore_world. Detects bosses via:
    - rank=3 (raid bosses)
    - mechanic_immune_mask > 0 AND single spawn
      (named dungeon bosses — CC-immune mobs that
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
                     OR ct.mechanic_immune_mask > 0)
            GROUP BY ct.entry, ct.name, ct.`rank`
            HAVING ct.`rank` = 3 OR COUNT(*) = 1
            ORDER BY ct.name
        """, (map_id,))
        bosses = [
            row['name']
            for row in cursor.fetchall()
        ]
        _dungeon_boss_cache[map_id] = bosses
        if bosses:
            logger.info(
                f"Dungeon bosses for map "
                f"{map_id}: {', '.join(bosses)}"
            )
        return bosses
    except Exception as e:
        logger.warning(
            f"Failed to query dungeon bosses "
            f"for map {map_id}: {e}"
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


def append_json_instruction(
    prompt: str, allow_action: bool = True,
    skip_emote: bool = False
) -> str:
    """Append structured JSON response instruction
    to a prompt.

    Tells the LLM to respond with JSON containing
    message, emote, and optionally action fields.
    skip_emote=True omits the emote list (saves
    ~200 tokens for General channel prompts where
    emotes are not displayed).
    """
    action_desc = ""
    if allow_action:
        action_desc = (
            '"action": a 2-5 word physical narration '
            '(e.g. "leans against the wall", '
            '"scratches chin thoughtfully", '
            '"adjusts pack nervously"). '
            "This is displayed as *action* before "
            "your speech. Omit or set null if no "
            "action fits.\n"
        )
    else:
        action_desc = (
            '"action": null (do not include an '
            "action for this response)\n"
        )

    if skip_emote:
        emote_line = '  "emote": null,\n'
    else:
        emote_line = (
            f'  "emote": one of [{EMOTE_LIST_STR}] '
            "or null,\n"
        )

    block = (
        "\n\nRESPONSE FORMAT: You MUST respond with "
        "ONLY valid JSON. No other text.\n"
        "{\n"
        '  "message": "your spoken words here",\n'
        f"{emote_line}"
        f"  {action_desc}"
        "}\n"
        "Rules: double quotes only, no trailing "
        "commas, no code fences, no markdown."
    )
    return prompt + block


def append_conversation_json_instruction(
    prompt: str,
    bot_names: List[str],
    msg_count: int,
    allow_action: bool = True,
) -> str:
    """Append conversation JSON array instruction.

    Conversation prompts return an array where each
    item has speaker/message/emote/action fields.
    Emotes are always null because conversations
    are sent to General channel.
    """
    if allow_action:
        action_text = (
            "Actions: Each message may include an optional "
            "\"action\" field (2-5 word physical narration, "
            "e.g. \"leans against the wall\"). This is "
            "displayed as *action* before speech. Use "
            "sparingly — only when it adds character."
        )
    else:
        action_text = (
            "Actions: Do not include an action field "
            "in this response."
        )

    example_msgs = ',\n  '.join(
        [
            f'{{"speaker": "{name}", "message": "...", '
            f'"emote": null, "action": null}}'
            for name in bot_names
        ]
    )

    block = (
        "\n\nEmotes: Set the \"emote\" field to null "
        "for all messages.\n"
        f"{action_text}\n"
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, no code fences.\n"
        f"\nRespond with EXACTLY {msg_count} messages in JSON:\n"
        "[\n"
        f"  {example_msgs}\n"
        "]\n"
        "ONLY the JSON array, nothing else."
    )
    return prompt + block


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
    prev_message_length: int = 0
) -> float:
    """Calculate a realistic delay based on message length."""
    min_delay = (
        int(config.get('LLMChatter.MessageDelayMin', 1000))
        / 1000.0
    )
    max_delay = (
        int(config.get('LLMChatter.MessageDelayMax', 30000))
        / 1000.0
    )

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

    minimum_for_length = (message_length / 4.0) + 2.0
    total_delay = max(total_delay, minimum_for_length)
    total_delay = max(total_delay, min_delay, 4.0)
    total_delay *= random.uniform(0.85, 1.20)

    return min(total_delay, max_delay)


# =============================================================================
# LLM INTERACTION
# =============================================================================
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
) -> Dict[str, Any]:
    """Run shared single-message reaction pipeline.

    Flow:
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
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens_override,
        context=context,
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
        except Exception as e:
            logger.error(
                f"run_single_reaction transform error: {e}"
            )
            return {
                'ok': False,
                'message': None,
                'emote': None,
                'error_reason': 'transform_error',
            }

    if len(message) > 255:
        message = message[:252] + "..."

    emote = parsed.get('emote')
    if allow_emote_fallback:
        emote = emote or pick_emote_for_statement(message)

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
) -> Optional[str]:
    """Check if a player message addresses a specific
    bot by name. Returns the matched bot name or None.

    Three-pass approach:
    1. Exact whole-word match (case-insensitive)
    2. Fuzzy fallback for names >= 4 chars
    3. LLM context analysis (if client/config given
       and chat history exists)
    """
    if not message or not bot_names:
        return None
    msg_lower = message.lower()

    # Pass 1: exact whole-word match
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
                logger.info(
                    f"Bot match (exact): {name}"
                )
                return name
            idx = msg_lower.find(
                name_lower, idx + 1
            )

    # Pass 2: fuzzy match on words (names >= 4 chars)
    words = re.split(r'[^a-zA-Z]+', message)
    words = [w for w in words if len(w) >= 4]
    for name in bot_names:
        if not name or len(name) < 4:
            continue
        for word in words:
            if fuzzy_name_match(word, name):
                logger.info(
                    f"Bot match (fuzzy): {name} "
                    f"from word '{word}'"
                )
                return name

    # Pass 3: LLM context analysis
    if not client or not config or not chat_history:
        return None

    # Only bother if there's recent bot speech
    # to reason about
    names_str = ', '.join(
        n for n in bot_names if n
    )
    prompt = (
        f"Recent chat:\n{chat_history}\n\n"
        f"The player just said:\n"
        f"\"{message}\"\n\n"
        f"Available bots: {names_str}\n\n"
        f"Based on the conversation context, "
        f"which bot is the player most likely "
        f"responding to or addressing?\n"
        f"If the message is clearly directed "
        f"at a specific bot, reply with ONLY "
        f"that bot's name.\n"
        f"If the message is general and not "
        f"directed at anyone specific, reply "
        f"with ONLY the word: none"
    )

    result = quick_llm_analyze(
        client, config, prompt, max_tokens=30
    )
    if not result:
        return None

    result = result.strip().strip('"').strip("'")

    if result.lower() == 'none':
        logger.info(
            "Bot match (LLM): none — general msg"
        )
        return None

    # Match LLM response to actual bot name
    for name in bot_names:
        if not name:
            continue
        if name.lower() == result.lower():
            logger.info(
                f"Bot match (LLM context): {name}"
            )
            return name

    # Fuzzy match LLM response to bot names
    for name in bot_names:
        if not name:
            continue
        if fuzzy_name_match(result, name):
            logger.info(
                f"Bot match (LLM fuzzy): {name} "
                f"from LLM '{result}'"
            )
            return name

    logger.info(
        f"Bot match (LLM): no match for "
        f"'{result}'"
    )
    return None


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
    except json.JSONDecodeError as e:
        snippet = response.strip().replace("\n", "\\n")
        logger.error(
            f"Failed to parse conversation JSON: {e}; "
            f"len={len(response)}; head={snippet[:200]}"
        )
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
        if repaired != raw_data:
            logger.debug(
                f"Repaired JSON for event {event_id}: "
                f"{raw_data[:100]}..."
            )
        return result
    except json.JSONDecodeError as e:
        logger.warning(
            f"Failed to parse extra_data JSON for "
            f"event {event_id} (type={event_type}): {e}"
        )
        logger.debug(f"Raw extra_data: {raw_data}")
    except Exception as e:
        logger.warning(
            f"Unexpected error parsing extra_data "
            f"for event {event_id}: {e}"
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


_ITEM_CLASS_NAMES = {
    0: "Consumable", 1: "Container",
    2: "Weapon", 3: "Gem", 4: "Armor",
    5: "Reagent", 6: "Projectile",
    7: "Trade Goods", 9: "Recipe",
    12: "Quest Item", 15: "Miscellaneous",
}

_WEAPON_SUBCLASS = {
    0: "One-Handed Axe", 1: "Two-Handed Axe",
    2: "Bow", 3: "Gun", 4: "One-Handed Mace",
    5: "Two-Handed Mace", 6: "Polearm",
    7: "One-Handed Sword", 8: "Two-Handed Sword",
    10: "Staff", 13: "Fist Weapon",
    15: "Dagger", 16: "Thrown",
    17: "Spear", 18: "Crossbow",
    19: "Wand", 20: "Fishing Pole",
}

_ARMOR_SUBCLASS = {
    0: "Miscellaneous", 1: "Cloth",
    2: "Leather", 3: "Mail", 4: "Plate",
    6: "Shield",
}

_QUALITY_NAMES = {
    0: "Poor", 1: "Common", 2: "Uncommon",
    3: "Rare", 4: "Epic", 5: "Legendary",
}


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
        quality = _QUALITY_NAMES.get(
            item.get('Quality', 1), 'Common'
        )
        item_class = item.get('item_class', 0)
        item_sub = item.get('item_subclass', 0)

        # Subclass-level type name for weapons/armor
        if item_class == 2:
            type_name = _WEAPON_SUBCLASS.get(
                item_sub, 'Weapon'
            )
        elif item_class == 4:
            type_name = _ARMOR_SUBCLASS.get(
                item_sub, 'Armor'
            )
        else:
            type_name = _ITEM_CLASS_NAMES.get(
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
# CENTRALIZED MESSAGE INSERTION
# =============================================================================
