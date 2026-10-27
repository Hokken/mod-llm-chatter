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
    4080: "Isle of Quel'Danas", 4298: "Plaguelands: The Scarlet Enclave",
    # Northrend
    3537: "Borean Tundra", 495: "Howling Fjord", 394: "Grizzly Hills",
    3711: "Sholazar Basin", 66: "Zul'Drak", 67: "The Storm Peaks",
    210: "Icecrown",
    65: "Dragonblight", 2817: "Crystalsong Forest", 4395: "Dalaran",
    4197: "Wintergrasp", 4228: "The Oculus",
    # Other
    406: "Stonetalon Mountains",
}

# Russian (ruRU) zone names -- extracted directly from
# Blizzard's own AreaTable.dbc (ruRU client data), field
# index 19 (the ruRU slot of the AreaName localized-string
# block: 11 scalar fields, then ruRU is locale slot 8 of
# 16, byte offset 76 into each 144-byte record). Verified
# against known translations (e.g. zone 14 Durotar ->
# "Дуротар") before extracting the full set. Keyed
# identically to ZONE_NAMES above (same zone IDs) so
# get_zone_name() can do a straight locale-map lookup
# with an English fallback.

# French (frFR) and German (deDE) zone names -- unlike
# ZONE_NAMES_RU above (extracted directly from Blizzard's
# own ruRU AreaTable.dbc, 100% authoritative), this data was
# sourced from warcraft.wiki.gg's community-maintained
# "LocalizedMapZones" addon-localization table, not from an
# official Blizzard client data extraction. Treat it as
# likely-accurate but NOT independently verified against
# official client data. Zone IDs were cross-checked against
# ZONE_NAMES above so every key here is a real, valid zone;
# entries with no translation available on the wiki page are
# simply omitted (get_zone_name() falls back to English for
# those) rather than guessed. Coverage is known to be
# incomplete, especially for French, which is missing most/
# all of Northrend and a handful of other zones (e.g. Mount
# Hyjal, Alterac Mountains, Hrothgar's Landing have no entry
# in either language because they aren't present in
# ZONE_NAMES at all).
#
# Update: 8 Northrend zone names were added to ZONE_NAMES_FR
# below (Borean Tundra, Howling Fjord, Dragonblight, Grizzly
# Hills, Zul'Drak, Sholazar Basin, The Storm Peaks,
# Icecrown), closing most of the French Northrend gap noted
# above. Unlike the wiki-sourced rest of this dict, these 8
# come from an official Blizzard press source
# (news.blizzard.com/fr-fr "Guide des zones de Wrath of the
# Lich King Classic" article series) and are genuinely
# higher-confidence -- same tier as the flagged es-es
# entries in ZONE_NAMES_ES below. Flagged inline on each
# entry.
#
# Update: 10 more zone names were added to ZONE_NAMES_FR
# below (Bloodmyst Isle, Isle of Quel'Danas, Eversong Woods,
# Azuremyst Isle, Ghostlands, Wintergrasp, Crystalsong
# Forest, Silvermoon City, The Exodar, The Oculus), covering
# most of the remaining Burning Crusade/Northrend gap.
# Sourced from Wowhead's French-locale zone database
# (cross-referenced across multiple expansion versions/URLs
# for consistency), with Wowpedia/WikiWoW's French wiki used
# for cross-confirmation on a couple of entries -- same
# confidence tier as the wiki-sourced rest of this dict
# above (likely accurate, not independently verified against
# DBC), NOT the official-press tier of the 8 entries flagged
# inline just above. "The Barrens" was deliberately not
# added: the only French source found for it ("Tarides du
# Nord") reflects the modern post-Cataclysm Northern/
# Southern Barrens split and doesn't reliably correspond to
# this server's single pre-split "The Barrens" zone_id 17,
# the same ambiguity already noted for the German dict.
# "Dalaran" was also skipped -- confirmed via Wowhead FR that
# it keeps the same name in French, not a real translation.


# Spanish (esES) zone names -- mixed provenance, unlike
# ZONE_NAMES_RU above (DBC-extracted, 100% authoritative)
# and closer in spirit to ZONE_NAMES_FR / ZONE_NAMES_DE
# (community-sourced, not verified against official client
# data). Most entries below come from an old (2007) Spanish
# WoW fan blog (worldofwarcraftesp.blogspot.com) covering
# classic-era zones only -- community-sourced, similar
# confidence tier to the wiki-sourced FR/DE data above, NOT
# independently verified against official client data.
# Nine entries -- Borean Tundra, Howling Fjord, Hellfire
# Peninsula, Dragonblight, Grizzly Hills, Zul'Drak, Sholazar
# Basin, The Storm Peaks, Icecrown (flagged inline below) --
# come from an actual official Blizzard press source
# (news.blizzard.com/es-es) instead, and are genuinely
# higher-confidence than the rest. A handful of source
# entries had typos or missing
# accents (e.g. "Dun Mor ogh" -> "Dun Morogh", "Paramos de
# Poniente" -> "Páramos de Poniente"); corrected to standard
# Spanish orthography where the intended word was
# unambiguous. Zone IDs were cross-referenced against
# ZONE_NAMES above and every source entry matched a real
# zone_id: "Stormwind" from the source (predating the
# "City" suffix) maps to zone_id 1519 ("Stormwind City"
# here); "The Barrens" was not present in the source at all,
# and ZONE_NAMES above has no Northern/Southern Barrens
# split to disambiguate against anyway, so there was nothing
# to add or guess at. Keyed identically to ZONE_NAMES above
# so get_zone_name() can do a straight locale-map lookup
# with an English fallback.
#
# Update: 17 more zone names were added to ZONE_NAMES_ES
# below (Blade's Edge Mountains, Netherstorm, Shadowmoon
# Valley, Terokkar Forest, Zangarmarsh, Crystalsong Forest,
# Wintergrasp, Azuremyst Isle, Bloodmyst Isle, Eversong
# Woods, Ghostlands, Silvermoon City, The Barrens, Shattrath
# City, The Exodar, The Oculus, Isle of Quel'Danas), mostly
# closing the Outland/Northrend gap. Sourced from
# wowictionary.blogspot.com's "zonas del mundo" page (a
# fan-maintained but broad/consistent Spanish translation
# reference) plus Wowhead's Spanish-locale zone database for
# a few entries (cross-referenced across expansion versions
# for consistency) -- same confidence tier as the rest of
# the fan-sourced entries above, NOT the official-press tier
# of the nine entries flagged inline above. "The Barrens" ->
# "Los Baldíos" was safe to add here (unlike the equivalent
# skip in ZONE_NAMES_FR above): this source is classic-era-
# only with no Northern/Southern Barrens split/version
# ambiguity, and ZONE_NAMES above likewise has no such split
# for this server, so it's a clean 1:1 match to zone_id 17.
# "Dalaran" and "Nagrand" were both skipped -- confirmed via
# Wowhead ES that they keep their English/original names in
# Spanish, not real translations.

# Korean (koKR) zone names -- a brand-new locale, not
# present before this addition. Unlike the wiki-sourced
# FR/DE data or the mixed-provenance ES data above, all 8
# entries here come directly from an official Blizzard press
# source (news.blizzard.com/ko-kr, the "리치 왕의 분노 클래식
# 지역 가이드" Wrath Classic zone guide article series) --
# same official-source confidence tier as the flagged es-es
# entries in ZONE_NAMES_ES above. Coverage is intentionally
# partial: only the 8 Northrend zones covered by that
# article series are included; every other zone falls back
# to English via get_zone_name(), the same fallback-safe
# pattern used for the other locales. Keyed identically to
# ZONE_NAMES above.

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

# Playable race IDs by faction: the one place a race decides the
# faction (get_race_faction() and the faction-scoped SQL filters).
# A server with races added through ChrRaces lists their IDs here.
ALLIANCE_RACE_IDS = (1, 3, 4, 7, 11)
HORDE_RACE_IDS = (2, 5, 6, 8, 10)

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
            "Lordaeron", "the cathedral", "King Varian",
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
            "Kaldorei", "Darnassus", "Nordrassil",
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
            "Guardianship of world trees, sacred groves, and wilderness sanctuaries is central.",
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
            "vengeance", "the apothecary", "Lordaeron",
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
            "Earth Mother", "the great hunt",
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
            "Destruction of their sacred fount caused magical withdrawal and social crisis.",
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

# Russian (ruRU) race speech profiles -- translated from the
# RACE_SPEECH_PROFILES entries above (same race keys, same
# traits/flavor_words/vocabulary/lore/worldview structure), not
# injected verbatim since the English text was leaking untranslated
# into Russian bot chat, and this dict is used to explicitly
# instruct bots to use specific words/phrases in their replies.
# `vocabulary` entries keep the conlang phrase (Orcish, Common,
# Darnassian, Thalassian, Draenei, etc. -- fictional in-world
# languages) UNCHANGED, exactly as in English, since these are
# proper in-universe language phrases, not English text; only the
# parenthetical English gloss is translated. `flavor_words`/`lore`/
# `traits`/`worldview` proper nouns reuse the official
# DBC-extracted terms from ZONE_NAMES_RU where covered there
# (Stormwind -> Штормград, Ironforge -> Стальгорн, etc.), mirroring
# ZONE_FLAVOR_RU's convention. Falls back to English
# RACE_SPEECH_PROFILES via get_race_speech_profile() for any locale
# other than ruRU.

# French (frFR) race speech profiles -- translated from the
# RACE_SPEECH_PROFILES entries above (same race keys, same
# traits/flavor_words/vocabulary/lore/worldview structure), not
# injected verbatim since the English text was leaking untranslated
# into French bot chat, and this dict is used to explicitly instruct
# bots to use specific words/phrases in their replies. `vocabulary`
# entries keep the conlang phrase (Orcish, Common, Darnassian,
# Thalassian, Draenei, etc. -- fictional in-world languages)
# UNCHANGED, exactly as in English, since these are proper
# in-universe language phrases, not English text; only the
# parenthetical English gloss is translated. `flavor_words`/`lore`/
# `traits`/`worldview` proper nouns reuse the community-sourced terms
# from ZONE_NAMES_FR where covered there (Stormwind -> Hurlevent,
# Ironforge -> Forgefer, etc.), mirroring ZONE_FLAVOR_FR's
# convention. Falls back to English RACE_SPEECH_PROFILES via
# get_race_speech_profile() for any locale other than frFR/ruRU.

# German (deDE) race speech profiles -- translated from the
# RACE_SPEECH_PROFILES entries above (same race keys, same
# traits/flavor_words/vocabulary/lore/worldview structure), not
# injected verbatim since the English text was leaking untranslated
# into German bot chat, and this dict is used to explicitly
# instruct bots to use specific words/phrases in their replies.
# `vocabulary` entries keep the conlang phrase (Orcish, Common,
# Darnassian, Thalassian, Draenei, Zandali, etc. -- fictional
# in-world languages) UNCHANGED, exactly as in English, since these
# are proper in-universe language phrases, not English text; only
# the parenthetical English gloss is translated. `flavor_words`/
# `lore`/`traits`/`worldview` proper nouns reuse the community-
# sourced terms from ZONE_NAMES_DE where covered there (Stormwind
# -> Sturmwind, Ironforge -> Eisenschmiede, etc.), mirroring
# ZONE_FLAVOR_DE's convention -- same confidence tier as
# ZONE_NAMES_DE/ZONE_FLAVOR_DE (community/wiki-sourced, not
# independently verified against official client DBC data, unlike
# RACE_SPEECH_PROFILES_RU's DBC-extracted base), with a handful of
# faction/organization names (Defias Brotherhood, Scourge,
# Forsaken, Scarlet Crusade, Cenarion Circle, Burning Legion, Sons
# of Hodir, Sundering) cross-checked against community WoW-DE
# databases for higher confidence, same tier as ZONE_FLAVOR_FR's
# approach. Falls back to English RACE_SPEECH_PROFILES via
# get_race_speech_profile() for any locale other than deDE/frFR/
# ruRU.

