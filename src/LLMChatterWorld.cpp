/*
 * mod-llm-chatter - world/event scripts and delivery ownership
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroup.h"
#include "LLMChatterShared.h"

#include "Channel.h"
#include "ChannelMgr.h"
#include "Chat.h"
#include "CellImpl.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "GameEventMgr.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "Log.h"
#include "MapMgr.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "ScriptMgr.h"
#include "Transport.h"
#include "Weather.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <cstdio>
#include <list>
#include <map>
#include <mutex>
#include <random>
#include <regex>
#include <set>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct NearbyGameObjectCheck
{
    WorldObject const* _obj;
    float _range;

    NearbyGameObjectCheck(
        WorldObject const* obj, float range)
        : _obj(obj), _range(range) {}

    WorldObject const& GetFocusObject() const
    {
        return *_obj;
    }

    bool operator()(GameObject* go)
    {
        return go
            && _obj->IsWithinDistInMap(go, _range)
            && go->isSpawned()
            && go->GetGOInfo();
    }
};

static std::map<std::string, time_t> _goNameCooldowns;

static const char* GetGoTypeName(
    GameobjectTypes type)
{
    switch (type)
    {
        case GAMEOBJECT_TYPE_CHEST:
            return "Chest";
        case GAMEOBJECT_TYPE_GENERIC:
            return "Landmark";
        case GAMEOBJECT_TYPE_SPELL_FOCUS:
            return "SpellFocus";
        case GAMEOBJECT_TYPE_TEXT:
            return "Book";
        case GAMEOBJECT_TYPE_GOOBER:
            return "World Object";
        case GAMEOBJECT_TYPE_QUESTGIVER:
            return "Quest Board";
        case GAMEOBJECT_TYPE_MAILBOX:
            return "Mailbox";
        case GAMEOBJECT_TYPE_MEETINGSTONE:
            return "Meeting Stone";
        case GAMEOBJECT_TYPE_SPELLCASTER:
            return "Portal";
        case GAMEOBJECT_TYPE_MO_TRANSPORT:
            return "Transport";
        case GAMEOBJECT_TYPE_FISHINGHOLE:
            return "Fishing School";
        default:
            return nullptr;
    }
}

static uint8 GetGatheringType(GameObject* go)
{
    if (!go || !go->GetGOInfo())
        return 0;

    uint32 lockId = go->GetGOInfo()->GetLockId();
    if (!lockId)
        return 0;

    LockEntry const* lock =
        sLockStore.LookupEntry(lockId);
    if (!lock)
        return 0;

    for (uint8 i = 0; i < MAX_LOCK_CASE; ++i)
    {
        if (lock->Type[i] != 2)
            continue;
        uint32 skill = lock->Index[i];
        if (skill == LOCKTYPE_HERBALISM)
            return 1;
        if (skill == LOCKTYPE_MINING)
            return 2;
    }

    return 0;
}

static bool IsInterestingGameObject(GameObject* go)
{
    if (!go || !go->GetGOInfo())
        return false;

    if (go->GetGOInfo()->IconName == "Point")
        return false;
    if (go->HasFlag(GAMEOBJECT_FLAGS,
            GO_FLAG_NOT_SELECTABLE))
        return false;

    static const std::set<GameobjectTypes>
        blacklist = {
        GAMEOBJECT_TYPE_TRAP,
        GAMEOBJECT_TYPE_FLAGSTAND,
        GAMEOBJECT_TYPE_FLAGDROP,
        GAMEOBJECT_TYPE_CAPTURE_POINT,
        GAMEOBJECT_TYPE_DO_NOT_USE,
        GAMEOBJECT_TYPE_DO_NOT_USE_2,
        GAMEOBJECT_TYPE_CAMERA,
        GAMEOBJECT_TYPE_MAP_OBJECT,
        GAMEOBJECT_TYPE_AURA_GENERATOR,
        GAMEOBJECT_TYPE_GUARDPOST,
        GAMEOBJECT_TYPE_DUEL_ARBITER,
        GAMEOBJECT_TYPE_AREADAMAGE,
        GAMEOBJECT_TYPE_BINDER,
        GAMEOBJECT_TYPE_DESTRUCTIBLE_BUILDING,
        GAMEOBJECT_TYPE_TRAPDOOR,
        GAMEOBJECT_TYPE_BUTTON,
        GAMEOBJECT_TYPE_SUMMONING_RITUAL,
        GAMEOBJECT_TYPE_DUNGEON_DIFFICULTY,
        GAMEOBJECT_TYPE_MINI_GAME,
        GAMEOBJECT_TYPE_GUILD_BANK,
        GAMEOBJECT_TYPE_FISHINGNODE,
        GAMEOBJECT_TYPE_CHAIR,
        GAMEOBJECT_TYPE_DOOR,
        GAMEOBJECT_TYPE_BARBER_CHAIR,
    };

    return blacklist.count(go->GetGoType()) == 0;
}

static int GetGoInterestScore(GameObject* go)
{
    static const std::set<GameobjectTypes> high = {
        GAMEOBJECT_TYPE_SPELL_FOCUS,
        GAMEOBJECT_TYPE_TEXT,
        GAMEOBJECT_TYPE_GENERIC,
        GAMEOBJECT_TYPE_GOOBER,
        GAMEOBJECT_TYPE_CHEST,
        GAMEOBJECT_TYPE_CHAIR,
    };

    if (high.count(go->GetGoType()))
        return 2;
    return 1;
}

struct NearbyCreatureCheck
{
    WorldObject const* _obj;
    float _range;

    NearbyCreatureCheck(
        WorldObject const* obj, float range)
        : _obj(obj), _range(range) {}

    WorldObject const& GetFocusObject() const
    {
        return *_obj;
    }

    bool operator()(Unit* unit)
    {
        if (!unit || !unit->IsAlive())
            return false;
        if (!unit->ToCreature())
            return false;
        return _obj->IsWithinDistInMap(unit, _range);
    }
};

static const char* GetCreatureRoleName(Creature* cr)
{
    uint32 npcFlags =
        cr->GetUInt32Value(UNIT_NPC_FLAGS);

    if (npcFlags & UNIT_NPC_FLAG_FLIGHTMASTER)
        return "FlightMaster";
    if (npcFlags & UNIT_NPC_FLAG_INNKEEPER)
        return "Innkeeper";
    if (npcFlags & UNIT_NPC_FLAG_QUESTGIVER)
        return "QuestGiver";
    if (npcFlags
        & (UNIT_NPC_FLAG_TRAINER
            | UNIT_NPC_FLAG_TRAINER_CLASS
            | UNIT_NPC_FLAG_TRAINER_PROFESSION))
        return "Trainer";
    if (npcFlags
        & (UNIT_NPC_FLAG_VENDOR
            | UNIT_NPC_FLAG_VENDOR_AMMO
            | UNIT_NPC_FLAG_VENDOR_FOOD
            | UNIT_NPC_FLAG_VENDOR_POISON
            | UNIT_NPC_FLAG_VENDOR_REAGENT))
        return "Vendor";

    uint32 rank = cr->GetCreatureTemplate()->rank;
    if (rank == 4)
        return "RareCreature";

    uint32 cType = cr->GetCreatureTemplate()->type;
    if (cType == CREATURE_TYPE_CRITTER)
        return "Critter";
    if (cType == CREATURE_TYPE_BEAST)
        return "Beast";

    return "NPC";
}

static bool IsInterestingCreature(
    Creature* cr, Player* bot)
{
    if (!cr || !cr->IsAlive())
        return false;

    if (cr->IsPet() || cr->IsTotem()
        || cr->IsGuardian())
        return false;
    if (cr->IsInCombat())
        return false;
    if (cr->IsPlayer())
        return false;

    CreatureTemplate const* tmpl =
        cr->GetCreatureTemplate();
    if (!tmpl)
        return false;

    uint32 cType = tmpl->type;
    if (cType == CREATURE_TYPE_TOTEM
        || cType == CREATURE_TYPE_NON_COMBAT_PET
        || cType == CREATURE_TYPE_GAS_CLOUD
        || cType == CREATURE_TYPE_NOT_SPECIFIED
        || cType == CREATURE_TYPE_MECHANICAL)
        return false;

    uint32 npcFlags =
        cr->GetUInt32Value(UNIT_NPC_FLAGS);
    uint32 rank = tmpl->rank;

    if (rank == 4)
        return true;
    if (npcFlags
        & (UNIT_NPC_FLAG_FLIGHTMASTER
            | UNIT_NPC_FLAG_INNKEEPER
            | UNIT_NPC_FLAG_QUESTGIVER
            | UNIT_NPC_FLAG_TRAINER
            | UNIT_NPC_FLAG_TRAINER_CLASS
            | UNIT_NPC_FLAG_TRAINER_PROFESSION
            | UNIT_NPC_FLAG_VENDOR
            | UNIT_NPC_FLAG_VENDOR_AMMO
            | UNIT_NPC_FLAG_VENDOR_FOOD
            | UNIT_NPC_FLAG_VENDOR_POISON
            | UNIT_NPC_FLAG_VENDOR_REAGENT))
        return true;

    if (cType == CREATURE_TYPE_CRITTER
        || cType == CREATURE_TYPE_BEAST)
        return true;

    if (cType == CREATURE_TYPE_HUMANOID
        && !tmpl->SubName.empty())
        return true;

    return false;
}

static int GetCreatureInterestScore(Creature* cr)
{
    CreatureTemplate const* tmpl =
        cr->GetCreatureTemplate();
    uint32 rank = tmpl->rank;
    uint32 npcFlags =
        cr->GetUInt32Value(UNIT_NPC_FLAGS);

    if (rank == 4)
        return 3;
    if (npcFlags
        & (UNIT_NPC_FLAG_FLIGHTMASTER
            | UNIT_NPC_FLAG_INNKEEPER
            | UNIT_NPC_FLAG_QUESTGIVER
            | UNIT_NPC_FLAG_TRAINER
            | UNIT_NPC_FLAG_TRAINER_CLASS
            | UNIT_NPC_FLAG_TRAINER_PROFESSION
            | UNIT_NPC_FLAG_VENDOR
            | UNIT_NPC_FLAG_VENDOR_AMMO
            | UNIT_NPC_FLAG_VENDOR_FOOD
            | UNIT_NPC_FLAG_VENDOR_POISON
            | UNIT_NPC_FLAG_VENDOR_REAGENT))
        return 2;

    return 1;
}

static std::map<std::string, time_t> _cooldownCache;

static bool IsOnCooldown(
    const std::string& cooldownKey,
    uint32 cooldownSeconds)
{
    auto it = _cooldownCache.find(cooldownKey);
    if (it != _cooldownCache.end())
    {
        time_t now = time(nullptr);
        if (now - it->second < cooldownSeconds)
            return true;
    }

    QueryResult result = CharacterDatabase.Query(
        "SELECT 1 FROM llm_chatter_events "
        "WHERE cooldown_key = '{}' AND created_at > "
        "DATE_SUB(NOW(), INTERVAL {} SECOND) LIMIT 1",
        cooldownKey, cooldownSeconds);

    return static_cast<bool>(result);
}

static void SetCooldown(
    const std::string& cooldownKey)
{
    _cooldownCache[cooldownKey] = time(nullptr);
}

static void QueueEvent(
    const std::string& eventType,
    const std::string& eventScope,
    uint32 zoneId, uint32 mapId,
    const std::string& cooldownKey,
    uint32 cooldownSeconds,
    uint32 subjectGuid,
    const std::string& subjectName,
    uint32 targetGuid,
    const std::string& targetName,
    uint32 targetEntry,
    const std::string& extraData)
{
    if (!sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem)
        return;

    if (eventType == "weather_ambient"
        && !sLLMChatterConfig->_eventsWeather)
        return;

    bool bypassEventCooldown =
        (eventType == "weather_change");

    if (!bypassEventCooldown
        && !cooldownKey.empty()
        && IsOnCooldown(cooldownKey, cooldownSeconds))
        return;

    if (!bypassEventCooldown && !cooldownKey.empty())
        SetCooldown(cooldownKey);

    bool alwaysFire =
        (eventType == "holiday_start"
            || eventType == "holiday_end"
            || eventType == "day_night_transition"
            || eventType == "weather_change");

    uint32 reactionChance =
        sLLMChatterConfig->_eventReactionChance;
    if (eventType == "transport_arrives"
        && sLLMChatterConfig->_transportEventChance > 0)
    {
        reactionChance =
            sLLMChatterConfig->_transportEventChance;
    }
    else if (eventType == "weather_ambient"
        && sLLMChatterConfig->_weatherAmbientChance > 0)
    {
        reactionChance =
            sLLMChatterConfig->_weatherAmbientChance;
    }
    else if (eventType == "minor_event"
        && sLLMChatterConfig->_minorEventChance > 0)
    {
        reactionChance =
            sLLMChatterConfig->_minorEventChance;
    }

    if (!alwaysFire
        && urand(1, 100) > reactionChance)
        return;

    uint32 reactionDelay =
        GetReactionDelaySeconds(eventType);
    uint32 expirationSeconds =
        reactionDelay
        + sLLMChatterConfig->_eventExpirationSeconds;
    std::string sqlSafeExtraData =
        EscapeString(extraData);

    QueueChatterEvent(
        eventType,
        eventScope,
        zoneId,
        mapId,
        GetChatterEventPriority(eventType),
        cooldownKey,
        subjectGuid,
        subjectName,
        targetGuid,
        targetName,
        targetEntry,
        sqlSafeExtraData,
        reactionDelay,
        expirationSeconds,
        true);
}

static bool IsHolidayEvent(uint16 eventId)
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    if (eventId >= events.size())
        return false;
    if (events[eventId].HolidayId == HOLIDAY_NONE)
        return false;

    std::string const& desc =
        events[eventId].Description;
    if (desc.find("Call to Arms") != std::string::npos)
        return false;
    if (desc.find("Building") != std::string::npos)
        return false;
    if (desc.find("Fishing Pools") != std::string::npos)
        return false;
    if (desc.find("Fireworks") != std::string::npos)
        return false;

    return true;
}

static bool IsMinorGameEvent(uint16 eventId)
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    if (eventId >= events.size())
        return false;
    if (events[eventId].HolidayId == HOLIDAY_NONE)
        return false;

    std::string const& desc =
        events[eventId].Description;
    if (desc.find("Call to Arms") != std::string::npos)
        return true;
    if (desc.find("Fishing Pools") != std::string::npos)
        return true;
    if (desc.find("Fireworks") != std::string::npos)
        return true;

    return false;
}

static bool IsCapitalCity(uint32 zoneId)
{
    if (AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(zoneId))
    {
        return (area->flags & AREA_FLAG_CAPITAL) != 0;
    }

    return false;
}

static bool IsInOverworld(Player* player)
{
    if (!player)
        return false;

    WorldSession* session = player->GetSession();
    if (!session || session->PlayerLoading())
        return false;

    Map* map = player->GetMap();
    if (!map)
        return false;

    return !map->Instanceable();
}

static std::vector<uint32> GetZonesWithRealPlayers()
{
    std::map<uint32, bool> zoneMap;
    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();

    for (auto const& pair : sessions)
    {
        WorldSession* session = pair.second;
        if (!session || session->PlayerLoading())
            continue;

        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld())
            continue;

        if (!IsPlayerBot(player)
            && IsInOverworld(player))
        {
            uint32 zoneId = player->GetZoneId();
            if (zoneId > 0)
                zoneMap[zoneId] = true;
        }
    }

    std::vector<uint32> zones;
    for (auto const& pair : zoneMap)
        zones.push_back(pair.first);
    return zones;
}

static void QueueHolidayForZones(
    uint16 eventId,
    const std::string& eventType = "holiday_start")
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    GameEventData const& eventData = events[eventId];

    std::vector<uint32> playerZones =
        GetZonesWithRealPlayers();
    for (uint32 zoneId : playerZones)
    {
        uint32 chance = IsCapitalCity(zoneId)
            ? sLLMChatterConfig->_holidayCityChance
            : sLLMChatterConfig->_holidayZoneChance;

        if (urand(1, 100) > chance)
            continue;

        std::string cooldownKey =
            eventType + ":" + std::to_string(eventId)
            + ":zone:" + std::to_string(zoneId);
        std::string extraData =
            "{\"event_name\":\""
            + JsonEscape(eventData.Description)
            + "\",\"zone_id\":"
            + std::to_string(zoneId) + "}";

        QueueEvent(
            eventType, "global",
            zoneId, 0, cooldownKey,
            sLLMChatterConfig
                ->_holidayCooldownSeconds,
            0, "", 0, "",
            eventId, extraData);
    }
}

std::string GetZoneName(uint32 zoneId)
{
    if (AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId))
    {
        uint8 locale = sWorld->GetDefaultDbcLocale();
        char const* n = area->area_name[locale];
        std::string zoneName = n ? n : "";
        if (zoneName.empty())
        {
            n = area->area_name[LOCALE_enUS];
            zoneName = n ? n : "";
        }
        if (!zoneName.empty())
            return zoneName;
    }

    return "Unknown Zone";
}

bool CanSpeakInGeneralChannel(Player* bot)
{
    if (!bot || !bot->IsInWorld())
        return false;

    // Ensure the bot is joined to the correct
    // General channel for its current zone.
    // Bots present when the server starts never
    // trigger OnPlayerUpdateZone, so without this
    // they would never be in any General channel.
    EnsureBotInGeneralChannel(bot);

    uint32 zoneId = bot->GetZoneId();
    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId);
    if (!area)
        return false;

    char const* zn =
        area->area_name[sWorld->GetDefaultDbcLocale()];
    std::string zoneName = zn ? zn : "";
    if (zoneName.empty())
    {
        zn = area->area_name[LOCALE_enUS];
        zoneName = zn ? zn : "";
    }
    if (zoneName.empty())
        return false;

    ChannelMgr* cMgr =
        ChannelMgr::forTeam(bot->GetTeamId());
    if (!cMgr)
        return false;

    for (auto const& [key, channel] :
         cMgr->GetChannels())
    {
        if (!channel)
            continue;
        if (channel->GetChannelId()
            != ChatChannelId::GENERAL)
            continue;
        if (channel->GetName().find(zoneName)
            == std::string::npos)
            continue;

        return bot->IsInChannel(channel);
    }

    return false;
}

class LLMChatterGameEventScript
    : public GameEventScript
{
public:
    LLMChatterGameEventScript()
        : GameEventScript(
              "LLMChatterGameEventScript",
              {GAMEEVENTHOOK_ON_START,
                  GAMEEVENTHOOK_ON_STOP}) {}

    void OnStart(uint16 eventId) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem)
            return;

        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();

        if (sLLMChatterConfig->_eventsHolidays
            && IsHolidayEvent(eventId))
        {
            QueueHolidayForZones(
                eventId, "holiday_start");
        }
        else if (sLLMChatterConfig->_eventsMinor
            && IsMinorGameEvent(eventId))
        {
            QueueHolidayForZones(
                eventId, "minor_event");
        }
    }

    void OnStop(uint16 eventId) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem)
            return;

        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();

        if (sLLMChatterConfig->_eventsHolidays
            && IsHolidayEvent(eventId))
        {
            QueueHolidayForZones(
                eventId, "holiday_end");
        }
    }
};

static std::map<uint32, WeatherState> _zoneWeatherState;

static std::string GetWeatherStateName(
    WeatherState state)
{
    switch (state)
    {
        case WEATHER_STATE_FINE: return "clear";
        case WEATHER_STATE_FOG: return "foggy";
        case WEATHER_STATE_LIGHT_RAIN:
            return "light rain";
        case WEATHER_STATE_MEDIUM_RAIN:
            return "rain";
        case WEATHER_STATE_HEAVY_RAIN:
            return "heavy rain";
        case WEATHER_STATE_LIGHT_SNOW:
            return "light snow";
        case WEATHER_STATE_MEDIUM_SNOW:
            return "snow";
        case WEATHER_STATE_HEAVY_SNOW:
            return "heavy snow";
        case WEATHER_STATE_LIGHT_SANDSTORM:
            return "light sandstorm";
        case WEATHER_STATE_MEDIUM_SANDSTORM:
            return "sandstorm";
        case WEATHER_STATE_HEAVY_SANDSTORM:
            return "heavy sandstorm";
        case WEATHER_STATE_THUNDERS:
            return "thunderstorm";
        case WEATHER_STATE_BLACKRAIN:
            return "black rain";
        case WEATHER_STATE_BLACKSNOW:
            return "black snow";
        default:
            return "unknown";
    }
}

static std::string GetWeatherCategory(
    WeatherState state)
{
    switch (state)
    {
        case WEATHER_STATE_LIGHT_RAIN:
        case WEATHER_STATE_MEDIUM_RAIN:
        case WEATHER_STATE_HEAVY_RAIN:
        case WEATHER_STATE_BLACKRAIN:
            return "rain";
        case WEATHER_STATE_LIGHT_SNOW:
        case WEATHER_STATE_MEDIUM_SNOW:
        case WEATHER_STATE_HEAVY_SNOW:
        case WEATHER_STATE_BLACKSNOW:
            return "snow";
        case WEATHER_STATE_LIGHT_SANDSTORM:
        case WEATHER_STATE_MEDIUM_SANDSTORM:
        case WEATHER_STATE_HEAVY_SANDSTORM:
            return "sandstorm";
        case WEATHER_STATE_FOG:
            return "fog";
        case WEATHER_STATE_THUNDERS:
            return "storm";
        default:
            return "weather";
    }
}

static std::string GetWeatherIntensity(float grade)
{
    if (grade < 0.25f)
        return "mild";
    if (grade < 0.5f)
        return "moderate";
    if (grade < 0.75f)
        return "strong";
    return "intense";
}

class LLMChatterALEScript : public ALEScript
{
public:
    LLMChatterALEScript()
        : ALEScript("LLMChatterALEScript") {}

    void OnWeatherChange(
        Weather* weather,
        WeatherState state,
        float grade) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem)
            return;
        if (!sLLMChatterConfig->_eventsWeather)
            return;

        uint32 zoneId = weather->GetZone();
        WeatherState prevState = WEATHER_STATE_FINE;
        auto it = _zoneWeatherState.find(zoneId);
        if (it != _zoneWeatherState.end())
            prevState = it->second;

        _zoneWeatherState[zoneId] = state;

        bool hasRealPlayer = false;
        auto const& sessions =
            sWorldSessionMgr->GetAllSessions();
        for (auto const& pair : sessions)
        {
            WorldSession* session = pair.second;
            if (!session || session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player || !player->IsInWorld())
                continue;

            if (!IsPlayerBot(player)
                && player->GetZoneId() == zoneId
                && IsInOverworld(player))
            {
                hasRealPlayer = true;
                break;
            }
        }

        if (!hasRealPlayer)
            return;

        std::string transitionType;
        if (prevState == WEATHER_STATE_FINE
            && state != WEATHER_STATE_FINE)
        {
            transitionType = "starting";
        }
        else if (prevState != WEATHER_STATE_FINE
            && state == WEATHER_STATE_FINE)
        {
            transitionType = "clearing";
        }
        else if (prevState != WEATHER_STATE_FINE
            && state != WEATHER_STATE_FINE)
        {
            if (GetWeatherCategory(prevState)
                == GetWeatherCategory(state))
                transitionType = "intensifying";
            else
                transitionType = "changing";
        }
        else
        {
            return;
        }

        std::string weatherName =
            GetWeatherStateName(state);
        std::string prevWeatherName =
            GetWeatherStateName(prevState);
        std::string intensity =
            GetWeatherIntensity(grade);
        std::string category =
            GetWeatherCategory(state);
        std::string cooldownKey =
            "weather:" + std::to_string(zoneId)
            + ":" + transitionType;

        std::string extraData =
            "{\"weather_type\":\"" + weatherName
            + "\","
            "\"previous_weather\":\""
            + prevWeatherName + "\","
            "\"transition\":\"" + transitionType
            + "\","
            "\"category\":\"" + category + "\","
            "\"intensity\":\"" + intensity + "\","
            "\"grade\":" + std::to_string(grade)
            + "}";

        QueueEvent("weather_change", "zone",
            zoneId, 0, cooldownKey,
            sLLMChatterConfig->_weatherCooldownSeconds,
            0, "", 0, "",
            static_cast<uint32>(state),
            extraData);
    }
};

struct TransportInfo
{
    uint32 entry;
    std::string fullName;
    std::string destination;
    std::string transportType;
    TeamId teamId = TEAM_NEUTRAL;
};

static std::map<uint32, TransportInfo> _transportCache;
static std::map<ObjectGuid::LowType,
    std::pair<uint32, uint32>> _transportZones;

static void ParseTransportName(
    const std::string& fullName,
    std::string& destination,
    std::string& transportType)
{
    destination = "";
    transportType = "";

    size_t andPos = fullName.find(" and ");
    if (andPos == std::string::npos)
    {
        destination = fullName;
        return;
    }

    std::string afterAnd =
        fullName.substr(andPos + 5);
    size_t parenPos = afterAnd.find(" (");
    if (parenPos != std::string::npos)
    {
        destination = afterAnd.substr(0, parenPos);
        std::string typeSection =
            afterAnd.substr(parenPos + 2);
        size_t commaPos = typeSection.find(',');
        if (commaPos != std::string::npos)
            transportType = typeSection.substr(0, commaPos);
        else
        {
            size_t closeParenPos =
                typeSection.find(')');
            if (closeParenPos != std::string::npos)
            {
                transportType = typeSection.substr(
                    0, closeParenPos);
            }
        }
    }
    else
    {
        destination = afterAnd;
    }
}

static TeamId ParseTransportTeam(
    std::string const& fullName)
{
    if (fullName.find(", Alliance")
        != std::string::npos)
        return TEAM_ALLIANCE;

    if (fullName.find(", Horde")
        != std::string::npos)
        return TEAM_HORDE;

    return TEAM_NEUTRAL;
}

static void LoadTransportCache()
{
    _transportCache.clear();

    QueryResult result = WorldDatabase.Query(
        "SELECT entry, name FROM transports");
    if (!result)
        return;

    do
    {
        Field* fields = result->Fetch();
        uint32 entry = fields[0].Get<uint32>();
        std::string name =
            fields[1].Get<std::string>();

        TransportInfo info;
        info.entry = entry;
        info.fullName = name;
        ParseTransportName(
            name, info.destination,
            info.transportType);
        info.teamId = ParseTransportTeam(name);

        _transportCache[entry] = info;
    } while (result->NextRow());
}

class LLMChatterWorldScript : public WorldScript
{
public:
    LLMChatterWorldScript()
        : WorldScript(
              "LLMChatterWorldScript",
              {WORLDHOOK_ON_AFTER_CONFIG_LOAD,
                  WORLDHOOK_ON_STARTUP,
                  WORLDHOOK_ON_UPDATE}) {}

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sLLMChatterConfig->LoadConfig();
    }

    void OnStartup() override
    {
        if (!sLLMChatterConfig->IsEnabled())
            return;

        CharacterDatabase.Execute(
            "DELETE FROM llm_chatter_messages "
            "WHERE delivered = 0");
        CharacterDatabase.Execute(
            "UPDATE llm_chatter_queue "
            "SET status = 'cancelled' "
            "WHERE status IN ('pending', 'processing')");
        CharacterDatabase.Execute(
            "UPDATE llm_chatter_events "
            "SET status = 'expired' "
            "WHERE status IN ('pending', 'processing')");
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_bot_traits");
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_chat_history");
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_cached_responses");

        LoadTransportCache();

        LoadNamedBossCache();

        _lastTriggerTime = 0;
        _lastDeliveryTime = 0;
        _lastEnvironmentCheckTime = 0;
        _lastTransportCheckTime = 0;
        _lastGoScanTime = 0;
        _lastQuestFlushTime = 0;
        _lastGroupJoinFlushTime = 0;
        _lastRaidMoraleTime = 0;
        _lastTimePeriod = "";
    }

    void OnUpdate(uint32 /*diff*/) override
    {
        if (!sLLMChatterConfig->IsEnabled())
            return;

        uint32 now = getMSTime();

        if (now - _lastDeliveryTime
            >= sLLMChatterConfig->_deliveryPollMs)
        {
            _lastDeliveryTime = now;
            DeliverPendingMessages();
        }

        if (now - _lastTriggerTime
            >= sLLMChatterConfig->_triggerIntervalSeconds
                * 1000)
        {
            _lastTriggerTime = now;
            TryTriggerChatter();
        }

        if (sLLMChatterConfig->_useEventSystem
            && now - _lastEnvironmentCheckTime
                >= sLLMChatterConfig
                    ->_environmentCheckSeconds
                    * 1000)
        {
            _lastEnvironmentCheckTime = now;
            CheckDayNightTransition();
            if (sLLMChatterConfig->_eventsHolidays
                || sLLMChatterConfig->_eventsMinor)
                CheckActiveHolidays();
            if (sLLMChatterConfig->_eventsWeather)
                CheckAmbientWeather();
        }

        if (sLLMChatterConfig->_useEventSystem
            && sLLMChatterConfig->_eventsTransports
            && now - _lastTransportCheckTime
                >= sLLMChatterConfig
                    ->_transportCheckSeconds
                    * 1000)
        {
            _lastTransportCheckTime = now;
            CheckTransportZones();
        }

        {
            static time_t lastCombatStateCheck = 0;
            time_t nowSec = time(nullptr);
            if (nowSec - lastCombatStateCheck
                >= (time_t)sLLMChatterConfig
                       ->_combatStateCheckInterval)
            {
                lastCombatStateCheck = nowSec;
                CheckGroupCombatState();
            }
        }

        if (sLLMChatterConfig->_nearbyObjectEnable
            && sLLMChatterConfig->_useGroupChatter
            && now - _lastGoScanTime
                >= sLLMChatterConfig
                    ->_nearbyObjectCheckInterval
                    * 1000)
        {
            _lastGoScanTime = now;
            CheckNearbyGameObjects();
        }

        if (sLLMChatterConfig->_useGroupChatter
            && now - _lastQuestFlushTime >= 1000)
        {
            _lastQuestFlushTime = now;
            FlushQuestAcceptBatches();
        }

        if (sLLMChatterConfig->_useGroupChatter
            && now - _lastGroupJoinFlushTime >= 1000)
        {
            _lastGroupJoinFlushTime = now;
            FlushGroupJoinBatches();
        }

        if (sLLMChatterConfig->_useEventSystem
            && sLLMChatterConfig->_raidChatterEnable
            && sLLMChatterConfig->_raidMoraleEnable
            && now - _lastRaidMoraleTime
                >= sLLMChatterConfig
                    ->_raidMoraleCooldown
                    * 1000)
        {
            _lastRaidMoraleTime = now;
            CheckRaidIdleMorale();
        }
    }

