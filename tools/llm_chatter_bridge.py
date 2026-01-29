#!/usr/bin/env python3
"""
LLM Chatter Bridge - Generates dynamic bot conversations via LLM

Supports both Anthropic (Claude) and OpenAI (GPT) models.

This script:
1. Polls the database for pending chatter requests
2. Sends prompts to LLM API based on bot personalities and zone context
3. Supports diverse message types: plain, quest links, item drops, quest+rewards
4. Parses responses and inserts messages with dynamic timing delays
"""

import argparse
import json
import logging
import random
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any

import anthropic
import openai
import mysql.connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# ZONE LEVEL MAPPING
# =============================================================================
# Maps zone IDs to (min_level, max_level) for querying appropriate content
ZONE_LEVELS = {
    # Eastern Kingdoms
    1: (1, 10),      # Dun Morogh
    12: (1, 10),     # Elwynn Forest
    38: (10, 20),    # Loch Modan
    40: (10, 20),    # Westfall
    44: (18, 30),    # Redridge Mountains
    46: (20, 30),    # Burning Steppes (actually higher but for variety)
    47: (30, 40),    # The Hinterlands
    51: (30, 40),    # Searing Gorge
    85: (1, 10),     # Tirisfal Glades
    130: (10, 20),   # Silverpine Forest
    267: (20, 30),   # Hillsbrad Foothills
    33: (30, 40),    # Stranglethorn Vale
    45: (35, 45),    # Arathi Highlands
    3: (40, 50),     # Badlands
    8: (45, 55),     # Swamp of Sorrows
    4: (50, 60),     # Blasted Lands
    139: (50, 60),   # Eastern Plaguelands
    28: (50, 60),    # Western Plaguelands
    41: (15, 25),    # Deadwind Pass
    10: (25, 35),    # Duskwood
    11: (30, 40),    # Wetlands

    # Kalimdor
    14: (1, 10),     # Durotar
    215: (1, 10),    # Mulgore
    141: (1, 10),    # Teldrassil
    148: (10, 20),   # Darkshore
    17: (10, 20),    # The Barrens
    331: (18, 28),   # Ashenvale
    405: (15, 25),   # Desolace
    400: (25, 35),   # Thousand Needles
    15: (35, 45),    # Dustwallow Marsh
    357: (40, 50),   # Feralas
    440: (40, 50),   # Tanaris
    16: (45, 55),    # Azshara
    361: (48, 55),   # Felwood
    490: (48, 55),   # Un'Goro Crater
    493: (50, 60),   # Moonglade
    618: (55, 60),   # Winterspring
    1377: (55, 60),  # Silithus

    # Outland
    3483: (58, 63),  # Hellfire Peninsula
    3518: (60, 64),  # Nagrand
    3519: (62, 65),  # Terokkar Forest
    3520: (64, 67),  # Shadowmoon Valley
    3521: (65, 68),  # Zangarmarsh
    3522: (67, 70),  # Blade's Edge Mountains
    3523: (67, 70),  # Netherstorm

    # Northrend
    3537: (68, 72),  # Borean Tundra
    495: (68, 72),   # Howling Fjord
    394: (71, 75),   # Grizzly Hills
    3711: (73, 76),  # Sholazar Basin
    66: (74, 77),    # Zul'Drak
    67: (76, 80),    # Storm Peaks
    210: (77, 80),   # Icecrown
}

# Item quality colors for WoW links (FF prefix for alpha channel)
ITEM_QUALITY_COLORS = {
    0: "FF9d9d9d",  # Poor (Gray)
    1: "FFffffff",  # Common (White)
    2: "FF1eff00",  # Uncommon (Green)
    3: "FF0070dd",  # Rare (Blue)
    4: "FFa335ee",  # Epic (Purple)
    5: "FFff8000",  # Legendary (Orange)
    6: "FFe6cc80",  # Artifact (Light Gold)
    7: "FF00ccff",  # Heirloom (Light Blue)
}

# Class bitmask values for AllowableClass field in item_template
# -1 means all classes can use, otherwise it's a bitmask
CLASS_BITMASK = {
    "Warrior": 1,
    "Paladin": 2,
    "Hunter": 4,
    "Rogue": 8,
    "Priest": 16,
    "Death Knight": 32,
    "Shaman": 64,
    "Mage": 128,
    "Warlock": 256,
    "Druid": 512,
}

# Message type distribution (cumulative percentages)
MSG_TYPE_PLAIN = 65
MSG_TYPE_QUEST = 80        # 15% chance (65-80)
MSG_TYPE_LOOT = 92         # 12% chance (80-92)
MSG_TYPE_QUEST_REWARD = 100  # 8% chance (92-100)

# =============================================================================
# CACHING
# =============================================================================
class ZoneDataCache:
    """Cache for zone-specific quest, loot, and mob data to avoid repeated DB queries."""

    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self.quest_cache: Dict[int, Tuple[List[dict], float]] = {}
        self.loot_cache: Dict[Tuple[int, int], Tuple[List[dict], float]] = {}
        self.mob_cache: Dict[Tuple[int, int], Tuple[List[str], float]] = {}

    def get_quests(self, zone_id: int) -> Optional[List[dict]]:
        """Get cached quests for zone, or None if expired/missing."""
        if zone_id in self.quest_cache:
            data, timestamp = self.quest_cache[zone_id]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    def set_quests(self, zone_id: int, quests: List[dict]):
        """Cache quests for zone."""
        self.quest_cache[zone_id] = (quests, time.time())

    def get_loot(self, min_level: int, max_level: int) -> Optional[List[dict]]:
        """Get cached loot for level range, or None if expired/missing."""
        key = (min_level, max_level)
        if key in self.loot_cache:
            data, timestamp = self.loot_cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    def set_loot(self, min_level: int, max_level: int, loot: List[dict]):
        """Cache loot for level range."""
        self.loot_cache[(min_level, max_level)] = (loot, time.time())

    def get_mobs(self, zone_id: int, bot_level: int) -> Optional[List[str]]:
        """Get cached mob names for zone, or None if expired/missing."""
        key = (zone_id, bot_level)
        if key in self.mob_cache:
            data, timestamp = self.mob_cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    def set_mobs(self, zone_id: int, bot_level: int, mobs: List[str]):
        """Cache mob names for zone."""
        self.mob_cache[(zone_id, bot_level)] = (mobs, time.time())