# Spanish (esES) race speech profiles -- translated from the
# RACE_SPEECH_PROFILES entries above (same race keys, same
# traits/flavor_words/vocabulary/lore/worldview structure), not
# injected verbatim since the English text was leaking untranslated
# into Spanish bot chat, and this dict is used to explicitly
# instruct bots to use specific words/phrases in their replies.
# `vocabulary` entries keep the conlang phrase (Orcish, Common,
# Darnassian, Thalassian, Draenei, Zandali, etc. -- fictional
# in-world languages) UNCHANGED, exactly as in English, since these
# are proper in-universe language phrases, not English text; only
# the parenthetical English gloss is translated. `flavor_words`/
# `lore`/`traits`/`worldview` proper nouns reuse the mixed-provenance
# terms from ZONE_NAMES_ES where covered there (Stormwind -> Ciudad
# de Ventormenta, Ironforge -> Forjaz, etc.), mirroring
# ZONE_FLAVOR_ES's convention -- same confidence tier as
# ZONE_NAMES_ES/ZONE_FLAVOR_ES (mixed community/official-press
# sourced, not independently verified against official client DBC
# data for the community-sourced portion), with a handful of
# faction/organization names (Defias Brotherhood, Scourge, Forsaken,
# Scarlet Crusade, Cenarion Circle, Burning Legion, Sons of Hodir,
# Sundering) cross-checked against community WoW-ES databases for
# higher confidence, same tier as RACE_SPEECH_PROFILES_FR/_DE's
# approach. Falls back to English RACE_SPEECH_PROFILES via
# get_race_speech_profile() for any locale other than esES/deDE/
# frFR/ruRU.


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
# PERSONALITY TRAITS - Used for random bot personality assignment
# =============================================================================
PERSONALITY_TRAITS = {
    'temperament': [
        'fiery', 'calm', 'brooding', 'volatile',
        'serene', 'melancholic', 'jovial',
        'quick-tempered', 'patient', 'restless',
        'placid', 'intense', 'mercurial',
        'even-keeled', 'passionate',
    ],
    'social': [
        'gregarious', 'reclusive', 'charming',
        'blunt', 'diplomatic', 'awkward',
        'commanding', 'deferential', 'flirtatious',
        'standoffish', 'nurturing', 'aloof',
        'boisterous', 'soft-spoken', 'gossipy',
        'tactful', 'abrasive', 'endearing',
    ],
    'outlook': [
        'hopeful', 'fatalistic', 'pragmatic',
        'idealistic', 'cynical', 'wistful',
        'defiant', 'resigned', 'ambitious',
        'content', 'suspicious', 'trusting',
        'world-weary', 'wide-eyed', 'jaded',
        'reverent', 'skeptical',
    ],
    'courage': [
        'fearless', 'cautious', 'reckless',
        'hesitant', 'bold', 'calculating',
        'foolhardy', 'steadfast', 'skittish',
        'dauntless', 'wary', 'brash',
        'unshakable', 'nervous', 'daring',
    ],
    'moral': [
        'honorable', 'ruthless', 'merciful',
        'vengeful', 'selfless', 'self-serving',
        'just', 'cunning', 'compassionate',
        'cold-hearted', 'principled', 'opportunistic',
        'forgiving', 'grudge-holding', 'charitable',
        'greedy', 'noble-spirited',
    ],
    'intellect': [
        'scholarly', 'simple-minded', 'cunning',
        'absent-minded', 'sharp-witted', 'naive',
        'perceptive', 'oblivious', 'philosophical',
        'literal-minded', 'inquisitive', 'incurious',
        'shrewd', 'bookish', 'street-smart',
    ],
    'humor': [
        'sarcastic', 'deadpan', 'mirthful',
        'dark-humored', 'self-deprecating', 'witty',
        'prankster', 'humorless', 'dry',
        'bawdy', 'whimsical', 'sardonic',
        'teasing', 'earnest', 'irreverent',
    ],
    'demeanor': [
        'stoic', 'dramatic', 'gruff',
        'gentle', 'stern', 'playful',
        'solemn', 'lighthearted', 'imposing',
        'unassuming', 'eccentric', 'dignified',
        'wild', 'composed', 'theatrical',
        'mysterious', 'plain-spoken',
    ],
    'drive': [
        'glory-seeker', 'duty-bound', 'treasure-hunter',
        'wanderer', 'protector', 'knowledge-seeker',
        'thrill-chaser', 'peacekeeper', 'avenger',
        'survivor', 'storyteller', 'homeward-bound',
        'legend-chaser', 'debt-payer', 'oath-keeper',
    ],
    'loyalty': [
        'fiercely loyal', 'lone wolf', 'pack-minded',
        'oath-sworn', 'fickle', 'devoted',
        'mercenary-hearted', 'clan-first',
        'bonds slowly', 'trusts too easily',
        'betrayal-scarred', 'ride-or-die',
        'fair-weather friend', 'blood-brother type',
        'wary of attachments', 'protective of friends',
    ],
    'discipline': [
        'military-minded', 'free-spirited', 'rigid',
        'improviser', 'by-the-book', 'anarchic',
        'meticulous', 'sloppy', 'drill-hardened',
        'self-taught', 'battle-drilled', 'undisciplined',
        'ritualistic', 'adaptable', 'routine-bound',
    ],
    'faith': [
        'deeply devout', 'quietly faithful', 'agnostic',
        'lapsed believer', 'zealous', 'spiritually torn',
        'fate-trusting', 'godless', 'prayer-muttering',
        'Light-questioning', 'ancestor-honoring',
        'doom-prophesying', 'miracle-hoping',
        'heretical', 'pilgrim-souled', 'blessing-counting',
    ],
    'pride': [
        'humble', 'vain', 'quietly confident',
        'boastful', 'self-doubting', 'arrogant',
        'modest to a fault', 'glory-hungry',
        'shame-carrying', 'unflappable ego',
        'easily embarrassed', 'swaggering',
        'dignified', 'insecure', 'self-assured',
        'honor-proud', 'hides behind bravado',
    ],
    'awakening': [
        'spiritually attuned', 'soul-searching',
        'enlightenment-seeking', 'inner-peace-finding',
        'third-eye-open', 'cosmically aware',
        'unawakened', 'spiritually dormant',
        'transcendence-chasing', 'meditation-practicing',
        'veil-piercing', 'aura-sensing',
        'past-life-remembering', 'chakra-aligned',
        'existentially questioning', 'ego-dissolving',
        'oneness-feeling', 'materially grounded',
        'between-worlds', 'divinely inspired',
    ],
    'arcane': [
        'mystical', 'occult-minded', 'enigmatic',
        'attuned to ley lines', 'spirit-touched',
        'rune-obsessed', 'shadow-whisperer',
        'star-gazer', 'void-curious', 'flame-drawn',
        'frost-blooded', 'nature-bonded',
        'death-touched', 'light-devoted',
        'fel-scarred', 'dream-walker',
        'ancestor-speaker', 'totem-listener',
    ],
    'quirk': [
        'superstitious', 'nostalgic', 'perfectionist',
        'absent-minded', 'competitive', 'sentimental',
        'paranoid', 'daydreamer', 'stubborn',
        'impulsive', 'methodical', 'hot-headed',
        'easily distracted', 'overly literal',
        'chronically late', 'hums when nervous',
        'talks to their weapon', 'collects bones',
        'afraid of the dark', 'never sits down',
    ],
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
# ZONE FLAVOR - Short zone context for chat prompts
# =============================================================================
# One paragraph per zone, summarizing the full zone description in
# subzone_lore.json (read by get_zone_lore()). Written in the world's
# voice for the WotLK 3.3.5 timeline: geography, climate, history and
# inhabitants, no game terms, no quest plots, neutral between the
# Alliance and the Horde. Keep the "<Zone name>: " prefix.
ZONE_FLAVOR = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Khaz Modan
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Snowbound highlands among the peaks of Khaz Modan, home of the dwarves of Ironforge and the exiled gnomes of Gnomeregan. Snow blankets the rocky hills, frozen lakes glint under a pale sun, and silent pine forests stand under heavy drifts. The air is sharp with frost, woodsmoke and the smell of the forge. Dwarven villages keep their fires burning against the endless cold, while troggs, frost trolls, wolves and bears make the wilds dangerous.""",

    1537: """Ironforge: The ancient capital of the dwarves, a vast city carved into the heart of a mountain in Dun Morogh. Torchlit halls and stone passages surround the Great Forge, fed by rivers of molten rock, where King Magni Bronzebeard rules Khaz Modan from the High Seat. The exiled gnomes of Gnomeregan live in Tinker Town, the Explorers' League seeks the secrets of dwarven origins in the Hall of Explorers, and the Deeprun Tram runs beneath the earth to Stormwind. The air is warm, smoky and loud with hammers and laughter.""",

    38: """Loch Modan: Rugged hills and green valleys in eastern Khaz Modan, around a great loch held back by the Stonewrought Dam, a marvel of dwarven engineering. The climate is cool and damp, with mists on the water, frequent rain and chill mornings. Dwarves fish the loch, mine the cliffs and cut timber from the town of Thelsamar. Broken Horde siege engines from the Second War still rust on the islands. Troggs infest the valleys, kobolds hold a mine, ogres keep a stronghold in the northeast, and Dark Iron dwarves threaten the dam.""",

    330: """Thandol Span: A massive dwarven bridge over the deep sea channel between Khaz Modan and Lordaeron, linking the Wetlands with the Arathi Highlands. For centuries it carried armies and trade between the dwarves and the northern human kingdoms. The Scourge damaged it in the Third War, and a Dark Iron attack has all but destroyed one of its bridges, leaving great sections lying beneath the waves. It is still the only land route between Lordaeron and the south. Wind and sea spray whip across its heights.""",

    269: """Dun Algaz: A tunneled mountain pass and old dwarven stronghold linking Loch Modan to the Wetlands, guarded at its southern end by the Algaz Gate. In the Second War it was the Horde's last hold in Khaz Modan. It remains the main road between the dwarven lands and Menethil Harbor, but Dragonmaw orcs have overrun the outpost in the middle of the pass, and dwarven mountaineers hold only the upper tunnel. The tunnels are dark, cold and echoing, and the road through them has become dangerous.""",

    11: """Wetlands: A vast, cold marshland in northern Khaz Modan, laced with rivers, bogs and reed-choked channels between the mountains and Baradin Bay. Mist cloaks the ground, the sky is a uniform grey and rain falls often. Once a land of Wildhammer strongholds, it was ravaged in the Second and Third Wars, when the Dragonmaw held Grim Batol and enslaved the Dragonqueen Alexstrasza. Menethil Harbor on the western coast links Khaz Modan by sea with Kalimdor and Northrend. Dragonmaw remnants, Dark Iron dwarves, gnolls, murlocs, raptors and crocolisks make the marshes dangerous.""",

    3: """Badlands: A sun-scorched wasteland of cracked red earth, mesas and winding canyons in southern Khaz Modan. Water is scarce, the days are fiercely hot and dust storms sweep the barren flats, where coyotes, buzzards, scorpids, basilisks and rock elementals survive. In the north lies Uldaman, a titan vault unearthed by dwarven digs and now defended by the troggs it awakened. Dark Iron dwarves dig there for their master Ragnaros, Dustbelcher ogres roam the land, black dragons nest in the eastern canyons, and the Horde holds the fortress of Kargath.""",

    51: """Searing Gorge: A volcanic wasteland of ash, cinders and lava between the Badlands and Blackrock Mountain, once part of the green Redridge Mountains until Thaurissan's summoning of Ragnaros shattered the land. The air is hot, dry and choked with smoke, and fire elementals roam among scorched rock. Dark Iron dwarves rule the gorge and work enslaved captives in the great excavation of the Cauldron. On its northern edge, the craftsmen of the Thorium Brotherhood, who broke away from their clan, keep the neutral town of Thorium Point.""",

    25: """Blackrock Mountain: A towering, still-active volcano between the Searing Gorge and the Burning Steppes, raised when the Dark Iron sorcerer-thane Thaurissan summoned the Firelord Ragnaros. The Dark Irons carved a vast city in its depths, and Blackrock Spire rises above. It is bitterly contested: Ragnaros and his Dark Iron servants rule the depths and the molten core, while the black dragon Nefarian commands orcs, ogres and dragonkin from the heights of the spire. Chains and platforms span a chamber of molten rock, and the heat, smoke and constant rumble never cease.""",

    46: """Burning Steppes: A scorched volcanic land south of Blackrock Mountain, the only land passage between Stormwind and Khaz Modan. Charred earth, craggy foothills and lava rivers lie under a sky glowing red from the mountain, with ash drifting on hot, dry air. Abandoned by Stormwind, the steppes are held by the minions of the black dragonflight and the agents of Ragnaros: Blackrock orcs who reject Thrall, Fire-Gut ogres, black dragons and Dark Iron dwarves. Here Anduin Lothar fell at the end of the Second War. The Alliance clings to Morgan's Vigil.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Azeroth
    # -------------------------------------------------------------------------
    12: """Elwynn Forest: The green heartland of the Kingdom of Stormwind, a mild land of oak and pine forests, meadows, lakes and farms south of the capital, with the village of Goldshire at its center and Northshire Abbey in a valley to the north. The Horde razed it in the First War, and the unpaid stonemasons who rebuilt Stormwind became the Defias Brotherhood. Its peace is fragile: Defias bandits seize farms, kobolds infest the mines, gnolls camp on the western border and murlocs haunt the lakes, while the guard is stretched thin by distant wars.""",

    1519: """Stormwind City: The capital of the Kingdom of Stormwind and the grandest human city in the world, rebuilt after the First War with white stone walls, blue-roofed towers and districts divided by canals. King Varian Wrynn rules from Stormwind Keep after his long absence. The Cathedral of Light is the heart of the faith of the Holy Light, and the city holds the Trade District, Old Town with SI:7, the Mage Quarter, the Dwarven District with the Deeprun Tram to Ironforge, and the Park with its moonwell. Humans, dwarves, gnomes, night elves and draenei walk its streets.""",

    40: """Westfall: Rolling farmland on the western coast of Stormwind, once the kingdom's breadbasket and now fallen into ruin. Fields lie fallow, the grass is yellow and sea winds carry dust over empty farmsteads. The Defias Brotherhood, outlaws born from the unpaid stonemasons of Stormwind, drove off many farmers, hold the ghost town of Moonbrook and set rogue harvest watchers loose in the fields. Gnolls raid from the south and murlocs prowl the coast. The People's Militia holds out at Sentinel Hill, and the farmers feel forgotten by the crown.""",

    44: """Redridge Mountains: Red-hued peaks, tall elms and rushing rivers east of Elwynn Forest, around the blue expanse of Lake Everstill and the old town of Lakeshire. Its hardy, self-governing folk supply Stormwind with timber, fish and crops. The range was shattered long ago by the summoning of Ragnaros. Today it is a frontier: Blackrock orcs from the Burning Steppes have seized the stronghold of Stonewatch and camp in the hills, gnolls claim the canyons, murlocs infest the lake and black whelps roam the heights. Lakeshire relies on its own small guard.""",

    10: """Duskwood: A dark, cursed forest south of Elwynn, once a bright woodland and now swallowed by an unnatural, eternal twilight. Black fog hangs among twisted trees, and the air is cold and smells of rot. Some blame the evil of Karazhan, others an ancient artifact and the worgen that came with the curse. The dead rise from the graveyards, worgen and giant spiders stalk the woods, and the Black Riders are said to ride out of the night. The stubborn people of Darkshire, guarded by the Night Watch, feel abandoned by Stormwind.""",

    41: """Deadwind Pass: A desolate, cursed canyon between Duskwood and the Swamp of Sorrows, where trees stand leafless and petrified, the grass is grey and a foul, keening wind never stops. Storms brew constantly and lightning strikes the barren rocks. In the south stands Karazhan, the tower of Medivh, the last Guardian of Tirisfal, who opened the Dark Portal; evil magic still leaks from it and drains the life from the land. Ogres, restless spirits and carrion birds haunt the pass, and it is whispered that a new dark presence has claimed the tower.""",

    8: """Swamp of Sorrows: A stagnant, mist-shrouded marsh of bogs, weeping willows and brackish pools east of Deadwind Pass, once the northern Black Morass. The air is humid and heavy, and crocolisks, jaguars, spiders and bog beasts lurk in the reeds. The Atal'ai built a temple to the blood god Hakkar here, and the Dragon Aspect Ysera drowned it beneath the largest bog, where her dragonspawn still keep watch. The Horde holds the rebuilt town of Stonard. Lost Ones and Broken draenei stranded on Azeroth live in the swamp, and murlocs inhabit the coast.""",

    4: """Blasted Lands: A scorched desert of crimson clay south of the Swamp of Sorrows, once the southern Black Morass, twisted by the magic of the Dark Portal. Lightning strikes often, nothing fertile grows, the days are hot and the nights bitterly cold. Mutated basilisks, scorpids and hyenas roam the land. The Dark Portal stands in a great crater in the southeast, open once more to Outland, and armies of the Alliance and the Horde guard its foot. Nethergarde Keep, founded by Khadgar, watches from the north; Dreadmaul ogres and Legion remnants lurk in the waste.""",

    33: """Stranglethorn Vale: A vast, steaming jungle across the southern tip of the Eastern Kingdoms, full of towering trees, vines and thorny undergrowth, alive with tigers, panthers, raptors, gorillas and crocolisks. It was the heart of the Gurubashi troll empire until the summoning of Hakkar tore it apart; ruins now cover the land, the Bloodscalp and Skullsplitter tribes fight outsiders, and Zul'Gurub has fallen again under Hakkar's sway. Goblins, pirates, ogres, naga and rebels all claim a share. Booty Bay is the bustling neutral port on the southern cape, and the Horde keeps Grom'gol on the coast.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Lordaeron
    # -------------------------------------------------------------------------
    85: """Tirisfal Glades: Rolling wooded hills on the northern coast of Lordaeron, once the heartland of the human kingdom and now the homeland of the Forsaken of Sylvanas Windrunner. The sky is gloomy and tinted green, and cold mist drifts over abandoned farms, silent lakes and ruined mills, yet the land keeps a melancholy beauty, especially around the village of Brill. Here Kel'Thuzad first spread the plague, and Arthas slew his father. Beneath the ruined capital lies the Undercity. The Scourge still haunts the farms, the Scarlet Crusade holds its monastery, and the Bulwark faces the Plaguelands.""",

    1497: """Undercity: The capital of the Forsaken, a vast underground city beneath the ruins of Lordaeron's royal capital, built from the old royal crypts, dungeons and sewers. Arthas began expanding it, and Sylvanas finished it after driving out the dreadlords. It is dark, cold and labyrinthine, built in rings around the Trade Quarter, with the Magic, Rogues' and War Quarters and the Apothecarium, where the Royal Apothecary Society brews plagues and poisons. Green sludge flows in its canals, great lifts carry travelers to the ruins above, and Sylvanas rules from the Royal Quarter.""",

    130: """Silverpine Forest: An ancient wood of tall, silver-barked pines along the western coast of Lordaeron, haunted and sickly since the Scourge burned and slaughtered its way through in the Third War. Ghostly mists drift among the trees, and razed farmsteads and abandoned mines dot the land. The Forsaken hold the north from the Sepulcher and fight plague-ridden gnolls. In the south, Dalaran's wizards guard Ambermill, Pyrewood Village bears a curse that turns its people into worgen at night, Arugal broods in Shadowfang Keep, and the Greymane Wall seals away Gilneas.""",

    170: """Lordamere Lake: One of the largest lakes in the Eastern Kingdoms, a vast expanse of cold, grey water at the heart of the fallen Kingdom of Lordaeron, whose capital once stood on its northern shore. Around it lay Lordaeron, Dalaran and Alterac, the great realms of the old Alliance. Today it divides the Forsaken lands from the Alterac Mountains. Fenris Isle and its dark keep lie at its center, the Dawning Isles form the rim of an ancient volcano, and an old plague left its waters strangely empty of life. Mist often hangs over the lake, and Vile Fin murlocs camp on its shores.""",

    267: """Hillsbrad Foothills: Green rolling hills, meadows, pine groves and farmland in southern Lordaeron, the best-preserved region of the fallen kingdom. A river from Darrowmere Lake runs through the hills, and small islands dot the southern coast. It is also one of the most blood-soaked battlefields in Azeroth: the first battle of the Second War was fought here, and Durnholde held the orc internment camps where young Thrall was a slave. The human town of Southshore and the Forsaken of Tarren Mill wage a bitter struggle, while the Syndicate holds Durnholde's ruins.""",

    36: """Alterac Mountains: Snow-capped peaks north of Hillsbrad, once the human kingdom of Alterac, destroyed by the Alliance after Lord Perenolde betrayed it to the Horde. The exiled nobles formed the Syndicate, which holds the Uplands and camps above Hillsbrad, while Crushridge ogres occupy the ruins of Alterac City. On the shore of Lordamere Lake lies the crater where Dalaran stood before it flew to Northrend. In a hidden valley the Frostwolf orcs battle the dwarves of the Stormpike Expedition, and the secretive Ravenholdt Manor hides among the peaks. Yetis and mountain lions roam the snows.""",

    45: """Arathi Highlands: Grey, windswept uplands of rolling grass and rocky outcrops in southeastern Lordaeron, the cradle of human civilization, where Thoradin founded the Empire of Arathor and humans and high elves first allied against the Amani. The kingdom of Stromgarde later rose here, but the Syndicate and Boulderfist ogres overran its capital, and its army now holds out at Refuge Pointe. The Horde holds Hammerfall, the old internment camp. Ogres, forest trolls, raptors and kobolds roam the land, and ancient stone circles are said to bind something imprisoned.""",

    293: """Thoradin's Wall: An immense stone wall on the border between the Hillsbrad Foothills and the Arathi Highlands, built in ancient times by King Thoradin, founder of the Empire of Arathor, against the Amani trolls. It later shielded Stromgarde from the advancing Scourge. Now it is collapsed and gaping, its great gate open and sections crumbled into rubble. The main road between Hillsbrad and Arathi passes beneath its shadow, a reminder of the glory of the first human empire and of how far its descendants have fallen.""",

    47: """The Hinterlands: A wild, mountainous land of lush forests, deep valleys and steep cliffs in the northern Eastern Kingdoms, untouched by the plague and mild in climate. It was the heart of the Amani troll empire, whose colossal ruins still stand among the trees. The Wildhammer dwarves of High Thane Falstad live above ground in Aerie Peak, a city carved like a gryphon's head, and ride the wild gryphons into battle. The Vilebranch hold Jintha'Alor, the Witherbark dwell in Shadra'Alor, and the Revantusk trolls have allied with the Horde. In the north, the tree of Seradane is a gateway to the Emerald Dream.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands, Quel'Thalas and southern isles
    # -------------------------------------------------------------------------
    28: """Western Plaguelands: A blighted land in northern Lordaeron, once the forested breadbasket of the kingdom's north. Here Kel'Thuzad and the Cult of the Damned poisoned Andorhal's grain with the plague of undeath. A smoky grey mist hangs over the land, the trees pulse with tumorous growths and the surviving beasts are blighted and savage. Undead infest Andorhal, the cauldron fields and the graveyards, and the Scourge trains necromancers in the Scholomance at Caer Darrow. The Scarlet Crusade holds Hearthglen, the Argent Dawn keeps Chillwind Camp, and the tomb of Uther the Lightbringer is one of the few peaceful places left.""",

    139: """Eastern Plaguelands: The more devastated half of the Plaguelands, once a land of farms and villages governed from Stratholme, where the Order of the Silver Hand was founded and Arthas carried out his purge. The Scourge's rule here is nearly absolute: the ground is brown and sick, trees have twisted into giant mushrooms and orange and green mists choke the air. Stratholme burns as the Scourge's capital in Lordaeron, and Plaguewood is full of ziggurats. The Scarlet Crusade holds Tyr's Hand, the Argent Dawn keeps Light's Hope Chapel open to all who fight the Scourge, and Acherus, the home of the death knights, hovers in the east.""",

    3430: """Eversong Woods: The enchanted forest at the heart of Quel'Thalas, standing in perpetual autumn under golden and crimson leaves, dotted with graceful spires, floating towers and arcane crystals. In the Third War, Arthas led the Scourge through the kingdom to the Sunwell and left the Dead Scar, a path of lifeless earth that cuts through the woods and Silvermoon itself. The survivors took the name blood elves and, under Regent Lord Lor'themar Theron, joined the Horde and rebuilt much of their land. Yet the Wretched haunt the ruins, arcane constructs run wild, trolls lurk in the hills and the runestones holding back the blight are weakening.""",

    3487: """Silvermoon City: The capital of the blood elves in Eversong Woods, founded thousands of years ago and perhaps the oldest capital still standing. Arthas led the Scourge through its gates in the Third War and slew the king. The blood elves have rebuilt the eastern half to much of its former glory, with golden spires, floating platforms, chained crystals brimming with magic and lush gardens, while the western half still lies in ruins beyond the Dead Scar. Regent Lord Lor'themar Theron rules from the Sunstrider Spire, arcane guardians patrol the streets, and an orb of translocation links the city to the Undercity.""",

    3433: """Ghostlands: The southern part of Quel'Thalas, a shadowy land of withered black trees, gloomy skies and deathly chill, devastated when the Scourge marched to the Sunwell and never recovered. The Dead Scar runs from Deatholme, the Scourge citadel ruled by the traitor Dar'Khan Drathir, who helped Arthas breach the kingdom. Ghosts of slain elves haunt the ruined villages. Blood elves and their Forsaken allies hold Tranquillien and strive to reclaim the land, while Amani trolls lurk near Zul'Aman in the east. The Thalassian Pass leads south through an ancient Elfgate to the Plaguelands.""",

    4080: """Isle of Quel'Danas: An island off the northern coast of Eversong Woods, where the founders of Quel'Thalas created the Sunwell, a fountain of immense power, seven thousand years ago. Arthas defiled it to raise Kel'Thuzad. In recent times the island became the stage of a desperate struggle, as Kael'thas Sunstrider and the Burning Legion sought to use the Sunwell as a gateway, and the Shattered Sun Offensive of the Aldor and Scryers made the harbor of Sun's Reach its base. Battle scars mark the land, yet its golden forests, white beaches and elegant spires remain beautiful, and the Sunwell Plateau rises at its heart.""",
    4298: """The Scarlet Enclave: The far eastern corner of the Plaguelands, a stretch of coast beyond Tyr's Hand that the Scarlet Crusade made its last refuge from the plague, with the town of New Avalon, the farms, mills and mine of Havenshire, the Chapel of the Crimson Flame and the anchorage of King's Harbor. Long spared the worst of the plague, its orchards and fields fed the Crusade's soldiers and the survivors under their protection. Over the western heights hangs Acherus, a vast floating necropolis and the home of the death knights, and from the barren plateau of Death's Breach beneath it the whole enclave lies in plain view.""",

    408: """Gillijim's Isle: A remote jungle island in the South Seas off the southern coast of Stranglethorn Vale. Old charts mark it as a former troll island, but few living sailors have set foot on its shores, and it lies far from the usual shipping lanes. The surrounding sea is warm, deep and blue, home to sharks and other creatures of the open ocean, and the currents can carry the unwary far from land. Tales speak of ancient troll ruins hidden in its jungles, but its secrets remain lost to most of the world.""",

    409: """Island of Doctor Lapidis: A remote jungle island in the South Seas off the southwestern coast of Stranglethorn Vale. Old charts mark crumbling ruins of the ancient jungle trolls there, but few have visited it in living memory, and the meaning of its name is known to few. The waters around it are deep, warm and empty of ships, home only to sharks and creatures of the open sea. It remains a mystery, a dark speck on the horizon that most sailors prefer to avoid.""",

    # -------------------------------------------------------------------------
    # Kalimdor - North
    # -------------------------------------------------------------------------
    141: """Teldrassil: A colossal World Tree rising from the Veiled Sea off northwestern Kalimdor, so vast that a land of forests, hills and lakes grows on its boughs above the clouds. Archdruid Fandral Staghelm grew it after the night elves lost their immortality, and their capital Darnassus stands in its western branches. The land lies in an eternal violet twilight, full of ancient trees, moonwells, wisps and nightsabers. But the tree was never blessed by the Dragon Aspects, and a creeping corruption is spreading: furbolgs have turned savage, timberlings rage and satyrs lurk in caves. Rut'theran Village at its foot is the harbor to the wider world.""",

    1657: """Darnassus: The capital of the night elves, built in the western boughs of Teldrassil and bathed in eternal violet twilight. Graceful terraces of living wood and white stone surround a central lake, joined by arching bridges. High Priestess Tyrande Whisperwind leads the night elves from the Temple of the Moon, while Archdruid Fandral Staghelm leads the Cenarion Circle from the Cenarion Enclave, often at odds with her. Malfurion Stormrage remains lost in the Emerald Dream. Sentinels and ancients guard the quiet, somewhat melancholy city, and a portal leads down to Rut'theran Village.""",

    148: """Darkshore: A long, rocky coast in northwestern Kalimdor of shadowed woods, misty beaches and crumbling ruins, where the weather is cold and stormy and fog is common. Once a prosperous region of the ancient Kaldorei empire, it was ravaged by the Great Sundering, and its cities have stood empty for thousands of years. The night elves rebuilt the port of Auberdine, the link to Teldrassil, the Azuremyst Isles and the Eastern Kingdoms. Beyond it, naga, satyrs and Highborne ghosts haunt the ruins, cultists hide in secret places, and furbolgs have been driven mad by corruption flowing down from Felwood.""",

    3524: """Azuremyst Isle: The larger of the Azuremyst Isles off western Kalimdor, long home only to furbolgs, owlkin and wild beasts, until the Exodar, the dimensional ship of the draenei, crashed onto its shores. The survivors under the Prophet Velen built their capital in its largest intact section. The island is a land of evergreen forests, purple flowers and rolling hills, but strange crystals from the wreck dot the landscape, arcane storms ripple across the sky and the crash has mutated some plants and animals. The friendly Stillpine furbolgs live in the north, naga lurk in old ruins and blood elf saboteurs hide in the hills.""",

    3557: """The Exodar: The capital of the draenei, built within the largest intact section of the dimensional ship that crashed on Azuremyst Isle. Once a satellite of Tempest Keep, it was seized in Outland by the Prophet Velen and his followers with the help of the naaru, sabotaged by blood elves and sent hurtling through the Twisting Nether. Now it is a city of gleaming crystal halls and glowing conduits that carry holy light and warmth. Velen resides in the Seat of the Naaru beside a naaru, and the city hums with the song of the naaru and the quiet devotion of a people who have wandered for thousands of years.""",

    3525: """Bloodmyst Isle: The northern of the two Azuremyst Isles, once called Silvergale, corrupted when pieces of the crashed Exodar scattered blood-red crystals across it. A blood-like liquid seeps from the crystals into the soil, mutating plants and beasts and filling the air with an eerie crimson mist; even the pines have turned red. The draenei study and heal the land from Blood Watch, facing blood elf invaders after the crystals' power, satyrs, naga, corrupted furbolgs and creatures escaped from the ship. Ancient night elf ruins dot the island, and the spirits of green dragons haunt Wyrmscar.""",

    331: """Ashenvale: A vast, ancient forest in northern Kalimdor and the ancestral homeland of the night elves, a primordial wilderness of towering trees, deep glades, lakes and rivers under a thick canopy. For thousands of years the night elves tended it without cutting it, guarded by Sentinels, druids and ancients. In the Third War, Grom Hellscream's orcs came for its lumber and slew the demigod Cenarius. Since then it has been bitterly contested: the night elves hold Astranaar in the west, the Warsong clan cuts timber in the east, and the Silverwing Sentinels and Warsong Outriders clash constantly. Demons, satyrs and corrupted furbolgs linger.""",

    361: """Felwood: A corrupted forest in northern Kalimdor, once a lush paradise protected by Cenarius, befouled by the Burning Legion with the Skull of Gul'dan in the Third War. Twisted trees, charred meadows and streams boiling with toxic sludge fill the land, and the ancients that once guarded it roam blindly, bleeding fel poison. Corrupted furbolgs, satyrs, demons and Shadow Council warlocks infest the woods, and starving beasts turn on each other. The druids of the Cenarion Circle strive to cleanse it, and the uncorrupted Timbermaw furbolgs hold the northern tunnels to Moonglade and Winterspring.""",

    493: """Moonglade: A sacred valley on the lower slopes of Mount Hyjal, sheltered by tall mountains and draped in perpetual night, where the moon bathes the land in silver and the air is a warm, endless summer eve. It is the home of the Cenarion Circle, where night elves and tauren live together in peace, and conflict between the races is not tolerated. For thousands of years the druids slumbered in the Barrow Dens here while their spirits walked the Emerald Dream; Malfurion Stormrage remains lost there still. The village of Nighthaven lies on the shores of Lake Elune'ara, watched over by the Keepers of the Grove.""",

    618: """Winterspring: A cold, snowy valley high on Mount Hyjal, in near-perpetual winter above the clouds over Moonglade. Snow blankets the hills, frozen lakes glitter and the air is crisp and clean. Night elves settled here after the Great Sundering, and their ruins still stand in the snow, while the exposed roots of the World Tree tower overhead like archways. The blue dragonflight of Mazthoril has long contended with the night elves. The goblin town of Everlook is open to all, corrupted Winterfall furbolgs, yetis and frostsabers roam the land, and demons hold Darkwhisper Gorge in the south.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Center and East
    # -------------------------------------------------------------------------
    14: """Durotar: A land of red, sun-baked earth, rugged canyons and rocky hills on the eastern coast of Kalimdor, whose harsh beauty recalls Draenor. Thrall claimed it as the new homeland of the orcs and Darkspear trolls after the Third War and named it for his father Durotan, founding Orgrimmar at its northern edge. It is the heart of the Horde, with Razor Hill at its crossroads and the troll village of Sen'jin on the southern coast. Dangers remain: quilboar raid from the west, centaurs lurk in the south, harpies nest in the canyons, the Burning Blade hides in caves and a Kul Tiran fortress still stands on the coast.""",

    1637: """Orgrimmar: The capital of the orcs and seat of the Horde, a mighty fortress city built into a canyon at the northern edge of Durotar, founded by Warchief Thrall after the Third War and named for Orgrim Doomhammer. Stout walls, massive gates and tall towers guard it, and its districts are valleys: Strength, the commercial heart; Spirits, home of trolls and shamans; Wisdom, where Thrall's Grommash Hold stands; and Honor. The Drag leads to the shadowy Cleft of Shadow. Its rustic wood, hide and stone are hung with spikes and banners, and zeppelins link it to the Eastern Kingdoms and Northrend.""",

    2917: """Hall of Legends: The great officers' hall of the Horde in the Valley of Strength in Orgrimmar, a massive building of wood, stone and hide hung with banners, trophies and the weapons of fallen enemies. It serves as barracks and gathering place for the Horde's most distinguished warriors, and its secret armory holds weapons from every continent of Azeroth and from Draenor, many of them spoils of war with proud histories. It is a place of honor and pride, where tales of glory are told around great fires and the legends of the Horde are remembered.""",

    377: """Southfury River: One of the great rivers of Kalimdor, rising from the highlands of Mount Hyjal and running south as a wide, swift river. It divides Ashenvale from Azshara and, further south, the Barrens from Durotar, passing near the walls of Orgrimmar. Its waters run cold and fast in the north and warm and murky in the south, where crocolisks lurk among the reeds. It empties into the Great Sea in a cascading waterfall near the goblin port of Ratchet. Bridges cross it at a few points, and travelers of every kind pass over its waters.""",

    16: """Azshara: A beautiful but cursed coastal land in northeastern Kalimdor, cloaked in eternal autumn, with brilliant orange and red trees, great cliffs and white beaches. Ten thousand years ago it was part of Zin-Azshari, the capital of Queen Azshara, until the Great Sundering drowned much of the city. Night elves consider it cursed; ruins perch on the cliffs and lie among the coral, and tales say the queen now rules the naga beneath the waves. Highborne ghosts, satyrs, naga and blue dragons haunt the land, the friendly Timbermaw hold the western mountains, and storms often sweep in from the sea.""",

    17: """The Barrens: A vast, hot savanna of yellow grass, thorny trees and dusty plains in central Kalimdor, between Ashenvale and Thousand Needles, with a few lush oases in the north. Night elf cities stood here before the Sundering, and the ancient Gold Road still carries caravans between Ratchet and the north. The Horde's Crossroads is the main hub, while the Alliance holds Northwatch Hold and the dig at Bael Modan. Centaurs and quilboar raid caravans, harpies nest in the hills, the Venture Company drills for oil and the Burning Blade hides on Dreadmist Peak. Ratchet on the coast is open to all.""",

    215: """Mulgore: Green plains and windswept mesas in central Kalimdor, the ancestral homeland of the tauren, walled by mountains with a single pass east to the Barrens. For centuries the tauren roamed as nomads, warring with the centaurs, until Thrall's Horde helped drive them out and Cairne Bloodhoof built Thunder Bluff atop the mesas. It is a sheltered, pastoral land of grasslands, clear lakes and pine-scented breezes, with tauren villages, windmills and carved totems. Quilboar hold the sacred Red Rocks, the Venture Company has seized the sacred wells and harpies nest in the north.""",

    1638: """Thunder Bluff: The capital of the tauren, built atop four towering mesas in northern Mulgore, high above the Golden Plains, the first permanent city of a people who wandered for centuries. Great tents, longhouses and totem poles crown the mesas, joined by swaying rope bridges, and wooden lifts carry visitors up from the plains. High Chieftain Cairne Bloodhoof rules from the central mesa, the druids gather on Elder Rise, the shamans on Spirit Rise above the misty Pools of Vision, and the hunters on Hunter Rise. The weather is warm and sunny, and the view over Mulgore is breathtaking.""",

    406: """Stonetalon Mountains: A rugged range in central Kalimdor, thrust high by the Great Sundering and carved by the Blackwolf River into canyons and cliffs. The lower slopes are hot, dry and windy, rain breaks on the western peaks and the violent Ill Winds whip through the canyons. Stonetalon Peak, sacred to night elves and tauren, was once the home of the Oracle. The goblins of the Venture Company are cutting down the ancient forests and fouling the waters, the Charred Vale is a burned ruin full of fire elementals, harpies hold canyon strongholds and renegade Grimtotem tauren attack their own kin.""",

    # -------------------------------------------------------------------------
    # Kalimdor - South
    # -------------------------------------------------------------------------
    405: """Desolace: A grey, rocky wasteland in western Kalimdor that seems to lie under a curse: the sky is always dark and stormy, lightning and high winds sweep the land, yellow polluted pools dot the ash and the skulls of ancient kodo stare from their graves. It is the homeland of the centaurs, said to be born in the depths of Maraudon, and four warring tribes fight each other as fiercely as outsiders. Ruins of the Highborne stand scattered across the land, naga haunt the northwest coast and the Burning Blade has summoned demons here. In sad contrast, the western coast is sunny and lush.""",

    357: """Feralas: A lush, ancient rainforest in southwestern Kalimdor of huge trees, misty valleys, rushing rivers and clear lakes, sheltered by high mountains. It was part of the night elf empire, and the vast Highborne city of Eldre'Thalas, now called Dire Maul, lies in ruins among the trees. The night elves hold Feathermoon Stronghold on Sardor Isle and the tauren keep Camp Mojache in the east. The bloodthirsty Gordunni ogres control many of the ruins, Grimtotem renegades keep a compound, naga infest the western isles, and a great tree in the northwest is a portal to the Emerald Dream.""",

    400: """Thousand Needles: A vast, dry canyon in southern Kalimdor filled with towering sandstone spires that rise like a forest of needles, shaped by water before the Sundering lifted the land. In the east it opens onto the Shimmering Flats, a salt pan where goblin and gnomish engineers race their machines, and the sunrises from the mesas are spectacular. Tauren tribes long lived precariously atop the mesas and now fight back from Freewind Post. Galak centaurs patrol the canyon floor, Grimtotem renegades hold Darkcloud Pinnacle, and rope bridges link the spires above the dangers below.""",

    15: """Dustwallow Marsh: A vast, hot and fetid swamp on the eastern coast of central Kalimdor, sunk by the Great Sundering, where mosquitoes buzz, trees trail fronds into stagnant pools and mud banks divide algae-choked channels. Raptors, spiders, crocolisks and murlocs lurk everywhere, and in the south the black dragon Onyxia is said to dwell in the Wyrmbog. Jaina Proudmoore founded Theramore on an island off the coast, the Stonemaul ogres welcome the Horde at Brackenwall, and here Admiral Daelin Proudmoore met his end. Covert skirmishes continue despite the truce, and the goblins of Mudsprocket welcome all.""",

    2159: """Onyxia's Lair: A volcanic cave in the Wyrmbog of southern Dustwallow Marsh, the lair of Onyxia, the great black dragon and daughter of Deathwing, brood mother of the black dragonflight. The cave winds deep into the warm earth, and the main cavern holds her vast clutch of eggs, guarded by whelps and dragonspawn. The floor is a thin crust over molten rock, and the air is thick with smoke, brimstone and the stench of her victims, with bones and treasure scattered among the rocks. Travelers tell grim tales of those taken by her brood, and few who enter return.""",

    440: """Tanaris: A vast desert in southeastern Kalimdor, an endless sea of dunes under a cloudless sky, blazing by day and swept by dangerous sandstorms, with mountains and deep caverns in the south. It is the ancestral home of the bronze dragonflight, whose Aspect Nozdormu dwells in the Caverns of Time, and in the south lies the sealed gateway to the titan city of Uldum. The Steamwheedle goblins keep the neutral town of Gadgetzan and Steamwheedle Port. The Sandfury trolls rule from Zul'Farrak, ogres hold southern ruins, Wastewander bandits seize the water towers and pirates hide on the coast.""",

    1941: """Caverns of Time: A vast network of caves in eastern Tanaris, home of the bronze dragonflight and their Aspect Nozdormu, guardians of the flow of time. Portals within lead to key moments in the world's history, such as the opening of the Dark Portal, Thrall's escape from Durnholde, the Battle of Mount Hyjal and the culling of Stratholme. Sand gives way to lush growth, great hourglasses turn and colossal bronze dragon statues tower overhead. In recent times the infinite dragonflight has begun meddling with history, and the bronze dragons seek aid. Those who enter uninvited are said to emerge changed.""",

    490: """Un'Goro Crater: A vast, lush crater in southern Kalimdor between Tanaris and Silithus, cut off by towering walls. A steaming jungle of exotic plants and giant creatures fills it: devilsaurs, stegodons and pterrordax roam freely, gorillas dwell in the caves and silithid dig hives in the south. The active volcano of Fire Plume Ridge rises at its center, hot springs and tar pits bubble, and strange crystals and mysterious pylons dot the land. Many scholars believe it was a place of the titans. Explorers of all races gather at Marshal's Refuge on the northern wall, and the jungle never falls silent.""",

    1377: """Silithus: A harsh desert of rock and sand in the southwestern corner of Kalimdor, broken by the towering hives of the insectoid silithid. A thousand years ago their Qiraji masters waged the War of the Shifting Sands until the night elves and the dragonflights sealed them behind the Scarab Wall in Ahn'Qiraj. In recent times the gates were opened once more, and the armies of the Alliance and the Horde marched against the Qiraji. The Cenarion Circle watches from Cenarion Hold, the bronze dragonflight has returned and the Twilight's Hammer camps across the land. The heat is relentless and the wind carries stinging sand.""",

    3478: """Gates of Ahn'Qiraj: The great gates in the Scarab Wall at the southern edge of Silithus, guarding Ahn'Qiraj, the ancient stronghold of the Qiraji and their silithid. A thousand years ago the night elves and the dragonflights sealed the Qiraji behind the wall; in recent times the gates were opened once more with the Scepter of the Shifting Sands, and the armies of the Alliance and the Horde marched in. Beyond lie the Ruins and the Temple of Ahn'Qiraj, where the true masters of the Qiraji are said to dwell. The sand before the gates is scarred by battle, and an ominous silence hangs over them.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Hellfire Peninsula: A barren, blood-red wasteland in eastern Outland, the shattered remains of Draenor and the first land seen beyond the Dark Portal. Orc warlocks drained its life long ago, the cracked red ground bursts with fire geysers, and fragments of land float at its edges against the swirling sky of the Twisting Nether. Here the Alliance Expedition fought the Horde of Draenor and sealed the Portal. Today Hellfire Citadel is the stronghold of the fel orcs, the Burning Legion assaults the Stair of Destiny from its forge camps, the Alliance holds Honor Hold and the Horde holds Thrallmar.""",

    3521: """Zangarmarsh: A hauntingly beautiful swamp in western Outland, covered by a forest of giant mushrooms towering over its lakes like great trees. Glowing fungi, luminous spores and bioluminescent creatures fill its eternal twilight with blue and green light, and it largely escaped the corruption that ravaged Draenor. Now its balance is failing: the naga of Lady Vashj drain its waters with great pumps in Coilfang Reservoir, ogres cut down the mushrooms, and the marsh is dying. The Cenarion Expedition defends it from Cenarion Refuge, and the peaceful sporelings, a race of sapient fungi, live at Sporeggar.""",

    3519: """Terokkar Forest: A dark, ancient forest in southern Outland of tall crystal pines, deep green canopy and misty glades, home to the bird-like arakkoa, whose hidden capital Skettis lies in the southeastern mountains. In the northwest stands Shattrath City, a sanctuary for refugees of every race. The southern half is the Bone Wastes, laid waste when the Shadow Council summoned a terrible entity in the draenei necropolis of Auchindoun and tore a rift that drew the ethereals into Outland. The Alliance holds Allerian Stronghold and the Horde Stonebreaker Hold, while fel orcs and Shadow Council warlocks lurk in the woods.""",

    3703: """Shattrath City: The City of Light, the ancient draenei capital in northwestern Terokkar Forest, fallen to the demon-corrupted orcs and rebuilt by the Sha'tar, naaru born from light, with the draenei priests of the Aldor. Blood elves sent by Kael'thas to destroy it laid down their arms and became the Scryers, bitter rivals of the Aldor in the same city. The naaru A'dal rules from the Terrace of Light, where the Archmage Khadgar also resides. The Lower City is crowded with refugees of every race, violence between the Alliance and the Horde is forbidden, and portals link the city to the capitals of Azeroth.""",

    3917: """Auchindoun: The shattered necropolis of the draenei at the heart of the Bone Wastes in Terokkar Forest, for thousands of years their most sacred place, where they interred their honored dead. Agents of the Shadow Council summoned an ancient elemental of sound within it, and the ritual blew the temple apart, laid waste to the forest and tore a rift that drew the ethereals into Outland. The draenei dead now walk the ruins as restless spirits. Its halls are claimed by different powers: ethereals in the Mana-Tombs, demons in the Auchenai Crypts, arakkoa in the Sethekk Halls and the Shadow Council in the Shadow Labyrinth.""",

    3518: """Nagrand: The last unscarred land of Outland, rolling green and golden grasslands, sparkling lakes and floating islands drifting under a pink-tinged sky. Its name means Land of Winds; it was the homeland of the Frostwolf clan and the gathering place of the orcs beneath the sacred mountain Oshu'gun. Elementals commune with mortals at the Throne of the Elements. The uncorrupted Mag'har orcs live in Garadar under Greatmother Geyah, and the Kurenai Broken in Telaar. Warmaul and Boulderfist ogres threaten the land, the Legion has forge camps in the west, and the town of Halaa is fought over by the Alliance and the Horde.""",

    3522: """Blade's Edge Mountains: Knife-sharp crags and axe-cut valleys in northern Outland, worn by harsh winds into dagger-like spikes under the green glow of the Twisting Nether. It is the land of the Bladespire and Bloodmaul ogres, who fight each other for the favor of the gronn, giants ruled by Gruul the Dragonkiller from his lair in the north; the bones of slain black dragons hang impaled on the peaks. The Legion has forge camps on the plateaus and black dragon cultists lurk in the north. The night elves hold Sylvanaar, the Horde Thunderlord Stronghold, and the enlightened ogres of Ogri'la dwell on a western plateau.""",

    3523: """Netherstorm: Great fragments of land and countless shards of rock floating in the Twisting Nether in northeastern Outland, once the Fields of Farahlon. A constant arcane storm warps the land: the soil is sickly purple, magical lightning arcs through violet haze and bands of energy twist across the sky as the region slowly tears apart. Blood elves loyal to Kael'thas siphon the Nether with great manaforges built from the technology of Tempest Keep, which they hold, and the Burning Legion has bases across the islands. The ethereals of the Consortium keep the Stormspire and their eco-domes, and goblins run Area 52.""",

    3520: """Shadowmoon Valley: A grim, blasted land in southeastern Outland where molten fel energy erupts day and night and lights the sky with green flame. Black rock and ash cover the ground, and the volcano called the Hand of Gul'dan spews green lava at its center. In the east stands the Black Temple, once the draenei Temple of Karabor, now the citadel of Illidan Stormrage, the self-proclaimed Lord of Outland, and his Illidari, who hold off the Burning Legion of Legion Hold. Dragonmaw fel orcs enslave the Netherwing drakes. The Wildhammer Stronghold, Shadowmoon Village and the camps of the Aldor and Scryers wage war on Illidan.""",

    3540: """Twisting Nether: The chaotic astral realm between worlds, a dimension of wild magic that links the worlds of the universe and is home to the demons of the Burning Legion. When Draenor was torn apart, its remnants were pulled into the Nether, and at the edges of Outland the land simply ends in an endless void of prismatic clouds, ribbons of colored energy and drifting rocks. Distant worlds can be glimpsed in the swirling heavens, physical laws seem uncertain and the mind strains to make sense of what the eye sees. Those who stray too far may never return.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Borean Tundra: A vast, wind-swept plain on the southwestern edge of Northrend, for many the first land seen in the war against the Lich King. Red-brown earth, lichen and ice stretch under a wind that can strip the beard from a dwarf's face; geysers steam in the middle, and the snowy east is harshest. Mammoths and woolly rhinos roam the plains, and the peaceful tuskarr fish and whale along the coast, their villages ravaged by kvaldir raiders. Malygos and the blue dragonflight rule the island of Coldarra, the Scourge holds En'kilah, and the Alliance's Valiance Keep and the Horde's Warsong Hold face the north.""",

    495: """Howling Fjord: A rugged land in southeastern Northrend of green meadows, icy rivers, dark pine forests and towering fjords whose cliffs plunge into the cold sea. At the head of Daggercap Bay, Utgarde Keep rises above Lake Cauldros. It was the ancient seat of the vrykul, giant warriors awakened from their long sleep, many of whom now serve the Lich King and raid all who come near. The Alliance holds the old port of Valgarde and Westguard Keep, the Forsaken of the Hand of Vengeance hold Vengeance Landing and New Agamand, and the Explorers' League digs for titan ruins where iron dwarves have appeared.""",

    65: """Dragonblight: The heart of southern Northrend, an arctic waste of glaring white glaciers littered with the gleaming bones of dragons, the place where dragons come to die. Here the titans' keepers made the first Dragon Aspects, and the bones of Galakrond still jut from the ice. At its center rises Wyrmrest Temple, where the dragonflights gather, ringed by the five dragonshrines. The Scourge besieges the shrines and raises frost wyrms from the bones, Naxxramas hovers over the eastern plains, and the Scarlet Onslaught holds a fortress on the coast. The Alliance and the Horde have raised strongholds before the Wrathgate, the barred entrance to Icecrown.""",

    394: """Grizzly Hills: A forested region of southeastern Northrend, low green foothills laced with pines rising toward craggy mountains, where the thick forest blocks the wind and the hills seem almost warm. Bears, wolves, deer and snowy owls fill the woods. It is the homeland of the furbolgs, whose city of Grizzlemaw stands in the stump of Vordrassil, a World Tree the druids destroyed when they found it corrupted, and a creeping madness spreads among their tribes. Trappers keep trading posts in the forest, the Scourge holds Drak'Tharon Keep in the north, and the Alliance and the Horde contest the logging camps.""",

    4201: """Vordrassil's Tears: One of the great fallen segments of the World Tree Vordrassil in the Grizzly Hills. Long ago Fandral Staghelm planted branches of Nordrassil across Northrend, and the greatest, Andrassil, the Crown of the Snow, towered over these hills for decades. But its roots reached the prison of an ancient evil, and madness spread among the creatures of the land, so the Cenarion Circle destroyed it and renamed it Vordrassil, the Broken Crown. Its pieces still lie in the forest, and the land around this segment is covered in living ooze, sign of the corruption that doomed it.""",

    3477: """Azjol-Nerub: A vast underground kingdom beneath half of Northrend, the ancient realm of the arachnid nerubians, a culture devoted to scholarship, art and philosophy, with polished corridors, carved halls and great libraries lit by glowing fungi. The Lich King saw them as the greatest threat to his power and overran the kingdom in the War of the Spider; every nerubian who fell rose to fight for the Scourge, and their own king Anub'arak now serves him. Undead nerubians guard egg clutches in the Upper Kingdom, living survivors wage a hidden war, and in the Old Kingdom of Ahn'kahet faceless ones stir.""",

    66: """Zul'Drak: The homeland of the Drakkari ice trolls in eastern Northrend, a valley that is itself one vast temple city of plazas, ziggurats, walls and aqueducts raised in tiers, with thornwood trees, frozen ponds and snow between the ruins. The Drakkari are among the oldest races of Azeroth, ruling from Gundrak, but their empire is collapsing. The Scourge holds Drak'Tharon Keep and its necropolises raise fallen trolls against their own people. In desperation the Drakkari prophets have slain their own gods, the loa, and drunk their blood for power, driving many mad. The Argent Crusade and the Zandalari have come to intervene.""",

    3711: """Sholazar Basin: A tropical jungle basin in the middle of Northrend, ringed by towering mountains, hot, humid and teeming with life after the bitter cold outside. The keeper Freya made it a cradle of life, and titan pylons crowned with swirling crystals keep its warmth and protect it from foul creatures. Four rivers meet at River's Heart in the dense Wildgrowth Mangal. Rhinos, gorillas, crocolisks and hydras roam the jungle, and the gorloc Oracles war with the Frenzyheart wolvar. The Scourge has broken into the basin from the east, and the Avatar of Freya fights to contain the spreading blight.""",

    2817: """Crystalsong Forest: A land in the middle of Northrend where every tree, every blade of grass and much of the earth has turned to glowing living crystal, humming with the wind so that the forest plays a soft, unending music. It was once Moonsong, where the Highborne kept the outpost of Shandaral; when the blue dragons came for revenge over stolen relics, the sorcerers' reckless spell crystallized the whole forest, and their spirits still wander it. Dalaran now hovers over the western forest, the Silver Covenant and the Sunreavers hold ruined towers on opposite sides, and the blue dragonflight wages its Nexus War in the south.""",

    4395: """Dalaran: The city of the magi and home of the Kirin Tor, whose violet spires once stood by Lordamere Lake until the Scourge destroyed it in the Third War. The Kirin Tor have lifted the whole city into the sky and moved it to Northrend, where it floats above Crystalsong Forest to oppose the Lich King and the blue Aspect Malygos, whose war on spellcasters makes it a prime target. The Council of Six under the archmage Rhonin rules from the Violet Citadel. Dalaran welcomes the Alliance and the Horde alike: the Silver Covenant and the Sunreavers keep their own enclaves and eye each other warily.""",

    4197: """Wintergrasp: A frozen valley in central Northrend, raised above the surrounding lands, the bed of a shrunken lake that has revealed titan ruins, dark forests, frozen marshes and a volcanic cauldron. At its heart stands Wintergrasp Fortress, a titan complex guarding the entrance to the Vault of Archavon, which holds titan relics of untold power, watched over by ancient giants who resent all intruders. Since the war against the Lich King began, the Alliance and the Horde have fought endlessly for the fortress and the vault, battering its walls with siege engines while control changes hands again and again.""",

    67: """The Storm Peaks: A towering mountain range in northeastern Northrend, harsh and dangerous, where fierce winds can pluck a dwarf off a cliff, avalanches thunder down the slopes and the glare off the ice blinds the unwary. The peaks were the home of the titans' keepers, and nearly every mountain hides temples, terraces and vast machines; the Temple of Storms crowns the highest peak, and to the north lies Ulduar, the greatest titan complex on Azeroth. Its keeper Loken has turned to darkness, and his iron dwarves and giants drive the earthen from their home. The frost giants of the Sons of Hodir hold the eastern valleys.""",

    210: """Icecrown: The dark heart of Northrend and seat of the Lich King, a land of mountains and glacier where the ice has gone black with corruption. From the Frozen Throne the Lich King enslaved the peoples of Northrend and raised the Scourge, and around it stands Icecrown Citadel, a cathedral of saronite blades visible from almost anywhere on the continent. Saronite walls and walkways link fortresses, necropolises and mines, and the undead outnumber all else. Now the war has come to his doorstep: the Argent Crusade and the Knights of the Ebon Blade strike from captured strongholds, and the Alliance and Horde gunships battle in the skies above.""",

    4742: """Hrothgar's Landing: A small, mist-shrouded island off the northern coast of Icecrown, across the strait called the Sea Reaver's Run. A tuskarr village once stood here, until the kvaldir, the cursed sea vrykul, came under their chieftain Hrothgar, slew or drove off its people and renamed the island after him. Now it is a staging point for kvaldir raids on ships in the strait, where they call up great kraken from the depths, while the fleets of the Silver Covenant and the Sunreavers battle to drive them back.""",

    # -------------------------------------------------------------------------
    # Seas
    # -------------------------------------------------------------------------
    308: """The Forbidding Sea: A vast, cold and largely uncharted sea along the eastern coast of the Eastern Kingdoms, from the Swamp of Sorrows north to Eversong Woods. Its grey waters are rough and often fog-bound, strong currents and sudden storms make sailing dangerous, and much of the coast is walled by cliffs and mountains. Few ships venture far from shore, and sailors tell of unknown lands and terrible creatures beyond the horizon. Sharks and sea serpents dwell in its depths, and murlocs and naga lurk along its shores.""",

    214: """The Great Sea: The vast ocean between the continents of Azeroth, created when the Well of Eternity was destroyed and ancient Kalimdor split apart in the Great Sundering; every sea in the world connects to it. Its deep blue waters stretch beyond the horizon, and sailors tell of lost islands, sunken cities and the great whirlpool of the Maelstrom at its heart, where the Well once stood. Storms rise suddenly, and sea serpents, giant sharks and naga are said to lurk in its depths. Ships of the Alliance, the Horde, the goblins and the pirates cross it constantly between the continents.""",

    332: """The Great Sea: The open ocean between the continents of Azeroth, born when the Well of Eternity imploded in the Great Sundering. Far from any shore, only endless blue water stretches in every direction, broken by a distant island or a passing ship. The swell rises and falls, seabirds circle high above and creatures few have ever seen swim in the depths. Sailors speak with awe of the Maelstrom, the colossal whirlpool at the center of the sea, and of the countless ships lost to storms and the deep. It is a place of solitude and danger, where wind and waves rule.""",

    457: """The Veiled Sea: The great ocean off the western coasts of Kalimdor, stretching from Darkshore, Ashenvale, Desolace and Feralas into the unknown west. It is often shrouded in mist, which gave it its name; its waters are deep, cold in the north and warmer in the south. Teldrassil rises from it off the northwestern coast, and the Azuremyst Isles lie within it. Naga, sea giants and sea serpents dwell in its depths, and the drowned ruins of ancient night elf cities lie beneath its waves. Beyond the known coasts it is largely uncharted.""",

    3479: """The Veiled Sea: The waters around the Azuremyst Isles off northwestern Kalimdor, where the draenei vessel known as the Exodar crashed. The sea is deep and often veiled in mist, and debris and crystals from the fallen ship give some coastal waters a strange glow, above all around Bloodmyst Isle, whose shores run red. Murlocs and naga dwell along the coasts, drowned night elf ruins lie beneath the waves, and ships sail between the Exodar and the night elf lands, with Teldrassil rising from the sea to the east.""",

    3455: """The North Sea: The cold waters off the northern shores of Quel'Thalas, stretching from the coasts of Eversong Woods north toward Northrend. The Isle of Quel'Danas rises from them off the northern coast, and the elven ships that sail them have long linked the elves' homeland with the wider world. The waters are cold and grey, and the winds that blow across them carry the chill of the frozen north.""",

    4258: """The North Sea: The cold waters along the southeastern coasts of Northrend, off the Grizzly Hills and the Howling Fjord, reaching south toward the northern coasts of Lordaeron. Islands such as Bloodmoon Isle and the Ruins of Tethys dot the grey water. Alliance and Forsaken ships cross it bound for the fjord's harbors, while vrykul longships and kvaldir raiders prowl the mists.""",

    4630: """The North Sea: The frigid waters around the eastern and northern coasts of Northrend, grey and full of drifting ice beneath bitter winds. Few ships venture far into them, for icebergs and fog hide the coasts, and the cursed kvaldir and other sea raiders are said to rise from the mists.""",

    3979: """The Frozen Sea: The cold sea south of Northrend, part of the Great Sea, stretching from the southern coasts of the Borean Tundra, the Dragonblight and the Howling Fjord toward the Maelstrom. Pack ice and icebergs drift on its grey waters. Alliance and Horde fleets cross it to reach the continent, tuskarr ride their giant turtles between coastal villages, and the carved columns of the ancient Path of the Titans rise from its waves. Kvaldir raiders and sea monsters haunt its depths.""",
}

