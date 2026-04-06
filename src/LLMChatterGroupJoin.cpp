/*
 * mod-llm-chatter - group join batching domain
 *
 * Owns:
 *   - QueueBotGreetingEvent()
 *   - EnsureGroupJoinQueued()
 *   - FlushGroupJoinBatches()
 *   - LLMChatterGroupScript (GroupScript)
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroup.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "Battleground.h"
#include "Chat.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Group.h"
#include "MapMgr.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "ScriptMgr.h"
#include "World.h"
#include "WorldSession.h"

#include <algorithm>
#include <mutex>
#include <string>
#include <vector>

// ============================================================================
// QueueBotGreetingEvent
// ============================================================================

// Queue a greeting event for a bot joining a group.
// When debounce > 0, accumulates into a batch so
// rapid invites are processed together with full
// group knowledge.  When debounce == 0, queues
// immediately (legacy behavior).
void QueueBotGreetingEvent(
    Player* bot, Group* group)
{
    if (!bot || !group)
        return;

    uint32 groupId = group->GetGUID().GetCounter();
    uint32 botGuid = bot->GetGUID().GetCounter();
    std::string botName = bot->GetName();

    // Get bot info
    uint8 botClass = bot->getClass();
    uint8 botRace = bot->getRace();
    uint8 botGender = bot->getGender();
    uint8 botLevel = bot->GetLevel();

    // Find real player name and area
    std::string playerName;
    Player* realPlayer = nullptr;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        if (Player* member = itr->GetSource())
        {
            if (!IsPlayerBot(member)
                && !realPlayer)
            {
                playerName = member->GetName();
                realPlayer = member;
            }
        }
    }
    uint32 playerAreaId = realPlayer
        ? realPlayer->GetAreaId() : 0;

    // Detect bot role for Python trait storage
    std::string role = "dps";
    PlayerbotAI* botAi = GET_PLAYERBOT_AI(bot);
    if (botAi)
    {
        if (PlayerbotAI::IsTank(bot))
            role = "tank";
        else if (PlayerbotAI::IsHeal(bot))
            role = "healer";
        else if (PlayerbotAI::IsRanged(bot))
            role = "ranged_dps";
        else
            role = "melee_dps";
    }

    uint32 debounce = sLLMChatterConfig
        ->_groupJoinDebounceSec;

    // Debounce disabled → queue immediately
    // (legacy single-bot path)
    if (debounce == 0)
    {
        uint32 groupSize = 0;
        for (GroupReference* itr =
                 group->GetFirstMember();
             itr != nullptr; itr = itr->next())
        {
            if (itr->GetSource())
                ++groupSize;
        }

        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(botGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(botName) + "\","
            "\"bot_class\":" +
                std::to_string(botClass) + ","
            "\"bot_race\":" +
                std::to_string(botRace) + ","
            "\"bot_gender\":" +
                std::to_string(botGender) + ","
            "\"bot_level\":" +
                std::to_string(botLevel) + ","
            "\"role\":\"" + role + "\","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"player_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"group_size\":" +
                std::to_string(groupSize) + ","
            "\"zone\":" +
                std::to_string(
                    bot->GetZoneId()) + ","
            "\"area\":" +
                std::to_string(
                    playerAreaId) + ","
            "\"map\":" +
                std::to_string(
                    bot->GetMapId()) +
            "}";
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_join",
            "player",
            bot->GetZoneId(),
            bot->GetMapId(),
            GetChatterEventPriority("bot_group_join"), "",
            botGuid, botName,
            0, "", 0,
            extraData,
            GetReactionDelaySeconds("bot_group_join"),
            120, false
        );

        return;
    }

    // ---- Debounce path: accumulate into batch ----
    uint32 zoneId = bot->GetZoneId();
    uint32 mapId = bot->GetMapId();
    bool groupFull = group->IsFull();

    GroupJoinEntry entry;
    entry.botGuid = botGuid;
    entry.botName = botName;
    entry.botClass = botClass;
    entry.botRace = botRace;
    entry.botGender = botGender;
    entry.botLevel = botLevel;
    entry.role = role;
    entry.zoneId = zoneId;
    entry.mapId = mapId;

    {
        std::lock_guard<std::mutex> guard(
            _groupJoinBatchMutex);

        // Skip if this specific bot was already
        // greeted (bots re-triggering OnAddMember
        // after teleport to player). Use per-bot
        // GUID so newly invited bots are NOT
        // blocked after the first batch flushes.
        if (_greetedBotGuids.count(botGuid))
            return;

        auto it = _groupJoinBatches.find(groupId);
        if (it != _groupJoinBatches.end())
        {
            it->second.bots.push_back(
                std::move(entry));
            // If group is full, force immediate
            // flush on next OnUpdate tick
            if (groupFull)
                it->second.lastJoinTime = 0;
            else
                it->second.lastJoinTime =
                    time(nullptr);
        }
        else
        {
            GroupJoinBatch batch;
            batch.groupId = groupId;
            batch.playerName = playerName;
            batch.zoneId = zoneId;
            batch.areaId = playerAreaId;
            batch.mapId = mapId;
            batch.lastJoinTime = groupFull
                ? 0 : time(nullptr);
            batch.bots.push_back(
                std::move(entry));
            _groupJoinBatches[groupId] =
                std::move(batch);
        }
    }

}

// ============================================================================
// EnsureGroupJoinQueued
// ============================================================================

// Ensure a bot_group_join_batch is queued for an
// LFG group where OnAddMember never fired.  Called
// from OnPlayerMapChanged when a bot enters a
// dungeon instance.  Thread-safe: acquires
// _groupJoinBatchMutex.
void EnsureGroupJoinQueued(
    Player* bot, Group* group)
{
    if (!bot || !group)
        return;

    uint32 botGuid =
        bot->GetGUID().GetCounter();
    uint32 groupId =
        group->GetGUID().GetCounter();

    // Quick check under mutex: skip if this bot
    // was already greeted, batch already flushed,
    // or bot already in an existing batch
    {
        std::lock_guard<std::mutex> guard(
            _groupJoinBatchMutex);

        if (_greetedBotGuids.count(botGuid))
            return;
        if (_groupJoinFlushed.count(groupId))
            return;
        if (_groupJoinBatches.count(groupId))
        {
            // Batch exists (from OnAddMember).
            // Check if this bot is already in it.
            auto& existing =
                _groupJoinBatches[groupId];
            for (auto const& e : existing.bots)
            {
                if (e.botGuid == botGuid)
                    return; // already captured
            }
            // Bot missing from batch — append it.
            GroupJoinEntry entry;
            entry.botGuid = botGuid;
            entry.botName = bot->GetName();
            entry.botClass = bot->getClass();
            entry.botRace = bot->getRace();
            entry.botGender = bot->getGender();
            entry.botLevel = bot->GetLevel();
            entry.role = "dps";
            PlayerbotAI* ai =
                GET_PLAYERBOT_AI(bot);
            if (ai)
            {
                if (PlayerbotAI::IsTank(bot))
                    entry.role = "tank";
                else if (
                    PlayerbotAI::IsHeal(bot))
                    entry.role = "healer";
                else if (
                    PlayerbotAI::IsRanged(bot))
                    entry.role = "ranged_dps";
                else
                    entry.role = "melee_dps";
            }
            existing.bots.push_back(
                std::move(entry));
            return;
        }
    }

    // Gather info for ALL bots in the group
    std::string playerName;
    Player* realPlayer = nullptr;
    uint32 realPlayerZone = 0;
    uint32 realPlayerMap = 0;
    std::vector<GroupJoinEntry> botEntries;

    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (!member)
            continue;

        if (!IsPlayerBot(member))
        {
            if (!realPlayer)
            {
                realPlayer = member;
                playerName = member->GetName();
                realPlayerZone =
                    member->GetZoneId();
                realPlayerMap =
                    member->GetMapId();
            }
            continue;
        }

        GroupJoinEntry entry;
        entry.botGuid =
            member->GetGUID().GetCounter();
        entry.botName = member->GetName();
        entry.botClass = member->getClass();
        entry.botRace = member->getRace();
        entry.botGender = member->getGender();
        entry.botLevel = member->GetLevel();

        entry.role = "dps";
        PlayerbotAI* ai =
            GET_PLAYERBOT_AI(member);
        if (ai)
        {
            if (PlayerbotAI::IsTank(member))
                entry.role = "tank";
            else if (PlayerbotAI::IsHeal(member))
                entry.role = "healer";
            else if (PlayerbotAI::IsRanged(member))
                entry.role = "ranged_dps";
            else
                entry.role = "melee_dps";
        }

        botEntries.push_back(std::move(entry));
    }

    if (botEntries.empty() || playerName.empty())
        return;

    // Build batch with lastJoinTime=0 so it
    // flushes on the very next OnUpdate tick
    GroupJoinBatch batch;
    batch.groupId = groupId;
    batch.playerName = playerName;
    // For instances, use MapEntry::linked_zone
    // (always correct from DBC). Bot/player
    // GetZoneId() is unreliable during teleport
    // since bots lack a real client and the real
    // player's zone hasn't updated yet.
    uint32 batchMapId = bot->GetMapId();
    uint32 batchZoneId = bot->GetZoneId();
    {
        MapEntry const* mapEntry =
            sMapStore.LookupEntry(batchMapId);
        if (mapEntry && mapEntry->linked_zone)
            batchZoneId = mapEntry->linked_zone;
        else if (realPlayerZone
                 && realPlayerZone < 10000)
            batchZoneId = realPlayerZone;
        // Guard: WotLK zone IDs are all < 10000.
        // Anything larger is uninitialized memory.
        if (batchZoneId > 10000)
            batchZoneId = 0;
    }
    batch.zoneId = batchZoneId;
    batch.areaId = realPlayer
        ? realPlayer->GetAreaId() : 0;
    batch.mapId = batchMapId;
    batch.lastJoinTime = 0;
    batch.bots = std::move(botEntries);

    size_t botCount = batch.bots.size();

    {
        std::lock_guard<std::mutex> guard(
            _groupJoinBatchMutex);

        // Re-check under lock (another thread
        // may have raced us)
        if (_groupJoinFlushed.count(groupId))
            return;
        if (_groupJoinBatches.count(groupId))
        {
            // Race: batch appeared while we were
            // gathering. Append any missing bots.
            auto& existing =
                _groupJoinBatches[groupId];
            for (auto& b : batch.bots)
            {
                bool found = false;
                for (auto const& e
                     : existing.bots)
                {
                    if (e.botGuid == b.botGuid)
                    {
                        found = true;
                        break;
                    }
                }
                if (!found)
                    existing.bots.push_back(
                        std::move(b));
            }
            return;
        }

        _groupJoinBatches[groupId] =
            std::move(batch);
    }

}

// ============================================================================
// FlushGroupJoinBatches
// ============================================================================

// Flush accumulated group join batches that have
// passed the debounce window.  Called from OnUpdate.
void FlushGroupJoinBatches()
{
    std::vector<GroupJoinBatch> ready;
    {
        std::lock_guard<std::mutex> guard(
            _groupJoinBatchMutex);

        if (_groupJoinBatches.empty())
            return;

        time_t now = time(nullptr);
        uint32 window = sLLMChatterConfig
            ->_groupJoinDebounceSec;

        std::vector<uint32> flushed;

        for (auto& kv : _groupJoinBatches)
        {
            if (now - kv.second.lastJoinTime
                < (time_t)window)
                continue;

            flushed.push_back(kv.first);
            // Record greeted bot GUIDs before
            // moving the batch into ready.
            for (auto& e : kv.second.bots)
            {
                _greetedBotGuids.insert(
                    e.botGuid);
                _groupGreetedBots[kv.first]
                    .push_back(e.botGuid);
            }
            ready.push_back(
                std::move(kv.second));
        }

        for (uint32 gid : flushed)
        {
            _groupJoinBatches.erase(gid);
            _groupJoinFlushed.insert(gid);
        }
    }
    // Mutex released — safe to do DB writes

    for (auto& b : ready)
    {
        // Suppress join greetings in raid/BG
        // (10-40 bots would flood chat)
        Player* firstBot =
            ObjectAccessor::FindPlayer(
                ObjectGuid::Create<HighGuid::Player>(
                    b.bots[0].botGuid));
        if (firstBot)
        {
            Map* jMap = firstBot->GetMap();
            if (jMap && jMap->IsBattleground())
            {
                continue;
            }
        }

        if (b.bots.size() == 1)
        {
            // Single bot → existing individual
            // event (Python handler unchanged)
            auto& e = b.bots[0];

            std::string extraData = "{"
                "\"bot_guid\":" +
                    std::to_string(e.botGuid) + ","
                "\"bot_name\":\"" +
                    JsonEscape(e.botName) + "\","
                "\"bot_class\":" +
                    std::to_string(e.botClass) + ","
                "\"bot_race\":" +
                    std::to_string(e.botRace) + ","
                "\"bot_gender\":" +
                    std::to_string(e.botGender) + ","
                "\"bot_level\":" +
                    std::to_string(e.botLevel) + ","
                "\"role\":\"" + e.role + "\","
                "\"group_id\":" +
                    std::to_string(b.groupId) + ","
                "\"player_name\":\"" +
                    JsonEscape(b.playerName) + "\","
                "\"group_size\":0,"
                "\"zone\":" +
                    std::to_string(e.zoneId) + ","
                "\"area\":" +
                    std::to_string(b.areaId) + ","
                "\"map\":" +
                    std::to_string(e.mapId) +
                "}";
            extraData = EscapeString(extraData);

            QueueChatterEvent(
                "bot_group_join",
                "player",
                b.zoneId, b.mapId,
                GetChatterEventPriority("bot_group_join"), "",
                e.botGuid, e.botName,
                0, "", 0,
                extraData,
                GetReactionDelaySeconds("bot_group_join"),
                120, false
            );

        }
        else
        {
            // Multiple bots → new batch event
            // Build JSON array of bot entries
            std::string botsJson = "[";
            for (size_t i = 0;
                 i < b.bots.size(); ++i)
            {
                auto& e = b.bots[i];
                if (i > 0) botsJson += ",";
                botsJson += "{"
                    "\"bot_guid\":" +
                        std::to_string(
                            e.botGuid) + ","
                    "\"bot_name\":\"" +
                        JsonEscape(e.botName)
                        + "\","
                    "\"bot_class\":" +
                        std::to_string(
                            e.botClass) + ","
                    "\"bot_race\":" +
                        std::to_string(
                            e.botRace) + ","
                    "\"bot_gender\":" +
                        std::to_string(
                            e.botGender) + ","
                    "\"bot_level\":" +
                        std::to_string(
                            e.botLevel) + ","
                    "\"role\":\"" + e.role +
                        "\","
                    "\"zone\":" +
                        std::to_string(
                            e.zoneId
                                ? e.zoneId
                                : b.zoneId) + ","
                    "\"map\":" +
                        std::to_string(
                            e.mapId
                                ? e.mapId
                                : b.mapId) +
                    "}";
            }
            botsJson += "]";

            std::string extraData = "{"
                "\"group_id\":" +
                    std::to_string(b.groupId) + ","
                "\"player_name\":\"" +
                    JsonEscape(b.playerName)
                    + "\","
                "\"zone\":" +
                    std::to_string(b.zoneId) + ","
                "\"area\":" +
                    std::to_string(b.areaId) + ","
                "\"map\":" +
                    std::to_string(b.mapId) + ","
                "\"bots\":" + botsJson +
                "}";
            extraData = EscapeString(extraData);

            // Use first bot as the subject
            QueueChatterEvent(
                "bot_group_join_batch",
                "player",
                b.zoneId, b.mapId,
                GetChatterEventPriority(
                    "bot_group_join_batch"), "",
                b.bots[0].botGuid,
                b.bots[0].botName,
                0, "", 0,
                extraData,
                GetReactionDelaySeconds(
                    "bot_group_join_batch"),
                120, false
            );

        }
    }
}

// ============================================================================
// LLMChatterGroupScript (GroupScript)
// ============================================================================

class LLMChatterGroupScript : public GroupScript
{
public:
    LLMChatterGroupScript()
        : GroupScript(
              "LLMChatterGroupScript",
              {GROUPHOOK_ON_ADD_MEMBER,
               GROUPHOOK_ON_REMOVE_MEMBER,
               GROUPHOOK_ON_DISBAND}) {}

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

        // Suppress greetings in raid/BG context
        // (10-40 bots would flood chat)
        Map* map = player->GetMap();
        if (map
            && (map->IsRaid()
                || map->IsBattleground()))
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
            uint32 botGuid =
                guid.GetCounter();

            // Cache cleanup uses only guid —
            // safe even if Player* is gone
            CharacterDatabase.Execute(
                "DELETE FROM "
                "llm_group_cached_responses "
                "WHERE group_id = {} "
                "AND bot_guid = {}",
                groupId, botGuid);

            // Cancel pending queue entries that
            // include this bot
            CharacterDatabase.Execute(
                "UPDATE llm_chatter_queue "
                "SET status = 'cancelled' "
                "WHERE status = 'pending' "
                "AND (bot1_guid = {} "
                "OR bot2_guid = {} "
                "OR bot3_guid = {} "
                "OR bot4_guid = {})",
                botGuid, botGuid,
                botGuid, botGuid);

            // Mark this bot's undelivered messages
            // as delivered so they won't fire
            CharacterDatabase.Execute(
                "UPDATE llm_chatter_messages "
                "SET delivered = 1 "
                "WHERE delivered = 0 "
                "AND bot_guid = {}",
                botGuid);

            Player* removed =
                ObjectAccessor::FindPlayer(guid);
            if (removed && IsPlayerBot(removed))
            {
                // Send farewell message before cleanup
                // (suppress in raid/BG — too frequent)
                Map* rMap = removed->GetMap();
                if (sLLMChatterConfig->_useFarewell
                    && !(rMap
                         && (rMap->IsRaid()
                             || rMap->IsBattleground())))
                {
                QueryResult farewell =
                    CharacterDatabase.Query(
                        "SELECT farewell_msg "
                        "FROM llm_group_bot_traits "
                        "WHERE group_id = {} "
                        "AND bot_guid = {}",
                        groupId, botGuid);
                if (farewell)
                {
                    std::string farewellMsg =
                        farewell->Fetch()[0]
                            .Get<std::string>();
                    if (!farewellMsg.empty())
                    {
                        // Build party chat packet
                        // from leaving bot
                        WorldPacket data;
                        ChatHandler::BuildChatPacket(
                            data,
                            CHAT_MSG_PARTY,
                            LANG_UNIVERSAL,
                            removed,
                            nullptr,
                            farewellMsg);

                        // Send to remaining members
                        for (GroupReference* itr =
                                 group->GetFirstMember();
                             itr != nullptr;
                             itr = itr->next())
                        {
                            Player* member =
                                itr->GetSource();
                            if (member
                                && member != removed
                                && member->GetSession())
                            {
                                member
                                    ->GetSession()
                                    ->SendPacket(
                                        &data);
                            }
                        }
                    }
                }
                } // _useFarewell

                // Emit farewell event so the Python
                // bridge can flush session memories
                // before the bot's data is cleaned up.
                {
                    uint32 playerGuid = 0;
                    for (GroupReference* itr =
                             group->GetFirstMember();
                         itr != nullptr;
                         itr = itr->next())
                    {
                        Player* m = itr->GetSource();
                        if (m && !IsPlayerBot(m))
                        {
                            playerGuid =
                                m->GetGUID()
                                    .GetCounter();
                            break;
                        }
                    }
                    if (playerGuid)
                    {
                        std::string extraData = "{"
                            "\"bot_guid\":" +
                                std::to_string(
                                    botGuid) + ","
                            "\"group_id\":" +
                                std::to_string(
                                    groupId) + ","
                            "\"player_guid\":" +
                                std::to_string(
                                    playerGuid) +
                            "}";
                        extraData =
                            EscapeString(extraData);

                        QueueChatterEvent(
                            "bot_group_farewell",
                            "player",
                            removed->GetZoneId(),
                            removed->GetMapId(),
                            GetChatterEventPriority(
                                "bot_group_farewell"),
                            "",
                            botGuid,
                            removed->GetName(),
                            0, "", 0,
                            extraData,
                            0,
                            60,
                            false);
                    }
                }

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
                // Clear state callout cooldowns
                _botLowHealthCooldowns
                    .erase(botGuid);
                _botOomCooldowns
                    .erase(botGuid);
                _botAggroCooldowns
                    .erase(botGuid);

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
// Registration helper called from AddLLMChatterGroupScripts()
// ============================================================================
void AddLLMChatterGroupJoinScripts()
{
    new LLMChatterGroupScript();
}
