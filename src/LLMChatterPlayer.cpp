/*
 * mod-llm-chatter - player/general ownership
 */

#include "LLMChatterConfig.h"
#include "LLMChatterBG.h"
#include "LLMChatterGroup.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "Battleground.h"
#include "BattlegroundAB.h"
#include "BattlegroundEY.h"
#include "BattlegroundWS.h"
#include "Channel.h"
#include "ChannelMgr.h"
#include "Chat.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Group.h"
#include "Log.h"
#include "MapMgr.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "ScriptMgr.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <cstdio>
#include <map>
#include <mutex>
#include <random>
#include <string>
#include <vector>

void EnsureBotInGeneralChannel(
    Player* bot)
{
    if (!bot || !bot->IsInWorld())
        return;

    uint32 zoneId = bot->GetZoneId();
    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId);
    if (!area)
        return;

    uint8 locale = sWorld->GetDefaultDbcLocale();
    char const* n = area->area_name[locale];
    std::string zoneName = n ? n : "";
    if (zoneName.empty())
    {
        n = area->area_name[LOCALE_enUS];
        zoneName = n ? n : "";
    }
    if (zoneName.empty())
        return;

    ChatChannelsEntry const* chEntry =
        sChatChannelsStore.LookupEntry(
            ChatChannelId::GENERAL);
    if (!chEntry)
        return;

    char nameBuf[100];
    std::snprintf(
        nameBuf,
        sizeof(nameBuf),
        chEntry->pattern[locale],
        zoneName.c_str());
    std::string newChanName(nameBuf);

    ChannelMgr* cMgr =
        ChannelMgr::forTeam(bot->GetTeamId());
    if (!cMgr)
        return;

    static std::mutex channelsLock;
    std::lock_guard<std::mutex> guard(
        channelsLock);

    for (auto const& [key, channel] :
         cMgr->GetChannels())
    {
        if (!channel)
            continue;
        if (channel->GetChannelId()
            != ChatChannelId::GENERAL)
            continue;
        if (channel->GetName() == newChanName)
            continue;

        channel->LeaveChannel(bot, false);
        bot->LeftChannel(channel);
    }

    Channel* joinChan =
        cMgr->GetJoinChannel(
            newChanName,
            ChatChannelId::GENERAL);
    if (joinChan)
        joinChan->JoinChannel(bot, "");
}

static std::map<uint32, time_t> _generalChatCooldowns;
static std::mutex _generalChatCooldownsMutex;

// Per-group subzone cooldown keyed by group counter.
// Uses the same configured cooldown as
// GroupChatter.ZoneTransitionCooldown.
static std::map<uint32, time_t>
    _subzoneCommentCooldowns;
static std::mutex _subzoneCooldownMutex;

struct IntrusionState
{
    time_t firstSeen;
    bool firstAlerted;
};

static std::map<std::pair<uint32, uint32>,
    IntrusionState> _intrusionStates;
static std::map<uint32, time_t>
    _zoneAlertThrottle;
static time_t _lastIntrusionEviction = 0;
static std::mutex _intrusionMutex;

static void CleanupIntrusionStateOnZoneChange(
    uint32 guid, uint32 newZone)
{
    auto it = _intrusionStates.begin();
    while (it != _intrusionStates.end())
    {
        if (it->first.first == guid
            && it->first.second != newZone)
            it = _intrusionStates.erase(it);
        else
            ++it;
    }
}

static bool CheckIntrusionGate(
    uint32 guid, uint32 zoneId, time_t now)
{
    // Zone-level throttle
    auto zt = _zoneAlertThrottle.find(zoneId);
    if (zt != _zoneAlertThrottle.end()
        && (now - zt->second)
           < (time_t)sLLMChatterConfig
               ->_zoneIntrusionZoneThrottleSec)
        return false;

    // Per-intruder first-alert check
    auto key = std::make_pair(guid, zoneId);
    auto it = _intrusionStates.find(key);
    if (it != _intrusionStates.end()
        && it->second.firstAlerted)
        return false;

    return true;
}

