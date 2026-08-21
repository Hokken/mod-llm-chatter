/*
 * mod-llm-chatter - group subsystem ownership
 *
 * After Phase 5 extraction this file retains:
 *   - shared state variable definitions
 *   - shared helper functions used across group TUs
 *   - pre-cache instant reaction helpers
 *   - named boss cache
 *   - CleanupGroupSession() coordinator
 *   - thin PlayerScript shell wrappers
 *   - AddLLMChatterGroupScripts() registration
 *
 * Extracted to separate files:
 *   - LLMChatterGroupJoin.cpp: join batching,
 *     GroupScript, FlushGroupJoinBatches()
 *   - LLMChatterGroupEmote.cpp: emote statics,
 *     delayed events, emote handlers,
 *     EvictEmoteCooldowns()
 *   - LLMChatterGroupQuest.cpp: quest batching,
 *     CreatureScript, FlushQuestAcceptBatches()
 *   - LLMChatterGroupCombat.cpp:
 *     PlayerScript hook implementations,
 *     HandleGroupPlayerUpdateZone(),
 *     CheckGroupCombatState()
 */

#include "LLMChatterConfig.h"
#include "LLMChatterBG.h"
#include "LLMChatterGroup.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "AchievementMgr.h"
#include "Battleground.h"
#include "CellImpl.h"
#include "Chat.h"
#include "Channel.h"
#include "ChannelMgr.h"
#include "Config.h"
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
#include "WorldPacket.h"
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
#include <utility>
#include <vector>

namespace
{
    char const* const kMultiBotPrefix = "MBOT";
    char const* const kMultiBotBridgeName =
        "mod-llm-chatter";
    char const* const kMultiBotProtocolVersion = "1";
    char const kMultiBotSeparator = '~';

    // Upstream AzerothCore renamed creature.id1 -> creature.id
    // (PR #25197, migration 2026_06_16_00). Resolve the column
    // name once (lazy, thread-safe magic static) so our SQL
    // works on both the old and updated core source.
    std::string const& GetCreatureEntryColumn()
    {
        static std::string const column = []() -> std::string
        {
            if (QueryResult r = WorldDatabase.Query(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = 'acore_world' "
                    "AND TABLE_NAME = 'creature' "
                    "AND COLUMN_NAME IN ('id', 'id1') "
                    "ORDER BY (COLUMN_NAME = 'id') DESC LIMIT 1"))
                return (*r)[0].Get<std::string>();
            return "id";
        }();
        return column;
    }

    std::string TrimMultiBot(std::string const& value)
    {
        size_t start = value.find_first_not_of(" \t\r\n");
        if (start == std::string::npos)
            return "";

        size_t end = value.find_last_not_of(" \t\r\n");
        return value.substr(start, end - start + 1);
    }

    std::string ToUpperMultiBot(std::string value)
    {
        std::transform(
            value.begin(), value.end(), value.begin(),
            [](unsigned char c)
            {
                return static_cast<char>(std::toupper(c));
            });
        return value;
    }

    std::pair<std::string, std::string> SplitMultiBotOnce(
        std::string const& value, char separator)
    {
        size_t pos = value.find(separator);
        if (pos == std::string::npos)
            return {value, ""};

        return {
            value.substr(0, pos),
            value.substr(pos + 1)};
    }

    std::string EncodeMultiBotField(std::string const& value)
    {
        static char const* hex = "0123456789ABCDEF";
        std::string out;
        out.reserve(value.size());

        for (unsigned char c : value)
        {
            if (c == '%' || c == '~'
                || c == '\r' || c == '\n')
            {
                out.push_back('%');
                out.push_back(hex[(c >> 4) & 0x0F]);
                out.push_back(hex[c & 0x0F]);
                continue;
            }

            out.push_back(static_cast<char>(c));
        }

        return out;
    }

    bool IsMultiBotCompatEnabled()
    {
        return sConfigMgr->GetOption<bool>(
            "LLMChatter.MultiBotCompat.Enable", false);
    }

