/*
 * mod-llm-chatter - group loot roll comments
 *
 * Owns:
 *   - polling open group loot rolls for party bots that
 *     voted Need or Greed
 *   - the per-item comment cap and its bookkeeping
 *   - the bot_group_loot_roll payload (item name, quality,
 *     class, subclass and inventory type)
 *
 * The core has no hook for a vote being cast; it only
 * reports the winner (OnPlayerGroupRollRewardItem, which
 * the loot reaction in LLMChatterGroupCombat.cpp uses).
 * Open rolls are public through Group::GetRolls(), so the
 * world update reads each roll's votes instead. It runs
 * between map updates, like CheckGroupCombatState().
 * Battlegrounds and arenas are excluded.
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroup.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "Group.h"
#include "ItemTemplate.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "World.h"
#include "WorldSessionMgr.h"

#include <map>
#include <set>
#include <string>
#include <tuple>
#include <vector>

namespace
{

// One open roll: the group, the loot source and its slot.
using RollKey = std::tuple<uint32, uint64, uint8>;

struct RollComments
{
    std::set<uint64> handledVoters;
    uint32 queued = 0;
};

std::map<RollKey, RollComments> _rollComments;

// Extra seconds between comments on the same item, so the
// lines do not land together.
constexpr uint32 kRollCommentStagger = 4;

struct BotVote
{
    Player* bot;
    RollVote vote;
};

void QueueLootRollComment(
    Player* bot, Group* group, Roll const* roll,
    RollVote vote, uint32 index)
{
    ItemTemplate const* tmpl =
        sObjectMgr->GetItemTemplate(roll->itemid);
    if (!tmpl)
        return;

    std::string itemName = GetLocalizedItemName(tmpl);
    uint32 groupId = group->GetGUID().GetCounter();

    std::string extraData = "{"
        + BuildBotIdentityFields(bot) + ","
        "\"is_bot\":1,"
        "\"roll_vote\":\""
            + std::string(vote == NEED ? "need" : "greed")
            + "\","
        "\"item_name\":\"" + JsonEscape(itemName) + "\","
        "\"item_entry\":" + std::to_string(roll->itemid) + ","
        "\"item_quality\":"
            + std::to_string(tmpl->Quality) + ","
        "\"item_class\":" + std::to_string(tmpl->Class) + ","
        "\"item_subclass\":"
            + std::to_string(tmpl->SubClass) + ","
        "\"item_inventory_type\":"
            + std::to_string(tmpl->InventoryType) + ","
        "\"group_id\":" + std::to_string(groupId)
        + "," + BuildBotStateJson(bot)
        + "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_loot_roll",
        "player",
        bot->GetZoneId(),
        bot->GetMapId(),
        GetChatterEventPriority("bot_group_loot_roll"),
        "",
        bot->GetGUID().GetCounter(),
        bot->GetName(),
        0,
        itemName,
        roll->itemid,
        extraData,
        GetReactionDelaySeconds("bot_group_loot_roll")
            + index * kRollCommentStagger,
        120,
        false
    );
}

void ScanGroupRolls(
    Group* group, std::set<RollKey>& openRolls)
{
    uint32 groupId = group->GetGUID().GetCounter();
    uint32 maxPerItem =
        sLLMChatterConfig->_lootRollCommentMaxPerItem;

    for (Roll const* roll : group->GetRolls())
    {
        if (!roll)
            continue;

        RollKey key{
            groupId, roll->itemGUID.GetRawValue(),
            roll->itemSlot};
        openRolls.insert(key);
        RollComments& state = _rollComments[key];

        // Need votes go first when one scan finds both.
        std::vector<BotVote> needs;
        std::vector<BotVote> greeds;
        for (auto const& [voterGuid, vote] : roll->playerVote)
        {
            if (vote != NEED && vote != GREED)
                continue;
            uint64 rawGuid = voterGuid.GetRawValue();
            if (state.handledVoters.count(rawGuid))
                continue;
            state.handledVoters.insert(rawGuid);

            Player* voter =
                ObjectAccessor::FindPlayer(voterGuid);
            if (!voter || !voter->IsInWorld()
                || !IsPlayerBot(voter)
                || voter->GetGroup() != group)
                continue;
            (vote == NEED ? needs : greeds)
                .push_back({voter, vote});
        }
        needs.insert(needs.end(), greeds.begin(), greeds.end());

        for (BotVote const& bv : needs)
        {
            if (state.queued >= maxPerItem)
                break;
            QueueLootRollComment(
                bv.bot, group, roll, bv.vote, state.queued);
            ++state.queued;
        }
    }
}

} // namespace

void CheckGroupLootRolls()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter
        || !sLLMChatterConfig->_lootRollCommentEnable)
    {
        _rollComments.clear();
        return;
    }

    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    std::set<uint32> visitedGroups;
    std::set<RollKey> openRolls;

    for (auto const& [id, session] : sessions)
    {
        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld()
            || IsPlayerBot(player))
            continue;

        Group* group = player->GetGroup();
        if (!group)
            continue;

        uint32 groupId = group->GetGUID().GetCounter();
        if (!visitedGroups.insert(groupId).second)
            continue;

        Map* map = player->GetMap();
        if (map && map->IsBattlegroundOrArena())
            continue;

        if (!GroupHasRealPlayer(group))
            continue;

        ScanGroupRolls(group, openRolls);
    }

    // Forget rolls that have ended.
    for (auto it = _rollComments.begin();
         it != _rollComments.end();)
    {
        if (openRolls.count(it->first))
            ++it;
        else
            it = _rollComments.erase(it);
    }
}
