"""
Chatter Prompts - Prompt builders and creative selection for LLM Chatter Bridge.

Imports from chatter_constants and chatter_shared.
"""

import logging
import random
from datetime import datetime
from typing import List, Tuple

from chatter_constants import (
    TONES, MOODS, CREATIVE_TWISTS, MESSAGE_CATEGORIES,
    LENGTH_HINTS,
    RP_TONES, RP_MOODS, RP_CREATIVE_TWISTS,
    RP_MESSAGE_CATEGORIES, RP_LENGTH_HINTS,
)
from chatter_shared import (
    get_chatter_mode, build_race_class_context,
    get_zone_flavor, format_price,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CREATIVE SELECTION FUNCTIONS
# =============================================================================
def pick_random_tone(mode: str = 'normal') -> str:
    """Pick a random tone for the message."""
    pool = RP_TONES if mode == 'roleplay' else TONES
    return random.choice(pool)


def pick_random_mood(mode: str = 'normal') -> str:
    """Pick a random mood/emotional angle for the message."""
    pool = RP_MOODS if mode == 'roleplay' else MOODS
    return random.choice(pool)


def maybe_get_creative_twist(
    chance: float = 0.3, mode: str = 'normal'
) -> str:
    """Maybe return a creative twist (30% chance by default)."""
    if random.random() < chance:
        pool = (
            RP_CREATIVE_TWISTS if mode == 'roleplay'
            else CREATIVE_TWISTS
        )
        return random.choice(pool)
    return None


def pick_random_message_category(mode: str = 'normal') -> str:
    """Pick a random message category."""
    pool = (
        RP_MESSAGE_CATEGORIES if mode == 'roleplay'
        else MESSAGE_CATEGORIES
    )
    return random.choice(pool)


def generate_conversation_mood_sequence(
    message_count: int, mode: str = 'normal'
) -> List[str]:
    """Generate a mood sequence for a conversation."""
    pool = RP_MOODS if mode == 'roleplay' else MOODS
    return [random.choice(pool) for _ in range(message_count)]


# Conversation length labels — short descriptions
# mapped to rough character counts for the LLM.
CONV_LENGTHS = [
    "very short (under 40 chars)",
    "short (40-70 chars)",
    "medium (70-120 chars)",
    "longer (120-180 chars)",
]
# Weights favour shorter messages; the occasional
# long one keeps it natural.
CONV_LENGTH_WEIGHTS = [30, 35, 25, 10]


def generate_conversation_length_sequence(
    message_count: int,
) -> List[str]:
    """Generate per-message length targets so
    conversations have varied message lengths
    instead of uniform output."""
    return random.choices(
        CONV_LENGTHS,
        weights=CONV_LENGTH_WEIGHTS,
        k=message_count,
    )


# =============================================================================
# ENVIRONMENTAL CONTEXT
# =============================================================================
def get_time_of_day_context() -> Tuple[str, str]:
    """Get current time-of-day context for immersive conversations."""
    hour = datetime.now().hour

    if 5 <= hour < 7:
        return (
            "dawn",
            "The early morning light is just appearing",
        )
    elif 7 <= hour < 9:
        return ("early_morning", "It's early morning")
    elif 9 <= hour < 12:
        return ("morning", "The morning sun is up")
    elif 12 <= hour < 14:
        return ("midday", "It's around midday")
    elif 14 <= hour < 17:
        return ("afternoon", "It's afternoon")
    elif 17 <= hour < 19:
        return ("evening", "Evening is approaching")
    elif 19 <= hour < 21:
        return ("dusk", "The sun is setting")
    elif 21 <= hour < 23:
        return ("night", "Night has fallen")
    elif hour == 23 or hour == 0:
        return ("midnight", "It's late at night")
    else:  # 1-4
        return (
            "late_night",
            "It's the deep hours of night",
        )


def get_environmental_context(
    current_weather: str = None
) -> dict:
    """Get environmental context for prompts.

    Time is always included. Weather is included
    when available (50% chance to mention it).
    """
    _, time_desc = get_time_of_day_context()
    result = {'time': time_desc, 'weather': None}

    if current_weather and random.random() < 0.50:
        result['weather'] = current_weather

    logger.info(
        f"Environmental context: "
        f"time={result['time']}, "
        f"weather={result['weather'] is not None}"
    )

    return result


# =============================================================================
# DYNAMIC GUIDELINES
# =============================================================================
def build_dynamic_guidelines(
    include_humor: bool = None,
    include_length: bool = True,
    config: dict = None,
    mode: str = 'normal'
) -> list:
    """Build a randomized list of guidelines."""
    is_rp = (mode == 'roleplay')

    if is_rp:
        guidelines = [
            "Stay in character but keep it natural and "
            "conversational, not dramatic or theatrical",
            "NEVER use brackets [] around quest names, "
            "item names, zone names, or faction names - "
            "write them as plain text. Only use brackets "
            "for NPC names like [Onu]. Only use "
            "{quest:Name} or {item:Name} placeholders "
            "when explicitly told to.",
        ]
    else:
        guidelines = [
            "Sound like a real player, not an NPC",
            "NEVER use brackets [] around quest names, "
            "item names, zone names, or faction names - "
            "write them as plain text. Only use brackets "
            "for NPC names like [Onu]. Only use "
            "{quest:Name} or {item:Name} placeholders "
            "when explicitly told to.",
        ]

    length_pool = RP_LENGTH_HINTS if is_rp else LENGTH_HINTS
    if include_length:
        guidelines.append(
            f"Length: {random.choice(length_pool)}"
        )
        long_chance = 15 if is_rp else 12
        if config is not None:
            try:
                long_chance = int(
                    config.get(
                        'LLMChatter.LongMessageChance',
                        long_chance
                    )
                )
                if is_rp:
                    long_chance = min(long_chance + 5, 30)
            except Exception:
                pass
        if random.randint(1, 100) <= long_chance:
            guidelines.append(
                "Length mode: long allowed (up to ~200 chars) "
                "if it feels natural"
            )
            guidelines.append(
                "If long, make it a single thought, "
                "not a paragraph"
            )
        else:
            guidelines.append(
                "Length mode: short/medium only "
                "(avoid long messages)"
            )

    if include_humor is None:
        include_humor = random.random() < (
            0.15 if is_rp else 0.25
        )
    if include_humor:
        if is_rp:
            guidelines.append(
                "A touch of wry or dry humor fits here"
            )
        else:
            guidelines.append(
                "A touch of humor fits here"
            )

    if is_rp:
        extras = [
            "Let your race flavor your words subtly, "
            "not heavily",
            "Keep it simple - like a real person talking, "
            "just in-character",
            "A small detail about the surroundings is nice",
            "Casual and grounded, not poetic or flowery",
        ]
    else:
        extras = [
            "Common terms ok (lfg, lf, ty, np)",
            "Can include a typo for realism",
            "Casual and natural chat style",
            "Brief and direct",
        ]
    if random.random() < 0.5:
        guidelines.append(random.choice(extras))

    return guidelines


# =============================================================================
# PROMPT BUILDERS
# =============================================================================
def build_plain_statement_prompt(
    bot: dict,
    zone_id: int = 0,
    zone_mobs: list = None,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a dynamically varied prompt for a plain statement."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    parts = []

    if is_rp:
        parts.append(
            f"You are {bot['name']}, a {bot.get('race', '')} "
            f"{bot.get('class', '')} in World of Warcraft. "
            f"Speak in-character in General chat in "
            f"{bot['zone']}."
        )
        rp_ctx = build_race_class_context(
            bot.get('race', ''), bot.get('class', '')
        )
        if rp_ctx:
            parts.append(rp_ctx)
    else:
        parts.append(
            f"Generate a brief WoW General chat message "
            f"from a player in {bot['zone']}."
        )

    zone_flavor = get_zone_flavor(zone_id)
    if zone_flavor:
        parts.append(f"Zone context: {zone_flavor}")

    env_context = get_environmental_context(current_weather)
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )

    if random.random() < 0.6:
        parts.append(f"Player level: {bot['level']}")

    if zone_mobs:
        parts.append(
            f"Creatures here: {', '.join(zone_mobs)}"
        )
        parts.append(
            "IMPORTANT: If mentioning any creature, ONLY use "
            "ones from the list above. Include the [[npc:...]] "
            "marker exactly as shown."
        )

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    parts.append(f"Tone: {tone}")
    parts.append(f"Mood: {mood}")

    twist = maybe_get_creative_twist(mode=mode)
    if twist:
        parts.append(f"Creative twist: {twist}")

    category = pick_random_message_category(mode)

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Prompt creativity: tone={tone}, mood={mood}, "
        f"category={category[:30]}{twist_log}"
    )
    parts.append(f"Message type: {category}")

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append(
        "Plain text only, except [[npc:...]] markers "
        "for creature names"
    )
    if is_rp:
        guidelines.append(
            "Stay in character but sound natural, "
            "not theatrical"
        )
        guidelines.append(
            "No game terms, abbreviations, "
            "or OOC references"
        )
    else:
        guidelines.append("Do NOT mention your race or class")
    guidelines.append(
        "Be ORIGINAL and UNPREDICTABLE - no common patterns, "
        "surprise the reader"
    )
    if zone_mobs:
        guidelines.append(
            "Only mention creatures from the provided list "
            "- do NOT invent creatures"
        )
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(
        "Respond with ONLY the message, nothing else."
    )

    return "\n".join(parts)


