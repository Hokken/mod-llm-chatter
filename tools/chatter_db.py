"""DB/query helpers extracted from chatter_shared (N15/N16)."""

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

import mysql.connector

from chatter_constants import (
    CAPITAL_CITY_ZONES,
    CLASS_IDS,
    EMOTE_LIST,
    ZONE_COORDINATES,
    ZONE_LEVELS,
)
from spell_names import SPELL_DESCRIPTIONS, SPELL_NAMES

logger = logging.getLogger(__name__)

# =====================================================================
# Lightweight TTL caches (module-level, thread-safe via _cache_lock)
# =====================================================================
_char_info_cache: dict = {}
_talent_cache: dict = {}
_online_cache: dict = {}
_cache_lock = threading.Lock()


def _cache_get(cache: dict, key, ttl: float):
    """Return cached value if within TTL, else None."""
    with _cache_lock:
        entry = cache.get(key)
        if entry and (time.time() - entry['ts']) < ttl:
            return entry['data']
        if entry:
            del cache[key]  # expired
        return None


def _cache_put(cache: dict, key, value, max_size: int = 500):
    """Store value in cache, evicting oldest if full."""
    with _cache_lock:
        if len(cache) >= max_size and key not in cache:
            oldest = min(
                cache, key=lambda k: cache[k]['ts']
            )
            del cache[oldest]
        cache[key] = {'data': value, 'ts': time.time()}


class ZoneDataCache:
    """Cache for zone-specific quest, loot, and mob data.

    Thread-safe: all methods are protected by a lock
    for concurrent access from worker threads.
    """

    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self._lock = threading.Lock()
        self.quest_cache: Dict[int, Tuple[List[dict], float]] = {}
        self.loot_cache: Dict[Tuple[int, int], Tuple[List[dict], float]] = {}
        self.mob_cache: Dict[Tuple[int, int], Tuple[List[str], float]] = {}
        self.recent_loot: Dict[int, Dict[int, float]] = {}

    def get_quests(self, zone_id: int) -> Optional[List[dict]]:
        with self._lock:
            if zone_id in self.quest_cache:
                data, timestamp = self.quest_cache[zone_id]
                if time.time() - timestamp < self.ttl:
                    return data
            return None

    def set_quests(self, zone_id: int, quests: List[dict]):
        with self._lock:
            self.quest_cache[zone_id] = (quests, time.time())

    def get_loot(
        self, min_level: int, max_level: int
    ) -> Optional[List[dict]]:
        with self._lock:
            key = (min_level, max_level)
            if key in self.loot_cache:
                data, timestamp = self.loot_cache[key]
                if time.time() - timestamp < self.ttl:
                    return data
            return None

    def set_loot(
        self, min_level: int, max_level: int, loot: List[dict]
    ):
        with self._lock:
            self.loot_cache[(min_level, max_level)] = (
                loot, time.time()
            )

    def get_mobs(
        self, zone_id: int, bot_level: int
    ) -> Optional[List[str]]:
        with self._lock:
            key = (zone_id, bot_level)
            if key in self.mob_cache:
                data, timestamp = self.mob_cache[key]
                if time.time() - timestamp < self.ttl:
                    return data
            return None

    def set_mobs(
        self, zone_id: int, bot_level: int, mobs: List[str]
    ):
        with self._lock:
            self.mob_cache[(zone_id, bot_level)] = (
                mobs, time.time()
            )

    def get_recent_loot_ids(
        self, zone_id: int, cooldown_seconds: int
    ) -> set:
        with self._lock:
            now = time.time()
            if zone_id not in self.recent_loot:
                return set()
            recent = {
                item_id: ts
                for item_id, ts
                in self.recent_loot[zone_id].items()
                if now - ts < cooldown_seconds
            }
            self.recent_loot[zone_id] = recent
            return set(recent.keys())

    def mark_loot_seen(self, zone_id: int, item_id: int):
        with self._lock:
            if zone_id not in self.recent_loot:
                self.recent_loot[zone_id] = {}
            self.recent_loot[zone_id][item_id] = time.time()