private:
    uint32 _lastTriggerTime = 0;
    uint32 _lastDeliveryTime = 0;
    uint32 _lastEnvironmentCheckTime = 0;
    uint32 _lastTransportCheckTime = 0;
    uint32 _lastGoScanTime = 0;
    uint32 _lastQuestFlushTime = 0;
    uint32 _lastGroupJoinFlushTime = 0;
    uint32 _lastRaidMoraleTime = 0;
    std::string _lastTimePeriod;

    void CheckDayNightTransition()
    {
        time_t now = time(nullptr);
        tm localTimeBuf = {};
#ifdef _WIN32
        localtime_s(&localTimeBuf, &now);
#else
        localtime_r(&now, &localTimeBuf);
#endif
        int hour = localTimeBuf.tm_hour;
        int minute = localTimeBuf.tm_min;

        std::string timePeriod;
        std::string description;
        if (hour >= 5 && hour < 8)
        {
            timePeriod = "dawn";
            description = "the first light of dawn";
        }
        else if (hour >= 8 && hour < 17)
        {
            timePeriod = "day";
            description = "full daylight";
        }
        else if (hour >= 17 && hour < 20)
        {
            timePeriod = "dusk";
            description = "the sun setting";
        }
        else
        {
            timePeriod = "night";
            description = "the dark of night";
        }

        std::string previousPeriod = _lastTimePeriod;
        _lastTimePeriod = timePeriod;
        if (previousPeriod.empty())
            return;

        bool isDay = (hour >= 6 && hour < 18);
        std::string cooldownKey =
            "time_period:" + timePeriod;
        std::string extraData = "{"
            "\"is_day\":"
            + std::string(isDay ? "true" : "false")
            + ","
            "\"hour\":" + std::to_string(hour)
            + ","
            "\"minute\":" + std::to_string(minute)
            + ","
            "\"time_period\":\"" + timePeriod + "\","
            "\"previous_period\":\"" + previousPeriod
            + "\","
            "\"description\":\""
            + JsonEscape(description) + "\""
            "}";

        QueueEvent("day_night_transition", "global",
            0, 0, cooldownKey,
            sLLMChatterConfig
                ->_dayNightCooldownSeconds,
            0, "", 0, "", 0, extraData);
    }

    void CheckAmbientWeather()
    {
        for (auto const& pair : _zoneWeatherState)
        {
            uint32 zoneId = pair.first;
            WeatherState state = pair.second;
            if (state == WEATHER_STATE_FINE)
                continue;

            bool hasRealPlayer = false;
            auto const& sessions =
                sWorldSessionMgr->GetAllSessions();
            for (auto const& sessionPair : sessions)
            {
                WorldSession* session =
                    sessionPair.second;
                if (!session || session->PlayerLoading())
                    continue;

                Player* player = session->GetPlayer();
                if (!player || !player->IsInWorld())
                    continue;

                if (!IsPlayerBot(player)
                    && player->GetZoneId() == zoneId
                    && IsInOverworld(player))
                {
                    hasRealPlayer = true;
                    break;
                }
            }

            if (!hasRealPlayer)
                continue;

            std::string weatherName =
                GetWeatherStateName(state);
            std::string category =
                GetWeatherCategory(state);
            std::string cooldownKey =
                "weather_ambient:"
                + std::to_string(zoneId) + ":"
                + weatherName;
            std::string extraData =
                "{\"weather_type\":\""
                + weatherName + "\","
                "\"category\":\"" + category + "\","
                "\"intensity\":\"sustained\","
                "\"is_ambient\":true}";

            QueueEvent(
                "weather_ambient", "zone",
                zoneId, 0, cooldownKey,
                sLLMChatterConfig
                    ->_weatherAmbientCooldownSeconds,
                0, "", 0, "",
                static_cast<uint32>(state),
                extraData);
        }
    }

    void CheckActiveHolidays()
    {
        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();
        for (uint16 eventId = 1;
             eventId < events.size();
             ++eventId)
        {
            if (!sGameEventMgr->IsActiveEvent(eventId))
                continue;

            if (sLLMChatterConfig->_eventsHolidays
                && IsHolidayEvent(eventId))
            {
                QueueHolidayForZones(eventId);
            }
            else if (
                sLLMChatterConfig->_eventsMinor
                && IsMinorGameEvent(eventId))
            {
                QueueHolidayForZones(
                    eventId, "minor_event");
            }
        }
    }

    void CheckTransportZones()
    {
        std::vector<uint32> activeZones =
            GetZonesWithRealPlayers();
        if (activeZones.empty())
            return;

        std::unordered_set<uint32> activeZoneSet(
            activeZones.begin(),
            activeZones.end());

        sMapMgr->DoForAllMaps([&](Map* map)
        {
            if (!map)
                return;

            TransportsContainer const& transports =
                map->GetAllTransports();

            for (Transport* transport : transports)
            {
                if (!transport)
                    continue;

                ObjectGuid::LowType guid =
                    transport->GetGUID().GetCounter();
                uint32 entry = transport->GetEntry();
                uint32 mapId = map->GetId();
                uint32 currentZone = map->GetZoneId(
                    transport->GetPhaseMask(),
                    transport->GetPositionX(),
                    transport->GetPositionY(),
                    transport->GetPositionZ());

                if (currentZone == 0)
                    continue;

                auto it = _transportZones.find(guid);
                if (it == _transportZones.end())
                {
                    _transportZones[guid] = {
                        currentZone, mapId};
                    continue;
                }

                uint32 lastZone = it->second.first;
                uint32 lastMap = it->second.second;
                if (lastZone == currentZone
                    && lastMap == mapId)
                    continue;

                if (activeZoneSet.find(currentZone)
                    == activeZoneSet.end())
                {
                    _transportZones[guid] = {
                        currentZone, mapId};
                    continue;
                }

                auto cacheIt =
                    _transportCache.find(entry);
                if (cacheIt == _transportCache.end())
                {
                    _transportZones[guid] = {
                        currentZone, mapId};
                    continue;
                }

                TransportInfo const& info =
                    cacheIt->second;
                std::vector<Player*> verifiedBots =
                    GetTransportBotsInZone(
                        currentZone, info.teamId);

                if (!verifiedBots.empty())
                {
                    std::string verifiedJson = "[";
                    for (size_t i = 0;
                         i < verifiedBots.size(); ++i)
                    {
                        if (i > 0)
                            verifiedJson += ",";
                        verifiedJson += std::to_string(
                            verifiedBots[i]
                                ->GetGUID()
                                .GetCounter());
                    }
                    verifiedJson += "]";

                    // Use one cooldown per transport
                    // entry so a single route cycle
                    // only announces once even if it
                    // crosses multiple zones while
                    // approaching the dock.
                    std::string cooldownKey =
                        "transport:"
                        + std::to_string(entry);
                    std::string extraData = "{"
                        "\"transport_entry\":"
                        + std::to_string(entry) + ","
                        "\"transport_name\":\""
                        + JsonEscape(info.fullName) + "\","
                        "\"destination\":\""
                        + JsonEscape(info.destination)
                        + "\","
                        "\"transport_type\":\""
                        + JsonEscape(info.transportType)
                        + "\","
                        "\"verified_bots\":"
                        + verifiedJson + "}";

                    QueueEvent(
                        "transport_arrives",
                        "zone",
                        currentZone,
                        mapId,
                        cooldownKey,
                        sLLMChatterConfig
                            ->_transportCooldownSeconds,
                        0, "", 0, info.fullName,
                        entry, extraData);
                }

                _transportZones[guid] = {
                    currentZone, mapId};
            }
        });
    }

    void CheckNearbyGameObjects()
    {
        time_t now = time(nullptr);
        for (auto it = _goNameCooldowns.begin();
             it != _goNameCooldowns.end();)
        {
            if (now - it->second
                > (time_t)sLLMChatterConfig
                      ->_nearbyObjectNameCooldown)
            {
                it = _goNameCooldowns.erase(it);
            }
            else
            {
                ++it;
            }
        }

        WorldSessionMgr::SessionMap const& sessions =
            sWorldSessionMgr->GetAllSessions();
        for (auto const& pair : sessions)
        {
            WorldSession* session = pair.second;
            if (!session || session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player || !player->IsInWorld()
                || IsPlayerBot(player))
                continue;

            Group* group = player->GetGroup();
            if (!group || !GroupHasBots(group))
                continue;

            Map* goMap = player->GetMap();
            if (player->IsInCombat()
                || player->InBattleground()
                || player->IsMounted()
                || player->IsFlying())
                continue;

            std::vector<Player*> bots;
            bool groupInCombat = false;
            for (auto ref = group->GetFirstMember();
                 ref; ref = ref->next())
            {
                Player* member = ref->GetSource();
                if (!member || !member->IsInWorld())
                    continue;
                if (member->IsInCombat())
                {
                    groupInCombat = true;
                    break;
                }
                if (IsPlayerBot(member)
                    && member->GetMapId()
                        == player->GetMapId())
                {
                    bots.push_back(member);
                }
            }

            if (groupInCombat || bots.empty())
                continue;

            Player* bot = bots[urand(0, bots.size() - 1)];
            uint32 botZoneId = bot->GetZoneId();
            std::string cooldownKey = fmt::format(
                "nearby_obj:group:{}:zone:{}",
                group->GetGUID().GetCounter(),
                botZoneId);
            if (IsOnCooldown(
                    cooldownKey,
                    sLLMChatterConfig
                        ->_nearbyObjectCooldown))
                continue;

            if (urand(1, 100)
                > sLLMChatterConfig
                      ->_nearbyObjectChance)
                continue;

            float radius =
                (float)sLLMChatterConfig
                    ->_nearbyObjectScanRadius;

            struct ScoredPOI
            {
                std::string name;
                std::string typeName;
                std::string subName;
                float distance;
                uint32 entry;
                uint32 spellFocusId;
                uint32 level;
                int score;
                bool isCreature;
            };

            std::vector<ScoredPOI> candidates;

            std::list<GameObject*> goList;
            NearbyGameObjectCheck goCheck(bot, radius);
            Acore::GameObjectListSearcher<
                NearbyGameObjectCheck>
                goSearcher(bot, goList, goCheck);
            Cell::VisitObjects(bot, goSearcher, radius);

            for (GameObject* go : goList)
            {
                if (!IsInterestingGameObject(go))
                    continue;

                std::string goName =
                    go->GetGOInfo()->name;
                if (goName.empty())
                    continue;

                std::string nameCdKey =
                    fmt::format("{}:{}",
                        bot->GetName(), goName);
                auto cdIt =
                    _goNameCooldowns.find(nameCdKey);
                if (cdIt != _goNameCooldowns.end()
                    && now - cdIt->second
                        < (time_t)sLLMChatterConfig
                              ->_nearbyObjectNameCooldown)
                    continue;

                ScoredPOI sp;
                sp.name = goName;

                uint8 gather = GetGatheringType(go);
                if (gather == 1)
                    sp.typeName = "Herb";
                else if (gather == 2)
                    sp.typeName = "Ore Vein";
                else
                {
                    const char* tn =
                        GetGoTypeName(go->GetGoType());
                    if (!tn)
                        continue;
                    sp.typeName = tn;
                }

                sp.subName = "";
                sp.distance = bot->GetDistance(go);
                sp.entry = go->GetEntry();
                sp.spellFocusId = 0;
                if (go->GetGoType()
                    == GAMEOBJECT_TYPE_SPELL_FOCUS)
                {
                    sp.spellFocusId =
                        go->GetGOInfo()
                            ->spellFocus.focusId;
                }
                sp.level = 0;
                sp.score = GetGoInterestScore(go);
                sp.isCreature = false;
                candidates.push_back(sp);
            }

            std::list<Creature*> crList;
            NearbyCreatureCheck crCheck(bot, radius);
            Acore::CreatureListSearcher<
                NearbyCreatureCheck>
                crSearcher(bot, crList, crCheck);
            Cell::VisitObjects(bot, crSearcher, radius);

            for (Creature* cr : crList)
            {
                if (!IsInterestingCreature(cr, bot))
                    continue;

                std::string crName = cr->GetName();
                if (crName.empty())
                    continue;

                std::string nameCdKey =
                    fmt::format("{}:{}",
                        bot->GetName(), crName);
                auto cdIt =
                    _goNameCooldowns.find(nameCdKey);
                if (cdIt != _goNameCooldowns.end()
                    && now - cdIt->second
                        < (time_t)sLLMChatterConfig
                              ->_nearbyObjectNameCooldown)
                    continue;

                ScoredPOI sp;
                sp.name = crName;
                sp.typeName =
                    GetCreatureRoleName(cr);
                sp.subName =
                    cr->GetCreatureTemplate()->SubName;
                sp.distance = bot->GetDistance(cr);
                sp.entry = cr->GetEntry();
                sp.spellFocusId = 0;
                sp.level = cr->GetLevel();
                sp.score =
                    GetCreatureInterestScore(cr);
                sp.isCreature = true;
                candidates.push_back(sp);
            }

            {
                std::map<std::string, size_t> best;
                for (size_t i = 0;
                     i < candidates.size();
                     ++i)
                {
                    auto bestIt =
                        best.find(candidates[i].name);
                    if (bestIt == best.end())
                        best[candidates[i].name] = i;
                    else if (
                        candidates[i].distance
                        < candidates[bestIt->second]
                              .distance)
                        bestIt->second = i;
                }

                std::vector<ScoredPOI> deduped;
                for (auto& [nm, idx] : best)
                    deduped.push_back(candidates[idx]);
                candidates = std::move(deduped);
            }

            if (candidates.empty())
                continue;

            // Shuffle before sort so same-score items are
            // randomly ordered. Prevents always picking the
            // same object when idle near multiple POIs.
            static std::mt19937 rng(std::random_device{}());
            std::shuffle(candidates.begin(),
                candidates.end(), rng);

            std::stable_sort(candidates.begin(),
                candidates.end(),
                [](const ScoredPOI& a,
                   const ScoredPOI& b) {
                    return a.score > b.score;
                });

            // Send only the top-scored POI to the LLM.
            // Multiple objects caused ambiguity in prompts
            // and complicate the facing feature.
            candidates.resize(1);

            std::string objectsJson = "[";
            for (size_t i = 0;
                 i < candidates.size(); ++i)
            {
                auto& c = candidates[i];
                if (i > 0)
                    objectsJson += ",";
                objectsJson += fmt::format(
                    R"({{"name":"{}",)"
                    R"("type":"{}",)"
                    R"("sub_name":"{}",)"
                    R"("distance_yards":{:.1f},)"
                    R"("entry":{},)"
                    R"("spell_focus_id":{},)"
                    R"("level":{},)"
                    R"("is_creature":{}}})",
                    JsonEscape(c.name),
                    JsonEscape(c.typeName),
                    JsonEscape(c.subName),
                    c.distance,
                    c.entry,
                    c.spellFocusId,
                    c.level,
                    c.isCreature ? "true" : "false");
            }
            objectsJson += "]";

            uint32 zoneId = bot->GetZoneId();
            uint32 areaId = bot->GetAreaId();
            uint32 mapId = bot->GetMapId();
            AreaTableEntry const* zone =
                sAreaTableStore.LookupEntry(zoneId);
            AreaTableEntry const* area =
                sAreaTableStore.LookupEntry(areaId);
            char const* zp = zone
                ? zone->area_name[
                    sWorld->GetDefaultDbcLocale()]
                : nullptr;
            std::string zoneName = zp ? zp : "";
            char const* sp = area
                ? area->area_name[
                    sWorld->GetDefaultDbcLocale()]
                : nullptr;
            std::string subzoneName = sp ? sp : "";
            bool inCity =
                zone
                && (zone->flags & AREA_FLAG_CAPITAL);
            bool inDungeon =
                bot->GetMap()
                && bot->GetMap()->IsDungeon();

            std::string extraJson = fmt::format(
                R"({{"objects":{},"bot_guid":{},)"
                R"("bot_name":"{}",)"
                R"("bot_class":{},)"
                R"("bot_race":{},)"
                R"("group_id":{},)"
                R"("zone_name":"{}",)"
                R"("subzone_name":"{}",)"
                R"("in_city":{},)"
                R"("in_dungeon":{}}})",
                objectsJson,
                bot->GetGUID().GetCounter(),
                JsonEscape(bot->GetName()),
                (int)bot->getClass(),
                (int)bot->getRace(),
                group->GetGUID().GetCounter(),
                JsonEscape(zoneName),
                JsonEscape(subzoneName),
                inCity ? "true" : "false",
                inDungeon ? "true" : "false");

            // This direct caller bypasses QueueEvent(), so it must keep
            // the JSON payload SQL-safe itself before insertion.
            extraJson = EscapeString(extraJson);

            // Primary POI for facing at delivery
            // time.  target_guid stores the creature
            // entry as a non-zero sentinel (not an
            // instance GUID); 0 = game object.
            auto& primary = candidates[0];
            uint32 facingTargetGuid =
                primary.isCreature
                    ? primary.entry : 0;
            uint32 facingTargetEntry =
                primary.entry;
            std::string facingTargetName =
                primary.name;

            QueueChatterEvent(
                "bot_group_nearby_object",
                "player",
                zoneId,
                mapId,
                GetChatterEventPriority(
                    "bot_group_nearby_object"),
                cooldownKey,
                bot->GetGUID().GetCounter(),
                bot->GetName(),
                facingTargetGuid,
                facingTargetName,
                facingTargetEntry,
                extraJson,
                GetReactionDelaySeconds(
                    "bot_group_nearby_object"),
                sLLMChatterConfig
                    ->_eventExpirationSeconds,
                // Keep direct-call semantics aligned with the group and
                // player paths instead of QueueEvent()'s NULL-on-zero
                // wrapper behavior.
                false);

            SetCooldown(cooldownKey);
            for (auto& c : candidates)
            {
                std::string nameCd = fmt::format(
                    "{}:{}",
                    bot->GetName(), c.name);
                _goNameCooldowns[nameCd] = now;
            }
        }
    }

    void CheckRaidIdleMorale()
    {
        static std::unordered_map<uint32, time_t>
            groupCooldowns;

        time_t nowSec = time(nullptr);
        std::set<uint32> seenGroups;

        WorldSessionMgr::SessionMap const& sessions =
            sWorldSessionMgr->GetAllSessions();
        for (auto const& pair : sessions)
        {
            WorldSession* session = pair.second;
            if (!session || session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player || !player->IsInWorld()
                || IsPlayerBot(player))
                continue;

            Map* map = player->GetMap();
            if (!map || !map->IsRaid())
                continue;

            if (player->IsMounted()
                || player->IsFlying())
                continue;

            Group* group = player->GetGroup();
            if (!group || !group->isRaidGroup())
                continue;
            if (!GroupHasBots(group))
                continue;

            // Check if ANY group member is in combat
            // or dead/ghost — morale is between-pull
            // only, not during wipe recovery
            bool anyBusy = false;
            for (auto const& mRef :
                 group->GetMemberSlots())
            {
                Player* member =
                    ObjectAccessor::FindPlayer(
                        mRef.guid);
                if (member
                    && (member->IsInCombat()
                        || !member->IsAlive()
                        || member->HasFlag(
                            PLAYER_FLAGS,
                            PLAYER_FLAGS_GHOST)))
                {
                    anyBusy = true;
                    break;
                }
            }
            if (anyBusy)
                continue;

            uint32 groupId =
                group->GetGUID().GetCounter();
            if (!seenGroups.insert(groupId).second)
                continue;

            auto cdIt =
                groupCooldowns.find(groupId);
            if (cdIt != groupCooldowns.end()
                && nowSec - cdIt->second
                    < (time_t)sLLMChatterConfig
                          ->_raidMoraleCooldown)
                continue;

            if (urand(1, 100)
                > sLLMChatterConfig
                      ->_raidMoraleChance)
                continue;

            // Match boss event format from
            // LLMChatterRaid.cpp
            std::string diffStr;
            switch (map->GetDifficulty())
            {
                case RAID_DIFFICULTY_10MAN_NORMAL:
                    diffStr = "10N";
                    break;
                case RAID_DIFFICULTY_25MAN_NORMAL:
                    diffStr = "25N";
                    break;
                case RAID_DIFFICULTY_10MAN_HEROIC:
                    diffStr = "10H";
                    break;
                case RAID_DIFFICULTY_25MAN_HEROIC:
                    diffStr = "25H";
                    break;
                default:
                    diffStr = "10N";
                    break;
            }

            // in_raid added by AppendRaidContext
            std::string json = fmt::format(
                R"({{"group_id":{},)"
                R"("player_name":"{}",)"
                R"("raid_name":"{}",)"
                R"("zone_id":{},)"
                R"("difficulty":"{}"}})",
                groupId,
                JsonEscape(player->GetName()),
                JsonEscape(map->GetMapName()),
                player->GetZoneId(),
                diffStr);

            AppendRaidContext(player, json);

            std::string cooldownKey =
                "raid_morale_"
                + std::to_string(groupId);

            QueueChatterEvent(
                "raid_idle_morale",
                "player",
                player->GetZoneId(),
                player->GetMapId(),
                GetChatterEventPriority(
                    "raid_idle_morale"),
                cooldownKey,
                player->GetGUID().GetCounter(),
                player->GetName(),
                0, "", 0,
                EscapeString(json),
                GetReactionDelaySeconds(
                    "raid_idle_morale"),
                sLLMChatterConfig
                    ->_eventExpirationSeconds,
                false);

            groupCooldowns[groupId] = nowSec;
        }
    }

    std::string GetClassName(uint8 classId)
    {
        switch (classId)
        {
            case CLASS_WARRIOR: return "Warrior";
            case CLASS_PALADIN: return "Paladin";
            case CLASS_HUNTER: return "Hunter";
            case CLASS_ROGUE: return "Rogue";
            case CLASS_PRIEST: return "Priest";
            case CLASS_DEATH_KNIGHT:
                return "Death Knight";
            case CLASS_SHAMAN: return "Shaman";
            case CLASS_MAGE: return "Mage";
            case CLASS_WARLOCK: return "Warlock";
            case CLASS_DRUID: return "Druid";
            default: return "Unknown";
        }
    }

    std::string GetRaceName(uint8 raceId)
    {
        switch (raceId)
        {
            case RACE_HUMAN: return "Human";
            case RACE_ORC: return "Orc";
            case RACE_DWARF: return "Dwarf";
            case RACE_NIGHTELF: return "Night Elf";
            case RACE_UNDEAD_PLAYER: return "Undead";
            case RACE_TAUREN: return "Tauren";
            case RACE_GNOME: return "Gnome";
            case RACE_TROLL: return "Troll";
            case RACE_BLOODELF: return "Blood Elf";
            case RACE_DRAENEI: return "Draenei";
            default: return "Unknown";
        }
    }

    uint32 GetFaction(Player* player)
    {
        return player->GetTeamId();
    }

    bool IsGroupedWithRealPlayer(Player* bot)
    {
        if (!bot)
            return false;

        Group* group = bot->GetGroup();
        if (!group)
            return false;

        for (GroupReference* itr =
                 group->GetFirstMember();
             itr != nullptr; itr = itr->next())
        {
            if (Player* member = itr->GetSource())
            {
                if (member != bot
                    && !IsPlayerBot(member))
                    return true;
            }
        }

        return false;
    }

    std::vector<Player*> GetBotsInZone(
        uint32 zoneId, uint32 faction)
    {
        std::vector<Player*> bots;
        PlayerBotMap allBots =
            sRandomPlayerbotMgr.GetAllBots();

        for (auto const& pair : allBots)
        {
            Player* player = pair.second;
            if (!player)
                continue;

            WorldSession* session = player->GetSession();
            if (session && session->PlayerLoading())
                continue;

            if (player->IsInWorld() && player->IsAlive())
            {
                if (player->GetZoneId() == zoneId
                    && GetFaction(player) == faction
                    && !IsGroupedWithRealPlayer(player))
                {
                    bots.push_back(player);
                }
            }
        }

        return bots;
    }

    std::vector<Player*> GetTransportBotsInZone(
        uint32 zoneId, TeamId teamId)
    {
        std::vector<Player*> bots;
        PlayerBotMap allBots =
            sRandomPlayerbotMgr.GetAllBots();

        for (auto const& pair : allBots)
        {
            Player* bot = pair.second;
            if (!bot)
                continue;

            WorldSession* session = bot->GetSession();
            if (session && session->PlayerLoading())
                continue;

            if (!bot->IsInWorld() || !bot->IsAlive())
                continue;

            if (bot->GetZoneId() != zoneId)
                continue;

            if (teamId != TEAM_NEUTRAL
                && bot->GetTeamId() != teamId)
                continue;

            // Transport chatter should include dockside
            // bots grouped with real players, so this
            // path intentionally does not reuse the
            // ambient-group exclusion above.
            if (!CanSpeakInGeneralChannel(bot))
                continue;

            bots.push_back(bot);
        }

        return bots;
    }

    uint32 GetDominantFactionInZone(uint32 zoneId)
    {
        uint32 allianceCount = 0;
        uint32 hordeCount = 0;

        WorldSessionMgr::SessionMap const& sessions =
            sWorldSessionMgr->GetAllSessions();

        for (auto const& pair : sessions)
        {
            WorldSession* session = pair.second;
            if (!session || session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player || !player->IsInWorld())
                continue;

            if (!IsPlayerBot(player)
                && player->GetZoneId() == zoneId)
            {
                if (GetFaction(player) == TEAM_ALLIANCE)
                    allianceCount++;
                else
                    hordeCount++;
            }
        }

        if (allianceCount > hordeCount)
            return TEAM_ALLIANCE;
        if (hordeCount > allianceCount)
            return TEAM_HORDE;
        return urand(0, 1);
    }

    void TryTriggerChatter()
    {
        std::vector<uint32> validZones =
            GetZonesWithRealPlayers();
        if (validZones.empty())
            return;

        QueryResult countResult =
            CharacterDatabase.Query(
                "SELECT COUNT(*) FROM llm_chatter_queue "
                "WHERE status IN ('pending', 'processing')");

        if (countResult)
        {
            uint32 pending =
                countResult->Fetch()[0].Get<uint32>();
            if (pending >= sLLMChatterConfig
                               ->_maxPendingRequests)
                return;
        }

        std::random_device rd;
        std::mt19937 g(rd());

        for (uint32 selectedZone : validZones)
        {
            uint32 triggerChance =
                sLLMChatterConfig->_triggerChance;
            if (IsCapitalCity(selectedZone))
            {
                triggerChance = std::min(
                    triggerChance
                        * sLLMChatterConfig
                              ->_cityChatterMultiplier,
                    100u);
            }

            if (urand(1, 100) > triggerChance)
                continue;

            std::string zoneName =
                GetZoneName(selectedZone);
            uint32 faction =
                GetDominantFactionInZone(selectedZone);
            std::vector<Player*> bots =
                GetBotsInZone(selectedZone, faction);

            bots.erase(
                std::remove_if(
                    bots.begin(), bots.end(),
                    [](Player* b) {
                        return !CanSpeakInGeneralChannel(b);
                    }),
                bots.end());

            bool isConversation =
                (urand(1, 100)
                 <= sLLMChatterConfig
                        ->_conversationChance);
            uint32 requiredBots =
                isConversation ? 2 : 1;
            if (bots.size() < requiredBots)
            {
                if (isConversation && bots.size() >= 1)
                    isConversation = false;
                else
                    continue;
            }

            std::shuffle(bots.begin(), bots.end(), g);

            uint32 botCount = 1;
            if (isConversation)
            {
                uint32 maxBots = std::min(
                    static_cast<uint32>(bots.size()),
                    4u);
                uint32 roll = urand(1, 100);
                if (roll <= 50 || maxBots == 2)
                    botCount = 2;
                else if (roll <= 80 || maxBots == 3)
                    botCount = std::min(3u, maxBots);
                else
                    botCount = maxBots;
            }

            Player* bot1 = bots[0];
            Player* bot2 =
                (botCount >= 2) ? bots[1] : nullptr;
            Player* bot3 =
                (botCount >= 3) ? bots[2] : nullptr;
            Player* bot4 =
                (botCount >= 4) ? bots[3] : nullptr;

            QueueChatterRequest(
                bot1, bot2, bot3, bot4,
                botCount, isConversation,
                zoneName, selectedZone);
        }
    }

    void QueueChatterRequest(
        Player* bot1, Player* bot2,
        Player* bot3, Player* bot4,
        uint32 botCount,
        bool isConversation,
        const std::string& zoneName,
        uint32 zoneId)
    {
        std::string requestType =
            isConversation
                ? "conversation"
                : "statement";
        std::string bot1Name = bot1->GetName();
        std::string bot1Class =
            GetClassName(bot1->getClass());
        std::string bot1Race =
            GetRaceName(bot1->getRace());
        uint8 bot1Level = bot1->GetLevel();

        std::string escapedZoneName =
            EscapeString(zoneName);
        std::string currentWeather = "clear";
        auto weatherIt = _zoneWeatherState.find(zoneId);
        if (weatherIt != _zoneWeatherState.end())
            currentWeather =
                GetWeatherStateName(weatherIt->second);

        if (isConversation && bot2)
        {
            std::string bot2Name = bot2->GetName();
            std::string bot2Class =
                GetClassName(bot2->getClass());
            std::string bot2Race =
                GetRaceName(bot2->getRace());
            uint8 bot2Level = bot2->GetLevel();

            std::string columns =
                "request_type, bot1_guid, bot1_name, "
                "bot1_class, bot1_race, bot1_level, "
                "bot1_zone, zone_id, weather, bot_count, "
                "bot2_guid, bot2_name, bot2_class, "
                "bot2_race, bot2_level";
            std::string values = fmt::format(
                "'{}', {}, '{}', '{}', '{}', {}, "
                "'{}', {}, '{}', {}, {}, '{}', "
                "'{}', '{}', {}",
                requestType,
                bot1->GetGUID().GetCounter(),
                EscapeString(bot1Name),
                bot1Class,
                bot1Race,
                bot1Level,
                escapedZoneName,
                zoneId,
                currentWeather,
                botCount,
                bot2->GetGUID().GetCounter(),
                EscapeString(bot2Name),
                bot2Class,
                bot2Race,
                bot2Level);

            if (bot3)
            {
                std::string bot3Name = bot3->GetName();
                std::string bot3Class =
                    GetClassName(bot3->getClass());
                std::string bot3Race =
                    GetRaceName(bot3->getRace());
                uint8 bot3Level = bot3->GetLevel();
                columns +=
                    ", bot3_guid, bot3_name, bot3_class, "
                    "bot3_race, bot3_level";
                values += fmt::format(
                    ", {}, '{}', '{}', '{}', {}",
                    bot3->GetGUID().GetCounter(),
                    EscapeString(bot3Name),
                    bot3Class,
                    bot3Race,
                    bot3Level);
            }

            if (bot4)
            {
                std::string bot4Name = bot4->GetName();
                std::string bot4Class =
                    GetClassName(bot4->getClass());
                std::string bot4Race =
                    GetRaceName(bot4->getRace());
                uint8 bot4Level = bot4->GetLevel();
                columns +=
                    ", bot4_guid, bot4_name, bot4_class, "
                    "bot4_race, bot4_level";
                values += fmt::format(
                    ", {}, '{}', '{}', '{}', {}",
                    bot4->GetGUID().GetCounter(),
                    EscapeString(bot4Name),
                    bot4Class,
                    bot4Race,
                    bot4Level);
            }

            columns += ", status";
            values += ", 'pending'";

            CharacterDatabase.Execute(
                "INSERT INTO llm_chatter_queue ({}) "
                "VALUES ({})",
                columns, values);
        }
        else
        {
            CharacterDatabase.Execute(
                "INSERT INTO llm_chatter_queue "
                "(request_type, bot1_guid, bot1_name, "
                "bot1_class, bot1_race, bot1_level, "
                "bot1_zone, zone_id, weather, "
                "bot_count, status) VALUES "
                "('{}', {}, '{}', '{}', '{}', {}, "
                "'{}', {}, '{}', 1, 'pending')",
                requestType,
                bot1->GetGUID().GetCounter(),
                EscapeString(bot1Name),
                bot1Class,
                bot1Race,
                bot1Level,
                escapedZoneName,
                zoneId,
                currentWeather);
        }
    }

    void DeliverPendingMessages()
    {
        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1, delivered_at = NOW() "
            "WHERE delivered = 0 "
            "AND deliver_at < DATE_SUB(NOW(), "
            "INTERVAL 60 SECOND)");

        QueryResult result;
        if (sLLMChatterConfig->_prioritySystemEnable
            && sLLMChatterConfig
                   ->_priorityDeliveryOrderEnable)
        {
            // Ambient rows flow through llm_chatter_queue
            // and therefore keep event_id = NULL.
            // Treat them as lowest priority via COALESCE.
            result = CharacterDatabase.Query(
                "SELECT m.id, m.bot_guid, "
                "m.bot_name, m.message, "
                "m.channel, m.emote, "
                "m.event_id, e.zone_id "
                "FROM llm_chatter_messages m "
                "LEFT JOIN llm_chatter_events e "
                "ON m.event_id = e.id "
                "WHERE m.delivered = 0 "
                "AND m.deliver_at <= NOW() "
                "ORDER BY COALESCE(e.priority, 0) "
                "DESC, m.deliver_at ASC LIMIT 1");
        }
        else
        {
            result = CharacterDatabase.Query(
                "SELECT m.id, m.bot_guid, m.bot_name, "
                "m.message, m.channel, m.emote, "
                "m.event_id, e.zone_id "
                "FROM llm_chatter_messages m "
                "LEFT JOIN llm_chatter_events e "
                "ON m.event_id = e.id "
                "WHERE m.delivered = 0 "
                "AND m.deliver_at <= NOW() "
                "ORDER BY m.deliver_at ASC LIMIT 1");
        }

        if (!result)
            return;

        Field* fields = result->Fetch();
        uint32 messageId = fields[0].Get<uint32>();
        uint32 botGuid = fields[1].Get<uint32>();
        std::string botName =
            fields[2].Get<std::string>();
        std::string message =
            fields[3].Get<std::string>();
        std::string channel =
            fields[4].Get<std::string>();
        std::string emoteName =
            fields[5].IsNull()
                ? ""
                : fields[5].Get<std::string>();
        uint32 eventId =
            fields[6].IsNull()
                ? 0
                : fields[6].Get<uint32>();
        uint32 eventZoneId =
            fields[7].IsNull()
                ? 0
                : fields[7].Get<uint32>();

        ObjectGuid guid =
            ObjectGuid::Create<HighGuid::Player>(
                botGuid);
        Player* bot =
            ObjectAccessor::FindPlayer(guid);

        if (bot)
        {
            WorldSession* session =
                bot->GetSession();
            if (session && session->PlayerLoading())
                bot = nullptr;
        }

        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1, delivered_at = NOW() "
            "WHERE id = {}",
            messageId);

        if (bot && bot->IsInWorld())
        {
            if (PlayerbotAI* ai =
                    GET_PLAYERBOT_AI(bot))
            {
                // --- Bot facing (Phase 1 + 2) ---
                if (sLLMChatterConfig->_facingEnable
                    && !bot->IsInCombat())
                {
                    bool faced = false;

                    // Phase 1: nearby object facing
                    if (eventId > 0)
                    {
                        QueryResult evRes =
                            CharacterDatabase.Query(
                                "SELECT target_entry"
                                ", target_guid "
                                "FROM "
                                "llm_chatter_events "
                                "WHERE id = {}",
                                eventId);
                        if (evRes)
                        {
                            Field* ef =
                                evRes->Fetch();
                            uint32 tEntry =
                                ef[0].Get<uint32>();
                            uint32 tGuid =
                                ef[1].Get<uint32>();
                            if (tEntry > 0)
                            {
                                float range =
                                    static_cast<
                                        float>(
                                    sLLMChatterConfig
                                    ->_nearbyObjectScanRadius);
                                // tGuid encodes creature
                                // vs GO: non-zero =
                                // creature entry (not an
                                // instance GUID).
                                WorldObject* target =
                                    (tGuid > 0)
                                    ? static_cast<
                                        WorldObject*>(
                                        bot->FindNearestCreature(
                                            tEntry,
                                            range))
                                    : static_cast<
                                        WorldObject*>(
                                        bot->FindNearestGameObject(
                                            tEntry,
                                            range));
                                if (target)
                                {
                                    bot->SetFacingToObject(
                                        target);
                                    faced = true;
                                }
                            }
                        }
                    }

                    // Phase 2: face mentioned member
                    if (!faced
                        && (channel == "party"
                            || channel == "raid"))
                    {
                        Group* grp =
                            bot->GetGroup();
                        if (grp)
                        {
                            Player* mentioned =
                                FindMentionedMember(
                                    bot, grp,
                                    message);
                            if (mentioned
                                && mentioned->IsInWorld())
                                bot->SetFacingToObject(
                                    mentioned);
                        }
                    }
                }

                std::string processedMessage =
                    ConvertAllLinks(message);
                bool sent = false;

                if (channel == "party")
                {
                    Group* grp = bot->GetGroup();
                    if (grp && grp->isRaidGroup())
                    {
                        SendPartyMessageInstant(
                            bot, grp,
                            processedMessage, "");
                        sent = true;
                    }
                    else
                    {
                        sent = ai->SayToParty(
                            processedMessage);
                    }
                }
                else if (channel == "raid")
                {
                    Group* grp = bot->GetGroup();
                    if (grp)
                    {
                        WorldPacket data;
                        ChatHandler::BuildChatPacket(
                            data,
                            CHAT_MSG_RAID,
                            bot->GetTeamId()
                                    == TEAM_ALLIANCE
                                ? LANG_COMMON
                                : LANG_ORCISH,
                            bot, nullptr,
                            processedMessage);
                        grp->BroadcastPacket(
                            &data, false);
                        sent = true;
                    }
                }
                else if (channel == "battleground")
                {
                    Group* grp = bot->GetGroup();
                    if (grp)
                    {
                        WorldPacket data;
                        ChatHandler::BuildChatPacket(
                            data,
                            CHAT_MSG_BATTLEGROUND,
                            bot->GetTeamId()
                                    == TEAM_ALLIANCE
                                ? LANG_COMMON
                                : LANG_ORCISH,
                            bot, nullptr,
                            processedMessage);
                        grp->BroadcastPacket(
                            &data, false);
                        sent = true;
                    }
                }
                else if (channel == "yell")
                {
                    if (!bot->IsAlive())
                    {
                    }
                    else if (eventZoneId
                        && bot->GetZoneId()
                            != eventZoneId)
                    {
                    }
                    else
                    {
                        sent = ai->Yell(
                            processedMessage);
                    }
                }
                else
                {
                    sent = ai->SayToChannel(
                        processedMessage,
                        ChatChannelId::GENERAL);
                }

                if (sent
                    && !emoteName.empty()
                    // General channel emotes are intentionally
                    // suppressed because text emotes are a
                    // proximity effect, not zone-wide chat.
                    && channel != "general"
                    && channel != "yell")
                {
                    if (!((channel == "battleground"
                            || (channel == "party"
                                && bot->GetBattleground()))
                            && !IsBGAllowedEmote(
                                emoteName)))
                    {
                        uint32 textEmoteId =
                            GetTextEmoteId(emoteName);
                        if (textEmoteId)
                        {
                            SendBotTextEmote(
                                bot, textEmoteId);
                        }
                    }
                }
            }
        }
    }
};

void AddLLMChatterWorldScripts()
{
    new LLMChatterWorldScript();
    new LLMChatterGameEventScript();
    new LLMChatterALEScript();
}