# Translated ZONE_FLAVOR copies for ruRU, frFR, deDE and esES live in
# tools/locales, keyed by the same zone IDs. get_zone_flavor() prefers
# the copy for LLMChatter.Language and falls back to the English text
# above for any other locale or missing zone.

# =============================================================================
# BATTLEGROUND MAP NAMES
# =============================================================================
# Map ID → display name for the six WotLK battlegrounds.
# Used to suppress AMBIENT topics and inject BG context
# into idle party chat prompts when players are inside a BG.
BG_MAP_NAMES = {
    30:  "Alterac Valley",
    489: "Warsong Gulch",
    529: "Arathi Basin",
    566: "Eye of the Storm",
    607: "Strand of the Ancients",
    628: "Isle of Conquest",
}

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'A hidden valley deep in the Alterac Mountains, home of '
            'the Frostwolf orcs since Gul\'dan exiled them there '
            'before the First War. The dwarves of the Stormpike '
            'Expedition came to dig for resources and titan relics '
            'and claim the valley for Ironforge, and the Frostwolves '
            'have vowed to drive them out. War now rages from the '
            'fortress of Dun Baldar in the north to Frostwolf Keep in '
            'the south.'
        ),
        'tone': (
            'Epic, large-scale, a true war in the snow between two '
            'armies.'
        ),
        'objectives': 'Kill the enemy general. Capture towers and graveyards.',
        'landmarks': (
            'Key locations: Dun Baldar and the Stormpike bunkers in '
            'the north, Stonehearth and Snowfall in the middle, '
            'Iceblood Tower and Tower Point, Frostwolf Graveyard and '
            'Frostwolf Keep in the south. Snow, pine forests, '
            'mountain passes and ice caves. Do NOT mention locations '
            'from other battlegrounds.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'A forest gulch in southern Ashenvale where Grom '
            'Hellscream\'s orcs cut great swaths of forest in the '
            'Third War. The orcs of the Warsong Outriders still '
            'harvest its timber for the Horde, and the night elf '
            'Silverwing Sentinels have sworn not to rest until every '
            'last orc is driven from the gulch.'
        ),
        'tone': 'Intense, fast and personal, a bitter fight over the forest.',
        'objectives': 'Capture the enemy flag 3 times.',
        'landmarks': (
            'Key locations: Silverwing Hold (night elf stronghold), '
            'the Warsong fort (orc stronghold), the tunnels beneath '
            'each base, the open midfield, the ramps and the '
            'graveyards. Tall trees, stumps and lumber piles. Do NOT '
            'mention locations from other battlegrounds like mills, '
            'farms, or towers.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'A fertile basin in the heart of the Arathi Highlands, '
            'rich in ore, timber and farmland. The League of Arathor, '
            'the remnant of Stromgarde, fights to reclaim the land\'s '
            'resources, while the Forsaken Defilers seek to seize '
            'them for the Horde.'
        ),
        'tone': (
            'Strategic and territorial, fought across the whole basin '
            'at once.'
        ),
        'objectives': 'Control nodes to reach 1600 resources first.',
        'landmarks': (
            'Key locations: Stables (north, open pastures with horse '
            'pens), Blacksmith (center crossroads, smoke and anvils), '
            'Lumber Mill (hilltop overlook, wooden platforms and '
            'sawblades), Gold Mine (southeast cave entrance, mine '
            'carts and torches), Farm (south, fields and haystacks '
            'near a farmhouse). Do NOT mention locations from other '
            'battlegrounds.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'A fragment of Draenor floating in the Twisting Nether at '
            'the edge of Netherstorm, where four ruins sit on a great '
            'island around a font of raw energy at its center. Both '
            'the Alliance and the Horde fight to control the island '
            'and its power.'
        ),
        'tone': (
            'Tense and chaotic, with the void of the Nether just '
            'beyond the edges.'
        ),
        'objectives': (
            'Control bases and capture the central flag to reach 1600 '
            'points.'
        ),
        'landmarks': (
            'Key locations: Fel Reaver Ruins, Blood Elf Tower, '
            'Draenei Ruins, Mage Tower, the bridges and the center '
            'flag. Purple stone, crackling energy and the endless '
            'Nether all around. Do NOT mention locations from other '
            'battlegrounds.'
        ),
    },
    9: {  # SA (BATTLEGROUND_SA = 9)
        'name': 'Strand of the Ancients',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'An island off the southern coast of the Dragonblight, '
            'where a titan relic rests behind the crumbling walls of '
            'an ancient citadel. Both the Alliance and the Horde seek '
            'it for the knowledge of the titans it is said to hold, '
            'one side storming the walls from the sea while the other '
            'holds them.'
        ),
        'tone': 'A grinding siege, wave after wave against ancient walls.',
        'objectives': (
            'Break through the gates and capture the relic, or defend '
            'it as long as possible.'
        ),
        'landmarks': (
            'Key locations: the beach and docks where attackers land, '
            'the Green Emerald and Blue Sapphire gates, the Red Sun '
            'and Purple Amethyst gates, the Yellow Moon gate, the '
            'Chamber of Ancient Relics, demolishers, cannons and '
            'graveyards. Glittering sand, titan stone and crashing '
            'waves. Do NOT mention locations from other '
            'battlegrounds.'
        ),
    },
    30: {  # IC (BATTLEGROUND_IC = 30)
        'name': 'Isle of Conquest',
        'alliance_faction': '7th Legion',
        'horde_faction': 'Warsong Offensive',
        'lore': (
            'An island of great strategic value for the war in '
            'Northrend, with docks, a quarry, an oil refinery, a '
            'siege workshop and a gunship hangar. The Alliance under '
            'High Commander Halford Wyrmbane and the Horde under '
            'Overlord Agmar each hold a keep on the island and fight '
            'to secure it.'
        ),
        'tone': (
            'Massive and mechanized, siege engines and gunships in '
            'open war.'
        ),
        'objectives': (
            'Kill the enemy general. Capture the docks, workshop and '
            'hangar to break the enemy keep.'
        ),
        'landmarks': (
            'Key locations: the Alliance Keep in the west, the Horde '
            'Keep in the east, the Docks, the Workshop, the Hangar '
            'with its gunships, the Quarry and the Refinery. Siege '
            'engines, cannons and iron walls. Do NOT mention '
            'locations from other battlegrounds.'
        ),
    },
}

