/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Main WorldScript for triggering chatter and delivering messages
 *
 * Active features:
 * - Day/Night transition events (WorldScript)
 * - Holiday start/stop events (GameEventScript)
 * - Weather change events (ALEScript) - tracks starting, clearing, intensifying
 * - Ambient bot conversations in zones with real players
 *
 * Future/Planned features:
 * - Transport arrival events
 *   Note: TransportScript is database-bound to specific transports via ScriptName.
 *   Would need to either:
 *   a) Add ScriptNames to transports table and register matching TransportScripts
 *   b) Add a custom periodic check that iterates Map::GetAllTransports()
 *   Both approaches require significant work and database/core understanding.
 */

#include "LLMChatterConfig.h"
#include "ScriptMgr.h"
#include "Player.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Log.h"
#include "Channel.h"
#include "ChannelMgr.h"
#include "ObjectAccessor.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "GameEventMgr.h"
#include "GameTime.h"
#include "Group.h"
#include "Weather.h"
#include "MapMgr.h"
#include "Transport.h"
#include "Spell.h"
#include <vector>
#include <map>
#include <set>
#include <random>
#include <sstream>
#include <unordered_map>

// Check if player is a bot (global helper function)
static bool IsPlayerBot(Player* player)
{
    if (!player)
        return false;

    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
    return ai != nullptr;
}

// Helper function to get item quality color
static const char* GetQualityColor(uint8 quality)
{
    switch (quality)
    {
        case 0: return "9d9d9d";  // Poor (gray)
        case 1: return "ffffff";  // Common (white)
        case 2: return "1eff00";  // Uncommon (green)
        case 3: return "0070dd";  // Rare (blue)
        case 4: return "a335ee";  // Epic (purple)
        case 5: return "ff8000";  // Legendary (orange)
        default: return "ffffff";
    }
}

// Convert [[item:ID:Name:Quality]] markers to WoW item links
static std::string ConvertItemLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[item:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 7, endPos - pos - 7);
        size_t firstColon = content.find(':');
        size_t lastColon = content.rfind(':');

        if (firstColon != std::string::npos && lastColon != std::string::npos && firstColon != lastColon)
        {
            std::string idStr = content.substr(0, firstColon);
            std::string name = content.substr(firstColon + 1, lastColon - firstColon - 1);
            std::string qualityStr = content.substr(lastColon + 1);

            try
            {
                uint32 itemId = std::stoul(idStr);
                uint8 quality = static_cast<uint8>(std::stoul(qualityStr));
                std::ostringstream link;
                link << "|cff" << GetQualityColor(quality)
                     << "|Hitem:" << itemId << ":0:0:0:0:0:0:0:0|h[" << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...) { pos = endPos + 2; }
        }
        else { pos = endPos + 2; }
    }
    return result;
}

// Convert [[quest:ID:Name:Level]] markers to WoW quest links
static std::string ConvertQuestLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[quest:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 8, endPos - pos - 8);
        size_t firstColon = content.find(':');
        size_t lastColon = content.rfind(':');

        if (firstColon != std::string::npos && lastColon != std::string::npos && firstColon != lastColon)
        {
            std::string idStr = content.substr(0, firstColon);
            std::string name = content.substr(firstColon + 1, lastColon - firstColon - 1);
            std::string levelStr = content.substr(lastColon + 1);

            try
            {
                uint32 questId = std::stoul(idStr);
                uint32 level = std::stoul(levelStr);
                std::ostringstream link;
                link << "|cffffff00|Hquest:" << questId << ":" << level << "|h[" << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...) { pos = endPos + 2; }
        }
        else { pos = endPos + 2; }
    }
    return result;
}

// Convert [[npc:ID:Name]] markers to green colored NPC names
static std::string ConvertNpcLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[npc:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 6, endPos - pos - 6);
        size_t colonPos = content.find(':');

        if (colonPos != std::string::npos)
        {
            std::string name = content.substr(colonPos + 1);
            std::string coloredName = "|cff00ff00" + name + "|r";
            result.replace(pos, endPos - pos + 2, coloredName);
            pos += coloredName.length();
        }
        else { pos = endPos + 2; }
    }
    return result;
}

// Convert [[spell:ID:Name]] markers to WoW spell links
static std::string ConvertSpellLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[spell:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos) break;

        std::string content = result.substr(pos + 8, endPos - pos - 8);
        size_t colonPos = content.find(':');

        if (colonPos != std::string::npos)
        {
            std::string idStr = content.substr(0, colonPos);
            std::string name = content.substr(colonPos + 1);

            try
            {
                uint32 spellId = std::stoul(idStr);
                std::ostringstream link;
                link << "|cff71d5ff|Hspell:" << spellId << "|h[" << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...) { pos = endPos + 2; }
        }
        else { pos = endPos + 2; }
    }
    return result;
}

// Convert all link markers to WoW hyperlinks
static std::string ConvertAllLinks(const std::string& text)
{
    std::string result = text;
    result = ConvertItemLinks(result);
    result = ConvertQuestLinks(result);
    result = ConvertSpellLinks(result);
    result = ConvertNpcLinks(result);
    return result;
}

// ============================================================================
// EVENT SYSTEM UTILITIES
// ============================================================================

// Cooldown cache to prevent spamming database checks
static std::map<std::string, time_t> _cooldownCache;

// Check if a cooldown key is still active
static bool IsOnCooldown(const std::string& cooldownKey, uint32 cooldownSeconds)
{
    auto it = _cooldownCache.find(cooldownKey);
    if (it != _cooldownCache.end())
    {
        time_t now = time(nullptr);
        if (now - it->second < cooldownSeconds)
            return true;
    }

    // Also check database for persistent cooldowns
    QueryResult result = CharacterDatabase.Query(
        "SELECT 1 FROM llm_chatter_events "
        "WHERE cooldown_key = '{}' AND created_at > DATE_SUB(NOW(), INTERVAL {} SECOND) "
        "LIMIT 1",
        cooldownKey, cooldownSeconds);

    if (result)
        return true;

    return false;
}

// Set cooldown in cache
static void SetCooldown(const std::string& cooldownKey)
{
    _cooldownCache[cooldownKey] = time(nullptr);
}

// Escape string for SQL
static std::string EscapeString(const std::string& str)
{
    std::string result = str;
    size_t pos = 0;
    // Escape backslashes first
    while ((pos = result.find('\\', pos)) != std::string::npos)
    {
        result.replace(pos, 1, "\\\\");
        pos += 2;
    }
    pos = 0;
    while ((pos = result.find('\'', pos)) != std::string::npos)
    {
        result.replace(pos, 1, "''");
        pos += 2;
    }
    return result;
}

// Escape string for JSON values that will be inserted via SQL string literal
// MySQL interprets backslashes in string literals, so we need double-escaping:
// - For a JSON quote (\"), we need \\" in SQL to store \" in the database
// - For a literal backslash (\\), we need \\\\ in SQL to store \\ in the database
//
// NOTE: JsonEscape handles BOTH JSON escaping AND SQL
// single-quote escaping. The escaped output is used
// directly in SQL string literals via fmt::format.
// If modifying this function, ensure single-quote
// escaping (case '\'') is preserved to prevent SQL
// injection in CharacterDatabase.Execute() calls.
static std::string JsonEscape(const std::string& str)
{
    std::string result;
    result.reserve(str.size() * 2);
    for (char c : str)
    {
        switch (c)
        {
            case '"':  result += "\\\\\""; break;  // \" in JSON, needs \\" in SQL
            case '\\': result += "\\\\\\\\"; break;  // \\ in JSON, needs \\\\ in SQL
            case '\n': result += "\\\\n"; break;
            case '\r': result += "\\\\r"; break;
            case '\t': result += "\\\\t"; break;
            case '\'': result += "''"; break;  // SQL single quote escape
            default:   result += c; break;
        }
    }
    return result;
}

// Calculate reaction delay based on event type
static uint32 GetReactionDelaySeconds(const std::string& eventType)
{
    // Returns delay in seconds (min, max)
    uint32 minDelay, maxDelay;

    if (eventType == "day_night_transition")
        { minDelay = 120; maxDelay = 600; }
    else if (eventType == "holiday_start" || eventType == "holiday_end")
        { minDelay = 300; maxDelay = 900; }
    else if (eventType == "weather_change")
        { minDelay = 60; maxDelay = 300; }
    else if (eventType == "transport_arrives")
        { minDelay = 5; maxDelay = 15; }  // React quickly while transport is still at dock
    else
        { minDelay = 30; maxDelay = 120; }

    return urand(minDelay, maxDelay);
}

// Queue an event to the database
static void QueueEvent(const std::string& eventType, const std::string& eventScope,
                       uint32 zoneId, uint32 mapId, uint8 priority,
                       const std::string& cooldownKey, uint32 cooldownSeconds,
                       uint32 subjectGuid, const std::string& subjectName,
                       uint32 targetGuid, const std::string& targetName, uint32 targetEntry,
                       const std::string& extraData)
{
    if (!sLLMChatterConfig->IsEnabled() || !sLLMChatterConfig->_useEventSystem)
        return;

    // Roll reaction chance
    // Holidays and day/night are rare one-time events;
    // always let them through
    bool alwaysFire =
        (eventType == "holiday_start"
         || eventType == "holiday_end"
         || eventType == "day_night_transition");

    uint32 reactionChance =
        sLLMChatterConfig->_eventReactionChance;
    if (eventType == "transport_arrives"
        && sLLMChatterConfig->_transportEventChance > 0)
        reactionChance =
            sLLMChatterConfig->_transportEventChance;

    if (!alwaysFire
        && urand(1, 100) > reactionChance)
    {
        if (eventType == "transport_arrives")
        {
            // LOG_INFO("module", "LLMChatter: Transport event skipped (reaction chance {})", reactionChance);
        }
        else
        {
            LOG_DEBUG("module", "LLMChatter: Event {} skipped (reaction chance)", eventType);
        }
        return;
    }

    // Check cooldown
    if (!cooldownKey.empty() && IsOnCooldown(cooldownKey, cooldownSeconds))
    {
        if (eventType == "transport_arrives")
        {
            // LOG_INFO("module", "LLMChatter: Transport event on cooldown ({})", cooldownKey);
        }
        else
        {
            LOG_DEBUG("module", "LLMChatter: Event {} on cooldown ({})", eventType, cooldownKey);
        }
        return;
    }

    // Calculate delays
    // Expiration must be AFTER reaction delay,
    // otherwise events expire before they fire
    uint32 reactionDelay = GetReactionDelaySeconds(eventType);
    uint32 expirationSeconds =
        reactionDelay
        + sLLMChatterConfig->_eventExpirationSeconds;

    // Set cooldown
    if (!cooldownKey.empty())
        SetCooldown(cooldownKey);

    // Insert event
    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_events "
        "(event_type, event_scope, zone_id, map_id, priority, cooldown_key, "
        "subject_guid, subject_name, target_guid, target_name, target_entry, "
        "extra_data, status, react_after, expires_at) "
        "VALUES ('{}', '{}', {}, {}, {}, '{}', {}, '{}', {}, '{}', {}, '{}', 'pending', "
        "DATE_ADD(NOW(), INTERVAL {} SECOND), DATE_ADD(NOW(), INTERVAL {} SECOND))",
        eventType, eventScope,
        zoneId > 0 ? std::to_string(zoneId) : "NULL",
        mapId > 0 ? std::to_string(mapId) : "NULL",
        priority, EscapeString(cooldownKey),
        subjectGuid > 0 ? std::to_string(subjectGuid) : "NULL",
        EscapeString(subjectName),
        targetGuid > 0 ? std::to_string(targetGuid) : "NULL",
        EscapeString(targetName),
        targetEntry > 0 ? std::to_string(targetEntry) : "NULL",
        extraData,  // Already JSON-escaped, don't double-escape
        reactionDelay, expirationSeconds);

    LOG_INFO("module", "LLMChatter: Queued event {} in zone {} (react in {}s)",
             eventType, zoneId, reactionDelay);
}

