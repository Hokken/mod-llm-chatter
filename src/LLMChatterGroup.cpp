/*
 * mod-llm-chatter - group subsystem ownership
 */

#include "LLMChatterConfig.h"
#include "LLMChatterBG.h"
#include "LLMChatterGroup.h"
#include "LLMChatterShared.h"

#include "AchievementMgr.h"
#include "Battleground.h"
#include "CellImpl.h"
#include "Chat.h"
#include "Channel.h"
#include "ChannelMgr.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "Log.h"
#include "MapMgr.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <cctype>
#include <ctime>
#include <map>
#include <mutex>
#include <random>
#include <regex>
#include <set>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

// ============================================================================
// PRE-CACHE INSTANT REACTION HELPERS
// ============================================================================

// Consume one cached response for a bot+category.
// Returns true on hit, populating outMessage/outEmote.
// Uses DirectExecute (sync) for UPDATE to prevent
// double-consume if two hooks fire same tick.
static bool TryConsumeCachedReaction(
    uint32 groupId, uint32 botGuid,
    const std::string& category,
    std::string& outMessage,
    std::string& outEmote)
{
    QueryResult result = CharacterDatabase.Query(
        "SELECT id, message, emote "
        "FROM llm_group_cached_responses "
        "WHERE group_id = {} AND bot_guid = {} "
        "AND event_category = '{}' "
        "AND status = 'ready' "
        "AND (expires_at IS NULL "
        "     OR expires_at > NOW()) "
        "ORDER BY created_at ASC LIMIT 1",
        groupId, botGuid,
        category);

    if (!result)
        return false;

    Field* fields = result->Fetch();
    uint32 cachedId = fields[0].Get<uint32>();
    outMessage = fields[1].Get<std::string>();
    outEmote = fields[2].IsNull()
        ? "" : fields[2].Get<std::string>();

    // Sync UPDATE prevents double-consume
    CharacterDatabase.DirectExecute(
        "UPDATE llm_group_cached_responses "
        "SET status = 'used', used_at = NOW() "
        "WHERE id = {}",
        cachedId);

    return true;
}

// Replace {target}, {caster}, {spell} placeholders
// with actual names from hook data. Strip unresolved
// tokens and clamp length.
static void ResolvePlaceholders(
    std::string& message,
    const std::string& target,
    const std::string& caster,
    const std::string& spell)
{
    std::string safeTarget =
        target.empty() ? "" : target;
    std::string safeCaster =
        caster.empty() ? "" : caster;
    std::string safeSpell =
        spell.empty() ? "" : spell;

    size_t pos;
    while ((pos = message.find("{target}"))
           != std::string::npos)
        message.replace(pos, 8, safeTarget);
    while ((pos = message.find("{caster}"))
           != std::string::npos)
        message.replace(pos, 8, safeCaster);
    while ((pos = message.find("{spell}"))
           != std::string::npos)
        message.replace(pos, 7, safeSpell);

    // Strip unresolved {tokens} (LLM hallucination)
    std::regex unresolvedRe("\\{[a-zA-Z_]+\\}");
    message = std::regex_replace(
        message, unresolvedRe, "");

    // Clean up punctuation artifacts from
    // empty placeholder replacement
    // ", ," -> ","  and " , " -> " "
    while ((pos = message.find(", ,"))
           != std::string::npos)
        message.replace(pos, 3, ",");
    while ((pos = message.find(" ,"))
           != std::string::npos)
        message.replace(pos, 2, "");
    // ", !" -> "!"  and ", ." -> "."
    while ((pos = message.find(", !"))
           != std::string::npos)
        message.replace(pos, 3, "!");
    while ((pos = message.find(", ."))
           != std::string::npos)
        message.replace(pos, 3, ".");
    // Trailing comma before end of string
    while (!message.empty()
           && (message.back() == ','
               || message.back() == ' '))
        message.pop_back();

    // Collapse double spaces
    while (message.find("  ") != std::string::npos)
    {
        pos = message.find("  ");
        message.replace(pos, 2, " ");
    }

    // Trim leading/trailing whitespace
    while (!message.empty()
           && message.front() == ' ')
        message.erase(0, 1);
    while (!message.empty()
           && message.back() == ' ')
        message.pop_back();

    // Clamp to max message length
    if (message.size()
        > sLLMChatterConfig->_maxMessageLength)
        message.resize(
            sLLMChatterConfig->_maxMessageLength);
}

// Record a pre-cached message in chat history
// so Python sees it for conversation context.
static void RecordCachedChatHistory(
    uint32 groupId, uint32 botGuid,
    const std::string& botName,
    const std::string& message)
{
    CharacterDatabase.Execute(
        "INSERT INTO llm_group_chat_history "
        "(group_id, speaker_guid, speaker_name, "
        "is_bot, message) "
        "VALUES ({}, {}, '{}', 1, '{}')",
        groupId, botGuid,
        EscapeString(botName),
        EscapeString(message));
}

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
            && member != exclude
            && member->IsAlive())
            bots.push_back(member);
    }

    if (bots.empty())
        return nullptr;

    return bots[urand(0, bots.size() - 1)];
}

// Count bots in a group (for dynamic chance scaling)
static uint32 CountBotsInGroup(Group* group)
{
    if (!group)
        return 0;

    uint32 count = 0;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (member && IsPlayerBot(member))
            ++count;
    }
    return count;
}

// ---- Group join batching (debounce) ----

struct GroupJoinEntry {
    uint32 botGuid{0};
    std::string botName;
    uint8 botClass{0};
    uint8 botRace{0};
    uint8 botLevel{0};
    std::string role;
    uint32 zoneId{0};
    uint32 mapId{0};
};

struct GroupJoinBatch {
    uint32 groupId{0};
    std::string playerName;
    uint32 zoneId{0};
    uint32 areaId{0};
    uint32 mapId{0};
    time_t lastJoinTime{0};
    std::vector<GroupJoinEntry> bots;
};

// groupId -> pending batch
static std::unordered_map<uint32, GroupJoinBatch>
    _groupJoinBatches;
// Protects _groupJoinBatches: written from
// OnAddMember (map worker threads),
// read+erased from FlushGroupJoinBatches (main).
static std::mutex _groupJoinBatchMutex;

// Groups that have already had a join batch
// flushed (prevents duplicate queueing for
// LFG groups where OnAddMember never fires).
// Protected by _groupJoinBatchMutex.
static std::unordered_set<uint32>
    _groupJoinFlushed;

// Bot GUIDs that have already been greeted
// (prevents teleport re-trigger from creating
// a second greeting for the same bot).
// Keyed by bot GUID so newly invited bots are
// NOT blocked after the first batch flushes.
// Protected by _groupJoinBatchMutex.
static std::unordered_set<uint32>
    _greetedBotGuids;
// groupId → list of bot GUIDs greeted in that
// session (used to clear _greetedBotGuids on
// CleanupGroupSession).
// Protected by _groupJoinBatchMutex.
static std::unordered_map<uint32,
    std::vector<uint32>> _groupGreetedBots;

