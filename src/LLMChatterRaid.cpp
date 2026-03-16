/*
 * mod-llm-chatter - PvE raid boss chatter hooks
 */

#include "LLMChatterConfig.h"
#include "LLMChatterRaid.h"
#include "LLMChatterShared.h"
#include "GameTime.h"
#include "Group.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"

#include <set>
#include <unordered_map>

struct RaidBossEntry
{
    uint32 creatureEntry;
    const char* bossName;
    const char* raidName;
    const char* wing;
};

static uint32 MakeKey(uint32 mapId, uint32 bossIndex)
{
    return (mapId << 16) | bossIndex;
}

// clang-format off
static const std::unordered_map<uint32, RaidBossEntry>
    _bossLookup =
{
    // --- Icecrown Citadel (map 631) ---
    {MakeKey(631, 0),
        {36612, "Lord Marrowgar",
         "Icecrown Citadel", "The Lower Spire"}},
    {MakeKey(631, 1),
        {36855, "Lady Deathwhisper",
         "Icecrown Citadel", "The Lower Spire"}},
    {MakeKey(631, 2),
        {0, "Icecrown Gunship Battle",
         "Icecrown Citadel", "The Lower Spire"}},
    {MakeKey(631, 3),
        {37813, "Deathbringer Saurfang",
         "Icecrown Citadel", "The Lower Spire"}},
    {MakeKey(631, 4),
        {36626, "Festergut",
         "Icecrown Citadel", "The Plagueworks"}},
    {MakeKey(631, 5),
        {36627, "Rotface",
         "Icecrown Citadel", "The Plagueworks"}},
    {MakeKey(631, 6),
        {36678, "Professor Putricide",
         "Icecrown Citadel", "The Plagueworks"}},
    {MakeKey(631, 7),
        {37972, "Blood Prince Council",
         "Icecrown Citadel",
         "The Crimson Hall"}},
    {MakeKey(631, 8),
        {37955, "Blood-Queen Lana'thel",
         "Icecrown Citadel",
         "The Crimson Hall"}},
    {MakeKey(631, 9),
        {37126, "Sister Svalna",
         "Icecrown Citadel",
         "The Frostwing Halls"}},
    {MakeKey(631, 10),
        {36789, "Valithria Dreamwalker",
         "Icecrown Citadel",
         "The Frostwing Halls"}},
    {MakeKey(631, 11),
        {36853, "Sindragosa",
         "Icecrown Citadel",
         "The Frostwing Halls"}},
    {MakeKey(631, 12),
        {36597, "The Lich King",
         "Icecrown Citadel",
         "The Frozen Throne"}},

    // --- Ulduar (map 603) ---
    {MakeKey(603, 0),
        {33113, "Flame Leviathan",
         "Ulduar", "The Siege"}},
    {MakeKey(603, 1),
        {33118, "Ignis the Furnace Master",
         "Ulduar", "The Siege"}},
    {MakeKey(603, 2),
        {33186, "Razorscale",
         "Ulduar", "The Siege"}},
    {MakeKey(603, 3),
        {33293, "XT-002 Deconstructor",
         "Ulduar", "The Siege"}},
    {MakeKey(603, 4),
        {32867, "Assembly of Iron",
         "Ulduar", "The Antechamber"}},
    {MakeKey(603, 5),
        {32930, "Kologarn",
         "Ulduar", "The Antechamber"}},
    {MakeKey(603, 6),
        {33515, "Auriaya",
         "Ulduar", "The Antechamber"}},
    {MakeKey(603, 7),
        {32906, "Freya",
         "Ulduar", "The Keepers"}},
    {MakeKey(603, 8),
        {32845, "Hodir",
         "Ulduar", "The Keepers"}},
    {MakeKey(603, 9),
        {33350, "Mimiron",
         "Ulduar", "The Keepers"}},
    {MakeKey(603, 10),
        {32865, "Thorim",
         "Ulduar", "The Keepers"}},
    {MakeKey(603, 11),
        {33271, "General Vezax",
         "Ulduar", "The Descent"}},
    {MakeKey(603, 12),
        {33288, "Yogg-Saron",
         "Ulduar", "The Descent"}},
    {MakeKey(603, 13),
        {32871, "Algalon the Observer",
         "Ulduar",
         "The Celestial Planetarium"}},

    // --- Naxxramas (map 533) ---
    {MakeKey(533, 0),
        {16028, "Patchwerk",
         "Naxxramas",
         "The Construct Quarter"}},
    {MakeKey(533, 1),
        {15931, "Grobbulus",
         "Naxxramas",
         "The Construct Quarter"}},
    {MakeKey(533, 2),
        {15932, "Gluth",
         "Naxxramas",
         "The Construct Quarter"}},
    {MakeKey(533, 3),
        {15954, "Noth the Plaguebringer",
         "Naxxramas",
         "The Plague Quarter"}},
    {MakeKey(533, 4),
        {15936, "Heigan the Unclean",
         "Naxxramas",
         "The Plague Quarter"}},
    {MakeKey(533, 5),
        {16011, "Loatheb",
         "Naxxramas",
         "The Plague Quarter"}},
    {MakeKey(533, 6),
        {15956, "Anub'Rekhan",
         "Naxxramas",
         "The Arachnid Quarter"}},
    {MakeKey(533, 7),
        {15953, "Grand Widow Faerlina",
         "Naxxramas",
         "The Arachnid Quarter"}},
    {MakeKey(533, 8),
        {15952, "Maexxna",
         "Naxxramas",
         "The Arachnid Quarter"}},
    {MakeKey(533, 9),
        {15928, "Thaddius",
         "Naxxramas",
         "The Construct Quarter"}},
    {MakeKey(533, 10),
        {16061, "Instructor Razuvious",
         "Naxxramas",
         "The Military Quarter"}},
    {MakeKey(533, 11),
        {16060, "Gothik the Harvester",
         "Naxxramas",
         "The Military Quarter"}},
    {MakeKey(533, 12),
        {30549, "The Four Horsemen",
         "Naxxramas",
         "The Military Quarter"}},
    {MakeKey(533, 13),
        {15989, "Sapphiron",
         "Naxxramas",
         "The Frostwyrm Lair"}},
    {MakeKey(533, 14),
        {15990, "Kel'Thuzad",
         "Naxxramas",
         "The Frostwyrm Lair"}},

    // --- Karazhan (map 532) ---
    {MakeKey(532, 0),
        {15550, "Attumen the Huntsman",
         "Karazhan", "The Stables"}},
    {MakeKey(532, 1),
        {15687, "Moroes",
         "Karazhan", "The Banquet Hall"}},
    {MakeKey(532, 2),
        {16457, "Maiden of Virtue",
         "Karazhan", "The Guest Chambers"}},
    {MakeKey(532, 4),
        {16812, "Opera Event",
         "Karazhan", "The Opera House"}},
    {MakeKey(532, 5),
        {15691, "The Curator",
         "Karazhan", "The Menagerie"}},
    {MakeKey(532, 6),
        {16524, "Shade of Aran",
         "Karazhan",
         "The Guardian's Library"}},
    {MakeKey(532, 7),
        {15688, "Terestian Illhoof",
         "Karazhan", "The Repository"}},
    {MakeKey(532, 8),
        {15689, "Netherspite",
         "Karazhan", "Netherspite's Lair"}},
    {MakeKey(532, 9),
        {16816, "Chess Event",
         "Karazhan",
         "The Gamesman's Hall"}},
    {MakeKey(532, 10),
        {15690, "Prince Malchezaar",
         "Karazhan", "The Netherspace"}},
    {MakeKey(532, 11),
        {17225, "Nightbane",
         "Karazhan",
         "The Master's Terrace"}},

    // --- Vault of Archavon (map 624) ---
    {MakeKey(624, 0),
        {31125, "Archavon the Stone Watcher",
         "Vault of Archavon", ""}},
    {MakeKey(624, 1),
        {33993, "Emalon the Storm Watcher",
         "Vault of Archavon", ""}},
    {MakeKey(624, 2),
        {35013, "Koralon the Flame Watcher",
         "Vault of Archavon", ""}},
    {MakeKey(624, 3),
        {38433, "Toravon the Ice Watcher",
         "Vault of Archavon", ""}},

    // --- The Obsidian Sanctum (map 615) ---
    {MakeKey(615, 0),
        {28860, "Sartharion",
         "The Obsidian Sanctum", ""}},
    {MakeKey(615, 1),
        {30452, "Tenebron",
         "The Obsidian Sanctum", ""}},
    {MakeKey(615, 2),
        {30449, "Vesperon",
         "The Obsidian Sanctum", ""}},
    {MakeKey(615, 3),
        {30451, "Shadron",
         "The Obsidian Sanctum", ""}},

    // --- The Eye of Eternity (map 616) ---
    {MakeKey(616, 0),
        {28859, "Malygos",
         "The Eye of Eternity", ""}},

    // --- The Ruby Sanctum (map 724) ---
    {MakeKey(724, 0),
        {39751, "Baltharus the Warborn",
         "The Ruby Sanctum", ""}},
    {MakeKey(724, 1),
        {39746, "General Zarithrian",
         "The Ruby Sanctum", ""}},
    {MakeKey(724, 2),
        {39747, "Saviana Ragefire",
         "The Ruby Sanctum", ""}},
    {MakeKey(724, 3),
        {39863, "Halion",
         "The Ruby Sanctum", ""}},

    // --- Trial of the Crusader (map 649) ---
    {MakeKey(649, 5),
        {34796, "Gormok the Impaler",
         "Trial of the Crusader",
         "The Northrend Beasts"}},
    {MakeKey(649, 9),
        {34797, "Icehowl",
         "Trial of the Crusader",
         "The Northrend Beasts"}},
    {MakeKey(649, 10),
        {34780, "Lord Jaraxxus",
         "Trial of the Crusader", ""}},
    {MakeKey(649, 13),
        {34564, "Anub'arak",
         "Trial of the Crusader", ""}},

    // --- Onyxia's Lair (map 249) ---
    {MakeKey(249, 0),
        {10184, "Onyxia",
         "Onyxia's Lair", ""}},

    // --- Molten Core (map 409) ---
    {MakeKey(409, 0),
        {12118, "Lucifron",
         "Molten Core", ""}},
    {MakeKey(409, 1),
        {11982, "Magmadar",
         "Molten Core", ""}},
    {MakeKey(409, 2),
        {12259, "Gehennas",
         "Molten Core", ""}},
    {MakeKey(409, 3),
        {12057, "Garr",
         "Molten Core", ""}},
    {MakeKey(409, 4),
        {12264, "Shazzrah",
         "Molten Core", ""}},
    {MakeKey(409, 5),
        {12056, "Baron Geddon",
         "Molten Core", ""}},
    {MakeKey(409, 6),
        {12098, "Sulfuron Harbinger",
         "Molten Core", ""}},
    {MakeKey(409, 7),
        {11988, "Golemagg the Incinerator",
         "Molten Core", ""}},
    {MakeKey(409, 8),
        {12018, "Majordomo Executus",
         "Molten Core", ""}},
    {MakeKey(409, 9),
        {11502, "Ragnaros",
         "Molten Core", ""}},

    // --- Blackwing Lair (map 469) ---
    {MakeKey(469, 0),
        {12435, "Razorgore the Untamed",
         "Blackwing Lair", ""}},
    {MakeKey(469, 1),
        {13020, "Vaelastrasz the Corrupt",
         "Blackwing Lair", ""}},
    {MakeKey(469, 2),
        {12017, "Broodlord Lashlayer",
         "Blackwing Lair", ""}},
    {MakeKey(469, 3),
        {11983, "Firemaw",
         "Blackwing Lair", ""}},
    {MakeKey(469, 4),
        {14601, "Ebonroc",
         "Blackwing Lair", ""}},
    {MakeKey(469, 5),
        {11981, "Flamegor",
         "Blackwing Lair", ""}},
    {MakeKey(469, 6),
        {14020, "Chromaggus",
         "Blackwing Lair", ""}},
    {MakeKey(469, 7),
        {11583, "Nefarian",
         "Blackwing Lair", ""}},

    // --- Ruins of Ahn'Qiraj (map 509) ---
    {MakeKey(509, 0),
        {15348, "Kurinnaxx",
         "Ruins of Ahn'Qiraj", ""}},
    {MakeKey(509, 1),
        {15341, "General Rajaxx",
         "Ruins of Ahn'Qiraj", ""}},
    {MakeKey(509, 2),
        {15340, "Moam",
         "Ruins of Ahn'Qiraj", ""}},
    {MakeKey(509, 3),
        {15370, "Buru the Gorger",
         "Ruins of Ahn'Qiraj", ""}},
    {MakeKey(509, 4),
        {15369, "Ayamiss the Hunter",
         "Ruins of Ahn'Qiraj", ""}},
    {MakeKey(509, 5),
        {15339, "Ossirian the Unscarred",
         "Ruins of Ahn'Qiraj", ""}},

    // --- Temple of Ahn'Qiraj (map 531) ---
    {MakeKey(531, 1),
        {15263, "The Prophet Skeram",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 2),
        {15544, "Bug Trio",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 3),
        {15516, "Battleguard Sartura",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 4),
        {15510, "Fankriss the Unyielding",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 5),
        {15299, "Viscidus",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 6),
        {15509, "Princess Huhuran",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 7),
        {15276, "The Twin Emperors",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 8),
        {15517, "Ouro",
         "Temple of Ahn'Qiraj", ""}},
    {MakeKey(531, 9),
        {15727, "C'Thun",
         "Temple of Ahn'Qiraj", ""}},

    // --- Zul'Gurub (map 309) ---
    {MakeKey(309, 0),
        {14517, "High Priestess Jeklik",
         "Zul'Gurub", ""}},
    {MakeKey(309, 1),
        {14507, "High Priest Venoxis",
         "Zul'Gurub", ""}},
    {MakeKey(309, 2),
        {14510, "High Priestess Mar'li",
         "Zul'Gurub", ""}},
    {MakeKey(309, 3),
        {14515, "High Priestess Arlokk",
         "Zul'Gurub", ""}},
    {MakeKey(309, 4),
        {14509, "High Priest Thekal",
         "Zul'Gurub", ""}},
    {MakeKey(309, 5),
        {14834, "Hakkar the Soulflayer",
         "Zul'Gurub", ""}},
    {MakeKey(309, 6),
        {11382, "Bloodlord Mandokir",
         "Zul'Gurub", ""}},
    {MakeKey(309, 7),
        {11380, "Jin'do the Hexxer",
         "Zul'Gurub", ""}},
    {MakeKey(309, 8),
        {15114, "Gahz'ranka",
         "Zul'Gurub", ""}},

    // --- Gruul's Lair (map 565) ---
    {MakeKey(565, 0),
        {18831, "High King Maulgar",
         "Gruul's Lair", ""}},
    {MakeKey(565, 1),
        {19044, "Gruul the Dragonkiller",
         "Gruul's Lair", ""}},

    // --- Magtheridon's Lair (map 544) ---
    {MakeKey(544, 0),
        {17257, "Magtheridon",
         "Magtheridon's Lair", ""}},

    // --- Serpentshrine Cavern (map 548) ---
    {MakeKey(548, 0),
        {21216, "Hydross the Unstable",
         "Serpentshrine Cavern", ""}},
    {MakeKey(548, 1),
        {21217, "The Lurker Below",
         "Serpentshrine Cavern", ""}},
    {MakeKey(548, 2),
        {21215, "Leotheras the Blind",
         "Serpentshrine Cavern", ""}},
    {MakeKey(548, 3),
        {21214, "Fathom-Lord Karathress",
         "Serpentshrine Cavern", ""}},
    {MakeKey(548, 4),
        {21213, "Morogrim Tidewalker",
         "Serpentshrine Cavern", ""}},
    {MakeKey(548, 5),
        {21212, "Lady Vashj",
         "Serpentshrine Cavern", ""}},

    // --- Tempest Keep: The Eye (map 550) ---
    {MakeKey(550, 0),
        {19514, "Al'ar",
         "Tempest Keep", ""}},
    {MakeKey(550, 1),
        {18805, "High Astromancer Solarian",
         "Tempest Keep", ""}},
    {MakeKey(550, 2),
        {19516, "Void Reaver",
         "Tempest Keep", ""}},
    {MakeKey(550, 3),
        {19622, "Kael'thas Sunstrider",
         "Tempest Keep", ""}},

    // --- Battle for Mount Hyjal (map 534) ---
    {MakeKey(534, 0),
        {17767, "Rage Winterchill",
         "Battle for Mount Hyjal", ""}},
    {MakeKey(534, 1),
        {17808, "Anetheron",
         "Battle for Mount Hyjal", ""}},
    {MakeKey(534, 2),
        {17888, "Kaz'rogal",
         "Battle for Mount Hyjal", ""}},
    {MakeKey(534, 3),
        {17842, "Azgalor",
         "Battle for Mount Hyjal", ""}},
    {MakeKey(534, 4),
        {17968, "Archimonde",
         "Battle for Mount Hyjal", ""}},

    // --- Black Temple (map 564) ---
    {MakeKey(564, 0),
        {22887, "High Warlord Naj'entus",
         "Black Temple", ""}},
    {MakeKey(564, 1),
        {22898, "Supremus",
         "Black Temple", ""}},
    {MakeKey(564, 2),
        {22841, "Shade of Akama",
         "Black Temple", ""}},
    {MakeKey(564, 3),
        {22871, "Teron Gorefiend",
         "Black Temple", ""}},
    {MakeKey(564, 4),
        {22948, "Gurtogg Bloodboil",
         "Black Temple", ""}},
    {MakeKey(564, 5),
        {22856, "Reliquary of Souls",
         "Black Temple", ""}},
    {MakeKey(564, 6),
        {22947, "Mother Shahraz",
         "Black Temple", ""}},
    {MakeKey(564, 7),
        {22949, "Illidari Council",
         "Black Temple", ""}},
    {MakeKey(564, 8),
        {23089, "Akama",
         "Black Temple", ""}},
    {MakeKey(564, 9),
        {22917, "Illidan Stormrage",
         "Black Temple", ""}},

    // --- Sunwell Plateau (map 580) ---
    {MakeKey(580, 0),
        {24850, "Kalecgos",
         "Sunwell Plateau", ""}},
    {MakeKey(580, 1),
        {24882, "Brutallus",
         "Sunwell Plateau", ""}},
    {MakeKey(580, 2),
        {25038, "Felmyst",
         "Sunwell Plateau", ""}},
    {MakeKey(580, 4),
        {25165, "Eredar Twins",
         "Sunwell Plateau", ""}},
    {MakeKey(580, 5),
        {25741, "M'uru",
         "Sunwell Plateau", ""}},
    {MakeKey(580, 6),
        {25315, "Kil'jaeden",
         "Sunwell Plateau", ""}},
};
// clang-format on

