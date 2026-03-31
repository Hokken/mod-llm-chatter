/*
 * mod-llm-chatter - ambient world/event ownership
 */

#include "LLMChatterAmbient.h"

#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "GameEventMgr.h"
#include "Group.h"
#include "Player.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "Weather.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <map>
#include <random>
#include <set>
#include <string>
#include <vector>

static std::map<std::string, time_t> _ambientCooldownCache;
static std::map<uint32, WeatherState> _zoneWeatherState;

static bool IsOnAmbientCooldown(
    const std::string& cooldownKey,
    uint32 cooldownSeconds)
{
    return IsEventOnCooldown(
        _ambientCooldownCache,
        cooldownKey,
        cooldownSeconds);
}

static void SetAmbientCooldown(
    const std::string& cooldownKey)
{
    SetEventCooldown(
        _ambientCooldownCache,
        cooldownKey);
}

static void QueueAmbientEvent(
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
        && IsOnAmbientCooldown(
            cooldownKey, cooldownSeconds))
        return;

    if (!bypassEventCooldown && !cooldownKey.empty())
        SetAmbientCooldown(cooldownKey);

    bool alwaysFire =
        (eventType == "holiday_start"
            || eventType == "holiday_end"
            || eventType == "day_night_transition"
            || eventType == "weather_change");

    uint32 reactionChance =
        sLLMChatterConfig->_eventReactionChance;
    if (eventType == "weather_ambient"
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

std::vector<uint32> GetZonesWithRealPlayers()
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

        QueueAmbientEvent(
            eventType, "global",
            zoneId, 0, cooldownKey,
            sLLMChatterConfig
                ->_holidayCooldownSeconds,
            0, "", 0, "",
            eventId, extraData);
    }
}

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

void HandleWeatherChange(
    Weather* weather, WeatherState state,
    float grade)
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
        + "\",\"previous_weather\":\""
        + prevWeatherName + "\",\"transition\":\""
        + transitionType + "\",\"category\":\""
        + category + "\",\"intensity\":\""
        + intensity + "\",\"grade\":"
        + std::to_string(grade) + "}";

    QueueAmbientEvent(
        "weather_change", "zone",
        zoneId, 0, cooldownKey,
        sLLMChatterConfig->_weatherCooldownSeconds,
        0, "", 0, "",
        static_cast<uint32>(state),
        extraData);
}

void HandleAmbientGameEventStart(uint16 eventId)
{
    if (!sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem)
        return;

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

void HandleAmbientGameEventStop(uint16 eventId)
{
    if (!sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem)
        return;

    if (sLLMChatterConfig->_eventsHolidays
        && IsHolidayEvent(eventId))
    {
        QueueHolidayForZones(
            eventId, "holiday_end");
    }
}

void CheckDayNightTransition(
    std::string& lastTimePeriod)
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

    std::string previousPeriod = lastTimePeriod;
    lastTimePeriod = timePeriod;
    if (previousPeriod.empty())
        return;

    bool isDay = (hour >= 6 && hour < 18);
    std::string cooldownKey =
        "time_period:" + timePeriod;
    std::string extraData = "{"
        "\"is_day\":"
        + std::string(isDay ? "true" : "false")
        + ",\"hour\":" + std::to_string(hour)
        + ",\"minute\":" + std::to_string(minute)
        + ",\"time_period\":\"" + timePeriod
        + "\",\"previous_period\":\""
        + previousPeriod + "\",\"description\":\""
        + JsonEscape(description) + "\"}";

    std::vector<uint32> playerZones =
        GetZonesWithRealPlayers();
    for (uint32 zoneId : playerZones)
    {
        std::string zoneKey =
            cooldownKey + ":"
            + std::to_string(zoneId);
        QueueAmbientEvent(
            "day_night_transition", "global",
            zoneId, 0, zoneKey,
            sLLMChatterConfig
                ->_dayNightCooldownSeconds,
            0, "", 0, "", 0, extraData);
    }
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
            + weatherName + "\",\"category\":\""
            + category + "\",\"intensity\":\"sustained\","
            "\"is_ambient\":true}";

        QueueAmbientEvent(
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
        else if (sLLMChatterConfig->_eventsMinor
            && IsMinorGameEvent(eventId))
        {
            QueueHolidayForZones(
                eventId, "minor_event");
        }
    }
}

static uint32 GetFaction(Player* player)
{
    return player->GetTeamId();
}

static bool IsGroupedWithRealPlayer(Player* bot)
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

static std::vector<Player*> GetBotsInZone(
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

static uint32 GetDominantFactionInZone(uint32 zoneId)
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

static void QueueChatterRequest(
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
