/*
 * mod-llm-chatter - outbound message delivery ownership
 */

#include "LLMChatterConfig.h"
#include "LLMChatterDelivery.h"
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

#include <cstdio>

namespace
{
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
            || creature->IsInCombat())
            return true;

        creature->SetFacingTo(_orientation);
        return true;
    }

private:
    ObjectGuid _playerGuid;
    uint32 _spawnId;
    float _orientation;
};
} // namespace

void DeliverPendingMessagesImpl()
{
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 1, delivered_at = NOW() "
        "WHERE delivered = 0 "
        "AND deliver_at < DATE_SUB(NOW(), "
        "INTERVAL 60 SECOND)");

    QueryResult result;
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
            "m.sequence, m.event_id, e.zone_id "
            "FROM llm_chatter_messages m "
            "LEFT JOIN llm_chatter_events e "
            "ON m.event_id = e.id "
            "WHERE m.delivered = 0 "
            "AND m.deliver_at <= NOW() "
            "ORDER BY COALESCE(e.priority, 0) "
            "DESC, m.deliver_at ASC LIMIT 1");
    }
    else
    {
        result = CharacterDatabase.Query(
            "SELECT m.id, m.bot_guid, m.bot_name, "
            "m.message, m.channel, m.emote, "
            "m.npc_spawn_id, m.player_guid, "
            "m.sequence, m.event_id, e.zone_id "
            "FROM llm_chatter_messages m "
            "LEFT JOIN llm_chatter_events e "
            "ON m.event_id = e.id "
            "WHERE m.delivered = 0 "
            "AND m.deliver_at <= NOW() "
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
        "SET delivered = 1 "
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

    // Only mark delivered after a successful
    // send (or if the bot is unavailable and
    // retrying would not help).
    bool sent = false;
    bool botUnavailable =
        (channel == "msay")
            ? false
            : !bot || !bot->IsInWorld();

    ObjectGuid playerObjGuid =
        ObjectGuid::Create<HighGuid::Player>(
            playerGuid);
    Player* anchorPlayer =
        ObjectAccessor::FindPlayer(playerObjGuid);

    if (bot && bot->IsInWorld())
    {
        if (PlayerbotAI* ai =
                GET_PLAYERBOT_AI(bot))
        {
            if (sLLMChatterConfig->_facingEnable
                && !bot->IsInCombat())
            {
                bool faced = false;

                if (eventId > 0)
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
                    Group* grp = bot->GetGroup();
                    if (grp)
                    {
                        Player* mentioned =
                            FindMentionedMember(
                                bot, grp, message);
                        if (mentioned
                            && mentioned->IsInWorld())
                        {
                            bot->SetFacingToObject(
                                mentioned);
                            faced = true;
                        }
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

            if (channel == "party")
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
                        SendBotTextEmote(
                            bot, textEmoteId);
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
            !speaker || !speaker->IsAlive()
            || speaker->IsInCombat();
        if (speakerUnavailable)
            botUnavailable = true;
        else
        {
            float originalOrientation =
                speaker->GetOrientation();
            if (sLLMChatterConfig->_facingEnable)
            {
                bool faced = false;
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
                                speaker->SetFacingToObject(
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
                                speaker->SetFacingToObject(
                                    prevBot);
                                faced = true;
                            }
                        }
                    }
                }

                if (!faced)
                    speaker->SetFacingToObject(
                        anchorPlayer);
            }
            std::string msayMessage =
                ConvertAllLinks(message);
            speaker->Say(
                msayMessage, LANG_UNIVERSAL);
            sent = true;

            if (!emoteName.empty())
            {
                uint32 textEmoteId =
                    GetTextEmoteId(emoteName);
                if (textEmoteId)
                    SendUnitTextEmote(
                        speaker, textEmoteId,
                        anchorPlayer->GetName());
            }

            if (sLLMChatterConfig
                    ->_proxChatterFacingResetDelay
                > 0)
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

        RecordDeliveredProximityLine(
            eventId,
            playerGuid,
            eventZoneId,
            channel == "say" ? botGuid : 0,
            channel == "msay" ? npcSpawnId : 0,
            replyEligible,
            botName,
            message);
    }

    if (sent || botUnavailable)
    {
        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1, "
            "delivered_at = NOW() "
            "WHERE id = {}",
            messageId);
    }
    else
    {
        // Unclaim and reschedule for retry
        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 0, "
            "deliver_at = DATE_ADD("
            "NOW(), INTERVAL 5 SECOND) "
            "WHERE id = {}",
            messageId);
    }
}
