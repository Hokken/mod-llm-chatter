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

# Zone-level transport cooldowns (in-memory, resets on bridge restart)
# Key: zone_id, Value: timestamp of last transport announcement
_zone_transport_cooldowns: Dict[int, float] = {}
ZONE_TRANSPORT_COOLDOWN_SECONDS = 300  # 5 minutes between transport announcements per zone

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
# ZONE NAMES - Human-readable zone names for prompts
# =============================================================================
ZONE_NAMES = {
    # Eastern Kingdoms
    1: "Dun Morogh", 12: "Elwynn Forest", 38: "Loch Modan", 40: "Westfall",
    44: "Redridge Mountains", 46: "Burning Steppes", 47: "The Hinterlands",
    51: "Searing Gorge", 85: "Tirisfal Glades", 130: "Silverpine Forest",
    267: "Hillsbrad Foothills", 33: "Stranglethorn Vale", 45: "Arathi Highlands",
    3: "Badlands", 8: "Swamp of Sorrows", 4: "Blasted Lands", 10: "Duskwood",
    11: "Wetlands", 139: "Eastern Plaguelands", 28: "Western Plaguelands",
    41: "Deadwind Pass", 1519: "Stormwind City", 1537: "Ironforge",
    1497: "Undercity",
    # Kalimdor
    14: "Durotar", 215: "Mulgore", 141: "Teldrassil", 148: "Darkshore",
    17: "The Barrens", 331: "Ashenvale", 405: "Desolace", 400: "Thousand Needles",
    15: "Dustwallow Marsh", 357: "Feralas", 440: "Tanaris", 16: "Azshara",
    361: "Felwood", 490: "Un'Goro Crater", 493: "Moonglade", 618: "Winterspring",
    1377: "Silithus", 1637: "Orgrimmar", 1638: "Thunder Bluff", 1657: "Darnassus",
    # Outland
    3483: "Hellfire Peninsula", 3518: "Nagrand", 3519: "Terokkar Forest",
    3520: "Shadowmoon Valley", 3521: "Zangarmarsh", 3522: "Blade's Edge Mountains",
    3523: "Netherstorm", 3524: "Shattrath City", 3703: "Shattrath City",
    3430: "Eversong Woods", 3433: "Ghostlands", 3487: "Silvermoon City",
    3525: "Bloodmyst Isle", 3557: "The Exodar", 4080: "Isle of Quel'Danas",
    # Northrend
    3537: "Borean Tundra", 495: "Howling Fjord", 394: "Grizzly Hills",
    3711: "Sholazar Basin", 66: "Zul'Drak", 67: "Storm Peaks", 210: "Icecrown",
    65: "Dragonblight", 2817: "Crystalsong Forest", 4395: "Dalaran",
    4197: "Wintergrasp", 4298: "The Oculus",
    # Other
    406: "Stonetalon Mountains", 148: "Darkshore", 16: "Azshara",
}

def get_zone_name(zone_id: int) -> str:
    """Get human-readable zone name from zone ID."""
    if zone_id in ZONE_NAMES:
        return ZONE_NAMES[zone_id]
    return f"zone {zone_id}"

# =============================================================================
# CLASS AND RACE MAPPINGS - Convert numeric IDs to names
# =============================================================================
CLASS_NAMES = {
    1: "Warrior", 2: "Paladin", 3: "Hunter", 4: "Rogue", 5: "Priest",
    6: "Death Knight", 7: "Shaman", 8: "Mage", 9: "Warlock", 11: "Druid"
}

RACE_NAMES = {
    1: "Human", 2: "Orc", 3: "Dwarf", 4: "Night Elf", 5: "Undead",
    6: "Tauren", 7: "Gnome", 8: "Troll", 10: "Blood Elf", 11: "Draenei"
}

def get_class_name(class_id: int) -> str:
    """Get human-readable class name from class ID."""
    return CLASS_NAMES.get(class_id, "Adventurer")

def get_race_name(race_id: int) -> str:
    """Get human-readable race name from race ID."""
    return RACE_NAMES.get(race_id, "Unknown")

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
        self.recent_loot: Dict[int, Dict[int, float]] = {}

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

    def get_recent_loot_ids(self, zone_id: int, cooldown_seconds: int) -> set:
        """Return item_ids seen recently in this zone."""
        now = time.time()
        if zone_id not in self.recent_loot:
            return set()
        # Clean expired entries
        recent = {
            item_id: ts
            for item_id, ts in self.recent_loot[zone_id].items()
            if now - ts < cooldown_seconds
        }
        self.recent_loot[zone_id] = recent
        return set(recent.keys())

    def mark_loot_seen(self, zone_id: int, item_id: int):
        """Mark a loot item as recently seen in this zone."""
        if zone_id not in self.recent_loot:
            self.recent_loot[zone_id] = {}
        self.recent_loot[zone_id][item_id] = time.time()
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
    Query loot appropriate for the zone.
    Uses coordinate-based filtering to get loot from creatures actually in the zone.
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
        # Use coordinate filtering if zone is in ZONE_COORDINATES for accuracy
        if zone_id in ZONE_COORDINATES:
            map_id, min_x, max_x, min_y, max_y = ZONE_COORDINATES[zone_id]
            cursor.execute("""
                SELECT DISTINCT
                    i.entry as item_id,
                    i.name as item_name,
                    i.Quality as item_quality,
                    i.AllowableClass as allowable_class,
                    ct.name as drops_from
                FROM creature c
                JOIN creature_template ct ON c.id1 = ct.entry
                JOIN creature_loot_template clt ON ct.lootid = clt.Entry
                JOIN item_template i ON clt.Item = i.entry
                WHERE c.map = %s
                  AND c.position_x BETWEEN %s AND %s
                  AND c.position_y BETWEEN %s AND %s
                  AND ct.minlevel >= %s AND ct.maxlevel <= %s
                  AND i.Quality IN (0, 1)
                  AND i.class IN (2, 4, 7)
                  AND clt.Chance >= 5
                ORDER BY RAND()
                LIMIT 15
            """, (map_id, min_x, max_x, min_y, max_y,
                  max(1, min_level - 3), max_level + 5))
            loot.extend(cursor.fetchall())
        else:
            # Fallback: level-based query if zone not in coordinate map
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


# =============================================================================
# WEATHER DATA
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
def calculate_dynamic_delay(message_length: int, config: dict, prev_message_length: int = 0) -> float:
    """
    Calculate a realistic delay based on message length with randomness.
    Accounts for:
    - Reading time for previous message
    - Thinking/reaction time
    - Typing time for current message
    - Random distraction (player busy fighting mobs, etc.)

    Not systematic - significant variance to feel natural.
    """
    min_delay = int(config.get('LLMChatter.MessageDelayMin', 1000)) / 1000.0
    max_delay = int(config.get('LLMChatter.MessageDelayMax', 30000)) / 1000.0

    # Reading time for previous message (if any) - modest impact
    reading_time = prev_message_length / random.uniform(4.0, 9.0) if prev_message_length > 0 else 0

    # Base reaction time - keep fairly small to avoid hitting max too often
    reaction_time = random.uniform(1.0, 4.0)

    # Typing time based on current message length
    # Average typing: 30-60 WPM = 2.5-5 chars/sec for casual chat
    if message_length < 15:
        # Very short (lol, ty, np, nice) - quick to type
        typing_time = random.uniform(1.0, 3.0)
    elif message_length < 40:
        # Short message
        typing_time = message_length / random.uniform(3.0, 6.0)
    elif message_length < 80:
        # Medium message
        typing_time = message_length / random.uniform(2.5, 5.0)
    else:
        # Long message - takes time
        typing_time = message_length / random.uniform(2.0, 4.0)

    # Random distraction - player might be fighting, looting, running, etc.
    # Heavily varies - sometimes quick, sometimes very delayed
    distraction_roll = random.random()
    if distraction_roll < 0.4:
        distraction = random.uniform(0, 3.0)  # Quick response
    elif distraction_roll < 0.85:
        distraction = random.uniform(2.0, 8.0)  # Normal - slightly busy
    else:
        distraction = random.uniform(6.0, 18.0)  # Delayed - was fighting/busy

    total_delay = reading_time + reaction_time + typing_time + distraction

    # Minimum delay MUST scale with message length - can't type fast
    # Target ~4 chars/sec + small reaction buffer
    minimum_for_length = (message_length / 4.0) + 2.0

    # Ensure at least the minimum for this message length
    total_delay = max(total_delay, minimum_for_length)

    # Global minimum
    total_delay = max(total_delay, min_delay, 4.0)

    # Add small jitter so similar lengths don't always map to the same delay
    total_delay *= random.uniform(0.85, 1.20)

    return min(total_delay, max_delay)


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
    "neutral",
    "dramatic",
    "deadpan",
    "roleplaying",
    "nostalgic",
    "impatient",
    "grateful",
    "showing off",
    "self-deprecating",
    "philosophical",
    "surprised",
    "helpful",
    "geeky",
    "tired",
    "competitive",
    "distracted",
]

