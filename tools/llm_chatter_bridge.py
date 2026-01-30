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

# Zone coordinate boundaries for accurate mob queries
# Format: zone_id: (map_id, min_x, max_x, min_y, max_y)
# These are approximate bounding boxes for each zone
ZONE_COORDINATES = {
    # Eastern Kingdoms (map = 0)
    1: (0, -6100, -4700, -700, 900),        # Dun Morogh
    12: (0, -9900, -8300, -1100, 500),      # Elwynn Forest
    38: (0, -5800, -4200, -3400, -2200),    # Loch Modan
    40: (0, -11500, -9800, 300, 2000),      # Westfall
    44: (0, -9700, -8700, -2600, -1200),    # Redridge Mountains
    47: (0, -600, 900, -4700, -3200),       # The Hinterlands
    51: (0, -7400, -6100, -1400, -400),     # Searing Gorge
    85: (0, 1600, 3000, -700, 1100),        # Tirisfal Glades
    130: (0, 400, 2000, 700, 2100),         # Silverpine Forest
    267: (0, -1200, 300, -500, 900),        # Hillsbrad Foothills
    33: (0, -14800, -11200, -1400, 1700),   # Stranglethorn Vale
    45: (0, -2400, -800, -3000, -1600),     # Arathi Highlands
    3: (0, -7100, -5700, -3800, -2800),     # Badlands
    8: (0, -10800, -9800, -4000, -2500),    # Swamp of Sorrows
    4: (0, -12100, -10300, -3400, -2200),   # Blasted Lands
    10: (0, -11300, -9800, -700, 600),      # Duskwood
    11: (0, -4600, -2700, -3000, -1700),    # Wetlands
    139: (0, 1300, 3300, -4800, -3000),     # Eastern Plaguelands
    28: (0, 1300, 2700, -2200, -800),       # Western Plaguelands

    # Kalimdor (map = 1)
    14: (1, -800, 1700, -5200, -3500),      # Durotar
    215: (1, -2700, -300, -1700, 400),      # Mulgore
    141: (1, 8800, 10500, 500, 2100),       # Teldrassil
    148: (1, 6200, 7900, -700, 1400),       # Darkshore
    17: (1, -3600, 500, -5000, -1300),      # The Barrens
    331: (1, 2200, 4500, -2400, 1100),      # Ashenvale
    405: (1, -2000, 600, 1000, 3200),       # Desolace
    400: (1, -5600, -4200, -1200, 1300),    # Thousand Needles
    15: (1, -5100, -2700, -4300, -2400),    # Dustwallow Marsh
    357: (1, -5200, -2800, 1700, 4700),     # Feralas
    440: (1, -8500, -6000, -3700, -1400),   # Tanaris
    16: (1, 2200, 4200, -5700, -3300),      # Azshara
    361: (1, 3200, 5700, -2000, 900),       # Felwood
    490: (1, -8100, -5700, -500, 1900),     # Un'Goro Crater
    618: (1, 5300, 7500, -1400, 1100),      # Winterspring
    1377: (1, -8200, -5900, 500, 2700),     # Silithus

    # Outland (map = 530)
    3483: (530, -1300, 1300, 5800, 8700),   # Hellfire Peninsula
    3518: (530, -2200, 500, 3000, 5900),    # Nagrand
    3519: (530, -3800, -1500, 2100, 5200),  # Terokkar Forest
    3520: (530, -5200, -2100, 700, 3500),   # Shadowmoon Valley
    3521: (530, -1500, 900, 2900, 6300),    # Zangarmarsh
    3522: (530, 500, 3500, 3500, 7700),     # Blade's Edge Mountains
    3523: (530, 1700, 4900, 800, 4200),     # Netherstorm

    # Northrend (map = 571)
    3537: (571, 2300, 5400, 3700, 7000),    # Borean Tundra
    495: (571, -800, 2400, -2200, 1400),    # Howling Fjord
    394: (571, 3200, 5000, -3400, -800),    # Grizzly Hills
    3711: (571, 5000, 6500, 3700, 6200),    # Sholazar Basin
    66: (571, 4400, 7000, -4800, -1700),    # Zul'Drak
    67: (571, 6000, 9100, -1600, 2100),     # Storm Peaks
    210: (571, 5600, 8700, 400, 3800),      # Icecrown
}

# =============================================================================
# ZONE FLAVOR - Rich context for immersive chat generation
# =============================================================================
# Each zone gets a description paragraph that gives the LLM world knowledge.
# The LLM uses this as creative inspiration, not a template to copy.
ZONE_FLAVOR = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Snowy dwarven highlands surrounding Ironforge. Troggs have
invaded from underground, and hostile ice trolls lurk in the mountains. Coldridge
Valley is where young dwarves and gnomes begin their journey. The air is crisp,
the ale is strong, and the mountains echo with the sound of gunfire and hammers.""",

    12: """Elwynn Forest: Peaceful human farmland outside Stormwind, but trouble
brews beneath the surface. Kobolds infest the mines crying "you no take candle,"
the Defias Brotherhood threatens the roads, and gnolls raid from the borders.
Goldshire inn is always lively. A deceptively calm zone with danger lurking.""",

    38: """Loch Modan: A mountainous region dominated by a massive lake. Troggs