def build_quest_statement_prompt(
    bot: dict,
    quest: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a dynamically varied prompt for a quest statement."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    parts = []

    if is_rp:
        parts.append(
            f"You are {bot['name']}, a {bot.get('race', '')} "
            f"{bot.get('class', '')}. Speak in-character about "
            f"a quest in {bot['zone']}."
        )
        rp_ctx = build_race_class_context(
            bot.get('race', ''), bot.get('class', '')
        )
        if rp_ctx:
            parts.append(rp_ctx)
    else:
        parts.append(
            "Generate a brief WoW General chat message "
            "mentioning a quest."
        )
        parts.append(f"Zone: {bot['zone']}")

    env_context = get_environmental_context(current_weather)
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )

    if random.random() < 0.5:
        parts.append(f"Player level: {bot['level']}")

    quest_placeholder = f"{{{{quest:{quest['quest_name']}}}}}"
    parts.append(f"Quest: {quest['quest_name']}")
    parts.append(
        f"REQUIRED: Include exactly {quest_placeholder} in "
        f"your message (this becomes a clickable link)"
    )

    if quest.get('description') and random.random() < 0.4:
        parts.append(
            f"Quest involves: {quest['description'][:80]}"
        )

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    parts.append(f"Tone: {tone}")
    parts.append(f"Mood: {mood}")

    twist = maybe_get_creative_twist(mode=mode)
    if twist:
        parts.append(f"Creative twist: {twist}")

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Quest statement creativity: tone={tone}, "
        f"mood={mood}, "
        f"quest={quest['quest_name'][:30]}{twist_log}"
    )

    if is_rp:
        quest_actions = [
            "seeking guidance on the task",
            "reflecting on the quest's meaning",
            "warning of the dangers involved",
            "rallying companions for the undertaking",
            "musing on the reward awaiting",
        ]
    else:
        quest_actions = [
            "asking where to find it",
            "asking for help",
            "complaining about difficulty",
            "celebrating completion",
            "asking about rewards",
            "warning others about it",
            "looking for group",
        ]
    if random.random() < 0.6:
        parts.append(
            f"Approach: {random.choice(quest_actions)}"
        )

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Keep under 110 characters")
    if is_rp:
        guidelines.append(
            "Stay in character but sound natural, "
            "not theatrical"
        )
    guidelines.append("Be creative and unpredictable")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(
        "Respond with ONLY the message - be creative "
        "and unpredictable."
    )

    return "\n".join(parts)


