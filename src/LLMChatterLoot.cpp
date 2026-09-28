/*
 * mod-llm-chatter - real bot loot announcements in General chat
 */

#include "LLMChatterLoot.h"

#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "Item.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "RandomPlayerbotMgr.h"
#include "ScriptMgr.h"
#include "Timer.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace
{
struct LootItemSnapshot
{
    uint32 entry = 0;
    std::string name;
    uint8 quality = 0;
    uint32 count = 0;
    int32 allowableClass = -1;
    uint32 requiredLevel = 0;
};

struct PendingLootSource
{
    uint32 botGuid = 0;
    std::string botName;
    ObjectGuid lootGuid;
    uint32 zoneId = 0;
    uint32 areaId = 0;
    uint32 mapId = 0;
    TeamId teamId = TEAM_ALLIANCE;
    bool passedChance = false;
    uint32 seenItems = 0;
    std::optional<LootItemSnapshot> selectedItem;
    uint32 lastSeenMs = 0;
};

struct BotLootAggregation
{
    std::optional<PendingLootSource> active;
    std::optional<PendingLootSource> completed;
};

std::map<uint32, BotLootAggregation> _lootAggregations;
std::mutex _lootAggregationsMutex;
std::map<std::string, time_t> _lootCooldownCache;
std::mutex _lootCooldownMutex;

std::string MakeLootCooldownKey(uint32 zoneId)
{
    return "general-loot:zone:" + std::to_string(zoneId);
}

bool IsLootOnCachedCooldown(uint32 zoneId)
{
    if (!sLLMChatterConfig->_generalLootZoneCooldownSeconds)
        return false;

    std::lock_guard<std::mutex> lock(_lootCooldownMutex);
    auto itr = _lootCooldownCache.find(
        MakeLootCooldownKey(zoneId));
    if (itr == _lootCooldownCache.end())
        return false;

    return time(nullptr) - itr->second
        < sLLMChatterConfig
            ->_generalLootZoneCooldownSeconds;
}

bool IsLootOnCooldown(uint32 zoneId)
{
    if (!sLLMChatterConfig->_generalLootZoneCooldownSeconds)
        return false;

    if (IsLootOnCachedCooldown(zoneId))
        return true;

    return IsPersistedEventOnCooldown(
        MakeLootCooldownKey(zoneId),
        sLLMChatterConfig->_generalLootZoneCooldownSeconds);
}

void SetLootCooldown(uint32 zoneId)
{
    if (!sLLMChatterConfig->_generalLootZoneCooldownSeconds)
        return;

    std::lock_guard<std::mutex> lock(_lootCooldownMutex);
    SetEventCooldown(
        _lootCooldownCache,
        MakeLootCooldownKey(zoneId));
}

bool ShouldReplaceReservoirItem(uint32 replacementRoll)
{
    return replacementRoll == 1;
}

void UpdateReservoir(
    PendingLootSource& source,
    LootItemSnapshot const& item,
    uint32 nowMs)
{
    ++source.seenItems;
    source.lastSeenMs = nowMs;
    if (!source.passedChance)
        return;

    uint32 replacementRoll = urand(1, source.seenItems);
    if (ShouldReplaceReservoirItem(replacementRoll))
        source.selectedItem = item;
}

bool HasLiveGeneralAudience(Player* bot)
{
    if (!bot)
        return false;

    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    for (auto const& pair : sessions)
    {
        WorldSession* session = pair.second;
        if (!session || session->PlayerLoading())
            continue;

        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld()
            || IsPlayerBot(player)
            || !IsInOverworld(player))
            continue;

        if (player->GetMapId() == bot->GetMapId()
            && player->GetZoneId() == bot->GetZoneId()
            && player->GetTeamId() == bot->GetTeamId())
            return true;
    }

    return false;
}