and kobolds plague the area, while Dark Iron dwarves cause trouble near the dam.
The great dam is an engineering marvel. Thelsamar is a quiet town of hunters and
excavators. The landscape feels rugged and frontier-like.""",

    40: """Westfall: Once fertile farmland, now dusty and abandoned. The Defias
Brotherhood controls much of the region from their hidden base. Homeless farmers
wander the roads, mechanical harvest watchers patrol empty fields, and gnolls
scavenge the edges. Sentinel Hill stands as the last bastion of order.""",

    44: """Redridge Mountains: A besieged human territory. Blackrock orcs pour
down from the mountains, gnolls roam freely, and the town of Lakeshire desperately
holds on. The bridge is always under threat. A zone that feels like a warfront,
with citizens caught in the crossfire.""",

    10: """Duskwood: Perpetually dark, cursed forest shrouded in eternal night.
Undead shamble through the woods, worgen howl in the darkness, and giant spiders
lurk everywhere. Darkshire's Night Watch barely holds back the horrors. An
unsettling zone where something terrible happened and the land never recovered.""",

    11: """Wetlands: Soggy marshland connecting the dwarven lands to Lordaeron.
Hostile crocolisks and raptors everywhere, Dark Iron dwarves scheme in the hills,
and dragonkin threaten from the northeast. Menethil Harbor is a rain-soaked port
town. Everything here is damp and slightly miserable.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Tirisfal Glades: Haunted forest surrounding the Undercity. The land
itself feels diseased - sickly trees, green fog, and restless undead. Scarlet
Crusade zealots hunt anything undead, while mindless zombies and bats roam freely.
Brill is a grim town of the Forsaken. The atmosphere is gothic and melancholic.""",

    130: """Silverpine Forest: Dark, misty woods south of Tirisfal. Worgen have
overrun much of the forest, and the Scourge presence lingers. Shadowfang Keep
looms ominously. The Forsaken fight for every inch of territory. A zone caught
between multiple threats, feeling isolated and dangerous.""",

    267: """Hillsbrad Foothills: Contested farmland where Horde and Alliance
clash openly. Southshore and Tarren Mill are in constant conflict. Yetis roam
the mountains, and the Syndicate bandits cause trouble. A zone defined by
faction warfare and old grudges.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """The Hinterlands: Remote forested highlands, home to the Wildhammer
dwarves and forest trolls locked in eternal conflict. Wolves and owlbeasts roam
the wilds. Aerie Peak sits atop a massive cliff. The zone feels untamed and
far from civilization.""",

    45: """Arathi Highlands: Rolling grasslands dotted with ancient ruins. The
Syndicate controls Stromgarde's ruins, ogres inhabit the caves, and raptors hunt
the plains. Refuge Pointe and Hammerfall eye each other warily. A windswept
frontier zone with echoes of fallen kingdoms.""",

    33: """Stranglethorn Vale: Dense, dangerous jungle teeming with life. Trolls,
pirates, raptors, tigers, and gorillas everywhere. Booty Bay is a lawless goblin
port where anything goes. Nesingwary's hunting expedition draws adventurers.
The zone is beautiful but deadly - something wants to eat you around every corner.""",

    3: """Badlands: Harsh, barren desert of red rock and dust. Hostile troggs,
coyotes, and black dragon whelps make travel dangerous. Scattered archaeology
sites hint at ancient secrets. Kargath is a rough Horde outpost. A zone that
feels desolate and unforgiving.""",

    8: """Swamp of Sorrows: Murky, depressing swampland. Lost ones wander aimlessly,
jaguars stalk the waters, and the Temple of Atal'Hakkar draws dark worshippers.
Everything is wet, muddy, and slightly hopeless. A forgotten corner of the world.""",

    4: """Blasted Lands: Scarred wasteland corrupted by the Dark Portal's energies.
Demons, mutated wildlife, and fel creatures roam freely. The very ground feels
wrong. Nethergarde Keep watches the Portal nervously. A zone that feels like the
edge of the world, where everything went wrong.""",

    51: """Searing Gorge: Volcanic wasteland controlled by Dark Iron dwarves.
Lava flows, fire elementals, and slag pits dominate the landscape. Thorium Point
is a small outpost of resistance. Brutally hot and industrially ravaged.""",

    46: """Burning Steppes: Blackrock orcs and black dragons rule this scorched
land. The Blackrock Spire looms overhead. Fire elementals and dragonkin patrol.
A high-level warzone where the Dark Horde masses its forces.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Western Plaguelands: Diseased farmland crawling with undead. Andorhal
is a ruined city contested by multiple factions. The Scourge presence is heavy,
and Cauldrons spread plague across the land. The Scarlet Crusade fights
fanatically. A zone of death, disease, and desperate struggles.""",

    139: """Eastern Plaguelands: The Scourge's heartland. Undead everywhere -
ghouls, abominations, necromancers. Stratholme burns eternally, Naxxramas floats
overhead. Light's Hope Chapel is humanity's last stand. The most corrupted,
dangerous zone on the continent. Hope is scarce here.""",

    41: """Deadwind Pass: Desolate canyon leading to Karazhan. Deadwind ogres lurk
in caves, restless spirits wander, and demonic corruption seeps from the tower.
The land itself feels drained of life. Creepy, empty, and ominous - something
terrible happened here.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Teldrassil: Massive world tree home to the night elves. The forest
is ancient and magical but something feels wrong - corruption spreads through
the wildlife. Gnarlpine furbolgs have gone hostile, and timberlings cause trouble.
Darnassus sits serenely above. Beautiful but troubled.""",

    148: """Darkshore: Long, misty coastline with an eerie atmosphere. Ancient
night elf ruins scatter the landscape. Murlocs and naga plague the beaches,
corrupted wildlife roams the forests. Auberdine is the main hub but feels
isolated. Something dark is corrupting the land.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Durotar: Harsh, rocky desert home to the orcs. Scorpids, raptors, and
boars roam the red canyons. Quilboar raid from the south, and Burning Blade
cultists hide in caves. Orgrimmar's gates welcome warriors. A zone that embodies
the Horde's strength through adversity.""",

    215: """Mulgore: Peaceful rolling plains of the tauren. Kodo beasts graze
lazily, but harpies swoop from the mountains and Venture Co. goblins exploit the
land. Thunder Bluff rises on its mesas. The most serene Horde zone - wide skies
and gentle winds, though danger lurks at the edges.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    17: """The Barrens: Vast, dry savanna stretching endlessly. Centaur, quilboar,
raptors, lions, and zhevra everywhere. The Crossroads is a major hub where
adventurers gather. Known for long travel times and memorable general chat.
A defining Horde leveling experience.""",

    331: """Ashenvale: Ancient night elf forest under siege. The Horde pushes in