// Helper: check if a game event is a holiday/calendar
// event by looking at the HolidayId field in
// GameEventData. Covers all holidays, Darkmoon Faire,
// Call to Arms weekends, fishing derbies, etc.
static bool IsHolidayEvent(uint16 eventId)
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    if (eventId >= events.size())
        return false;
    return events[eventId].HolidayId != HOLIDAY_NONE;
}

// Helper: check if a zone is a capital city
static bool IsCapitalCity(uint32 zoneId)
{
    if (AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(zoneId))
        return (area->flags
                & AREA_FLAG_CAPITAL) != 0;
    return false;
}

// Helper: check if player is in the overworld
// (not dungeon/raid/BG/arena)
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

// Helper: get zones where real (non-bot) players are
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

// Queue a holiday event for zones where real
// players are present. Cities get a higher
// chance, open-world zones get a lower chance.
static void QueueHolidayForZones(
    uint16 eventId,
    const std::string& eventType = "holiday_start")
{
    GameEventMgr::GameEventDataMap const& events =
        sGameEventMgr->GetEventMap();
    GameEventData const& eventData =
        events[eventId];

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
            eventType + ":"
            + std::to_string(eventId)
            + ":zone:"
            + std::to_string(zoneId);
        std::string extraData =
            "{\"event_name\":\""
            + JsonEscape(eventData.Description)
            + "\",\"zone_id\":"
            + std::to_string(zoneId) + "}";

        QueueEvent(
            eventType, "global",
            zoneId, 0, 2, cooldownKey,
            sLLMChatterConfig
                ->_holidayCooldownSeconds,
            0, "", 0, "",
            eventId, extraData);
    }
}

// Get zone name from zone ID (free function for cross-class use)
static std::string GetZoneName(uint32 zoneId)
{
    if (AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId))
    {
        return area->area_name[0];  // English name
    }
    return "Unknown Zone";
}

// ============================================================================
// GAME EVENT SCRIPT - Holiday Events
// ============================================================================

class LLMChatterGameEventScript : public GameEventScript
{
public:
    LLMChatterGameEventScript() : GameEventScript("LLMChatterGameEventScript") {}

    void OnStart(uint16 eventId) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem)
            return;
        if (!sLLMChatterConfig->_eventsHolidays)
            return;
        if (!IsHolidayEvent(eventId))
            return;

        QueueHolidayForZones(eventId,
            "holiday_start");

        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();
        LOG_INFO("module",
            "LLMChatter: Holiday started - {}",
            events[eventId].Description);
    }

    void OnStop(uint16 eventId) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem)
            return;
        if (!sLLMChatterConfig->_eventsHolidays)
            return;
        if (!IsHolidayEvent(eventId))
            return;

        QueueHolidayForZones(eventId,
            "holiday_end");

        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();
        LOG_INFO("module",
            "LLMChatter: Holiday ended - {}",
            events[eventId].Description);
    }
};

// ============================================================================
// ALE SCRIPT - Weather Events
// ============================================================================

// Track previous weather state per zone for transition detection
static std::map<uint32, WeatherState> _zoneWeatherState;

// Convert WeatherState enum to readable string
static std::string GetWeatherStateName(WeatherState state)
{
    switch (state)
    {
        case WEATHER_STATE_FINE:             return "clear";
        case WEATHER_STATE_FOG:              return "foggy";
        case WEATHER_STATE_LIGHT_RAIN:       return "light rain";
        case WEATHER_STATE_MEDIUM_RAIN:      return "rain";
        case WEATHER_STATE_HEAVY_RAIN:       return "heavy rain";
        case WEATHER_STATE_LIGHT_SNOW:       return "light snow";
        case WEATHER_STATE_MEDIUM_SNOW:      return "snow";
        case WEATHER_STATE_HEAVY_SNOW:       return "heavy snow";
        case WEATHER_STATE_LIGHT_SANDSTORM:  return "light sandstorm";
        case WEATHER_STATE_MEDIUM_SANDSTORM: return "sandstorm";
        case WEATHER_STATE_HEAVY_SANDSTORM:  return "heavy sandstorm";
        case WEATHER_STATE_THUNDERS:         return "thunderstorm";
        case WEATHER_STATE_BLACKRAIN:        return "black rain";
        case WEATHER_STATE_BLACKSNOW:        return "black snow";
        default:                             return "unknown";
    }
}

// Get weather category (rain, snow, sand, other)
static std::string GetWeatherCategory(WeatherState state)
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

// Get weather intensity description (based on grade)
static std::string GetWeatherIntensity(float grade)
{
    if (grade < 0.25f)
        return "mild";
    else if (grade < 0.5f)
        return "moderate";
    else if (grade < 0.75f)
        return "strong";
    else
        return "intense";
}

class LLMChatterALEScript : public ALEScript
{
public:
    LLMChatterALEScript() : ALEScript("LLMChatterALEScript") {}

    void OnWeatherChange(Weather* weather, WeatherState state, float grade) override
    {
        LOG_DEBUG("module", "LLMChatter: ALEScript OnWeatherChange - zone {} state {} grade {}",
                  weather->GetZone(), static_cast<uint32>(state), grade);

        if (!sLLMChatterConfig->IsEnabled() || !sLLMChatterConfig->_useEventSystem)
            return;
        if (!sLLMChatterConfig->_eventsWeather)
            return;

        uint32 zoneId = weather->GetZone();

        // Get previous weather state for this zone (default to FINE if unknown)
        // IMPORTANT: Always track state changes even if we skip the event,
        // otherwise transition detection becomes incorrect when a player enters later
        WeatherState prevState = WEATHER_STATE_FINE;
        auto it = _zoneWeatherState.find(zoneId);
        if (it != _zoneWeatherState.end())
            prevState = it->second;

        // Update tracked state (before checking for real players)
        _zoneWeatherState[zoneId] = state;

        // Only create weather events for zones where a real player is present
        // Note: GetAllSessions() is safe to iterate here as ALEScript hooks
        // are called from the main world thread during weather updates
        bool hasRealPlayer = false;
        auto const& sessions = sWorldSessionMgr->GetAllSessions();
        for (auto const& pair : sessions)
        {
            WorldSession* session = pair.second;
            if (!session || session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player || !player->IsInWorld())
                continue;

            if (!IsPlayerBot(player) && player->GetZoneId() == zoneId)
            {
                hasRealPlayer = true;
                break;
            }
        }

        if (!hasRealPlayer)
        {
            LOG_DEBUG("module", "LLMChatter: No real player in zone {}, skipping weather event", zoneId);
            return;
        }

        // Determine what kind of transition this is
        std::string transitionType;
        if (prevState == WEATHER_STATE_FINE && state != WEATHER_STATE_FINE)
        {
            // Weather starting
            transitionType = "starting";
        }
        else if (prevState != WEATHER_STATE_FINE && state == WEATHER_STATE_FINE)
        {
            // Weather clearing
            transitionType = "clearing";
        }
        else if (prevState != WEATHER_STATE_FINE && state != WEATHER_STATE_FINE)
        {
            // Weather changing (e.g., rain getting heavier, or changing type)
            if (GetWeatherCategory(prevState) == GetWeatherCategory(state))
            {
                // Same category, intensity change
                transitionType = "intensifying";
            }
            else
            {
                // Different weather type
                transitionType = "changing";
            }
        }
        else
        {
            // FINE to FINE - no change
            return;
        }

        std::string weatherName = GetWeatherStateName(state);
        std::string prevWeatherName = GetWeatherStateName(prevState);
        std::string intensity = GetWeatherIntensity(grade);
        std::string category = GetWeatherCategory(state);

        // Use zone + transition specific cooldown
        std::string cooldownKey = "weather:" + std::to_string(zoneId) + ":" + transitionType;

        // Build extra data JSON with transition context
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{\"weather_type\":\"" + weatherName + "\","
                               "\"previous_weather\":\"" + prevWeatherName + "\","
                               "\"transition\":\"" + transitionType + "\","
                               "\"category\":\"" + category + "\","
                               "\"intensity\":\"" + intensity + "\","
                               "\"grade\":" + std::to_string(grade) + "}";

        QueueEvent("weather_change", "zone",
                   zoneId, 0, 5, cooldownKey,
                   sLLMChatterConfig
                       ->_weatherCooldownSeconds,
                   0, "", 0, "",
                   static_cast<uint32>(state),
                   extraData);

        // LOG_INFO("module", "LLMChatter: Weather {} in zone {} - {} -> {} ({})",
        //          transitionType, zoneId, prevWeatherName, weatherName, intensity);
    }
};

// ============================================================================
// TRANSPORT TRACKING
// ============================================================================

// Cached transport info (loaded from DB on startup)
struct TransportInfo
{
    uint32 entry;
    std::string fullName;
    std::string destination;
    std::string transportType;  // "Boat", "Zeppelin", "Turtle"
};

// Transport info cache: entry -> TransportInfo
static std::map<uint32, TransportInfo> _transportCache;

// Transport zone tracking: GUID -> (lastZoneId, lastMapId)
static std::map<ObjectGuid::LowType, std::pair<uint32, uint32>> _transportZones;

// Parse transport name to extract destination and type
// Example: "Auberdine, Darkshore and Stormwind Harbor (Boat, Alliance ("The Bravery"))"
// Returns: destination = "Stormwind Harbor", type = "Boat"
static void ParseTransportName(const std::string& fullName, std::string& destination, std::string& transportType)
{
    destination = "";
    transportType = "";

    // Find " and " to split origin/destination
    size_t andPos = fullName.find(" and ");
    if (andPos == std::string::npos)
    {
        destination = fullName;
        return;
    }

    // Get everything after " and "
    std::string afterAnd = fullName.substr(andPos + 5);

    // Find " (" to cut off the transport type portion
    size_t parenPos = afterAnd.find(" (");
    if (parenPos != std::string::npos)
    {
        destination = afterAnd.substr(0, parenPos);

        // Extract transport type from parentheses
        std::string typeSection = afterAnd.substr(parenPos + 2);
        size_t commaPos = typeSection.find(',');
        if (commaPos != std::string::npos)
        {
            transportType = typeSection.substr(0, commaPos);
        }
        else
        {
            size_t closeParenPos = typeSection.find(')');
            if (closeParenPos != std::string::npos)
            {
                transportType = typeSection.substr(0, closeParenPos);
            }
        }
    }
    else
    {
        destination = afterAnd;
    }
}

// Load transport info from database
static void LoadTransportCache()
{
    _transportCache.clear();

    QueryResult result = WorldDatabase.Query(
        "SELECT entry, name FROM transports");

    if (!result)
    {
        LOG_INFO("module", "LLMChatter: No transports found in database");
        return;
    }

    uint32 count = 0;
    do
    {
        Field* fields = result->Fetch();
        uint32 entry = fields[0].Get<uint32>();
        std::string name = fields[1].Get<std::string>();

        TransportInfo info;
        info.entry = entry;
        info.fullName = name;
        ParseTransportName(name, info.destination, info.transportType);

        _transportCache[entry] = info;
        count++;

        LOG_DEBUG("module", "LLMChatter: Loaded transport {} -> {} ({})",
                  entry, info.destination, info.transportType);
    }
    while (result->NextRow());

    LOG_INFO("module", "LLMChatter: Loaded {} transports into cache", count);
}

// ============================================================================
// WORLD SCRIPT - Main chatter logic, day/night transitions
// ============================================================================

class LLMChatterWorldScript : public WorldScript
{
public:
    LLMChatterWorldScript() : WorldScript("LLMChatterWorldScript") {}

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sLLMChatterConfig->LoadConfig();
    }