// Queue a greeting event for a bot joining a group.
// When debounce > 0, accumulates into a batch so
// rapid invites are processed together with full
// group knowledge.  When debounce == 0, queues
// immediately (legacy behavior).
static void QueueBotGreetingEvent(
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

// Ensure a bot_group_join_batch is queued for an
// LFG group where OnAddMember never fired.  Called
// from OnPlayerMapChanged when a bot enters a
// dungeon instance.  Thread-safe: acquires
// _groupJoinBatchMutex.
static void EnsureGroupJoinQueued(
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

// Named boss entries: creature entries that are
// dungeon/raid bosses (mechanic-immune + single
// spawn per map, OR rank=3). Loaded at startup
// from the world DB.
static std::unordered_set<uint32> _namedBossEntries;

void LoadNamedBossCache()
{
    _namedBossEntries.clear();
    // Named bosses: mechanic_immune_mask > 0 and
    // only 1 spawn on their map (filters out trash
    // like Molten Elementals that have immunities
    // but spawn many times)
    QueryResult result = WorldDatabase.Query(
        "SELECT entry FROM ("
        "  SELECT ct.entry, ct.`rank`,"
        "    ct.mechanic_immune_mask,"
        "    COUNT(*) AS spawns"
        "  FROM creature_template ct"
        "  JOIN creature c ON c.id1 = ct.entry"
        "  WHERE ct.`rank` = 3"
        "    OR ct.mechanic_immune_mask > 0"
        "  GROUP BY ct.entry, c.map"
        "  HAVING ct.`rank` = 3 OR COUNT(*) = 1"
        ") AS bosses");
    if (result)
    {
        do
        {
            Field* fields = result->Fetch();
            _namedBossEntries.insert(
                fields[0].Get<uint32>());
        } while (result->NextRow());
    }
}

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

// Group cooldown maps below, plus
// _questAcceptTimestamps, preserve the pre-split
// threading model from LLMChatterScript.cpp:
// PlayerScript, GroupScript, and CreatureScript
// hook paths mutate them on map update threads,
// and the world flush path does not access them.
// If this module must support cross-map concurrent
// writes under MapUpdate.Threads > 1, these maps
// need explicit synchronization rather than more
// shared callers.

// Per-group+quest accept timestamp:
// (groupId << 32 | questId) -> accept time
// Used to suppress duplicate objectives events
// for travel/breadcrumb quests
static std::unordered_map<uint64, time_t>
    _questAcceptTimestamps;

// Per-group+quest complete dedup:
// (groupId << 32 | questId) -> last complete time
// Prevents duplicate quest_complete events when
// multiple bots complete the same quest at once.
static std::unordered_map<uint64, time_t>
    _questCompleteCd;

// Quest accept batching: accumulate quests accepted
// within a short window and flush as one event.
struct QuestAcceptEntry {
    uint32 questId;
    std::string questName;
    int32 questLevel;
};

// ---- Quest accept batching (debounce) ----

struct QuestAcceptBatch {
    uint32 reactorGuid;
    std::string reactorName;
    uint8 reactorClass;
    uint8 reactorRace;
    uint32 reactorLevel;
    std::string acceptorName;
    uint32 zoneId;
    std::string zoneName;
    uint32 mapId;
    uint32 groupId;
    time_t lastAcceptTime;
    std::vector<QuestAcceptEntry> quests;
    // Store details/objectives for single-quest path
    std::string firstQuestDetails;
    std::string firstQuestObjectives;
};

// groupId -> pending batch
static std::unordered_map<uint32, QuestAcceptBatch>
    _questAcceptBatches;
// Protects _questAcceptBatches: written from
// CanCreatureQuestAccept (map worker threads),
// read+erased from FlushQuestAcceptBatches (main).
static std::mutex _questBatchMutex;

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


// Per-bot state callout cooldowns:
// bot_guid -> last callout time
static std::map<uint32, time_t>
    _botLowHealthCooldowns;
static std::map<uint32, time_t>
    _botOomCooldowns;
static std::map<uint32, time_t>
    _botAggroCooldowns;

// Pre-enqueue filter for known playerbot control
// messages. Keep this aligned with the Python-side
// PLAYERBOT_COMMANDS fallback list so command
// traffic does not enter the chatter event queue.
static bool IsLikelyPlayerbotControlCommand(
    std::string const& message)
{
    auto trim = [](std::string const& input)
    {
        size_t start =
            input.find_first_not_of(" \t\n\r");
        if (start == std::string::npos)
            return std::string();

        size_t end =
            input.find_last_not_of(" \t\n\r");
        return input.substr(start, end - start + 1);
    };

    auto toLowerAscii = [](std::string value)
    {
        std::transform(value.begin(), value.end(),
            value.begin(),
            [](unsigned char c)
            {
                return static_cast<char>(
                    std::tolower(c));
            });
        return value;
    };

    std::string msg = toLowerAscii(trim(message));
    if (msg.empty())
        return false;

    static std::unordered_set<std::string>
        exactCommands = {
            "u", "c", "e", "s", "b", "r", "t",
            "q", "ll", "ss", "co", "nc", "de",
            "ra", "gb", "nt", "qi",
            "follow", "stay", "flee",
            "runaway", "warning", "grind",
            "go", "home", "disperse",
            "move from group", "attack",
            "max dps", "tank attack",
            "pet attack", "do attack my target",
            "use", "items", "inventory", "inv",
            "equip", "unequip", "sell", "buy",
            "open items", "unlock items",
            "unlock traded item", "loot all",
            "add all loot", "destroy", "quests",
            "accept", "drop", "reward", "share",
            "rpg status", "rpg do quest",
            "query item usage", "cast",
            "castnc", "spell", "buff", "glyphs",
            "glyph equip", "remove glyph", "pet",
            "tame", "trainer", "talent",
            "talents", "spells", "trade",
            "nontrade", "craft", "flag", "mail",
            "sendmail", "bank", "gbank", "talk",
            "emote", "enter vehicle",
            "leave vehicle", "stats",
            "reputation", "rep", "pvp stats",
            "dps", "who", "position", "aura",
            "attackers", "target", "help", "log",
            "los", "ready", "ready check",
            "leave", "invite", "summon",
            "formation", "stance",
            "give leader", "wipe", "roll",
            "repair", "maintenance", "release",
            "revive", "autogear",
            "equip upgrade", "save mana",
            "reset botai", "teleport", "taxi",
            "outline", "rti", "range", "wts",
            "cs", "cdebug", "debug", "cheat",
            "calc", "drink", "honor",
            "outdoors", "ginvite",
            "guild promote", "guild demote",
            "guild remove", "guild leave", "lfg",
            "chat", "loot"
        };

    if (exactCommands.find(msg)
        != exactCommands.end())
        return true;

    size_t firstSpace = msg.find(' ');
    if (firstSpace != std::string::npos)
    {
        std::string firstWord =
            msg.substr(0, firstSpace);
        if (exactCommands.find(firstWord)
            != exactCommands.end())
            return true;
    }

    for (std::string const& command
         : exactCommands)
    {
        if (command.find(' ') == std::string::npos)
            continue;

        if (msg.rfind(command, 0) == 0)
            return true;
    }

    return false;
}

// Per-group emote observer cooldown
// (PlayerScript-only access -- no mutex needed)
static std::unordered_map<uint32, time_t>
    _emoteObserverCooldowns;

// Clean up traits when group no longer qualifies
static void CleanupGroupSession(uint32 groupId)
{
    // Cancel pending queue entries for all bots
    // that belonged to this group
    CharacterDatabase.Execute(
        "UPDATE llm_chatter_queue "
        "SET status = 'cancelled' "
        "WHERE status = 'pending' "
        "AND ("
        "bot1_guid IN (SELECT bot_guid "
        "FROM llm_group_bot_traits "
        "WHERE group_id = {0}) "
        "OR bot2_guid IN (SELECT bot_guid "
        "FROM llm_group_bot_traits "
        "WHERE group_id = {0}) "
        "OR bot3_guid IN (SELECT bot_guid "
        "FROM llm_group_bot_traits "
        "WHERE group_id = {0}) "
        "OR bot4_guid IN (SELECT bot_guid "
        "FROM llm_group_bot_traits "
        "WHERE group_id = {0})"
        ")",
        groupId);

    // Mark undelivered messages for all group
    // bots as delivered
    CharacterDatabase.Execute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 1 "
        "WHERE delivered = 0 "
        "AND bot_guid IN ("
        "SELECT bot_guid "
        "FROM llm_group_bot_traits "
        "WHERE group_id = {})",
        groupId);

    CharacterDatabase.Execute(
        "DELETE FROM llm_group_bot_traits "
        "WHERE group_id = {}",
        groupId);
    CharacterDatabase.Execute(
        "DELETE FROM llm_group_chat_history "
        "WHERE group_id = {}",
        groupId);
    CharacterDatabase.Execute(
        "DELETE FROM llm_group_cached_responses "
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
    _emoteObserverCooldowns.erase(groupId);

    // Prune combined-key (groupId<<32|questId) maps
    // unordered_map has no lower_bound — linear scan
    {
        uint64 lo = (uint64)groupId << 32;
        uint64 hi = lo | 0xFFFFFFFFu;
        auto eraseGroupKeys = [lo, hi](auto& m)
        {
            for (auto it = m.begin(); it != m.end(); )
            {
                if (it->first >= lo && it->first <= hi)
                    it = m.erase(it);
                else
                    ++it;
            }
        };
        eraseGroupKeys(_questAcceptTimestamps);
        eraseGroupKeys(_questCompleteCd);
    }

    // Discard any pending join batch and clear
    // the flushed flag for this group
    {
        std::lock_guard<std::mutex> guard(
            _groupJoinBatchMutex);
        _groupJoinBatches.erase(groupId);
        _groupJoinFlushed.erase(groupId);
        auto git = _groupGreetedBots.find(
            groupId);
        if (git != _groupGreetedBots.end())
        {
            for (uint32 bguid : git->second)
                _greetedBotGuids.erase(bguid);
            _groupGreetedBots.erase(git);
        }
    }

    // Discard any pending quest-accept batch for a
    // disbanded group so FlushQuestAcceptBatches
    // cannot emit a stale event after cleanup.
    {
        std::lock_guard<std::mutex> guard(
            _questBatchMutex);
        _questAcceptBatches.erase(groupId);
    }

}

// ── Emote reaction system ──────────────────────────────

/// Fires SendBotTextEmote after a short delay so the
/// mirror emote doesn't look instant/robotic.
class DelayedCreatureMirrorEmoteEvent : public BasicEvent
{
public:
    DelayedCreatureMirrorEmoteEvent(ObjectGuid playerGuid,
                                    ObjectGuid creatureGuid,
                                    uint32 emoteId,
                                    std::string playerName)
        : _playerGuid(playerGuid)
        , _creatureGuid(creatureGuid)
        , _emoteId(emoteId)
        , _playerName(std::move(playerName))
    {}

    bool Execute(uint64 /*time*/,
                 uint32 /*diff*/) override
    {
        Player* player =
            ObjectAccessor::FindConnectedPlayer(
                _playerGuid);
        if (!player || !player->IsInWorld())
            return true;

        Creature* creature =
            player->GetMap()->GetCreature(
                _creatureGuid);
        if (!creature || !creature->IsAlive()
            || creature->IsInCombat())
            return true;

        // Face the player just before animating
        creature->SetFacingToObject(player);
        SendUnitTextEmote(
            creature, _emoteId, _playerName);
        return true;
    }

private:
    ObjectGuid  _playerGuid;
    ObjectGuid  _creatureGuid;
    uint32      _emoteId;
    std::string _playerName;
};

class DelayedMirrorEmoteEvent : public BasicEvent
{
public:
    DelayedMirrorEmoteEvent(ObjectGuid botGuid,
                            ObjectGuid playerGuid,
                            uint32 emoteId,
                            std::string playerName)
        : _botGuid(botGuid)
        , _playerGuid(playerGuid)
        , _emoteId(emoteId)
        , _playerName(std::move(playerName))
    {}

    bool Execute(uint64 /*time*/,
                 uint32 /*diff*/) override
    {
        Player* bot =
            ObjectAccessor::FindConnectedPlayer(
                _botGuid);
        if (!bot || !bot->IsInWorld()
            || !bot->IsAlive())
            return true;

        // Face player just before the animation
        // so the bot hasn't drifted since hook time
        if (sLLMChatterConfig->_facingEnable
            && !bot->IsInCombat())
        {
            Player* target =
                ObjectAccessor::FindConnectedPlayer(
                    _playerGuid);
            if (target)
                bot->SetFacingToObject(target);
        }

        SendBotTextEmote(bot, _emoteId, _playerName);
        return true;
    }

private:
    ObjectGuid  _botGuid;
    ObjectGuid  _playerGuid;
    uint32      _emoteId;
    std::string _playerName;
};

// Emotes that should NOT trigger social reactions.
// All other text emotes are fair game -- even purely
// text-only emotes can generate interesting LLM responses.
// Combat callouts are handled separately by
// s_combatCalloutEmotes.
static const std::unordered_set<uint32>
    s_ignoredEmotes = {
    TEXT_EMOTE_BRB,           // out-of-character meta
    TEXT_EMOTE_MESSAGE,       // system-ish
    TEXT_EMOTE_MOUNT_SPECIAL, // mount ability, not social
    TEXT_EMOTE_STOPATTACK,    // combat directive
};

// Combat callouts excluded from social reactions
static const std::unordered_set<uint32>
    s_combatCalloutEmotes = {
    TEXT_EMOTE_HELPME, TEXT_EMOTE_INCOMING,
    TEXT_EMOTE_CHARGE, TEXT_EMOTE_FLEE,
    TEXT_EMOTE_ATTACKMYTARGET, TEXT_EMOTE_OOM,
    TEXT_EMOTE_FOLLOW, TEXT_EMOTE_WAIT,
    TEXT_EMOTE_HEALME, TEXT_EMOTE_OPENFIRE,
};

// Mirror map: incoming emote ID -> bot response emote ID
static const std::unordered_map<uint32, uint32>
    s_mirrorEmoteMap = {
    {TEXT_EMOTE_WAVE,         TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_HELLO,        TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_GREET,        TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_BYE,          TEXT_EMOTE_BYE},
    {TEXT_EMOTE_WELCOME,      TEXT_EMOTE_NOD},
    {TEXT_EMOTE_BOW,          TEXT_EMOTE_BOW},
    {TEXT_EMOTE_SALUTE,       TEXT_EMOTE_SALUTE},
    {TEXT_EMOTE_CURTSEY,      TEXT_EMOTE_BOW},
    {TEXT_EMOTE_KNEEL,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_NOD,          TEXT_EMOTE_NOD},
    {TEXT_EMOTE_NO,           TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_THANK,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_YW,           TEXT_EMOTE_NOD},
    {TEXT_EMOTE_CHEER,        TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_APPLAUD,      TEXT_EMOTE_APPLAUD},
    {TEXT_EMOTE_CLAP,         TEXT_EMOTE_CLAP},
    {TEXT_EMOTE_VICTORY,      TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_COMMEND,      TEXT_EMOTE_NOD},
    {TEXT_EMOTE_CONGRATULATE, TEXT_EMOTE_APPLAUD},
    {TEXT_EMOTE_TOAST,        TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_FLIRT,        TEXT_EMOTE_SHY},
    {TEXT_EMOTE_KISS,         TEXT_EMOTE_BLUSH},
    {TEXT_EMOTE_LAUGH,        TEXT_EMOTE_LAUGH},
    {TEXT_EMOTE_GIGGLE,       TEXT_EMOTE_GIGGLE},
    {TEXT_EMOTE_ROFL,         TEXT_EMOTE_LAUGH},
    {TEXT_EMOTE_GOLFCLAP,     TEXT_EMOTE_GOLFCLAP},
    {TEXT_EMOTE_JOKE,         TEXT_EMOTE_LAUGH},
    {TEXT_EMOTE_RUDE,         TEXT_EMOTE_CHICKEN},
    {TEXT_EMOTE_CHICKEN,      TEXT_EMOTE_RUDE},
    {TEXT_EMOTE_TAUNT,        TEXT_EMOTE_ROAR},
    {TEXT_EMOTE_INSULT,       TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_BLAME,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_DISAGREE,     TEXT_EMOTE_NO},
    {TEXT_EMOTE_DOUBT,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_CRY,          TEXT_EMOTE_MOURN},
    {TEXT_EMOTE_PLEAD,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_GROVEL,       TEXT_EMOTE_NOD},
    {TEXT_EMOTE_BEG,          TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_SURRENDER,    TEXT_EMOTE_NOD},
    {TEXT_EMOTE_DANCE,        TEXT_EMOTE_DANCE},
    {TEXT_EMOTE_POINT,        TEXT_EMOTE_NOD},
    // affection
    {TEXT_EMOTE_HUG,          TEXT_EMOTE_HUG},
    {TEXT_EMOTE_LOVE,         TEXT_EMOTE_BLUSH},
    {TEXT_EMOTE_PAT,          TEXT_EMOTE_NOD},
    {TEXT_EMOTE_WINK,         TEXT_EMOTE_SHY},
    {TEXT_EMOTE_POKE,         TEXT_EMOTE_SHY},
    {TEXT_EMOTE_TICKLE,       TEXT_EMOTE_GIGGLE},
    {TEXT_EMOTE_CUDDLE,       TEXT_EMOTE_SHY},
    // social / greeting
    {TEXT_EMOTE_SMILE,        TEXT_EMOTE_SMILE},
    {TEXT_EMOTE_AGREE,        TEXT_EMOTE_NOD},
    {TEXT_EMOTE_INTRODUCE,    TEXT_EMOTE_WAVE},
    {TEXT_EMOTE_HIGHFIVE,     TEXT_EMOTE_HIGHFIVE},
    {TEXT_EMOTE_GOODLUCK,     TEXT_EMOTE_NOD},
    // gratitude / encouragement
    {TEXT_EMOTE_APOLOGIZE,    TEXT_EMOTE_NOD},
    {TEXT_EMOTE_PRAISE,       TEXT_EMOTE_APPLAUD},
    {TEXT_EMOTE_ENCOURAGE,    TEXT_EMOTE_CHEER},
    {TEXT_EMOTE_TRUCE,        TEXT_EMOTE_NOD},
    // mockery / provocation responses
    {TEXT_EMOTE_MOCK,         TEXT_EMOTE_RUDE},
    {TEXT_EMOTE_SLAP,         TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_PUNCH,        TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_SPIT,         TEXT_EMOTE_ANGRY},
    {TEXT_EMOTE_POUNCE,       TEXT_EMOTE_ROAR},
    // misc expressive
    {TEXT_EMOTE_PANIC,        TEXT_EMOTE_CONFUSED},
    {TEXT_EMOTE_FACEPALM,     TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_ROLLEYES,     TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_FROWN,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_SHRUG,        TEXT_EMOTE_SHRUG},
    {TEXT_EMOTE_THINK,        TEXT_EMOTE_PONDER},
};

// Contagious emotes -- secondary bots may join in
// (mood spread, Phase 6)
static const std::unordered_set<uint32>
    s_contagiousEmotes = {
    TEXT_EMOTE_DANCE, TEXT_EMOTE_CHEER,
    TEXT_EMOTE_LAUGH, TEXT_EMOTE_APPLAUD,
    TEXT_EMOTE_ROFL, TEXT_EMOTE_VICTORY,
};

// Target type enum (file-scope for helper methods)
enum EmoteTargetType
{
    EMOTE_TGT_NONE,
    EMOTE_TGT_GROUP_BOT,
    EMOTE_TGT_GROUP_PLAYER,
    EMOTE_TGT_EXT_PLAYER,
    EMOTE_TGT_CREATURE,
};

// Per-bot mirror cooldown
// (PlayerScript-only access -- no mutex needed)
static std::unordered_map<uint32, time_t>
    _emoteReactCooldowns;
// Per-group observer cooldown -- declared earlier
// (before CleanupGroupSession)
// Per-bot verbal reaction cooldown
// (PlayerScript-only access -- no mutex)
static std::unordered_map<uint32, time_t>
    _emoteVerbalCooldowns;
// Per-creature mirror cooldown
// (PlayerScript-only access -- no mutex)
static std::unordered_map<uint32, time_t>
    _creatureEmoteCooldowns;

// ── End emote reaction system statics ──────────────────

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

class LLMChatterGroupPlayerScript : public PlayerScript
{
public:
    LLMChatterGroupPlayerScript()
        : PlayerScript(
              "LLMChatterGroupPlayerScript",
              {PLAYERHOOK_CAN_PLAYER_USE_GROUP_CHAT,
               PLAYERHOOK_ON_CREATURE_KILL,
               PLAYERHOOK_ON_PLAYER_KILLED_BY_CREATURE,
               PLAYERHOOK_ON_LOOT_ITEM,
               PLAYERHOOK_ON_GROUP_ROLL_REWARD_ITEM,
               PLAYERHOOK_ON_PLAYER_ENTER_COMBAT,
               PLAYERHOOK_ON_BEFORE_SEND_CHAT_MESSAGE,
               PLAYERHOOK_ON_LEVEL_CHANGED,
               PLAYERHOOK_ON_BEFORE_QUEST_COMPLETE,
               PLAYERHOOK_ON_PLAYER_COMPLETE_QUEST,
               PLAYERHOOK_ON_ACHI_COMPLETE,
               PLAYERHOOK_ON_SPELL_CAST,
               PLAYERHOOK_ON_PLAYER_RESURRECT,
               PLAYERHOOK_ON_PLAYER_RELEASED_GHOST,
               PLAYERHOOK_ON_MAP_CHANGED,

               PLAYERHOOK_ON_TEXT_EMOTE}) {}

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

        // Suppress creature kills in BGs
        // (PvP kills handled by OnPVPKill)
        if (killer->InBattleground())
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
        // Named dungeon bosses (Taragaman, etc.)
        // often lack rank=3 but have mechanic
        // immunities + single spawn per map.
        // _namedBossEntries is loaded at startup.
        bool isBoss = (rank == 3)
            || (tmpl->type_flags
                & CREATURE_TYPE_FLAG_BOSS_MOB)
            || killed->IsDungeonBoss()
            || _namedBossEntries.count(
                killed->GetEntry());
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

        // Build JSON payload. SQL escaping happens
        // below via EscapeString(extraData).
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
                std::to_string(groupId) + ","
            + BuildBotStateJson(reactor) + "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_kill",
            "player",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            GetChatterEventPriority("bot_group_kill"),
            "",
            botGuid,
            botName,
            0,
            creatureName,
            creatureEntry,
            extraData,
            GetReactionDelaySeconds("bot_group_kill"),
            120,
            false
        );

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

            // Need minimum members for a "wipe"
            if (allDead
                && memberCount
                   >= sLLMChatterConfig
                       ->_wipeMinGroupSize)
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
                            kEntry) + ","
                    + BuildBotStateJson(wipeReactor)
                    + "}";

                wipeData =
                    EscapeString(wipeData);

                QueueChatterEvent(
                    "bot_group_wipe",
                    "player",
                    killed->GetZoneId(),
                    killed->GetMapId(),
                    GetChatterEventPriority(
                        "bot_group_wipe"),
                    "",
                    wrGuid,
                    wrName,
                    0,
                    kName,
                    kEntry,
                    wipeData,
                    GetReactionDelaySeconds(
                        "bot_group_wipe"),
                    120,
                    false
                );

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

        // Pick a living bot to react
        // (exclude dead player)
        Player* reactor = GetRandomBotInGroup(
            group, killed);
        if (!reactor)
            return;

        uint32 reactorGuid =
            reactor->GetGUID().GetCounter();
        std::string reactorName =
            reactor->GetName();

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
                std::to_string(reactorGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(reactorName) + "\","
            "\"bot_class\":" +
                std::to_string(
                    reactor->getClass()) + ","
            "\"bot_race\":" +
                std::to_string(
                    reactor->getRace()) + ","
            "\"bot_level\":" +
                std::to_string(
                    reactor->GetLevel()) + ","
            "\"dead_name\":\"" +
                JsonEscape(deadName) + "\","
            "\"dead_guid\":" +
                std::to_string(deadGuid) + ","
            "\"killer_name\":\"" +
                JsonEscape(killerName) + "\","
            "\"killer_entry\":" +
                std::to_string(killerEntry) + ","
            "\"group_id\":" +
                std::to_string(groupId) + ","
            "\"is_player_death\":" +
                std::string(
                    isPlayerDeath
                        ? "true" : "false") + ","
            + BuildBotStateJson(reactor) + "}";

        // Inject BG context if in a battleground
        if (reactor->InBattleground())
        {
            Battleground* bg =
                reactor->GetBattleground();
            if (bg)
                AppendBGContext(
                    bg, reactor, extraData);
        }

        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_death",
            "player",
            killed->GetZoneId(),
            killed->GetMapId(),
            GetChatterEventPriority("bot_group_death"),
            "",
            reactorGuid,
            reactorName,
            0,
            killerName,
            killerEntry,
            extraData,
            GetReactionDelaySeconds("bot_group_death"),
            120,
            false
        );

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

        if (!player)
            return;

        // Group check BEFORE any Item* access —
        // filters bot-only groups (main crash vector)
        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        // Suppress loot chatter in BG
        Map* lMap = player->GetMap();
        if (lMap && lMap->IsBattleground())
            return;

        bool isBot = IsPlayerBot(player);

        // Item* safety: The use-after-free crash
        // (Session 27b) only affected random bots in
        // bot-only groups, already filtered above by
        // GroupHasRealPlayer(). For bots in the
        // player's group, Item* is valid (StoreLootItem
        // just stored it, hook fires synchronously).
        // Null checks remain as extra safety.
        if (!item)
            return;
        ItemTemplate const* tmpl =
            item->GetTemplate();
        if (!tmpl)
            return;

        uint8 quality = tmpl->Quality;

        // In raids, only react to epic+ (quality >= 4)
        if (lMap && lMap->IsRaid() && quality < 4)
            return;

        if (quality < 2)
            return;
        std::string itemName = tmpl->Name1;
        uint32 itemEntry = item->GetEntry();

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

        std::string looterName = player->GetName();

        // Reactor selection: pick who comments
        // on the loot. 50% self, 50% other bot.
        // Real player loot always gets a bot reactor.
        Player* reactor = nullptr;
        if (!isBot)
        {
            reactor = GetRandomBotInGroup(group);
        }
        else if (urand(0, 1) == 0)
        {
            // Another bot comments on this loot
            reactor =
                GetRandomBotInGroup(group, player);
            if (!reactor)
                reactor = player; // fallback: self
        }
        else
        {
            reactor = player;
        }

        if (!reactor)
            return;

        uint32 reactorGuid =
            reactor->GetGUID().GetCounter();
        std::string reactorName = reactor->GetName();

        // Build extra_data JSON
        std::string extraData = "{"
            "\"bot_guid\":" +
                std::to_string(reactorGuid) + ","
            "\"bot_name\":\"" +
                JsonEscape(reactorName) + "\","
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
            "\"looter_name\":\"" +
                JsonEscape(looterName) + "\","
            "\"item_name\":\"" +
                JsonEscape(itemName) + "\","
            "\"item_entry\":" +
                std::to_string(itemEntry) + ","
            "\"item_quality\":" +
                std::to_string(quality) + ","
            "\"group_id\":" +
                std::to_string(groupId) +
            "," + BuildBotStateJson(reactor)
            + "}";

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_loot",
            "player",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            GetChatterEventPriority("bot_group_loot"),
            "",
            reactorGuid,
            reactorName,
            0,
            itemName,
            itemEntry,
            extraData,
            GetReactionDelaySeconds("bot_group_loot"),
            120,
            false
        );

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

        // Per-group cooldown: boss bypasses,
        // elite uses half, normal uses full
        time_t now = time(nullptr);
        if (!isBoss)
        {
            uint32 cooldownSec = isElite
                ? sLLMChatterConfig->_groupKillCooldown
                  / 2
                : sLLMChatterConfig->_groupKillCooldown;
            auto it =
                _groupCombatCooldowns.find(groupId);
            if (it != _groupCombatCooldowns.end()
                && (now - it->second)
                   < (time_t)cooldownSec)
                return;
        }

        // RNG by creature rank (configurable)
        uint32 chance;
        if (isBoss)
            chance = sLLMChatterConfig
                ->_combatChanceBoss;
        else if (isElite)
            chance = sLLMChatterConfig
                ->_combatChanceElite;
        else
            chance = sLLMChatterConfig
                ->_combatChanceNormal;
        if (urand(1, 100) > chance)
            return;

        _groupCombatCooldowns[groupId] = now;

        uint32 botGuid =
            player->GetGUID().GetCounter();
        std::string botName = player->GetName();
        std::string creatureName =
            creature->GetName();

        // --- Pre-cache instant delivery ---
        if (sLLMChatterConfig->_preCacheEnable
            && sLLMChatterConfig
                   ->_preCacheCombatEnable)
        {
            std::string cachedMsg, cachedEmote;
            if (TryConsumeCachedReaction(
                    groupId, botGuid,
                    "combat_pull",
                    cachedMsg, cachedEmote))
            {
                ResolvePlaceholders(
                    cachedMsg, creatureName,
                    "", "");
                SendPartyMessageInstant(
                    player, group,
                    cachedMsg, cachedEmote);
                RecordCachedChatHistory(
                    groupId, botGuid,
                    botName, cachedMsg);
                return;
            }
            if (!sLLMChatterConfig
                    ->_preCacheFallbackToLive)
                return;
        }

        // Build JSON payload. SQL escaping happens
        // below via EscapeString(extraData).
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
                std::to_string(groupId) + ","
            + BuildBotStateJson(player) + "}";

        // Inject BG context if in a battleground
        if (player->InBattleground())
        {
            Battleground* bg =
                player->GetBattleground();
            if (bg)
                AppendBGContext(
                    bg, player, extraData);
        }

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_combat",
            "player",
            player->GetZoneId(),
            player->GetMapId(),
            GetChatterEventPriority("bot_group_combat"),
            "",
            botGuid,
            botName,
            0,
            creatureName,
            creature->GetEntry(),
            extraData,
            GetReactionDelaySeconds("bot_group_combat"),
            30,
            false
        );

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
        if (safeMsg.size()
            > sLLMChatterConfig->_maxMessageLength)
            safeMsg = safeMsg.substr(
                0,
                sLLMChatterConfig->_maxMessageLength);

        if (IsLikelyPlayerbotControlCommand(
                safeMsg))
        {
            return;
        }

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

        QueueChatterEvent(
            "bot_group_player_msg",
            "player",
            player->GetZoneId(),
            player->GetMapId(),
            GetChatterEventPriority(
                "bot_group_player_msg"),
            "",
            player->GetGUID().GetCounter(),
            playerName,
            0,
            "",
            0,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_player_msg"),
            60,
            false
        );

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
            return;
        }

        if (!player)
        {
            return;
        }

        Group* group = player->GetGroup();
        if (!group)
        {
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            return;
        }

        // Suppress in raid/BG (irrelevant)
        {
            Map* lvlMap = player->GetMap();
            if (lvlMap
                && (lvlMap->IsRaid()
                    || lvlMap->IsBattleground()))
                return;
        }

        // Must actually be gaining a level
        uint8 newLevel = player->GetLevel();
        if (newLevel <= oldLevel)
        {
            return;
        }

        bool isBot = IsPlayerBot(player);

        // Pick reactor: a different bot reacts.
        // Exclude the leveler so bots don't
        // congratulate themselves.
        Player* reactor = isBot
            ? GetRandomBotInGroup(group, player)
            : GetRandomBotInGroup(group);

        if (!reactor)
        {
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

        // EscapeString makes the JSON blob SQL-safe
        // for the single-quoted INSERT literal.
        // JsonEscape only handles JSON encoding
        // inside individual values.
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_levelup",
            "player",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            GetChatterEventPriority("bot_group_levelup"),
            "",
            botGuid,
            botName,
            0,
            "",
            0,
            extraData,
            GetReactionDelaySeconds("bot_group_levelup"),
            120,
            false
        );

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

        // Player-centric: only react to the real
        // player's quest progress, not bot auto-
        // completes (avoids confusing messages)
        if (IsPlayerBot(player))
            return true;

        Group* group = player->GetGroup();
        if (!group)
            return true;

        if (!GroupHasRealPlayer(group))
            return true;

        // Suppress quest objectives in BG
        {
            Map* qoMap = player->GetMap();
            if (qoMap && qoMap->IsBattleground())
                return true;
        }

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

        // Suppress if quest was just accepted
        // (travel/breadcrumb quests fire objectives
        // immediately after accept)
        uint64 questKey =
            ((uint64)groupId << 32) | questId;
        {
            auto it =
                _questAcceptTimestamps.find(questKey);
            if (it != _questAcceptTimestamps.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_questObjSuppressWindow)
            {
                return true;
            }
        }

        // RNG chance to avoid reacting
        // to every single quest objective
        if (urand(1, 100) >
            sLLMChatterConfig
                ->_groupQuestObjectiveChance)
            return true;

        // Set cooldown only after RNG passes so a
        // miss doesn't eat 30 seconds of cooldown.
        _groupQuestObjCooldowns[groupId] = now;

        // Pick reactor: a random bot reacts.
        // Player is always real here (bots returned
        // early above), so no exclusion needed.
        Player* reactor =
            GetRandomBotInGroup(group);

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
            "\"quest_details\":\"" +
                JsonEscape(
                    quest->GetDetails()
                        .substr(0, 200)) + "\","
            "\"quest_objectives\":\"" +
                JsonEscape(
                    quest->GetObjectives()
                        .substr(0, 150)) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_quest_objectives",
            "player",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            GetChatterEventPriority(
                "bot_group_quest_objectives"),
            "",
            botGuid,
            botName,
            0,
            questName,
            questId,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_quest_objectives"),
            120,
            false
        );

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
            return;
        }

        if (!player || !quest)
        {
            return;
        }

        // Player-centric: only react to the real
        // player turning in quests
        if (IsPlayerBot(player))
            return;

        Group* group = player->GetGroup();
        if (!group)
        {
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            return;
        }

        // Suppress quest chatter in BG
        {
            Map* qMap = player->GetMap();
            if (qMap && qMap->IsBattleground())
                return;
        }

        uint32 groupId =
            group->GetGUID().GetCounter();
        uint32 questId = quest->GetQuestId();

        // Per-group+quest dedup: only ONE reaction
        // per quest per group (all bots complete
        // the same quest within seconds).
        uint64 questKey =
            ((uint64)groupId << 32) | questId;
        time_t now = time(nullptr);
        {
            auto it = _questCompleteCd.find(questKey);
            if (it != _questCompleteCd.end()
                && (now - it->second)
                   < (time_t)sLLMChatterConfig
                       ->_questDeduplicationWindow)
            {
                return;
            }
            _questCompleteCd[questKey] = now;
        }

        // RNG chance to avoid reacting to every
        // quest completion.
        if (urand(1, 100) >
            sLLMChatterConfig
                ->_groupQuestCompleteChance)
            return;

        // Pick reactor: random bot from group
        Player* reactor =
            GetRandomBotInGroup(group);

        if (!reactor)
        {
            return;
        }

        uint32 botGuid =
            reactor->GetGUID().GetCounter();
        std::string botName = reactor->GetName();
        std::string playerName = player->GetName();
        std::string questName =
            quest->GetTitle();

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
            "\"completer_name\":\"" +
                JsonEscape(playerName) + "\","
            "\"quest_name\":\"" +
                JsonEscape(questName) + "\","
            "\"quest_id\":" +
                std::to_string(questId) + ","
            "\"quest_details\":\"" +
                JsonEscape(
                    quest->GetDetails()
                        .substr(0, 200)) + "\","
            "\"quest_objectives\":\"" +
                JsonEscape(
                    quest->GetObjectives()
                        .substr(0, 150)) + "\","
            "\"group_id\":" +
                std::to_string(groupId) +
            "}";

        // EscapeString makes the JSON blob SQL-safe
        // for the single-quoted INSERT literal.
        // JsonEscape only handles JSON encoding
        // inside individual values.
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_quest_complete",
            "player",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            GetChatterEventPriority(
                "bot_group_quest_complete"),
            "",
            botGuid,
            botName,
            0,
            questName,
            questId,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_quest_complete"),
            120,
            false
        );

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
            return;
        }

        if (!player || !achievement)
        {
            return;
        }

        Group* group = player->GetGroup();
        if (!group)
        {
            return;
        }

        if (!GroupHasRealPlayer(group))
        {
            return;
        }

        // Suppress achievements when BG has ended
        // (e.g. "Warsong Gulch Victory" spam)
        if (player->InBattleground())
        {
            Battleground* bg =
                player->GetBattleground();
            if (bg && bg->GetStatus()
                    != STATUS_IN_PROGRESS)
                return;
        }

        bool isBot = IsPlayerBot(player);

        // Pick reactor: a different bot reacts.
        // Exclude the achiever so bots don't
        // congratulate themselves.
        Player* reactor = isBot
            ? GetRandomBotInGroup(group, player)
            : GetRandomBotInGroup(group);

        if (!reactor)
        {
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

        // Inject BG context if in a battleground
        if (reactor->InBattleground())
        {
            Battleground* bg =
                reactor->GetBattleground();
            if (bg)
                AppendBGContext(
                    bg, reactor, extraData);
        }

        // EscapeString makes the JSON blob SQL-safe
        // for the single-quoted INSERT literal.
        // JsonEscape only handles JSON encoding
        // inside individual values.
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_achievement",
            "player",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            GetChatterEventPriority(
                "bot_group_achievement"),
            "",
            botGuid,
            botName,
            0,
            achName,
            achId,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_achievement"),
            120,
            false
        );

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
        // per configured seconds. Check BEFORE any
        // spell classification (cheapest filter first).
        uint32 groupId =
            group->GetGUID().GetCounter();
        time_t now = time(nullptr);
        {
            auto it =
                _groupSpellCooldowns.find(groupId);
            if (it != _groupSpellCooldowns.end()
                && (now - it->second)
                    < sLLMChatterConfig
                        ->_groupSpellCastCooldown)
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

        // Skip player self-casts: bots should not
        // comment on the player buffing/shielding
        // themselves (e.g. Aspects, self-heals).
        // Area aura buffs (Bloodlust) are excluded
        // since they affect the whole group.
        if (!IsPlayerBot(player)
            && spellInfo->IsPositive()
            && !spellInfo->HasAreaAuraEffect())
        {
            Unit* tgt =
                spell->m_targets.GetUnitTarget();
            if (!tgt || tgt == player)
                return;
        }

        // --- Classify the spell ---
        // Categories: heal, dispel, cc, resurrect,
        // shield, buff
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
        //    Includes HoTs (Renew, Rejuvenation, etc.)
        else if (
            spellInfo->HasEffect(SPELL_EFFECT_HEAL)
            || spellInfo->HasEffect(
                   SPELL_EFFECT_HEAL_MAX_HEALTH)
            || spellInfo->HasAura(
                   SPELL_AURA_PERIODIC_HEAL))
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
        // 3. DISPEL — removing debuffs from a
        //    groupmate (Cleanse, Dispel Magic, etc.)
        else if (
            spellInfo->HasEffect(SPELL_EFFECT_DISPEL))
        {
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

            spellCategory = "dispel";
        }
        // 4. CC (Crowd Control) — stun, root, fear,
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
        // 5. SHIELD/IMMUNITY — positive spell with
        //    immunity, absorb, or damage reduction
        //    (Pain Suppression, Guardian Spirit, etc.)
        else if (spellInfo->IsPositive()
            && (spellInfo->HasAura(
                    SPELL_AURA_SCHOOL_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_DAMAGE_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_MECHANIC_IMMUNITY)
                || spellInfo->HasAura(
                       SPELL_AURA_SCHOOL_ABSORB)
                || spellInfo->HasAura(
                       SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN)
                || spellInfo->HasAura(
                       SPELL_AURA_SPLIT_DAMAGE_PCT)
                || spellInfo->HasAura(
                       SPELL_AURA_SPLIT_DAMAGE_FLAT)))
        {
            spellCategory = "shield";
        }
        // 6. BUFF — positive spell on a groupmate
        //    (not self). Catches MotW, Fort, Kings,
        //    Arcane Intellect, Bloodlust, Innervate,
        //    etc.
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
                    SPELL_AURA_MOD_POWER_REGEN_PERCENT)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_INCREASE_SPEED)
                || spellInfo->HasAura(
                    SPELL_AURA_MOD_MELEE_HASTE)
                || spellInfo->HasAura(
                    SPELL_AURA_HASTE_SPELLS)))
        {
            // Party/raid-wide buffs (Bloodlust,
            // Prayer of Fortitude, Gift of the Wild,
            // Greater Blessings) are self/area-targeted
            // — allow without a distinct friendly target
            if (!spellInfo->HasAreaAuraEffect())
            {
                // Single-target buff: must target
                // a different group member
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
            }

            spellCategory = "buff";
        }
        // 7. OFFENSIVE — negative spell while in combat
        //    (Fireball, Frostbolt, Arcane Bolt, etc.)
        else if (!spellInfo->IsPositive()
                 && player->IsInCombat())
        {
            spellCategory = "offensive";
        }
        // 8. GENERIC SUPPORT — positive spell not
        //    matching the specific categories above
        //    (e.g. misc buffs, utility spells cast
        //    on groupmates)
        else if (spellInfo->IsPositive())
        {
            // Single-target: must target a group
            // member (not NPC/pet/self)
            if (!spellInfo->HasAreaAuraEffect())
            {
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
            }
            spellCategory = "support";
        }
        else
        {
            // Non-combat negative spell (mounts,
            // food, professions) — ignore
            return;
        }

        // --- RNG gate ---
        // Resurrect: 100% in party, but uses
        // BGChatter.RezChance in battlegrounds
        // to reduce rez spam.
        // Everything else: scale by bot count.
        if (spellCategory == "resurrect")
        {
            Map* rzMap = player->GetMap();
            if (rzMap && rzMap->IsBattleground())
            {
                uint32 rzChance =
                    sLLMChatterConfig
                        ->_bgRezChance;
                if (urand(1, 100) > rzChance)
                    return;
            }
        }
        else
        {
            uint32 numBots = CountBotsInGroup(group);
            uint32 effectiveChance =
                sLLMChatterConfig
                    ->_groupSpellCastChance
                / std::max(numBots, 1u);
            if (effectiveChance < 1)
                effectiveChance = 1;
            if (urand(1, 100) > effectiveChance)
                return;
        }

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
        bool isAreaBuff =
            spellInfo->HasAreaAuraEffect();
        Unit* spellTarget =
            spell->m_targets.GetUnitTarget();

        bool preferVictimTarget =
            (spellCategory == "offensive"
             || spellCategory == "cc");

        if (isAreaBuff)
        {
            // Party-wide: "the group" instead of
            // a single target name
            targetName = "the group";
        }
        else if (spellTarget
                 && (!preferVictimTarget
                     || spellTarget->GetGUID()
                            != player->GetGUID()))
        {
            targetName = spellTarget->GetName();
        }
        if (targetName.empty()
            && preferVictimTarget)
        {
            // Hostile spells can surface with a
            // self target in the packet. Use the
            // current victim instead so the LLM
            // sees the real enemy actor.
            Unit* victim = player->GetVictim();
            if (victim)
                targetName = victim->GetName();
        }

        if (preferVictimTarget
            && targetName.empty())
            return;

        // Self-cast: no comment needed when a bot
        // casts on itself (e.g. PW:Shield on self)
        // Exception: area aura buffs (Bloodlust,
        // Prayer of Fortitude) are self-targeted
        // but affect the whole group
        bool isSelfCast = (!preferVictimTarget
            && !isAreaBuff
            && spellTarget
            && spellTarget->GetGUID()
                   == player->GetGUID());
        if (isSelfCast)
            return;

        // --- Pre-cache instant delivery ---
        // Skip resurrect (too important for cached).
        // Pick cache key based on category; offensive
        // cache is caster-perspective so only valid
        // when the bot itself is the caster. Player-
        // cast offensive spells skip cache entirely
        // and fall through to live LLM.
        std::string cacheKey;
        bool canUseCache = true;
        if (spellCategory == "offensive")
        {
            cacheKey = "spell_offensive";
            // Offensive cache is caster-perspective —
            // only valid when bot is the caster
            if (!casterIsBot)
                canUseCache = false;
        }
        else
        {
            cacheKey = "spell_support";
        }

        if (spellCategory != "resurrect"
            && canUseCache
            && sLLMChatterConfig->_preCacheEnable
            && sLLMChatterConfig
                   ->_preCacheSpellEnable)
        {
            std::string cachedMsg, cachedEmote;
            if (TryConsumeCachedReaction(
                    groupId, botGuid,
                    cacheKey,
                    cachedMsg, cachedEmote))
            {
                ResolvePlaceholders(
                    cachedMsg, targetName,
                    casterName, spellName);
                SendPartyMessageInstant(
                    reactor, group,
                    cachedMsg, cachedEmote);
                RecordCachedChatHistory(
                    groupId, botGuid,
                    botName, cachedMsg);
                return;
            }
            if (!sLLMChatterConfig
                    ->_preCacheFallbackToLive)
                return;
        }

        // Build JSON payload. SQL escaping happens
        // below via EscapeString(extraData).
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
                std::to_string(groupId) + ","
            + BuildBotStateJson(reactor) + "}";

        // Inject BG context if in a battleground
        if (reactor->InBattleground())
        {
            Battleground* bg =
                reactor->GetBattleground();
            if (bg)
                AppendBGContext(
                    bg, reactor, extraData);
        }

        // SQL-escape the whole JSON blob so
        // apostrophes in names don't break the
        // INSERT
        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_spell_cast",
            "player",
            reactor->GetZoneId(),
            reactor->GetMapId(),
            GetChatterEventPriority(
                "bot_group_spell_cast"),
            "",
            botGuid,
            botName,
            0,
            casterName,
            0,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_spell_cast"),
            120,
            false
        );

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

        // Suppress resurrect events in BGs
        if (player->InBattleground())
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

        QueueChatterEvent(
            "bot_group_resurrect",
            "player",
            player->GetZoneId(),
            player->GetMapId(),
            GetChatterEventPriority(
                "bot_group_resurrect"),
            "",
            botGuid,
            botName,
            0,
            "",
            0,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_resurrect"),
            120,
            false
        );

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

        // Suppress in BG (redirected to bg_respawn
        // in Phase 3); keep in raids
        {
            Map* crMap = player->GetMap();
            if (crMap && crMap->IsBattleground())
                return;
        }

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

        QueueChatterEvent(
            "bot_group_corpse_run",
            "player",
            zoneId,
            player->GetMapId(),
            GetChatterEventPriority(
                "bot_group_corpse_run"),
            "",
            botGuid,
            botName,
            0,
            "",
            0,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_corpse_run"),
            120,
            false
        );

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

        // Real player enters dungeon/raid →
        // queue bot_group_dungeon_entry once
        if (!IsPlayerBot(player)) {
            Map* map = player->GetMap();
            if (!map
                || (!map->IsDungeon()
                    && !map->IsRaid()))
                return;

            Group* group = player->GetGroup();
            if (!group
                || !GroupHasBots(group))
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

            _groupDungeonCooldowns[groupId] =
                now;

            uint32 mapId = map->GetId();
            std::string mapName =
                map->GetMapName()
                    ? map->GetMapName() : "";
            bool isRaid = map->IsRaid();

            std::string extraData = "{"
                "\"group_id\":" +
                    std::to_string(groupId) +
                    ","
                "\"map_id\":" +
                    std::to_string(mapId) + ","
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

            QueueChatterEvent(
                "bot_group_dungeon_entry",
                "player",
                player->GetZoneId(),
                mapId,
                GetChatterEventPriority(
                    "bot_group_dungeon_entry"),
                "",
                player->GetGUID()
                    .GetRawValue(),
                player->GetName(),
                0,
                mapName,
                0,
                extraData,
                GetReactionDelaySeconds(
                    "bot_group_dungeon_entry"),
                300,
                false
            );
            return;
        }

        // Bot path: only ensure traits for
        // LFG / BG groups (no dungeon entry)
        Map* map = player->GetMap();
        if (!map
            || (!map->IsDungeon()
                && !map->IsBattleground()))
            return;

        Group* group = player->GetGroup();
        if (!group)
            return;

        if (!GroupHasRealPlayer(group))
            return;

        EnsureGroupJoinQueued(player, group);

        // BG entry handled elsewhere
        if (map->IsBattleground())
            return;

    }

    // ────────────────────────────────────────────
    // Emote reaction system
    // ────────────────────────────────────────────
    void OnPlayerTextEmote(
        Player* player, uint32 textEmote,
        uint32 /*emoteNum*/,
        ObjectGuid guid) override
    {
        // Bots don't trigger reactions to each other
        if (IsPlayerBot(player)) return;

        // Denylist and exclusion guards
        if (s_ignoredEmotes.count(textEmote))
            return;
        if (s_combatCalloutEmotes.count(textEmote))
            return;
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled())
            return;
        if (!sLLMChatterConfig->_emoteReactionsEnable)
            return;

        Group* group = player->GetGroup();
        if (!group || !GroupHasRealPlayer(group))
            return;

        // Build the set of alive bots within 40 yd.
        // Used for both the proximity gate and as the
        // reactor candidate pool -- ensures the same
        // bots that enabled the reaction can speak.
        constexpr float RANGE = 40.0f;
        std::vector<Player*> nearbyAliveBots;
        for (GroupReference* itr =
                 group->GetFirstMember();
             itr; itr = itr->next())
        {
            Player* m = itr->GetSource();
            if (m && IsPlayerBot(m)
                && m->IsAlive()
                && m->GetDistance(player) <= RANGE)
                nearbyAliveBots.push_back(m);
        }
        if (nearbyAliveBots.empty()) return;

        // Classify target
        EmoteTargetType tgtType = EMOTE_TGT_NONE;
        std::string targetName;
        uint32 npcRank = 0;
        uint32 npcType = 0;
        Player* cachedTargetPlayer = nullptr;
        Creature* cachedTargetCreature = nullptr;

        if (!guid.IsEmpty())
        {
            if (guid.IsPlayer())
            {
                Player* tgt =
                    ObjectAccessor::FindPlayer(guid);
                if (tgt)
                {
                    cachedTargetPlayer = tgt;
                    targetName = tgt->GetName();
                    if (tgt->GetGroup() == group)
                        tgtType = IsPlayerBot(tgt)
                            ? EMOTE_TGT_GROUP_BOT
                            : EMOTE_TGT_GROUP_PLAYER;
                    else
                        tgtType =
                            EMOTE_TGT_EXT_PLAYER;
                }
            }
            else if (guid.IsCreature())
            {
                Creature* npc =
                    ObjectAccessor::GetCreature(
                        *player, guid);
                if (npc)
                {
                    tgtType = EMOTE_TGT_CREATURE;
                    cachedTargetCreature = npc;
                    targetName = npc->GetName();
                    npcRank =
                        npc->GetCreatureTemplate()
                            ->rank;
                    npcType =
                        npc->GetCreatureTemplate()
                            ->type;
                }
            }
        }

        if (sLLMChatterConfig->IsDebugLog())
            LOG_DEBUG("module",
                "LLMChatter: TextEmote {} "
                "tgtType={} target='{}'",
                textEmote,
                static_cast<int>(tgtType),
                targetName);

        switch (tgtType)
        {
            case EMOTE_TGT_GROUP_BOT:
                if (cachedTargetPlayer)
                    HandleEmoteAtGroupBot(
                        player, cachedTargetPlayer,
                        textEmote, group);
                break;
            case EMOTE_TGT_CREATURE:
                if (cachedTargetCreature)
                    HandleEmoteAtCreature(
                        player,
                        cachedTargetCreature,
                        textEmote);
                if (!player->IsInCombat())
                    HandleEmoteObserver(
                        player, textEmote, group,
                        tgtType, targetName,
                        npcRank, npcType,
                        cachedTargetCreature
                            ? cachedTargetCreature
                                  ->GetEntry()
                            : 0u,
                        cachedTargetCreature
                            ? cachedTargetCreature
                                  ->GetCreatureTemplate()
                                  ->SubName
                            : "",
                        nearbyAliveBots);
                break;
            case EMOTE_TGT_EXT_PLAYER:
            case EMOTE_TGT_NONE:
                if (!player->IsInCombat())
                    HandleEmoteObserver(
                        player, textEmote, group,
                        tgtType, targetName,
                        npcRank, npcType,
                        0u, "",
                        nearbyAliveBots);
                break;
            case EMOTE_TGT_GROUP_PLAYER:
                break;
        }
    }