# Global cache instance
zone_cache = ZoneDataCache()


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
            return True
        except Exception as e:
            if attempt == max_retries:
                return False
            time.sleep(delay)
            delay = min(delay * 1.5, 30.0)

    return False


def _get_zone_level_range(
    zone_id: int, bot_level: int
) -> Tuple[int, int]:
    """Get level range for a zone, falling back to bot level."""
    if zone_id in ZONE_LEVELS:
        return ZONE_LEVELS[zone_id]
    return (max(1, bot_level - 5), bot_level + 5)


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

    except Exception:
        return []


def query_zone_loot(
    config: dict, zone_id: int, bot_level: int
) -> List[dict]:
    """Query loot appropriate for the zone."""
    # No loot drops in capital cities
    if zone_id in CAPITAL_CITY_ZONES:
        return []

    min_level, max_level = _get_zone_level_range(zone_id, bot_level)

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

    except Exception:
        return []


def query_zone_mobs(
    config: dict, zone_id: int, bot_level: int
) -> List[str]:
    """Query hostile mob names from the specific zone."""
    # No hostile creatures in capital cities
    if zone_id in CAPITAL_CITY_ZONES:
        return []

    min_level, max_level = _get_zone_level_range(zone_id, bot_level)

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
                row['name']
                for row in cursor.fetchall()
                if row['name']
            ]

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
                row['name']
                for row in cursor.fetchall()
                if row['name']
            ]

        db.close()

        zone_cache.set_mobs(zone_id, bot_level, mobs)
        return mobs

    except Exception:
        return []


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

    except Exception:
        return []


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
    except Exception:
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
    except Exception:
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass


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
              AND m.channel IN (
                  'general', 'say', 'party',
                  'battleground', 'raid'
              )
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
    except Exception:
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
    except Exception:
        return []


def get_group_location(db, group_id):
    """Get the group's current zone, area, and map
    from llm_group_bot_traits.

    C++ OnPlayerUpdateZone keeps these columns
    updated in real-time for all bots in the group.
    This is the single source of truth for location.

    Returns (zone_id, area_id, map_id) or (0, 0, 0).
    """
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT zone, area, map"
            " FROM llm_group_bot_traits"
            " WHERE group_id = %s"
            " LIMIT 1",
            (group_id,),
        )
        row = cursor.fetchone()
        if row:
            return (
                int(row.get('zone', 0) or 0),
                int(row.get('area', 0) or 0),
                int(row.get('map', 0) or 0),
            )
    except Exception:
        pass
    return (0, 0, 0)


def get_character_info_by_name(
    db, char_name: str
) -> Optional[dict]:
    """Look up character guid and class by name.

    Returns {'guid': int, 'class': int} or None.
    Cached with 10-minute TTL, 500-entry max.
    """
    cached = _cache_get(_char_info_cache, char_name, 600)
    if cached is not None:
        return cached

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT guid, class FROM characters "
            "WHERE name = %s",
            (char_name,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = {
            'guid': int(row['guid']),
            'class': int(row['class']),
        }
        _cache_put(
            _char_info_cache, char_name, result, 500
        )
        return result
    except Exception:
        return None


def is_player_online(
    db, player_name: str
) -> bool:
    """Check if a player is currently online.

    Queries characters.online column.
    Returns True if online=1, False if 0 or not found.
    Cached with 30-second TTL, 200-entry max.
    """
    if not player_name:
        return False

    cached = _cache_get(
        _online_cache, player_name, 30
    )
    if cached is not None:
        return cached

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT online FROM characters "
            "WHERE name = %s LIMIT 1",
            (player_name,),
        )
        row = cursor.fetchone()
        if not row:
            _cache_put(
                _online_cache, player_name,
                False, 200
            )
            return False
        result = int(row['online']) == 1
        _cache_put(
            _online_cache, player_name,
            result, 200
        )
        return result
    except Exception:
        return True  # assume online on error