# Translated BG_LORE copies for ruRU, frFR, deDE and esES live in
# tools/locales, keyed by the same bg_type_id. Only the prose fields
# ('lore', 'tone', 'objectives', 'landmarks') are translated; 'name' and
# the faction fields stay English. get_bg_lore() falls back to the
# English entry for any other locale.

# Raid instance map IDs (Classic, TBC, WotLK)
RAID_MAP_IDS = {
    # Classic
    249, 309, 409, 469, 509, 531,
    # TBC
    532, 534, 544, 548, 550, 564, 565, 580,
    # WotLK
    533, 603, 615, 616, 624, 631, 649, 724,
}

# =============================================================================
# OPEN-AIR INSTANCES - dungeons, raids and arenas under the open sky
# =============================================================================
# Only these get time of day, season and weather in prompts; every
# other instance is indoors (prisons, caves, crypts, keeps), where the
# sky is not visible. Keyed by map ID; the value is the DBC map name,
# which raid events carry instead of a map ID. Mixed instances that are
# mostly indoors (Deadmines, Scarlet Monastery, Ulduar, ICC...) are left
# out on purpose.
OPEN_AIR_INSTANCES = {
    47: "Razorfen Kraul",
    129: "Razorfen Downs",
    209: "Zul'Farrak",
    329: "Stratholme",
    543: "Hellfire Ramparts",
    560: "Old Hillsbrad Foothills",
    269: "The Black Morass",
    578: "The Oculus",
    595: "The Culling of Stratholme",
    650: "Trial of the Champion",
    658: "Pit of Saron",
    309: "Zul'Gurub",
    509: "Ruins of Ahn'Qiraj",
    534: "Battle for Mount Hyjal",
    568: "Zul'Aman",
    649: "Trial of the Crusader",
    559: "Nagrand Arena",
    562: "Blade's Edge Arena",
    572: "Ruins of Lordaeron",
    618: "The Ring of Valor",
}