def build_loot_statement_prompt(
    bot: dict,
    item: dict,
    can_use: bool,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a dynamically varied prompt for a loot statement."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    quality_names = {
        0: "gray", 1: "white", 2: "green",
        3: "blue", 4: "purple",
    }
    quality = quality_names.get(
        item.get('item_quality', 2), "green"
    )

    parts = []
    item_placeholder = f"{{{{item:{item['item_name']}}}}}"

    if is_rp:
        parts.append(
            f"You are {bot['name']}, a {bot.get('race', '')} "
            f"{bot.get('class', '')}. Speak in-character about "
            f"finding loot."
        )
        rp_ctx = build_race_class_context(
            bot.get('race', ''), bot.get('class', '')
        )
        if rp_ctx:
            parts.append(rp_ctx)
    else:
        parts.append(
            "Generate a brief WoW General chat message "
            "about a loot drop."
        )

    env_context = get_environmental_context(current_weather)
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )
    parts.append(
        f"Item: {item['item_name']} ({quality} quality)"
    )
    parts.append(
        f"REQUIRED: Include exactly {item_placeholder} in "
        f"your message (this becomes a clickable link)"
    )

    if random.random() < 0.6:
        parts.append(f"Player class: {bot['class']}")
        if random.random() < 0.4:
            usability = (
                "can equip"
                if can_use
                else "cannot equip (wrong class)"
            )
            parts.append(f"Class fit: {usability}")

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    parts.append(f"Tone: {tone}")
    parts.append(f"Mood: {mood}")

    twist = maybe_get_creative_twist(mode=mode)
    if twist:
        parts.append(f"Creative twist: {twist}")

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Loot statement creativity: tone={tone}, "
        f"mood={mood}, "
        f"item={item['item_name'][:30]}{twist_log}"
    )

    if is_rp:
        reactions = [
            "awe at the craftsmanship of the item",
            "weighing whether the item suits your path",
            "offering the spoils to a worthy companion",
            "reflecting on fortune and fate",
            "examining the item with a practiced eye",
        ]
    else:
        reactions = [
            "excitement about the drop",
            "meh, vendor fodder",
            "offering to trade/give away",
            "commenting on luck",
            "just mentioning what dropped",
            "comparing to previous drops",
            "wondering about the item",
        ]
    parts.append(f"Reaction style: {random.choice(reactions)}")

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Keep under 110 characters")
    if is_rp:
        guidelines.append(
            "Stay in character but sound natural, "
            "not theatrical"
        )
    guidelines.append("Be creative and unpredictable")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(
        "Respond with ONLY the message - be creative "
        "and unpredictable."
    )

    return "\n".join(parts)


def build_quest_reward_statement_prompt(
    bot: dict,
    quest: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for quest completion with reward."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')

    item_name = (
        quest.get('item1_name') or quest.get('item2_name')
    )
    item_quality = (
        quest.get('item1_quality')
        or quest.get('item2_quality')
        or 2
    )

    if not item_name:
        return build_quest_statement_prompt(
            bot, quest, config, current_weather
        )

    quality_names = {
        0: "gray", 1: "white", 2: "green",
        3: "blue", 4: "purple",
    }
    quality = quality_names.get(item_quality, "green")

    parts = []

    if is_rp:
        parts.append(
            f"You are {bot['name']}, a {bot.get('race', '')} "
            f"{bot.get('class', '')}. Speak in-character about "
            f"completing a quest and its reward."
        )
        rp_ctx = build_race_class_context(
            bot.get('race', ''), bot.get('class', '')
        )
        if rp_ctx:
            parts.append(rp_ctx)
    else:
        parts.append(
            "Generate a brief WoW General chat message "
            "about finishing a quest."
        )

    env_context = get_environmental_context(current_weather)
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )

    parts.append(
        f"Quest: {quest['quest_name']} "
        f"(use {{{{quest:{quest['quest_name']}}}}} placeholder)"
    )
    parts.append(
        f"Reward: {item_name} ({quality}) "
        f"(use {{{{item:{item_name}}}}} placeholder)"
    )

    if random.random() < 0.5:
        parts.append(f"Player class: {bot['class']}")

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    parts.append(f"Tone: {tone}")
    parts.append(f"Mood: {mood}")

    twist = maybe_get_creative_twist(mode=mode)
    if twist:
        parts.append(f"Creative twist: {twist}")

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Quest+reward statement creativity: tone={tone}, "
        f"mood={mood}, "
        f"quest={quest['quest_name'][:30]}{twist_log}"
    )

    if is_rp:
        reactions = [
            "satisfaction at fulfilling the task",
            "examining the reward with appreciation",
            "reflecting on the journey it took",
            "offering thanks to those who aided",
        ]
    else:
        reactions = [
            "relief at finishing",
            "excitement about reward",
            "meh about the reward",
            "just noting completion",
            "sharing the achievement",
        ]
    if random.random() < 0.5:
        parts.append(
            f"Reaction: {random.choice(reactions)}"
        )

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Use BOTH placeholders, each once")
    guidelines.append("Keep under 110 characters")
    if is_rp:
        guidelines.append(
            "Stay in character but sound natural, "
            "not theatrical"
        )
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append("Respond with ONLY the message.")

    return "\n".join(parts)


