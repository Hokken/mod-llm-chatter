"""
Chatter Shared - Shared utilities, DB, LLM, queries for the LLM Chatter Bridge.

Imports from chatter_constants only. No circular dependencies.
"""

import json
import logging
import random
import re
import sys
import time
from typing import Optional, Dict, List, Tuple, Any

import anthropic
import openai
import mysql.connector

from chatter_constants import (
    ZONE_LEVELS, ZONE_COORDINATES, ZONE_NAMES,
    CAPITAL_CITY_ZONES,
    CLASS_NAMES, RACE_NAMES, CLASS_IDS,
    RACE_SPEECH_PROFILES, CLASS_SPEECH_MODIFIERS,
    CLASS_ROLE_MAP, ROLE_COMBAT_PERSPECTIVES,
    ZONE_FLAVOR, DUNGEON_FLAVOR,
    ITEM_QUALITY_COLORS, CLASS_BITMASK,
    MSG_TYPE_PLAIN, MSG_TYPE_QUEST, MSG_TYPE_LOOT,
    MSG_TYPE_QUEST_REWARD, MSG_TYPE_TRADE,
    MSG_TYPE_SPELL,
    DEFAULT_ANTHROPIC_MODEL, DEFAULT_OPENAI_MODEL,
    ZONE_TRANSPORT_COOLDOWN_SECONDS,
    EMOTE_LIST, EMOTE_KEYWORDS,
    EMOTE_LIST_STR,
)
from spell_names import SPELL_NAMES, SPELL_DESCRIPTIONS

logger = logging.getLogger(__name__)


# =============================================================================
# GLOBAL MUTABLE STATE
# =============================================================================

# Zone-level transport cooldowns (in-memory, resets on bridge restart)
# Key: zone_id, Value: timestamp of last transport announcement
_zone_transport_cooldowns: Dict[int, float] = {}


# =============================================================================
# CACHING
# =============================================================================
class ZoneDataCache:
    """Cache for zone-specific quest, loot, and mob data."""

    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self.quest_cache: Dict[int, Tuple[List[dict], float]] = {}
        self.loot_cache: Dict[Tuple[int, int], Tuple[List[dict], float]] = {}
        self.mob_cache: Dict[Tuple[int, int], Tuple[List[str], float]] = {}
        self.recent_loot: Dict[int, Dict[int, float]] = {}

    def get_quests(self, zone_id: int) -> Optional[List[dict]]:
        if zone_id in self.quest_cache:
            data, timestamp = self.quest_cache[zone_id]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    def set_quests(self, zone_id: int, quests: List[dict]):
        self.quest_cache[zone_id] = (quests, time.time())

    def get_loot(
        self, min_level: int, max_level: int
    ) -> Optional[List[dict]]:
        key = (min_level, max_level)
        if key in self.loot_cache:
            data, timestamp = self.loot_cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    def set_loot(
        self, min_level: int, max_level: int, loot: List[dict]
    ):
        self.loot_cache[(min_level, max_level)] = (loot, time.time())

    def get_mobs(
        self, zone_id: int, bot_level: int
    ) -> Optional[List[str]]:
        key = (zone_id, bot_level)
        if key in self.mob_cache:
            data, timestamp = self.mob_cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    def set_mobs(
        self, zone_id: int, bot_level: int, mobs: List[str]
    ):
        self.mob_cache[(zone_id, bot_level)] = (mobs, time.time())

    def get_recent_loot_ids(
        self, zone_id: int, cooldown_seconds: int
    ) -> set:
        now = time.time()
        if zone_id not in self.recent_loot:
            return set()
        recent = {
            item_id: ts
            for item_id, ts in self.recent_loot[zone_id].items()
            if now - ts < cooldown_seconds
        }
        self.recent_loot[zone_id] = recent
        return set(recent.keys())

    def mark_loot_seen(self, zone_id: int, item_id: int):
        if zone_id not in self.recent_loot:
            self.recent_loot[zone_id] = {}
        self.recent_loot[zone_id][item_id] = time.time()