# =============================================================================
# DUNGEON FLAVOR - Context for dungeon, raid and arena chat
# =============================================================================
# Keyed by map ID (not zone ID). Written in the world's voice for the WotLK
# 3.3.5 timeline: history, inhabitants and atmosphere, no game terms, no
# quest plots; bosses are described as present powers, never as defeated.
# Keep the "<Instance name>: " prefix; callers split on it for the name.
DUNGEON_FLAVOR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Shadowfang Keep: A haunted keep on a bluff above Pyrewood Village in southern Silverpine Forest, once the seat of Baron Silverlaine. During the Third War the archmage Arugal summoned the worgen to fight the Scourge, but they turned on everyone; driven mad with guilt, he took them as his children and made the keep his lair. Worgen stalk the courtyards and towers, undead servants walk the halls, and the vengeful ghost of the baron is said to linger. Cold stone, flickering torches and the howls of wolves fill the night.""",

    34: """The Stockade: A high-security prison hidden beneath the canal district of Stormwind City, home to petty crooks, political agitators, murderers and some of the most dangerous criminals in the land, many of them Defias. A recent revolt has driven out the guards, and the convicts now roam the cells and corridors freely under the cunning felon who led the uprising. The air is damp and close, water drips from the stone, and the shouts of prisoners echo down the narrow halls.""",

    36: """The Deadmines: An old gold mine beneath the ghost town of Moonbrook in Westfall, the hidden stronghold of the Defias Brotherhood, the outlaws born from the unpaid stonemasons of Stormwind. Defias miners, goblin engineers and ogres work the tunnels, and the passages open onto a vast hidden cove where the Brotherhood is building a great warship, the heart of its plans against the kingdom. The tunnels are dark and cramped, smelling of dust, oil and gunpowder, with the creak of timber and the clank of machinery all around.""",

    43: """Wailing Caverns: A network of caves beneath the heart of the Barrens, named for the long, mournful wails of the steam fissures venting through them. The night elf druid Naralex hoped to use their springs and the power of the Emerald Dream to make the Barrens green again, but his dream became a nightmare. The waters turned foul, the beasts within grew into vicious predators, and his own disciples were twisted into the Druids of the Fang. Naralex is said to lie somewhere in the depths, trapped in his waking nightmare.""",

    47: """Razorfen Kraul: The great thorn warren of the quilboar at the southern edge of the Barrens, grown from the vines that sprouted where the blood of the demigod Agamaggan fell in the War of the Ancients. The quilboar hold it sacred as the home of their race. The old crone Charlga Razorflank rules it, and her shamans stage raids on rival tribes and Horde villages, while some whisper that she deals with agents of the Scourge. Massive thorny vines arch overhead, and the tunnels are muddy, cramped and full of boars.""",

    48: """Blackfathom Deeps: Once a glorious temple to the moon goddess Elune on the Zoram Strand of Ashenvale, shattered by the Great Sundering and sunk beneath the waves of the Veiled Sea. Its flooded caverns and broken ruins lead deep toward a shrine of the Old Gods. Naga and satyrs plumb its secrets, the Twilight's Hammer cult works alongside them, and the ancient beast Aku'mai, a favored pet of the Old Gods, is said to dwell in its depths. Cold water, slick stone and dim, eerie light fill the deeps.""",

    70: """Uldaman: An ancient titan vault buried deep in the northern Badlands, recently breached by dwarven excavations, which released the troggs, the titans' first failed creations. Legends hold that the vault records the secrets of the dwarves' own creation on the fabled Discs of Norgannon. Dark Iron dwarves dig there for their master Ragnaros, while living stone guardians crush any intruder. Vast halls of carved stone, collapsed passages and silent titan machinery lie under the weight of the mountains.""",

    90: """Gnomeregan: The technological wonder that was the capital of the gnomes, beneath the snows of Dun Morogh, lost when troggs invaded from the depths and the gnomes vented the city's radioactive waste in a desperate attempt to stop them. The troggs, irradiated but unbroken, still roam its halls, and the surviving gnomes fled to Ironforge. The traitor Mekgineer Thermaplugg rules the ruins as their mad techno-overlord. Clanking machinery, leaking pipes, toxic sludge and alarm sentries fill the twisting corridors.""",

    109: """Sunken Temple: The Temple of Atal'Hakkar, raised by the exiled Atal'ai priests in the Swamp of Sorrows to prepare the return of the blood god Hakkar the Soulflayer. The Dragon Aspect Ysera smashed it beneath the marshes, and her green dragons still guard the drowned ruins, some of them now corrupted. Yet fanatical Atal'ai survive within and serve Hakkar still. Flooded halls, crumbling stone and troll idols lie in murky water, and the air is heavy with rot and old blood magic.""",

    129: """Razorfen Downs: The ancestral burial grounds and traditional capital of the quilboar, a sprawling labyrinth of thorns at the southern edge of the Barrens, grown from the same mighty vines as Razorfen Kraul. A looming shadow has fallen over it: it is said that the Scourge has taken hold of the downs, that a lich commands the quilboar high priests of the Death's Head, and that the dead of the burial grounds are rising again. Cold mist clings to the brambles, and the stench of death mixes with mud and thorns.""",

    189: """Scarlet Monastery: Once a proud center of learning of Lordaeron's priesthood in northeastern Tirisfal Glades, now a fortress of the fanatical Scarlet Crusade, which trusts no one who is not human and sees every outsider as a carrier of the plague. Its graveyard, library, armory and cathedral are held by zealous warriors under Scarlet Commander Mograine, while the High Inquisitor Whitemane, said to raise the fallen to fight again, is the monastery's true master. Red banners, incense and the cries of the faithful fill its halls.""",

    209: """Zul'Farrak: The walled city of the Sandfury trolls in the deserts of northwestern Tanaris, sun-scorched stone and pyramids rising from the dunes. Its warriors, priests and witch doctors guard it fiercely and raise the dead to defend it. Legends tell of a powerful troll sword split in two that lies somewhere within, of mercenaries who wandered into the city and were never seen again, and of an ancient creature sleeping in the sacred pool at its heart. Heat, sand and scorpids are everywhere.""",

    229: """Blackrock Spire: The fortress carved into the upper reaches of Blackrock Mountain, built by the Dark Iron mason Franclorn Forgewright as a symbol of their power. The orcish Horde made it their capital in the Second War. Now it is held by the Dark Horde of Warchief Rend Blackhand, with orcs, ogres and trolls, and by the black dragon Nefarian and his dragonkin, who rule the upper spire and war against Ragnaros in the depths below. Lava, chains, iron gates and drakes circling in the smoke make it a vast and deadly fortress.""",

    230: """Blackrock Depths: The once-great capital of the Dark Iron dwarves, a volcanic labyrinth deep in Blackrock Mountain, now ruled by Emperor Dagran Thaurissan as the seat of power of Ragnaros the Firelord. Forges blaze, lava flows through the halls, golems of living stone are built for the Firelord's army, and an arena, a prison and a tavern lie among its vast chambers. Dark Iron soldiers, fire elementals and enslaved captives fill the city. The heat is crushing, and the hammering never stops.""",

    269: """The Black Morass: A journey through the Caverns of Time into the swamp of the Black Morass, on the day Medivh, the last Guardian of Tirisfal, opened the Dark Portal and let the orcish Horde into Azeroth. The bronze dragonflight guards the moment, for the infinite dragonflight sends wave after wave through rifts in time to slay Medivh and change history. Fog, stagnant water and twisted trees surround the growing portal, while time itself seems to tremble.""",

    289: """Scholomance: A school of necromancy in the crypts beneath Caer Darrow, an old keep on an island in Darrowmere Lake. The noble Barov family gave the keep to Kel'Thuzad's Cult of the Damned in exchange for promised immortality, and the cult turned its crypts into an academy that trained the agents who spread the plague. The Barovs now walk its halls as undead, the lich Ras Frostwhisper guards it for the Scourge, and the necromancer Darkmaster Gandling rules as headmaster. Candles, bones and forbidden tomes fill its classrooms.""",

    329: """Stratholme: The second city of Lordaeron, where the Order of the Silver Hand was founded and where Prince Arthas purged the plague-ridden population. Now it is the Scourge's capital in Lordaeron and burns to this day. The city is split between the Scarlet Crusade, which holds the Scarlet Bastion under Grand Crusader Dathrohan, and the Scourge, whose death knight Baron Rivendare rules the ziggurats of the eastern districts. Ash drifts over shattered streets, and the dead fill the squares.""",

    349: """Maraudon: A holy place of the centaurs in the Valley of Spears in Desolace, the tomb of Zaetar, son of Cenarius, and the home of the earth elemental princess Theradras, the mother of the centaur race. Their cursed children slew their father, and Theradras keeps his body in her crystal caverns. Nature's blessing turned his resting place into a paradise of flowers and pools deep underground, while purple-stained caves, earth elementals and the spirits of centaur khans fill the maze. The Maraudine centaurs guard it fiercely.""",

    389: """Ragefire Chasm: A network of volcanic caverns beneath Orgrimmar, full of lava and fire. Ragefire troggs have crept up from the depths and refuse all attempts at peace, and a cult loyal to the Burning Blade and the Shadow Council has taken refuge in the chasm, plotting to destroy all that the Horde has built in Durotar. The tunnels are scorching hot, the light is red, and the hiss of molten rock never ceases, a danger lurking right beneath the capital.""",

    429: """Dire Maul: The ruins of Eldre'Thalas, a Highborne city built twelve thousand years ago in northern Feralas to guard Queen Azshara's most prized arcane secrets. Ravaged by the Great Sundering, much of it still stands. Gordunni ogres rule the northern district, satyrs and corrupted ancients haunt the eastern gardens, and the last Highborne, the secretive Shen'dralar, keep the western halls and their great library, guarding the ancient evils locked in its vaults. Broken marble, elven arches and overgrown courtyards fill the city.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Onyxia's Lair: A volcanic cave in the Wyrmbog of southern Dustwallow Marsh, the lair of Onyxia, the black dragon broodmother and daughter of Deathwing. A narrow tunnel of scorched rock winds down past whelps and dragonspawn into an enormous chamber littered with bones and egg clutches. The floor of the cavern is only a thin crust over molten rock, and the air is thick with smoke and brimstone. Onyxia herself fills the chamber with fire and shadow, and few who enter her lair return.""",

    309: """Zul'Gurub: The ancient capital of the Gurubashi Empire in northeastern Stranglethorn Vale, a vast troll city of temples and ziggurats overgrown by jungle. Over a thousand years ago the Atal'ai summoned Hakkar the Soulflayer and shattered the empire; now the blood god has returned in the heart of the ruins. The high priests sent by the tribes to stop him, champions of the Bat, Panther, Tiger, Spider and Snake, have fallen under his sway and feed his power. Blood rituals, drums and the cries of jungle beasts fill the air.""",

    409: """Molten Core: The burning heart of Blackrock Mountain, at the very bottom of the depths, where Thaurissan summoned Ragnaros the Firelord into the world. The Firelord dwells here in a lake of fire that acts as a rift to the Elemental Plane, and his lieutenants, the flamewakers and their majordomo Executus, command the elementals and the enslaved Dark Irons. Rivers of lava run between obsidian platforms, core hounds and molten giants roam the caverns, and the heat is overwhelming.""",

    469: """Blackwing Lair: The lair of the black dragon Nefarian at the very top of Blackrock Spire, where he plots to crush Ragnaros and claim all of Blackrock Mountain. Like his father Deathwing before him, he breeds a new army, experimenting with the blood of all the dragonflights to create unstoppable warriors. Laboratories, suppression chambers and drake hatcheries fill the lair, guarded by black dragonkin, drakonids and his most terrible creations. Heat, smoke and the stench of dragon blood hang in the halls.""",

    509: """Ruins of Ahn'Qiraj: The outer ruins of the city of Ahn'Qiraj behind the Scarab Wall in southern Silithus, where the Qiraji and their silithid were sealed a thousand years ago at the end of the War of the Shifting Sands. The gates have been opened once more, and the armies of the Alliance and the Horde have driven the Qiraji back into the ruins. Colossal stone structures and pillars rise from the sand among silithid hives, and the Qiraji generals and their swarms defend the ruins fiercely.""",

    531: """Temple of Ahn'Qiraj: The great temple at the heart of Ahn'Qiraj in southern Silithus, stronghold of the Qiraji emperors and their silithid swarms. Dark whispers say that beneath it an Old God stirs in his lair, regaining his power after thousands of years, and that the dragons who sacrificed themselves to imprison him lie weakened or enslaved within. Vast insectile halls, pulsing hives and twisted chambers lead deeper and deeper, and an alien, oppressive dread grows with every step.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Shattered Halls: The innermost wing of Hellfire Citadel on Hellfire Peninsula, the training ground and barracks of the fel orcs. Here Warchief Kargath Bladefist commands the Fel Horde, warlocks of the Shadow Council work their dark magic, gladiators fight in the arena and archers rain fire on the narrow corridors. The halls are brutal, cramped and filled with the clash of arms. Every hall is soaked in blood and fel energy.""",

    542: """Blood Furnace: A wing of Hellfire Citadel on Hellfire Peninsula, where the fel orcs bleed the imprisoned pit lord Magtheridon and use his blood to breed a new Fel Horde, infused with demonic power. Vats of corrupted blood, cells of prisoners and chained warlocks line the furnace halls. Fel orc sorcerers channel the energies of the captive demon below, and the air is thick with fel fumes, heat and screams.""",

    543: """Hellfire Ramparts: The fortified outer walls and towers of Hellfire Citadel on Hellfire Peninsula, the first line of defense of the fel orcs. Bonechewer fel orcs patrol the battlements, their watchkeepers command the walls, and a fel orc champion rides a nether dragon above the towers. The ramparts overlook the red wasteland, the Dark Portal and the Legion's forge camps. Wind, fel fire and the roar of drakes fill the air.""",

    545: """The Steamvault: The heart of Coilfang Reservoir in Zangarmarsh, where the naga of Lady Vashj run great steam-driven machines and pumps that drain the waters of the marsh. Naga warriors, sirens and water elementals guard the vault, and enslaved Broken toil in the halls. Hissing pipes, roaring turbines and clouds of steam fill the air, and the walls run with condensation. The hum of the machines never stops.""",

    546: """The Underbog: A wing of Coilfang Reservoir in Zangarmarsh, home to the last of the marsh's natural life not yet stamped out by the naga. Giant fungi, bog lords, spore bats and hungry beasts thrive in its caverns, while the naga defend a temple where they keep their hydra god Ghaz'an. Glowing mushrooms, murky water and thick, spore-laden air make it a wild, untamed place.""",

    547: """The Slave Pens: The first wing of Coilfang Reservoir in Zangarmarsh, where the naga of Lady Vashj keep enslaved Broken draenei and bog lords to labor on their great pumps. Naga taskmasters and their servants patrol the pens, while the enslaved toil in chains. Wooden walkways, iron cages and dripping water fill the halls, and the cries of the captives echo across the reservoir.""",

    552: """The Arcatraz: A satellite of Tempest Keep in Netherstorm where the naaru imprisoned the most dangerous creatures they met on their journeys: demons, agents of the black dragonflight and even servants of the Old Gods. The blood elves of Kael'thas now guard it, but they are corruptible, and the prisoners are breaking free. Cells of shimmering force, crystal corridors and the howls of escaped horrors fill the prison.""",

    553: """The Botanica: A satellite of Tempest Keep in Netherstorm, where blood elf scientists loyal to Kael'thas use stolen naaru technology to experiment on the plants and creatures of Outland, seeking new powers. Gardens of strange flora grow under crystal domes, but the experiments have gone out of control, and mutated plants and enraged treants now fill the halls. The air is humid and thick with pollen.""",

    554: """The Mechanar: A satellite of Tempest Keep in Netherstorm, turned by Kael'thas into a factory that harnesses naaru technology to create great amounts of power, stored in manacells piled in walls and heaps. Blood elves under the command of Pathaleon the Calculator run the machines, aided by demons of the Burning Legion. Humming engines, arcane conduits and clanking constructs fill the purple crystal halls.""",

    555: """Shadow Labyrinth: The deepest wing of Auchindoun in Terokkar Forest, where the Shadow Council summoned an ancient elemental of sound whose ritual blew the necropolis apart. The council still plots here, struggling to contain and harness the entity it unleashed, served by fel orcs and demons. Long halls, ritual chambers and a constant, deafening echo fill the labyrinth, and the very air trembles.""",

    556: """Sethekk Halls: A wing of Auchindoun in Terokkar Forest, held by the Sethekk, renegade arakkoa who broke away from Skettis under the insane Talon King Ikiss. They believe the destruction of Auchindoun heralded the return of their master and search the ruins for him. Feathered idols, ritual fires and dark magic fill the ancient draenei halls, and the shrieks of the arakkoa echo through them.""",

    557: """Mana-Tombs: A wing of Auchindoun in Terokkar Forest, where renegade ethereals led by Nexus-Prince Shaffar plunder the crypts and siphon arcane energy from the ruins. Wards keep their rivals of the Consortium out. Shimmering energy, floating debris and the restless spirits of the draenei dead fill the tombs, and the halls hum with stolen power.""",

    558: """Auchenai Crypts: A wing of Auchindoun in Terokkar Forest, the burial crypts of the draenei, where the Auchenai priests tended their honored dead. Since the necropolis was shattered, the crypts have fallen to darkness: demons of the Burning Legion harvest souls here, and the draenei dead rise as restless spirits and undead. Cold stone, faded holy light and the whispers of the dead fill the halls.""",

    560: """Old Hillsbrad Foothills: A journey through the Caverns of Time to Hillsbrad years before the Third War, when the young orc Thrall was a slave of Aedelas Blackmoore at Durnholde Keep and the orcs languished in internment camps. The bronze dragonflight guards the moment of his escape, for the infinite dragonflight seeks to change it. Green hills, peaceful farms, the town of Southshore and the stone walls of Durnholde appear as they once were.""",

    568: """Zul'Aman: The temple city of the Amani forest trolls in the eastern Ghostlands, the last remnant of the empire that once spanned Lordaeron before humans and high elves broke it together. Warlord Zul'jin, who never forgave the elves, has rallied his trolls and sealed the power of the Amani animal gods, the bear, eagle, lynx and dragonhawk, within his strongest champions, with the Hex Lord's help. Stepped ziggurats, voodoo totems and drums fill the dark, primal forest.""",

    585: """Magisters' Terrace: An elegant blood elf compound on the northeastern corner of the Isle of Quel'Danas, with an observatory looking out over the Sunwell. It is held by followers of Kael'thas Sunstrider, who is said to have retreated here, and the halls hum with stolen arcane power and the energy of mana-crystals. Golden spires, gardens and observatory domes fill the terrace, beautiful and dangerous.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: The ivory tower of Medivh, the last Guardian of Tirisfal, in Deadwind Pass, standing on a nexus of ley lines where reality is weak. After Medivh's death a terrible curse fell over the tower and the lands around it. Now it has reawakened: an evil presence has claimed it, its halls crawl with spirits and demons, ghostly nobles of Darkshire relive an endless feast, and echoes of the past play out in its libraries, opera house and menagerie. Dusty grandeur and cold magic fill every chamber.""",

    534: """Hyjal Summit: A journey through the Caverns of Time to the slopes of Mount Hyjal at the end of the Third War, when humans, orcs and night elves stood together against the Burning Legion and the Scourge. The demon lord Archimonde marches up the mountain to drain the power of the World Tree Nordrassil. The bronze dragonflight guards the battle as it was, while the defenders fall back from base to base. Ancient forests, the great tree above and the burning armies of the Legion below.""",

    544: """Magtheridon's Lair: A chamber deep beneath Hellfire Citadel where the pit lord Magtheridon, former master of Outland, lies chained and imprisoned since Illidan defeated him. His blood is harvested to breed the Fel Horde, and Hellfire channelers keep his bonds in place. The cavern trembles with his rage, the ceiling cracks under his power, and fel fire flickers around the cage. It is a place of raw demonic fury.""",

    548: """Serpentshrine Cavern: The lair of Lady Vashj, the naga sorceress who serves Illidan, deep within Coilfang Reservoir in Zangarmarsh, where the waters pumped from the marsh collect. Her most powerful lieutenants guard the shrine, from a corrupted water elemental to a lurker in the deep, and the waters swarm with naga. Vast flooded caverns, coral pillars and shimmering pools glow in an eerie blue light.""",

    550: """Tempest Keep - The Eye: The inner palace of Tempest Keep, the naaru fortress in Netherstorm seized by the blood elves of Kael'thas Sunstrider, the Sun King, who rules here with his phoenixes and his most powerful advisors. Crystal halls, arcane machinery and floating platforms glow with stolen naaru energy, and a captured naaru is drained for power. The Eye looks out over the twisting storms of the Nether, magnificent and cold.""",

    564: """Black Temple: Once the Temple of Karabor, the most sacred place of the draenei and refuge of the Prophet Velen, conquered by Gul'dan as the headquarters of the Shadow Council and later held by the Burning Legion. Now it is the fortress-citadel of Illidan Stormrage, the self-proclaimed Lord of Outland, guarded by his Illidari: naga, blood elves, Broken, demons and fel orcs. Fel fire burns in its sanctuaries, shadow fills its halls, and the cries of tormented souls echo from its depths.""",

    565: """Gruul's Lair: A cavernous lair in the northern Blade's Edge Mountains, home of Gruul the Dragonkiller, the merciless overlord of the gronn, and his son, the ogre High King Maulgar, who rule the ogres of the mountains. The bones of slain dragons hang from the walls, and the ground shakes beneath the footsteps of giants. Crude ogre banners, trophies and raw stone fill the vast cave, a place of brute strength and violence.""",

    580: """Sunwell Plateau: The holiest place of the elves on the Isle of Quel'Danas, where the Sunwell, the fountain of power that sustained Quel'Thalas, stands at the heart of graceful courtyards and halls. In recent times the Burning Legion has sought to use it as a gateway for the eredar lord Kil'jaeden, and the Legion's servants, demons and blood elves loyal to them, hold the plateau. Golden spires, captured naaru and fel energy surround the defiled well.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Utgarde Keep: The great vrykul fortress on the cliffs above Lake Cauldros in the Howling Fjord, built into the fjord with waterfalls tumbling down on either side, home of the Dragonflayer clan. Long silent, it has awakened, and its warriors raid all settlements nearby, rumored to serve the Lich King, who raises the most worthy of them beyond the grave. Proto-drakes, worgs and the undead serve the vrykul, and the higher one climbs in the keep, the mightier its dwellers.""",

    575: """Utgarde Pinnacle: The highest reaches of Utgarde Keep in the Howling Fjord, where the mightiest of the vrykul dwell and King Ymiron holds his throne, eager to prove his people worthy of the Lich King's favor. Great halls of stone and timber, carved skulls and the trophies of fallen enemies fill the pinnacle, and proto-drakes circle the cold heights above the fjord.""",

    576: """The Nexus: The ancient home of the blue dragonflight beneath the island of Coldarra off the Borean Tundra, an arcane fortress of ice and floating crystal where the Aspect of Magic, Malygos, wages his war against all mortal spellcasters. The blue dragons and their servants guard its frozen halls, and captured enemies are held in prisons of ice. Arcane energy crackles through the air, and the ice glows with magic.""",

    578: """The Oculus: The great tower of floating rings above the Nexus on Coldarra, where Malygos channels the ley lines of Azeroth, diverting the world's magic through the Nexus and into the Twisting Nether. The Kirin Tor and the red dragonflight fight to stop him. The rings drift high in the sky, crackling with arcane power, and drakes are the only way between them. Raw magic splinters the air and distant rifts tear at reality.""",

    595: """Culling of Stratholme: A journey through the Caverns of Time to the day the plague reached Stratholme in infected grain and Prince Arthas, refusing to let its people rise as undead, ordered the city purged. The dreadlord Mal'Ganis watches over the dying city, and the infinite dragonflight seeks to twist the moment. The streets are full of frightened citizens, burning houses and the first of the walking dead, a day that marked the beginning of Arthas's fall.""",

    599: """Halls of Stone: A wing of the titan city of Ulduar in the Storm Peaks, home of the Tribunal of Ages, the vast stone archive of the titans' history, and of the Forge of Wills. Iron dwarves and stone giants, corrupted by the fallen keeper Loken, now hold its halls and guard their secrets. Towering statues, carved reliefs and titan machinery fill the vast halls of stone, silent but for the rumble of the machines.""",

    600: """Drak'Tharon Keep: An old ice troll fortress of spires and carved walls on the border of the Grizzly Hills and Zul'Drak, seized by the Scourge, which raises the fallen Drakkari to fight against their own empire. Its former leader, the Prophet Tharon'ja, has been twisted into a monstrous undead form, and undead trolls pour from its gates into the hills. Bones, Scourge banners and frozen troll carvings fill the keep.""",

    601: """Azjol-Nerub: The Upper Kingdom of the nerubians beneath the Dragonblight, a grand underground realm of scholarship and art overrun by the Scourge in the War of the Spider. Undead nerubians now patrol its polished halls, guarding clutches of eggs that will hatch into new Scourge warriors, and their fallen king Anub'arak serves the Lich King. Webs, carved murals and glowing fungi fill the vast caverns, while living nerubians fight a hidden, losing war.""",

    602: """Halls of Lightning: The eastern wing of the titan city of Ulduar in the Storm Peaks, where the fallen keeper Loken sits on his throne and mass-produces iron vrykul and constructs for his dark purposes. Storm elementals, iron giants and lightning-forged guardians serve him, and great forges and machines thunder throughout. Lightning crackles across the vast halls of stone and metal.""",

    604: """Gundrak: The capital of the Drakkari ice trolls in Zul'Drak, a massive city of thick walls, tall towers and tiered buildings wound together like a nest. In desperation against the Scourge, its high prophets have slain their own gods, the loa, and drink their blood for power, steeping the sacred shrines in the mojo of slain gods. Rhino, snake and mammoth idols stand in the courtyards, and drums echo through the stepped streets.""",

    608: """Violet Hold: The prison of the Kirin Tor in Dalaran, its magically shielded cells holding powerful and dangerous prisoners. The blue dragonflight of Malygos has broken in through a great crack in its roof and pours through portals within, testing the prison's defenses and freeing its inmates. Arcane wards flicker, violet stone glows, and the guards of the Kirin Tor fight to hold the line.""",

    619: """Ahn'kahet: The Old Kingdom, the deepest reaches of Azjol-Nerub beneath the Dragonblight, a vast underground city of the ancient nerubian empire. Scourge nerubians and the mysterious faceless ones hold it, the latter said to answer to an evil power lurking beneath Northrend, and the Twilight's Hammer stirs among them. Fungal forests, great webbed chambers and an oppressive darkness fill the depths.""",

    632: """Forge of Souls: The first of the Frozen Halls within Icecrown Citadel, a massive production facility where soul grinders, the latest foul construct of the Lich King, are built. Tormented souls are bound into the machines amid saronite pillars and spectral chains. The air is thick with despair and the moans of the dead.""",

    650: """Trial of the Champion: The tournament grounds of the Argent Crusade beneath the Argent Coliseum in Icecrown, where champions of the Alliance and the Horde joust and duel to prove their worth for the war against the Lich King. Mounts, lances, banners and the roar of the crowd fill the arena, festive and proud, though the Scourge is never far away.""",

    658: """Pit of Saron: The great saronite mine below Icecrown Citadel, where the Scourge forces Alliance and Horde prisoners to dig the ore that builds its fortresses, under the lash of the Scourgelord Tyrannus. Saronite veins pulse in the walls, slaves toil in chains, and the dead are raised to keep working. The cold, the dark and the cracks of whips fill the pit.""",

    668: """Halls of Reflection: The private chambers of the Lich King within Icecrown Citadel, the only place where he lets his guard down, a dark and twisted replica of Lordaeron's throne room. Frostmourne, the runeblade of the Lich King, waits here, and the spirits trapped within it haunt the halls. Ice, silence and memories of the past fill the chambers.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: A Scourge necropolis floating over the Dragonblight, once a nerubian ziggurat overrun by the Scourge and raised into the sky by the Lich King's dark magic. It is the seat of the archlich Kel'Thuzad, who has brought it back to Northrend to lay siege to Wintergarde. Its four quarters house horrors of every kind: arachnid crypt lords, plague laboratories and abominations, legions of death knights, and the flesh-stitched constructs. Green slime, rotting flesh and the cold of the grave fill its halls.""",

    603: """Ulduar: The greatest titan complex on Azeroth, perfectly preserved in the snows of the Storm Peaks, hidden behind rock and ice, a profusion of tunnels, stairs and balconies carved from a vast cave. It was home to the titans' keepers and their engines of creation, but whispers speak of a great evil at work behind its fall, and its corrupted guardians now turn on all intruders. Colossal statues, titan machines and star-filled observatories fill its halls.""",

    615: """Obsidian Sanctum: The black dragonflight's chamber beneath Wyrmrest Temple in the Dragonblight, part of the Chamber of the Aspects, where Sartharion the Onyx Guardian guards a clutch of twilight dragon eggs. Three twilight drakes watch over their own islands amid rivers of lava between platforms of obsidian. The chamber glows orange and red, and heat shimmers in the air.""",

    616: """Eye of Eternity: The personal domain of the blue Aspect Malygos, high above the Nexus on Coldarra, from which he directs his war to reclaim dominance over the arcane energies of Azeroth. It is a vast floating platform in an endless void of swirling arcane energy and stars, where the world's magic flows. Raw power fills the air.""",

    624: """Vault of Archavon: A titan vault beneath Wintergrasp Fortress, holding relics of untold power, guarded by ancient stone watchers who resent all intruders. Its halls open only to those who hold the fortress above. Carved stone, titan machinery and an eerie silence fill the vault.""",

    631: """Icecrown Citadel: The Lich King's fortress, rising from the black ice of Icecrown, a cathedral of saronite blades and spires wrapped around the Frozen Throne. Its halls swarm with the most loyal and vile of the Scourge: death knights, cultists, abominations and frost wyrms. The Lower Spire, the Plagueworks, the Crimson Hall and the Frostwing Halls lead toward the throne. The Ashen Verdict leads the assault, and the cold seeps into the bones.""",

    649: """Trial of the Crusader: The great Argent Coliseum in Icecrown, built by the Argent Crusade to test the champions worthy of the assault on the Lich King. Banners of the Alliance and the Horde fly above cheering crowds, and fearsome beasts and champions are brought into its arena under the eyes of Highlord Tirion Fordring. Pageantry and spectacle unfold at the very doorstep of the Lich King, and the old rivalry of the two factions burns in the stands.""",

    724: """Ruby Sanctum: The red dragonflight's sanctum beneath Wyrmrest Temple in the Dragonblight, part of the Chamber of the Aspects, a peaceful refuge of red dragon eggs, warm light and green growth. Its guardians have fallen silent and the portal's guards have been slain; a dark force has breached the sanctum, and twilight dragons now threaten the eggs of the red flight.""",

    # -------------------------------------------------------------------------
    # Arenas
    # -------------------------------------------------------------------------
    559: """Nagrand Arena: The Ring of Trials in the grasslands of Nagrand, an ancient proving ground of the orcs built in the style of the old ogre empire. Gladiators of every race meet here to fight for glory. A ring of weathered stone pillars stands open to the sky, the wind sweeps over the grass, and spectators watch from the hills.""",

    562: """Blade's Edge Arena: The Circle of Blood in the Blade's Edge Mountains, an ogre-built arena where gladiators fight for glory before roaring crowds. A wooden bridge spans a pit at its center, ropes and pillars cross the ring, and the jagged peaks rise all around. Rough timber, bones and banners give it a brutal, savage air.""",

    572: """Ruins of Lordaeron: An arena among the shattered ruins of Lordaeron's capital city in Tirisfal Glades, above the Undercity, where the great palace still stands as a sad reminder of the city's fall. Broken walls, toppled statues and a ruined tomb surround the fighting ground, and the memory of the kingdom's tragic end hangs over the stones.""",

    617: """Dalaran Sewers: An arena hidden in the Underbelly, the sewers beneath the floating city of Dalaran, where gladiators fight in a pit surrounded by water channels and pipes. Damp stone, the rush of water and the murmur of a rough crowd fill the arena, far from the grandeur of the violet city above.""",

    618: """The Ring of Valor: The great arena in the Valley of Honor in Orgrimmar, where the gladiators of the Crimson Ring train and fight. Columns rise from the floor, the spectators roar from the stands, and the heat of Durotar beats down on the sand. It is a place of honor, strength and spectacle.""",
}