static void CommitIntrusionState(
    uint32 guid, uint32 zoneId, time_t now)
{
    auto key = std::make_pair(guid, zoneId);
    _intrusionStates[key] = {now, true};
    _zoneAlertThrottle[zoneId] = now;
}

static void HandleEnemyZoneIntrusion(
    Player* player, uint32 newZone)
{
    if (!sLLMChatterConfig->_zoneIntrusionEnable)
        return;

    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(newZone);
    if (!area)
        return;

    // Only faction-owned zones
    if (area->team != AREATEAM_ALLY
        && area->team != AREATEAM_HORDE)
        return;

    // Determine if intruder is enemy
    TeamId playerTeam = player->GetTeamId();
    bool isEnemy = false;
    TeamId defenderTeam;
    if (area->team == AREATEAM_ALLY
        && playerTeam == TEAM_HORDE)
    {
        isEnemy = true;
        defenderTeam = TEAM_ALLIANCE;
    }
    else if (area->team == AREATEAM_HORDE
        && playerTeam == TEAM_ALLIANCE)
    {
        isEnemy = true;
        defenderTeam = TEAM_HORDE;
    }

    if (!isEnemy)
        return;

    uint32 guid = player->GetGUID().GetCounter();
    time_t now = time(nullptr);

    // First gate check (cheap, under mutex)
    {
        std::lock_guard<std::mutex> guard(
            _intrusionMutex);
        if (!CheckIntrusionGate(
                guid, newZone, now))
            return;
    }

    // Defender search (expensive, no lock held)
    Player* defender = FindNearbyDefenderBot(
        player, newZone, defenderTeam);
    if (!defender)
        return;

    // Re-check gate + commit atomically
    {
        std::lock_guard<std::mutex> guard(
            _intrusionMutex);
        if (!CheckIntrusionGate(
                guid, newZone, now))
            return;
        CommitIntrusionState(guid, newZone, now);
    }

    bool isCapital =
        (area->flags & AREA_FLAG_CAPITAL) != 0;

    std::string zoneName = GetZoneName(newZone);
    if (zoneName.empty())
        zoneName = "Unknown";

    uint8 intruderClass = player->getClass();
    uint8 intruderRace = player->getRace();
    uint32 intruderLevel = player->GetLevel();

    uint32 defGuid =
        defender->GetGUID().GetCounter();
    uint8 defClass = defender->getClass();
    uint8 defRace = defender->getRace();
    uint32 defLevel = defender->GetLevel();

    std::string extraData = "{"
        "\"intruder_name\":\"" +
            JsonEscape(player->GetName()) + "\","
        "\"intruder_class\":" +
            std::to_string(intruderClass) + ","
        "\"intruder_race\":" +
            std::to_string(intruderRace) + ","
        "\"intruder_level\":" +
            std::to_string(intruderLevel) + ","
        "\"intruder_is_bot\":false,"
        "\"is_capital\":" +
            std::string(
                isCapital ? "true" : "false") + ","
        "\"zone_name\":\"" +
            JsonEscape(zoneName) + "\","
        "\"defender_guid\":" +
            std::to_string(defGuid) + ","
        "\"defender_name\":\"" +
            JsonEscape(defender->GetName()) + "\","
        "\"defender_class\":" +
            std::to_string(defClass) + ","
        "\"defender_race\":" +
            std::to_string(defRace) + ","
        "\"defender_level\":" +
            std::to_string(defLevel) +
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "player_enters_zone",
        "zone",
        newZone,
        player->GetMapId(),
        GetChatterEventPriority(
            "player_enters_zone"),
        "zone_intrusion:" +
            std::to_string(newZone),
        player->GetGUID().GetCounter(),
        player->GetName(),
        defGuid,
        defender->GetName(),
        0,
        extraData,
        GetReactionDelaySeconds(
            "player_enters_zone"),
        120,
        false
    );

}