    void OnStartup() override
    {
        if (!sLLMChatterConfig->IsEnabled())
            return;

        // Clear any stale undelivered messages from previous session
        CharacterDatabase.Execute(
            "DELETE FROM llm_chatter_messages WHERE delivered = 0");
        CharacterDatabase.Execute(
            "UPDATE llm_chatter_queue SET status = 'cancelled' "
            "WHERE status IN ('pending', 'processing')");
        CharacterDatabase.Execute(
            "UPDATE llm_chatter_events SET status = 'expired' "
            "WHERE status IN ('pending', 'processing')");

        // Clear stale group data (groups don't persist across restarts)
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_bot_traits");
        CharacterDatabase.Execute(
            "DELETE FROM llm_group_chat_history");

        // Load transport info cache for transport events
        LoadTransportCache();

        // Check for holidays already active at
        // startup (OnStart hook only fires at the
        // moment an event begins, not if the server
        // restarts mid-event)
        if (sLLMChatterConfig->_useEventSystem
            && sLLMChatterConfig->_eventsHolidays)
        {
            GameEventMgr::GameEventDataMap const&
                events =
                    sGameEventMgr->GetEventMap();
            for (uint16 eventId = 1;
                 eventId < events.size();
                 ++eventId)
            {
                if (!sGameEventMgr
                        ->IsActiveEvent(eventId))
                    continue;

                if (!IsHolidayEvent(eventId))
                    continue;

                // Just log - CheckActiveHolidays()
                // handles per-city queuing once
                // players are in cities
                GameEventData const& eventData =
                    events[eventId];
                LOG_INFO("module",
                    "LLMChatter: Holiday active "
                    "at startup - {}",
                    eventData.Description);
            }
        }

        LOG_INFO("module", "LLMChatter: Cleared stale messages, events, group traits, and chat history on startup");
        _lastTriggerTime = 0;
        _lastDeliveryTime = 0;
        _lastEnvironmentCheckTime = 0;
        _lastTransportCheckTime = 0;
        _lastTimePeriod = "";
    }

    void OnUpdate(uint32 /*diff*/) override
    {
        if (!sLLMChatterConfig->IsEnabled())
            return;

        uint32 now = getMSTime();

        // Check for message delivery (simple polling - always check)
        if (now - _lastDeliveryTime >= sLLMChatterConfig->_deliveryPollMs)
        {
            _lastDeliveryTime = now;
            DeliverPendingMessages();
        }

        // Check for new chatter trigger
        if (now - _lastTriggerTime >= sLLMChatterConfig->_triggerIntervalSeconds * 1000)
        {
            _lastTriggerTime = now;
            TryTriggerChatter();
        }

        // Check for environmental events (configurable)
        if (sLLMChatterConfig->_useEventSystem &&
            now - _lastEnvironmentCheckTime >=
                sLLMChatterConfig
                    ->_environmentCheckSeconds * 1000)
        {
            _lastEnvironmentCheckTime = now;
            CheckDayNightTransition();
            if (sLLMChatterConfig->_eventsHolidays)
                CheckActiveHolidays();
        }

        // Check for transport zone changes
        if (sLLMChatterConfig->_useEventSystem &&
            sLLMChatterConfig->_eventsTransports &&
            now - _lastTransportCheckTime >=
                sLLMChatterConfig
                    ->_transportCheckSeconds * 1000)
        {
            _lastTransportCheckTime = now;
            CheckTransportZones();
        }
    }

private:
    uint32 _lastTriggerTime = 0;
    uint32 _lastDeliveryTime = 0;
    uint32 _lastEnvironmentCheckTime = 0;
    uint32 _lastTransportCheckTime = 0;
    std::string _lastTimePeriod = "";

    // Get detailed time period from hour
    // Returns both the period name and a descriptive phrase
    std::pair<std::string, std::string> GetTimePeriod(int hour)
    {
        // Time periods based on typical WoW day cycle
        if (hour >= 5 && hour < 7)
            return {"dawn", "The sun is rising on the horizon"};
        else if (hour >= 7 && hour < 9)
            return {"early_morning", "It's early morning"};
        else if (hour >= 9 && hour < 12)
            return {"morning", "The morning is well underway"};
        else if (hour >= 12 && hour < 14)
            return {"midday", "The sun is at its peak"};
        else if (hour >= 14 && hour < 17)
            return {"afternoon", "It's afternoon"};
        else if (hour >= 17 && hour < 19)
            return {"evening", "Evening approaches"};
        else if (hour >= 19 && hour < 21)
            return {"dusk", "The sun is setting"};
        else if (hour >= 21 && hour < 23)
            return {"night", "Night has fallen"};
        else if (hour == 23 || hour == 0)
            return {"midnight", "It's the middle of the night"};
        else // 1-4
            return {"late_night", "The night is deep and quiet"};
    }

    // Check for time-of-day transitions
    void CheckDayNightTransition()
    {
        if (!sLLMChatterConfig->_eventsDayNight)
            return;

        // Get in-game time
        time_t gameTime = GameTime::GetGameTime().count();
        struct tm* timeInfo = localtime(&gameTime);
        int hour = timeInfo->tm_hour;
        int minute = timeInfo->tm_min;

        // Get current time period
        auto [timePeriod, description] = GetTimePeriod(hour);

        // Only trigger if time period changed
        if (timePeriod == _lastTimePeriod)
            return;

        std::string previousPeriod = _lastTimePeriod;
        _lastTimePeriod = timePeriod;

        // Skip initial state (server just started)
        if (previousPeriod.empty())
            return;

        // Determine if it's day or night (for backward compatibility)
        bool isDay = (hour >= 6 && hour < 18);

        // Use period-specific cooldown
        std::string cooldownKey = "time_period:" + timePeriod;

        // Build rich time context for the LLM
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"is_day\":" + std::string(isDay ? "true" : "false") + ","
            "\"hour\":" + std::to_string(hour) + ","
            "\"minute\":" + std::to_string(minute) + ","
            "\"time_period\":\"" + timePeriod + "\","
            "\"previous_period\":\"" + previousPeriod + "\","
            "\"description\":\"" + JsonEscape(description) + "\""
            "}";

        QueueEvent("day_night_transition", "global",
                   0, 0, 7, cooldownKey,
                   sLLMChatterConfig
                       ->_dayNightCooldownSeconds,
                   0, "", 0, "", 0, extraData);

        // LOG_INFO("module", "LLMChatter: Time transition - {} -> {} ({}:{})",
        //          previousPeriod, timePeriod, hour, minute);
    }

    // Periodically re-queue holiday events when a
    // real player is in a capital city.
    void CheckActiveHolidays()
    {
        GameEventMgr::GameEventDataMap const& events =
            sGameEventMgr->GetEventMap();

        for (uint16 eventId = 1;
             eventId < events.size(); ++eventId)
        {
            if (!sGameEventMgr->IsActiveEvent(eventId))
                continue;
            if (!IsHolidayEvent(eventId))
                continue;

            QueueHolidayForZones(eventId);
        }
    }

    // Check for transport zone changes
    void CheckTransportZones()
    {
        // Iterate all maps to find transports
        sMapMgr->DoForAllMaps([](Map* map)
        {
            if (!map)
                return;

            // Get all transports on this map
            TransportsContainer const& transports = map->GetAllTransports();

            for (Transport* transport : transports)
            {
                if (!transport)
                    continue;

                ObjectGuid::LowType guid = transport->GetGUID().GetCounter();
                uint32 entry = transport->GetEntry();
                uint32 mapId = map->GetId();

                // Get current zone from transport position
                float x = transport->GetPositionX();
                float y = transport->GetPositionY();
                float z = transport->GetPositionZ();
                uint32 currentZone = map->GetZoneId(transport->GetPhaseMask(), x, y, z);

                // Check for zone change
                auto it = _transportZones.find(guid);
                if (it != _transportZones.end())
                {
                    uint32 lastZone = it->second.first;
                    uint32 lastMap = it->second.second;

                    // Detect zone change or map change
                    if (currentZone != lastZone || mapId != lastMap)
                    {
                        // If we are in "no zone" (open sea), just track it.
                        // We'll announce when we enter a real zone.
                        if (currentZone == 0)
                        {
                            _transportZones[guid] = {currentZone, mapId};
                            continue;
                        }

                        // Zone changed! Queue event if we have transport info
                        auto cacheIt = _transportCache.find(entry);
                        if (cacheIt != _transportCache.end())
                        {
                            const TransportInfo& info = cacheIt->second;

                            // Build cooldown key
                            std::string cooldownKey = "transport:" + std::to_string(entry) +
                                                     ":zone:" + std::to_string(currentZone);

                            // Build extra data JSON
                            // NOTE: extraData is inserted
                            // into SQL via fmt::format;
                            // relies on JsonEscape for
                            // single-quote safety
                            // (see JsonEscape comment)
                            std::string extraData = "{"
                                "\"transport_entry\":" + std::to_string(entry) + ","
                                "\"transport_name\":\"" + JsonEscape(info.fullName) + "\","
                                "\"destination\":\"" + JsonEscape(info.destination) + "\","
                                "\"transport_type\":\"" + JsonEscape(info.transportType) + "\""
                                "}";

                            QueueEvent(
                                "transport_arrives",
                                "zone",
                                currentZone,
                                mapId,
                                6,  // priority
                                cooldownKey,
                                sLLMChatterConfig->_transportCooldownSeconds,  // per transport+zone cooldown
                                0, "",  // no subject
                                0, info.fullName, entry,  // target info
                                extraData
                            );

                        }
                        else
                        {
                        }
                    }
                }

                // Update tracking
                _transportZones[guid] = {currentZone, mapId};
            }
        });
    }

    // Get class name from class ID
    std::string GetClassName(uint8 classId)
    {
        switch (classId)
        {
            case CLASS_WARRIOR:      return "Warrior";
            case CLASS_PALADIN:      return "Paladin";
            case CLASS_HUNTER:       return "Hunter";
            case CLASS_ROGUE:        return "Rogue";
            case CLASS_PRIEST:       return "Priest";
            case CLASS_DEATH_KNIGHT: return "Death Knight";
            case CLASS_SHAMAN:       return "Shaman";
            case CLASS_MAGE:         return "Mage";
            case CLASS_WARLOCK:      return "Warlock";
            case CLASS_DRUID:        return "Druid";
            default:                 return "Unknown";
        }
    }

    // Get race name from race ID
    std::string GetRaceName(uint8 raceId)
    {
        switch (raceId)
        {
            case RACE_HUMAN:         return "Human";
            case RACE_ORC:           return "Orc";
            case RACE_DWARF:         return "Dwarf";
            case RACE_NIGHTELF:      return "Night Elf";
            case RACE_UNDEAD_PLAYER: return "Undead";
            case RACE_TAUREN:        return "Tauren";
            case RACE_GNOME:         return "Gnome";
            case RACE_TROLL:         return "Troll";
            case RACE_BLOODELF:      return "Blood Elf";
            case RACE_DRAENEI:       return "Draenei";
            default:                 return "Unknown";
        }
    }

    // Get faction (0 = Alliance, 1 = Horde)
    uint32 GetFaction(Player* player)
    {
        return player->GetTeamId();  // TEAM_ALLIANCE = 0, TEAM_HORDE = 1
    }

    // Check if a bot is grouped with a real player
    bool IsGroupedWithRealPlayer(Player* bot)
    {
        if (!bot)
            return false;

        Group* group = bot->GetGroup();
        if (!group)
            return false;  // Not in a group, so not grouped with real player

        // Check all group members for real players
        for (GroupReference* itr = group->GetFirstMember(); itr != nullptr; itr = itr->next())
        {
            if (Player* member = itr->GetSource())
            {
                if (member != bot && !IsPlayerBot(member))
                {
                    return true;  // Found a real player in the group
                }
            }
        }

        return false;  // Only bots in the group
    }

    // Get bots in a specific zone, filtered by faction
    // Excludes bots that are grouped with real players
    std::vector<Player*> GetBotsInZone(uint32 zoneId, uint32 faction)
    {
        std::vector<Player*> bots;

        // Get all playerbots from RandomPlayerbotMgr
        PlayerBotMap allBots = sRandomPlayerbotMgr.GetAllBots();

        for (auto const& pair : allBots)
        {
            Player* player = pair.second;
            if (!player)
                continue;

            // Check if bot is fully loaded
            WorldSession* session = player->GetSession();
            if (session && session->PlayerLoading())
                continue;

            if (player->IsInWorld() && player->IsAlive())
            {
                if (player->GetZoneId() == zoneId)
                {
                    if (GetFaction(player) == faction)
                    {
                        // Only include bots NOT grouped with real players
                        if (!IsGroupedWithRealPlayer(player))
                        {
                            bots.push_back(player);
                        }
                    }
                }
            }
        }

        return bots;
    }

