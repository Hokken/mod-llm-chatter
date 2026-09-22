/*
 * mod-llm-chatter - outbound message delivery ownership
 */

#include "LLMChatterConfig.h"
#include "Guild.h"
#include "LLMChatterBossDialogue.h"
#include "LLMChatterDelivery.h"
#include "LLMChatterGuild.h"
#include "LLMChatterProximity.h"
#include "LLMChatterShared.h"

#include "Channel.h"
#include "ChannelMgr.h"
#include "Chat.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Group.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "World.h"
#include "WorldSession.h"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <ctime>
#include <limits>
#include <map>

namespace
{
using SceneFacingKey = std::pair<uint32, uint32>;
struct SceneFacingState
{
    float orientation;
    time_t updatedAt;
    uint32 playerGuid;
};
static std::map<SceneFacingKey, SceneFacingState>
    _sceneOriginalFacings;

class DelayedNPCFacingResetEvent : public BasicEvent
{
public:
    DelayedNPCFacingResetEvent(
        ObjectGuid playerGuid, uint32 spawnId,
        float orientation)
        : _playerGuid(playerGuid)
        , _spawnId(spawnId)
        , _orientation(orientation)
    {
    }

    bool Execute(uint64 /*time*/,
                 uint32 /*diff*/) override
    {
        Player* player =
            ObjectAccessor::FindConnectedPlayer(
                _playerGuid);
        if (!player || !player->IsInWorld())
            return true;

        Creature* creature = FindCreatureBySpawnId(
            player->GetMap(), _spawnId);
        if (!creature || !creature->IsAlive()
            || creature->IsInCombat()
            || !IsSafeForChatterFacing(creature))
            return true;

        creature->SetFacingTo(_orientation);
        return true;
    }

private:
    ObjectGuid _playerGuid;
    uint32 _spawnId;
    float _orientation;
};

void ScheduleSceneFacingResets(
    uint32 eventId, uint32 delaySeconds)
{
    if (!eventId)
        return;

    for (auto it = _sceneOriginalFacings.begin();
         it != _sceneOriginalFacings.end();)
    {
        if (it->first.first != eventId)
        {
            ++it;
            continue;
        }

        uint32 spawnId = it->first.second;
        SceneFacingState const state = it->second;
        ObjectGuid playerGuid =
            ObjectGuid::Create<HighGuid::Player>(
                state.playerGuid);
        Player* player =
            ObjectAccessor::FindConnectedPlayer(
                playerGuid);
        Creature* creature = player && player->IsInWorld()
            ? FindCreatureBySpawnId(
                player->GetMap(), spawnId)
            : nullptr;
        if (creature && creature->IsInWorld())
        {
            creature->m_Events.AddEvent(
                new DelayedNPCFacingResetEvent(
                    playerGuid, spawnId,
                    state.orientation),
                creature->m_Events.CalculateTime(
                    delaySeconds * IN_MILLISECONDS));
        }
        it = _sceneOriginalFacings.erase(it);
    }
}

uint32 ExtractJsonUInt(
    std::string const& json, char const* key)
{
    if (!key || !*key)
        return 0;

    std::string marker = std::string("\"")
        + key + "\":";
    size_t pos = json.find(marker);
    if (pos == std::string::npos)
        return 0;
    pos += marker.size();
    while (pos < json.size()
        && std::isspace(
            static_cast<unsigned char>(json[pos])))
    {
        ++pos;
    }

    uint64 value = 0;
    bool foundDigit = false;
    while (pos < json.size()
        && std::isdigit(
            static_cast<unsigned char>(json[pos])))
    {
        foundDigit = true;
        value = value * 10
            + static_cast<uint64>(json[pos] - '0');
        if (value > std::numeric_limits<uint32>::max())
            return 0;
        ++pos;
    }
    return foundDigit ? static_cast<uint32>(value) : 0;
}

bool HasNonEmptyJsonString(
    std::string const& json, char const* key)
{
    if (!key || !*key)
        return false;

    std::string marker = std::string("\"")
        + key + "\":";
    size_t pos = json.find(marker);
    if (pos == std::string::npos)
        return false;
    pos += marker.size();
    while (pos < json.size()
        && std::isspace(
            static_cast<unsigned char>(json[pos])))
    {
        ++pos;
    }
    if (pos >= json.size() || json[pos] != '"')
        return false;
    ++pos;
    return pos < json.size() && json[pos] != '"';
}

bool IsDirectedProximityEvent(
    std::string const& eventType)
{
    return eventType == "proximity_player_say"
        || eventType == "proximity_player_conversation"
        || eventType == "proximity_player_emote";
}

bool IsFactionBoundReplyEvent(
    std::string const& eventType)
{
    return eventType == "player_general_msg"
        || eventType == "bot_group_player_msg"
        || eventType == "guild_player_message"
        || eventType == "guild_login_greeting";
}

void FinalizeDroppedMessage(
    uint32 messageId,
    uint32 eventId,
    uint32 sequence,
    std::string const& eventType,
    char const* reason)
{
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 1, delivered_at = NOW(), "
        "drop_reason = '{}' WHERE id = {}",
        EscapeString(reason ? reason : "delivery_failed"),
        messageId);