# Global cache instance
zone_cache = ZoneDataCache()


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
        parts.append(
            f"As a {race}, you tend to be {profile['traits']}. "
            f"You might occasionally use words like: "
            f"{', '.join(profile['flavor_words'])} "
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


def get_db_connection(config: dict, database: str = None):
    """Create database connection from config."""
    return mysql.connector.connect(
        host=config.get('LLMChatter.Database.Host', 'localhost'),
        port=int(config.get('LLMChatter.Database.Port', 3306)),
        user=config.get('LLMChatter.Database.User', 'acore'),
        password=config.get(
            'LLMChatter.Database.Password', 'acore'
        ),
        database=database or config.get(
            'LLMChatter.Database.Name', 'acore_characters'
        )
    )


def wait_for_database(
    config: dict,
    max_retries: int = 30,
    initial_delay: float = 2.0
) -> bool:
    """Wait for database to become available with exponential backoff."""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_db_connection(config)
            conn.close()
            logger.info(
                f"Database connection established "
                f"(attempt {attempt})"
            )
            return True
        except mysql.connector.Error as e:
            if attempt == max_retries:
                logger.error(
                    f"Failed to connect to database after "
                    f"{max_retries} attempts: {e}"
                )
                return False
            logger.info(
                f"Waiting for database... "
                f"(attempt {attempt}/{max_retries}, "
                f"retry in {delay:.1f}s)"
            )
            time.sleep(delay)
            delay = min(delay * 1.5, 30.0)

    return False


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
    acore_world (rank=3 = boss). Results are
    cached since boss lists never change.
    """
    if map_id in _dungeon_boss_cache:
        return _dungeon_boss_cache[map_id]

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT ct.name
            FROM acore_world.creature c
            JOIN acore_world.creature_template ct
                ON c.id1 = ct.entry
            WHERE c.map = %s AND ct.rank = 3
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


def query_zone_quests(
    config: dict, zone_id: int, bot_level: int
) -> List[dict]:
    """Query quests available in a zone with rewards."""
    cached = zone_cache.get_quests(zone_id)
    if cached is not None:
        return cached

    try:
        db = get_db_connection(config, 'acore_world')
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                MIN(q.ID) as quest_id,
                q.LogTitle as quest_name,
                MIN(q.QuestLevel) as quest_level,
                MIN(LEFT(q.LogDescription, 150)) as description,
                MIN(q.RewardMoney) as reward_money,
                MIN(i1.entry) as item1_id,
                MIN(i1.name) as item1_name,
                MIN(i1.Quality) as item1_quality,
                MIN(i2.entry) as item2_id,
                MIN(i2.name) as item2_name,
                MIN(i2.Quality) as item2_quality
            FROM quest_template q
            LEFT JOIN item_template i1
                ON q.RewardItem1 = i1.entry
            LEFT JOIN item_template i2
                ON q.RewardItem2 = i2.entry
            WHERE q.QuestSortID = %s
              AND q.QuestLevel BETWEEN %s AND %s
              AND q.LogTitle IS NOT NULL
              AND q.LogTitle != ''
              AND q.LogTitle NOT LIKE '<%%'
            GROUP BY q.LogTitle
            ORDER BY RAND()
            LIMIT 20
        """, (zone_id, max(1, bot_level - 5), bot_level + 8))

        quests = cursor.fetchall()
        db.close()

        zone_cache.set_quests(zone_id, quests)
        return quests

    except Exception as e:
        logger.error(f"Error querying zone quests: {e}")
        return []


def query_zone_loot(
    config: dict, zone_id: int, bot_level: int
) -> List[dict]:
    """Query loot appropriate for the zone."""
    # No loot drops in capital cities
    if zone_id in CAPITAL_CITY_ZONES:
        return []

    min_level, max_level = get_zone_level_range(zone_id, bot_level)

    cached = zone_cache.get_loot(zone_id, 0)
    if cached is not None:
        return cached

    try:
        db = get_db_connection(config, 'acore_world')
        cursor = db.cursor(dictionary=True)

        loot = []

        if zone_id in ZONE_COORDINATES:
            map_id, min_x, max_x, min_y, max_y = (
                ZONE_COORDINATES[zone_id]
            )
            cursor.execute("""
                SELECT DISTINCT
                    i.entry as item_id,
                    i.name as item_name,
                    i.Quality as item_quality,
                    i.AllowableClass as allowable_class,
                    i.SellPrice as sell_price,
                    ct.name as drops_from
                FROM creature c
                JOIN creature_template ct ON c.id1 = ct.entry
                JOIN creature_loot_template clt
                    ON ct.lootid = clt.Entry
                JOIN item_template i ON clt.Item = i.entry
                WHERE c.map = %s
                  AND c.position_x BETWEEN %s AND %s
                  AND c.position_y BETWEEN %s AND %s
                  AND ct.minlevel >= %s
                  AND ct.maxlevel <= %s
                  AND i.Quality IN (0, 1)
                  AND i.class IN (2, 4, 7)
                  AND clt.Chance >= 5
                ORDER BY RAND()
                LIMIT 15
            """, (
                map_id, min_x, max_x, min_y, max_y,
                max(1, min_level - 3), max_level + 5
            ))
            loot.extend(cursor.fetchall())
        else:
            cursor.execute("""
                SELECT DISTINCT
                    i.entry as item_id,
                    i.name as item_name,
                    i.Quality as item_quality,
                    i.AllowableClass as allowable_class,
                    i.SellPrice as sell_price,
                    ct.name as drops_from
                FROM creature_template ct
                JOIN creature_loot_template clt
                    ON ct.lootid = clt.Entry
                JOIN item_template i ON clt.Item = i.entry
                WHERE ct.minlevel >= %s
                  AND ct.maxlevel <= %s
                  AND i.Quality IN (0, 1)
                  AND i.class IN (2, 4, 7)
                  AND clt.Chance >= 5
                ORDER BY RAND()
                LIMIT 15
            """, (max(1, min_level - 3), max_level + 5))
            loot.extend(cursor.fetchall())

        # Green/Blue/Epic from reference loot tables
        green_ref_min = 1020000 + (min_level * 100) + min_level
        green_ref_max = 1020000 + (max_level * 100) + max_level
        blue_ref_min = 1030000 + (min_level * 100) + min_level
        blue_ref_max = 1030000 + (max_level * 100) + max_level
        epic_ref_min = 1040000 + (min_level * 100) + min_level
        epic_ref_max = 1040000 + (max_level * 100) + max_level

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
                i.SellPrice as sell_price,
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

        zone_cache.set_loot(zone_id, 0, loot)
        return loot

    except Exception as e:
        logger.error(f"Error querying zone loot: {e}")
        return []