from the east, demons lurk in the shadows, and furbolgs have gone mad. Astranaar
and Splintertree outpost represent the faction conflict. A beautiful forest
marred by war and corruption.""",

    405: """Desolace: Barren, grey wasteland. Centaur tribes war endlessly with
each other and everyone else. Kodo graveyards dot the landscape. The zone feels
empty and hopeless - even the sky seems drained of color. One of the most
depressing places in Azeroth.""",

    400: """Thousand Needles: Dramatic canyon of towering stone spires. Before
the Cataclysm, a dry desert floor with the Shimmering Flats raceway. Centaur
and harpies control various pillars. The Great Lift connects to the Barrens.
Visually stunning but harsh to travel.""",

    15: """Dustwallow Marsh: Hot, humid swampland. Black dragons scheme in the
south, hostile crocolisks and spiders lurk in the murk, and Theramore stands as
an Alliance fortress. The ruins of a burned inn hint at darker plots.
Oppressively muggy and dangerous.""",

    357: """Feralas: Lush, overgrown jungle and forest. Yetis in the mountains,
naga on the coast, ogres and gnolls throughout. Twin Colossals are massive trees,
and Dire Maul's ruins loom large. A wild, untamed zone that swallows travelers.""",

    440: """Tanaris: Scorching desert surrounding the goblin port of Gadgetzan.
Pirates, bandits, basilisks, and silithid insects everywhere. Zul'Farrak's trolls
are hostile. The Caverns of Time hide nearby. Blazing hot during the day, the
desert is unforgiving but profitable.""",

    16: """Azshara: Ruined night elf coastline, hauntingly beautiful but empty.
Naga control much of the shore, and the Blue Dragonflight maintains a presence.
Giant sea creatures roam, and Legion remnants linger at Forlorn Ridge. The zone
feels abandoned and sad - a monument to what was lost.""",

    361: """Felwood: Corrupted forest oozing with demonic taint. Slimes, satyrs,
and corrupted wildlife plague every corner. The trees themselves seem sick.
Timbermaw furbolgs are wary but neutral; Deadwood furbolgs are hostile. A zone
that makes you feel unclean just passing through.""",

    490: """Un'Goro Crater: Prehistoric jungle crater teeming with dinosaurs.
Devilsaurs are apex predators, raptors hunt in packs, and elementals guard
pylons. It's like stepping back in time - lush, dangerous, and full of wonder.
Crystal formations hold mysterious power.""",

    493: """Moonglade: Sacred druid sanctuary. Largely peaceful and safe, with
few hostile creatures. The Cenarion Circle gathers here, and the zone feels
timeless and serene - a respite from the chaos of the world. Druids meet at
Nighthaven.""",

    618: """Winterspring: Frozen highland of eternal winter. Frostsaber cats,
yetis, and ice giants roam the snow. Everlook is a goblin town of questionable
dealings. Winterfall furbolgs are hostile throughout. Beautiful but deadly cold,
the zone rewards only the well-prepared.""",

    1377: """Silithus: Desert wasteland swarming with silithid insects. The
Qiraji threat looms from Ahn'Qiraj. Cenarion Circle druids fight desperately
against the hive. Sand storms, giant bugs, and an overwhelming sense that
something ancient and evil stirs beneath the sands.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Hellfire Peninsula: Shattered red wasteland, first zone through the
Dark Portal. Fel orcs, demons, and Burning Legion forces everywhere. Honor Hold
and Thrallmar are the faction bases. The sky is torn, the ground is cracked,
and war rages constantly. Brutal introduction to Outland.""",

    3521: """Zangarmarsh: Surreal mushroom swamp glowing with bioluminescence.
Giant fungi tower overhead, sporebats float lazily, and naga drain the waters.
Cenarion Refuge works to save the ecosystem. Strangely beautiful and alien -
nothing here looks like Azeroth.""",

    3518: """Nagrand: Floating islands and lush green plains - Outland's last
paradise. Clefthoof and talbuks graze peacefully, but ogres and the Burning
Blade threaten the land. Garadar and Telaar represent the factions. The most
beautiful zone in Outland, a reminder of what Draenor once was.""",

    3519: """Terokkar Forest: Divided between lush forest and the bone-littered
wastes around Auchindoun. Arakkoa lurk in the trees, and the Shadow Council
conducts dark rituals. Shattrath City is the neutral capital. A zone of
contrasts between life and death.""",

    3522: """Blade's Edge Mountains: Jagged, hostile landscape of towering spikes.
Ogres rule here, and gronn giants are the apex predators. The Burning Legion
maintains outposts, and dragons circle overhead. Dangerous terrain where the
land itself seems to want to kill you.""",

    3520: """Shadowmoon Valley: Dark, fel-corrupted wasteland. The Black Temple
looms ominously, and Illidan's forces control the region. Demons, fel orcs, and
death knights patrol. The sky burns green. The most dangerous and oppressive
zone in Outland - hope feels distant here.""",

    3523: """Netherstorm: Shattered islands floating in the Twisting Nether.
Mana forges harvest the land's energy, blood elves and ethereals compete for
resources, and mana creatures roam wildly. The eco-domes preserve life
artificially. A zone tearing itself apart at the seams.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Borean Tundra: Frozen coastal tundra, one of two entry points to
Northrend. Nerubians burrow beneath, the Scourge probes defenses, and tuskarr
fish the shores. Warsong Hold and Valiance Keep are the faction strongholds.
The cold bites hard - winter is just beginning.""",

    495: """Howling Fjord: Dramatic Viking-inspired coastline with towering
cliffs. Vrykul warriors raid from their villages, and the Scourge corrupts the
dead. Valgarde and Vengeance Landing are the landing points. The fjords are
breathtaking but the vrykul are relentless.""",

    394: """Grizzly Hills: Forested frontier that feels almost peaceful. Furbolgs
corrupted by the Scourge, iron dwarves dig for secrets, and the worgen curse
spreads. Logging operations scar the hillsides. A zone that would be beautiful
if not for the creeping corruption.""",

    3711: """Sholazar Basin: Lush jungle crater untouched by the Scourge,
maintained by titan technology. Dinosaurs, gorillas, and exotic beasts thrive.
The Frenzyheart and Oracles wage petty war. An unexpected paradise in frozen
Northrend - but something threatens the pylons.""",

    66: """Zul'Drak: Frozen troll kingdom in collapse. The Drakkari sacrifice
their own gods to fight the Scourge. Undead and desperate trolls clash
everywhere. The zone feels like watching a civilization die - grim, cold,
and hopeless.""",

    67: """Storm Peaks: Towering frozen mountains home to titan secrets. Storm
giants, iron dwarves, and proto-drakes dominate. Ulduar's entrance looms above.
The Sons of Hodir are wary of outsiders. Epic scale, brutal conditions,
ancient mysteries.""",

    210: """Icecrown: The Lich King's domain. Endless undead armies, necropolis
fortresses, and the Icecrown Citadel itself. The Argent Crusade makes its final
stand. The air itself feels dead. This is the end of the road - victory
or oblivion.""",
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
# Production values: 65% plain, 15% quest, 12% loot, 8% quest+reward
MSG_TYPE_PLAIN = 65
MSG_TYPE_QUEST = 80        # 15% chance (66-80)
MSG_TYPE_LOOT = 92         # 12% chance (81-92)
MSG_TYPE_QUEST_REWARD = 100  # 8% chance (93-100)

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