private:
    void HandleEmoteAtGroupBot(
        Player* player, Player* targetBot,
        uint32 textEmote, Group* group)
    {
        if (urand(1, 100)
            > sLLMChatterConfig->_emoteMirrorChance)
            return;

        if (!targetBot->IsAlive()) return;

        uint32 botGuid =
            targetBot->GetGUID().GetCounter();
        uint32 groupId =
            group->GetGUID().GetCounter();
        time_t now = time(nullptr);

        // Only react if this emote has a mirror
        auto mit = s_mirrorEmoteMap.find(textEmote);
        if (mit == s_mirrorEmoteMap.end()) return;
        uint32 mirrorEmote = mit->second;

        // Per-bot mirror cooldown (checked and stamped
        // after confirming a mirror exists so unsupported
        // emotes don't consume the cooldown slot)
        auto it =
            _emoteReactCooldowns.find(botGuid);
        if (it != _emoteReactCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                     ->_emoteMirrorCooldown)
            return;
        _emoteReactCooldowns[botGuid] = now;

        uint32 delayMs = urand(800, 2500);
        targetBot->m_Events.AddEvent(
            new DelayedMirrorEmoteEvent(
                targetBot->GetGUID(),
                player->GetGUID(),
                mirrorEmote,
                player->GetName()),
            targetBot->m_Events.CalculateTime(
                delayMs));

        // Phase 4 -- queue verbal reaction
        if (urand(1, 100)
            <= sLLMChatterConfig
                   ->_emoteReactionChance)
        {
            auto vit =
                _emoteVerbalCooldowns.find(botGuid);
            if (vit == _emoteVerbalCooldowns.end()
                || (now - vit->second)
                   >= (time_t)(
                       sLLMChatterConfig
                           ->_emoteMirrorCooldown
                       * 2))
            {
                _emoteVerbalCooldowns[botGuid] = now;
                std::string emoteName =
                    GetTextEmoteName(textEmote);

                std::string extraData =
                    "{\"bot_guid\":"
                    + std::to_string(botGuid)
                    + ",\"bot_name\":\""
                    + JsonEscape(
                          targetBot->GetName())
                    + "\",\"bot_class\":"
                    + std::to_string(
                          targetBot->getClass())
                    + ",\"bot_race\":"
                    + std::to_string(
                          targetBot->getRace())
                    + ",\"bot_level\":"
                    + std::to_string(
                          targetBot->GetLevel())
                    + ",\"emote_name\":\""
                    + JsonEscape(emoteName)
                    + "\",\"player_name\":\""
                    + JsonEscape(player->GetName())
                    + "\",\"directed\":true"
                    + ",\"group_id\":"
                    + std::to_string(groupId)
                    + "}";

                QueueChatterEvent(
                    "bot_group_emote_reaction",
                    "player",
                    player->GetZoneId(),
                    player->GetMapId(),
                    GetChatterEventPriority(
                        "bot_group_emote_reaction"),
                    "",
                    botGuid,
                    targetBot->GetName(),
                    0, "", 0,
                    EscapeString(extraData),
                    GetReactionDelaySeconds(
                        "bot_group_emote_reaction"),
                    60, false
                );
            }
        }
        // Mood spread (Phase 6 -- deferred):
        // s_contagiousEmotes check goes here
    }

    void HandleEmoteAtCreature(
        Player* player, Creature* creature,
        uint32 textEmote)
    {
        if (!sLLMChatterConfig->_emoteNPCMirrorEnable)
            return;
        if (!creature->IsAlive()) return;
        if (creature->IsInCombat()) return;
        if (creature->IsHostileTo(player)) return;
        if (creature->GetCreatureTemplate()->rank >= 3)
            return; // no bosses

        auto mit = s_mirrorEmoteMap.find(textEmote);
        if (mit == s_mirrorEmoteMap.end()) return;
        uint32 mirrorEmote = mit->second;

        uint32 creatureGuidLow =
            creature->GetGUID().GetCounter();
        time_t now = time(nullptr);
        auto it =
            _creatureEmoteCooldowns.find(
                creatureGuidLow);
        if (it != _creatureEmoteCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                     ->_emoteMirrorCooldown)
            return;

        if (urand(1, 100)
            > sLLMChatterConfig->_emoteMirrorChance)
            return;

        _creatureEmoteCooldowns[creatureGuidLow] = now;

        uint32 delayMs = urand(800, 2500);
        player->m_Events.AddEvent(
            new DelayedCreatureMirrorEmoteEvent(
                player->GetGUID(),
                creature->GetGUID(),
                mirrorEmote,
                player->GetName()),
            player->m_Events.CalculateTime(delayMs));
    }

    void HandleEmoteObserver(
        Player* player, uint32 textEmote,
        Group* group,
        EmoteTargetType tgtType,
        const std::string& targetName,
        uint32 npcRank, uint32 npcType,
        uint32 npcEntry,
        const std::string& npcSubName,
        const std::vector<Player*>& candidates)
    {
        if (candidates.empty()) return;

        uint32 groupId =
            group->GetGUID().GetCounter();
        time_t now = time(nullptr);

        // Per-group observer cooldown
        auto it =
            _emoteObserverCooldowns.find(groupId);
        if (it != _emoteObserverCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                     ->_emoteObserverCooldown)
            return;
        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_emoteObserverChance)
            return;
        _emoteObserverCooldowns[groupId] = now;

        // Pick reactor from nearby alive bots only
        Player* reactor = candidates[
            urand(0, (uint32)(candidates.size() - 1))];
        if (!reactor) return;

        std::string emoteName =
            GetTextEmoteName(textEmote);

        const char* tgtTypeStr =
            (tgtType == EMOTE_TGT_CREATURE)
                ? "creature"
            : (tgtType == EMOTE_TGT_EXT_PLAYER)
                ? "player_external"
            : "none";

        std::string extraData =
            "{\"bot_guid\":"
            + std::to_string(
                reactor->GetGUID().GetCounter())
            + ",\"bot_name\":\""
            + JsonEscape(reactor->GetName())
            + "\",\"bot_class\":"
            + std::to_string(reactor->getClass())
            + ",\"bot_race\":"
            + std::to_string(reactor->getRace())
            + ",\"bot_level\":"
            + std::to_string(reactor->GetLevel())
            + ",\"emote_name\":\""
            + JsonEscape(emoteName)
            + "\",\"player_name\":\""
            + JsonEscape(player->GetName())
            + "\",\"target_type\":\""
            + tgtTypeStr
            + "\",\"target_name\":\""
            + JsonEscape(targetName)
            + "\",\"npc_rank\":"
            + std::to_string(npcRank)
            + ",\"npc_type\":"
            + std::to_string(npcType)
            + ",\"npc_subname\":\""
            + JsonEscape(npcSubName)
            + "\",\"group_id\":"
            + std::to_string(groupId)
            + "}";

        // For creature targets pass npcEntry as both
        // target_guid (creature sentinel: non-zero)
        // and target_entry so the delivery loop's
        // Phase 1 can FindNearestCreature() and face
        // the bot toward the NPC before speaking.
        uint32 facingEntry =
            (tgtType == EMOTE_TGT_CREATURE)
                ? npcEntry : 0u;

        QueueChatterEvent(
            "bot_group_emote_observer",
            "player",
            player->GetZoneId(),
            player->GetMapId(),
            GetChatterEventPriority(
                "bot_group_emote_observer"),
            "",
            reactor->GetGUID().GetCounter(),
            reactor->GetName(),
            facingEntry, targetName, facingEntry,
            EscapeString(extraData),
            GetReactionDelaySeconds(
                "bot_group_emote_observer"),
            60, false
        );
    }
};