    // Get the dominant faction of real players in a zone
    uint32 GetDominantFactionInZone(uint32 zoneId)
    {
        uint32 allianceCount = 0;
        uint32 hordeCount = 0;

        WorldSessionMgr::SessionMap const& sessions = sWorldSessionMgr->GetAllSessions();

        for (auto const& pair : sessions)
        {
            WorldSession* session = pair.second;
            if (!session)
                continue;

            // Check if session is still loading a player
            if (session->PlayerLoading())
                continue;

            Player* player = session->GetPlayer();
            if (!player)
                continue;

            // Skip players not fully in world
            if (!player->IsInWorld())
                continue;

            if (!IsPlayerBot(player) && player->GetZoneId() == zoneId)
            {
                if (GetFaction(player) == TEAM_ALLIANCE)
                    allianceCount++;
                else
                    hordeCount++;
            }
        }

        // Return the faction with more players, or random if equal
        if (allianceCount > hordeCount)
            return TEAM_ALLIANCE;
        else if (hordeCount > allianceCount)
            return TEAM_HORDE;
        else
            return urand(0, 1);  // Random if equal
    }

    void TryTriggerChatter()
    {
        // Find zones with real players
        std::vector<uint32> validZones =
            GetZonesWithRealPlayers();
        if (validZones.empty())
            return;

        // Check pending requests (once, before
        // per-zone loop)
        QueryResult countResult =
            CharacterDatabase.Query(
                "SELECT COUNT(*) FROM "
                "llm_chatter_queue "
                "WHERE status IN "
                "('pending', 'processing')");

        if (countResult)
        {
            uint32 pending =
                countResult->Fetch()[0]
                    .Get<uint32>();
            if (pending >= sLLMChatterConfig
                               ->_maxPendingRequests)
            {
                LOG_DEBUG("module",
                    "LLMChatter: Max pending "
                    "requests reached ({})",
                    pending);
                return;
            }
        }

        // Per-zone triggering: each zone with a
        // real player gets an independent roll.
        // Cities get a boosted chance.
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
                GetDominantFactionInZone(
                    selectedZone);

            std::vector<Player*> bots =
                GetBotsInZone(selectedZone, faction);

            bool isConversation =
                (urand(1, 100)
                 <= sLLMChatterConfig
                        ->_conversationChance);

            uint32 requiredBots =
                isConversation ? 2 : 1;
            if (bots.size() < requiredBots)
            {
                if (isConversation
                    && bots.size() >= 1)
                    isConversation = false;
                else
                    continue;
            }

            std::shuffle(
                bots.begin(), bots.end(), g);

            uint32 botCount = 1;
            if (isConversation)
            {
                uint32 maxBots = std::min(
                    static_cast<uint32>(
                        bots.size()), 4u);
                uint32 roll = urand(1, 100);
                if (roll <= 50 || maxBots == 2)
                    botCount = 2;
                else if (roll <= 80
                         || maxBots == 3)
                    botCount =
                        std::min(3u, maxBots);
                else
                    botCount = maxBots;
            }

            Player* bot1 = bots[0];
            Player* bot2 =
                (botCount >= 2)
                    ? bots[1] : nullptr;
            Player* bot3 =
                (botCount >= 3)
                    ? bots[2] : nullptr;
            Player* bot4 =
                (botCount >= 4)
                    ? bots[3] : nullptr;

            QueueChatterRequest(
                bot1, bot2, bot3, bot4,
                botCount, isConversation,
                zoneName, selectedZone);
        }
    }

    void QueueChatterRequest(Player* bot1, Player* bot2, Player* bot3, Player* bot4,
                             uint32 botCount, bool isConversation, const std::string& zoneName, uint32 zoneId)
    {
        std::string requestType = isConversation ? "conversation" : "statement";
        std::string bot1Name = bot1->GetName();
        std::string bot1Class = GetClassName(bot1->getClass());
        std::string bot1Race = GetRaceName(bot1->getRace());
        uint8 bot1Level = bot1->GetLevel();

        // Escape zone name for SQL
        std::string escapedZoneName =
            EscapeString(zoneName);

        // Get current weather for this zone
        std::string currentWeather = "clear";
        auto weatherIt = _zoneWeatherState.find(zoneId);
        if (weatherIt != _zoneWeatherState.end())
        {
            currentWeather = GetWeatherStateName(weatherIt->second);
        }

        if (isConversation && bot2)
        {
            std::string bot2Name = bot2->GetName();
            std::string bot2Class = GetClassName(bot2->getClass());
            std::string bot2Race = GetRaceName(bot2->getRace());
            uint8 bot2Level = bot2->GetLevel();

            // Build the SQL dynamically based on how many bots we have
            std::string columns = "request_type, bot1_guid, bot1_name, bot1_class, bot1_race, bot1_level, bot1_zone, zone_id, weather, bot_count, "
                                  "bot2_guid, bot2_name, bot2_class, bot2_race, bot2_level";
            std::string values = fmt::format(
                "'{}', {}, '{}', '{}', '{}', {}, "
                "'{}', {}, '{}', {}, "
                "{}, '{}', '{}', '{}', {}",
                requestType,
                bot1->GetGUID().GetCounter(),
                EscapeString(bot1Name),
                bot1Class, bot1Race, bot1Level,
                escapedZoneName, zoneId,
                currentWeather, botCount,
                bot2->GetGUID().GetCounter(),
                EscapeString(bot2Name),
                bot2Class, bot2Race, bot2Level);

            // Add bot3 if present
            if (bot3)
            {
                std::string bot3Name = bot3->GetName();
                std::string bot3Class = GetClassName(bot3->getClass());
                std::string bot3Race = GetRaceName(bot3->getRace());
                uint8 bot3Level = bot3->GetLevel();
                columns += ", bot3_guid, bot3_name, bot3_class, bot3_race, bot3_level";
                values += fmt::format(
                    ", {}, '{}', '{}', '{}', {}",
                    bot3->GetGUID().GetCounter(),
                    EscapeString(bot3Name),
                    bot3Class, bot3Race,
                    bot3Level);
            }

            // Add bot4 if present
            if (bot4)
            {
                std::string bot4Name = bot4->GetName();
                std::string bot4Class = GetClassName(bot4->getClass());
                std::string bot4Race = GetRaceName(bot4->getRace());
                uint8 bot4Level = bot4->GetLevel();
                columns += ", bot4_guid, bot4_name, bot4_class, bot4_race, bot4_level";
                values += fmt::format(
                    ", {}, '{}', '{}', '{}', {}",
                    bot4->GetGUID().GetCounter(),
                    EscapeString(bot4Name),
                    bot4Class, bot4Race,
                    bot4Level);
            }

            columns += ", status";
            values += ", 'pending'";

            CharacterDatabase.Execute("INSERT INTO llm_chatter_queue ({}) VALUES ({})", columns, values);

            if (botCount == 2)
                LOG_INFO("module", "LLMChatter: Queued {}-bot conversation in {} between {} and {}",
                         botCount, zoneName, bot1Name, bot2Name);
            else if (botCount == 3)
                LOG_INFO("module", "LLMChatter: Queued {}-bot conversation in {} between {}, {}, and {}",
                         botCount, zoneName, bot1Name, bot2Name, bot3->GetName());
            else
                LOG_INFO("module", "LLMChatter: Queued {}-bot conversation in {} between {}, {}, {}, and {}",
                         botCount, zoneName, bot1Name, bot2Name, bot3->GetName(), bot4->GetName());
        }
        else
        {
            CharacterDatabase.Execute(
                "INSERT INTO llm_chatter_queue "
                "(request_type, bot1_guid, "
                "bot1_name, bot1_class, bot1_race, "
                "bot1_level, bot1_zone, zone_id, "
                "weather, bot_count, status) "
                "VALUES ('{}', {}, '{}', '{}', "
                "'{}', {}, '{}', {}, '{}', "
                "1, 'pending')",
                requestType,
                bot1->GetGUID().GetCounter(),
                EscapeString(bot1Name),
                bot1Class, bot1Race, bot1Level,
                escapedZoneName, zoneId,
                currentWeather);

            LOG_INFO("module", "LLMChatter: Queued statement in {} for {} ({} {}) [weather: {}]",
                     zoneName, bot1Name, bot1Race, bot1Class, currentWeather);
        }
    }

    void DeliverPendingMessages()
    {
        // Find messages ready for delivery
        QueryResult result = CharacterDatabase.Query(
            "SELECT id, bot_guid, bot_name, message, channel "
            "FROM llm_chatter_messages "
            "WHERE delivered = 0 AND deliver_at <= NOW() "
            "ORDER BY deliver_at ASC LIMIT 1");

        if (!result)
            return;

        do
        {
            Field* fields = result->Fetch();
            uint32 messageId = fields[0].Get<uint32>();
            uint32 botGuid = fields[1].Get<uint32>();
            std::string botName = fields[2].Get<std::string>();
            std::string message = fields[3].Get<std::string>();
            std::string channel = fields[4].Get<std::string>();

            // Find the bot player (supports both
            // random bots and account character bots)
            ObjectGuid guid =
                ObjectGuid::Create<HighGuid::Player>(
                    botGuid);
            Player* bot =
                ObjectAccessor::FindPlayer(guid);

            // Skip if bot is still loading
            if (bot)
            {
                WorldSession* session =
                    bot->GetSession();
                if (session
                    && session->PlayerLoading())
                    bot = nullptr;
            }

            if (bot && bot->IsInWorld())
            {
                // Send to channel using PlayerbotAI
                if (PlayerbotAI* ai =
                        GET_PLAYERBOT_AI(bot))
                {
                    std::string processedMessage =
                        ConvertAllLinks(message);

                    if (channel == "party")
                    {
                        ai->SayToParty(
                            processedMessage);
                    }
                    else
                    {
                        ai->SayToChannel(
                            processedMessage,
                            ChatChannelId::GENERAL);
                        // History stored by Python
                        // bridge (chatter_general.py)
                    }
                }

                // Mark delivered after successful
                // delivery attempt
                CharacterDatabase.DirectExecute(
                    "UPDATE llm_chatter_messages "
                    "SET delivered = 1, "
                    "delivered_at = NOW() "
                    "WHERE id = {}",
                    messageId);
            }
            else
            {
                // Bot offline/not found - still mark
                // delivered to prevent infinite retry
                LOG_DEBUG("module",
                    "LLMChatter: Bot {} not found "
                    "or offline, skipping message",
                    botName);
                CharacterDatabase.DirectExecute(
                    "UPDATE llm_chatter_messages "
                    "SET delivered = 1, "
                    "delivered_at = NOW() "
                    "WHERE id = {}",
                    messageId);
            }

        } while (result->NextRow());
    }
};

// ============================================================================
// GROUP SCRIPT - Group chatter when bots join real player groups
// ============================================================================

// Check if a group has at least one real (non-bot) player
static bool GroupHasRealPlayer(Group* group)
{
    if (!group)
        return false;

    for (GroupReference* itr = group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        if (Player* member = itr->GetSource())
        {
            if (!IsPlayerBot(member))
                return true;
        }
    }
    return false;
}

// Pick a random bot from the group, optionally
// excluding a specific player (e.g. the killer)
static Player* GetRandomBotInGroup(
    Group* group, Player* exclude = nullptr)
{
    if (!group)
        return nullptr;

    std::vector<Player*> bots;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (member && IsPlayerBot(member)
            && member != exclude)
            bots.push_back(member);
    }

    if (bots.empty())
        return nullptr;

    return bots[urand(0, bots.size() - 1)];
}

