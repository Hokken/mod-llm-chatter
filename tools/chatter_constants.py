"""
Chatter Constants - All data/constants for the LLM Chatter Bridge.

Pure data module with no logic and no chatter imports.
"""

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
    17: "The Barrens", 331: "Ashenvale", 405: "Desolace",
    400: "Thousand Needles",
    15: "Dustwallow Marsh", 357: "Feralas", 440: "Tanaris", 16: "Azshara",
    361: "Felwood", 490: "Un'Goro Crater", 493: "Moonglade",
    618: "Winterspring",
    1377: "Silithus", 1637: "Orgrimmar", 1638: "Thunder Bluff",
    1657: "Darnassus",
    # Outland
    3483: "Hellfire Peninsula", 3518: "Nagrand",
    3519: "Terokkar Forest",
    3520: "Shadowmoon Valley", 3521: "Zangarmarsh",
    3522: "Blade's Edge Mountains",
    3523: "Netherstorm", 3524: "Shattrath City", 3703: "Shattrath City",
    3430: "Eversong Woods", 3433: "Ghostlands", 3487: "Silvermoon City",
    3525: "Bloodmyst Isle", 3557: "The Exodar",
    4080: "Isle of Quel'Danas",
    # Northrend
    3537: "Borean Tundra", 495: "Howling Fjord", 394: "Grizzly Hills",
    3711: "Sholazar Basin", 66: "Zul'Drak", 67: "Storm Peaks",
    210: "Icecrown",
    65: "Dragonblight", 2817: "Crystalsong Forest", 4395: "Dalaran",
    4197: "Wintergrasp", 4298: "The Oculus",
    # Other
    406: "Stonetalon Mountains",
}

# Capital cities - no hostile creatures to list
CAPITAL_CITY_ZONES = {
    1519,  # Stormwind City
    1537,  # Ironforge
    1657,  # Darnassus
    3557,  # The Exodar
    1637,  # Orgrimmar
    1638,  # Thunder Bluff
    1497,  # Undercity
    3487,  # Silvermoon City
    3524,  # Shattrath City
    3703,  # Shattrath City (alt)
    4395,  # Dalaran
}

# =============================================================================
# CLASS AND RACE MAPPINGS - Convert numeric IDs to names
# =============================================================================
CLASS_NAMES = {
    1: "Warrior", 2: "Paladin", 3: "Hunter", 4: "Rogue", 5: "Priest",
    6: "Death Knight", 7: "Shaman", 8: "Mage", 9: "Warlock", 11: "Druid"
}

# Reverse mapping: class name -> numeric ID (for trainer_spell queries)
CLASS_IDS = {v: k for k, v in CLASS_NAMES.items()}

RACE_NAMES = {
    1: "Human", 2: "Orc", 3: "Dwarf", 4: "Night Elf", 5: "Undead",
    6: "Tauren", 7: "Gnome", 8: "Troll", 10: "Blood Elf", 11: "Draenei"
}