# Global cache instance
zone_cache = ZoneDataCache()


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


def get_db_connection(config: dict, database: str = None):
    """Create database connection from config."""
    return mysql.connector.connect(
        host=config.get('LLMChatter.Database.Host', 'localhost'),
        port=int(config.get('LLMChatter.Database.Port', 3306)),
        user=config.get('LLMChatter.Database.User', 'acore'),
        password=config.get('LLMChatter.Database.Password', 'acore'),
        database=database or config.get('LLMChatter.Database.Name', 'acore_characters')
    )


# =============================================================================
# ZONE DATA QUERIES
# =============================================================================
def get_zone_level_range(zone_id: int, bot_level: int) -> Tuple[int, int]:
    """Get level range for a zone, falling back to bot level if unknown."""
    if zone_id in ZONE_LEVELS:
        return ZONE_LEVELS[zone_id]
    # Fallback: use bot level +/- 5
    return (max(1, bot_level - 5), bot_level + 5)


def can_class_use_item(class_name: str, allowable_class: int) -> bool:
    """Check if a class can use an item based on AllowableClass bitmask."""
    # -1 or 0 means all classes can use
    if allowable_class in (-1, 0):
        return True
    # Get the class bitmask
    class_bit = CLASS_BITMASK.get(class_name, 0)
    if class_bit == 0:
        return True  # Unknown class, assume can use
    # Check if the class bit is set in allowable_class
    return (allowable_class & class_bit) != 0