static const char* GetDifficultyString(Map* map)
{
    if (!map)
        return "Unknown";

    Difficulty diff = map->GetDifficulty();

    switch (diff)
    {
        case RAID_DIFFICULTY_10MAN_NORMAL:
            return "10N";
        case RAID_DIFFICULTY_25MAN_NORMAL:
            return "25N";
        case RAID_DIFFICULTY_10MAN_HEROIC:
            return "10H";
        case RAID_DIFFICULTY_25MAN_HEROIC:
            return "25H";
        default:
            return "10N";
    }
}

class LLMChatterRaidScript : public GlobalScript
{
public:
    LLMChatterRaidScript()
        : GlobalScript(
              "LLMChatterRaidScript",
              {GLOBALHOOK_ON_BEFORE_SET_BOSS_STATE})
    {}

    bool IsDatabaseBound() const override
    {
        return false;
    }

    void OnBeforeSetBossState(
        uint32 id, EncounterState newState,
        EncounterState oldState,
        Map* instance) override
    {
        if (!instance || !instance->IsRaid())
            return;

        if (newState == TO_BE_DECIDED)
            return;

        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem
            || !sLLMChatterConfig
                   ->_raidChatterEnable)
            return;

        std::string eventType;
        std::string subtype;
        uint32 chance = 0;