void QueueFinalizedLoot(PendingLootSource const& source)
{
    if (!source.passedChance || !source.selectedItem)
        return;

    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_generalChannelEnable
        || !sLLMChatterConfig->_useEventSystem
        || !sLLMChatterConfig->_generalLootEnable)
        return;

    ObjectGuid botGuid =
        ObjectGuid::Create<HighGuid::Player>(source.botGuid);
    Player* bot = ObjectAccessor::FindPlayer(botGuid);
    if (!bot || !bot->IsInWorld() || !bot->IsAlive()
        || !IsPlayerBot(bot)
        || !sRandomPlayerbotMgr.IsRandomBot(bot)
        || !IsInOverworld(bot)
        || IsGroupedWithRealPlayer(bot))
        return;

    if (bot->GetMapId() != source.mapId
        || bot->GetZoneId() != source.zoneId
        || bot->GetTeamId() != source.teamId
        || !HasLiveGeneralAudience(bot)
        || !CanSpeakInGeneralChannel(bot))
        return;

    if (IsLootOnCooldown(source.zoneId))
        return;

    LootItemSnapshot const& item = *source.selectedItem;
    std::string extraData = "{"
        "\"item_id\":" + std::to_string(item.entry) + ","
        "\"item_name\":\"" + JsonEscape(item.name) + "\","
        "\"item_quality\":" + std::to_string(item.quality) + ","
        "\"item_count\":" + std::to_string(item.count) + ","
        "\"allowable_class\":"
            + std::to_string(item.allowableClass) + ","
        "\"required_level\":"
            + std::to_string(item.requiredLevel) + ","
        "\"loot_source_guid\":\""
            + JsonEscape(source.lootGuid.ToString()) + "\","
        "\"zone_id\":" + std::to_string(source.zoneId) + ","
        "\"area_id\":" + std::to_string(source.areaId)
        + "}";

    uint32 reactionDelay =
        GetReactionDelaySeconds("bot_loot_item");
    QueueChatterEvent(
        "bot_loot_item",
        "player",
        source.zoneId,
        source.mapId,
        GetChatterEventPriority("bot_loot_item"),
        MakeLootCooldownKey(source.zoneId),
        source.botGuid,
        bot->GetName(),
        0,
        item.name,
        item.entry,
        EscapeString(extraData),
        reactionDelay,
        reactionDelay
            + sLLMChatterConfig->_eventExpirationSeconds,
        true);
    SetLootCooldown(source.zoneId);
}

void CaptureLoot(
    Player* player, Item* item,
    uint32 count, ObjectGuid lootGuid)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_generalChannelEnable
        || !sLLMChatterConfig->_useEventSystem
        || !sLLMChatterConfig->_generalLootEnable
        || !player || !item)
        return;

    // StoreNewItem can free the callback Item when it stacks into an
    // existing slot. This field remains safe to read after that free.
    if (!item->IsInWorld())
        return;

    if (lootGuid.IsEmpty()
        || !IsPlayerBot(player)
        || !player->IsInWorld()
        || !player->IsAlive()
        || !IsInOverworld(player)
        || IsGroupedWithRealPlayer(player))
        return;

    uint32 mapId = player->GetMapId();
    uint32 zoneId = player->GetZoneId();
    TeamId teamId = player->GetTeamId();
    if (!HasCachedGeneralAudience(mapId, zoneId, teamId))
        return;

    ItemTemplate const* itemTemplate = item->GetTemplate();
    if (!itemTemplate
        || itemTemplate->Quality
            < sLLMChatterConfig->_generalLootMinQuality)
        return;

    LootItemSnapshot itemSnapshot;
    itemSnapshot.entry = item->GetEntry();
    itemSnapshot.name = itemTemplate->Name1;
    itemSnapshot.quality = itemTemplate->Quality;
    itemSnapshot.count = count;
    itemSnapshot.allowableClass = itemTemplate->AllowableClass;
    itemSnapshot.requiredLevel = itemTemplate->RequiredLevel;

    uint32 botGuid = player->GetGUID().GetCounter();
    uint32 nowMs = getMSTime();
    {
        std::lock_guard<std::mutex> lock(
            _lootAggregationsMutex);
        auto aggregationIt = _lootAggregations.find(botGuid);
        if (aggregationIt != _lootAggregations.end()
            && aggregationIt->second.active
            && aggregationIt->second.active->lootGuid
                == lootGuid)
        {
            UpdateReservoir(
                *aggregationIt->second.active,
                itemSnapshot,
                nowMs);
            return;
        }

        if (aggregationIt != _lootAggregations.end()
            && aggregationIt->second.active)
        {
            aggregationIt->second.completed =
                std::move(aggregationIt->second.active);
            aggregationIt->second.active.reset();
        }
    }

    if (IsLootOnCachedCooldown(zoneId))
        return;

    std::lock_guard<std::mutex> lock(
        _lootAggregationsMutex);
    BotLootAggregation& aggregation =
        _lootAggregations[botGuid];
    if (aggregation.active
        && aggregation.active->lootGuid == lootGuid)
    {
        UpdateReservoir(
            *aggregation.active,
            itemSnapshot,
            nowMs);
        return;
    }
    if (aggregation.active)
        aggregation.completed = std::move(aggregation.active);

    uint32 chance = std::min(
        sLLMChatterConfig->_eventReactionChance,
        100u);
    PendingLootSource source;
    source.botGuid = botGuid;
    source.botName = player->GetName();
    source.lootGuid = lootGuid;
    source.zoneId = zoneId;
    source.areaId = player->GetAreaId();
    source.mapId = mapId;
    source.teamId = teamId;
    source.passedChance =
        chance > 0 && urand(1, 100) <= chance;
    UpdateReservoir(source, itemSnapshot, nowMs);
    aggregation.active = std::move(source);
}