    if (!eventId || !IsDirectedProximityEvent(eventType))
        return;

    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 1, delivered_at = NOW(), "
        "drop_reason = 'cancelled_after_directed_drop' "
        "WHERE event_id = {} AND sequence > {} "
        "AND delivered = 0",
        eventId, sequence);

    ScheduleSceneFacingResets(
        eventId,
        sLLMChatterConfig
            ? sLLMChatterConfig
                  ->_proxChatterFacingResetDelay
            : 0);
}
} // namespace

void DeliverPendingMessagesImpl()
{
    time_t now = time(nullptr);
    for (auto it = _sceneOriginalFacings.begin();
         it != _sceneOriginalFacings.end();)
    {
        if (now - it->second.updatedAt > 120)
        {
            uint32 staleEventId = it->first.first;
            ScheduleSceneFacingResets(staleEventId, 0);
            it = _sceneOriginalFacings.begin();
        }
        else
            ++it;
    }

    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 1, delivered_at = NOW(), "
        "drop_reason = 'expired_before_delivery' "
        "WHERE delivered = 0 "
        "AND deliver_at < DATE_SUB(NOW(), "
        "INTERVAL 60 SECOND)");

    QueryResult result;
    // Proximity conversations are scheduled with
    // cumulative deliver_at gaps. If one line is
    // delivered late, gate the next line on the
    // previous line's actual delivered_at so the
    // conversation cannot bunch up afterward.
    if (sLLMChatterConfig->_prioritySystemEnable
        && sLLMChatterConfig
               ->_priorityDeliveryOrderEnable)
    {
        // Ambient rows flow through llm_chatter_queue
        // and therefore keep event_id = NULL.
        // Treat them as lowest priority via COALESCE.
        result = CharacterDatabase.Query(
            "SELECT m.id, m.bot_guid, "
            "m.bot_name, m.message, "
            "m.channel, m.emote, "
            "m.npc_spawn_id, m.player_guid, "
            "m.sequence, m.event_id, e.zone_id, "
            "m.group_id, m.delivery_policy, "
            "m.delivery_reason, m.owner_subsystem, "
            "m.addressee_player_guid, "
            "m.addressee_bot_guid, "
            "m.addressee_npc_spawn_id, "
            "e.map_id, e.extra_data, e.event_type, "
            "e.subject_guid "
            "FROM llm_chatter_messages m "
            "LEFT JOIN llm_chatter_events e "
            "ON m.event_id = e.id "
            "WHERE m.delivered = 0 "
            "AND m.deliver_at <= NOW() "
            "AND (m.channel NOT IN ('say', 'msay') "
            "OR m.sequence = 0 "
            "OR NOT EXISTS ("
            "SELECT 1 FROM llm_chatter_messages p "
            "WHERE p.event_id = m.event_id "
            "AND p.sequence = m.sequence - 1 "
            "AND (p.delivered = 0 "
            "OR p.delivered_at IS NULL "
            "OR TIMESTAMPDIFF(SECOND, "
            "p.delivered_at, NOW()) < "
            "TIMESTAMPDIFF(SECOND, "
            "p.deliver_at, m.deliver_at)))) "
            "ORDER BY COALESCE(e.priority, 0) "
            "DESC, m.deliver_at ASC LIMIT 1");
    }
    else
    {
        result = CharacterDatabase.Query(
            "SELECT m.id, m.bot_guid, m.bot_name, "
            "m.message, m.channel, m.emote, "
            "m.npc_spawn_id, m.player_guid, "
            "m.sequence, m.event_id, e.zone_id, "
            "m.group_id, m.delivery_policy, "
            "m.delivery_reason, m.owner_subsystem, "
            "m.addressee_player_guid, "
            "m.addressee_bot_guid, "
            "m.addressee_npc_spawn_id, "
            "e.map_id, e.extra_data, e.event_type, "
            "e.subject_guid "
            "FROM llm_chatter_messages m "
            "LEFT JOIN llm_chatter_events e "
            "ON m.event_id = e.id "
            "WHERE m.delivered = 0 "
            "AND m.deliver_at <= NOW() "
            "AND (m.channel NOT IN ('say', 'msay') "
            "OR m.sequence = 0 "
            "OR NOT EXISTS ("
            "SELECT 1 FROM llm_chatter_messages p "
            "WHERE p.event_id = m.event_id "
            "AND p.sequence = m.sequence - 1 "
            "AND (p.delivered = 0 "
            "OR p.delivered_at IS NULL "
            "OR TIMESTAMPDIFF(SECOND, "
            "p.delivered_at, NOW()) < "
            "TIMESTAMPDIFF(SECOND, "
            "p.deliver_at, m.deliver_at)))) "
            "ORDER BY m.deliver_at ASC LIMIT 1");
    }

    if (!result)
        return;

    Field* fields = result->Fetch();
    uint32 messageId = fields[0].Get<uint32>();

    // Claim the row immediately to prevent
    // double-delivery on the next poll tick.
    // Final delivered_at is set after send.
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 1, drop_reason = NULL "
        "WHERE id = {} AND delivered = 0",
        messageId);
    uint32 botGuid = fields[1].Get<uint32>();
    std::string botName =
        fields[2].Get<std::string>();
    std::string message =
        fields[3].Get<std::string>();
    std::string channel =
        fields[4].Get<std::string>();
    std::string emoteName =
        fields[5].IsNull()
            ? ""
            : fields[5].Get<std::string>();
    uint32 npcSpawnId =
        fields[6].IsNull()
            ? 0
            : fields[6].Get<uint32>();
    uint32 playerGuid =
        fields[7].IsNull()
            ? 0
            : fields[7].Get<uint32>();
    uint32 sequence =
        fields[8].IsNull()
            ? 0
            : fields[8].Get<uint32>();
    uint32 eventId =
        fields[9].IsNull()
            ? 0
            : fields[9].Get<uint32>();
    uint32 eventZoneId =
        fields[10].IsNull()
            ? 0
            : fields[10].Get<uint32>();
    uint32 groupId =
        fields[11].IsNull()
            ? 0
            : fields[11].Get<uint32>();
    std::string deliveryPolicy =
        fields[12].IsNull()
            ? ""
            : fields[12].Get<std::string>();
    std::string deliveryReason =
        fields[13].IsNull()
            ? ""
            : fields[13].Get<std::string>();
    std::string ownerSubsystem =
        fields[14].IsNull()
            ? ""
            : fields[14].Get<std::string>();
    uint32 addresseePlayerGuid =
        fields[15].IsNull()
            ? 0
            : fields[15].Get<uint32>();
    uint32 addresseeBotGuid =
        fields[16].IsNull()
            ? 0
            : fields[16].Get<uint32>();
    uint32 addresseeNPCSpawnId =
        fields[17].IsNull()
            ? 0
            : fields[17].Get<uint32>();
    bool hasEventMapId = !fields[18].IsNull();
    uint32 eventMapId =
        !hasEventMapId
            ? 0
            : fields[18].Get<uint32>();
    std::string eventExtraData =
        fields[19].IsNull()
            ? ""
            : fields[19].Get<std::string>();
    uint32 eventInstanceId =
        ExtractJsonUInt(
            eventExtraData, "instance_id");
    std::string eventType =
        fields[20].IsNull()
            ? ""
            : fields[20].Get<std::string>();
    uint32 eventSubjectGuid =
        fields[21].IsNull()
            ? 0
            : fields[21].Get<uint32>();

    // Master General-channel toggle. If General chatter is
    // disabled, deliberately consume any already-queued General
    // rows instead of speaking them. The row was claimed
    // (delivered = 1) above, so returning here drops it without
    // retry — flipping LLMChatter.GeneralChannel.Enable = 0 via
    // .reload config takes effect immediately for pending rows.
    if (channel == "general"
        && !sLLMChatterConfig->_generalChannelEnable)
    {
        FinalizeDroppedMessage(
            messageId, eventId, sequence,
            eventType, "general_disabled");
        return;
    }

    // Master GroupChatter toggle. Party/raid channels are
    // shared by group, raid-boss, and BG chatter, so we gate
    // on owner_subsystem (the authoritative classifier set at
    // insert time) rather than channel. Group-owned rows are
    // consumed when group chatter is disabled; raid/bg rows
    // (tagged 'raid'/'bg') are untouched. Takes effect
    // immediately for pending rows via .reload config.
    if (ownerSubsystem == "group"
        && !sLLMChatterConfig->_useGroupChatter)
    {
        FinalizeDroppedMessage(
            messageId, eventId, sequence,
            eventType, "group_chatter_disabled");
        return;
    }

    // Master ProximityChatter toggle. Consume already-queued
    // proximity rows (open-world say/msay) when proximity
    // chatter is disabled, so flipping
    // LLMChatter.ProximityChatter.Enable = 0 via .reload
    // config takes effect immediately for pending rows too.
    if ((ownerSubsystem == "proximity"
            || ownerSubsystem == "boss_dialogue")
        && !sLLMChatterConfig->_proxChatterEnable)
    {
        FinalizeDroppedMessage(
            messageId, eventId, sequence,
            eventType, "proximity_chatter_disabled");
        return;
    }
    if (ownerSubsystem == "boss_dialogue"
        && !sLLMChatterConfig->_proxBossDialogueEnable)
    {
        FinalizeDroppedMessage(
            messageId, eventId, sequence,
            eventType, "boss_dialogue_disabled");
        return;
    }

    // Master GuildChatter toggle. Consume already-queued
    // guild rows when guild chatter is disabled, so flipping
    // LLMChatter.GuildChatter.Enable = 0 takes effect
    // immediately for pending rows (otherwise the generic
    // retry path resets delivered = 0 and retries forever).
    if (ownerSubsystem == "guild"
        && !sLLMChatterConfig->_guildChatterEnable)
    {
        FinalizeDroppedMessage(
            messageId, eventId, sequence,
            eventType, "guild_chatter_disabled");
        return;
    }

    ObjectGuid guid =
        ObjectGuid::Create<HighGuid::Player>(
            botGuid);
    Player* bot =
        ObjectAccessor::FindPlayer(guid);

    if (bot)
    {
        WorldSession* session =
            bot->GetSession();
        if (session && session->PlayerLoading())
            bot = nullptr;
    }

    if (bot && eventSubjectGuid
        && IsFactionBoundReplyEvent(eventType))
    {
        Player* subject = ObjectAccessor::FindPlayer(
            ObjectGuid::Create<HighGuid::Player>(
                eventSubjectGuid));
        if (subject
            && subject->GetTeamId()
                != bot->GetTeamId())
        {
            FinalizeDroppedMessage(
                messageId, eventId, sequence,
                eventType, "faction_mismatch");
            return;
        }
    }

    // Only mark delivered after a successful
    // send (or if the bot is unavailable and
    // retrying would not help).
    bool sent = false;
    bool botUnavailable =
        (channel == "msay" || channel == "myell")
            ? false
            : !bot || !bot->IsInWorld();
    std::string dropReason = botUnavailable
        ? "speaker_unavailable" : "";

    ObjectGuid playerObjGuid =
        ObjectGuid::Create<HighGuid::Player>(
            playerGuid);
    Player* anchorPlayer =
        ObjectAccessor::FindPlayer(playerObjGuid);

    bool proximityLocal =
        ownerSubsystem == "proximity"
        && (channel == "say" || channel == "msay");
    bool addressedPlayerSay =
        (eventType == "proximity_player_say"
            || eventType
                == "proximity_player_conversation")
        && HasNonEmptyJsonString(
            eventExtraData, "addressed_name");
    bool allowMountedProximityBot =
        addressedPlayerSay
        || eventType == "proximity_player_emote"
        || eventType == "proximity_reply";
    float proximityRadius = static_cast<float>(
        std::max(
            sLLMChatterConfig->_proxChatterScanRadius,
            sLLMChatterConfig
                ->_proxChatterPlayerSayScanRadius));
    if (proximityLocal)
    {
        bool anchorValid =
            IsProximityAnchorEligible(anchorPlayer)
            && (!hasEventMapId
                || anchorPlayer->GetMapId()
                    == eventMapId)
            && (!eventInstanceId
                || (anchorPlayer->GetMap()
                    && anchorPlayer->GetMap()
                           ->GetInstanceId()
                        == eventInstanceId));
        if (!anchorValid)
        {
            bot = nullptr;
            anchorPlayer = nullptr;
            botUnavailable = true;
            dropReason = "anchor_player_invalid";
        }
        else if (channel == "say"
            && !IsProximityPlayerbotEligible(
                anchorPlayer, bot, proximityRadius,
                allowMountedProximityBot))
        {
            bot = nullptr;
            botUnavailable = true;
            dropReason = "speaker_ineligible";
        }
    }

    Unit* explicitAddressee = nullptr;
    if (anchorPlayer && anchorPlayer->IsInWorld())
    {
        if (addresseePlayerGuid
            == anchorPlayer->GetGUID().GetCounter())
        {
            explicitAddressee = anchorPlayer;
        }
        else if (addresseeNPCSpawnId)
        {
            explicitAddressee = FindCreatureBySpawnId(
                anchorPlayer->GetMap(),
                addresseeNPCSpawnId);
        }
        else if (addresseeBotGuid)
        {
            ObjectGuid addresseeGuid =
                ObjectGuid::Create<HighGuid::Player>(
                    addresseeBotGuid);
            Player* addresseeBot =
                ObjectAccessor::FindPlayer(addresseeGuid);
            if (addresseeBot && addresseeBot->IsInWorld()
                && addresseeBot->GetMap()
                    == anchorPlayer->GetMap())
            {
                explicitAddressee = addresseeBot;
            }
        }
    }

    if (bot && bot->IsInWorld())
    {
        if (PlayerbotAI* ai =
                GET_PLAYERBOT_AI(bot))
        {
            Player* emoteTarget = nullptr;
            if (channel == "party" || channel == "raid")
            {
                Group* grp = bot->GetGroup();
                if (grp)
                {
                    emoteTarget = FindMentionedMember(
                        bot, grp, message);
                    if (emoteTarget
                        && !emoteTarget->IsInWorld())
                        emoteTarget = nullptr;
                }
            }

            if (sLLMChatterConfig->_facingEnable
                && !bot->IsInCombat()
                && IsSafeForChatterFacing(bot))
            {
                bool faced = false;

                if (explicitAddressee
                    && explicitAddressee != bot
                    && explicitAddressee->IsAlive())
                {
                    bot->SetFacingToObject(
                        explicitAddressee);
                    faced = true;
                }

                if (!faced && eventId > 0)
                {
                    QueryResult evRes =
                        CharacterDatabase.Query(
                            "SELECT target_entry"
                            ", target_guid "
                            "FROM "
                            "llm_chatter_events "
                            "WHERE id = {}",
                            eventId);
                    if (evRes)
                    {
                        Field* ef =
                            evRes->Fetch();
                        uint32 tEntry =
                            ef[0].Get<uint32>();
                        uint32 tGuid =
                            ef[1].Get<uint32>();
                        if (tEntry > 0)
                        {
                            float range =
                                static_cast<float>(
                                    sLLMChatterConfig
                                        ->_nearbyObjectScanRadius);
                            // tGuid encodes creature vs GO:
                            // non-zero = creature entry
                            // (not an instance GUID).
                            WorldObject* target =
                                (tGuid > 0)
                                ? static_cast<
                                    WorldObject*>(
                                    bot->FindNearestCreature(
                                        tEntry,
                                        range))
                                : static_cast<
                                    WorldObject*>(
                                    bot->FindNearestGameObject(
                                        tEntry,
                                        range));
                            if (target)
                            {
                                bot->SetFacingToObject(
                                    target);
                                faced = true;
                            }
                        }
                    }
                }

                if (!faced
                    && channel == "say"
                    && anchorPlayer
                    && anchorPlayer->IsInWorld())
                {
                    if (sequence > 0 && eventId > 0)
                    {
                        QueryResult prevRes =
                            CharacterDatabase.Query(
                                "SELECT bot_guid,"
                                " npc_spawn_id"
                                " FROM llm_chatter_messages"
                                " WHERE event_id = {}"
                                " AND sequence = {}"
                                " LIMIT 1",
                                eventId, sequence - 1);
                        if (prevRes)
                        {
                            Field* pf = prevRes->Fetch();
                            uint32 prevBotGuid =
                                pf[0].IsNull()
                                    ? 0
                                    : pf[0].Get<uint32>();
                            uint32 prevNpcSpawnId =
                                pf[1].IsNull()
                                    ? 0
                                    : pf[1].Get<uint32>();
                            if (prevNpcSpawnId)
                            {
                                Creature* prevCreature =
                                    FindCreatureBySpawnId(
                                        anchorPlayer->GetMap(),
                                        prevNpcSpawnId);
                                if (prevCreature)
                                {
                                    bot->SetFacingToObject(
                                        prevCreature);
                                    faced = true;
                                }
                            }
                            else if (prevBotGuid)
                            {
                                ObjectGuid prevGuid =
                                    ObjectGuid::Create
                                        <HighGuid::Player>(
                                            prevBotGuid);
                                Player* prevBot =
                                    ObjectAccessor
                                        ::FindPlayer(
                                            prevGuid);
                                if (prevBot
                                    && prevBot->IsInWorld())
                                {
                                    bot->SetFacingToObject(
                                        prevBot);
                                    faced = true;
                                }
                            }
                        }
                    }

                    if (!faced)
                    {
                        bot->SetFacingToObject(
                            anchorPlayer);
                        faced = true;
                    }
                }

                if (!faced
                    && (channel == "party"
                        || channel == "raid"))
                {
                    if (emoteTarget)
                    {
                        bot->SetFacingToObject(
                            emoteTarget);
                        faced = true;
                    }
                }

                if (!faced
                    && (channel == "party"
                        || channel == "raid"))
                {
                    Group* grp = bot->GetGroup();
                    if (grp)
                    {
                        Player* nearest = nullptr;
                        float bestDist = 1e9f;
                        for (auto const& ref :
                            grp->GetMemberSlots())
                        {
                            if (ref.guid
                                == bot->GetGUID())
                                continue;

                            Player* p =
                                ObjectAccessor
                                    ::FindPlayer(
                                        ref.guid);
                            if (!p
                                || !p->IsInWorld()
                                || IsPlayerBot(p)
                                || p->GetMapId()
                                    != bot->GetMapId())
                                continue;

                            float d =
                                bot->GetDistance(p);
                            if (d < bestDist)
                            {
                                bestDist = d;
                                nearest = p;
                            }
                        }

                        if (nearest)
                        {
                            bot->SetFacingToObject(
                                nearest);
                            faced = true;
                        }
                    }
                }
            }

            std::string processedMessage =
                ConvertAllLinks(message);

            bool emoteOnly = processedMessage.empty()
                && !emoteName.empty()
                && (channel == "say"
                    || (channel == "party"
                        && bot->GetGroup()));
            if (emoteOnly)
            {
                bool bgEmoteBlocked =
                    (channel == "battleground"
                        || (channel == "party"
                            && bot->GetBattleground()))
                    && !IsBGAllowedEmote(emoteName);
                if (bgEmoteBlocked)
                {
                    botUnavailable = true;
                    dropReason = "bg_emote_blocked";
                }
                else
                {
                    uint32 textEmoteId =
                        GetTextEmoteId(emoteName);
                    if (textEmoteId)
                    {
                        std::string emoteTargetName =
                            explicitAddressee
                                ? explicitAddressee->GetName()
                                : (emoteTarget
                                    ? emoteTarget->GetName()
                                    : "");
                        if (emoteName == "talk"
                            && emoteTargetName.empty())
                        {
                            PlayUnitTextEmoteAnimation(
                                bot, textEmoteId);
                        }
                        else
                        {
                            SendBotTextEmote(
                                bot, textEmoteId,
                                emoteTargetName);
                        }
                        sent = true;
                    }
                    else
                    {
                        botUnavailable = true;
                        dropReason = "invalid_emote";
                    }
                }
            }
            else if (channel == "party")
            {
                Group* grp = bot->GetGroup();
                if (grp && grp->isRaidGroup())
                {
                    SendPartyMessageInstant(
                        bot, grp, processedMessage,
                        "");
                    sent = true;
                }
                else
                {
                    sent = ai->SayToParty(
                        processedMessage);
                }
            }
            else if (channel == "raid")
            {
                Group* grp = bot->GetGroup();
                if (grp)
                {
                    WorldPacket data;
                    ChatHandler::BuildChatPacket(
                        data,
                        CHAT_MSG_RAID,
                        bot->GetTeamId()
                                == TEAM_ALLIANCE
                            ? LANG_COMMON
                            : LANG_ORCISH,
                        bot, nullptr,
                        processedMessage);
                    grp->BroadcastPacket(
                        &data, false);
                    sent = true;
                }
            }
            else if (channel == "battleground")
            {
                Group* grp = bot->GetGroup();
                if (grp)
                {
                    WorldPacket data;
                    ChatHandler::BuildChatPacket(
                        data,
                        CHAT_MSG_BATTLEGROUND,
                        bot->GetTeamId()
                                == TEAM_ALLIANCE
                            ? LANG_COMMON
                            : LANG_ORCISH,
                        bot, nullptr,
                        processedMessage);
                    grp->BroadcastPacket(
                        &data, false);
                    sent = true;
                }
            }
            else if (channel == "say")
            {
                sent = ai->Say(processedMessage);
            }
            else if (channel == "guild")
            {
                // The master-toggle guard above already
                // consumes guild rows when the feature is
                // off, so we only reach here when enabled.
                Guild* guild = bot->GetGuild();
                WorldSession* session =
                    bot->GetSession();

                if (guild && session)
                {
                    guild->BroadcastToGuild(
                        session, false,
                        processedMessage.c_str(),
                        LANG_UNIVERSAL);
                    sent = true;
                }
                else
                {
                    // a missing guild/session is not
                    // transient -> do not retry forever.
                    botUnavailable = true;
                }
            }
            else if (channel == "yell")
            {
                if (!bot->IsAlive())
                {
                }
                else if (eventZoneId
                    && bot->GetZoneId()
                        != eventZoneId)
                {
                }
                else
                {
                    sent = ai->Yell(
                        processedMessage);
                }
            }
            else
            {
                // Force-enroll the bot in the
                // correct General channel before
                // sending. Bots selected by Python
                // may never have been enrolled if
                // they spawned in the zone without
                // a zone change.
                EnsureBotInGeneralChannel(bot);

                ChannelMgr* cMgr =
                    ChannelMgr::forTeam(
                        bot->GetTeamId());
                if (cMgr)
                {
                    uint32 zId = bot->GetZoneId();
                    AreaTableEntry const* ar =
                        sAreaTableStore
                            .LookupEntry(zId);
                    if (ar)
                    {
                        uint8 loc = sWorld
                            ->GetDefaultDbcLocale();
                        char const* zn =
                            ar->area_name[loc];
                        std::string zName =
                            zn ? zn : "";
                        if (zName.empty())
                        {
                            zn = ar->area_name[
                                LOCALE_enUS];
                            zName = zn ? zn : "";
                        }

                        ChatChannelsEntry const*
                            chEntry =
                                sChatChannelsStore
                                    .LookupEntry(
                                        ChatChannelId
                                            ::GENERAL);
                        if (chEntry && !zName.empty())
                        {
                            char buf[100];
                            std::snprintf(
                                buf, sizeof(buf),
                                chEntry
                                    ->pattern[loc],
                                zName.c_str());

                            std::string exactName(buf);
                            for (auto const& [k, ch] :
                                cMgr->GetChannels())
                            {
                                if (!ch)
                                    continue;
                                if (ch->GetName()
                                    != exactName)
                                    continue;
                                if (!bot->IsInChannel(
                                        ch))
                                    continue;

                                ch->Say(
                                    bot->GetGUID(),
                                    processedMessage
                                        .c_str(),
                                    LANG_UNIVERSAL);
                                sent = true;
                                break;
                            }
                        }
                    }
                }
            }

            if (sent
                && !emoteOnly
                && !emoteName.empty()
                && channel != "general"
                && channel != "yell")
            {
                if (!((channel == "battleground"
                        || (channel == "party"
                            && bot->GetBattleground()))
                        && !IsBGAllowedEmote(
                            emoteName)))
                {
                    uint32 textEmoteId =
                        GetTextEmoteId(emoteName);
                    if (textEmoteId)
                    {
                        std::string emoteTargetName =
                            explicitAddressee
                                ? explicitAddressee->GetName()
                                : (emoteTarget
                                    ? emoteTarget->GetName()
                                    : "");
                        if (emoteName == "talk"
                            && emoteTargetName.empty())
                        {
                            PlayUnitTextEmoteAnimation(
                                bot, textEmoteId);
                        }
                        else
                        {
                            SendBotTextEmote(
                                bot, textEmoteId,
                                emoteTargetName);
                        }
                    }
                }
            }
        }
    }
    else if (channel == "msay"
        && anchorPlayer
        && anchorPlayer->IsInWorld())
    {
        Creature* speaker = FindCreatureBySpawnId(
            anchorPlayer->GetMap(), npcSpawnId);
        bool speakerUnavailable =
            !IsProximityNPCEligible(
                anchorPlayer, speaker,
                proximityRadius);
        if (speakerUnavailable)
        {
            botUnavailable = true;
            dropReason = "npc_speaker_unavailable";
        }
        else
        {
            float originalOrientation =
                speaker->GetOrientation();
            SceneFacingKey facingKey = {
                eventId, npcSpawnId,
            };
            bool facingApplied = false;
            if (sLLMChatterConfig->_facingEnable
                && IsSafeForChatterFacing(speaker))
            {
                if (eventId
                    && sLLMChatterConfig
                        ->_proxChatterFacingResetDelay > 0)
                {
                    auto inserted =
                        _sceneOriginalFacings.emplace(
                            facingKey,
                            SceneFacingState{
                                originalOrientation,
                                now,
                                playerGuid});
                    originalOrientation = inserted.first
                        ->second.orientation;
                    inserted.first->second.updatedAt = now;
                }
                bool faced = false;
                if (explicitAddressee
                    && explicitAddressee != speaker
                    && explicitAddressee->IsAlive())
                {
                    speaker->SetFacingToObject(
                        explicitAddressee);
                    faced = true;
                    facingApplied = true;
                }
                if (!faced && sequence > 0 && eventId > 0)
                {
                    QueryResult prevRes =
                        CharacterDatabase.Query(
                            "SELECT bot_guid,"
                            " npc_spawn_id"
                            " FROM llm_chatter_messages"
                            " WHERE event_id = {}"
                            " AND sequence = {}"
                            " LIMIT 1",
                            eventId, sequence - 1);
                    if (prevRes)
                    {
                        Field* pf = prevRes->Fetch();
                        uint32 prevBotGuid =
                            pf[0].IsNull()
                                ? 0
                                : pf[0].Get<uint32>();
                        uint32 prevNpcSpawnId =
                            pf[1].IsNull()
                                ? 0
                                : pf[1].Get<uint32>();
                        if (prevNpcSpawnId)
                        {
                            Creature* prevCreature =
                                FindCreatureBySpawnId(
                                    anchorPlayer->GetMap(),
                                    prevNpcSpawnId);
                            if (prevCreature)
                            {
                                speaker->SetFacingToObject(
                                    prevCreature);
                                faced = true;
                                facingApplied = true;
                            }
                        }
                        else if (prevBotGuid)
                        {
                            ObjectGuid prevGuid =
                                ObjectGuid::Create
                                    <HighGuid::Player>(
                                        prevBotGuid);
                            Player* prevBot =
                                ObjectAccessor
                                    ::FindPlayer(
                                        prevGuid);
                            if (prevBot
                                && prevBot->IsInWorld())
                            {
                                speaker->SetFacingToObject(
                                    prevBot);
                                faced = true;
                                facingApplied = true;
                            }
                        }
                    }
                }

                if (!faced)
                {
                    speaker->SetFacingToObject(
                        anchorPlayer);
                    facingApplied = true;
                }
            }
            std::string msayMessage =
                ConvertAllLinks(message);
            bool msayEmoteOnly =
                msayMessage.empty()
                && !emoteName.empty();
            if (!msayMessage.empty())
            {
                speaker->Say(
                    msayMessage, LANG_UNIVERSAL);
                sent = true;
            }

            if (!emoteName.empty())
            {
                uint32 textEmoteId =
                    GetTextEmoteId(emoteName);
                if (textEmoteId)
                {
                    std::string targetName =
                        explicitAddressee
                            ? explicitAddressee->GetName()
                            : anchorPlayer->GetName();
                    SendUnitTextEmote(
                        speaker, textEmoteId,
                        targetName);
                    sent = true;
                }
                else if (msayEmoteOnly)
                {
                    botUnavailable = true;
                    dropReason = "invalid_emote";
                }
            }

            if (sLLMChatterConfig
                    ->_proxChatterFacingResetDelay > 0)
            {
                bool hasLaterLine = false;
                if (eventId)
                {
                    QueryResult laterLine =
                        CharacterDatabase.Query(
                        "SELECT 1 FROM llm_chatter_messages "
                        "WHERE event_id = {} AND sequence > {} "
                        "AND delivered = 0 LIMIT 1",
                        eventId, sequence);
                    hasLaterLine = static_cast<bool>(laterLine);
                }
                if (!hasLaterLine && eventId)
                {
                    ScheduleSceneFacingResets(
                        eventId,
                        sLLMChatterConfig
                            ->_proxChatterFacingResetDelay);
                }
                else if (!hasLaterLine && facingApplied)
                {
                    speaker->m_Events.AddEvent(
                        new DelayedNPCFacingResetEvent(
                            playerObjGuid,
                            npcSpawnId,
                            originalOrientation),
                        speaker->m_Events.CalculateTime(
                            sLLMChatterConfig
                                    ->_proxChatterFacingResetDelay
                                * IN_MILLISECONDS));
                }
            }
        }
    }

    else if (channel == "myell"
        && ownerSubsystem == "boss_dialogue"
        && anchorPlayer
        && anchorPlayer->IsInWorld())
    {
        bool anchorValid =
            IsProximityAnchorEligible(anchorPlayer)
            && (!hasEventMapId
                || anchorPlayer->GetMapId() == eventMapId)
            && (!eventInstanceId
                || (anchorPlayer->GetMap()
                    && anchorPlayer->GetMap()->GetInstanceId()
                        == eventInstanceId));
        Creature* speaker = anchorValid
            ? FindCreatureBySpawnId(
                anchorPlayer->GetMap(), npcSpawnId)
            : nullptr;
        bool speakerUnavailable =
            !anchorValid
            || !IsBossDialogueSpeakerEligible(
                anchorPlayer,
                speaker,
                static_cast<float>(
                    sLLMChatterConfig
                        ->_proxBossApproachMaxRadius));
        if (speakerUnavailable)
        {
            botUnavailable = true;
            dropReason = "boss_speaker_unavailable";
        }
        else
        {
            speaker->Yell(
                ConvertAllLinks(message),
                LANG_UNIVERSAL);
            sent = true;
        }
    }

    if (sent && eventId > 0
        && playerGuid > 0
        && (channel == "say" || channel == "msay"))
    {
        bool replyEligible = true;
        QueryResult pendingRes =
            CharacterDatabase.Query(
                "SELECT 1 FROM llm_chatter_messages "
                "WHERE event_id = {} "
                "AND sequence > {} "
                "AND delivered = 0 LIMIT 1",
                eventId, sequence);
        if (pendingRes)
            replyEligible = false;

        std::string deliveredContext = message;
        if (deliveredContext.empty()
            && !emoteName.empty())
        {
            deliveredContext = std::string(
                "[performed /") + emoteName + "]";
        }
        RecordDeliveredProximityLine(
            eventId,
            playerGuid,
            eventZoneId,
            eventMapId,
            eventInstanceId,
            channel == "say" ? botGuid : 0,
            channel == "msay" ? npcSpawnId : 0,
            replyEligible,
            botName,
            deliveredContext);
    }

    if (sent && channel == "party")
    {
        uint32 gateGroupId = groupId;
        if (gateGroupId == 0 && bot)
        {
            if (Group* grp = bot->GetGroup())
                gateGroupId = grp->GetGUID().GetCounter();
        }

        RecordPartyChatGateActivity(
            gateGroupId,
            deliveryPolicy.empty()
                ? "contextual" : deliveryPolicy,
            deliveryReason.empty()
                ? "party_delivery" : deliveryReason);
    }

    if (sent && channel == "guild" && bot)
    {
        RecordDeliveredGuildLine(
            bot->GetGuildId(),
            eventId,
            botGuid,
            botName,
            message);
    }

    if (sent)
    {
        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1, "
            "delivered_at = NOW(), "
            "drop_reason = NULL "
            "WHERE id = {}",
            messageId);
    }
    else if (botUnavailable)
    {
        FinalizeDroppedMessage(
            messageId, eventId, sequence,
            eventType,
            dropReason.empty()
                ? "speaker_unavailable"
                : dropReason.c_str());
    }
    else
    {
        // Unclaim and reschedule for retry
        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 0, "
            "drop_reason = NULL, "
            "deliver_at = DATE_ADD("
            "NOW(), INTERVAL 5 SECOND) "
            "WHERE id = {}",
            messageId);
    }
}
