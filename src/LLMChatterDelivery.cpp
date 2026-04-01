/*
 * mod-llm-chatter - outbound message delivery ownership
 */

#include "LLMChatterConfig.h"
#include "LLMChatterDelivery.h"
#include "LLMChatterShared.h"

#include "Channel.h"
#include "ChannelMgr.h"
#include "Chat.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "World.h"
#include "WorldSession.h"

#include <cstdio>

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
            "m.event_id, e.zone_id "
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
            "m.event_id, e.zone_id "
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
    uint32 eventId =
        fields[6].IsNull()
            ? 0
            : fields[6].Get<uint32>();
    uint32 eventZoneId =
        fields[7].IsNull()
            ? 0
            : fields[7].Get<uint32>();

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
        !bot || !bot->IsInWorld();

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