def query_zone_mobs(
    config: dict, zone_id: int, bot_level: int
) -> List[str]:
    """Query hostile mob names from the specific zone."""
    # No hostile creatures in capital cities
    if zone_id in CAPITAL_CITY_ZONES:
        return []

    min_level, max_level = get_zone_level_range(zone_id, bot_level)

    cached = zone_cache.get_mobs(zone_id, bot_level)
    if cached is not None:
        return cached

    try:
        db = get_db_connection(config, 'acore_world')
        cursor = db.cursor(dictionary=True)

        mobs = []

        mob_filter = """
            ct.type IN (1, 2, 3, 4, 5, 6, 7, 9, 10)
            AND ct.faction NOT IN (
                35, 55, 79, 80, 84, 126, 875, 876, 1078, 1080
            )
            AND ct.unit_flags = 0
            AND ct.npcflag = 0
            AND ct.name NOT LIKE '%%Trigger%%'
            AND ct.name NOT LIKE '%%Invisible%%'
            AND ct.name NOT LIKE '%%Bunny%%'
            AND ct.name NOT LIKE '%%DND%%'
            AND ct.name NOT LIKE '%%Spirit%%'
            AND ct.name NOT LIKE '%%Quest%%'
            AND ct.name NOT LIKE '%%(%%'
            AND ct.name NOT LIKE '%%[%%'
            AND ct.name NOT LIKE '%%<%%'
            AND LENGTH(ct.name) > 3
        """

        if zone_id in ZONE_COORDINATES:
            map_id, min_x, max_x, min_y, max_y = (
                ZONE_COORDINATES[zone_id]
            )
            cursor.execute(f"""
                SELECT DISTINCT ct.entry, ct.name
                FROM creature c
                JOIN creature_template ct ON c.id1 = ct.entry
                WHERE c.map = %s
                  AND c.position_x BETWEEN %s AND %s
                  AND c.position_y BETWEEN %s AND %s
                  AND ct.minlevel >= %s
                  AND ct.maxlevel <= %s
                  AND {mob_filter}
                ORDER BY RAND()
                LIMIT 50
            """, (
                map_id, min_x, max_x, min_y, max_y,
                max(1, min_level - 3), max_level + 5
            ))
            mobs = [
                f"[[npc:{row['entry']}:{row['name']}]]"
                for row in cursor.fetchall()
            ]

            if mobs:
                logger.info(
                    f"Found {len(mobs)} mobs for zone "
                    f"{zone_id} using coordinates"
                )

        if not mobs:
            cursor.execute(f"""
                SELECT DISTINCT ct.entry, ct.name
                FROM creature_template ct
                WHERE ct.minlevel >= %s
                  AND ct.maxlevel <= %s
                  AND {mob_filter}
                ORDER BY RAND()
                LIMIT 50
            """, (max(1, min_level - 2), max_level + 3))
            mobs = [
                f"[[npc:{row['entry']}:{row['name']}]]"
                for row in cursor.fetchall()
            ]
            logger.debug(
                f"Using level-based fallback: {len(mobs)} mobs "
                f"for level {min_level}-{max_level}"
            )

        db.close()

        zone_cache.set_mobs(zone_id, bot_level, mobs)
        return mobs

    except Exception as e:
        logger.error(f"Error querying zone mobs: {e}")
        return []