def build_plain_conversation_prompt(
    bots: List[dict],
    zone_id: int = 0,
    zone_mobs: list = None,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for a plain conversation with 2-4 bots."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    if is_rp:
        parts.append(
            f"Generate an in-character General chat exchange "
            f"between {bot_count} adventurers in "
            f"{bots[0]['zone']}. Each speaks as their "
            f"race and class."
        )
    elif bot_count == 2:
        parts.append(
            f"Generate a casual General chat exchange between "
            f"two WoW players in {bots[0]['zone']}."
        )
    else:
        parts.append(
            f"Generate a casual General chat exchange between "
            f"{bot_count} WoW players in {bots[0]['zone']}."
        )

    zone_flavor = get_zone_flavor(zone_id)
    if zone_flavor:
        parts.append(f"Zone context: {zone_flavor}")

    env_context = get_environmental_context(current_weather)
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )

    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(
        "Names: Sometimes use their name when addressing "
        "directly (maybe 1-2 times in a conversation), but "
        "not every message - vary it naturally."
    )

    for bot in bots:
        if is_rp or random.random() < 0.4:
            parts.append(
                f"{bot['name']} is a "
                f"{bot['race']} {bot['class']}"
            )
            if is_rp:
                rp_ctx = build_race_class_context(
                    bot.get('race', ''),
                    bot.get('class', ''),
                )
                if rp_ctx:
                    parts.append(f"  {rp_ctx}")

    if zone_mobs:
        parts.append(
            f"Creatures here: {', '.join(zone_mobs)}"
        )
        parts.append(
            "IMPORTANT: If mentioning any creature, ONLY use "
            "ones from the list above. Include the [[npc:...]] "
            "marker exactly as shown."
        )

    tone = pick_random_tone(mode)
    parts.append(f"Overall tone: {tone}")

    twist = maybe_get_creative_twist(chance=0.4, mode=mode)
    if twist:
        parts.append(
            f"Creative twist for this conversation: {twist}"
        )

    min_msgs = bot_count
    max_msgs = bot_count + 3
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(
        msg_count, mode
    )
    length_sequence = generate_conversation_length_sequence(
        msg_count
    )

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Conversation creativity: tone={tone}, "
        f"moods={mood_sequence}{twist_log}"
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow this for each message):"
    )
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(
            f"  Message {i+1} ({speaker}): "
            f"mood={mood}, "
            f"length={length_sequence[i]}"
        )

    if is_rp:
        topics = [
            "discussing the dangers of these lands",
            "sharing tales of past battles",
            "debating the best path forward",
            "exchanging news from distant regions",
            "reflecting on the state of the war",
        ]
    else:
        topics = [
            "asking for directions or help",
            "chatting about the zone",
            "looking for group",
            "sharing tips",
            "random banter",
            "complaining about something",
            "celebrating something",
        ]
    if random.random() < 0.5:
        parts.append(
            f"Topic hint: {random.choice(topics)}"
        )

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append(
        "Plain text only, except [[npc:...]] markers "
        "for creature names"
    )
    guidelines.append("Follow the mood and length sequence above")
    if is_rp:
        guidelines.append(
            "Each speaker stays in character for their "
            "race and class"
        )
        guidelines.append(
            "No game terms, abbreviations, or OOC references"
        )
        guidelines.append(
            "VARY message lengths naturally - some brief, "
            "some more expressive"
        )
    else:
        guidelines.append(
            "VARY message lengths naturally "
            "- some short, some medium, some longer"
        )
    if zone_mobs:
        guidelines.append(
            "Only mention creatures from the provided list "
            "- do NOT invent creatures"
        )
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, no code fences."
    )
    example_msgs = ',\n  '.join(
        [f'{{"speaker": "{name}", "message": "..."}}'
         for name in bot_names]
    )
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_quest_conversation_prompt(
    bots: List[dict],
    quest: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for a quest conversation with 2-4 bots."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    if is_rp:
        parts.append(
            f"Generate an in-character General chat exchange "
            f"about a quest in {bots[0]['zone']}. Each speaker "
            f"stays true to their race and class."
        )
    else:
        parts.append(
            f"Generate a casual General chat exchange about "
            f"a quest in {bots[0]['zone']}."
        )
    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(
        "Names: Sometimes use their name when addressing "
        "directly (maybe 1-2 times), but not every message."
    )

    if is_rp:
        for bot in bots:
            parts.append(
                f"{bot['name']} is a "
                f"{bot['race']} {bot['class']}"
            )

    env_context = get_environmental_context(current_weather)
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )

    parts.append(
        f"Quest: {quest['quest_name']} "
        f"(use {{{{quest:{quest['quest_name']}}}}} placeholder)"
    )
    if quest.get('description') and random.random() < 0.4:
        parts.append(
            f"Quest involves: {quest['description'][:60]}"
        )

    tone = pick_random_tone(mode)
    parts.append(f"Overall tone: {tone}")

    twist = maybe_get_creative_twist(chance=0.4, mode=mode)
    if twist:
        parts.append(
            f"Creative twist for this conversation: {twist}"
        )

    min_msgs = bot_count
    max_msgs = bot_count + 3
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(
        msg_count, mode
    )
    length_sequence = generate_conversation_length_sequence(
        msg_count
    )

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Quest conv creativity: tone={tone}, "
        f"moods={mood_sequence}{twist_log}"
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow this for each message):"
    )
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(
            f"  Message {i+1} ({speaker}): "
            f"mood={mood}, "
            f"length={length_sequence[i]}"
        )

    if is_rp:
        angles = [
            "seeking allies for a perilous task",
            "debating the best approach to the objective",
            "sharing knowledge of the quest's history",
            "steeling each other for the dangers ahead",
        ]
    else:
        angles = [
            "asking for help with the quest",
            "sharing where to find objectives",
            "complaining about quest difficulty",
            "discussing rewards",
            "warning about dangers",
            "celebrating completion",
        ]
    if random.random() < 0.5:
        parts.append(
            f"Angle hint: {random.choice(angles)}"
        )

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Use quest placeholder at least once")
    guidelines.append("Follow the mood and length sequence above")
    guidelines.append(
        "Keep each message under 140 characters; "
        "short/medium is the norm"
    )
    if is_rp:
        guidelines.append(
            "Each speaker stays in character for their "
            "race and class"
        )
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, no code fences."
    )
    example_msgs = ',\n  '.join(
        [f'{{"speaker": "{name}", "message": "..."}}'
         for name in bot_names]
    )
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_loot_conversation_prompt(
    bots: List[dict],
    item: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for a loot conversation with 2-4 bots."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    quality_names = {
        0: "gray", 1: "white", 2: "green",
        3: "blue", 4: "purple",
    }
    quality = quality_names.get(
        item.get('item_quality', 2), "green"
    )
    item_placeholder = f"{{{{item:{item['item_name']}}}}}"

    if is_rp:
        parts.append(
            f"Generate an in-character General chat exchange "
            f"about a loot find in {bots[0]['zone']}."
        )
    else:
        parts.append(
            f"Generate a casual General chat exchange about "
            f"a loot drop in {bots[0]['zone']}."
        )
    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(
        "Names: Sometimes use their name when addressing "
        "directly (maybe once), but not every message."
    )

    if is_rp:
        for bot in bots:
            parts.append(
                f"{bot['name']} is a "
                f"{bot['race']} {bot['class']}"
            )

    env_context = get_environmental_context(current_weather)
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )

    parts.append(
        f"Item: {item['item_name']} ({quality} quality)"
    )
    parts.append(
        f"REQUIRED: Use {item_placeholder} placeholder "
        f"when mentioning the item"
    )

    tone = pick_random_tone(mode)
    parts.append(f"Overall tone: {tone}")

    twist = maybe_get_creative_twist(chance=0.4, mode=mode)
    if twist:
        parts.append(
            f"Creative twist for this conversation: {twist}"
        )

    min_msgs = bot_count
    max_msgs = bot_count + 2
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(
        msg_count, mode
    )
    length_sequence = generate_conversation_length_sequence(
        msg_count
    )

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Loot conv creativity: tone={tone}, "
        f"moods={mood_sequence}{twist_log}"
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow this for each message):"
    )
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(
            f"  Message {i+1} ({speaker}): "
            f"mood={mood}, "
            f"length={length_sequence[i]}"
        )

    if is_rp:
        angles = [
            "one examines the find while others "
            "judge its worth",
            "debating who is most suited to wield it",
            "one offers the spoils to the group",
            "appraising the craftsmanship with "
            "lore knowledge",
        ]
    else:
        angles = [
            "one player got the drop and others are "
            "jealous/congratulating",
            "discussing if the item is good for "
            "their class",
            "debating whether to vendor or auction it",
            "one asking if others need the drop",
            "comparing drops they've gotten today",
        ]
    parts.append(f"Angle: {random.choice(angles)}")

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Use item placeholder at least once")
    guidelines.append("Follow the mood and length sequence above")
    guidelines.append(
        "Keep each message under 140 characters; "
        "short/medium is the norm"
    )
    if is_rp:
        guidelines.append(
            "Each speaker stays in character for their "
            "race and class"
        )
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, no code fences."
    )
    example_msgs = ',\n  '.join(
        [f'{{"speaker": "{name}", "message": "..."}}'
         for name in bot_names]
    )
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_event_conversation_prompt(
    bots: List[dict],
    event_context: str,
    zone_id: int = 0,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for an event-triggered conversation."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    if is_rp:
        parts.append(
            f"Generate an in-character General chat exchange "
            f"between {bot_count} adventurers in "
            f"{bots[0]['zone']}."
        )
    else:
        parts.append(
            f"Generate a casual General chat exchange between "
            f"{bot_count} WoW players in {bots[0]['zone']}."
        )
    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(
        "Names: Sometimes use their name when addressing "
        "directly (maybe once), but not every message."
    )

    parts.append(f"\nEVENT CONTEXT: {event_context}")

    is_transport = (
        'boat' in event_context.lower()
        or 'zeppelin' in event_context.lower()
        or 'turtle' in event_context.lower()
    )
    is_holiday = (
        'festival' in event_context.lower()
    )
    if is_transport:
        parts.append(
            "This transport just arrived - at least one bot "
            "should comment on it!"
        )
        parts.append(
            "Use the specific transport type "
            "(boat/zeppelin/turtle), NOT the generic word "
            "'transport'."
        )
        parts.append(
            "CRITICAL: Read the event context carefully - "
            "it tells you WHERE the transport arrived (your "
            "current location) and WHERE it came FROM."
        )
        parts.append(
            "If bots want to board or leave, they go TO the "
            "origin (where it came from), NOT to their "
            "current location!"
        )
        parts.append(
            "If a ship name is mentioned (e.g., 'The "
            "Moonspray'), you can optionally include it."
        )
    elif is_holiday:
        parts.append(
            "This conversation should be ABOUT the "
            "festival! Each bot shares their opinion or "
            "feelings about the holiday - excited, "
            "annoyed, nostalgic, indifferent, etc. "
            "Mention the holiday by name."
        )
    else:
        parts.append(
            "The conversation may naturally reference this "
            "event, or players may chat about something else."
        )
        parts.append(
            "The event provides atmosphere - you don't HAVE "
            "to mention it explicitly."
        )

    zone_flavor = get_zone_flavor(zone_id)
    if zone_flavor:
        parts.append(f"Zone context: {zone_flavor}")

    weather_for_context = (
        current_weather
        if 'weather' not in event_context.lower()
        else None
    )
    env_context = get_environmental_context(
        weather_for_context
    )
    if env_context['time']:
        parts.append(f"Time of day: {env_context['time']}")
    if env_context['weather']:
        parts.append(
            f"Current weather: {env_context['weather']}"
        )

    for bot in bots:
        if is_rp or random.random() < 0.4:
            parts.append(
                f"{bot['name']} is a "
                f"{bot['race']} {bot['class']}"
            )
            if is_rp:
                rp_ctx = build_race_class_context(
                    bot.get('race', ''),
                    bot.get('class', ''),
                )
                if rp_ctx:
                    parts.append(f"  {rp_ctx}")

    tone = pick_random_tone(mode)
    parts.append(f"Overall tone: {tone}")

    twist = maybe_get_creative_twist(chance=0.4, mode=mode)
    if twist:
        parts.append(
            f"Creative twist for this conversation: {twist}"
        )

    min_msgs = bot_count
    max_msgs = bot_count + 2
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(
        msg_count, mode
    )
    length_sequence = generate_conversation_length_sequence(
        msg_count
    )

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Event conv creativity: tone={tone}, "
        f"moods={mood_sequence}{twist_log}"
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow this for each message):"
    )
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(
            f"  Message {i+1} ({speaker}): "
            f"mood={mood}, "
            f"length={length_sequence[i]}"
        )

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Follow the mood and length sequence above")
    if is_rp:
        guidelines.append(
            "Each speaker stays in character for their "
            "race and class"
        )
        guidelines.append(
            "VARY message lengths naturally - some brief, "
            "some more expressive"
        )
    else:
        guidelines.append(
            "VARY message lengths naturally - some very "
            "short ('lol', 'yeah'), some medium, "
            "occasionally longer"
        )
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, no code fences."
    )
    example_msgs = ',\n  '.join(
        [f'{{"speaker": "{name}", "message": "..."}}'
         for name in bot_names]
    )
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