# =============================================================================
# ROLEPLAY PERSONALITY DATA
# =============================================================================
RACE_SPEECH_PROFILES = {
    "Human": {
        "traits": (
            "practical, resilient, civic-minded, disciplined, "
            "ambitious, and quick to rally in a crisis"
        ),
        "flavor_words": [
            "for the Alliance", "by the Light", "Stormwind",
            "Lordaeron", "the Light", "King Varian",
        ],
        "vocabulary": [
            ("Light be with you", "blessing/greeting"),
            ("By the Light!", "exclamation of surprise or resolve"),
            ("Well met", "formal greeting"),
            ("For the Alliance!", "battle cry"),
            ("Go with honor, friend", "farewell"),
            ("Safe travels", "farewell"),
        ],
        "lore": [
            "Humans rebuilt Stormwind after devastation during the early wars.",
            "Northern human kingdoms were shattered, especially Lordaeron by the Scourge.",
            "The Church of the Holy Light strongly influences culture and institutions.",
            "Knightly orders, militias, and city guard traditions are central social pillars.",
            "Stormwind under King Varian is a major political and military Alliance center.",
            "Human realms balance idealism, survival pressure, and realpolitik.",
            "Titan records in Northrend connect human ancestry to the vrykul.",
        ],
        "worldview": (
            "Human politics center on Stormwind and the Alliance war effort. Faith in "
            "the Holy Light, military service, and civic order are strong social norms. "
            "After losses in Lordaeron and repeated invasions, human communities are "
            "cautious, patriotic, and focused on security."
        ),
    },
    "Orc": {
        "traits": (
            "blunt, proud, honor-bound, tribal, intense, and "
            "protective of hard-won freedom"
        ),
        "flavor_words": [
            "Lok'tar ogar", "blood and thunder", "for the Horde",
            "Durotar", "Orgrimmar", "ancestors",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "Victory or death!"),
            ("Zug-zug", "acknowledgment, like 'okay'"),
            ("Dabu", "I obey / I agree"),
            ("Throm-ka", "Well met"),
            ("Aka'Magosh", "A blessing on you and yours"),
            ("Lok-Narash!", "Arm yourselves!"),
            ("Gol'Kosh!", "By my axe!"),
        ],
        "lore": [
            "Orcs came from Draenor and were manipulated into fel corruption.",
            "After the Second War, many were held in internment camps.",
            "Thrall united clans and founded a new Horde based in Durotar.",
            "Shamanic traditions and ancestral respect were reclaimed from earlier corruption.",
            "Orc society values clan memory, martial prowess, and personal honor.",
            "In Wrath, Garrosh Hellscream's rise in Horde command sharpens political tension.",
            "The legacy of demonic enslavement still shapes identity and pride.",
        ],
        "worldview": (
            "Orc identity in the New Horde is built on recovery from demonic corruption, "
            "loyalty to clan and Horde, and restored shamanic traditions. Durotar and "
            "Orgrimmar represent self-rule after internment. Honor, strength, and survival "
            "are treated as inseparable duties."
        ),
    },
    "Dwarf": {
        "traits": (
            "hearty, stubborn, craft-proud, clan-loyal, blunt, "
            "and curious about old secrets"
        ),
        "flavor_words": [
            "by my beard", "aye", "stone and steel",
            "Ironforge", "Khaz Modan", "clan",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "farewell"),
            ("Fer Khaz Modan!", "For Khaz Modan! — battle cry"),
            ("Well met", "greeting"),
            ("Off with ye", "casual farewell"),
        ],
        "lore": [
            "Dwarves descend from titan-forged earthen changed by the Curse of Flesh.",
            "Three major clans define politics: Bronzebeard, Wildhammer, and Dark Iron.",
            "Ironforge is a key Alliance stronghold and trade center.",
            "Engineering, smithing, firearms, and brewing are major cultural strengths.",
            "The Explorers League drives archaeology and titan research across Azeroth.",
            "Clan memory and grudges can last generations.",
            "Dwarves are battle-tested Alliance veterans from multiple wars.",
        ],
        "worldview": (
            "Dwarven society is clan-based and strongly tied to Ironforge, craft traditions, "
            "and titan archaeology. Military service and practical labor are both respected. "
            "Alliances are judged by loyalty and proven deeds."
        ),
    },
    "Night Elf": {
        "traits": (
            "ancient, reverent, guarded, patient, proud, and "
            "fiercely protective of nature"
        ),
        "flavor_words": [
            "Elune", "Elune guide you", "the wilds",
            "Kaldorei", "Darnassus", "moonwell",
        ],
        "vocabulary": [
            ("Ishnu-alah", "Good fortune to you"),
            ("Ishnu-dal-dieb", "Good fortune to your family"),
            ("Elune-adore", "Elune be with you"),
            ("Ande'thoras-ethil", "May your troubles be diminished"),
            ("Andu-falah-dor!", "Let balance be restored!"),
            ("Bandu Thoribas!", "Prepare to fight!"),
            ("Fandu-dath-belore?", "Who goes there?"),
            ("Tor ilisar'thera'nal!", "Let our enemies beware!"),
        ],
        "lore": [
            "Ancient Kaldorei civilization was shattered by the Sundering.",
            "Strong devotion to Elune, druidism, and sentinel traditions.",
            "Long history of fighting demons, satyrs, and corruption in sacred forests.",
            "Immortality ended after events surrounding Nordrassil and the Third War.",
            "Alliance membership after Warcraft III remains practical rather than intimate.",
            "Guardianship of moonwells, world trees, and wilderness sanctuaries is central.",
            "Arcane excess is feared due to memories of past global catastrophe.",
        ],
        "worldview": (
            "Kaldorei priorities are defense of sacred lands, Elune worship, and druidic "
            "balance. Collective memory of the Sundering makes them cautious about reckless "
            "arcane use. Alliance cooperation exists, but cultural distance from younger "
            "races remains."
        ),
    },
    "Undead": {
        "traits": (
            "darkly sardonic, bitter, pragmatic, ruthless, "
            "survivor-minded, and fiercely insular"
        ),
        "flavor_words": [
            "Dark Lady", "plague", "the grave",
            "Forsaken", "Undercity", "Scourge",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "farewell/blessing"),
            ("Victory for Sylvanas", "rallying cry"),
            ("Embrace the shadow", "farewell"),
            ("Our time will come", "expression of resolve"),
        ],
        "lore": [
            "Forsaken are former Scourge undead who regained free will.",
            "Led by Sylvanas Windrunner from the Undercity.",
            "Born from the ruins of Lordaeron and rejected by most living.",
            "Royal Apothecary Society develops blight and other brutal chemical weapons.",
            "Wrath-era events include the Wrathgate betrayal and internal faction purges.",
            "Horde membership is strategic and often marked by mutual distrust.",
            "Vengeance against the Lich King is a core emotional and political driver.",
        ],
        "worldview": (
            "Forsaken politics center on preserving free will, securing Lordaeron holdings, "
            "and destroying Scourge threats. Undercity society is militarized and heavily "
            "influenced by apothecary and intelligence networks. Their Horde relationship is "
            "strategic, shaped by shared enemies more than trust."
        ),
    },
    "Tauren": {
        "traits": (
            "calm, grounded, spiritual, honorable, patient, "
            "and protective of kin and land"
        ),
        "flavor_words": [
            "Earth Mother", "walk with the Earth Mother",
            "ancestors", "Thunder Bluff", "shu'halo",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "farewell/blessing"),
            ("Ancestors watch over you", "farewell"),
            ("Winds be at your back", "farewell/blessing"),
            ("Earth Mother guide you", "blessing"),
        ],
        "lore": [
            "Nomadic tribes were unified under Cairne Bloodhoof.",
            "Thunder Bluff became the central tauren city in Mulgore.",
            "Spiritual life centers on the Earth Mother and ancestors.",
            "Druidism and shamanism are core cultural pillars.",
            "Joined the Horde after orc aid against centaur aggression.",
            "Strong hunting and oral-tradition culture preserves identity and history.",
            "In Wrath, Cairne Bloodhoof is one of the senior Horde leaders.",
        ],
        "worldview": (
            "Tauren social order emphasizes tribal duty, elders, and reverence for the "
            "Earth Mother and ancestors. They value mediation and restraint, but defend kin "
            "and territory decisively. Horde membership is framed as an oath of gratitude "
            "and mutual defense."
        ),
    },
    "Gnome": {
        "traits": (
            "inventive, curious, upbeat, analytical, quick-thinking, "
            "and relentless under pressure"
        ),
        "flavor_words": [
            "tinkering", "by my calculations", "brilliant",
            "High Tinker", "Mekkatorque", "Gnomeregan",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "battle cry"),
            ("Salutations!", "formal greeting"),
            ("My, you're a tall one!", "greeting, self-aware humor"),
        ],
        "lore": [
            "Native to Gnomeregan, famed for engineering and invention.",
            "The city was lost to trogg invasion and catastrophic irradiation.",
            "Survivors became refugees hosted near Ironforge.",
            "High Tinker Mekkatorque leads recovery efforts in Wrath era.",
            "Culture prizes experimentation, improvisation, and technical literacy.",
            "Engineering spans warfare, transport, medicine, and daily life tools.",
            "Alliance ties are close, especially with dwarves in Ironforge.",
        ],
        "worldview": (
            "Gnomish culture treats engineering and science as civic service, not just "
            "profession. Recovery of Gnomeregan remains a unifying political goal under "
            "Gelbin Mekkatorque. Their Alliance role often focuses on logistics, invention, "
            "and technical support."
        ),
    },
    "Troll": {
        "traits": (
            "laid-back, spiritual, streetwise, proud, adaptive, "
            "and dangerous when crossed"
        ),
        "flavor_words": [
            "mon", "da spirits", "loa",
            "Darkspear", "Vol'jin", "Echo Isles",
        ],
        "vocabulary": [
            ("Taz'dingo!", "war cry / cheer"),
            ("Spirits be with ya, mon", "farewell/blessing"),
            ("Stay away from da voodoo", "warning/farewell"),
        ],
        "lore": [
            "Playable trolls are Darkspear, not Amani or Gurubashi.",
            "Darkspear were rescued by Thrall and joined the Horde.",
            "Loa worship, voodoo practice, and shadow hunter traditions shape culture.",
            "Vol'jin leads the Darkspear in Wrath era politics.",
            "Ancient troll empires predate many younger civilizations on Azeroth.",
            "Darkspear identity is shaped by exile, migration, and survival at the margins.",
            "Tribal memory and practical spirituality guide daily decisions.",
        ],
        "worldview": (
            "Darkspear worldview is tribal, survival-focused, and guided by loa tradition. "
            "Leadership under Vol'jin emphasizes loyalty to the Horde while preserving "
            "distinct troll identity. Oral history, shadow hunter practice, and adaptability "
            "are core cultural traits."
        ),
    },
    "Blood Elf": {
        "traits": (
            "proud, elegant, disciplined, image-conscious, "
            "arcane-focused, and emotionally guarded"
        ),
        "flavor_words": [
            "Sin'dorei", "Sunwell", "arcane",
            "Quel'Thalas", "Silvermoon", "regent lord",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "Greetings, traveler"),
            ("Shorel'aran", "Farewell"),
            ("Selama ashal'anore", "Justice for our people"),
            ("Anar'alah belore", "By the light of the sun"),
            ("Anu belore dela'na", "The sun guides us"),
            ("Sinu a'manore", "Well met"),
            ("Doral ana'diel?", "How fare you?"),
            ("Al diel shala", "Safe travels"),
        ],
        "lore": [
            "Sin'dorei are survivors of Quel'Thalas after Scourge devastation.",
            "Sunwell destruction caused magical withdrawal and social crisis.",
            "Kael'thas alliance with the Legion ended in open betrayal.",
            "Sunwell was restored with Light and arcane energy in late TBC.",
            "Lor'themar Theron governs as regent lord in the Wrath period.",
            "Blood Knights transformed from siphoning power to serving restored Light sources.",
            "Horde ties are pragmatic, shaped by politics, memory, and survival.",
        ],
        "worldview": (
            "Blood elf policy prioritizes security of Quel'Thalas, protection of the restored "
            "Sunwell, and control of arcane resources. Public culture prizes discipline and "
            "dignity after national trauma. Horde membership is practical statecraft shaped "
            "by past abandonment and current threats."
        ),
    },
    "Draenei": {
        "traits": (
            "devout, resilient, contemplative, compassionate, "
            "ancient, and quietly battle-hardened"
        ),
        "flavor_words": [
            "the Naaru", "the Light", "Argus",
            "Exodar", "Velen", "Draenor",
        ],
        "vocabulary": [
            ("Archenon poros", "Good fortune"),
            ("Dioniss aca", "Safe journey"),
            ("Krona ki cristorr!", "The Legion will fall!"),
            ("Pheta vi acahachi!", "Light give me strength!"),
            ("Pheta thones gamera", "Light, guide our path"),
        ],
        "lore": [
            "Descended from eredar exiles led by Prophet Velen.",
            "Fled Argus and endured millennia of Legion pursuit.",
            "Arrived on Azeroth after the Exodar crash on Azuremyst.",
            "Guided by the naaru, the Light, and vindicator martial orders.",
            "Draenor history includes devastation by the Horde before current alliances formed.",
            "Society combines mystic faith with advanced crystalline technology.",
            "Carries deep memory of loss alongside patient, disciplined hope.",
        ],
        "worldview": (
            "Draenei society is organized around Velen's leadership, reverence for the naaru, "
            "and long memory of exile. Alliance membership serves both moral alignment and "
            "strategic defense against Legion remnants. Their culture combines advanced crystal "
            "technology with religious duty and communal healing."
        ),
    },
}

