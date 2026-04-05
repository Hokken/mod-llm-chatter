/*
 * mod-llm-chatter - world/event script ownership
 */

#include "LLMChatterAmbient.h"
#include "LLMChatterConfig.h"
#include "LLMChatterDelivery.h"
#include "LLMChatterGroup.h"
#include "LLMChatterNearby.h"
#include "LLMChatterProximity.h"
#include "LLMChatterShared.h"

#include "DatabaseEnv.h"
#include "Group.h"
#include "Log.h"
#include "MapMgr.h"
#include "ObjectAccessor.h"
#include "Player.h"
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

static std::map<std::string, time_t> _cooldownCache;

static bool IsOnCooldown(
    const std::string& cooldownKey,
    uint32 cooldownSeconds)
{
    return IsEventOnCooldown(
        _cooldownCache,
        cooldownKey,
        cooldownSeconds);
}

static void SetCooldown(
    const std::string& cooldownKey)
{
    SetEventCooldown(_cooldownCache, cooldownKey);
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

    if (!cooldownKey.empty()
        && IsOnCooldown(cooldownKey, cooldownSeconds))
        return;

    if (!cooldownKey.empty())
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
        HandleAmbientGameEventStart(eventId);
    }

    void OnStop(uint16 eventId) override
    {
        HandleAmbientGameEventStop(eventId);
    }
};

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
        HandleWeatherChange(weather, state, grade);
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
        _lastProximityScanTime = 0;
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

        if (sLLMChatterConfig->_proxChatterEnable
            && now - _lastProximityScanTime
                >= sLLMChatterConfig
                       ->_proxChatterScanInterval
                    * 1000)
        {
            _lastProximityScanTime = now;
            CheckProximityChatter();
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
    uint32 _lastProximityScanTime = 0;
    uint32 _lastQuestFlushTime = 0;
    uint32 _lastGroupJoinFlushTime = 0;
    uint32 _lastRaidMoraleTime = 0;
    std::string _lastTimePeriod;

    void CheckDayNightTransition()
    {
        ::CheckDayNightTransition(_lastTimePeriod);
    }

    void CheckAmbientWeather()
    {
        ::CheckAmbientWeather();
    }

    void CheckActiveHolidays()
    {
        ::CheckActiveHolidays();
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
        ::CheckNearbyGameObjects();
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

            // Block morale only during active combat.
            // Dead/ghost members are fine — banter
            // between pulls should still fire even if
            // someone hasn't been rezzed yet.
            bool anyCombat = false;
            for (auto const& mRef :
                 group->GetMemberSlots())
            {
                Player* member =
                    ObjectAccessor::FindPlayer(
                        mRef.guid);
                if (member && member->IsInCombat())
                {
                    anyCombat = true;
                    break;
                }
            }
            if (anyCombat)
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

    void TryTriggerChatter()
    {
        ::TryTriggerChatter();
    }

    void DeliverPendingMessages()
    {
        DeliverPendingMessagesImpl();
    }
};

void AddLLMChatterWorldScripts()
{
    new LLMChatterWorldScript();
    new LLMChatterGameEventScript();
    new LLMChatterALEScript();
}