# =============================================================================
# SPELL PROMPTS
# =============================================================================
def build_spell_statement_prompt(
    bot: dict,
    spell: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for a spell/ability statement."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    parts = []

    spell_placeholder = (
        f"{{{{spell:{spell['spell_name']}}}}}"
    )

    if is_rp:
        parts.append(
            f"You are {bot['name']}, a "
            f"{bot.get('race', '')} "
            f"{bot.get('class', '')}. "
            f"Speak in-character about a spell "
            f"or ability you know."
        )
        rp_ctx = build_race_class_context(
            bot.get('race', ''),
            bot.get('class', '')
        )
        if rp_ctx:
            parts.append(rp_ctx)
    else:
        parts.append(
            "Generate a brief WoW General chat "
            "message about a class spell or ability."
        )
        parts.append(f"Zone: {bot['zone']}")

    env_context = get_environmental_context(
        current_weather
    )
    if env_context['time']:
        parts.append(
            f"Time of day: {env_context['time']}"
        )
    if env_context['weather']:
        parts.append(
            f"Current weather: "
            f"{env_context['weather']}"
        )

    if random.random() < 0.5:
        parts.append(f"Player level: {bot['level']}")
    parts.append(f"Player class: {bot['class']}")

    parts.append(
        f"Spell: {spell['spell_name']}"
    )
    if spell.get('spell_desc'):
        parts.append(
            f"What it does: {spell['spell_desc']}"
        )
    parts.append(
        f"REQUIRED: Include exactly "
        f"{spell_placeholder} in your message "
        f"(this becomes a clickable spell link)"
    )

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    parts.append(f"Tone: {tone}")
    parts.append(f"Mood: {mood}")

    twist = maybe_get_creative_twist(mode=mode)
    if twist:
        parts.append(f"Creative twist: {twist}")

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Spell statement creativity: "
        f"tone={tone}, mood={mood}, "
        f"spell={spell['spell_name'][:30]}"
        f"{twist_log}"
    )

    if is_rp:
        approaches = [
            "reflecting on mastering the ability",
            "describing how the power feels",
            "discussing training with a mentor",
            "comparing it to another technique",
            "musing on the responsibility it "
            "brings",
        ]
    else:
        approaches = [
            "just trained it, excited",
            "asking if it's worth the gold",
            "comparing to another ability",
            "complaining about the spell",
            "bragging about damage/healing",
            "asking for tips on using it",
            "discussing spec or talent build",
        ]
    if random.random() < 0.6:
        parts.append(
            f"Approach: {random.choice(approaches)}"
        )

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Keep under 110 characters")
    if is_rp:
        guidelines.append(
            "Stay in character but sound natural, "
            "not theatrical"
        )
    guidelines.append(
        "Be creative and unpredictable"
    )
    parts.append(
        "Guidelines: " + "; ".join(guidelines)
    )

    parts.append(
        "Respond with ONLY the message - be "
        "creative and unpredictable."
    )

    return "\n".join(parts)