def get_character_talents(
    db, char_guid: int
) -> dict:
    """Get learned talents for a character's active spec.

    Returns {'talents': [...], 'tree_totals': {...}}
    or empty dict on error/no data.
    Cached with 5-minute TTL, 500-entry max.
    """
    empty = {'talents': [], 'tree_totals': {}}

    # Query active spec first for cache key
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT activeTalentGroup "
            "FROM characters WHERE guid = %s",
            (char_guid,),
        )
        spec_row = cursor.fetchone()
        if not spec_row:
            return empty
        active_spec = int(
            spec_row['activeTalentGroup']
        )
    except Exception:
        return empty

    cache_key = (char_guid, active_spec)
    cached = _cache_get(
        _talent_cache, cache_key, 60
    )
    if cached is not None:
        return cached

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                tt.Name_Lang_enUS AS tree_name,
                s.Name_Lang_enUS AS talent_name,
                CASE
                    WHEN ct.spell = t.SpellRank_1 THEN 1
                    WHEN ct.spell = t.SpellRank_2 THEN 2
                    WHEN ct.spell = t.SpellRank_3 THEN 3
                    WHEN ct.spell = t.SpellRank_4 THEN 4
                    WHEN ct.spell = t.SpellRank_5 THEN 5
                    ELSE 0
                END AS points
            FROM acore_characters.character_talent ct
            JOIN acore_world.talent_dbc t
                ON ct.spell IN (
                    t.SpellRank_1, t.SpellRank_2,
                    t.SpellRank_3, t.SpellRank_4,
                    t.SpellRank_5
                )
            JOIN acore_world.talenttab_dbc tt
                ON tt.ID = t.TabID
            JOIN acore_world.spell_dbc s
                ON s.ID = t.SpellRank_1
            WHERE ct.guid = %s
              AND (ct.specMask & (1 << %s)) <> 0
            ORDER BY tt.OrderIndex, t.TierID,
                     t.ColumnIndex
        """, (char_guid, active_spec))

        rows = cursor.fetchall()
        if not rows:
            _cache_put(
                _talent_cache, cache_key, empty, 500
            )
            return empty

        talents = []
        tree_totals: Dict[str, int] = {}
        for row in rows:
            tree = row['tree_name'] or 'Unknown'
            name = row['talent_name'] or 'Unknown'
            pts = int(row['points'] or 0)
            talents.append({
                'tree_name': tree,
                'talent_name': name,
                'points': pts,
            })
            tree_totals[tree] = (
                tree_totals.get(tree, 0) + pts
            )

        result = {
            'talents': talents,
            'tree_totals': tree_totals,
        }
        _cache_put(
            _talent_cache, cache_key, result, 500
        )
        return result

    except Exception:
        return empty


def any_real_players_online(db) -> bool:
    """Check if any non-bot player is online.

    Single cheap query — use as a global gate to
    skip all background work when nobody is playing.
    Excludes playerbot accounts (username LIKE
    'RNDBOT%') which also set online=1.
    """
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT 1 FROM characters c "
            "JOIN acore_auth.account a "
            "  ON c.account = a.id "
            "WHERE c.online = 1 "
            "  AND a.username NOT LIKE 'RNDBOT%%' "
            "LIMIT 1"
        )
        row = cursor.fetchone()
        return row is not None
    except Exception:
        # On error, assume online to avoid
        # accidentally suppressing work
        return True


def cleanup_stale_groups(db) -> int:
    """Remove llm_group_bot_traits rows for groups
    whose real player is no longer online.

    Handles clean logout, crash, and alt-F4 — the
    server always sets characters.online=0 when the
    TCP connection drops.

    Also cancels pending events and queue entries
    for the stale group, and purges cached responses.

    Returns number of groups cleaned up.
    """
    try:
        cursor = db.cursor(dictionary=True)
        # Find groups where no non-bot member is
        # online. Bot GUIDs are in the traits table;
        # real player GUIDs are in group_member but
        # NOT in traits.
        cursor.execute("""
            SELECT DISTINCT t.group_id
            FROM llm_group_bot_traits t
            WHERE NOT EXISTS (
                SELECT 1
                FROM group_member gm
                JOIN characters c
                  ON c.guid = gm.memberGuid
                WHERE gm.guid = t.group_id
                  AND c.online = 1
                  AND gm.memberGuid NOT IN (
                      SELECT bot_guid
                      FROM llm_group_bot_traits
                      WHERE group_id = t.group_id
                  )
            )
        """)
        stale = cursor.fetchall()
        if not stale:
            return 0

        cleaned = 0
        for row in stale:
            gid = row['group_id']
            # Cancel pending events
            cursor.execute(
                "UPDATE llm_chatter_events "
                "SET status = 'cancelled' "
                "WHERE status = 'pending' "
                "  AND JSON_EXTRACT("
                "    extra_data, '$.group_id'"
                "  ) = %s",
                (gid,),
            )
            # Cancel pending queue entries
            # (mirrors C++ CleanupGroupSession)
            cursor.execute(
                "UPDATE llm_chatter_queue "
                "SET status = 'cancelled' "
                "WHERE status = 'pending' "
                "AND ("
                "  bot1_guid IN ("
                "    SELECT bot_guid FROM"
                "    llm_group_bot_traits"
                "    WHERE group_id = %s) "
                "  OR bot2_guid IN ("
                "    SELECT bot_guid FROM"
                "    llm_group_bot_traits"
                "    WHERE group_id = %s) "
                "  OR bot3_guid IN ("
                "    SELECT bot_guid FROM"
                "    llm_group_bot_traits"
                "    WHERE group_id = %s) "
                "  OR bot4_guid IN ("
                "    SELECT bot_guid FROM"
                "    llm_group_bot_traits"
                "    WHERE group_id = %s)"
                ")",
                (gid, gid, gid, gid),
            )
            # Mark undelivered messages as delivered
            # (by bot_guid — no group_id column on
            # llm_chatter_messages)
            cursor.execute(
                "UPDATE llm_chatter_messages "
                "SET delivered = 1 "
                "WHERE delivered = 0 "
                "  AND bot_guid IN ("
                "    SELECT bot_guid FROM"
                "    llm_group_bot_traits"
                "    WHERE group_id = %s"
                "  )",
                (gid,),
            )
            # Purge cached responses
            cursor.execute(
                "DELETE FROM "
                "llm_group_cached_responses "
                "WHERE group_id = %s",
                (gid,),
            )
            # Purge group chat history
            cursor.execute(
                "DELETE FROM "
                "llm_group_chat_history "
                "WHERE group_id = %s",
                (gid,),
            )
            # Remove traits (stops all background
            # workers for this group)
            cursor.execute(
                "DELETE FROM llm_group_bot_traits "
                "WHERE group_id = %s",
                (gid,),
            )
            # Clear in-memory session state
            try:
                from chatter_memory import (
                    teardown_group_session,
                )
                teardown_group_session(gid)
            except Exception:
                pass
            cleaned += 1

        db.commit()
        if cleaned:
            logger.info(
                "[CLEANUP] Purged %d stale group(s)"
                " — player offline", cleaned
            )
        return cleaned

    except Exception:
        logger.error(
            "[CLEANUP] stale group cleanup failed",
            exc_info=True,
        )
        return 0


def cleanup_all_session_data(db):
    """Wipe all ephemeral session tables.

    Called once when the last real player goes
    offline. Clears everything except persistent
    data (llm_bot_identities, llm_bot_memories).

    Tables cleared:
    - llm_group_bot_traits
    - llm_group_chat_history
    - llm_group_cached_responses
    - llm_general_chat_history
    - llm_chatter_queue (pending/processing)
    - llm_chatter_messages (undelivered)
    - llm_chatter_events (pending/processing)
    """
    try:
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM llm_group_bot_traits"
        )
        cursor.execute(
            "DELETE FROM llm_group_chat_history"
        )
        cursor.execute(
            "DELETE FROM llm_group_cached_responses"
        )
        cursor.execute(
            "DELETE FROM llm_general_chat_history"
        )
        cursor.execute(
            "DELETE FROM llm_chatter_queue"
        )
        cursor.execute(
            "DELETE FROM llm_chatter_messages"
        )
        cursor.execute(
            "DELETE FROM llm_chatter_events"
        )
        db.commit()
        logger.info(
            "[CLEANUP] All session data cleared"
            " — no players online"
        )
    except Exception:
        logger.error(
            "[CLEANUP] session data wipe failed",
            exc_info=True,
        )