# =============================================================================
# SPELL QUERIES
# =============================================================================
def query_bot_spells(
    config: dict,
    class_name: str,
    bot_level: int
) -> List[dict]:
    """Query class-appropriate spells for a bot.

    Uses trainer_spell + spell_dbc from acore_world,
    falling back to SPELL_NAMES dict for missing names.
    """
    class_id = CLASS_IDS.get(class_name)
    if not class_id:
        return []

    try:
        db = get_db_connection(config, 'acore_world')
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT
                ts.SpellId as spell_id,
                ts.ReqLevel as req_level,
                COALESCE(
                    sd.Name_Lang_enUS, NULL
                ) as spell_name
            FROM trainer t
            JOIN trainer_spell ts
                ON t.Id = ts.TrainerId
            LEFT JOIN spell_dbc sd
                ON ts.SpellId = sd.ID
            WHERE t.Type = 0
              AND t.Requirement = %s
              AND ts.ReqLevel <= %s
              AND ts.ReqLevel > 0
            ORDER BY RAND()
            LIMIT 10
        """, (class_id, bot_level))

        spells = cursor.fetchall()
        db.close()

        # Fill in missing names from SPELL_NAMES dict
        # and add descriptions for richer prompts
        result = []
        for spell in spells:
            name = spell.get('spell_name')
            if not name:
                name = SPELL_NAMES.get(
                    spell['spell_id']
                )
            if name:
                desc = SPELL_DESCRIPTIONS.get(
                    spell['spell_id'], ''
                )
                result.append({
                    'spell_id': spell['spell_id'],
                    'spell_name': name,
                    'spell_desc': desc,
                    'req_level': spell['req_level'],
                })

        return result

    except Exception as e:
        logger.error(
            f"Error querying bot spells: {e}"
        )
        return []


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


def strip_speaker_prefix(message: str, bot_name: str) -> str:
    """Strip 'BotName:' prefix that LLMs sometimes add."""
    if message.startswith(f"{bot_name}:"):
        return message[len(bot_name) + 1:].strip()
    return message


# Module-level action chance (set from config at startup)
_action_chance = 0.10


def set_action_chance(chance_pct: int):
    """Set from config: LLMChatter.ActionChance (0-100)."""
    global _action_chance
    _action_chance = chance_pct / 100.0


def get_action_chance() -> float:
    """Return the configured action chance (0.0-1.0)."""
    return _action_chance


def append_json_instruction(
    prompt: str, allow_action: bool = True
) -> str:
    """Append structured JSON response instruction
    to a prompt.

    Tells the LLM to respond with JSON containing
    message, emote, and optionally action fields.
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

    block = (
        "\n\nRESPONSE FORMAT: You MUST respond with "
        "ONLY valid JSON. No other text.\n"
        "{\n"
        '  "message": "your spoken words here",\n'
        f'  "emote": one of [{EMOTE_LIST_STR}] '
        "or null,\n"
        f"  {action_desc}"
        "}\n"
        "Rules: double quotes only, no trailing "
        "commas, no code fences, no markdown."
    )
    return prompt + block


def parse_single_response(response: str) -> dict:
    """Parse a single LLM response that may be JSON
    with message/emote/action fields.

    Returns dict with 'message', 'emote', 'action'.
    Falls back to plain text if JSON parsing fails.
    """
    if not response:
        return {
            'message': '',
            'emote': None,
            'action': None,
        }

    cleaned = response.strip()
    # Strip ```json wrapper
    cleaned = re.sub(
        r'```(?:json)?', '', cleaned,
        flags=re.IGNORECASE
    ).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            msg = data.get('message', '')
            if isinstance(msg, str):
                msg = msg.strip().strip('"')
            else:
                msg = str(msg).strip()

            # Validate emote
            raw_emote = data.get('emote')
            emote = validate_emote(raw_emote)

            # Sanitize action
            raw_action = data.get('action')
            action = _sanitize_action(raw_action)

            return {
                'message': msg,
                'emote': emote,
                'action': action,
            }
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: treat as plain text
    msg = cleaned.strip().strip('"')
    return {
        'message': msg,
        'emote': None,
        'action': None,
    }


def _sanitize_action(raw_action) -> Optional[str]:
    """Clean and validate an action string from
    LLM JSON output.

    Returns sanitized action (2-80 chars) or None.
    Filters out LLM null-like strings ("none", "null",
    "n/a", "no action", etc.).
    """
    if not raw_action or not isinstance(
        raw_action, str
    ):
        return None
    action = raw_action.strip().strip('*"\'')
    # LLM sometimes returns "none"/"null" as string
    # instead of JSON null — strip trailing punct
    # first to catch "none." / "null," variants
    check = action.rstrip('.,!;:').lower()
    if check in (
        'none', 'null', 'n/a', 'no action',
        'no', 'na', '',
    ):
        return None
    if len(action) < 2 or len(action) > 80:
        return None
    return action