def wait_for_database(config: dict, max_retries: int = 30, initial_delay: float = 2.0) -> bool:
    """Wait for database to become available with exponential backoff.

    Args:
        config: Configuration dictionary
        max_retries: Maximum number of connection attempts
        initial_delay: Initial delay between retries (increases with backoff, max 30s)

    Returns:
        True if connected successfully, False if all retries exhausted
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_db_connection(config)
            conn.close()
            logger.info(f"Database connection established (attempt {attempt})")
            return True
        except mysql.connector.Error as e:
            if attempt == max_retries:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                return False
            logger.info(f"Waiting for database... (attempt {attempt}/{max_retries}, retry in {delay:.1f}s)")
            time.sleep(delay)
            delay = min(delay * 1.5, 30.0)  # Exponential backoff, max 30s

    return False


# =============================================================================
# ZONE DATA QUERIES
# =============================================================================
def get_zone_level_range(zone_id: int, bot_level: int) -> Tuple[int, int]:
    """Get level range for a zone, falling back to bot level if unknown."""
    if zone_id in ZONE_LEVELS:
        return ZONE_LEVELS[zone_id]
    # Fallback: use bot level +/- 5
    return (max(1, bot_level - 5), bot_level + 5)


def get_zone_flavor(zone_id: int) -> Optional[str]:
    """Get rich zone flavor text for immersive context.

    Returns a paragraph describing the zone's atmosphere, dangers, and feel.
    Returns None if zone not in ZONE_FLAVOR.
    """
    return ZONE_FLAVOR.get(zone_id)


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

        # Query zone quests - use MIN(ID) to get one quest per title
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
            LEFT JOIN item_template i1 ON q.RewardItem1 = i1.entry
            LEFT JOIN item_template i2 ON q.RewardItem2 = i2.entry
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

    Uses coordinate-based queries for accuracy:
    1. First tries zone coordinate boundaries (most accurate, no server config needed)
    2. Falls back to level-based query if zone not in coordinate map

    Returns a list of mob markers ([[npc:entry:name]]) that can be randomly selected for context.
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

        # Filter for valid mobs (beasts, humanoids, undead, etc.)
        # type: 1=Beast, 2=Dragonkin, 3=Demon, 4=Elemental, 5=Giant, 6=Undead, 7=Humanoid, 8=Critter, 9=Mechanical, 10=NotSpecified
        # Exclude friendly factions (35=Friendly, 79=Darnassus, 80=Undercity, 84=Stormwind, etc.)
        # Note: We rely on coordinates + level + type to filter, rather than trying to list all hostile factions
        mob_filter = """
            ct.type IN (1, 2, 3, 4, 5, 6, 7, 9, 10)
            AND ct.faction NOT IN (35, 55, 79, 80, 84, 126, 875, 876, 1078, 1080)
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

        # APPROACH 1: Use coordinate boundaries (accurate, no server config needed)
        if zone_id in ZONE_COORDINATES:
            map_id, min_x, max_x, min_y, max_y = ZONE_COORDINATES[zone_id]
            cursor.execute(f"""
                SELECT DISTINCT ct.entry, ct.name
                FROM creature c
                JOIN creature_template ct ON c.id1 = ct.entry
                WHERE c.map = %s
                  AND c.position_x BETWEEN %s AND %s
                  AND c.position_y BETWEEN %s AND %s
                  AND ct.minlevel >= %s AND ct.maxlevel <= %s
                  AND {mob_filter}
                ORDER BY RAND()
                LIMIT 50
            """, (map_id, min_x, max_x, min_y, max_y, max(1, min_level - 3), max_level + 5))
            # Format as NPC markers for link conversion
            mobs = [f"[[npc:{row['entry']}:{row['name']}]]" for row in cursor.fetchall()]

            if mobs:
                logger.info(f"Found {len(mobs)} mobs for zone {zone_id} using coordinates")

        # APPROACH 2: Fall back to level-based query if zone not mapped
        if not mobs:
            cursor.execute(f"""
                SELECT DISTINCT ct.entry, ct.name
                FROM creature_template ct
                WHERE ct.minlevel >= %s AND ct.maxlevel <= %s
                  AND {mob_filter}
                ORDER BY RAND()
                LIMIT 50
            """, (max(1, min_level - 2), max_level + 3))
            mobs = [f"[[npc:{row['entry']}:{row['name']}]]" for row in cursor.fetchall()]
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
        link = format_item_link(
            item_data['item_id'],
            item_data.get('item_quality', 2),
            item_data['item_name']
        )
        if re.search(item_pattern, result):
            result = re.sub(item_pattern, link, result)
        else:
            # Fallback: LLM didn't use placeholder, look for [ItemName] patterns
            # Replace first bracketed item-like word with the correct item link
            # This catches hallucinated items like [Malachite] when LLM ignores prompt
            bracket_pattern = r'\[([A-Z][a-zA-Z\' ]{2,25})\]'
            if re.search(bracket_pattern, result):
                result = re.sub(bracket_pattern, link, result, count=1)

    return result