CLASS_SPEECH_MODIFIERS = {
    "Warrior": (
        "direct and battle-tested; values discipline, grit, and frontline courage; "
        "talks in practical terms about weapons, formations, and surviving the fight"
    ),
    "Paladin": (
        "righteous and resolute; frames choices as duty and sacrifice; speaks of "
        "the Light, justice, oaths, and protecting the innocent"
    ),
    "Hunter": (
        "observant and patient; notices tracks, terrain, and creature behavior; "
        "speaks like a scout who trusts preparation, instincts, and steady aim"
    ),
    "Rogue": (
        "guarded and sharp-tongued; favors understatement, hints, and dry humor; "
        "references stealth, opportunity, poisons, and clean execution"
    ),
    "Priest": (
        "contemplative and empathetic; offers counsel, comfort, or stern warnings; "
        "speaks of faith, spirit, and inner resolve in crisis"
    ),
    "Death Knight": (
        "cold, disciplined, and haunted; matter-of-fact about death and suffering; "
        "uses grim, military phrasing shaped by Scourge memories"
    ),
    "Shaman": (
        "grounded and reverent; speaks of elements, ancestors, and imbalance; "
        "tone is communal and spiritual, with practical respect for natural forces"
    ),
    "Mage": (
        "precise and scholarly; references arcane theory, runes, and control; "
        "curious about magical anomalies but wary of unstable power"
    ),
    "Warlock": (
        "calmly unsettling and sardonic; treats forbidden magic as a tool; "
        "references pacts, curses, and risk with controlled confidence"
    ),
    "Druid": (
        "serene but firm; speaks of balance, cycles, and stewardship of the wilds; "
        "frames conflict as restoring harmony when nature is threatened"
    ),
}

# =============================================================================
# CLASS ROLE MAP - Maps class to primary group role
# =============================================================================
# Hybrids get flexible roles since we lack spec/talent data.
CLASS_ROLE_MAP = {
    "Warrior": "tank",
    "Death Knight": "tank",
    "Priest": "healer",
    "Rogue": "melee_dps",
    "Hunter": "ranged_dps",
    "Mage": "ranged_dps",
    "Warlock": "ranged_dps",
    "Paladin": "hybrid_tank",
    "Druid": "hybrid_tank",
    "Shaman": "hybrid_healer",
}

