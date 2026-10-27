/*
 * mod-llm-chatter - group loot roll comments
 *
 * Owns:
 *   - polling open group loot rolls for party bots that
 *     voted Need or Greed
 *   - the per-item comment cap, and the per-vote chance and
 *     per-group cooldown of Need and of Greed comments, and
 *     their bookkeeping
 *   - the Need/Greed and equipment/other switches
 *   - the bot_group_loot_roll payload (item name, quality,
 *     class, subclass, inventory type, whether the item is
 *     equipment, whether the bot can use it, and the roll's
 *     source and slot)
 *   - closed rolls: cancelling their pending events and
 *     LootRollCommentDropReason() for delivery
 *
 * The core has no hook for a vote being cast; it only
 * reports the winner (OnPlayerGroupRollRewardItem, which
 * the loot reaction in LLMChatterGroupCombat.cpp uses).
 * Open rolls are public through Group::GetRolls(), so the
 * world update reads each roll's votes instead. It runs
 * between map updates, like CheckGroupCombatState().
 * Battlegrounds and arenas are excluded.
 *
 * Coverage is bounded: the last vote resolves and deletes a
 * roll at once (Group::CountRollVote), so a vote cast just
 * before that is never seen, and a comment can be ready
 * after the roll has closed. Such comments are cancelled or
 * dropped at delivery, never spoken late.
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroup.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterJsonFields.h"
#include "LLMChatterShared.h"

#include "DatabaseEnv.h"
#include "Group.h"
#include "GroupMgr.h"
#include "ItemTemplate.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "World.h"
#include "WorldSessionMgr.h"

#include <cstdint>
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

// Group -> when its last commented roll got its first
// comment, per vote (LootRollComment.NeedCooldown and
// .GreedCooldown).
std::map<uint32, time_t> _needCommentCooldowns;
std::map<uint32, time_t> _greedCommentCooldowns;

// Extra seconds between comments on the same item, so the
// lines do not land together.
constexpr uint32 kRollCommentStagger = 4;

struct BotVote
{
    Player* bot;
    RollVote vote;
};

// Anything with an equipment slot counts as equipment:
// armor, weapons, jewelry, shirts and tabards, and also
// bags, quivers and ammunition.
bool IsEquipment(ItemTemplate const* tmpl)
{
    return tmpl->InventoryType != INVTYPE_NON_EQUIP;
}

bool VoteCommentEnabled(RollVote vote)
{
    return vote == NEED
        ? sLLMChatterConfig->_lootRollCommentNeedEnable
        : sLLMChatterConfig->_lootRollCommentGreedEnable;
}

uint32 VoteCommentChance(RollVote vote)
{
    return vote == NEED
        ? sLLMChatterConfig->_lootRollCommentNeedChance
        : sLLMChatterConfig->_lootRollCommentGreedChance;
}

time_t VoteCommentCooldown(RollVote vote)
{
    return static_cast<time_t>(vote == NEED
        ? sLLMChatterConfig->_lootRollCommentNeedCooldown
        : sLLMChatterConfig->_lootRollCommentGreedCooldown);
}

std::map<uint32, time_t>& VoteCommentCooldowns(RollVote vote)
{
    return vote == NEED
        ? _needCommentCooldowns : _greedCommentCooldowns;
}

void PruneCommentCooldowns(RollVote vote, time_t now)
{
    std::map<uint32, time_t>& cooldowns = VoteCommentCooldowns(vote);
    time_t cooldown = VoteCommentCooldown(vote);
    for (auto it = cooldowns.begin(); it != cooldowns.end();)
    {
        if (now - it->second >= cooldown)
            it = cooldowns.erase(it);
        else
            ++it;
    }
}

// Whether this bot can use the item, as a fact for the
// prompt: "yes", "class" (never, for its class, race or
// faction), "proficiency" (not trained for this armor or
// weapon type), "skill" (a profession or other skill is
// missing or too low), "level" (RequiredLevel above the
// bot's), or "no" (anything else).
char const* LootRollUse(Player* bot, ItemTemplate const* tmpl)
{
    switch (bot->CanUseItem(tmpl))
    {
        case EQUIP_ERR_OK:
            break;
        case EQUIP_ERR_YOU_CAN_NEVER_USE_THAT_ITEM:
            return "class";
        case EQUIP_ERR_NO_REQUIRED_PROFICIENCY:
        case EQUIP_ERR_CANT_EQUIP_SKILL:
            return "skill";
        case EQUIP_ERR_CANT_EQUIP_LEVEL_I:
            return "level";
        default:
            return "no";
    }
    // CanUseItem(ItemTemplate) skips the armor and weapon
    // proficiency that CanUseItem(Item*) checks, so plate
    // would pass for a mage.
    uint32 skill = tmpl->GetSkill();
    if (skill && bot->GetSkillValue(skill) == 0)
        return "proficiency";
    return "yes";
}

void QueueLootRollComment(
    Player* bot, Group* group, Roll const* roll,
    ItemTemplate const* tmpl, RollVote vote, uint32 index)
{
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
        "\"item_is_equipment\":"
            + std::string(IsEquipment(tmpl) ? "1" : "0") + ","
        "\"item_use\":\""
            + std::string(LootRollUse(bot, tmpl)) + "\","
        "\"item_required_level\":"
            + std::to_string(tmpl->RequiredLevel) + ","
        "\"roll_source_guid\":"
            + std::to_string(roll->itemGUID.GetRawValue()) + ","
        "\"roll_slot\":" + std::to_string(roll->itemSlot) + ","
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
    time_t now = time(nullptr);

    for (Roll const* roll : group->GetRolls())
    {
        if (!roll)
            continue;

        RollKey key{
            groupId, roll->itemGUID.GetRawValue(),
            roll->itemSlot};
        openRolls.insert(key);
        RollComments& state = _rollComments[key];

        ItemTemplate const* tmpl =
            sObjectMgr->GetItemTemplate(roll->itemid);
        // Equipment and other items have their own switch;
        // a switched-off kind skips the whole roll.
        bool kindEnabled = tmpl
            && (IsEquipment(tmpl)
                ? sLLMChatterConfig->_lootRollCommentEquipmentEnable
                : sLLMChatterConfig->_lootRollCommentOtherEnable);

        // Need votes go first when one scan finds both.
        // A vote is handled once, whether or not it is
        // commented, so a switched-off kind or a failed
        // chance roll is never reconsidered.
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
            if (!kindEnabled || !VoteCommentEnabled(vote))
                continue;
            if (urand(1, 100) > VoteCommentChance(vote))
                continue;

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
        if (needs.empty())
            continue;

        // A roll that already has a comment may finish up to
        // MaxPerItem. The first comment on any other roll
        // waits out the group's cooldown for its vote, so
        // several items dropping at once get comments on one
        // of them; Need and Greed keep separate cooldowns.
        for (BotVote const& bv : needs)
        {
            if (state.queued >= maxPerItem)
                break;
            if (state.queued == 0)
            {
                std::map<uint32, time_t>& cooldowns =
                    VoteCommentCooldowns(bv.vote);
                auto cd = cooldowns.find(groupId);
                if (cd != cooldowns.end()
                    && now - cd->second
                        < VoteCommentCooldown(bv.vote))
                    continue;
                cooldowns[groupId] = now;
            }
            QueueLootRollComment(
                bv.bot, group, roll, tmpl, bv.vote,
                state.queued);
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
        _needCommentCooldowns.clear();
        _greedCommentCooldowns.clear();
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

    // Forget rolls that have ended. Their comments that the
    // bridge has not picked up yet are cancelled: the roll
    // is decided, and its comment would arrive too late.
    for (auto it = _rollComments.begin();
         it != _rollComments.end();)
    {
        if (openRolls.count(it->first))
        {
            ++it;
            continue;
        }
        if (it->second.queued > 0)
        {
            auto const& [groupId, sourceGuid, slot] = it->first;
            CharacterDatabase.Execute(
                "UPDATE llm_chatter_events "
                "SET status = 'cancelled' "
                "WHERE event_type = 'bot_group_loot_roll' "
                "AND status = 'pending' "
                "AND JSON_EXTRACT(extra_data, '$.group_id') = {} "
                "AND JSON_EXTRACT(extra_data, "
                "'$.roll_source_guid') = {} "
                "AND JSON_EXTRACT(extra_data, '$.roll_slot') = {}",
                groupId, sourceGuid, uint32(slot));
        }
        it = _rollComments.erase(it);
    }

    time_t now = time(nullptr);
    PruneCommentCooldowns(NEED, now);
    PruneCommentCooldowns(GREED, now);
}

char const* LootRollCommentDropReason(
    std::string const& eventExtraData, uint32 botGuid)
{
    // extra_data comes back from a MySQL JSON column, so use
    // the whitespace-tolerant readers. Every roll comment
    // payload carries these fields; a row without them is
    // dropped rather than spoken unchecked.
    std::uint64_t groupId = 0;
    std::uint64_t sourceGuid = 0;
    std::uint64_t slot = 0;
    std::string voteName;
    if (!LLMChatterJson::ReadUInt64(
            eventExtraData, "group_id", groupId)
        || !LLMChatterJson::ReadUInt64(
            eventExtraData, "roll_source_guid", sourceGuid)
        || !LLMChatterJson::ReadUInt64(
            eventExtraData, "roll_slot", slot)
        || !LLMChatterJson::ReadString(
            eventExtraData, "roll_vote", voteName))
        return "loot_roll_closed";
    RollVote vote;
    if (voteName == "need")
        vote = NEED;
    else if (voteName == "greed")
        vote = GREED;
    else
        return "loot_roll_closed";

    Group* group = sGroupMgr->GetGroupByGUID(
        static_cast<ObjectGuid::LowType>(groupId));
    if (!group)
        return "loot_roll_closed";

    // Party lines go to bot->GetGroup(), so a bot that left
    // (and maybe joined another party) must not speak: its
    // roll stays open for the others.
    Player* bot = ObjectAccessor::FindPlayer(
        ObjectGuid::Create<HighGuid::Player>(botGuid));
    if (!bot || bot->GetGroup() != group)
        return "loot_roll_speaker_left";

    for (Roll const* roll : group->GetRolls())
    {
        if (!roll || roll->itemGUID.GetRawValue() != sourceGuid
            || roll->itemSlot != slot)
            continue;
        // A leaving member's vote is removed from the roll.
        auto voted = roll->playerVote.find(bot->GetGUID());
        if (voted == roll->playerVote.end()
            || voted->second != vote)
            return "loot_roll_speaker_left";
        return nullptr;
    }
    return "loot_roll_closed";
}