# Creative twists - random modifiers to push creativity (picked ~30% of the time)
CREATIVE_TWISTS = [
    # Structure twists
    "Start with an interjection",
    "End mid-thought with ...",
    "Use a single word or two-word reaction",
    "Ask a rhetorical question",
    "Answer your own question",
    "Trail off at the end",
    "Start mid-sentence as if continuing a thought",
    # Content twists
    "Include an unexpected observation",
    "Reference something mundane from real life",
    "Use a metaphor or comparison",
    "Mention something completely unrelated briefly",
    "React to something nobody else mentioned",
    "Misremember something slightly",
    "Get distracted mid-message",
    "Correct yourself mid-sentence",
    # Tone twists
    "Be unusually brief",
    "Overreact to something minor",
    "Underreact to something major",
    "Sound half-asleep",
    "Be weirdly specific about a detail",
    "Sound like you're multitasking",
    "Respond as if you misheard something",
    # Player behavior twists
    "Mention a keybind or UI element",
    "Reference lag or FPS",
    "Sound like you're eating while typing",
    "Mention being AFK briefly",
    "Reference the time of day IRL",
    "Sound like you just got back to keyboard",
    "Mention having multiple tabs/windows open",
    # Social twists
    "Respond to an imaginary previous message",
    "Change topic abruptly",
    "Agree with something nobody said",
    "Disagree politely with thin air",
    "Give unsolicited advice",
    "Ask a question then immediately answer it yourself",
    # Expression twists
    "Use onomatopoeia",
    "Stretch a woooord for emphasis",
    "Use ALL CAPS for one word only",
    "Add a random lol or haha mid-sentence",
    "Use excessive punctuation for one thing!!!",
    "Be overly casual with spelling",
    "Use gaming slang naturally",
]

# Message categories - abstract directions that force original content (no copying)
MESSAGE_CATEGORIES = [
    # Observations
    "observation about surroundings or atmosphere",
    "noticing something interesting nearby",
    "comment about the zone's vibe",
    "remarking on how empty or busy the area is",
    "noting something weird or unexpected",
    # Reactions
    "reaction to something that just happened",
    "celebrating a small victory",
    "expressing relief after a close call",
    "pleasant surprise",
    "genuine excitement about something",
    "feeling lucky",
    "enjoying the moment",
    # Questions
    "question to other players",
    "asking if anyone else experienced something",
    "wondering aloud about game mechanics",
    "asking for directions or location help",
    "checking if others are having the same issue",
    # Social
    "looking for group or help with something",
    "offering to help others",
    "greeting or acknowledging other players",
    "friendly banter with nearby players",
    "inviting others to join activity",
    "complimenting another player",
    "thanking someone",
    "encouraging others",
    "sharing enthusiasm with the community",
    # Mild frustrations (keep minimal)
    "mild frustration played for laughs",
    "joking about bad luck",
    # Humor and joy
    "lighthearted joke",
    "playful observation",
    "finding humor in the situation",
    "absurd or random humor",
    "pun or wordplay",
    "laughing at something silly",
    "infectious enthusiasm",
    "wholesome moment",
    # Progress and grind
    "comment about the grind or progress",
    "sharing level or milestone progress",
    "talking about goals or plans",
    "reflecting on how long something is taking",
    "comparing current progress to past",
    # Creatures and combat
    "comment about creature behavior or difficulty",
    "remarking on enemy abilities",
    "discussing pull strategies",
    "noting creature spawn patterns",
    "commenting on aggro or adds",
    # Gear and loot
    "wishing for a specific drop",
    "commenting on equipment needs",
    "discussing stats or upgrades",
    # Meta and real life
    "random thought or musing",
    "commenting on real life briefly",
    "mentioning being tired or hungry",
    "talking about time played today",
    "referencing something outside the game",
    # Advice
    "advice or tip for others",
    "warning about danger ahead",
    "sharing useful information",
    "recommending a strategy",
    # Roleplay-adjacent
    "speaking partially in character",
    "commenting on lore or story",
    "reacting to NPC dialogue",
    # Atmospheric
    "appreciating the beauty of the landscape",
    "commenting on the lighting or sky",
    "noting the sounds of the environment",
    "feeling the mood of the place",
    "describing the weather's effect on the scene",
    "immersed in the environment",
    "pausing to take in the view",
    "feeling small in a vast world",
    # Mystical and wonder
    "sensing something magical nearby",
    "wondering about ancient mysteries",
    "feeling the presence of old magic",
    "marveling at the world's secrets",
    "pondering the unknown",
    "touched by something ethereal",
    "questioning what lies beyond",
    "feeling connected to something greater",
    # Nostalgic
    "remembering earlier adventures",
    "missing how things used to be",
    "reminiscing about old friends or guilds",
    "feeling nostalgic about a place",
    "recalling a memorable moment",
    "thinking about the journey so far",
    "appreciating how far they've come",
    "bittersweet reflection on the past",
    "wishing to relive a memory",
    # Contemplative
    "philosophical moment about the game world",
    "quiet reflection",
    "finding peace in the moment",
    "appreciating the simple things",
    "moment of gratitude",
    "feeling content",
    # Misc
    "sharing a random fact",
    "expressing boredom",
    "thinking out loud about next steps",
    "making a prediction",
    "expressing confusion",
    "stating the obvious humorously",
    "non-sequitur or random tangent",
]


# Length hints
LENGTH_HINTS = [
    "very brief (3-6 words)",
    "short (6-12 words)",
    "short sentence (<=14 words)",
    "medium if needed (15-22 words)",
]

# Length mode probabilities (percent)

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


def maybe_get_creative_twist(chance: float = 0.3) -> str:
    """Maybe return a creative twist to add unpredictability (30% chance by default)."""
    if random.random() < chance:
        return random.choice(CREATIVE_TWISTS)
    return None


def generate_conversation_mood_sequence(message_count: int) -> List[str]:
    """Generate a mood sequence for a conversation - each message gets a mood."""
    return [random.choice(MOODS) for _ in range(message_count)]


def get_time_of_day_context() -> Tuple[str, str]:
    """Get current time-of-day context for immersive conversations.

    Returns:
        Tuple of (time_period, description) for use in prompts
    """
    # Use current hour - this gives natural variation
    # In WoW, time passes faster, but for chatter purposes, real time works well
    hour = datetime.now().hour

    if 5 <= hour < 7:
        return ("dawn", "The early morning light is just appearing")
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
        return ("late_night", "It's the deep hours of night")


def build_dynamic_guidelines(include_humor: bool = None,
                             include_length: bool = True,
                             include_focus: bool = None,
                             config: dict = None) -> list:
    """Build a randomized list of guidelines."""
    guidelines = [
        "Sound like a real player, not an NPC",
        "NEVER use brackets [] around quest names, item names, zone names, or faction names - write them as plain text. Only use brackets for NPC names like [Onu]. Only use {quest:Name} or {item:Name} placeholders when explicitly told to."
    ]

    # Length hint (usually include)
    if include_length:
        guidelines.append(f"Length: {random.choice(LENGTH_HINTS)}")
        # Deterministic length mode: mostly short/medium, occasional long
        long_chance = 12
        if config is not None:
            try:
                long_chance = int(config.get('LLMChatter.LongMessageChance', long_chance))
            except Exception:
                pass
        if random.randint(1, 100) <= long_chance:
            guidelines.append("Length mode: long allowed (up to ~200 chars) if it feels natural")
            guidelines.append("If long, make it a single thought, not a paragraph")
        else:
            guidelines.append("Length mode: short/medium only (avoid long messages)")

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
def build_plain_statement_prompt(bot: dict, zone_id: int = 0, zone_mobs: list = None, config: dict = None, current_weather: str = 'clear') -> str:
    """Build a dynamically varied prompt for a plain text statement."""
    parts = []

    # Core context (always include zone)
    parts.append(f"Generate a brief WoW General chat message from a player in {bot['zone']}.")

    # Zone flavor - rich context about the zone's atmosphere and feel
    zone_flavor = get_zone_flavor(zone_id)
    if zone_flavor:
        parts.append(f"Zone context: {zone_flavor}")

    # Current weather conditions - always include so LLM can naturally reference any weather
    if current_weather:
        parts.append(f"Current weather: {current_weather}")

    # Randomly include level (60% chance)
    if random.random() < 0.6:
        parts.append(f"Player level: {bot['level']}")

    # Zone creature context - tells the LLM what actually exists in this zone
    if zone_mobs:
        parts.append(f"Creatures here: {', '.join(zone_mobs)}")
        parts.append("IMPORTANT: If mentioning any creature, ONLY use ones from the list above. Include the [[npc:...]] marker exactly as shown.")

    # Random tone and mood - these shape the personality
    tone = pick_random_tone()
    mood = pick_random_mood()
    parts.append(f"Tone: {tone}")
    parts.append(f"Mood: {mood}")

    # Maybe add a creative twist for unpredictability
    twist = maybe_get_creative_twist()
    if twist:
        parts.append(f"Creative twist: {twist}")

    # Pick a random message category (forces original content, no examples to copy)
    category = random.choice(MESSAGE_CATEGORIES)

    # Log the creative selections
    twist_log = f", twist={twist}" if twist else ""
    logger.info(f"Prompt creativity: tone={tone}, mood={mood}, category={category[:30]}{twist_log}")
    parts.append(f"Message type: {category}")

    # Build dynamic guidelines
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Plain text only, except [[npc:...]] markers for creature names")
    guidelines.append("Do NOT mention your race or class")
    # Message length - mostly short, occasionally longer
    if random.random() < 0.75:
        guidelines.append("Keep SHORT - under 60 characters, punchy and brief")
    else:
        guidelines.append("Can be longer this time - up to 100 characters for a fuller thought")
    guidelines.append("Be ORIGINAL and UNPREDICTABLE - no common patterns, surprise the reader")
    if zone_mobs:
        guidelines.append("Only mention creatures from the provided list - do NOT invent creatures")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append("Respond with ONLY the message, nothing else.")

    return "\n".join(parts)