# Translated DUNGEON_FLAVOR copies for ruRU, frFR, deDE and esES live in
# tools/locales, keyed by the same map IDs and prefixed with the
# localized instance name. get_dungeon_flavor() falls back to the
# English text for any other locale or missing map.

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

ITEM_QUALITY_NAMES = {
    0: 'Poor', 1: 'Common', 2: 'Uncommon',
    3: 'Rare', 4: 'Epic', 5: 'Legendary',
    6: 'Artifact', 7: 'Heirloom',
}

ITEM_CLASS_NAMES = {
    0: "Consumable", 1: "Container",
    2: "Weapon", 3: "Gem", 4: "Armor",
    5: "Reagent", 6: "Projectile",
    7: "Trade Goods", 9: "Recipe",
    11: "Quiver", 12: "Quest Item", 13: "Key",
    15: "Miscellaneous", 16: "Glyph",
}

WEAPON_SUBCLASS_NAMES = {
    0: "One-Handed Axe", 1: "Two-Handed Axe",
    2: "Bow", 3: "Gun", 4: "One-Handed Mace",
    5: "Two-Handed Mace", 6: "Polearm",
    7: "One-Handed Sword", 8: "Two-Handed Sword",
    10: "Staff", 13: "Fist Weapon",
    15: "Dagger", 16: "Thrown",
    17: "Spear", 18: "Crossbow",
    19: "Wand", 20: "Fishing Pole",
}

ARMOR_SUBCLASS_NAMES = {
    0: "Miscellaneous", 1: "Cloth",
    2: "Leather", 3: "Mail", 4: "Plate",
    6: "Shield",
}

# What an armor-class item is, by equip slot (item_template
# InventoryType), for describe_item_type().
ARMOR_PIECE_NAMES = {
    1: "helm", 2: "necklace", 3: "shoulders", 4: "shirt",
    5: "chest piece", 6: "belt", 7: "leggings", 8: "boots",
    9: "bracers", 10: "gloves", 11: "ring", 12: "trinket",
    14: "shield", 16: "cloak", 19: "tabard", 20: "robe",
    23: "off-hand item", 28: "relic",
}

# Armor subclasses that name the item themselves.
ARMOR_KIND_SUBCLASS_NAMES = {
    5: "shield", 6: "shield",
    7: "libram", 8: "idol", 9: "totem", 10: "sigil",
}

# Subtypes of the other item classes (3.3.5 ItemSubClass.dbc),
# keyed by class, then subclass.
ITEM_SUBCLASS_NAMES = {
    0: {
        0: "consumable", 1: "potion", 2: "elixir", 3: "flask",
        4: "scroll", 5: "food or drink", 6: "item enhancement",
        7: "bandage", 8: "consumable",
    },
    1: {
        0: "bag", 1: "soul bag", 2: "herb bag", 3: "enchanting bag",
        4: "engineering bag", 5: "gem bag", 6: "mining bag",
        7: "leatherworking bag", 8: "inscription bag",
    },
    3: {
        0: "red gem", 1: "blue gem", 2: "yellow gem", 3: "purple gem",
        4: "green gem", 5: "orange gem", 6: "meta gem",
        7: "simple gem", 8: "prismatic gem",
    },
    6: {2: "arrows", 3: "bullets"},
    7: {
        0: "trade goods", 1: "parts", 2: "explosives", 3: "device",
        4: "jewelcrafting material", 5: "cloth", 6: "leather",
        7: "metal and stone", 8: "meat", 9: "herb", 10: "elemental",
        11: "trade goods", 12: "enchanting material", 13: "material",
        14: "armor enchantment", 15: "weapon enchantment",
    },
    9: {
        0: "book", 1: "leatherworking pattern", 2: "tailoring pattern",
        3: "engineering schematic", 4: "blacksmithing plans",
        5: "cooking recipe", 6: "alchemy recipe",
        7: "first aid manual", 8: "enchanting formula",
        9: "fishing manual", 10: "jewelcrafting design",
    },
    11: {2: "quiver", 3: "ammo pouch"},
    13: {0: "key", 1: "lockpick"},
    15: {
        0: "junk", 1: "reagent", 2: "companion pet", 3: "holiday item",
        4: "miscellaneous", 5: "mount",
    },
    16: {
        1: "warrior glyph", 2: "paladin glyph", 3: "hunter glyph",
        4: "rogue glyph", 5: "priest glyph", 6: "death knight glyph",
        7: "shaman glyph", 8: "mage glyph", 9: "warlock glyph",
        11: "druid glyph",
    },
}

# One-handed weapons that fit only one hand.
WEAPON_HAND_NAMES = {21: "main hand", 22: "off hand"}

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

# =============================================================================
# AMBIENT CHAT TOPICS
# =============================================================================
# Topics for party idle chatter and General ambient chatter.
# Excluded: items, quests, quest rewards, spells, trade
# (handled by dedicated message-type paths).
#
# Shared entries go to both modes, so they must make sense for a
# player and for a character in the world alike. Nothing here may
# assume a condition the prompt does not supply: weather, season,
# time of day, a feature of the current place, or the speaker's
# mount, profession or home. Place-bound subjects come from
# location_topics.json (chatter_location_topics) instead.
_AMBIENT_CHAT_TOPICS_SHARED = [
    # Class / Race
    'mentioning something about their class abilities',
    'comparing fighting styles or approaches',
    # Food / Drink
    'asking if anyone has food or water',
    'complaining about being hungry or thirsty',
    'mentioning a favorite food or drink',
    # Travel
    'commenting on how far they have walked',
    'wondering how long until the next rest stop',
    # Capital Cities / Inns
    'talking about a capital city or inn they like',
    'talking about what they do in town',
    'mentioning a favorite hangout spot',
    # Gear / Equipment
    'commenting on their own gear or armor',
    # General banter
    'cracking a joke or making a witty observation',
    'complaining about something minor',
    'sharing a random thought',
]

# Player-side topics used only in normal mode. Keep these out of
# AMBIENT_CHAT_TOPICS_RP so expanding OOC variety cannot change RP
# behavior. The first block holds game and surroundings subjects
# that read fine as player chatter but, in roleplay, either sound
# out of world or invent weather and scenery the prompt never gave.
AMBIENT_CHAT_TOPICS = _AMBIENT_CHAT_TOPICS_SHARED + [
    # Surroundings, weather and time
    'commenting on the scenery or surroundings',
    'noticing something interesting in the zone',
    'remarking on the local wildlife or creatures',
    'observing the landscape or terrain',
    'commenting on the weather',
    'noticing the time of day',
    'mentioning how the light looks',
    # Class, mounts, professions, gear and levels
    'mentioning something about their race or class perks',
    'sharing class-specific knowledge or tips',
    'talking about their mount',
    'wishing they had a faster mount',
    'mentioning their profession skill progress',
    'talking about gathering or crafting',
    'asking if anyone needs something crafted',
    'noticing a party member looks well-equipped',
    'wishing they had better equipment',
    'mentioning how close they are to leveling',
    'talking about what abilities they want next',
    'reflecting on how far they have come',
    # AFK / Bio / Humor
    'joking about needing a bio break',
    'making a joke about falling asleep at the keys',
    'making small talk with another player',

    # Zone navigation and pacing
    'commenting on whether the current route feels efficient',
    'wondering if the group missed a turn or useful shortcut',
    'mentioning that this area is easier to navigate with the map open',
    'comparing the pace here with another part of the game',
    'noticing that the group has circled past the same landmark',
    'asking whether everyone wants to keep moving or pause briefly',
    'commenting on how spread out the group has become',
    'mentioning that the next safe stopping point should be close',
    'wondering whether mounting would actually save time here',
    'commenting on a route that looks direct but rarely is',
    'noticing that the area is busier or quieter than usual',
    'mentioning that the current location is a useful meeting point',

    # Group play and cooperation
    'checking whether the current pace suits everyone',
    'giving the group credit for staying together',
    'mentioning that the group composition feels comfortable',
    'asking whether anyone needs a short break before continuing',
    'commenting on how smoothly everyone is handling the session',
    'noticing that communication has been pleasantly simple',
    'mentioning that relaxed groups can still make good progress',
    'asking whether someone wants to lead the way for a while',
    'commenting on a party member quietly doing their role well',
    'mentioning that nobody seems to be in a rush',
    'asking whether the group wants advice or prefers to experiment',
    'commenting on how different classes complement each other',

    # Combat rhythm and playstyle
    'commenting on whether the recent fights feel easy or demanding',
    'mentioning that the group has found a comfortable combat rhythm',
    'wondering whether the next section will require more care',
    'commenting on a useful interrupt, heal, or defensive play',
    'mentioning that careful positioning is making things easier',
    'asking whether the group prefers larger or safer pulls',
    'commenting on an enemy type that is awkward for their role',
    'mentioning that resource management is going better now',
    'wondering whether a different target order would feel smoother',
    'commenting on how quickly the group recovers between fights',
    'mentioning that a close call was handled calmly',
    'asking whether everyone is ready before the pace picks up',

    # Roles, classes, and character progress
    'mentioning that their current role feels good in this group',
    'commenting on an ability that is useful more often than expected',
    'wondering how another class approaches the same situation',
    'mentioning a talent choice they are still getting used to',
    'commenting on how their class playstyle has changed while leveling',
    'asking whether another player enjoys their current role',
    'mentioning a class weakness they have learned to work around',
    'commenting on a simple gameplay habit that improved their play',
    'wondering which role they would try on another character',
    'mentioning that they are close to a personal character milestone',
    'commenting on how equipment changes can alter the feel of a class',
    'asking whether someone prefers solo play or group support',

    # Interface, performance, and controls
    'mentioning a minimap detail they almost overlooked',
    'commenting on a brief delay or harmless lag spike',
    'wondering whether anyone else changed a useful interface setting',
    'mentioning a keybind they are still trying to remember',
    'commenting on camera movement in a cramped area',
    'asking whether someone plays with many addons or very few',
    'mentioning that the game music fits the current area well',
    'commenting on how clear or cluttered the screen feels right now',
    'wondering whether a sound cue came from the game or voice chat',
    'mentioning that the frame rate is better away from a busy city',
    'commenting on an interface notification arriving at an odd time',
    'asking whether anyone else accidentally pressed the wrong key',

    # Session habits and ordinary small talk
    'asking how long everyone plans to keep playing',
    'mentioning that they are settling into a relaxed session',
    'commenting on playing after a long day without making it dramatic',
    'asking whether anyone is leveling another character too',
    'mentioning that they came online without a particular plan',
    'commenting on how quickly the session has passed',
    'asking whether the others usually play around this time',
    'mentioning that they may need to step away briefly later',
    'commenting on enjoying quiet conversation while playing',
    'asking a low-pressure question about how everyone is doing',
    'mentioning a snack, drink, or short real-life distraction',
    'commenting that complete sentences are easier than typing in combat',

    # Light humour and player texture
    'making a dry joke about confidently going the wrong direction',
    'joking that the map and the actual route disagree',
    'making a self-deprecating comment about reaction time',
    'joking about forgetting what they were about to say',
    'commenting that standing still somehow became the current strategy',
    'making a mild joke about everyone waiting for everyone else',
    'admitting they were watching the wrong part of the screen',
    'joking about needing more bag space without discussing an item',
    'making a dry observation about another routine repair stop',
    'commenting on a harmless mistake that looked intentional',
    'joking that the group is professionally avoiding the obvious route',
    'mentioning that patience is carrying the run more than skill',
]