static void HandleBotEntersEnemyTerritory(
    Player* player, uint32 newZone)
{
    if (!sLLMChatterConfig->_zoneIntrusionEnable)
        return;

    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(newZone);
    if (!area)
        return;

    if (area->team != AREATEAM_ALLY
        && area->team != AREATEAM_HORDE)
        return;

    TeamId playerTeam = player->GetTeamId();
    bool isEnemy = false;
    TeamId defenderTeam;
    if (area->team == AREATEAM_ALLY
        && playerTeam == TEAM_HORDE)
    {
        isEnemy = true;
        defenderTeam = TEAM_ALLIANCE;
    }
    else if (area->team == AREATEAM_HORDE
        && playerTeam == TEAM_ALLIANCE)
    {
        isEnemy = true;
        defenderTeam = TEAM_HORDE;
    }

    if (!isEnemy)
        return;

    // Only fire when a real human player is in the
    // target zone to witness the yell — no point
    // generating LLM chatter for bot-vs-bot events
    // in empty zones the user will never see.
    {
        bool hasRealPlayer = false;
        uint32 intruderMap = player->GetMapId();
        for (auto const& [pguid, p] :
             ObjectAccessor::GetPlayers())
        {
            if (!p || !p->IsInWorld())
                continue;
            if (IsPlayerBot(p))
                continue;
            if (p->GetZoneId() != newZone)
                continue;
            if (p->GetMapId() != intruderMap)
                continue;
            hasRealPlayer = true;
            break;
        }
        if (!hasRealPlayer)
            return;
    }

    uint32 guid = player->GetGUID().GetCounter();
    time_t now = time(nullptr);

    // First gate check (cheap, under mutex)
    {
        std::lock_guard<std::mutex> guard(
            _intrusionMutex);
        if (!CheckIntrusionGate(
                guid, newZone, now))
            return;
    }

    // Defender search (expensive, no lock held)
    Player* defender = FindNearbyDefenderBot(
        player, newZone, defenderTeam);
    if (!defender)
        return;

    // Re-check gate + commit atomically
    {
        std::lock_guard<std::mutex> guard(
            _intrusionMutex);
        if (!CheckIntrusionGate(
                guid, newZone, now))
            return;
        CommitIntrusionState(guid, newZone, now);
    }

    std::string zoneName = GetZoneName(newZone);
    if (zoneName.empty())
        zoneName = "Unknown";

    uint8 intruderClass = player->getClass();
    uint8 intruderRace = player->getRace();
    uint32 intruderLevel = player->GetLevel();

    uint32 defGuid =
        defender->GetGUID().GetCounter();

    std::string extraData = "{"
        "\"intruder_name\":\"" +
            JsonEscape(player->GetName()) + "\","
        "\"intruder_class\":" +
            std::to_string(intruderClass) + ","
        "\"intruder_race\":" +
            std::to_string(intruderRace) + ","
        "\"intruder_level\":" +
            std::to_string(intruderLevel) + ","
        "\"intruder_is_bot\":true,"
        "\"is_capital\":true,"
        "\"zone_name\":\"" +
            JsonEscape(zoneName) + "\","
        "\"defender_guid\":" +
            std::to_string(defGuid) + ","
        "\"defender_name\":\"" +
            JsonEscape(defender->GetName()) + "\","
        "\"defender_class\":" +
            std::to_string(
                defender->getClass()) + ","
        "\"defender_race\":" +
            std::to_string(
                defender->getRace()) + ","
        "\"defender_level\":" +
            std::to_string(
                defender->GetLevel()) +
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "player_enters_zone",
        "zone",
        newZone,
        player->GetMapId(),
        GetChatterEventPriority(
            "player_enters_zone"),
        "zone_intrusion:" +
            std::to_string(newZone),
        player->GetGUID().GetCounter(),
        player->GetName(),
        defGuid,
        defender->GetName(),
        0,
        extraData,
        GetReactionDelaySeconds(
            "player_enters_zone"),
        120,
        false
    );

}

// ============================================================
// Delayed rejoin queue — definitions + processing
// ============================================================

std::mutex _rejoinMutex;
std::vector<PendingRejoin> _pendingRejoins;