def build_quest_statement_prompt(bot: dict, quest: dict, config: dict = None) -> str:
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

    # Maybe add a creative twist
    twist = maybe_get_creative_twist()
    if twist:
        parts.append(f"Creative twist: {twist}")

    # Quest-specific approaches
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
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Keep under 110 characters")
    guidelines.append("Be creative and unpredictable")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append("Respond with ONLY the message - be creative and unpredictable.")

    return "\n".join(parts)


def build_loot_statement_prompt(bot: dict, item: dict, can_use: bool, config: dict = None) -> str:
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

    # Maybe add a creative twist
    twist = maybe_get_creative_twist()
    if twist:
        parts.append(f"Creative twist: {twist}")

    # Loot-specific reactions to vary
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

    # Guidelines
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Keep under 110 characters")
    guidelines.append("Be creative and unpredictable")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append("Respond with ONLY the message - be creative and unpredictable.")

    return "\n".join(parts)




def build_quest_reward_statement_prompt(bot: dict, quest: dict, config: dict = None) -> str:
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

    # Maybe add a creative twist
    twist = maybe_get_creative_twist()
    if twist:
        parts.append(f"Creative twist: {twist}")

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
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Use BOTH placeholders, each once")
    guidelines.append("Keep under 110 characters")
    parts.append("Guidelines: " + "; ".join(guidelines))

    parts.append("Respond with ONLY the message.")

    return "\n".join(parts)


def build_plain_conversation_prompt(bots: List[dict], zone_id: int = 0, zone_mobs: list = None, config: dict = None, current_weather: str = 'clear') -> str:
    """Build a dynamically varied prompt for a plain conversation with 2-4 bots.

    Args:
        bots: List of 2-4 bot dicts with name, race, class, level, zone
        zone_id: Zone ID for flavor text lookup
        zone_mobs: Optional list of mob markers from the zone
        current_weather: Current weather state in the zone
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

    # Current weather conditions - always include so LLM can naturally reference any weather
    if current_weather:
        parts.append(f"Current weather: {current_weather}")

    # Time of day context - adds natural atmosphere variation
    time_period, time_desc = get_time_of_day_context()
    parts.append(f"Time of day: {time_desc}. Feel free to naturally reference the time in conversation if it fits.")

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
    tone = pick_random_tone()
    parts.append(f"Overall tone: {tone}")

    # Maybe add a creative twist for the whole conversation
    twist = maybe_get_creative_twist(chance=0.4)
    if twist:
        parts.append(f"Creative twist for this conversation: {twist}")

    # Generate mood sequence - this is the "script" the LLM must follow
    # More messages for more participants
    min_msgs = bot_count
    max_msgs = bot_count + 3
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    # Log the creative selections
    twist_log = f", twist={twist}" if twist else ""
    logger.info(f"Conversation creativity: tone={tone}, moods={mood_sequence}{twist_log}")

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
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Plain text only, except [[npc:...]] markers for creature names")
    guidelines.append("Follow the mood sequence above")
    guidelines.append("VARY message lengths naturally like real players - some very short ('lol', 'yeah'), some medium, some longer")
    if zone_mobs:
        guidelines.append("Only mention creatures from the provided list - do NOT invent creatures")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction with examples for all speakers
    parts.append("JSON rules: Use double quotes, escape quotes/newlines, no trailing commas, no code fences.")
    example_msgs = ',\n  '.join([f'{{"speaker": "{name}", "message": "..."}}' for name in bot_names])
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_quest_conversation_prompt(bots: List[dict], quest: dict, config: dict = None) -> str:
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

    # Time of day context
    time_period, time_desc = get_time_of_day_context()
    parts.append(f"Time of day: {time_desc}")

    # Quest info
    parts.append(f"Quest: {quest['quest_name']} (use {{{{quest:{quest['quest_name']}}}}} placeholder)")
    if quest.get('description') and random.random() < 0.4:
        parts.append(f"Quest involves: {quest['description'][:60]}")

    # Random tone for the overall conversation
    tone = pick_random_tone()
    parts.append(f"Overall tone: {tone}")

    # Maybe add a creative twist for the whole conversation
    twist = maybe_get_creative_twist(chance=0.4)
    if twist:
        parts.append(f"Creative twist for this conversation: {twist}")

    # Generate mood sequence - the "script" for the conversation
    min_msgs = bot_count
    max_msgs = bot_count + 3
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    # Log the creative selections
    twist_log = f", twist={twist}" if twist else ""
    logger.info(f"Quest conv creativity: tone={tone}, moods={mood_sequence}{twist_log}")

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
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Use quest placeholder at least once")
    guidelines.append("Follow the mood sequence above")
    guidelines.append("Keep each message under 140 characters; short/medium is the norm")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction with examples for all speakers
    parts.append("JSON rules: Use double quotes, escape quotes/newlines, no trailing commas, no code fences.")
    example_msgs = ',\n  '.join([f'{{"speaker": "{name}", "message": "..."}}' for name in bot_names])
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_loot_conversation_prompt(bots: List[dict], item: dict, config: dict = None) -> str:
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

    # Time of day context
    time_period, time_desc = get_time_of_day_context()
    parts.append(f"Time of day: {time_desc}")

    # Item info
    parts.append(f"Item: {item['item_name']} ({quality} quality)")
    parts.append(f"REQUIRED: Use {item_placeholder} placeholder when mentioning the item")

    # Random tone for the overall conversation
    tone = pick_random_tone()
    parts.append(f"Overall tone: {tone}")

    # Maybe add a creative twist for the whole conversation
    twist = maybe_get_creative_twist(chance=0.4)
    if twist:
        parts.append(f"Creative twist for this conversation: {twist}")

    # Generate mood sequence
    min_msgs = bot_count
    max_msgs = bot_count + 2
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    # Log the creative selections
    twist_log = f", twist={twist}" if twist else ""
    logger.info(f"Loot conv creativity: tone={tone}, moods={mood_sequence}{twist_log}")

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
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Use item placeholder at least once")
    guidelines.append("Follow the mood sequence above")
    guidelines.append("Keep each message under 140 characters; short/medium is the norm")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction with examples for all speakers
    parts.append("JSON rules: Use double quotes, escape quotes/newlines, no trailing commas, no code fences.")
    example_msgs = ',\n  '.join([f'{{"speaker": "{name}", "message": "..."}}' for name in bot_names])
    parts.append(f"""