void EvictEmoteCooldowns()
{
    // Age-based eviction for per-bot and per-creature
    // emote cooldown maps.  These are keyed by unit
    // GUID (not group), so CleanupGroupSession can't
    // reach them.  Called from the World update tick
    // on the same interval as nearby-object scans.
    time_t now = time(nullptr);
    auto evict = [now](
        std::unordered_map<uint32, time_t>& m,
        time_t window)
    {
        for (auto it = m.begin(); it != m.end();)
        {
            if (now - it->second > window)
                it = m.erase(it);
            else
                ++it;
        }
    };
    time_t mirrorWindow =
        (time_t)sLLMChatterConfig->_emoteMirrorCooldown;
    evict(_emoteReactCooldowns,   mirrorWindow);
    evict(_emoteVerbalCooldowns,  mirrorWindow * 2);
    evict(_creatureEmoteCooldowns, mirrorWindow);
}

void HandleGroupPlayerUpdateZone(
    Player* player, uint32 newZone,
    uint32 newArea)
{
    if (!player || !sLLMChatterConfig)
        return;

    Group* grp = player->GetGroup();
    if (!grp)
        return;

    uint32 gId = grp->GetGUID().GetCounter();
    uint32 mapId = player->GetMapId();

    if (!IsPlayerBot(player))
    {
        // Real player: update ALL bots in the
        // group to the same zone/area/map.
        // Bots lack a real client so their
        // UpdateZone() may never fire after
        // instance teleports. Area is only
        // set from the real player to avoid
        // stale bot GetAreaId() values.
        CharacterDatabase.Execute(
            "UPDATE llm_group_bot_traits "
            "SET zone = {}, area = {}, map = {} "
            "WHERE group_id = {}",
            newZone, newArea, mapId, gId);
    }
    else
    {
        // Bot: update only zone+map (not area).
        // Bot GetAreaId() can be stale after
        // teleports — area is set exclusively
        // by the real player's hooks.
        uint32 bGuid =
            player->GetGUID().GetCounter();
        CharacterDatabase.Execute(
            "UPDATE llm_group_bot_traits "
            "SET zone = {}, map = {} "
            "WHERE group_id = {} "
            "AND bot_guid = {}",
            newZone, mapId, gId, bGuid);
    }

    // Zone transition events are triggered by
    // the real player only. Bots following the
    // same path would race on _groupZoneCooldowns
    // from separate map worker threads, causing
    // duplicate events.
    if (IsPlayerBot(player))
        return;

    if (!sLLMChatterConfig->_useGroupChatter)
        return;

    // Suppress zone transition in raid/BG
    // (single zone, not meaningful).
    {
        Map* zMap = player->GetMap();
        if (zMap
            && (zMap->IsRaid()
                || zMap->IsBattleground()))
            return;
    }

    Group* group = player->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    uint32 groupId = group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    auto it = _groupZoneCooldowns.find(groupId);
    if (it != _groupZoneCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
               ->_groupZoneCooldown)
        return;

    if (urand(1, 100)
        > sLLMChatterConfig->_groupZoneChance)
        return;

    std::string zoneName = GetZoneName(newZone);
    if (zoneName.empty())
        return;

    _groupZoneCooldowns[groupId] = now;

    uint32 botGuid =
        player->GetGUID().GetCounter();
    std::string botName = player->GetName();

    std::string areaName;
    {
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
    }

    std::string extraData = "{"
        "\"bot_guid\":" +
            std::to_string(botGuid) + ","
        "\"bot_name\":\"" +
            JsonEscape(botName) + "\","
        "\"bot_class\":" +
            std::to_string(player->getClass()) + ","
        "\"bot_race\":" +
            std::to_string(player->getRace()) + ","
        "\"bot_level\":" +
            std::to_string(player->GetLevel()) + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"zone_id\":" +
            std::to_string(newZone) + ","
        "\"zone_name\":\"" +
            JsonEscape(zoneName) + "\","
        "\"area_id\":" +
            std::to_string(newArea) + ","
        "\"area_name\":\"" +
            JsonEscape(areaName) + "\""
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_zone_transition",
        "player",
        newZone,
        player->GetMapId(),
        GetChatterEventPriority(
            "bot_group_zone_transition"),
        "",
        botGuid,
        botName,
        0,
        zoneName,
        0,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_zone_transition"),
        120,
        false
    );

}