void ProcessPendingRejoins()
{
    if (!sLLMChatterConfig->_useGroupChatter)
        return;

    std::vector<PendingRejoin> work;
    {
        std::lock_guard<std::mutex> guard(
            _rejoinMutex);
        if (_pendingRejoins.empty())
            return;
        work.swap(_pendingRejoins);
    }

    time_t now = time(nullptr);
    std::vector<PendingRejoin> deferred;

    for (auto const& entry : work)
    {
        // Minimum 10s before first attempt.
        if (now - entry.loginTime < 10)
        {
            deferred.push_back(entry);
            continue;
        }

        bool timedOut =
            (now - entry.loginTime > 120);

        Player* player =
            ObjectAccessor::FindPlayer(
                ObjectGuid::Create<HighGuid::Player>(
                    entry.playerGuid));
        if (!player)
            continue;

        Group* group = player->GetGroup();
        if (!group)
            continue;
        if (group->GetGUID().GetCounter()
            != entry.groupId)
            continue;

        // Check if all non-self members have loaded
        // Player* objects. Uses the persisted member
        // list (GetMemberSlots) for the total count
        // and live GroupReference for loaded count.
        // No bot-type filtering — avoids coupling
        // to mod-playerbots eligibility categories.
        auto const& slots =
            group->GetMemberSlots();
        uint32 totalOther = 0;
        for (auto const& slot : slots)
        {
            if (slot.guid.GetCounter()
                != entry.playerGuid)
                ++totalOther;
        }
        uint32 loadedOther = 0;
        for (GroupReference* itr =
                 group->GetFirstMember();
             itr != nullptr; itr = itr->next())
        {
            Player* m = itr->GetSource();
            if (m && m->GetGUID().GetCounter()
                != entry.playerGuid)
                ++loadedOther;
        }

        // Defer if members still loading, unless
        // the hard cap (120s) has been reached —
        // then process whatever is available.
        if (loadedOther < totalOther && !timedOut)
        {
            deferred.push_back(entry);
            continue;
        }

        // All members loaded — collect bot data.
        uint32 groupId = entry.groupId;
        uint32 pZone = player->GetZoneId();
        uint32 pArea = player->GetAreaId();
        uint32 pMap  = player->GetMapId();

        std::vector<uint32> botGuids;
        std::string firstBotName;
        std::string botsJson = "[";
        bool first = true;

        for (GroupReference* itr =
                 group->GetFirstMember();
             itr != nullptr; itr = itr->next())
        {
            Player* member = itr->GetSource();
            if (!member
                || !IsPlayerBot(member))
                continue;

            uint32 bguid =
                member->GetGUID().GetCounter();
            botGuids.push_back(bguid);
            if (first)
                firstBotName = member->GetName();

            std::string role = "dps";
            PlayerbotAI* ai =
                GET_PLAYERBOT_AI(member);
            if (ai)
            {
                if (PlayerbotAI::IsTank(member))
                    role = "tank";
                else if (
                    PlayerbotAI::IsHeal(member))
                    role = "healer";
                else if (
                    PlayerbotAI::IsRanged(member))
                    role = "ranged_dps";
                else
                    role = "melee_dps";
            }

            if (!first) botsJson += ",";
            first = false;
            botsJson += "{"
                "\"bot_guid\":" +
                    std::to_string(bguid) + ","
                "\"bot_name\":\"" +
                    JsonEscape(
                        member->GetName()) +
                    "\","
                "\"bot_class\":" +
                    std::to_string(
                        member->getClass()) +
                    ","
                "\"bot_race\":" +
                    std::to_string(
                        member->getRace()) +
                    ","
                "\"bot_gender\":" +
                    std::to_string(
                        member->getGender()) +
                    ","
                "\"bot_level\":" +
                    std::to_string(
                        member->GetLevel()) +
                    ","
                "\"role\":\"" + role + "\","
                "\"zone\":" +
                    std::to_string(pZone) + ","
                "\"map\":" +
                    std::to_string(pMap) +
                "}";
        }

        if (botGuids.empty())
            continue;

        botsJson += "]";

        std::string extraData = "{"
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"player_name\":\"" +
                JsonEscape(player->GetName()) +
                "\","
            "\"zone\":" +
                std::to_string(pZone) + ","
            "\"area\":" +
                std::to_string(pArea) + ","
            "\"map\":" +
                std::to_string(pMap) + ","
            "\"rejoin\":true,"
            "\"bots\":" + botsJson +
            "}";
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_join_batch",
            "player",
            pZone, pMap,
            GetChatterEventPriority(
                "bot_group_join_batch"), "",
            botGuids[0], firstBotName,
            0, "", 0,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_join_batch"),
            120, false);

        // Mark bots as greeted.
        {
            std::lock_guard<std::mutex> guard(
                _groupJoinBatchMutex);
            for (uint32 bguid : botGuids)
            {
                _greetedBotGuids.insert(bguid);
                _groupGreetedBots[groupId]
                    .push_back(bguid);
            }
            _groupJoinFlushed.insert(groupId);
        }
    }

    // Re-insert entries that haven't aged enough.
    if (!deferred.empty())
    {
        std::lock_guard<std::mutex> guard(
            _rejoinMutex);
        _pendingRejoins.insert(
            _pendingRejoins.end(),
            deferred.begin(),
            deferred.end());
    }
}

