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
ZONE_NAMES_RU = {
    1: "Дун Морог", 3: "Бесплодные земли", 4: "Выжженные земли",
    8: "Болото Печали", 10: "Сумеречный лес", 11: "Болотина",
    12: "Элвиннский лес", 14: "Дуротар", 15: "Пылевые топи",
    16: "Азшара", 17: "Степи", 28: "Западные Чумные земли",
    33: "Тернистая долина", 38: "Лок Модан", 40: "Западный Край",
    41: "Перевал Мертвого Ветра", 44: "Красногорье", 45: "Нагорье Арати",
    46: "Пылающие степи", 47: "Внутренние земли", 51: "Тлеющее ущелье",
    65: "Драконий Погост", 66: "Зул'Драк", 67: "Грозовая Гряда",
    85: "Тирисфальские леса", 130: "Серебряный бор", 139: "Восточные Чумные земли",
    141: "Тельдрассил", 148: "Темные берега", 210: "Ледяная Корона",
    215: "Мулгор", 267: "Предгорья Хилсбрада", 331: "Ясеневый лес",
    357: "Фералас", 361: "Оскверненный лес", 394: "Седые холмы",
    400: "Тысяча Игл", 405: "Пустоши", 406: "Когтистые горы",
    440: "Танарис", 490: "Кратер Ун'Горо", 493: "Лунная поляна",
    495: "Ревущий фьорд", 618: "Зимние Ключи", 1377: "Силитус",
    1497: "Подгород", 1519: "Штормград", 1537: "Стальгорн",
    1637: "Оргриммар", 1638: "Громовой Утес", 1657: "Дарнас",
    2817: "Лес Хрустальной Песни", 3430: "Леса Вечной Песни", 3433: "Призрачные земли",
    3483: "Полуостров Адского Пламени", 3487: "Луносвет", 3518: "Награнд",
    3519: "Лес Тероккар", 3520: "Долина Призрачной Луны", 3521: "Зангартопь",
    3522: "Острогорье", 3523: "Пустоверть", 3524: "Остров Лазурной Дымки",
    3525: "Остров Кровавой Дымки", 3537: "Борейская тундра", 3557: "Экзодар",
    3703: "Шаттрат", 3711: "Низина Шолазар", 4080: "Остров Кель'Данас",
    4197: "Озеро Ледяных Оков", 4228: "Окулус", 4395: "Даларан",
}

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
ZONE_NAMES_FR = {
    1: "Dun Morogh", 3: "Terres Ingrates", 4: "Terres Foudroyées",
    8: "Marais des chagrins", 10: "Bois de la pénombre", 11: "Les Paluns",
    12: "Forêt d'Elwynn", 14: "Durotar", 15: "Marécage d'Aprefange",
    16: "Azshara", 28: "Maleterres de l'Ouest",
    33: "Vallée de Strangleronce", 38: "Loch Modan",
    40: "La Marche de l'Ouest", 41: "Défilé de Deuillevent",
    44: "Les Carmines", 45: "Hautes-terres d'Arathi", 46: "Steppes ardentes",
    47: "Les Hinterlands", 51: "Gorge des Vents brûlants",
    85: "Clairières de Tirisfal", 130: "Forêt des Pins argentés",
    139: "Maleterres de l'Est", 141: "Teldrassil", 148: "Sombrivage",
    215: "Mulgore", 267: "Contreforts de Hautebrande", 331: "Ashenvale",
    357: "Feralas", 361: "Gangrebois", 400: "Mille pointes", 405: "Desolace",
    406: "Les Serres-Rocheuses", 440: "Tanaris", 490: "Cratère d'Un'Goro",
    493: "Reflet-de-Lune", 618: "Berceau-de-l'Hiver", 1377: "Silithus",
    1497: "Les Fossoyeuses", 1519: "Hurlevent", 1537: "Forgefer",
    1637: "Orgrimmar", 1638: "Pitons-du-Tonnerre", 1657: "Darnassus",
    3483: "Péninsule des Flammes Infernales", 3518: "Nagrand",
    3519: "Forêt de Terokkar", 3520: "Vallée d'Ombrelune",
    3521: "Marécage de Zangar", 3522: "Les Tranchantes",
    3523: "Raz-de-néant", 3703: "Shattrath",
    65: "Désolation des Dragons",  # verified: official Blizzard fr-fr news source
    66: "Zul'Drak",  # verified: official Blizzard fr-fr news source
    67: "Pics Foudroyés",  # verified: official Blizzard fr-fr news source
    210: "Couronne de Glace",  # verified: official Blizzard fr-fr news source
    394: "Les Grisonnes",  # verified: official Blizzard fr-fr news source
    495: "Fjord Hurlant",  # verified: official Blizzard fr-fr news source
    3537: "Toundra Boréenne",  # verified: official Blizzard fr-fr news source
    3711: "Bassin de Sholazar",  # verified: official Blizzard fr-fr news source
    3525: "Île de Brume-Sang", 4080: "Île de Quel'Danas",
    3430: "Bois des Chants Éternels", 3524: "Île de Brume-Azur",
    3433: "Les Terres Fantômes", 4197: "Joug-d'Hiver",
    2817: "Forêt du Chant de Cristal", 3487: "Lune-d'Argent",
    3557: "L'Exodar", 4228: "L'Oculus",
}

ZONE_NAMES_DE = {
    1: "Dun Morogh", 3: "Ödland", 4: "Verwüstete Lande",
    8: "Sümpfe des Elends", 10: "Dämmerwald", 11: "Sumpfland",
    12: "Wald von Elwynn", 14: "Durotar", 15: "Düstermarschen",
    16: "Azshara", 28: "Westliche Pestländer", 33: "Schlingendorntal",
    38: "Loch Modan", 40: "Westfall", 41: "Gebirgspass der Totenwinde",
    44: "Rotkammgebirge", 45: "Arathihochland", 46: "Brennende Steppe",
    47: "Hinterland", 51: "Sengende Schlucht", 65: "Drachenöde",
    66: "Zul'Drak", 67: "Die Sturmgipfel", 85: "Tirisfal", 130: "Silberwald",
    139: "Östliche Pestländer", 141: "Teldrassil", 148: "Dunkelküste",
    210: "Eiskrone", 215: "Mulgore", 267: "Vorgebirge des Hügellands",
    331: "Eschental", 357: "Feralas", 361: "Teufelswald",
    394: "Grizzlyhügel", 400: "Tausend Nadeln", 405: "Desolace",
    406: "Steinkrallengebirge", 440: "Tanaris", 490: "Krater von Un'Goro",
    493: "Mondlichtung", 495: "Der Heulende Fjord", 618: "Winterquell",
    1377: "Silithus", 1497: "Unterstadt", 1519: "Sturmwind",
    1537: "Eisenschmiede", 1637: "Orgrimmar", 1638: "Donnerfels",
    1657: "Darnassus", 2817: "Kristallsangwald", 3430: "Immersangwald",
    3433: "Geisterlande", 3483: "Höllenfeuerhalbinsel", 3487: "Silbermond",
    3518: "Nagrand", 3519: "Wälder von Terokkar", 3520: "Schattenmondtal",
    3521: "Zangarmarschen", 3522: "Schergrat", 3523: "Nethersturm",
    3524: "Azurmythosinsel", 3525: "Blutmythosinsel",
    3537: "Boreanische Tundra", 3703: "Shattrath", 3711: "Sholazarbecken",
    4080: "Insel von Quel'Danas", 4197: "Tausendwintersee", 4395: "Dalaran",
}

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
ZONE_NAMES_ES = {
    1: "Dun Morogh", 3: "Tierras Inhóspitas", 4: "Las Tierras Devastadas",
    8: "Pantano de las Penas", 10: "Bosque del Ocaso", 11: "Los Humedales",
    12: "Bosque de Elwynn", 14: "Durotar", 15: "Marjal Revolcafango",
    16: "Azshara", 28: "Tierras de la Peste del Oeste",
    33: "Vega de Tuercespina", 38: "Loch Modan", 40: "Páramos de Poniente",
    41: "Paso de la Muerte", 44: "Montañas Crestagrana",
    45: "Tierras Altas de Arathi", 46: "Las Estepas Ardientes",
    47: "Tierras del Interior", 51: "La Garganta de Fuego",
    85: "Claros de Trisfal", 130: "Bosque de Argénteos",
    139: "Tierras de la Peste del Este", 141: "Teldrassil",
    148: "Costa Oscura", 215: "Mulgore", 267: "Laderas de Trabalomas",
    331: "Vallefresno", 357: "Feralas", 361: "Frondavil",
    400: "Las Mil Agujas", 405: "Desolace", 406: "Sierra Espolón",
    440: "Tanaris", 490: "Cráter de Un'Goro", 493: "Claro de la Luna",
    495: "Fiordo Aquilonal",  # verified: official Blizzard es-es news source
    618: "Cuna del Invierno", 1377: "Silithus", 1497: "Entrañas",
    1519: "Ciudad de Ventormenta", 1537: "Forjaz", 1637: "Orgrimmar",
    1638: "Cima del Trueno", 1657: "Darnassus",
    3483: "Península del Fuego Infernal",  # verified: official Blizzard es-es news source
    3537: "Tundra Boreal",  # verified: official Blizzard es-es news source
    65: "Cementerio de Dragones",  # verified: official Blizzard es-es news source
    66: "Zul'Drak",  # verified: official Blizzard es-es news source
    67: "Cumbres Tormentosas",  # verified: official Blizzard es-es news source
    210: "Corona de Hielo",  # verified: official Blizzard es-es news source
    394: "Colinas Pardas",  # verified: official Blizzard es-es news source
    3711: "Cuenca de Sholazar",  # verified: official Blizzard es-es news source
    3522: "Montañas Filoespada", 3523: "Tormenta Abisal",
    3520: "Valle Sombraluna", 3519: "Bosque de Terokkar",
    3521: "Marisma de Zangar", 2817: "Bosque Canto de Cristal",
    4197: "Conquista del Invierno", 3524: "Isla Bruma Azur",
    3525: "Isla Bruma de Sangre", 3430: "Bosque Canción Eterna",
    3433: "Tierras Fantasma", 3487: "Ciudad de Lunargenta",
    17: "Los Baldíos", 3703: "Ciudad de Shattrath",
    3557: "El Exodar", 4228: "El Oculus",
    4080: "Isla de Quel'Danas",
}

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
ZONE_NAMES_KO = {
    65: "용의 안식처",  # verified: official Blizzard ko-kr news source
    66: "줄드락",  # verified: official Blizzard ko-kr news source
    67: "폭풍우 봉우리",  # verified: official Blizzard ko-kr news source
    210: "얼음왕관",  # verified: official Blizzard ko-kr news source
    394: "회색 구릉지",  # verified: official Blizzard ko-kr news source
    495: "울부짖는 협만",  # verified: official Blizzard ko-kr news source
    3537: "북풍의 땅",  # verified: official Blizzard ko-kr news source
    3711: "숄라자르 분지",  # verified: official Blizzard ko-kr news source
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
RACE_SPEECH_PROFILES_RU = {
    "Human": {
        "traits": [
            "практичны, стойки, гражданственны, дисциплинированны и быстро сплачиваются в кризис",
            "приспособляемы, амбициозны, ориентированы на общину, движимы долгом и возможностями",
            "верны короне и товарищам, закалены войной, руководствуются прагматичным идеализмом",
            "находчивы и трудолюбивы, сочетают приграничную стойкость с космополитичной дипломатией",
            "патриотичны и преданы долгу, закалены потерями, но упрямо надеются на будущее",
            "социально проницательны, сведущи в торговле и склонны строить союзы, а не таить обиды",
            "храбры под огнём, быстро организуются и тяжело переносят затяжную неопределённость",
            "укоренены в традициях, но открыты новым идеям, когда того требует выживание",
        ],
        "flavor_words": [
            "за Альянс", "во имя Света", "Штормград",
            "Лордерон", "собор", "король Вариан",
            "честь", "долг", "королевство",
            "Нортшир", "корона", "павшие герои",
        ],
        "vocabulary": [
            ("Light be with you", "благословение/приветствие"),
            ("By the Light!", "восклицание удивления или решимости"),
            ("Well met", "формальное приветствие"),
            ("For the Alliance!", "боевой клич"),
            ("Go with honor, friend", "прощание"),
            ("Safe travels", "прощание"),
        ],
        "lore": [
            "Люди отстроили Штормград после разрушений ранних войн.",
            "Северные людские королевства были разрушены, особенно Лордерон — Плетью.",
            "Церковь Света оказывает сильное влияние на культуру и институты.",
            "Рыцарские ордена, ополчение и традиции городской стражи — центральные общественные опоры.",
            "Штормград под властью короля Вариана — важный политический и военный центр Альянса.",
            "Людские земли балансируют между идеализмом, давлением выживания и реальной политикой.",
            "Записи титанов в Нордсколе связывают происхождение людей с врайкулами.",
        ],
        "worldview": (
            "Политика людей сосредоточена вокруг Штормграда и военных усилий Альянса. "
            "Вера в Свет, военная служба и гражданский порядок — сильные общественные нормы. "
            "После потерь в Лордероне и повторных вторжений людские общины настороженны, "
            "патриотичны и сосредоточены на безопасности."
        ),
    },
    "Orc": {
        "traits": [
            "прямолинейны, горды, привержены чести, племенные, напористы и защищают с трудом добытую свободу",
            "яростно преданы клану, закалены войной, движимы потребностью доказать свою ценность",
            "прямолинейны и склонны к конфронтации, ценят силу, смягчённую мудростью предков",
            "страстно относятся к чести, подозрительны к дипломатии, быстро бросают вызов слабости",
            "закалены битвами, общинны, обретают идентичность через общую борьбу и победу",
            "духовно укоренены в шаманской традиции, но преследуемы наследием порчи",
            "прямолинейны в речи и нетерпеливы к политике, предпочитают действие размышлениям",
            "глубоко защищают суверенитет Орды, настороженны к чужакам и гордятся выживанием",
        ],
        "flavor_words": [
            "Лок'тар огар", "кровь и гром", "за Орду",
            "Дуротар", "Оргриммар", "предки",
            "честь", "кланы", "Тралл",
            "Дренор", "боевые барабаны", "духи волков",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "Победа или смерть!"),
            ("Zug-zug", "согласие, вроде «ладно»"),
            ("Dabu", "я подчиняюсь / я согласен"),
            ("Throm-ka", "рад встрече"),
            ("Aka'Magosh", "благословение тебе и твоим близким"),
            ("Lok-Narash!", "К оружию!"),
            ("Gol'Kosh!", "Клянусь топором!"),
        ],
        "lore": [
            "Орки пришли с Дренора и были обмануты, впав в скверну Пылающего Легиона.",
            "После Второй войны многих держали в лагерях для интернированных.",
            "Тралл объединил кланы и основал новую Орду в Дуротаре.",
            "Шаманские традиции и почитание предков были возрождены после прежней скверны.",
            "Орочье общество ценит память клана, воинскую доблесть и личную честь.",
            "В эпоху Гнева восхождение Гарроша Адского Крика во главе Орды обостряет политическую напряжённость.",
            "Наследие демонического порабощения по-прежнему формирует их идентичность и гордость.",
        ],
        "worldview": (
            "Идентичность орков в новой Орде строится на исцелении от демонической скверны, "
            "верности клану и Орде, а также на возрождённых шаманских традициях. Дуротар и "
            "Оргриммар символизируют самоуправление после интернирования. Честь, сила и "
            "выживание воспринимаются как неразрывные обязанности."
        ),
    },
    "Dwarf": {
        "traits": [
            "крепкие, упрямые, гордятся ремеслом, верны клану, прямолинейны и любопытны к древним тайнам",
            "непоколебимы в бою, любят выпивку и байки, преданы родне до глубины души",
            "суровы, но добросердечны, глубоко уважают традиции и честный труд",
            "бесконечно любопытны к реликвиям титанов, стремятся копать глубже и знать больше",
            "просты в речах, упрямы в лучшем смысле слова, преданы до последнего",
            "гордятся кузницей и семьёй, быстро смеются и медленно прощают предательство",
            "практичны и приземлены, доверяют молотам и рукопожатиям больше, чем красивым словам",
            "стойки духом и выносливы, закалены горными зимами и веками клановых распрей",
        ],
        "flavor_words": [
            "клянусь бородой", "ага", "камень и сталь",
            "Стальгорн", "Каз Модан", "клан",
            "кузница", "эль", "реликвии титанов",
            "гора", "Лига исследователей", "наковальня",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "прощание"),
            ("Fer Khaz Modan!", "За Каз Модан! — боевой клич"),
            ("Well met", "приветствие"),
            ("Off with ye", "непринуждённое прощание"),
        ],
        "lore": [
            "Дворфы произошли от земельников, созданных титанами и изменённых Проклятием Плоти.",
            "Три главных клана определяют политику: Бронзобороды, Хмельногривы и Тёмное Железо.",
            "Стальгорн — ключевой оплот Альянса и торговый центр.",
            "Инженерное дело, кузнечное ремесло, огнестрельное оружие и пивоварение — главные культурные сильные стороны.",
            "Лига исследователей ведёт археологические изыскания и исследования титанов по всему Азероту.",
            "Клановая память и обиды могут длиться поколениями.",
            "Дворфы — закалённые в боях ветераны Альянса, прошедшие через множество войн.",
        ],
        "worldview": (
            "Дворфийское общество организовано по кланам и тесно связано со Стальгорном, "
            "ремесленными традициями и археологией титанов. Уважаются как военная служба, "
            "так и практический труд. Союзы оцениваются по верности и доказанным делам."
        ),
    },
    "Night Elf": {
        "traits": [
            "древние, благоговейные, замкнутые, терпеливые, гордые и яростно защищают природу",
            "созерцательны и уравновешенны, хранят тысячелетия памяти в каждом решении",
            "глубоко духовны, чувствительны к лунным циклам и настороженны к безрассудству чародейства",
            "изящны, но свирепы в защите священных рощ и земель предков",
            "сдержанны с чужаками, но безмерно преданы в узах доверия и общей цели",
            "меланхоличны, но непреклонны, закалены утраченным бессмертием и долгом, который не угасает",
            "внимательны и неторопливы, предпочитают терпение и точность спешке",
            "тихо властны, черпают авторитет из возраста и преданности, а не из звания",
        ],
        "flavor_words": [
            "Элуна", "да хранит тебя Элуна", "звёздный свет",
            "калдорай", "Дарнас", "Нордрассил",
            "древние корни", "Тельдрассил", "древние обычаи",
            "Кенарий", "лунный свет", "Изумрудный Сон",
        ],
        "vocabulary": [
            ("Ishnu-alah", "удачи тебе"),
            ("Ishnu-dal-dieb", "удачи твоей семье"),
            ("Elune-adore", "да пребудет с тобой Элуна"),
            ("Ande'thoras-ethil", "пусть твои беды поубавятся"),
            ("Andu-falah-dor!", "да восстановится равновесие!"),
            ("Bandu Thoribas!", "готовьтесь к бою!"),
            ("Fandu-dath-belore?", "кто идёт?"),
            ("Tor ilisar'thera'nal!", "да трепещут наши враги!"),
        ],
        "lore": [
            "Древняя цивилизация калдорай была разрушена Раздроблением.",
            "Сильная преданность Элуне, друидизму и традициям стражей.",
            "Долгая история борьбы с демонами, сатирами и порчей в священных лесах.",
            "Бессмертие закончилось после событий вокруг Нордрассила и Третьей войны.",
            "Членство в Альянсе после событий Warcraft III остаётся практичным, а не тесным.",
            "Защита мировых древ, священных рощ и заповедных чащ — центральная ценность.",
            "Избыток чародейства внушает страх из-за памяти о прошлой всемирной катастрофе.",
        ],
        "worldview": (
            "Приоритеты калдорай — защита священных земель, почитание Элуны и друидическое "
            "равновесие. Коллективная память о Раздроблении делает их осторожными в отношении "
            "безрассудного использования чародейства. Сотрудничество с Альянсом существует, "
            "но культурная дистанция с более молодыми расами сохраняется."
        ),
    },
    "Undead": {
        "traits": [
            "мрачно ироничны, озлобленны, прагматичны, безжалостны, ориентированы на выживание и крайне замкнуты",
            "холодны и расчётливы, никому не доверяют полностью, но верны тем, кто доказал себя",
            "мрачно-юмористичны, прямолинейны в отношении смерти и презирают наивный оптимизм",
            "движимы местью и самосохранением, мало терпимы к сентиментальности",
            "холодны и отстранённы, смотрят на живых со смесью зависти и презрения",
            "хитры и находчивы, ожидают худшего от союзников из-за пережитых предательств",
            "мрачно решительны, находят смысл в упрямстве, а не в надежде",
            "территориальны и подозрительны, безжалостно защищают интересы Отрёкшихся",
        ],
        "flavor_words": [
            "Тёмная Госпожа", "чума", "могила",
            "Отрёкшиеся", "Подгород", "Плеть",
            "месть", "аптекарь", "Лордерон",
            "тлен", "свободная воля", "Король-лич",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "прощание/благословение"),
            ("Victory for Sylvanas", "боевой клич"),
            ("Embrace the shadow", "прощание"),
            ("Our time will come", "выражение решимости"),
        ],
        "lore": [
            "Отрёкшиеся — бывшая нежить Плети, вернувшая себе свободную волю.",
            "Их ведёт Сильвана Ветрокрылая из Подгорода.",
            "Рождены из руин Лордерона и отвергнуты большинством живых.",
            "Королевское аптекарское общество разрабатывает чуму и другое жестокое химическое оружие.",
            "События эпохи Гнева включают предательство у Врат Гнева и внутренние фракционные чистки.",
            "Членство в Орде стратегично и часто отмечено взаимным недоверием.",
            "Месть Королю-личу — ключевой эмоциональный и политический двигатель.",
        ],
        "worldview": (
            "Политика Отрёкшихся сосредоточена на сохранении свободной воли, удержании "
            "владений в Лордероне и уничтожении угроз Плети. Общество Подгорода сильно "
            "военизировано и находится под сильным влиянием аптекарских и разведывательных "
            "сетей. Их отношения с Ордой стратегические, определяются скорее общими врагами, "
            "чем доверием."
        ),
    },
    "Tauren": {
        "traits": [
            "спокойны, приземлены, духовны, честны, терпеливы и защищают родню и землю",
            "мягки в совете, но непоколебимы в защите, руководствуются старейшинами и древними обрядами",
            "глубоко общинны, оценивают ценность через служение племени, а не личную славу",
            "созерцательны и медленно гневаются, но сокрушительны, если пробуждены на защиту невинных",
            "почитают природу и предков, находят мудрость в смене сезонов и течении лет",
            "стойки и надёжны, предпочитают взвешенные слова и решительные действия хвастовству",
            "тепло и гостеприимно относятся к союзникам, осторожны и настороженны с чужаками",
            "духовно чутки и физически внушительны, сочетают нежность с грубой силой",
        ],
        "flavor_words": [
            "Мать-Земля", "великая охота", "предки",
            "Громовой Утёс", "шу'хало", "равнины",
            "Мулгор", "старейшины племени", "охота",
            "тотем", "Кэрн", "ветер",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "прощание/благословение"),
            ("Ancestors watch over you", "прощание"),
            ("Winds be at your back", "прощание/благословение"),
            ("Earth Mother guide you", "благословение"),
        ],
        "lore": [
            "Кочевые племена были объединены Кэрном Кровавым Копытом.",
            "Громовой Утёс стал центральным городом тауренов в Мулгоре.",
            "Духовная жизнь сосредоточена вокруг Матери-Земли и предков.",
            "Друидизм и шаманизм — основные культурные опоры.",
            "Присоединились к Орде после орочьей помощи против набегов кентавров.",
            "Сильная культура охоты и устных преданий сохраняет их идентичность и историю.",
            "В эпоху Гнева Кэрн Кровавое Копыто — один из старших лидеров Орды.",
        ],
        "worldview": (
            "Общественный порядок тауренов делает акцент на племенном долге, старейшинах и "
            "почитании Матери-Земли и предков. Они ценят посредничество и сдержанность, но "
            "решительно защищают родню и территорию. Членство в Орде преподносится как "
            "клятва благодарности и взаимной защиты."
        ),
    },
    "Gnome": {
        "traits": [
            "изобретательны, любопытны, жизнерадостны, аналитичны, быстро соображают и неутомимы под давлением",
            "бесконечно оптимистичны, воспринимают неудачи как данные, а не поражения",
            "технически одержимы, склонны к жаргону и искренне восторгаются изящными решениями",
            "упрямы и решительны, компенсируют малый рост непомерной уверенностью",
            "интеллектуально неугомонны, постоянно возятся с идеями даже в непринуждённой беседе",
            "жизнерадостны и эксцентричны, воспринимают опасность как инженерную задачу",
            "методичны, но спонтанны, переключаются между тщательным анализом и диким импровизированием",
            "социально воодушевлены, охотно объясняют свои изобретения, спрашивают их об этом или нет",
        ],
        "flavor_words": [
            "возня с механизмами", "по моим расчётам", "гениально",
            "Высший Механик", "Меккаторк", "Гномреган",
            "шестерёнки", "чертежи", "прототип",
            "изобретение", "калибровка", "свеча зажигания",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "боевой клич"),
            ("Salutations!", "формальное приветствие"),
            ("My, you're a tall one!", "приветствие с самоиронией"),
        ],
        "lore": [
            "Родом из Гномрегана, славятся инженерным делом и изобретательством.",
            "Город был потерян из-за нашествия троггов и катастрофического облучения.",
            "Выжившие стали беженцами, приютившимися рядом со Стальгорном.",
            "Высший Механик Меккаторк возглавляет усилия по восстановлению в эпоху Гнева.",
            "Культура ценит эксперименты, импровизацию и техническую грамотность.",
            "Инженерное дело охватывает войну, транспорт, медицину и повседневные инструменты.",
            "Тесные связи с Альянсом, особенно с дворфами в Стальгорне.",
        ],
        "worldview": (
            "Гномья культура воспринимает инженерное дело и науку как гражданский долг, а не "
            "просто профессию. Восстановление Гномрегана остаётся объединяющей политической "
            "целью под руководством Гелбина Меккаторка. Их роль в Альянсе часто сосредоточена "
            "на логистике, изобретениях и технической поддержке."
        ),
    },
    "Troll": {
        "traits": [
            "невозмутимы, духовны, изворотливы, горды, приспособляемы и опасны, если их разозлить",
            "внешне беспечны, но яростно преданы племени под этой непринуждённой манерой",
            "хитры и проницательны, быстро считывают ситуацию и адаптируются без колебаний",
            "суеверны и почитают лоа, вплетают веру в повседневные решения",
            "гордятся наследием Черного Копья, носят изгнание и выживание как знак идентичности",
            "расслаблены и веселы в компании, но холодны и сосредоточены при появлении угрозы",
            "терпеливы и оппортунистичны, предпочитают ждать подходящего момента для удара",
            "глубоко общинны, ценят верность племени выше личных амбиций или комфорта",
        ],
        "flavor_words": [
            "приятель", "духи", "лоа",
            "Черное Копьё", "Волджин", "Эхо-острова",
            "вуду", "предки", "охотник за тенями",
            "остров", "джуджу", "жертвоприношение",
        ],
        "vocabulary": [
            ("Taz'dingo!", "боевой клич / возглас радости"),
            ("Spirits be with ya, mon", "прощание/благословение"),
            ("Stay away from da voodoo", "предостережение/прощание"),
        ],
        "lore": [
            "Играбельные тролли — Черное Копьё, а не амани и не гурубаши.",
            "Тролли Черного Копья были спасены Траллом и присоединились к Орде.",
            "Почитание лоа, практика вуду и традиции охотников за тенями формируют их культуру.",
            "Волджин возглавляет Черное Копьё в политике эпохи Гнева.",
            "Древние империи троллей предшествуют многим более молодым цивилизациям Азерота.",
            "Идентичность Черного Копья сформирована изгнанием, миграцией и выживанием на окраинах.",
            "Племенная память и практическая духовность направляют повседневные решения.",
        ],
        "worldview": (
            "Мировоззрение Черного Копья племенное, ориентировано на выживание и опирается на "
            "традиции лоа. Руководство Волджина подчёркивает верность Орде при сохранении "
            "самобытной троллиной идентичности. Устная история, практика охотников за тенями и "
            "приспособляемость — ключевые культурные черты."
        ),
    },
    "Blood Elf": {
        "traits": [
            "горды, изящны, дисциплинированны, заботятся об имидже, сосредоточены на чародействе и эмоционально сдержанны",
            "утончённы и невозмутимы, скрывают глубокую скорбь за самообладанием и культурной гордостью",
            "магически одарены и интеллектуально остры, предъявляют жёсткие требования ко всему",
            "политически проницательны, ведут союзы с изяществом, но мало кому доверяют полностью",
            "эстетически ориентированы, ценят красоту и порядок как выражение национальной идентичности",
            "стойки под лоском, закалены зависимостью, предательством и национальной катастрофой",
            "социально изящны, но внутренне напряжённы, направляют страсть в долг и мастерство",
            "достойны и самодостаточны, воспринимают спокойствие под давлением как моральный долг",
        ],
        "flavor_words": [
            "синдорай", "Солнечный Колодец", "чародейство",
            "Кель'Талас", "Луносвет", "регент-лорд",
            "Лор'темар", "мана", "магистры",
            "рыцари крови", "Кель'тас", "Шпиль",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "приветствие, путник"),
            ("Shorel'aran", "прощание"),
            ("Selama ashal'anore", "справедливость для нашего народа"),
            ("Anar'alah belore", "светом солнца"),
            ("Anu belore dela'na", "солнце ведёт нас"),
            ("Sinu a'manore", "рад встрече"),
            ("Doral ana'diel?", "как поживаешь?"),
            ("Al diel shala", "счастливого пути"),
        ],
        "lore": [
            "Синдорай — выжившие из Кель'Таласа после разрушений, причинённых Плетью.",
            "Уничтожение их священного источника вызвало магическую ломку и общественный кризис.",
            "Союз Кель'таса с Легионом закончился открытым предательством.",
            "Солнечный Колодец был восстановлен Светом и энергией чародейства в конце эпохи Пылающего Крестового похода.",
            "Лор'темар Терон правит как регент-лорд в эпоху Гнева.",
            "Рыцари крови перешли от высасывания силы к служению восстановленным источникам Света.",
            "Связи с Ордой прагматичны, обусловлены политикой, памятью и выживанием.",
        ],
        "worldview": (
            "Политика эльфов крови в приоритете ставит безопасность Кель'Таласа, защиту "
            "восстановленного Солнечного Колодца и контроль над источниками чародейства. "
            "Общественная культура ценит дисциплину и достоинство после национальной травмы. "
            "Членство в Орде — практическая государственная политика, обусловленная прошлым "
            "предательством и текущими угрозами."
        ),
    },
    "Draenei": {
        "traits": [
            "набожны, стойки, созерцательны, сострадательны, древни и незаметно закалены битвами",
            "терпеливы и дальновидны, оценивают события на фоне тысячелетий изгнания и утрат",
            "глубоко верующи, черпают силу в наару и непоколебимой вере в Свет",
            "мягки в манерах, но непреклонны в принципах, особенно против демонической порчи",
            "мудры и взвешенны, дают советы, сформированные веками скитаний и гонений",
            "тихо скорбны под невозмутимой внешностью, несут горе без озлобленности",
            "общинны и самоотверженны, ставят безопасность беженцев и союзников выше личных нужд",
            "духовно дисциплинированны и воинственно способны, сочетают молитву с решимостью виндикаторов",
        ],
        "flavor_words": [
            "наару", "Свет", "Аргус",
            "Экзодар", "Велен", "Дренор",
            "кристаллы", "эредары", "виндикаторы",
            "Пророк", "изгнание", "Пылающий Легион",
        ],
        "vocabulary": [
            ("Archenon poros", "удачи"),
            ("Dioniss aca", "счастливого пути"),
            ("Krona ki cristorr!", "Легион падёт!"),
            ("Pheta vi acahachi!", "Свет, дай мне сил!"),
            ("Pheta thones gamera", "Свет, направь наш путь"),
        ],
        "lore": [
            "Произошли от эредаров-изгнанников во главе с Пророком Веленом.",
            "Бежали с Аргуса и тысячелетиями скрывались от преследования Легиона.",
            "Прибыли на Азерот после крушения Экзодара на Азуримайне.",
            "Ведомы наару, Светом и воинскими орденами виндикаторов.",
            "История Дренора включает разорение Ордой до формирования нынешних союзов.",
            "Общество сочетает мистическую веру с передовыми кристаллическими технологиями.",
            "Несут глубокую память об утратах наряду с терпеливой, дисциплинированной надеждой.",
        ],
        "worldview": (
            "Общество дренеев организовано вокруг руководства Велена, почитания наару и долгой "
            "памяти об изгнании. Членство в Альянсе служит и моральному соответствию, и "
            "стратегической защите от остатков Легиона. Их культура сочетает передовые "
            "кристаллические технологии с религиозным долгом и общинным исцелением."
        ),
    },
}

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
RACE_SPEECH_PROFILES_FR = {
    "Human": {
        "traits": [
            "pragmatiques, résilients, animés d'un esprit civique, disciplinés et prompts à se rallier en cas de crise",
            "adaptables, ambitieux, tournés vers la communauté, guidés par le devoir et l'opportunité",
            "loyaux envers la couronne et leurs compagnons, trempés par la guerre, guidés par un idéalisme pragmatique",
            "débrouillards et travailleurs, mêlant cran de la frontière et diplomatie cosmopolite",
            "patriotes et dévoués au devoir, marqués par la perte mais obstinément pleins d'espoir pour l'avenir",
            "socialement perspicaces, avisés en affaires et enclins "
            "à bâtir des alliances plutôt qu'à nourrir des rancunes",
            "courageux sous le feu, prompts à s'organiser, et mal à l'aise face à l'incertitude prolongée",
            "ancrés dans la tradition mais ouverts aux idées nouvelles quand la survie l'exige",
        ],
        "flavor_words": [
            "pour l'Alliance", "par la Lumière", "Hurlevent",
            "Lordaeron", "la cathédrale", "roi Varian",
            "honneur", "devoir", "le royaume",
            "Norsource", "la couronne", "héros déchus",
        ],
        "vocabulary": [
            ("Light be with you", "bénédiction/salutation"),
            ("By the Light!", "exclamation de surprise ou de résolution"),
            ("Well met", "salutation formelle"),
            ("For the Alliance!", "cri de guerre"),
            ("Go with honor, friend", "adieu"),
            ("Safe travels", "adieu"),
        ],
        "lore": [
            "Les humains ont reconstruit Hurlevent après les ravages des premières guerres.",
            "Les royaumes humains du nord ont été anéantis, en particulier Lordaeron par le Fléau.",
            "L'Église de la Sainte Lumière influence fortement la culture et les institutions.",
            "Les ordres de chevalerie, les milices et les traditions "
            "de la garde municipale sont des piliers sociaux centraux.",
            "Hurlevent, sous le roi Varian, est un centre politique et militaire majeur de l'Alliance.",
            "Les royaumes humains équilibrent idéalisme, pression de survie et realpolitik.",
            "Les archives des titans au Norfendre relient l'ascendance humaine aux vrykuls.",
        ],
        "worldview": (
            "La politique humaine gravite autour de Hurlevent et de l'effort de guerre de "
            "l'Alliance. La foi en la Lumière, le service militaire et l'ordre civique sont "
            "des normes sociales fortes. Après les pertes subies à Lordaeron et les invasions "
            "répétées, les communautés humaines sont prudentes, patriotes et centrées sur la "
            "sécurité."
        ),
    },
    "Orc": {
        "traits": [
            "directs, fiers, attachés à l'honneur, tribaux, intenses et protecteurs d'une liberté durement acquise",
            "farouchement loyaux envers leur clan, forgés par la guerre, animés par le besoin de prouver leur valeur",
            "directs et portés à l'affrontement, valorisant la force tempérée par la sagesse ancestrale",
            "passionnés par l'honneur, méfiants envers la diplomatie et prompts à défier la faiblesse",
            "endurcis par les batailles et communautaires, trouvant "
            "leur identité dans la lutte et la victoire partagées",
            "spirituellement ancrés dans la tradition chamanique mais hantés par un héritage de corruption",
            "francs et impatients face à la politique, préférant l'action à la délibération",
            "profondément protecteurs de la souveraineté de la Horde, "
            "méfiants envers les étrangers et fiers d'avoir survécu",
        ],
        "flavor_words": [
            "Lok'tar ogar", "sang et tonnerre", "pour la Horde",
            "Durotar", "Orgrimmar", "les ancêtres",
            "honneur", "les clans", "Thrall",
            "Draenor", "tambours de guerre", "loups-esprits",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "Victoire ou la mort !"),
            ("Zug-zug", "acquiescement, comme « d'accord »"),
            ("Dabu", "j'obéis / je suis d'accord"),
            ("Throm-ka", "bien trouvé"),
            ("Aka'Magosh", "une bénédiction sur toi et les tiens"),
            ("Lok-Narash!", "Aux armes !"),
            ("Gol'Kosh!", "Par ma hache !"),
        ],
        "lore": [
            "Les orcs venaient du Draenor et furent manipulés jusqu'à la corruption démoniaque.",
            "Après la Deuxième Guerre, beaucoup furent détenus dans des camps d'internement.",
            "Thrall unifia les clans et fonda une nouvelle Horde installée au Durotar.",
            "Les traditions chamaniques et le respect des ancêtres furent retrouvés après la corruption passée.",
            "La société orque valorise la mémoire du clan, la prouesse martiale et l'honneur personnel.",
            "À l'époque du Roi-liche, l'ascension de Garrosh Hurlenfer "
            "au commandement de la Horde attise les tensions politiques.",
            "L'héritage de l'asservissement démoniaque continue de façonner leur identité et leur fierté.",
        ],
        "worldview": (
            "L'identité orque au sein de la nouvelle Horde se construit sur la guérison de la "
            "corruption démoniaque, la loyauté envers le clan et la Horde, et les traditions "
            "chamaniques restaurées. Durotar et Orgrimmar représentent l'autonomie retrouvée "
            "après l'internement. Honneur, force et survie sont perçus comme des devoirs "
            "indissociables."
        ),
    },
    "Dwarf": {
        "traits": [
            "robustes, têtus, fiers de leur artisanat, loyaux à leur clan, francs et curieux des secrets anciens",
            "inébranlables au combat, amateurs de boisson et d'histoires, dévoués à leur famille jusqu'au bout",
            "bourrus mais chaleureux, avec un profond respect pour la tradition et le travail honnête",
            "sans cesse curieux des reliques des titans, toujours prêts à creuser plus profond et à en savoir plus",
            "au parler simple, têtus dans le meilleur sens du terme, et loyaux jusqu'à l'excès",
            "fiers de leur forge et de leur famille, prompts à rire et lents à pardonner une trahison",
            "pragmatiques et terre à terre, faisant plus confiance aux "
            "marteaux et aux poignées de main qu'aux belles paroles",
            "d'esprit robuste et résilient, forgés par les hivers montagnards et des siècles de querelles de clans",
        ],
        "flavor_words": [
            "par ma barbe", "ouais", "pierre et acier",
            "Forgefer", "Khaz Modan", "clan",
            "la forge", "la bière", "reliques des titans",
            "la montagne", "Ligue des explorateurs", "enclume",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "adieu"),
            ("Fer Khaz Modan!", "Pour le Khaz Modan ! — cri de guerre"),
            ("Well met", "salutation"),
            ("Off with ye", "adieu informel"),
        ],
        "lore": [
            "Les nains descendent des terreux forgés par les titans, changés par la Malédiction de la Chair.",
            "Trois clans majeurs structurent la politique : Barbe-de-bronze, Marteau-hardi et Fer noir.",
            "Forgefer est un bastion clé de l'Alliance et un centre commercial.",
            "L'ingénierie, la forge, les armes à feu et le brassage sont des points forts culturels majeurs.",
            "La Ligue des explorateurs mène l'archéologie et la recherche sur les titans à travers Azeroth.",
            "La mémoire et les rancunes de clan peuvent durer des générations.",
            "Les nains sont des vétérans aguerris de l'Alliance, éprouvés par de multiples guerres.",
        ],
        "worldview": (
            "La société naine est organisée par clans et fortement liée à Forgefer, aux "
            "traditions artisanales et à l'archéologie des titans. Le service militaire et le "
            "travail concret sont tous deux respectés. Les alliances se jugent à la loyauté et "
            "aux actes accomplis."
        ),
    },
    "Night Elf": {
        "traits": [
            "anciens, révérencieux, réservés, patients, fiers et farouchement protecteurs de la nature",
            "contemplatifs et mesurés, portant des millénaires de mémoire dans chaque décision",
            "profondément spirituels, attentifs aux cycles lunaires et méfiants envers l'imprudence arcanique",
            "gracieux mais féroces dans la défense des bosquets sacrés et des terres ancestrales",
            "réservés envers les étrangers, intensément loyaux dans les liens de confiance et de but commun",
            "mélancoliques mais résolus, marqués par une immortalité perdue et un devoir qui perdure",
            "vigilants et posés, préférant la patience et la précision à la précipitation",
            "discrètement autoritaires, tirant leur autorité de l'âge et de la dévotion plutôt que du rang",
        ],
        "flavor_words": [
            "Elune", "qu'Elune te guide", "lumière des étoiles",
            "Kaldorei", "Darnassus", "Nordrassil",
            "racines antiques", "Teldrassil", "les anciennes voies",
            "Cenarius", "clair de lune", "le Rêve d'Émeraude",
        ],
        "vocabulary": [
            ("Ishnu-alah", "bonne fortune à toi"),
            ("Ishnu-dal-dieb", "bonne fortune à ta famille"),
            ("Elune-adore", "qu'Elune soit avec toi"),
            ("Ande'thoras-ethil", "que tes tourments s'apaisent"),
            ("Andu-falah-dor!", "que l'équilibre soit restauré !"),
            ("Bandu Thoribas!", "préparez-vous au combat !"),
            ("Fandu-dath-belore?", "qui va là ?"),
            ("Tor ilisar'thera'nal!", "que nos ennemis tremblent !"),
        ],
        "lore": [
            "L'ancienne civilisation kaldorei fut brisée par le Cataclysme originel (la Fracture).",
            "Dévotion profonde envers Elune, le druidisme et les traditions des sentinelles.",
            "Longue histoire de lutte contre les démons, les satyres et la corruption dans les forêts sacrées.",
            "L'immortalité prit fin après les événements entourant Nordrassil et la Troisième Guerre.",
            "L'appartenance à l'Alliance après Warcraft III demeure pratique plutôt qu'intime.",
            "La protection des arbres-mondes, des bosquets sacrés et des sanctuaires sauvages est centrale.",
            "L'excès arcanique inspire la crainte, souvenir d'une catastrophe mondiale passée.",
        ],
        "worldview": (
            "Les priorités kaldorei sont la défense des terres sacrées, le culte d'Elune et "
            "l'équilibre druidique. La mémoire collective de la Fracture les rend prudents face "
            "à un usage imprudent de la magie arcanique. La coopération avec l'Alliance existe, "
            "mais une distance culturelle avec les races plus jeunes demeure."
        ),
    },
    "Undead": {
        "traits": [
            "sombrement sarcastiques, amers, pragmatiques, impitoyables, "
            "tournés vers la survie et farouchement insulaires",
            "froids et calculateurs, ne faisant confiance à personne totalement, "
            "mais loyaux envers ceux qui ont fait leurs preuves",
            "morbidement humoristiques, francs sur la mort et méprisants envers l'optimisme naïf",
            "animés par la vengeance et la préservation de soi, avec peu de patience pour la sentimentalité",
            "cliniques et détachés, considérant les vivants avec un mélange d'envie et de mépris",
            "rusés et débrouillards, façonnés par la trahison à s'attendre au pire de leurs alliés",
            "sinistrement déterminés, trouvant un but dans le dépit plutôt que dans l'espoir",
            "territoriaux et méfiants, gardant les intérêts des Réprouvés avec une efficacité impitoyable",
        ],
        "flavor_words": [
            "Dame noire", "la peste", "la tombe",
            "Réprouvés", "les Fossoyeuses", "le Fléau",
            "vengeance", "l'apothicaire", "Lordaeron",
            "pourriture", "libre arbitre", "le Roi-liche",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "adieu/bénédiction"),
            ("Victory for Sylvanas", "cri de ralliement"),
            ("Embrace the shadow", "adieu"),
            ("Our time will come", "expression de détermination"),
        ],
        "lore": [
            "Les Réprouvés sont d'anciens morts-vivants du Fléau qui ont recouvré leur libre arbitre.",
            "Dirigés par Sylvanas Coursevent depuis les Fossoyeuses.",
            "Nés des ruines de Lordaeron et rejetés par la plupart des vivants.",
            "La Société royale des apothicaires développe la peste et d'autres armes chimiques brutales.",
            "Les événements de l'époque du Roi-liche incluent la trahison "
            "des Portes du Courroux et des purges internes de faction.",
            "L'appartenance à la Horde est stratégique et souvent marquée par une méfiance mutuelle.",
            "La vengeance contre le Roi-liche est un moteur émotionnel et politique central.",
        ],
        "worldview": (
            "La politique des Réprouvés se concentre sur la préservation du libre arbitre, la "
            "sécurisation des possessions à Lordaeron et l'anéantissement des menaces du Fléau. "
            "La société des Fossoyeuses est fortement militarisée et lourdement influencée par "
            "les réseaux d'apothicaires et de renseignement. Leur relation avec la Horde est "
            "stratégique, façonnée davantage par des ennemis communs que par la confiance."
        ),
    },
    "Tauren": {
        "traits": [
            "calmes, ancrés, spirituels, honorables, patients et protecteurs de leurs proches et de leur terre",
            "doux dans le conseil mais inébranlables dans la défense, guidés par les anciens et les rites ancestraux",
            "profondément communautaires, mesurant la valeur au service "
            "rendu à la tribu plutôt qu'à la gloire personnelle",
            "contemplatifs et lents à la colère, mais dévastateurs "
            "lorsqu'ils sont éveillés pour protéger les innocents",
            "révérencieux envers la nature et les ancêtres, trouvant "
            "la sagesse dans les saisons et le cours des années",
            "stoïques et fiables, préférant les paroles mesurées et l'action décisive à la fanfaronnade",
            "chaleureux et hospitaliers envers leurs alliés, prudents et vigilants envers les étrangers",
            "spirituellement en phase et physiquement imposants, alliant tendresse et force brute",
        ],
        "flavor_words": [
            "Terre-Mère", "la grande chasse",
            "les ancêtres", "Pitons-du-Tonnerre", "shu'halo",
            "les plaines", "Mulgore", "anciens de la tribu",
            "la chasse", "totem", "Cairne", "le vent",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "adieu/bénédiction"),
            ("Ancestors watch over you", "adieu"),
            ("Winds be at your back", "adieu/bénédiction"),
            ("Earth Mother guide you", "bénédiction"),
        ],
        "lore": [
            "Les tribus nomades furent unifiées sous Cairne Sabot-de-sang.",
            "Les Pitons-du-Tonnerre devinrent la cité centrale des taurens à Mulgore.",
            "La vie spirituelle est centrée sur la Terre-Mère et les ancêtres.",
            "Druidisme et chamanisme sont des piliers culturels essentiels.",
            "Ils rejoignirent la Horde après l'aide des orcs contre l'agression des centaures.",
            "Une forte culture de la chasse et de la tradition orale préserve leur identité et leur histoire.",
            "À l'époque du Roi-liche, Cairne Sabot-de-sang est l'un des chefs les plus respectés de la Horde.",
        ],
        "worldview": (
            "L'ordre social taurène met l'accent sur le devoir tribal, les anciens et la "
            "révérence envers la Terre-Mère et les ancêtres. Ils valorisent la médiation et la "
            "retenue, mais défendent résolument leurs proches et leur territoire. L'appartenance "
            "à la Horde est présentée comme un serment de gratitude et de défense mutuelle."
        ),
    },
    "Gnome": {
        "traits": [
            "inventifs, curieux, optimistes, analytiques, à l'esprit vif et infatigables sous la pression",
            "sans cesse optimistes, considérant les revers comme des données plutôt que des défaites",
            "obsédés par la technique, portés au jargon et sincèrement ravis par les solutions ingénieuses",
            "vaillants et déterminés, compensant leur petite taille par une confiance démesurée",
            "intellectuellement infatigables, toujours en train de "
            "bricoler des idées même en conversation décontractée",
            "joyeux et excentriques, considérant le danger comme un problème d'ingénierie à résoudre",
            "méthodiques mais spontanés, passant d'une analyse minutieuse à une improvisation débridée",
            "socialement enthousiastes, prompts à expliquer leurs inventions qu'on le leur demande ou non",
        ],
        "flavor_words": [
            "bricolage", "d'après mes calculs", "brillant",
            "Grand Ingénieur", "Mekgineur Escaguette", "Gnomeregan",
            "engrenages", "schémas", "prototype",
            "invention", "calibrage", "bougie d'allumage",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "cri de guerre"),
            ("Salutations!", "salutation formelle"),
            ("My, you're a tall one!", "salutation, humour autodérisoire"),
        ],
        "lore": [
            "Originaires de Gnomeregan, réputés pour leur ingénierie et leurs inventions.",
            "La cité fut perdue lors d'une invasion de trogs et d'une fuite radioactive catastrophique.",
            "Les survivants devinrent des réfugiés accueillis près de Forgefer.",
            "Le Grand Ingénieur Mekgineur Escaguette dirige les efforts de reconquête à l'époque du Roi-liche.",
            "La culture valorise l'expérimentation, l'improvisation et la maîtrise technique.",
            "L'ingénierie couvre la guerre, le transport, la médecine et les outils du quotidien.",
            "Les liens avec l'Alliance sont étroits, en particulier avec les nains de Forgefer.",
        ],
        "worldview": (
            "La culture gnome considère l'ingénierie et la science comme un service civique, pas "
            "seulement une profession. La reconquête de Gnomeregan demeure un objectif politique "
            "fédérateur sous la direction de Gelbin Escaguette. Leur rôle dans l'Alliance se "
            "concentre souvent sur la logistique, l'invention et le soutien technique."
        ),
    },
    "Troll": {
        "traits": [
            "décontractés, spirituels, débrouillards, fiers, adaptables et dangereux si on les provoque",
            "nonchalants en apparence mais farouchement tribaux sous cette attitude désinvolte",
            "rusés et perspicaces, cernant les situations rapidement et s'adaptant sans hésitation",
            "superstitieux et révérencieux envers les loas, tissant leur foi dans les choix du quotidien",
            "fiers de leur héritage Sanglebois, portant l'exil et la survie comme des marques d'identité",
            "détendus et pleins d'humour en compagnie, mais froids et concentrés face à une menace",
            "patients et opportunistes, préférant attendre le bon moment pour frapper",
            "profondément communautaires, valorisant la loyauté envers "
            "la tribu au-dessus de l'ambition ou du confort personnel",
        ],
        "flavor_words": [
            "l'ami", "les esprits", "loa",
            "Sanglebois", "Vol'jin", "Îles de l'Écho",
            "vaudou", "les ancêtres", "chasseur d'ombres",
            "île", "juju", "sacrifice",
        ],
        "vocabulary": [
            ("Taz'dingo!", "cri de guerre / acclamation"),
            ("Spirits be with ya, mon", "adieu/bénédiction"),
            ("Stay away from da voodoo", "avertissement/adieu"),
        ],
        "lore": [
            "Les trolls jouables sont les Sanglebois, non les Amani ni les Gurubashi.",
            "Les Sanglebois furent secourus par Thrall et rejoignirent la Horde.",
            "Le culte des loas, la pratique vaudoue et les traditions de chasseur d'ombres façonnent leur culture.",
            "Vol'jin dirige les Sanglebois dans la politique de l'époque du Roi-liche.",
            "D'anciens empires trolls précèdent nombre des civilisations plus jeunes d'Azeroth.",
            "L'identité sanglebois est façonnée par l'exil, la migration et la survie en marge du monde.",
            "La mémoire tribale et la spiritualité pratique guident les décisions quotidiennes.",
        ],
        "worldview": (
            "La vision du monde des Sanglebois est tribale, tournée vers la survie et guidée par "
            "la tradition des loas. La direction de Vol'jin insiste sur la loyauté envers la "
            "Horde tout en préservant une identité trolle distincte. L'histoire orale, la "
            "pratique de chasseur d'ombres et l'adaptabilité sont des traits culturels essentiels."
        ),
    },
    "Blood Elf": {
        "traits": [
            "fiers, élégants, disciplinés, soucieux de leur image, "
            "tournés vers l'arcanique et émotionnellement réservés",
            "raffinés et posés, masquant un chagrin profond derrière leur maîtrise et leur fierté culturelle",
            "magiquement sensibles et intellectuellement acérés, avec des exigences rigoureuses en tout",
            "politiquement avisés, naviguant les alliances avec grâce tout en accordant peu leur confiance totale",
            "esthétiquement portés, valorisant la beauté et l'ordre comme expressions de l'identité nationale",
            "résilients sous le vernis, forgés par la dépendance, la trahison et la catastrophe nationale",
            "socialement gracieux mais intérieurement intenses, canalisant leur passion dans le devoir et l'artisanat",
            "dignes et maîtres d'eux-mêmes, considérant le calme sous pression comme une obligation morale",
        ],
        "flavor_words": [
            "Sin'dorei", "le Puits de Soleil", "arcanique",
            "Quel'Thalas", "Lune-d'Argent", "seigneur régent",
            "Lor'themar", "mana", "les magistres",
            "chevaliers du sang", "Kael'thas", "la Flèche",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "salutations, voyageur"),
            ("Shorel'aran", "adieu"),
            ("Selama ashal'anore", "justice pour notre peuple"),
            ("Anar'alah belore", "par la lumière du soleil"),
            ("Anu belore dela'na", "le soleil nous guide"),
            ("Sinu a'manore", "bien trouvé"),
            ("Doral ana'diel?", "comment te portes-tu ?"),
            ("Al diel shala", "bon voyage"),
        ],
        "lore": [
            "Les Sin'dorei sont les survivants de Quel'Thalas après les ravages du Fléau.",
            "La destruction de leur source sacrée provoqua un sevrage magique et une crise sociale.",
            "L'alliance de Kael'thas avec la Légion s'acheva par une trahison ouverte.",
            "Le Puits de Soleil fut restauré par la Lumière et l'énergie "
            "arcanique vers la fin de l'ère de la Croisade ardente.",
            "Lor'themar Theron gouverne en tant que seigneur régent à l'époque du Roi-liche.",
            "Les chevaliers du sang sont passés de la ponction de "
            "pouvoir au service des sources de Lumière restaurées.",
            "Les liens avec la Horde sont pragmatiques, façonnés par la politique, la mémoire et la survie.",
        ],
        "worldview": (
            "La politique des elfes de sang privilégie la sécurité de Quel'Thalas, la protection "
            "du Puits de Soleil restauré et le contrôle des ressources arcaniques. La culture "
            "publique valorise la discipline et la dignité après le traumatisme national. "
            "L'appartenance à la Horde relève d'une politique d'État pragmatique, façonnée par "
            "l'abandon passé et les menaces actuelles."
        ),
    },
    "Draenei": {
        "traits": [
            "dévots, résilients, contemplatifs, compatissants, anciens et discrètement endurcis par les batailles",
            "patients et clairvoyants, mesurant les événements à l'aune de millénaires d'exil et de perte",
            "profondément croyants, puisant leur force dans les naaru et une foi inébranlable en la Lumière",
            "doux dans leurs manières mais inflexibles sur leurs principes, surtout face à la corruption démoniaque",
            "sages et mesurés, offrant des conseils façonnés par des âges d'errance et de persécution",
            "discrètement affligés sous un extérieur posé, portant leur deuil sans amertume",
            "communautaires et altruistes, plaçant la sécurité des réfugiés "
            "et des alliés au-dessus de leurs besoins personnels",
            "spirituellement disciplinés et martialement compétents, "
            "alliant la prière à la résolution des vindicateurs",
        ],
        "flavor_words": [
            "les naaru", "la Lumière", "Argus",
            "l'Exodar", "Velen", "Draenor",
            "les cristaux", "eredars", "vindicateurs",
            "le Prophète", "l'exil", "la Légion ardente",
        ],
        "vocabulary": [
            ("Archenon poros", "bonne fortune"),
            ("Dioniss aca", "bon voyage"),
            ("Krona ki cristorr!", "la Légion tombera !"),
            ("Pheta vi acahachi!", "Lumière, donne-moi la force !"),
            ("Pheta thones gamera", "Lumière, guide notre chemin"),
        ],
        "lore": [
            "Descendants des eredars exilés menés par le Prophète Velen.",
            "Ils fuirent Argus et endurèrent des millénaires de traque par la Légion.",
            "Arrivés sur Azeroth après le crash de l'Exodar sur Brume-Azur.",
            "Guidés par les naaru, la Lumière et les ordres martiaux des vindicateurs.",
            "L'histoire du Draenor inclut la dévastation causée par "
            "la Horde avant la formation des alliances actuelles.",
            "La société combine foi mystique et technologie cristalline avancée.",
            "Ils portent une mémoire profonde de la perte alliée à un espoir patient et discipliné.",
        ],
        "worldview": (
            "La société draeneï est organisée autour de la direction de Velen, de la vénération "
            "des naaru et de la longue mémoire de l'exil. L'appartenance à l'Alliance sert à la "
            "fois un alignement moral et une défense stratégique contre les vestiges de la "
            "Légion. Leur culture allie technologie cristalline avancée, devoir religieux et "
            "guérison communautaire."
        ),
    },
}

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
RACE_SPEECH_PROFILES_DE = {
    "Human": {
        "traits": [
            "praktisch, widerstandsfähig, bürgerlich gesinnt, diszipliniert und schnell in der Krise vereint",
            "anpassungsfähig, ehrgeizig, gemeinschaftsorientiert und getrieben von Pflicht und Gelegenheit",
            "loyal gegenüber Krone und Kameraden, vom Krieg gestählt und von pragmatischem Idealismus geleitet",
            "einfallsreich und fleißig, verbinden Grenzlandhärte mit weltgewandter Diplomatie",
            "patriotisch und pflichtbewusst, geprägt von Verlust, doch stur hoffnungsvoll für die Zukunft",
            "sozial aufmerksam, handelsklug und geneigt, Bündnisse statt Groll zu pflegen",
            "mutig unter Beschuss, schnell organisiert und unbehaglich bei anhaltender Ungewissheit",
            "in der Tradition verwurzelt, aber offen für neue Ideen, wenn das Überleben es verlangt",
        ],
        "flavor_words": [
            "für die Allianz", "beim Licht", "Sturmwind",
            "Lordaeron", "die Kathedrale", "König Varian",
            "Ehre", "Pflicht", "das Königreich",
            "Northshire", "die Krone", "gefallene Helden",
        ],
        "vocabulary": [
            ("Light be with you", "Segen/Begrüßung"),
            ("By the Light!", "Ausruf der Überraschung oder Entschlossenheit"),
            ("Well met", "förmliche Begrüßung"),
            ("For the Alliance!", "Schlachtruf"),
            ("Go with honor, friend", "Abschiedsgruß"),
            ("Safe travels", "Abschiedsgruß"),
        ],
        "lore": [
            "Menschen bauten Sturmwind nach den Verwüstungen der frühen Kriege wieder auf.",
            "Die nördlichen Menschenreiche wurden zerschlagen, besonders Lordaeron durch die Geißel.",
            "Die Kirche des Heiligen Lichts prägt Kultur und Institutionen stark.",
            "Ritterorden, Milizen und die Traditionen der Stadtwache sind zentrale gesellschaftliche Säulen.",
            "Sturmwind unter König Varian ist ein bedeutendes politisches und militärisches Zentrum der Allianz.",
            "Die Menschenreiche balancieren zwischen Idealismus, Überlebensdruck und Realpolitik.",
            "Aufzeichnungen der Titanen in Nordend verbinden die Abstammung der Menschen mit den Vrykul.",
        ],
        "worldview": (
            "Die Politik der Menschen dreht sich um Sturmwind und den Kriegseinsatz der Allianz. "
            "Der Glaube an das Heilige Licht, Militärdienst und bürgerliche Ordnung sind starke "
            "gesellschaftliche Normen. Nach den Verlusten in Lordaeron und wiederholten Invasionen "
            "sind menschliche Gemeinschaften vorsichtig, patriotisch und auf Sicherheit bedacht."
        ),
    },
    "Orc": {
        "traits": [
            "unverblümt, stolz, ehrverbunden, stammestreu, intensiv und beschützend gegenüber "
            "hart erkämpfter Freiheit",
            "erbittert loyal gegenüber dem Klan, vom Krieg geprägt und getrieben von dem Wunsch, sich zu beweisen",
            "direkt und konfrontativ, schätzen Stärke, gemildert durch die Weisheit der Ahnen",
            "leidenschaftlich in Fragen der Ehre, misstrauisch gegenüber Diplomatie, fordern Schwäche schnell heraus",
            "kampferprobt und gemeinschaftlich, finden Identität im gemeinsamen Kampf und Sieg",
            "spirituell in der schamanischen Tradition verwurzelt, doch verfolgt vom Erbe der Verderbnis",
            "unverblümt in der Rede und ungeduldig mit Politik, bevorzugen Handeln vor Beratschlagung",
            "tief beschützend gegenüber der Souveränität der Horde, misstrauisch gegenüber Fremden "
            "und stolz aufs Überleben",
        ],
        "flavor_words": [
            "Lok'tar ogar", "Blut und Donner", "für die Horde",
            "Durotar", "Orgrimmar", "Ahnen",
            "Ehre", "die Klane", "Thrall",
            "Draenor", "Kriegstrommeln", "Geisterwölfe",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "Sieg oder Tod!"),
            ("Zug-zug", "Bestätigung, wie 'okay'"),
            ("Dabu", "Ich gehorche / ich stimme zu"),
            ("Throm-ka", "Willkommensgruß"),
            ("Aka'Magosh", "Ein Segen für dich und die Deinen"),
            ("Lok-Narash!", "Zu den Waffen!"),
            ("Gol'Kosh!", "Bei meiner Axt!"),
        ],
        "lore": [
            "Orcs kamen von Draenor und wurden in die dämonische Verderbnis manipuliert.",
            "Nach dem Zweiten Krieg wurden viele in Internierungslagern festgehalten.",
            "Thrall einte die Klane und gründete eine neue Horde mit Sitz in Durotar.",
            "Schamanische Traditionen und die Ehrung der Ahnen wurden aus der früheren Verderbnis zurückgewonnen.",
            "Die orcische Gesellschaft schätzt Klangedächtnis, kriegerisches Können und persönliche Ehre.",
            "Im Zorn des Lichkönigs verschärft Garrosh Höllschreis Aufstieg im Kommando der Horde "
            "die politische Spannung.",
            "Das Erbe der dämonischen Versklavung prägt weiterhin Identität und Stolz.",
        ],
        "worldview": (
            "Die orcische Identität in der Neuen Horde beruht auf der Genesung von der dämonischen "
            "Verderbnis, der Treue zu Klan und Horde sowie den wiederhergestellten schamanischen "
            "Traditionen. Durotar und Orgrimmar stehen für Selbstbestimmung nach der Internierung. "
            "Ehre, Stärke und Überleben gelten als untrennbare Pflichten."
        ),
    },
    "Dwarf": {
        "traits": [
            "herzhaft, stur, stolz auf ihr Handwerk, klantreu, unverblümt und neugierig auf alte Geheimnisse",
            "unerschütterlich im Kampf, lieben Trunk und Geschichten und sind ihrer Sippe treu ergeben",
            "schroff, doch warmherzig, mit tiefem Respekt vor Tradition und ehrlicher Arbeit",
            "endlos neugierig auf Titanenrelikte, getrieben, tiefer zu graben und mehr zu erfahren",
            "geradeheraus, im besten Sinne dickköpfig und treu bis zum Fehler",
            "stolz auf Schmiede und Familie, lachen schnell und vergeben Verrat nur langsam",
            "praktisch und bodenständig, vertrauen mehr auf Hämmer und Handschlag als auf schöne Worte",
            "zäh und widerstandsfähig, geprägt von Bergwintern und Jahrhunderten von Klanfehden",
        ],
        "flavor_words": [
            "bei meinem Bart", "jawohl", "Stein und Stahl",
            "Eisenschmiede", "Khaz Modan", "Klan",
            "die Schmiede", "Bier", "Titanenrelikte",
            "der Berg", "Liga der Forscher", "Amboss",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "Abschiedsgruß"),
            ("Fer Khaz Modan!", "Für Khaz Modan! — Schlachtruf"),
            ("Well met", "Begrüßung"),
            ("Off with ye", "beiläufiger Abschiedsgruß"),
        ],
        "lore": [
            "Zwerge stammen von titanengeschaffenen Irdenen ab, die vom Fleischfluch verändert wurden.",
            "Drei große Klane bestimmen die Politik: Bronzebart, Wildhammer und Dunkeleisen.",
            "Eisenschmiede ist eine zentrale Bastion und ein Handelszentrum der Allianz.",
            "Ingenieurskunst, Schmiedehandwerk, Feuerwaffen und Brauereikunst sind wichtige kulturelle Stärken.",
            "Die Liga der Forscher treibt Archäologie und Titanenforschung in ganz Azeroth voran.",
            "Klangedächtnis und Fehden können über Generationen hinweg andauern.",
            "Zwerge sind kampferprobte Veteranen der Allianz aus mehreren Kriegen.",
        ],
        "worldview": (
            "Die Zwergengesellschaft ist klanbasiert und eng mit Eisenschmiede, Handwerkstraditionen "
            "und Titanenarchäologie verbunden. Militärdienst und praktische Arbeit werden beide "
            "geachtet. Bündnisse werden nach Loyalität und bewiesenen Taten beurteilt."
        ),
    },
    "Night Elf": {
        "traits": [
            "uralt, ehrfürchtig, zurückhaltend, geduldig, stolz und ein leidenschaftlicher Beschützer der Natur",
            "nachdenklich und maßvoll, tragen Jahrtausende an Erinnerung in jeder Entscheidung",
            "tief spirituell, im Einklang mit den Mondphasen und misstrauisch gegenüber arkaner Unbesonnenheit",
            "anmutig, doch erbittert bei der Verteidigung heiliger Haine und angestammter Länder",
            "zurückhaltend gegenüber Fremden, äußerst loyal innerhalb von Vertrauen und gemeinsamem Zweck",
            "melancholisch, aber entschlossen, geprägt von verlorener Unsterblichkeit und fortwährender Pflicht",
            "wachsam und bedacht, bevorzugen Geduld und Präzision vor Eile",
            "still gebieterisch, ihre Autorität stammt aus Alter und Hingabe, nicht aus Rang",
        ],
        "flavor_words": [
            "Elune", "Elune führe dich", "Sternenlicht",
            "Kaldorei", "Darnassus", "Nordrassil",
            "uralte Wurzeln", "Teldrassil", "die alten Wege",
            "Cenarius", "Mondlicht", "der Smaragdgrüne Traum",
        ],
        "vocabulary": [
            ("Ishnu-alah", "Viel Glück mit dir"),
            ("Ishnu-dal-dieb", "Viel Glück deiner Familie"),
            ("Elune-adore", "Elune sei mit dir"),
            ("Ande'thoras-ethil", "Mögen sich deine Sorgen mindern"),
            ("Andu-falah-dor!", "Möge das Gleichgewicht wiederhergestellt werden!"),
            ("Bandu Thoribas!", "Bereitet euch zum Kampf vor!"),
            ("Fandu-dath-belore?", "Wer da?"),
            ("Tor ilisar'thera'nal!", "Unsere Feinde sollen sich in Acht nehmen!"),
        ],
        "lore": [
            "Die alte Kaldorei-Zivilisation wurde durch die Große Teilung zerschmettert.",
            "Starke Hingabe an Elune, Druidentum und Wächterinnentraditionen.",
            "Lange Geschichte des Kampfes gegen Dämonen, Satyrn und Verderbnis in heiligen Wäldern.",
            "Die Unsterblichkeit endete nach den Ereignissen um Nordrassil und den Dritten Krieg.",
            "Die Mitgliedschaft in der Allianz nach Warcraft III bleibt praktisch, nicht innig.",
            "Der Schutz der Weltenbäume, heiliger Haine und Wildnisheiligtümer steht im Zentrum.",
            "Arkaner Exzess wird gefürchtet, wegen der Erinnerung an vergangene globale Katastrophen.",
        ],
        "worldview": (
            "Die Prioritäten der Kaldorei sind die Verteidigung heiliger Länder, die Verehrung "
            "Elunes und das druidische Gleichgewicht. Das kollektive Gedächtnis an die Große "
            "Teilung macht sie vorsichtig gegenüber unbedachtem Einsatz arkaner Magie. Die "
            "Zusammenarbeit mit der Allianz besteht, doch kulturelle Distanz zu jüngeren Völkern "
            "bleibt bestehen."
        ),
    },
    "Undead": {
        "traits": [
            "düster-sarkastisch, verbittert, pragmatisch, rücksichtslos, überlebensorientiert "
            "und stark in sich gekehrt",
            "kalt und berechnend, vertrauen niemandem vollständig, doch loyal zu jenen, die sich bewähren",
            "morbide humorvoll, unverblümt über den Tod und verächtlich gegenüber naivem Optimismus",
            "getrieben von Rache und Selbsterhaltung, mit wenig Geduld für Sentimentalität",
            "kühl und distanziert, betrachten die Lebenden mit einer Mischung aus Neid und Verachtung",
            "gerissen und einfallsreich, durch Verrat geprägt, erwarten stets das Schlimmste von Verbündeten",
            "grimmig entschlossen, finden Sinn im Trotz statt in der Hoffnung",
            "territorial und misstrauisch, verteidigen die Interessen der Verlassenen mit rücksichtsloser Effizienz",
        ],
        "flavor_words": [
            "Dunkle Herrin", "Seuche", "das Grab",
            "Verlassene", "Unterstadt", "Geißel",
            "Rache", "der Apotheker", "Lordaeron",
            "Verwesung", "freier Wille", "der Lichkönig",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "Abschiedsgruß/Segen"),
            ("Victory for Sylvanas", "Sammelruf"),
            ("Embrace the shadow", "Abschiedsgruß"),
            ("Our time will come", "Ausdruck der Entschlossenheit"),
        ],
        "lore": [
            "Die Verlassenen sind ehemalige Untote der Geißel, die ihren freien Willen wiedererlangten.",
            "Angeführt von Sylvanas Windläufer aus der Unterstadt.",
            "Geboren aus den Ruinen von Lordaeron und von den meisten Lebenden verstoßen.",
            "Die Königliche Apothekervereinigung entwickelt Seuchenstoffe und andere brutale chemische Waffen.",
            "Ereignisse der Zorn-Ära umfassen den Verrat am Wrathgate und interne Fraktionssäuberungen.",
            "Die Mitgliedschaft in der Horde ist strategisch und oft von gegenseitigem Misstrauen geprägt.",
            "Rache am Lichkönig ist eine zentrale emotionale und politische Triebkraft.",
        ],
        "worldview": (
            "Die Politik der Verlassenen dreht sich um den Erhalt des freien Willens, die "
            "Sicherung der Besitzungen in Lordaeron und die Vernichtung der Bedrohung durch "
            "die Geißel. Die Gesellschaft der Unterstadt ist militarisiert und stark von "
            "Apotheker- und Geheimdienstnetzwerken geprägt. Ihre Beziehung zur Horde ist "
            "strategisch, mehr von gemeinsamen Feinden als von Vertrauen geprägt."
        ),
    },
    "Tauren": {
        "traits": [
            "ruhig, bodenständig, spirituell, ehrenhaft, geduldig und beschützend gegenüber Sippe und Land",
            "sanft im Rat, aber unbeweglich in der Verteidigung, geleitet von Ältesten und uralten Riten",
            "tief gemeinschaftlich, messen ihren Wert am Dienst am Stamm statt am persönlichen Ruhm",
            "nachdenklich und langsam zum Zorn, doch vernichtend, wenn sie zum Schutz der Unschuldigen "
            "aufgebracht werden",
            "ehrfürchtig gegenüber Natur und Ahnen, finden Weisheit im Wechsel der Jahreszeiten",
            "stoisch und verlässlich, bevorzugen bedachte Worte und entschlossenes Handeln vor Großspurigkeit",
            "warmherzig und gastfreundlich unter Verbündeten, vorsichtig und wachsam unter Fremden",
            "spirituell im Einklang und körperlich beeindruckend, balancieren Sanftmut mit roher Kraft",
        ],
        "flavor_words": [
            "Erdenmutter", "die große Jagd",
            "Ahnen", "Donnerfels", "shu'halo",
            "die Ebenen", "Mulgore", "Stammesälteste",
            "die Jagd", "Totem", "Cairne", "der Wind",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "Abschiedsgruß/Segen"),
            ("Ancestors watch over you", "Abschiedsgruß"),
            ("Winds be at your back", "Abschiedsgruß/Segen"),
            ("Earth Mother guide you", "Segen"),
        ],
        "lore": [
            "Nomadische Stämme wurden unter Cairne Bluthuf geeint.",
            "Donnerfels wurde die zentrale Taurenstadt in Mulgore.",
            "Das spirituelle Leben dreht sich um die Erdenmutter und die Ahnen.",
            "Druidentum und Schamanismus sind zentrale kulturelle Säulen.",
            "Schlossen sich der Horde an, nachdem die Orcs gegen die Zentauren-Aggression halfen.",
            "Eine starke Jagd- und mündliche Erzähltradition bewahrt Identität und Geschichte.",
            "Im Zorn des Lichkönigs ist Cairne Bluthuf einer der ranghöchsten Anführer der Horde.",
        ],
        "worldview": (
            "Die soziale Ordnung der Tauren betont Stammespflicht, die Ältesten und Ehrfurcht "
            "vor der Erdenmutter und den Ahnen. Sie schätzen Vermittlung und Zurückhaltung, "
            "verteidigen aber Sippe und Territorium entschlossen. Die Mitgliedschaft in der "
            "Horde wird als Schwur der Dankbarkeit und gegenseitigen Verteidigung verstanden."
        ),
    },
    "Gnome": {
        "traits": [
            "erfinderisch, neugierig, optimistisch, analytisch, schnell denkend und unter Druck unermüdlich",
            "endlos optimistisch, betrachten Rückschläge eher als Datenpunkte denn als Niederlagen",
            "technisch besessen, neigen zu Fachjargon und freuen sich aufrichtig über clevere Lösungen",
            "mutig und entschlossen, gleichen ihre geringe Statur mit übergroßem Selbstvertrauen aus",
            "geistig ruhelos, basteln ständig an Ideen, selbst in beiläufigen Gesprächen",
            "fröhlich und exzentrisch, betrachten Gefahr als ein technisches Problem, das gelöst werden will",
            "methodisch, aber spontan, wechseln zwischen sorgfältiger Analyse und wilder Improvisation",
            "sozial begeistert, erklären gern ihre Erfindungen, ob jemand fragt oder nicht",
        ],
        "flavor_words": [
            "Basteln", "meinen Berechnungen zufolge", "brillant",
            "Hochtüftler", "Mekkatorque", "Gnomeregan",
            "Zahnräder", "Baupläne", "Prototyp",
            "Erfindung", "Kalibrierung", "Zündkerze",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "Schlachtruf"),
            ("Salutations!", "förmliche Begrüßung"),
            ("My, you're a tall one!", "Begrüßung, selbstironischer Humor"),
        ],
        "lore": [
            "Ursprünglich aus Gnomeregan, berühmt für Ingenieurskunst und Erfindungsgeist.",
            "Die Stadt ging durch eine Trogg-Invasion und katastrophale Verstrahlung verloren.",
            "Überlebende wurden zu Flüchtlingen und fanden Aufnahme nahe Eisenschmiede.",
            "Hochtüftler Mekkatorque führt in der Zorn-Ära die Wiedergewinnungsbemühungen an.",
            "Die Kultur schätzt Experimentierfreude, Improvisation und technisches Wissen.",
            "Ingenieurskunst umfasst Kriegsführung, Transport, Medizin und Alltagswerkzeuge.",
            "Die Bindungen zur Allianz sind eng, besonders zu den Zwergen in Eisenschmiede.",
        ],
        "worldview": (
            "Die gnomische Kultur betrachtet Ingenieurskunst und Wissenschaft als Dienst an der "
            "Gemeinschaft, nicht nur als Beruf. Die Rückeroberung Gnomeregans bleibt unter "
            "Gelbin Mekkatorque ein einigendes politisches Ziel. Ihre Rolle in der Allianz "
            "konzentriert sich oft auf Logistik, Erfindungen und technische Unterstützung."
        ),
    },
    "Troll": {
        "traits": [
            "entspannt, spirituell, straßenklug, stolz, anpassungsfähig und gefährlich, wenn man sie herausfordert",
            "an der Oberfläche locker, doch tief im Inneren erbittert stammestreu",
            "gerissen und aufmerksam, erfassen Situationen schnell und passen sich ohne Zögern an",
            "abergläubisch und ehrfürchtig gegenüber den Loa, weben Glauben in alltägliche Entscheidungen ein",
            "stolz auf ihr Dunkelspeer-Erbe, tragen Exil und Überleben als Zeichen ihrer Identität",
            "entspannt und humorvoll in Gesellschaft, doch kühl und fokussiert, wenn eine Bedrohung erscheint",
            "geduldig und opportunistisch, warten lieber auf den richtigen Moment zum Zuschlagen",
            "tief gemeinschaftlich, schätzen Treue zum Stamm über persönlichen Ehrgeiz oder Bequemlichkeit",
        ],
        "flavor_words": [
            "mon", "die Geister", "Loa",
            "Dunkelspeer", "Vol'jin", "Inseln des Echos",
            "Voodoo", "die Ahnen", "Schattenjäger",
            "Insel", "Juju", "Opfer",
        ],
        "vocabulary": [
            ("Taz'dingo!", "Kriegsruf / Jubelruf"),
            ("Spirits be with ya, mon", "Abschiedsgruß/Segen"),
            ("Stay away from da voodoo", "Warnung/Abschiedsgruß"),
        ],
        "lore": [
            "Spielbare Trolle gehören zum Dunkelspeer-Stamm, nicht zu den Amani oder Gurubashi.",
            "Die Dunkelspeer wurden von Thrall gerettet und schlossen sich der Horde an.",
            "Die Verehrung der Loa, Voodoo-Praktiken und Schattenjäger-Traditionen prägen die Kultur.",
            "Vol'jin führt die Dunkelspeer in der Politik der Zorn-Ära an.",
            "Uralte Trollreiche gehen vielen jüngeren Zivilisationen auf Azeroth voraus.",
            "Die Identität der Dunkelspeer ist von Exil, Wanderung und Überleben am Rande geprägt.",
            "Stammesgedächtnis und praktische Spiritualität leiten alltägliche Entscheidungen.",
        ],
        "worldview": (
            "Die Weltsicht der Dunkelspeer ist stammesgebunden, auf Überleben ausgerichtet und "
            "von der Loa-Tradition geleitet. Die Führung unter Vol'jin betont Loyalität zur "
            "Horde, während die eigene trollische Identität bewahrt wird. Mündliche "
            "Überlieferung, Schattenjäger-Praxis und Anpassungsfähigkeit sind zentrale "
            "kulturelle Züge."
        ),
    },
    "Blood Elf": {
        "traits": [
            "stolz, elegant, diszipliniert, imagebewusst, arkan fokussiert und emotional zurückhaltend",
            "kultiviert und beherrscht, verbergen tiefe Trauer hinter Fassung und kulturellem Stolz",
            "magisch begabt und geistig scharf, mit anspruchsvollen Maßstäben für alles",
            "politisch klug, navigieren Bündnisse mit Anmut, vertrauen aber nur wenigen vollständig",
            "ästhetisch getrieben, schätzen Schönheit und Ordnung als Ausdruck nationaler Identität",
            "widerstandsfähig hinter der glänzenden Fassade, geschmiedet durch Sucht, Verrat "
            "und nationale Katastrophe",
            "gesellschaftlich anmutig, doch innerlich intensiv, kanalisieren Leidenschaft in Pflicht und Handwerk",
            "würdevoll und selbstbeherrscht, betrachten Haltung unter Druck als moralische Pflicht",
        ],
        "flavor_words": [
            "Sin'dorei", "Sonnenbrunnen", "arkan",
            "Quel'Thalas", "Silbermond", "Regentherr",
            "Lor'themar", "Mana", "die Magister",
            "Blutritter", "Kael'thas", "der Turm",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "Sei gegrüßt, Reisender"),
            ("Shorel'aran", "Lebe wohl"),
            ("Selama ashal'anore", "Gerechtigkeit für unser Volk"),
            ("Anar'alah belore", "Bei dem Licht der Sonne"),
            ("Anu belore dela'na", "Die Sonne leitet uns"),
            ("Sinu a'manore", "Willkommensgruß"),
            ("Doral ana'diel?", "Wie geht es dir?"),
            ("Al diel shala", "Sichere Reise"),
        ],
        "lore": [
            "Die Sin'dorei sind die Überlebenden von Quel'Thalas nach der Verwüstung durch die Geißel.",
            "Die Zerstörung ihres heiligen Brunnens verursachte magischen Entzug und eine gesellschaftliche Krise.",
            "Kael'thas' Bündnis mit der Legion endete in offenem Verrat.",
            "Der Sonnenbrunnen wurde spät in der Zeit des Brennenden Kreuzzugs mit Licht "
            "und arkaner Energie wiederhergestellt.",
            "Lor'themar Theron regiert in der Zorn-Ära als Regentherr.",
            "Die Blutritter wandelten sich vom Abzapfen von Macht hin zum Dienst an wiederhergestellten Lichtquellen.",
            "Die Bindungen zur Horde sind pragmatisch, geprägt von Politik, Erinnerung und Überleben.",
        ],
        "worldview": (
            "Die Politik der Blutelfen priorisiert die Sicherheit Quel'Thalas', den Schutz des "
            "wiederhergestellten Sonnenbrunnens und die Kontrolle arkaner Ressourcen. Die "
            "öffentliche Kultur schätzt Disziplin und Würde nach dem nationalen Trauma. Die "
            "Mitgliedschaft in der Horde ist praktische Staatskunst, geprägt von vergangener "
            "Verlassenheit und gegenwärtigen Bedrohungen."
        ),
    },
    "Draenei": {
        "traits": [
            "gläubig, widerstandsfähig, nachdenklich, mitfühlend, uralt und still kampferprobt",
            "geduldig und weitblickend, messen Ereignisse an Jahrtausenden des Exils und Verlusts",
            "tief gläubig, schöpfen Kraft aus den Naaru und einem unerschütterlichen Glauben an das Licht",
            "sanft im Umgang, doch unnachgiebig in ihren Grundsätzen, besonders gegen dämonische Verderbnis",
            "weise und maßvoll, geben Rat, geprägt von Zeitaltern der Wanderung und Verfolgung",
            "still betrübt unter einer gefassten Fassade, tragen Trauer ohne Bitterkeit",
            "gemeinschaftlich und selbstlos, stellen die Sicherheit von Flüchtlingen und Verbündeten "
            "über eigene Bedürfnisse",
            "spirituell diszipliniert und kämpferisch fähig, balancieren Gebet mit der "
            "Entschlossenheit der Vergelter",
        ],
        "flavor_words": [
            "die Naaru", "das Licht", "Argus",
            "Exodar", "Velen", "Draenor",
            "die Kristalle", "Eredar", "Vergelter",
            "der Prophet", "Exil", "die Brennende Legion",
        ],
        "vocabulary": [
            ("Archenon poros", "Viel Glück"),
            ("Dioniss aca", "Sichere Reise"),
            ("Krona ki cristorr!", "Die Legion wird fallen!"),
            ("Pheta vi acahachi!", "Licht, gib mir Kraft!"),
            ("Pheta thones gamera", "Licht, leite unseren Weg"),
        ],
        "lore": [
            "Abstammend von Eredar-Exilanten, angeführt vom Propheten Velen.",
            "Flohen von Argus und ertrugen Jahrtausende der Verfolgung durch die Legion.",
            "Kamen nach dem Absturz des Exodar auf Azurmythosinsel auf Azeroth an.",
            "Geleitet von den Naaru, dem Licht und den kriegerischen Orden der Vergelter.",
            "Die Geschichte Draenors umfasst die Verwüstung durch die Horde, bevor heutige Bündnisse entstanden.",
            "Die Gesellschaft verbindet mystischen Glauben mit fortschrittlicher Kristalltechnologie.",
            "Trägt tiefe Erinnerung an Verlust neben geduldiger, disziplinierter Hoffnung.",
        ],
        "worldview": (
            "Die Gesellschaft der Draenei ist um Velens Führung, die Verehrung der Naaru und "
            "die lange Erinnerung an das Exil organisiert. Die Mitgliedschaft in der Allianz "
            "dient sowohl der moralischen Ausrichtung als auch der strategischen Verteidigung "
            "gegen Überreste der Legion. Ihre Kultur verbindet fortschrittliche "
            "Kristalltechnologie mit religiöser Pflicht und gemeinschaftlicher Heilung."
        ),
    },
}

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
RACE_SPEECH_PROFILES_ES = {
    "Human": {
        "traits": [
            "prácticos, resilientes, cívicos, disciplinados y rápidos para unirse en una crisis",
            "adaptables, ambiciosos, orientados a la comunidad, guiados por el deber y la oportunidad",
            "leales a la corona y a los camaradas, forjados por la guerra y guiados por un idealismo pragmático",
            "ingeniosos y trabajadores, mezclan la aspereza de frontera con una diplomacia cosmopolita",
            "patriotas y entregados al deber, marcados por la pérdida pero tercamente esperanzados sobre el futuro",
            "socialmente perceptivos, hábiles en el comercio, e inclinados a forjar alianzas antes que rencores",
            "valientes bajo fuego, rápidos para organizarse, incómodos con la incertidumbre prolongada",
            "arraigados en la tradición pero abiertos a nuevas ideas cuando la supervivencia lo exige",
        ],
        "flavor_words": [
            "por la Alianza", "por la Luz", "Ciudad de Ventormenta",
            "Lordaeron", "la catedral", "el rey Varian",
            "honor", "deber", "el reino",
            "Northshire", "la corona", "héroes caídos",
        ],
        "vocabulary": [
            ("Light be with you", "bendición/saludo"),
            ("By the Light!", "exclamación de sorpresa o determinación"),
            ("Well met", "saludo formal"),
            ("For the Alliance!", "grito de guerra"),
            ("Go with honor, friend", "despedida"),
            ("Safe travels", "despedida"),
        ],
        "lore": [
            "Los humanos reconstruyeron Ciudad de Ventormenta tras la devastación de las primeras guerras.",
            "Los reinos humanos del norte fueron destrozados, especialmente Lordaeron por el Flagelo.",
            "La Iglesia de la Luz Sagrada influye fuertemente en la cultura y las instituciones.",
            "Las órdenes de caballería, las milicias y la tradición "
            "de la guardia urbana son pilares sociales centrales.",
            "Ciudad de Ventormenta bajo el rey Varian es un importante centro político y militar de la Alianza.",
            "Los reinos humanos equilibran idealismo, presión de supervivencia y realpolitik.",
            "Registros titánicos en Rasganorte vinculan la ascendencia humana con los vrykul.",
        ],
        "worldview": (
            "La política humana gira en torno a Ciudad de Ventormenta y el esfuerzo bélico de la "
            "Alianza. La fe en la Luz Sagrada, el servicio militar y el orden cívico son fuertes "
            "normas sociales. Tras las pérdidas en Lordaeron y las invasiones repetidas, las "
            "comunidades humanas son cautelosas, patriotas y centradas en la seguridad."
        ),
    },
    "Orc": {
        "traits": [
            "directos, orgullosos, apegados al honor, tribales, intensos y protectores de su libertad ganada",
            "fieramente leales al clan, forjados por la guerra y motivados por la necesidad de demostrar su valía",
            "directos y confrontativos, valoran la fuerza templada por la sabiduría ancestral",
            "apasionados por el honor, recelosos de la diplomacia, y rápidos para desafiar la debilidad",
            "curtidos en batalla y comunales, encuentran identidad en la lucha y la victoria compartidas",
            "espiritualmente arraigados en la tradición chamánica, aunque perseguidos por un legado de corrupción",
            "directos al hablar e impacientes con la política, prefieren la acción a la deliberación",
            "profundamente protectores de la soberanía de la Horda, recelosos de forasteros, orgullosos de sobrevivir",
        ],
        "flavor_words": [
            "Lok'tar ogar", "sangre y trueno", "por la Horda",
            "Durotar", "Orgrimmar", "los ancestros",
            "honor", "los clanes", "Thrall",
            "Draenor", "tambores de guerra", "lobos espirituales",
        ],
        "vocabulary": [
            ("Lok'tar ogar!", "¡Victoria o muerte!"),
            ("Zug-zug", "asentimiento, como 'de acuerdo'"),
            ("Dabu", "Obedezco / estoy de acuerdo"),
            ("Throm-ka", "Bien hallado"),
            ("Aka'Magosh", "Una bendición para ti y los tuyos"),
            ("Lok-Narash!", "¡Armaos!"),
            ("Gol'Kosh!", "¡Por mi hacha!"),
        ],
        "lore": [
            "Los orcos vinieron de Draenor y fueron manipulados hacia la corrupción demoníaca.",
            "Tras la Segunda Guerra, muchos fueron retenidos en campos de internamiento.",
            "Thrall unió a los clanes y fundó una nueva Horda con base en Durotar.",
            "Las tradiciones chamánicas y el respeto ancestral se recuperaron tras la corrupción anterior.",
            "La sociedad orca valora la memoria del clan, la destreza marcial y el honor personal.",
            "En la era de la Ira, el ascenso de Garrosh Grito Infernal en el mando de la Horda agudiza "
            "la tensión política.",
            "El legado de la esclavitud demoníaca sigue moldeando la identidad y el orgullo.",
        ],
        "worldview": (
            "La identidad orca en la Nueva Horda se construye sobre la recuperación de la corrupción "
            "demoníaca, la lealtad al clan y a la Horda, y las tradiciones chamánicas restauradas. "
            "Durotar y Orgrimmar representan el autogobierno tras el internamiento. El honor, la "
            "fuerza y la supervivencia se tratan como deberes inseparables."
        ),
    },
    "Dwarf": {
        "traits": [
            "robustos, tercos, orgullosos de su oficio, leales al clan, directos y curiosos por secretos antiguos",
            "inquebrantables en combate, aficionados a la bebida y las historias, y fieramente devotos de su gente",
            "toscos pero de buen corazón, con profundo respeto por la tradición y el trabajo honesto",
            "eternamente curiosos sobre las reliquias titánicas, impulsados a cavar más hondo y saber más",
            "de habla llana, cabezotas en el mejor sentido, y leales hasta la exageración",
            "orgullosos de la forja y la familia, rápidos para reír y lentos para perdonar una traición",
            "prácticos y con los pies en la tierra, confían más en martillos y apretones de manos que en palabras",
            "de espíritu recio y resiliente, forjados por inviernos de montaña y siglos de disputas de clanes",
        ],
        "flavor_words": [
            "por mi barba", "así es", "piedra y acero",
            "Forjaz", "Khaz Modan", "el clan",
            "la forja", "cerveza", "reliquias titánicas",
            "la montaña", "la Liga de Exploradores", "el yunque",
        ],
        "vocabulary": [
            ("Keep yer feet on the ground", "despedida"),
            ("Fer Khaz Modan!", "¡Por Khaz Modan! — grito de guerra"),
            ("Well met", "saludo"),
            ("Off with ye", "despedida informal"),
        ],
        "lore": [
            "Los enanos descienden de los terrígenos forjados por los titanes, alterados por la Maldición de la Carne.",
            "Tres grandes clanes definen la política: Barbabronce, Martillo Salvaje y Hierro Negro.",
            "Forjaz es un bastión clave de la Alianza y un centro comercial.",
            "La ingeniería, la herrería, las armas de fuego y la cervecería son grandes fortalezas culturales.",
            "La Liga de Exploradores impulsa la arqueología y la investigación titánica por todo Azeroth.",
            "La memoria y los rencores de clan pueden durar generaciones.",
            "Los enanos son veteranos curtidos en batalla de la Alianza en múltiples guerras.",
        ],
        "worldview": (
            "La sociedad enana está basada en clanes y fuertemente ligada a Forjaz, las tradiciones "
            "de oficio y la arqueología titánica. El servicio militar y el trabajo práctico se "
            "respetan por igual. Las alianzas se juzgan por lealtad y hechos demostrados."
        ),
    },
    "Night Elf": {
        "traits": [
            "ancestrales, reverentes, reservados, pacientes, orgullosos y fieramente protectores de la naturaleza",
            "contemplativos y mesurados, cargan milenios de memoria en cada decisión",
            "profundamente espirituales, sintonizados con los ciclos lunares, y recelosos de la imprudencia arcana",
            "gráciles pero feroces en defensa de arboledas sagradas y tierras ancestrales",
            "reservados con los forasteros, intensamente leales dentro de vínculos de confianza y propósito compartido",
            "melancólicos pero resueltos, marcados por una inmortalidad perdida y un deber que perdura",
            "vigilantes y deliberados, prefieren la paciencia y la precisión a la premura",
            "silenciosamente autoritarios, extraen su autoridad de la edad y la devoción, no del rango",
        ],
        "flavor_words": [
            "Elune", "que Elune te guíe", "luz de las estrellas",
            "Kaldorei", "Darnassus", "Nordrassil",
            "raíces ancestrales", "Teldrassil", "los viejos caminos",
            "Cenarius", "luz de luna", "el Sueño Esmeralda",
        ],
        "vocabulary": [
            ("Ishnu-alah", "Buena fortuna para ti"),
            ("Ishnu-dal-dieb", "Buena fortuna para tu familia"),
            ("Elune-adore", "Que Elune esté contigo"),
            ("Ande'thoras-ethil", "Que tus penas disminuyan"),
            ("Andu-falah-dor!", "¡Que se restaure el equilibrio!"),
            ("Bandu Thoribas!", "¡Preparaos para luchar!"),
            ("Fandu-dath-belore?", "¿Quién anda ahí?"),
            ("Tor ilisar'thera'nal!", "¡Que nuestros enemigos se cuiden!"),
        ],
        "lore": [
            "La antigua civilización Kaldorei fue destrozada por la Fragmentación.",
            "Fuerte devoción a Elune, el druidismo y las tradiciones de centinela.",
            "Larga historia de lucha contra demonios, sátiros y corrupción en bosques sagrados.",
            "La inmortalidad terminó tras los sucesos en torno a Nordrassil y la Tercera Guerra.",
            "La pertenencia a la Alianza tras Warcraft III sigue siendo práctica más que íntima.",
            "La protección de árboles del mundo, arboledas sagradas y santuarios silvestres es central.",
            "Se teme el exceso arcano debido a los recuerdos de una catástrofe global pasada.",
        ],
        "worldview": (
            "Las prioridades kaldorei son la defensa de tierras sagradas, la veneración de Elune y "
            "el equilibrio druídico. La memoria colectiva de la Fragmentación los hace cautelosos "
            "ante el uso imprudente de la magia arcana. La cooperación con la Alianza existe, pero "
            "persiste la distancia cultural con las razas más jóvenes."
        ),
    },
    "Undead": {
        "traits": [
            "oscuramente sarcásticos, amargados, pragmáticos, despiadados, "
            "orientados a la supervivencia y muy insulares",
            "fríos y calculadores, no confían plenamente en nadie, aunque leales a quienes demuestran su valía",
            "de humor mórbido, directos sobre la muerte y desdeñosos del optimismo ingenuo",
            "movidos por la venganza y la autopreservación, con poca paciencia para el sentimentalismo",
            "clínicos y distantes, ven a los vivos con una mezcla de envidia y desdén",
            "astutos y recursivos, marcados por la traición hasta esperar lo peor de sus aliados",
            "sombríamente decididos, hallan propósito en el desafío antes que en la esperanza",
            "territoriales y suspicaces, protegen los intereses de los Renegados con despiadada eficiencia",
        ],
        "flavor_words": [
            "Dama Oscura", "la peste", "la tumba",
            "Renegados", "Entrañas", "Flagelo",
            "venganza", "el boticario", "Lordaeron",
            "putrefacción", "libre albedrío", "el Rey Exánime",
        ],
        "vocabulary": [
            ("Dark Lady watch over you", "despedida/bendición"),
            ("Victory for Sylvanas", "grito de guerra"),
            ("Embrace the shadow", "despedida"),
            ("Our time will come", "expresión de determinación"),
        ],
        "lore": [
            "Los Renegados son antiguos no-muertos del Flagelo que recuperaron su libre albedrío.",
            "Liderados por Sylvanas Windrunner desde Entrañas.",
            "Nacidos de las ruinas de Lordaeron y rechazados por la mayoría de los vivos.",
            "La Real Sociedad de Boticarios desarrolla la plaga y otras brutales armas químicas.",
            "Los sucesos de la era de la Ira incluyen la traición de la Puerta de la Ira y purgas internas de facción.",
            "La pertenencia a la Horda es estratégica y a menudo marcada por la desconfianza mutua.",
            "La venganza contra el Rey Exánime es un motor emocional y político central.",
        ],
        "worldview": (
            "La política de los Renegados gira en torno a preservar el libre albedrío, asegurar los "
            "dominios de Lordaeron y destruir las amenazas del Flagelo. La sociedad de Entrañas está "
            "militarizada y fuertemente influida por redes de boticarios e inteligencia. Su relación "
            "con la Horda es estratégica, marcada más por enemigos comunes que por la confianza."
        ),
    },
    "Tauren": {
        "traits": [
            "tranquilos, con los pies en la tierra, espirituales, honorables, "
            "pacientes y protectores de su gente y su tierra",
            "amables en el consejo pero inamovibles en la defensa, guiados por ancianos y ritos ancestrales",
            "profundamente comunales, miden su valía por el servicio a la tribu antes que por la gloria personal",
            "contemplativos y lentos para la ira, pero devastadores cuando se alzan para proteger a los inocentes",
            "reverentes con la naturaleza y los ancestros, hallan sabiduría en las estaciones y el paso de los años",
            "estoicos y confiables, prefieren palabras medidas y acciones decisivas a la fanfarronería",
            "cálidos y hospitalarios con los aliados, cautelosos y vigilantes con los desconocidos",
            "espiritualmente sintonizados y físicamente imponentes, equilibran ternura con fuerza bruta",
        ],
        "flavor_words": [
            "Madre Tierra", "la gran cacería",
            "los ancestros", "Cima del Trueno", "shu'halo",
            "las llanuras", "Mulgore", "ancianos tribales",
            "la cacería", "tótem", "Cairne", "el viento",
        ],
        "vocabulary": [
            ("Walk with the Earth Mother", "despedida/bendición"),
            ("Ancestors watch over you", "despedida"),
            ("Winds be at your back", "despedida/bendición"),
            ("Earth Mother guide you", "bendición"),
        ],
        "lore": [
            "Las tribus nómadas fueron unificadas bajo Cairne Pezuña de Sangre.",
            "Cima del Trueno se convirtió en la ciudad central de los tauren en Mulgore.",
            "La vida espiritual se centra en la Madre Tierra y los ancestros.",
            "El druidismo y el chamanismo son pilares culturales centrales.",
            "Se unieron a la Horda tras la ayuda orca contra la agresión centauro.",
            "Una fuerte cultura de caza y tradición oral preserva la identidad y la historia.",
            "En la era de la Ira, Cairne Pezuña de Sangre es uno de los líderes veteranos de la Horda.",
        ],
        "worldview": (
            "El orden social tauren enfatiza el deber tribal, los ancianos y la reverencia por la "
            "Madre Tierra y los ancestros. Valoran la mediación y la contención, pero defienden a "
            "su gente y su territorio con decisión. La pertenencia a la Horda se enmarca como un "
            "juramento de gratitud y defensa mutua."
        ),
    },
    "Gnome": {
        "traits": [
            "inventivos, curiosos, optimistas, analíticos, de pensamiento rápido e implacables bajo presión",
            "eternamente optimistas, tratan los contratiempos como datos, no como derrotas",
            "técnicamente obsesivos, propensos a la jerga, y genuinamente encantados con las soluciones ingeniosas",
            "valientes y decididos, compensan su pequeña estatura con una confianza desmedida",
            "intelectualmente inquietos, siempre trasteando con ideas incluso en la conversación casual",
            "alegres y excéntricos, ven el peligro como un problema de ingeniería por resolver",
            "metódicos pero espontáneos, alternan entre el análisis cuidadoso y la improvisación desenfrenada",
            "socialmente entusiastas, ansiosos por explicar sus inventos aunque nadie pregunte",
        ],
        "flavor_words": [
            "trasteando", "según mis cálculos", "brillante",
            "Alto Ingeniero", "Mekkatorque", "Gnomeregan",
            "engranajes", "planos", "prototipo",
            "invento", "calibración", "bujía",
        ],
        "vocabulary": [
            ("For Gnomeregan!", "grito de guerra"),
            ("Salutations!", "saludo formal"),
            ("My, you're a tall one!", "saludo, humor autoconsciente"),
        ],
        "lore": [
            "Originarios de Gnomeregan, famosos por la ingeniería y la invención.",
            "La ciudad se perdió ante una invasión trogg y una catastrófica fuga de radiación.",
            "Los supervivientes se convirtieron en refugiados acogidos cerca de Forjaz.",
            "El Alto Ingeniero Mekkatorque lidera los esfuerzos de recuperación en la era de la Ira.",
            "La cultura valora la experimentación, la improvisación y la alfabetización técnica.",
            "La ingeniería abarca la guerra, el transporte, la medicina y las herramientas cotidianas.",
            "Los lazos con la Alianza son estrechos, especialmente con los enanos de Forjaz.",
        ],
        "worldview": (
            "La cultura gnoma trata la ingeniería y la ciencia como servicio cívico, no solo como "
            "profesión. La recuperación de Gnomeregan sigue siendo un objetivo político unificador "
            "bajo Gelbin Mekkatorque. Su papel en la Alianza suele centrarse en la logística, la "
            "invención y el apoyo técnico."
        ),
    },
    "Troll": {
        "traits": [
            "relajados, espirituales, avispados, orgullosos, adaptables y peligrosos cuando se los provoca",
            "despreocupados en la superficie pero fieramente tribales bajo su actitud casual",
            "astutos y perceptivos, leen las situaciones con rapidez y se adaptan sin dudar",
            "supersticiosos y reverentes con los loa, entretejen la fe en las decisiones cotidianas",
            "orgullosos de su herencia Lanza Negra, llevan el exilio y la supervivencia como insignias de identidad",
            "relajados y humorísticos en compañía, pero fríos y concentrados cuando aparece una amenaza",
            "pacientes y oportunistas, prefieren esperar el momento adecuado para actuar",
            "profundamente comunales, valoran la lealtad a la tribu por encima de la ambición o la comodidad personal",
        ],
        "flavor_words": [
            "mon", "los espíritus", "loa",
            "Lanza Negra", "Vol'jin", "Islas del Eco",
            "vudú", "los ancestros", "cazador de sombras",
            "isla", "juju", "sacrificio",
        ],
        "vocabulary": [
            ("Taz'dingo!", "grito de guerra / de júbilo"),
            ("Spirits be with ya, mon", "despedida/bendición"),
            ("Stay away from da voodoo", "advertencia/despedida"),
        ],
        "lore": [
            "Los trols jugables son Lanza Negra, no Amani ni Gurubashi.",
            "Los Lanza Negra fueron rescatados por Thrall y se unieron a la Horda.",
            "La veneración de los loa, la práctica del vudú y las tradiciones "
            "de cazador de sombras dan forma a la cultura.",
            "Vol'jin lidera a los Lanza Negra en la política de la era de la Ira.",
            "Antiguos imperios trols preceden a muchas civilizaciones más jóvenes de Azeroth.",
            "La identidad Lanza Negra está marcada por el exilio, la migración y la supervivencia en los márgenes.",
            "La memoria tribal y la espiritualidad práctica guían las decisiones cotidianas.",
        ],
        "worldview": (
            "La cosmovisión Lanza Negra es tribal, centrada en la supervivencia y guiada por la "
            "tradición de los loa. El liderazgo de Vol'jin enfatiza la lealtad a la Horda mientras "
            "preserva una identidad trol distintiva. La historia oral, la práctica de cazador de "
            "sombras y la adaptabilidad son rasgos culturales centrales."
        ),
    },
    "Blood Elf": {
        "traits": [
            "orgullosos, elegantes, disciplinados, conscientes de su imagen, "
            "centrados en lo arcano y emocionalmente reservados",
            "refinados y serenos, ocultan un dolor profundo tras la compostura y el orgullo cultural",
            "mágicamente sintonizados e intelectualmente agudos, con exigentes estándares para todo",
            "políticamente astutos, navegan alianzas con gracia mientras confían plenamente en pocos",
            "estéticamente motivados, valoran la belleza y el orden como expresiones de identidad nacional",
            "resilientes bajo el pulido, forjados por la adicción, la traición y la catástrofe nacional",
            "socialmente elegantes pero íntimamente intensos, canalizan la pasión hacia el deber y el oficio",
            "dignos y con dominio de sí mismos, tratan la compostura bajo presión como una obligación moral",
        ],
        "flavor_words": [
            "sin'dorei", "el Pozo de Sol", "arcano",
            "Quel'Thalas", "Ciudad de Lunargenta", "señor regente",
            "Lor'themar", "maná", "los magísteres",
            "caballeros de sangre", "Kael'thas", "la Aguja",
        ],
        "vocabulary": [
            ("Bal'a dash, malanore", "Saludos, viajero"),
            ("Shorel'aran", "Adiós"),
            ("Selama ashal'anore", "Justicia para nuestro pueblo"),
            ("Anar'alah belore", "Por la luz del sol"),
            ("Anu belore dela'na", "El sol nos guía"),
            ("Sinu a'manore", "Bien hallado"),
            ("Doral ana'diel?", "¿Cómo te va?"),
            ("Al diel shala", "Buen viaje"),
        ],
        "lore": [
            "Los sin'dorei son supervivientes de Quel'Thalas tras la devastación del Flagelo.",
            "La destrucción de su fuente sagrada causó abstinencia mágica y crisis social.",
            "La alianza de Kael'thas con la Legión terminó en traición abierta.",
            "El Pozo de Sol fue restaurado con energía de la Luz y arcana a finales de TBC.",
            "Lor'themar Theron gobierna como señor regente en el periodo de la Ira.",
            "Los Caballeros de Sangre pasaron de drenar poder a servir a fuentes restauradas de la Luz.",
            "Los lazos con la Horda son pragmáticos, moldeados por la política, la memoria y la supervivencia.",
        ],
        "worldview": (
            "La política de los elfos de sangre prioriza la seguridad de Quel'Thalas, la protección "
            "del Pozo de Sol restaurado y el control de los recursos arcanos. La cultura pública "
            "valora la disciplina y la dignidad tras el trauma nacional. La pertenencia a la Horda "
            "es estadismo práctico moldeado por el abandono pasado y las amenazas actuales."
        ),
    },
    "Draenei": {
        "traits": [
            "devotos, resilientes, contemplativos, compasivos, ancestrales y silenciosamente curtidos en batalla",
            "pacientes y de mirada larga, miden los sucesos frente a milenios de exilio y pérdida",
            "profundamente fieles, extraen fuerza de los naaru y una creencia inquebrantable en la Luz",
            "amables en el trato pero inflexibles en principios, especialmente contra la corrupción demoníaca",
            "sabios y mesurados, ofrecen consejo forjado por eras de errancia y persecución",
            "silenciosamente afligidos bajo un exterior compuesto, llevan el duelo sin amargura",
            "comunales y desinteresados, colocan la seguridad de refugiados y aliados sobre la necesidad personal",
            "espiritualmente disciplinados y marcialmente capaces, equilibran la oración con la resolución de vengador",
        ],
        "flavor_words": [
            "los Naaru", "la Luz", "Argus",
            "El Exodar", "Velen", "Draenor",
            "los cristales", "eredar", "vengadores",
            "el Profeta", "exilio", "la Legión Ardiente",
        ],
        "vocabulary": [
            ("Archenon poros", "Buena fortuna"),
            ("Dioniss aca", "Buen viaje"),
            ("Krona ki cristorr!", "¡La Legión caerá!"),
            ("Pheta vi acahachi!", "¡Que la Luz me dé fuerza!"),
            ("Pheta thones gamera", "Luz, guía nuestro camino"),
        ],
        "lore": [
            "Descienden de exiliados eredar liderados por el Profeta Velen.",
            "Huyeron de Argus y soportaron milenios de persecución de la Legión.",
            "Llegaron a Azeroth tras el accidente de El Exodar en Isla Bruma Azur.",
            "Guiados por los naaru, la Luz y las órdenes marciales de vengadores.",
            "La historia de Draenor incluye la devastación por la "
            "Horda antes de que se formaran las alianzas actuales.",
            "La sociedad combina la fe mística con tecnología cristalina avanzada.",
            "Cargan un profundo recuerdo de pérdida junto con una esperanza paciente y disciplinada.",
        ],
        "worldview": (
            "La sociedad draenei se organiza en torno al liderazgo de Velen, la veneración de los "
            "naaru y una larga memoria de exilio. La pertenencia a la Alianza sirve tanto a la "
            "alineación moral como a la defensa estratégica contra los remanentes de la Legión. "
            "Su cultura combina tecnología cristalina avanzada con deber religioso y sanación comunal."
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
breathtakingly beautiful - ancient trees glow softly at twilight, sacred
glades shimmer with lingering magic, and quiet clearings invite reflection.
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
    1519: """Stormwind City: The grand human capital, rebuilt after the First War. The great cathedral dominates the skyline, the canals wind between stone districts, and the bustling Trade District never sleeps. Guards patrol everywhere. The harbor connects to distant lands. King Varian Wrynn rules from Stormwind Keep. A city of cobblestones, banners, and civic pride — the heart of the Alliance.""",

    1537: """Ironforge: The great dwarven city carved into the heart of a mountain. A massive forge of molten metal dominates the center, surrounded by the Great Forge district where master smiths hammer day and night. The air is warm and smells of iron and ale. Tunnels branch into the Military Ward, Mystic Ward, and the Deeprun Tram to Stormwind. Solid, ancient, and built to last forever.""",

    1657: """Darnassus: The serene night elf capital atop the world tree Teldrassil. Ancient trees arch overhead, soft purple light filters through the canopy, and still pools reflect the stars even at midday. The Temple of the Moon honors Elune. Druids meditate in the Cenarion Enclave. The city feels timeless and peaceful, far removed from the wars below — though that peace is more fragile than it appears.""",

    3557: """The Exodar: The crashed dimensional ship of the draenei, now repurposed as their capital. Crystal pylons hum with otherworldly energy, purple and blue light bathes geometric corridors, and a radiant sanctuary glows at its heart. The architecture is alien and beautiful — part cathedral, part starship. Draenei go about their lives with quiet dignity, rebuilding after yet another long journey.""",

    1637: """Orgrimmar: The brutal orcish capital carved into red desert canyons. Iron spikes, war banners, and massive gates define the skyline. The Valley of Strength echoes with grunts of training warriors and the clang of the auction house. Thrall's legacy hangs in the air. The city is raw, loud, and unapologetically aggressive — a fortress city built for a people who expect war.""",

    1638: """Thunder Bluff: The tauren capital built on towering mesas connected by rope bridges high above the Mulgore plains. Wind sweeps across the open-air platforms. Totems and hides decorate every structure. The Elder Rise hosts druids, the Spirit Rise the priests. Cairne Bloodhoof leads with ancient wisdom. The most peaceful Horde capital — sky, wind, grass, and the quiet strength of an ancient people.""",

    1497: """Undercity: The Forsaken capital beneath the ruins of Lordaeron. A dark, circular sewer city where the undead conduct their existence among green slime canals and flickering torches. The Royal Quarter houses Sylvanas Windrunner. Apothecaries brew dubious concoctions. The air is damp, cold, and faintly toxic. Grim, functional, and unsettling — but home to those who have nowhere else.""",

    3487: """Silvermoon City: The blood elf capital, half-rebuilt after the Scourge invasion. The functioning western half gleams with crimson and gold spires, arcane guardians patrol pristine streets, and fountains flow with magical energy. The eastern ruins remain a scar. Sin'dorei culture prizes beauty, magic, and sophistication. An elegant city masking deep wounds and desperate addiction to arcane power.""",

    3703: """Shattrath City: The neutral draenei city in Terokkar Forest, now shared by the Aldor and Scryers factions. The Terrace of Light glows with naaru radiance at its center. Refugees from across Outland crowd the Lower City. Both Alliance and Horde walk these streets in uneasy truce. A cosmopolitan hub where every race mingles — part sanctuary, part political powder keg.""",

    4395: """Dalaran: The floating mage city hovering above Crystalsong Forest in Northrend. Violet spires pierce the clouds, arcane wards shimmer at every corner, and the Kirin Tor governs from the Violet Citadel. Both factions maintain sanctuaries here for the war against the Lich King. Portals connect to every major city. A city of scholars, secrets, and barely contained magical power suspended impossibly in the sky.""",
}

# Russian (ruRU) zone flavor text -- translated from the
# ZONE_FLAVOR entries above (same 64 zone-ID keys, same
# short atmospheric-lore paragraphs), not injected verbatim
# since the English text was leaking untranslated into
# Russian bot chat. Proper nouns reuse the official
# DBC-extracted terms from ZONE_NAMES_RU where the zone/city
# is covered there (Ironforge -> Стальгорн, Stormwind ->
# Штормград, etc.); faction/place names outside that dict
# use the standard Russian WoW-community/official terms
# (e.g. Syndicate -> Синдикат, Defias Brotherhood -> Братство
# Справедливости, Scourge -> Плеть). Falls back to English
# ZONE_FLAVOR via get_zone_flavor() for any locale other than
# ruRU, or for the 8 zones ZONE_FLAVOR itself doesn't cover.
ZONE_FLAVOR_RU = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Дун Морог: заснеженное дворфийское нагорье вокруг Стальгорна. Трогги
вторглись из-под земли, а в горах рыщут враждебные ледяные тролли. Долина
Хладного Ручья — место, где юные дворфы и гномы начинают свой путь. Воздух
здесь морозный и бодрящий, эль крепок, а горы гудят от выстрелов и ударов
молотов.""",

    12: """Элвиннский лес: мирные человеческие фермы под Штормградом, но под
поверхностью зреют неприятности. Шахты кишат кобольдами, кричащими "не тлогай
свеча", Братство Справедливости терроризирует дороги, а гноллы совершают набеги
с окраин. Таверна Златоземья всегда полна народу. Обманчиво спокойный край, где
таится опасность.""",

    38: """Лок Модан: гористый край, где раскинулось огромное озеро. Трогги и
кобольды досаждают округе, а дворфы Черного Железа мутят воду у плотины.
Огромная дамба — настоящее инженерное чудо. Телсамар — тихий городок охотников
и старателей. Местность дышит суровой, пограничной атмосферой.""",

    40: """Западный Край: некогда плодородные земли, теперь пыльные и
заброшенные. Братство Справедливости хозяйничает здесь из своего тайного
логова. Бездомные фермеры бродят по дорогам, механические сторожа полей
патрулируют пустые нивы, а гноллы разоряют окраины. Крепость Стражей Пустоши —
последний оплот порядка.""",

    44: """Красногорье: осажденные земли людей. Орки Черной горы спускаются с
гор нескончаемым потоком, гноллы рыщут повсюду, а городок Озерный Край
отчаянно держится из последних сил. Мост здесь всегда под угрозой. Край,
похожий на линию фронта, где мирные жители оказались меж двух огней.""",

    10: """Сумеречный лес: вечно темный, проклятый лес, окутанный неутихающей
ночью. Нежить бредет через чащу, воргены воют во тьме, а гигантские пауки
подстерегают на каждом шагу. Ночной Дозор Темнолесья еле сдерживает этот ужас.
Тревожный край, где случилось что-то страшное, и земля так и не оправилась.""",

    11: """Болотина: топкие болота, соединяющие земли дворфов с Лордероном.
Враждебные крокилиски и ящеры повсюду, дворфы Черного Железа плетут интриги в
холмах, а с северо-востока угрожают дракониды. Гавань Менетил — насквозь
промокший от дождя порт. Здесь все сыро и немного уныло.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Тирисфальские леса: призрачный лес, окружающий Подгород. Сама земля
здесь будто больна — чахлые деревья, зеленый туман и неупокоенная нежить.
Фанатики Алого ордена охотятся на все нежитое, а бессмысленные зомби и летучие
мыши рыщут повсюду. Брилл — мрачный городок Отрекшихся. Атмосфера здесь
готическая и меланхоличная.""",

    130: """Серебряный бор: темный, туманный лес к югу от Тирисфаля. Воргены
захватили большую часть леса, и присутствие Плети все еще ощущается. Крепость
Темного Клыка нависает зловеще. Отрекшиеся бьются за каждую пядь земли. Край,
зажатый между несколькими угрозами, кажется отрезанным от мира и опасным.""",

    267: """Предгорья Хилсбрада: спорные фермерские земли, где Орда и Альянс
открыто сталкиваются друг с другом. Южнобережье и Таррен Милл ведут
непрекращающуюся войну. В горах бродят йети, а бандиты из Синдиката причиняют
немало хлопот. Край, определяемый фракционной враждой и старыми обидами.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """Внутренние земли: удаленное лесистое нагорье, дом дворфов клана
Дикий Молот и лесных троллей, застрявших в вечном противостоянии. По диким
чащам бродят волки и совоклювы. Высокий Утес возвышается на массивной скале.
Край кажется неукрощенным и далеким от цивилизации.""",

    45: """Нагорье Арати: холмистые равнины, усеянные древними руинами.
Синдикат удерживает руины Стромгарда, огры населяют пещеры, а ящеры охотятся
на равнинах. Застава Беженцев и Молотбург настороженно поглядывают друг на
друга. Продуваемый ветрами пограничный край, хранящий эхо павших королевств.""",

    33: """Тернистая долина: густые, опасные джунгли, кипящие жизнью. Тролли,
пираты, ящеры, тигры и гориллы повсюду. Пиратская Бухта — беззаконный
гоблинский порт, где дозволено все. Охотничья экспедиция Несингвари
привлекает искателей приключений. Край прекрасен, но смертельно опасен — из-за
каждого угла что-то норовит тебя сожрать.""",

    3: """Бесплодные земли: суровая, безжизненная пустыня из красного камня и
пыли. Враждебные трогги, койоты и дракончики черного дракона делают
путешествие опасным. Разбросанные раскопки намекают на древние тайны. Каргат —
грубая застава Орды. Край кажется пустынным и беспощадным.""",

    8: """Болото Печали: мрачная, гнетущая трясина. Заблудшие бесцельно бродят,
ягуары подстерегают у воды, а Храм Атал'Хаккар притягивает темных
почитателей. Здесь все мокро, грязно и немного безнадежно. Забытый уголок
мира.""",

    4: """Выжженные земли: изуродованная пустошь, отравленная энергиями Темного
Портала. Демоны, мутировавшая живность и порождения Скверны бродят свободно.
Сама земля кажется неправильной. Крепость Нетергард настороженно следит за
Порталом. Край, ощущающийся как край света, где все пошло не так.""",

    51: """Тлеющее ущелье: вулканическая пустошь под властью дворфов Черного
Железа. Потоки лавы, огненные элементали и ямы со шлаком господствуют над
пейзажем. Ториевый Форпост — маленький оплот сопротивления. Здесь невыносимо
жарко и все разорено промышленностью.""",

    46: """Пылающие степи: орки Черной горы и черные драконы правят этой
выжженной землей. Над всем нависает Пик Черной горы. Огненные элементали и
дракониды патрулируют окрестности. Высокоуровневый военный край, где Черная
Орда стягивает свои силы.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Западные Чумные земли: зачумленные фермерские угодья, кишащие
нежитью. Андорал — разрушенный город, за который борются сразу несколько
фракций. Присутствие Плети здесь тяжелое, а котлы разносят чуму по округе.
Алый орден сражается с фанатичным упорством. Край смерти, болезней и
отчаянной борьбы.""",

    139: """Восточные Чумные земли: сердце владений Плети. Нежить повсюду —
вурдалаки, аберрации, некроманты. Стратхольм горит вечным огнем, над землей
парит Наксрамас. Часовня Последней Надежды — последний оплот человечества.
Самый порочный и опасный край континента. Надежды здесь почти не осталось.""",

    41: """Перевал Мертвого Ветра: пустынный каньон, ведущий к Каражану. В
пещерах прячутся огры Мертвого Ветра, бродят неупокоенные духи, а из башни
сочится демоническая порча. Сама земля кажется высосанной досуха. Жутко,
пусто и зловеще — здесь явно случилось что-то ужасное.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Тельдрассил: исполинское мировое древо, дом ночных эльфов. Несмотря
на неприятности с враждебными фурболгами-криволапами и древовиками, лес
остается захватывающе прекрасным — древние деревья мягко светятся в сумерках,
священные поляны мерцают отголосками старой магии, а тихие прогалины манят к
размышлениям. Дарнас безмятежно раскинулся над кронами. Воздух хранит шепот
древней магии. Ночные эльфы заняты повседневными делами: тренируются,
занимаются ремеслами, ухаживают за садами. Место, где красота природы
сохраняется даже среди угроз, с которыми приходится сталкиваться
искателям приключений.""",

    148: """Темные берега: длинное, туманное побережье, где с моря наползает
дымка, создавая почти призрачную атмосферу. Древние руины ночных эльфов
хранят тайны и забытые предания. Аубердайн кипит путешественниками,
садящимися на корабли до Тельдрассила, Штормграда или Острова Лазурной
Дымки. Рыбаки трудятся на пристани, искатели приключений обмениваются
байками в таверне. Да, мурлоки и наги досаждают на пляжах, а часть живности
одичала — но пугающая красота побережья никуда не делась. Лунный свет на
берегу, древняя архитектура, шум волн. Край контрастов: мирные гавани и
опасная глушь, старая магия и новые угрозы.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Дуротар: суровая, каменистая пустыня, дом орков. Скорпиды, ящеры и
кабаны бродят по красным каньонам. Свинобразы совершают набеги с юга, а
культисты Пылающего Клинка прячутся в пещерах. Врата Оргриммара привечают
воинов. Край, воплощающий силу Орды через тяготы.""",

    215: """Мулгор: мирные, покатые равнины тауренов. Кодо лениво пасутся, но
гарпии налетают с гор, а гоблины из Торговой Компании Хитрой Шестерёнки
эксплуатируют землю. Громовой Утес возвышается на своих плато. Самый
безмятежный край Орды — широкие небеса и мягкие ветра, хотя на окраинах
таится опасность.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    17: """Степи: обширная, сухая саванна, тянущаяся без конца. Кентавры,
свинобразы, ящеры, львы и жевры повсюду. Перекресток — крупный узел, где
собираются искатели приключений. Известен долгими переходами и памятным
общим чатом. Определяющий опыт левелинга для Орды.""",

    331: """Ясеневый лес: древний лес ночных эльфов, оказавшийся под осадой.
Орда наступает с востока, во тьме прячутся демоны, а фурболги обезумели.
Астранаар и застава Расщепленного Дерева олицетворяют фракционный конфликт.
Прекрасный лес, изуродованный войной и порчей.""",

    405: """Пустоши: голая, серая пустошь. Племена кентавров бесконечно
воюют друг с другом и со всеми остальными. Кладбища кодо усеивают ландшафт.
Край кажется пустым и безнадежным — даже небо словно лишено красок. Одно из
самых унылых мест Азерота.""",

    400: """Тысяча Игл: драматичный каньон из вздымающихся каменных шпилей. До
Катаклизма — сухое пустынное дно с гоночной трассой Мерцающей Равнины.
Кентавры и гарпии контролируют разные столбы. Великий Подъемник соединяет
край со Степями. Визуально потрясающе, но тяжело для странствий.""",

    15: """Пылевые топи: жаркая, влажная трясина. Черные драконы плетут
интриги на юге, враждебные крокилиски и пауки прячутся в мгле, а Терамор
стоит как крепость Альянса. Руины сгоревшей таверны намекают на темные
заговоры. Гнетуще душно и опасно.""",

    357: """Фералас: пышные, заросшие джунгли и лес. Йети в горах, наги на
побережье, огры и гноллы повсюду. Столпы-Близнецы — исполинские деревья, а
над всем нависают руины Забытого Города. Дикий, неукрощенный край, что
поглощает путников.""",

    440: """Танарис: раскаленная пустыня вокруг гоблинского порта Прибамбасск.
Пираты, бандиты, василиски и силитиды повсюду. Тролли Зул'Фаррака враждебны.
Неподалеку скрываются Пещеры Времени. Днем пустыня нещадно палит, но она же
приносит прибыль.""",

    16: """Азшара: разрушенное побережье ночных эльфов, пугающе прекрасное и
пустынное. Наги контролируют большую часть берега, а синие драконы
сохраняют здесь свое присутствие. Гигантские морские твари бродят вдоль
берега, а остатки Легиона задержались у Заброшенного Кряжа. Край кажется
покинутым и печальным — памятник тому, что было утрачено.""",

    361: """Оскверненный лес: испорченный лес, сочащийся демонической порчей.
Слизни, сатиры и оскверненная живность терзают каждый уголок. Сами деревья
выглядят больными. Фурболги Древобрюхов настороженны, но нейтральны;
фурболги Мертвого Леса враждебны. Край, от одного прохождения через который
чувствуешь себя нечистым.""",

    490: """Кратер Ун'Горо: доисторические джунгли в кратере, кишащие
динозаврами. Дьяволозавры — здешние хищники-вершины, ящеры охотятся стаями, а
элементали охраняют пилоны. Будто шаг назад во времени — пышно, опасно и
полно чудес. Кристаллические образования хранят таинственную силу.""",

    493: """Лунная поляна: священное святилище друидов. Здесь по большей
части мирно и безопасно, враждебных существ мало. Круг Кенария собирается
именно тут, а сам край кажется вневременным и безмятежным — передышкой от
хаоса внешнего мира. Друиды встречаются в Приюте Ночи.""",

    618: """Зимние Ключи: заснеженное нагорье вечной зимы. Ледопарды, йети и
ледяные великаны бродят по снегам. Круговзор — гоблинский городок сомнительных
делишек. Фурболги Морозной Чащи враждебны на всей территории. Прекрасно, но
смертельно холодно — край вознаграждает лишь хорошо подготовленных.""",

    1377: """Силитус: пустынная пустошь, кишащая силитидами. Угроза кираджи
нависает из Ан'Киража. Друиды Круга Кенария отчаянно бьются против роя.
Песчаные бури, гигантские насекомые и гнетущее ощущение, что под песками
шевелится нечто древнее и злое.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Полуостров Адского Пламени: разбитая красная пустошь, первый
край по ту сторону Темного Портала. Орки Скверны, демоны и силы Пылающего
Легиона повсюду. Оплот Чести и Траллмар — базы противостоящих фракций. Небо
разорвано, земля растрескалась, а война не утихает ни на миг. Жестокое
знакомство с Запредельем.""",

    3521: """Зангартопь: сюрреалистичное грибное болото, светящееся
биолюминесценцией. Гигантские грибы возвышаются над головой, споровые
летучие мыши лениво парят, а наги осушают воды. Кенарийское Пристанище
пытается спасти экосистему. Странно прекрасный, инопланетный край — здесь
ничто не похоже на Азерот.""",

    3518: """Награнд: парящие острова и пышные зеленые равнины — последний
райский уголок Запределья. Копытни и талбуки мирно пасутся, но огры и
Пылающий Клинок угрожают этой земле. Гарадар и Телаар олицетворяют
противостоящие фракции. Самый прекрасный край Запределья, напоминание о том,
каким Дренор был когда-то.""",

    3519: """Лес Тероккар: разделен между пышным лесом и усеянными костями
пустошами вокруг Аукиндона. Араккоа прячутся среди деревьев, а Совет Теней
проводит темные ритуалы. Шаттрат — нейтральная столица. Край контрастов
между жизнью и смертью.""",

    3522: """Острогорье: изрезанный, враждебный ландшафт из вздымающихся
шпилей. Здесь правят огры, а гронны-великаны — вершина хищной цепи.
Пылающий Легион удерживает здесь заставы, а над головой кружат драконы.
Опасная местность, где сама земля будто хочет тебя убить.""",

    3520: """Долина Призрачной Луны: темная, оскверненная Скверной пустошь.
Над всем нависает Черный Храм, а силы Иллидана контролируют регион. Демоны,
орки Скверны и рыцари смерти патрулируют округу. Небо горит зеленым. Самый
опасный и гнетущий край Запределья — здесь надежда кажется недосягаемой.""",

    3523: """Пустоверть: разбитые острова, парящие в Круговерти Пустоты.
Манагорны выкачивают энергию земли, эльфы крови и эфириалы борются за
ресурсы, а магические создания бродят где вздумается. Экокуполы искусственно
поддерживают жизнь. Край, разрывающий себя на части по швам.""",

    3524: """Остров Лазурной Дымки: безмятежный остров дренеев, пронизанный
мягким лазурным сиянием и гулом кристальных технологий. Место крушения
Экзодара все еще светится остаточной энергией, а выжившие дренеи залечивают
раны и отстраиваются заново. Кроткая живность, мерцающие озерца и
кристальные руины соседствуют здесь с обнадеживающим началом жизни
перемещенного народа, обретающего почву под ногами на новом мире.""",

    3525: """Остров Кровавой Дымки: остров-близнец Лазурной Дымки, окрашенный
багрянцем испорченными кристаллами с обломков Экзодара. Скверна исказила
местную живность в опасных хищников и изуродовала растительность. Эльфы
крови и демоны трудятся над дальнейшим осквернением земли. Место красоты,
обернувшейся зловещей — здесь дренеям приходится расхлебывать последствия
крушения собственного корабля.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Борейская тундра: замерзшая прибрежная тундра, одна из двух
точек входа в Нордскол. Нерубианцы роют туннели под землей, Плеть
прощупывает оборону, а клыкарры промышляют рыбной ловлей на побережье.
Крепость Песни Войны и Оплот Доблести — опорные пункты противостоящих
фракций. Холод здесь кусается по-настоящему — и это лишь начало зимы.""",

    495: """Ревущий фьорд: живописное побережье в духе викингов с высокими
утесами. Воины-врайкулы совершают набеги из своих деревень, а Плеть
поднимает мертвецов. Валгард и Уступ Возмездия — места высадки. Фьорды
захватывают дух, но врайкулы неумолимы.""",

    394: """Седые холмы: лесистый пограничный край, почти умиротворяющий.
Фурболги, испорченные Плетью, железные дворфы, копающиеся в поисках тайн, и
расползающееся проклятие воргенов. Лесозаготовки уродуют склоны холмов. Край,
что был бы прекрасен, если бы не подступающая порча.""",

    3711: """Низина Шолазар: пышные джунгли в кратере, не тронутые Плетью и
поддерживаемые технологиями титанов. Динозавры, гориллы и экзотические твари
процветают здесь. Дети Бешеного Сердца и Оракулы ведут мелочную войну.
Неожиданный райский уголок в промерзшем Нордсколе — но что-то угрожает
пилонам.""",

    66: """Зул'Драк: замерзшее троллиное королевство на грани краха. Дреккари
приносят в жертву собственных богов в борьбе с Плетью. Нежить и отчаявшиеся
тролли сталкиваются повсюду. Край ощущается как наблюдение за гибелью целой
цивилизации — мрачный, холодный и безнадежный.""",

    67: """Грозовая Гряда: вздымающиеся заснеженные горы, хранящие тайны
титанов. Штормовые великаны, железные дворфы и протодраконы господствуют
здесь. Над всем нависает вход в Ульдуар. Сыны Ходира настороженно относятся
к чужакам. Эпический размах, суровые условия, древние тайны.""",

    210: """Ледяная Корона: владения Короля-лича. Нескончаемые армии нежити,
крепости-некрополи и сама Цитадель Ледяной Короны. Серебряный Авангард
держит здесь свой последний рубеж. Сам воздух кажется мертвым. Это конец
пути — победа или небытие.""",

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Штормград: величественная человеческая столица, отстроенная
заново после Первой войны. Над горизонтом возвышается огромный собор, каналы
вьются меж каменных кварталов, а Торговый квартал никогда не спит. Стражники
патрулируют повсюду. Гавань связывает город с дальними землями. Король Вариан
Ринн правит из Штормградской крепости. Город брусчатки, знамен и гражданской
гордости — сердце Альянса.""",

    1537: """Стальгорн: великий город дворфов, высеченный в сердце горы.
Огромная кузня из расплавленного металла господствует в центре, окруженная
Великой Кузней, где мастера-кузнецы день и ночь бьют молотами. Воздух теплый
и пахнет железом и элем. Туннели ведут в Военный квартал, квартал Мистиков и
к Подземному трамваю до Штормграда. Основательный, древний город, построенный
на века.""",

    1657: """Дарнас: безмятежная столица ночных эльфов на вершине мирового
древа Тельдрассил. Над головой смыкаются древние деревья, сквозь кроны
пробивается мягкий фиолетовый свет, а тихие озерца отражают звезды даже в
полдень. Храм Луны чтит Элуну. Друиды медитируют в Анклаве Кенария. Город
кажется вневременным и мирным, вдали от войн внизу — хотя этот покой более
хрупок, чем кажется.""",

    3557: """Экзодар: разбившийся межпространственный корабль дренеев, ныне
служащий их столицей. Кристальные пилоны гудят потусторонней энергией,
пурпурный и синий свет омывает геометрические коридоры, а в самом сердце
светится лучезарное святилище. Архитектура чужда и прекрасна одновременно —
нечто среднее между собором и звездолетом. Дренеи с тихим достоинством
продолжают свою жизнь, отстраиваясь после очередного долгого странствия.""",

    1637: """Оргриммар: суровая орочья столица, высеченная в красных
пустынных каньонах. Железные пики, боевые знамена и массивные врата
определяют облик города. Долина Силы гудит от ворчания тренирующихся воинов
и стука аукционного дома. Наследие Тралла ощущается повсюду. Город суров,
громок и без извинений агрессивен — крепость, построенная для народа, что
всегда готов к войне.""",

    1638: """Громовой Утес: столица тауренов, возведенная на высоких плато,
соединенных веревочными мостами над равнинами Мулгора. Ветер гуляет по
открытым платформам. Тотемы и шкуры украшают каждое строение. Возвышение
Старейшин принимает друидов, Возвышение Духов — жрецов. Кэрн Кровавое Копыто
правит с древней мудростью. Самая мирная столица Орды — небо, ветер, трава и
тихая сила древнего народа.""",

    1497: """Подгород: столица Отрекшихся под руинами Лордерона. Темный,
кольцевой город канализаций, где нежить проводит свое существование среди
зеленых слизистых каналов и мерцающих факелов. В Королевском квартале живет
Сильвана Ветрокрылая. Аптекари варят сомнительные зелья. Воздух здесь сырой,
холодный и слегка ядовитый. Мрачный, функциональный и тревожный — но дом для
тех, кому больше некуда идти.""",

    3487: """Луносвет: столица эльфов крови, наполовину отстроенная после
вторжения Плети. Действующая западная половина сияет багряными и золотыми
шпилями, чародейские стражи патрулируют безупречные улицы, а фонтаны текут
магической энергией. Восточные руины остаются незаживающим шрамом. Культура
синдорай ценит красоту, магию и изысканность. Элегантный город, скрывающий
глубокие раны и отчаянную зависимость от тайной силы.""",

    3703: """Шаттрат: нейтральный город дренеев в Лесу Тероккар, теперь
разделенный между Алдорами и Провидцами. Терраса Света в его центре сияет
светом наару. Беженцы со всего Запределья заполняют Нижний Город. И Альянс, и
Орда ходят по этим улицам в шатком перемирии. Космополитичный узел, где
смешиваются все расы — отчасти святилище, отчасти пороховая бочка политики.""",

    4395: """Даларан: летающий город магов, парящий над Лесом Хрустальной
Песни в Нордсколе. Фиолетовые шпили пронзают облака, магические обереги
мерцают на каждом углу, а Кирин-Тор правит из Аметистовой Цитадели. Обе
фракции держат здесь свои святилища для войны с Королем-личом. Порталы
связывают город со всеми крупными столицами. Город ученых, тайн и едва
сдерживаемой магической мощи, невероятным образом парящий в небе.""",
}

# French (frFR) zone flavor text -- translated from the
# ZONE_FLAVOR entries above, covering only the zone_ids present
# in ZONE_NAMES_FR (62 of ZONE_FLAVOR's 64 zone-ID keys; The
# Barrens/17 and Dalaran/4395 have no French zone name in
# ZONE_NAMES_FR and are intentionally left uncovered here, same
# as ZONE_FLAVOR_RU's scoping principle), not injected verbatim
# since the English text was leaking untranslated into French
# bot chat. Proper nouns reuse the community-sourced terms from
# ZONE_NAMES_FR where the zone/city is covered there (Ironforge
# -> Forgefer, Stormwind -> Hurlevent, etc.) -- same confidence
# tier as ZONE_NAMES_FR itself (community/wiki-sourced, not
# independently verified against official client DBC data,
# unlike ZONE_FLAVOR_RU's DBC-extracted ZONE_NAMES_RU base).
# Faction/creature-race names outside that dict use the
# standard French WoW-community terms (e.g. Defias Brotherhood
# -> Confrérie Defias, Scourge -> le Fléau, Forsaken ->
# Réprouvés); minor creature-race names with no well-established
# French term (troggs, kobolds, gnolls, furbolgs, murlocs, naga,
# quilboars, etc.) are left as commonly used in French WoW
# community discourse rather than invented ad hoc. Falls back to
# English ZONE_FLAVOR via get_zone_flavor() for any locale other
# than frFR/ruRU, or for the zones this dict doesn't cover.
ZONE_FLAVOR_FR = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Dun Morogh : hautes terres enneigées des nains autour de Forgefer. Des trogs ont
envahi les lieux depuis les profondeurs, et de hostiles trolls des glaces rôdent dans les
montagnes. La vallée de Coldridge est l'endroit où les jeunes nains et gnomes entament leur
voyage. L'air est vif, la bière est forte, et les montagnes résonnent de coups de feu et de
marteaux.""",

    12: """Forêt d'Elwynn : paisibles fermes humaines aux portes de Hurlevent, mais le trouble
couve sous la surface. Les mines grouillent de kobolds qui crient « pas toucher bougie »,
la Confrérie Defias menace les routes, et des gnolls pillent depuis les frontières.
L'auberge de Rive-d'Or est toujours animée. Une zone trompeusement calme où le danger guette.""",

    38: """Loch Modan : région montagneuse dominée par un immense lac. Trogs et kobolds
infestent le secteur, tandis que les nains de Fer noir sèment le trouble près du barrage.
Le grand barrage est une merveille d'ingénierie. Thelsamar est une ville tranquille de
chasseurs et de fouilleurs. Le paysage respire l'atmosphère rude d'une terre frontalière.""",

    40: """La Marche de l'Ouest : autrefois terres fertiles, aujourd'hui poussiéreuses et
abandonnées. La Confrérie Defias contrôle une grande partie de la région depuis sa base
cachée. Des fermiers sans-abri errent sur les routes, des gardiens de récolte mécaniques
patrouillent des champs vides, et des gnolls pillent les abords. La colline des Sentinelles
demeure le dernier bastion de l'ordre.""",

    44: """Les Carmines : territoire humain assiégé. Les orcs de la Roche noire déferlent des
montagnes, des gnolls errent librement, et la ville de Lakeshire tient désespérément bon.
Le pont est constamment menacé. Une zone qui ressemble à un front de guerre, où les
habitants se retrouvent pris entre deux feux.""",

    10: """Bois de la pénombre : forêt maudite, plongée en permanence dans une nuit
éternelle. Des morts-vivants errent dans les bois, des worgens hurlent dans l'obscurité, et
d'immenses araignées guettent partout. La Garde de Nuit de Sombrelune contient à peine ces
horreurs. Une zone troublante où quelque chose de terrible s'est produit et où la terre ne
s'en est jamais remise.""",

    11: """Les Paluns : marécages détrempés reliant les terres naines à Lordaeron. Des
crocolisques et raptors hostiles pullulent partout, les nains de Fer noir complotent dans
les collines, et des draconiens menacent depuis le nord-est. Port-Menethil est une ville
portuaire trempée de pluie. Tout ici est humide et un peu misérable.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Clairières de Tirisfal : forêt hantée entourant les Fossoyeuses. La terre
elle-même semble malade — arbres chétifs, brume verte et morts-vivants agités. Les zélotes
de la Croisade écarlate traquent tout ce qui est mort-vivant, tandis que des zombies
hébétés et des chauves-souris errent librement. Brill est une ville sinistre des
Réprouvés. L'atmosphère est gothique et mélancolique.""",

    130: """Forêt des Pins argentés : bois sombres et brumeux au sud de Tirisfal. Les
worgens ont envahi une grande partie de la forêt, et la présence du Fléau persiste. La
Citadelle de Croc-Ombrageux se dresse, menaçante. Les Réprouvés se battent pour chaque
pouce de territoire. Une zone prise entre plusieurs menaces, qui semble isolée et
dangereuse.""",

    267: """Contreforts de Hautebrande : terres fermières disputées où la Horde et
l'Alliance s'affrontent ouvertement. Rives-Australes et Moulin-Taure sont en conflit
permanent. Des yétis rôdent dans les montagnes, et les bandits du Syndicat causent des
ennuis. Une zone définie par la guerre des factions et de vieilles rancunes.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """Les Hinterlands : hautes terres boisées et reculées, foyer des nains
Marteau-hardi et des trolls des forêts pris dans un conflit éternel. Loups et chouettes
géantes parcourent ces contrées sauvages. Pic-de-l'Aire se dresse au sommet d'une falaise
massive. La zone semble indomptée et loin de toute civilisation.""",

    45: """Hautes-terres d'Arathi : prairies vallonnées parsemées de ruines antiques. Le
Syndicat contrôle les ruines de Stromgarde, des ogres habitent les grottes, et des
raptors chassent dans les plaines. Pointe-du-Refuge et Hammerfall s'observent avec
méfiance. Une zone frontalière balayée par le vent, hantée par l'écho de royaumes déchus.""",

    33: """Vallée de Strangleronce : jungle dense et dangereuse, grouillante de vie. Trolls,
pirates, raptors, tigres et gorilles partout. Baie-du-Butin est un port gobelin sans loi
où tout est permis. L'expédition de chasse de Nesingwary attire les aventuriers. La zone
est magnifique mais mortelle — quelque chose veut vous dévorer à chaque détour.""",

    3: """Terres Ingrates : désert âpre et aride de roche rouge et de poussière. Trogs,
coyotes et dragonnets noirs hostiles rendent le voyage périlleux. Des sites
archéologiques épars laissent deviner d'anciens secrets. Kargath est un rude avant-poste
de la Horde. Une zone qui semble désolée et impitoyable.""",

    8: """Marais des chagrins : marécage sombre et déprimant. Des Éperdus errent sans but,
des jaguars traquent dans les eaux, et le Temple d'Atal'Hakkar attire de sombres
adorateurs. Tout ici est mouillé, boueux et légèrement désespéré. Un coin oublié du
monde.""",

    4: """Terres Foudroyées : terre balafrée, corrompue par les énergies de la Porte des
Ténèbres. Démons, faune mutée et créatures démoniaques errent librement. Le sol lui-même
semble contre nature. La forteresse de Nethergarde surveille la Porte avec nervosité. Une
zone qui semble être le bout du monde, là où tout a mal tourné.""",

    51: """Gorge des Vents brûlants : terre volcanique désolée sous le contrôle des nains
de Fer noir. Coulées de lave, élémentaires de feu et fosses de scories dominent le
paysage. Pointe-du-Thorium est un petit avant-poste de résistance. Une chaleur brutale et
un ravage industriel.""",

    46: """Steppes ardentes : les orcs de la Roche noire et les dragons noirs règnent sur
cette terre calcinée. Le Pic de la Roche noire domine les environs. Élémentaires de feu et
draconiens patrouillent. Une zone de guerre de haut niveau où la Horde noire rassemble ses
forces.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Maleterres de l'Ouest : terres fermières malades, grouillantes de morts-vivants.
Andorhal est une cité en ruines disputée par plusieurs factions. La présence du Fléau est
lourde, et les chaudrons répandent la peste sur la terre. La Croisade écarlate se bat
avec un acharnement fanatique. Une zone de mort, de maladie et de luttes désespérées.""",

    139: """Maleterres de l'Est : le cœur des terres du Fléau. Des morts-vivants partout —
goules, abominations, nécromanciens. Stratholme brûle éternellement, Naxxramas plane
au-dessus. La Chapelle de l'Espoir de la Lumière est le dernier rempart de l'humanité. La
zone la plus corrompue et dangereuse du continent. L'espoir y est rare.""",

    41: """Défilé de Deuillevent : canyon désolé menant à Karazhan. Des ogres de
Deuillevent se tapissent dans les grottes, des esprits agités errent, et la corruption
démoniaque suinte de la tour. La terre elle-même semble vidée de toute vie. Sinistre,
vide et menaçant — quelque chose de terrible s'est produit ici.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Teldrassil : immense arbre-monde, foyer des elfes de la nuit. Malgré quelques
ennuis avec les farfadets Griffe-Noueuse et les entrelaceurs hostiles, la forêt demeure
d'une beauté à couper le souffle — les arbres anciens rougeoient doucement au crépuscule,
des clairières sacrées scintillent d'une magie persistante, et de tranquilles clairières
invitent à la réflexion. Darnassus repose sereinement au-dessus de la canopée. L'air
porte les murmures d'une magie ancienne. Les elfes de la nuit vaquent à leurs occupations
quotidiennes : entraînement, artisanat, entretien des jardins. Un lieu où la beauté de la
nature persiste même face aux menaces auxquelles les aventuriers doivent faire face.""",

    148: """Sombrivage : long littoral brumeux où le brouillard roule depuis la mer,
créant une atmosphère éthérée. D'anciennes ruines des elfes de la nuit recèlent des
mystères et des légendes oubliées. Auberdine grouille de voyageurs prenant le bateau
pour Teldrassil, Hurlevent ou l'Île de Brume-Azur. Des pêcheurs travaillent sur les
quais, des aventuriers échangent des histoires à l'auberge. Certes, murlocs et naga
sèment le trouble sur les plages, et une partie de la faune est devenue agressive — mais
la beauté envoûtante du littoral demeure. Rivages baignés de lune, architecture antique,
bruit des vagues. Une zone de contrastes : ports paisibles et étendues sauvages
dangereuses, magie ancienne et menaces nouvelles.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Durotar : désert rocailleux et âpre, foyer des orcs. Scorpides, raptors et
sangliers parcourent les canyons rouges. Les quilbêtes pillent depuis le sud, et des
cultistes de la Lame ardente se cachent dans les grottes. Les portes d'Orgrimmar
accueillent les guerriers. Une zone qui incarne la force de la Horde face à l'adversité.""",

    215: """Mulgore : plaines paisibles et vallonnées des taurens. Les kodos paissent
tranquillement, mais des harpies fondent des montagnes et les gobelins de la Compagnie
d'Expédition exploitent la terre. Les Pitons-du-Tonnerre s'élèvent sur leurs mesas. La
zone la plus sereine de la Horde — vastes cieux et vents doux, bien que le danger guette
aux frontières.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    331: """Ashenvale : forêt ancienne des elfes de la nuit assiégée. La Horde progresse
depuis l'est, des démons se tapissent dans les ombres, et les farfadets ont sombré dans
la folie. Astranaar et l'avant-poste de l'Arbre-Fendu incarnent le conflit des factions.
Une belle forêt marquée par la guerre et la corruption.""",

    405: """Desolace : désolation grise et aride. Les tribus centaures se font
inlassablement la guerre entre elles et à tout le reste. Des cimetières de kodo
parsèment le paysage. La zone semble vide et sans espoir — même le ciel semble privé de
couleur. L'un des endroits les plus déprimants d'Azeroth.""",

    400: """Mille pointes : canyon spectaculaire d'imposants pics rocheux. Avant le
Cataclysme, un fond désertique aride avec le circuit des Plaines Scintillantes. Centaures
et harpies contrôlent divers piliers. Le Grand Ascenseur relie la zone aux Tarides.
Visuellement saisissant mais rude à traverser.""",

    15: """Marécage d'Aprefange : marécage chaud et humide. Des dragons noirs complotent
au sud, crocolisques et araignées hostiles se tapissent dans la vase, et Theramore se
dresse en bastion de l'Alliance. Les ruines d'une auberge incendiée laissent deviner de
sombres complots. Étouffant et dangereux.""",

    357: """Feralas : jungle et forêt luxuriante et envahissante. Yétis dans les
montagnes, naga sur la côte, ogres et gnolls partout. Les Jumeaux Colossaux sont
d'immenses arbres, et les ruines de Dfirmaul se dressent au loin. Une zone sauvage et
indomptée qui engloutit les voyageurs.""",

    440: """Tanaris : désert brûlant entourant le port gobelin de Gadgetzan. Pirates,
bandits, basilics et silithides partout. Les trolls de Zul'Farrak sont hostiles. Les
Cavernes du Temps se cachent à proximité. Torride le jour, ce désert est impitoyable
mais rentable.""",

    16: """Azshara : littoral en ruines des elfes de la nuit, d'une beauté envoûtante mais
désert. Les naga contrôlent une grande partie de la côte, et le clan draconique Bleu y
maintient une présence. D'immenses créatures marines rôdent, et des vestiges de la
Légion s'attardent au Rebord de l'Oubli. La zone semble abandonnée et triste — un
monument à ce qui a été perdu.""",

    361: """Gangrebois : forêt corrompue suintant de souillure démoniaque. Limons, satyres
et faune corrompue infestent chaque recoin. Les arbres eux-mêmes semblent malades. Les
farfadets Poil-des-Bois se méfient mais restent neutres ; les farfadets Bois-mort sont
hostiles. Une zone qui donne l'impression de se salir rien qu'en la traversant.""",

    490: """Cratère d'Un'Goro : jungle préhistorique en cratère grouillant de dinosaures.
Les diablosaures sont les prédateurs suprêmes, les raptors chassent en meute, et des
élémentaires gardent des pylônes. C'est comme remonter le temps — luxuriant, dangereux
et plein d'émerveillement. Des formations cristallines recèlent un pouvoir mystérieux.""",

    493: """Reflet-de-Lune : sanctuaire sacré des druides. Largement paisible et sûr, avec
peu de créatures hostiles. Le Cercle Cénarien s'y rassemble, et la zone semble
intemporelle et sereine — un répit loin du chaos du monde. Les druides se retrouvent à
Havre-Nocturne.""",

    618: """Berceau-de-l'Hiver : hautes terres gelées d'un hiver éternel. Chats-frimas,
yétis et géants de glace parcourent la neige. Guet-Nordique est une ville gobeline aux
affaires douteuses. Les farfadets Feuille-de-Givre sont hostiles sur tout le territoire.
Magnifique mais mortellement froid, la zone ne récompense que les bien préparés.""",

    1377: """Silithus : désert désolé grouillant de silithides. La menace qiraji plane
depuis Ahn'Qiraj. Les druides du Cercle Cénarien luttent désespérément contre l'essaim.
Tempêtes de sable, insectes géants et une sensation écrasante que quelque chose d'ancien
et de maléfique s'agite sous les sables.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Péninsule des Flammes Infernales : terre rouge brisée, première zone
franchie après la Porte des Ténèbres. Orcs corrompus, démons et forces de la Légion
ardente partout. Fort de l'Honneur et Thrallmar sont les bases des factions. Le ciel est
déchiré, le sol est fissuré, et la guerre fait rage sans relâche. Une introduction
brutale à l'Outreterre.""",

    3521: """Marécage de Zangar : marais champignonnesque surréaliste, luisant de
bioluminescence. D'immenses champignons dominent les lieux, des sporebêtes volent
paresseusement, et les naga drainent les eaux. Le Refuge Cénarien œuvre à sauver
l'écosystème. Étrangement magnifique et étranger — rien ici ne ressemble à Azeroth.""",

    3518: """Nagrand : îles flottantes et plaines vertes luxuriantes — le dernier paradis
de l'Outreterre. Fendragons et talbukins paissent paisiblement, mais des ogres et la Lame
ardente menacent cette terre. Garadar et Telaar incarnent les factions. La plus belle
zone de l'Outreterre, un rappel de ce que le Dranor fut jadis.""",

    3519: """Forêt de Terokkar : partagée entre forêt luxuriante et étendues jonchées
d'ossements autour d'Auchindoun. Des arakkoas se tapissent dans les arbres, et le Conseil
des Ombres mène de sombres rituels. Shattrath est la capitale neutre. Une zone de
contrastes entre vie et mort.""",

    3522: """Les Tranchantes : paysage escarpé et hostile de pics vertigineux. Les ogres y
règnent, et les géants gronn sont les prédateurs suprêmes. La Légion ardente y maintient
des avant-postes, et des dragons décrivent des cercles au-dessus. Un terrain dangereux où
la terre elle-même semble vouloir vous tuer.""",

    3520: """Vallée d'Ombrelune : terre sombre, corrompue par la Légion. Le Temple noir se
dresse, menaçant, et les forces d'Illidan contrôlent la région. Démons, orcs corrompus et
chevaliers de la mort patrouillent. Le ciel brûle d'un vert malsain. La zone la plus
dangereuse et oppressante de l'Outreterre — l'espoir y semble lointain.""",

    3523: """Raz-de-néant : îles brisées flottant dans le Néant Distordu. Des forges de
mana récoltent l'énergie de la terre, elfes de sang et éthérés se disputent les
ressources, et des créatures de mana errent en liberté. Les éco-dômes préservent la vie
artificiellement. Une zone qui se déchire elle-même aux coutures.""",

    3524: """Île de Brume-Azur : île paisible des draeneï, baignée d'une douce lumière
azur et du bourdonnement de la technologie cristalline. Le site du crash de l'Exodar
luit encore d'une énergie résiduelle, et les survivants draeneï pansent leurs blessures
et rebâtissent. Faune douce, bassins scintillants et ruines cristallines côtoient les
débuts pleins d'espoir d'un peuple déplacé qui reprend pied dans un monde nouveau.""",

    3525: """Île de Brume-Sang : île jumelle de Brume-Azur, teintée de rouge par les
cristaux corrompus de l'épave de l'Exodar. L'énergie démoniaque a transformé la faune
locale en prédateurs dangereux et muté la végétation. Elfes de sang et démons œuvrent à
corrompre davantage la terre. Un lieu de beauté devenu sinistre, où les draeneï doivent
affronter les dégâts causés par le crash de leur propre vaisseau.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Toundra Boréenne : toundra côtière gelée, l'un des deux points d'entrée au
Norfendre. Des nérubiens creusent sous terre, le Fléau sonde les défenses, et des tuskarr
pêchent le long des côtes. Fort-Chant-de-Guerre et Fort Valeur sont les bastions des
factions. Le froid mord fort — et l'hiver ne fait que commencer.""",

    495: """Fjord Hurlant : littoral spectaculaire d'inspiration viking aux falaises
imposantes. Des guerriers vrykuls attaquent depuis leurs villages, et le Fléau corrompt
les morts. Valgarde et le Débarcadère de la Vengeance sont les points d'accostage. Les
fjords coupent le souffle mais les vrykuls sont implacables.""",

    394: """Les Grisonnes : frontière boisée presque paisible. Farfadets corrompus par le
Fléau, nains de fer fouillant pour des secrets, et la malédiction des worgens qui se
propage. Des exploitations forestières balafrent les collines. Une zone qui serait belle
sans la corruption rampante.""",

    3711: """Bassin de Sholazar : jungle luxuriante en cratère, épargnée par le Fléau et
entretenue par la technologie des titans. Dinosaures, gorilles et bêtes exotiques y
prospèrent. Les Cœurs Frénétiques et les Oracles se livrent une guerre mesquine. Un
paradis inattendu dans le Norfendre glacé — mais quelque chose menace les pylônes.""",

    66: """Zul'Drak : royaume troll gelé en pleine chute. Les Drakkari sacrifient leurs
propres dieux pour combattre le Fléau. Morts-vivants et trolls désespérés s'affrontent
partout. La zone donne l'impression d'assister à l'agonie d'une civilisation — sombre,
froide et sans espoir.""",

    67: """Pics Foudroyés : montagnes gelées et imposantes, gardiennes des secrets des
titans. Géants des tempêtes, nains de fer et proto-drakes y dominent. L'entrée d'Ulduar
se dresse au-dessus. Les Fils de Hodir se méfient des étrangers. Échelle épique,
conditions brutales, mystères anciens.""",

    210: """Couronne de Glace : le domaine du Roi-liche. Armées interminables de
morts-vivants, forteresses nécropoles et la Citadelle de la Couronne de Glace
elle-même. La Croisade argentée fait son dernier combat. L'air lui-même semble mort.
C'est le bout du chemin — victoire ou néant.""",

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Hurlevent : la grande capitale humaine, reconstruite après la Première
Guerre. La grande cathédrale domine l'horizon, les canaux serpentent entre les quartiers
de pierre, et le quartier marchand ne dort jamais. Des gardes patrouillent partout. Le
port relie la ville à des terres lointaines. Le roi Varian Wrynn règne depuis le Château
de Hurlevent. Une ville de pavés, de bannières et de fierté civique — le cœur de
l'Alliance.""",

    1537: """Forgefer : la grande cité naine taillée dans le cœur d'une montagne. Une
immense forge de métal en fusion domine le centre, entourée du quartier de la Grande
Forge où des maîtres forgerons martèlent jour et nuit. L'air est chaud et embaume le fer
et la bière. Des tunnels mènent au Quartier militaire, au Quartier mystique et au tramway
souterrain vers Hurlevent. Solide, ancienne, et bâtie pour durer toujours.""",

    1657: """Darnassus : la sereine capitale des elfes de la nuit, au sommet de
l'arbre-monde Teldrassil. D'anciens arbres se voûtent au-dessus, une douce lumière
violette filtre à travers la canopée, et des bassins immobiles reflètent les étoiles même
en plein midi. Le Temple de la Lune honore Elune. Les druides méditent dans l'Enclave
Cénarienne. La ville semble intemporelle et paisible, loin des guerres d'en bas — bien
que cette paix soit plus fragile qu'il n'y paraît.""",

    3557: """L'Exodar : le vaisseau interdimensionnel écrasé des draeneï, désormais
reconverti en leur capitale. Des pylônes de cristal bourdonnent d'une énergie
d'un autre monde, une lumière pourpre et bleue baigne des corridors géométriques, et un
sanctuaire radieux luit en son cœur. L'architecture est étrangère et magnifique — mi-
cathédrale, mi-vaisseau spatial. Les draeneï poursuivent leur vie avec une dignité
tranquille, se reconstruisant après un long voyage de plus.""",

    1637: """Orgrimmar : la brutale capitale orque taillée dans des canyons désertiques
rouges. Piques de fer, bannières de guerre et portes massives définissent l'horizon. La
Vallée de la Force résonne des grognements de guerriers en entraînement et du vacarme de
l'hôtel des ventes. L'héritage de Thrall imprègne l'air. La ville est brute, bruyante et
sans excuses agressive — une forteresse bâtie pour un peuple qui s'attend toujours à la
guerre.""",

    1638: """Pitons-du-Tonnerre : la capitale taurène bâtie sur d'imposantes mesas reliées
par des ponts de corde au-dessus des plaines de Mulgore. Le vent balaie les plateformes
à ciel ouvert. Totems et peaux décorent chaque structure. L'Élévation des Anciens
accueille les druides, l'Élévation des Esprits les prêtres. Cairne Sabot-de-sang règne
avec une sagesse ancestrale. La capitale la plus paisible de la Horde — ciel, vent, herbe
et la force tranquille d'un peuple ancien.""",

    1497: """Les Fossoyeuses : la capitale des Réprouvés sous les ruines de Lordaeron.
Une cité souterraine sombre et circulaire où les morts-vivants mènent leur existence
parmi des canaux de vase verte et des torches vacillantes. Le Quartier royal abrite
Sylvanas Coursevent. Les apothicaires concoctent de douteux breuvages. L'air est humide,
froid et légèrement toxique. Sinistre, fonctionnelle et troublante — mais un foyer pour
ceux qui n'ont nulle part ailleurs où aller.""",

    3487: """Lune-d'Argent : la capitale des elfes de sang, à moitié reconstruite après
l'invasion du Fléau. La moitié occidentale, en activité, brille de flèches cramoisies et
dorées, des gardiens arcaniques patrouillent des rues impeccables, et des fontaines
coulent d'énergie magique. Les ruines orientales demeurent une cicatrice. La culture
sin'dorei prise la beauté, la magie et le raffinement. Une ville élégante masquant de
profondes blessures et une dépendance désespérée au pouvoir arcanique.""",

    3703: """Shattrath : la cité neutre des draeneï dans la Forêt de Terokkar, désormais
partagée entre les factions Aldor et Voyants. La Terrasse de Lumière brille en son
centre de la radiance des naaru. Des réfugiés venus de toute l'Outreterre affluent dans
la Cité basse. Alliance et Horde arpentent ces rues dans une trêve précaire. Un carrefour
cosmopolite où toutes les races se mêlent — mi-sanctuaire, mi-poudrière politique.""",
}

# German (deDE) zone flavor text -- translated from the
# ZONE_FLAVOR entries above, covering only the zone_ids present
# in ZONE_NAMES_DE (62 of ZONE_FLAVOR's 64 zone-ID keys; The
# Barrens/17 and The Exodar/3557 have no German zone name in
# ZONE_NAMES_DE and are intentionally left uncovered here, same
# as ZONE_FLAVOR_RU/ZONE_FLAVOR_FR's scoping principle), not
# injected verbatim since the English text was leaking
# untranslated into German bot chat. Proper nouns reuse the
# community-sourced terms from ZONE_NAMES_DE where the zone/city
# is covered there (Ironforge -> Eisenschmiede, Stormwind ->
# Sturmwind, etc.) -- same confidence tier as ZONE_NAMES_DE
# itself (community/wiki-sourced, not independently verified
# against official client DBC data, unlike ZONE_FLAVOR_RU's
# DBC-extracted ZONE_NAMES_RU base). Faction/creature-race names
# outside that dict use the standard official German WoW terms
# where one exists (e.g. Defias Brotherhood -> Bruderschaft der
# Defias, Scourge -> Geißel, Forsaken -> Verlassene, Scarlet
# Crusade -> Scharlachroter Kreuzzug, Cenarion Circle -> Zirkel
# des Cenarius, Burning Legion -> Brennende Legion); minor
# creature-race names with no well-established German term
# (troggs, kobolds, gnolls, furbolgs, murlocs, naga, quilboars,
# etc.) are left as commonly used in German WoW community
# discourse rather than invented ad hoc, same as ZONE_FLAVOR_FR's
# approach. Falls back to English ZONE_FLAVOR via
# get_zone_flavor() for any locale other than deDE/frFR/ruRU, or
# for the zones this dict doesn't cover.
ZONE_FLAVOR_DE = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Verschneites Zwergenhochland rund um Eisenschmiede. Troggs sind
aus dem Untergrund eingefallen, und feindselige Eistrolle streifen durch die Berge.
Im Kältenbachtal beginnen junge Zwerge und Gnome ihre Reise. Die Luft ist frisch,
das Bier ist stark, und die Berge hallen wider von Schüssen und Hammerschlägen.""",

    12: """Wald von Elwynn: Friedliches menschliches Ackerland vor den Toren
Sturmwinds, doch unter der Oberfläche braut sich Ärger zusammen. Die Minen wimmeln
von Kobolden, die "keine Kerze anfassen" kreischen, die Bruderschaft der Defias
bedroht die Straßen, und Gnolle plündern von den Rändern her. Die Taverne von
Goldhain ist immer belebt. Eine trügerisch ruhige Zone, in der Gefahr lauert.""",

    38: """Loch Modan: Ein gebirgiges Gebiet, beherrscht von einem gewaltigen See.
Troggs und Kobolde plagen die Gegend, während Dunkeleisenzwerge an der Talsperre
Ärger machen. Der große Staudamm ist ein technisches Meisterwerk. Thelsamar ist
ein ruhiges Städtchen der Jäger und Schürfer. Die Landschaft wirkt rau und wie an
der Grenze zur Wildnis.""",

    40: """Westfall: Einst fruchtbares Ackerland, heute staubig und verlassen. Die
Bruderschaft der Defias kontrolliert weite Teile der Region von ihrem verborgenen
Stützpunkt aus. Heimatlose Bauern ziehen über die Straßen, mechanische
Erntewächter patrouillieren leere Felder, und Gnolle plündern an den Rändern.
Sentinelhügel ist die letzte Bastion der Ordnung.""",

    44: """Rotkammgebirge: Ein belagertes menschliches Territorium. Orks vom
Schwarzfels strömen aus den Bergen herab, Gnolle streifen frei umher, und die
Stadt Seebruch hält verzweifelt stand. Die Brücke steht ständig unter Beschuss.
Eine Zone, die sich wie eine Kriegsfront anfühlt, mit Bürgern zwischen den
Fronten.""",

    10: """Dämmerwald: Ein von ewiger Nacht umhüllter, ständig dunkler, verfluchter
Wald. Untote wanken durch die Wälder, Worgen heulen in der Dunkelheit, und
riesige Spinnen lauern überall. Die Nachtwache von Düsterbruch hält die Schrecken
kaum in Schach. Eine unheimliche Zone, in der etwas Furchtbares geschah und das
Land sich nie erholt hat.""",

    11: """Sumpfland: Ein sumpfiges Marschland, das die Zwergenlande mit Lordaeron
verbindet. Feindselige Krokolisken und Echsen überall, Dunkeleisenzwerge schmieden
Ränke in den Hügeln, und aus dem Nordosten drohen Drachkin. Menethils Hafen ist
eine regennasse Hafenstadt. Hier ist alles feucht und ein wenig trübsinnig.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Tirisfal: Ein von Geistern heimgesuchter Wald rund um die Unterstadt.
Das Land selbst wirkt krank - kränkelnde Bäume, grüner Nebel und ruhelose Untote.
Fanatiker des Scharlachroten Kreuzzugs jagen alles Untote, während hirnlose
Zombies und Fledermäuse frei umherstreifen. Brill ist eine trostlose Stadt der
Verlassenen. Die Atmosphäre ist gotisch und melancholisch.""",

    130: """Silberwald: Dunkler, nebliger Wald südlich von Tirisfal. Worgen haben
weite Teile des Waldes überrannt, und die Präsenz der Geißel hält an. Die
Schattenfangfeste ragt bedrohlich empor. Die Verlassenen kämpfen um jeden
Zoll Boden. Eine Zone zwischen mehreren Bedrohungen, die sich abgeschnitten und
gefährlich anfühlt.""",

    267: """Vorgebirge des Hügellands: Umkämpftes Ackerland, in dem Horde und
Allianz offen aufeinandertreffen. Südbucht und Tarrens Mühle stehen in
ständigem Konflikt. Yetis streifen durch die Berge, und Banditen des Syndikats
sorgen für Ärger. Eine Zone, geprägt von Fraktionskrieg und alten Fehden.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """Hinterland: Abgelegenes, bewaldetes Hochland, Heimat der
Wildhammer-Zwerge und der Waldtrolle, die in ewigem Konflikt gefangen sind.
Wölfe und Eulenbestien streifen durch die Wildnis. Ährenspitze thront auf einer
gewaltigen Klippe. Die Zone wirkt ungezähmt und fern der Zivilisation.""",

    45: """Arathihochland: Sanfte Graslandschaften, übersät mit uralten Ruinen. Das
Syndikat kontrolliert die Ruinen von Stromgarde, Oger bewohnen die Höhlen, und
Echsen jagen auf den Ebenen. Zufluchtspunkt und Hammerfall beäugen sich
misstrauisch. Eine windgepeitschte Grenzzone mit dem Echo gefallener
Königreiche.""",

    33: """Schlingendorntal: Dichter, gefährlicher Dschungel, wimmelnd vor Leben.
Trolle, Piraten, Echsen, Tiger und Gorillas überall. Beutebucht ist ein
gesetzloser Goblinhafen, in dem alles erlaubt ist. Nesingwarys
Jagdexpedition zieht Abenteurer an. Die Zone ist wunderschön, aber tödlich -
hinter jeder Ecke lauert etwas, das dich fressen will.""",

    3: """Ödland: Karge, öde Wüste aus rotem Fels und Staub. Feindselige Troggs,
Kojoten und schwarze Drachenwelpen machen das Reisen gefährlich. Verstreute
archäologische Stätten deuten auf uralte Geheimnisse hin. Kargath ist ein
rauer Außenposten der Horde. Eine Zone, die trostlos und unerbittlich wirkt.""",

    8: """Sümpfe des Elends: Trübes, deprimierendes Sumpfland. Verlorene irren
ziellos umher, Jaguare lauern in den Gewässern, und der Tempel des
Atal'Hakkar zieht dunkle Anbeter an. Alles ist nass, schlammig und ein wenig
hoffnungslos. Ein vergessener Winkel der Welt.""",

    4: """Verwüstete Lande: Vernarbtes Ödland, verdorben von den Energien des
Dunklen Portals. Dämonen, mutierte Tierwelt und Teufelskreaturen streifen frei
umher. Der Boden selbst fühlt sich falsch an. Nethergardefeste beobachtet das
Portal nervös. Eine Zone, die sich wie der Rand der Welt anfühlt, wo alles
schiefgelaufen ist.""",

    51: """Sengende Schlucht: Vulkanisches Ödland unter der Kontrolle der
Dunkeleisenzwerge. Lavaströme, Feuerelementare und Schlackegruben beherrschen
die Landschaft. Thoriumpunkt ist ein kleiner Außenposten des Widerstands.
Brutal heiß und industriell verwüstet.""",

    46: """Brennende Steppe: Orks vom Schwarzfels und schwarze Drachen beherrschen
dieses versengte Land. Der Schwarzfelsgipfel ragt darüber empor. Feuerelementare
und Drachkin patrouillieren. Eine Kriegszone für hochstufige Abenteurer, in der
die Schwarze Horde ihre Kräfte sammelt.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Westliche Pestländer: Verseuchtes Ackerland, das vor Untoten wimmelt.
Andorhal ist eine zerstörte Stadt, um die mehrere Fraktionen kämpfen. Die
Präsenz der Geißel ist stark, und Kessel verbreiten die Pest über das Land.
Der Scharlachrote Kreuzzug kämpft fanatisch. Eine Zone des Todes, der
Krankheit und des verzweifelten Kampfes.""",

    139: """Östliche Pestländer: Das Kernland der Geißel. Untote überall -
Ghule, Abscheulichkeiten, Nekromanten. Stratholme brennt in Ewigkeit, Naxxramas
schwebt darüber. Die Kapelle der Hoffnung ist die letzte Bastion der
Menschheit. Die verdorbenste, gefährlichste Zone des Kontinents. Hoffnung ist
hier rar.""",

    41: """Gebirgspass der Totenwinde: Öde Schlucht, die zu Karazhan führt.
Oger der Totenwinde lauern in Höhlen, ruhelose Geister wandern umher, und
dämonische Verderbnis sickert aus dem Turm. Das Land selbst wirkt vom Leben
ausgesaugt. Gruselig, leer und unheilvoll - hier ist etwas Schreckliches
geschehen.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Teldrassil: Gewaltiger Weltenbaum, Heimat der Nachtelfen. Trotz
einiger Schwierigkeiten mit feindseligen Zottelpelz-Furbolgs und Holzknechten
bleibt der Wald atemberaubend schön - uralte Bäume leuchten sanft in der
Dämmerung, heilige Lichtungen schimmern von verbliebener Magie, und stille
Waldlichtungen laden zur Besinnung ein. Darnassus thront ruhig über dem
Blätterdach. Die Luft trägt das Flüstern alter Magie. Nachtelfen gehen ihrem
täglichen Leben nach: trainieren, arbeiten am Handwerk, pflegen Gärten. Ein Ort,
an dem die Schönheit der Natur fortbesteht, selbst während Abenteurer sich mit
Bedrohungen auseinandersetzen.""",

    148: """Dunkelküste: Lange, neblige Küstenlinie, über die Nebel vom Meer
hereinzieht und eine geisterhafte Atmosphäre schafft. Uralte Ruinen der
Nachtelfen bergen Geheimnisse und vergessenes Wissen. Auberdine ist voller
Reisender, die Schiffe nach Teldrassil, Sturmwind oder zur Azurmythosinsel
nehmen. Fischer arbeiten an den Docks, Abenteurer tauschen Geschichten in der
Taverne aus. Ja, Murlocs und Naga machen an den Stränden Ärger, und ein Teil
der Tierwelt ist verwildert - doch die eindringliche Schönheit der Küste bleibt
bestehen. Mondbeschienene Ufer, uralte Architektur, das Rauschen der Wellen.
Eine Zone der Gegensätze: friedliche Häfen und gefährliche Wildnis, alte Magie
und neue Bedrohungen.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Durotar: Karge, felsige Wüste, Heimat der Orcs. Skorpide, Echsen und
Wildschweine streifen durch die roten Canyons. Wildschweinmenschen greifen aus
dem Süden an, und Kultisten der Brennenden Klinge verstecken sich in Höhlen.
Die Tore von Orgrimmar heißen Krieger willkommen. Eine Zone, die die Stärke der
Horde durch Widrigkeiten verkörpert.""",

    215: """Mulgore: Friedliche, sanft geschwungene Ebenen der Tauren. Kodos
weiden gemächlich, doch Harpyien stürzen von den Bergen herab, und
Venture-Co.-Goblins beuten das Land aus. Donnerfels erhebt sich auf seinen
Tafelbergen. Die friedlichste Zone der Horde - weite Himmel und sanfte Winde,
auch wenn an den Rändern Gefahr lauert.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    331: """Eschental: Uralter Wald der Nachtelfen unter Belagerung. Die Horde
drängt von Osten herein, Dämonen lauern im Schatten, und Furbolgs sind dem
Wahnsinn verfallen. Astranaar und der Außenposten Splitterbaum stehen für den
Fraktionskonflikt. Ein wunderschöner Wald, gezeichnet von Krieg und Verderbnis.""",

    405: """Desolace: Karges, graues Ödland. Zentaurenstämme führen endlosen
Krieg gegeneinander und gegen alle anderen. Kodo-Friedhöfe säumen die
Landschaft. Die Zone wirkt leer und hoffnungslos - selbst der Himmel scheint
seiner Farbe beraubt. Einer der deprimierendsten Orte in Azeroth.""",

    400: """Tausend Nadeln: Dramatischer Canyon aus aufragenden Steinnadeln. Vor
dem Kataklysmus ein trockener Wüstenboden mit der Rennstrecke der Schimmernden
Tiefebene. Zentauren und Harpyien kontrollieren verschiedene Felssäulen. Der
Große Lift verbindet die Zone mit den Steppen. Optisch atemberaubend, aber
mühsam zu bereisen.""",

    15: """Düstermarschen: Heißes, feuchtes Sumpfland. Schwarze Drachen schmieden
Ränke im Süden, feindselige Krokolisken und Spinnen lauern im Morast, und
Theramore steht als Bastion der Allianz. Die Ruinen eines niedergebrannten
Gasthauses deuten auf dunklere Machenschaften hin. Drückend schwül und
gefährlich.""",

    357: """Feralas: Üppiger, überwucherter Dschungel und Wald. Yetis in den
Bergen, Naga an der Küste, Oger und Gnolle überall. Die Zwillingskolosse sind
gewaltige Bäume, und die Ruinen von Düsterbruch ragen groß auf. Eine wilde,
ungezähmte Zone, die Reisende verschlingt.""",

    440: """Tanaris: Glühend heiße Wüste rund um den Goblinhafen Gadgetzan.
Piraten, Banditen, Basilisken und Silithiden überall. Die Trolle von Zul'Farrak
sind feindselig. Die Höhlen der Zeit verbergen sich in der Nähe. Tagsüber
brütend heiß, doch die Wüste ist so unerbittlich wie einträglich.""",

    16: """Azshara: Zerstörte Küstenlinie der Nachtelfen, eindringlich schön,
doch leer. Naga kontrollieren weite Teile der Küste, und der blaue
Drachenschwarm behält hier seine Präsenz. Riesige Meereskreaturen streifen
umher, und Überreste der Legion verweilen am Verlorenen Grat. Die Zone wirkt
verlassen und traurig - ein Denkmal für das, was verloren ging.""",

    361: """Teufelswald: Verdorbener Wald, der von dämonischer Verderbnis trieft.
Schleime, Satyrn und verdorbene Tierwelt plagen jeden Winkel. Selbst die Bäume
wirken krank. Die Furbolgs vom Zottelklauenstamm sind wachsam, aber neutral;
die vom Totholzstamm sind feindselig. Eine Zone, nach deren Durchqueren man sich
unrein fühlt.""",

    490: """Krater von Un'Goro: Prähistorischer Dschungel in einem Krater,
wimmelnd vor Dinosauriern. Teufelssaurier sind die Spitzenprädatoren hier,
Echsen jagen in Rudeln, und Elementare bewachen Pylonen. Es fühlt sich an wie
ein Schritt zurück in der Zeit - üppig, gefährlich und voller Wunder.
Kristallformationen bergen geheimnisvolle Kraft.""",

    493: """Mondlichtung: Heiliges Heiligtum der Druiden. Größtenteils friedlich
und sicher, mit wenigen feindseligen Kreaturen. Der Zirkel des Cenarius
versammelt sich hier, und die Zone wirkt zeitlos und ruhig - eine Erholung vom
Chaos der Welt. Druiden treffen sich in Nachthafen.""",

    618: """Winterquell: Vereistes Hochland ewigen Winters. Frostsäbler,
Yetis und Eisriesen streifen durch den Schnee. Sturmschleier ist eine
Goblinstadt zweifelhafter Geschäfte. Furbolgs vom Winterfallstamm sind im
gesamten Gebiet feindselig. Wunderschön, aber tödlich kalt - die Zone belohnt
nur die gut Vorbereiteten.""",

    1377: """Silithus: Wüstenödland, das von Silithiden wimmelt. Die Bedrohung
durch die Qiraji droht aus Ahn'Qiraj. Druiden des Zirkels des Cenarius kämpfen
verzweifelt gegen den Schwarm. Sandstürme, riesige Insekten und das
überwältigende Gefühl, dass sich unter dem Sand etwas Uraltes und Böses
regt.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Höllenfeuerhalbinsel: Zerschmettertes rotes Ödland, die erste Zone
jenseits des Dunklen Portals. Teufelsorks, Dämonen und Streitkräfte der
Brennenden Legion überall. Ehrenfeste und Thrallmar sind die Stützpunkte der
Fraktionen. Der Himmel ist zerrissen, der Boden aufgerissen, und der Krieg
tobt ununterbrochen. Eine brutale Einführung in Outland.""",

    3521: """Zangarmarschen: Surreales Pilzsumpfland, das von Biolumineszenz
erstrahlt. Riesige Pilze ragen empor, Sporenfledermäuse gleiten träge dahin,
und Naga saugen die Gewässer aus. Die Zuflucht des Cenarius bemüht sich, das
Ökosystem zu retten. Seltsam schön und fremdartig - hier gleicht nichts
Azeroth.""",

    3518: """Nagrand: Schwebende Inseln und üppige grüne Ebenen - Outlands
letztes Paradies. Klauentiere und Talbuks weiden friedlich, doch Oger und die
Brennende Klinge bedrohen das Land. Garadar und Telaar stehen für die
Fraktionen. Die schönste Zone in Outland, eine Erinnerung daran, was Draenor
einst war.""",

    3522: """Schergrat: Zerklüftete, feindselige Landschaft aus aufragenden
Felsnadeln. Hier herrschen Oger, und Gronn-Riesen sind die Spitzenprädatoren.
Die Brennende Legion unterhält Außenposten, und Drachen kreisen darüber. Ein
gefährliches Terrain, in dem das Land selbst dich zu töten scheint.""",

    3519: """Wälder von Terokkar: Geteilt zwischen üppigem Wald und den
knochenübersäten Ödländern rund um Auchindoun. Arakkoa lauern in den Bäumen,
und der Schattenrat vollführt dunkle Rituale. Shattrath ist die neutrale
Hauptstadt. Eine Zone der Gegensätze zwischen Leben und Tod.""",

    3520: """Schattenmondtal: Dunkles, von der Legion verdorbenes Ödland. Der
Schwarze Tempel ragt bedrohlich empor, und Illidans Streitkräfte kontrollieren
die Region. Dämonen, Teufelsorks und Todesritter patrouillieren. Der Himmel
brennt grün. Die gefährlichste und bedrückendste Zone in Outland - Hoffnung
scheint hier fern.""",

    3523: """Nethersturm: Zerschmetterte Inseln, schwebend im Wirbel des
Nethers. Manaschmieden ernten die Energie des Landes, Blutelfen und Ätherwesen
konkurrieren um Ressourcen, und Manakreaturen streifen wild umher. Die
Öko-Kuppeln erhalten Leben künstlich aufrecht. Eine Zone, die sich selbst an
den Nähten auseinanderreißt.""",

    3524: """Azurmythosinsel: Ruhige Draenei-Insel, durchdrungen von sanftem
azurblauem Licht und dem Summen kristalliner Technologie. Die Absturzstelle des
Exodar glimmt noch von Restenergie, und überlebende Draenei versorgen ihre
Wunden und bauen wieder auf. Sanfte Tierwelt, schimmernde Teiche und
kristalline Ruinen teilen sich den Raum mit dem hoffnungsvollen Neubeginn eines
vertriebenen Volkes, das auf einer neuen Welt Fuß fasst.""",

    3525: """Blutmythosinsel: Schwesterinsel zur Azurmythosinsel, blutrot
gefärbt von verdorbenen Kristallen aus dem Wrack des Exodar. Die Verderbnis
hat die einheimische Tierwelt in gefährliche Raubtiere verwandelt und die
Vegetation mutieren lassen. Blutelfen und Dämonen arbeiten daran, das Land
weiter zu verderben. Ein Ort der Schönheit, ins Finstere gewendet, an dem die
Draenei den Schaden bewältigen müssen, den der Absturz ihres eigenen Schiffes
verursacht hat.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Boreanische Tundra: Vereiste Küstentundra, einer von zwei
Eingangspunkten nach Nordend. Nerubianer graben sich unter der Erde,
die Geißel testet die Verteidigung, und Tuskarr fischen an den Küsten.
Kriegsgesangsfeste und Feste der Tapferkeit sind die Stützpunkte der
Fraktionen. Die Kälte beißt hart zu - und der Winter fängt gerade erst an.""",

    495: """Der Heulende Fjord: Dramatische, von Wikingern inspirierte
Küstenlinie mit hoch aufragenden Klippen. Vrykul-Krieger überfallen aus ihren
Dörfern, und die Geißel verdirbt die Toten. Valgarde und die Rachelände sind
die Anlandepunkte. Die Fjorde sind atemberaubend, doch die Vrykul sind
unerbittlich.""",

    394: """Grizzlyhügel: Bewaldetes Grenzland, das fast friedlich wirkt. Von
der Geißel verdorbene Furbolgs, Eisenzwerge, die nach Geheimnissen graben, und
sich ausbreitender Worgenfluch. Holzfällerlager vernarben die Hänge. Eine
Zone, die schön wäre, wäre da nicht die vordringende Verderbnis.""",

    3711: """Sholazarbecken: Üppiger Dschungel in einem Krater, unberührt von
der Geißel und aufrechterhalten durch Titanentechnologie. Dinosaurier,
Gorillas und exotische Bestien gedeihen hier. Die Wildherzen und die Orakel
führen einen kleinlichen Krieg. Ein unerwartetes Paradies im gefrorenen
Nordend - doch etwas bedroht die Pylonen.""",

    66: """Zul'Drak: Vereistes Trollkönigreich im Zusammenbruch. Die Drakkari
opfern ihre eigenen Götter, um gegen die Geißel zu kämpfen. Untote und
verzweifelte Trolle stoßen überall aufeinander. Die Zone fühlt sich an wie das
Zusehen beim Sterben einer ganzen Zivilisation - düster, kalt und
hoffnungslos.""",

    67: """Die Sturmgipfel: Aufragende, vereiste Berge, Heimat der Geheimnisse
der Titanen. Sturmriesen, Eisenzwerge und Protodrachen beherrschen die
Gegend. Der Eingang zu Ulduar ragt darüber empor. Die Söhne Hodirs sind
Fremden gegenüber misstrauisch. Episches Ausmaß, brutale Bedingungen, uralte
Geheimnisse.""",

    210: """Eiskrone: Das Reich des Lichkönigs. Endlose Armeen der Untoten,
Nekropolen-Festungen und die Zitadelle der Eiskrone selbst. Der
Argentumkreuzzug leistet hier seinen letzten Widerstand. Die Luft selbst
scheint tot. Dies ist das Ende des Weges - Sieg oder Vernichtung.""",

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Sturmwind: Die prächtige menschliche Hauptstadt, wiederaufgebaut
nach dem Ersten Krieg. Die große Kathedrale beherrscht die Skyline, die Kanäle
schlängeln sich zwischen steinernen Vierteln, und das Handelsviertel schläft
nie. Wachen patrouillieren überall. Der Hafen verbindet die Stadt mit fernen
Ländern. König Varian Wrynn regiert von der Festung Sturmwind aus. Eine Stadt
aus Kopfsteinpflaster, Bannern und Bürgerstolz - das Herz der Allianz.""",

    1537: """Eisenschmiede: Die große Zwergenstadt, gehauen ins Herz eines
Berges. Eine gewaltige Schmiede aus geschmolzenem Metall beherrscht das
Zentrum, umgeben vom Bezirk der Großen Schmiede, wo Meisterschmiede Tag und
Nacht hämmern. Die Luft ist warm und riecht nach Eisen und Bier. Tunnel
verzweigen sich in den Militärring, den Ring der Mystiker und zur
Tiefenbahn nach Sturmwind. Solide, uralt und für die Ewigkeit gebaut.""",

    1657: """Darnassus: Die ruhige Hauptstadt der Nachtelfen auf der Spitze des
Weltenbaums Teldrassil. Uralte Bäume wölben sich über den Köpfen, sanftes
violettes Licht sickert durch das Blätterdach, und stille Teiche spiegeln die
Sterne selbst am Mittag. Der Tempel des Mondes ehrt Elune. Druiden meditieren
im Zirkel des Cenarius. Die Stadt wirkt zeitlos und friedlich, fern der Kriege
weiter unten - doch dieser Frieden ist brüchiger, als er scheint.""",

    1637: """Orgrimmar: Die brutale Orc-Hauptstadt, gehauen in rote
Wüstenschluchten. Eisenspitzen, Kriegsbanner und massive Tore prägen die
Skyline. Das Tal der Stärke hallt wider vom Grunzen trainierender Krieger und
dem Lärm des Auktionshauses. Thralls Vermächtnis liegt in der Luft. Die Stadt
ist roh, laut und unentschuldbar aggressiv - eine Festung, gebaut für ein
Volk, das den Krieg erwartet.""",

    1638: """Donnerfels: Die Hauptstadt der Tauren, erbaut auf hoch aufragenden
Tafelbergen, verbunden durch Seilbrücken hoch über den Ebenen von Mulgore. Der
Wind fegt über die offenen Plattformen. Totems und Häute schmücken jedes
Gebäude. Der Ältestenring beherbergt Druiden, der Geisterring die Priester.
Cairne Bluthuf regiert mit uralter Weisheit. Die friedlichste Hauptstadt der
Horde - Himmel, Wind, Gras und die stille Kraft eines uralten Volkes.""",

    1497: """Unterstadt: Die Hauptstadt der Verlassenen unter den Ruinen von
Lordaeron. Eine dunkle, kreisförmige Kanalisationsstadt, in der die Untoten
ihre Existenz zwischen grünen Schleimkanälen und flackernden Fackeln fristen.
Im Königlichen Viertel residiert Sylvanas Windläufer. Apotheker brauen
zweifelhafte Gebräue. Die Luft ist feucht, kalt und leicht giftig. Düster,
zweckmäßig und beunruhigend - doch eine Heimat für jene, die sonst nirgendwo
hin können.""",

    3487: """Silbermond: Die Hauptstadt der Blutelfen, halb wiederaufgebaut
nach der Invasion der Geißel. Die funktionierende westliche Hälfte erstrahlt
in purpurfarbenen und goldenen Türmen, arkane Wächter patrouillieren makellose
Straßen, und Brunnen fließen mit arkaner Energie. Die östlichen Ruinen bleiben
eine Narbe. Die Kultur der Sin'dorei schätzt Schönheit, Magie und
Raffinesse. Eine elegante Stadt, die tiefe Wunden und eine verzweifelte Sucht
nach arkaner Macht verbirgt.""",

    3703: """Shattrath: Die neutrale Draenei-Stadt im Wald von Terokkar, nun
geteilt zwischen den Aldor und den Sehern. Die Terrasse des Lichts erstrahlt
in ihrem Zentrum im Glanz der Naaru. Flüchtlinge aus ganz Outland drängen sich
in der Unterstadt. Sowohl Allianz als auch Horde wandeln auf diesen Straßen in
einem brüchigen Waffenstillstand. Ein kosmopolitisches Zentrum, in dem sich
alle Völker vermischen - halb Zufluchtsort, halb politisches Pulverfass.""",

    4395: """Dalaran: Die schwebende Magierstadt über dem Kristallsangwald in
Nordend. Violette Türme durchstoßen die Wolken, arkane Schutzzeichen
schimmern an jeder Ecke, und der Kirin Tor regiert von der Violetten
Zitadelle aus. Beide Fraktionen unterhalten hier Zufluchtsorte für den Krieg
gegen den Lichkönig. Portale verbinden die Stadt mit allen bedeutenden
Hauptstädten. Eine Stadt der Gelehrten, Geheimnisse und kaum gebändigter
magischer Macht, unglaublicherweise schwebend am Himmel.""",
}

# Spanish (esES) zone flavor text -- translated from the
# ZONE_FLAVOR entries above, scoped to the intersection of
# ZONE_FLAVOR's 64 zone-ID keys and ZONE_NAMES_ES's ~70 zone-ID
# keys (62 zones), not injected verbatim since the English text
# was leaking untranslated into Spanish bot chat. Two zones covered
# by ZONE_FLAVOR (Nagrand, Dalaran) have no Spanish name in
# ZONE_NAMES_ES to draw on (both are confirmed by ZONE_NAMES_ES's
# own comment to keep their English/original names in Spanish) and
# are intentionally omitted here, exactly mirroring
# ZONE_FLAVOR_FR/ZONE_FLAVOR_DE's 62/64 scoping. Proper nouns reuse
# the mixed-provenance terms from ZONE_NAMES_ES where the zone/city
# is covered there; faction/place names outside that dict use
# community-sourced Spanish WoW terminology (e.g. Defias Brotherhood
# -> Hermandad Defias, Scourge -> Flagelo, Scarlet Crusade ->
# Cruzada Escarlata, Syndicate -> Sindicato), same confidence tier
# as ZONE_FLAVOR_FR/ZONE_FLAVOR_DE's community-sourced approach, NOT
# independently verified against official client data. Falls back
# to English ZONE_FLAVOR via get_zone_flavor() for any locale other
# than esES/ruRU/frFR/deDE, or for zones this dict doesn't cover.
ZONE_FLAVOR_ES = {
    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Alliance Starting Zones
    # -------------------------------------------------------------------------
    1: """Dun Morogh: Tierras altas nevadas de los enanos que rodean Forjaz. Los troggs
han invadido desde las profundidades, y trols de hielo hostiles acechan en las
montañas. El Valle Cresta Fría es donde jóvenes enanos y gnomos comienzan su
viaje. El aire es fresco, la cerveza es fuerte, y las montañas resuenan con
disparos y martillazos.""",

    12: """Bosque de Elwynn: Tierras de labranza humanas y pacíficas a las afueras de
Ciudad de Ventormenta, pero los problemas se gestan bajo la superficie. Los
kobolds infestan las minas gritando "tú no tocar vela", la Hermandad Defias
amenaza los caminos, y los gnolls asaltan desde las fronteras. La posada de
Loma de Oro siempre está animada. Una zona engañosamente tranquila donde
acecha el peligro.""",

    38: """Loch Modan: Una región montañosa dominada por un enorme lago. Los troggs y
kobolds plagan la zona, mientras los enanos Hierro Negro causan problemas cerca
de la presa. La gran presa es una maravilla de la ingeniería. Thelsamar es un
pueblo tranquilo de cazadores y excavadores. El paisaje se siente agreste y
fronterizo.""",

    40: """Páramos de Poniente: Antaño fértiles tierras de labranza, ahora polvorientas
y abandonadas. La Hermandad Defias controla gran parte de la región desde su
base oculta. Granjeros sin hogar vagan por los caminos, vigías mecánicos de
la cosecha patrullan campos vacíos, y gnolls merodean por los límites. Colina
Centinela sigue siendo el último bastión del orden.""",

    44: """Montañas Crestagrana: Un territorio humano asediado. Los orcos de Roca Negra
descienden de las montañas, los gnolls campan a sus anchas, y el pueblo de
Lagoto resiste desesperadamente. El puente está siempre bajo amenaza. Una
zona que se siente como un frente de guerra, con ciudadanos atrapados en
el fuego cruzado.""",

    10: """Bosque del Ocaso: Un bosque perpetuamente oscuro y maldito, envuelto en
noche eterna. Los no-muertos deambulan entre los árboles, los worgen aúllan
en la oscuridad, y arañas gigantes acechan por doquier. La Guardia Nocturna
de Los Sombríos apenas contiene los horrores. Una zona inquietante donde algo
terrible ocurrió y la tierra nunca se recuperó.""",

    11: """Los Humedales: Marismas empapadas que conectan las tierras enanas con
Lordaeron. Crocolisks y raptores hostiles por todas partes, los enanos Hierro
Negro conspiran en las colinas, y dragontes amenazan desde el noreste. El
Puerto de Menethil es una ciudad portuaria empapada de lluvia. Todo aquí está
húmedo y algo desdichado.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Horde Starting Zones
    # -------------------------------------------------------------------------
    85: """Claros de Trisfal: Bosque encantado que rodea Entrañas. La propia tierra se
siente enferma - árboles enfermizos, niebla verde, y no-muertos inquietos.
Los fanáticos de la Cruzada Escarlata cazan cualquier cosa no-muerta,
mientras zombis sin mente y murciélagos deambulan libremente. Brill es un
pueblo sombrío de los Renegados. La atmósfera es gótica y melancólica.""",

    130: """Bosque de Argénteos: Bosques oscuros y brumosos al sur de Trisfal. Los
worgen han invadido gran parte del bosque, y persiste la presencia del
Flagelo. La Fortaleza de Colmillo Sombrío se alza amenazante. Los Renegados
luchan por cada palmo de territorio. Una zona atrapada entre múltiples
amenazas, que se siente aislada y peligrosa.""",

    267: """Laderas de Trabalomas: Tierras de labranza disputadas donde la Horda y
la Alianza chocan abiertamente. Bahía del Sur y Molino Tarren están en
constante conflicto. Los yetis rondan las montañas, y los bandidos del
Sindicato causan problemas. Una zona definida por la guerra de facciones y
viejos rencores.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Mid-Level Zones
    # -------------------------------------------------------------------------
    47: """Tierras del Interior: Remotas tierras altas boscosas, hogar de los enanos
Martillo Salvaje y los trols del bosque, atrapados en un conflicto eterno.
Lobos y bestias búho rondan la espesura. Cima del Águila se asienta sobre
un acantilado imponente. La zona se siente indómita y alejada de la
civilización.""",

    45: """Tierras Altas de Arathi: Praderas onduladas salpicadas de ruinas
antiguas. El Sindicato controla las ruinas de Stromgarde, ogros habitan
las cuevas, y raptores cazan en las llanuras. Punto de Refugio y Marfil
se vigilan mutuamente con recelo. Una zona fronteriza azotada por el
viento con ecos de reinos caídos.""",

    33: """Vega de Tuercespina: Selva densa y peligrosa rebosante de vida. Trols,
piratas, raptores, tigres y gorilas por todas partes. Bahía del Botín es
un puerto goblin sin ley donde todo vale. La expedición de caza de
Nesingwary atrae a aventureros. La zona es hermosa pero mortal - algo
quiere devorarte en cada esquina.""",

    3: """Tierras Inhóspitas: Desierto árido y hostil de roca roja y polvo. Troggs
hostiles, coyotes y crías de dragón negro hacen peligroso el viaje.
Sitios arqueológicos dispersos insinúan secretos antiguos. Kargath es un
tosco puesto avanzado de la Horda. Una zona que se siente desolada e
implacable.""",

    8: """Pantano de las Penas: Turbio y deprimente pantano. Los perdidos deambulan
sin rumbo, jaguares acechan en las aguas, y el Templo de Atal'Hakkar
atrae a oscuros adoradores. Todo está mojado, embarrado y algo
desesperanzado. Un rincón olvidado del mundo.""",

    4: """Las Tierras Devastadas: Tierra baldía marcada por cicatrices, corrompida
por las energías del Portal Oscuro. Demonios, fauna mutada y criaturas
corrompidas por el vil deambulan libremente. El propio suelo se siente
mal. La Fortaleza Guardia Norte vigila el Portal con nerviosismo. Una
zona que se siente como el borde del mundo, donde todo salió mal.""",

    51: """La Garganta de Fuego: Tierra baldía volcánica controlada por los enanos
Hierro Negro. Ríos de lava, elementales de fuego y fosas de escoria
dominan el paisaje. Puesto Torio es un pequeño enclave de resistencia.
Brutalmente caluroso y devastado por la industria.""",

    46: """Las Estepas Ardientes: Orcos de Roca Negra y dragones negros gobiernan
esta tierra calcinada. La Cima de Roca Negra se alza sobre el paisaje.
Elementales de fuego y dragontes patrullan. Una zona de guerra de alto
nivel donde la Horda Oscura reúne sus fuerzas.""",

    # -------------------------------------------------------------------------
    # Eastern Kingdoms - Plaguelands
    # -------------------------------------------------------------------------
    28: """Tierras de la Peste del Oeste: Tierras de labranza enfermas plagadas de
no-muertos. Andorhal es una ciudad en ruinas disputada por múltiples
facciones. La presencia del Flagelo es intensa, y los Calderos esparcen
la peste por la tierra. La Cruzada Escarlata lucha con fanatismo. Una
zona de muerte, enfermedad y luchas desesperadas.""",

    139: """Tierras de la Peste del Este: El corazón del Flagelo. No-muertos por
todas partes - carroñeros, abominaciones, nigromantes. Stratholme arde
eternamente, Naxxramas flota en lo alto. La Capilla de la Esperanza de
la Luz es el último bastión de la humanidad. La zona más corrompida y
peligrosa del continente. Aquí la esperanza escasea.""",

    41: """Paso de la Muerte: Cañón desolado que conduce a Karazhan. Ogros de
Paso de la Muerte acechan en las cuevas, espíritus inquietos deambulan,
y la corrupción demoníaca se filtra desde la torre. La propia tierra se
siente drenada de vida. Espeluznante, vacía y ominosa - algo terrible
ocurrió aquí.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Alliance Starting Zones
    # -------------------------------------------------------------------------
    141: """Teldrassil: Un inmenso árbol del mundo, hogar de los elfos de la
noche. A pesar de algunos problemas con furbolgs Zarpa Retorcida y
elementales de madera hostiles, el bosque sigue siendo de una belleza
sobrecogedora - árboles antiguos que brillan suavemente al atardecer,
claros sagrados que resplandecen con magia persistente, y quietos
claros que invitan a la reflexión. Darnassus se asienta serenamente
sobre el dosel. El aire lleva susurros de magia antigua. Los elfos de
la noche siguen con su vida diaria: entrenan, elaboran, cuidan jardines.
Un lugar donde la belleza de la naturaleza persiste incluso mientras
los aventureros lidian con amenazas.""",

    148: """Costa Oscura: Una costa larga y brumosa donde la niebla llega desde el
mar, creando una atmósfera etérea. Ruinas antiguas de los elfos de la
noche guardan misterios y sabiduría olvidada. Auberdine bulle de
viajeros que toman barcos hacia Teldrassil, Ciudad de Ventormenta o
Isla Bruma Azur. Los pescadores trabajan en los muelles, los
aventureros comparten historias en la posada. Sí, los murlocs y los
naga causan problemas en las playas, y algo de la vida salvaje se ha
vuelto agresiva - pero la inquietante belleza del litoral perdura.
Costas iluminadas por la luna, arquitectura antigua, el sonido de las
olas. Una zona de contrastes: puertos apacibles y tierras salvajes
peligrosas, magia antigua y nuevas amenazas.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Horde Starting Zones
    # -------------------------------------------------------------------------
    14: """Durotar: Desierto rocoso y hostil, hogar de los orcos. Escórpidos,
raptores y jabalíes rondan los cañones rojos. Los quilboar asaltan desde
el sur, y cultistas de la Hoja Ardiente se ocultan en cuevas. Las
puertas de Orgrimmar dan la bienvenida a los guerreros. Una zona que
encarna la fuerza de la Horda frente a la adversidad.""",

    215: """Mulgore: Llanuras onduladas y pacíficas de los tauren. Los kodo pastan
plácidamente, pero las arpías descienden en picado desde las montañas
y los goblins de la Compañía Venture explotan la tierra. Cima del
Trueno se alza sobre sus mesetas. La zona de la Horda más serena -
cielos amplios y vientos suaves, aunque el peligro acecha en los
bordes.""",

    # -------------------------------------------------------------------------
    # Kalimdor - Mid-Level Zones
    # -------------------------------------------------------------------------
    17: """Los Baldíos: Vasta y árida sabana que se extiende sin fin. Centauros,
quilboar, raptores, leones y zhevras por todas partes. La Encrucijada
es un importante centro donde se reúnen los aventureros. Conocida por
sus largos tiempos de viaje y su memorable chat general. Una
experiencia definitoria del ascenso de nivel de la Horda.""",

    331: """Vallefresno: Antiguo bosque de elfos de la noche bajo asedio. La
Horda avanza desde el este, demonios acechan en las sombras, y los
furbolgs han enloquecido. Astranaar y el puesto avanzado de
Bosquespina representan el conflicto entre facciones. Un bosque
hermoso empañado por la guerra y la corrupción.""",

    405: """Desolace: Tierra baldía árida y gris. Las tribus centauro guerrean
sin cesar entre sí y contra todos los demás. Cementerios de kodo
salpican el paisaje. La zona se siente vacía y desesperanzada -
incluso el cielo parece drenado de color. Uno de los lugares más
deprimentes de Azeroth.""",

    400: """Las Mil Agujas: Cañón dramático de agujas de piedra imponentes. Antes
del Cataclismo, un lecho desértico y seco con la pista de carreras de
los Bajíos Relucientes. Centauros y arpías controlan varios pilares.
El Gran Ascensor conecta con Los Baldíos. Visualmente impresionante
pero duro para viajar.""",

    15: """Marjal Revolcafango: Pantano cálido y húmedo. Dragones negros conspiran
en el sur, crocolisks y arañas hostiles acechan en el fango, y
Theramore se alza como fortaleza de la Alianza. Las ruinas de una
posada incendiada insinúan complots más oscuros. Opresivamente
bochornoso y peligroso.""",

    357: """Feralas: Selva y bosque exuberantes y desbordantes. Yetis en las
montañas, naga en la costa, ogros y gnolls por doquier. Los Colosales
Gemelos son árboles inmensos, y las ruinas de Dire Maul se alzan
imponentes. Una zona salvaje e indómita que engulle a los viajeros.""",

    440: """Tanaris: Desierto abrasador que rodea el puerto goblin de Gadgetzan.
Piratas, bandidos, basiliscos e insectos silítidos por todas partes.
Los trols de Zul'Farrak son hostiles. Las Cavernas del Tiempo se
esconden cerca. Ardiente durante el día, el desierto es implacable
pero rentable.""",

    16: """Azshara: Costa arruinada de los elfos de la noche, de una belleza
inquietante pero vacía. Los naga controlan gran parte de la orilla, y
la Bandada de Dragones Azules mantiene una presencia. Criaturas
marinas gigantes rondan, y restos de la Legión persisten en Cresta
Perdida. La zona se siente abandonada y triste - un monumento a lo
que se perdió.""",

    361: """Frondavil: Bosque corrompido que rezuma con la mancha demoníaca.
Limos, sátiros y fauna corrompida plagan cada rincón. Los propios
árboles parecen enfermos. Los furbolgs Fauces de Madera son
cautelosos pero neutrales; los furbolgs Bosque Muerto son hostiles.
Una zona que te hace sentir sucio con solo atravesarla.""",

    490: """Cráter de Un'Goro: Cráter selvático prehistórico rebosante de
dinosaurios. Los devilsaurios son depredadores dominantes, los
raptores cazan en manadas, y elementales custodian pilones. Es como
retroceder en el tiempo - exuberante, peligroso y lleno de maravillas.
Formaciones de cristal albergan un poder misterioso.""",

    493: """Claro de la Luna: Santuario sagrado de los druidas. Mayormente
pacífico y seguro, con pocas criaturas hostiles. El Círculo Cenarion
se reúne aquí, y la zona se siente atemporal y serena - un respiro
del caos del mundo. Los druidas se reúnen en Refugio Nocturno.""",

    618: """Cuna del Invierno: Tierras altas heladas de invierno eterno. Gatos
Zarpa de Escarcha, yetis y gigantes de hielo rondan la nieve.
Vistalejos es un pueblo goblin de tratos cuestionables. Los furbolgs
Otoño de Invierno son hostiles en toda la zona. Hermosa pero
mortalmente fría, la zona solo recompensa a quien está bien preparado.""",

    1377: """Silithus: Tierra baldía desértica plagada de insectos silítidos. La
amenaza qiraji se cierne desde Ahn'Qiraj. Los druidas del Círculo
Cenarion luchan desesperadamente contra la colmena. Tormentas de
arena, insectos gigantes, y una sensación abrumadora de que algo
antiguo y maligno se agita bajo las arenas.""",

    # -------------------------------------------------------------------------
    # Outland
    # -------------------------------------------------------------------------
    3483: """Península del Fuego Infernal: Tierra baldía roja y destrozada,
primera zona tras el Portal Oscuro. Orcos del vil, demonios y fuerzas
de la Legión Ardiente por todas partes. Fortaleza Honor y Thrallmar
son las bases de las facciones. El cielo está desgarrado, el suelo
está agrietado, y la guerra ruge constantemente. Una introducción
brutal a Outland.""",

    3521: """Marisma de Zangar: Surrealista pantano de setas que brilla con
bioluminiscencia. Hongos gigantes se alzan en lo alto, esporomurciélagos
flotan perezosamente, y los naga drenan las aguas. El Refugio Cenarion
trabaja para salvar el ecosistema. Extrañamente hermoso y alienígena -
nada aquí se parece a Azeroth.""",

    3519: """Bosque de Terokkar: Dividido entre el bosque exuberante y las
tierras baldías sembradas de huesos alrededor de Auchindoun. Arakkoa
acechan entre los árboles, y el Consejo de las Sombras conduce rituales
oscuros. Ciudad de Shattrath es la capital neutral. Una zona de
contrastes entre la vida y la muerte.""",

    3522: """Montañas Filoespada: Paisaje escarpado y hostil de picos imponentes.
Los ogros gobiernan aquí, y los gigantes gronn son los depredadores
dominantes. La Legión Ardiente mantiene puestos avanzados, y dragones
sobrevuelan en círculos. Terreno peligroso donde la propia tierra
parece querer matarte.""",

    3520: """Valle Sombraluna: Tierra baldía oscura, corrompida por el vil. El
Templo Negro se alza amenazante, y las fuerzas de Illidan controlan
la región. Demonios, orcos del vil y caballeros de la muerte patrullan.
El cielo arde en verde. La zona más peligrosa y opresiva de Outland -
aquí la esperanza se siente distante.""",

    3523: """Tormenta Abisal: Islas destrozadas flotando en el Vacío Retorcido.
Forjas de maná cosechan la energía de la tierra, elfos de sangre y
etéreos compiten por recursos, y criaturas de maná deambulan
salvajemente. Las eco-cúpulas preservan la vida artificialmente. Una
zona que se desgarra a sí misma en las costuras.""",

    3524: """Isla Bruma Azur: Tranquila isla draenei bañada por una suave luz
azulada y el zumbido de la tecnología de cristal. El lugar del
accidente de El Exodar aún brilla con energía residual, y los
supervivientes draenei atienden sus heridas y reconstruyen. Fauna
apacible, estanques resplandecientes y ruinas cristalinas comparten
espacio con los esperanzadores inicios de un pueblo desplazado que
encuentra su lugar en un nuevo mundo.""",

    3525: """Isla Bruma de Sangre: Isla hermana de Bruma Azur, teñida de carmesí
por cristales corrompidos de los restos de El Exodar. La energía del
vil ha convertido a la fauna local en depredadores peligrosos y
mutado la vegetación. Elfos de sangre y demonios trabajan para
corromper aún más la tierra. Un lugar de belleza vuelto siniestro,
donde los draenei deben afrontar el daño causado por el accidente de
su propia nave.""",

    # -------------------------------------------------------------------------
    # Northrend
    # -------------------------------------------------------------------------
    3537: """Tundra Boreal: Tundra costera helada, uno de los dos puntos de
entrada a Rasganorte. Los nerubianos se ocultan bajo tierra, el
Flagelo pone a prueba las defensas, y los tuskarr pescan en las
orillas. Baluarte Grito de Guerra y Fortaleza Vigilancia son los
bastiones de las facciones. El frío muerde con fuerza - el invierno
apenas comienza.""",

    495: """Fiordo Aquilonal: Costa dramática de inspiración vikinga con
acantilados imponentes. Guerreros vrykul asaltan desde sus aldeas, y
el Flagelo corrompe a los muertos. Valgarde y Aterrizaje Venganza son
los puntos de desembarco. Los fiordos son sobrecogedores pero los
vrykul son implacables.""",

    394: """Colinas Pardas: Frontera boscosa que se siente casi pacífica.
Furbolgs corrompidos por el Flagelo, enanos de hierro excavan en
busca de secretos, y la maldición worgen se propaga. Operaciones de
tala cicatrizan las laderas. Una zona que sería hermosa de no ser
por la corrupción que se extiende.""",

    3711: """Cuenca de Sholazar: Exuberante cráter selvático intacto por el
Flagelo, mantenido por la tecnología de los titanes. Dinosaurios,
gorilas y bestias exóticas prosperan. Los Corazón Salvaje y los
Oráculos libran una guerra mezquina. Un paraíso inesperado en el
gélido Rasganorte - pero algo amenaza los pilones.""",

    66: """Zul'Drak: Reino trol congelado en colapso. Los Drakkari sacrifican
a sus propios dioses para luchar contra el Flagelo. No-muertos y
trols desesperados chocan por doquier. La zona se siente como
presenciar la muerte de una civilización - sombría, fría y sin
esperanza.""",

    67: """Cumbres Tormentosas: Montañas heladas e imponentes, hogar de secretos
de los titanes. Gigantes de tormenta, enanos de hierro y proto-dracos
dominan. La entrada a Ulduar se alza en lo alto. Los Hijos de Hodir
recelan de los forasteros. Escala épica, condiciones brutales,
misterios ancestrales.""",

    210: """Corona de Hielo: El dominio del Rey Exánime. Interminables
ejércitos no-muertos, fortalezas necrópolis, y la propia Ciudadela
de Corona de Hielo. La Cruzada Argenta hace su última resistencia.
El propio aire se siente muerto. Este es el final del camino -
victoria u olvido.""",

    # -------------------------------------------------------------------------
    # Capital Cities
    # -------------------------------------------------------------------------
    1519: """Ciudad de Ventormenta: La gran capital humana, reconstruida tras la Primera Guerra. La
gran catedral domina el horizonte, los canales serpentean entre distritos de piedra, y
el bullicioso Distrito Comercial nunca duerme. Los guardias patrullan por doquier. El
puerto conecta con tierras lejanas. El rey Varian Wrynn gobierna desde Ventormenta. Una
ciudad de adoquines, estandartes y orgullo cívico — el corazón de la Alianza.""",

    1537: """Forjaz: La gran ciudad enana tallada en el corazón de una montaña. Una enorme forja de
metal fundido domina el centro, rodeada por el distrito de la Gran Forja donde los
maestros herreros martillean día y noche. El aire es cálido y huele a hierro y cerveza.
Túneles se ramifican hacia el Distrito Militar, el Distrito Místico y el Tranvía de las
Profundidades hacia Ciudad de Ventormenta. Sólida, ancestral y construida para durar
para siempre.""",

    1657: """Darnassus: La serena capital de los elfos de la noche en la cima del árbol del mundo
Teldrassil. Árboles ancestrales se arquean en lo alto, una suave luz púrpura se filtra
por el dosel, y aguas quietas reflejan las estrellas incluso al mediodía. El Templo de
la Luna honra a Elune. Los druidas meditan en el Enclave Cenarion. La ciudad se siente
atemporal y pacífica, alejada de las guerras de abajo — aunque esa paz es más frágil de
lo que parece.""",

    3557: """El Exodar: La nave dimensional estrellada de los draenei, ahora reutilizada como su
capital. Pilones de cristal zumban con energía de otro mundo, luz púrpura y azul baña
corredores geométricos, y un santuario radiante brilla en su corazón. La arquitectura es
alienígena y hermosa — mitad catedral, mitad nave estelar. Los draenei siguen con sus
vidas con tranquila dignidad, reconstruyendo tras otro largo viaje.""",

    1637: """Orgrimmar: La brutal capital orca tallada en cañones de desierto rojo. Púas de hierro,
estandartes de guerra y puertas colosales definen el horizonte. El Valle del Poder
resuena con los gruñidos de guerreros en entrenamiento y el estruendo de la casa de
subastas. El legado de Thrall flota en el aire. La ciudad es cruda, ruidosa y
descaradamente agresiva — una ciudad fortaleza construida para un pueblo que espera la
guerra.""",

    1638: """Cima del Trueno: La capital tauren construida sobre mesetas imponentes conectadas por
puentes de cuerda muy por encima de las llanuras de Mulgore. El viento barre las
plataformas al aire libre. Tótems y pieles decoran cada estructura. La Cornisa de los
Ancianos alberga a los druidas, la Cornisa del Espíritu a los sacerdotes. Cairne Pezuña
de Sangre lidera con sabiduría ancestral. La capital de la Horda más pacífica — cielo,
viento, hierba, y la fuerza serena de un pueblo ancestral.""",

    1497: """Entrañas: La capital de los Renegados bajo las ruinas de Lordaeron. Una ciudad de
alcantarillas oscura y circular donde los no-muertos llevan su existencia entre canales
de limo verde y antorchas parpadeantes. El Distrito Real alberga a Sylvanas Windrunner.
Los boticarios elaboran pociones dudosas. El aire es húmedo, frío y ligeramente tóxico.
Sombría, funcional e inquietante — pero un hogar para quienes no tienen otro lugar
adonde ir.""",

    3487: """Ciudad de Lunargenta: La capital de los elfos de sangre, medio reconstruida tras la
invasión del Flagelo. La mitad occidental, en funcionamiento, brilla con agujas carmesí
y doradas, guardianes arcanos patrullan calles impecables, y fuentes fluyen con energía
mágica. Las ruinas orientales siguen siendo una cicatriz. La cultura sin'dorei valora la
belleza, la magia y la sofisticación. Una ciudad elegante que enmascara heridas
profundas y una desesperada adicción al poder arcano.""",

    3703: """Ciudad de Shattrath: La ciudad draenei neutral en el Bosque de Terokkar, ahora
compartida por las facciones Aldor y Videntes. La Terraza de la Luz brilla con
resplandor naaru en su centro. Refugiados de toda Outland abarrotan la Ciudad Baja.
Tanto la Alianza como la Horda caminan estas calles en una incómoda tregua. Un centro
cosmopolita donde se mezclan todas las razas — mitad santuario, mitad polvorín político.""",
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

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'The frozen mountain conflict — Stormpike dwarves vs '
            'Frostwolf orcs in the Alterac Mountains.'
        ),
        'tone': (
            'Epic, large-scale, war-like. 40v40 feels like an '
            'actual battle.'
        ),
        'objectives': (
            'Kill the enemy general. Capture towers and graveyards.'
        ),
        'landmarks': (
            'Key locations: Stormpike Base, Dun Baldar, Icewing '
            'Bunker, Stonehearth Graveyard, Snowfall Graveyard, '
            'Iceblood Tower, Tower Point, Frostwolf Graveyard, '
            'Frostwolf Keep. Do NOT mention locations from other '
            'battlegrounds.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'The lumber war in Ashenvale — Silverwing defend the '
            'forest, Warsong seek its resources.'
        ),
        'tone': (
            'Intense, fast, personal. Small team, every player '
            'matters.'
        ),
        'objectives': 'Capture the enemy flag 3 times.',
        'landmarks': (
            'Key locations: Silverwing Hold (Alliance base), '
            'Warsong Fort (Horde base), the tunnel, midfield, the '
            'ramp. Do NOT mention locations from other battlegrounds '
            'like mills, farms, or towers.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'The fight for Arathi Highlands resources between '
            'Stromgarde and Forsaken.'
        ),
        'tone': (
            'Strategic, territorial, spread out. Reactions about '
            'node control.'
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
        'lore': 'A Netherstorm battlefield over a fragment of Draenor.',
        'tone': (
            'Hybrid tension. Holding bases while fighting over a '
            'central flag.'
        ),
        'objectives': (
            'Control bases and capture the central flag to reach '
            '1600 points.'
        ),
        'landmarks': (
            'Key locations: Fel Reaver Ruins, Blood Elf Tower, '
            'Draenei Ruins, Mage Tower, the center flag. Do NOT '
            'mention locations from other battlegrounds.'
        ),
    },
}

# Russian (ruRU) battleground lore text -- translated from the
# BG_LORE entries above (same bg_type_id keys). 'name',
# 'alliance_faction', and 'horde_faction' are left as English proper
# nouns (out of scope here; only 'lore'/'tone'/'objectives'/
# 'landmarks' -- the genuine English prose fields that were leaking
# into Russian bot chat -- are translated), mirroring how
# ZONE_FLAVOR_RU/DUNGEON_FLAVOR_RU only translate the prose lore
# text and reuse the official/community Russian place names inline.
# Falls back to English BG_LORE via get_bg_lore() for any locale
# other than ruRU.
BG_LORE_RU = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Замерзший горный конфликт — дворфы Штормового Пика '
            'против орков Северного Волка в Альтеракских горах.'
        ),
        'tone': (
            'Эпично, масштабно, по-военному. 40 на 40 ощущается '
            'как настоящее сражение.'
        ),
        'objectives': (
            'Убейте вражеского генерала. Захватывайте башни и кладбища.'
        ),
        'landmarks': (
            'Ключевые точки: База Штормового Пика, Дун Балдар, '
            'Бункер Ледяного Крыла, кладбище Каменного Очага, '
            'кладбище Снегопада, башня Ледяной Крови, Точка Башни, '
            'кладбище Северного Волка, крепость Северного Волка. НЕ '
            'упоминайте локации из других полей боя.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'Война за лес в Ясеневом лесу — Среброкрылые защищают '
            'лес, Песнь Войны жаждет его ресурсов.'
        ),
        'tone': (
            'Напряженно, быстро, лично. Маленькая команда, каждый '
            'игрок на счету.'
        ),
        'objectives': 'Захватите вражеский флаг 3 раза.',
        'landmarks': (
            'Ключевые точки: Приют Среброкрылых (база Альянса), '
            'Форт Песни Войны (база Орды), туннель, центр поля, '
            'рампа. НЕ упоминайте локации из других полей боя, '
            'такие как мельницы, фермы или башни.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'Борьба за ресурсы Нагорья Арати между Стромгардом и '
            'Отрёкшимися.'
        ),
        'tone': (
            'Стратегично, территориально, рассредоточено. Реакции '
            'на контроль точек.'
        ),
        'objectives': (
            'Контролируйте точки, чтобы первыми набрать 1600 ресурсов.'
        ),
        'landmarks': (
            'Ключевые точки: Конюшни (север, открытые пастбища с '
            'загонами для лошадей), Кузница (центральный перекрёсток, '
            'дым и наковальни), Лесопилка (вершина холма, деревянные '
            'настилы и пилы), Золотой Рудник (юго-восточный вход в '
            'пещеру, вагонетки и факелы), Ферма (юг, поля и стога сена '
            'у фермерского дома). НЕ упоминайте локации из других '
            'полей боя.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': 'Поле боя в Пустоверти над обломком Дренора.',
        'tone': (
            'Гибридное напряжение. Удержание баз при борьбе за '
            'центральный флаг.'
        ),
        'objectives': (
            'Контролируйте базы и захватите центральный флаг, чтобы '
            'набрать 1600 очков.'
        ),
        'landmarks': (
            'Ключевые точки: Руины Осквернителя, Башня эльфов крови, '
            'Руины дренеев, Башня магов, центральный флаг. НЕ '
            'упоминайте локации из других полей боя.'
        ),
    },
}

# French (frFR) battleground lore text -- translated from the
# BG_LORE entries above (same bg_type_id keys). 'name',
# 'alliance_faction', and 'horde_faction' are left as English proper
# nouns (out of scope here; only 'lore'/'tone'/'objectives'/
# 'landmarks' -- the genuine English prose fields that were leaking
# into French bot chat -- are translated), mirroring how
# ZONE_FLAVOR_FR/DUNGEON_FLAVOR_FR only translate the prose lore
# text and reuse the community-sourced French place names inline.
# Falls back to English BG_LORE via get_bg_lore() for any locale
# other than frFR/ruRU.
BG_LORE_FR = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Le conflit des montagnes gelées — les nains de l\'Expédition Pic-de-Tempête '
            'contre les orcs du clan Loup-de-givre dans les montagnes d\'Alterac.'
        ),
        'tone': (
            'Épique, à grande échelle, guerrier. Le 40 contre 40 ressemble à une '
            'véritable bataille.'
        ),
        'objectives': (
            'Tuez le général ennemi. Capturez les tours et les cimetières.'
        ),
        'landmarks': (
            'Lieux clés : Base de Pic-de-Tempête, Dun Baldar, Bunker Aile-de-glace, '
            'Cimetière du Foyer-de-Pierre, Cimetière de Chute-de-neige, Tour de '
            'Sang-glacé, Pointe de la Tour, Cimetière du Loup-de-givre, Fort du '
            'Loup-de-givre. NE mentionnez PAS de lieux appartenant à d\'autres '
            'champs de bataille.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'La guerre du bois dans Ashenvale — les Sentinelles Aile-d\'argent défendent la '
            'forêt, les Éclaireurs Cri-de-guerre convoitent ses ressources.'
        ),
        'tone': (
            'Intense, rapide, personnel. Petite équipe, chaque joueur compte.'
        ),
        'objectives': 'Capturez le drapeau ennemi 3 fois.',
        'landmarks': (
            'Lieux clés : Bastion Aile-d\'argent (base de l\'Alliance), Fort Cri-de-guerre '
            '(base de la Horde), le tunnel, le milieu du terrain, la rampe. NE mentionnez '
            'PAS de lieux appartenant à d\'autres champs de bataille comme les moulins, '
            'les fermes ou les tours.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'La lutte pour les ressources des Hautes-terres d\'Arathi entre Stromgarde et '
            'les Réprouvés.'
        ),
        'tone': (
            'Stratégique, territorial, dispersé. Des réactions centrées sur le contrôle '
            'des points.'
        ),
        'objectives': 'Contrôlez les points pour atteindre 1600 ressources en premier.',
        'landmarks': (
            'Lieux clés : les Écuries (au nord, pâturages ouverts avec des enclos à '
            'chevaux), la Forge (carrefour central, fumée et enclumes), la Scierie '
            '(surplomb au sommet d\'une colline, plateformes en bois et scies), la Mine '
            'd\'or (entrée de grotte au sud-est, wagonnets et torches), la Ferme (au sud, '
            'champs et meules de foin près d\'une ferme). NE mentionnez PAS de lieux '
            'appartenant à d\'autres champs de bataille.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': 'Un champ de bataille de Raz-de-néant au-dessus d\'un fragment du Draenor.',
        'tone': (
            'Tension hybride. Tenir les bases tout en se battant pour un drapeau central.'
        ),
        'objectives': (
            'Contrôlez les bases et capturez le drapeau central pour atteindre 1600 points.'
        ),
        'landmarks': (
            'Lieux clés : Ruines du Ravageur ardent, Tour des elfes de sang, Ruines '
            'draeneï, Tour des mages, le drapeau central. NE mentionnez PAS de lieux '
            'appartenant à d\'autres champs de bataille.'
        ),
    },
}

# German (deDE) battleground lore text -- translated from the
# BG_LORE entries above (same bg_type_id keys). 'name',
# 'alliance_faction', and 'horde_faction' are left as English proper
# nouns (out of scope here; only 'lore'/'tone'/'objectives'/
# 'landmarks' -- the genuine English prose fields that were leaking
# into German bot chat -- are translated), mirroring how
# ZONE_FLAVOR_DE/DUNGEON_FLAVOR_DE only translate the prose lore
# text and reuse the community-sourced German place names inline.
# Falls back to English BG_LORE via get_bg_lore() for any locale
# other than deDE/frFR/ruRU.
BG_LORE_DE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'Der Konflikt im vereisten Gebirge — Sturmlanzen-Zwerge gegen '
            'Frostwolf-Orcs in den Alteracbergen.'
        ),
        'tone': (
            'Episch, groß angelegt, kriegerisch. 40 gegen 40 fühlt sich '
            'wie eine echte Schlacht an.'
        ),
        'objectives': (
            'Tötet den feindlichen General. Erobert Türme und Friedhöfe.'
        ),
        'landmarks': (
            'Wichtige Orte: Sturmlanzen-Basis, Dun Baldar, Eisschwingen-Bunker, '
            'Steinherd-Friedhof, Schneefall-Friedhof, Eisblut-Turm, Turmspitze, '
            'Frostwolf-Friedhof, Frostwolf-Feste. Erwähnt KEINE Orte aus anderen '
            'Schlachtfeldern.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'Der Holzkrieg im Eschental — die Silberschwingen verteidigen den '
            'Wald, die Kriegsgesang-Kundschafter wollen seine Ressourcen.'
        ),
        'tone': (
            'Intensiv, schnell, persönlich. Kleines Team, jeder Spieler '
            'zählt.'
        ),
        'objectives': 'Erobert die feindliche Flagge 3 Mal.',
        'landmarks': (
            'Wichtige Orte: Silberschwingen-Hort (Basis der Allianz), '
            'Kriegsgesang-Fort (Basis der Horde), der Tunnel, das Mittelfeld, '
            'die Rampe. Erwähnt KEINE Orte aus anderen Schlachtfeldern wie '
            'Mühlen, Höfe oder Türme.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'Der Kampf um die Ressourcen des Arathihochlands zwischen '
            'Stromgarde und den Verlassenen.'
        ),
        'tone': (
            'Strategisch, territorial, weit verteilt. Reaktionen drehen '
            'sich um die Kontrolle der Punkte.'
        ),
        'objectives': 'Kontrolliert Punkte, um als Erste 1600 Ressourcen zu erreichen.',
        'landmarks': (
            'Wichtige Orte: Ställe (Norden, offene Weiden mit Pferdekoppeln), '
            'Schmiede (zentrale Kreuzung, Rauch und Ambosse), Sägewerk '
            '(Hügelkuppe, hölzerne Plattformen und Sägeblätter), Goldmine '
            '(südöstlicher Höhleneingang, Loren und Fackeln), Bauernhof '
            '(Süden, Felder und Heuhaufen bei einem Bauernhaus). Erwähnt KEINE '
            'Orte aus anderen Schlachtfeldern.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': 'Ein Schlachtfeld im Nethersturm über einem Fragment von Draenor.',
        'tone': (
            'Hybride Spannung. Basen halten, während um eine zentrale Flagge '
            'gekämpft wird.'
        ),
        'objectives': (
            'Kontrolliert Basen und erobert die zentrale Flagge, um 1600 Punkte '
            'zu erreichen.'
        ),
        'landmarks': (
            'Wichtige Orte: Ruinen des Teufelswrackers, Turm der Blutelfen, '
            'Ruinen der Draenei, Turm der Magier, die zentrale Flagge. Erwähnt '
            'KEINE Orte aus anderen Schlachtfeldern.'
        ),
    },
}

# Spanish (esES) battleground lore text -- translated from the
# BG_LORE entries above (same bg_type_id keys). 'name',
# 'alliance_faction', and 'horde_faction' are left as English proper
# nouns (out of scope here; only 'lore'/'tone'/'objectives'/
# 'landmarks' -- the genuine English prose fields that were leaking
# into Spanish bot chat -- are translated), mirroring how
# ZONE_FLAVOR_ES/DUNGEON_FLAVOR_ES only translate the prose lore text
# and reuse the community/official-press-sourced Spanish place names
# inline. Falls back to English BG_LORE via get_bg_lore() for any
# locale other than esES/deDE/frFR/ruRU.
BG_LORE_ES = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'El conflicto en las montañas heladas — enanos de la Expedición Cima '
            'Tempestuosa contra orcos del Clan Lobo Gélido en las Montañas de Alterac.'
        ),
        'tone': (
            'Épico, a gran escala, marcial. 40 contra 40 se siente como una '
            'batalla de verdad.'
        ),
        'objectives': (
            'Matad al general enemigo. Capturad torres y cementerios.'
        ),
        'landmarks': (
            'Ubicaciones clave: Base de Cima Tempestuosa, Dun Baldar, Búnker Ala de '
            'Hielo, Cementerio Corazón de Piedra, Cementerio Nevado, Torre Sangre '
            'Helada, Punto de la Torre, Cementerio Lobo Gélido, Fortaleza Lobo '
            'Gélido. NO menciones ubicaciones de otros campos de batalla.'
        ),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'La guerra por la madera en Vallefresno — las Centinelas Ala de Plata '
            'defienden el bosque, los Exploradores Grito de Guerra buscan sus recursos.'
        ),
        'tone': (
            'Intenso, rápido, personal. Equipo pequeño, cada jugador importa.'
        ),
        'objectives': 'Capturad la bandera enemiga 3 veces.',
        'landmarks': (
            'Ubicaciones clave: Refugio Ala de Plata (base de la Alianza), Fuerte '
            'Grito de Guerra (base de la Horda), el túnel, el campo medio, la '
            'rampa. NO menciones ubicaciones de otros campos de batalla como '
            'molinos, granjas o torres.'
        ),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'La lucha por los recursos de las Tierras Altas de Arathi entre '
            'Stromgarde y los Renegados.'
        ),
        'tone': (
            'Estratégico, territorial, disperso. Reacciones centradas en el '
            'control de los puntos.'
        ),
        'objectives': 'Controlad puntos para alcanzar 1600 recursos primero.',
        'landmarks': (
            'Ubicaciones clave: Establos (norte, pastos abiertos con corrales de '
            'caballos), Herrería (cruce central, humo y yunques), Aserradero '
            '(mirador en la cima de una colina, plataformas de madera y sierras), '
            'Mina de Oro (entrada de cueva al sureste, vagonetas y antorchas), '
            'Granja (sur, campos y pajares junto a una casa de labranza). NO '
            'menciones ubicaciones de otros campos de batalla.'
        ),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': 'Un campo de batalla en Tormenta Abisal sobre un fragmento de Draenor.',
        'tone': (
            'Tensión híbrida. Mantener bases mientras se lucha por una bandera '
            'central.'
        ),
        'objectives': (
            'Controlad bases y capturad la bandera central para alcanzar 1600 '
            'puntos.'
        ),
        'landmarks': (
            'Ubicaciones clave: Ruinas del Devastador Vil, Torre de los Elfos de '
            'Sangre, Ruinas Draenei, Torre de los Magos, la bandera central. NO '
            'menciones ubicaciones de otros campos de batalla.'
        ),
    },
}


# Raid instance map IDs (Classic, TBC, WotLK)
RAID_MAP_IDS = {
    # Classic
    249, 309, 409, 469, 509, 531,
    # TBC
    532, 534, 544, 548, 550, 564, 565, 580,
    # WotLK
    533, 603, 615, 616, 624, 631, 649, 724,
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

# Russian (ruRU) dungeon/raid flavor text -- translated from the
# DUNGEON_FLAVOR entries above (same map-ID keys, same
# paragraph-length atmospheric lore), not injected verbatim since
# the English text was leaking untranslated into Russian bot chat.
# Falls back to English DUNGEON_FLAVOR via get_dungeon_flavor() for
# any locale other than ruRU, mirroring ZONE_FLAVOR_RU/
# get_zone_flavor()'s convention.
DUNGEON_FLAVOR_RU = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Крепость Темного Клыка: населенная призраками цитадель в Серебряном бору, захваченная воргенами и нежитью некроманта Аругала. Призрачные дворяне бродят по темным залам, спектральные псы воют во дворах, а неудачные чародейские эксперименты таятся в каждой тени. Крепость похожа на готическую историю ужасов — холодный камень, мерцающий свет факелов и постоянное ощущение, что за тобой наблюдают.""",

    34: """Тюрьма: темница под Штормградом, где заключенные подняли восстание и захватили контроль. Мятежники Братства Справедливости, обезумевшие каторжники и главари банд бродят по тесным каменным блокам. Подземелье клаустрофобное и жестокое — узкие коридоры, железные решетки и звуки насилия, эхом отдающиеся от сырых стен. Быстро, грязно и опасно.""",

    36: """Заброшенные рудники: обширный рудничный комплекс под Западным Краем, тайно служащий штабом Братства Справедливости. Путь вьется через прорытые гоблинами туннели, лесопилки и плавильни, прежде чем выходит в огромную подземную пещеру, где в скрытой бухте стоит настоящий пиратский корабль. Ощущение, будто ты раскрыл преступную империю прямо под носом у Штормграда.""",

    43: """Пещеры Стенаний: лабиринт извивающихся пещер в Степях, заросших пышной растительностью, питаемой оскверненной друидской магией. Мутировавшие существа — раптор-мутанты, змеи и слизни — ползают по тоннелям с изумрудным оттенком. Друиды Клыка потеряли себя в Изумрудном Кошмаре. Воздух здесь густой, влажный и пахнет джунглевой гнилью.""",

    47: """Пронзающий Терн: колючий лабиринт, выросший из огромных зарослей ежевики в Степях, дом свинобразов и их матриарха Чарлги Терношип. Воины и шаманы свинобразов вместе со своими вепрями заполняют извилистые коридоры, увитые шипами. Подземелье кажется первобытным и диким — природа, скрученная в крепость из кости, шипов и грязи.""",

    48: """Черные Глубины: частично затопленный древний храм на побережье Темных берегов, посвященный темным силам. Наги, сатиры и культисты сумерек поклоняются древним богам в затопленных залах, украшенных осыпающейся архитектурой ночных эльфов. Вода светится жутким сине-зеленым светом, а атмосфера гнетущая и древняя — что-то могущественное спит в глубочайших омутах.""",

    70: """Ульдаман: раскопки титанов, погребенные в Бесплодных землях, наполовину раскоп, наполовину подземелье. Каменные трогги, землескульные конструкты и археологические опасности заполняют залы отполированного металла титанов и необработанного камня. Чем глубже спускаешься, тем более чуждой становится архитектура — гладкие геометрические залы, гудящие дремлющей силой. Ощущение, будто вторгаешься в библиотеку, построенную богами.""",

    90: """Гномреган: облученные руины гномьей столицы, потерянной из-за нашествия троггов и катастрофической радиационной утечки. Обезумевшие гномы-прокаженные, неисправные роботы и токсичные слизни населяют многоуровневый механический комплекс. Ревут сирены тревоги, светятся зеленые радиоактивные лужи, а сломанные механизмы искрят повсюду. Одновременно трагично и абсурдно.""",

    109: """Затонувший Храм: Храм Атал'Хаккара, троллий храм, затянутый под болота Зеленым Драконьим Роем. Тролли Атал'ай поклоняются кровавому богу Хаккару в затопленных, увитых лианами залах. Драконы охраняют нижние уровни, а лабиринтообразная планировка сбивает с толку. Атмосфера насыщена джунглевой влажностью, древней троллиной магией и ощущением запретного ритуала.""",

    129: """Курганы Разорфена: место захоронения свинобразов в Степях, кишащее нежитью. Прислужник Плети Амненнар Хладонес поднял мертвых свинобразов, превратив их священные склепы в некрополь из костей и шипов. Скелеты-свинобразы и чумные летучие мыши заполняют мрачные коридоры. Место, где сталкиваются два вида смерти — первобытная и некромантическая.""",

    189: """Монастырь Алого ордена: укрепленный монастырь в Тирисфальских лесах, оплот фанатичного Алого Крестового похода. Четыре крыла вмещают библиотеку запретных текстов, оружейную, кишащую фанатиками, собор извращенной веры и населенное призраками кладбище. Крестоносцы хорошо вооружены, дисциплинированны и абсолютно безумны — уверены, что все вокруг тайно являются нежитью. Прекрасная архитектура, скрывающая кровожадный фанатизм.""",

    209: """Зул'Фаррак: троллий город, наполовину погребенный в песках Танариса, дом враждебных троллей Песчаной Ярости. Опаленные солнцем каменные храмы, жертвенные алтари и песчаные дворы составляют это подземелье под открытым небом. Знаменитая битва на лестнице сталкивает тебя с волнами троллей-воинов. Жар пустыни беспощаден, тролли свирепы, а древняя магия потрескивает среди руин.""",

    229: """Вершина Черной горы: массивная орочья крепость, вырубленная в верхних отрогах Черной горы. Нижний шпиль кишит орками Черной горы, ограми и троллями, а верхний шпиль — резиденция вождя Ренда Черной Руки и его союзников-драконидов. Внизу светится лава, непрестанно гремят боевые барабаны, а воздух пропитан дымом и кровью. Обширная военная твердыня в сердце Черной Орды.""",

    230: """Глубины Черной горы: обширный город дворфов Черного Железа глубоко внутри Черной горы, построенный вокруг озера расплавленной лавы. Здесь находятся таверна "Мрачный Ковш", тронный зал императора и порог Огненных Недр. Элементали, големы и фанатичные дворфы Черного Железа заполняют невероятно огромный подземный мегаполис. Ощущение, будто здесь существует целая цивилизация — темная, трудолюбивая и враждебная.""",

    269: """Черная топь: инстанс Пещер Времени, разворачивающийся в первобытном болоте, которое станет Опаленными землями. Агенты Бесконечного Драконьего Роя пытаются помешать Медиву открыть Темный портал, а волны драконидов атакуют сквозь разрывы времени. Болото темное, туманное и первобытное, а энергия портала потрескивает вдали. Само время здесь кажется нестабильным.""",

    289: """Некроситет Скольжения: некромантическая академия в криптах под Каэр Дарроу, управляемая Культом Проклятых. Студенты и профессора темной магии практикуют свое ремесло как на мертвых, так и на живых. Скелеты, призраки и плотяные големы заполняют классы и лаборатории. У подземелья извращенная научная атмосфера — лекционные залы и библиотеки, полностью посвященные магии смерти.""",

    329: """Стратхольм: горящие руины некогда великого города, вечно объятого пламенем с тех пор, как Артас его очистил. Нежить Плети контролирует восточную половину, а Алый Крестовый поход фанатично удерживает западные врата. Здания рушатся в непрекращающемся огне, аббоминации бредут по улицам, а пепел никогда не оседает. Памятник трагедии и безумию — каждый угол хранит память о резне.""",

    349: """Мародон: священная система пещер в Пустошах, искаженная принцессой Терадрас и ее потомками-кентаврами после смерти хранителя Заэтара. Три цветных пути вьются сквозь кристальные пещеры, ядовитые водопады и пышные подземные сады, прежде чем достигают внутреннего святилища. Глубинные залы завораживающе прекрасны — светящиеся кристаллы, чистые водоемы и древняя магия земли, борющаяся против порчи. Природа, скорбь и стихийная ярость, переплетенные воедино.""",

    389: """Бездна Огненной Пропасти: вулканическая система пещер под самим Оргриммаром, где укоренились культисты Пылающего Клинка и трогги. Лава течет по узким туннелям, огненные элементали патрулируют коридоры, а жара удушающая. Короткое и жестокое подземелье — из тех, что напоминают, что Орда построила свою столицу прямо на вулкане.""",

    429: """Забытый Город: разрушенный город высокорожденных в Фераласе, разделенный на три крыла. Огры захватили северное крыло, сатиры и оскверненные древние заполонили восточное, а призрачные духи высокорожденных населяют западное крыло с библиотекой. Осыпающаяся эльфийская архитектура ошеломляющей красоты медленно уступает джунглевым зарослям. Подземелье ощущается огромным, древним и меланхоличным — труп великой цивилизации, растаскиваемый мародерами.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Логово Ониксии: единая обширная пещера в Болоте Печали, дом матери драконьего выводка Ониксии. Путь вьется по узкому тоннелю обугленной скалы, прежде чем открывается в огромный зал, усыпанный костями и кладками яиц. Детеныши роятся, лава бурлит у краев, а сама Ониксия заполняет пещеру огнем и тенью. Клаустрофобный тоннель, ведущий в подавляющую своими масштабами арену драконьего огня.""",

    309: """Зул'Гуруб: массивный троллий храмовый комплекс в джунглях Тернистой долины, где племя Гурубаши освободило кровавого бога Хаккара. Заросшие дворы, жертвенные алтари и площади, полные тварей, окружают центральный храм, сочащийся кровавой магией. Жрецы-змеи, наездники на летучих мышах и культисты-тигры служат своим темным хозяевам. Сами джунгли словно пульсируют первобытной энергией вуду.""",

    409: """Огненные Недра: пылающее сердце Черной горы, царство чистого огня под властью Рагнароса Повелителя Огня. Реки лавы текут между обсидиановыми платформами, огненные элементали и расплавленные великаны патрулируют повсюду, а жара апокалиптическая. Многоголовые огненные псы, возвышающиеся лавовые всплески и древние огневещатели охраняют своего хозяина. Высшее испытание огнем — прекрасное и ужасающее в равной мере.""",

    469: """Логово Крыла Тьмы: твердыня Нефариана на вершине шпиля Черной горы, темная лаборатория, где черный дракон экспериментирует над другими драконьими родами. Дракониды-солдаты, хромированные дракончики и неудачные эксперименты заполняют залы из темного железа и драконьей кости. Каждая палата представляет собой уникальное тактическое испытание. Рейд ощущается клиническим и зловещим — логово безумного ученого, увеличенное до драконьих масштабов.""",

    509: """Руины Ан'Кираж: поле боя под открытым небом в Силитусе, где силы киражи собираются на войну. Насекомоподобные воины, обсидиановые разрушители и массивные жукоподобные существа роятся среди песчаных дворов и осыпающихся храмовых руин. Архитектура чуждая и хитиновая, наполовину египетская гробница, наполовину насекомий улей. Пустынный ветер несет щелканье миллионов лап.""",

    531: """Храм Ан'Кираж: запечатанное внутреннее святилище империи киражи, кошмар чуждой архитектуры и порчи древнего бога. Внутри таятся близнецы-императоры, массивные особы силитидов и сам древний бог К'Тун. Стены пульсируют органическим ростом, глаза наблюдают с каждой поверхности, а реальность искривляется вблизи темницы древнего бога. Самое чуждое и тревожное место в классическом Азероте.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Разрушенные Залы: твердыня орков Скверны в цитадели Адского Пламени, кровавый гаунтлет самых фанатичных слуг Пылающего Легиона. Орки-гладиаторы Скверны, легионеры и берсерки заполняют каждый коридор, а пленники прикованы к стенам. Архитектура — грубое железо и красный камень, испачканные следами постоянного насилия. Неослабевающий штурм крепости, которая сопротивляется на каждом шагу.""",

    542: """Кузня Крови: демоническая фабрика в цитадели Адского Пламени, где орки Скверны создаются через темные ритуалы. Чаны с кипящей кровью, закованные в цепи пленники, ожидающие превращения, и демоническая механика заполняют дымящиеся камеры. Новорожденные орки Скверны и их надзиратели охраняют производственные линии. Подземелье пропахло кровью и серой — промышленное шоу ужасов.""",

    543: """Бастион Адского Пламени: внешние укрепления цитадели Адского Пламени, первая линия обороны армии орков Скверны. Сторожевые башни, бастионы и узкие переходы открывают панорамный вид на разрушенный полуостров Адского Пламени внизу. Солдаты Скверны, наездники на воргах и плененный дракон охраняют стены. Ветер воет сквозь разрушенные бастионы, а красное небо Запределья простирается бесконечно над головой.""",

    545: """Паровое Подземелье: контролируемая нагами водонасосная станция в резервуаре Гнилого Клыка, где силы леди Вайш осушают Зангартопь. Массивные трубы, клапаны и водные каналы доминируют в промышленной планировке. Наги, болотные владыки и водные элементали охраняют механизмы. Пар шипит из каждого стыка, а рев бушующей воды оглушителен. Подземелье, ощущающееся как саботаж на враждебной фабрике.""",

    546: """Нижетопь: гниющее болото под резервуаром Гнилого Клыка, кишащее мутировавшими грибными существами и враждебными духами природы. Споровые великаны, болотные владыки и ядовитая живность заполняют заросшие пещеры. Биолюминесцентные грибы отбрасывают жуткое свечение на застойные лужи. Воздух густой от спор и запаха гнили — природа, вышедшая из-под контроля и ставшая враждебной.""",

    547: """Загоны для рабов: трудовые лагеря резервуара Гнилого Клыка, где надсмотрщики-наги держат в плену Сломленных дренеев. Затопленные туннели, грубые загоны и надсмотрщики-наги с плетьми определяют атмосферу. Грибные наросты и болотные твари проникли в комплекс. Подземелье, пропитанное страданием и угнетением, полузатопленное и гниющее.""",

    552: """Аркатрац: спутниковая тюрьма Крепости Бурь в другом измерении, удерживающая самых опасных существ космоса. Эредарские чернокнижники, существа Пустоты и саботажники из эльфов крови бродят по блокам, спроектированным для сдерживания невообразимых ужасов. Архитектура — кристальная технология дренеев, искаженная своими же узниками. Каждая дверь камеры заставляет задуматься, что вырвалось наружу — и что все еще заперто внутри.""",

    553: """Ботаника: обширный биокупол-спутник Крепости Бурь, где некогда культивировалась экзотическая флора со всего космоса. Эльфы крови захватили объект, а растения выросли дикими и враждебными. Хлысты, древни и чужеродные ботанические образцы заполняют оранжереи мерцающего кристалла. Прекрасно, но смертельно опасно — каждый цветок может убить, а эльфы крови еще хуже.""",

    554: """Механар: производственное крыло Крепости Бурь, теперь контролируемое инженерами эльфов крови и их механическими творениями. Чародейские конструкты, скверноносные жнецы и надзиратели-нетермансеры охраняют коридоры сверкающего кристалла и гудящих механизмов. Технология изящна и чужеродна — инженерия дренеев, переделанная для зловещих целей. Все вокруг гудит от едва сдерживаемой чародейской энергии.""",

    555: """Лабиринт Теней: самое глубокое крыло Аукиндона, где Совет Теней проводит свои темнейшие ритуалы. Ходячие пустоты, чародеи Скверны и культисты Кабала поклоняются в залах, густых от теневой магии. Мурмур, первородный звуковой элементаль, закован в глубочайшей палате. Тьма здесь кажется живой и голодной — тени движутся сами по себе, а шепот раздается отовсюду и ниоткуда.""",

    556: """Чертоги Сетекк: храмовые залы аракков в Аукиндоне, занятые фанатиками, преданными богу-ворону Анзу. Обезумевшие жрецы-аракки, призванные ими духи и призрачные стражи заполняют коридоры, усыпанные перьями. Архитектура смешивает стили дренеев и аракков тревожащим образом. Обитатели полностью сошли с ума, а залы отдаются безумным клекотом и мрачными пророчествами.""",

    557: """Гробницы Маны: зараженное эфириалами крыло Аукиндона, где консорциум принца-нексус Шаффара разграбляет погребальные хранилища дренеев. Эфириальные бандиты, чародейские конструкты и неупокоенные духи дренеев сталкиваются в кристальных гробничных палатах. Гробницы светятся остаточной святой энергией, пока эфириалы выкачивают ее прочь. Священное место, систематически разграбляемое межпространственными ворами.""",

    558: """Аухенайские склепы: погребальные земли дренеев под Аукиндоном, где жрецы-аухенаи сошли с ума, общаясь с мертвыми. Неупокоенные духи, одержимые клирики и нежить-дренеи заполняют склепы, обрамленные костями. То, что некогда было местом почтительной памяти, стало домом мертвецов. Трагедия ощутима — это были хранители, потерявшие себя в горе.""",

    560: """Старые предгорья Хилсбрада: инстанс Пещер Времени, разворачивающийся в прошлом, когда Тралл еще был рабом в крепости Дарнхолд. Хилсбрад тех лет зелен, мирен и полон ничего не подозревающих людей, занятых своими делами. Бесконечный Драконий Рой пытается изменить историю, помешав побегу Тралла. Ощущение сюрреалистичности — идти по месту, которое ты знаешь еще до того, как все пошло не так.""",

    568: """Зул'Аман: твердыня лесных троллей в Призрачных землях, где военачальник Зул'джин наделил своих чемпионов сущностью животных богов. Духи рыси, медведя, орла и дракондора наполняют силой троллиных стражей храма. Архитектура лесного храма Амани яркая и первобытная, украшена масками, тотемами и боевой раскраской. Гаунтлет на время, где важна скорость, а троллиные барабаны никогда не смолкают.""",

    585: """Терраса Магистров: последний оплот Кель'таса Солнечного Скитальца на острове Кель'Данас, дворец эльфов крови ошеломляющего изящества, скрывающий демоническую порчу. Кристаллы Скверны питают чародейские конструкты, магистры эльфов крови направляют запретную магию, а плененный наару лишается своего Света. Красота архитектуры Луносвета, искаженная отчаянием и зависимостью — золоченые залы, скрывающие чудовищную сделку.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Каражан: населенная призраками башня последнего Хранителя, Медива, в Мертвецком Перевале. Призрачный званый ужин, оперная сцена с потусторонними исполнителями, ожившая партия в шахматы и небесная обсерватория заполняют невероятно высокую башню. Башня существует частично вне обычной реальности — комнаты смещаются, время искривляется, а отголоски безумия Медива разыгрываются вечно. Завораживающе прекрасно, глубоко жутко и совершенно уникально.""",

    534: """Вершина Хиджал: рейд Пещер Времени, разворачивающийся во время битвы за гору Хиджал, кульминационного противостояния Архимонду и Пылающему Легиону. Волны нежити и демонов штурмуют три базы поочередно — человеческую, ордынскую и ночноэльфийскую. Мировое древо Нордрассил возвышается над горящим лесом. Эпический оборонительный сценарий, где на кону судьба Азерота, а легендарные герои сражаются рядом с тобой.""",

    544: """Логово Магтеридона: единственная жестокая палата под цитаделью Адского Пламени, где закован повелитель ямы Магтеридон. Направители поддерживают его темницу, пока энергия адского пламени пульсирует по комнате. Пространство удушающе жаркое, пропахшее демонической кровью и серой. Прямолинейное, но изнуряющее сражение — один массивный демон, одна смертоносная комната, никакого права на ошибку.""",

    548: """Змеиное святилище: подводная твердыня леди Вайш в резервуаре Гнилого Клыка, затопленный дворец оскверненной красоты. Наги, приливоходцы и колоссальные гидры охраняют палаты, где водопады низвергаются в светящиеся водоемы. Мосты пересекают подземные озера, а глубинные палаты пульсируют оскверненными водами Зангартопи. Изящная архитектура наг встречается с необузданной силой подземного океана.""",

    550: """Крепость Бурь — Око: захваченная крепость наару Кель'таса Солнечного Скитальца, кристальная цитадель, парящая над Пустовертью. Советники из эльфов крови, чародейские конструкты и существа Пустоты охраняют палаты сверкающего кристалла дренеев. Технология захватывающе чужеродна и прекрасна, переделана отчаявшимися эльфами, кормящими свою магическую зависимость. Вид на разрушенную Пустоверть с платформ одновременно ошеломляющий и пугающий.""",

    564: """Черный Храм: крепость Иллидана Ярости Бури в Долине Призрачной Луны, огромный храм дренеев, оскверненный демонической оккупацией. Орки Скверны, демоны, наги и эльфы крови служат Предателю среди обширных дворов, канализационных систем и величественных залов. Изначальная красота храма изуродована скверной — треснувшие святые символы, оскверненные алтари и зеленое пламя там, где некогда был Свет. Кульминация истории Запределья, завершающаяся у трона Иллидана.""",

    565: """Логово Груула: грубый пещерный комплекс в Острогорье, дом отца гроннов Груула Драконоубийцы. Слуги-огры и чудовищные сыновья Груула охраняют подступы к его палате, усыпанной драконьими костями и трофеями. Пещеры кажутся первобытными и жестокими — никакой архитектуры, никаких украшений, лишь голый камень, вылепленный кулаками великанов.""",

    580: """Плато Солнечного Колодца: последний рейд Пылающего Крестового похода, разворачивающийся в сердце восстановленного Солнечного Колодца на острове Кель'Данас. Пылающий Легион пытается призвать Кил'джедена через сам Солнечный Колодец. Безупречная эльфийская архитектура захватывающей красоты обрамляет отчаянную битву против сильнейших демонов армии Легиона. Святой свет Солнечного Колодца сталкивается с демонической тьмой в каждой палате.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Крепость Утгард: крепость врайкулов на берегах Ревущего фьорда, первое знакомство с опасностями Нордскола. Залы в скандинавском стиле из темного камня и железа, освещенные ревущими очагами и украшенные драконьими черепами. Воины-врайкулы, укротители протодраконов и их нежить-слуги заполняют великие залы. Подземелье похоже на набег на норвежский длинный дом — холодное, жестокое и пропитанное культурой воинов.""",

    575: """Вершина Утгард: верхние уровни крепости Утгард, где правит со своего ледяного трона король врайкулов Имирон. Залы трофеев, вольеры орлов и ритуальные палаты возвышаются над фьордом. Архитектура становится все более грандиозной и угрожающей по мере подъема, достигая кульминации в покрытом инеем тронном зале Имирона. Ветер воет сквозь открытые бастионы, а вид на замерзший ландшафт внизу вызывает головокружение.""",

    576: """Нексус: кристальные пещеры под Холодарой, твердыня войны Синего Драконьего Роя против смертной магии. Замерзшие пещеры невероятной красоты содержат чародейские аномалии, обезумевших охотников на магов и разрывы в реальности. Кристаллизованные драконы застыли в полете. Подземелье мерцает нестабильной чародейской энергией — синие, фиолетовые и белые тона преломляются сквозь лед и кристалл во всех направлениях.""",

    578: """Окулус: верхние кольца Нексуса, серия парящих платформ, соединенных магическими мостами высоко над узлом линий силы. Игроки садятся на драконов, чтобы перемещаться между кольцевыми сегментами, сражаясь с силами Малигоса. Пустота простирается внизу, чародейская энергия потрескивает между платформами, а головокружение здесь настоящее. Подземелье, ощущающееся как полет сквозь магическую бурю на краю реальности.""",

    595: """Расправа над Стратхольмом: инстанс Пещер Времени, разворачивающийся во время рокового очищения зачумленного города Артасом. Улицы Стратхольма целы, но обречены — горожане превращаются в нежить прямо на глазах, а Артас мрачно приказывает предать их смерти, прежде чем свершится перемена. Подземелье уникально тревожное, потому что ты сам помогаешь совершить злодеяние, положившее начало падению Артаса. Мрачнейший момент истории, переживаемый заново.""",

    599: """Чертоги Камня: комплекс титанов в Штормпике, часть обширного комплекса Ульдуара. Каменные коридоры геометрического совершенства вмещают неисправные конструкты титанов, железных дворфов и древние оборонительные системы. Трибунал Веков хранит записи самого творения. Подземелье ощущается научным и древним — музей, где экспонаты дают отпор, а хранящаяся здесь история способна сокрушить цивилизации.""",

    600: """Крепость Драк'Тарон: зараженная Плетью троллиная крепость на границе Седых холмов и Зул'Драка. Плеть подняла мертвых троллей и осквернила их ящероподобных зверей, создав нечестивый союз троллиной культуры и некромантической силы. Скелеты-рапторы, зомби-тролли и лич Новос Призыватель заполняют разлагающиеся залы. Троллиная архитектура, рушащаяся под тяжестью нежизни.""",

    601: """Азжол-Неруб: разрушенное царство нерубианов под Нордсколом, оплетенный паутиной вертикальный спуск сквозь империю пауков. Нерубианская архитектура из шелка и хитина простирается через огромные подземные пропасти. Нежить-нерубианы служат Плети, пока живые отчаянно сражаются. Подземелье увлекает все глубже и глубже сквозь обрушивающиеся полы — клаустрофобное, чуждое и кишащее тем, чего не должно существовать.""",

    602: """Чертоги Молний: кузница титанов в Ульдуаре, потрескивающая электрической энергией. Железные дворфы, штормовые великаны и рунические конструкты охраняют коридоры сверкающего металла и разряжающихся молний. Локен, осквернённый хранитель-титан, ждет в глубочайшей палате. Каждая поверхность гудит силой, искры танцуют по стенам, а гром кузни непрестанен и оглушителен.""",

    604: """Гундрак: троллиный храм драккари в Зул'Драке, где тролли жертвуют своих собственных животных богов, чтобы питать войну против Плети. Алтари истекают священной кровью, пока пожираются духи змея, мамонта и носорога. Храм огромен и первобытен — резной камень, ритуальные водоемы и отчаянная энергия умирающей цивилизации, сжигающей собственных богов ради выживания.""",

    608: """Аметистовая Крепость: магическая тюрьма под Дэлараном, где Кирин-Тор удерживает самых опасных существ Нордскола. Агенты Лазурного Драконьего Роя штурмуют тюрьму через порталы, освобождая узников волнами. Архитектура — изящный дэларанский фиолетовый и серебряный, но узники поистине кошмарны. Сценарий обороны башни внутри волшебного подземелья — чародейские обереги напрягаются под натиском хаоса.""",

    619: """Ань'кахет: Старое Королевство: глубочайшие пределы Азжол-Неруба, где Безликие служат древнему богу Йогг-Сарону. Архитектура сменяется с нерубианской на нечто гораздо более древнее и чуждое — органические стены пульсируют, реальность искривляется, а эффекты безумия атакуют разум. Забытые, швыряющие заклятия и вестник Волазж таятся в палатах, бросающих вызов геометрии. Самое тревожное подземелье Нордскола.""",

    632: """Кузня Душ: первое из трех подземелий Цитадели Ледяной Короны, массивный двигатель, перемалывающий души, где Король-лич обрабатывает мертвых. Реки истерзанных душ текут сквозь железные механизмы, призрачные кузнецы куют на наковальнях страдания, а Пожиратель Душ охраняет кузню. Крики не смолкают никогда. Промышленный кошмар, питаемый вечной мукой.""",

    650: """Испытание Чемпиона: грандиозная турнирная арена под Аргентовым Колизеем в Ледяной Короне, где чемпионы Альянса и Орды доказывают свою доблесть. Конные поединки, дуэли чемпионов и финальная засада Черного Рыцаря разворачиваются на турнирных землях. Атмосфера праздничная и соревновательная, пока нежить не срывает торжество. Пышность и зрелище с темным поворотом.""",

    658: """Яма Сарона: жестокий рудник рабов в Ледяной Короне, где силы Плети заставляют пленников добывать сароновую руду до смерти. Яма открыта морозному небу, повсюду массивные цепи, добычные платформы и залежи сарона. Кузнец-мастер Мерзлоскал швыряет валуны, пока Тираннус патрулирует небо на своем морозном протодраконе. Безнадежность и жестокость, застывшие в мерзлом камне и темном металле.""",

    668: """Чертоги Отражений: населенные призраками Морозные Чертоги Цитадели Ледяной Короны, где эхо жертв Ледяной Скорби витает вокруг палаты клинка. Сам Король-лич преследует тебя сквозь рушащиеся коридоры, пока волны призраков атакуют. Чертоги безупречно ледяные и темно-сароновые, а ужас здесь настоящий — ты не можешь сражаться с ним, только бежать. Самое напряженное в сюжетном плане подземелье в игре, отчаянный побег от неизбежной гибели.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Наксрамас: парящий некрополь верховного лича Кел'Тузада, зависший над Драконьим Погостом. Четыре тематических крыла ужасов — Паучье крыло гигантских пауков, Чумное крыло болезней и аббоминаций, Военное крыло командиров рыцарей смерти и крыло Конструктов из плотяных големов. Готическая архитектура из темного камня и зеленой слизи, с холодной точностью нежити военной организации. Шедевр смерти Плети.""",

    603: """Ульдуар: город-тюрьма титанов в Штормпике, величайший рейд Нордскола. Массивные залы сверкающего металла и камня вмещают оскверненных хранителей-титанов и их слуг, а древний бог Йогг-Сарон заточен в глубочайшем хранилище. Масштаб ошеломляющий — битвы на транспортных средствах у ворот, обсерватория, открытая космосу, сады неземной красоты и спуск в само безумие. Древний, величественный и ужасающий.""",

    615: """Обсидиановое святилище: вулканическая палата под храмом Крыла Вечности, где Сарторион охраняет яйца сумеречных драконов. Реки лавы разделяют обсидиановые платформы, а три лейтенанта-сумеречных дракона патрулируют собственные острова. Палата светится оранжевым и красным, жаркое марево искажает воздух, а предательство черного драконьего рода обнажено полностью. Прямолинейная арена огня и чешуи.""",

    616: """Око Вечности: личное святилище Малигоса на вершине Нексуса над Холодарой, платформа, парящая в чистой энергии линий силы. Здесь нет земли, нет стен — лишь диск магической силы над бездной кружащейся синей и фиолетовой чародейской энергии. Ткач Заклинаний атакует со всей мощью Синего Драконьего Роя. Рейд ощущается потусторонним — сражение с аспектом дракона в сердце чародейской бури Азерота.""",

    624: """Хранилище Архавона: сокровищница титанов под крепостью Зимних Ключей, доступная лишь фракции, контролирующей зону. Каменные великаны и стихийные конструкты охраняют палаты в прямолинейной серии сражений с боссами. Архитектура — утилитарный дизайн титанов: функциональный, массивный и без украшений. Награда за победу в PvP, быстрая и жестокая.""",

    631: """Цитадель Ледяной Короны: трон Короля-лича, кульминация Гнева Короля-лича. Возвышающаяся крепость из сарона и льда, поднимающаяся из сердца Ледяной Короны. Каждое крыло усиливает ужас — от армий нежити Нижнего Шпиля через Чумные Работы, Багровый Чертог и Морозные Крылья до самого Ледяного Трона. Архитектура гнетущая, прекрасная в своей жестокости и созданная, чтобы сломить надежду. Это конец.""",

    649: """Испытание Крестоносца: Аргентовый Колизей в Ледяной Короне, турнирная арена, погружающаяся под землю, когда пол обрушивается в подземную нерубианскую пещеру. Верхний уровень — яркие знамена и ликующая толпа; нижний уровень — хитиновый ужас и владения Ануб'арака. Контраст между праздничным состязанием наверху и древним ужасом внизу определяет весь опыт.""",

    724: """Рубиновое святилище: палата под храмом Крыла Вечности, где сумеречный драконий род вторгся в святилище красных драконов. Халион, сумеречный разрушитель, перемещается между физическим миром и миром теней. Палата переходит между теплым рубиновым светом и холодной фиолетовой тенью. Последний рейд перед Катаклизмом — краткое, зловещее предупреждение о грядущем разрушении.""",
}

# French (frFR) dungeon/raid flavor text -- translated from the
# DUNGEON_FLAVOR entries above (same map-ID keys, same
# paragraph-length atmospheric lore), not injected verbatim since
# the English text was leaking untranslated into French bot chat.
# Proper nouns reuse the community-sourced terms from ZONE_NAMES_FR
# where covered there; dungeon/raid names themselves and most NPC
# names use well-known French WoW-community terms (community/wiki-
# sourced confidence, same tier as ZONE_NAMES_FR, not independently
# re-verified against official client DBC data). Falls back to
# English DUNGEON_FLAVOR via get_dungeon_flavor() for any locale
# other than frFR/ruRU, mirroring ZONE_FLAVOR_FR/get_zone_flavor()'s
# convention.
DUNGEON_FLAVOR_FR = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Château de Croc-Ombrageux : forteresse hantée dans la Forêt des Pins argentés, envahie par
les worgens et les serviteurs morts-vivants du nécromancien Arugal. Des nobles
fantomatiques errent dans les couloirs obscurs, des chiens spectraux hurlent dans les
cours, et des expériences arcaniques ratées se tapissent dans chaque ombre. Le château
évoque un roman d'épouvante gothique — pierre froide, lueur vacillante des torches, et
l'impression constante d'être observé.""",

    34: """La Prison : geôle sous Hurlevent où les détenus se sont révoltés et en ont pris le
contrôle. Émeutiers Defias, forçats déments et chefs de gang errent dans les blocs
cellulaires exigus. Le donjon est claustrophobe et brutal — couloirs étroits, barreaux de
fer, et les bruits de violence qui résonnent sur les murs humides. Rapide, sale et
dangereux.""",

    36: """Les Mines de Fer : vaste complexe minier sous la Marche de l'Ouest, secrètement le
quartier général de la Confrérie Defias. Le chemin serpente à travers des tunnels aménagés
par des gobelins, des scieries et des fonderies avant de déboucher dans une immense
caverne souterraine où un navire pirate grandeur nature repose dans une crique cachée. On
a l'impression de découvrir un empire criminel juste sous le nez de Hurlevent.""",

    43: """Cavernes des Lamentations : labyrinthe de cavernes sinueuses dans les Tarides, envahi
d'une végétation luxuriante nourrie par une magie druidique corrompue. Des créatures
dévoyées — raptors mutés, serpents et vases — se faufilent dans les tunnels aux teintes
émeraude. Les Druides du Croc se sont perdus dans le Cauchemar d'Émeraude. L'air est
épais, humide, et sent la pourriture de la jungle.""",

    47: """Les Épines de Razorfen : labyrinthe épineux né d'immenses ronciers dans les Tarides, foyer
des quilbêtes et de leur matriarche Charlga Griffedéchirante. Guerriers et chamans
quilbêtes, accompagnés de leurs sangliers, remplissent les couloirs sinueux tapissés
d'épines. Le donjon semble primitif et féral — la nature tordue en une forteresse d'os,
d'épines et de boue.""",

    48: """Les Profondeurs de Fangelombre : temple ancien partiellement submergé sur la côte de
Sombrivage, consacré à de sombres puissances. Naga, satyres et cultistes du crépuscule
vénèrent d'anciens dieux dans des salles inondées, ornées d'une architecture elfique en
ruine. L'eau luit d'un bleu-vert inquiétant, et l'atmosphère est oppressante et ancienne —
quelque chose de puissant dort dans les bassins les plus profonds.""",

    70: """Uldaman : site de fouilles des titans enfoui dans les Terres Ingrates, à mi-chemin entre
le chantier archéologique et le donjon. Trogs de pierre, golems terreux et dangers
archéologiques emplissent des chambres de métal titanesque poli et de roche brute. Plus on
descend, plus l'architecture devient étrangère — salles géométriques lisses bourdonnant
d'une puissance endormie. On a l'impression de s'introduire dans une bibliothèque bâtie
par des dieux.""",

    90: """Gnomeregan : les ruines irradiées de la capitale gnome, perdue lors d'une invasion de
trogs et d'une fuite radioactive catastrophique. Des gnomes lépreux déments, des robots
défaillants et des vases toxiques peuplent le complexe mécanique à niveaux multiples. Les
sirènes d'alarme retentissent, des flaques de radiations vertes luisent, et des machines
brisées étincellent partout. À la fois tragique et absurde.""",

    109: """Temple immergé : le Temple d'Atal'Hakkar, un temple troll entraîné sous les marais par le
clan draconique Vert. Les trolls Atal'ai vénèrent le dieu du sang Hakkar dans des salles
inondées et envahies de lianes. Des draconiens gardent les niveaux profonds, et
l'agencement labyrinthique désoriente. L'atmosphère est saturée d'humidité de jungle,
d'ancienne magie trolle et d'un sentiment de rituel interdit.""",

    129: """Nécropole de Razorfen : cimetière quilbête dans les Tarides, infesté de morts-vivants.
L'agent du Fléau Amnennar le Porteur-de-froid a relevé les quilbêtes morts, transformant
leurs cryptes sacrées en une nécropole d'os et d'épines. Quilbêtes squelettiques et
chauves-souris pestiférées remplissent les couloirs lugubres. Un lieu où deux formes de
mort entrent en collision — primitive et nécromantique.""",

    189: """Monastère écarlate : monastère fortifié dans les Clairières de Tirisfal, bastion de la
fanatique Croisade écarlate. Quatre ailes abritent une bibliothèque de textes interdits,
un arsenal grouillant de zélotes, une cathédrale d'une foi dévoyée, et un cimetière hanté.
Les croisés sont bien armés, disciplinés et complètement fous — convaincus que tout le
monde est secrètement mort-vivant. Une architecture magnifique dissimulant un fanatisme
meurtrier.""",

    209: """Zul'Farrak : cité trolle à moitié ensevelie dans les sables de Tanaris, foyer des trolls
Sablefurie hostiles. Temples de pierre baignés de soleil, autels sacrificiels et cours
sablonneuses composent ce donjon à ciel ouvert. La célèbre bataille de l'escalier vous
oppose à des vagues de guerriers trolls. La chaleur du désert est implacable, les trolls
sont sauvages, et une magie ancienne crépite à travers les ruines.""",

    229: """Spire de la Roche noire : immense forteresse orque taillée dans les hauteurs de la
montagne de la Roche noire. La spire basse grouille d'orcs de la Roche noire, d'ogres et
de trolls, tandis que la spire haute est le siège du chef de guerre Rend Main-Noire et de
ses alliés draconiques. La lave luit en contrebas, les tambours de guerre résonnent sans
cesse, et l'air empeste la fumée et le sang. Un vaste bastion militaire au cœur de la
Horde noire.""",

    230: """Profondeurs de Roche noire : vaste cité des nains de Fer noir au cœur de la montagne de la
Roche noire, bâtie autour d'un lac de lave en fusion. La taverne du Gargouillis lugubre,
la salle du trône de l'Empereur et le seuil du Cœur du Magma se trouvent tous ici.
Élémentaires, golems et nains de Fer noir fanatiques peuplent une métropole souterraine
d'une ampleur incroyable. On croirait qu'une civilisation entière existe là, sombre,
industrieuse et hostile.""",

    269: """Le Marais Trouble-Temps : instance des Cavernes du Temps se déroulant dans le marécage
primordial qui deviendra les Terres Foudroyées. Des agents du clan draconique Infini
tentent d'empêcher Medivh d'ouvrir la Porte des Ténèbres, et des vagues de draconiens
attaquent à travers des failles temporelles. Le marais est sombre, embrumé et primitif, et
l'énergie de la Porte crépite au loin. Le temps lui-même semble instable ici.""",

    289: """Salle d'Examen de la Mort : académie nécromantique dans les cryptes sous Caer Darrow,
dirigée par le Culte des Damnés. Étudiants et professeurs de magie noire pratiquent leur
art sur les morts comme sur les vivants. Squelettes, fantômes et golems de chair
remplissent salles de classe et laboratoires. Le donjon dégage une atmosphère
universitaire perverse — amphithéâtres et bibliothèques entièrement voués à la magie de la
mort.""",

    329: """Stratholme : les ruines embrasées d'une cité jadis grande, à jamais en flammes depuis
qu'Arthas l'a purgée. Le Fléau mort-vivant contrôle la moitié orientale tandis que la
Croisade écarlate tient fanatiquement les portes occidentales. Les bâtiments s'effondrent
dans un feu perpétuel, des abominations traînent dans les rues, et les cendres ne se
déposent jamais. Un monument à la tragédie et à la folie — chaque coin de rue porte le
souvenir du massacre.""",

    349: """Maraudon : système de cavernes sacrées à Desolace, altéré par la princesse Theradras et
ses descendants centaures après la mort du gardien Zaetar. Trois voies codées par couleur
serpentent à travers des grottes de cristal, des cascades empoisonnées et de luxuriants
jardins souterrains avant d'atteindre le sanctuaire intérieur. Les chambres les plus
profondes sont d'une beauté envoûtante — cristaux luminescents, bassins limpides, et une
ancienne magie terrestre luttant contre la corruption. Nature, deuil et fureur élémentaire
s'y entremêlent.""",

    389: """Gouffre de Cendre-brûlante : réseau de cavernes volcaniques sous Orgrimmar même, où
cultistes de la Lame ardente et trogs se sont installés. La lave coule à travers d'étroits
tunnels, des élémentaires de feu patrouillent, et la chaleur est suffocante. Court et
brutal — le genre d'endroit qui rappelle que la Horde a bâti sa capitale sur un volcan.""",

    429: """Donjon de Feu-Sombre : cité en ruines des Éveillés dans Feralas, divisée en trois ailes.
Les ogres ont revendiqué le nord, satyres et anciens corrompus infestent l'est, et des
esprits Éveillés fantomatiques hantent la bibliothèque de l'aile ouest. Une architecture
elfique en ruine, d'une beauté saisissante, succombe lentement à l'envahissement de la
jungle. Le donjon semble vaste, ancien et mélancolique — le cadavre d'une grande
civilisation dépecé par des squatteurs.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Repaire d'Onyxia : une unique et vaste caverne dans le Marécage d'Aprefange, foyer de la
reine-mère Onyxia. L'approche serpente à travers un étroit tunnel de roche calcinée avant
de s'ouvrir sur une chambre immense, jonchée d'ossements et de couvées d'œufs. Les
dragonnets pullulent, la lave bouillonne sur les bords, et Onyxia elle-même emplit la
caverne de feu et d'ombre. Un tunnel claustrophobe menant à une arène écrasante de feu
draconique.""",

    309: """Zul'Gurub : vaste complexe de temples trolls dans les jungles de Strangleronce, où la
tribu Gurubashi a déchaîné le dieu du sang Hakkar. Cours envahies de végétation, autels
sacrificiels et places grouillantes de bêtes entourent un temple central suintant de magie
sanglante. Prêtres serpents, monteurs de chauves-souris et cultistes-tigres servent leurs
sombres maîtres. La jungle elle-même semble pulser d'une énergie vaudou primitive.""",

    409: """Le Cœur du Magma : le cœur ardent de la montagne de la Roche noire, un royaume de feu pur
gouverné par Ragnaros le Seigneur du Feu. Des rivières de lave coulent entre des
plateformes d'obsidienne, élémentaires de feu et géants de magma patrouillent partout, et
la chaleur est apocalyptique. Des molosses du Cœur à plusieurs têtes, d'imposants geysers
de lave et d'anciens éveilleurs de flammes gardent leur maître. L'ultime épreuve du feu —
belle et terrifiante à parts égales.""",

    469: """Repaire de l'Aile Noire : le bastion de Nefarian au sommet de la Spire de la Roche noire,
un laboratoire ténébreux où le dragon noir expérimente sur d'autres clans draconiques.
Soldats draconides, drakes chromatiques et expériences ratées emplissent des salles de fer
noir et d'os de dragon. Chaque chambre présente un défi tactique unique. Le raid dégage
une atmosphère clinique et sinistre — le repaire d'un savant fou à l'échelle d'un dragon.""",

    509: """Ruines d'Ahn'Qiraj : champ de bataille à ciel ouvert à Silithus où les forces qiraji se
rassemblent pour la guerre. Guerriers insectoïdes, destructeurs d'obsidienne et créatures
géantes en forme de scarabée déferlent sur des cours balayées par le sable et des ruines
de temples effondrées. L'architecture est étrangère et chitineuse, à mi-chemin entre
tombeau égyptien et ruche d'insectes. Le vent du désert porte le cliquetis d'un million de
pattes.""",

    531: """Temple d'Ahn'Qiraj : le sanctuaire intérieur scellé de l'empire qiraji, un cauchemar
d'architecture étrangère et de corruption des dieux anciens. Les empereurs jumeaux, une
royauté silithide massive, et le dieu ancien C'Thun lui-même se tapissent en son sein. Les
murs pulsent d'une croissance organique, des yeux observent depuis chaque surface, et la
réalité se déforme près de la prison du dieu ancien. L'endroit le plus étranger et le plus
dérangeant de l'Azeroth classique.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Salles brisées : le bastion des orcs corrompus au sein de la Citadelle des Flammes
Infernales, un parcours sanglant à travers les serviteurs les plus fanatiques de la Légion
ardente. Gladiateurs, légionnaires et berserkers orcs corrompus emplissent chaque couloir,
avec des prisonniers enchaînés aux murs. L'architecture est faite de fer brutal et de
pierre rouge, marquée par les traces d'une violence constante. Un assaut incessant contre
une forteresse qui riposte à chaque pas.""",

    542: """Fournaise ardente : une usine démoniaque au sein de la Citadelle des Flammes Infernales où
l'on fabrique des orcs corrompus par de sombres rituels. Cuves de sang bouillonnant,
prisonniers enchaînés attendant leur transformation, et machinerie démoniaque emplissent
des chambres fumantes. De jeunes orcs corrompus et leurs surveillants gardent les chaînes
de production. Le donjon empeste le sang et le soufre — un spectacle d'horreur
industrielle.""",

    543: """Remparts des Flammes Infernales : les fortifications extérieures de la Citadelle des
Flammes Infernales, première ligne de défense de l'armée des orcs corrompus. Tours de
guet, créneaux et passerelles étroites offrent une vue panoramique sur la Péninsule des
Flammes Infernales brisée en contrebas. Soldats orcs corrompus, monteurs de worgs et un
dragon captif gardent les murailles. Le vent hurle à travers les remparts brisés, et le
ciel rouge de l'Outreterre s'étend à l'infini au-dessus.""",

    545: """La Cuve à Vapeur : une station de pompage contrôlée par les naga dans le Réservoir de
Nasseau, où les forces de Dame Vashj drainent le Marécage de Zangar. D'immenses tuyaux,
vannes et canaux d'eau dominent cette structure industrielle. Naga, seigneurs des marais
et élémentaires d'eau gardent la machinerie. La vapeur siffle à chaque jointure et le
grondement des eaux vives est assourdissant. Un donjon qui donne l'impression de saboter
une usine ennemie.""",

    546: """Le Marais souterrain : marécage en putréfaction sous le Réservoir de Nasseau, grouillant
de créatures fongiques mutées et d'esprits de la nature hostiles. Géants sporifères,
seigneurs des marais et faune venimeuse emplissent les cavernes envahies de végétation.
Des champignons bioluminescents projettent une lueur inquiétante sur les eaux stagnantes.
L'air est chargé de spores et d'une odeur de décomposition — la nature devenue sauvage et
hostile.""",

    547: """Les Enclos des esclaves : les camps de travail du Réservoir de Nasseau où les draeneï
Corrompus sont retenus captifs par des maîtres esclavagistes naga. Tunnels détrempés,
enclos rudimentaires et surveillants naga armés de fouets définissent l'atmosphère. Des
croissances fongiques et des créatures des marais ont infiltré le complexe. Un donjon
empreint de misère et d'oppression, à moitié noyé et putréfié.""",

    552: """L'Arcatraz : une prison dimensionnelle satellite de la Citadelle des Tempêtes, retenant
les entités les plus dangereuses du cosmos. Des démonistes eredars, des créatures du Néant
et des saboteurs elfes de sang rôdent dans des blocs cellulaires conçus pour contenir des
horreurs indescriptibles. L'architecture est une technologie cristalline draeneï dévoyée
par ses détenus. Chaque porte de cellule dépassée vous fait vous demander ce qui s'est
échappé — et ce qui est encore enfermé à l'intérieur.""",

    553: """La Botanique : un vaste biodôme satellite de la Citadelle des Tempêtes, où l'on cultivait
jadis une flore exotique venue de tout le cosmos. Les elfes de sang se sont emparés de
l'installation, et les plantes ont poussé à l'état sauvage et hostile. Fouettards,
chênerons et spécimens botaniques étrangers emplissent des serres de cristal scintillant.
Magnifique mais mortel — chaque fleur pourrait vous tuer, et les elfes de sang sont pires
encore.""",

    554: """Le Mécanar : une aile de fabrication de la Citadelle des Tempêtes, désormais contrôlée par
des ingénieurs elfes de sang et leurs créations mécaniques. Constructs arcaniques,
ravageurs corrompus et surveillants némancien gardent des couloirs de cristal étincelant
et de machinerie bourdonnante. La technologie est élégante et étrangère — une ingénierie
draeneï détournée à des fins sinistres. Tout bourdonne d'une énergie arcanique à peine
contenue.""",

    555: """Labyrinthe des Ombres : l'aile la plus profonde d'Auchindoun, où le Conseil des Ombres
mène ses rituels les plus sombres. Marcheurs du Néant, incantateurs corrompus et cultistes
de la Cabale vénèrent dans des chambres saturées de magie des ombres. Murmure, un
élémentaire du son primordial, est enchaîné dans la chambre la plus profonde. L'obscurité
y semble vivante et affamée — les ombres bougent d'elles-mêmes, et des chuchotements
viennent de partout et de nulle part.""",

    556: """Salles de Sethekk : salles-temples arakkoa au sein d'Auchindoun, occupées par des
fanatiques dévoués au Dieu-corbeau Anzu. Prêtres arakkoa déments, esprits invoqués et
gardiens spectraux emplissent des couloirs jonchés de plumes. L'architecture mêle les
styles draeneï et arakkoa de façon troublante. Les habitants ont sombré dans une folie
totale, et les salles résonnent de cris déments et de sombres prophéties.""",

    557: """Les Tombeaux de Mana : l'aile infestée d'éthérés d'Auchindoun, où le consortium du
prince-nexus Shaffar pille les caveaux funéraires draeneï. Bandits éthérés, constructs
arcaniques et esprits draeneï agités s'affrontent dans des chambres funéraires
cristallines. Les tombeaux luisent d'une énergie sacrée résiduelle tandis que les éthérés
la siphonnent. Un lieu sacré systématiquement pillé par des voleurs interdimensionnels.""",

    558: """Cryptes des Auchenaï : les lieux funéraires draeneï sous Auchindoun, où les prêtres
auchenaï ont sombré dans la folie en communiant avec les morts. Esprits agités, clercs
possédés et draeneï morts-vivants emplissent les cryptes tapissées d'ossements. Ce qui fut
jadis un lieu de recueillement respectueux est devenu un charnier. La tragédie est
palpable — ces gardiens se sont perdus dans le chagrin.""",

    560: """Contreforts de Hautebrande d'antan : instance des Cavernes du Temps se déroulant dans le
passé, quand Thrall était encore esclave au fort de Durnholde. Le Hautebrande d'autrefois
est verdoyant, paisible et peuplé d'humains insouciants vaquant à leur vie. Le clan
draconique Infini tente d'altérer l'histoire en empêchant l'évasion de Thrall. C'est
surréaliste — traverser un lieu qu'on connaît avant que tout ne tourne mal.""",

    568: """Zul'Aman : bastion des trolls des forêts dans les Terres fantômes, où le seigneur de
guerre Zul'jin a doté ses champions de l'essence de dieux animaux. Esprits de lynx,
d'ours, d'aigle et de dracochevaux imprègnent les gardiens du temple troll. L'architecture
du temple-forêt amani est vive et primitive, décorée de masques, de totems et de peintures
de guerre. Un parcours chronométré où la vitesse compte et où les tambours trolls ne
cessent jamais de battre.""",

    585: """Terrasse des Magistres : le dernier bastion de Kael'thas Soleil-filant sur l'Île de
Quel'Danas, un palais elfe de sang d'une élégance saisissante dissimulant une corruption
démoniaque. Des cristaux corrompus alimentent des constructs arcaniques, des magistres
elfes de sang canalisent une magie interdite, et un naaru captif est vidé de sa Lumière.
La beauté de l'architecture de Lune-d'Argent, tordue par le désespoir et la dépendance —
des salles dorées dissimulant un pacte monstrueux.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan : la tour hantée du dernier Gardien, Medivh, dans le Défilé de Deuillevent. Un
dîner spectral, une scène d'opéra aux interprètes fantomatiques, une partie d'échecs
prenant vie, et un observatoire céleste emplissent cette tour d'une hauteur impossible. La
tour existe partiellement hors de la réalité normale — les pièces se déplacent, le temps
se distord, et les échos de la folie de Medivh se rejouent éternellement. D'une beauté
envoûtante, profondément troublante, et absolument unique.""",

    534: """Sommet du Mont Hyjal : un raid des Cavernes du Temps se déroulant durant la Bataille du
Mont Hyjal, l'affrontement final contre Archimonde et la Légion ardente. Des vagues de
morts-vivants et de démons assaillent trois bases successives — humaine, de la Horde, et
elfe de la nuit. L'arbre-monde Nordrassil se dresse au-dessus tandis que la forêt brûle.
Un scénario de défense épique où le destin d'Azeroth est en jeu et où des héros
légendaires combattent à vos côtés.""",

    544: """Repaire de Magtheridon : une unique chambre brutale sous la Citadelle des Flammes
Infernales où le seigneur de la fosse Magtheridon est enchaîné. Des canalisateurs
maintiennent sa prison tandis que l'énergie des flammes infernales pulse dans la pièce.
L'espace est oppressivement chaud, empestant le sang de démon et le soufre. Une
confrontation directe mais impitoyable — un démon massif, une salle mortelle, aucune place
pour l'erreur.""",

    548: """Caverne de l'Écume-de-serpent : le bastion sous-marin de Dame Vashj dans le Réservoir de
Nasseau, un palais inondé d'une beauté corrompue. Naga, ondemarcheurs et hydres colossales
gardent des chambres où des cascades se déversent dans des bassins luminescents. Des ponts
enjambent des lacs souterrains, et les chambres les plus profondes pulsent des eaux
corrompues du Marécage de Zangar. Une architecture naga élégante rencontre la puissance
brute d'un océan souterrain.""",

    550: """La Citadelle des Tempêtes - L'Œil : la forteresse naaru capturée de Kael'thas
Soleil-filant, une citadelle cristalline flottant au-dessus de Raz-de-néant. Conseillers
elfes de sang, constructs arcaniques et créatures du Néant gardent des chambres de cristal
draeneï scintillant. La technologie est à la fois étrangère et magnifique à couper le
souffle, détournée par des elfes désespérés nourrissant leur dépendance à la magie. La vue
sur Raz-de-néant brisé depuis les plateformes est aussi saisissante que terrifiante.""",

    564: """Temple noir : la forteresse d'Illidan Hurlorage dans la Vallée d'Ombrelune, un immense
temple draeneï corrompu par une occupation démoniaque. Orcs corrompus, démons, naga et
elfes de sang servent le Traître à travers de vastes cours, des égouts et de grandes
salles. La beauté originelle du temple est balafrée par la corruption démoniaque —
symboles sacrés fissurés, autels profanés, et feu vert là où brillait jadis la Lumière.
L'aboutissement de l'histoire de l'Outreterre, se terminant devant le trône d'Illidan.""",

    565: """Repaire de Gruul : un rude complexe de cavernes dans les Tranchantes, foyer du père gronn
Gruul le Tueur-de-dragons. Serviteurs ogres et fils monstrueux de Gruul gardent l'approche
de sa chambre, jonchée d'ossements de dragons et de trophées. Les grottes semblent
primitives et brutales — aucune architecture, aucun ornement, seulement de la roche brute
façonnée par les poings de géants.""",

    580: """Plateau du Puits de Soleil : le raid final de la Croisade ardente, situé au cœur du Puits
de Soleil restauré sur l'Île de Quel'Danas. La Légion ardente tente d'invoquer Kil'jaeden
à travers le Puits de Soleil lui-même. Une architecture elfique immaculée d'une beauté à
couper le souffle encadre une bataille désespérée contre les démons les plus puissants de
l'armée de la Légion. La lumière sacrée du Puits de Soleil s'oppose aux ténèbres
démoniaques dans chaque chambre.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Fort d'Utgarde : forteresse vrykul sur les rives du Fjord Hurlant, premier avant-goût des
dangers du Norfendre. Des salles d'inspiration viking en pierre sombre et fer, éclairées
par des âtres rugissants et ornées de crânes de dragons. Guerriers vrykuls, dresseurs de
proto-drakes et leurs serviteurs morts-vivants emplissent les grandes salles. Le donjon
donne l'impression de mettre à sac une longère nordique — froid, brutal, et empreint d'une
culture guerrière.""",

    575: """Pinacle d'Utgarde : les hauteurs du Fort d'Utgarde, où le roi vrykul Ymiron règne depuis
son trône gelé. Salles de trophées, volières d'aigles et chambres rituelles dominent le
fjord. L'architecture devient plus grandiose et plus menaçante à mesure qu'on s'élève,
culminant dans la salle du trône givré d'Ymiron. Le vent hurle à travers les créneaux
ouverts, et la vue sur le paysage gelé en contrebas donne le vertige.""",

    576: """Le Nexus : les grottes cristallines sous Coldarra, bastion de la guerre du clan draconique
Bleu contre la magie mortelle. Des cavernes gelées d'une beauté impossible renferment des
anomalies arcaniques, des chasseurs de mages déments et des failles dans la réalité. Des
dragons cristallisés restent figés en plein vol. Le donjon scintille d'une énergie
arcanique instable — bleus, violets et blancs se réfractant à travers la glace et le
cristal dans toutes les directions.""",

    578: """L'Oculus : les anneaux supérieurs du Nexus, une série de plateformes flottantes reliées
par des ponts magiques loin au-dessus du nexus de lignes telluriques. Les joueurs montent
des drakes pour naviguer entre les segments d'anneau tout en combattant les forces de
Malygos. Le vide s'étend en contrebas, l'énergie arcanique crépite entre les plateformes,
et le vertige est bien réel. Un donjon qui donne l'impression de voler à travers une
tempête magique au bord de la réalité.""",

    595: """L'Épuration de Stratholme : instance des Cavernes du Temps se déroulant durant la purge
fatidique de la cité pestiférée par Arthas. Les rues de Stratholme sont intactes mais
condamnées — les citoyens se transforment en morts-vivants sous vos yeux, et Arthas
ordonne froidement leur mise à mort avant la transformation. Le donjon est singulièrement
troublant, car vous contribuez à l'atrocité qui amorce la chute d'Arthas. Le moment le
plus sombre de l'histoire, revécu.""",

    599: """Salles de Pierre : une installation des titans dans les Pics Foudroyés, faisant partie du
vaste complexe d'Ulduar. Des couloirs de pierre à la perfection géométrique abritent des
constructs des titans défaillants, des nains de fer et d'anciens systèmes de défense. Le
Tribunal des Âges conserve les archives de la création elle-même. Le donjon dégage une
atmosphère érudite et ancienne — un musée où les expositions ripostent et où l'histoire
qui y est conservée pourrait briser des civilisations.""",

    600: """Fort de Drak'Tharon : forteresse trolle infestée par le Fléau, à la frontière des
Grisonnes et de Zul'Drak. Le Fléau a relevé les trolls morts et corrompu leurs bêtes
dinosaures, créant une fusion impie de culture trolle et de pouvoir nécromantique. Raptors
squelettiques, trolls zombifiés et la liche Novos l'Invocatrice emplissent les salles
délabrées. Une architecture trolle s'effondrant sous le poids de la non-mort.""",

    601: """Azjol-Nerub : le royaume nérubien en ruines sous le Norfendre, une descente verticale
étouffée de toiles à travers l'empire des araignées. L'architecture nérubienne de soie et
de chitine s'étend à travers de vastes gouffres souterrains. Des nérubiens morts-vivants
servent le Fléau tandis que les vivants se battent désespérément. Le donjon vous entraîne
toujours plus profond à travers des sols qui s'effondrent — claustrophobe, étranger, et
grouillant de choses qui ne devraient pas exister.""",

    602: """Salles de la Foudre : un complexe de forges des titans dans Ulduar, crépitant d'énergie
électrique. Nains de fer, géants des tempêtes et constructs runiques gardent des couloirs
de métal étincelant traversés d'éclairs. Loken, le gardien titan corrompu, attend dans la
chambre la plus profonde. Chaque surface bourdonne de puissance, des étincelles dansent
sur les murs, et le tonnerre de la forge est constant et assourdissant.""",

    604: """Gundrak : temple troll des Drakkari à Zul'Drak, où les trolls sacrifient leurs propres
dieux animaux pour alimenter leur guerre contre le Fléau. Le sang divin coule sur les
autels tandis que les esprits du serpent, du mammouth et du rhinocéros sont consumés. Le
temple est massif et primitif — pierre sculptée, bassins rituels, et l'énergie désespérée
d'une civilisation mourante brûlant ses propres dieux pour survivre.""",

    608: """Antre Violet : prison magique sous Dalaran, où le Kirin Tor retient les créatures les plus
dangereuses du Norfendre. Des agents du clan draconique Azur assaillent la prison depuis
des portails, libérant des détenus par vagues. L'architecture est un élégant violet et
argent typique de Dalaran, mais les détenus sont cauchemardesques. Un scénario de défense
de tour dans le donjon d'un mage — les protections arcaniques peinent à contenir le chaos.""",

    619: """Ahn'kahet : l'Ancien Royaume : les profondeurs les plus reculées d'Azjol-Nerub, où les
Sans-Visage servent le dieu ancien Yogg-Saron. L'architecture passe du nérubien à quelque
chose de bien plus ancien et plus étranger — les murs organiques pulsent, la réalité se
déforme, et des effets de folie assaillent l'esprit. Oubliés, jeteurs de sorts et le
héraut Volazj se tapissent dans des chambres qui défient toute géométrie. Le donjon le
plus troublant du Norfendre.""",

    632: """Forge des Âmes : le premier des trois donjons de la Citadelle de la Couronne de Glace, une
machine broyeuse d'âmes où le Roi-liche traite les morts. Des fleuves d'âmes torturées
coulent à travers une machinerie de fer, des forgerons spectraux martèlent des enclumes de
souffrance, et le Dévoreur d'Âmes garde la forge. Les hurlements ne s'arrêtent jamais. Un
cauchemar industriel alimenté par un tourment éternel.""",

    650: """Épreuve du Champion : une grande arène de tournoi sous le Colisée argenté en Couronne de
Glace, où les champions de l'Alliance et de la Horde prouvent leur valeur. Joutes à
cheval, duels de champions et une ultime embuscade du Chevalier noir se déroulent sur le
terrain du tournoi. L'atmosphère est festive et compétitive jusqu'à ce que les
morts-vivants ne fassent irruption dans la fête. Faste et spectacle avec un revirement
sombre.""",

    658: """Fosse de Saron : une mine d'esclaves brutale en Couronne de Glace où les forces du Fléau
font travailler des prisonniers jusqu'à la mort pour extraire du saronite. La fosse est
ouverte au ciel gelé, avec d'immenses chaînes, des plateformes minières et des gisements
de saronite partout. Le maître-forgeron Frimasfort lance des rochers tandis que Tyrannus
patrouille au-dessus sur son drake du couvoir givré. Désespoir et cruauté distillés dans
la pierre gelée et le métal sombre.""",

    668: """Salles de Réflexion : les Salles gelées hantées de la Citadelle de la Couronne de Glace,
où les échos des victimes de Frostmourne s'attardent autour de la chambre de la lame. Le
Roi-liche lui-même vous poursuit à travers des couloirs qui s'effondrent tandis que des
vagues de fantômes attaquent. Les salles sont de glace immaculée et de saronite sombre, et
la terreur est bien réelle — vous ne pouvez pas le combattre, seulement fuir. Le donjon le
plus intense narrativement du jeu, une fuite désespérée devant un destin inévitable.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas : la nécropole flottante de l'archiliche Kel'Thuzad, planant au-dessus de la
Désolation des Dragons. Quatre ailes d'horreurs thématiques — le Quartier Arachnéen des
araignées géantes, le Quartier de la Peste de la maladie et des abominations, le Quartier
Militaire des commandants chevaliers de la mort, et le Quartier des Constructs des golems
de chair. Une architecture gothique de pierre sombre et de vase verte, avec la froide
précision d'une organisation militaire morte-vivante. Le chef-d'œuvre de mort du Fléau.""",

    603: """Ulduar : une cité-prison des titans dans les Pics Foudroyés, le plus grandiose raid du
Norfendre. D'immenses salles de métal et de pierre étincelants abritent les gardiens
titans corrompus et leurs serviteurs, tandis que le dieu ancien Yogg-Saron est emprisonné
dans le caveau le plus profond. L'ampleur est stupéfiante — batailles de véhicules aux
portes, un observatoire ouvert sur le cosmos, des jardins d'une beauté surnaturelle, et
une descente dans la folie elle-même. Ancien, magnifique et terrifiant.""",

    615: """Sanctuaire d'Obsidienne : une chambre volcanique sous le Temple du Repos-des-Dragons où
Sartharion garde des œufs de dragons crépusculaires. Des rivières de lave divisent les
plateformes d'obsidienne, et trois lieutenants drakes crépusculaires patrouillent leurs
propres îlots. La chambre luit d'orange et de rouge, la chaleur déforme l'air en ondulant,
et la trahison du clan draconique Noir est mise à nu. Une arène directe de feu et
d'écailles.""",

    616: """Sanctuaire de l'Éternité : le sanctuaire personnel de Malygos au sommet du Nexus au-dessus
de Coldarra, une plateforme suspendue dans une énergie tellurique brute. Il n'y a ni sol
ni murs — seulement un disque de force magique au-dessus d'un vide d'arcane bleu et violet
tourbillonnant. Le Tisse-sorts attaque avec toute la puissance du clan draconique Bleu. Le
raid semble surnaturel — affronter un aspect draconique au cœur de la tempête arcanique
d'Azeroth.""",

    624: """Caveau d'Archavon : un caveau des titans sous la forteresse de Grognard, accessible
uniquement à la faction contrôlant la zone. Géants de pierre et constructs élémentaires
gardent les chambres dans une série directe de combats de boss. L'architecture est un
design titan utilitaire — fonctionnel, massif et dépourvu d'ornement. Une récompense pour
une victoire en JcJ, rapide et brutale.""",

    631: """Citadelle de la Couronne de Glace : le trône du Roi-liche, l'aboutissement de l'ère du
Roi-liche. Une forteresse imposante de saronite et de glace s'élevant au cœur de la
Couronne de Glace. Chaque aile intensifie l'horreur — des armées mortes-vivantes de la
Spire basse, en passant par les Ouvroirs de la Peste, la Salle cramoisie et les Salles de
l'Aile givrée, jusqu'au Trône gelé lui-même. L'architecture est oppressante, belle dans sa
cruauté, et conçue pour briser l'espoir. C'est la fin.""",

    649: """Épreuve du Croisé : le Colisée argenté en Couronne de Glace, une arène de tournoi qui
s'enfonce dans la terre lorsque le sol s'effondre dans une caverne nérubienne souterraine.
Le niveau supérieur est fait de bannières éclatantes et de foules en liesse ; le niveau
inférieur est une horreur chitineuse, domaine d'Anub'arak. Le contraste entre la
compétition festive au-dessus et la terreur ancienne en dessous définit toute
l'expérience.""",

    724: """Sanctuaire Rubis : une chambre sous le Temple du Repos-des-Dragons où le clan draconique
Crépusculaire a envahi le sanctuaire des dragons rouges. Halion, le destructeur
crépusculaire, oscille entre le plan physique et le plan des ombres. La chambre alterne
entre une chaude lumière rubis et une froide ombre violette. Le dernier raid avant le
Cataclysme — un bref et sinistre avertissement de la destruction à venir.""",
}

# German (deDE) dungeon/raid flavor text -- translated from the
# DUNGEON_FLAVOR entries above (same map-ID keys, same
# paragraph-length atmospheric lore), not injected verbatim since
# the English text was leaking untranslated into German bot chat.
# Falls back to English DUNGEON_FLAVOR via get_dungeon_flavor() for
# any locale other than deDE/frFR/ruRU, mirroring ZONE_FLAVOR_DE/
# get_zone_flavor()'s convention. Proper nouns reuse community-
# sourced German WoW terms (Shadowfang Keep -> Schattenfangfeste,
# Ironforge -> Eisenschmiede, etc.), same confidence tier as
# ZONE_FLAVOR_DE/RACE_SPEECH_PROFILES_DE above (community/
# wiki-sourced, not independently verified against official client
# DBC data).
DUNGEON_FLAVOR_DE = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Schattenfangfeste: Eine von Geistern heimgesuchte Festung im Silberwald, überrannt von
Worgen und den untoten Dienern des Nekromanten Arugal. Geisterhafte Adlige wandern durch
die dunklen Hallen, spektrale Hunde heulen in den Höfen, und misslungene arkane
Experimente lauern in jedem Schatten. Die Feste fühlt sich an wie eine gotische
Horrorgeschichte - kalter Stein, flackerndes Fackellicht und das ständige Gefühl,
beobachtet zu werden.""",

    34: """Das Verlies: Ein Gefängnis unter Sturmwind, in dem die Insassen revoltiert und die
Kontrolle übernommen haben. Aufständische der Defias, wahnsinnige Sträflinge und
Bandenführer streifen durch die engen Steinzellenblöcke. Der Dungeon ist klaustrophobisch
und brutal - schmale Gänge, Eisenstäbe und das Echo von Gewalt an feuchten Wänden.
Schnell, schmutzig und gefährlich.""",

    36: """Die Todesminen: Ein weitläufiger Minenkomplex unter Westfall, heimlich das
Hauptquartier der Bruderschaft der Defias. Der Weg windet sich durch von Goblins
konstruierte Tunnel, Sägewerke und Schmelzanlagen, bevor er in eine gewaltige
unterirdische Höhle mündet, in der ein Piratenschiff in Originalgröße in einer
verborgenen Bucht liegt. Es fühlt sich an, als entdecke man ein kriminelles Imperium
direkt vor Sturmwinds Toren.""",

    43: """Klagende Höhlen: Ein Labyrinth aus gewundenen Höhlen in den Steppen, überwuchert von
üppiger Vegetation, genährt von verdorbener Druidenmagie. Missgestaltete Kreaturen -
mutierte Echsen, Schlangen und Schleime - schlängeln sich durch die smaragdgrün
schimmernden Tunnel. Die Druiden des Fangs haben sich im Smaragdgrünen Albtraum
verloren. Die Luft ist dick, feucht und riecht nach Dschungelfäulnis.""",

    47: """Dornenkrallenpferch: Ein dorniges Labyrinth aus gewaltigen Dornenranken in den
Steppen, Heimat der Wildschweinmenschen und ihrer Matriarchin Charlga Klingenhauer.
Wildschweinmenschen-Krieger, Schamanen und ihre Wildschweingefährten füllen die
gewundenen, dornbewachsenen Gänge. Der Dungeon wirkt urtümlich und wild - Natur,
verdreht zu einer Festung aus Knochen, Dornen und Schlamm.""",

    48: """Schwarzflossentiefen: Ein teilweise überfluteter uralter Tempel an der Küste der
Dunkelküste, geweiht dunklen Mächten. Naga, Satyrn und Zwielicht-Kultisten verehren
alte Götter in gefluteten Hallen, geschmückt mit bröckelnder Nachtelfen-Architektur.
Das Wasser leuchtet in einem unheimlichen Blaugrün, und die Atmosphäre ist bedrückend
und uralt - etwas Mächtiges schläft in den tiefsten Becken.""",

    70: """Uldaman: Eine Ausgrabungsstätte der Titanen, vergraben im Ödland, halb Grabung, halb
Dungeon. Steintroggs, irdene Konstrukte und archäologische Gefahren füllen Kammern
aus poliertem Titanenmetall und rohem Fels. Je tiefer man vordringt, desto
fremdartiger wird die Architektur - glatte geometrische Hallen, die von ruhender
Macht summen. Es fühlt sich an, als betrete man unbefugt eine von Göttern erbaute
Bibliothek.""",

    90: """Gnomeregan: Die verstrahlten Ruinen der gnomischen Hauptstadt, verloren an eine
Trogg-Invasion und ein katastrophales Strahlenleck. Wahnsinnige Leprakin-Gnome,
fehlfunktionierende Roboter und toxische Schleime bevölkern den mehrstöckigen
mechanischen Komplex. Alarmsirenen heulen, grüne Strahlungspfützen leuchten, und
überall funkt zerbrochene Maschinerie. Gleichermaßen tragisch und absurd.""",

    109: """Versunkener Tempel: Der Tempel des Atal'Hakkar, ein Trolltempel, von der Grünen
Drachenschwinge unter die Sümpfe gezogen. Atal'ai-Trolle verehren den Blutgott
Hakkar in gefluteten, von Ranken überwucherten Hallen. Drachkin bewachen die
tieferen Ebenen, und das labyrinthartige Layout ist verwirrend. Die Atmosphäre ist
schwer von Dschungelfeuchtigkeit, uralter Trollmagie und dem Gefühl eines verbotenen
Rituals.""",

    129: """Dornenkrallenruh: Eine Grabstätte der Wildschweinmenschen in den Steppen, verseucht
von Untoten. Der Geißel-Agent Amnennar der Kältebringer hat die toten
Wildschweinmenschen erweckt und ihre heiligen Krypten in eine Nekropole aus Knochen
und Dornen verwandelt. Skelettierte Wildschweinmenschen und Pestfledermäuse füllen
die düsteren Gänge. Ein Ort, an dem zwei Arten des Todes aufeinanderprallen - urtümlich
und nekromantisch.""",

    189: """Kloster der Scharlachroten: Ein befestigtes Kloster in Tirisfal, Bollwerk des
fanatischen Scharlachroten Kreuzzugs. Vier Flügel beherbergen eine Bibliothek
verbotener Texte, eine Waffenkammer voller Fanatiker, eine Kathedrale verdrehten
Glaubens und einen von Geistern heimgesuchten Friedhof. Die Kreuzritter sind gut
bewaffnet, diszipliniert und völlig wahnsinnig - überzeugt, dass jeder heimlich
untot ist. Prächtige Architektur, die mörderischen Fanatismus verbirgt.""",

    209: """Zul'Farrak: Eine Trollstadt, halb begraben im Sand von Tanaris, Heimat der
feindseligen Sandfury-Trolle. Sonnenverbrannte Steintempel, Opferaltäre und
sandige Innenhöfe bilden diesen Freiluft-Dungeon. Die berühmte Treppenschlacht
stellt euch gegen Wellen von Trollkriegern. Die Wüstenhitze ist unerbittlich, die
Trolle sind wild, und uralte Magie knistert durch die Ruinen.""",

    229: """Schwarzfelsspitze: Eine gewaltige Orc-Festung, gehauen in die oberen Höhen des
Schwarzfelsbergs. Die untere Spitze wimmelt von Schwarzfels-Orcs, Ogern und
Trollen, während die obere Spitze der Sitz von Kriegshäuptling Rend Schwarzhand
und seinen Drachkin-Verbündeten ist. Lava glüht darunter, Kriegstrommeln hallen
unaufhörlich, und die Luft stinkt nach Rauch und Blut. Eine weitläufige
Militärfestung im Herzen der Schwarzen Horde.""",

    230: """Schwarzfelstiefen: Eine gewaltige Stadt der Dunkeleisenzwerge tief im Inneren des
Schwarzfelsbergs, erbaut um einen See geschmolzener Lava. Die Taverne "Grimmiger
Schlund", der Thronsaal des Kaisers und die Schwelle zum Feuerland - alles ist
hier zu finden. Elementare, Golems und fanatische Dunkeleisenzwerge füllen eine
unglaublich große unterirdische Metropole. Es fühlt sich an, als existiere hier
unten eine ganze Zivilisation, dunkel, geschäftig und feindselig.""",

    269: """Der Schwarze Morast: Eine Instanz der Höhlen der Zeit, angesiedelt im urzeitlichen
Sumpf, der einst zu den Verwüsteten Landen werden sollte. Agenten der Unendlichen
Drachenschwinge versuchen zu verhindern, dass Medivh das Dunkle Portal öffnet, und
Wellen von Drachkin stürmen durch Zeitrisse. Der Sumpf ist dunkel, neblig und
urzeitlich, während die Energie des Portals in der Ferne knistert. Die Zeit selbst
wirkt hier instabil.""",

    289: """Scholomance: Eine nekromantische Akademie in den Krypten unter Caer Darrow, geführt
vom Kult der Verdammten. Schüler und Professoren der dunklen Magie üben ihr
Handwerk an Toten wie Lebenden aus. Skelette, Geister und Fleischgolems füllen
Klassenzimmer und Laboratorien. Der Dungeon hat eine pervers gelehrte Atmosphäre -
Hörsäle und Bibliotheken, die vollständig der Todesmagie gewidmet sind.""",

    329: """Stratholme: Die brennenden Ruinen einer einst großen Stadt, für immer in Flammen
seit Arthas sie läuterte. Die untote Geißel kontrolliert die östliche Hälfte,
während der Scharlachrote Kreuzzug fanatisch die westlichen Tore hält. Gebäude
zerfallen in ewigem Feuer, Abscheulichkeiten stapfen durch die Straßen, und die
Asche legt sich nie. Ein Denkmal der Tragödie und des Wahnsinns - jede Ecke birgt
die Erinnerung an das Gemetzel.""",

    349: """Maraudon: Ein heiliges Höhlensystem in Desolace, verzerrt von Prinzessin Theradras
und ihren Zentauren-Nachkommen nach dem Tod des Wächters Zaetar. Drei farblich
gekennzeichnete Pfade winden sich durch kristalline Höhlen, giftige Wasserfälle
und üppige unterirdische Gärten, bevor sie das innere Heiligtum erreichen. Die
tieferen Kammern sind von eindringlicher Schönheit - leuchtende Kristalle, klare
Teiche und uralte Erdmagie, die gegen die Verderbnis ankämpft. Natur, Trauer und
elementarer Zorn, ineinander verwoben.""",

    389: """Ragefire-Schlucht: Ein vulkanisches Höhlensystem unter Orgrimmar selbst, wo sich
Kultisten der Brennenden Klinge und Troggs niedergelassen haben. Lava fließt durch
enge Tunnel, Feuerelementare patrouillieren, und die Hitze ist erstickend. Kurz
und brutal - die Art von Ort, die einen daran erinnert, dass die Horde ihre
Hauptstadt auf einem Vulkan erbaut hat.""",

    429: """Düsterbruch: Eine zerstörte Stadt der Hochgeborenen in Feralas, unterteilt in
drei Flügel. Oger haben den Norden beansprucht, Satyrn und verdorbene Ahnen
verseuchen den Osten, und geisterhafte Hochgeborene-Seelen spuken in der
Bibliothek des Westflügels. Zerfallende Elfen-Architektur von atemberaubender
Schönheit erliegt langsam dem wuchernden Dschungel. Der Dungeon fühlt sich
gewaltig, uralt und melancholisch an - der Leichnam einer großen Zivilisation,
ausgeschlachtet von Besetzern.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """Onyxias Hort: Eine einzelne gewaltige Höhle in den Düstermarschen, Heimat der
Bruthüterin Onyxia. Der Zugang windet sich durch einen engen Tunnel aus versengtem
Fels, bevor er sich zu einer riesigen Kammer öffnet, übersät mit Knochen und
Gelegen. Welpen schwärmen aus, Lava blubbert an den Rändern, und Onyxia selbst
erfüllt die Höhle mit Feuer und Schatten. Ein klaustrophobischer Tunnel, der in
eine überwältigende Arena aus Drachenfeuer mündet.""",

    309: """Zul'Gurub: Ein gewaltiger Trolltempel-Komplex im Dschungel von Schlingendorn, wo der
Gurubashi-Stamm den Blutgott Hakkar entfesselt hat. Überwucherte Innenhöfe,
Opferaltäre und von Bestien bevölkerte Plätze umgeben einen zentralen Tempel, der
von Blutmagie trieft. Schlangenpriester, Fledermausreiter und Tigerkultisten
dienen ihren dunklen Herren. Der Dschungel selbst scheint vor urtümlicher
Voodoo-Energie zu pulsieren.""",

    409: """Geschmolzener Kern: Das brennende Herz des Schwarzfelsbergs, ein Reich aus reinem
Feuer, beherrscht von Ragnaros, dem Feuerlord. Lavaströme fließen zwischen
Obsidianplattformen, Feuerelementare und schmelzende Riesen patrouillieren
überall, und die Hitze ist apokalyptisch. Kernhunde mit mehreren Köpfen,
aufragende Lavawoger und uralte Flammenwecker bewachen ihren Herrn. Die ultimative
Feuerprobe - gleichermaßen wunderschön und schrecklich.""",

    469: """Schwarzflügelhort: Nefarians Bollwerk auf der Schwarzfelsspitze, ein dunkles
Laboratorium, in dem der schwarze Drache mit anderen Drachenschwingen
experimentiert. Drakonidensoldaten, chromatische Drachen und misslungene
Experimente füllen Hallen aus Dunkeleisen und Drachenknochen. Jede Kammer stellt
eine einzigartige taktische Herausforderung dar. Der Raid wirkt klinisch und
unheilvoll - das Versteck eines wahnsinnigen Wissenschaftlers, hochskaliert auf
Drachenausmaße.""",

    509: """Ruinen von Ahn'Qiraj: Ein Freiluft-Schlachtfeld in Silithus, wo sich Qiraji-
Streitkräfte zum Krieg sammeln. Insektoide Krieger, Obsidian-Zerstörer und
gewaltige käferähnliche Kreaturen schwärmen über sandverwehte Innenhöfe und
zerfallende Tempelruinen. Die Architektur ist fremdartig und chitinös,
gleichermaßen ägyptisches Grabmal und Insektenbau. Der Wüstenwind trägt das
Klicken von einer Million Beinen.""",

    531: """Tempel von Ahn'Qiraj: Das versiegelte innere Heiligtum des Qiraji-Imperiums, ein
Albtraum aus fremdartiger Architektur und der Verderbnis alter Götter. Die
Zwillingskaiser, gewaltige silithidische Königlichkeit und der uralte Gott
C'Thun selbst lauern im Inneren. Wände pulsieren mit organischem Wachstum, Augen
beobachten von jeder Oberfläche, und die Realität verbiegt sich nahe dem Gefängnis
des alten Gottes. Der fremdartigste und beunruhigendste Ort im klassischen
Azeroth.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Zerschmetterte Hallen: Das Bollwerk der Teufelsorks in der Höllenfeuerzitadelle,
ein blutgetränkter Spießrutenlauf durch die fanatischsten Diener der Brennenden
Legion. Teufelsork-Gladiatoren, Legionäre und Berserker füllen jeden Gang, mit
Gefangenen, die an die Wände gekettet sind. Die Architektur besteht aus brutalem
Eisen und rotem Stein, gezeichnet von den Beweisen ständiger Gewalt. Ein
unerbittlicher Angriff auf eine Festung, die sich bei jedem Schritt zur Wehr
setzt.""",

    542: """Blutschmiede: Eine dämonische Fabrik in der Höllenfeuerzitadelle, in der
Teufelsorks durch dunkle Rituale hergestellt werden. Bottiche mit kochendem Blut,
gefangene Häftlinge, die auf ihre Verwandlung warten, und teuflische Maschinerie
füllen die dampfenden Kammern. Werdende Teufelsorks und ihre Aufseher bewachen
die Fertigungslinien. Der Dungeon stinkt nach Blut und Schwefel - eine
industrielle Horrorshow.""",

    543: """Höllenfeuerbollwerk: Die äußeren Befestigungen der Höllenfeuerzitadelle, erste
Verteidigungslinie der Teufelsork-Armee. Wachtürme, Zinnen und schmale
Laufstege bieten weite Ausblicke auf die zerschmetterte Höllenfeuerhalbinsel
darunter. Teufelsork-Soldaten, Worgreiter und ein gefangener Drache bewachen die
Mauern. Der Wind heult durch zerbrochene Bollwerke, und der rote Himmel Outlands
erstreckt sich endlos darüber.""",

    545: """Dampfkessel: Eine von Naga kontrollierte Wasserpumpstation im Rollfangreservoir,
wo Lady Vashjs Streitkräfte die Zangarmarschen entwässern. Massive Rohre,
Ventile und Wasserkanäle beherrschen die industrielle Anlage. Naga, Sumpflords
und Wasserelementare bewachen die Maschinerie. Dampf zischt aus jeder Fuge, und
das Tosen des strömenden Wassers ist ohrenbetäubend. Ein Dungeon, der sich
anfühlt wie die Sabotage einer feindlichen Fabrik.""",

    546: """Der Modermorast: Ein eiternder Sumpf unter dem Rollfangreservoir, wimmelnd von
mutierten Pilzkreaturen und feindseligen Naturgeistern. Sporenriesen, Sumpflords
und giftige Tierwelt füllen die überwucherten Höhlen. Biolumineszente Pilze
werfen ein unheimliches Leuchten über stagnierende Tümpel. Die Luft ist dick von
Sporen und dem Geruch der Verwesung - wild gewordene, feindselig gewordene
Natur.""",

    547: """Die Sklavengruben: Die Arbeitslager des Rollfangreservoirs, wo die Zerschlagenen
Draenei von Naga-Sklaventreibern gefangen gehalten werden. Wassergetränkte
Tunnel, primitive Gehege und Naga-Aufseher mit ihren Peitschen bestimmen die
Atmosphäre. Pilzwucherungen und Sumpfkreaturen haben den Komplex infiltriert. Ein
Dungeon, durchdrungen von Elend und Unterdrückung, halb ertrunken und
verrottend.""",

    552: """Der Arcatraz: Ein dimensionaler Gefängnissatellit der Sturmfeste, in dem die
gefährlichsten Wesen des Kosmos gefangen gehalten werden. Eredar-Hexenmeister,
Leerwesen und blutelfische Saboteure streifen durch Zellenblöcke, entworfen, um
Schrecken jenseits der Vorstellungskraft einzudämmen. Die Architektur ist
kristalline Draenei-Technologie, verzerrt von ihren Insassen. Jede Zellentür, an
der man vorbeikommt, lässt einen fragen, was entkommen ist - und was noch
eingesperrt ist.""",

    553: """Die Botanika: Ein gewaltiger Biodom-Satellit der Sturmfeste, in dem einst
exotische Flora aus dem gesamten Kosmos kultiviert wurde. Blutelfen haben die
Anlage in Besitz genommen, und die Pflanzen sind wild und feindselig gewachsen.
Peitschenpflanzen, Baumwesen und außerirdische botanische Exemplare füllen
Gewächshäuser aus schimmerndem Kristall. Wunderschön, aber tödlich - jede Blüte
könnte einen töten, und die Blutelfen sind schlimmer.""",

    554: """Der Mechanar: Ein Fertigungsflügel der Sturmfeste, nun kontrolliert von
blutelfischen Ingenieuren und ihren mechanischen Schöpfungen. Arkane Konstrukte,
Teufelswracker und Nethermanten-Aufseher bewachen Gänge aus glänzendem Kristall
und summender Maschinerie. Die Technologie ist elegant und fremdartig -
Draenei-Ingenieurskunst, umfunktioniert für finstere Zwecke. Alles summt vor kaum
gebändigter arkaner Energie.""",

    555: """Schattenlabyrinth: Der tiefste Flügel Auchindouns, wo der Schattenrat seine
dunkelsten Rituale vollführt. Leerwandler, Teufelsbeschwörer und Kultisten der
Kabale beten in Kammern, dick von Schattenmagie. Murmur, ein urzeitlicher
Klangelementar, ist in der tiefsten Kammer angekettet. Die Dunkelheit hier fühlt
sich lebendig und hungrig an - Schatten bewegen sich von selbst, und Flüstern
kommt von überall und nirgendwo.""",

    556: """Sethekk-Hallen: Arakkoa-Tempelhallen innerhalb Auchindouns, besetzt von
Fanatikern, die dem Rabengott Anzu ergeben sind. Wahnsinnige Arakkoa-Priester,
ihre beschworenen Geister und spektrale Wächter füllen die federbestreuten
Gänge. Die Architektur mischt Draenei- und Arakkoa-Stile auf beunruhigende
Weise. Die Bewohner sind völlig dem Wahnsinn verfallen, und die Hallen hallen
wider von irrem Kreischen und dunkler Prophezeiung.""",

    557: """Managräber: Der von Ätherwesen befallene Flügel Auchindouns, wo Nexus-Prinz
Shaffars Konsortium Draenei-Grabkammern plündert. Ätherische Banditen, arkane
Konstrukte und ruhelose Draenei-Geister prallen in kristallenen Grabkammern
aufeinander. Die Gräber leuchten von verbliebener heiliger Energie, während die
Ätherwesen sie abzapfen. Ein heiliger Ort, systematisch geplündert von
interdimensionalen Dieben.""",

    558: """Auchenai-Krypten: Die Grabstätten der Draenei unter Auchindoun, wo die
Auchenai-Priester im Umgang mit den Toten dem Wahnsinn verfallen sind.
Ruhelose Geister, besessene Kleriker und untote Draenei füllen die von Knochen
gesäumten Krypten. Was einst ein Ort respektvollen Gedenkens war, ist zu einem
Beinhaus geworden. Die Tragödie ist greifbar - dies waren Hüter, die sich in
ihrer Trauer verloren haben.""",

    560: """Altes Hügelland von Hillsbrad: Eine Instanz der Höhlen der Zeit, angesiedelt in
der Vergangenheit, als Thrall noch ein Sklave in der Festung Durnholde war. Das
Hügelland von damals ist grün, friedlich und voller ahnungsloser Menschen, die
ihrem Alltag nachgehen. Die Unendliche Drachenschwinge versucht, die Geschichte
zu verändern, indem sie Thralls Flucht verhindert. Es fühlt sich surreal an -
durch einen Ort zu wandern, den man kennt, bevor alles schiefging.""",

    568: """Zul'Aman: Ein Bollwerk der Waldtrolle in den Geisterlanden, wo Kriegsherr Zul'jin
seine Champions mit der Essenz der Tiergötter erstarkt hat. Luchs-, Bären-,
Adler- und Drachenfalkengeister durchdringen die Trolltempel-Wächter. Die
Amani-Waldtempel-Architektur ist lebhaft und urtümlich, geschmückt mit Masken,
Totems und Kriegsbemalung. Ein zeitgesteuerter Spießrutenlauf, bei dem
Geschwindigkeit zählt und die Trolltrommeln niemals aufhören zu schlagen.""",

    585: """Terrasse der Magister: Kael'thas Sonnenläufers letztes Bollwerk auf der Insel
von Quel'Danas, ein blutelfischer Palast von atemberaubender Eleganz, der
dämonische Verderbnis verbirgt. Teufelskristalle speisen arkane Konstrukte,
blutelfische Magister kanalisieren verbotene Magie, und ein gefangener Naaru wird
seines Lichts entleert. Die Schönheit der Silbermond-Architektur, verdreht von
Verzweiflung und Sucht - vergoldete Hallen, die einen monströsen Pakt
verbergen.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: Der von Geistern heimgesuchte Turm des letzten Wächters, Medivh, im
Gebirgspass der Totenwinde. Eine geisterhafte Dinnergesellschaft, eine
Opernbühne mit gespenstischen Darstellern, ein zum Leben erwachtes Schachspiel
und ein himmlisches Observatorium füllen den unmöglich hohen Turm. Der Turm
existiert teilweise außerhalb der normalen Realität - Räume verschieben sich,
Zeit verbiegt sich, und Echos von Medivhs Wahnsinn spielen sich ewig ab.
Eindringlich schön, zutiefst unheimlich und völlig einzigartig.""",

    534: """Gipfel des Hyjal: Ein Raid der Höhlen der Zeit, angesiedelt während der Schlacht
um den Berg Hyjal, dem entscheidenden Widerstand gegen Archimonde und die
Brennende Legion. Wellen von Untoten und Dämonen greifen nacheinander drei
Basen an - Menschen, Horde und Nachtelfen. Der Weltenbaum Nordrassil ragt
darüber empor, während der Wald brennt. Ein episches Verteidigungsszenario, in
dem das Schicksal Azeroths auf Messers Schneide steht und legendäre Helden an
eurer Seite kämpfen.""",

    544: """Magtheridons Hort: Eine einzelne brutale Kammer unter der Höllenfeuerzitadelle,
in der der Grubenlord Magtheridon angekettet ist. Kanalisierer halten sein
Gefängnis aufrecht, während Höllenfeuerenergie durch den Raum pulsiert. Der
Raum ist bedrückend heiß und stinkt nach Dämonenblut und Schwefel. Eine
geradlinige, doch bestrafende Begegnung - ein gewaltiger Dämon, ein tödlicher
Raum, kein Raum für Fehler.""",

    548: """Serpentschrein-Höhle: Lady Vashjs unterwasserisches Bollwerk im
Rollfangreservoir, ein geflutetes Schloss verdorbener Schönheit. Naga,
Flutwandler und kolossale Hydren bewachen Kammern, in denen Wasserfälle in
leuchtende Becken stürzen. Brücken überspannen unterirdische Seen, und die
tieferen Kammern pulsieren mit den verdorbenen Wassern der Zangarmarschen.
Elegante Naga-Architektur trifft auf die rohe Kraft eines unterirdischen
Ozeans.""",

    550: """Sturmfeste - Das Auge: Kael'thas Sonnenläufers gefangene Naaru-Festung, eine
kristalline Zitadelle, schwebend über dem Nethersturm. Blutelfische Berater,
arkane Konstrukte und Leerwesen bewachen Kammern aus schimmerndem
Draenei-Kristall. Die Technologie ist atemberaubend fremdartig und schön,
umfunktioniert von verzweifelten Elfen, die ihre Magiesucht stillen. Der
Ausblick auf den zerschmetterten Nethersturm von den Plattformen aus ist
gleichermaßen atemberaubend und beängstigend.""",

    564: """Der Schwarze Tempel: Illidan Sturmgrimms Festung im Schattenmondtal, ein
gewaltiger Draenei-Tempel, verdorben durch dämonische Besetzung. Teufelsorks,
Dämonen, Naga und Blutelfen dienen dem Verräter durch weitläufige Innenhöfe,
Abwassersysteme und große Hallen. Die ursprüngliche Schönheit des Tempels ist
von teuflischer Verderbnis vernarbt - zerbrochene heilige Symbole, geschändete
Altäre und grünes Feuer, wo einst Licht war. Der Höhepunkt der Geschichte
Outlands, endend an Illidans Thron.""",

    565: """Gruuls Hort: Ein rauer Höhlenkomplex im Schergrat, Heimat des Gronn-Vaters
Gruul des Drachentöters. Oger-Diener und Gruuls monströse Söhne bewachen den
Zugang zu seiner Kammer, übersät mit Drachenknochen und Trophäen. Die Höhlen
wirken urtümlich und brutal - keine Architektur, keine Verzierung, nur roher
Fels, geformt von den Fäusten von Riesen.""",

    580: """Sonnenbrunnenplateau: Der letzte Raid des Brennenden Kreuzzugs, angesiedelt im
Herzen des wiederhergestellten Sonnenbrunnens auf der Insel von Quel'Danas.
Die Brennende Legion versucht, Kil'jaeden durch den Sonnenbrunnen selbst zu
beschwören. Makellose Elfen-Architektur von atemberaubender Schönheit umrahmt
einen verzweifelten Kampf gegen die mächtigsten Dämonen in der Armee der
Legion. Das heilige Licht des Sonnenbrunnens prallt in jeder Kammer mit
dämonischer Dunkelheit zusammen.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Feste Utgarde: Eine Vrykul-Festung an den Küsten des Heulenden Fjords, der
erste Vorgeschmack auf die Gefahren Nordends. Von Wikingern inspirierte Hallen
aus dunklem Stein und Eisen, erleuchtet von lodernden Feuerstellen und
geschmückt mit Drachenschädeln. Vrykul-Krieger, Protodrachen-Betreuer und ihre
untoten Diener füllen die großen Hallen. Der Dungeon fühlt sich an wie das
Überfallen einer nordischen Langhalle - kalt, brutal und tief in
Kriegerkultur verwurzelt.""",

    575: """Utgarde-Gipfel: Die oberen Höhen der Feste Utgarde, wo der Vrykul-König
Ymiron von seinem vereisten Thron regiert. Trophäenhallen, Adlervolieren und
Ritualkammern ragen über den Fjord empor. Die Architektur wird grandioser und
bedrohlicher, je höher man aufsteigt, bis hin zu Ymirons frostbedecktem
Thronsaal. Wind heult durch offene Zinnen, und der Ausblick auf die vereiste
Landschaft darunter ist schwindelerregend.""",

    576: """Der Nexus: Die kristallinen Höhlen unter Kaltenau, Bollwerk des Krieges der
Blauen Drachenschwinge gegen sterbliche Magie. Vereiste Höhlen von
unmöglicher Schönheit enthalten arkane Anomalien, wahnsinnige Magierjäger und
Risse in der Realität. Kristallisierte Drachen hängen mitten im Flug erstarrt.
Der Dungeon schimmert von instabiler arkaner Energie - Blau, Violett und Weiß
brechen sich in jede Richtung durch Eis und Kristall.""",

    578: """Der Oculus: Die oberen Ringe des Nexus, eine Reihe schwebender Plattformen,
verbunden durch magische Brücken hoch über dem Ley-Linien-Nexus. Spieler
reiten Drachen, um zwischen den Ringsegmenten zu navigieren, während sie gegen
Malygos' Streitkräfte kämpfen. Die Leere erstreckt sich darunter, arkane
Energie knistert zwischen den Plattformen, und der Schwindel ist real. Ein
Dungeon, der sich anfühlt, als fliege man durch einen magischen Sturm am Rande
der Realität.""",

    595: """Die Läuterung Stratholmes: Eine Instanz der Höhlen der Zeit, angesiedelt
während Arthas' schicksalhafter Läuterung der verseuchten Stadt. Die Straßen
Stratholmes sind intakt, aber dem Untergang geweiht - Bürger verwandeln sich
vor euren Augen in Untote, und Arthas ordnet grimmig ihren Tod an, bevor die
Verwandlung geschieht. Der Dungeon ist einzigartig verstörend, weil ihr dabei
helft, die Gräueltat zu begehen, die Arthas' Fall einleitet. Die dunkelste
Stunde der Geschichte, wiedererlebt.""",

    599: """Hallen des Steins: Eine Titananlage in den Sturmgipfeln, Teil des gewaltigen
Ulduar-Komplexes. Steinerne Gänge von geometrischer Perfektion beherbergen
fehlfunktionierende Titankonstrukte, Eisenzwerge und uralte
Verteidigungssysteme. Das Tribunal der Zeitalter bewahrt Aufzeichnungen der
Schöpfung selbst. Der Dungeon wirkt gelehrt und uralt - ein Museum, dessen
Exponate sich wehren und dessen gespeicherte Geschichte Zivilisationen
zerschmettern könnte.""",

    600: """Festung Drak'Tharon: Eine von der Geißel befallene Trollfestung an der Grenze
zwischen den Grizzlyhügeln und Zul'Drak. Die Geißel hat die toten Trolle
erweckt und ihre Dinosaurierbestien verdorben, wodurch eine unheilige
Verschmelzung aus Trollkultur und nekromantischer Macht entstand. Skelett-
Echsen, Zombie-Trolle und der Lich Novos der Rufer füllen die verfallenden
Hallen. Trollarchitektur, zerbröckelnd unter dem Gewicht der Untotheit.""",

    601: """Azjol-Nerub: Das zerstörte Nerubianer-Königreich unter Nordend, ein von
Spinnweben verstopfter, vertikaler Abstieg durch das Spinnenimperium.
Nerubianer-Architektur aus Seide und Chitin erstreckt sich über gewaltige
unterirdische Schluchten. Untote Nerubianer dienen der Geißel, während die
Lebenden verzweifelt kämpfen. Der Dungeon lässt euch immer tiefer durch
einstürzende Böden fallen - klaustrophobisch, fremdartig und wimmelnd von
Dingen, die nicht existieren sollten.""",

    602: """Hallen des Blitzes: Ein Titanenschmiede-Komplex in Ulduar, knisternd vor
elektrischer Energie. Eisenzwerge, Sturmriesen und runische Konstrukte
bewachen Gänge aus glänzendem Metall und peitschenden Blitzen. Loken, der
verdorbene Titanenwächter, wartet in der tiefsten Kammer. Jede Oberfläche
summt vor Macht, Funken tanzen über die Wände, und der Donner der Schmiede
ist konstant und ohrenbetäubend.""",

    604: """Gundrak: Ein Drakkari-Trolltempel in Zul'Drak, wo die Trolle ihre eigenen
Tiergötter opfern, um ihren Krieg gegen die Geißel zu befeuern. Altäre rinnen
von göttlichem Blut, während Schlangen-, Mammut- und Nashorngeister
verzehrt werden. Der Tempel ist gewaltig und urtümlich - behauener Stein,
Ritualbecken und die verzweifelte Energie einer sterbenden Zivilisation, die
ihre eigenen Götter zum Überleben verbrennt.""",

    608: """Violette Feste: Ein magisches Gefängnis unter Dalaran, in dem der Kirin Tor
die gefährlichsten Kreaturen Nordends einsperrt. Agenten der Blauen
Drachenschwinge stürmen das Gefängnis durch Portale und befreien wellenweise
Insassen. Die Architektur ist elegantes Dalaran-Violett und -Silber, doch die
Insassen sind albtraumhaft. Ein Tower-Defense-Szenario in einem
Magierverlies - arkane Schutzzeichen kämpfen gegen das Chaos an.""",

    619: """Ahn'kahet: Das Alte Königreich: Die tiefsten Bereiche von Azjol-Nerub, wo
Gesichtslose dem alten Gott Yogg-Saron dienen. Die Architektur wandelt sich von
nerubianisch zu etwas weit Älterem und Fremdartigerem - organische Wände
pulsieren, die Realität verzerrt sich, und Wahnsinnseffekte greifen den
Verstand an. Vergessene, Zauberschleuderer und der Herold Volazj lauern in
Kammern, die jeder Geometrie trotzen. Der beunruhigendste Dungeon in
Nordend.""",

    632: """Schmiede der Seelen: Der erste von drei Dungeons der Eiskronenzitadelle, eine
gewaltige seelenmahlende Maschine, in der der Lichkönig die Toten verarbeitet.
Ströme gequälter Seelen fließen durch eiserne Maschinerie, spektrale Schmiede
hämmern auf Ambosse des Leidens, und der Verschlinger der Seelen bewacht die
Schmiede. Das Schreien hört niemals auf. Ein industrieller Albtraum, gespeist
von ewiger Qual.""",

    650: """Prüfung des Champions: Eine grandiose Turnierarena unter dem Argentumkoloss
in Eiskrone, wo Champions der Allianz und der Horde ihren Wert beweisen.
Berittenes Turnierstechen, Champion-Duelle und ein finaler Hinterhalt durch den
Schwarzen Ritter spielen sich auf dem Turniergelände ab. Die Atmosphäre ist
festlich und wettkämpferisch, bis die Untoten die Feier stören. Prunk und
Spektakel mit einer dunklen Wendung.""",

    658: """Die Grube von Saron: Eine brutale Sklavenmine in Eiskrone, in der Streitkräfte
der Geißel Gefangene zu Tode arbeiten lassen, um Saroniterz zu fördern. Die
Grube liegt offen unter dem gefrorenen Himmel, mit gewaltigen Ketten,
Abbauplattformen und Saronitvorkommen überall. Schmiedemeister Kaltfrost
schleudert Felsbrocken, während Tyrannus auf seinem Frostbrut-Drachen darüber
patrouilliert. Hoffnungslosigkeit und Grausamkeit, destilliert in gefrorenem
Stein und dunklem Metall.""",

    668: """Hallen der Reflexion: Die von Geistern heimgesuchten Gefrorenen Hallen der
Eiskronenzitadelle, wo Echos von Frostgrams Opfern um die Kammer der Klinge
verweilen. Der Lichkönig selbst verfolgt euch durch einstürzende Gänge,
während Wellen von Geistern angreifen. Die Hallen sind makelloses Eis und
dunkles Saronit, und der Schrecken ist real - ihr könnt nicht gegen ihn
kämpfen, nur fliehen. Der erzählerisch intensivste Dungeon des Spiels, eine
verzweifelte Flucht vor unausweichlichem Verderben.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: Die schwebende Nekropole des Erzlichs Kel'Thuzad, schwebend über
dem Drachenöde. Vier Flügel thematischer Schrecken - der Spinnentierflügel
riesiger Spinnen, der Seuchenflügel von Krankheit und Abscheulichkeiten, der
Militärflügel der Todesritter-Kommandanten und der Konstruktflügel der
Fleischgolems. Gotische Architektur aus dunklem Stein und grünem Schleim,
mit der kalten Präzision untoter militärischer Organisation. Das Meisterwerk
des Todes der Geißel.""",

    603: """Ulduar: Eine Titanen-Stadtfestung in den Sturmgipfeln, der grandioseste Raid
in Nordend. Gewaltige Hallen aus glänzendem Metall und Stein beherbergen die
verdorbenen Titanenwächter und ihre Diener, mit dem alten Gott Yogg-Saron
eingesperrt im tiefsten Gewölbe. Das Ausmaß ist überwältigend -
Fahrzeugschlachten an den Toren, ein Observatorium, offen zum Kosmos, Gärten
von unirdischer Schönheit und ein Abstieg in den Wahnsinn selbst. Uralt,
prächtig und schrecklich.""",

    615: """Obsidiansanktum: Eine vulkanische Kammer unter dem Drachenhorttempel, wo
Sartharion Zwielichtdracheneier bewacht. Lavaflüsse teilen die
Obsidianplattformen, und drei Zwielichtdrachen-Leutnants patrouillieren ihre
eigenen Inseln. Die Kammer glüht orange und rot, Hitzeflimmern verzerrt die
Luft, und der Verrat der schwarzen Drachenschwinge liegt offen zutage. Eine
geradlinige Arena aus Feuer und Schuppen.""",

    616: """Auge der Ewigkeit: Malygos' persönliches Heiligtum an der Spitze des Nexus
über Kaltenau, eine Plattform, schwebend in roher Ley-Energie. Es gibt keinen
Boden, keine Wände - nur eine Scheibe magischer Kraft über einer Leere
wirbelnder blauer und violetter Arkanmagie. Der Zauberweber greift mit der
vollen Macht der Blauen Drachenschwinge an. Der Raid fühlt sich
außerweltlich an - der Kampf gegen einen Drachenaspekt im Herzen von Azeroths
arkanem Sturm.""",

    624: """Gewölbe von Archavon: Ein Titanengewölbe unter der Festung Wintergrasp,
zugänglich nur für die Fraktion, die die Zone kontrolliert. Steinriesen und
elementare Konstrukte bewachen die Kammern in einer geradlinigen Abfolge von
Bosskämpfen. Die Architektur ist zweckmäßiges Titanendesign - funktional,
gewaltig und schmucklos. Eine Belohnung für den PvP-Sieg, schnell und brutal.""",

    631: """Eiskronenzitadelle: Der Thron des Lichkönigs, der Höhepunkt des Zorns des
Lichkönigs. Eine aufragende Festung aus Saronit und Eis, aufsteigend aus dem
Herzen von Eiskrone. Jeder Flügel steigert den Schrecken - von den untoten
Armeen der Unteren Spitze über die Seuchenwerke, die Purpurne Halle und die
Frostschwingenhallen bis hin zum Gefrorenen Thron selbst. Die Architektur ist
bedrückend, schön in ihrer Grausamkeit und darauf ausgelegt, Hoffnung zu
brechen. Dies ist das Ende.""",

    649: """Prüfung des Kreuzfahrers: Der Argentumkoloss in Eiskrone, eine Turnierarena,
die in die Erde hinabsinkt, wenn der Boden in eine unterirdische
Nerubianer-Höhle einbricht. Die obere Ebene besteht aus leuchtenden Bannern
und jubelnden Menschenmengen; die untere Ebene ist chitinöser Schrecken und
Anub'araks Reich. Der Kontrast zwischen festlichem Wettkampf oben und uraltem
Grauen unten prägt das gesamte Erlebnis.""",

    724: """Rubinsanktum: Eine Kammer unter dem Drachenhorttempel, in der die
Zwielichtdrachenschwinge das Heiligtum der roten Drachen überfallen hat.
Halion, der Zwielichtzerstörer, wechselt zwischen der physischen Ebene und der
Schattenebene. Die Kammer wechselt zwischen warmem Rubinlicht und kaltem
violettem Schatten. Der letzte Raid vor dem Kataklysmus - eine kurze,
unheilvolle Warnung vor der kommenden Zerstörung.""",
}

# Spanish (esES) dungeon/raid flavor text -- translated from the
# DUNGEON_FLAVOR entries above (same map-ID keys, same
# paragraph-length atmospheric lore), not injected verbatim since
# the English text was leaking untranslated into Spanish bot chat.
# Falls back to English DUNGEON_FLAVOR via get_dungeon_flavor() for
# any locale other than esES/deDE/frFR/ruRU, mirroring
# ZONE_FLAVOR_ES/get_zone_flavor()'s convention. Proper nouns reuse
# ZONE_NAMES_ES/ZONE_FLAVOR_ES's mixed-provenance terms where
# covered there; faction/place names outside those dicts use
# community-sourced Spanish WoW terminology, same confidence tier
# as ZONE_FLAVOR_ES's community-sourced portion, NOT independently
# verified against official client data.
DUNGEON_FLAVOR_ES = {
    # -------------------------------------------------------------------------
    # Classic Dungeons
    # -------------------------------------------------------------------------
    33: """Colmillo Sombrío: Una fortaleza encantada en el Bosque de Argénteos, invadida por worgen
y los sirvientes no-muertos del nigromante Arugal. Nobles fantasmales deambulan por los
pasillos oscuros, sabuesos espectrales aúllan en los patios, y experimentos arcanos
fallidos acechan en cada sombra. La fortaleza se siente como una historia de terror
gótico - piedra fría, luz de antorchas parpadeante, y la constante sensación de que algo
está observando.""",

    34: """El Calabozo: Una prisión bajo Ciudad de Ventormenta donde los presos se han rebelado y
tomado el control. Amotinados Defias, convictos enloquecidos y jefes de banda merodean
por las estrechas celdas de piedra. El calabozo es claustrofóbico y brutal - corredores
angostos, barrotes de hierro, y el eco de la violencia contra muros húmedos. Rápido,
sucio y peligroso.""",

    36: """Las Minas de la Muerte: Un extenso complejo minero bajo Páramos de Poniente, sede
secreta de la Hermandad Defias. El camino serpentea por túneles diseñados por goblins,
aserraderos y operaciones de fundición antes de emerger en una caverna subterránea
inmensa donde un barco pirata a tamaño real descansa en una cala oculta. Se siente como
descubrir un imperio criminal escondido justo bajo las narices de Ciudad de Ventormenta.""",

    43: """Las Cavernas del Lamento: Un laberinto de cavernas retorcidas en Los Baldíos, cubierto
de vegetación exuberante alimentada por magia druídica corrompida. Criaturas mutantes -
raptores, serpientes y limos mutados - se deslizan por túneles teñidos de esmeralda. Los
Druidas del Colmillo se han perdido en la Pesadilla Esmeralda. El aire es espeso, húmedo
y huele a podredumbre de jungla.""",

    47: """Cuchilla Espinosa: Un laberinto espinoso crecido a partir de zarzas colosales en Los
Baldíos, hogar de los quilboar y su matriarca Charlga Zarpa Cuchilla. Guerreros
quilboar, chamanes y sus jabalíes compañeros llenan los sinuosos corredores de espinas.
El calabozo se siente primitivo y feroz - naturaleza retorcida en una fortaleza de
hueso, espina y lodo.""",

    48: """Las Profundidades de Vientonegro: Un templo antiguo parcialmente sumergido en la costa
de Costa Oscura, sagrado para poderes oscuros. Naga, sátiros y cultistas del crepúsculo
adoran a viejos dioses en salones inundados adornados con arquitectura de elfos de la
noche en ruinas. El agua brilla de un azul-verde inquietante, y la atmósfera es opresiva
y ancestral - algo poderoso duerme en las pozas más profundas.""",

    70: """Uldaman: Un yacimiento de excavación titánico enterrado en Tierras Inhóspitas, mitad
excavación, mitad calabozo. Troggs de piedra, autómatas terrígenos y peligros
arqueológicos llenan cámaras de metal titánico pulido y roca en bruto. Cuanto más
profundo se va, más alienígena se vuelve la arquitectura - salones geométricos y lisos
que zumban con poder latente. Se siente como allanar una biblioteca construida por
dioses.""",

    90: """Gnomeregan: Las ruinas irradiadas de la capital gnoma, perdida ante una invasión trogg y
una fuga de radiación catastrófica. Gnomos leprosos enloquecidos, robots averiados y
limos tóxicos pueblan el complejo mecánico de múltiples niveles. Sirenas de alarma
resuenan, charcos de radiación verde brillan, y maquinaria rota chispea por doquier. Es
a partes iguales trágico y absurdo.""",

    109: """El Templo Sumergido: El Templo de Atal'Hakkar, un templo trol arrastrado bajo los
pantanos por la Bandada de Dragones Verdes. Los trols Atal'ai adoran al dios de sangre
Hakkar en salones inundados y cubiertos de enredaderas. Dragontes custodian los niveles
más profundos, y el diseño laberíntico es desorientador. La atmósfera está cargada de
humedad de jungla, magia trol ancestral, y una sensación de ritual prohibido.""",

    129: """Cuchilla Espinosa: Necrópolis: Un cementerio quilboar en Los Baldíos, infestado de
no-muertos. El agente del Flagelo Amnennar el Portador del Frío ha resucitado a los
quilboar muertos, convirtiendo sus criptas sagradas en una necrópolis de hueso y espina.
Quilboar esqueléticos y murciélagos de la peste llenan los corredores sombríos. Un lugar
donde chocan dos tipos de muerte - primitiva y nigromántica.""",

    189: """Monasterio Escarlata: Un monasterio fortificado en Claros de Trisfal, bastión de la
fanática Cruzada Escarlata. Cuatro alas albergan una biblioteca de textos prohibidos, un
arsenal repleto de fanáticos, una catedral de fe retorcida, y un cementerio encantado.
Los Cruzados están bien armados, disciplinados y completamente dementes - convencidos de
que todos son secretamente no-muertos. Arquitectura hermosa que oculta un fanatismo
asesino.""",

    209: """Zul'Farrak: Una ciudad trol medio enterrada en las arenas de Tanaris, hogar de los
hostiles trols Furia de Arena. Templos de piedra abrasados por el sol, altares
sacrificiales y patios arenosos componen este calabozo al aire libre. La famosa batalla
de la escalera te enfrenta a oleadas de guerreros trols. El calor del desierto es
implacable, los trols son salvajes, y la magia ancestral crepita entre las ruinas.""",

    229: """La Cima de Roca Negra: Una fortaleza orca colosal tallada en las alturas de la Montaña
Roca Negra. La cima inferior rebosa de orcos de Roca Negra, ogros y trols, mientras la
cima superior es el asiento del Señor de la Guerra Rend Manonegra y sus aliados
dragontes. La lava brilla abajo, los tambores de guerra resuenan constantemente, y el
aire apesta a humo y sangre. Un bastión militar extenso en el corazón de la Horda
Oscura.""",

    230: """Las Profundidades de Roca Negra: Una vasta ciudad de enanos Hierro Negro en las
profundidades de la Montaña Roca Negra, construida alrededor de un lago de lava fundida.
La taberna El Trago Amargo, la sala del trono del Emperador, y el umbral del Núcleo de
Magma están todos aquí. Elementales, gólems y fanáticos enanos Hierro Negro llenan una
metrópolis subterránea de tamaño imposible. Se siente como si toda una civilización
existiera bajo tierra, oscura, industriosa y hostil.""",

    269: """El Pantano Negro: Una instancia de las Cavernas del Tiempo ambientada en el pantano
primigenio que se convertiría en Las Tierras Devastadas. Agentes de la Bandada de
Dragones Infinitos intentan evitar que Medivh abra el Portal Oscuro, y oleadas de
dragontes atacan a través de grietas temporales. El pantano es oscuro, brumoso y
primigenio, con la energía del Portal crepitando a lo lejos. El tiempo mismo se siente
inestable aquí.""",

    289: """Escuela de la Muerte: Una academia nigromántica en las criptas bajo Caer Darrow,
dirigida por el Culto de los Condenados. Estudiantes y profesores de magia oscura
practican su oficio tanto en los muertos como en los vivos. Esqueletos, fantasmas y
gólems de carne llenan aulas y laboratorios. El calabozo tiene una atmósfera académica
perversa - salones de conferencia y bibliotecas dedicados enteramente a la magia de la
muerte.""",

    329: """Stratholme: Las ruinas ardientes de una ciudad antaño grandiosa, en llamas eternas desde
que Arthas la purgó. El Flagelo no-muerto controla la mitad oriental mientras la Cruzada
Escarlata sostiene fanáticamente las puertas occidentales. Los edificios se derrumban en
fuego perpetuo, abominaciones deambulan por las calles, y la ceniza nunca se asienta. Un
monumento a la tragedia y la locura - cada rincón guarda la memoria de la masacre.""",

    349: """Maraudon: Un sistema de cavernas sagradas en Desolace, deformado por la Princesa
Theradras y sus descendientes centauro tras la muerte del guardián Zaetar. Tres senderos
codificados por color serpentean por cuevas cristalinas, cascadas venenosas y jardines
subterráneos exuberantes antes de llegar al santuario interior. Las cámaras más
profundas son de una belleza inquietante - cristales brillantes, aguas cristalinas, y
magia terrestre ancestral luchando contra la corrupción. Naturaleza, duelo y furia
elemental entrelazados.""",

    389: """La Sima Fuego Rabioso: Un sistema de cavernas volcánicas bajo la propia Orgrimmar, donde
cultistas de la Hoja Ardiente y troggs se han asentado. La lava fluye por túneles
angostos, elementales de fuego patrullan, y el calor es sofocante. Corto y brutal - el
tipo de lugar que te recuerda que la Horda construyó su capital sobre un volcán.""",

    429: """Dire Maul: Una ciudad Altiborne en ruinas en Feralas, dividida en tres alas. Los ogros
han reclamado el norte, sátiros y ancestrales corrompidos infestan el este, y espíritus
fantasmales Altiborne rondan la biblioteca del ala oeste. Una arquitectura élfica en
ruinas de asombrosa belleza sucumbe lentamente al crecimiento de la jungla. El calabozo
se siente vasto, ancestral y melancólico - el cadáver de una gran civilización siendo
despojado por ocupantes.""",

    # -------------------------------------------------------------------------
    # Classic Raids
    # -------------------------------------------------------------------------
    249: """La Guarida de Onyxia: Una única caverna vasta en Marjal Revolcafango, hogar de la madre
de cría Onyxia. El acceso serpentea por un túnel angosto de roca calcinada antes de
abrirse a una cámara enorme sembrada de huesos y nidadas de huevos. Los crías pululan,
la lava burbujea en los bordes, y la propia Onyxia llena la caverna de fuego y sombra.
Un túnel claustrofóbico que da paso a una arena abrumadora de fuego de dragón.""",

    309: """Zul'Gurub: Un complejo de templo trol colosal en las junglas de Vega de Tuercespina,
donde la tribu Gurubashi ha liberado al dios de sangre Hakkar. Patios cubiertos de
vegetación, altares sacrificiales y plazas repletas de bestias rodean un templo central
que rezuma magia de sangre. Sacerdotes serpiente, jinetes de murciélagos y cultistas
tigre sirven a sus oscuros amos. La propia jungla parece palpitar con energía vudú
primitiva.""",

    409: """El Núcleo de Magma: El corazón ardiente de la Montaña Roca Negra, un reino de fuego puro
gobernado por Ragnaros el Señor del Fuego. Ríos de lava fluyen entre plataformas de
obsidiana, elementales de fuego y gigantes fundidos patrullan por doquier, y el calor es
apocalíptico. Sabuesos del núcleo de múltiples cabezas, torreones de lava imponentes, y
despertadores de llama ancestrales custodian a su amo. La prueba definitiva de fuego -
hermosa y aterradora a partes iguales.""",

    469: """La Guarida del Ala Negra: El bastión de Nefarian en la cima de la Cima de Roca Negra, un
laboratorio oscuro donde el dragón negro experimenta con otras bandadas de dragones.
Soldados dracónidos, dragontes cromáticos y experimentos fallidos llenan salones de
hierro oscuro y hueso de dragón. Cada cámara presenta un desafío táctico único. La
incursión se siente clínica y siniestra - la guarida de un científico loco a escala de
dragón.""",

    509: """Ruinas de Ahn'Qiraj: Un campo de batalla al aire libre en Silithus donde las fuerzas
qiraji se congregan para la guerra. Guerreros insectoides, destructores de obsidiana y
colosales criaturas parecidas a escarabajos pululan por patios barridos por la arena y
ruinas de templos derrumbados. La arquitectura es alienígena y quitinosa, mitad tumba
egipcia, mitad colmena de insectos. El viento del desierto lleva el chasquido de un
millón de patas.""",

    531: """Templo de Ahn'Qiraj: El santuario interior sellado del imperio qiraji, una pesadilla de
arquitectura alienígena y corrupción de dios antiguo. Los emperadores gemelos, la
realeza silítida colosal, y el propio dios antiguo C'Thun acechan en su interior. Las
paredes palpitan con crecimiento orgánico, ojos observan desde cada superficie, y la
realidad se dobla cerca de la prisión del dios antiguo. El lugar más alienígena y
perturbador del Azeroth clásico.""",

    # -------------------------------------------------------------------------
    # TBC Dungeons
    # -------------------------------------------------------------------------
    540: """Salas Destrozadas: El bastión de los orcos del vil dentro de la Ciudadela del Fuego
Infernal, un pasillo empapado de sangre de los sirvientes más fanáticos de la Legión
Ardiente. Gladiadores, legionarios y berserkers orcos del vil abarrotan cada corredor,
con prisioneros encadenados a los muros. La arquitectura es de hierro brutal y piedra
roja, manchada por evidencia de violencia constante. Un asalto implacable contra una
fortaleza que contraataca en cada paso.""",

    542: """El Alto Horno de Sangre: Una fábrica demoníaca dentro de la Ciudadela del Fuego Infernal
donde se fabrican orcos del vil mediante rituales oscuros. Cubas de sangre hirviendo,
prisioneros enjaulados a la espera de la transformación, y maquinaria vil llenan las
cámaras humeantes. Orcos del vil nacientes y sus supervisores custodian las líneas de
producción. El calabozo apesta a sangre y azufre - un espectáculo de horror industrial.""",

    543: """Las Murallas del Fuego Infernal: Las fortificaciones exteriores de la Ciudadela del
Fuego Infernal, primera línea de defensa del ejército orco del vil. Torres de
vigilancia, almenas y pasarelas angostas ofrecen vistas panorámicas de la destrozada
Península del Fuego Infernal abajo. Soldados orcos del vil, jinetes de worgs, y un
dragón cautivo custodian los muros. El viento aúlla entre las murallas destrozadas, y el
cielo rojo de Outland se extiende sin fin en lo alto.""",

    545: """La Cámara de Vapor: Una estación naga de bombeo de agua en el Embalse Colmillo
Serpiente, donde las fuerzas de Lady Vashj drenan la Marisma de Zangar. Tuberías,
válvulas y canales de agua colosales dominan el diseño industrial. Naga, señores del
pantano y elementales de agua custodian la maquinaria. El vapor silba de cada junta y el
rugido del agua torrencial es ensordecedor. Un calabozo que se siente como sabotear una
fábrica hostil.""",

    546: """El Bajo Pantano: Un pantano en descomposición bajo el Embalse Colmillo Serpiente,
plagado de criaturas fúngicas mutadas y espíritus de la naturaleza hostiles. Gigantes de
esporas, señores del pantano y fauna venenosa llenan las cavernas cubiertas de
vegetación. Hongos bioluminiscentes proyectan un brillo inquietante sobre pozas
estancadas. El aire está cargado de esporas y del olor a descomposición - naturaleza
desbocada vuelta hostil.""",

    547: """Los Corrales de Esclavos: Los campos de trabajo del Embalse Colmillo Serpiente donde los
draenei Rotos son mantenidos cautivos por capataces naga. Túneles anegados, corrales
toscos y supervisores naga con sus látigos definen la atmósfera. Crecimientos fúngicos y
criaturas del pantano han infiltrado el complejo. Un calabozo impregnado de miseria y
opresión, medio inundado y en descomposición.""",

    552: """El Arcatraz: Un satélite carcelario dimensional de la Fortaleza de la Tempestad, que
retiene a las entidades más peligrosas del cosmos. Brujos eredar, criaturas del vacío y
saboteadores elfos de sangre deambulan por celdas diseñadas para contener horrores más
allá de la imaginación. La arquitectura es tecnología cristalina draenei deformada por
sus internos. Cada puerta de celda que pasas te hace preguntarte qué escapó - y qué
sigue encerrado dentro.""",

    553: """La Botánica: Una biocúpula colosal satélite de la Fortaleza de la Tempestad, donde
antaño se cultivaba flora exótica de todo el cosmos. Los elfos de sangre se han
apoderado de la instalación, y las plantas han crecido salvajes y hostiles. Azotadores,
treants y especímenes botánicos alienígenas llenan invernaderos de cristal
resplandeciente. Hermosa pero mortal - cada flor podría matarte, y los elfos de sangre
son peores.""",

    554: """El Mecanar: Un ala de fabricación de la Fortaleza de la Tempestad, ahora controlada por
ingenieros elfos de sangre y sus creaciones mecánicas. Autómatas arcanos, devastadores
del vil y supervisores nigromantes custodian corredores de cristal reluciente y
maquinaria zumbante. La tecnología es elegante y alienígena - ingeniería draenei
reutilizada para fines siniestros. Todo zumba con energía arcana apenas contenida.""",

    555: """El Laberinto de las Sombras: El ala más profunda de Auchindoun, donde el Consejo de las
Sombras conduce sus rituales más oscuros. Caminantes del vacío, invocadores del vil y
cultistas de la Cábala adoran en cámaras cargadas de magia sombría. Murmullo, un
elemental de sonido primordial, está encadenado en la cámara más profunda. La oscuridad
aquí se siente viva y hambrienta - las sombras se mueven por sí solas, y los susurros
vienen de todas partes y de ninguna.""",

    556: """Salas de Sethekk: Salas de templo arakkoa dentro de Auchindoun, ocupadas por fanáticos
devotos del Dios Cuervo Anzu. Sacerdotes arakkoa enloquecidos, sus espíritus invocados y
guardianes espectrales llenan corredores cubiertos de plumas. La arquitectura mezcla
estilos draenei y arakkoa de formas inquietantes. Los habitantes se han vuelto
completamente dementes, y las salas resuenan con chillidos desquiciados y profecías
oscuras.""",

    557: """Tumbas de Maná: El ala infestada de etéreos de Auchindoun, donde el consorcio del
Príncipe-Nexo Shaffar saquea las bóvedas funerarias draenei. Bandidos etéreos, autómatas
arcanos y espíritus draenei inquietos chocan en cámaras funerarias cristalinas. Las
tumbas brillan con energía sagrada residual mientras los etéreos la drenan
sistemáticamente. Un lugar sagrado siendo saqueado sistemáticamente por ladrones
interdimensionales.""",

    558: """Criptas Auchenai: El cementerio draenei bajo Auchindoun, donde los sacerdotes auchenai
han enloquecido comunicándose con los muertos. Espíritus inquietos, clérigos poseídos y
draenei no-muertos llenan las criptas revestidas de huesos. Lo que antes fue un lugar de
recuerdo respetuoso se ha convertido en una casa de osarios. La tragedia es palpable -
eran cuidadores que se perdieron a sí mismos en el duelo.""",

    560: """Antiguas Laderas de Trabalomas: Una instancia de las Cavernas del Tiempo ambientada en
el pasado, cuando Thrall aún era esclavo en la Fortaleza Durnholde. El Trabalomas de
años atrás es verde, pacífico y lleno de humanos ajenos que siguen con sus vidas. La
Bandada de Dragones Infinitos intenta alterar la historia impidiendo la fuga de Thrall.
Se siente surrealista - caminar por un lugar que conoces antes de que todo saliera mal.""",

    568: """Zul'Aman: Un bastión de trols del bosque en las Tierras Fantasma, donde el Señor de la
Guerra Zul'jin ha imbuido a sus campeones con la esencia de dioses animales. Espíritus
de lince, oso, águila y halcón dragón infunden a los guardianes del templo trol. La
arquitectura selva-templo Amani es vívida y primitiva, decorada con máscaras, tótems y
pintura de guerra. Un desafío contrarreloj donde la velocidad importa y los tambores
trols nunca dejan de sonar.""",

    585: """Terraza de los Magísteres: El último bastión de Kael'thas Solestridente en la Isla de
Quel'Danas, un palacio de elfos de sangre de asombrosa elegancia que oculta corrupción
demoníaca. Cristales del vil alimentan autómatas arcanos, magísteres elfos de sangre
canalizan magia prohibida, y un naaru capturado está siendo drenado de su Luz. La
belleza de la arquitectura de Ciudad de Lunargenta retorcida por la desesperación y la
adicción - salones dorados que ocultan un pacto monstruoso.""",

    # -------------------------------------------------------------------------
    # TBC Raids
    # -------------------------------------------------------------------------
    532: """Karazhan: La torre encantada del último Guardián, Medivh, en Paso de la Muerte. Una cena
espectral, un escenario de ópera con intérpretes fantasmales, una partida de ajedrez
cobrando vida, y un observatorio celestial llenan la torre imposiblemente alta. La torre
existe parcialmente fuera de la realidad normal - las habitaciones cambian, el tiempo se
dobla, y ecos de la locura de Medivh se repiten eternamente. Inquietantemente hermosa,
profundamente espeluznante, y absolutamente única.""",

    534: """Cumbre del Hyjal: Una incursión de las Cavernas del Tiempo ambientada durante la Batalla
del Monte Hyjal, la resistencia culminante contra Archimonde y la Legión Ardiente.
Oleadas de no-muertos y demonios asaltan tres bases sucesivamente - humana, de la Horda
y de elfos de la noche. El árbol del mundo Nordrassil se alza en lo alto mientras el
bosque arde. Un escenario de defensa épico donde el destino de Azeroth pende de un hilo
y héroes legendarios luchan a tu lado.""",

    544: """La Guarida de Magtheridon: Una única cámara brutal bajo la Ciudadela del Fuego Infernal
donde el señor del abismo Magtheridon está encadenado. Canalizadores mantienen su
prisión mientras la energía del fuego infernal palpita por la sala. El espacio es
opresivamente caluroso, apesta a sangre demoníaca y azufre. Un encuentro directo pero
castigador - un demonio colosal, una sala mortal, sin margen de error.""",

    548: """La Caverna del Santuario de la Serpiente: El bastión submarino de Lady Vashj en el
Embalse Colmillo Serpiente, un palacio inundado de belleza corrompida. Naga, caminantes
de marea y hidras colosales custodian cámaras donde cascadas caen en pozas luminosas.
Puentes cruzan lagos subterráneos, y las cámaras más profundas palpitan con las aguas
corrompidas de la Marisma de Zangar. Elegante arquitectura naga se encuentra con el
poder crudo de un océano subterráneo.""",

    550: """Fortaleza de la Tempestad - El Ojo: La fortaleza naaru capturada de Kael'thas
Solestridente, una ciudadela cristalina flotando sobre Tormenta Abisal. Consejeros elfos
de sangre, autómatas arcanos y criaturas del vacío custodian cámaras de cristal draenei
resplandeciente. La tecnología es asombrosamente alienígena y hermosa, reutilizada por
elfos desesperados que alimentan su adicción a la magia. La vista de Tormenta Abisal
destrozada desde las plataformas es tan impresionante como aterradora.""",

    564: """El Templo Negro: La fortaleza de Illidan Tempestira en Valle Sombraluna, un templo
draenei colosal corrompido por la ocupación demoníaca. Orcos del vil, demonios, naga y
elfos de sangre sirven al Traidor a través de patios extensos, sistemas de
alcantarillado y grandes salones. La belleza original del templo está marcada por la
corrupción del vil - símbolos sagrados agrietados, altares profanados, y fuego verde
donde antes hubo Luz. La culminación de la historia de Outland, terminando en el trono
de Illidan.""",

    565: """La Guarida de Gruul: Un tosco complejo de cavernas en las Montañas Filoespada, hogar del
padre gronn Gruul el Matadragones. Sirvientes ogros y los hijos monstruosos de Gruul
custodian el acceso a su cámara, sembrada de huesos de dragón y trofeos. Las cuevas se
sienten primitivas y brutales - sin arquitectura, sin decoración, solo roca cruda
moldeada por los puños de gigantes.""",

    580: """Meseta del Pozo de Sol: La incursión final de la Cruzada Ardiente, ambientada en el
corazón del Pozo de Sol restaurado en la Isla de Quel'Danas. La Legión Ardiente intenta
invocar a Kil'jaeden a través del propio Pozo de Sol. Una arquitectura élfica impecable
de belleza sobrecogedora enmarca una batalla desesperada contra los demonios más
poderosos del ejército de la Legión. La luz sagrada del Pozo de Sol choca con la
oscuridad demoníaca en cada cámara.""",

    # -------------------------------------------------------------------------
    # WotLK Dungeons
    # -------------------------------------------------------------------------
    574: """Fuerte Utgarde: Una fortaleza vrykul en las costas del Fiordo Aquilonal, la primera
muestra de los peligros de Rasganorte. Salones de inspiración vikinga de piedra oscura y
hierro, iluminados por hogares rugientes y decorados con cráneos de dragón. Guerreros
vrykul, cuidadores de proto-dracos y sus sirvientes no-muertos llenan los grandes
salones. El calabozo se siente como asaltar un salón nórdico - frío, brutal, e
impregnado de cultura guerrera.""",

    575: """Pináculo de Utgarde: Las alturas superiores del Fuerte Utgarde, donde el rey vrykul
Ymiron gobierna desde su trono helado. Salones de trofeos, pajareras de águilas, y
cámaras rituales se alzan sobre el fiordo. La arquitectura se vuelve más grandiosa y
amenazante a medida que se asciende, culminando en la sala del trono escarchada de
Ymiron. El viento aúlla entre las almenas abiertas, y la vista del paisaje helado abajo
produce vértigo.""",

    576: """El Nexo: Las cuevas cristalinas bajo Fríallende, bastión de la guerra de la Bandada de
Dragones Azules contra la magia mortal. Cavernas heladas de belleza imposible contienen
anomalías arcanas, cazadores de magos enloquecidos, y grietas en la realidad. Dragones
cristalizados cuelgan congelados en pleno vuelo. El calabozo resplandece con energía
arcana inestable - azules, púrpuras y blancos que se refractan a través del hielo y el
cristal en todas direcciones.""",

    578: """El Oculus: Los anillos superiores del Nexo, una serie de plataformas flotantes
conectadas por puentes mágicos muy por encima del nexo de líneas ley. Los jugadores
montan dracos para navegar entre segmentos de anillo mientras luchan contra las fuerzas
de Malygos. El vacío se extiende abajo, la energía arcana crepita entre plataformas, y
el vértigo es real. Un calabozo que se siente como volar a través de una tormenta mágica
al borde de la realidad.""",

    595: """La Masacre de Stratholme: Una instancia de las Cavernas del Tiempo ambientada durante la
fatídica purga de Arthas en la ciudad infectada por la plaga. Las calles de Stratholme
están intactas pero condenadas - los ciudadanos se transforman en no-muertos ante tus
ojos, y Arthas ordena sombríamente su muerte antes de la transformación. El calabozo es
únicamente perturbador porque estás ayudando a cometer la atrocidad que inicia la caída
de Arthas. El momento más oscuro de la historia, revivido.""",

    599: """Salas de Piedra: Una instalación titánica en las Cumbres Tormentosas, parte del vasto
complejo de Ulduar. Corredores de piedra de perfección geométrica albergan autómatas
titánicos averiados, enanos de hierro, y antiguos sistemas de defensa. El Tribunal de
las Eras guarda registros de la propia creación. El calabozo se siente académico y
ancestral - un museo donde las exhibiciones contraatacan y la historia guardada aquí
podría destrozar civilizaciones.""",

    600: """Fuerte Drak'Tharon: Una fortaleza trol infestada por el Flagelo en la frontera entre
Colinas Pardas y Zul'Drak. El Flagelo ha resucitado a los trols muertos y corrompido a
sus bestias dinosaurio, creando una fusión antinatural de cultura trol y poder
nigromántico. Raptores esqueléticos, trols zombis, y el liche Novos el Convocador llenan
los salones en decadencia. Arquitectura trol desmoronándose bajo el peso de la
no-muerte.""",

    601: """Azjol-Nerub: El reino nerubiano en ruinas bajo Rasganorte, un descenso vertical
asfixiado de telarañas a través del imperio arácnido. La arquitectura nerubiana de seda
y quitina se extiende por vastos abismos subterráneos. Nerubianos no-muertos sirven al
Flagelo mientras los vivos luchan desesperadamente. El calabozo te hace caer cada vez
más profundo a través de suelos que se derrumban - claustrofóbico, alienígena, y plagado
de cosas que no deberían existir.""",

    602: """Salas del Relámpago: Un complejo de forja titánico en Ulduar, crepitando con energía
eléctrica. Enanos de hierro, gigantes de tormenta y autómatas rúnicos custodian
corredores de metal reluciente y relámpagos en arco. Loken, el guardián titán
corrompido, espera en la cámara más profunda. Cada superficie zumba con poder, chispas
bailan por los muros, y el trueno de la forja es constante y ensordecedor.""",

    604: """Gundrak: Un templo trol Drakkari en Zul'Drak, donde los trols sacrifican a sus propios
dioses animales para alimentar su guerra contra el Flagelo. Los altares rebosan de
sangre divina mientras espíritus de serpiente, mamut y rinoceronte son consumidos. El
templo es masivo y primitivo - piedra tallada, pozas rituales, y la energía desesperada
de una civilización agonizante quemando a sus propios dioses por sobrevivir.""",

    608: """Fortaleza Violeta: Una prisión mágica bajo Dalaran, donde el Kirin Tor contiene a las
criaturas más peligrosas de Rasganorte. Agentes de la Bandada de Dragones Azur asaltan
la prisión desde portales, liberando internos en oleadas. La arquitectura es un elegante
púrpura y plata de Dalaran, pero los internos son de pesadilla. Un escenario de defensa
de torre en un calabozo de magos - las salvaguardas arcanas se tensan contra el caos.""",

    619: """Ahn'kahet: El Antiguo Reino: Las profundidades más recónditas de Azjol-Nerub, donde los
Sinrostro sirven al dios antiguo Yogg-Saron. La arquitectura cambia de nerubiana a algo
mucho más antiguo y alienígena - las paredes orgánicas palpitan, la realidad se deforma,
y efectos de locura asaltan la mente. Olvidados, lanzadores de hechizos, y el heraldo
Volazj acechan en cámaras que desafían la geometría. El calabozo más perturbador de
Rasganorte.""",

    632: """Forja de Almas: El primero de tres calabozos de la Ciudadela de Corona de Hielo, un
motor colosal que muele almas donde el Rey Exánime procesa a los muertos. Ríos de almas
torturadas fluyen por maquinaria de hierro, herreros espectrales martillean yunques de
sufrimiento, y el Devorador de Almas custodia la forja. Los gritos nunca cesan. Una
pesadilla industrial alimentada por tormento eterno.""",

    650: """Prueba del Campeón: Una gran arena de torneo bajo el Coliseo Argenta en Corona de Hielo,
donde campeones de la Alianza y la Horda demuestran su valía. Justas montadas, duelos de
campeones, y una emboscada final del Caballero Negro se desarrollan en el terreno del
torneo. La atmósfera es festiva y competitiva hasta que los no-muertos irrumpen en la
fiesta. Pompa y espectáculo con un giro oscuro.""",

    658: """Fosa de Saron: Una brutal mina de esclavos en Corona de Hielo donde las fuerzas del
Flagelo trabajan a los prisioneros hasta la muerte extrayendo mena de saronita. La fosa
está abierta al cielo helado, con cadenas colosales, plataformas mineras, y depósitos de
saronita por doquier. El Maestro de Forja Garfrost lanza rocas mientras Tyrannus
patrulla en su draco de cría escarchada en lo alto. Desesperanza y crueldad destiladas
en piedra helada y metal oscuro.""",

    668: """Salas del Reflejo: Los Pasillos Helados encantados de la Ciudadela de Corona de Hielo,
donde los ecos de las víctimas de Añoranza persisten alrededor de la cámara de la hoja.
El propio Rey Exánime te persigue a través de corredores que se derrumban mientras
oleadas de fantasmas atacan. Los pasillos son de hielo prístino y saronita oscura, y el
terror es real - no puedes luchar contra él, solo huir. El calabozo más intenso
narrativamente del juego, una huida desesperada de una perdición inevitable.""",

    # -------------------------------------------------------------------------
    # WotLK Raids
    # -------------------------------------------------------------------------
    533: """Naxxramas: La necrópolis flotante del archiliche Kel'Thuzad, cerniéndose sobre
Cementerio de Dragones. Cuatro alas de horrores temáticos - el Cuartel Arácnido de
arañas gigantes, el Cuartel de la Plaga de enfermedad y abominaciones, el Cuartel
Militar de comandantes caballeros de la muerte, y el Cuartel de Autómatas de gólems de
carne. Arquitectura gótica de piedra oscura y limo verde, con la fría precisión de la
organización militar no-muerta. La obra maestra de muerte del Flagelo.""",

    603: """Ulduar: Una ciudad-prisión titánica en las Cumbres Tormentosas, la incursión más
grandiosa de Rasganorte. Salones colosales de metal reluciente y piedra albergan a los
guardianes titánicos corrompidos y sus sirvientes, con el dios antiguo Yogg-Saron
aprisionado en la bóveda más profunda. La escala es asombrosa - batallas de vehículos en
las puertas, un observatorio abierto al cosmos, jardines de belleza sobrenatural, y un
descenso a la propia locura. Ancestral, magnífica y aterradora.""",

    615: """Santuario de Obsidiana: Una cámara volcánica bajo el Templo del Reposo del Wyrm donde
Sartharion custodia huevos de dragón del crepúsculo. Ríos de lava dividen las
plataformas de obsidiana, y tres lugartenientes dracos del crepúsculo patrullan sus
propias islas. La cámara brilla en naranja y rojo, el calor distorsiona el aire, y la
traición de la bandada de dragones negros queda al descubierto. Una arena directa de
fuego y escamas.""",

    616: """El Ojo de la Eternidad: El santuario personal de Malygos en la cúspide del Nexo sobre
Fríallende, una plataforma suspendida en energía ley cruda. No hay suelo, no hay muros -
solo un disco de fuerza mágica sobre un vacío de arcano azul y violeta arremolinado. El
Tejedor de Hechizos ataca con todo el poder de la Bandada de Dragones Azules. La
incursión se siente de otro mundo - luchar contra un aspecto de dragón en el corazón de
la tormenta arcana de Azeroth.""",

    624: """Bóveda de Archavon: Una bóveda titánica bajo la Fortaleza de Fríallende, accesible solo
para la facción que controla la zona. Gigantes de piedra y autómatas elementales
custodian las cámaras en una serie directa de encuentros con jefes. La arquitectura es
diseño titánico utilitario - funcional, colosal y sin adornos. Una recompensa por la
victoria en JcJ, rápida y brutal.""",

    631: """Ciudadela de Corona de Hielo: El trono del Rey Exánime, la culminación de la Ira del Rey
Exánime. Una fortaleza imponente de saronita y hielo que se alza desde el corazón de
Corona de Hielo. Cada ala intensifica el horror - desde los ejércitos no-muertos de la
Cima Inferior, pasando por las Obras de la Plaga, el Salón Carmesí y las Salas del Ala
Escarchada, hasta el propio Trono Helado. La arquitectura es opresiva, hermosa en su
crueldad, y diseñada para quebrar la esperanza. Este es el final.""",

    649: """Prueba del Cruzado: El Coliseo Argenta en Corona de Hielo, una arena de torneo que
desciende a la tierra cuando el suelo se derrumba en una caverna nerubiana subterránea.
El nivel superior es estandartes brillantes y multitudes vitoreando; el nivel inferior
es horror quitinoso y el dominio de Anub'arak. El contraste entre la competición festiva
arriba y el terror ancestral abajo define toda la experiencia.""",

    724: """Santuario Rubí: Una cámara bajo el Templo del Reposo del Wyrm donde la bandada de
dragones del crepúsculo ha invadido el santuario de los dragones rojos. Halion, el
destructor del crepúsculo, se desplaza entre el reino físico y el reino de las sombras.
La cámara alterna entre cálida luz rubí y fría sombra púrpura. La última incursión antes
del Cataclismo - una breve y ominosa advertencia de la destrucción por venir.""",
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
    12: "Quest Item", 15: "Miscellaneous",
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
# PROXIMITY CHAT TOPICS
# =============================================================================
# Topics for proximity /say chatter between bots, NPCs, and the player.
# These are casual, lightweight, daily-life snippets — overheard
# fragments as the player walks through the world.  Distinct from
# AMBIENT_CHAT_TOPICS which are party/group-focused.
# Keep entries short and concrete so the LLM produces brief replies.
PROXIMITY_CHAT_TOPICS = [
    # ── Weather & Nature ────────────────────────────────────────────
    'complaining about the rain',
    'enjoying the sunshine',
    'wondering if a storm is coming',
    'commenting on the fog rolling in',
    'remarking on the cold wind',
    'noting the first snow of the season',
    'wishing for warmer weather',
    'complaining about the heat',
    'admiring the sunset',
    'commenting on the moonlight',
    'noticing the stars are unusually bright tonight',
    'remarking on the autumn leaves',
    'talking about the river rising after rain',
    'mentioning the harvest moon',

    # ── Local News & Rumors ─────────────────────────────────────────
    'sharing a rumor about trouble on the roads',
    'mentioning travelers arriving from far away',
    'gossiping about a local official',
    'discussing news from the front lines',
    'wondering about strange lights seen in the hills',
    'talking about a merchant caravan that went missing',
    'speculating about troop movements nearby',
    'repeating a rumor heard at the tavern last night',
    'mentioning a wanted poster they just saw',
    'discussing a bounty on a local bandit',
    'wondering about a mysterious stranger in town',
    'talking about a ship that arrived in port',
    'mentioning a fire that broke out near the market',
    'sharing news of a wedding or birth in the village',
    'gossiping about a noble who fell from favor',

    # ── Commerce & Trade ────────────────────────────────────────────
    'complaining about rising prices',
    'mentioning a new shop opening nearby',
    'talking about a sale at the general goods store',
    'grumbling about the cost of repairs',
    'discussing the quality of local goods',
    'asking if anyone knows a good blacksmith',
    'mentioning a shipment of rare fabrics',
    'complaining about the auction house prices',
    'talking about a merchant who cheated them',
    'wondering if the fishing has been good lately',
    'discussing the price of ore or leather',
    'mentioning a bargain they found at the market',
    'talking about trade routes being disrupted',
    'complaining about taxes or tolls',

    # ── Fashion & Appearance ────────────────────────────────────────
    'admiring someone passing by and their armor',
    'commenting on a new cloak style from Dalaran',
    'mentioning that gnomish goggles are in fashion',
    'discussing the look of a new weapon design',
    'talking about elven tailoring being the finest',
    'wondering where to get boots like those',
    'remarking on the colors of a tabard',
    'complaining that their armor is out of style',
    'admiring dwarven craftsmanship on a shield',
    'commenting on jewelry trends',

    # ── Home & Daily Life ───────────────────────────────────────────
    'talking about their garden not growing well',
    'mentioning home repairs they need to do',
    'complaining about a leaky roof',
    'talking about redecorating their house',
    'mentioning their neighbor is too loud',
    'discussing the best wood for furniture',
    'talking about getting new curtains',
    'complaining about pests in the pantry',
    'mentioning they need to fix the fence',
    'talking about a recipe they want to try',
    'discussing the best place to buy candles',
    'mentioning they just cleaned the chimney',

    # ── Food & Drink ────────────────────────────────────────────────
    'recommending a tavern or inn nearby',
    'complaining about watered-down ale',
    'praising a local baker or cook',
    'discussing a new recipe they tried',
    'arguing about the best pie in town',
    'mentioning a cheese that pairs well with bread',
    'talking about a terrible meal they had',
    'praising the stew at a particular inn',
    'discussing the merits of dwarven ale vs elven wine',
    'asking if anyone wants to grab a drink later',
    'complaining about bland rations',
    'mentioning a secret ingredient in their cooking',
    'talking about seasonal fruit at the market',
    'praising fresh bread from the bakery this morning',

    # ── Petty Crime & Mischief ──────────────────────────────────────
    'mentioning a pickpocket working the market',
    'talking about a burglary on their street',
    'complaining about vandals defacing a sign',
    'discussing a drunk who caused a scene last night',
    'mentioning someone was caught cheating at cards',
    'talking about a stolen pie from a window ledge',
    'gossiping about who broke the tavern window',
    'mentioning a fight that broke out at the inn',
    'complaining about rowdy sailors in port',
    'discussing a con artist selling fake potions',
    'mentioning graffiti found on the town hall',
    'talking about a chicken thief in the neighborhood',
    'wondering who keeps stealing apples from the cart',
    'discussing a gambling ring behind the warehouse',

    # ── Travel & Roads ──────────────────────────────────────────────
    'warning about bandits on the south road',
    'recommending a shortcut through the hills',
    'complaining about the road conditions',
    'mentioning a bridge that was washed out',
    'talking about a scenic route they discovered',
    'discussing the best path to the next town',
    'warning about wolves near the forest road',
    'mentioning the flight master raised prices',
    'talking about a long journey they just returned from',
    'recommending an inn along the trade road',
    'complaining about how dusty the roads are',
    'talking about a cart that broke an axle yesterday',
    'mentioning a new road being built',
    'discussing whether it is safe to travel at night',

    # ── People & Gossip ─────────────────────────────────────────────
    'gossiping about a neighbor',
    'talking about someone who left town suddenly',
    'mentioning a couple that just got engaged',
    'discussing a local hero or adventurer',
    'speculating about why the mayor looks worried',
    'talking about an old friend they lost touch with',
    'mentioning a family feud between two households',
    'gossiping about the innkeeper and the baker',
    'wondering what happened to the old hermit',
    'discussing a healer who just arrived in town',
    'talking about a soldier who came home wounded',
    'mentioning a child who ran away from home',
    'gossiping about a secret romance',

    # ── Professions & Craft ─────────────────────────────────────────
    'complaining about finding good ore',
    'talking about a difficult smithing project',
    'mentioning a new alchemy recipe they learned',
    'discussing the best leather for armor',
    'talking about enchanting costs being too high',
    'mentioning a rare herb they found',
    'discussing tailoring patterns from the east',
    'complaining about failed crafting attempts',
    'talking about engineering gone wrong',
    'mentioning a jewel they are trying to cut',
    'discussing the apprentice system',
    'talking about training under a new master',

    # ── Lore & History ──────────────────────────────────────────────
    'wondering about the ruins outside town',
    'mentioning a legend about this place',
    'talking about the war and how things have changed',
    'recalling a historical battle that happened nearby',
    'mentioning an old king or queen from stories',
    'wondering about the origins of a local monument',
    'talking about ancient magic felt in the area',
    'mentioning a ghost story about a nearby tower',
    'discussing a prophecy an elder once told them',
    'talking about the fall of a great city',
    'wondering who built the old bridge',
    'mentioning a dragon sighting from years ago',

    # ── Festivals & Holidays ────────────────────────────────────────
    'looking forward to Brewfest',
    'talking about last year\'s Hallow\'s End',
    'mentioning the Darkmoon Faire is coming',
    'discussing plans for Winter Veil gifts',
    'reminiscing about the Midsummer Fire Festival',
    'wondering if the Lunar Festival will be good',
    'talking about festival food they love',
    'mentioning a prize they won at a fair',
    'discussing the best fireworks display',
    'looking forward to the Pilgrim\'s Bounty feast',

    # ── Children's Talk ─────────────────────────────────────────────
    'wanting to be an adventurer when they grow up',
    'asking if dragons are real',
    'daring a friend to touch the graveyard gate',
    'talking about a frog they caught by the pond',
    'arguing about who is the strongest hero',
    'pretending to cast a spell',
    'talking about a scary noise they heard last night',
    'asking why the sky is that color',
    'wondering where the road goes',
    'talking about a stray cat they want to keep',
    'making up a story about a treasure map',
    'complaining about chores they have to do',

    # ── Guard & Military ────────────────────────────────────────────
    'complaining about a long shift',
    'discussing patrol routes',
    'mentioning a suspicious person they saw earlier',
    'talking about the night watch being short-staffed',
    'grumbling about standing in the rain',
    'discussing orders from the captain',
    'mentioning they miss their family back home',
    'talking about a close call on patrol last week',
    'complaining about the quality of guard rations',
    'mentioning a deserter who was caught',
    'discussing new recruits and their readiness',
    'wondering when their relief will arrive',
    'talking about a skirmish at the border',
    'mentioning armor that needs repair',

    # ── Health & Ailments ───────────────────────────────────────────
    'complaining about a bad back',
    'mentioning a healer they should visit',
    'talking about a cold going around town',
    'discussing a potion that helped their aches',
    'complaining about not sleeping well',
    'mentioning an old wound acting up',
    'talking about the cost of healing these days',
    'asking if anyone knows a remedy for headaches',
    'discussing the local herbalist\'s remedies',
    'mentioning they feel better after rest',

    # ── Animals & Pets ──────────────────────────────────────────────
    'talking about their dog or cat',
    'mentioning a wild animal they saw near town',
    'discussing the best breed of horse',
    'complaining about rats in the cellar',
    'talking about a hawk circling overhead',
    'mentioning stray dogs in the market',
    'discussing whether wolves have been closer lately',
    'talking about a fisherman\'s catch today',
    'mentioning a bear spotted near the farm',
    'wondering if the murlocs will bother the shore again',

    # ── Superstition & Omens ────────────────────────────────────────
    'mentioning a bad omen they noticed',
    'talking about a lucky charm they carry',
    'discussing an old wives\' tale about crows',
    'mentioning that full moons bring trouble',
    'talking about a curse on an old house',
    'wondering if stepping on a crack really matters',
    'mentioning a dream that felt like a warning',
    'discussing a fortune teller at the market',
    'talking about a strange feeling in the graveyard',
    'mentioning that spilling salt is bad luck',

    # ── Leisure & Entertainment ─────────────────────────────────────
    'talking about a bard performing at the inn tonight',
    'mentioning a card game they played last night',
    'discussing a fishing spot they like',
    'talking about arm wrestling at the tavern',
    'mentioning a book they just finished',
    'talking about a song stuck in their head',
    'discussing a storyteller who visits the square',
    'mentioning a swimming hole nearby',
    'talking about a race between two riders they saw',
    'discussing the best board game to pass time',

    # ── Romantic & Social ───────────────────────────────────────────
    'mentioning someone they fancy',
    'talking about a love letter they received',
    'discussing a wedding they attended',
    'mentioning a breakup in the neighborhood',
    'talking about courting customs in their culture',
    'wondering what to get someone as a gift',
    'mentioning a dance at the town hall',
    'discussing a dinner invitation they are nervous about',

    # ── Complaints & Grumbles ───────────────────────────────────────
    'complaining about the noise at night',
    'grumbling about the early morning bell',
    'talking about the smell from the tannery',
    'complaining about crowded streets',
    'mentioning that the well water tastes strange',
    'grumbling about the cobblestones being uneven',
    'complaining about the mail being slow',
    'talking about mosquitoes near the canal',
    'mentioning a rude merchant at the market',
    'grumbling about the price of firewood',
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
DEFAULT_GOOGLE_MODEL = 'gemini-3.1-flash-lite'
DEFAULT_OPENROUTER_MODEL = 'openai/gpt-4o-mini'
GOOGLE_OPENAI_BASE_URL = (
    'https://generativelanguage.googleapis.com/v1beta/openai/'
)
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'

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


# =============================================================================
# GUILD CHAT TOPICS (roadmap #2) — random subject pool for guild idle chatter.
# Only the in-character RP pool is used; guild chatter runs in character mode
# and its prompt bans game-mechanic talk. Selected per event and injected as an
# optional "topic idea" nudge.
# =============================================================================
GUILD_CHAT_TOPICS_RP = [
    "the dangers of the road you're traveling",
    "a rumor overheard in the last town",
    "the code or philosophy you live by",
    "honoring a fallen comrade",
    "the beauty or menace of the land around you",
    "a personal vow or quest you carry",
    "distrust of the opposing faction",
    "the burden of your calling",
    "a memory from your homeland",
    "wariness of the local wildlife",
    "an omen or strange sight on your path",
    "gratitude for a guildmate's aid",
    "the toll of endless fighting",
    "a wish of good fortune for the guild",
    "longing for a quieter life",
    "pride in your craft or lineage",
    "a warning about a place best avoided",
    "the changing of the seasons or the hour",
    "an old legend tied to this region",
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
    "the quiet before a coming storm",
    "homesickness creeping in at dusk",
    "gratitude for simply seeing another dawn",
    "doubts that visit in the dark hours",
    "the strange peace found in solitude",
    "weariness that sleep won't cure",
    "hope found in a small kindness",
    # --- lore & places ---
    "ruins that hint at a forgotten people",
    "a shrine or grave you passed on the road",
    "stories the elders told when you were young",
    "a battlefield long since grown over with grass",
    "spirits said to linger in this place",
    "a festival or holy day from your youth",
    # --- the calling & the blade ---
    "the weight of the weapon you carry",
    "scars that each tell their own story",
    "an enemy you respect despite everything",
    "the thin line between duty and vengeance",
    "the first time you faced true danger",
    "the discipline your training demanded",
    # --- faction & war ---
    "rumors of the enemy massing nearby",
    "the price the war has taken from your people",
    "an uneasy truce you doubt will hold",
    "tales of heroes who turned the tide",
    # --- nature, beasts & weather ---
    "tracks of a great beast crossing your trail",
    "birdsong, or its uneasy absence, at dawn",
    "a sudden storm that caught you unready",
    "the first frost, or the first thaw",
    "a loyal beast that once saved your life",
    "the night sky far from any town",
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
]