def cleanup_message(message: str) -> str:
    """Clean up any formatting issues from LLM output."""
    result = message

    # Convert npc:ID:Name markers to just the creature name (plain text)
    # Handles: [[npc:1234:Creature Name]], [npc:1234:Creature Name], npc:1234:Creature Name
    result = re.sub(r'\[\[npc:\d+:([^\]]+)\]\]', r'\1', result)
    result = re.sub(r'\[npc:\d+:([^\]]+)\]', r'\1', result)
    result = re.sub(r'npc:\d+:([A-Za-z][A-Za-z\' ]+)', r'\1', result)

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
    max_delay = int(config.get('LLMChatter.MessageDelayMax', 30000)) / 1000.0

    # Very short messages (ty, np, lol, yes, no) - quick replies
    if message_length < 10:
        if random.random() < 0.4:
            return random.uniform(2.0, 5.0)  # Quick response
        else:
            return random.uniform(5.0, 12.0)  # Slightly distracted

    # Short messages (< 30 chars) - moderate delays
    elif message_length < 30:
        typing_time = message_length / random.uniform(3.0, 8.0)  # Varied typing speed
        distraction = random.uniform(3.0, 15.0)  # Flat random, not clustered
        return min(typing_time + distraction, max_delay)

    # Medium messages (30-80 chars)
    elif message_length < 80:
        typing_time = message_length / random.uniform(2.5, 6.0)
        distraction = random.uniform(5.0, 18.0)
        return min(typing_time + distraction, max_delay)

    # Longer messages - longer delays (player taking time to type)
    else:
        typing_time = message_length / random.uniform(2.0, 5.0)
        distraction = random.uniform(8.0, 22.0)
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
def build_plain_statement_prompt(bot: dict, zone_id: int = 0, zone_mobs: list = None) -> str:
    """Build a dynamically varied prompt for a plain text statement."""
    parts = []

    # Core context (always include zone)
    parts.append(f"Generate a brief WoW General chat message from a player in {bot['zone']}.")

    # Zone flavor - rich context about the zone's atmosphere and feel
    zone_flavor = get_zone_flavor(zone_id)
    if zone_flavor:
        parts.append(f"Zone context: {zone_flavor}")

    # Randomly include level (60% chance)
    if random.random() < 0.6:
        parts.append(f"Player level: {bot['level']}")

    # Zone creature context - tells the LLM what actually exists in this zone
    if zone_mobs:
        parts.append(f"Creatures here: {', '.join(zone_mobs)}")
        parts.append("IMPORTANT: If mentioning any creature, ONLY use ones from the list above. Include the [[npc:...]] marker exactly as shown.")

    # Random tone and mood - these shape the personality
    parts.append(f"Tone: {pick_random_tone()}")
    parts.append(f"Mood: {pick_random_mood()}")

    # Pick random examples (2-3 from random sets)
    examples = pick_random_examples(PLAIN_EXAMPLE_SETS, random.randint(2, 3))
    parts.append("Example styles: " + ", ".join(f'"{ex}"' for ex in examples))

    # Build dynamic guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Plain text only, except [[npc:...]] markers for creature names")
    guidelines.append("Do NOT mention your race or class")
    if zone_mobs:
        guidelines.append("Only mention creatures from the provided list - do NOT invent creatures")
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