# =============================================================================
# ROLE COMBAT PERSPECTIVES - Injected into group prompts
# =============================================================================
ROLE_COMBAT_PERSPECTIVES = {
    "tank": (
        "Your group role is to lead the charge and take hits "
        "so others don't have to. You think about positioning, "
        "threat, and keeping enemies focused on you. When "
        "someone gets hurt, you feel responsible. Only "
        "reference your role during combat situations."
    ),
    "healer": (
        "Your group role is keeping everyone alive. You watch "
        "health bars constantly, manage your mana carefully, "
        "and worry when someone takes unexpected damage. You "
        "notice who plays recklessly. Only reference your "
        "role during combat situations."
    ),
    "melee_dps": (
        "Your group role is dealing damage up close. You care "
        "about hitting hard, staying behind the target, and "
        "not pulling aggro from the tank. You respect the "
        "healer keeping you alive. Only reference your role "
        "during combat situations."
    ),
    "ranged_dps": (
        "Your group role is dealing damage from a safe "
        "distance. You think about positioning, crowd control, "
        "and burning targets down efficiently. You keep one "
        "eye on your threat. Only reference your role during "
        "combat situations."
    ),
    "hybrid_tank": (
        "You can fill multiple roles depending on what the "
        "group needs — tanking, healing, or damage. You think "
        "about group balance and adapt your mindset to "
        "whatever the situation demands. Only reference your "
        "role during combat situations."
    ),
    "hybrid_healer": (
        "You can heal or deal damage depending on what the "
        "group needs. You keep one eye on health bars while "
        "contributing damage, ready to switch focus if "
        "someone is in danger. Only reference your role "
        "during combat situations."
    ),
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
    141: """Teldrassil: Massive world tree home to the night elves. Despite some
troubles with hostile Gnarlpine furbolgs and timberlings, the forest remains
breathtakingly beautiful - ancient trees glow softly at twilight, moonwells
shimmer with arcane energy, and peaceful glades invite quiet reflection.
Darnassus sits serenely above the canopy. The air carries whispers of old
magic. Night elves go about daily life: training, crafting, tending gardens.
A place where nature's beauty persists even as adventurers deal with threats.""",

    148: """Darkshore: Long, misty coastline where fog rolls in from the sea,
creating an ethereal atmosphere. Ancient night elf ruins hold mysteries and
forgotten lore. Auberdine bustles with travelers catching boats to Teldrassil,
Stormwind, or Azuremyst Isle. Fishermen work the docks, adventurers trade
stories at the inn. Yes, murlocs and naga cause trouble on the beaches, and
some wildlife has turned aggressive - but the coastline's haunting beauty
endures. Moonlit shores, ancient architecture, the sound of waves. A zone
of contrasts: peaceful harbors and dangerous wilds, old magic and new threats.""",

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

# =============================================================================
# DUNGEON FLAVOR - Rich context for immersive dungeon/raid chat generation
# =============================================================================
# Each dungeon/raid gets a description that gives the LLM world knowledge.
# Keyed by Map ID (not zone ID). The LLM uses this as creative inspiration.
DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Shadowfang Keep: A haunted fortress in Silverpine Forest, overrun by worgen and the undead servants of the necromancer Arugal. Ghostly nobles wander the dark halls, spectral hounds bay in the courtyards, and arcane experiments gone wrong lurk in every shadow. The keep feels like a gothic horror story - cold stone, flickering torchlight, and the constant sense that something is watching.""",

    34: """The Stockade: A prison beneath Stormwind City where the inmates have revolted and taken control. Defias rioters, crazed convicts, and gang leaders roam the cramped stone cellblocks. The dungeon is claustrophobic and brutal - narrow corridors, iron bars, and the sounds of violence echoing off damp walls. Quick, dirty, and dangerous.""",

    36: """The Deadmines: A sprawling mine complex beneath Westfall, secretly the headquarters of the Defias Brotherhood. The path winds through goblin-engineered tunnels, lumber mills, and smelting operations before emerging in a massive underground cavern where a full-sized pirate ship sits in a hidden cove. It feels like discovering a criminal empire hidden right under Stormwind's nose.""",

    43: """Wailing Caverns: A maze of twisting caverns in the Barrens, overgrown with lush vegetation fed by corrupted druid magic. Deviate creatures - mutated raptors, serpents, and oozes - slither through the emerald-tinted tunnels. The Druids of the Fang have lost themselves to the Emerald Nightmare. The air is thick, humid, and smells of jungle rot.""",

    47: """Razorfen Kraul: A thorny labyrinth grown from massive briars in the Barrens, home to the quilboar and their matriarch Charlga Razorflank. Quilboar warriors, shamans, and their boar companions fill the winding thorn-walled corridors. The dungeon feels primal and feral - nature twisted into a fortress of bone, thorn, and mud.""",

    48: """Blackfathom Deeps: A partially submerged ancient temple on Darkshore's coast, sacred to dark powers. Naga, satyrs, and twilight cultists worship old gods in flooded halls adorned with crumbling night elf architecture. The water glows an eerie blue-green, and the atmosphere is oppressive and ancient - something powerful sleeps in the deepest pools.""",

    70: """Uldaman: A titan excavation site buried in the Badlands, half-dig and half-dungeon. Stone troggs, earthen constructs, and archaeological hazards fill chambers of polished titan metal and raw rock. The deeper you go, the more alien the architecture becomes - smooth geometric halls humming with dormant power. It feels like trespassing in a library built by gods.""",

    90: """Gnomeregan: The irradiated ruins of the gnomish capital city, lost to a trogg invasion and a catastrophic radiation leak. Crazed leper gnomes, malfunctioning robots, and toxic oozes populate the multi-leveled mechanical complex. Alarm klaxons blare, green radiation pools glow, and broken machinery sparks everywhere. It is equal parts tragic and absurd.""",

    109: """Sunken Temple: The Temple of Atal'Hakkar, a troll temple dragged beneath the swamps by the Green Dragonflight. Atal'ai trolls worship the blood god Hakkar in flooded, vine-choked halls. Dragonkin guard the deeper levels, and the maze-like layout is disorienting. The atmosphere is thick with jungle humidity, ancient troll magic, and a sense of forbidden ritual.""",

    129: """Razorfen Downs: A quilboar burial ground in the Barrens, infested with undead. The Scourge agent Amnennar the Coldbringer has raised the quilboar dead, turning their sacred crypts into a necropolis of bone and thorn. Skeletal quilboar and plague bats fill the gloomy corridors. A place where two kinds of death collide - primal and necromantic.""",

    189: """Scarlet Monastery: A fortified monastery in Tirisfal Glades, stronghold of the fanatical Scarlet Crusade. Four wings house a library of forbidden texts, an armory bristling with zealots, a cathedral of twisted faith, and a haunted graveyard. The Crusaders are well-armed, disciplined, and utterly insane - convinced everyone is secretly undead. Beautiful architecture hiding murderous fanaticism.""",

    209: """Zul'Farrak: A troll city half-buried in the sands of Tanaris, home to the hostile Sandfury trolls. Sun-baked stone temples, sacrificial altars, and sandy courtyards make up this open-air dungeon. The famous staircase battle pits you against waves of troll warriors. The desert heat is relentless, the trolls are savage, and ancient magic crackles through the ruins.""",

    229: """Blackrock Spire: A massive orc fortress carved into the upper reaches of Blackrock Mountain. The lower spire teems with Blackrock orcs, ogres, and trolls, while the upper spire is the seat of Warchief Rend Blackhand and his dragonkin allies. Lava glows below, war drums echo constantly, and the air reeks of smoke and blood. A sprawling military stronghold at the heart of the Dark Horde.""",

    230: """Blackrock Depths: A vast Dark Iron dwarf city deep within Blackrock Mountain, built around a lake of molten lava. The Grim Guzzler tavern, the Emperor's throne room, and Molten Core's doorstep are all here. Elementals, golems, and fanatical Dark Iron dwarves fill an impossibly large underground metropolis. It feels like an entire civilization exists down here, dark and industrious and hostile.""",

    269: """The Black Morass: A Caverns of Time instance set in the primordial swamp that would become the Blasted Lands. Infinite Dragonflight agents attempt to prevent Medivh from opening the Dark Portal, and waves of dragonkin assault through time rifts. The swamp is dark, foggy, and primeval, with the Portal's energy crackling in the distance. Time itself feels unstable here.""",

    289: """Scholomance: A necromantic academy in the crypts beneath Caer Darrow, run by the Cult of the Damned. Students and professors of dark magic practice their craft on the dead and the living alike. Skeletons, ghosts, and flesh golems fill classrooms and laboratories. The dungeon has a perverse scholarly atmosphere - lecture halls and libraries devoted entirely to death magic.""",

    329: """Stratholme: The burning ruins of a once-great city, forever aflame since Arthas purged it. The undead Scourge controls the eastern half while the Scarlet Crusade fanatically holds the western gates. Buildings crumble in perpetual fire, abominations lumber through the streets, and the ash never settles. A monument to tragedy and madness - every corner holds the memory of slaughter.""",

    349: """Maraudon: A sacred cavern system in Desolace, warped by Princess Theradras and her centaur descendants after the death of the keeper Zaetar. Three color-coded paths wind through crystalline caves, poisonous waterfalls, and lush underground gardens before reaching the inner sanctum. The deeper chambers are hauntingly beautiful - glowing crystals, clear pools, and ancient earth magic struggling against corruption. Nature, grief, and elemental fury tangled together.""",

    389: """Ragefire Chasm: A volcanic cavern system beneath Orgrimmar itself, where Burning Blade cultists and troggs have taken root. Lava flows through narrow tunnels, fire elementals patrol, and the heat is suffocating. Short and brutal - the kind of place that reminds you the Horde built their capital on top of a volcano.""",

    429: """Dire Maul: A ruined Highborne city in Feralas, divided into three wings. Ogres have claimed the north, satyrs and corrupted ancients infest the east, and ghostly Highborne spirits haunt the west wing's library. Crumbling elven architecture of staggering beauty slowly succumbs to jungle overgrowth. The dungeon feels vast, ancient, and melancholy - a great civilization's corpse being picked apart by squatters.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Onyxia's Lair: A single vast cavern in Dustwallow Marsh, home to the broodmother Onyxia. The approach winds through a narrow tunnel of scorched rock before opening into an enormous chamber littered with bones and egg clutches. Whelps swarm, lava bubbles at the edges, and Onyxia herself fills the cavern with fire and shadow. Claustrophobic tunnel into an overwhelming arena of dragonfire.""",

    309: """Zul'Gurub: A massive troll temple complex in the jungles of Stranglethorn, where the Gurubashi tribe has unleashed the blood god Hakkar. Overgrown courtyards, sacrificial altars, and beast-filled plazas surround a central temple dripping with blood magic. Snake priests, bat riders, and tiger cultists serve their dark masters. The jungle itself seems to pulse with primal voodoo energy.""",

    409: """Molten Core: The burning heart of Blackrock Mountain, a realm of pure fire ruled by Ragnaros the Firelord. Rivers of lava flow between obsidian platforms, fire elementals and molten giants patrol everywhere, and the heat is apocalyptic. Core hounds with multiple heads, towering lava surgers, and ancient flamewakers guard their master. The ultimate trial by fire - beautiful and terrifying in equal measure.""",

    469: """Blackwing Lair: Nefarian's stronghold atop Blackrock Spire, a dark laboratory where the black dragon experiments on other dragonflights. Drakonid soldiers, chromatic drakes, and failed experiments fill halls of dark iron and dragon bone. Each chamber presents a unique tactical challenge. The raid feels clinical and sinister - a mad scientist's lair scaled up to dragon proportions.""",

    509: """Ruins of Ahn'Qiraj: An open-air battlefield in Silithus where qiraji forces mass for war. Insectoid warriors, obsidian destroyers, and massive beetle-like creatures swarm across sand-swept courtyards and crumbling temple ruins. The architecture is alien and chitinous, equal parts Egyptian tomb and insect hive. The desert wind carries the clicking of a million legs.""",

    531: """Temple of Ahn'Qiraj: The sealed inner sanctum of the qiraji empire, a nightmare of alien architecture and old god corruption. The twin emperors, massive silithid royalty, and the ancient god C'Thun itself lurk within. Walls pulse with organic growth, eyes watch from every surface, and reality bends near the old god's prison. The most alien and disturbing place in classic Azeroth.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Shattered Halls: The fel orc stronghold within Hellfire Citadel, a blood-soaked gauntlet of the most fanatical Burning Legion servants. Fel orc gladiators, legionnaires, and berserkers pack every corridor, with prisoners chained to the walls. The architecture is brutal iron and red stone, stained with the evidence of constant violence. An unrelenting assault on a fortress that fights back at every step.""",

    542: """Blood Furnace: A demonic factory within Hellfire Citadel where fel orcs are manufactured through dark rituals. Vats of boiling blood, caged prisoners awaiting transformation, and fel machinery fill the steaming chambers. Nascent fel orcs and their overseers guard the production lines. The dungeon reeks of blood and brimstone - an industrial horror show.""",

    543: """Hellfire Ramparts: The outer fortifications of Hellfire Citadel, first line of defense for the fel orc army. Watchtowers, battlements, and narrow walkways offer sweeping views of the shattered Hellfire Peninsula below. Fel orc soldiers, worg riders, and a captive dragon guard the walls. The wind howls through broken ramparts, and the red sky of Outland stretches endlessly overhead.""",

    545: """The Steamvault: A naga-controlled water pumping station in Coilfang Reservoir, where Lady Vashj's forces drain Zangarmarsh. Massive pipes, valves, and water channels dominate the industrial layout. Naga, bog lords, and water elementals guard the machinery. Steam hisses from every joint and the roar of rushing water is deafening. A dungeon that feels like sabotaging a hostile factory.""",

    546: """The Underbog: A festering swamp beneath Coilfang Reservoir, teeming with mutated fungal creatures and hostile nature spirits. Spore giants, bog lords, and venomous wildlife fill the overgrown caverns. Bioluminescent fungi cast an eerie glow over stagnant pools. The air is thick with spores and the smell of decay - nature run wild and turned hostile.""",

    547: """The Slave Pens: The labor camps of Coilfang Reservoir where the Broken draenei are held captive by naga slavemasters. Waterlogged tunnels, crude holding pens, and naga overseers with their whips define the atmosphere. Fungal growths and marsh creatures have infiltrated the complex. A dungeon suffused with misery and oppression, half-drowned and rotting.""",

    552: """The Arcatraz: A dimensional prison satellite of Tempest Keep, holding the most dangerous entities in the cosmos. Eredar warlocks, void creatures, and blood elf saboteurs roam cellblocks designed to contain horrors beyond imagination. The architecture is crystalline draenei technology warped by its inmates. Every cell door you pass makes you wonder what got out - and what is still locked inside.""",

    553: """The Botanica: A vast biodome satellite of Tempest Keep, where exotic flora from across the cosmos was once cultivated. Blood elves have seized the facility, and the plants have grown wild and hostile. Lashers, treants, and alien botanical specimens fill conservatories of shimmering crystal. Beautiful but deadly - every flower might kill you, and the blood elves are worse.""",

    554: """The Mechanar: A manufacturing wing of Tempest Keep, now controlled by blood elf engineers and their mechanical creations. Arcane constructs, fel reavers, and nethermancer overseers guard corridors of gleaming crystal and humming machinery. The technology is elegant and alien - draenei engineering repurposed for sinister ends. Everything hums with barely contained arcane energy.""",

    555: """Shadow Labyrinth: The deepest wing of Auchindoun, where the Shadow Council conducts its darkest rituals. Void walkers, fel casters, and Cabal cultists worship in chambers thick with shadow magic. Murmur, a primordial sound elemental, is chained in the deepest chamber. The darkness here feels alive and hungry - shadows move on their own, and whispers come from everywhere and nowhere.""",

    556: """Sethekk Halls: Arakkoa temple halls within Auchindoun, occupied by fanatics devoted to the Raven God Anzu. Crazed arakkoa priests, their summoned spirits, and spectral guardians fill the feather-strewn corridors. The architecture mixes draenei and arakkoa styles in unsettling ways. The inhabitants have gone utterly insane, and the halls echo with deranged screeching and dark prophecy.""",

    557: """Mana-Tombs: The ethereal-infested wing of Auchindoun, where Nexus-Prince Shaffar's consortium plunders draenei burial vaults. Ethereal bandits, arcane constructs, and restless draenei spirits clash in crystalline tomb chambers. The tombs glow with residual holy energy while the ethereals siphon it away. A sacred place being systematically looted by interdimensional thieves.""",

    558: """Auchenai Crypts: The draenei burial grounds beneath Auchindoun, where the Auchenai priests have gone mad communing with the dead. Restless spirits, possessed clerics, and undead draenei fill the bone-lined crypts. What was once a place of respectful remembrance has become a charnel house. The tragedy is palpable - these were caretakers who lost themselves to grief.""",

    560: """Old Hillsbrad Foothills: A Caverns of Time instance set in the past, when Thrall was still a slave in Durnholde Keep. The Hillsbrad of years ago is green, peaceful, and full of unsuspecting humans going about their lives. The Infinite Dragonflight tries to alter history by preventing Thrall's escape. It feels surreal - walking through a place you know before it all went wrong.""",

    568: """Zul'Aman: A forest troll stronghold in the Ghostlands, where Warlord Zul'jin has empowered his champions with the essence of animal gods. Lynx, bear, eagle, and dragonhawk spirits infuse the troll temple guardians. The Amani forest-temple architecture is vivid and primal, decorated with masks, totems, and war paint. A timed gauntlet where speed matters and the troll drums never stop beating.""",

    585: """Magisters' Terrace: The final bastion of Kael'thas Sunstrider on the Isle of Quel'Danas, a blood elf palace of stunning elegance hiding demonic corruption. Fel crystals power arcane constructs, blood elf magisters channel forbidden magic, and a captured naaru is being drained of its Light. The beauty of Silvermoon architecture twisted by desperation and addiction - gilded halls concealing a monstrous bargain.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: The haunted tower of the last Guardian, Medivh, in Deadwind Pass. A spectral dinner party, an opera stage with ghostly performers, a chess game come to life, and a celestial observatory fill the impossibly tall tower. The tower exists partially outside normal reality - rooms shift, time bends, and echoes of Medivh's madness play out eternally. Hauntingly beautiful, deeply eerie, and utterly unique.""",

    534: """Hyjal Summit: A Caverns of Time raid set during the Battle of Mount Hyjal, the climactic stand against Archimonde and the Burning Legion. Waves of undead and demons assault three bases in succession - human, Horde, and night elf. The world tree Nordrassil looms above while the forest burns. An epic defense scenario where the fate of Azeroth hangs in the balance and legendary heroes fight at your side.""",

    544: """Magtheridon's Lair: A single brutal chamber beneath Hellfire Citadel where the pit lord Magtheridon is chained. Channelers maintain his prison while hellfire energy pulses through the room. The space is oppressively hot, reeking of demon blood and brimstone. A straightforward but punishing encounter - one massive demon, one deadly room, no room for error.""",

    548: """Serpentshrine Cavern: Lady Vashj's underwater stronghold in Coilfang Reservoir, a flooded palace of corrupted beauty. Naga, tidewalkers, and colossal hydras guard chambers where waterfalls cascade into luminous pools. Bridges span underground lakes, and the deeper chambers pulse with the corrupted waters of Zangarmarsh. Elegant naga architecture meets the raw power of a subterranean ocean.""",

    550: """Tempest Keep - The Eye: Kael'thas Sunstrider's captured naaru fortress, a crystalline citadel floating above Netherstorm. Blood elf advisors, arcane constructs, and void creatures guard chambers of shimmering draenei crystal. The technology is breathtakingly alien and beautiful, repurposed by desperate elves feeding their magic addiction. The view of the shattered Netherstorm from the platforms is both stunning and terrifying.""",

    564: """Black Temple: Illidan Stormrage's fortress in Shadowmoon Valley, a massive draenei temple corrupted by demonic occupation. Fel orcs, demons, naga, and blood elves serve the Betrayer through sprawling courtyards, sewer systems, and grand halls. The temple's original beauty is scarred by fel corruption - cracked holy symbols, defiled altars, and green fire where there was once Light. The culmination of Outland's story, ending at Illidan's throne.""",

    565: """Gruul's Lair: A rough cavern complex in Blade's Edge Mountains, home to the gronn father Gruul the Dragonkiller. Ogre servants and Gruul's monstrous sons guard the approach to his chamber, which is littered with dragon bones and trophies. The caves feel primal and brutal - no architecture, no decoration, just raw stone shaped by the fists of giants.""",

    580: """Sunwell Plateau: The final raid of the Burning Crusade, set in the heart of the restored Sunwell on the Isle of Quel'Danas. The Burning Legion attempts to summon Kil'jaeden through the Sunwell itself. Pristine elven architecture of breathtaking beauty frames a desperate battle against the most powerful demons in the Legion's army. The holy light of the Sunwell clashes with demonic darkness in every chamber.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Utgarde Keep: A vrykul fortress on the shores of the Howling Fjord, the first taste of Northrend's dangers. Viking-inspired halls of dark stone and iron, lit by roaring hearths and decorated with dragon skulls. Vrykul warriors, proto-drake handlers, and their undead servants fill the great halls. The dungeon feels like raiding a Norse longhouse - cold, brutal, and steeped in warrior culture.""",

    575: """Utgarde Pinnacle: The upper reaches of Utgarde Keep, where the vrykul king Ymiron rules from his frozen throne. Trophy halls, eagle aviaries, and ritual chambers tower above the fjord. The architecture grows grander and more menacing as you ascend, culminating in Ymiron's frost-rimed throne room. Wind howls through open battlements, and the view of the frozen landscape below is dizzying.""",

    576: """The Nexus: The crystalline caves beneath Coldarra, stronghold of the Blue Dragonflight's war on mortal magic. Frozen caverns of impossible beauty contain arcane anomalies, crazed mage hunters, and rifts in reality. Crystallized dragons hang frozen in mid-flight. The dungeon shimmers with unstable arcane energy - blues, purples, and whites refracting through ice and crystal in every direction.""",

    578: """The Oculus: The upper rings of the Nexus, a series of floating platforms connected by magical bridges high above the ley line nexus. Players mount drakes to navigate between ring segments while battling Malygos's forces. The void stretches below, arcane energy crackles between platforms, and the vertigo is real. A dungeon that feels like flying through a magical storm at the edge of reality.""",

    595: """Culling of Stratholme: A Caverns of Time instance set during Arthas's fateful purge of the plagued city. The streets of Stratholme are intact but doomed - citizens transform into undead as you watch, and Arthas grimly orders their deaths before the change. The dungeon is uniquely disturbing because you are helping commit the atrocity that begins Arthas's fall. History's darkest moment, relived.""",

    599: """Halls of Stone: A titan facility in the Storm Peaks, part of Ulduar's vast complex. Stone corridors of geometric perfection house malfunctioning titan constructs, iron dwarves, and ancient defense systems. The Tribunal of Ages holds records of creation itself. The dungeon feels scholarly and ancient - a museum where the exhibits fight back and the history stored here could shatter civilizations.""",

    600: """Drak'Tharon Keep: A Scourge-infested troll fortress on the border of Grizzly Hills and Zul'Drak. The Scourge has raised the troll dead and corrupted their dinosaur beasts, creating an unholy fusion of troll culture and necromantic power. Skeletal raptors, zombie trolls, and the lich Novos the Summoner fill the decaying halls. Troll architecture crumbling under the weight of undeath.""",

    601: """Azjol-Nerub: The ruined nerubian kingdom beneath Northrend, a web-choked vertical descent through the spider empire. Nerubian architecture of silk and chitin stretches across vast underground chasms. Undead nerubians serve the Scourge while the living fight desperately. The dungeon drops you deeper and deeper through collapsing floors - claustrophobic, alien, and crawling with things that should not exist.""",

    602: """Halls of Lightning: A titan forge complex in Ulduar, crackling with electrical energy. Iron dwarves, storm giants, and runic constructs guard corridors of gleaming metal and arcing lightning. Loken, the corrupted titan keeper, waits in the deepest chamber. Every surface hums with power, sparks dance across the walls, and the thunder of the forge is constant and deafening.""",

    604: """Gundrak: A Drakkari troll temple in Zul'Drak, where the trolls sacrifice their own animal gods to fuel their war against the Scourge. Altars run with divine blood as serpent, mammoth, and rhino spirits are consumed. The temple is massive and primal - carved stone, ritual pools, and the desperate energy of a dying civilization burning its own gods for survival.""",

    608: """Violet Hold: A magical prison beneath Dalaran, where the Kirin Tor contains the most dangerous creatures in Northrend. Azure Dragonflight agents assault the prison from portals, releasing inmates in waves. The architecture is elegant Dalaran purple and silver, but the inmates are nightmarish. A tower defense scenario in a wizard's dungeon - arcane wards strain against chaos.""",

    619: """Ahn'kahet: The Old Kingdom: The deepest reaches of Azjol-Nerub, where Faceless Ones serve the old god Yogg-Saron. The architecture shifts from nerubian to something far older and more alien - organic walls pulse, reality warps, and insanity effects assault the mind. Forgotten ones, spell flingers, and the herald Volazj lurk in chambers that defy geometry. The most disturbing dungeon in Northrend.""",

    632: """Forge of Souls: The first of three Icecrown Citadel dungeons, a massive soul-grinding engine where the Lich King processes the dead. Rivers of tortured souls flow through iron machinery, spectral smiths hammer at anvils of suffering, and the Devourer of Souls guards the forge. The screaming never stops. An industrial nightmare powered by eternal torment.""",

    650: """Trial of the Champion: A grand tournament arena beneath the Argent Coliseum in Icecrown, where champions of the Alliance and Horde prove their worth. Mounted jousting, champion duels, and a final ambush by the Black Knight play out on the tournament grounds. The atmosphere is festive and competitive until the undead crash the party. Pageantry and spectacle with a dark twist.""",

    658: """Pit of Saron: A brutal slave mine in Icecrown where Scourge forces work prisoners to death extracting saronite ore. The pit is open to the frozen sky, with massive chains, mining platforms, and saronite deposits everywhere. Forgemaster Garfrost hurls boulders while Tyrannus patrols on his frostbrood drake overhead. Hopelessness and cruelty distilled into frozen stone and dark metal.""",

    668: """Halls of Reflection: The haunted Frozen Halls of Icecrown Citadel, where echoes of Frostmourne's victims linger around the blade's chamber. The Lich King himself pursues you through collapsing corridors as waves of ghosts attack. The halls are pristine ice and dark saronite, and the terror is real - you cannot fight him, only run. The most narratively intense dungeon in the game, a desperate flight from inevitable doom.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: The floating necropolis of the arch-lich Kel'Thuzad, hovering over Dragonblight. Four wings of themed horrors - the Arachnid Quarter of giant spiders, the Plague Quarter of disease and abominations, the Military Quarter of death knight commanders, and the Construct Quarter of flesh golems. Gothic architecture of dark stone and green slime, with the cold precision of undead military organization. The Scourge's masterwork of death.""",

    603: """Ulduar: A titan city-prison in the Storm Peaks, the grandest raid in Northrend. Massive halls of gleaming metal and stone house the corrupted titan keepers and their servants, with the old god Yogg-Saron imprisoned in the deepest vault. The scale is staggering - vehicle battles at the gates, an observatory open to the cosmos, gardens of unearthly beauty, and a descent into madness itself. Ancient, magnificent, and terrifying.""",

    615: """Obsidian Sanctum: A volcanic chamber beneath Wyrmrest Temple where Sartharion guards twilight dragon eggs. Lava rivers divide the obsidian platforms, and three twilight drake lieutenants patrol their own islands. The chamber glows orange and red, heat shimmers distort the air, and the black dragonflight's betrayal is laid bare. A straightforward arena of fire and scale.""",

    616: """Eye of Eternity: Malygos's personal sanctum at the apex of the Nexus above Coldarra, a platform suspended in raw ley energy. There is no ground, no walls - only a disc of magical force over a void of swirling blue and violet arcana. The Spell-Weaver attacks with the full power of the Blue Dragonflight. The raid feels otherworldly - fighting a dragon aspect in the heart of Azeroth's arcane storm.""",

    624: """Vault of Archavon: A titan vault beneath Wintergrasp Fortress, accessible only to the faction controlling the zone. Stone giants and elemental constructs guard the chambers in a straightforward series of boss encounters. The architecture is utilitarian titan design - functional, massive, and unadorned. A reward for PvP victory, quick and brutal.""",

    631: """Icecrown Citadel: The Lich King's throne, the culmination of Wrath of the Lich King. A towering fortress of saronite and ice rising from the heart of Icecrown. Every wing escalates the horror - from the Lower Spire's undead armies, through the Plagueworks, Crimson Hall, and Frostwing Halls, to the Frozen Throne itself. The architecture is oppressive, beautiful in its cruelty, and designed to break hope. This is the end.""",

    649: """Trial of the Crusader: The Argent Coliseum in Icecrown, a tournament arena that descends into the earth when the floor collapses into an underground nerubian cavern. The upper level is bright banners and cheering crowds; the lower level is chitinous horror and Anub'arak's domain. The contrast between festive competition above and ancient terror below defines the entire experience.""",

    724: """Ruby Sanctum: A chamber beneath Wyrmrest Temple where the twilight dragonflight has invaded the red dragons' sanctum. Halion, the twilight destroyer, phases between the physical realm and the shadow realm. The chamber shifts between warm ruby light and cold purple shadow. The last raid before the Cataclysm - a brief, ominous warning of the destruction to come.""",
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
# 50% plain, 15% quest, 12% loot, 8% quest+reward, 10% trade, 5% spell
MSG_TYPE_PLAIN = 50
MSG_TYPE_QUEST = 65        # 15% chance (51-65)
MSG_TYPE_LOOT = 77         # 12% chance (66-77)
MSG_TYPE_QUEST_REWARD = 85   # 8% chance (78-85)
MSG_TYPE_TRADE = 95          # 10% chance (86-95)
MSG_TYPE_SPELL = 100         # 5% chance (96-100)

# =============================================================================
# DYNAMIC PROMPT BUILDING - Tone, Mood, Twist, Category, Length constants
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
    "pleasantly surprised",
    "thoughtful and quiet",
    "gently amused",
    "cautiously optimistic",
    "deadpan and dry",
    "nostalgic about old content",
    "easygoing and unhurried",
    "chill but opinionated",
    "genuinely impressed",
    "sleepy and unfocused",
    "warm and conversational",
]