// ============================================================
// State-triggered callout helpers (free functions)
// ============================================================

static void QueueStateCallout(
    Player* bot, Group* group,
    const char* eventType, uint32 groupId)
{
    // Dead bots should not call out
    // low health, OOM, or aggro loss
    if (!bot->IsAlive())
        return;

    std::string botName = bot->GetName();
    uint32 botGuid =
        bot->GetGUID().GetCounter();

    // Get target name for context
    std::string targetName = "";
    Unit* victim = bot->GetVictim();
    if (victim)
        targetName = victim->GetName();

    // Who has aggro (for aggro_loss context)
    std::string aggroTarget = "";
    if (victim && victim->GetVictim()
        && victim->GetVictim() != bot)
    {
        aggroTarget =
            victim->GetVictim()->GetName();
    }

    // --- Pre-cache instant delivery ---
    if (sLLMChatterConfig->_preCacheEnable
        && sLLMChatterConfig
               ->_preCacheStateEnable
        && group)
    {
        // Map event type to cache category
        std::string category;
        std::string evtStr(eventType);
        if (evtStr == "bot_group_low_health")
            category = "state_low_health";
        else if (evtStr == "bot_group_oom")
            category = "state_oom";
        else if (evtStr == "bot_group_aggro_loss")
            category = "state_aggro_loss";

        if (!category.empty())
        {
            std::string cachedMsg, cachedEmote;
            if (TryConsumeCachedReaction(
                    groupId, botGuid,
                    category,
                    cachedMsg, cachedEmote))
            {
                // aggro_loss uses {target}
                std::string tgt =
                    (category == "state_aggro_loss")
                    ? targetName : "";
                ResolvePlaceholders(
                    cachedMsg, tgt, "", "");
                SendPartyMessageInstant(
                    bot, group,
                    cachedMsg, cachedEmote);
                RecordCachedChatHistory(
                    groupId, botGuid,
                    botName, cachedMsg);
                return;
            }
            if (!sLLMChatterConfig
                    ->_preCacheFallbackToLive)
                return;
        }
    }

    std::string extraData = "{"
        "\"bot_guid\":" +
            std::to_string(botGuid) + ","
        "\"bot_name\":\"" +
            JsonEscape(botName) + "\","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"target_name\":\"" +
            JsonEscape(targetName) + "\","
        "\"aggro_target\":\"" +
            JsonEscape(aggroTarget) + "\","
        + BuildBotStateJson(bot) + "}";

    // Inject BG context when in a battleground
    if (bot->InBattleground())
    {
        Battleground* bg =
            bot->GetBattleground();
        if (bg)
            AppendBGContext(bg, bot, extraData);
    }

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        eventType,
        "player",
        bot->GetZoneId(),
        bot->GetMapId(),
        GetChatterEventPriority(eventType),
        std::string("state:") + eventType + ":" + std::to_string(botGuid),
        botGuid,
        botName,
        0,
        "",
        0,
        extraData,
        GetReactionDelaySeconds(eventType),
        60,
        false
    );

}

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