    bool TryExtractMultiBotPayload(
        uint32 language, std::string const& msg,
        std::string& payload)
    {
        if (language != LANG_ADDON)
            return false;

        std::string const trimmed = TrimMultiBot(msg);
        std::string const prefix =
            std::string(kMultiBotPrefix) + "\t";
        if (trimmed.rfind(prefix, 0) != 0)
            return false;

        payload = TrimMultiBot(trimmed.substr(prefix.size()));
        return !payload.empty();
    }

    ChatMsg NormalizeMultiBotReplyType(uint32 type)
    {
        switch (type)
        {
            case CHAT_MSG_PARTY:
            case CHAT_MSG_PARTY_LEADER:
            case CHAT_MSG_RAID:
            case CHAT_MSG_RAID_LEADER:
            case CHAT_MSG_GUILD:
            case CHAT_MSG_OFFICER:
            case CHAT_MSG_WHISPER:
            case CHAT_MSG_CHANNEL:
                return static_cast<ChatMsg>(type);
            default:
                return CHAT_MSG_WHISPER;
        }
    }

    void SendMultiBotAddonPacket(
        Player* player, ChatMsg chatType,
        std::string const& opcode,
        std::string const& payload = "")
    {
        if (!player || !player->GetSession())
            return;

        std::string wire =
            std::string(kMultiBotPrefix) + "\t" + opcode;
        if (!payload.empty())
        {
            wire += std::string(1, kMultiBotSeparator)
                + payload;
        }

        if (sLLMChatterConfig
            && sLLMChatterConfig->IsDebugLog())
        {
            LOG_INFO(
                "module",
                "LLMChatter: MultiBotCompat TX [{}] type={}",
                wire, static_cast<uint32>(chatType));
        }

        WorldPacket data;
        ChatHandler::BuildChatPacket(
            data, chatType, LANG_ADDON,
            player, nullptr, wire.c_str());
        player->SendDirectMessage(&data);
    }

    uint32 GetMultiBotPct(uint32 current, uint32 max)
    {
        if (!max)
            return 0;

        return static_cast<uint32>(
            (current * 100u) / max);
    }

    void AppendMultiBotVisibleBot(
        Player* bot, std::vector<Player*>& bots,
        std::set<ObjectGuid>& seen)
    {
        if (!bot || !bot->IsInWorld()
            || !sPlayerbotsMgr.GetPlayerbotAI(bot))
            return;

        if (!seen.insert(bot->GetGUID()).second)
            return;

        bots.push_back(bot);
    }

    bool CanExposeRandomMultiBot(
        Player* requester, Player* bot)
    {
        if (!requester || !bot)
            return false;

        PlayerbotAI* botAI =
            sPlayerbotsMgr.GetPlayerbotAI(bot);
        if (!botAI)
            return false;

        Group* requesterGroup = requester->GetGroup();
        if (requesterGroup
            && bot->GetGroup() == requesterGroup)
            return true;

        return botAI->GetMaster() == requester;
    }

    std::vector<Player*> GetMultiBotVisibleBots(
        Player* player)
    {
        std::vector<Player*> bots;
        std::set<ObjectGuid> seen;
        if (!player)
            return bots;

        if (PlayerbotMgr* mgr =
                sPlayerbotsMgr.GetPlayerbotMgr(player))
        {
            for (PlayerBotMap::const_iterator it =
                     mgr->GetPlayerBotsBegin();
                 it != mgr->GetPlayerBotsEnd(); ++it)
            {
                AppendMultiBotVisibleBot(
                    it->second, bots, seen);
            }
        }

        if (Group* group = player->GetGroup())
        {
            for (GroupReference* itr =
                     group->GetFirstMember();
                 itr != nullptr; itr = itr->next())
            {
                AppendMultiBotVisibleBot(
                    itr->GetSource(), bots, seen);
            }
        }

        for (PlayerBotMap::const_iterator it =
                 sRandomPlayerbotMgr.GetPlayerBotsBegin();
             it != sRandomPlayerbotMgr.GetPlayerBotsEnd();
             ++it)
        {
            Player* bot = it->second;
            if (CanExposeRandomMultiBot(player, bot))
                AppendMultiBotVisibleBot(bot, bots, seen);
        }

        return bots;
    }