Respond with EXACTLY {msg_count} messages in JSON:
[
  {example_msgs}
]
ONLY the JSON array, nothing else.""")

    return "\n".join(parts)


def build_event_conversation_prompt(bots: List[dict], event_context: str, zone_id: int = 0, config: dict = None) -> str:
    """Build a prompt for an event-triggered conversation with 2-4 bots.

    Args:
        bots: List of 2-4 bot dicts with name, race, class, level, zone
        event_context: Description of the event (weather change, etc.)
        zone_id: Zone ID for additional context
    """
    parts = []
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    parts.append(f"Generate a casual General chat exchange between {bot_count} WoW players in {bots[0]['zone']}.")
    parts.append(f"Speakers: {', '.join(bot_names)}")
    parts.append(f"Names: Sometimes use their name when addressing directly (maybe once), but not every message.")

    # Event context - the trigger for this conversation
    parts.append(f"\nEVENT CONTEXT: {event_context}")

    # Transport events should be mentioned more directly
    if 'boat' in event_context.lower() or 'zeppelin' in event_context.lower() or 'turtle' in event_context.lower():
        parts.append("This transport just arrived - at least one bot should comment on it!")
        parts.append("Use the specific transport type (boat/zeppelin/turtle), NOT the generic word 'transport'.")
        parts.append("IMPORTANT: Always mention the destination from the event context above.")
        parts.append("If a ship name is mentioned (e.g., 'The Moonspray'), you can optionally include it.")
    else:
        parts.append("The conversation may naturally reference this event, or players may chat about something else.")
        parts.append("The event provides atmosphere - you don't HAVE to mention it explicitly.")

    # Zone flavor
    zone_flavor = get_zone_flavor(zone_id)
    if zone_flavor:
        parts.append(f"Zone context: {zone_flavor}")

    # Randomly include some character details (40% chance per bot)
    for bot in bots:
        if random.random() < 0.4:
            parts.append(f"{bot['name']} is a {bot['race']} {bot['class']}")

    # Random tone for the overall conversation
    tone = pick_random_tone()
    parts.append(f"Overall tone: {tone}")

    # Maybe add a creative twist for the whole conversation
    twist = maybe_get_creative_twist(chance=0.4)
    if twist:
        parts.append(f"Creative twist for this conversation: {twist}")

    # Generate mood sequence
    min_msgs = bot_count
    max_msgs = bot_count + 2
    msg_count = random.randint(min_msgs, max_msgs)
    mood_sequence = generate_conversation_mood_sequence(msg_count)

    # Log the creative selections
    twist_log = f", twist={twist}" if twist else ""
    logger.info(f"Event conv creativity: tone={tone}, moods={mood_sequence}{twist_log}")

    parts.append(f"\nMOOD SEQUENCE (follow this for each message):")
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % bot_count]
        parts.append(f"  Message {i+1} ({speaker}): {mood}")

    # Guidelines
    guidelines = build_dynamic_guidelines(config=config)
    guidelines.append("Follow the mood sequence above")
    guidelines.append("VARY message lengths naturally - some very short ('lol', 'yeah'), some medium, occasionally longer")
    parts.append("Guidelines: " + "; ".join(guidelines))

    # JSON format instruction
    parts.append("JSON rules: Use double quotes, escape quotes/newlines, no trailing commas, no code fences.")
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


def call_llm(client: Any, prompt: str, config: dict, max_tokens_override: int = None) -> str:
    """Call LLM API (Anthropic or OpenAI) and return response."""
    provider = config.get('LLMChatter.Provider', 'anthropic').lower()
    model_alias = config.get('LLMChatter.Model', 'haiku')
    model = resolve_model(model_alias)
    if max_tokens_override is not None:
        max_tokens = max_tokens_override
    else:
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
        cleaned = response.strip()
        cleaned = re.sub(r'```(?:json)?', '', cleaned, flags=re.IGNORECASE).strip()
        json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if json_match:
            try:
                messages = json.loads(json_match.group())
            except json.JSONDecodeError:
                # Fallback: try widest bracket span in case of extra text
                start = cleaned.find('[')
                end = cleaned.rfind(']')
                if start != -1 and end != -1 and end > start:
                    messages = json.loads(cleaned[start:end + 1])
                else:
                    raise
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
        snippet = response.strip().replace("\n", "\\n")
        logger.error(f"Failed to parse conversation JSON: {e}; len={len(response)}; head={snippet[:200]}")
    return []


def extract_conversation_msg_count(prompt: str) -> int:
    """Extract expected message count from a prompt if present."""
    match = re.search(r'EXACTLY (\d+) messages', prompt)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return 0
    return 0


# =============================================================================
# REQUEST PROCESSING
# =============================================================================
def process_statement(db, cursor, client, config, request, bot: dict):
    """Process a single statement request."""
    channel = 'general'

    # Select message type
    zone_id = request.get('zone_id', 0)
    current_weather = request.get('weather', 'clear')  # Get current weather from C++
    msg_type = select_message_type()
    logger.info(f"Statement type: {msg_type}")

    # Get zone data if needed
    quest_data = None
    item_data = None

    if msg_type == "quest" or msg_type == "quest_reward":
        quests = query_zone_quests(config, zone_id, bot['level'])
        if quests:
            quest_data = random.choice(quests)
            logger.info(f"Selected quest: {quest_data['quest_name']}")
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "loot":
        loot = query_zone_loot(config, zone_id, bot['level'])
        if loot:
            cooldown = int(config.get('LLMChatter.LootRecentCooldownSeconds', 0))
            if cooldown > 0:
                recent_ids = zone_cache.get_recent_loot_ids(zone_id, cooldown)
                filtered = [item for item in loot if item.get('item_id') not in recent_ids]
                if filtered:
                    loot = filtered
            # Weight selection by quality - epics should be rare
            # Quality: 0=gray, 1=white, 2=green, 3=blue, 4=epic
            quality_weights = {0: 35, 1: 30, 2: 22, 3: 10, 4: 3}  # Blue 10%, Epic 3%
            weights = [quality_weights.get(item.get('item_quality', 2), 10) for item in loot]
            item_data = random.choices(loot, weights=weights, k=1)[0]
            if cooldown > 0 and item_data.get('item_id'):
                zone_cache.mark_loot_seen(zone_id, item_data['item_id'])
            # Check if bot's class can use the item
            item_can_use = can_class_use_item(bot['class'], item_data.get('allowable_class', -1))
            quality_names = {0: "gray", 1: "white", 2: "green", 3: "blue", 4: "epic"}
            logger.info(f"Selected loot: {item_data['item_name']} ({quality_names.get(item_data.get('item_quality', 2), 'unknown')}) - {bot['class']} can use: {item_can_use}")
        else:
            msg_type = "plain"  # Fallback

    # Build appropriate prompt
    if msg_type == "plain":
        # Get zone mobs for context - pass up to 10 random mobs so LLM knows what exists
        zone_mobs = []
        mobs = query_zone_mobs(config, zone_id, bot['level'])
        if mobs:
            zone_mobs = random.sample(mobs, min(10, len(mobs)))
        # Log zone context being used
        zone_flavor = get_zone_flavor(zone_id)
        logger.info(f"Zone context: id={zone_id}, flavor={'yes' if zone_flavor else 'no'}, mobs={len(zone_mobs)}, weather={current_weather}")
        prompt = build_plain_statement_prompt(bot, zone_id, zone_mobs, config, current_weather)
    elif msg_type == "quest":
        prompt = build_quest_statement_prompt(bot, quest_data, config)
    elif msg_type == "loot":
        prompt = build_loot_statement_prompt(bot, item_data, item_can_use, config)
    elif msg_type == "quest_reward":
        prompt = build_quest_reward_statement_prompt(bot, quest_data, config)
        # Also set item_data for replacement
        if quest_data and quest_data.get('item1_name'):
            item_data = {
                'item_id': quest_data['item1_id'],
                'item_name': quest_data['item1_name'],
                'item_quality': quest_data.get('item1_quality', 2)
            }
    else:
        prompt = build_plain_statement_prompt(bot, zone_id, config=config, current_weather=current_weather)

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

    zone_id = request.get('zone_id', 0)
    current_weather = request.get('weather', 'clear')  # Get current weather from C++

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
            cooldown = int(config.get('LLMChatter.LootRecentCooldownSeconds', 0))
            if cooldown > 0:
                recent_ids = zone_cache.get_recent_loot_ids(zone_id, cooldown)
                filtered = [item for item in loot if item.get('item_id') not in recent_ids]
                if filtered:
                    loot = filtered
            quality_weights = {0: 30, 1: 30, 2: 25, 3: 12, 4: 3}
            weights = [quality_weights.get(item.get('item_quality', 2), 10) for item in loot]
            item_data = random.choices(loot, weights=weights, k=1)[0]
            if cooldown > 0 and item_data.get('item_id'):
                zone_cache.mark_loot_seen(zone_id, item_data['item_id'])
            logger.info(f"Selected loot for conversation: {item_data['item_name']}")
        else:
            msg_type = "plain"

    # Build prompt
    if msg_type == "plain":
        # Get zone mobs for context - pass up to 10 random mobs so LLM knows what exists
        zone_mobs = []
        mobs = query_zone_mobs(config, zone_id, bots[0]['level'])
        if mobs:
            zone_mobs = random.sample(mobs, min(10, len(mobs)))
        # Log zone context being used
        zone_flavor = get_zone_flavor(zone_id)
        logger.info(f"Zone context: id={zone_id}, flavor={'yes' if zone_flavor else 'no'}, mobs={len(zone_mobs)}, weather={current_weather}")
        prompt = build_plain_conversation_prompt(bots, zone_id, zone_mobs, config, current_weather)
    elif msg_type == "quest":
        prompt = build_quest_conversation_prompt(bots, quest_data, config)
    else:  # loot
        prompt = build_loot_conversation_prompt(bots, item_data, config)

    # Call LLM
    conversation_max_tokens = int(
        config.get(
            'LLMChatter.ConversationMaxTokens',
            config.get('LLMChatter.MaxTokens', 200)
        )
    )
    response = call_llm(client, prompt, config, max_tokens_override=conversation_max_tokens)

    if response:
        messages = parse_conversation_response(response, bot_names)

        if not messages:
            msg_count = extract_conversation_msg_count(prompt)
            repair_prompt = (
                "Your previous output was invalid JSON. Output ONLY a JSON array of "
                f"{msg_count if msg_count else 'the required number of'} messages with the "
                f"speakers: {', '.join(bot_names)}. Use double quotes, escape quotes/newlines, "
                "no trailing commas, no code fences."
            )
            response = call_llm(client, repair_prompt, config, max_tokens_override=conversation_max_tokens)
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

        # Mark as completed only if processing succeeded
        if success:
            cursor.execute(
                "UPDATE llm_chatter_queue SET status = 'completed', processed_at = NOW() WHERE id = %s",
                (request_id,)
            )
            db.commit()
            return True
        else:
            logger.warning(f"Request #{request_id} processing returned failure, marking as failed")
            cursor.execute(
                "UPDATE llm_chatter_queue SET status = 'failed' WHERE id = %s",
                (request_id,)
            )
            db.commit()
            return False

    except Exception as e:
        logger.error(f"Error processing request #{request_id}: {e}")
        cursor.execute(
            "UPDATE llm_chatter_queue SET status = 'failed' WHERE id = %s",
            (request_id,)
        )
        db.commit()
        return False


# =============================================================================
# EVENT PROCESSING
# =============================================================================

# Event type to human-readable description
EVENT_DESCRIPTIONS = {
    'weather_change': 'weather changing',
    'holiday_start': 'a holiday beginning',
    'holiday_end': 'a holiday ending',
    'creature_death_boss': 'a boss being defeated',
    'creature_death_rare': 'a rare creature being killed',
    'creature_death_guard': 'a city guard being killed',
    'player_enters_zone': 'a player entering the area',
    'bot_pvp_kill': 'a PvP fight happening',
    'bot_level_up': 'gaining a level',
    'bot_achievement': 'earning an achievement',
    'bot_quest_complete': 'completing a quest',
    'world_boss_spawn': 'a world boss appearing',
    'rare_spawn': 'a rare creature appearing',
    'transport_arrives': 'a boat or zeppelin arriving',
    'day_night_transition': 'the time of day changing',
    'enemy_player_near': 'enemy players nearby',
    'bot_loot_item': 'finding valuable loot',
}


def repair_json_string(raw_json: str) -> str:
    """
    Attempt to repair common JSON escaping issues from C++ side.

    Common issues:
    - Unescaped quotes inside string values: ("The Moonspray") should be (\"The Moonspray\")
    - Nested quotes without proper escaping
    """
    if not raw_json:
        return raw_json

    # Try to fix unescaped quotes inside parentheses like ("name")
    # Pattern: find ("...") where the quotes aren't escaped
    import re

    # First, try direct parse - maybe it's already valid
    try:
        json.loads(raw_json)
        return raw_json  # Already valid
    except:
        pass

    # Strategy: Find quoted strings in JSON and check for unescaped inner quotes
    # This is tricky because we need to find the JSON string boundaries first

    # Simple approach: find patterns like ("word") or ("word word") and escape them
    # Pattern matches: opening paren + quote + content + quote + closing paren
    def escape_inner_quotes(match):
        full = match.group(0)
        # Replace the inner quotes with escaped quotes
        # ("The Moonspray") -> (\"The Moonspray\")
        inner = match.group(1)
        return '(\\"' + inner + '\\")'

    # Match: ( followed by " followed by non-quote content followed by " followed by )
    # The non-quote content shouldn't contain unescaped quotes
    repaired = re.sub(r'\("([^"\\]+)"\)', escape_inner_quotes, raw_json)

    # Also handle cases with escaped content already
    # Try parsing the repaired version
    try:
        json.loads(repaired)
        return repaired
    except:
        pass

    # More aggressive repair: try to identify string values and escape inner quotes
    # This is a simplified approach - extract known fields and rebuild
    try:
        # Extract key-value pairs using regex
        # Pattern for "key":"value" pairs
        result = {}

        # Find transport_entry (numeric)
        entry_match = re.search(r'"transport_entry":(\d+)', raw_json)
        if entry_match:
            result['transport_entry'] = int(entry_match.group(1))

        # Find transport_type - it's usually simple like "Boat"
        type_match = re.search(r'"transport_type":"([^"]+)"', raw_json)
        if type_match:
            result['transport_type'] = type_match.group(1)

        # Find destination - usually after transport_type or before it
        dest_match = re.search(r'"destination":"([^"]+)"', raw_json)
        if dest_match:
            result['destination'] = dest_match.group(1)

        # transport_name is the problematic one - extract everything between
        # "transport_name":" and the next "," before "destination" or "transport_type"
        name_match = re.search(r'"transport_name":"(.+?)","(?:destination|transport_type)"', raw_json)
        if name_match:
            result['transport_name'] = name_match.group(1)

        if result:
            # Rebuild as proper JSON
            return json.dumps(result)
    except:
        pass

    # Return original if all repairs failed
    return raw_json


def parse_extra_data(raw_data: str, event_id=None, event_type=None) -> dict:
    """Parse extra_data JSON with repair attempts for malformed data."""
    if not raw_data:
        return {}

    # First try: direct parse
    try:
        return json.loads(raw_data)
    except json.JSONDecodeError:
        pass

    # Second try: repair and parse
    repaired = repair_json_string(raw_data)
    try:
        result = json.loads(repaired)
        if repaired != raw_data:
            logger.debug(f"Repaired JSON for event {event_id}: {raw_data[:100]}...")
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse extra_data JSON for event {event_id} "
                      f"(type={event_type}): {e}")
        logger.debug(f"Raw extra_data: {raw_data}")
    except Exception as e:
        logger.warning(f"Unexpected error parsing extra_data for event {event_id}: {e}")

    return {}


def build_event_context(event: dict) -> str:
    """Build context string for an event."""
    event_type = event['event_type']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event.get('id'),
        event_type
    )

    context_parts = []

    if event_type == 'holiday_start':
        name = extra_data.get('event_name', 'a holiday')
        context_parts.append(f"The {name} festival has just begun!")

    elif event_type == 'holiday_end':
        name = extra_data.get('event_name', 'a holiday')
        context_parts.append(f"The {name} festival is coming to an end.")

    elif event_type == 'world_boss_spawn':
        target = event.get('target_name', 'A world boss')
        context_parts.append(f"{target} has been spotted in the world!")

    elif event_type == 'rare_spawn':
        target = event.get('target_name', 'A rare creature')
        context_parts.append(f"A rare creature ({target}) has appeared nearby.")

    elif event_type == 'creature_death_boss':
        target = event.get('target_name', 'A boss')
        killer = extra_data.get('killer_name', 'someone')
        context_parts.append(f"{target} has been defeated by {killer}!")

    elif event_type == 'creature_death_rare':
        target = event.get('target_name', 'A rare')
        context_parts.append(f"A rare creature ({target}) was just killed.")

    elif event_type == 'bot_level_up':
        subject = event.get('subject_name', 'Someone')
        new_level = extra_data.get('new_level', '?')
        is_milestone = extra_data.get('is_milestone', False)
        if is_milestone:
            context_parts.append(f"{subject} has reached level {new_level}!")
        else:
            context_parts.append(f"{subject} leveled up to {new_level}.")

    elif event_type == 'bot_quest_complete':
        subject = event.get('subject_name', 'Someone')
        quest_name = extra_data.get('quest_name', 'a quest')
        context_parts.append(f"{subject} just completed the quest '{quest_name}'.")

    elif event_type == 'bot_achievement':
        subject = event.get('subject_name', 'Someone')
        achi_name = extra_data.get('achievement_name', 'an achievement')
        context_parts.append(f"{subject} earned the achievement '{achi_name}'!")

    elif event_type == 'bot_pvp_kill':
        subject = event.get('subject_name', 'Someone')
        target = event.get('target_name', 'an enemy')
        context_parts.append(f"{subject} defeated {target} in PvP combat!")

    elif event_type == 'bot_loot_item':
        subject = event.get('subject_name', 'Someone')
        item_name = extra_data.get('item_name', 'something valuable')
        quality = extra_data.get('quality', 0)
        quality_name = ['poor', 'common', 'uncommon', 'rare', 'epic', 'legendary'][min(quality, 5)]
        context_parts.append(f"{subject} found a {quality_name} item: {item_name}!")

    elif event_type == 'day_night_transition':
        time_period = extra_data.get('time_period', 'day')
        previous_period = extra_data.get('previous_period', '')
        hour = extra_data.get('hour', 12)
        description = extra_data.get('description', '')

        # Time period descriptions for context
        period_contexts = {
            'dawn': "The first light of dawn breaks over the horizon. The sky turns pink and gold.",
            'early_morning': "It's early morning. The world is waking up, dew still on the grass.",
            'morning': "The morning sun climbs higher. It's a good time for adventures.",
            'midday': "The sun reaches its peak. Shadows are short and the day is warm.",
            'afternoon': "The afternoon sun casts long shadows. The day is well underway.",
            'evening': "Evening approaches. The light turns golden as the sun descends.",
            'dusk': "Dusk settles over the land. The sky blazes with sunset colors.",
            'night': "Night has fallen. Stars begin to appear in the darkening sky.",
            'midnight': "It's the middle of the night. The world is quiet under the stars.",
            'late_night': "The deep hours of night. Few are awake at this hour.",
        }

        desc = period_contexts.get(time_period, description or "The time of day is changing.")
        context_parts.append(desc)

        # Add time info for additional context
        if hour is not None:
            context_parts.append(f"(In-game time: {hour:02d}:00)")

    elif event_type == 'weather_change':
        weather_type = extra_data.get('weather_type', 'unusual weather')
        previous_weather = extra_data.get('previous_weather', 'clear')
        transition = extra_data.get('transition', 'changing')
        intensity = extra_data.get('intensity', 'moderate')
        category = extra_data.get('category', 'weather')

        # Weather starting descriptions
        starting_descriptions = {
            'light rain': "A light drizzle has begun to fall.",
            'rain': "Rain clouds have rolled in and it's starting to rain.",
            'heavy rain': "Dark clouds have gathered and heavy rain is pouring down!",
            'light snow': "A few snowflakes are beginning to drift down from the sky.",
            'snow': "It's starting to snow, white flakes covering the ground.",
            'heavy snow': "A blizzard is setting in with heavy snowfall!",
            'foggy': "A thick fog is rolling in, reducing visibility.",
            'light sandstorm': "The wind is picking up, kicking sand into the air.",
            'sandstorm': "A sandstorm is sweeping through the area!",
            'heavy sandstorm': "A massive sandstorm has engulfed everything!",
            'thunderstorm': "Storm clouds are gathering, thunder rumbles in the distance!",
            'black rain': "Strange dark clouds have formed... black rain is falling!",
            'black snow': "Something ominous... black snow is drifting down from above.",
        }

        # Weather clearing descriptions
        clearing_descriptions = {
            'rain': "The rain is stopping. Clouds are parting.",
            'snow': "The snowfall is easing. The sky is clearing.",
            'sandstorm': "The sandstorm is dying down. Visibility is returning.",
            'fog': "The fog is lifting, revealing the landscape.",
            'storm': "The storm is passing. The thunder fades away.",
            'weather': "The weather is clearing up.",
        }

        # Weather intensifying descriptions
        intensifying_descriptions = {
            'rain': f"The rain is getting heavier - now {weather_type}.",
            'snow': f"The snow is intensifying - now {weather_type}.",
            'sandstorm': f"The sandstorm grows stronger - now {weather_type}.",
            'storm': "The storm is intensifying!",
            'weather': f"The {category} is getting worse.",
        }

        if transition == 'starting':
            desc = starting_descriptions.get(weather_type,
                f"The weather is changing to {weather_type}.")
        elif transition == 'clearing':
            desc = clearing_descriptions.get(category,
                "The weather is clearing up. The sky brightens.")
        elif transition == 'intensifying':
            desc = intensifying_descriptions.get(category,
                f"The {weather_type} is getting more intense.")
        else:  # changing (different weather type)
            desc = f"The weather is shifting from {previous_weather} to {weather_type}."

        context_parts.append(desc)

    elif event_type == 'transport_arrives':
        transport_type = extra_data.get('transport_type', '')
        destination = extra_data.get('destination', '')
        transport_name = extra_data.get('transport_name', '')

        # Extract the ship's actual name (e.g., "The Moonspray") from transport_name
        # Format: 'Auberdine, Darkshore and Rut'theran Village, Teldrassil (Boat, Alliance ("The Moonspray"))'
        ship_name = ''
        if transport_name:
            import re
            # Look for quoted name like ("The Moonspray") or ("Orgrim's Hammer")
            name_match = re.search(r'\("([^"]+)"\)', transport_name)
            if name_match:
                ship_name = name_match.group(1)

        # Fallback: parse target_name if extra_data failed
        # Format: "Auberdine, Darkshore and Rut'theran Village, Teldrassil (Boat, Alliance)"
        target_name = event.get('target_name', '')
        if not destination and target_name:
            # Try to extract destination from "X and Y (Type)" format
            if ' and ' in target_name:
                parts = target_name.split(' and ')
                if len(parts) >= 2:
                    # Second part before parenthesis is destination
                    dest_part = parts[1].split('(')[0].strip()
                    destination = dest_part
            # Try to extract transport type
            if not transport_type and '(' in target_name:
                type_part = target_name.split('(')[-1].rstrip(')')
                if 'Boat' in type_part:
                    transport_type = 'Boat'
                elif 'Zeppelin' in type_part:
                    transport_type = 'Zeppelin'
                elif 'Turtle' in type_part:
                    transport_type = 'Turtle'

        # Extract origin from transport_name (first part before ' and ')
        origin = ''
        if transport_name and ' and ' in transport_name:
            origin = transport_name.split(' and ')[0].strip()

        # Final defaults
        if not transport_type:
            transport_type = 'transport'
        if not destination:
            destination = 'its next stop'

        # Build description based on transport type with ship name
        ship_info = f' "{ship_name}"' if ship_name else ''
        route_info = f' (route: {origin} to {destination})' if origin else f' heading to {destination}'

        if transport_type.lower() == 'zeppelin':
            desc = f"A zeppelin{ship_info} has just arrived!{route_info}"
        elif transport_type.lower() == 'boat':
            desc = f"A boat{ship_info} has just docked at the pier!{route_info}"
        elif transport_type.lower() == 'turtle':
            desc = f"A giant sea turtle transport{ship_info} has arrived!{route_info}"
        else:
            desc = f"A {transport_type}{ship_info} has arrived,{route_info}"

        context_parts.append(desc)
        context_parts.append(f"IMPORTANT: Bots should mention the destination '{destination}' and optionally the ship name '{ship_name}' in their conversation.")

    elif event_type == 'player_enters_zone':
        subject = event.get('subject_name', 'A player')
        level = extra_data.get('level', '?')
        context_parts.append(f"A level {level} player ({subject}) entered the area.")

    else:
        desc = EVENT_DESCRIPTIONS.get(event_type, 'something happened')
        context_parts.append(f"Something notable happened: {desc}.")

    return ' '.join(context_parts)


def cleanup_expired_events(db) -> int:
    """Mark expired events and clean up old completed events."""
    cursor = db.cursor()

    # Mark pending events that have expired
    cursor.execute("""
        UPDATE llm_chatter_events
        SET status = 'expired'
        WHERE status = 'pending'
          AND expires_at IS NOT NULL
          AND expires_at < NOW()
    """)
    expired_count = cursor.rowcount

    # Delete old completed/expired/skipped events (older than 24 hours)
    cursor.execute("""
        DELETE FROM llm_chatter_events
        WHERE status IN ('completed', 'expired', 'skipped')
          AND created_at < DATE_SUB(NOW(), INTERVAL 24 HOUR)
    """)
    deleted_count = cursor.rowcount

    db.commit()

    if expired_count > 0 or deleted_count > 0:
        logger.debug(f"Event cleanup: {expired_count} expired, {deleted_count} deleted")

    return expired_count + deleted_count


def reset_stuck_processing_events(db) -> int:
    """Reset events stuck in 'processing' status back to 'pending'.

    Called on bridge startup - if any events are stuck in 'processing',
    it means the bridge crashed before completing them. Reset them so
    they can be retried.
    """
    cursor = db.cursor()

    cursor.execute("""
        UPDATE llm_chatter_events
        SET status = 'pending'
        WHERE status = 'processing'
    """)
    reset_count = cursor.rowcount
    db.commit()

    if reset_count > 0:
        logger.info(f"Reset {reset_count} stuck 'processing' events to 'pending'")

    return reset_count


def process_pending_events(db, client, config) -> bool:
    """Process pending events from llm_chatter_events table."""
    cursor = db.cursor(dictionary=True)

    # First, find where real players are located (non-RNDBOT accounts)
    # Then prioritize events in those zones
    cursor.execute("""
        SELECT DISTINCT c.zone as player_zone
        FROM characters c
        JOIN acore_auth.account a ON c.account = a.id
        WHERE c.online = 1
          AND a.username NOT LIKE 'RNDBOT%'
    """)
    player_zones = [row['player_zone'] for row in cursor.fetchall()]

    event = None

    # Prefer transport events in zones where real players are
    if player_zones:
        cursor.execute("""
            SELECT e.*
            FROM llm_chatter_events e
            WHERE e.status = 'pending'
              AND e.event_type = 'transport_arrives'
              AND (e.react_after IS NULL OR e.react_after <= NOW())
              AND (e.expires_at IS NULL OR e.expires_at > NOW())
              AND e.zone_id IN (%s)
              AND EXISTS (
                  SELECT 1 FROM characters c
                  JOIN acore_auth.account a ON c.account = a.id
                  WHERE c.online = 1 AND c.zone = e.zone_id
                    AND a.username LIKE 'RNDBOT%%'
              )
            ORDER BY e.priority ASC, e.created_at ASC
            LIMIT 1
        """ % ','.join(['%s'] * len(player_zones)), tuple(player_zones))
        event = cursor.fetchone()

    if event:
        logger.info(f"Prioritizing transport event #{event['id']} in zone {event.get('zone_id')} (player present)")
    else:
        # Get pending events that are ready, but only if they have bots + real player in-zone
        # Uses account-based detection: RNDBOT% = bot, non-RNDBOT% = real player
        cursor.execute("""
            SELECT e.*
            FROM llm_chatter_events e
            WHERE e.status = 'pending'
              AND (e.react_after IS NULL OR e.react_after <= NOW())
              AND (e.expires_at IS NULL OR e.expires_at > NOW())
              AND (
                  e.zone_id IS NULL
                  OR (
                      EXISTS (
                          SELECT 1 FROM characters c
                          JOIN acore_auth.account a ON c.account = a.id
                          WHERE c.online = 1 AND c.zone = e.zone_id
                            AND a.username LIKE 'RNDBOT%%'
                      )
                      AND EXISTS (
                          SELECT 1 FROM characters rp
                          JOIN acore_auth.account a ON rp.account = a.id
                          WHERE rp.online = 1 AND rp.zone = e.zone_id
                            AND a.username NOT LIKE 'RNDBOT%%'
                      )
                  )
              )
            ORDER BY e.priority ASC, e.created_at ASC
            LIMIT 1
        """)
        event = cursor.fetchone()

    if not event:
        return False

    event_id = event['id']
    event_type = event['event_type']
    zone_id = event.get('zone_id')

    # Transport events have a chance-based filter (not every arrival should trigger chat)
    if event_type == 'transport_arrives':
        transport_chance = int(config.get('LLMChatter.TransportEventChance', 30))
        roll = random.randint(1, 100)
        if roll > transport_chance:
            # Skip this transport event but don't mark it as failed
            cursor.execute(
                "UPDATE llm_chatter_events SET status = 'skipped' WHERE id = %s",
                (event_id,))
            db.commit()
            logger.info(f"Transport event #{event_id} skipped: chance roll {roll} > {transport_chance}%")
            return False

        # Zone-level transport cooldown (prevents multiple boat announcements in same zone)
        if zone_id:
            now = time.time()
            last_transport = _zone_transport_cooldowns.get(zone_id, 0)
            if now - last_transport < ZONE_TRANSPORT_COOLDOWN_SECONDS:
                remaining = int(ZONE_TRANSPORT_COOLDOWN_SECONDS - (now - last_transport))
                cursor.execute(
                    "UPDATE llm_chatter_events SET status = 'skipped' WHERE id = %s",
                    (event_id,))
                db.commit()
                logger.info(f"Transport event #{event_id} skipped: zone {zone_id} on cooldown ({remaining}s remaining)")
                return False
            # Update zone cooldown
            _zone_transport_cooldowns[zone_id] = now

    logger.info(f"Processing event #{event_id}: {event_type}")

    # Mark as processing
    cursor.execute(
        "UPDATE llm_chatter_events SET status = 'processing' WHERE id = %s",
        (event_id,))
    db.commit()

    try:
        # Build event context
        event_context = build_event_context(event)

        # Find bots in the zone (if zone-specific)
        # Uses account-based detection: RNDBOT% accounts = bots
        if zone_id:
            # Get online bots (RNDBOT accounts) currently in this zone
            cursor.execute("""
                SELECT DISTINCT c.guid as bot1_guid, c.name as bot1_name,
                       c.class as bot1_class, c.race as bot1_race, c.level as bot1_level,
                       c.zone as zone_id
                FROM characters c
                JOIN acore_auth.account a ON c.account = a.id
                WHERE c.online = 1 AND c.zone = %s
                  AND a.username LIKE 'RNDBOT%%'
                ORDER BY RAND()
                LIMIT 10
            """, (zone_id,))
            recent_bots = cursor.fetchall()

            if not recent_bots:
                # No bots found, skip event
                cursor.execute(
                    "UPDATE llm_chatter_events SET status = 'skipped' WHERE id = %s",
                    (event_id,))
                db.commit()
                logger.info(f"Event #{event_id} skipped: no bots in zone {zone_id}")
                return False

            # Convert numeric class/race to names for all bots
            for bot in recent_bots:
                if isinstance(bot.get('bot1_class'), int):
                    bot['bot1_class'] = get_class_name(bot['bot1_class'])
                if isinstance(bot.get('bot1_race'), int):
                    bot['bot1_race'] = get_race_name(bot['bot1_race'])
        else:
            # Global event - find any online bot (RNDBOT account)
            cursor.execute("""
                SELECT DISTINCT c.guid as bot1_guid, c.name as bot1_name,
                       c.class as bot1_class, c.race as bot1_race, c.level as bot1_level,
                       c.zone as zone_id
                FROM characters c
                JOIN acore_auth.account a ON c.account = a.id
                WHERE c.online = 1
                  AND a.username LIKE 'RNDBOT%%'
                ORDER BY RAND()
                LIMIT 20
            """)
            recent_bots = cursor.fetchall()

            if not recent_bots:
                cursor.execute(
                    "UPDATE llm_chatter_events SET status = 'skipped' WHERE id = %s",
                    (event_id,))
                db.commit()
                logger.info(f"Event #{event_id} skipped: no online bots found")
                return False

            # Convert numeric class/race to names for all bots
            for bot in recent_bots:
                if isinstance(bot.get('bot1_class'), int):
                    bot['bot1_class'] = get_class_name(bot['bot1_class'])
                if isinstance(bot.get('bot1_race'), int):
                    bot['bot1_race'] = get_race_name(bot['bot1_race'])

        # Check zone fatigue (if zone-specific event)
        # Transport events bypass zone fatigue to ensure they can always fire
        if zone_id and event_type != 'transport_arrives':
            fatigue_threshold = int(config.get('LLMChatter.ZoneFatigueThreshold', 3))
            fatigue_cooldown = int(config.get('LLMChatter.ZoneFatigueCooldownSeconds', 900))
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM llm_chatter_events
                WHERE zone_id = %s AND status = 'completed'
                  AND processed_at > DATE_SUB(NOW(), INTERVAL %s SECOND)
            """, (zone_id, fatigue_cooldown))
            result = cursor.fetchone()
            if result and result['cnt'] >= fatigue_threshold:
                cursor.execute(
                    "UPDATE llm_chatter_events SET status = 'skipped' WHERE id = %s",
                    (event_id,))
                db.commit()
                logger.info(f"Event #{event_id} skipped: zone {zone_id} fatigue threshold ({fatigue_threshold}) reached")
                return False

        # Decide: statement (40%) vs conversation (60%)
        # Conversations require at least 2 bots
        use_conversation = len(recent_bots) >= 2 and random.randint(1, 100) <= 60

        if use_conversation:
            # Select 2-4 bots for conversation
            num_bots = min(random.randint(2, 4), len(recent_bots))
            selected_bots = random.sample(list(recent_bots), num_bots)

            # Format bots for conversation prompt
            bots = []
            for b in selected_bots:
                bots.append({
                    'guid': b['bot1_guid'],
                    'name': b['bot1_name'],
                    'class': b['bot1_class'],
                    'race': b['bot1_race'],
                    'level': b['bot1_level'],
                    'zone': get_zone_name(b.get('zone_id', zone_id))
                })

            bot_names = [b['name'] for b in bots]
            bot_guids = {b['name']: b['guid'] for b in bots}

            logger.info(f"Event #{event_id} triggering {num_bots}-bot conversation: {', '.join(bot_names)}")

            # Build event conversation prompt
            prompt = build_event_conversation_prompt(bots, event_context, zone_id)

            # Call LLM
            response = call_llm(client, prompt, config)

            if response:
                messages = parse_conversation_response(response, bot_names)

                if messages:
                    logger.info(f"Event conversation with {len(messages)} messages:")

                    cumulative_delay = 0.0
                    for i, msg in enumerate(messages):
                        bot_guid = bot_guids.get(msg['name'], bots[0]['guid'])
                        final_message = cleanup_message(msg['message'])

                        if i > 0:
                            delay = calculate_dynamic_delay(len(final_message), config)
                            cumulative_delay += delay

                        cursor.execute("""
                            INSERT INTO llm_chatter_messages
                            (event_id, sequence, bot_guid, bot_name, message, channel, delivered, deliver_at)
                            VALUES (%s, %s, %s, %s, %s, 'general', 0, DATE_ADD(NOW(), INTERVAL %s SECOND))
                        """, (event_id, i, bot_guid, msg['name'], final_message, cumulative_delay))

                        logger.info(f"  [{i}] +{cumulative_delay:.1f}s {msg['name']}: {final_message}")

                    # Mark event completed
                    cursor.execute(
                        "UPDATE llm_chatter_events SET status = 'completed', processed_at = NOW() WHERE id = %s",
                        (event_id,))
                    db.commit()
                    return True

            # Fallback to statement if conversation failed
            logger.warning(f"Event conversation failed, falling back to statement")
            use_conversation = False

        # Statement mode (single bot)
        if not use_conversation:
            bot = dict(random.choice(list(recent_bots)))
            is_transport_event = event_type == 'transport_arrives'

            # Transport events bypass cooldown - they're high priority
            if not is_transport_event:
                # Check bot speaker cooldown for non-transport events
                cooldown = int(config.get('LLMChatter.BotSpeakerCooldownSeconds', 900))
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM llm_chatter_messages
                    WHERE bot_guid = %s AND delivered = 1
                      AND delivered_at > DATE_SUB(NOW(), INTERVAL %s SECOND)
                """, (bot['bot1_guid'], cooldown))
                result = cursor.fetchone()
                if result and result['cnt'] > 0:
                    cursor.execute(
                        "UPDATE llm_chatter_events SET status = 'skipped' WHERE id = %s",
                        (event_id,))
                    db.commit()
                    logger.info(f"Event #{event_id} skipped: bot {bot['bot1_name']} on cooldown")
                    return False
            else:
                logger.info(f"Transport event #{event_id}: bypassing cooldown for bot {bot['bot1_name']}")

            # Get zone name
            zone_name = get_zone_name(bot.get('zone_id', zone_id)) or "the world"

            # Build prompt for event-triggered statement
            tone = random.choice(TONES)

            # Transport events get more direct instructions
            is_transport = 'boat' in event_context.lower() or 'zeppelin' in event_context.lower() or 'turtle' in event_context.lower()
            if is_transport:
                event_instruction = """Comment on this transport arrival! Use the specific type (boat/zeppelin/turtle), NOT 'transport'.