def cleanup_message(
    message: str, action: str = None
) -> str:
    """Clean up any formatting issues from LLM output.

    If action is provided (from structured JSON),
    prepend *action* and skip Phase 1/2 regex
    narration detection (JSON supersedes heuristic).
    """
    result = message

    # Collapse newlines into single space (WoW chat
    # is single-line; multi-line LLM output causes
    # ugly spacing)
    result = re.sub(r'\s*\n\s*', ' ', result)

    # Em-dashes
    result = re.sub(r'\s*—\s*', ', ', result)

    # Backslash escapes leaking from SQL/JSON encoding
    result = result.replace("\\'", "'")
    result = result.replace('\\"', '"')
    result = result.replace('\\\\', '\\')

    # Structured action from JSON — prepend *action*
    # and skip Phase 1/2 heuristic detection
    _skip_narration_detection = False
    if action:
        result = f"*{action}* {result}"
        _skip_narration_detection = True

    # Keep asterisk emotes (*action*) — they display
    # nicely in WoW chat as RP emote markers.

    if not _skip_narration_detection:
        # Non-asterisk emote phrases — LLM sometimes
        # embeds action descriptions without asterisks.
        _EMOTE_VERBS = (
            'gazes', 'glances', 'stares', 'peers',
            'leans', 'nods', 'sighs', 'shrugs',
            'gestures', 'stretches',
            'tilts', 'grins',
            'smiles', 'frowns', 'chuckles',
            'scratches', 'rubs', 'taps',
            'flexes', 'adjusts', 'fidgets',
        )

        # Phase 1: Wrap leading third-person narration
        _NARRATION_FOLLOWERS = (
            'at', 'over', 'around', 'back', 'up',
            'down', 'toward', 'towards', 'away',
            'into', 'across', 'through', 'aside',
            'forward',
            'nervously', 'softly', 'quietly',
            'slowly', 'briefly', 'slightly',
            'deeply', 'heavily', 'warmly',
            'sadly', 'wearily', 'knowingly',
            'absently', 'idly', 'lazily',
            'cautiously', 'warily', 'tiredly',
            'thoughtfully', 'solemnly', 'grimly',
            'wistfully', 'fondly', 'gently',
            'happily', 'excitedly', 'curiously',
            'suspiciously', 'proudly',
            'sheepishly',
            'awkwardly', 'abruptly', 'eagerly',
            'impatiently', 'casually',
            'dismissively',
            'appreciatively', 'gratefully',
            'uncomfortably', 'uncertainly',
        )
        _verb_start = re.compile(
            r'^(' + '|'.join(_EMOTE_VERBS) + r')\s+'
            r'(' + '|'.join(
                _NARRATION_FOLLOWERS
            ) + r')\b',
            re.IGNORECASE
        )
        if _verb_start.match(result):
            _speech_re = re.compile(
                r'[,.](?:\.\.)?\s+'
                r'(?!(?:then|and|while|before|as)\b)',
                re.IGNORECASE
            )
            matches = list(
                _speech_re.finditer(result)
            )
            if matches:
                cut = matches[0]
                emote_part = (
                    result[:cut.start()].strip()
                )
                remainder = (
                    result[cut.end():].strip()
                )
                if len(remainder) > 10:
                    remainder = (
                        remainder[0].upper()
                        + remainder[1:]
                    )
                    result = (
                        f"*{emote_part}* "
                        f"{remainder}"
                    )
                else:
                    result = f"*{result}*"
            else:
                result = f"*{result}*"

        # Phase 2: Wrap mid-message emote clauses
        _emote_pattern = re.compile(
            r'(?:,\s*|\.\.?\.\s*|\.\s+)'
            r'((?:' + '|'.join(_EMOTE_VERBS) + r')'
            r'\s+\w[\w\s]*?)'
            r'(?=[,.]|\s*$)',
            re.IGNORECASE
        )

        def _wrap_emote(m):
            return f" *{m.group(1).strip()}*"

        result = _emote_pattern.sub(
            _wrap_emote, result
        )

    result = result.strip()

    # Clean up spacing
    result = re.sub(r'\s{2,}', ' ', result)

    # Multi-speaker truncation: LLM sometimes embeds
    # a second speaker in the response, e.g.
    # "Well fought! Cylaea: Hold, do you smell that?"
    # Truncate at "Name: " pattern appearing after
    # the first 20 characters (to avoid false-matching
    # legitimate uses at the start of a message).
    if len(result) > 20:
        second_speaker = re.search(
            r'\b[A-Z][a-z]{2,}:\s', result[20:]
        )
        if second_speaker:
            cut_pos = 20 + second_speaker.start()
            truncated = result[:cut_pos].rstrip(
                ' ,.-'
            )
            if len(truncated) > 10:
                result = truncated
                logger.debug(
                    "Truncated multi-speaker at "
                    "pos %d", cut_pos
                )

    # Emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE
    )
    result = emoji_pattern.sub('', result)

    # NPC markers to plain text
    result = re.sub(
        r'\[\[npc:\d+:([^\]]+)\]\]', r'\1', result
    )
    result = re.sub(
        r'\[npc:\d+:([^\]]+)\]', r'\1', result
    )
    result = re.sub(
        r'npc:\d+:([A-Za-z][A-Za-z\' ]+)', r'\1', result
    )

    # Fix {[Name]} -> [Name]
    result = re.sub(r'\{\[([^\]]+)\]\}', r'[\1]', result)

    # Fix [[Name]] -> [Name]
    result = re.sub(r'\[\[([^\]]+)\]\]', r'[\1]', result)

    # Fix {Name} when not a known placeholder
    # Preserve pre-cache placeholders: {target},
    # {caster}, {spell} and WoW link prefixes
    result = re.sub(
        r'\{(?!quest:|item:|spell:|'
        r'target\}|caster\}|spell\})'
        r'([^}]+)\}',
        r'\1', result
    )

    # Remove brackets around zone/faction names
    def maybe_remove_brackets(match):
        full_match = match.group(0)
        content = match.group(1)
        start_pos = match.start()

        prefix = result[max(0, start_pos-2):start_pos]
        if '|h' in prefix or prefix.endswith('|h'):
            return full_match

        words = content.split()
        if len(words) <= 2 and len(content) < 20:
            return f'[{content}]'
        return content

    result = re.sub(
        r'\[([^\]|]+)\]', maybe_remove_brackets, result
    )

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
def resolve_model(model_name: str) -> str:
    """Pass through model name (no aliasing)."""
    return model_name