def build_plain_conversation_prompt(bots: List[dict], zone_id: int = 0, zone_mobs: list = None) -> str:
    """Build a dynamically varied prompt for a plain conversation with 2-4 bots.

    Args:
        bots: List of 2-4 bot dicts with name, race, class, level, zone
        zone_id: Zone ID for flavor text lookup
        zone_mobs: Optional list of mob markers from the zone
    """
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    if bot_count == 2:
        parts.append(f"Generate a casual General chat exchange between two WoW players in {bots[0]['zone']}.")
    else:
        parts.append(f"Generate a casual General chat exchange between {bot_count} WoW players in {bots[0]['zone']}.")

    # Zone flavor - rich context about the zone's atmosphere and feel
    zone_flavor = get_zone_flavor(zone_id)
    if zone_flavor:
        parts.append(f"Zone context: {zone_flavor}")

    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(f"Names: Sometimes use their name when addressing directly (maybe 1-2 times in a conversation), but not every message - vary it naturally like real players.")

    # Randomly include some character details (40% chance per bot)
    for bot in bots:
        if random.random() < 0.4:
            parts.append(f"{bot['name']} is a {bot['race']} {bot['class']}")

    # Zone creature context - tells the LLM what actually exists in this zone
    if zone_mobs:
        parts.append(f"Creatures here: {', '.join(zone_mobs)}")
        parts.append("IMPORTANT: If mentioning any creature, ONLY use ones from the list above. Include the [[npc:...]] marker exactly as shown.")

    # Random tone for the overall conversation
    parts.append(f"Overall tone: {pick_random_tone()}")

    # Generate mood sequence - this is the "script" the LLM must follow
    # More messages for more participants
    min_msgs = bot_count
    max_msgs = bot_count + 3
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    parts.append(f"\nMOOD SEQUENCE (follow this for each message):")
    for i, mood in enumerate(mood_sequence):
        # Cycle through speakers
        speaker = bot_names[i % bot_count]
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
    guidelines.append("Plain text only, except [[npc:...]] markers for creature names")
    guidelines.append("Follow the mood sequence above")
    if zone_mobs:
        guidelines.append("Only mention creatures from the provided list - do NOT invent creatures")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction with examples for all speakers
    example_msgs = ',\n  '.join([f'{{"speaker": "{name}", "message": "..."}}' for name in bot_names])
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_quest_conversation_prompt(bots: List[dict], quest: dict) -> str:
    """Build a dynamically varied prompt for a quest conversation with 2-4 bots.

    Args:
        bots: List of 2-4 bot dicts with name, race, class, level, zone
        quest: Quest data dict with quest_name, description, etc.
    """
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    parts.append(f"Generate a casual General chat exchange about a quest in {bots[0]['zone']}.")
    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(f"Names: Sometimes use their name when addressing directly (maybe 1-2 times in a conversation), but not every message - vary it naturally.")

    # Quest info
    parts.append(f"Quest: {quest['quest_name']} (use {{{{quest:{quest['quest_name']}}}}} placeholder)")
    if quest.get('description') and random.random() < 0.4:
        parts.append(f"Quest involves: {quest['description'][:60]}")

    # Random tone for the overall conversation
    parts.append(f"Overall tone: {pick_random_tone()}")

    # Generate mood sequence - the "script" for the conversation
    min_msgs = bot_count
    max_msgs = bot_count + 3
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    parts.append(f"\nMOOD SEQUENCE (follow this for each message):")
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
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

    # JSON format instruction with examples for all speakers
    example_msgs = ',\n  '.join([f'{{"speaker": "{name}", "message": "..."}}' for name in bot_names])
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_loot_conversation_prompt(bots: List[dict], item: dict) -> str:
    """Build a dynamically varied prompt for a loot conversation with 2-4 bots.

    Args:
        bots: List of 2-4 bot dicts with name, race, class, level, zone
        item: Item data dict with item_name, item_quality, etc.
    """
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    quality_names = {0: "gray", 1: "white", 2: "green", 3: "blue", 4: "purple"}
    quality = quality_names.get(item.get('item_quality', 2), "green")
    item_placeholder = f"{{{{item:{item['item_name']}}}}}"

    parts.append(f"Generate a casual General chat exchange about a loot drop in {bots[0]['zone']}.")
    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(f"Names: Sometimes use their name when addressing directly (maybe once in the conversation), but not every message - vary it naturally.")

    # Item info
    parts.append(f"Item: {item['item_name']} ({quality} quality)")
    parts.append(f"REQUIRED: Use {item_placeholder} placeholder when mentioning the item")

    # Random tone for the overall conversation
    parts.append(f"Overall tone: {pick_random_tone()}")

    # Generate mood sequence
    min_msgs = bot_count
    max_msgs = bot_count + 2
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    parts.append(f"\nMOOD SEQUENCE (follow this for each message):")
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(f"  Message {i+1} ({speaker}): {mood}")

    # Loot conversation angles
    angles = [
        "one player got the drop and others are jealous/congratulating",
        "discussing if the item is good for their class",
        "debating whether to vendor or auction it",
        "one asking if others need the drop",
        "comparing drops they've gotten today",
    ]
    parts.append(f"Angle: {random.choice(angles)}")

    # Guidelines
    guidelines = build_dynamic_guidelines()
    guidelines.append("Use item placeholder at least once")
    guidelines.append("Follow the mood sequence above")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction with examples for all speakers
    example_msgs = ',\n  '.join([f'{{"speaker": "{name}", "message": "..."}}' for name in bot_names])
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
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


