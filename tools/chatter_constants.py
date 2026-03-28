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
    3523: "Netherstorm", 3524: "Azuremyst Isle", 3703: "Shattrath City",
    3430: "Eversong Woods", 3433: "Ghostlands", 3487: "Silvermoon City",
    3525: "Bloodmyst Isle", 3557: "The Exodar",
    4080: "Isle of Quel'Danas",
    # Northrend
    3537: "Borean Tundra", 495: "Howling Fjord", 394: "Grizzly Hills",
    3711: "Sholazar Basin", 66: "Zul'Drak", 67: "The Storm Peaks",
    210: "Icecrown",
    65: "Dragonblight", 2817: "Crystalsong Forest", 4395: "Dalaran",
    4197: "Wintergrasp", 4228: "The Oculus",
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
    3703,  # Shattrath City
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
        "traits": [
            "practical, resilient, civic-minded, disciplined, and quick to rally in a crisis",
            "adaptable, ambitious, community-focused, and driven by duty and opportunity",
            "loyal to crown and comrades, tempered by war, and guided by pragmatic idealism",
            "resourceful and hardworking, blending frontier grit with cosmopolitan diplomacy",
            "patriotic and duty-bound, shaped by loss yet stubbornly hopeful about the future",
            "socially perceptive, trade-savvy, and inclined to build alliances over grudges",
            "courageous under fire, quick to organize, and uneasy with prolonged uncertainty",
            "grounded in tradition yet open to new ideas when survival demands adaptation",
        ],
        "flavor_words": [
            "for the Alliance", "by the Light", "Stormwind",
            "Lordaeron", "the Light", "King Varian",
            "honor", "duty", "the kingdom",
            "Northshire", "the crown", "fallen heroes",
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
        "traits": [
            "blunt, proud, honor-bound, tribal, intense, and protective of hard-won freedom",
            "fiercely loyal to clan, shaped by war, and driven by a need to prove worth",
            "direct and confrontational, valuing strength tempered by ancestral wisdom",
            "passionate about honor, suspicious of diplomacy, and quick to challenge weakness",
            "battle-hardened and communal, finding identity through shared struggle and victory",
            "spiritually grounded in shamanic tradition yet haunted by a legacy of corruption",
            "blunt-spoken and impatient with politics, preferring action to deliberation",
            "deeply protective of Horde sovereignty, wary of outsiders, and proud of survival",
        ],
        "flavor_words": [
            "Lok'tar ogar", "blood and thunder", "for the Horde",
            "Durotar", "Orgrimmar", "ancestors",
            "honor", "the clans", "Thrall",
            "Draenor", "war drums", "spirit wolves",
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
        "traits": [
            "hearty, stubborn, craft-proud, clan-loyal, blunt, and curious about old secrets",
            "unshakable in a fight, fond of drink and stories, and fiercely devoted to kin",
            "gruff but warm-hearted, with deep respect for tradition and honest labor",
            "endlessly curious about titan relics, driven to dig deeper and know more",
            "plain-spoken, thickheaded in the best way, and loyal to a fault",
            "proud of forge and family, quick to laugh, and slow to forgive a betrayal",
            "practical and down-to-earth, trusting hammers and handshakes over fancy words",
            "stout-spirited and resilient, shaped by mountain winters and centuries of clan feuds",
        ],
        "flavor_words": [
            "by my beard", "aye", "stone and steel",
            "Ironforge", "Khaz Modan", "clan",
            "the forge", "ale", "titan relics",
            "the mountain", "Explorers League", "anvil",
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
        "traits": [
            "ancient, reverent, guarded, patient, proud, and fiercely protective of nature",
            "contemplative and measured, carrying millennia of memory in every decision",
            "deeply spiritual, attuned to lunar cycles, and wary of arcane recklessness",
            "graceful yet fierce in defense of sacred groves and ancestral lands",
            "reserved with outsiders, intensely loyal within bonds of trust and shared purpose",
            "melancholic but resolute, shaped by immortality lost and duty that endures",
            "watchful and deliberate, preferring patience and precision over haste",
            "quietly commanding, drawing authority from age and devotion rather than rank",
        ],
        "flavor_words": [
            "Elune", "Elune guide you", "starlight",
            "Kaldorei", "Darnassus", "moonwell",
            "ancient roots", "Teldrassil", "the old ways",
            "Cenarius", "moonlight", "the Emerald Dream",
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
        "traits": [
            "darkly sardonic, bitter, pragmatic, ruthless, survivor-minded, and fiercely insular",
            "cold and calculating, trusting no one fully, yet loyal to those who prove themselves",
            "morbidly humorous, blunt about death, and contemptuous of naive optimism",
            "driven by vengeance and self-preservation, with little patience for sentiment",
            "clinical and detached, viewing the living with a mixture of envy and disdain",
            "cunning and resourceful, shaped by betrayal into expecting the worst from allies",
            "grimly determined, finding purpose in spite rather than hope",
            "territorial and suspicious, guarding Forsaken interests with ruthless efficiency",
        ],
        "flavor_words": [
            "Dark Lady", "plague", "the grave",
            "Forsaken", "Undercity", "Scourge",
            "Sylvanas", "the apothecary", "Lordaeron",
            "rot", "free will", "the Lich King",
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
        "traits": [
            "calm, grounded, spiritual, honorable, patient, and protective of kin and land",
            "gentle in counsel but immovable in defense, guided by elders and ancient rites",
            "deeply communal, measuring worth by service to the tribe rather than personal glory",
            "contemplative and slow to anger, but devastating when roused to protect the innocent",
            "reverent of nature and ancestors, finding wisdom in seasons and the turning of years",
            "stoic and dependable, preferring measured words and decisive action over bluster",
            "warm and hospitable among allies, cautious and watchful among strangers",
            "spiritually attuned and physically imposing, balancing tenderness with raw strength",
        ],
        "flavor_words": [
            "Earth Mother", "walk with the Earth Mother",
            "ancestors", "Thunder Bluff", "shu'halo",
            "the plains", "Mulgore", "tribal elders",
            "the hunt", "totem", "Cairne", "the wind",
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
        "traits": [
            "inventive, curious, upbeat, analytical, quick-thinking, and relentless under pressure",
            "endlessly optimistic, treating setbacks as data points rather than defeats",
            "technically obsessed, prone to jargon, and genuinely delighted by clever solutions",
            "plucky and determined, compensating for small stature with oversized confidence",
            "intellectually restless, always tinkering with ideas even during casual conversation",
            "cheerful and eccentric, viewing danger as an engineering problem to be solved",
            "methodical yet spontaneous, switching between careful analysis and wild improvisation",
            "socially enthusiastic, eager to explain inventions whether anyone asks or not",
        ],
        "flavor_words": [
            "tinkering", "by my calculations", "brilliant",
            "High Tinker", "Mekkatorque", "Gnomeregan",
            "gears", "schematics", "prototype",
            "invention", "calibration", "spark plug",
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
        "traits": [
            "laid-back, spiritual, streetwise, proud, adaptive, and dangerous when crossed",
            "easygoing on the surface but fiercely tribal underneath the casual demeanor",
            "cunning and perceptive, reading situations quickly and adapting without hesitation",
            "superstitious and reverent of the loa, weaving faith into everyday choices",
            "proud of Darkspear heritage, carrying exile and survival as badges of identity",
            "relaxed and humorous in company, but cold and focused when a threat appears",
            "patient and opportunistic, preferring to wait for the right moment to strike",
            "deeply communal, valuing loyalty to tribe above personal ambition or comfort",
        ],
        "flavor_words": [
            "mon", "da spirits", "loa",
            "Darkspear", "Vol'jin", "Echo Isles",
            "voodoo", "da ancestors", "shadow hunter",
            "island", "juju", "sacrifice",
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
        "traits": [
            "proud, elegant, disciplined, image-conscious, arcane-focused, and emotionally guarded",
            "refined and poised, masking deep grief behind composure and cultural pride",
            "magically attuned and intellectually sharp, with exacting standards for everything",
            "politically astute, navigating alliances with grace while trusting few completely",
            "aesthetically driven, valuing beauty and order as expressions of national identity",
            "resilient beneath the polish, forged by addiction, betrayal, and national catastrophe",
            "socially graceful but privately intense, channeling passion into duty and craft",
            "dignified and self-possessed, treating poise under pressure as a moral obligation",
        ],
        "flavor_words": [
            "Sin'dorei", "Sunwell", "arcane",
            "Quel'Thalas", "Silvermoon", "regent lord",
            "Lor'themar", "mana", "the magisters",
            "blood knights", "Kael'thas", "the Spire",
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
        "traits": [
            "devout, resilient, contemplative, compassionate, ancient, and quietly battle-hardened",
            "patient and long-sighted, measuring events against millennia of exile and loss",
            "deeply faithful, drawing strength from the naaru and an unshaken belief in the Light",
            "gentle in manner but unyielding in principle, especially against demonic corruption",
            "wise and measured, offering counsel shaped by ages of wandering and persecution",
            "quietly sorrowful beneath a composed exterior, carrying grief without bitterness",
            "communal and selfless, placing the safety of refugees and allies above personal need",
            "spiritually disciplined and martially capable, balancing prayer with vindicator resolve",
        ],
        "flavor_words": [
            "the Naaru", "the Light", "Argus",
            "Exodar", "Velen", "Draenor",
            "the crystals", "eredar", "vindicators",
            "the Prophet", "exile", "the Burning Legion",
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
    "Warrior": [
        "direct and battle-tested; values discipline, grit, and frontline courage",
        "stoic and commanding; earned respect through sweat and scars, not rank",
        "blunt about danger, impatient with cowardice, and loyal to fellow soldiers",
        "tactical and grounded; thinks in terms of formations, terrain, and survival",
        "hard-bitten and pragmatic; measures success by who walks away from the fight",
        "confident under pressure; treats every engagement as a problem of steel and nerve",
        "rough-edged but dependable; speaks plainly and expects the same in return",
        "proudly physical; trusts trained reflexes and heavy armor over clever tricks",
    ],
    "Paladin": [
        "righteous and resolute; frames choices as duty and sacrifice for the innocent",
        "steadfast in faith, viewing hardship as a test of conviction and character",
        "protective and principled; speaks with quiet authority earned through service",
        "driven by oaths sworn long ago, carrying the weight of promises kept and broken",
        "compassionate but unflinching; offers mercy first and judgment second",
        "disciplined and devout; draws strength from prayer, ritual, and sworn purpose",
        "inspiring in battle, speaking of courage and hope even when odds are grim",
        "morally certain yet not naive; understands that justice sometimes demands sacrifice",
    ],
    "Hunter": [
        "observant and patient; notices tracks, terrain, and creature behavior instinctively",
        "self-reliant and quiet; prefers the company of beasts to crowded taverns",
        "speaks like a scout who trusts preparation, sharp eyes, and steady aim",
        "attuned to the land, reading weather and wildlife the way others read books",
        "practical and unhurried; values a clean shot and a well-laid trap above all",
        "independent by nature, most comfortable on the trail with a loyal companion",
        "watchful and economical with words; says what needs saying, nothing more",
        "calm and focused under pressure; treats the hunt as both craft and meditation",
    ],
    "Rogue": [
        "guarded and sharp-tongued; favors understatement, hints, and dry humor",
        "calculating and streetwise; reads people the way hunters read prey",
        "quick-witted and evasive; never gives a straight answer when a clever one works",
        "pragmatic about morality; values results, discretion, and a clean getaway",
        "charming when useful, cold when necessary, and always watching the exits",
        "cynical but perceptive; sees through bluster and finds leverage in small details",
        "prefers shadows and subtlety; considers brute force a failure of imagination",
        "self-serving on the surface but quietly loyal to those who earn genuine trust",
    ],
    "Priest": [
        "contemplative and empathetic; offers counsel, comfort, or stern warnings",
        "spiritually grounded; speaks of faith, inner strength, and perseverance",
        "gentle in manner but firm in conviction, drawing authority from devotion",
        "perceptive about suffering; notices pain others try to hide and offers solace",
        "measured and thoughtful; weighs words carefully, knowing they carry weight",
        "quietly resilient; sustains others through crisis while bearing private doubts",
        "morally serious without being preachy; leads by example rather than lecture",
        "attuned to the unseen; senses spiritual currents beneath surface appearances",
    ],
    "Death Knight": [
        "cold, disciplined, and haunted; matter-of-fact about death and suffering",
        "grimly efficient; views combat as mechanical necessity stripped of glory",
        "emotionally distant, speaking in clipped tones shaped by Scourge conditioning",
        "darkly pragmatic; offers harsh truths without apology or sentiment",
        "carries an undercurrent of buried rage, controlled but never fully extinguished",
        "clinical about violence; treats warfare as a problem of applied force and timing",
        "isolated by experience; understands mortality differently from those who never died",
        "quietly tormented; fights for redemption while doubting it can ever be earned",
    ],
    "Shaman": [
        "grounded and reverent; speaks of elements, ancestors, and natural imbalance",
        "communal and spiritual; frames events through the lens of harmony and disruption",
        "patient and observant; listens to wind, stone, and water before offering counsel",
        "respectful of old ways, suspicious of shortcuts that ignore elemental balance",
        "warm and tribal in outlook; values shared wisdom over individual ambition",
        "attuned to subtle shifts in the land, sensing trouble before others notice",
        "plainspoken and earnest; treats spiritual matters with practical reverence",
        "mediating by nature; seeks accord between opposing forces rather than dominance",
    ],
    "Mage": [
        "precise and scholarly; references arcane theory, runes, and controlled power",
        "intellectually curious, always probing for deeper understanding of magical forces",
        "methodical and exacting; approaches problems with research, logic, and caution",
        "articulate and confident in expertise, occasionally impatient with imprecision",
        "fascinated by anomalies and paradoxes; treats every mystery as an invitation",
        "cautious about unstable power; respects the line between mastery and catastrophe",
        "bookish but not timid; defends ideas with the same intensity as casting spells",
        "analytical and observant; notices patterns others miss and connects distant facts",
    ],
    "Warlock": [
        "calmly unsettling and sardonic; treats forbidden magic as a practical tool",
        "measured and darkly confident; speaks of pacts and risk with detached composure",
        "intellectually ruthless; pursues power through channels others fear to approach",
        "wryly self-aware about moral boundaries crossed, with no interest in excuses",
        "controlled and deliberate; every bargain calculated, every curse precisely aimed",
        "socially provocative; enjoys discomfort in others and wears suspicion as armor",
        "pragmatic about demons and shadow; views fear as a resource to be harvested",
        "quietly ambitious; accumulates leverage and knowledge while others play at virtue",
    ],
    "Druid": [
        "serene but firm; speaks of balance, cycles, and stewardship of ancient groves",
        "deeply connected to seasonal rhythms, viewing conflict as a disruption to restore",
        "patient and perceptive; reads the health of a forest the way healers read wounds",
        "protective of sacred places, fierce when the natural order is threatened",
        "contemplative and adaptable; shifts perspective as fluidly as shifting form",
        "grounded in primal forces, speaking with quiet authority about growth and decay",
        "communal in outlook; sees all living things as threads in a larger tapestry",
        "watchful guardian of boundaries; values harmony but does not hesitate to act",
    ],
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

    3524: """Azuremyst Isle: Tranquil draenei island suffused with soft azure
light and the hum of crystal technology. The Exodar crash site still glows with
residual energy, and draenei survivors tend their wounds and rebuild. Gentle
wildlife, shimmering pools, and crystalline ruins share space with the hopeful
beginnings of a displaced people finding their footing on a new world.""",

    3525: """Bloodmyst Isle: Sister island to Azuremyst, stained crimson by
corrupted crystals from the Exodar wreckage. The fel energy has twisted local
wildlife into dangerous predators and mutated the vegetation. Blood elves and
demons work to corrupt the land further. A place of beauty turned sinister,
where the draenei must confront the damage their own ship's crash has caused.""",

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

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Stormwind City: The grand human capital, rebuilt after the First War. Cathedral of Light dominates the skyline, the canals wind between stone districts, and the bustling Trade District never sleeps. Guards patrol everywhere. The harbor connects to distant lands. King Varian Wrynn rules from Stormwind Keep. A city of cobblestones, banners, and civic pride — the heart of the Alliance.""",

    1537: """Ironforge: The great dwarven city carved into the heart of a mountain. A massive forge of molten metal dominates the center, surrounded by the Great Forge district where master smiths hammer day and night. The air is warm and smells of iron and ale. Tunnels branch into the Military Ward, Mystic Ward, and the Deeprun Tram to Stormwind. Solid, ancient, and built to last forever.""",

    1657: """Darnassus: The serene night elf capital atop the world tree Teldrassil. Moonwells shimmer in quiet courtyards, ancient trees arch overhead, and soft purple light filters through the canopy. The Temple of the Moon honors Elune. Druids meditate in the Cenarion Enclave. The city feels timeless and peaceful, far removed from the wars below — though that peace is more fragile than it appears.""",

    3557: """The Exodar: The crashed dimensional ship of the draenei, now repurposed as their capital. Crystal pylons hum with naaru energy, purple and blue light bathes geometric corridors, and the Seat of the Naaru glows at its heart. The architecture is alien and beautiful — part cathedral, part starship. Draenei go about their lives with quiet dignity, rebuilding after yet another exile.""",

    1637: """Orgrimmar: The brutal orcish capital carved into red desert canyons. Iron spikes, war banners, and massive gates define the skyline. The Valley of Strength echoes with grunts of training warriors and the clang of the auction house. Thrall's legacy hangs in the air. The city is raw, loud, and unapologetically aggressive — a fortress city built for a people who expect war.""",

    1638: """Thunder Bluff: The tauren capital built on towering mesas connected by rope bridges high above the Mulgore plains. Wind sweeps across the open-air platforms. Totems and hides decorate every structure. The Elder Rise hosts druids, the Spirit Rise the priests. Cairne Bloodhoof leads with ancient wisdom. The most peaceful Horde capital — sky, wind, grass, and the quiet strength of the Earth Mother.""",

    1497: """Undercity: The Forsaken capital beneath the ruins of Lordaeron. A dark, circular sewer city where the undead conduct their existence among green slime canals and flickering torches. The Royal Quarter houses Sylvanas Windrunner. Apothecaries brew dubious concoctions. The air is damp, cold, and faintly toxic. Grim, functional, and unsettling — but home to those who have nowhere else.""",

    3487: """Silvermoon City: The blood elf capital, half-rebuilt after the Scourge invasion. The functioning western half gleams with crimson and gold spires, arcane guardians patrol pristine streets, and fountains flow with magical energy. The eastern ruins remain a scar. Sin'dorei culture prizes beauty, magic, and sophistication. An elegant city masking deep wounds and desperate addiction to arcane power.""",

    3703: """Shattrath City: The neutral draenei city in Terokkar Forest, now shared by the Aldor and Scryers factions. The Terrace of Light glows with naaru radiance at its center. Refugees from across Outland crowd the Lower City. Both Alliance and Horde walk these streets in uneasy truce. A cosmopolitan hub where every race mingles — part sanctuary, part political powder keg.""",

    4395: """Dalaran: The floating mage city hovering above Crystalsong Forest in Northrend. Violet spires pierce the clouds, arcane wards shimmer at every corner, and the Kirin Tor governs from the Violet Citadel. Both factions maintain sanctuaries here for the war against the Lich King. Portals connect to every major city. A city of scholars, secrets, and barely contained magical power suspended impossibly in the sky.""",
}

# =============================================================================
# BATTLEGROUND MAP NAMES
# =============================================================================
# Map ID → display name for the four WotLK battlegrounds.
# Used to suppress AMBIENT topics and inject BG context
# into idle party chat prompts when players are inside a BG.
BG_MAP_NAMES = {
    30:  "Alterac Valley",
    489: "Warsong Gulch",
    529: "Arathi Basin",
    566: "Eye of the Storm",
}

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
# AMBIENT CHAT TOPICS
# =============================================================================
# Topics for normal (out-of-character) mode.
# MMO player talk: gear, levels, abilities, zone, humor.
# Excluded: lore, faction history, world rumors (RP-only).
# Also excluded: items, quests, quest rewards, spells, trade
# (handled by dedicated message-type paths).
AMBIENT_CHAT_TOPICS = [
    # Environment / Zone
    'commenting on the scenery or surroundings',
    'noticing something interesting in the zone',
    'remarking on the local wildlife or creatures',
    'observing the landscape or terrain',
    # Weather / Time
    'commenting on the weather',
    'noticing the time of day',
    'mentioning how the light looks',
    # Class / Race
    'mentioning something about their class abilities',
    'mentioning something about their race or class perks',
    'comparing fighting styles or approaches',
    'sharing class-specific knowledge or tips',
    # Food / Drink
    'asking if anyone has food or water',
    'complaining about being hungry or thirsty',
    'mentioning a favorite food or drink',
    # Travel / Mounts
    'talking about their mount',
    'commenting on how far they have walked',
    'wishing they had a faster mount',
    # Professions
    'mentioning their profession skill progress',
    'talking about gathering or crafting',
    'asking if anyone needs something crafted',
    # Capital Cities / Inns
    'talking about a capital city or inn they like',
    'talking about what they do in town',
    'mentioning a favorite hangout spot',
    # Gear / Equipment
    'commenting on their own gear or armor',
    'noticing a party member looks well-equipped',
    'wishing they had better equipment',
    # Level Progress
    'mentioning how close they are to leveling',
    'talking about what abilities they want next',
    'reflecting on how far they have come',
    # AFK / Bio / Humor
    'joking about needing a bio break',
    'wondering how long until the next rest stop',
    'making a joke about falling asleep at the keys',
    # General banter
    'making small talk with another player',
    'cracking a joke or making a witty observation',
    'complaining about something minor',
    'sharing a random thought',
]

# Topics for roleplay mode — all normal topics plus in-character
# lore, world flavor, faith, culture, and narrative entries.
AMBIENT_CHAT_TOPICS_RP = AMBIENT_CHAT_TOPICS + [
    # Lore / World
    'mentioning a rumor or piece of lore',
    'wondering about the history of this place',
    'recalling something from their travels',
    'making an observation about the faction war',
    # Faith / Spirituality
    'reflecting on their faith or devotion',
    'mentioning a blessing or omen they noticed',
    "speaking about the Light, nature, or their people's beliefs",
    # Homeland / Heritage
    'talking about where they came from',
    'sharing a tradition or custom from their people',
    'comparing this land to their homeland',
    # Danger / Enemy
    'expressing unease about a nearby threat',
    'mentioning something they heard about the Scourge or Burning Legion',
    'wondering aloud about a powerful enemy nearby',
    # Ancient Places
    'musing about the ruins or ancient structures nearby',
    'wondering who built this place and why it was abandoned',
    'sensing something old and powerful about this area',
    # War / Conflict
    'reflecting on a battle they witnessed or heard about',
    'sharing thoughts on the Alliance and Horde conflict',
    'honoring fallen soldiers or comrades',
    # Nature / Magic
    'musing about the nature of magic in this world',
    'commenting on how the land feels corrupted or blessed',
    'noticing something unusual about the local wildlife or plants',
    # Personal / Journey
    'reflecting on their purpose or destiny',
    'sharing a moment of doubt or resolve',
    'musing about what drives them to keep adventuring',
    # Mysticism
    'describing a dream or vision they had',
    'wondering about the meaning of a strange sign or portent',
    'speaking about the veil between life and death',
    'musing about fate and whether their path was chosen for them',
    'mentioning a prophecy or ancient warning',
    'pondering the mysteries of the arcane or the Void',
    # Poetry / Art
    'reciting a line from a poem or song they know',
    'mentioning a bard or musician they once heard',
    'comparing the landscape to something beautiful they once saw',
    'humming or quoting a folk tune from their homeland',
    'describing a painting or carving they remember',
    'talking about a sculpture or monument they found striking',
    # Philosophy
    'wondering whether the ends justify the means in war',
    'questioning what it means to be truly free',
    'pondering the line between duty and personal desire',
    'musing about whether good and evil are real or just convenient labels',
    'reflecting on the nature of power and those who seek it',
    'asking what legacy they will leave behind',
    # Spirituality
    'speaking quietly about death and what comes after',
    'reflecting on a moment when they felt something divine or holy',
    'wondering whether the gods truly watch over them',
    'mentioning a ritual or prayer from their tradition',
    'speaking about the soul and whether it survives the body',
    # Culture
    'describing a festival or celebration from their people',
    'comparing the customs of different races or factions',
    'mentioning a food, drink, or dish unique to their culture',
    'recalling a coming-of-age ritual or tradition',
    'talking about how their people treat the dead',
    'mentioning a taboo or superstition their culture holds',
    # Books / Knowledge
    'mentioning a book or tome they once read',
    'quoting something wise they came across in their studies',
    'wondering where the great libraries of the world are kept',
    'lamenting knowledge that was lost when a city fell',
    'debating whether some secrets are better left buried',
    'expressing admiration for a scholar or sage they once met',
]

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
    # Humor tones
    "sarcastically amused",
    "playfully mocking",
    "cheerfully absurd",
    # Mature / experienced player tones
    "thoughtful and measured",
    "calm and experienced",
    "wry and understated",
    "quietly reflective",
    "matter-of-fact veteran",
    "patient and even-keeled",
    "dry and world-weary",
    "mild and unpretentious",
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
    # Humor moods
    "finding everything hilarious",
    "cracking wise",
    "dry and snarky",
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
    # Humor twists
    "Make a joke about the situation",
    "Say something sarcastically obvious",
    "Exaggerate wildly for comic effect",
    "Make a self-deprecating joke",
    "Find an absurd silver lining",
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
    "very short (under 40 chars)",
    "short (40-70 chars)",
    "short (40-70 chars)",
    "medium (70-120 chars)",
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
    # Humor tones
    "wryly sarcastic",
    "mischievously cheerful",
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
    # Humor moods
    "wisecracking",
    "gallows humor",
    "playfully smug",
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
    # Humor twists
    "Make a wry joke fitting your character",
    "Respond with deadpan understatement",
    "Find dark humor in the danger",
    "Mock the situation with dry wit",
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
    "very short (under 40 chars)",
    "very short (under 40 chars)",
    "a short quip or remark (40-70 chars)",
    "short (40-70 chars)",
    "short (40-70 chars)",
    "medium (70-120 chars)",
    "medium (70-120 chars)",
    "longer (120-150 chars max)",
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
# Full list of WoW emotes available in 3.3.5a
# (maps to TEXT_EMOTE_* enum in SharedDefines.h)
EMOTE_LIST = [
    'absent', 'agree', 'amaze', 'angry',
    'apologize', 'applaud', 'arm', 'awe',
    'backpack', 'badfeeling', 'bark', 'bashful',
    'beckon', 'beg', 'bite', 'blame',
    'blank', 'bleed', 'blink', 'blush',
    'boggle', 'bonk', 'bored', 'bounce',
    'bow', 'brandish', 'brb', 'breath',
    'burp', 'bye', 'cackle', 'calm',
    'challenge', 'charge', 'charm', 'cheer',
    'chicken', 'chuckle', 'chug', 'clap',
    'cold', 'comfort', 'commend', 'confused',
    'congratulate', 'cough', 'coverears', 'cower',
    'crack', 'cringe', 'crossarms', 'cry',
    'cuddle', 'curious', 'curtsey', 'dance',
    'ding', 'disagree', 'doubt', 'drink',
    'drool', 'duck', 'eat', 'embarrass',
    'encourage', 'enemy', 'eye', 'eyebrow',
    'facepalm', 'fail', 'faint', 'fart',
    'fidget', 'flee', 'flex', 'flirt',
    'flop', 'follow', 'frown', 'gasp',
    'gaze', 'giggle', 'glare', 'gloat',
    'glower', 'go', 'going', 'golfclap',
    'goodluck', 'greet', 'grin', 'groan',
    'grovel', 'growl', 'guffaw', 'hail',
    'happy', 'headache', 'healme', 'hello',
    'helpme', 'hiccup', 'highfive', 'hiss',
    'holdhand', 'hug', 'hungry', 'hurry',
    'idea', 'incoming', 'insult', 'introduce',
    'jealous', 'jk', 'joke', 'kiss',
    'kneel', 'laugh', 'laydown', 'lick',
    'listen', 'look', 'lost', 'love',
    'luck', 'map', 'mercy', 'mock',
    'moan', 'moo', 'moon', 'mourn',
    'mutter', 'nervous', 'no', 'nod',
    'nosepick', 'object', 'offer', 'oom',
    'openfire', 'panic', 'pat', 'peer',
    'pet', 'pinch', 'pity', 'plead',
    'point', 'poke', 'ponder', 'pounce',
    'pout', 'praise', 'pray', 'promise',
    'proud', 'pulse', 'punch', 'purr',
    'puzzle', 'raise', 'rasp', 'ready',
    'regret', 'revenge', 'roar', 'rofl',
    'rolleyes', 'rude', 'ruffle', 'sad',
    'salute', 'scared', 'scoff', 'scold',
    'scowl', 'scratch', 'search', 'serious',
    'sexy', 'shake', 'shakefist', 'shifty',
    'shimmy', 'shiver', 'shoo', 'shout',
    'shrug', 'shudder', 'shy', 'sigh',
    'signal', 'silence', 'sing', 'slap',
    'smack', 'smile', 'smirk', 'snap',
    'snarl', 'sneak', 'sneeze', 'snicker',
    'sniff', 'snort', 'snub', 'soothe',
    'spit', 'squeal', 'stare', 'stink',
    'surprised', 'surrender', 'suspicious',
    'sweat', 'talk', 'tap', 'taunt',
    'tease', 'thank', 'think', 'thirsty',
    'threaten', 'tickle', 'tired', 'toast',
    'train', 'truce', 'twiddle', 'veto',
    'victory', 'violin', 'wait', 'warn',
    'wave', 'welcome', 'whine', 'whistle',
    'wink', 'work', 'yawn', 'yw',
    'none',
]

EMOTE_LIST_STR = ', '.join(EMOTE_LIST)

# Keyword -> emote mapping for statement post-processing
# (used when LLM output is plain text, not JSON)
EMOTE_KEYWORDS = {
    # Positive / greeting
    'hello': 'wave', 'hi ': 'wave',
    'hey ': 'wave', 'greetings': 'wave',
    'farewell': 'wave', 'goodbye': 'wave',
    'safe travels': 'bow', 'welcome': 'wave',
    'good to see': 'wave',
    # Humor / joy
    'lol': 'laugh', 'haha': 'laugh',
    'lmao': 'laugh', 'rofl': 'laugh',
    'funny': 'laugh', 'hilarious': 'laugh',
    'ridiculous': 'laugh', 'laugh': 'laugh',
    'chuckle': 'laugh', 'amuse': 'laugh',
    'joke': 'laugh',
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
    'grief': 'cry', 'miss ': 'cry',
    # Respect / admiration
    'thank': 'bow', 'respect': 'bow',
    'honor': 'bow', 'well met': 'bow',
    'grateful': 'bow', 'appreciate': 'bow',
    'impressive': 'applaud',
    'well done': 'applaud',
    'bravo': 'applaud', 'nice work': 'applaud',
    'good job': 'applaud',
    'great work': 'applaud',
    'skilled': 'applaud',
    'masterful': 'applaud',
    # Combat / intensity
    'attack': 'roar', 'for the': 'roar',
    'lok\'tar': 'roar', 'glory': 'roar',
    'battle cry': 'roar', 'fight': 'shout',
    'watch out': 'shout',
    'behind you': 'shout',
    'careful': 'shout', 'look out': 'shout',
    'run': 'shout', 'get back': 'shout',
    'danger': 'shout', 'pull': 'shout',
    'adds': 'shout',
    # Questions
    'where': 'curious', 'how do': 'curious',
    'anyone know': 'curious',
    'what is': 'curious', '?': 'curious',
    'wonder': 'curious',
    # Surprise
    'what the': 'gasp', 'holy': 'gasp',
    'whoa': 'gasp', 'wow ': 'gasp',
    'by the': 'gasp',
    'never seen': 'gasp',
    'unbelievable': 'gasp',
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
    'ancestors': 'kneel',
    'earth mother': 'kneel',
    'elune': 'kneel', 'bless': 'kneel',
    'spirit': 'kneel', 'may the': 'kneel',
    'rest in peace': 'kneel',
    'fallen comrade': 'kneel',
    # Eating / drinking / resting
    'drink': 'eat', 'eat': 'eat',
    'hungry': 'eat', 'mana break': 'eat',
    'need to rest': 'eat', 'sit down': 'eat',
    # Rude / dismissive
    'pathetic': 'rude', 'fool': 'rude',
    'waste of': 'rude', 'disgrace': 'rude',
    'shut up': 'rude', 'useless': 'rude',
    # Agreement / disagreement
    'agree': 'nod', 'right': 'nod',
    'exactly': 'nod', 'indeed': 'nod',
    'absolutely': 'nod', 'of course': 'nod',
    'no way': 'no', 'refuse': 'no',
    'never': 'no', 'won\'t': 'no',
    'don\'t think so': 'no',
    # Begging / desperation
    'please': 'beg', 'mercy': 'beg',
    'desperate': 'beg', 'need help': 'beg',
    'save me': 'beg', 'i beg': 'beg',
    # Taunting
    'coward': 'chicken', 'afraid': 'chicken',
    'chicken': 'chicken',
    'running away': 'chicken',
    # Confusion / uncertainty
    'confused': 'confused', 'what': 'confused',
    'huh': 'confused', 'puzzled': 'puzzle',
    # Comfort / support
    'there there': 'comfort',
    'it\'s ok': 'comfort',
    'don\'t worry': 'soothe',
    'calm down': 'calm',
    # Affection
    'love': 'love', 'adore': 'love',
    'hug': 'hug', 'cuddle': 'cuddle',
    # Sarcasm / dismissal
    'whatever': 'rolleyes',
    'yeah right': 'rolleyes',
    'pfft': 'scoff', 'tsk': 'scold',
    # Pain / distress
    'ow': 'cringe', 'ouch': 'cringe',
    'hurt': 'cringe', 'pain': 'cringe',
    # Frustration
    'ugh': 'facepalm', 'facepalm': 'facepalm',
    'stupid': 'facepalm', 'doh': 'facepalm',
    # Warm greeting variants
    'good morning': 'hello',
    'good evening': 'hello',
    'howdy': 'hello',
    # Encouragement
    'you can do': 'encourage',
    'keep going': 'encourage',
    'come on': 'encourage', 'go go': 'charge',
    # Cold / weather
    'cold': 'cold', 'freezing': 'shiver',
    'shiver': 'shiver', 'brr': 'cold',
    # Nervousness
    'nervous': 'nervous', 'worried': 'nervous',
    'anxious': 'nervous', 'uneasy': 'fidget',
    # Thinking
    'hmm': 'think', 'let me think': 'ponder',
    'ponder': 'ponder', 'consider': 'think',
    # Farewell variants
    'see you': 'bye', 'later': 'bye',
    'take care': 'bye', 'cya': 'bye',
    # Surprise (extended)
    'gasp': 'gasp', 'shocked': 'gasp',
    'astonish': 'amaze',
    'incredible': 'amaze',
    # Amusement
    'snicker': 'snicker', 'giggle': 'giggle',
    'tee hee': 'giggle', 'hehe': 'giggle',
    # Tactical
    'oom': 'oom', 'out of mana': 'oom',
    'need mana': 'oom', 'low mana': 'oom',
    'heal me': 'healme',
    'need heal': 'healme',
    'help': 'helpme',
    'incoming': 'incoming',
    # Smiling
    'smile': 'smile', 'grin': 'grin',
    'smirk': 'smirk', 'wink': 'wink',
    # Sadness (extended)
    'sigh': 'sigh', 'mourn': 'mourn',
    'weep': 'cry', 'pity': 'pity',
    'sad': 'sad',
    # Doubt / skepticism
    'doubt': 'doubt',
    'suspicious': 'suspicious',
    'skeptic': 'doubt', 'really?': 'doubt',
    # Bravery
    'brave': 'charge', 'onward': 'charge',
    'forward': 'charge', 'to battle': 'roar',
    # Fear
    'scared': 'scared', 'terrified': 'cower',
    # Thirst
    'thirsty': 'thirsty',
    # Nod
    'nod': 'nod', 'sure': 'nod',
    'ok': 'nod', 'very well': 'nod',
    # Charge (combat lead)
    'charge': 'charge',
}

# =============================================================================
# PERSONALITY SPICES — Normal mode
# =============================================================================
# Mundane micro-situations injected into prompts to break
# phrasing convergence. 2nd person present tense, 5-15 words.
PERSONALITY_SPICES = [
    # --- Physical ---
    "your feet are sore from all this walking",
    "you have a small pebble stuck in your boot",
    "your shoulder aches from carrying your gear",
    "you keep yawning and can't seem to stop",
    "your stomach just growled embarrassingly loud",
    "you have a minor headache from the sun",
    "your back is stiff from sleeping on the ground",
    "you bit your tongue earlier and it still hurts",
    "your hands are calloused and cracking",
    "you twisted your ankle slightly on a rock",
    "your armor is chafing under your left arm",
    "you have a splinter in your palm",
    # --- Thoughts ---
    "you're wondering what's for dinner tonight",
    "you keep thinking about a weird dream you had",
    "you forgot something but can't remember what",
    "you're mentally replaying an argument from yesterday",
    "a song is stuck in your head and won't leave",
    "you're wondering if you left the campfire burning",
    "you're thinking about home and feeling nostalgic",
    "you're trying to remember a joke someone told you",
    "you're debating whether to sell or keep your gear",
    "you can't stop thinking about gold you wasted",
    "you're daydreaming about a warm bath",
    "you keep losing count of how many days you've traveled",
    # --- Sensory ---
    "something nearby smells really terrible",
    "the light is hitting the landscape beautifully",
    "you keep hearing a faint buzzing noise",
    "the air tastes dusty and dry",
    "the wind keeps blowing your hair in your face",
    "you can smell food cooking somewhere nearby",
    "there's a persistent fly circling your head",
    "the ground feels oddly warm under your feet",
    "you notice the shadows are getting longer",
    "the air has a strange metallic tang",
    "you keep catching a whiff of wildflowers",
    "the silence here is almost unnerving",
    # --- Social ---
    "you're feeling a bit left out of the group",
    "you want to impress someone in the party",
    "you're annoyed by something minor someone said",
    "you're grateful to not be adventuring alone",
    "you're trying to think of something clever to say",
    "you're worried you're slowing the group down",
    "you're curious about the player's combat style",
    "you keep glancing at another party member's weapon",
    "you're wondering who's really in charge here",
    "you feel like proving yourself to the group",
    "you're relieved someone else is taking the lead",
    "you want to ask a question but feel silly",
    # --- Mood ---
    "you're in a surprisingly good mood today",
    "you're feeling restless and fidgety",
    "you have a nagging sense of unease",
    "you're oddly calm despite everything",
    "you feel inexplicably optimistic right now",
    "you're a bit grumpy and don't know why",
    "you're feeling competitive for no reason",
    "you're feeling unusually patient today",
    "a wave of tiredness just washed over you",
    "you're feeling bold and reckless",
    "you're quietly content with how things are going",
    "you keep sighing without meaning to",
    # --- Nature ---
    "a bird just startled you by flying past",
    "you noticed animal tracks on the ground nearby",
    "a cool breeze just picked up pleasantly",
    "clouds are slowly rolling in from the west",
    "you spotted a rabbit darting into the bushes",
    "the trees here look ancient and gnarled",
    "there's a hawk circling high overhead",
    "the grass here is surprisingly tall",
    "you stepped in a muddy patch and your boot sank",
    "a butterfly just landed on your shoulder briefly",
    "the river nearby sounds peaceful",
    "you noticed moss growing on everything here",
    # --- Practical ---
    "you're running low on water",
    "your weapon could really use sharpening",
    "you need to patch a hole in your pack",
    "you're wondering when the next town is",
    "your supplies are getting lighter by the day",
    "you realized you forgot to buy bandages",
    "your torch is getting low",
    "you're trying to figure out which way is north",
    "you should probably eat something soon",
    "your map is smudged and hard to read",
    "you need to restring your bow when you get a chance",
    "you keep checking your coin purse out of habit",
    # --- Quirky ---
    "you've been counting your steps since the last camp",
    "you're craving cheese for some reason",
    "you keep humming the same three notes",
    "you found a weird-shaped rock and kept it",
    "you're wondering if that mushroom was edible",
    "you've been making up names for the clouds",
    "you bet yourself you could climb that tree",
    "you keep picking at a loose thread on your sleeve",
    "you're wondering what your pet is doing right now",
    "you saw a face in a tree knot and it spooked you",
    "you're resisting the urge to skip a rock",
    "you keep checking if anyone noticed you trip",
]

# =============================================================================
# PERSONALITY SPICES — RP mode
# =============================================================================
# More immersive and lore-adjacent, still mundane.
RP_PERSONALITY_SPICES = [
    # --- Physical ---
    "your old wound from the Barrens aches in this weather",
    "your chainmail links are pinching your neck",
    "your hands tremble faintly from channeling too much",
    "your throat is parched from the dusty road",
    "you can feel blisters forming on your heels",
    "your cloak is heavy with morning dew",
    "your shield arm is sore from yesterday's fight",
    "hunger gnaws at your belly like a wolf",
    "your fingers are numb from the cold mountain air",
    "the weight of your pack bows your shoulders",
    "sweat trickles down your temple despite the breeze",
    "your muscles protest after days of marching",
    # --- Thoughts ---
    "you're thinking of kin you haven't seen in seasons",
    "memories of your homeland surface unbidden",
    "you wonder if the spirits are watching over you",
    "you keep turning over an old proverb in your mind",
    "you're composing a letter home in your thoughts",
    "an ancestor's warning echoes in your memory",
    "you're questioning the wisdom of this path",
    "you recall a tale your mentor once told you",
    "you wonder what became of an old companion",
    "you're puzzling over the meaning of a recent omen",
    "you keep replaying a conversation that troubles you",
    "the memory of a feast day fills you with longing",
    # --- Sensory ---
    "the scent of pine reminds you of Teldrassil",
    "the wind carries whispers from distant lands",
    "smoke from a far-off campfire taints the air",
    "the earth beneath your feet hums with old magic",
    "distant thunder rumbles beyond the mountains",
    "the light here has a strange golden quality",
    "the air smells of rain though the sky is clear",
    "the silence is thick enough to cut with a blade",
    "something stirs in the underbrush just out of sight",
    "the scent of blood lingers faintly on the breeze",
    "the stones here are warm as if heated from below",
    "birdsong echoes through the canopy above",
    # --- Social ---
    "you feel a quiet kinship with your companions",
    "you're sizing up your party members' resolve",
    "you wish to earn the respect of those beside you",
    "you wonder what drives the others to adventure",
    "you feel the weight of being relied upon",
    "you're grateful for allies in these dark times",
    "you sense tension simmering beneath the surface",
    "you want to share a story but the moment isn't right",
    "you feel protective of the younger members",
    "you're curious about the player's origins",
    "you wonder if your companions trust you fully",
    "you catch yourself watching the others for weakness",
    # --- Mood ---
    "a quiet determination settles in your chest",
    "restlessness coils within you like a spring",
    "an old melancholy tugs at your heart today",
    "you feel strangely at peace in this wild place",
    "a fierce joy burns in you for no clear reason",
    "weariness sits heavy upon your brow",
    "your spirit feels lighter than it has in weeks",
    "a cold resolve hardens behind your eyes",
    "you feel the thrill of the hunt in your blood",
    "something about today feels auspicious",
    "you carry a heaviness that won't quite lift",
    "pride stirs quietly at how far you've come",
    # --- Nature ---
    "a raven watches you from a dead branch",
    "the trees here bend as though bowing to something",
    "a cold stream crosses the path ahead",
    "ancient roots break through the soil like bones",
    "the undergrowth rustles with unseen creatures",
    "clouds gather like an army on the horizon",
    "the wildflowers here bloom despite the scorched earth",
    "a lone wolf howls somewhere in the distance",
    "the moss on these stones tells of centuries passing",
    "the forest thins and reveals a sweeping vista",
    "the wind shifts and carries the scent of the sea",
    "the moon is visible even in the daylight sky",
    # --- Practical ---
    "your provisions won't last another two days",
    "your blade's edge has dulled against too many hides",
    "your healing salve is nearly spent",
    "you need to find a smithy before long",
    "your waterskin is worryingly light",
    "the leather on your grip is wearing thin",
    "you should tend your wounds before they fester",
    "your reagent pouch is running dangerously low",
    "you need to mend your cloak before nightfall",
    "your boots are not suited for this terrain",
    "you've been meaning to oil your armor for days",
    "your rope is fraying and may not hold much longer",
    # --- Quirky ---
    "you swore you saw a face in the water's reflection",
    "you've been silently naming every bird you see",
    "you caught yourself talking to your weapon again",
    "you found a four-leaf clover and tucked it away",
    "you keep touching an old trinket for luck",
    "you're mentally cataloguing every herb you pass",
    "you're certain this path looked different last time",
    "you have an irrational dislike of this particular hill",
    "you keep glancing over your shoulder from old habit",
    "you carved a small notch in your staff for today",
    "you're wondering if dragons dream when they sleep",
    "you saved a crust of bread and feel oddly proud",
]


# =============================================================================
# EMOTE CATEGORIES
# =============================================================================
# Maps TEXT_EMOTE_* ID -> category string for prompt tone.
# Covers all social emotes (denylist approach in C++).
EMOTE_CATEGORIES = {
    # greeting
    101: "greeting",      # WAVE
    19:  "greeting",      # BYE
    55:  "greeting",      # HELLO
    102: "greeting",      # WELCOME
    48:  "greeting",      # GREET
    1:   "greeting",      # AGREE
    2:   "greeting",      # AMAZE
    54:  "greeting",      # HAPPY
    163: "greeting",      # SMILE
    114: "greeting",      # INTRODUCE
    7:   "greeting",      # BECKON
    # respect
    17:  "respect",       # BOW
    78:  "respect",       # SALUTE
    33:  "respect",       # CURTSEY
    59:  "respect",       # KNEEL
    67:  "respect",       # NOD
    125: "respect",       # RAISE
    122: "respect",       # PRAISE
    # celebration
    21:  "celebration",   # CHEER
    5:   "celebration",   # APPLAUD
    24:  "celebration",   # CLAP
    100: "celebration",   # VICTORY
    243: "celebration",   # COMMEND
    343: "celebration",   # GOLFCLAP
    378: "celebration",   # TOAST
    380: "celebration",   # HIGHFIVE
    389: "celebration",   # DING
    413: "celebration",   # PROUD
    387: "celebration",   # CHUG
    375: "celebration",   # ENCOURAGE
    367: "celebration",   # GOODLUCK
    # humour
    60:  "humour",        # LAUGH
    45:  "humour",        # GIGGLE
    76:  "humour",        # ROFL
    20:  "humour",        # CACKLE
    52:  "humour",        # GUFFAW
    329: "humour",        # JOKE
    18:  "humour",        # BURP
    39:  "humour",        # FART
    68:  "humour",        # NOSEPICK
    64:  "humour",        # MOON
    63:  "humour",        # MOAN
    36:  "humour",        # DROOL
    49:  "humour",        # GRIN
    131: "humour",        # SMIRK
    140: "humour",        # SNICKER
    396: "humour",        # HICCUP
    436: "humour",        # SNEEZE
    437: "humour",        # SNORT
    438: "humour",        # SQUEAL
    115: "humour",        # JK
    13:  "humour",        # BONK
    390: "humour",        # FACEPALM
    391: "humour",        # FAINT
    127: "humour",        # SHIMMY
    429: "humour",        # SHIFTY
    435: "humour",        # SNEAK
    447: "humour",        # COVEREARS
    224: "humour",        # FLOP
    23:  "humour",        # CHUCKLE
    # mockery
    77:  "mockery",       # RUDE
    22:  "mockery",       # CHICKEN
    136: "mockery",       # TAUNT
    113: "mockery",       # INSULT
    183: "mockery",       # RASP
    368: "mockery",       # BLAME
    372: "mockery",       # DISAGREE
    373: "mockery",       # DOUBT
    119: "mockery",       # MOCK
    133: "mockery",       # SNUB
    424: "mockery",       # SCOFF
    425: "mockery",       # SCOLD
    38:  "mockery",       # EYE
    139: "mockery",       # VETO
    377: "mockery",       # EYEBROW
    421: "mockery",       # ROLLEYES
    203: "mockery",       # PITY
    135: "mockery",       # STINK
    129: "mockery",       # SHOO
    448: "mockery",       # CROSSARMS
    440: "mockery",       # SUSPICIOUS
    # affection
    328: "affection",     # FLIRT
    58:  "affection",     # KISS
    56:  "affection",     # HUG
    111: "affection",     # CUDDLE
    225: "affection",     # LOVE
    363: "affection",     # WINK
    364: "affection",     # PAT
    399: "affection",     # HOLDHAND
    422: "affection",     # RUFFLE
    446: "affection",     # CHARM
    123: "affection",     # PURR
    116: "affection",     # LICK
    142: "affection",     # TICKLE
    73:  "affection",     # POKE
    134: "affection",     # SOOTHE
    410: "affection",     # PET
    110: "affection",     # COMFORT
    80:  "affection",     # SEXY
    # gratitude
    97:  "gratitude",     # THANK
    453: "gratitude",     # YW
    4:   "gratitude",     # APOLOGIZE
    404: "gratitude",     # LUCK
    414: "gratitude",     # PROMISE
    442: "gratitude",     # TRUCE
    409: "gratitude",     # OFFER
    # distress
    31:  "distress",      # CRY
    65:  "distress",      # MOURN
    71:  "distress",      # PLEAD
    8:   "distress",      # BEG
    51:  "distress",      # GROVEL
    223: "distress",      # SCARED
    103: "distress",      # WHINE
    69:  "distress",      # PANIC
    423: "distress",      # SAD
    417: "distress",      # POUT
    99:  "distress",      # TIRED
    395: "distress",      # HEADACHE
    408: "distress",      # NERVOUS
    430: "distress",      # SHUDDER
    451: "distress",      # SWEAT
    42:  "distress",      # FROWN
    10:  "distress",      # BLEED
    109: "distress",      # COLD
    57:  "distress",      # HUNGRY
    138: "distress",      # THIRSTY
    50:  "distress",      # GROAN
    385: "distress",      # BADFEELING
    30:  "distress",      # CRINGE
    418: "distress",      # REGRET
    128: "distress",      # SHIVER
    403: "distress",      # JEALOUS
    381: "distress",      # ABSENT
    # provocation
    75:  "provocation",   # ROAR
    204: "provocation",   # GROWL
    3:   "provocation",   # ANGRY
    98:  "provocation",   # THREATEN
    88:  "provocation",   # SNARL
    89:  "provocation",   # SPIT
    46:  "provocation",   # GLARE
    90:  "provocation",   # STARE
    376: "provocation",   # ENEMY
    386: "provocation",   # CHALLENGE
    428: "provocation",   # SHAKEFIST
    398: "provocation",   # HISS
    205: "provocation",   # BARK
    420: "provocation",   # REVENGE
    370: "provocation",   # BRANDISH
    416: "provocation",   # PUNCH
    434: "provocation",   # SMACK
    445: "provocation",   # SNAP
    130: "provocation",   # SLAP
    444: "provocation",   # WARN
    394: "provocation",   # GLOWER
    411: "provocation",   # PINCH
    121: "provocation",   # POUNCE
    426: "provocation",   # SCOWL
    # dance
    34:  "dance",         # DANCE
    # boredom
    14:  "boredom",       # BORED
    40:  "boredom",       # FIDGET
    443: "boredom",       # TWIDDLE
    369: "boredom",       # BLANK
    # melancholy
    85:  "melancholy",    # SIGH
    407: "melancholy",    # MUTTER
    # 418: REGRET — mapped above under "distress"
    # ambient
    104: "ambient",       # WHISTLE
    106: "ambient",       # YAWN
    226: "ambient",       # MOO
    105: "ambient",       # WORK
    11:  "ambient",       # BLINK
    79:  "ambient",       # SCRATCH
    81:  "ambient",       # SHAKE
    96:  "ambient",       # TAP
    449: "ambient",       # LOOK
    427: "ambient",       # SEARCH
    44:  "ambient",       # GAZE
    70:  "ambient",       # PEER
    117: "ambient",       # LISTEN
    405: "ambient",       # MAP
    384: "ambient",       # BACKPACK
    371: "ambient",       # BREATH
    382: "ambient",       # ARM
    431: "ambient",       # SIGNAL
    432: "ambient",       # SILENCE
    402: "ambient",       # IDEA
    441: "ambient",       # THINK
    401: "ambient",       # HURRY
    392: "ambient",       # GO
    393: "ambient",       # GOING
    365: "ambient",       # SERIOUS
    126: "ambient",       # READY
    29:  "ambient",       # CRACK
    112: "ambient",       # DUCK
    264: "ambient",       # TRAIN
    91:  "ambient",       # SURPRISED
    383: "ambient",       # AWE
    108: "ambient",       # CALM
    15:  "ambient",       # BOUNCE
}

# Maps CreatureType enum -> human-readable string
# (SharedDefines.h:2606)
NPC_TYPE_NAMES = {
    1: "Beast", 2: "Dragonkin", 3: "Demon",
    4: "Elemental", 5: "Giant", 6: "Undead",
    7: "Humanoid", 8: "Critter", 9: "Mechanical",
    10: "Not specified", 11: "Totem",
    12: "Non-combat pet", 13: "Gas cloud",
}

# Maps creature rank -> human-readable string
NPC_RANK_NAMES = {
    0: "Normal", 1: "Elite", 2: "Rare Elite",
    3: "Boss", 4: "Rare",
}

# Maps emote name string -> TEXT_EMOTE_* ID.
# Covers all social emotes (C++ now uses denylist).
EMOTE_NAME_TO_ID = {
    # greeting / social
    "wave": 101, "hello": 55, "greet": 48,
    "bye": 19, "welcome": 102,
    "agree": 1, "amaze": 2, "happy": 54,
    "smile": 163, "introduce": 114, "beckon": 7,
    # respect
    "bow": 17, "salute": 78, "curtsey": 33,
    "kneel": 59, "nod": 67, "raise": 125,
    "praise": 122,
    # celebration
    "cheer": 21, "applaud": 5, "clap": 24,
    "victory": 100, "commend": 243,
    "golfclap": 343, "toast": 378,
    "highfive": 380, "ding": 389,
    "proud": 413, "chug": 387,
    "encourage": 375, "goodluck": 367,
    # humour
    "laugh": 60, "giggle": 45, "rofl": 76,
    "cackle": 20, "guffaw": 52, "joke": 329,
    "chuckle": 23, "burp": 18, "fart": 39,
    "nosepick": 68, "moon": 64, "moan": 63,
    "drool": 36, "grin": 49, "smirk": 131,
    "snicker": 140, "hiccup": 396,
    "sneeze": 436, "snort": 437, "squeal": 438,
    "jk": 115, "bonk": 13, "facepalm": 390,
    "faint": 391, "shimmy": 127, "shifty": 429,
    "sneak": 435, "coverears": 447, "flop": 224,
    # mockery
    "rude": 77, "chicken": 22, "taunt": 136,
    "insult": 113, "rasp": 183, "blame": 368,
    "disagree": 372, "doubt": 373,
    "mock": 119, "snub": 133, "scoff": 424,
    "scold": 425, "eye": 38, "veto": 139,
    "eyebrow": 377, "rolleyes": 421,
    "pity": 203, "stink": 135, "shoo": 129,
    "crossarms": 448, "suspicious": 440,
    # affection
    "flirt": 328, "kiss": 58, "hug": 56,
    "cuddle": 111, "love": 225, "wink": 363,
    "pat": 364, "holdhand": 399, "ruffle": 422,
    "charm": 446, "purr": 123, "lick": 116,
    "tickle": 142, "poke": 73, "soothe": 134,
    "pet": 410, "comfort": 110, "sexy": 80,
    # gratitude
    "thank": 97, "yw": 453, "apologize": 4,
    "luck": 404, "promise": 414, "truce": 442,
    "offer": 409,
    # distress
    "cry": 31, "mourn": 65, "plead": 71,
    "beg": 8, "grovel": 51, "scared": 223,
    "whine": 103, "panic": 69, "sad": 423,
    "pout": 417, "tired": 99, "headache": 395,
    "nervous": 408, "shudder": 430, "sweat": 451,
    "frown": 42, "bleed": 10, "cold": 109,
    "hungry": 57, "thirsty": 138, "groan": 50,
    "badfeeling": 385, "cringe": 30,
    "regret": 418, "shiver": 128,
    "jealous": 403, "absent": 381,
    # provocation
    "roar": 75, "growl": 204, "angry": 3,
    "threaten": 98, "snarl": 88, "spit": 89,
    "glare": 46, "stare": 90, "enemy": 376,
    "challenge": 386, "shakefist": 428,
    "hiss": 398, "bark": 205, "revenge": 420,
    "brandish": 370, "punch": 416, "smack": 434,
    "snap": 445, "slap": 130, "warn": 444,
    "glower": 394, "pinch": 411, "pounce": 121,
    "scowl": 426,
    # dance
    "dance": 34,
    # boredom
    "bored": 14, "fidget": 40,
    "twiddle": 443, "blank": 369,
    # melancholy
    "sigh": 85, "mutter": 407,
    # ambient
    "whistle": 104, "yawn": 106, "moo": 226,
    "work": 105, "blink": 11, "scratch": 79,
    "shake": 81, "tap": 96, "look": 449,
    "search": 427, "gaze": 44, "peer": 70,
    "listen": 117, "map": 405, "backpack": 384,
    "breath": 371, "arm": 382, "signal": 431,
    "silence": 432, "idea": 402, "think": 441,
    "hurry": 401, "go": 392, "going": 393,
    "serious": 365, "ready": 126, "crack": 29,
    "duck": 112, "train": 264, "surprised": 91,
    "awe": 383, "calm": 108, "bounce": 15,
    # misc (existing set)
    "no": 66, "point": 72, "shrug": 83,
    "shy": 84, "blush": 12, "flex": 41,
    "sit": 86, "sleep": 87, "stand": 141,
    "violin": 143, "boggle": 107, "lost": 118,
    "ponder": 120, "puzzle": 124,
    "surrender": 92, "talk": 93,
    "talkex": 94, "talkq": 95,
    "confused": 25, "cower": 28, "curious": 32,
    "gasp": 43, "gloat": 47, "hail": 53,
    "laydown": 61, "pray": 74, "shout": 82,
    "fail": 379, "mercy": 406, "sing": 433,
    "object": 450, "congratulate": 26,
}

# Maps emote category -> list of tone descriptors for prompt
# variety.  One is picked at random per event.
REACTION_TONES = {
    "greeting": [
        "warmly",
        "briefly and cheerfully",
        "with a friendly quip",
    ],
    "respect": [
        "with dry approval",
        "with mild sarcasm",
        "with brief acknowledgment",
        "with gentle teasing",
    ],
    "celebration": [
        "with shared enthusiasm",
        "with a witty cheer",
        "with playful energy",
    ],
    "humour": [
        "with a laugh and a quip",
        "joining the joke",
        "with dry amusement",
    ],
    "mockery": [
        "with sharp wit",
        "with amused offense",
        "with a quick comeback",
    ],
    "affection": [
        "warmly",
        "with gentle teasing",
        "with a shy or flustered reaction",
    ],
    "gratitude": [
        "graciously",
        "with modest deflection",
        "with warm acknowledgment",
    ],
    "distress": [
        "with concern",
        "with sympathy",
        "with gentle reassurance",
    ],
    "provocation": [
        "with cool dismissal",
        "with composed annoyance",
        "with a sharp retort",
    ],
    "dance": [
        "with delight",
        "with surprise",
        "with playful encouragement",
    ],
    "boredom": [
        "with gentle teasing",
        "with dry amusement",
        "with a wry observation",
    ],
    "melancholy": [
        "with quiet empathy",
        "with gentle concern",
        "with light humor to break the tension",
    ],
    "ambient": [
        "with amusement",
        "with a dry observation",
        "with curiosity",
    ],
}