def call_llm(
    client: Any,
    prompt: str,
    config: dict,
    max_tokens_override: int = None,
    context: str = ''
) -> str:
    """Call LLM API (Anthropic, OpenAI, or Ollama)."""
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()
    model = config.get(
        'LLMChatter.Model', DEFAULT_ANTHROPIC_MODEL
    )
    if max_tokens_override is not None:
        max_tokens = max_tokens_override
    else:
        max_tokens = int(
            config.get('LLMChatter.MaxTokens', 200)
        )
    temperature = float(
        config.get('LLMChatter.Temperature', 0.85)
    )

    logger.info(
        f"LLM prompt ({provider}/{model}, "
        f"max_tokens={max_tokens}):\n{prompt}"
    )

    try:
        if provider == 'ollama':
            actual_prompt = prompt
            disable_thinking = (
                config.get(
                    'LLMChatter.Ollama.DisableThinking', '1'
                ) == '1'
            )
            if disable_thinking:
                actual_prompt = "/no_think " + prompt

            context_size = int(
                config.get(
                    'LLMChatter.Ollama.ContextSize', 2048
                )
            )

            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": actual_prompt}
                ],
                extra_body={
                    "options": {"num_ctx": context_size}
                }
            )
            return response.choices[0].message.content.strip()
        elif provider == 'openai':
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        else:
            # Anthropic (default)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
    except Exception as e:
        ctx = f" [{context}]" if context else ""
        logger.error(
            f"LLM API error ({provider}){ctx}: {e}"
        )
        return None


# Cached client for quick analyze when provider
# differs from main provider
_quick_analyze_client = None
_quick_analyze_provider = None


def _get_quick_analyze_client(config):
    """Get or create the LLM client for quick
    analyze calls. Returns (client, provider).

    If QuickAnalyze.Provider matches the main
    provider (or is empty), returns None so the
    caller uses the main client.
    """
    global _quick_analyze_client
    global _quick_analyze_provider

    import anthropic
    import openai

    qa_provider = config.get(
        'LLMChatter.QuickAnalyze.Provider', ''
    ).strip().lower()
    main_provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()

    # Empty = use main provider
    if not qa_provider or qa_provider == main_provider:
        return None, main_provider

    # Return cached client if already created
    if (
        _quick_analyze_client is not None
        and _quick_analyze_provider == qa_provider
    ):
        return _quick_analyze_client, qa_provider

    # Create new client for the quick analyze
    # provider
    if qa_provider == 'ollama':
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://localhost:11434'
        )
        ollama_api_url = (
            f"{base_url.rstrip('/')}/v1"
        )
        _quick_analyze_client = openai.OpenAI(
            base_url=ollama_api_url,
            api_key="ollama"
        )
    elif qa_provider == 'openai':
        api_key = config.get(
            'LLMChatter.OpenAI.ApiKey', ''
        )
        if not api_key:
            logger.warning(
                "QuickAnalyze: No OpenAI API key"
            )
            return None, main_provider
        _quick_analyze_client = openai.OpenAI(
            api_key=api_key
        )
    elif qa_provider == 'anthropic':
        api_key = config.get(
            'LLMChatter.Anthropic.ApiKey', ''
        )
        if not api_key:
            logger.warning(
                "QuickAnalyze: No Anthropic key"
            )
            return None, main_provider
        _quick_analyze_client = anthropic.Anthropic(
            api_key=api_key
        )
    else:
        logger.warning(
            f"QuickAnalyze: Unknown provider "
            f"'{qa_provider}', using main"
        )
        return None, main_provider

    _quick_analyze_provider = qa_provider
    logger.info(
        f"QuickAnalyze: Created {qa_provider} client"
    )
    return _quick_analyze_client, qa_provider