# Topics for roleplay mode: the original shared ambient topics plus
# in-character lore, world flavor, faith, culture, and narrative entries.
AMBIENT_CHAT_TOPICS_RP = _AMBIENT_CHAT_TOPICS_SHARED + [
    # Lore / World
    'mentioning a rumor or piece of lore',
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
    'mentioning something they heard about the Scourge or Burning Legion',
    'recalling the most dangerous foe they ever faced',
    # War / Conflict
    'reflecting on a battle they witnessed or heard about',
    'sharing thoughts on the Alliance and Horde conflict',
    'honoring fallen soldiers or comrades',
    # Magic
    'musing about the nature of magic in this world',
    # Personal / Journey
    'reflecting on their purpose or destiny',
    'sharing a moment of doubt or resolve',
    'musing about what drives them to keep adventuring',
    'recalling a lesson an old mentor taught them',
    'remembering the first time they left home',
    'speaking of a promise they mean to keep',
    'naming something they would never do, whatever the cost',
    'wondering what they would do with a year of peace',
    'telling the story behind an old scar',
    'admitting they once misjudged an enemy',
    'remembering a kindness from a stranger',
    'confessing a mistake they still regret',
    'mentioning a keepsake they carry for luck or remembrance',
    'talking about the people they fight for',
    'wishing they had learned some skill when they had the chance',
    'musing about what makes a good companion on the road',
    'reflecting on how war has changed people they knew',
    'repeating a saying their people use in hard times',
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
    'wondering whether courage can be learned',
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
    # Companionship / Banter
    'wondering what the people back home would think of them now',
    'teasing a companion about a habit of theirs',
    'arguing about the best way to spend a day of rest',
    'recalling a feast they will never forget',
    'talking about a friend they lost touch with',
    'wondering which of them would last longest alone in the wild',
    'boasting about a feat that may or may not be true',
    'asking what the others miss most about home',
    'sharing a piece of advice they were once given',
    'mentioning a hero of their people they look up to',
    'reflecting on how they have changed since they first took up arms',
    'wondering whether peace between the factions could ever last',
    'debating whether the fallen kingdoms will ever rise again',
]

# =============================================================================
# PROXIMITY CHAT TOPICS
# =============================================================================
# Topics for proximity /say chatter between bots, NPCs, and the player.
# These are casual, lightweight, daily-life snippets — overheard
# fragments as the player walks through the world.  Distinct from
# AMBIENT_CHAT_TOPICS which are party/group-focused.
# Keep entries short and concrete so the LLM produces brief replies.
# Any speaker may draw any entry, anywhere: a guard, a vendor, a
# traveler or an adventurer, in a city, a camp or a dungeon. So no
# entry may assume the weather, the season or a holiday, a feature
# of the place (a market, a port, ruins outside town), or the
# speaker's job, home or age. Place-bound subjects come from
# location_topics.json (chatter_location_topics) instead.

# Normal-mode (player voice) weather topic; outdoors only.
PROXIMITY_PLAYER_WEATHER_TOPICS = [
    'reacting to the in-game weather or lighting',
]

PROXIMITY_CHAT_TOPICS = [
    # ── Rumors & News ───────────────────────────────────────────────
    'sharing a rumor about trouble on the roads',
    'mentioning travelers arriving from far away',
    'discussing news from the front lines',
    'talking about a merchant caravan that went missing',
    'repeating a rumor heard at an inn',
    'wondering about a mysterious stranger they passed',
    'gossiping about a noble who fell from favor',
    'sharing news of a wedding or birth among friends',
    'mentioning a bounty posted on some outlaw',
    'passing on a warning someone gave them earlier',
    'repeating news from one of the capital cities',
    'wondering whether a rumor they heard is true',
    'mentioning someone who came back from a long journey with strange tales',
    'talking about what the war means for ordinary people',
    'speculating about what the leaders of their faction are planning',

    # ── Commerce & Coin ─────────────────────────────────────────────
    'complaining about rising prices',
    'grumbling about the cost of repairs',
    'talking about a merchant who cheated them',
    'mentioning a bargain they found',
    'talking about trade routes being disrupted',
    'complaining about taxes or tolls',
    'counting how much coin they have left',
    'wondering whether something they bought was worth it',
    'recalling the best deal they ever struck',
    'arguing about whether gold or reputation matters more',

    # ── Fashion & Appearance ────────────────────────────────────────
    'admiring someone passing by and their armor',
    'remarking on the colors of a tabard',
    'wondering where to get boots like those',
    'admiring fine craftsmanship on a weapon or shield',
    'talking about elven tailoring being the finest',
    'commenting on jewelry trends',
    'complaining that their own clothes have seen better days',

    # ── Food & Drink ────────────────────────────────────────────────
    'complaining about watered-down ale',
    'praising a cook they once knew',
    'discussing a recipe they want to try',
    'talking about a terrible meal they had',
    'discussing the merits of dwarven ale vs elven wine',
    'asking if anyone wants to grab a drink later',
    'complaining about bland rations',
    'mentioning a secret ingredient in their cooking',
    'arguing about the best pie they ever ate',
    'mentioning a cheese that pairs well with bread',
    'remembering the taste of food from home',
    'debating what makes a proper hearty stew',

    # ── Travel & Roads ──────────────────────────────────────────────
    'warning about bandits on the roads',
    'complaining about the road conditions',
    'talking about a long journey they just returned from',
    'discussing whether it is safe to travel at night',
    'recommending a good inn they once stayed at',
    'talking about a cart that broke an axle on the road',
    'complaining about the price of flight paths',
    'mentioning a shortcut that turned out to be a mistake',
    'arguing about the best way to pack for a long trip',
    'wondering how long it would take to reach a place they want to see',

    # ── People & Gossip ─────────────────────────────────────────────
    'gossiping about an acquaintance',
    'talking about someone who vanished without a word',
    'mentioning a couple that just got engaged',
    'discussing a hero or adventurer everyone talks about',
    'talking about an old friend they lost touch with',
    'mentioning a family feud they heard about',
    'wondering what happened to someone they used to know',
    'talking about a soldier who came home wounded',
    'gossiping about a secret romance',
    'discussing a healer whose skill everyone praises',
    'mentioning someone who owes them money',
    'talking about an argument they had earlier',
    'wondering why a friend has been avoiding them',

    # ── Lore & History ──────────────────────────────────────────────
    'mentioning a legend they grew up with',
    'talking about the war and how things have changed',
    'recalling a historical battle from the old stories',
    'mentioning an old king or queen from stories',
    'talking about the fall of a great city',
    'mentioning a dragon sighting from years ago',
    'discussing a prophecy an elder once told them',
    'talking about the heroes of the Second War',
    'recalling the stories told about the Third War',
    'wondering what the world was like before the orcs came',
    'mentioning a ghost story they once heard',
    'arguing about which old tale is true',

    # ── Health & Ailments ───────────────────────────────────────────
    'complaining about a bad back',
    'mentioning a healer they should visit',
    'talking about a cold going around',
    'discussing a potion that helped their aches',
    'complaining about not sleeping well',
    'mentioning an old wound acting up',
    'talking about the cost of healing these days',
    'asking if anyone knows a remedy for headaches',
    'discussing herbal remedies that actually work',
    'mentioning they feel better after a good rest',

    # ── Animals & Pets ──────────────────────────────────────────────
    'talking about a loyal animal they once owned',
    'discussing the best breed of horse',
    'complaining about rats getting into the supplies',
    'arguing about whether cats or dogs make better companions',
    'mentioning a wild beast that nearly caught them once',
    'wondering whether animals understand more than they let on',
    'talking about a pet they would like to have',

    # ── Superstition & Omens ────────────────────────────────────────
    'mentioning a bad omen they noticed',
    'talking about a lucky charm they carry',
    'discussing an old wives\' tale about crows',
    'mentioning that full moons bring trouble',
    'talking about a curse they half believe in',
    'mentioning a dream that felt like a warning',
    'discussing a fortune teller they once visited',
    'mentioning that spilling salt is bad luck',
    'arguing about whether luck is real',
    'telling a superstition from their homeland',

    # ── Leisure & Entertainment ─────────────────────────────────────
    'talking about a bard they once heard perform',
    'mentioning a card game they played last night',
    'talking about arm wrestling at a tavern',
    'mentioning a book they just finished',
    'talking about a song stuck in their head',
    'discussing a storyteller they once heard',
    'talking about a race between two riders they saw',
    'discussing the best game to pass the time',
    'mentioning a dice game they lost badly',
    'talking about how they like to spend a free day',

    # ── Romantic & Social ───────────────────────────────────────────
    'mentioning someone they fancy',
    'talking about an anonymous love letter they received',
    'discussing a wedding they attended',
    'mentioning a breakup they heard about',
    'talking about courting customs in their culture',
    'wondering what to get someone as a gift',
    'discussing a dinner invitation they are nervous about',
    'talking about a dance they went to',

    # ── Worries & Hopes ─────────────────────────────────────────────
    'worrying about a loved one far away',
    'hoping for better days ahead',
    'talking about plans for when the war is over',
    'mentioning a letter they need to write',
    'wondering if they made the right choice coming here',
    'talking about saving up for something special',
    'sharing good news they just received',
    'complaining about a promise someone broke',
    'talking about a debt they need to repay',
    'wondering what tomorrow will bring',
    'talking about a skill they are trying to learn',
    'mentioning a favor they owe someone',

    # ── Faith ───────────────────────────────────────────────────────
    'mentioning a prayer they say before a journey',
    'talking about a priest or shaman whose words stayed with them',
    'wondering whether the Light or the spirits really listen',
    'discussing what their people believe happens after death',
    'mentioning a blessing someone gave them',
    'talking about a holy place they hope to visit',

    # ── Complaints & Grumbles ───────────────────────────────────────
    'complaining about the noise at night',
    'complaining about crowds',
    'mentioning a rude merchant they dealt with',
    'grumbling about being kept waiting',
    'complaining that nobody listens to them',
    'grumbling about too much work and too little pay',
    'complaining about a letter that never arrived',
    'grumbling about the price of firewood',
]

