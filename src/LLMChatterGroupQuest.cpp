/*
 * mod-llm-chatter - group quest domain
 *
 * Owns:
 *   - FlushQuestAcceptBatches()
 *   - LLMChatterCreatureScript (AllCreatureScript)
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "DatabaseEnv.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Playerbots.h"
#include "ScriptMgr.h"

#include <mutex>
#include <string>
#include <vector>

// ============================================================================
// FlushQuestAcceptBatches
// ============================================================================

// Flush accumulated quest accept batches that have
// passed the debounce window.  Called from OnUpdate.
void FlushQuestAcceptBatches()
{
    // Extract ready batches under the mutex,
    // then release it before doing DB work.
    std::vector<QuestAcceptBatch> ready;
    {
        std::lock_guard<std::mutex> guard(
            _questBatchMutex);

        if (_questAcceptBatches.empty())
            return;

        time_t now = time(nullptr);
        uint32 window = sLLMChatterConfig
            ->_groupQuestAcceptDebounceSec;

        std::vector<uint32> flushed;

        for (auto& kv : _questAcceptBatches)
        {
            if (now - kv.second.lastAcceptTime
                < (time_t)window)
                continue;

            flushed.push_back(kv.first);
            ready.push_back(
                std::move(kv.second));
        }

        for (uint32 gid : flushed)
            _questAcceptBatches.erase(gid);
    }
    // Mutex released — safe to do DB writes

    for (auto& b : ready)
    {
        // Suppress quest accept in raid/BG
        Player* qaBot =
            ObjectAccessor::FindPlayer(
                ObjectGuid::Create<HighGuid::Player>(
                    b.reactorGuid));
        if (qaBot)
        {
            Map* qaMap = qaBot->GetMap();
            if (qaMap && qaMap->IsBattleground())
                continue;
        }

        if (b.quests.size() == 1)
        {
            // Single quest → existing individual
            // event (same as non-debounce path)
            auto& q = b.quests[0];

            std::string extraData = "{"
                "\"bot_guid\":" +
                    std::to_string(
                        b.reactorGuid) + ","
                "\"bot_name\":\"" +
                    JsonEscape(b.reactorName)
                    + "\","
                "\"bot_class\":" +
                    std::to_string(
                        b.reactorClass) + ","
                "\"bot_race\":" +
                    std::to_string(
                        b.reactorRace) + ","
                "\"bot_level\":" +
                    std::to_string(
                        b.reactorLevel) + ","
                "\"is_bot\":1,"
                "\"acceptor_is_bot\":0,"
                "\"acceptor_name\":\"" +
                    JsonEscape(b.acceptorName)
                    + "\","
                "\"quest_name\":\"" +
                    JsonEscape(q.questName)
                    + "\","
                "\"quest_id\":" +
                    std::to_string(q.questId)
                    + ","
                "\"quest_level\":" +
                    std::to_string(q.questLevel)
                    + ","
                "\"zone_name\":\"" +
                    JsonEscape(b.zoneName)
                    + "\","
                "\"quest_details\":\"" +
                    JsonEscape(
                        b.firstQuestDetails)
                    + "\","
                "\"quest_objectives\":\"" +
                    JsonEscape(
                        b.firstQuestObjectives)
                    + "\","
                "\"group_id\":" +
                    std::to_string(b.groupId) +
                "}";
            extraData = EscapeString(extraData);

            std::string cooldownKey =
                "quest_accept:" +
                std::to_string(b.groupId) + ":" +
                std::to_string(q.questId);

            uint32 delay =
                GetReactionDelaySeconds(
                    "bot_group_quest_accept");
            QueueChatterEvent(
                "bot_group_quest_accept",
                "player",
                b.zoneId, b.mapId,
                GetChatterEventPriority(
                    "bot_group_quest_accept"),
                cooldownKey,
                b.reactorGuid,
                b.reactorName,
                0,
                q.questName,
                q.questId,
                extraData,
                delay,
                delay + 120,
                false
            );

        }
        else
        {
            // Multiple quests → batch event
            std::string questNamesArr = "[";
            for (size_t i = 0;
                i < b.quests.size(); ++i)
            {
                if (i > 0) questNamesArr += ",";
                questNamesArr +=
                    "\"" +
                    JsonEscape(
                        b.quests[i].questName) +
                    "\"";
            }
            questNamesArr += "]";

            uint32 firstQuestId =
                b.quests[0].questId;
            std::string firstQuestName =
                b.quests[0].questName;

            std::string extraData = "{"
                "\"bot_guid\":" +
                    std::to_string(
                        b.reactorGuid) + ","
                "\"bot_name\":\"" +
                    JsonEscape(b.reactorName)
                    + "\","
                "\"bot_class\":" +
                    std::to_string(
                        b.reactorClass) + ","
                "\"bot_race\":" +
                    std::to_string(
                        b.reactorRace) + ","
                "\"bot_level\":" +
                    std::to_string(
                        b.reactorLevel) + ","
                "\"is_bot\":1,"
                "\"acceptor_is_bot\":0,"
                "\"acceptor_name\":\"" +
                    JsonEscape(b.acceptorName)
                    + "\","
                "\"quest_names\":" +
                    questNamesArr + ","
                "\"quest_count\":" +
                    std::to_string(
                        b.quests.size()) + ","
                "\"zone_name\":\"" +
                    JsonEscape(b.zoneName)
                    + "\","
                "\"group_id\":" +
                    std::to_string(b.groupId) +
                "}";
            extraData = EscapeString(extraData);

            std::string cooldownKey =
                "quest_accept_batch:" +
                std::to_string(b.groupId);

            uint32 delay =
                GetReactionDelaySeconds(
                    "bot_group_quest_accept_batch"
                );
            QueueChatterEvent(
                "bot_group_quest_accept_batch",
                "player",
                b.zoneId, b.mapId,
                GetChatterEventPriority(
                    "bot_group_quest_accept_batch"),
                cooldownKey,
                b.reactorGuid,
                b.reactorName,
                0,
                firstQuestName,
                firstQuestId,
                extraData,
                delay,
                delay + 120,
                false
            );

        }
    }
}

// ============================================================================
// LLMChatterCreatureScript (AllCreatureScript)
// ============================================================================

class LLMChatterCreatureScript
    : public AllCreatureScript
{
public:
    LLMChatterCreatureScript()
        // AllCreatureScript only exposes the
        // name-based ScriptRegistry constructor in
        // AzerothCore, so there is no enabled-hooks
        // overload to narrow here.
        : AllCreatureScript(
              "LLMChatterCreatureScript") {}

    bool CanCreatureQuestAccept(
        Player* player,
        Creature* /*creature*/,
        Quest const* quest) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_useEventSystem
            || !sLLMChatterConfig->_useGroupChatter)
            return false;

        if (!player || !quest)
            return false;

        // Player-centric: only react to the real
        // player accepting quests
        if (IsPlayerBot(player))
            return false;

        Group* group = player->GetGroup();
        if (!group)
            return false;

        if (!GroupHasRealPlayer(group))
            return false;

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 questId = quest->GetQuestId();

        // Per-group+quest dedup (same quest)
        uint64 questKey =
            ((uint64)groupId << 32) | questId;
        time_t now = time(nullptr);
        auto cdIt =
            _questAcceptTimestamps.find(questKey);
        if (cdIt != _questAcceptTimestamps.end()
            && (now - cdIt->second)
               < (time_t)sLLMChatterConfig
                   ->_groupQuestAcceptCooldown)
        {
            return false;
        }

        // RNG chance gate (roll once per quest)
        if (urand(1, 100) >
            sLLMChatterConfig
                ->_groupQuestAcceptChance)
            return false;

        // Debounce disabled (0) → queue directly
        uint32 debounceSec =
            sLLMChatterConfig
                ->_groupQuestAcceptDebounceSec;
        if (debounceSec == 0)
        {
            // Immediate path (no batching)
            Player* reactor =
                GetRandomBotInGroup(group);
            if (!reactor)
                return false;

            _questAcceptTimestamps[questKey] = now;

            uint32 botGuid =
                reactor->GetGUID().GetCounter();
            std::string botName =
                reactor->GetName();
            std::string playerName =
                player->GetName();
            std::string questName =
                quest->GetTitle();
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
                "\"is_bot\":1,"
                "\"acceptor_is_bot\":" +
                    std::string(
                        IsPlayerBot(player)
                            ? "1" : "0") + ","
                "\"acceptor_name\":\"" +
                    JsonEscape(playerName) + "\","
                "\"quest_name\":\"" +
                    JsonEscape(questName) + "\","
                "\"quest_id\":" +
                    std::to_string(questId) + ","
                "\"quest_level\":" +
                    std::to_string(
                        quest->GetQuestLevel())
                    + ","
                "\"zone_name\":\"" +
                    JsonEscape(zoneName) + "\","
                "\"quest_details\":\"" +
                    JsonEscape(
                        quest->GetDetails()
                            .substr(0, 200))
                    + "\","
                "\"quest_objectives\":\"" +
                    JsonEscape(
                        quest->GetObjectives()
                            .substr(0, 150))
                    + "\","
                "\"group_id\":" +
                    std::to_string(groupId) +
                "}";
            extraData = EscapeString(extraData);

            std::string cooldownKey =
                "quest_accept:" +
                std::to_string(groupId) + ":" +
                std::to_string(questId);

            uint32 delay =
                GetReactionDelaySeconds(
                    "bot_group_quest_accept");
            QueueChatterEvent(
                "bot_group_quest_accept",
                "player",
                reactor->GetZoneId(),
                reactor->GetMapId(),
                GetChatterEventPriority(
                    "bot_group_quest_accept"),
                cooldownKey,
                botGuid,
                botName,
                0,
                questName,
                questId,
                extraData,
                delay,
                delay + 120,
                false
            );

            return false;
        }

        // --- Debounce path: accumulate into batch ---
        // Gather all data from game objects BEFORE
        // acquiring the mutex to minimize hold time.
        std::string questName = quest->GetTitle();
        int32 questLevel = quest->GetQuestLevel();
        std::string questDetails =
            quest->GetDetails().substr(0, 200);
        std::string questObjectives =
            quest->GetObjectives().substr(0, 150);
        std::string playerName = player->GetName();

        // Pre-select reactor outside lock (only
        // needed for the new-batch path; wasted if
        // we append, but avoids holding mutex
        // during GetRandomBotInGroup).
        Player* reactor =
            GetRandomBotInGroup(group);

        // Capture reactor data outside lock
        uint32 rGuid = 0;
        std::string rName;
        uint8 rClass = 0, rRace = 0;
        uint32 rLevel = 0;
        uint32 pZoneId = player->GetZoneId();
        std::string pZoneName =
            GetZoneName(pZoneId);
        uint32 pMapId = player->GetMapId();

        if (reactor)
        {
            rGuid =
                reactor->GetGUID().GetCounter();
            rName = reactor->GetName();
            rClass = reactor->getClass();
            rRace = reactor->getRace();
            rLevel = reactor->GetLevel();
        }

        {
            std::lock_guard<std::mutex> batchGuard(
                _questBatchMutex);

            auto batchIt =
                _questAcceptBatches.find(groupId);

            if (batchIt !=
                _questAcceptBatches.end())
            {
                // Append to existing batch
                _questAcceptTimestamps[questKey] =
                    now;
                batchIt->second.quests.push_back(
                    { questId, questName,
                      questLevel });
                batchIt->second.lastAcceptTime =
                    now;
                // Track latest acceptor for
                // multi-player groups
                if (batchIt->second.acceptorName
                    != playerName)
                {
                    batchIt->second.acceptorName =
                        playerName;
                }
                return false;
            }

            // First quest in a new batch
            if (!reactor)
                return false;

            _questAcceptTimestamps[questKey] = now;

            QuestAcceptBatch batch;
            batch.reactorGuid = rGuid;
            batch.reactorName = rName;
            batch.reactorClass = rClass;
            batch.reactorRace = rRace;
            batch.reactorLevel = rLevel;
            batch.acceptorName = playerName;
            batch.zoneId = pZoneId;
            batch.zoneName = pZoneName;
            batch.mapId = pMapId;
            batch.groupId = groupId;
            batch.lastAcceptTime = now;
            batch.quests.push_back(
                { questId, questName,
                  questLevel });
            batch.firstQuestDetails =
                questDetails;
            batch.firstQuestObjectives =
                questObjectives;

            _questAcceptBatches[groupId] =
                std::move(batch);
        }
        // Mutex released

        // Return false = don't block quest accept
        return false;
    }
};

// ============================================================================
// Registration helper called from AddLLMChatterGroupScripts()
// ============================================================================
void AddLLMChatterGroupQuestScripts()
{
    new LLMChatterCreatureScript();
}