def quick_llm_analyze(
    client: Any,
    config: dict,
    prompt: str,
    max_tokens: int = 50
) -> Optional[str]:
    """Fast LLM call for pre-processing analysis.

    Uses the configured QuickAnalyze provider/model,
    or defaults to the fastest model on the main
    provider (Haiku for Anthropic, gpt-4o-mini for
    OpenAI, main model for Ollama).

    Useful for tasks like:
    - Determining which bot a player is addressing
    - Classifying message intent or sentiment
    - Summarizing context before a full prompt

    Returns raw text response, or None on error.
    """
    # Check for separate quick analyze provider
    qa_client, provider = (
        _get_quick_analyze_client(config)
    )
    if qa_client is not None:
        active_client = qa_client
    else:
        active_client = client

    # Resolve model
    qa_model = config.get(
        'LLMChatter.QuickAnalyze.Model', ''
    ).strip()

    if qa_model:
        model = qa_model
    elif provider == 'anthropic':
        model = DEFAULT_ANTHROPIC_MODEL
    elif provider == 'openai':
        model = DEFAULT_OPENAI_MODEL
    else:
        # Ollama: use configured model
        model = config.get(
            'LLMChatter.Model',
            DEFAULT_ANTHROPIC_MODEL
        )

    logger.info(
        f"Quick LLM analyze ({provider}/{model}, "
        f"max_tokens={max_tokens}):\n{prompt}"
    )

    try:
        if provider == 'ollama':
            actual_prompt = prompt
            disable_thinking = (
                config.get(
                    'LLMChatter.Ollama.'
                    'DisableThinking', '1'
                ) == '1'
            )
            if disable_thinking:
                actual_prompt = (
                    "/no_think " + prompt
                )
            context_size = int(config.get(
                'LLMChatter.Ollama.ContextSize',
                2048
            ))
            response = (
                active_client
                .chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": actual_prompt
                    }],
                    extra_body={
                        "options": {
                            "num_ctx": context_size
                        }
                    }
                )
            )
            return (
                response.choices[0]
                .message.content.strip()
            )
        elif provider == 'openai':
            response = (
                active_client
                .chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )
            return (
                response.choices[0]
                .message.content.strip()
            )
        else:
            response = (
                active_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )
            return response.content[0].text.strip()
    except Exception as e:
        logger.warning(
            f"Quick LLM analyze error "
            f"({provider}): {e}"
        )
        return None


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


def extract_conversation_msg_count(prompt: str) -> int:
    """Extract expected message count from a prompt."""
    match = re.search(r'EXACTLY (\d+) messages', prompt)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return 0
    return 0


# =============================================================================
# EVENT HELPERS
# =============================================================================
def repair_json_string(raw_json: str) -> str:
    """Attempt to repair common JSON escaping issues."""
    if not raw_json:
        return raw_json

    try:
        json.loads(raw_json)
        return raw_json
    except Exception:
        pass

    def escape_inner_quotes(match):
        inner = match.group(1)
        return '(\\"' + inner + '\\")'

    repaired = re.sub(
        r'\("([^"\\]+)"\)', escape_inner_quotes, raw_json
    )

    try:
        json.loads(repaired)
        return repaired
    except Exception:
        pass

    try:
        result = {}

        entry_match = re.search(
            r'"transport_entry":(\d+)', raw_json
        )
        if entry_match:
            result['transport_entry'] = int(
                entry_match.group(1)
            )

        type_match = re.search(
            r'"transport_type":"([^"]+)"', raw_json
        )
        if type_match:
            result['transport_type'] = type_match.group(1)

        dest_match = re.search(
            r'"destination":"([^"]+)"', raw_json
        )
        if dest_match:
            result['destination'] = dest_match.group(1)

        name_match = re.search(
            r'"transport_name":"(.+?)","'
            r'(?:destination|transport_type)"',
            raw_json
        )
        if name_match:
            result['transport_name'] = name_match.group(1)

        if result:
            return json.dumps(result)
    except Exception:
        pass

    return raw_json


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
def validate_emote(emote_str: Optional[str]) -> Optional[str]:
    """Clean and validate an emote string from LLM output.

    Returns a valid emote name or None.
    """
    if not emote_str or not isinstance(emote_str, str):
        return None
    cleaned = emote_str.strip().lower()
    # Strip quotes the LLM might add
    cleaned = cleaned.strip('"').strip("'")
    if cleaned in EMOTE_LIST and cleaned != 'none':
        return cleaned
    return None


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