def query_zone_quests(config: dict, zone_id: int, bot_level: int) -> List[dict]:
    """Query quests available in a zone with rewards."""
    # Check cache first
    cached = zone_cache.get_quests(zone_id)
    if cached is not None:
        return cached

    try:
        db = get_db_connection(config, 'acore_world')
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                q.ID as quest_id,
                q.LogTitle as quest_name,
                q.QuestLevel as quest_level,
                LEFT(q.LogDescription, 150) as description,
                q.RewardMoney as reward_money,
                i1.entry as item1_id,
                i1.name as item1_name,
                i1.Quality as item1_quality,
                i2.entry as item2_id,
                i2.name as item2_name,
                i2.Quality as item2_quality
            FROM quest_template q
            LEFT JOIN item_template i1 ON q.RewardItem1 = i1.entry
            LEFT JOIN item_template i2 ON q.RewardItem2 = i2.entry
            WHERE q.QuestSortID = %s
              AND q.QuestLevel BETWEEN %s AND %s
              AND q.LogTitle IS NOT NULL
              AND q.LogTitle != ''
              AND q.LogTitle NOT LIKE '<%%'
            ORDER BY RAND()
            LIMIT 20
        """, (zone_id, max(1, bot_level - 5), bot_level + 8))

        quests = cursor.fetchall()
        db.close()

        # Cache the results
        zone_cache.set_quests(zone_id, quests)
        return quests

    except Exception as e:
        logger.error(f"Error querying zone quests: {e}")
        return []


def query_zone_loot(config: dict, zone_id: int, bot_level: int) -> List[dict]:
    """
    Query loot appropriate for the zone level range.
    Includes all qualities (gray, white, green, blue, epic) with realistic distribution.
    """
    min_level, max_level = get_zone_level_range(zone_id, bot_level)

    # Check cache first
    cached = zone_cache.get_loot(zone_id, 0)
    if cached is not None:
        return cached

    try:
        db = get_db_connection(config, 'acore_world')
        cursor = db.cursor(dictionary=True)

        loot = []

        # Query 1: Gray/White items from creature loot (common drops)
        # Item classes: 2=weapon, 4=armor, 7=trade goods (cloth, leather, etc)
        cursor.execute("""
            SELECT DISTINCT
                i.entry as item_id,
                i.name as item_name,
                i.Quality as item_quality,
                i.AllowableClass as allowable_class,
                ct.name as drops_from
            FROM creature_template ct
            JOIN creature_loot_template clt ON ct.lootid = clt.Entry
            JOIN item_template i ON clt.Item = i.entry
            WHERE ct.minlevel >= %s AND ct.maxlevel <= %s
              AND i.Quality IN (0, 1)
              AND i.class IN (2, 4, 7)
              AND clt.Chance >= 5
            ORDER BY RAND()
            LIMIT 15
        """, (max(1, min_level - 3), max_level + 5))
        loot.extend(cursor.fetchall())

        # Query 2: Green/Blue/Epic items from reference loot tables (world drops)
        # Reference format: 102XXYY=green, 103XXYY=blue, 104XXYY=epic
        # The RequiredLevel filter ensures only appropriate items are returned
        green_ref_min = 1020000 + (min_level * 100) + min_level
        green_ref_max = 1020000 + (max_level * 100) + max_level
        blue_ref_min = 1030000 + (min_level * 100) + min_level
        blue_ref_max = 1030000 + (max_level * 100) + max_level
        epic_ref_min = 1040000 + (min_level * 100) + min_level
        epic_ref_max = 1040000 + (max_level * 100) + max_level

        # Include all quality tiers - DB is source of truth for what can drop
        ref_filter = f"""
            (rlt.Entry BETWEEN {green_ref_min} AND {green_ref_max}
             OR rlt.Entry BETWEEN {blue_ref_min} AND {blue_ref_max}
             OR rlt.Entry BETWEEN {epic_ref_min} AND {epic_ref_max})
        """

        cursor.execute(f"""
            SELECT DISTINCT
                i.entry as item_id,
                i.name as item_name,
                i.Quality as item_quality,
                i.AllowableClass as allowable_class,
                'world drop' as drops_from
            FROM reference_loot_template rlt
            JOIN item_template i ON rlt.Item = i.entry
            WHERE {ref_filter}
              AND i.class IN (2, 4)
              AND i.RequiredLevel BETWEEN %s AND %s
            ORDER BY RAND()
            LIMIT 15
        """, (max(1, min_level - 5), max_level + 5))
        loot.extend(cursor.fetchall())

        db.close()

        # Cache the results by zone
        zone_cache.set_loot(zone_id, 0, loot)
        return loot

    except Exception as e:
        logger.error(f"Error querying zone loot: {e}")
        return []


def query_zone_mobs(config: dict, zone_id: int, bot_level: int) -> List[str]:
    """
    Query hostile mob names from the specific zone.

    Uses a hybrid approach for community compatibility:
    1. First tries to query by zoneId (most accurate, requires Calculate.Creature.Zone.Area.Data = 1)
    2. Falls back to level-based query if zoneId isn't populated for the zone

    Returns a list of mob names that can be randomly selected for context.
    """
    min_level, max_level = get_zone_level_range(zone_id, bot_level)

    # Check cache first - use zone_id as part of key for zone-specific caching
    cached = zone_cache.get_mobs(zone_id, bot_level)
    if cached is not None:
        return cached

    try:
        db = get_db_connection(config, 'acore_world')
        cursor = db.cursor(dictionary=True)

        mobs = []

        # Common filters for hostile mobs
        # faction 14 = hostile to all, others are various hostile factions
        # type: 1=Beast, 2=Dragonkin, 4=Demon, 5=Elemental, 6=Giant, 7=Undead, 8=Humanoid, 10=Mechanical
        hostile_filter = """
            ct.faction IN (14, 16, 17, 21, 22, 24, 28, 32, 45, 48, 49, 50, 51, 54, 64, 91, 93)
            AND ct.type IN (1, 2, 4, 5, 6, 7, 8, 10)
            AND ct.unit_flags = 0
            AND ct.name NOT LIKE '%%Trigger%%'
            AND ct.name NOT LIKE '%%Invisible%%'
            AND ct.name NOT LIKE '%%Bunny%%'
            AND ct.name NOT LIKE '%%DND%%'
            AND ct.name NOT LIKE '%%(%%'
            AND ct.name NOT LIKE '%%[%%'
            AND ct.name NOT LIKE '%%<%%'
            AND LENGTH(ct.name) > 3
        """

        # APPROACH 1: Try zone-specific query using creature.zoneId
        # This is accurate but requires Calculate.Creature.Zone.Area.Data = 1 in worldserver.conf
        if zone_id > 0:
            cursor.execute(f"""
                SELECT DISTINCT ct.name
                FROM creature c
                JOIN creature_template ct ON c.id1 = ct.entry
                WHERE c.zoneId = %s
                  AND {hostile_filter}
                ORDER BY RAND()
                LIMIT 50
            """, (zone_id,))
            mobs = [row['name'] for row in cursor.fetchall()]

            if mobs:
                logger.debug(f"Found {len(mobs)} mobs for zone {zone_id} using zoneId")

        # APPROACH 2: Fall back to level-based query if zoneId not populated
        if not mobs:
            cursor.execute(f"""
                SELECT DISTINCT ct.name
                FROM creature_template ct
                WHERE ct.minlevel >= %s AND ct.maxlevel <= %s
                  AND {hostile_filter}
                ORDER BY RAND()
                LIMIT 50
            """, (max(1, min_level - 2), max_level + 3))
            mobs = [row['name'] for row in cursor.fetchall()]
            logger.debug(f"Using level-based fallback: {len(mobs)} mobs for level {min_level}-{max_level}")

        db.close()

        # Cache the results by zone_id
        zone_cache.set_mobs(zone_id, bot_level, mobs)
        return mobs

    except Exception as e:
        logger.error(f"Error querying zone mobs: {e}")
        return []


# =============================================================================
# LINK FORMATTING
# =============================================================================
def format_quest_link(quest_id: int, quest_level: int, quest_name: str) -> str:
    """Format a clickable quest link for WoW chat."""
    return f"|cFFFFFF00|Hquest:{quest_id}:{quest_level}|h[{quest_name}]|h|r"


def format_item_link(item_id: int, item_quality: int, item_name: str) -> str:
    """Format a clickable item link for WoW chat."""
    color = ITEM_QUALITY_COLORS.get(item_quality, "ffffff")
    return f"|c{color}|Hitem:{item_id}:0:0:0:0:0:0:0|h[{item_name}]|h|r"


def replace_placeholders(message: str, quest_data: dict = None, item_data: dict = None) -> str:
    """Replace {quest:...} and {item:...} placeholders with WoW links."""
    result = message

    # Replace quest placeholders: {quest:ID:Name} or {quest:Name}
    if quest_data:
        # Pattern for {quest:anything}
        quest_pattern = r'\{quest:[^}]+\}'
        if re.search(quest_pattern, result):
            link = format_quest_link(
                quest_data['quest_id'],
                quest_data.get('quest_level', 1),
                quest_data['quest_name']
            )
            result = re.sub(quest_pattern, link, result)

    # Replace item placeholders: {item:ID:Quality:Name} or {item:Name}
    if item_data:
        item_pattern = r'\{item:[^}]+\}'
        if re.search(item_pattern, result):
            link = format_item_link(
                item_data['item_id'],
                item_data.get('item_quality', 2),
                item_data['item_name']
            )
            result = re.sub(item_pattern, link, result)

    return result


def cleanup_message(message: str) -> str:
    """Clean up any formatting issues from LLM output."""
    result = message

    # Fix {[Name]} -> [Name] (curly braces around brackets)
    result = re.sub(r'\{\[([^\]]+)\]\}', r'[\1]', result)

    # Fix [[Name]] -> [Name] (double brackets)
    result = re.sub(r'\[\[([^\]]+)\]\]', r'[\1]', result)

    # Fix {Name} when it's not a placeholder (no quest: or item: prefix)
    # But preserve valid placeholders like {quest:Name} and {item:Name}
    result = re.sub(r'\{(?!quest:|item:)([^}]+)\}', r'\1', result)

    # Remove brackets around zone/faction names (common LLM mistake)
    # But NEVER touch brackets that are part of WoW links (inside |h...|h)
    # Keep brackets only if it looks like an NPC name (short, capitalized)
    def maybe_remove_brackets(match):
        full_match = match.group(0)
        content = match.group(1)
        start_pos = match.start()

        # Check if this bracket is part of a WoW link by looking for |h before it
        # WoW links have format: |h[Name]|h - so if |h precedes [, keep it
        prefix = result[max(0, start_pos-2):start_pos]
        if '|h' in prefix or prefix.endswith('|h'):
            return full_match  # Keep brackets - it's part of a WoW link

        # Keep brackets if it's a short NPC-like name (1-2 words, < 20 chars)
        words = content.split()
        if len(words) <= 2 and len(content) < 20:
            return f'[{content}]'
        # Remove brackets for longer phrases (likely quest/zone/faction names)
        return content

    result = re.sub(r'\[([^\]|]+)\]', maybe_remove_brackets, result)

    return result


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
    else:
        return "quest_reward"


# =============================================================================
# DYNAMIC DELAYS
# =============================================================================
def calculate_dynamic_delay(message_length: int, config: dict) -> float:
    """
    Calculate a realistic delay based on message length with randomness.
    Players are often busy killing mobs, so delays tend to be longer.
    But very short replies (ty, np, lol) can be quick.
    """
    min_delay = int(config.get('LLMChatter.MessageDelayMin', 1000)) / 1000.0
    max_delay = int(config.get('LLMChatter.MessageDelayMax', 15000)) / 1000.0

    # Very short messages (ty, np, lol, yes, no) - can be quick replies
    if message_length < 10:
        if random.random() < 0.3:
            return random.uniform(2.0, 4.0)
        else:
            return random.uniform(4.0, 10.0)

    # Short messages (< 30 chars) - moderate delays
    elif message_length < 30:
        typing_time = message_length / random.uniform(4.0, 7.0)
        distraction = random.triangular(2.0, 12.0, 8.0)
        return min(typing_time + distraction, max_delay)

    # Longer messages - longer delays
    else:
        typing_time = message_length / random.uniform(3.0, 6.0)
        distraction = random.triangular(4.0, 15.0, 10.0)
        return min(typing_time + distraction, max_delay)


# =============================================================================
# DYNAMIC PROMPT BUILDING
# =============================================================================
# Tone variations - affects the overall feel of the message
TONES = [
    "casual and relaxed",
    "slightly tired from grinding",
    "cheerful and social",
    "focused on gameplay",
    "a bit bored",
    "curious about the zone",
    "friendly and helpful",
    "mildly frustrated",
    "just vibing",
]

# Mood variations - the emotional angle of the message
MOODS = [
    "questioning",
    "complaining",
    "happy",
    "disappointed",
    "joking around",
    "slightly sarcastic",
    "enthusiastic",
    "confused",
    "proud",
    "neutral/matter-of-fact",
    "dramatic/exaggerating",
    "deadpan",
    "roleplaying (speaking in character)",
    "nostalgic",
    "impatient",
    "grateful",
    "showing off",
    "self-deprecating",
    "philosophical",
    "surprised/shocked",
    "helpful/mentoring",
]

# Example pools for plain statements - rotated randomly
PLAIN_EXAMPLE_SETS = [
    # Set A - Questions/Help
    [
        "anyone know where the flight path is",
        "how do i get to ironforge from here",
        "where do i learn cooking",
    ],
    # Set B - Social/LFG
    [
        "lfg anything",
        "need 1 more for elite quest",
        "any guild recruiting",
    ],
    # Set C - Reactions/Commentary
    [
        "this zone takes forever",
        "finally hit 20",
        "these respawns are brutal",
    ],
    # Set D - Casual/Humor
    [
        "just died to fall damage lol",
        "forgot to repair again",
        "why is my bags always full",
    ],
]

# Example pools for loot statements
LOOT_EXAMPLE_SETS = [
    # Set A - Excitement
    [
        "nice {item:X} just dropped",
        "finally got {item:X}!",
        "sweet {item:X}",
    ],
    # Set B - Meh/Vendor
    [
        "{item:X} more vendor trash",
        "another {item:X} lol",
        "{item:X} at least its gold",
    ],
    # Set C - Social
    [
        "anyone need {item:X}",
        "got {item:X} if someone wants",
        "{item:X} free to good home",
    ],
    # Set D - Class reaction
    [
        "{item:X} perfect for me",
        "{item:X} too bad wrong class",
        "{item:X} wish i could use it",
    ],
]

# Length hints
LENGTH_HINTS = [
    "very brief (3-6 words)",
    "short (5-10 words)",
    "one quick sentence",
    "brief but complete thought",
]

# Focus/emphasis options
FOCUS_OPTIONS = [
    "gameplay (quests, mobs, leveling)",
    "social (other players, groups, help)",
    "exploration (locations, travel, zones)",
    "loot and gear",
    "general chat and banter",
]


def pick_random_tone() -> str:
    """Pick a random tone for the message."""
    return random.choice(TONES)


def pick_random_mood() -> str:
    """Pick a random mood/emotional angle for the message."""
    return random.choice(MOODS)


def generate_conversation_mood_sequence(message_count: int) -> List[str]:
    """Generate a mood sequence for a conversation - each message gets a mood."""
    return [random.choice(MOODS) for _ in range(message_count)]


def pick_random_examples(example_sets: list, count: int = 2) -> list:
    """Pick random examples from random sets."""
    # Pick 1-2 random sets and sample from them
    selected_sets = random.sample(example_sets, min(2, len(example_sets)))
    all_examples = [ex for s in selected_sets for ex in s]
    return random.sample(all_examples, min(count, len(all_examples)))


def build_dynamic_guidelines(include_humor: bool = None,
                             include_length: bool = True,
                             include_focus: bool = None) -> list:
    """Build a randomized list of guidelines."""
    guidelines = [
        "Sound like a real player, not an NPC",
        "NEVER use brackets [] around quest names, item names, zone names, or faction names - write them as plain text. Only use brackets for NPC names like [Onu]. Only use {quest:Name} or {item:Name} placeholders when explicitly told to."
    ]

    # Length hint (usually include)
    if include_length and random.random() < 0.8:
        guidelines.append(f"Length: {random.choice(LENGTH_HINTS)}")

    # Humor (random chance)
    if include_humor is None:
        include_humor = random.random() < 0.25
    if include_humor:
        guidelines.append("A touch of humor fits here")

    # Focus (random chance)
    if include_focus is None:
        include_focus = random.random() < 0.3
    if include_focus:
        guidelines.append(f"Lean towards: {random.choice(FOCUS_OPTIONS)}")

    # Random extras
    extras = [
        "Abbreviations ok (lfg, lf, ty, np, lol)",
        "Can include a typo for realism",
        "Casual MMO chat style",
        "Brief and direct",
    ]
    if random.random() < 0.5:
        guidelines.append(random.choice(extras))

    return guidelines


# =============================================================================
# PROMPT BUILDERS
# =============================================================================
def build_plain_statement_prompt(bot: dict, mob_name: str = None) -> str:
    """Build a dynamically varied prompt for a plain text statement."""
    parts = []

    # Core context (always include zone)
    parts.append(f"Generate a brief WoW General chat message from a player in {bot['zone']}.")

    # Randomly include level (60% chance)
    if random.random() < 0.6:
        parts.append(f"Player level: {bot['level']}")

    # Mob context (if provided, make it optional)
    if mob_name:
        parts.append(f"A creature nearby: {mob_name} (may mention or ignore)")

    # Random tone and mood - these shape the personality
    parts.append(f"Tone: {pick_random_tone()}")
    parts.append(f"Mood: {pick_random_mood()}")

    # Pick random examples (2-3 from random sets)
    examples = pick_random_examples(PLAIN_EXAMPLE_SETS, random.randint(2, 3))
    parts.append("Example styles: " + ", ".join(f'"{ex}"' for ex in examples))

    # Build dynamic guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Plain text only, no formatting or links")
    guidelines.append("Do NOT mention your race or class")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append("Respond with ONLY the message, nothing else.")

    return "\n".join(parts)


def build_quest_statement_prompt(bot: dict, quest: dict) -> str:
    """Build a dynamically varied prompt for a quest statement."""
    parts = []

    parts.append(f"Generate a brief WoW General chat message mentioning a quest.")
    parts.append(f"Zone: {bot['zone']}")

    # Randomly include level
    if random.random() < 0.5:
        parts.append(f"Player level: {bot['level']}")

    # Quest info - make placeholder requirement very explicit
    quest_placeholder = f"{{{{quest:{quest['quest_name']}}}}}"
    parts.append(f"Quest: {quest['quest_name']}")
    parts.append(f"REQUIRED: Include exactly {quest_placeholder} in your message (this becomes a clickable link)")

    # Randomly include description
    if quest.get('description') and random.random() < 0.4:
        parts.append(f"Quest involves: {quest['description'][:80]}")

    # Random tone and mood
    parts.append(f"Tone: {pick_random_tone()}")
    parts.append(f"Mood: {pick_random_mood()}")

    # Quest-specific example actions
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
        parts.append(f"Approach: {random.choice(quest_actions)}")

    # Guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Keep under 60 characters")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append(f"Example: anyone done {quest_placeholder} yet? seems rough")
    parts.append("Respond with ONLY the message.")

    return "\n".join(parts)


def build_loot_statement_prompt(bot: dict, item: dict, can_use: bool) -> str:
    """Build a dynamically varied prompt for a loot statement."""
    quality_names = {0: "gray", 1: "white", 2: "green", 3: "blue", 4: "purple"}
    quality = quality_names.get(item.get('item_quality', 2), "green")

    parts = []

    item_placeholder = f"{{{{item:{item['item_name']}}}}}"
    parts.append(f"Generate a brief WoW General chat message about a loot drop.")
    parts.append(f"Item: {item['item_name']} ({quality} quality)")
    parts.append(f"REQUIRED: Include exactly {item_placeholder} in your message (this becomes a clickable link)")

    # Randomly include class info (60% chance)
    if random.random() < 0.6:
        parts.append(f"Player class: {bot['class']}")
        # Only sometimes mention usability (40% of class mentions)
        if random.random() < 0.4:
            usability = "can equip" if can_use else "cannot equip (wrong class)"
            parts.append(f"Class fit: {usability}")

    # Random tone and mood
    parts.append(f"Tone: {pick_random_tone()}")
    parts.append(f"Mood: {pick_random_mood()}")

    # Pick examples from loot sets
    examples = pick_random_examples(LOOT_EXAMPLE_SETS, 2)
    parts.append("Example styles: " + ", ".join(f'"{ex}"' for ex in examples))

    # Loot-specific reactions to vary
    reactions = [
        "excitement about the drop",
        "meh, vendor fodder",
        "offering to trade/give away",
        "commenting on luck (good or bad)",
        "just mentioning what dropped",
    ]
    if random.random() < 0.5:
        parts.append(f"Reaction style: {random.choice(reactions)}")

    # Guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Keep under 60 characters")
    parts.append("Guidelines: " + "; ".join(guidelines))
    parts.append(f"Example: nice {item_placeholder} just dropped lol")

    parts.append("Respond with ONLY the message.")

    return "\n".join(parts)


def build_quest_reward_statement_prompt(bot: dict, quest: dict) -> str:
    """Build a dynamically varied prompt for quest completion with reward."""
    # Get reward item info
    item_name = quest.get('item1_name') or quest.get('item2_name')
    item_quality = quest.get('item1_quality') or quest.get('item2_quality') or 2

    if not item_name:
        # Fallback to plain quest if no item reward
        return build_quest_statement_prompt(bot, quest)

    quality_names = {0: "gray", 1: "white", 2: "green", 3: "blue", 4: "purple"}
    quality = quality_names.get(item_quality, "green")

    parts = []

    parts.append(f"Generate a brief WoW General chat message about finishing a quest.")
    parts.append(f"Quest: {quest['quest_name']} (use {{{{quest:{quest['quest_name']}}}}} placeholder)")
    parts.append(f"Reward: {item_name} ({quality}) (use {{{{item:{item_name}}}}} placeholder)")

    # Randomly include class (50% chance)
    if random.random() < 0.5:
        parts.append(f"Player class: {bot['class']}")

    # Random tone and mood
    parts.append(f"Tone: {pick_random_tone()}")
    parts.append(f"Mood: {pick_random_mood()}")

    # Completion reactions
    reactions = [
        "relief at finishing",
        "excitement about reward",
        "meh about the reward",
        "just noting completion",
        "sharing the achievement",
    ]
    if random.random() < 0.5:
        parts.append(f"Reaction: {random.choice(reactions)}")

    # Guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Use BOTH placeholders, each once")
    guidelines.append("Keep under 70 characters")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append("Respond with ONLY the message.")

    return "\n".join(parts)


def build_plain_conversation_prompt(bot1: dict, bot2: dict, mob_name: str = None) -> str:
    """Build a dynamically varied prompt for a plain conversation."""
    parts = []

    parts.append(f"Generate a casual General chat exchange between two WoW players in {bot1['zone']}.")
    parts.append(f"Speakers: {bot1['name']} and {bot2['name']}")

    # Randomly include some character details
    if random.random() < 0.4:
        parts.append(f"{bot1['name']} is a {bot1['race']} {bot1['class']}")
    if random.random() < 0.4:
        parts.append(f"{bot2['name']} is a {bot2['race']} {bot2['class']}")

    # Mob context (if provided)
    if mob_name:
        parts.append(f"A creature in the area: {mob_name} (may be mentioned)")

    # Random tone for the overall conversation
    parts.append(f"Overall tone: {pick_random_tone()}")

    # Generate mood sequence - this is the "script" the LLM must follow
    msg_count = random.randint(2, 5)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    parts.append(f"\nMOOD SEQUENCE (follow this for each message):")
    for i, mood in enumerate(mood_sequence):
        speaker = bot1['name'] if i % 2 == 0 else bot2['name']
        parts.append(f"  Message {i+1} ({speaker}): {mood}")

    # Conversation topics to suggest
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
        parts.append(f"Topic hint: {random.choice(topics)}")

    # Guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Plain text only")
    guidelines.append("Follow the mood sequence above")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {{"speaker": "{bot1['name']}", "message": "..."}},
  {{"speaker": "{bot2['name']}", "message": "..."}}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_quest_conversation_prompt(bot1: dict, bot2: dict, quest: dict) -> str:
    """Build a dynamically varied prompt for a quest conversation."""
    parts = []

    parts.append(f"Generate a casual General chat exchange about a quest in {bot1['zone']}.")
    parts.append(f"Speakers: {bot1['name']} and {bot2['name']}")

    # Quest info
    parts.append(f"Quest: {quest['quest_name']} (use {{{{quest:{quest['quest_name']}}}}} placeholder)")
    if quest.get('description') and random.random() < 0.4:
        parts.append(f"Quest involves: {quest['description'][:60]}")

    # Random tone for the overall conversation
    parts.append(f"Overall tone: {pick_random_tone()}")

    # Generate mood sequence - the "script" for the conversation
    msg_count = random.randint(2, 5)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    parts.append(f"\nMOOD SEQUENCE (follow this for each message):")
    for i, mood in enumerate(mood_sequence):
        speaker = bot1['name'] if i % 2 == 0 else bot2['name']
        parts.append(f"  Message {i+1} ({speaker}): {mood}")

    # Quest conversation angles
    angles = [
        "asking for help with the quest",
        "sharing where to find objectives",
        "complaining about quest difficulty",
        "discussing rewards",
        "warning about dangers",
        "celebrating completion",
    ]
    if random.random() < 0.5:
        parts.append(f"Angle hint: {random.choice(angles)}")

    # Guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Use quest placeholder at least once")
    guidelines.append("Follow the mood sequence above")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {{"speaker": "{bot1['name']}", "message": "..."}},
  {{"speaker": "{bot2['name']}", "message": "..."}}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


# =============================================================================
# LLM INTERACTION
# =============================================================================

# Model aliases for easy config
MODEL_ALIASES = {
    # Anthropic
    'opus': 'claude-opus-4-5-20251001',
    'sonnet': 'claude-sonnet-4-20250514',
    'haiku': 'claude-haiku-4-5-20251001',
    # OpenAI
    'gpt4o': 'gpt-4o',
    'gpt4o-mini': 'gpt-4o-mini',
}


def resolve_model(model_name: str) -> str:
    """Resolve model alias to full model name."""
    return MODEL_ALIASES.get(model_name, model_name)


def call_llm(client: Any, prompt: str, config: dict) -> str:
    """Call LLM API (Anthropic or OpenAI) and return response."""
    provider = config.get('LLMChatter.Provider', 'anthropic').lower()
    model_alias = config.get('LLMChatter.Model', 'haiku')
    model = resolve_model(model_alias)
    max_tokens = int(config.get('LLMChatter.MaxTokens', 200))
    temperature = float(config.get('LLMChatter.Temperature', 0.85))

    try:
        if provider == 'openai':
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        else:
            # Anthropic (default)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"LLM API error ({provider}): {e}")
        return None


def parse_conversation_response(response: str, bot1_name: str, bot2_name: str) -> list:
    """Parse conversation JSON response into message list."""
    try:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            messages = json.loads(json_match.group())
            result = []
            for msg in messages:
                speaker = msg.get('speaker', '').strip()
                message = msg.get('message', '').strip()
                if speaker and message:
                    if speaker.lower() == bot1_name.lower():
                        result.append({'name': bot1_name, 'message': message})
                    elif speaker.lower() == bot2_name.lower():
                        result.append({'name': bot2_name, 'message': message})
            return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse conversation JSON: {e}")
        logger.debug(f"Response was: {response}")
    return []


# =============================================================================
# REQUEST PROCESSING
# =============================================================================
def process_statement(db, cursor, client, config, request, bot: dict):
    """Process a single statement request."""
    channel = 'general'

    # Select message type
    msg_type = select_message_type()
    logger.info(f"Statement type: {msg_type}")

    # Get zone data if needed
    quest_data = None
    item_data = None

    if msg_type == "quest" or msg_type == "quest_reward":
        quests = query_zone_quests(config, request.get('zone_id', 0), bot['level'])
        if quests:
            quest_data = random.choice(quests)
            logger.info(f"Selected quest: {quest_data['quest_name']}")
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "loot":
        loot = query_zone_loot(config, request.get('zone_id', 0), bot['level'])
        if loot:
            # Weight selection by quality - epics should be rare
            # Quality: 0=gray, 1=white, 2=green, 3=blue, 4=epic
            quality_weights = {0: 30, 1: 30, 2: 25, 3: 12, 4: 3}  # Epic only 3%
            weights = [quality_weights.get(item.get('item_quality', 2), 10) for item in loot]
            item_data = random.choices(loot, weights=weights, k=1)[0]
            # Check if bot's class can use the item
            item_can_use = can_class_use_item(bot['class'], item_data.get('allowable_class', -1))
            quality_names = {0: "gray", 1: "white", 2: "green", 3: "blue", 4: "epic"}
            logger.info(f"Selected loot: {item_data['item_name']} ({quality_names.get(item_data.get('item_quality', 2), 'unknown')}) - {bot['class']} can use: {item_can_use}")
        else:
            msg_type = "plain"  # Fallback

    # Build appropriate prompt
    if msg_type == "plain":
        # Get a random mob from the zone for context (50% chance to include)
        mob_name = None
        if random.random() < 0.5:
            mobs = query_zone_mobs(config, request.get('zone_id', 0), bot['level'])
            if mobs:
                mob_name = random.choice(mobs)
                logger.debug(f"Including mob context: {mob_name}")
        prompt = build_plain_statement_prompt(bot, mob_name)
    elif msg_type == "quest":
        prompt = build_quest_statement_prompt(bot, quest_data)
    elif msg_type == "loot":
        prompt = build_loot_statement_prompt(bot, item_data, item_can_use)
    elif msg_type == "quest_reward":
        prompt = build_quest_reward_statement_prompt(bot, quest_data)
        # Also set item_data for replacement
        if quest_data and quest_data.get('item1_name'):
            item_data = {
                'item_id': quest_data['item1_id'],
                'item_name': quest_data['item1_name'],
                'item_quality': quest_data.get('item1_quality', 2)
            }
    else:
        prompt = build_plain_statement_prompt(bot)

    # Call LLM
    response = call_llm(client, prompt, config)

    if response:
        # Clean and replace placeholders
        message = response.strip().strip('"').strip()
        message = replace_placeholders(message, quest_data, item_data)
        message = cleanup_message(message)

        logger.info(f"Statement from {bot['name']} [{msg_type}]: {message}")

        # Insert for delivery
        cursor.execute("""
            INSERT INTO llm_chatter_messages
            (queue_id, sequence, bot_guid, bot_name, message, channel, deliver_at)
            VALUES (%s, 0, %s, %s, %s, %s, NOW())
        """, (request['id'], bot['guid'], bot['name'], message, channel))

        return True
    return False


def process_conversation(db, cursor, client, config, request, bot1: dict, bot2: dict):
    """Process a conversation request."""
    channel = 'general'

    # Select message type (conversations can be plain or quest-related)
    roll = random.randint(1, 100)
    if roll <= 75:
        msg_type = "plain"
    else:
        msg_type = "quest"

    logger.info(f"Conversation type: {msg_type}")

    # Get quest data if needed
    quest_data = None
    if msg_type == "quest":
        quests = query_zone_quests(config, request.get('zone_id', 0), bot1['level'])
        if quests:
            quest_data = random.choice(quests)
            logger.info(f"Selected quest: {quest_data['quest_name']}")
        else:
            msg_type = "plain"

    # Build prompt
    if msg_type == "plain":
        # Get a random mob from the zone for context (50% chance to include)
        mob_name = None
        if random.random() < 0.5:
            mobs = query_zone_mobs(config, request.get('zone_id', 0), bot1['level'])
            if mobs:
                mob_name = random.choice(mobs)
                logger.debug(f"Including mob context in conversation: {mob_name}")
        prompt = build_plain_conversation_prompt(bot1, bot2, mob_name)
    else:
        prompt = build_quest_conversation_prompt(bot1, bot2, quest_data)

    # Call LLM
    response = call_llm(client, prompt, config)

    if response:
        messages = parse_conversation_response(response, bot1['name'], bot2['name'])

        if messages:
            logger.info(f"Conversation in {bot1['zone']} with {len(messages)} messages:")

            cumulative_delay = 0.0
            for i, msg in enumerate(messages):
                bot_guid = bot1['guid'] if msg['name'] == bot1['name'] else bot2['guid']

                # Replace placeholders and cleanup
                final_message = replace_placeholders(msg['message'], quest_data, None)
                final_message = cleanup_message(final_message)

                if i > 0:
                    delay = calculate_dynamic_delay(len(final_message), config)
                    cumulative_delay += delay

                cursor.execute("""
                    INSERT INTO llm_chatter_messages
                    (queue_id, sequence, bot_guid, bot_name, message, channel, deliver_at)
                    VALUES (%s, %s, %s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL %s SECOND))
                """, (request['id'], i, bot_guid, msg['name'], final_message, channel, cumulative_delay))

                logger.info(f"  [{i}] +{cumulative_delay:.1f}s {msg['name']}: {final_message}")

            return True
    return False


def process_pending_requests(db, client: anthropic.Anthropic, config: dict):
    """Process all pending chatter requests."""
    cursor = db.cursor(dictionary=True)

    # Get pending requests
    cursor.execute("""
        SELECT * FROM llm_chatter_queue
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT 1
    """)
    request = cursor.fetchone()

    if not request:
        return False

    request_id = request['id']
    request_type = request['request_type']

    logger.info(f"Processing {request_type} request #{request_id}")

    # Mark as processing
    cursor.execute(
        "UPDATE llm_chatter_queue SET status = 'processing' WHERE id = %s",
        (request_id,)
    )
    db.commit()

    try:
        # Get zone_id from the request (added to queue table)
        zone_id = request.get('zone_id', 0)
        request['zone_id'] = zone_id if zone_id else 0

        if request_type == 'statement':
            bot = {
                'guid': request['bot1_guid'],
                'name': request['bot1_name'],
                'class': request['bot1_class'],
                'race': request['bot1_race'],
                'level': request['bot1_level'],
                'zone': request['bot1_zone']
            }
            success = process_statement(db, cursor, client, config, request, bot)
        else:
            bot1 = {
                'guid': request['bot1_guid'],
                'name': request['bot1_name'],
                'class': request['bot1_class'],
                'race': request['bot1_race'],
                'level': request['bot1_level'],
                'zone': request['bot1_zone']
            }
            bot2 = {
                'guid': request['bot2_guid'],
                'name': request['bot2_name'],
                'class': request['bot2_class'],
                'race': request['bot2_race'],
                'level': request['bot2_level'],
                'zone': request['bot1_zone']
            }
            success = process_conversation(db, cursor, client, config, request, bot1, bot2)

        # Mark as completed
        cursor.execute(
            "UPDATE llm_chatter_queue SET status = 'completed', processed_at = NOW() WHERE id = %s",
            (request_id,)
        )
        db.commit()
        return True

    except Exception as e:
        logger.error(f"Error processing request #{request_id}: {e}")
        import traceback
        traceback.print_exc()
        cursor.execute(
            "UPDATE llm_chatter_queue SET status = 'failed' WHERE id = %s",
            (request_id,)
        )
        db.commit()
        return False


# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description='LLM Chatter Bridge')
    parser.add_argument('--config', required=True, help='Path to config file')
    args = parser.parse_args()

    # Load config
    config = parse_config(args.config)

    # Check if enabled
    if config.get('LLMChatter.Enable', '0') != '1':
        logger.info("LLMChatter is disabled in config. Exiting.")
        sys.exit(0)

    # Get API key
    # Get provider and initialize appropriate client
    provider = config.get('LLMChatter.Provider', 'anthropic').lower()
    model_alias = config.get('LLMChatter.Model', 'haiku')
    model = resolve_model(model_alias)

    if provider == 'openai':
        api_key = config.get('LLMChatter.OpenAI.ApiKey', '')
        if not api_key:
            logger.error("No OpenAI API key configured!")
            sys.exit(1)
        client = openai.OpenAI(api_key=api_key)
    else:
        # Anthropic (default)
        api_key = config.get('LLMChatter.Anthropic.ApiKey', '')
        if not api_key:
            logger.error("No Anthropic API key configured!")
            sys.exit(1)
        client = anthropic.Anthropic(api_key=api_key)

    # Get poll interval
    poll_interval = int(config.get('LLMChatter.Bridge.PollIntervalSeconds', 3))

    logger.info("=" * 60)
    logger.info("LLM Chatter Bridge v3.0 - Multi-Provider Support")
    logger.info("=" * 60)
    logger.info(f"Provider: {provider}")
    logger.info(f"Model: {model} (alias: {model_alias})")
    logger.info(f"Poll interval: {poll_interval}s")
    logger.info(f"Message type distribution: {MSG_TYPE_PLAIN}% plain, "
                f"{MSG_TYPE_QUEST - MSG_TYPE_PLAIN}% quest, "
                f"{MSG_TYPE_LOOT - MSG_TYPE_QUEST}% loot, "
                f"{MSG_TYPE_QUEST_REWARD - MSG_TYPE_LOOT}% quest+reward")
    logger.info("=" * 60)

    # Main loop
    while True:
        try:
            db = get_db_connection(config)
            processed = process_pending_requests(db, client, config)
            db.close()

            if not processed:
                time.sleep(poll_interval)

        except mysql.connector.Error as e:
            logger.error(f"Database error: {e}")
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(poll_interval)


if __name__ == '__main__':
    main()