    Player* FindMultiBotByName(
        Player* player, std::string const& botName)
    {
        std::string const wanted = TrimMultiBot(botName);
        if (wanted.empty())
            return nullptr;

        for (Player* bot : GetMultiBotVisibleBots(player))
        {
            if (bot->GetName() == wanted)
                return bot;
        }

        return nullptr;
    }

    std::string JoinMultiBotStrategies(
        std::vector<std::string> const& strategies)
    {
        std::ostringstream out;
        for (size_t i = 0; i < strategies.size(); ++i)
        {
            if (i)
                out << ", ";

            out << strategies[i];
        }

        return out.str();
    }

    std::string BuildMultiBotRosterPayload(Player* player)
    {
        std::ostringstream out;
        bool first = true;

        for (Player* bot : GetMultiBotVisibleBots(player))
        {
            if (!first)
                out << ';';
            first = false;

            out << bot->GetName()
                << ',' << static_cast<uint32>(bot->getClass())
                << ',' << static_cast<uint32>(bot->GetLevel())
                << ',' << static_cast<uint32>(bot->GetMapId())
                << ',' << (bot->IsAlive() ? '1' : '0')
                << ',' << GetMultiBotPct(
                    bot->GetHealth(), bot->GetMaxHealth())
                << ',' << GetMultiBotPct(
                    bot->GetPower(POWER_MANA),
                    bot->GetMaxPower(POWER_MANA));
        }

        return out.str();
    }

    std::string BuildMultiBotDetailPayload(Player* bot)
    {
        if (!bot)
            return "";

        std::string const gender =
            static_cast<uint8>(bot->getGender()) == 1
                ? "Female" : "Male";

        std::ostringstream out;
        out << EncodeMultiBotField(bot->GetName())
            << kMultiBotSeparator
            << EncodeMultiBotField(
                GetRaceName(static_cast<uint8>(
                    bot->getRace())))
            << kMultiBotSeparator
            << EncodeMultiBotField(gender)
            << kMultiBotSeparator
            << EncodeMultiBotField(
                GetChatterClassName(static_cast<uint8>(
                    bot->getClass())))
            << kMultiBotSeparator
            << static_cast<uint32>(bot->GetLevel())
            << kMultiBotSeparator << 0
            << kMultiBotSeparator << 0
            << kMultiBotSeparator << 0
            << kMultiBotSeparator << 0;

        return out.str();
    }

    std::string BuildMultiBotDetailPayload(
        Player* player, std::string const& botName)
    {
        return BuildMultiBotDetailPayload(
            FindMultiBotByName(player, botName));
    }

    void SendMultiBotDetailPackets(
        Player* player, ChatMsg replyType)
    {
        bool sent = false;
        for (Player* bot : GetMultiBotVisibleBots(player))
        {
            std::string const payload =
                BuildMultiBotDetailPayload(bot);
            if (payload.empty())
                continue;

            SendMultiBotAddonPacket(
                player, replyType, "DETAIL", payload);
            sent = true;
        }

        if (!sent)
        {
            SendMultiBotAddonPacket(
                player, replyType, "DETAILS", "");
        }
    }

    std::string BuildMultiBotStatePayloadForBot(
        Player* bot, std::string const& fallbackName)
    {
        if (!bot)
        {
            return TrimMultiBot(fallbackName)
                + std::string(1, kMultiBotSeparator)
                + std::string(1, kMultiBotSeparator);
        }

        PlayerbotAI* botAI =
            sPlayerbotsMgr.GetPlayerbotAI(bot);
        if (!botAI)
        {
            return bot->GetName()
                + std::string(1, kMultiBotSeparator)
                + std::string(1, kMultiBotSeparator);
        }

        std::ostringstream out;
        out << bot->GetName()
            << kMultiBotSeparator
            << JoinMultiBotStrategies(
                botAI->GetStrategies(BOT_STATE_COMBAT))
            << kMultiBotSeparator
            << JoinMultiBotStrategies(
                botAI->GetStrategies(
                    BOT_STATE_NON_COMBAT));

        return out.str();
    }