def query_item_details(
    db, entry: int,
) -> Optional[dict]:
    """Query acore_world.item_template for an item's
    stats. Returns dict or None.
    """
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT entry, name, Quality,
                   class AS item_class,
                   subclass AS item_subclass,
                   ItemLevel, RequiredLevel,
                   AllowableClass,
                   stat_type1, stat_value1,
                   stat_type2, stat_value2,
                   dmg_min1, dmg_max1,
                   armor, block
            FROM acore_world.item_template
            WHERE entry = %s
        """, (entry,))
        return cursor.fetchone()
    except Exception as e:
        logger.warning(
            f"Failed to query item {entry}: {e}"
        )
        return None


def query_quest_turnin_npc(
    config, quest_id: int
) -> Optional[str]:
    """Look up the NPC name that a quest is turned
    in to via creature_questender + creature_template.
    Returns NPC name string or None.
    """
    try:
        db = get_db_connection(
            config, 'acore_world'
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT ct.name
            FROM creature_questender cqe
            JOIN creature_template ct
                ON cqe.id = ct.entry
            WHERE cqe.quest = %s
            LIMIT 1
        """, (quest_id,))
        row = cursor.fetchone()
        return row['name'] if row else None
    except Exception as e:
        logger.warning(
            f"Failed to query quest turnin NPC "
            f"for quest {quest_id}: {e}"
        )
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass


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
def get_recent_zone_messages(
    db, zone_id: int,
    limit: int = 15,
    minutes: int = 30
) -> list:
    """Fetch recent delivered messages for a zone.

    Returns list of message strings (newest first).
    Zone-scoped via JOIN on queue_id or event_id
    (llm_chatter_messages has no zone_id column).
    """
    if not zone_id:
        return []
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.message
            FROM llm_chatter_messages m
            LEFT JOIN llm_chatter_queue q
                ON m.queue_id = q.id
            LEFT JOIN llm_chatter_events e
                ON m.event_id = e.id
            WHERE m.delivered = 1
              AND m.channel IN ('general', 'say')
              AND m.delivered_at > DATE_SUB(
                  NOW(), INTERVAL %s MINUTE
              )
              AND (q.zone_id = %s
                   OR e.zone_id = %s)
            ORDER BY m.delivered_at DESC
            LIMIT %s
        """, (minutes, zone_id, zone_id, limit))
        rows = cursor.fetchall()
        return [r['message'] for r in rows if r.get(
            'message'
        )]
    except Exception as e:
        logger.debug(
            f"get_recent_zone_messages error: {e}"
        )
        return []


def get_recent_bot_messages(
    db, bot_guid: int,
    limit: int = 10,
    minutes: int = 60
) -> list:
    """Fetch recent messages from a specific bot.

    Returns list of message strings (newest first).
    Covers all channels (party, general, say).
    """
    if not bot_guid:
        return []
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT message FROM llm_chatter_messages
            WHERE delivered = 1
              AND bot_guid = %s
              AND delivered_at > DATE_SUB(
                  NOW(), INTERVAL %s MINUTE
              )
            ORDER BY delivered_at DESC
            LIMIT %s
        """, (bot_guid, minutes, limit))
        rows = cursor.fetchall()
        return [r['message'] for r in rows if r.get(
            'message'
        )]
    except Exception as e:
        logger.debug(
            f"get_recent_bot_messages error: {e}"
        )
        return []


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


def _extract_ngrams(text: str, n: int = 4) -> set:
    """Extract word n-grams from text for similarity
    comparison. Lowercased, punctuation stripped."""
    words = re.sub(
        r'[^\w\s]', '', text.lower()
    ).split()
    if len(words) < n:
        return set()
    return {
        ' '.join(words[i:i+n])
        for i in range(len(words) - n + 1)
    }


def is_too_similar(
    new_message: str,
    recent_messages: list,
    threshold: int = 3
) -> bool:
    """Check if new_message shares too many n-grams
    with recent messages.

    Args:
        new_message: The message to check
        recent_messages: List of recent message strings
        threshold: Min shared 4-grams to trigger
            rejection. Default 3 avoids false positives
            from common phrases like "in the heart of"
            while catching real repetitions.

    Returns True if message should be rejected.
    """
    if not recent_messages or not new_message:
        return False

    new_ngrams = _extract_ngrams(new_message, 4)
    if not new_ngrams:
        return False

    # Pool all recent n-grams together
    recent_ngrams = set()
    for msg in recent_messages:
        recent_ngrams.update(_extract_ngrams(msg, 4))

    overlap = new_ngrams & recent_ngrams
    if len(overlap) >= threshold:
        logger.info(
            f"Anti-repetition: rejected "
            f"({len(overlap)} shared 4-grams >= "
            f"{threshold}): "
            f"{list(overlap)[:5]}"
        )
        return True

    return False


# =============================================================================
# CENTRALIZED MESSAGE INSERTION
# =============================================================================
def insert_chat_message(
    db,
    bot_guid: int,
    bot_name: str,
    message: str,
    channel: str = 'party',
    delay_seconds: float = 2.0,
    event_id: int = None,
    queue_id: int = None,
    sequence: int = 0,
    emote: str = None,
):
    """Insert a message into llm_chatter_messages.

    Centralised helper replacing individual INSERT
    statements across the codebase. Handles the emote
    column transparently.
    """
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO llm_chatter_messages
        (event_id, queue_id, sequence, bot_guid,
         bot_name, message, emote, channel,
         delivered, deliver_at)
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, 0,
            DATE_ADD(NOW(), INTERVAL %s SECOND)
        )
    """, (
        event_id, queue_id, sequence,
        bot_guid, bot_name, message,
        validate_emote(emote), channel,
        int(delay_seconds),
    ))
    db.commit()