// Queue a greeting event for a bot joining a group
// Bypasses QueueEvent() since greetings are mandatory
// (no reaction chance, no cooldowns)
static void QueueBotGreetingEvent(
    Player* bot, Group* group)
{
    if (!bot || !group)
        return;

    uint32 groupId = group->GetGUID().GetCounter();
    uint32 botGuid = bot->GetGUID().GetCounter();
    std::string botName = bot->GetName();

    // Get bot info for extra_data
    uint8 botClass = bot->getClass();
    uint8 botRace = bot->getRace();
    uint8 botLevel = bot->GetLevel();

    // Build extra_data JSON
    // NOTE: extraData is inserted into SQL via
    // fmt::format; relies on JsonEscape for
    // single-quote safety (see JsonEscape comment)
    std::string extraData = "{"
        "\"bot_guid\":" + std::to_string(botGuid) + ","
        "\"bot_name\":\"" + JsonEscape(botName) + "\","
        "\"bot_class\":" + std::to_string(botClass) + ","
        "\"bot_race\":" + std::to_string(botRace) + ","
        "\"bot_level\":" + std::to_string(botLevel) + ","
        "\"group_id\":" + std::to_string(groupId) +
        "}";

    // SQL-escape the whole JSON blob so
    // apostrophes in names don't break the
    // INSERT (JsonEscape handles JSON + SQL
    // inside values, this covers the wrapper)
    extraData = EscapeString(extraData);

    // Direct INSERT - bypass QueueEvent to skip
    // reaction chance and cooldown checks
    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_events "
        "(event_type, event_scope, zone_id, map_id, "
        "priority, cooldown_key, "
        "subject_guid, subject_name, "
        "target_guid, target_name, target_entry, "
        "extra_data, status, react_after, expires_at) "
        "VALUES ('bot_group_join', 'player', "
        "{}, {}, 0, '', "
        "{}, '{}', 0, '', 0, "
        "'{}', 'pending', "
        "DATE_ADD(NOW(), INTERVAL 3 SECOND), "
        "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
        bot->GetZoneId(),
        bot->GetMapId(),
        botGuid, EscapeString(botName),
        extraData);

    LOG_INFO("module",
        "LLMChatter: Queued bot_group_join for {} "
        "(group {})",
        botName, groupId);
}

// Per-zone General channel cooldown: zone_id -> last reaction time
static std::map<uint32, time_t> _generalChatCooldowns;

// Per-group kill cooldown cache: group_id -> last kill event time
static std::map<uint32, time_t> _groupKillCooldowns;

// Per-group death cooldown cache: group_id -> last death event time
static std::map<uint32, time_t> _groupDeathCooldowns;

// Per-group loot cooldown cache: group_id -> last loot event time
static std::map<uint32, time_t> _groupLootCooldowns;

// Per-group player message response cooldown
static std::map<uint32, time_t> _groupPlayerMsgCooldowns;

// Per-group combat engage cooldown
static std::map<uint32, time_t> _groupCombatCooldowns;

// Per-group spell cast cooldown: group_id -> last spell event time
static std::unordered_map<uint32, time_t>
    _groupSpellCooldowns;

// Per-group quest objectives cooldown:
// group_id -> last quest objectives event time
static std::map<uint32, time_t>
    _groupQuestObjCooldowns;

// Per-group resurrect cooldown:
// group_id -> last resurrect event time
static std::map<uint32, time_t>
    _groupResurrectCooldowns;

// Per-group zone transition cooldown:
// group_id -> last zone change event time
static std::map<uint32, time_t>
    _groupZoneCooldowns;

// Per-group dungeon entry cooldown:
// group_id -> last dungeon entry event time
static std::map<uint32, time_t>
    _groupDungeonCooldowns;

// Per-group wipe cooldown:
// group_id -> last wipe event time
static std::map<uint32, time_t>
    _groupWipeCooldowns;

// Per-group corpse run cooldown:
// group_id -> last corpse run event time
static std::map<uint32, time_t>
    _groupCorpseRunCooldowns;

// Clean up traits when group no longer qualifies
static void CleanupGroupSession(uint32 groupId)
{
    CharacterDatabase.Execute(
        "DELETE FROM llm_group_bot_traits "
        "WHERE group_id = {}",
        groupId);
    CharacterDatabase.Execute(
        "DELETE FROM llm_group_chat_history "
        "WHERE group_id = {}",
        groupId);

    // Prune in-memory cooldown maps for this group
    _groupKillCooldowns.erase(groupId);
    _groupDeathCooldowns.erase(groupId);
    _groupLootCooldowns.erase(groupId);
    _groupPlayerMsgCooldowns.erase(groupId);
    _groupCombatCooldowns.erase(groupId);
    _groupSpellCooldowns.erase(groupId);
    _groupQuestObjCooldowns.erase(groupId);
    _groupResurrectCooldowns.erase(groupId);
    _groupZoneCooldowns.erase(groupId);
    _groupDungeonCooldowns.erase(groupId);
    _groupWipeCooldowns.erase(groupId);
    _groupCorpseRunCooldowns.erase(groupId);

    LOG_INFO("module",
        "LLMChatter: Cleaned up group {} "
        "(traits + chat history + cooldowns)",
        groupId);
}

class LLMChatterGroupScript : public GroupScript
{
public:
    LLMChatterGroupScript()
        : GroupScript("LLMChatterGroupScript") {}

    void OnAddMember(
        Group* group, ObjectGuid guid) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        // Find the player who just joined
        Player* player =
            ObjectAccessor::FindPlayer(guid);
        if (!player)
            return;

        // Only trigger for bots joining a group
        // that has a real player
        if (!IsPlayerBot(player))
            return;

        if (!GroupHasRealPlayer(group))
            return;

        QueueBotGreetingEvent(player, group);
    }

    void OnRemoveMember(
        Group* group, ObjectGuid guid,
        RemoveMethod /*method*/, ObjectGuid /*kicker*/,
        const char* /*reason*/) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!group)
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Always clean up the removed bot's data
        if (guid)
        {
            Player* removed =
                ObjectAccessor::FindPlayer(guid);
            if (removed && IsPlayerBot(removed))
            {
                uint32 botGuid =
                    guid.GetCounter();
                CharacterDatabase.Execute(
                    "DELETE FROM llm_group_bot_traits "
                    "WHERE group_id = {} "
                    "AND bot_guid = {}",
                    groupId, botGuid);
                CharacterDatabase.Execute(
                    "DELETE FROM "
                    "llm_group_chat_history "
                    "WHERE group_id = {} "
                    "AND speaker_guid = {} "
                    "AND is_bot = 1",
                    groupId, botGuid);
                LOG_INFO("module",
                    "LLMChatter: Cleaned "
                    "traits/history for removed "
                    "bot {} (group {})",
                    botGuid, groupId);
            }
        }

        // If no real player remains, full cleanup
        if (!GroupHasRealPlayer(group))
        {
            CleanupGroupSession(groupId);
        }
    }

    void OnDisband(Group* group) override
    {
        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!group)
            return;

        CleanupGroupSession(
            group->GetGUID().GetCounter());
    }
};

// ============================================================================
// PLAYER SCRIPT - Combat events for grouped bots
// ============================================================================

class LLMChatterPlayerScript : public PlayerScript
{
public:
    LLMChatterPlayerScript()
        : PlayerScript("LLMChatterPlayerScript") {}

    // ------------------------------------------------
    // General channel: player message reaction
    // ------------------------------------------------
    bool OnPlayerCanUseChat(
        Player* player, uint32 /*type*/,
        uint32 /*language*/, std::string& msg,
        Channel* channel) override
    {
        // Always allow chat - we just observe
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGeneralChatReact)
            return true;

        // Only General channel (channelId 1)
        if (!channel || channel->GetChannelId() != 1)
            return true;

        // Skip bots
        if (!player || IsPlayerBot(player))
            return true;

        if (msg.empty())
            return true;

        // Filter ALL_CAPS_WITH_UNDERSCORES (addons)
        {
            bool hasUnderscore = false;
            bool allCapsOrSep = true;
            for (char c : msg)
            {
                if (c == '_')
                    hasUnderscore = true;
                else if (c != ' ' && c != '\t'
                    && c != '\n' && c != '\r'
                    && !(c >= 'A' && c <= 'Z'))
                {
                    allCapsOrSep = false;
                    break;
                }
            }
            if (hasUnderscore && allCapsOrSep)
                return true;
        }

        // Skip link-only messages
        if (msg.size() > 2 && msg[0] == '|'
            && msg[1] == 'c')
        {
            std::string stripped = msg;
            size_t start, end;
            while ((start = stripped.find("|c"))
                   != std::string::npos
                && (end = stripped.find("|r", start))
                   != std::string::npos)
            {
                stripped.erase(start,
                    end - start + 2);
            }
            stripped.erase(0,
                stripped.find_first_not_of(" \t"));
            if (!stripped.empty())
            {
                stripped.erase(
                    stripped.find_last_not_of(
                        " \t") + 1);
            }
            if (stripped.empty())
                return true;
        }

        // Trim and truncate message
        std::string safeMsg = msg;
        size_t firstChar =
            safeMsg.find_first_not_of(" \t\n\r");
        if (firstChar == std::string::npos)
            return true;
        if (firstChar > 0)
            safeMsg = safeMsg.substr(firstChar);
        size_t lastChar =
            safeMsg.find_last_not_of(" \t\n\r");
        if (lastChar != std::string::npos)
            safeMsg =
                safeMsg.substr(0, lastChar + 1);
        if (safeMsg.empty())
            return true;
        if (safeMsg.size() > 250)
            safeMsg = safeMsg.substr(0, 250);

        uint32 zoneId = player->GetZoneId();
        std::string playerName = player->GetName();

        // Store in General chat history
        CharacterDatabase.Execute(
            "INSERT INTO llm_general_chat_history "
            "(zone_id, speaker_name, is_bot, message)"
            " VALUES ({}, '{}', 0, '{}')",
            zoneId,
            EscapeString(playerName),
            EscapeString(safeMsg));

        // Prune history to 15 per zone
        CharacterDatabase.Execute(
            "DELETE FROM llm_general_chat_history "
            "WHERE zone_id = {} AND id NOT IN "
            "(SELECT id FROM (SELECT id FROM "
            "llm_general_chat_history "
            "WHERE zone_id = {} "
            "ORDER BY id DESC LIMIT 15) AS keep)",
            zoneId, zoneId);

        // Per-zone cooldown
        time_t now = time(nullptr);
        auto it =
            _generalChatCooldowns.find(zoneId);
        if (it != _generalChatCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_generalChatCooldown)
            return true;

        // RNG: questions get higher chance
        bool isQuestion =
            !safeMsg.empty()
            && safeMsg.back() == '?';
        uint32 chance = isQuestion
            ? sLLMChatterConfig
                ->_generalChatQuestionChance
            : sLLMChatterConfig
                ->_generalChatChance;
        if (urand(1, 100) > chance)
            return true;

        _generalChatCooldowns[zoneId] = now;

        // Get zone name
        AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(zoneId);
        std::string zoneName =
            area ? area->area_name[0] : "Unknown";

        // Find bots in the same zone (1-4)
        std::vector<Player*> zoneBots;
        auto allBots =
            sRandomPlayerbotMgr.GetAllBots();
        for (auto& pair : allBots)
        {
            Player* bot = pair.second;
            if (!bot || !bot->IsInWorld())
                continue;
            if (bot->GetZoneId() != zoneId)
                continue;
            zoneBots.push_back(bot);
            if (zoneBots.size() >= 8)
                break;
        }

        // Also check account bots via sessions
        if (zoneBots.size() < 8)
        {
            WorldSessionMgr::SessionMap const&
                sessions =
                sWorldSessionMgr
                    ->GetAllSessions();
            for (auto const& pair : sessions)
            {
                WorldSession* session = pair.second;
                if (!session)
                    continue;
                Player* p = session->GetPlayer();
                if (!p || !p->IsInWorld())
                    continue;
                if (!IsPlayerBot(p))
                    continue;
                if (p->GetZoneId() != zoneId)
                    continue;
                // Avoid duplicates
                bool found = false;
                for (Player* b : zoneBots)
                {
                    if (b->GetGUID() == p->GetGUID())
                    {
                        found = true;
                        break;
                    }
                }
                if (!found)
                {
                    zoneBots.push_back(p);
                    if (zoneBots.size() >= 8)
                        break;
                }
            }
        }