def fuzzy_name_match(speaker: str, expected_name: str, max_distance: int = 2) -> bool:
    """Check if speaker matches expected_name with tolerance for typos.

    Uses simple Levenshtein-like distance: counts character differences.
    Returns True if names match within max_distance edits.
    """
    s1 = speaker.lower()
    s2 = expected_name.lower()

    # Exact match
    if s1 == s2:
        return True

    # Length difference too big
    if abs(len(s1) - len(s2)) > max_distance:
        return False

    # Simple character-by-character comparison
    # Count differences (substitutions, missing chars)
    differences = 0
    i, j = 0, 0
    while i < len(s1) and j < len(s2):
        if s1[i] != s2[j]:
            differences += 1
            # Try to align by skipping one char in longer string
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

    # Add remaining characters as differences
    differences += (len(s1) - i) + (len(s2) - j)

    return differences <= max_distance


def parse_conversation_response(response: str, bot_names: List[str]) -> list:
    """Parse conversation JSON response into message list.

    Args:
        response: Raw LLM response containing JSON array
        bot_names: List of valid bot names (2-4 names)

    Returns:
        List of dicts with 'name' and 'message' keys
    """
    try:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            messages = json.loads(json_match.group())
            result = []
            for msg in messages:
                speaker = msg.get('speaker', '').strip()
                message = msg.get('message', '').strip()
                if speaker and message:
                    # Use fuzzy matching to handle minor typos in names
                    matched_name = None
                    for bot_name in bot_names:
                        if fuzzy_name_match(speaker, bot_name):
                            matched_name = bot_name
                            break
                    if matched_name:
                        result.append({'name': matched_name, 'message': message})
            return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse conversation JSON: {e}")
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
            quality_weights = {0: 35, 1: 30, 2: 22, 3: 10, 4: 3}  # Blue 10%, Epic 3%
            weights = [quality_weights.get(item.get('item_quality', 2), 10) for item in loot]
            item_data = random.choices(loot, weights=weights, k=1)[0]
            # Check if bot's class can use the item
            item_can_use = can_class_use_item(bot['class'], item_data.get('allowable_class', -1))
            quality_names = {0: "gray", 1: "white", 2: "green", 3: "blue", 4: "epic"}
            logger.info(f"Selected loot: {item_data['item_name']} ({quality_names.get(item_data.get('item_quality', 2), 'unknown')}) - {bot['class']} can use: {item_can_use}")
        else:
            msg_type = "plain"  # Fallback

    # Build appropriate prompt
    zone_id = request.get('zone_id', 0)
    if msg_type == "plain":
        # Get zone mobs for context - pass up to 10 random mobs so LLM knows what exists
        zone_mobs = []
        mobs = query_zone_mobs(config, zone_id, bot['level'])
        if mobs:
            zone_mobs = random.sample(mobs, min(10, len(mobs)))
        # Log zone context being used
        zone_flavor = get_zone_flavor(zone_id)
        logger.info(f"Zone context: id={zone_id}, flavor={'yes' if zone_flavor else 'no'}, mobs={len(zone_mobs)}")
        prompt = build_plain_statement_prompt(bot, zone_id, zone_mobs)
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
        prompt = build_plain_statement_prompt(bot, zone_id)

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
        db.commit()

        return True
    return False