# Playerbot-only proximity topics for normal mode. NPCs and roleplay-mode
# playerbots continue to use the in-world pool above.
PROXIMITY_PLAYER_CHAT_TOPICS = [
    # Nearby NPCs and services
    'commenting on an NPC voice line or animation',
    'asking what a nearby vendor sells',
    'mentioning a quest giver or trainer nearby',
    'wondering whether the nearby NPC starts a useful quest chain',
    'asking if the nearby trainer teaches anything new yet',
    'commenting on how often a nearby NPC repeats the same line',
    'pointing out an NPC with an unusually memorable name',
    'asking whether the nearby innkeeper sets a useful hearth location',
    'noticing that a vendor is easy to miss behind other NPCs',
    'wondering why an NPC is standing in such an odd place',
    'mentioning that a nearby NPC is part of a later quest',
    'asking whether the flight master here connects to the next zone',
    'commenting on a nearby guard giving useful directions',
    'asking where the local class or profession trainers are',

    # Zone layout and navigation
    'commenting on the zone layout or visual design',
    'asking which road leads toward the next quest hub',
    'checking whether the group is heading the right way',
    'mentioning that the map makes the route look shorter than it is',
    'asking whether there is a shortcut through the nearby buildings',
    'pointing out a path that is easy to walk past',
    'wondering where the nearest mailbox is',
    'asking whether the bank is in this part of town',
    'mentioning that this city is still confusing to navigate',
    'comparing this zone layout with another leveling zone',
    'noticing an elevator, tram, boat, or portal route nearby',
    'asking which exit avoids a long detour',
    'commenting that the quest marker is sending them in circles',
    'checking the map before choosing a direction',
    'mentioning a nearby landmark used for navigation',

    # Other players and characters
    'noticing another player character passing by',
    'complimenting another player character name',
    'commenting on an unusual race and class combination nearby',
    'noticing someone with an impressive weapon or shield',
    'wondering where another player got a distinctive mount',
    'commenting on a funny pet name',
    'noticing several players waiting around the same NPC',
    'wondering whether a nearby player is waiting for a group',
    'commenting on a character jumping repeatedly while waiting',
    'noticing someone who looks ready for a dungeon',
    'mentioning that a nearby player seems lost',
    'wondering whether the crowd means an event is starting',
    'commenting on a guild name seen nearby',
    'noticing two characters with almost matching names',

    # Vendors, repairs, bags, and town errands
    'asking whether anyone needs to repair or vendor',
    'mentioning that their bags are nearly full',
    'asking whether gray items are worth vendoring here',
    'checking if anyone needs to visit the bank',
    'mentioning that they forgot to buy reagents again',
    'asking where to restock arrows or bullets',
    'wondering whether to keep or vendor a questionable item',
    'commenting on how quickly repair bills add up',
    'asking if the group can pause for a quick sell run',
    'mentioning that bank space disappears too quickly',
    'checking whether the nearby merchant buys unwanted gear',
    'asking if anyone needs food or water before leaving town',
    'mentioning a forgotten hearthstone or missing bag slot',
    'sorting bags while everyone is standing nearby',

    # Waiting and ordinary social chatter
    'making a brief joke about standing around in town',
    'asking how long everyone has been waiting here',
    'mentioning that someone is probably still loading',
    'wondering whether the last group member went AFK',
    'saying hello to someone who just walked up',
    'making polite small talk while another player finishes an errand',
    'asking whether everyone is ready to move',
    'mentioning they can wait a minute if someone needs a break',
    'commenting on how quiet the area is right now',
    'noticing that the same players have been standing here for a while',
    'asking if anyone else is just passing through',
    'making a dry observation about waiting for a slow boat',
    'checking whether the group is still together',
    'welcoming a player who has just arrived',

    # Economy and professions
    'commenting on auction house or vendor prices',
    'wondering whether a material is worth putting on the auction house',
    'asking if anyone nearby can craft a bag',
    'mentioning they are short a few points in a profession',
    'asking where the nearest forge or anvil is',
    'noticing a herb, ore node, or fishing pool on the minimap',
    'commenting on a material that never seems to drop',
    'asking whether gathering in this zone is any good',
    'mentioning that a profession recipe sent them here',
    'wondering whether to level a second profession',
    'asking if anyone needs a quick enchant or crafted item',
    'commenting on the price difference between vendor and auction house',
    'mentioning a stack of materials taking up bag space',
    'asking whether a nearby object is usable for a profession',

    # Transport and movement
    'asking where a nearby path or transport goes',
    'checking how long until the next boat or zeppelin arrives',
    'mentioning that they should have taken the flight path',
    'asking whether everyone has the local flight point',
    'commenting on an awkward jump or narrow walkway',
    'wondering if mounting is allowed in this part of the city',
    'mentioning that autorun nearly sent them the wrong way',
    'asking whether a portal is one-way',
    'commenting on a character getting stuck on scenery',
    'wondering whether swimming across would actually be faster',
    'asking if there is a safer route around nearby mobs',
    'mentioning a long corpse run through this area',
    'commenting on the wait for an elevator platform',
    'asking if the next stop has an inn or flight master',

    # Questing and local gameplay
    'asking whether anyone else has the nearby quest',
    'checking if a quest objective is shared with the group',
    'mentioning that a quest item has a poor drop rate',
    'asking where a hard-to-find quest object spawns',
    'wondering whether a nearby named mob is part of a quest',
    'commenting that the quest text was not very clear',
    'asking whether this hub leads naturally into the next zone',
    'mentioning that they have outleveled one nearby quest',
    'asking if anyone wants help before turning a quest in',
    'wondering whether an escort quest is worth doing',
    'commenting on several quests sharing the same area',
    'asking whether the local quest chain has a good reward',
    'mentioning a quest that is easier with two people',
    'checking whether everyone got credit for the objective',

    # Classes, abilities, and builds
    'asking how another class handles multiple enemies',
    'commenting on a useful movement ability',
    'wondering when their class learns its next important spell',
    'asking whether a talent choice feels noticeable while leveling',
    'mentioning that they forgot to visit the class trainer',
    'commenting on the convenience of portals, summons, or stealth',
    'asking whether someone is using a leveling or dungeon build',
    'mentioning an ability that makes travel easier',
    'wondering how a nearby class manages mana or rage',
    'commenting on a buff that is useful for the current area',
    'asking for a quick class tip without demanding a perfect answer',
    'mentioning that an ability name is easy to confuse with another',
    'commenting on how different two class playstyles feel',
    'asking whether a pet needs to be dismissed before transport',

    # Grouping and dungeon preparation
    'asking whether anyone nearby is looking for the same dungeon',
    'checking whether the group still needs a tank or healer',
    'mentioning that a summon would save everyone some travel time',
    'asking if everyone has repaired before the run',
    'checking whether anyone needs quest sharing before entering',
    'commenting on the group forming faster than expected',
    'wondering whether the instance entrance is nearby',
    'asking if this is the meeting spot for the group',
    'mentioning that one more player should be enough to start',
    'checking whether loot rules have been agreed',
    'asking if the run is meant to be quick or complete',
    'commenting on everyone arriving from different directions',
    'offering to wait for a player who is almost there',
    'asking whether anyone has done this dungeon recently',

    # Interface, performance, and controls
    'mentioning bags, bank space, or profession errands',
    *PROXIMITY_PLAYER_WEATHER_TOPICS,
    'commenting on the music changing in this area',
    'mentioning a brief lag spike without making a scene',
    'asking whether anyone else saw an NPC behave strangely',
    'commenting on a minimap icon they nearly missed',
    'mentioning that the camera angle is awkward in this spot',
    'asking whether a nearby object can actually be clicked',
    'commenting on the loading screen for this area',
    'mentioning a keybind they keep pressing by mistake',
    'wondering why an ability is still on cooldown',
    'commenting on clutter from names or characters nearby',
    'asking whether the game sound gave away something nearby',
    'mentioning that the zone runs more smoothly than a busy city',

    # Light humour and everyday player texture
    'making ordinary small talk while waiting',
    'joking about running past the correct NPC twice',
    'making a self-deprecating comment about getting lost',
    'joking that bag management is the real endgame',
    'commenting dryly on an NPC taking their job very seriously',
    'making a mild joke about everyone jumping while waiting',
    'admitting they were looking at the wrong part of the map',
    'joking about forgetting why they came to town',
    'commenting that the nearby bench looks suspiciously popular',
    'making a gentle joke about a strange character name',
    'mentioning that real life briefly interrupted their route',
    'asking how everyone is doing without forcing conversation',
    'commenting that it is nice to see the area active',
    'sharing a small, harmless real-life aside while waiting',
    'making a dry comment about another routine trip to the bank',
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
    "casually immersed in the game",
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

GOSSIP_CREATIVE_TWISTS = [
    "Frame it as a rumor you heard nearby",
    "Sound mildly skeptical about the subject",
    "Ask a rhetorical question about the subject",
    "Make a quick joke about the subject",
    "Mention how locals might react to the subject",
    "Misremember one harmless detail, then correct yourself",
    "Give an unsolicited opinion about the subject",
    "Keep it brief, like passing gossip",
    "Mention why the subject caught your attention",
    "Compare the subject to someone you met before",
    "Sound like you only half-believe the rumor",
    "Make the comment sound overheard from chat",
    "Mention that the subject has a reputation",
    "Wonder what the subject is really up to",
    "Say the subject seems oddly memorable",
    "Hint that the subject knows more than they say",
    "Mention a small detail about the subject's look",
    "Mention a small detail about the subject's role",
    "Act surprised that nobody else mentioned them",
    "Give a practical warning about the subject",
    "Give a practical compliment about the subject",
    "Make a dry aside about trusting rumors",
    "Sound like you are repeating tavern gossip",
    "Sound like you are trying not to gossip too much",
    "Turn the gossip into a quick question",
    "Answer your own gossip question immediately",
    "Start with 'I heard' or a similar phrase",
    "Start with 'Apparently' or a similar phrase",
    "Suggest the subject is more important than they look",
    "Suggest the subject is less impressive than rumored",
    "Notice how often people talk about the subject",
    "Mention the subject's timing seems suspicious",
    "Frame it as friendly gossip, not accusation",
    "Use a little playful exaggeration",
    "Use understatement about an obvious detail",
    "Focus on what the subject might know",
    "Focus on how the subject affects the zone",
    "Focus on how other adventurers might see them",
    "Make a mild joke about their name",
    "Make a mild joke about their job or role",
    "Sound briefly distracted, then return to the subject",
    "Correct yourself before the rumor gets too wild",
    "End with a small doubt about the rumor",
    "End with a small compliment about the subject",
    "End with a practical takeaway",
    "Keep the tone casual, like idle zone chat",
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
    # Story and presentation
    "commenting on a quest story or lore as a player",
    "reacting to NPC dialogue",
    # Atmospheric
    "appreciating the beauty of the landscape",
    "commenting on the lighting or sky",
    "noting the game's ambient sounds",
    "commenting on the mood the zone creates",
    "describing how weather changes the zone visually",
    "getting immersed in the game for a moment",
    "pausing the run to look at the view",
    "being impressed by the scale of the game world",
    # Lore and wonder from a player's perspective
    "wondering what a magical object does in the game",
    "asking about the story behind an ancient place",
    "being impressed by a magical visual effect",
    "wondering whether a detail matters to a later quest",
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

RP_GOSSIP_CREATIVE_TWISTS = [
    "Frame it as something heard from another traveler",
    "Mention a small rumor without claiming certainty",
    "Make a dry observation about the subject's reputation",
    "Wonder aloud what the subject's story is",
    "Notice how locals seem to regard the subject",
    "Offer an unsolicited opinion about the subject",
    "Add a cautious aside, then return to the subject",
    "Keep the comment understated and matter-of-fact",
    "Use a mild oath, but keep the focus on the subject",
    "Make a wry joke fitting your character about the subject",
    "Speak as if repeating something heard near a hearth",
    "Mention that the road carries many rumors",
    "Frame the subject as part of the local mood",
    "Wonder what burdens the subject carries",
    "Wonder what loyalties guide the subject",
    "Notice a small habit or manner the subject might have",
    "Mention how the subject fits into the surrounding land",
    "Mention how the subject's role shapes local life",
    "Offer guarded praise about the subject",
    "Offer a cautious warning about the subject",
    "Sound impressed but unwilling to say so plainly",
    "Sound skeptical but not hostile",
    "Sound curious despite trying to seem indifferent",
    "Sound like you are trying not to spread gossip",
    "Begin as if the thought slipped out accidentally",
    "Start with a quiet aside about the subject",
    "Use a cultural saying, then tie it to the subject",
    "Use a mild racial oath, then return to the subject",
    "Compare the subject to someone from your homeland",
    "Compare the subject to a traveler from an old tale",
    "Mention a memory the subject brings to mind",
    "Mention an old lesson that applies to the subject",
    "Frame the gossip as tavern talk",
    "Frame the gossip as road talk",
    "Frame the gossip as something scouts would notice",
    "Frame the gossip as something merchants would whisper",
    "Suggest the subject may know more than they reveal",
    "Suggest the subject is watched more closely than they know",
    "Suggest the subject's reputation has grown in the telling",
    "Suggest the subject's reputation may be unfair",
    "Question whether the rumor does the subject justice",
    "Question whether appearances hide the truth",
    "Make a dry joke about believing every rumor",
    "Make a wry comment about local gossip traveling fast",
    "Use understatement about the subject's importance",
    "Use a brief poetic image, but keep it grounded",
    "Let suspicion show for one phrase only",
    "Let admiration show for one phrase only",
    "End with a small reservation",
    "End with a practical observation",
    "End with a quiet joke",
    "Keep the gossip respectful but pointed",
    "Keep the gossip casual, like campfire talk",
    "Keep the gossip focused on what the subject does",
    "Keep the gossip focused on how others see the subject",
    "Avoid certainty; speak as if the truth is still unclear",
    "Avoid drama; make the rumor feel ordinary and lived-in",
]

# Nothing here may assume what the prompt does not supply: the
# weather, the time of day, ruins, a town nearby or a fight that
# never happened. The zone description and nearby creatures are
# supplied, so remarks about the area stay.
RP_MESSAGE_CATEGORIES = [
    # Observations
    "commenting on the area around you",
    "noticing something about the wildlife or creatures",
    "observing other travelers",
    "noting something odd or out of place",
    "remembering a place this one reminds you of",
    # Reactions
    "being relieved about something",
    "bracing for trouble ahead",
    "complaining about the long walk",
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
    # World and lore
    "mentioning something you heard about this place",
    "referencing your homeland briefly",
    "recalling a story or rumor",
    "commenting on the local people or culture",
    "tales of distant lands or adventures",
    "story heard in an inn or from a traveler",
    "mystical story or legend related to the area",
    # Atmospheric
    "feeling uneasy about something nearby",
    "sharing a hope for the days ahead",
    "thinking about the war",
    # Personal
    "thinking about home",
    "remembering an old friend",
    "admitting you're not sure about something",
    "enjoying a quiet moment",
    "grumbling about something minor",
    "mentioning a friend you hope to see again",
    "mentioning something you're looking forward to",
    "sharing a small joke",
    "wondering what the day will bring",
    "noting that your gear could use some mending",
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
DEFAULT_GOOGLE_MODEL = 'gemini-3.1-flash-lite'
DEFAULT_OPENROUTER_MODEL = 'openai/gpt-4o-mini'
GOOGLE_OPENAI_BASE_URL = (
    'https://generativelanguage.googleapis.com/v1beta/openai/'
)
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
# The generic openai_compatible provider deliberately has no default
# model or base URL: both must name the user's own server.

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
    # --- At the keyboard ---
    "you are playing late and starting to get tired",
    "you are eating while trying to keep up with the group",
    "your music is a little too loud for the game audio",
    "you just got back after a very short AFK",
    "you are trying to type between pulls",
    "your attention briefly wandered to another window",
    "you keep reaching for the wrong keybind",
    "your connection had a small lag spike",
    "your frame rate dipped in the busy area",
    "you are wondering how long this session will run",
    # --- Game progress ---
    "you are watching the experience bar creep forward",
    "you are deciding whether the next upgrade is worth it",
    "you forgot to repair before joining the group",
    "your bags are almost full again",
    "your character is low on food or water",
    "you are checking whether everyone finished the quest step",
    "you are trying to remember the quickest route",
    "you are wondering whether a rare spawn is up",
    "you are comparing this run with the last one",
    "you are saving gold for a faster mount",
    "you are one drop away from finishing a set",
    "you are debating whether to vendor an item",
    # --- Group dynamics ---
    "you are not completely sure who is leading",
    "you want to keep the run moving without rushing people",
    "you are mildly annoyed but not looking for an argument",
    "you are impressed by a clean pull",
    "you noticed someone quietly carrying the group",
    "you are trying not to admit that mistake was yours",
    "you are relieved someone else knows the route",
    "you are waiting for the slowest party member to catch up",
    "you want to tease a guildmate without being mean",
    "you are curious why someone chose that talent build",
    "you are hoping nobody starts loot drama",
    "you are trying to make an awkward group less quiet",
    # --- Opinions and mood ---
    "you have a strong opinion about this zone's layout",
    "you like this dungeon more than most players seem to",
    "you are nostalgic for an older run through this content",
    "you are bored with the grind but still making progress",
    "you are in a surprisingly patient mood",
    "you are feeling competitive after a close call",
    "you are quietly pleased with how the group is doing",
    "you find the current situation funnier than it should be",
    "you are skeptical that the advertised strategy is faster",
    "you are trying to stay awake for one more objective",
    # --- Small observations ---
    "you just noticed an odd creature animation",
    "the zone lighting looks better than you remembered",
    "the ambient sound is making the area feel eerie",
    "you spotted a shortcut the group nearly missed",
    "the character model is clipping through the terrain",
    "you are amused by an NPC's repeated voice line",
    "the weather effect is making targets hard to see",
    "you are wondering why this path takes such a long detour",
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


# =============================================================================
# GUILD CHAT TOPICS (roadmap #2) — random subject pool for guild idle chatter.
# Normal mode uses player-side topics. Roleplay mode uses the in-world pool.
# The selected entry is an optional topic nudge, never a required phrase.
# =============================================================================
GUILD_CHAT_TOPICS = [
    # Current activities and check-ins
    "asking what everyone is working on",
    "asking how everyone's current run or questing session is going",
    "checking whether anyone has just logged in",
    "asking what zone people are playing in tonight",
    "mentioning they have a little time before logging off",
    "checking whether the guild is having a quiet or busy evening",
    "asking whether anyone is taking a break between activities",
    "mentioning they are deciding what to do next",
    "asking if anyone wants company while leveling",
    "checking whether someone is still busy in an instance",
    "mentioning they are finishing one last objective",
    "asking whether people are on mains or alts tonight",

    # Groups, dungeons, and raids
    "looking for help with a quest or dungeon",
    "checking whether anyone needs a tank or healer",
    "commenting on a recent wipe or clean pull",
    "asking who is interested in a relaxed dungeon run",
    "checking whether a group has room for one more damage dealer",
    "asking if anyone can help summon at an instance entrance",
    "mentioning that a dungeon quest would be good to clear together",
    "asking whether the group wants a full clear or a quick run",
    "checking who knows the route through a confusing instance",
    "asking whether everyone has repaired and bought consumables",
    "mentioning a boss mechanic that caught the group out last time",
    "asking if anyone wants to continue after the current run",
    "checking whether a raid still needs a particular role",
    "asking what time a planned guild run is starting",
    "mentioning that a patient group matters more than a perfect setup",
    "checking whether newer players need an explanation before a pull",
    "asking who can stay for the whole instance",
    "commenting on a run going more smoothly than expected",

    # Roles, classes, and builds
    "asking how a class feels to level at the moment",
    "checking which role someone prefers to play",
    "asking for a practical talent suggestion",
    "comparing two class abilities without declaring one objectively best",
    "mentioning an ability they keep forgetting to use",
    "asking how another player manages mana, rage, or energy",
    "discussing whether a build is comfortable for solo play",
    "asking which class someone would choose for a new alt",
    "mentioning a class utility spell that saved a recent run",
    "asking whether someone enjoys healing, tanking, or damage more",
    "comparing leveling and dungeon talent choices",
    "giving a guildmate credit for using their class well",
    "asking about a useful keybind or action-bar setup",
    "mentioning that a class becomes more fun after a certain level",

    # Progression, leveling, and alts
    "asking how close someone is to their next level",
    "mentioning a milestone their character recently reached",
    "asking which zone is good for a particular level range",
    "checking whether anyone is leveling an alt in the same range",
    "talking about the difference between leveling solo and in a group",
    "asking which character someone considers their main",
    "mentioning that rested experience makes an alt tempting",
    "asking what class someone tried but never quite enjoyed",
    "discussing whether to finish a zone or move on early",
    "offering to help a lower-level guildmate catch up",
    "remembering when a now-geared character was still leveling",
    "asking what ability or mount someone is working toward next",
    "mentioning that progress was slow but still enjoyable",
    "checking whether anyone needs help with an elite quest",

    # Loot, equipment, and preparation
    "complaining mildly about repair costs",
    "talking about a useful drop or unlucky loot streak",
    "asking whether a new item is actually an upgrade",
    "mentioning a piece of gear that refuses to drop",
    "asking how much importance to give a particular stat",
    "commenting on finally replacing a very old item",
    "checking whether anyone needs an item before disenchanting it",
    "asking what consumables are useful for an upcoming run",
    "mentioning they forgot to repair before traveling",
    "talking about balancing upgrades against saving gold",
    "asking where a useful reputation reward comes from",
    "commenting on an unexpectedly generous loot roll",
    "giving someone credit for passing an item to a guildmate",
    "asking whether to keep an off-spec item",
    "mentioning that bag space is disappearing under spare gear",
    "joking mildly about the game detecting exactly what they need",

    # Professions and the economy
    "asking for profession help or materials",
    "asking whether a guildmate can craft a particular item",
    "offering spare materials before putting them on the auction house",
    "checking who has a particular profession leveled",
    "asking where to farm a material without expecting a perfect route",
    "mentioning a profession skill-up that took too many attempts",
    "asking if anyone needs an enchant while they are in town",
    "talking about whether a recipe is worth buying",
    "commenting on an auction price that seems unusually high or low",
    "asking whether to sell materials now or save them for crafting",
    "mentioning that leveling professions empties the bank quickly",
    "offering to make bags or consumables for a newer guildmate",
    "asking for help locating a profession trainer",
    "comparing gathering while leveling with farming later",
    "mentioning a rare recipe they would like to find",

    # Quests, zones, and exploration
    "sharing a practical tip about a zone or boss",
    "asking whether a quest chain is worth finishing",
    "mentioning a quest objective that is easy to overlook",
    "asking if anyone remembers where a named mob spawns",
    "checking whether a group quest can be shared",
    "talking about a favorite leveling zone",
    "comparing two routes through the same level range",
    "mentioning a zone they always get lost in",
    "asking whether a long escort quest has a useful reward",
    "commenting on a quest story they actually stopped to read",
    "asking if anyone is already near a particular flight point",
    "mentioning an area that looks good but is awkward to traverse",
    "checking whether everyone received quest credit",
    "asking about a shortcut to a distant quest hub",
    "remembering a quest that was harder than its level suggested",

    # Scheduling and guild coordination
    "checking whether anyone is about to go AFK",
    "asking what time people expect to be online tomorrow",
    "checking whether a planned run still suits everyone",
    "mentioning that they may arrive a few minutes late",
    "asking whether someone can hold a spot without pressure",
    "checking who needs a summon before the group starts",
    "asking whether voice chat is needed for the planned activity",
    "mentioning that a shorter run would fit their available time",
    "checking whether the guild bank needs any routine supplies",
    "asking if someone can invite a returning guildmate",
    "welcoming someone back after they have been away",
    "letting the guild know they need to step away briefly",
    "asking whether anyone wants to plan something for the weekend",
    "confirming that it is fine if a run stays casual",

    # Camaraderie and helpfulness
    "teasing a guildmate about a harmless mistake",
    "thanking a guildmate for patient help",
    "congratulating someone on a level, item, or achievement",
    "offering directions to someone who sounds lost",
    "checking whether a new guildmate needs anything explained",
    "reassuring someone after an ordinary mistake",
    "asking how a returning player is finding the game again",
    "offering to fill an inconvenient role for the group",
    "giving someone credit for organizing a run",
    "asking whether anyone needs a quick portal or summon",
    "sharing a useful item instead of vendoring it",
    "saying good luck to guildmates starting a difficult fight",
    "checking on someone whose group has been struggling",
    "mentioning that there is no rush while someone learns",

    # Repetition, grind, and mild frustration
    "commenting on how long the current grind is taking",
    "complaining mildly about a stubborn drop rate",
    "mentioning a quest they will be happy never to repeat",
    "making a restrained comment about an inconvenient corpse run",
    "wondering why one objective takes longer than all the others",
    "commenting on an unlucky series of rolls",
    "mentioning that a route looked simpler on the map",
    "admitting they caused a wipe without becoming dramatic",
    "complaining about forgetting an item back in the bank",
    "mentioning that a mob respawned at exactly the wrong moment",
    "making a dry remark about another repair trip",
    "commenting on a session where very little went to plan",
    "asking whether anyone else is getting unusual lag",

    # Lockouts, PvP, and game systems
    "asking whether an instance lockout is still available",
    "checking whether anyone wants to queue for a battleground",
    "asking which battleground people enjoy most",
    "mentioning a close match without blaming teammates",
    "asking whether the guild needs help defending an objective",
    "commenting on a good flag capture or base defense",
    "discussing a practical battleground tactic",
    "asking whether anyone is working toward a PvP reward",
    "mentioning an opponent who played particularly well",
    "checking when a raid or heroic lockout resets",
    "asking whether a saved instance still has useful bosses available",
    "discussing whether to queue now or wait for another guildmate",
    "commenting on server lag during a busy fight",

    # Routine maintenance and resources
    "mentioning bags, repairs, consumables, or bank space",
    "asking whether everyone remembered ammunition or reagents",
    "mentioning a hearthstone set somewhere inconvenient",
    "checking whether mail or auctions need collecting",
    "asking for a short town stop before the next activity",
    "commenting on how quickly consumables run out",
    "mentioning an inventory cleanup that took longer than expected",
    "asking whether an item should go in the guild bank",
    "checking if anyone needs food or water",
    "mentioning they are reorganizing action bars between runs",
    "asking for a moment to train newly learned abilities",

    # Opinions and playstyles
    "giving someone credit for a good play",
    "debating a route, build, or strategy without hostility",
    "asking whether people prefer efficient runs or relaxed full clears",
    "comparing keyboard turning and mouse movement without being rude",
    "discussing whether guides make the game more or less enjoyable",
    "asking whether someone reads quest text on a first playthrough",
    "talking about soloing versus grouping for ordinary quests",
    "comparing careful pulls with moving quickly",
    "asking what makes a dungeon enjoyable to repeat",
    "discussing when advice is helpful and when to let people learn",
    "mentioning a small quality-of-life setting others may have missed",
    "asking whether someone prefers one main or many alts",
    "comparing busy capital cities with quieter quest hubs",
    "sharing an opinion while making room for other preferences",

    # Humour, nostalgia, and off-topic texture
    "making a dry joke about RNG or server lag",
    "asking who is still online for one more run",
    "talking briefly about something outside the game",
    "remembering a previous guild run",
    "making ordinary small talk while everyone plays",
    "laughing about a harmless mistake from an old guild run",
    "remembering a character name they used years ago",
    "joking about spending more time in the bank than in combat",
    "mentioning a dungeon that still feels familiar after many runs",
    "making a self-deprecating joke about navigation",
    "asking what music people listen to while playing",
    "mentioning a snack or drink during a quiet moment",
    "talking about playing after work, school, or family responsibilities",
    "asking whether anyone else is staying up later than planned",
    "commenting on how different the game feels with a friendly guild",
    "remembering an unexpectedly funny wipe",
    "making a gentle joke about a guildmate's favorite class",
    "asking a low-pressure question about everyone's day",
]


# Guild speakers are in different places, so no entry may assume a
# place, the weather, the season or the hour. The Guild zone and
# subzone topics (chatter_guild) cover talk about where a speaker is.
GUILD_CHAT_TOPICS_RP = [
    "the dangers of the roads these days",
    "a rumor you overheard recently",
    "the code or philosophy you live by",
    "honoring a fallen comrade",
    "a personal vow or quest you carry",
    "distrust of the opposing faction",
    "the burden of your calling",
    "a memory from your homeland",
    "an omen or strange sight on your path",
    "gratitude for a guildmate's aid",
    "the toll of endless fighting",
    "a wish of good fortune for the guild",
    "longing for a quieter life",
    "pride in your craft or lineage",
    "a warning about a place best avoided",
    "resolve before a hard task ahead",
    # --- camaraderie & guild bonds ---
    "what the guild's banner means to you",
    "a newcomer who needs looking after",
    "trust earned in the heat of battle",
    "an oath sworn between guildmates",
    "missing a comrade who rides apart from the rest",
    "a gathering you hope to share when the fighting's done",
    "thanks for a warning that saved your skin",
    "the worth of standing shoulder to shoulder",
    # --- daily life on the road ---
    "a hearty meal you can't stop thinking about",
    "the best tavern you ever set foot in",
    "a drink shared around a campfire",
    "good-natured grumbling about sore feet",
    "the comfort of a warm fire after a cold march",
    "a tune stuck in your head since morning",
    "the simple luxury of dry boots",
    "a long road with no end in sight",
    # --- humor & light banter ---
    "teasing a guildmate about an old blunder",
    "a tall tale you swear is true",
    "boasting (perhaps too much) about a past victory",
    "a ridiculous wager between friends",
    "an argument over the best ale in the land",
    "a cooking mishap around the campfire",
    # --- mood & reflection ---
    "homesickness that creeps in when things go quiet",
    "gratitude for simply seeing another dawn",
    "doubts that visit in the dark hours",
    "the strange peace found in solitude",
    "weariness that sleep won't cure",
    "hope found in a small kindness",
    # --- lore & places ---
    "stories the elders told when you were young",
    "a festival or holy day from your youth",
    # --- the calling & the blade ---
    "the weight of the weapon you carry",
    "scars that each tell their own story",
    "an enemy you respect despite everything",
    "the thin line between duty and vengeance",
    "the first time you faced true danger",
    "the discipline your training demanded",
    # --- faction & war ---
    "the price the war has taken from your people",
    "an uneasy truce you doubt will hold",
    "tales of heroes who turned the tide",
    # --- nature, beasts & weather ---
    "a loyal beast that once saved your life",
    # --- craft & trade ---
    "the satisfaction of mending your own gear by hand",
    "the smell of a forge or a brewing pot",
    "a trade secret passed down in your family",
    "pride in something you made with your hands",
    # --- omens & the uncanny ---
    "a dream that felt like a warning",
    "a stranger's cryptic words on the road",
    "lights or sounds with no earthly source",
    "a curse you half-believe in",
    # --- legacy & loss ---
    "what you'd want remembered after you're gone",
    "a debt of honor still unpaid",
    "the names of those you've lost",
    # --- roads & memories ---
    "a place you swore never to return to",
    "the strangest thing you ever saw on your travels",
    "a landmark of your homeland you miss",
    "the hardest journey you ever made",
    "a night watch you will never forget",
    "an animal companion you remember fondly",
    "a lesson learned the hard way",
    "a city you'd most like to see again",
    # --- the guild at ease ---
    "a song the guild should learn together",
    "what you'd do with a month of rest",
    "advice for a guildmate just starting out",
    "a meal you'd cook for the whole guild",
]

# Per-language tables (ZONE_NAMES, ZONE_FLAVOR, BG_LORE,
# DUNGEON_FLAVOR and RACE_SPEECH_PROFILES for ruRU, frFR,
# deDE, esES and koKR) live in the locales package rather
# than here. They are bulk translation data, and keeping
# them out of this module keeps it about game constants.
# See tools/locales/__init__.py for the registry.