class LLMChatterPlayerScript : public PlayerScript
{
public:
    LLMChatterPlayerScript()
        : PlayerScript(
              "LLMChatterPlayerScript",
              {PLAYERHOOK_ON_LOGIN,
               PLAYERHOOK_CAN_PLAYER_USE_CHANNEL_CHAT,
               PLAYERHOOK_ON_UPDATE_ZONE,
               PLAYERHOOK_ON_UPDATE_AREA,
               PLAYERHOOK_ON_PVP_KILL}) {}

    void OnPlayerLogin(Player* player) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled())
            return;

        if (!player || IsPlayerBot(player))
            return;

        // Defensive crash-recovery cleanup: if the
        // server crashed, CleanupGroupSession never
        // ran and stale entries may linger. Grace
        // 5-minute window: entries this old are
        // definitively stale (crash recovery only).
        // Protects active sessions of other online
        // players — normal delivery completes in
        // seconds, never minutes.
        CharacterDatabase.Execute(
            "UPDATE llm_chatter_queue "
            "SET status = 'cancelled' "
            "WHERE status = 'pending' "
            "AND created_at < NOW() "
            "- INTERVAL 5 MINUTE");

        CharacterDatabase.Execute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1 "
            "WHERE delivered = 0 "
            "AND deliver_at < NOW() "
            "- INTERVAL 5 MINUTE");

        // Re-initialize group state after relog.
        // Python cleanup_stale_groups() deletes
        // bot_traits while the player is offline;
        // OnAddMember doesn't fire on relog because
        // the group already exists.  Bots aren't
        // loaded yet at login time (PlayerbotMgr
        // spawns them asynchronously), so queue for
        // delayed processing from OnUpdate.
        if (!sLLMChatterConfig->_useGroupChatter)
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        // Clear dedup state so the rejoin batch
        // can be queued when bots are loaded.
        {
            std::lock_guard<std::mutex> guard(
                _groupJoinBatchMutex);
            _groupJoinFlushed.erase(groupId);
            auto git =
                _groupGreetedBots.find(groupId);
            if (git != _groupGreetedBots.end())
            {
                for (uint32 bguid : git->second)
                    _greetedBotGuids.erase(bguid);
                _groupGreetedBots.erase(git);
            }
        }

        // Queue for delayed processing.
        {
            std::lock_guard<std::mutex> guard(
                _rejoinMutex);
            _pendingRejoins.push_back(
                {groupId,
                 player->GetGUID().GetCounter(),
                 time(nullptr)});
        }
    }

    bool OnPlayerCanUseChat(
        Player* player, uint32 /*type*/,
        uint32 /*language*/, std::string& msg,
        Channel* channel) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useGeneralChatReact)
            return true;

        if (!channel
            || channel->GetChannelId()
                != ChatChannelId::GENERAL)
            return true;

        if (player)
        {
            Map* gMap = player->GetMap();
            if (gMap
                && (gMap->IsRaid()
                    || gMap->IsBattleground()))
                return true;
        }

        if (!player || IsPlayerBot(player))
            return true;

        if (msg.empty())
            return true;

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
        if (safeMsg.size()
            > sLLMChatterConfig->_maxMessageLength)
            safeMsg = safeMsg.substr(
                0,
                sLLMChatterConfig->_maxMessageLength);

        uint32 zoneId = player->GetZoneId();
        std::string playerName = player->GetName();

        CharacterDatabase.Execute(
            "INSERT INTO llm_general_chat_history "
            "(zone_id, speaker_name, is_bot, message)"
            " VALUES ({}, '{}', 0, '{}')",
            zoneId,
            EscapeString(playerName),
            EscapeString(safeMsg));

        CharacterDatabase.Execute(
            "DELETE FROM llm_general_chat_history "
            "WHERE zone_id = {} AND id NOT IN "
            "(SELECT id FROM (SELECT id FROM "
            "llm_general_chat_history "
            "WHERE zone_id = {} "
            "ORDER BY id DESC LIMIT "
            + std::to_string(
                sLLMChatterConfig
                    ->_generalChatHistoryLimit)
            + ") AS keep)",
            zoneId, zoneId);

        time_t now = time(nullptr);
        {
            std::lock_guard<std::mutex> guard(
                _generalChatCooldownsMutex);
            auto it =
                _generalChatCooldowns.find(zoneId);
            if (it != _generalChatCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_generalChatCooldown)
                return true;
        }

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

        {
            std::lock_guard<std::mutex> guard(
                _generalChatCooldownsMutex);
            auto it =
                _generalChatCooldowns.find(zoneId);
            if (it != _generalChatCooldowns.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_generalChatCooldown)
                return true;
            _generalChatCooldowns[zoneId] = now;
        }

        std::string zoneName = GetZoneName(zoneId);
        if (zoneName.empty())
            zoneName = "Unknown";

        std::vector<Player*> zoneBots;
        zoneBots.reserve(8);

        {
            WorldSessionMgr::SessionMap const& sessions =
                sWorldSessionMgr->GetAllSessions();
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
                zoneBots.push_back(p);
                if (zoneBots.size()
                    >= sLLMChatterConfig
                        ->_maxBotsPerZone)
                    break;
            }
        }

        if (zoneBots.size()
            < sLLMChatterConfig->_maxBotsPerZone)
        {
            auto allBots =
                sRandomPlayerbotMgr.GetAllBots();
            for (auto& pair : allBots)
            {
                Player* bot = pair.second;
                if (!bot || !bot->IsInWorld())
                    continue;
                if (bot->GetZoneId() != zoneId)
                    continue;

                bool found = false;
                for (Player* b : zoneBots)
                {
                    if (b->GetGUID() == bot->GetGUID())
                    {
                        found = true;
                        break;
                    }
                }
                if (!found)
                {
                    zoneBots.push_back(bot);
                    if (zoneBots.size()
                        >= sLLMChatterConfig
                            ->_maxBotsPerZone)
                        break;
                }
            }
        }

        zoneBots.erase(
            std::remove_if(
                zoneBots.begin(), zoneBots.end(),
                [](Player* b) {
                    return !CanSpeakInGeneralChannel(b);
                }),
            zoneBots.end());

        if (zoneBots.empty())
            return true;

        std::shuffle(
            zoneBots.begin(), zoneBots.end(),
            std::mt19937{std::random_device{}()});
        uint32 pickCount = zoneBots.size();

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
            botGuids += std::to_string(
                bot->GetGUID().GetCounter());
            botNames += "\"" +
                JsonEscape(bot->GetName()) + "\"";
        }
        botGuids += "]";
        botNames += "]";

        std::string extraData = "{"
            "\"player_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"player_gender\":" +
                std::to_string(player->getGender()) + ","
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

        QueueChatterEvent(
            "player_general_msg",
            "zone",
            zoneId,
            player->GetMapId(),
            GetChatterEventPriority(
                "player_general_msg"),
            "general_chat:" +
                std::to_string(zoneId),
            player->GetGUID().GetCounter(),
            playerName,
            0,
            "",
            0,
            extraData,
            GetReactionDelaySeconds(
                "player_general_msg"),
            120,
            false
        );

        return true;
    }

    void OnPlayerPVPKill(
        Player* killer, Player* killed) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_bgChatterEnable)
            return;
        if (!killer || !killed)
            return;

        if (!killer->InBattleground())
            return;
        Battleground* bg = killer->GetBattleground();
        if (!bg || !bg->isBattleground())
            return;

        if (urand(1, 100)
            > sLLMChatterConfig->_eventReactionChance)
            return;

        std::string extraBase = "{"
            "\"victim_name\":\"" +
                JsonEscape(killed->GetName()) +
                "\","
            "\"victim_class\":" +
                std::to_string(
                    killed->getClass()) +
            ",\"killer_name\":\"" +
                JsonEscape(killer->GetName()) +
                "\","
            "\"killer_is_real_player\":"
                + std::string(
                    IsPlayerBot(killer)
                    ? "false" : "true") +
            "}";

        for (auto const& [g, p] : bg->GetPlayers())
        {
            Player* rp =
                ObjectAccessor::FindPlayer(g);
            if (!rp || IsPlayerBot(rp))
                continue;
            if (rp->GetBgTeamId()
                != killer->GetBgTeamId())
                continue;

            Group* group = rp->GetGroup();
            if (!group || !GroupHasBots(group))
                continue;

            std::string extra = extraBase;
            AppendBGContext(bg, rp, extra);
            QueueBGEvent(rp, "bg_pvp_kill", extra);
        }

    }

    void OnPlayerUpdateArea(
        Player* player, uint32 oldArea,
        uint32 newArea) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled())
            return;

        if (!player || IsPlayerBot(player))
            return;

        Group* grp = player->GetGroup();
        if (!grp || !GroupHasBots(grp))
            return;

        uint32 gId =
            grp->GetGUID().GetCounter();

        // Always update the area column
        CharacterDatabase.Execute(
            "UPDATE llm_group_bot_traits "
            "SET area = {} "
            "WHERE group_id = {}",
            newArea, gId);

        // Skip if area didn't actually change
        // (can happen on login/teleport)
        if (oldArea == newArea || !newArea)
            return;

        // Skip if the zone also changed — the
        // zone transition handler covers that
        uint32 curZone = player->GetZoneId();
        AreaTableEntry const* oldEntry =
            sAreaTableStore.LookupEntry(oldArea);
        uint32 oldZone = 0;
        if (oldEntry)
            oldZone = oldEntry->zone
                ? oldEntry->zone : oldArea;
        if (oldZone != curZone)
            return;

        uint32 subzoneCooldown =
            sLLMChatterConfig->_groupZoneCooldown;
        uint32 subzoneChance =
            sLLMChatterConfig->_groupZoneChance;

        // Per-group cooldown (shared across all
        // subzones so rapid area crossings don't
        // spam the party channel).
        time_t now = time(nullptr);
        {
            std::lock_guard<std::mutex> guard(
                _subzoneCooldownMutex);
            auto it =
                _subzoneCommentCooldowns.find(gId);
            if (it != _subzoneCommentCooldowns.end()
                && (now - it->second)
                   < static_cast<time_t>(
                         subzoneCooldown))
                return;
        }

        if (urand(1, 100) > subzoneChance)
            return;

        // Resolve area name
        std::string areaName;
        AreaTableEntry const* areaEntry =
            sAreaTableStore.LookupEntry(newArea);
        if (areaEntry)
        {
            uint8 loc =
                sWorld->GetDefaultDbcLocale();
            char const* n =
                areaEntry->area_name[loc];
            areaName = n ? n : "";
            if (areaName.empty())
            {
                n = areaEntry
                    ->area_name[LOCALE_enUS];
                areaName = n ? n : "";
            }
        }
        if (areaName.empty())
            return;

        // Pick a random alive bot from the group
        std::vector<Player*> aliveBots;
        for (auto const& ref :
            grp->GetMemberSlots())
        {
            Player* m =
                ObjectAccessor::FindPlayer(
                    ref.guid);
            if (m && IsPlayerBot(m)
                && m->IsAlive())
                aliveBots.push_back(m);
        }
        if (aliveBots.empty())
            return;
        Player* bot = aliveBots[
            urand(0, aliveBots.size() - 1)];

        // Resolve zone name
        std::string zoneName;
        AreaTableEntry const* zoneEntry =
            sAreaTableStore.LookupEntry(curZone);
        if (zoneEntry)
        {
            uint8 loc =
                sWorld->GetDefaultDbcLocale();
            char const* n =
                zoneEntry->area_name[loc];
            zoneName = n ? n : "";
            if (zoneName.empty())
            {
                n = zoneEntry
                    ->area_name[LOCALE_enUS];
                zoneName = n ? n : "";
            }
        }

        uint32 botGuid =
            bot->GetGUID().GetCounter();

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(bot->GetName()) + "\","
            "\"bot_class\":" +
                std::to_string(
                    bot->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    bot->getRace()) + ","
            "\"bot_gender\":" +
                std::to_string(
                    bot->getGender()) + ","
            "\"bot_level\":" +
                std::to_string(
                    bot->GetLevel()) + ","
            "\"group_id\":" +
                std::to_string(gId) + ","
            "\"zone_id\":" +
                std::to_string(curZone) + ","
            "\"zone_name\":\"" +
                JsonEscape(zoneName) + "\","
            "\"area_id\":" +
                std::to_string(newArea) + ","
            "\"area_name\":\"" +
                JsonEscape(areaName) + "\""
            "}";

        extraData = EscapeString(extraData);

        // Stamp cooldown only after all guards pass
        // and the configured RNG succeeded.
        {
            std::lock_guard<std::mutex> guard(
                _subzoneCooldownMutex);
            _subzoneCommentCooldowns[gId] = now;
        }

        QueueChatterEvent(
            "bot_group_subzone_change",
            "player",
            curZone,
            player->GetMapId(),
            GetChatterEventPriority(
                "bot_group_subzone_change"),
            "",
            botGuid,
            bot->GetName(),
            0,
            areaName,
            0,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_subzone_change"),
            120,
            false
        );
    }

    void OnPlayerUpdateZone(
        Player* player, uint32 newZone,
        uint32 newArea) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled())
            return;

        if (!player)
            return;

        // Eviction sweep + cleanup under mutex
        {
            std::lock_guard<std::mutex> guard(
                _intrusionMutex);

            // Eviction sweep (every 300s, TTL 1800s)
            time_t now = time(nullptr);
            if (now - _lastIntrusionEviction > 300)
            {
                _lastIntrusionEviction = now;
                auto it =
                    _intrusionStates.begin();
                while (it
                    != _intrusionStates.end())
                {
                    if (now - it->second.firstSeen
                        > 1800)
                        it = _intrusionStates
                            .erase(it);
                    else
                        ++it;
                }
                auto zt =
                    _zoneAlertThrottle.begin();
                while (zt
                    != _zoneAlertThrottle.end())
                {
                    if (now - zt->second > 1800)
                        zt = _zoneAlertThrottle
                            .erase(zt);
                    else
                        ++zt;
                }
            }

            // Clean up intrusion state for ALL
            // players on zone change
            CleanupIntrusionStateOnZoneChange(
                player->GetGUID().GetCounter(),
                newZone);
        }

        if (!IsPlayerBot(player))
        {
            // Immediately persist zone + map so the
            // Python bridge sees fresh data without
            // waiting for the 15-min autosave.
            CharacterDatabase.Execute(
                "UPDATE characters "
                "SET zone = {}, map = {} "
                "WHERE guid = {}",
                newZone,
                player->GetMapId(),
                player->GetGUID().GetCounter());

            // Real player: update all bot zones
            // in group + check for enemy zone
            HandleGroupPlayerUpdateZone(
                player, newZone, newArea);
            HandleEnemyZoneIntrusion(
                player, newZone);
            return;
        }

        // Bot paths
        EnsureBotInGeneralChannel(player);
        HandleGroupPlayerUpdateZone(
            player, newZone, newArea);
        HandleBotEntersEnemyTerritory(
            player, newZone);
    }
};

void AddLLMChatterPlayerScripts()
{
    new LLMChatterPlayerScript();
}