def build_spell_conversation_prompt(
    bots: List[dict],
    spell: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for a spell conversation
    with 2-4 bots discussing an ability."""
    mode = (
        get_chatter_mode(config)
        if config else 'normal'
    )
    is_rp = (mode == 'roleplay')
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    spell_placeholder = (
        f"{{{{spell:{spell['spell_name']}}}}}"
    )

    if is_rp:
        parts.append(
            f"Generate an in-character General "
            f"chat exchange about an ability "
            f"in {bots[0]['zone']}."
        )
    else:
        parts.append(
            f"Generate a casual General chat "
            f"exchange where players discuss a "
            f"class ability in {bots[0]['zone']}."
        )

    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    parts.append(
        "Names: Sometimes use their name when "
        "addressing directly (maybe once), but "
        "not every message."
    )
    parts.append(
        f"The first speaker ({bot_names[0]}) is a "
        f"{bots[0]['class']} who knows this spell."
    )

    for bot in bots:
        parts.append(
            f"{bot['name']} is a "
            f"{bot['race']} {bot['class']}"
        )
        if is_rp:
            rp_ctx = build_race_class_context(
                bot.get('race', ''),
                bot.get('class', ''),
            )
            if rp_ctx:
                parts.append(f"  {rp_ctx}")

    env_context = get_environmental_context(
        current_weather
    )
    if env_context['time']:
        parts.append(
            f"Time of day: {env_context['time']}"
        )
    if env_context['weather']:
        parts.append(
            f"Current weather: "
            f"{env_context['weather']}"
        )

    parts.append(
        f"Spell being discussed: "
        f"{spell['spell_name']} "
        f"({bots[0]['class']} ability)"
    )
    if spell.get('spell_desc'):
        parts.append(
            f"What it does: {spell['spell_desc']}"
        )
    parts.append(
        f"REQUIRED: Use {spell_placeholder} "
        f"placeholder when mentioning this spell"
    )
    parts.append(
        "Other speakers may mention their own "
        "class abilities by name (plain text, no "
        "placeholder) for comparison."
    )

    tone = pick_random_tone(mode)
    parts.append(f"Overall tone: {tone}")

    twist = maybe_get_creative_twist(
        chance=0.4, mode=mode
    )
    if twist:
        parts.append(
            f"Creative twist for this "
            f"conversation: {twist}"
        )

    min_msgs = bot_count
    max_msgs = bot_count + 2
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = (
        generate_conversation_mood_sequence(
            msg_count, mode
        )
    )
    length_sequence = (
        generate_conversation_length_sequence(
            msg_count
        )
    )

    twist_log = (
        f", twist={twist}" if twist else ""
    )
    logger.info(
        f"Spell conv creativity: tone={tone}, "
        f"moods={mood_sequence}{twist_log}"
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow this for each message):"
    )
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(
            f"  Message {i+1} ({speaker}): "
            f"mood={mood}, "
            f"length={length_sequence[i]}"
        )

    if is_rp:
        angles = [
            "comparing techniques and training "
            "methods",
            "one demonstrates while others "
            "react",
            "debating which abilities are most "
            "vital",
            "sharing stories of the spell in "
            "battle",
        ]
    else:
        angles = [
            "one just learned it and others "
            "react with jealousy or advice",
            "debating if the spell is overpowered "
            "or underpowered",
            "comparing to similar abilities in "
            "other classes",
            "tips on when and how to use it "
            "effectively",
            "discussing talent builds that "
            "improve the spell",
        ]
    parts.append(f"Angle: {random.choice(angles)}")

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append(
        "Use spell placeholder at least once"
    )
    guidelines.append(
        "Follow the mood and length sequence above"
    )
    guidelines.append(
        "Keep each message under 140 characters; "
        "short/medium is the norm"
    )
    if is_rp:
        guidelines.append(
            "Each speaker stays in character for "
            "their race and class"
        )
    parts.append(
        "Guidelines: " + "; ".join(guidelines)
    )

    parts.append(
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, "
        "no code fences."
    )
    example_msgs = ',\n  '.join(
        [
            f'{{"speaker": "{name}", '
            f'"message": "..."}}'
            for name in bot_names
        ]
    )
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


# =============================================================================
# TRADE / SELL PROMPTS
# =============================================================================
def build_trade_statement_prompt(
    bot: dict,
    item: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for a trade/sell statement."""
    mode = get_chatter_mode(config) if config else 'normal'
    is_rp = (mode == 'roleplay')
    quality_names = {
        0: "gray", 1: "white", 2: "green",
        3: "blue", 4: "purple",
    }
    quality = quality_names.get(
        item.get('item_quality', 2), "green"
    )

    parts = []
    item_placeholder = (
        f"{{{{item:{item['item_name']}}}}}"
    )

    if is_rp:
        parts.append(
            f"You are {bot['name']}, a "
            f"{bot.get('race', '')} "
            f"{bot.get('class', '')}. You want to "
            f"sell or trade an item you found. "
            f"Speak in-character."
        )
        rp_ctx = build_race_class_context(
            bot.get('race', ''), bot.get('class', '')
        )
        if rp_ctx:
            parts.append(rp_ctx)
    else:
        parts.append(
            "Generate a WoW General chat message "
            "where a player is selling or looking "
            "to trade an item."
        )

    env_context = get_environmental_context(
        current_weather
    )
    if env_context['time']:
        parts.append(
            f"Time of day: {env_context['time']}"
        )
    if env_context['weather']:
        parts.append(
            f"Current weather: "
            f"{env_context['weather']}"
        )

    parts.append(
        f"Item: {item['item_name']} ({quality} "
        f"quality)"
    )
    vendor_price = format_price(
        item.get('sell_price', 0)
    )
    if vendor_price:
        # Player prices ~2-5x vendor for whites,
        # more for greens/blues
        parts.append(
            f"Vendor sell price: {vendor_price} "
            f"(player price should be higher, "
            f"roughly 2-5x vendor value)"
        )
    parts.append(
        f"REQUIRED: Include exactly "
        f"{item_placeholder} in your message "
        f"(this becomes a clickable link)"
    )

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    parts.append(f"Tone: {tone}")
    parts.append(f"Mood: {mood}")

    twist = maybe_get_creative_twist(mode=mode)
    if twist:
        parts.append(f"Creative twist: {twist}")

    twist_log = f", twist={twist}" if twist else ""
    logger.info(
        f"Trade statement creativity: tone={tone}, "
        f"mood={mood}, "
        f"item={item['item_name'][:30]}"
        f", vendor={vendor_price or 'n/a'}"
        f"{twist_log}"
    )

    if is_rp:
        styles = [
            "offering wares like a traveling "
            "merchant",
            "seeking a fair trade with a fellow "
            "adventurer",
            "parting with gear you've outgrown",
            "hawking your find to passers-by",
        ]
    else:
        styles = [
            "WTS style - short trade post with "
            "price",
            "casual offer - mentioning you don't "
            "need it",
            "asking if anyone needs the item",
            "advertising the item with enthusiasm",
            "lowkey mention you're selling cheap",
            "LF buyer, taking offers",
        ]
    parts.append(f"Style: {random.choice(styles)}")

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append("Keep under 110 characters")
    guidelines.append(
        "Include a realistic price in gold/silver "
        "(e.g. 2g, 50s, 1g20s)"
    )
    guidelines.append(
        "Trade abbreviations encouraged: WTS, WTB, "
        "WTT, pst, /w, OBO"
    )
    if is_rp:
        guidelines.append(
            "Stay in character but sound natural"
        )
    parts.append(
        "Guidelines: " + "; ".join(guidelines)
    )

    parts.append(
        "Respond with ONLY the message - be "
        "creative and unpredictable."
    )

    return "\n".join(parts)


def build_trade_conversation_prompt(
    bots: List[dict],
    item: dict,
    config: dict = None,
    current_weather: str = 'clear'
) -> str:
    """Build a prompt for a trade conversation
    with 2-4 bots haggling over an item."""
    mode = (
        get_chatter_mode(config)
        if config else 'normal'
    )
    is_rp = (mode == 'roleplay')
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    quality_names = {
        0: "gray", 1: "white", 2: "green",
        3: "blue", 4: "purple",
    }
    quality = quality_names.get(
        item.get('item_quality', 2), "green"
    )
    item_placeholder = (
        f"{{{{item:{item['item_name']}}}}}"
    )

    if is_rp:
        parts.append(
            f"Generate an in-character General "
            f"chat exchange about trading/selling "
            f"an item in {bots[0]['zone']}."
        )
    else:
        parts.append(
            f"Generate a casual General chat "
            f"exchange where players haggle or "
            f"discuss selling an item in "
            f"{bots[0]['zone']}."
        )

    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    parts.append(
        "Names: Sometimes use their name when "
        "addressing directly (maybe once), but "
        "not every message."
    )
    parts.append(
        f"The first speaker ({bot_names[0]}) is "
        f"the seller."
    )

    if is_rp:
        for bot in bots:
            parts.append(
                f"{bot['name']} is a "
                f"{bot['race']} {bot['class']}"
            )

    env_context = get_environmental_context(
        current_weather
    )
    if env_context['time']:
        parts.append(
            f"Time of day: {env_context['time']}"
        )
    if env_context['weather']:
        parts.append(
            f"Current weather: "
            f"{env_context['weather']}"
        )

    parts.append(
        f"Item for sale: {item['item_name']} "
        f"({quality} quality)"
    )
    vendor_price = format_price(
        item.get('sell_price', 0)
    )
    if vendor_price:
        parts.append(
            f"Vendor sell price: {vendor_price} "
            f"(player price should be higher, "
            f"roughly 2-5x vendor value)"
        )
    parts.append(
        f"REQUIRED: Use {item_placeholder} "
        f"placeholder when mentioning the item"
    )

    tone = pick_random_tone(mode)
    parts.append(f"Overall tone: {tone}")

    twist = maybe_get_creative_twist(
        chance=0.4, mode=mode
    )
    if twist:
        parts.append(
            f"Creative twist for this "
            f"conversation: {twist}"
        )

    min_msgs = bot_count
    max_msgs = bot_count + 2
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = (
        generate_conversation_mood_sequence(
            msg_count, mode
        )
    )
    length_sequence = (
        generate_conversation_length_sequence(
            msg_count
        )
    )

    twist_log = (
        f", twist={twist}" if twist else ""
    )
    logger.info(
        f"Trade conv creativity: tone={tone}, "
        f"moods={mood_sequence}{twist_log}"
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow this for each message):"
    )
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(
            f"  Message {i+1} ({speaker}): "
            f"mood={mood}, "
            f"length={length_sequence[i]}"
        )

    if is_rp:
        angles = [
            "bartering with in-character haggling",
            "one offers an item and others "
            "appraise its worth",
            "negotiating a trade between "
            "adventurers",
            "debating a fair price with lore "
            "flavor",
        ]
    else:
        angles = [
            "seller posts WTS, buyer haggles on "
            "price",
            "seller offers item, others comment "
            "on whether it's worth it",
            "back-and-forth negotiation with a "
            "deal or walkaway",
            "someone undercuts or offers a better "
            "item",
            "casual price check turning into a "
            "sale",
        ]
    parts.append(f"Angle: {random.choice(angles)}")

    guidelines = build_dynamic_guidelines(
        config=config, mode=mode
    )
    guidelines.append(
        "Use item placeholder at least once"
    )
    guidelines.append(
        "Include realistic prices in gold/silver "
        "(use vendor price as reference)"
    )
    guidelines.append(
        "Trade abbreviations OK: WTS, WTB, WTT, "
        "pst, OBO"
    )
    guidelines.append(
        "Follow the mood and length sequence above"
    )
    guidelines.append(
        "Keep each message under 140 characters; "
        "short/medium is the norm"
    )
    if is_rp:
        guidelines.append(
            "Each speaker stays in character for "
            "their race and class"
        )
    parts.append(
        "Guidelines: " + "; ".join(guidelines)
    )

    parts.append(
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, "
        "no code fences."
    )
    example_msgs = ',\n  '.join(
        [
            f'{{"speaker": "{name}", '
            f'"message": "..."}}'
            for name in bot_names
        ]
    )
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)