def process_conversation(db, cursor, client, config, request, bots: List[dict]):
    """Process a conversation request with 2-4 bots.

    Args:
        db: Database connection
        cursor: Database cursor
        client: LLM client (Anthropic or OpenAI)
        config: Configuration dict
        request: Queue request row
        bots: List of 2-4 bot dicts with guid, name, class, race, level, zone
    """
    channel = 'general'
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    # Create guid lookup for message insertion
    bot_guids = {b['name']: b['guid'] for b in bots}

    logger.info(f"Processing {bot_count}-bot conversation: {', '.join(bot_names)}")

    # Select message type (conversations can be plain, quest, or loot)
    roll = random.randint(1, 100)
    if roll <= 50:
        msg_type = "plain"
    elif roll <= 75:
        msg_type = "quest"
    else:
        msg_type = "loot"

    # Get quest/loot data if needed
    quest_data = None
    item_data = None

    if msg_type == "quest":
        quests = query_zone_quests(config, request.get('zone_id', 0), bots[0]['level'])
        if quests:
            quest_data = random.choice(quests)
            logger.info(f"Selected quest: {quest_data['quest_name']}")
        else:
            msg_type = "plain"

    if msg_type == "loot":
        loot = query_zone_loot(config, request.get('zone_id', 0), bots[0]['level'])
        if loot:
            quality_weights = {0: 30, 1: 30, 2: 25, 3: 12, 4: 3}
            weights = [quality_weights.get(item.get('item_quality', 2), 10) for item in loot]
            item_data = random.choices(loot, weights=weights, k=1)[0]
            logger.info(f"Selected loot for conversation: {item_data['item_name']}")
        else:
            msg_type = "plain"

    # Build prompt
    zone_id = request.get('zone_id', 0)
    if msg_type == "plain":
        # Get zone mobs for context - pass up to 10 random mobs so LLM knows what exists
        zone_mobs = []
        mobs = query_zone_mobs(config, zone_id, bots[0]['level'])
        if mobs:
            zone_mobs = random.sample(mobs, min(10, len(mobs)))
        # Log zone context being used
        zone_flavor = get_zone_flavor(zone_id)
        logger.info(f"Zone context: id={zone_id}, flavor={'yes' if zone_flavor else 'no'}, mobs={len(zone_mobs)}")
        prompt = build_plain_conversation_prompt(bots, zone_id, zone_mobs)
    elif msg_type == "quest":
        prompt = build_quest_conversation_prompt(bots, quest_data)
    else:  # loot
        prompt = build_loot_conversation_prompt(bots, item_data)

    # Call LLM
    response = call_llm(client, prompt, config)

    if response:
        messages = parse_conversation_response(response, bot_names)

        if messages:
            logger.info(f"Conversation in {bots[0]['zone']} with {len(messages)} messages ({bot_count} participants):")

            cumulative_delay = 0.0
            for i, msg in enumerate(messages):
                bot_guid = bot_guids.get(msg['name'], bots[0]['guid'])

                # Replace placeholders and cleanup
                final_message = replace_placeholders(msg['message'], quest_data, item_data)
                final_message = cleanup_message(final_message)

                if i > 0:
                    delay = calculate_dynamic_delay(len(final_message), config)
                    cumulative_delay += delay
                    logger.info(f"    Delay calc: msg_len={len(final_message)}, delay={delay:.1f}s")

                cursor.execute("""
                    INSERT INTO llm_chatter_messages
                    (queue_id, sequence, bot_guid, bot_name, message, channel, deliver_at)
                    VALUES (%s, %s, %s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL %s SECOND))
                """, (request['id'], i, bot_guid, msg['name'], final_message, channel, cumulative_delay))

                logger.info(f"  [{i}] +{cumulative_delay:.1f}s {msg['name']}: {final_message}")

            db.commit()
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
            # Build list of 2-4 bots from request
            bots = []

            # Bot 1 (always present)
            bots.append({
                'guid': request['bot1_guid'],
                'name': request['bot1_name'],
                'class': request['bot1_class'],
                'race': request['bot1_race'],
                'level': request['bot1_level'],
                'zone': request['bot1_zone']
            })

            # Bot 2 (always present for conversations)
            if request.get('bot2_guid'):
                bots.append({
                    'guid': request['bot2_guid'],
                    'name': request['bot2_name'],
                    'class': request['bot2_class'],
                    'race': request['bot2_race'],
                    'level': request['bot2_level'],
                    'zone': request['bot1_zone']
                })

            # Bot 3 (optional)
            if request.get('bot3_guid'):
                bots.append({
                    'guid': request['bot3_guid'],
                    'name': request['bot3_name'],
                    'class': request['bot3_class'],
                    'race': request['bot3_race'],
                    'level': request['bot3_level'],
                    'zone': request['bot1_zone']
                })

            # Bot 4 (optional)
            if request.get('bot4_guid'):
                bots.append({
                    'guid': request['bot4_guid'],
                    'name': request['bot4_name'],
                    'class': request['bot4_class'],
                    'race': request['bot4_race'],
                    'level': request['bot4_level'],
                    'zone': request['bot1_zone']
                })

            success = process_conversation(db, cursor, client, config, request, bots)

        # Mark as completed
        cursor.execute(
            "UPDATE llm_chatter_queue SET status = 'completed', processed_at = NOW() WHERE id = %s",
            (request_id,)
        )
        db.commit()
        return True

    except Exception as e:
        logger.error(f"Error processing request #{request_id}: {e}")
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
    logger.info("LLM Chatter Bridge v3.1")
    logger.info("=" * 60)
    logger.info(f"Provider: {provider}")
    logger.info(f"Model: {model} (alias: {model_alias})")
    logger.info(f"Poll interval: {poll_interval}s")
    logger.info(f"Max tokens: {config.get('LLMChatter.MaxTokens', 200)}")
    logger.info(f"Message type distribution: {MSG_TYPE_PLAIN}% plain, "
                f"{MSG_TYPE_QUEST - MSG_TYPE_PLAIN}% quest, "
                f"{MSG_TYPE_LOOT - MSG_TYPE_QUEST}% loot, "
                f"{MSG_TYPE_QUEST_REWARD - MSG_TYPE_LOOT}% quest+reward")
    logger.info("=" * 60)

    # Wait for database to be ready (handles Docker startup order)
    if not wait_for_database(config):
        logger.error("Could not connect to database. Exiting.")
        sys.exit(1)

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
            time.sleep(poll_interval)


if __name__ == '__main__':
    main()