# Mood variations - the emotional angle of the message
MOODS = [
    "questioning",
    "complaining",
    "happy",
    "disappointed",
    "joking around",
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
    "Use a single word or two-word reaction",
    "Ask a rhetorical question",
    "Answer your own question",
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

# Message categories - abstract directions that force original content
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

# =============================================================================
# ROLEPLAY MODE CONSTANTS (parallel to normal constants above)
# =============================================================================
RP_TONES = [
    "relaxed but in-character",
    "tired from traveling",
    "quietly observant",
    "cautiously optimistic",
    "matter-of-fact",
    "friendly and approachable",
    "a little grumpy",
    "confident",
    "calm and easygoing",
    "dry and understated",
    "wary but polite",
    "amused by something",
    "distracted by surroundings",
    "pragmatic and no-nonsense",
    "homesick",
    "pleasantly surprised",
    "stubbornly opinionated",
    "quietly annoyed",
    "casually curious",
    "grateful and warm",
]

RP_MOODS = [
    "wary",
    "calm",
    "curious",
    "amused",
    "tired",
    "hopeful",
    "grateful",
    "suspicious",
    "nostalgic",
    "restless",
    "gruff",
    "friendly",
    "irritated",
    "impressed",
    "distracted",
    "cautious",
    "content",
    "dry humor",
    "matter-of-fact",
    "thoughtful",
]

RP_CREATIVE_TWISTS = [
    "Use a casual saying from your culture",
    "Mention something from your past briefly",
    "React to a sound or smell nearby",
    "Mutter something half to yourself",
    "Use a mild oath from your race",
    "Make a dry or sarcastic observation",
    "Notice something small in the environment",
    "Complain about something minor",
    "Give a piece of unsolicited advice",
    "Change the subject abruptly",
    "Shrug something off casually",
    "Reference food, drink, or rest",
    "Start to say something then think better of it",
    "Ask a rhetorical question",
]

RP_MESSAGE_CATEGORIES = [
    # Observations
    "commenting on the area around you",
    "noticing something about the wildlife or creatures",
    "remarking on the weather or scenery",
    "observing other travelers",
    "noting something odd or out of place",
    # Reactions
    "reacting to a noise nearby",
    "mentioning a fight you just had",
    "being relieved about something",
    "bracing for trouble ahead",
    "complaining about the road or terrain",
    # Social
    "greeting someone casually",
    "giving a warning or tip",
    "sharing a bit of news",
    "asking about what lies ahead",
    "thanking someone nearby",
    # Everyday
    "thinking about food or drink",
    "commenting on being tired or sore",
    "mentioning needing supplies",
    "talking about where you're headed next",
    "wondering how far the next town is",
    # World and lore
    "mentioning something you heard about this place",
    "referencing your homeland briefly",
    "wondering about some old ruins",
    "recalling a story or rumor",
    "commenting on the local people or culture",
    "tales of distant lands or adventures",
    "story heard in an inn or from a traveler",
    "mystical story or legend related to the area",
    # Atmospheric
    "noticing the weather changing",
    "commenting on the time of day",
    "listening to the sounds around you",
    "noticing a smell on the wind",
    "feeling uneasy about something nearby",
    # Personal
    "thinking about home",
    "remembering an old friend",
    "admitting you're not sure about something",
    "enjoying a quiet moment",
    "grumbling about something minor",
]

RP_LENGTH_HINTS = [
    "short and casual (5-10 words)",
    "a normal sentence (10-16 words)",
    "a couple of short thoughts (12-18 words)",
    "a bit longer if it feels natural (16-24 words)",
]

# =============================================================================
# LLM DEFAULT MODELS
# =============================================================================
# Default model for each provider when none is
# configured. Used by quick_llm_analyze() auto-
# selection and as config fallbacks.
DEFAULT_ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001'
DEFAULT_OPENAI_MODEL = 'gpt-4o-mini'

# =============================================================================
# EVENT DESCRIPTIONS
# =============================================================================
# Event type to human-readable description
EVENT_DESCRIPTIONS = {
    'weather_change': 'weather changing',
    'holiday_start': 'a holiday beginning',
    'holiday_end': 'a holiday ending',
    'minor_event': 'a game event happening',
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

# Transport cooldown constant (seconds)
ZONE_TRANSPORT_COOLDOWN_SECONDS = 300

# =============================================================================
# EMOTE SYSTEM - Emotes bots can play alongside messages
# =============================================================================
# Curated list of emotes that map to WoW
# EMOTE_ONESHOT_* animations
EMOTE_LIST = [
    'talk', 'bow', 'wave', 'cheer', 'exclamation',
    'question', 'eat', 'laugh', 'rude', 'roar',
    'kneel', 'kiss', 'cry', 'chicken', 'beg',
    'applaud', 'shout', 'flex', 'shy', 'point',
    'salute', 'dance', 'yes', 'no', 'none',
]

EMOTE_LIST_STR = ', '.join(EMOTE_LIST)

# Keyword -> emote mapping for statement post-processing
# (used when LLM output is plain text, not JSON)
EMOTE_KEYWORDS = {
    # Positive / greeting
    'hello': 'wave', 'hi ': 'wave', 'hey ': 'wave',
    'greetings': 'wave', 'farewell': 'wave',
    'goodbye': 'wave', 'safe travels': 'bow',
    'welcome': 'wave', 'good to see': 'wave',
    # Humor / joy
    'lol': 'laugh', 'haha': 'laugh', 'lmao': 'laugh',
    'rofl': 'laugh', 'funny': 'laugh',
    'hilarious': 'laugh', 'ridiculous': 'laugh',
    'laugh': 'laugh', 'chuckle': 'laugh',
    'amuse': 'laugh', 'joke': 'laugh',
    # Excitement
    'nice': 'cheer', 'awesome': 'cheer',
    'amazing': 'cheer', 'grats': 'cheer',
    'congrats': 'cheer', 'woo': 'cheer',
    'hell yeah': 'cheer', 'let\'s go': 'cheer',
    'fantastic': 'cheer', 'brilliant': 'cheer',
    'victory': 'cheer', 'won': 'cheer',
    'level': 'cheer', 'well fought': 'cheer',
    # Sadness / frustration
    'rip': 'cry', 'tragic': 'cry',
    'terrible': 'cry', 'awful': 'cry',
    'lost': 'cry', 'fallen': 'cry',
    'mourn': 'cry', 'grief': 'cry',
    'sad': 'cry', 'miss ': 'cry',
    # Respect / admiration
    'thank': 'bow', 'respect': 'bow',
    'honor': 'bow', 'well met': 'bow',
    'grateful': 'bow', 'appreciate': 'bow',
    'impressive': 'applaud', 'well done': 'applaud',
    'bravo': 'applaud', 'nice work': 'applaud',
    'good job': 'applaud', 'great work': 'applaud',
    'skilled': 'applaud', 'masterful': 'applaud',
    # Combat / intensity
    'charge': 'roar', 'attack': 'roar',
    'for the': 'roar', 'lok\'tar': 'roar',
    'glory': 'roar', 'battle cry': 'roar',
    'fight': 'shout', 'watch out': 'shout',
    'incoming': 'shout', 'behind you': 'shout',
    'careful': 'shout', 'look out': 'shout',
    'run': 'shout', 'get back': 'shout',
    'help': 'shout', 'danger': 'shout',
    'pull': 'shout', 'adds': 'shout',
    # Questions
    'where': 'question', 'how do': 'question',
    'anyone know': 'question', 'what is': 'question',
    '?': 'question',
    'wonder': 'question', 'curious': 'question',
    # Surprise
    'what the': 'exclamation', 'holy': 'exclamation',
    'whoa': 'exclamation', 'wow ': 'exclamation',
    'by the': 'exclamation', 'never seen': 'exclamation',
    'unbelievable': 'exclamation',
    # Pride
    'check this': 'flex', 'look at': 'flex',
    'finally got': 'flex', 'strong': 'flex',
    'nothing can': 'flex', 'easy': 'flex',
    # Directions
    'over there': 'point', 'that way': 'point',
    'look over': 'point', 'see that': 'point',
    'ahead': 'point', 'notice': 'point',
    # Shy / embarrassment
    'oops': 'shy', 'sorry': 'shy',
    'my bad': 'shy', 'awkward': 'shy',
    'mistake': 'shy', 'didn\'t mean': 'shy',
    # Formal
    'hail': 'salute', 'commander': 'salute',
    'sir': 'salute', 'reporting': 'salute',
    'soldier': 'salute', 'officer': 'salute',
    # Dance
    'dance': 'dance', 'party': 'dance',
    'celebrate': 'dance', 'festival': 'dance',
    # Prayer / devotion
    'pray': 'kneel', 'light guide': 'kneel',
    'ancestors': 'kneel', 'earth mother': 'kneel',
    'elune': 'kneel', 'bless': 'kneel',
    'spirit': 'kneel', 'may the': 'kneel',
    'rest in peace': 'kneel', 'fallen comrade': 'kneel',
    # Eating / drinking / resting
    'drink': 'eat', 'eat': 'eat', 'hungry': 'eat',
    'thirsty': 'eat', 'mana break': 'eat',
    'need to rest': 'eat', 'sit down': 'eat',
    # Rude / dismissive
    'pathetic': 'rude', 'fool': 'rude',
    'waste of': 'rude', 'disgrace': 'rude',
    'shut up': 'rude', 'useless': 'rude',
    # Agreement / disagreement
    'agree': 'yes', 'right': 'yes',
    'exactly': 'yes', 'indeed': 'yes',
    'absolutely': 'yes', 'of course': 'yes',
    'no way': 'no', 'refuse': 'no',
    'never': 'no', 'won\'t': 'no',
    'don\'t think so': 'no', 'doubt': 'no',
    # Begging / desperation
    'please': 'beg', 'mercy': 'beg',
    'desperate': 'beg', 'need help': 'beg',
    'save me': 'beg', 'i beg': 'beg',
    # Taunting
    'coward': 'chicken', 'scared': 'chicken',
    'afraid': 'chicken', 'chicken': 'chicken',
    'running away': 'chicken',
}
