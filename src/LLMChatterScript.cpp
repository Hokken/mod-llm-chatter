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
#include <vector>
#include <map>
#include <set>
#include <random>
#include <sstream>

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

// Convert all link markers to WoW hyperlinks
static std::string ConvertAllLinks(const std::string& text)
{
    std::string result = text;
    result = ConvertItemLinks(result);
    result = ConvertQuestLinks(result);
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
    while ((pos = result.find('\'', pos)) != std::string::npos)
    {
        result.replace(pos, 1, "''");
        pos += 2;
    }
    return result;
}

// Escape string for JSON values (escapes quotes and backslashes)
static std::string JsonEscape(const std::string& str)
{
    std::string result;
    result.reserve(str.size());
    for (char c : str)
    {
        switch (c)
        {
            case '"':  result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\t': result += "\\t"; break;
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
        { minDelay = 60; maxDelay = 300; }
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
    if (urand(1, 100) > sLLMChatterConfig->_eventReactionChance)
    {
        LOG_DEBUG("module", "LLMChatter: Event {} skipped (reaction chance)", eventType);
        return;
    }

    // Check cooldown
    if (!cooldownKey.empty() && IsOnCooldown(cooldownKey, cooldownSeconds))
    {
        LOG_DEBUG("module", "LLMChatter: Event {} on cooldown ({})", eventType, cooldownKey);
        return;
    }

    // Calculate delays
    uint32 reactionDelay = GetReactionDelaySeconds(eventType);
    uint32 expirationSeconds = sLLMChatterConfig->_eventExpirationSeconds;

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
        EscapeString(extraData),
        reactionDelay, expirationSeconds);

    LOG_INFO("module", "LLMChatter: Queued event {} in zone {} (react in {}s)",
             eventType, zoneId, reactionDelay);
}

// Known holiday event IDs
static const std::set<uint16> HOLIDAY_EVENTS = {
    1,   // Midsummer Fire Festival
    2,   // Winter Veil
    7,   // Lunar Festival
    8,   // Love is in the Air
    9,   // Noblegarden
    10,  // Children's Week
    11,  // Harvest Festival
    12,  // Hallow's End
    24,  // Brewfest
    26,  // Pilgrim's Bounty
    50,  // Pirates' Day
    51,  // Day of the Dead
};

// ============================================================================
// GAME EVENT SCRIPT - Holiday Events
// ============================================================================

class LLMChatterGameEventScript : public GameEventScript
{
public:
    LLMChatterGameEventScript() : GameEventScript("LLMChatterGameEventScript") {}

    void OnStart(uint16 eventId) override
    {
        LOG_DEBUG("module", "LLMChatter: GameEvent OnStart - hook called for event {}", eventId);
        if (!sLLMChatterConfig->IsEnabled() || !sLLMChatterConfig->_useEventSystem)
            return;
        if (!sLLMChatterConfig->_eventsHolidays)
            return;

        // Only care about holiday events
        if (HOLIDAY_EVENTS.find(eventId) == HOLIDAY_EVENTS.end())
            return;

        GameEventMgr::GameEventDataMap const& events = sGameEventMgr->GetEventMap();
        if (eventId >= events.size())
            return;
        GameEventData const& eventData = events[eventId];
        std::string cooldownKey = "holiday:" + std::to_string(eventId);

        std::string extraData = "{\"event_name\":\"" + JsonEscape(eventData.Description) + "\"}";

        QueueEvent("holiday_start", "global", 0, 0, 2, cooldownKey, 86400 * 7,
                   0, "", 0, "", eventId, extraData);

        LOG_INFO("module", "LLMChatter: Holiday started - {}", eventData.Description);
    }

    void OnStop(uint16 eventId) override
    {
        LOG_DEBUG("module", "LLMChatter: GameEvent OnStop - hook called for event {}", eventId);
        if (!sLLMChatterConfig->IsEnabled() || !sLLMChatterConfig->_useEventSystem)
            return;
        if (!sLLMChatterConfig->_eventsHolidays)
            return;

        if (HOLIDAY_EVENTS.find(eventId) == HOLIDAY_EVENTS.end())
            return;

        GameEventMgr::GameEventDataMap const& events = sGameEventMgr->GetEventMap();
        if (eventId >= events.size())
            return;
        GameEventData const& eventData = events[eventId];
        std::string cooldownKey = "holiday_end:" + std::to_string(eventId);

        std::string extraData = "{\"event_name\":\"" + JsonEscape(eventData.Description) + "\"}";

        QueueEvent("holiday_end", "global", 0, 0, 3, cooldownKey, 86400 * 7,
                   0, "", 0, "", eventId, extraData);
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
        WeatherState prevState = WEATHER_STATE_FINE;
        auto it = _zoneWeatherState.find(zoneId);
        if (it != _zoneWeatherState.end())
            prevState = it->second;

        // Update tracked state
        _zoneWeatherState[zoneId] = state;

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
        std::string extraData = "{\"weather_type\":\"" + weatherName + "\","
                               "\"previous_weather\":\"" + prevWeatherName + "\","
                               "\"transition\":\"" + transitionType + "\","
                               "\"category\":\"" + category + "\","
                               "\"intensity\":\"" + intensity + "\","
                               "\"grade\":" + std::to_string(grade) + "}";

        QueueEvent("weather_change", "zone", zoneId, 0, 5, cooldownKey, 1800,
                   0, "", 0, "", static_cast<uint32>(state), extraData);

        LOG_INFO("module", "LLMChatter: Weather {} in zone {} - {} -> {} ({})",
                 transitionType, zoneId, prevWeatherName, weatherName, intensity);
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

        // Load transport info cache for transport events
        LoadTransportCache();

        LOG_INFO("module", "LLMChatter: Cleared stale messages and events, WorldScript initialized");
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

        // Check for environmental events (every 60 seconds)
        if (sLLMChatterConfig->_useEventSystem &&
            now - _lastEnvironmentCheckTime >= 60000)
        {
            _lastEnvironmentCheckTime = now;
            CheckDayNightTransition();
        }

        // Check for transport zone changes (every 5 seconds)
        if (sLLMChatterConfig->_useEventSystem &&
            sLLMChatterConfig->_eventsTransports &&
            now - _lastTransportCheckTime >= 5000)
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
        std::string extraData = "{"
            "\"is_day\":" + std::string(isDay ? "true" : "false") + ","
            "\"hour\":" + std::to_string(hour) + ","
            "\"minute\":" + std::to_string(minute) + ","
            "\"time_period\":\"" + timePeriod + "\","
            "\"previous_period\":\"" + previousPeriod + "\","
            "\"description\":\"" + JsonEscape(description) + "\""
            "}";

        QueueEvent("day_night_transition", "global", 0, 0, 7, cooldownKey, 7200,
                   0, "", 0, "", 0, extraData);

        LOG_INFO("module", "LLMChatter: Time transition - {} -> {} ({}:{})",
                 previousPeriod, timePeriod, hour, minute);
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

                // Skip if zone lookup failed
                if (currentZone == 0)
                    continue;

                // Check for zone change
                auto it = _transportZones.find(guid);
                if (it != _transportZones.end())
                {
                    uint32 lastZone = it->second.first;
                    uint32 lastMap = it->second.second;

                    // Detect zone change or map change
                    if (currentZone != lastZone || mapId != lastMap)
                    {
                        // Zone changed! Queue event if we have transport info
                        auto cacheIt = _transportCache.find(entry);
                        if (cacheIt != _transportCache.end())
                        {
                            const TransportInfo& info = cacheIt->second;

                            // Build cooldown key
                            std::string cooldownKey = "transport:" + std::to_string(entry) +
                                                     ":zone:" + std::to_string(currentZone);

                            // Build extra data JSON
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
                                600,  // 10 minute cooldown per transport+zone
                                0, "",  // no subject
                                0, info.fullName, entry,  // target info
                                extraData
                            );

                            LOG_INFO("module", "LLMChatter: Transport {} ({}) arrived in zone {}",
                                     info.transportType, info.destination, currentZone);
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

    // Get zone name from zone ID
    std::string GetZoneName(uint32 zoneId)
    {
        if (AreaTableEntry const* area = sAreaTableStore.LookupEntry(zoneId))
        {
            return area->area_name[0];  // English name
        }
        return "Unknown Zone";
    }

    // Check if player is a bot
    bool IsPlayerBot(Player* player)
    {
        if (!player)
            return false;

        PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
        return ai != nullptr;
    }

    // Get faction (0 = Alliance, 1 = Horde)
    uint32 GetFaction(Player* player)
    {
        return player->GetTeamId();  // TEAM_ALLIANCE = 0, TEAM_HORDE = 1
    }

    // Check if player is in the overworld (not an instance)
    bool IsInOverworld(Player* player)
    {
        if (!player)
            return false;

        // Check if player is fully loaded (not in character creation cinematic)
        WorldSession* session = player->GetSession();
        if (!session)
            return false;

        if (session->PlayerLoading())
            return false;

        Map* map = player->GetMap();
        if (!map)
            return false;

        // Only allow chatter in common world maps (not dungeons, raids, BGs, arenas)
        return !map->Instanceable();
    }

    // Find zones that have real (non-bot) players in the overworld
    std::vector<uint32> GetZonesWithRealPlayers()
    {
        std::map<uint32, bool> zoneMap;

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

            // Only count real players (not bots) in the overworld
            if (!IsPlayerBot(player) && IsInOverworld(player))
            {
                uint32 zoneId = player->GetZoneId();
                if (zoneId > 0)
                {
                    zoneMap[zoneId] = true;
                }
            }
        }

        std::vector<uint32> zones;
        for (auto const& pair : zoneMap)
        {
            zones.push_back(pair.first);
        }

        LOG_DEBUG("module", "LLMChatter: GetZonesWithRealPlayers - returning {} zones", zones.size());
        return zones;
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
        LOG_INFO("module", "LLMChatter: TryTriggerChatter called");

        // Roll for trigger chance
        uint32 roll = urand(1, 100);
        if (roll > sLLMChatterConfig->_triggerChance)
        {
            LOG_INFO("module", "LLMChatter: Skipped (roll {} > chance {})", roll, sLLMChatterConfig->_triggerChance);
            return;
        }

        // Check pending requests
        QueryResult countResult = CharacterDatabase.Query(
            "SELECT COUNT(*) FROM llm_chatter_queue WHERE status IN ('pending', 'processing')");

        if (countResult)
        {
            uint32 pending = countResult->Fetch()[0].Get<uint32>();
            if (pending >= sLLMChatterConfig->_maxPendingRequests)
            {
                LOG_DEBUG("module", "LLMChatter: Max pending requests reached ({})", pending);
                return;
            }
        }

        // Find zones with real players
        std::vector<uint32> validZones = GetZonesWithRealPlayers();
        if (validZones.empty())
        {
            LOG_INFO("module", "LLMChatter: No zones with real players found");
            return;
        }
        LOG_INFO("module", "LLMChatter: Found {} zones with real players", validZones.size());

        // Pick one zone randomly
        std::random_device rd;
        std::mt19937 g(rd());
        std::shuffle(validZones.begin(), validZones.end(), g);
        uint32 selectedZone = validZones[0];
        std::string zoneName = GetZoneName(selectedZone);

        // Get the dominant faction in this zone
        uint32 faction = GetDominantFactionInZone(selectedZone);
        LOG_DEBUG("module", "LLMChatter: Selected zone {} ({}), dominant faction: {}",
                 selectedZone, zoneName, faction == TEAM_ALLIANCE ? "Alliance" : "Horde");

        // Get bots in this zone with matching faction
        std::vector<Player*> bots = GetBotsInZone(selectedZone, faction);

        // Decide: statement or conversation
        bool isConversation = (urand(1, 100) <= sLLMChatterConfig->_conversationChance);

        // Check if we have enough bots
        uint32 requiredBots = isConversation ? 2 : 1;
        if (bots.size() < requiredBots)
        {
            // Try single statement if not enough for conversation
            if (isConversation && bots.size() >= 1)
            {
                isConversation = false;
                LOG_DEBUG("module", "LLMChatter: Not enough bots for conversation in {}, falling back to statement",
                          zoneName);
            }
            else
            {
                LOG_DEBUG("module", "LLMChatter: No bots in {} (faction {})", zoneName, faction);
                return;
            }
        }

        // Shuffle bots and pick
        std::shuffle(bots.begin(), bots.end(), g);

        // For conversations, randomly decide 2-4 participants based on available bots
        uint32 botCount = 1;
        if (isConversation)
        {
            // Determine max possible bots (2-4, limited by available bots)
            uint32 maxBots = std::min(static_cast<uint32>(bots.size()), 4u);
            // Randomly pick 2-4 bots with weighted distribution (2 bots more common)
            // 50% chance for 2 bots, 30% for 3 bots, 20% for 4 bots
            uint32 roll = urand(1, 100);
            if (roll <= 50 || maxBots == 2)
                botCount = 2;
            else if (roll <= 80 || maxBots == 3)
                botCount = std::min(3u, maxBots);
            else
                botCount = maxBots;
        }

        Player* bot1 = bots[0];
        Player* bot2 = (botCount >= 2) ? bots[1] : nullptr;
        Player* bot3 = (botCount >= 3) ? bots[2] : nullptr;
        Player* bot4 = (botCount >= 4) ? bots[3] : nullptr;

        // Queue the request
        QueueChatterRequest(bot1, bot2, bot3, bot4, botCount, isConversation, zoneName, selectedZone);
    }

    void QueueChatterRequest(Player* bot1, Player* bot2, Player* bot3, Player* bot4,
                             uint32 botCount, bool isConversation, const std::string& zoneName, uint32 zoneId)
    {
        std::string requestType = isConversation ? "conversation" : "statement";
        std::string bot1Name = bot1->GetName();
        std::string bot1Class = GetClassName(bot1->getClass());
        std::string bot1Race = GetRaceName(bot1->getRace());
        uint8 bot1Level = bot1->GetLevel();

        // Escape zone name for SQL (handle apostrophes)
        std::string escapedZoneName = zoneName;
        size_t pos = 0;
        while ((pos = escapedZoneName.find('\'', pos)) != std::string::npos)
        {
            escapedZoneName.replace(pos, 1, "''");
            pos += 2;
        }

        if (isConversation && bot2)
        {
            std::string bot2Name = bot2->GetName();
            std::string bot2Class = GetClassName(bot2->getClass());
            std::string bot2Race = GetRaceName(bot2->getRace());
            uint8 bot2Level = bot2->GetLevel();

            // Build the SQL dynamically based on how many bots we have
            std::string columns = "request_type, bot1_guid, bot1_name, bot1_class, bot1_race, bot1_level, bot1_zone, zone_id, bot_count, "
                                  "bot2_guid, bot2_name, bot2_class, bot2_race, bot2_level";
            std::string values = fmt::format("'{}', {}, '{}', '{}', '{}', {}, '{}', {}, {}, {}, '{}', '{}', '{}', {}",
                requestType,
                bot1->GetGUID().GetCounter(), bot1Name, bot1Class, bot1Race, bot1Level, escapedZoneName, zoneId, botCount,
                bot2->GetGUID().GetCounter(), bot2Name, bot2Class, bot2Race, bot2Level);

            // Add bot3 if present
            if (bot3)
            {
                std::string bot3Name = bot3->GetName();
                std::string bot3Class = GetClassName(bot3->getClass());
                std::string bot3Race = GetRaceName(bot3->getRace());
                uint8 bot3Level = bot3->GetLevel();
                columns += ", bot3_guid, bot3_name, bot3_class, bot3_race, bot3_level";
                values += fmt::format(", {}, '{}', '{}', '{}', {}",
                    bot3->GetGUID().GetCounter(), bot3Name, bot3Class, bot3Race, bot3Level);
            }

            // Add bot4 if present
            if (bot4)
            {
                std::string bot4Name = bot4->GetName();
                std::string bot4Class = GetClassName(bot4->getClass());
                std::string bot4Race = GetRaceName(bot4->getRace());
                uint8 bot4Level = bot4->GetLevel();
                columns += ", bot4_guid, bot4_name, bot4_class, bot4_race, bot4_level";
                values += fmt::format(", {}, '{}', '{}', '{}', {}",
                    bot4->GetGUID().GetCounter(), bot4Name, bot4Class, bot4Race, bot4Level);
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
                "(request_type, bot1_guid, bot1_name, bot1_class, bot1_race, bot1_level, bot1_zone, zone_id, bot_count, status) "
                "VALUES ('{}', {}, '{}', '{}', '{}', {}, '{}', {}, 1, 'pending')",
                requestType,
                bot1->GetGUID().GetCounter(), bot1Name, bot1Class, bot1Race, bot1Level, escapedZoneName, zoneId);

            LOG_INFO("module", "LLMChatter: Queued statement in {} for {} ({} {})",
                     zoneName, bot1Name, bot1Race, bot1Class);
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

            // Mark as delivered FIRST to prevent duplicate delivery
            CharacterDatabase.DirectExecute(
                "UPDATE llm_chatter_messages SET delivered = 1, delivered_at = NOW() WHERE id = {}",
                messageId);

            // Find the bot player from RandomPlayerbotMgr
            Player* bot = nullptr;
            PlayerBotMap allBots = sRandomPlayerbotMgr.GetAllBots();

            for (auto const& pair : allBots)
            {
                Player* player = pair.second;
                if (!player)
                    continue;

                if (player->GetGUID().GetCounter() == botGuid)
                {
                    // Check if bot is fully loaded before using
                    WorldSession* session = player->GetSession();
                    if (session && session->PlayerLoading())
                    {
                        // Don't use this bot, it's not ready
                        break;
                    }
                    bot = player;
                    break;
                }
            }

            if (bot && bot->IsInWorld())
            {
                // Send to channel using PlayerbotAI
                if (PlayerbotAI* ai = GET_PLAYERBOT_AI(bot))
                {
                    // Convert any link markers to WoW hyperlinks
                    std::string processedMessage = ConvertAllLinks(message);
                    ai->SayToChannel(processedMessage, ChatChannelId::GENERAL);
                    LOG_INFO("module", "LLMChatter: [General] {}: {}", botName, processedMessage);
                }
            }
            else
            {
                LOG_DEBUG("module", "LLMChatter: Bot {} not found or offline, skipping message", botName);
            }

        } while (result->NextRow());
    }
};

// Register scripts
void AddLLMChatterScripts()
{
    new LLMChatterWorldScript();
    new LLMChatterGameEventScript();
    new LLMChatterALEScript();
}