        if (zoneBots.empty())
            return true;

        // Shuffle and send all found bots — Python
        // decides how many to use (1 for statement,
        // 2 for conversation)
        std::shuffle(
            zoneBots.begin(), zoneBots.end(),
            std::mt19937{std::random_device{}()});
        uint32 pickCount = zoneBots.size();

        // Build JSON arrays of bot info
        std::string botGuids = "[";
        std::string botNames = "[";
        for (uint32 i = 0; i < pickCount; ++i)
        {
            Player* bot = zoneBots[i];
            if (i > 0)
            {
                botGuids += ",";
                botNames += ",";
            }
            botGuids +=
                std::to_string(
                    bot->GetGUID().GetCounter());
            botNames += "\"" +
                JsonEscape(bot->GetName()) + "\"";
        }
        botGuids += "]";
        botNames += "]";

        std::string extraData = "{"
            "\"player_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"player_message\":\"" +
                JsonEscape(safeMsg) + "\","
            "\"zone_id\":" +
                std::to_string(zoneId) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\","
            "\"bot_guids\":" + botGuids + ","
            "\"bot_names\":" + botNames +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('player_general_msg', "
            "'zone', "
            "{}, {}, 2, 'general_chat:{}', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            zoneId,
            player->GetMapId(),
            zoneId,
            player->GetGUID().GetCounter(),
            EscapeString(playerName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued player_general_msg "
            "from {} in zone {} ({} bots)",
            playerName, zoneName, pickCount);

        return true;
    }