    std::string BuildMultiBotStatePayload(
        Player* player, std::string const& botName)
    {
        return BuildMultiBotStatePayloadForBot(
            FindMultiBotByName(player, botName), botName);
    }

    void SendMultiBotStatePackets(
        Player* player, ChatMsg replyType)
    {
        bool sent = false;
        for (Player* bot : GetMultiBotVisibleBots(player))
        {
            SendMultiBotAddonPacket(
                player, replyType, "STATE",
                BuildMultiBotStatePayloadForBot(
                    bot, bot->GetName()));
            sent = true;
        }

        if (!sent)
        {
            SendMultiBotAddonPacket(
                player, replyType, "STATES", "");
        }
    }

    bool HandleMultiBotOpcode(
        Player* player, ChatMsg replyType,
        std::string const& opcode,
        std::string const& payload)
    {
        std::string const normalized =
            ToUpperMultiBot(TrimMultiBot(opcode));

        if (normalized == "HELLO")
        {
            SendMultiBotAddonPacket(
                player, replyType, "HELLO_ACK",
                std::string(kMultiBotProtocolVersion)
                    + kMultiBotSeparator
                    + kMultiBotBridgeName);
            return true;
        }

        if (normalized == "PING")
        {
            SendMultiBotAddonPacket(
                player, replyType, "PONG", payload);
            return true;
        }

        if (normalized != "GET")
            return false;

        std::pair<std::string, std::string> const request =
            SplitMultiBotOnce(payload, kMultiBotSeparator);
        std::string const requestType =
            ToUpperMultiBot(TrimMultiBot(request.first));

        if (requestType == "ROSTER")
        {
            SendMultiBotAddonPacket(
                player, replyType, "ROSTER",
                BuildMultiBotRosterPayload(player));
            return true;
        }

        if (requestType == "STATE")
        {
            SendMultiBotAddonPacket(
                player, replyType, "STATE",
                BuildMultiBotStatePayload(
                    player, request.second));
            return true;
        }

        if (requestType == "STATES")
        {
            SendMultiBotStatePackets(player, replyType);
            return true;
        }

        if (requestType == "DETAIL")
        {
            SendMultiBotAddonPacket(
                player, replyType, "DETAIL",
                BuildMultiBotDetailPayload(
                    player, request.second));
            return true;
        }

        if (requestType == "DETAILS")
        {
            SendMultiBotDetailPackets(player, replyType);
            return true;
        }

        return false;
    }

    bool TryHandleMultiBotCompatChat(
        Player* player, uint32 type, uint32 language,
        std::string& msg)
    {
        if (!IsMultiBotCompatEnabled() || !player)
            return false;

        std::string payload;
        if (!TryExtractMultiBotPayload(
                language, msg, payload))
            return false;

        if (sLLMChatterConfig
            && sLLMChatterConfig->IsDebugLog())
        {
            LOG_INFO(
                "module",
                "LLMChatter: MultiBotCompat RX [{}] type={}",
                payload, type);
        }

        std::pair<std::string, std::string> const packet =
            SplitMultiBotOnce(payload, kMultiBotSeparator);
        return HandleMultiBotOpcode(
            player, NormalizeMultiBotReplyType(type),
            packet.first, packet.second);
    }
}

// ============================================================================
// PRE-CACHE INSTANT REACTION HELPERS
// ============================================================================