void FlushLootAggregations()
{
    std::vector<PendingLootSource> ready;
    uint32 nowMs = getMSTime();
    {
        std::lock_guard<std::mutex> lock(
            _lootAggregationsMutex);
        for (auto itr = _lootAggregations.begin();
             itr != _lootAggregations.end();)
        {
            BotLootAggregation& aggregation = itr->second;
            if (aggregation.completed)
            {
                ready.push_back(
                    std::move(*aggregation.completed));
                aggregation.completed.reset();
            }

            if (aggregation.active
                && getMSTimeDiff(
                    aggregation.active->lastSeenMs,
                    nowMs)
                    >= sLLMChatterConfig
                        ->_generalLootAggregationDelayMs)
            {
                ready.push_back(std::move(*aggregation.active));
                aggregation.active.reset();
            }

            if (!aggregation.active && !aggregation.completed)
                itr = _lootAggregations.erase(itr);
            else
                ++itr;
        }
    }

    for (PendingLootSource const& source : ready)
        QueueFinalizedLoot(source);
}

void ClearLootAggregations()
{
    std::lock_guard<std::mutex> lock(
        _lootAggregationsMutex);
    _lootAggregations.clear();
}

class LLMChatterLootPlayerScript : public PlayerScript
{
public:
    LLMChatterLootPlayerScript()
        : PlayerScript(
              "LLMChatterLootPlayerScript",
              {PLAYERHOOK_ON_LOOT_ITEM}) {}

    void OnPlayerLootItem(
        Player* player, Item* item,
        uint32 count, ObjectGuid lootGuid) override
    {
        CaptureLoot(player, item, count, lootGuid);
    }
};

class LLMChatterLootWorldScript : public WorldScript
{
public:
    LLMChatterLootWorldScript()
        : WorldScript(
              "LLMChatterLootWorldScript",
              {WORLDHOOK_ON_UPDATE}) {}

    void OnUpdate(uint32 /*diff*/) override
    {
        if (!sLLMChatterConfig
            || !sLLMChatterConfig->IsEnabled()
            || !sLLMChatterConfig->_generalChannelEnable
            || !sLLMChatterConfig->_useEventSystem
            || !sLLMChatterConfig->_generalLootEnable)
        {
            ClearLootAggregations();
            return;
        }

        FlushLootAggregations();
    }
};
}

void AddLLMChatterLootScripts()
{
    new LLMChatterLootPlayerScript();
    new LLMChatterLootWorldScript();
}