    // ------------------------------------------------
    // Creature Kill event (group chatter)
    // ------------------------------------------------
    void OnPlayerCreatureKill(
        Player* killer, Creature* killed) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!killer || !killed)
            return;

        Group* group = killer->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        // Pick a bot to react: use killer if bot,
        // otherwise pick a random bot from group
        Player* reactor = nullptr;
        if (IsPlayerBot(killer))
            reactor = killer;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
            return;

        // Ranks: 0=Normal, 1=Elite, 2=Rare Elite,
        //        3=Boss, 4=Rare
        CreatureTemplate const* tmpl =
            killed->GetCreatureTemplate();
        if (!tmpl)
            return;

        uint32 rank = tmpl->rank;
        bool isBoss = (rank == 3)
            || (tmpl->type_flags
                & CREATURE_TYPE_FLAG_BOSS_MOB);
        bool isRare = (rank == 2 || rank == 4);
        bool isNormal = !isBoss && !isRare;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown: boss/rare bypass,
        // normal uses config cooldown
        time_t now = time(nullptr);
        if (isNormal)
        {
            auto it =
                _groupKillCooldowns.find(groupId);
            if (it != _groupKillCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_groupKillCooldown)
                return;
        }

        // RNG: boss/rare = 100%, normal = config%
        if (isNormal && urand(1, 100)
            > sLLMChatterConfig
                ->_groupKillChanceNormal)
            return;

        _groupKillCooldowns[groupId] = now;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string creatureName = killed->GetName();
        uint32 creatureEntry = killed->GetEntry();

        // Build extra_data JSON
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"creature_name\":\"" +
                JsonEscape(creatureName) + "\","
            "\"creature_entry\":" +
                std::to_string(creatureEntry) + ","
            "\"is_boss\":" +
                std::string(
                    isBoss ? "true" : "false") + ","
            "\"is_rare\":" +
                std::string(
                    isRare ? "true" : "false") + ","
            "\"is_normal\":" +
                std::string(
                    isNormal ? "true" : "false") + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        // Direct INSERT with short react_after
        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_kill', 'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(creatureName),
            creatureEntry,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_kill "
            "for {} killing {}",
            botName, creatureName);
    }

    void OnPlayerKilledByCreature(
        Creature* killer, Player* killed) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!killed)
            return;

        Group* group = killed->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();
        time_t now = time(nullptr);

        // === Wipe detection (checked BEFORE death
        // cooldown/RNG so wipes aren't suppressed
        // by individual death filters) ===
        {
            bool allDead = true;
            uint32 memberCount = 0;
            for (GroupReference* itr =
                     group->GetFirstMember();
                 itr != nullptr;
                 itr = itr->next())
            {
                Player* member =
                    itr->GetSource();
                if (!member)
                    continue;
                memberCount++;
                if (member->IsAlive())
                {
                    allDead = false;
                    break;
                }
            }

            // Need at least 2 members
            // for a "wipe"
            if (allDead && memberCount >= 2)
            {
                // Check wipe-specific cooldown
                auto wit =
                    _groupWipeCooldowns
                        .find(groupId);
                if (wit
                    != _groupWipeCooldowns.end()
                    && (now - wit->second)
                       < (time_t)
                           sLLMChatterConfig
                               ->_groupWipeCooldown)
                {
                    // Wipe on cooldown, also
                    // skip normal death
                    return;
                }

                // RNG chance from config
                if (urand(1, 100)
                    > sLLMChatterConfig
                        ->_groupWipeChance)
                    return;

                _groupWipeCooldowns[groupId] =
                    now;

                // Pick a random bot to react
                Player* wipeReactor =
                    GetRandomBotInGroup(group);
                if (!wipeReactor)
                    return;

                uint32 wrGuid =
                    wipeReactor->GetGUID()
                        .GetCounter();
                std::string wrName =
                    wipeReactor->GetName();
                std::string kName =
                    killer
                        ? killer->GetName()
                        : "";
                uint32 kEntry =
                    killer
                        ? killer->GetEntry()
                        : 0;

                std::string wipeData = "{"
                    "\"bot_guid\":" +
                        std::to_string(
                            wrGuid) + ","
                    "\"bot_name\":\"" +
                        JsonEscape(
                            wrName) + "\","
                    "\"bot_class\":" +
                        std::to_string(
                            wipeReactor
                                ->getClass())
                        + ","
                    "\"bot_race\":" +
                        std::to_string(
                            wipeReactor
                                ->getRace())
                        + ","
                    "\"bot_level\":" +
                        std::to_string(
                            wipeReactor
                                ->GetLevel())
                        + ","
                    "\"group_id\":" +
                        std::to_string(
                            groupId) + ","
                    "\"killer_name\":\"" +
                        JsonEscape(
                            kName) + "\","
                    "\"killer_entry\":" +
                        std::to_string(
                            kEntry) +
                    "}";

                wipeData =
                    EscapeString(wipeData);

                CharacterDatabase.Execute(
                    "INSERT INTO "
                    "llm_chatter_events "
                    "(event_type, event_scope, "
                    "zone_id, map_id, priority, "
                    "cooldown_key, "
                    "subject_guid, "
                    "subject_name, "
                    "target_guid, "
                    "target_name, "
                    "target_entry, "
                    "extra_data, status, "
                    "react_after, expires_at) "
                    "VALUES ("
                    "'bot_group_wipe', "
                    "'player', "
                    "{}, {}, 1, '', "
                    "{}, '{}', 0, '{}', {}, "
                    "'{}', 'pending', "
                    "DATE_ADD(NOW(), "
                    "INTERVAL 3 SECOND), "
                    "DATE_ADD(NOW(), "
                    "INTERVAL 120 SECOND))",
                    killed->GetZoneId(),
                    killed->GetMapId(),
                    wrGuid,
                    EscapeString(wrName),
                    EscapeString(kName),
                    kEntry,
                    wipeData);

                LOG_INFO("module",
                    "LLMChatter: GROUP WIPE "
                    "detected! {} reacting "
                    "(killed by {})",
                    wrName, kName);

                // Skip normal death event
                return;
            }
        }

        // --- Normal death reaction (not a wipe) ---
        // Per-group cooldown
        auto it = _groupDeathCooldowns.find(groupId);
        if (it != _groupDeathCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupDeathCooldown)
            return;

        // RNG: config% chance to react to a death
        if (urand(1, 100)
            > sLLMChatterConfig->_groupDeathChance)
            return;

        _groupDeathCooldowns[groupId] = now;

        bool isPlayerDeath =
            !IsPlayerBot(killed);
        uint32 deadGuid =
            killed->GetGUID().GetCounter();
        std::string deadName =
            killed->GetName();
        std::string killerName =
            killer ? killer->GetName() : "";
        uint32 killerEntry =
            killer ? killer->GetEntry() : 0;

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(deadGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(deadName) + "\","
            "\"killer_name\":\"" +
                JsonEscape(killerName) + "\","
            "\"killer_entry\":" +
                std::to_string(killerEntry) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"is_player_death\":" +
                std::string(
                    isPlayerDeath
                        ? "true" : "false")
            + "}";

        extraData = EscapeString(extraData);

        // Direct INSERT with short react_after
        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_death', 'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            killed->GetZoneId(),
            killed->GetMapId(),
            deadGuid,
            EscapeString(deadName),
            EscapeString(killerName),
            killerEntry,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_death "
            "for {} killed by {}{}",
            deadName, killerName,
            isPlayerDeath
                ? " (player)" : "");
    }

    // Shared loot handler for both direct loot
    // and group roll rewards
    void HandleGroupLootEvent(
        Player* player, Item* item)
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player || !item)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        ItemTemplate const* tmpl =
            item->GetTemplate();
        if (!tmpl)
            return;

        uint8 quality = tmpl->Quality;
        if (quality < 2)
            return;

        bool isBot = IsPlayerBot(player);

        // Quality-based chance from config:
        // green/blue configurable, epic+=100%
        uint32 chance;
        if (quality == 2)
            chance = sLLMChatterConfig
                ->_groupLootChanceGreen;
        else if (quality == 3)
            chance = sLLMChatterConfig
                ->_groupLootChanceBlue;
        else
            chance = 100;

        if (urand(1, 100) > chance)
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group loot cooldown: config seconds
        // for green/blue, epic+ bypasses cooldown
        time_t now = time(nullptr);
        if (quality < 4)
        {
            auto it =
                _groupLootCooldowns.find(groupId);
            if (it != _groupLootCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_groupLootCooldown)
                return;
        }

        _groupLootCooldowns[groupId] = now;

        uint32 looterGuid =
            player->GetGUID().GetCounter();
        std::string looterName = player->GetName();
        std::string itemName = tmpl->Name1;
        uint32 itemEntry = item->GetEntry();

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(looterGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(looterName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"is_bot\":" +
                std::string(
                    isBot ? "1" : "0") + ","
            "\"item_name\":\"" +
                JsonEscape(itemName) + "\","
            "\"item_entry\":" +
                std::to_string(itemEntry) + ","
            "\"item_quality\":" +
                std::to_string(quality) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_loot', 'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 3 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 120 SECOND))",
            player->GetZoneId(),
            player->GetMapId(),
            looterGuid, EscapeString(looterName),
            EscapeString(itemName),
            itemEntry,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_loot "
            "for {} looting {} (quality={})",
            looterName, itemName, quality);
    }

    void OnPlayerLootItem(
        Player* player, Item* item,
        uint32 /*count*/,
        ObjectGuid /*lootguid*/) override
    {
        HandleGroupLootEvent(player, item);
    }

    void OnPlayerGroupRollRewardItem(
        Player* player, Item* item,
        uint32 /*count*/,
        RollVote /*voteType*/,
        Roll* /*roll*/) override
    {
        HandleGroupLootEvent(player, item);
    }

    void OnPlayerEnterCombat(
        Player* player, Unit* enemy) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player || !enemy)
            return;

        if (!IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        Creature* creature = enemy->ToCreature();
        if (!creature)
            return;

        CreatureTemplate const* tmpl =
            creature->GetCreatureTemplate();
        if (!tmpl)
            return;

        // Ranks: 0=Normal, 1=Elite, 2=Rare Elite,
        //        3=Boss, 4=Rare
        uint32 rank = tmpl->rank;
        bool isBoss = (rank == 3)
            || (tmpl->type_flags
                & CREATURE_TYPE_FLAG_BOSS_MOB);
        bool isElite = (rank >= 1);
        bool isNormal = !isBoss && !isElite;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown: normal uses config,
        // elite+ uses half
        time_t now = time(nullptr);
        uint32 cooldownSec = isNormal
            ? sLLMChatterConfig->_groupKillCooldown
            : sLLMChatterConfig->_groupKillCooldown
              / 2;
        auto it =
            _groupCombatCooldowns.find(groupId);
        if (it != _groupCombatCooldowns.end()
            && (now - it->second)
               < (time_t)cooldownSec)
            return;

        // RNG: Boss=100%, Elite/Rare=40%, Normal=15%
        uint32 chance;
        if (isBoss)
            chance = 100;
        else if (isElite)
            chance = 40;
        else
            chance = 15;
        if (urand(1, 100) > chance)
            return;

        _groupCombatCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName = player->GetName();
        std::string creatureName =
            creature->GetName();

        // Build extra_data JSON
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"creature_name\":\"" +
                JsonEscape(creatureName) + "\","
            "\"creature_entry\":" +
                std::to_string(
                    creature->GetEntry()) + ","
            "\"is_boss\":" +
                std::string(
                    isBoss ? "1" : "0") + ","
            "\"is_elite\":" +
                std::string(
                    isElite ? "1" : "0") + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_combat', "
            "'player', {}, {}, 2, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 1 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 30 SECOND))",
            player->GetZoneId(),
            player->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(creatureName),
            creature->GetEntry(),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_combat "
            "for {} vs {}",
            botName, creatureName);
    }

    void OnPlayerBeforeSendChatMessage(
        Player* player, uint32& type,
        uint32& /*lang*/,
        std::string& msg) override
    {
        if (type != CHAT_MSG_PARTY
            && type != CHAT_MSG_PARTY_LEADER)
            return;

        if (!sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player || msg.empty())
            return;

        // Filter internal/addon messages
        // (ALL_CAPS_WITH_UNDERSCORES patterns)
        {
            bool hasUnderscore = false;
            bool allCapsOrSep = true;
            for (char c : msg)
            {
                if (c == '_')
                    hasUnderscore = true;
                else if (c != ' ' && c != '\t'
                    && c != '\n' && c != '\r'
                    && !(c >= 'A' && c <= 'Z'))
                {
                    allCapsOrSep = false;
                    break;
                }
            }
            if (hasUnderscore && allCapsOrSep)
                return;
        }

        // Skip link-only messages (no real text)
        if (msg.size() > 2 && msg[0] == '|'
            && msg[1] == 'c')
        {
            std::string stripped = msg;
            size_t start, end;
            while ((start = stripped.find("|c"))
                   != std::string::npos
                && (end = stripped.find("|r", start))
                   != std::string::npos)
            {
                stripped.erase(start,
                    end - start + 2);
            }
            stripped.erase(0,
                stripped.find_first_not_of(" \t"));
            if (!stripped.empty())
            {
                stripped.erase(
                    stripped.find_last_not_of(
                        " \t") + 1);
            }
            if (stripped.empty())
                return;
        }

        if (IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Must have at least one bot in group
        bool hasBotInGroup = false;
        for (GroupReference* itr =
                 group->GetFirstMember();
             itr != nullptr; itr = itr->next())
        {
            if (Player* member = itr->GetSource())
            {
                if (IsPlayerBot(member))
                {
                    hasBotInGroup = true;
                    break;
                }
            }
        }
        if (!hasBotInGroup)
            return;

        std::string playerName = player->GetName();
        uint32 playerGuid =
            player->GetGUID().GetCounter();

        // Trim and truncate message
        std::string safeMsg = msg;
        size_t firstChar = safeMsg.find_first_not_of(
            " \t\n\r");
        if (firstChar == std::string::npos)
            return;
        if (firstChar > 0)
            safeMsg = safeMsg.substr(firstChar);
        size_t lastChar = safeMsg.find_last_not_of(
            " \t\n\r");
        if (lastChar != std::string::npos)
            safeMsg = safeMsg.substr(0, lastChar + 1);
        if (safeMsg.empty())
            return;
        if (safeMsg.size() > 250)
            safeMsg = safeMsg.substr(0, 250);

        // Always store in chat history
        CharacterDatabase.Execute(
            "INSERT INTO llm_group_chat_history "
            "(group_id, speaker_guid, speaker_name,"
            " is_bot, message) "
            "VALUES ({}, {}, '{}', 0, '{}')",
            groupId, playerGuid,
            EscapeString(playerName),
            EscapeString(safeMsg));

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupPlayerMsgCooldowns.find(groupId);
        if (it != _groupPlayerMsgCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupPlayerMsgCooldown)
            return;

        _groupPlayerMsgCooldowns[groupId] = now;

        std::string extraData = "{"
            "\"player_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"player_message\":\"" +
                JsonEscape(safeMsg) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names/messages don't
        // break the INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_player_msg', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 3 SECOND), "
            "DATE_ADD(NOW(), INTERVAL 60 SECOND))",
            player->GetZoneId(),
            player->GetMapId(),
            player->GetGUID().GetCounter(),
            EscapeString(playerName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued player_msg "
            "from {} in group {}",
            playerName, groupId);
    }

    // ------------------------------------------------
    // Level Up event
    // ------------------------------------------------
    void OnPlayerLevelChanged(
        Player* player, uint8 oldLevel) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- config disabled");
            return;
        }

        if (!player)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no player");
            return;
        }

        LOG_INFO("module",
            "LLMChatter: LevelChanged - entered "
            "for {} (old lvl {})",
            player->GetName(), oldLevel);

        Group* group = player->GetGroup();
        if (!group)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no group for {}",
                player->GetName());
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no real player in group");
            return;
        }

        // Must actually be gaining a level
        uint8 newLevel = player->GetLevel();
        if (newLevel <= oldLevel)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- level unchanged {} -> {}",
                oldLevel, newLevel);
            return;
        }

        bool isBot = IsPlayerBot(player);

        // Pick reactor: bot uses self, real player
        // picks a random bot from group to react
        Player* reactor = nullptr;
        if (isBot)
            reactor = player;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
        {
            LOG_INFO("module",
                "LLMChatter: LevelChanged "
                "- no reactor bot for {}",
                player->GetName());
            return;
        }

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();

        // Build extra_data JSON
        // leveler_* = who leveled up
        // bot_* = who will react to it
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(newLevel) + ","
            "\"old_level\":" +
                std::to_string(oldLevel) + ","
            "\"is_bot\":" +
                std::string(
                    isBot ? "1" : "0") + ","
            "\"leveler_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT (JsonEscape handles JSON + SQL
        // inside values, this covers the wrapper)
        extraData = EscapeString(extraData);

        LOG_INFO("module",
            "LLMChatter: LevelChanged "
            "- queuing for {} (lvl {} -> {})",
            botName, oldLevel, newLevel);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ('bot_group_levelup', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued bot_group_levelup "
            "for {} (lvl {} -> {})",
            botName, oldLevel, newLevel);
    }

    // ------------------------------------------------
    // Quest Objectives Complete event
    // (fires when all objectives are done,
    //  BEFORE the player turns in the quest)
    // ------------------------------------------------
    bool OnPlayerBeforeQuestComplete(
        Player* player, uint32 questId) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return true;

        if (!player)
            return true;

        Group* group = player->GetGroup();
        if (!group)
            return true;

        if (!GroupHasRealPlayer(group))
            return true;

        // Get quest template for the name
        Quest const* quest =
            sObjectMgr->GetQuestTemplate(questId);
        if (!quest)
            return true;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown to avoid spam
        // from multiple objectives completing
        time_t now = time(nullptr);
        {
            auto it = _groupQuestObjCooldowns
                .find(groupId);
            if (it != _groupQuestObjCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_groupQuestObjectiveCooldown)
                return true;
        }

        // RNG chance to avoid reacting
        // to every single quest objective
        if (urand(1, 100) >
            sLLMChatterConfig
                ->_groupQuestObjectiveChance)
            return true;

        _groupQuestObjCooldowns[groupId] = now;

        bool isBot = IsPlayerBot(player);

        // Pick reactor: bot uses self, real player
        // picks a random bot from group to react
        Player* reactor = nullptr;
        if (isBot)
            reactor = player;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
            return true;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();
        std::string questName = quest->GetTitle();

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"quest_name\":\"" +
                JsonEscape(questName) + "\","
            "\"quest_id\":" +
                std::to_string(questId) + ","
            "\"completer_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_quest_objectives', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(questName),
            questId,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_quest_objectives "
            "for {} completing objectives [{}]",
            botName, questName);

        return true;
    }

    // ------------------------------------------------
    // Quest Complete event
    // ------------------------------------------------
    void OnPlayerCompleteQuest(
        Player* player,
        Quest const* quest) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- config disabled");
            return;
        }

        if (!player || !quest)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no player or quest");
            return;
        }

        LOG_INFO("module",
            "LLMChatter: QuestComplete - entered "
            "for {} quest [{}] (id {})",
            player->GetName(),
            quest->GetTitle(),
            quest->GetQuestId());

        Group* group = player->GetGroup();
        if (!group)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no group for {}",
                player->GetName());
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no real player in group");
            return;
        }

        bool isBot = IsPlayerBot(player);

        // Pick reactor: bot uses self, real player
        // picks a random bot from group to react
        Player* reactor = nullptr;
        if (isBot)
            reactor = player;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
        {
            LOG_INFO("module",
                "LLMChatter: QuestComplete "
                "- no reactor bot for {}",
                player->GetName());
            return;
        }

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();
        std::string questName =
            quest->GetTitle();
        uint32 questId = quest->GetQuestId();

        // Build extra_data JSON
        // completer_* = who finished the quest
        // bot_* = who will react to it
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"is_bot\":" +
                std::string(
                    isBot ? "1" : "0") + ","
            "\"completer_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"quest_name\":\"" +
                JsonEscape(questName) + "\","
            "\"quest_id\":" +
                std::to_string(questId) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT (JsonEscape handles JSON + SQL
        // inside values, this covers the wrapper)
        extraData = EscapeString(extraData);

        LOG_INFO("module",
            "LLMChatter: QuestComplete "
            "- queuing for {} completing [{}]",
            botName, questName);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_quest_complete', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(questName),
            questId,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_quest_complete "
            "for {} completing [{}]",
            botName, questName);
    }

    // ------------------------------------------------
    // Achievement Complete event
    // ------------------------------------------------
    void OnPlayerAchievementComplete(
        Player* player,
        AchievementEntry const* achievement) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- config disabled");
            return;
        }

        if (!player || !achievement)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no player or achievement");
            return;
        }

        LOG_INFO("module",
            "LLMChatter: Achievement - entered "
            "for {} achievement [{}] (id {})",
            player->GetName(),
            achievement->name[0]
                ? achievement->name[0] : "?",
            achievement->ID);

        Group* group = player->GetGroup();
        if (!group)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no group for {}",
                player->GetName());
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no real player in group");
            return;
        }

        bool isBot = IsPlayerBot(player);

        // Pick reactor: bot uses self, real player
        // picks a random bot from group to react
        Player* reactor = nullptr;
        if (isBot)
            reactor = player;
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
        {
            LOG_INFO("module",
                "LLMChatter: Achievement "
                "- no reactor bot for {}",
                player->GetName());
            return;
        }

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();

        // Achievement name is locale-indexed;
        // index 0 = English (enUS)
        std::string achName =
            achievement->name[0]
                ? achievement->name[0] : "";
        uint32 achId = achievement->ID;

        // Build extra_data JSON
        // achiever_* = who earned the achievement
        // bot_* = who will react to it
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"is_bot\":" +
                std::string(
                    isBot ? "1" : "0") + ","
            "\"achiever_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"achievement_name\":\"" +
                JsonEscape(achName) + "\","
            "\"achievement_id\":" +
                std::to_string(achId) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT (JsonEscape handles JSON + SQL
        // inside values, this covers the wrapper)
        extraData = EscapeString(extraData);

        LOG_INFO("module",
            "LLMChatter: Achievement "
            "- queuing for {} earning [{}]",
            botName, achName);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_achievement', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', {}, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(achName),
            achId,
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_achievement "
            "for {} earning [{}]",
            botName, achName);
    }

    // ------------------------------------------------
    // Spell Cast event — heals, CC, resurrects,
    // shields, buffs cast in groups
    // ------------------------------------------------
    void OnPlayerSpellCast(
        Player* player, Spell* spell,
        bool /*skipCheck*/) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGroupChatter)
            return;

        if (!player || !spell)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        // Per-group rate limiter: max 1 spell event
        // per 45 seconds. Check BEFORE any spell
        // classification work (cheapest filter first).
        uint32 groupId =
            group->GetGUID().GetCounter();
        time_t now = time(nullptr);
        {
            auto it =
                _groupSpellCooldowns.find(groupId);
            if (it != _groupSpellCooldowns.end()
                && (now - it->second) < 45)
                return;
        }

        if (!GroupHasRealPlayer(group))
            return;

        SpellInfo const* spellInfo =
            spell->GetSpellInfo();
        if (!spellInfo)
            return;

        // --- Filters (before classification) ---

        // Skip passive spells
        if (spellInfo->IsPassive())
            return;

        // Skip hidden spells (not shown in UI)
        if (spellInfo->HasAttribute(
                SPELL_ATTR0_DO_NOT_DISPLAY))
            return;

        // Skip triggered spells (procs, etc.)
        if (spell->IsTriggered())
            return;

        // Skip spells with no name
        if (!spellInfo->SpellName[0]
            || spellInfo->SpellName[0][0] == '\0')
            return;

        // --- Classify the spell ---
        // Categories: heal, cc, resurrect, shield,
        // buff
        std::string spellCategory;

        // 1. RESURRECT — check first (rare, always
        //    fires at 100%)
        if (spellInfo->HasEffect(SPELL_EFFECT_RESURRECT)
            || spellInfo->HasEffect(
                   SPELL_EFFECT_RESURRECT_NEW))
        {
            spellCategory = "resurrect";
        }
        // 2. HEAL — must target a different player
        //    in the same group (not self-heal)
        else if (
            spellInfo->HasEffect(SPELL_EFFECT_HEAL)
            || spellInfo->HasEffect(
                   SPELL_EFFECT_HEAL_MAX_HEALTH))
        {
            Unit* target =
                spell->m_targets.GetUnitTarget();
            if (!target || target == player)
                return;

            Player* targetPlayer =
                target->ToPlayer();
            if (!targetPlayer)
                return;

            // Target must be in the same group
            if (!targetPlayer->GetGroup()
                || targetPlayer->GetGroup()
                       != group)
                return;

            spellCategory = "heal";
        }
        // 3. CC (Crowd Control) — stun, root, fear,
        //    charm, confuse (polymorph etc.)
        else if (
            spellInfo->HasAura(
                SPELL_AURA_MOD_STUN)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_ROOT)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_FEAR)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_CHARM)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_CONFUSE))
        {
            spellCategory = "cc";
        }
        // 4. SHIELD/IMMUNITY — positive spell with
        //    immunity or absorb aura
        else if (spellInfo->IsPositive()
            && (spellInfo->HasAura(
                    SPELL_AURA_SCHOOL_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_DAMAGE_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_MECHANIC_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_SCHOOL_ABSORB)))
        {
            spellCategory = "shield";
        }
        // 5. BUFF — positive spell on a groupmate
        //    (not self). Catches MotW, Fort, Kings,
        //    Arcane Intellect, etc.
        else if (spellInfo->IsPositive()
            && (spellInfo->HasAura(
                    SPELL_AURA_MOD_STAT)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_RESISTANCE)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_ATTACK_POWER)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_POWER_REGEN)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_INCREASE_SPEED)))
        {
            // Must target a different group member
            Unit* target =
                spell->m_targets.GetUnitTarget();
            if (!target || target == player)
                return;

            Player* targetPlayer =
                target->ToPlayer();
            if (!targetPlayer)
                return;

            if (!targetPlayer->GetGroup()
                || targetPlayer->GetGroup()
                       != group)
                return;

            spellCategory = "buff";
        }
        else
        {
            // Not a meaningful spell category
            return;
        }

        // --- RNG gate ---
        // Resurrect always fires (100%);
        // everything else configurable chance
        if (spellCategory != "resurrect"
            && urand(1, 100) >
                sLLMChatterConfig
                    ->_groupSpellCastChance)
            return;

        // Update the per-group cooldown
        _groupSpellCooldowns[groupId] = now;

        // --- Determine reactor bot ---
        // If caster is a bot: the caster speaks
        // about their own spell (more natural).
        // If caster is the real player: pick a
        // random bot to react (e.g. say thanks).
        bool casterIsBot = IsPlayerBot(player);
        Player* reactor = nullptr;
        if (casterIsBot)
            reactor = player;  // caster speaks
        else
            reactor = GetRandomBotInGroup(group);

        if (!reactor)
            return;

        // --- Gather data ---
        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string casterName = player->GetName();
        std::string spellName =
            spellInfo->SpellName[0]
                ? spellInfo->SpellName[0] : "";

        // Determine target name
        std::string targetName;
        Unit* spellTarget =
            spell->m_targets.GetUnitTarget();
        if (spellTarget)
            targetName = spellTarget->GetName();

        // Build extra_data JSON
        // NOTE: extraData is inserted into SQL via
        // fmt::format; relies on JsonEscape for
        // single-quote safety (see JsonEscape comment)
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"caster_name\":\"" +
                JsonEscape(casterName) + "\","
            "\"spell_name\":\"" +
                JsonEscape(spellName) + "\","
            "\"spell_category\":\"" +
                spellCategory + "\","
            "\"target_name\":\"" +
                JsonEscape(targetName) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, zone_id, "
            "map_id, priority, cooldown_key, "
            "subject_guid, subject_name, "
            "target_guid, target_name, "
            "target_entry, extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_spell_cast', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), INTERVAL 2 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            botGuid, EscapeString(botName),
            EscapeString(casterName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_spell_cast "
            "for {} casting {} [{}]",
            casterName, spellName, spellCategory);
    }

    // -----------------------------------------------
    // Hook: Bot resurrects in a group with real player
    // -----------------------------------------------
    void OnPlayerResurrect(
        Player* player, float /*restore_percent*/,
        bool /*applySickness*/) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        if (!IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupResurrectCooldowns
                .find(groupId);
        if (it
            != _groupResurrectCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupResurrectCooldown)
            return;

        // RNG chance from config
        if (urand(1, 100)
            > sLLMChatterConfig
                ->_groupResurrectChance)
            return;

        _groupResurrectCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName =
            player->GetName();

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_resurrect', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 3 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            player->GetZoneId(),
            player->GetMapId(),
            botGuid,
            EscapeString(botName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_resurrect for {}",
            botName);
    }

    // -----------------------------------------------
    // Hook: Bot releases spirit (corpse run)
    // -----------------------------------------------
    void OnPlayerReleasedGhost(Player* player) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupCorpseRunCooldowns
                .find(groupId);
        if (it
            != _groupCorpseRunCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupCorpseRunCooldown)
            return;

        // RNG chance from config
        if (urand(1, 100)
            > sLLMChatterConfig
                ->_groupCorpseRunChance)
            return;

        _groupCorpseRunCooldowns[groupId] = now;

        bool isPlayerDeath =
            !IsPlayerBot(player);
        std::string deadName =
            player->GetName();

        // Pick a bot to react — for player
        // deaths, any bot; for bot deaths,
        // a different bot
        Player* reactor = isPlayerDeath
            ? GetRandomBotInGroup(group)
            : GetRandomBotInGroup(
                  group, player);
        if (!reactor)
            return;

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName =
            reactor->GetName();
        uint32 zoneId = player->GetZoneId();
        std::string zoneName =
            GetZoneName(zoneId);

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"zone_id\":" +
                std::to_string(zoneId) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\","
            "\"dead_name\":\"" +
                JsonEscape(deadName) + "\","
            "\"is_player_death\":" +
                std::string(
                    isPlayerDeath
                        ? "true" : "false")
            + "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_corpse_run', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            zoneId,
            player->GetMapId(),
            botGuid,
            EscapeString(botName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_corpse_run for "
            "{} (died: {}) in {}",
            botName, deadName, zoneName);
    }

    // -----------------------------------------------
    // Hook: Bot enters a new zone in a group
    // -----------------------------------------------
    void OnPlayerUpdateZone(
        Player* player, uint32 newZone,
        uint32 /*newArea*/) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        if (!IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupZoneCooldowns.find(groupId);
        if (it != _groupZoneCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupZoneCooldown)
            return;

        // RNG chance
        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_groupZoneChance)
            return;

        // Get zone name from DBC, skip if empty
        AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(
                newZone);
        std::string zoneName =
            area ? area->area_name[0] : "";
        if (zoneName.empty())
            return;

        _groupZoneCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName =
            player->GetName();

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"zone_id\":" +
                std::to_string(newZone) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\""
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_zone_transition', "
            "'player', "
            "{}, {}, 3, '', "
            "{}, '{}', 0, '{}', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 120 SECOND))",
            newZone,
            player->GetMapId(),
            botGuid,
            EscapeString(botName),
            EscapeString(zoneName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_zone_transition "
            "for {} entering {}",
            botName, zoneName);
    }

    // -----------------------------------------------
    // Hook: Bot enters a dungeon/raid instance
    // -----------------------------------------------
    void OnPlayerMapChanged(
        Player* player) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig
                   ->_useGroupChatter)
            return;

        if (!player)
            return;

        if (!IsPlayerBot(player))
            return;

        Map* map = player->GetMap();
        if (!map || !map->IsDungeon())
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Per-group cooldown
        time_t now = time(nullptr);
        auto it =
            _groupDungeonCooldowns
                .find(groupId);
        if (it
            != _groupDungeonCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupDungeonCooldown)
            return;

        // RNG chance
        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_groupDungeonChance)
            return;

        _groupDungeonCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName =
            player->GetName();
        std::string mapName =
            map->GetMapName();
        bool isRaid = map->IsRaid();

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    player->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    player->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    player->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"map_id\":" +
                std::to_string(
                    map->GetId()) + ","
            "\"map_name\":\"" +
                JsonEscape(mapName) + "\","
            "\"is_raid\":" +
                std::string(
                    isRaid
                        ? "true"
                        : "false") + ","
            "\"zone_id\":" +
                std::to_string(
                    player->GetZoneId()) +
            "}";

        extraData = EscapeString(extraData);

        CharacterDatabase.Execute(
            "INSERT INTO llm_chatter_events "
            "(event_type, event_scope, "
            "zone_id, map_id, priority, "
            "cooldown_key, subject_guid, "
            "subject_name, target_guid, "
            "target_name, target_entry, "
            "extra_data, status, "
            "react_after, expires_at) "
            "VALUES ("
            "'bot_group_dungeon_entry', "
            "'player', "
            "{}, {}, 1, '', "
            "{}, '{}', 0, '{}', 0, "
            "'{}', 'pending', "
            "DATE_ADD(NOW(), "
            "INTERVAL 5 SECOND), "
            "DATE_ADD(NOW(), "
            "INTERVAL 300 SECOND))",
            player->GetZoneId(),
            map->GetId(),
            botGuid,
            EscapeString(botName),
            EscapeString(mapName),
            extraData);

        LOG_INFO("module",
            "LLMChatter: Queued "
            "bot_group_dungeon_entry "
            "for {} entering {} (raid={})",
            botName, mapName,
            isRaid ? "yes" : "no");
    }
};

// Register scripts
void AddLLMChatterScripts()
{
    new LLMChatterWorldScript();
    new LLMChatterGameEventScript();
    new LLMChatterALEScript();
    new LLMChatterGroupScript();
    new LLMChatterPlayerScript();
}