// Consume one cached response for a bot+category.
// Returns true on hit, populating outMessage/outEmote.
// Uses DirectExecute (sync) for UPDATE to prevent
// double-consume if two hooks fire same tick.
bool TryConsumeCachedReaction(
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
void ResolvePlaceholders(
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

    // Clamp to max message length (UTF-8 safe: never
    // split a multi-byte character)
    message = NormalizeChatTextForDb(
        message, sLLMChatterConfig->_maxMessageLength);
}

// Record a pre-cached message in chat history
// so Python sees it for conversation context.
void RecordCachedChatHistory(
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
// SHARED GROUP HELPERS
// ============================================================================

// Check if a group has at least one real (non-bot) player
bool GroupHasRealPlayer(Group* group)
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
Player* GetRandomBotInGroup(
    Group* group, Player* exclude)
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
uint32 CountBotsInGroup(Group* group)
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

// ============================================================================
// SHARED STATE VARIABLE DEFINITIONS
//
// These are the canonical definitions for all extern
// declarations in LLMChatterGroupInternal.h.
// ============================================================================

// -- Group join batching --
std::unordered_map<uint32, GroupJoinBatch>
    _groupJoinBatches;
std::mutex _groupJoinBatchMutex;
std::unordered_set<uint32>
    _groupJoinFlushed;
std::unordered_set<uint32>
    _greetedBotGuids;
std::unordered_map<uint32,
    std::vector<uint32>> _groupGreetedBots;

// -- Quest accept batching --
std::unordered_map<uint32, QuestAcceptBatch>
    _questAcceptBatches;
std::mutex _questBatchMutex;

// -- Per-group+quest timestamp/dedup maps --
std::unordered_map<uint64, time_t>
    _questAcceptTimestamps;
std::unordered_map<uint64, time_t>
    _questCompleteCd;

// -- Named boss entries --
std::unordered_set<uint32> _namedBossEntries;

// -- Per-group cooldown maps --
std::map<uint32, time_t> _groupKillCooldowns;
std::map<uint32, time_t> _groupDeathCooldowns;
std::map<uint32, time_t> _groupLootCooldowns;
std::map<uint32, time_t> _groupPlayerMsgCooldowns;
std::map<uint32, time_t> _groupCombatCooldowns;
std::unordered_map<uint32, time_t>
    _groupSpellCooldowns;
std::map<uint32, time_t>
    _groupQuestObjCooldowns;
std::map<uint32, time_t>
    _groupResurrectCooldowns;
std::map<uint32, time_t>
    _groupZoneCooldowns;
std::map<uint32, time_t>
    _groupDungeonCooldowns;
std::map<uint32, time_t>
    _groupWipeCooldowns;
std::map<uint32, time_t>
    _groupCorpseRunCooldowns;

// -- Per-bot state callout cooldowns --
std::map<uint32, time_t>
    _botLowHealthCooldowns;
std::map<uint32, time_t>
    _botOomCooldowns;
std::map<uint32, time_t>
    _botAggroCooldowns;

// -- Emote cooldown maps --
std::unordered_map<uint32, time_t>
    _emoteReactCooldowns;
std::unordered_map<uint32, time_t>
    _emoteObserverCooldowns;
std::unordered_map<uint32, time_t>
    _emoteVerbalCooldowns;
std::unordered_map<uint32, time_t>
    _creatureEmoteCooldowns;

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

// ============================================================================
// NAMED BOSS CACHE
// ============================================================================

void LoadNamedBossCache()
{
    _namedBossEntries.clear();
    // Named bosses: CreatureImmunitiesId > 0 and
    // only 1 spawn on their map (filters out trash
    // like Molten Elementals that have immunities
    // but spawn many times)
    std::string query =
        "SELECT entry FROM ("
        "  SELECT ct.entry, ct.`rank`,"
        "    ct.CreatureImmunitiesId,"
        "    COUNT(*) AS spawns"
        "  FROM creature_template ct"
        "  JOIN creature c ON c." + GetCreatureEntryColumn() + " = ct.entry"
        "  WHERE ct.`rank` = 3"
        "    OR ct.CreatureImmunitiesId > 0"
        "  GROUP BY ct.entry, c.map"
        "  HAVING ct.`rank` = 3 OR COUNT(*) = 1"
        ") AS bosses";
    QueryResult result = WorldDatabase.Query(query);
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

// ============================================================================
// PLAYERBOT COMMAND FILTER
// ============================================================================

// Pre-enqueue filter for known playerbot control
// messages. Keep this aligned with the Python-side
// PLAYERBOT_COMMANDS fallback list so command
// traffic does not enter the chatter event queue.
bool IsLikelyPlayerbotControlCommand(
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

    // Playerbots @target selector syntax is control traffic,
    // not conversational content.
    if (msg[0] == '@')
    {
        size_t selectorEnd = msg.find_first_of(" \t");
        std::string selector =
            msg.substr(0, selectorEnd);

        static std::unordered_set<std::string>
            selectorPrefixes = {
                "@tank", "@dps", "@heal",
                "@ranged", "@melee",
                "@rangeddps", "@meleedps",
                "@dk", "@druid", "@hunter",
                "@mage", "@paladin", "@priest",
                "@rogue", "@shaman", "@warlock",
                "@warrior",
                "@star", "@circle", "@diamond",
                "@triangle", "@moon", "@square",
                "@cross", "@skull",
                "@hpal", "@ppal", "@rpal",
                "@disc", "@hpr", "@spr",
                "@arc", "@frost", "@fire",
                "@arms", "@fury", "@pwar",
                "@affl", "@demo", "@dest",
                "@ele", "@enh", "@rsha",
                "@bal", "@rdru",
                "@bmh", "@mmh", "@svh",
                "@mut", "@comb", "@sub",
                "@fdk", "@udk"
            };

        bool knownSelector =
            selectorPrefixes.find(selector)
                != selectorPrefixes.end()
            || selector.rfind("@group", 0) == 0
            || selector.rfind("@aura", 0) == 0
            || selector.rfind("@noaura", 0) == 0
            || selector.rfind("@aggroby", 0) == 0;

        auto isDigits = [](std::string const& value)
        {
            if (value.empty())
                return false;

            return std::all_of(
                value.begin(), value.end(),
                [](unsigned char c)
                {
                    return std::isdigit(c) != 0;
                });
        };

        if (!knownSelector && selector.size() > 1)
        {
            std::string levelSelector =
                selector.substr(1);
            size_t dash = levelSelector.find('-');

            knownSelector =
                isDigits(levelSelector)
                || (dash != std::string::npos
                    && isDigits(
                        levelSelector.substr(0, dash))
                    && isDigits(
                        levelSelector.substr(dash + 1)));
        }

        if (knownSelector)
            return true;

        // Also support @command forms such as @follow while
        // preserving normal @name conversation.
        msg.erase(0, 1);
        size_t commandStart =
            msg.find_first_not_of(" \t");
        if (commandStart == std::string::npos)
            return true;
        if (commandStart > 0)
            msg.erase(0, commandStart);
    }

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

// ============================================================================
// CLEANUP COORDINATOR
// ============================================================================

// Clean up traits when group no longer qualifies
void CleanupGroupSession(uint32 groupId)
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

// ============================================================================
// PlayerScript hook implementation declarations
// (owned by LLMChatterGroupCombat.cpp)
// ============================================================================

void HandleGroupCreatureKillImpl(
    Player* killer, Creature* killed);
void HandleGroupPlayerKilledByCreatureImpl(
    Creature* killer, Player* killed);
void HandleGroupLootEventImpl(
    Player* player, Item* item);
void HandleGroupPlayerEnterCombatImpl(
    Player* player, Unit* enemy);
void HandleGroupPlayerBeforeSendChatMessageImpl(
    Player* player, uint32& type, uint32& lang,
    std::string& msg);
void HandleGroupPlayerLevelChangedImpl(
    Player* player, uint8 oldLevel);
bool HandleGroupPlayerBeforeQuestCompleteImpl(
    Player* player, uint32 questId);
void HandleGroupPlayerCompleteQuestImpl(
    Player* player, Quest const* quest);
void HandleGroupPlayerAchievementCompleteImpl(
    Player* player,
    AchievementEntry const* achievement);
void HandleGroupPlayerSpellCastImpl(
    Player* player, Spell* spell);
void HandleGroupPlayerResurrectImpl(
    Player* player);
void HandleGroupPlayerReleasedGhostImpl(
    Player* player);
void HandleGroupPlayerMapChangedImpl(
    Player* player);
void HandleGroupPlayerTextEmoteImpl(
    Player* player, uint32 textEmote,
    ObjectGuid guid);
void HandleGroupPlayerUpdateZoneImpl(
    Player* player, uint32 newZone,
    uint32 newArea);
void CheckGroupCombatStateImpl();

// ============================================================================
// LLMChatterGroupPlayerScript (PlayerScript shell)
// ============================================================================

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

    bool OnPlayerCanUseChat(
        Player* player, uint32 type, uint32 lang,
        std::string& msg, Group* /*group*/) override
    {
        if (TryHandleMultiBotCompatChat(
                player, type, lang, msg))
            return false;

        return true;
    }

    // ------------------------------------------------
    // Creature Kill event (group chatter)
    // ------------------------------------------------
    void OnPlayerCreatureKill(
        Player* killer, Creature* killed) override
    {
        HandleGroupCreatureKillImpl(killer, killed);
    }

    void OnPlayerKilledByCreature(
        Creature* killer, Player* killed) override
    {
        HandleGroupPlayerKilledByCreatureImpl(
            killer, killed);
    }

    // Shared loot handler for both direct loot
    // and group roll rewards
    void HandleGroupLootEvent(
        Player* player, Item* item)
    {
        HandleGroupLootEventImpl(player, item);
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
        HandleGroupPlayerEnterCombatImpl(
            player, enemy);
    }
    void OnPlayerBeforeSendChatMessage(
        Player* player, uint32& type,
        uint32& lang,
        std::string& msg) override
    {
        HandleGroupPlayerBeforeSendChatMessageImpl(
            player, type, lang, msg);
    }
    void OnPlayerLevelChanged(
        Player* player, uint8 oldLevel) override
    {
        HandleGroupPlayerLevelChangedImpl(
            player, oldLevel);
    }
    bool OnPlayerBeforeQuestComplete(
        Player* player, uint32 questId) override
    {
        return HandleGroupPlayerBeforeQuestCompleteImpl(
            player, questId);
    }
    void OnPlayerCompleteQuest(
        Player* player,
        Quest const* quest) override
    {
        HandleGroupPlayerCompleteQuestImpl(
            player, quest);
    }
    void OnPlayerAchievementComplete(
        Player* player,
        AchievementEntry const* achievement) override
    {
        HandleGroupPlayerAchievementCompleteImpl(
            player, achievement);
    }
    void OnPlayerSpellCast(
        Player* player, Spell* spell,
        bool /*skipCheck*/) override
    {
        HandleGroupPlayerSpellCastImpl(
            player, spell);
    }
    void OnPlayerResurrect(
        Player* player, float /*restore_percent*/,
        bool& /*applySickness*/) override
    {
        HandleGroupPlayerResurrectImpl(player);
    }
    void OnPlayerReleasedGhost(Player* player) override
    {
        HandleGroupPlayerReleasedGhostImpl(
            player);
    }
    void OnPlayerMapChanged(
        Player* player) override
    {
        HandleGroupPlayerMapChangedImpl(player);
    }
    void OnPlayerTextEmote(
        Player* player, uint32 textEmote,
        uint32 /*emoteNum*/,
        ObjectGuid guid) override
    {
        HandleGroupPlayerTextEmoteImpl(
            player, textEmote, guid);
    }
};

// ============================================================
// HandleGroupPlayerUpdateZone
// ============================================================

void HandleGroupPlayerUpdateZone(
    Player* player, uint32 newZone,
    uint32 newArea)
{
    HandleGroupPlayerUpdateZoneImpl(
        player, newZone, newArea);
}

// ============================================================
// State-triggered callout polling delegation
// ============================================================

// ============================================================
// CheckGroupCombatState
// ============================================================

void CheckGroupCombatState()
{
    CheckGroupCombatStateImpl();
}

// ============================================================
// Registration
// ============================================================

// Forward declarations for sub-domain registration
void AddLLMChatterGroupJoinScripts();
void AddLLMChatterGroupQuestScripts();

void AddLLMChatterGroupScripts()
{
    AddLLMChatterGroupJoinScripts();
    new LLMChatterGroupPlayerScript();
    AddLLMChatterGroupQuestScripts();
}