void CheckGroupCombatState()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig
            ->_stateCalloutEnabled)
        return;

    if (!sLLMChatterConfig->_useGroupChatter)
        return;

    time_t now = time(nullptr);
    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    std::set<uint32> visitedGroups;

    for (auto const& [id, session] : sessions)
    {
        Player* player =
            session->GetPlayer();
        if (!player
            || !player->IsInWorld())
            continue;
        if (IsPlayerBot(player))
            continue;

        Group* group = player->GetGroup();
        if (!group)
            continue;

        uint32 groupId =
            group->GetGUID().GetCounter();
        if (visitedGroups.count(groupId))
            continue;
        visitedGroups.insert(groupId);

        bool inBG = player->InBattleground();

        for (GroupReference* itr =
                 group->GetFirstMember();
             itr; itr = itr->next())
        {
            Player* bot = itr->GetSource();
            if (!bot || !IsPlayerBot(bot))
                continue;

            uint32 botGuid =
                bot->GetGUID().GetCounter();
            uint32 cd = sLLMChatterConfig
                ->_stateCalloutCooldown;
            uint32 chance = sLLMChatterConfig
                ->_stateCalloutChance;

            // In BGs, state callouts are less
            // interesting — triple the cooldown
            // and halve the chance
            if (inBG)
            {
                cd *= 3;
                chance /= 2;
            }

            // --- Low Health Check ---
            if (sLLMChatterConfig
                    ->_stateCalloutLowHealth)
            {
                float hp =
                    bot->GetHealthPct();
                if (hp > 0 && hp <=
                    sLLMChatterConfig
                        ->_lowHealthThreshold)
                {
                    auto it =
                        _botLowHealthCooldowns
                            .find(botGuid);
                    if (it ==
                        _botLowHealthCooldowns
                            .end()
                        || (now - it->second)
                            >= (time_t)cd)
                    {
                        if (urand(1, 100)
                            <= chance)
                        {
                            QueueStateCallout(
                                bot, group,
                                "bot_group_"
                                "low_health",
                                groupId);
                        }
                        _botLowHealthCooldowns
                            [botGuid] = now;
                    }
                }
            }

            // --- OOM Check ---
            if (sLLMChatterConfig
                    ->_stateCalloutOom)
            {
                if (bot->GetMaxPower(
                        POWER_MANA) > 0)
                {
                    float mp =
                        bot->GetPowerPct(
                            POWER_MANA);
                    if (mp <=
                        sLLMChatterConfig
                            ->_oomThreshold)
                    {
                        auto it =
                            _botOomCooldowns
                                .find(botGuid);
                        if (it ==
                            _botOomCooldowns
                                .end()
                            || (now - it->second)
                                >= (time_t)cd)
                        {
                            if (urand(1, 100)
                                <= chance)
                            {
                                QueueStateCallout(
                                    bot, group,
                                    "bot_group_"
                                    "oom",
                                    groupId);
                            }
                            _botOomCooldowns
                                [botGuid] = now;
                        }
                    }
                }
            }

            // --- Aggro Loss Check ---
            // (combat-only: requires active target)
            // Skip in BGs (aggro is chaotic/meaningless)
            if (!inBG
                && sLLMChatterConfig
                    ->_stateCalloutAggro
                && bot->IsInCombat())
            {
                PlayerbotAI* ai =
                    GET_PLAYERBOT_AI(bot);
                if (ai && PlayerbotAI
                        ::IsTank(bot))
                {
                    Unit* victim =
                        bot->GetVictim();
                    if (victim
                        && victim->GetVictim()
                        && victim->GetVictim()
                            != bot)
                    {
                        Player* threatened =
                            victim->GetVictim()
                                ->ToPlayer();
                        if (threatened
                            && group->IsMember(
                                threatened
                                    ->GetGUID()))
                        {
                            auto it =
                                _botAggroCooldowns
                                    .find(
                                        botGuid);
                            if (it ==
                                _botAggroCooldowns
                                    .end()
                                || (now
                                    - it->second)
                                    >= (time_t)cd)
                            {
                                if (urand(1, 100)
                                    <= chance)
                                {
                                    QueueStateCallout(
                                        bot,
                                        group,
                                        "bot_group"
                                        "_aggro_"
                                        "loss",
                                        groupId);
                                }
                                _botAggroCooldowns
                                    [botGuid]
                                        = now;
                            }
                        }
                    }
                }
            }
        }
    }
}

// ================================================
// AllCreatureScript - Quest Accept hook
// (no PlayerScript equivalent exists)
// ================================================
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

void AddLLMChatterGroupScripts()
{
    new LLMChatterGroupScript();
    new LLMChatterGroupPlayerScript();
    new LLMChatterCreatureScript();
}