        if (oldState == NOT_STARTED
            && newState == IN_PROGRESS)
        {
            eventType = "raid_boss_pull";
            subtype = "pull";
            chance = sLLMChatterConfig
                ->_raidBossPullChance;
        }
        else if (oldState == IN_PROGRESS
                 && newState == DONE)
        {
            eventType = "raid_boss_kill";
            subtype = "kill";
            chance = sLLMChatterConfig
                ->_raidBossKillChance;
        }
        else if (oldState == IN_PROGRESS
                 && newState == FAIL)
        {
            eventType = "raid_boss_wipe";
            subtype = "wipe";
            chance = sLLMChatterConfig
                ->_raidBossWipeChance;
        }
        else
        {
            return;
        }

        if (urand(1, 100) > chance)
            return;

        // Look up boss metadata
        static const RaidBossEntry UNKNOWN_BOSS =
            {0, "Unknown Boss",
             "Unknown Raid", ""};
        auto it = _bossLookup.find(
            MakeKey(instance->GetId(), id));
        RaidBossEntry const& boss =
            (it != _bossLookup.end())
                ? it->second : UNKNOWN_BOSS;

        const char* difficulty =
            GetDifficultyString(instance);

        // Iterate players in the raid instance
        std::set<uint32> seenGroups;

        Map::PlayerList const& players =
            instance->GetPlayers();
        for (Map::PlayerList::const_iterator
                 itr = players.begin();
             itr != players.end(); ++itr)
        {
            Player* player = itr->GetSource();
            if (!player)
                continue;
            if (IsPlayerBot(player))
                continue;

            Group* group = player->GetGroup();
            if (!group || !GroupHasBots(group))
                continue;

            uint32 groupCounter =
                group->GetGUID().GetCounter();
            if (!seenGroups.insert(groupCounter)
                     .second)
                continue;

            // Build JSON extra_data
            std::string json = "{";
            json += "\"boss_name\":\""
                + JsonEscape(boss.bossName)
                + "\",";
            json += "\"boss_index\":"
                + std::to_string(id) + ",";
            json += "\"boss_entry\":"
                + std::to_string(
                    boss.creatureEntry) + ",";
            json += "\"raid_name\":\""
                + JsonEscape(boss.raidName)
                + "\",";
            if (boss.wing[0] != '\0')
            {
                json += "\"wing\":\""
                    + JsonEscape(boss.wing)
                    + "\",";
            }
            json += "\"difficulty\":\""
                + std::string(difficulty) + "\",";
            json += "\"event_subtype\":\""
                + subtype + "\",";
            json += "\"group_id\":"
                + std::to_string(groupCounter)
                + ",";
            json += "\"player_name\":\""
                + JsonEscape(player->GetName())
                + "\",";
            json += "\"zone_id\":"
                + std::to_string(
                    player->GetZoneId());
            // in_raid added by AppendRaidContext
            json += "}";

            AppendRaidContext(player, json);

            // Per-group, event-type-specific cooldown
            // key prevents pull suppressing kill/wipe
            // and allows multiple groups in same
            // instance to each get their own event
            std::string cooldownKey =
                eventType + "_"
                + std::to_string(
                    instance->GetId())
                + "_" + std::to_string(id)
                + "_" + std::to_string(
                    groupCounter);

            // Enforce cooldown before queueing
            {
                static std::map<std::string, time_t>
                    _raidBossCooldowns;
                time_t now = time(nullptr);
                auto it =
                    _raidBossCooldowns.find(
                        cooldownKey);
                if (it != _raidBossCooldowns.end()
                    && now - it->second < 120)
                {
                    continue;
                }
                _raidBossCooldowns[cooldownKey] =
                    now;
            }

            QueueChatterEvent(
                eventType,
                "player",
                player->GetZoneId(),
                player->GetMapId(),
                GetChatterEventPriority(eventType),
                cooldownKey,
                player->GetGUID().GetCounter(),
                player->GetName(),
                0, "", 0,
                EscapeString(json),
                GetReactionDelaySeconds(eventType),
                120,
                true);

        }
    }
};

void AddLLMChatterRaidScripts()
{
    new LLMChatterRaidScript();
}