Mention the destination if known. Be creative and original - no canned phrases."""
            else:
                event_instruction = """You may naturally reference this event in your message, or you may chat about something else entirely.
The event provides atmosphere - you don't HAVE to mention it explicitly."""

            system_prompt = f"""You are {bot['bot1_name']}, a {bot['bot1_race']} {bot['bot1_class']} adventurer in World of Warcraft.
You are level {bot['bot1_level']} and currently in {zone_name}.

CONTEXT: {event_context}

{event_instruction}

Your current mood: {tone}

Respond with a single short sentence (under 100 characters) that a player might say in General chat.
Be casual and authentic. No quotes. No asterisks. No emotes."""

            # Call LLM
            provider = config.get('LLMChatter.Provider', 'anthropic').lower()
            model = resolve_model(config.get('LLMChatter.Model', 'haiku'))
            max_tokens = int(config.get('LLMChatter.MaxTokens', 200))
            temperature = float(config.get('LLMChatter.Temperature', 0.8))

            if provider == 'openai':
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Say something in General chat."}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                message = response.choices[0].message.content.strip()
            else:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": "Say something in General chat."}]
                )
                message = response.content[0].text.strip()

            # Clean up message
            message = message.strip('"').strip()
            if len(message) > 255:
                message = message[:252] + "..."

            # Insert message for delivery
            delay_min = int(config.get('LLMChatter.MessageDelayMin', 1000))
            delay_max = int(config.get('LLMChatter.MessageDelayMax', 30000))
            delay_ms = random.randint(delay_min, delay_max)

            cursor.execute("""
                INSERT INTO llm_chatter_messages
                (event_id, sequence, bot_guid, bot_name, message, channel, delivered, deliver_at)
                VALUES (%s, 0, %s, %s, %s, 'general', 0, DATE_ADD(NOW(), INTERVAL %s SECOND))
            """, (event_id, bot['bot1_guid'], bot['bot1_name'], message, delay_ms // 1000))

            # Mark event completed
            cursor.execute(
                "UPDATE llm_chatter_events SET status = 'completed', processed_at = NOW() WHERE id = %s",
                (event_id,))
            db.commit()

            logger.info(f"Event #{event_id} processed: {bot['bot1_name']} will say: {message[:50]}...")
            return True

    except Exception as e:
        logger.error(f"Error processing event #{event_id}: {e}")
        cursor.execute(
            "UPDATE llm_chatter_events SET status = 'skipped' WHERE id = %s",
            (event_id,))
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

    # Check event system config
    use_event_system = config.get('LLMChatter.UseEventSystem', '1') == '1'

    logger.info("=" * 60)
    logger.info("LLM Chatter Bridge v3.3")
    logger.info("=" * 60)
    logger.info(f"Provider: {provider}")
    logger.info(f"Model: {model} (alias: {model_alias})")
    logger.info(f"Poll interval: {poll_interval}s")
    base_max = config.get('LLMChatter.MaxTokens', 200)
    convo_max = config.get('LLMChatter.ConversationMaxTokens', base_max)
    logger.info(f"Max tokens (statements): {base_max}")
    logger.info(f"Max tokens (conversations): {convo_max}")
    logger.info(f"Event system: {'enabled' if use_event_system else 'disabled'}")
    logger.info(f"Message type distribution: {MSG_TYPE_PLAIN}% plain, "
                f"{MSG_TYPE_QUEST - MSG_TYPE_PLAIN}% quest, "
                f"{MSG_TYPE_LOOT - MSG_TYPE_QUEST}% loot, "
                f"{MSG_TYPE_QUEST_REWARD - MSG_TYPE_LOOT}% quest+reward")
    logger.info("-" * 60)
    logger.info("Chatter settings (from config):")
    logger.info(f"  TriggerIntervalSeconds: {config.get('LLMChatter.TriggerIntervalSeconds', 60)}")
    logger.info(f"  TriggerChance: {config.get('LLMChatter.TriggerChance', 30)}%")
    logger.info(f"  ConversationChance: {config.get('LLMChatter.ConversationChance', 50)}%")
    logger.info(f"  BotSpeakerCooldownSeconds: {config.get('LLMChatter.BotSpeakerCooldownSeconds', 900)}")
    logger.info(f"  ZoneFatigueThreshold: {config.get('LLMChatter.ZoneFatigueThreshold', 3)}")
    logger.info("-" * 60)
    logger.info("Transport settings:")
    logger.info(f"  TransportEventChance: {config.get('LLMChatter.TransportEventChance', 30)}%")
    logger.info(f"  TransportCooldownSeconds (C++): {config.get('LLMChatter.TransportCooldownSeconds', 300)}")
    logger.info(f"  ZoneTransportCooldown (Python): {ZONE_TRANSPORT_COOLDOWN_SECONDS}s")
    logger.info("=" * 60)

    # Wait for database to be ready (handles Docker startup order)
    if not wait_for_database(config):
        logger.error("Could not connect to database. Exiting.")
        sys.exit(1)

    # Startup cleanup: reset any events stuck in 'processing' from previous crash
    if use_event_system:
        try:
            db = get_db_connection(config)
            reset_stuck_processing_events(db)
            db.close()
        except Exception as e:
            logger.warning(f"Could not reset stuck events on startup: {e}")

    # Main loop
    last_cleanup = 0
    cleanup_interval = 60  # Cleanup expired events every 60 seconds

    while True:
        try:
            db = get_db_connection(config)

            # Periodic cleanup of expired events
            current_time = time.time()
            if use_event_system and current_time - last_cleanup >= cleanup_interval:
                cleanup_expired_events(db)
                last_cleanup = current_time

            # Process regular chatter requests
            processed_request = process_pending_requests(db, client, config)

            # Process event-driven chatter (if enabled)
            processed_event = False
            if use_event_system:
                processed_event = process_pending_events(db, client, config)

            db.close()

            # Only sleep if nothing was processed
            if not processed_request and not processed_event:
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
