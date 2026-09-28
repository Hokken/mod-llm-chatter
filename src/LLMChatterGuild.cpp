/*
 * mod-llm-chatter - player-driven Guild Chat
 */

#include "LLMChatterGuild.h"

#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "DatabaseEnv.h"
#include "Guild.h"
#include "GuildMgr.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "Random.h"
#include "RandomPlayerbotMgr.h"
#include "ScriptMgr.h"
#include "WorldSession.h"

#include <algorithm>
#include <cctype>
#include <ctime>
#include <mutex>
#include <random>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace
{
std::mutex sGuildActivityMutex;
std::unordered_map<uint32, time_t>
    sLastGuildPlayerInteraction;

struct PendingGuildLoginGreeting
{
    uint32 guildId = 0;
    uint64 sessionId = 0;
    uint32 initialDelaySeconds = 0;
    std::string initialDelayBand;
    time_t dueAt = 0;
    time_t expiresAt = 0;
};

std::unordered_map<uint32, PendingGuildLoginGreeting>
    sPendingGuildLoginGreetings;

void CancelGuildLoginGreeting(uint32 playerGuid)
{
    sPendingGuildLoginGreetings.erase(playerGuid);

    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages m "
        "JOIN llm_chatter_events e "
        "ON e.id = m.event_id "
        "SET m.delivered = 1, "
        "m.delivered_at = NOW() "
        "WHERE m.delivered = 0 "
        "AND e.event_type = 'guild_login_greeting' "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT("
        "e.extra_data, '$.player_guid')) "
        "AS UNSIGNED) = {}",
        playerGuid);

    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_events "
        "SET status = 'skipped', "
        "processed_at = NOW() "
        "WHERE event_type = 'guild_login_greeting' "
        "AND status IN ('pending', 'processing') "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT("
        "extra_data, '$.player_guid')) "
        "AS UNSIGNED) = {}",
        playerGuid);
}

void CleanupGuildPlayerSession(uint32 playerGuid)
{
    sPendingGuildLoginGreetings.erase(playerGuid);

    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages m "
        "JOIN llm_chatter_events e "
        "ON e.id = m.event_id "
        "SET m.delivered = 1, "
        "m.delivered_at = NOW() "
        "WHERE m.delivered = 0 "
        "AND e.event_type IN ("
        "'guild_player_message',"
        "'guild_login_greeting') "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT("
        "e.extra_data, '$.player_guid')) "
        "AS UNSIGNED) = {}",
        playerGuid);

    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_events "
        "SET status = 'expired', "
        "processed_at = NOW() "
        "WHERE event_type IN ("
        "'guild_player_message',"
        "'guild_login_greeting') "
        "AND status IN ('pending', 'processing') "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT("
        "extra_data, '$.player_guid')) "
        "AS UNSIGNED) = {}",
        playerGuid);

    CharacterDatabase.DirectExecute(
        "DELETE h FROM llm_guild_session_history h "
        "JOIN llm_guild_chat_sessions s "
        "ON s.id = h.session_id "
        "WHERE s.player_guid = {}",
        playerGuid);

    CharacterDatabase.DirectExecute(
        "DELETE FROM llm_guild_chat_sessions "
        "WHERE player_guid = {}",
        playerGuid);
}

uint64 StartGuildPlayerSession(Player* player)
{
    if (!player)
        return 0;

    uint32 guildId = player->GetGuildId();
    if (!guildId)
        return 0;

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    CleanupGuildPlayerSession(playerGuid);

    CharacterDatabase.DirectExecute(
        "INSERT INTO llm_guild_chat_sessions "
        "(player_guid, player_name, guild_id) "
        "VALUES ({}, '{}', {})",
        playerGuid,
        EscapeString(player->GetName()),
        guildId);

    QueryResult result = CharacterDatabase.Query(
        "SELECT id FROM llm_guild_chat_sessions "
        "WHERE player_guid = {} "
        "AND guild_id = {} LIMIT 1",
        playerGuid, guildId);
    if (!result)
        return 0;

    uint64 sessionId =
        result->Fetch()[0].Get<uint64>();
    return sessionId;
}

uint64 EnsureGuildPlayerSession(Player* player)
{
    if (!player || !player->GetGuildId())
        return 0;

    uint32 playerGuid =
        player->GetGUID().GetCounter();
    uint32 guildId = player->GetGuildId();
    QueryResult result = CharacterDatabase.Query(
        "SELECT id, guild_id "
        "FROM llm_guild_chat_sessions "
        "WHERE player_guid = {} LIMIT 1",
        playerGuid);
    if (result)
    {
        Field* fields = result->Fetch();
        uint64 sessionId = fields[0].Get<uint64>();
        if (fields[1].Get<uint32>() == guildId)
            return sessionId;
    }

    return StartGuildPlayerSession(player);
}

uint32 AdvanceGuildPlayerTurn(uint64 sessionId)
{
    CharacterDatabase.DirectExecute(
        "UPDATE llm_guild_chat_sessions "
        "SET turn_id = turn_id + 1, "
        "last_activity_at = NOW() "
        "WHERE id = {}",
        sessionId);

    QueryResult result = CharacterDatabase.Query(
        "SELECT turn_id "
        "FROM llm_guild_chat_sessions "
        "WHERE id = {} LIMIT 1",
        sessionId);
    if (!result)
        return 0;

    return result->Fetch()[0].Get<uint32>();
}

void StorePlayerGuildLine(
    Player* player, std::string const& message)
{
    uint32 guildId = player->GetGuildId();
    uint32 playerGuid =
        player->GetGUID().GetCounter();

    CharacterDatabase.DirectExecute(
        "INSERT INTO llm_guild_session_history "
        "(session_id, guild_id, speaker_guid, "
        "speaker_name, is_bot, source_kind, message, "
        "delivered_at) "
        "SELECT id, guild_id, {}, '{}', 0, "
        "'player', '{}', NOW() "
        "FROM llm_guild_chat_sessions "
        "WHERE guild_id = {}",
        playerGuid,
        EscapeString(player->GetName()),
        EscapeString(message),
        guildId);

    CharacterDatabase.DirectExecute(
        "UPDATE llm_guild_chat_sessions "
        "SET last_activity_at = NOW() "
        "WHERE guild_id = {}",
        guildId);
}

void CancelSupersededGuildReplies(
    uint64 sessionId, uint32 turnId)
{
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages m "
        "JOIN llm_chatter_events e "
        "ON e.id = m.event_id "
        "SET m.delivered = 1, "
        "m.delivered_at = NOW() "
        "WHERE m.delivered = 0 "
        "AND e.event_type = 'guild_player_message' "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT("
        "e.extra_data, '$.session_id')) "
        "AS UNSIGNED) = {}",
        sessionId);

    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_events "
        "SET status = 'skipped', "
        "processed_at = NOW() "
        "WHERE event_type = 'guild_player_message' "
        "AND status = 'pending' "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT("
        "extra_data, '$.session_id')) "
        "AS UNSIGNED) = {} "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT("
        "extra_data, '$.turn_id')) "
        "AS UNSIGNED) < {}",
        sessionId, turnId);
}

bool ContainsNameWithBoundary(
    std::string const& message,
    std::string const& name)
{
    std::string messageLower = message;
    std::string nameLower = name;
    auto lower = [](unsigned char c)
    {
        return static_cast<char>(std::tolower(c));
    };
    std::transform(
        messageLower.begin(), messageLower.end(),
        messageLower.begin(), lower);
    std::transform(
        nameLower.begin(), nameLower.end(),
        nameLower.begin(), lower);

    size_t position = messageLower.find(nameLower);
    while (position != std::string::npos)
    {
        bool leftOk =
            position == 0
            || !std::isalpha(
                static_cast<unsigned char>(
                    messageLower[position - 1]));
        size_t end = position + nameLower.size();
        bool rightOk =
            end >= messageLower.size()
            || !std::isalpha(
                static_cast<unsigned char>(
                    messageLower[end]));
        if (leftOk && rightOk)
            return true;

        position = messageLower.find(
            nameLower, position + 1);
    }
    return false;
}

std::vector<Player*> GetEligibleGuildBots(
    uint32 guildId,
    TeamId playerTeam,
    std::string const& playerMessage,
    uint32 maxCandidates)
{
    std::vector<Player*> mentionedBots;
    std::vector<Player*> otherBots;
    auto allBots = sRandomPlayerbotMgr.GetAllBots();
    for (auto const& pair : allBots)
    {
        Player* bot = pair.second;
        if (!bot || !bot->IsInWorld()
            || !bot->IsAlive()
            || bot->IsInCombat()
            || bot->GetGuildId() != guildId
            || bot->GetTeamId() != playerTeam)
        {
            continue;
        }

        WorldSession* session = bot->GetSession();
        if (!session || session->PlayerLoading())
            continue;

        if (ContainsNameWithBoundary(
                playerMessage, bot->GetName()))
        {
            mentionedBots.push_back(bot);
        }
        else
            otherBots.push_back(bot);
    }

    std::mt19937 generator{std::random_device{}()};
    std::shuffle(
        mentionedBots.begin(), mentionedBots.end(),
        generator);
    std::shuffle(
        otherBots.begin(), otherBots.end(),
        generator);

    std::vector<Player*> bots;
    bots.reserve(
        mentionedBots.size() + otherBots.size());
    bots.insert(
        bots.end(),
        mentionedBots.begin(), mentionedBots.end());
    bots.insert(
        bots.end(),
        otherBots.begin(), otherBots.end());

    maxCandidates = std::max(1u, maxCandidates);
    if (bots.size() > maxCandidates)
        bots.resize(maxCandidates);
    return bots;
}

std::string BuildGuildCandidatesJson(
    std::vector<Player*> const& bots)
{
    std::string candidates = "[";
    for (uint32 index = 0;
         index < bots.size(); ++index)
    {
        Player* bot = bots[index];
        if (index)
            candidates += ",";
        candidates += fmt::format(
            R"({{"guid":{},"name":"{}",)"
            R"("zone_id":{},"map_id":{}}})",
            bot->GetGUID().GetCounter(),
            JsonEscape(bot->GetName()),
            bot->GetZoneId(),
            bot->GetMapId());
    }
    candidates += "]";
    return candidates;
}

bool IsHiddenGuildPayload(
    uint32 language, std::string const& message)
{
    if (language == LANG_ADDON)
        return true;

    bool hasUnderscore = false;
    bool allCapsOrSeparator = true;
    for (char c : message)
    {
        if (c == '_')
            hasUnderscore = true;
        else if (c != ' ' && c != '\t'
            && c != '\n' && c != '\r'
            && !(c >= 'A' && c <= 'Z'))
        {
            allCapsOrSeparator = false;
            break;
        }
    }
    return hasUnderscore && allCapsOrSeparator;
}

void HandleGuildPlayerMessage(
    Player* player,
    uint32 type,
    uint32 language,
    std::string const& rawMessage)
{
    if (type != CHAT_MSG_GUILD
        || !sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_guildChatterEnable
        || !player
        || IsPlayerBot(player)
        || !player->GetGuildId()
        || rawMessage.empty()
        || IsHiddenGuildPayload(language, rawMessage))
    {
        return;
    }

    if (sLLMChatterConfig
            ->IsPlayerChatPrefixIgnored(rawMessage))
        return;

    // A real Guild message is more current than a
    // scheduled login acknowledgement. Cancel both
    // in-memory and already queued greeting work.
    CancelGuildLoginGreeting(
        player->GetGUID().GetCounter());

    if (!sLLMChatterConfig
            ->_guildPlayerRepliesEnable)
    {
        return;
    }

    std::string message = NormalizeChatTextForDb(
        rawMessage,
        sLLMChatterConfig->_maxMessageLength);
    if (message.empty())
        return;

    uint64 sessionId =
        EnsureGuildPlayerSession(player);
    if (!sessionId)
        return;

    StorePlayerGuildLine(player, message);
    uint32 turnId =
        AdvanceGuildPlayerTurn(sessionId);
    if (!turnId)
        return;

    CancelSupersededGuildReplies(
        sessionId, turnId);

    uint32 guildId = player->GetGuildId();
    NoteGuildPlayerInteraction(guildId);

    std::vector<Player*> bots =
        GetEligibleGuildBots(
            guildId,
            player->GetTeamId(),
            message,
            sLLMChatterConfig
                ->_guildPlayerReplyMaxCandidates);
    if (bots.empty())
    {
        LOG_DEBUG(
            "module",
            "LLMChatter: no eligible Guild bot for "
            "player={} guild={}",
            player->GetName(), guildId);
        return;
    }

    Guild* guild =
        sGuildMgr->GetGuildById(guildId);
    std::string guildName =
        guild ? guild->GetName() : "the guild";

    std::string candidates =
        BuildGuildCandidatesJson(bots);

    char const* teamName =
        player->GetTeamId() == TEAM_ALLIANCE
            ? "Alliance" : "Horde";
    std::string extraData = fmt::format(
        R"({{"guild_id":{},)"
        R"("guild_name":"{}",)"
        R"("session_id":{},)"
        R"("turn_id":{},)"
        R"("player_guid":{},)"
        R"("player_name":"{}",)"
        R"("player_gender":{},)"
        R"("player_message":"{}",)"
        R"("team":"{}",)"
        R"("candidates":{}}})",
        guildId,
        JsonEscape(guildName),
        sessionId,
        turnId,
        player->GetGUID().GetCounter(),
        JsonEscape(player->GetName()),
        player->getGender(),
        JsonEscape(message),
        teamName,
        candidates);

    QueueChatterEvent(
        "guild_player_message",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(
            "guild_player_message"),
        "",
        player->GetGUID().GetCounter(),
        player->GetName(),
        0, "", 0,
        EscapeString(extraData),
        sLLMChatterConfig
            ->_guildPlayerReplyDebounceSeconds,
        120,
        false);

    LOG_DEBUG(
        "module",
        "LLMChatter: queued Guild player turn "
        "player={} guild={} session={} turn={} "
        "candidates={}",
        player->GetName(),
        guildId,
        sessionId,
        turnId,
        bots.size());
}

std::pair<uint32, char const*>
SelectGuildLoginGreetingDelay()
{
    uint32 roll = urand(1, 100);
    uint32 quickChance =
        sLLMChatterConfig
            ->_guildLoginGreetingQuickChance;
    uint32 busyChance =
        sLLMChatterConfig
            ->_guildLoginGreetingBusyChance;

    if (roll <= quickChance)
        return {urand(2, 5), "quick"};
    if (roll <= quickChance + busyChance)
        return {urand(25, 45), "busy"};
    return {urand(8, 20), "ordinary"};
}

void ScheduleGuildLoginGreeting(
    Player* player, uint64 sessionId)
{
    if (!player || !sessionId
        || !sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem
        || !sLLMChatterConfig->_guildChatterEnable
        || !sLLMChatterConfig
                ->_guildLoginGreetingEnable
        || !player->GetGuildId())
    {
        return;
    }

    uint32 chance =
        sLLMChatterConfig
            ->_guildLoginGreetingChance;
    if (!chance || urand(1, 100) > chance)
        return;

    time_t now = time(nullptr);
    auto [delaySeconds, delayBand] =
        SelectGuildLoginGreetingDelay();
    PendingGuildLoginGreeting pending;
    pending.guildId = player->GetGuildId();
    pending.sessionId = sessionId;
    pending.initialDelaySeconds = delaySeconds;
    pending.initialDelayBand = delayBand;
    pending.dueAt = now + delaySeconds;
    pending.expiresAt =
        now + sLLMChatterConfig
                  ->_guildLoginGreetingReadinessTimeout;
    sPendingGuildLoginGreetings[
        player->GetGUID().GetCounter()] = pending;

    LOG_DEBUG(
        "module",
        "LLMChatter: scheduled Guild login greeting "
        "player={} guild={} session={} delay={} band={}",
        player->GetName(),
        pending.guildId,
        pending.sessionId,
        pending.initialDelaySeconds,
        pending.initialDelayBand);
}

bool IsGuildLoginSessionCurrent(
    uint64 sessionId,
    uint32 playerGuid,
    uint32 guildId)
{
    QueryResult result = CharacterDatabase.Query(
        "SELECT 1 FROM llm_guild_chat_sessions "
        "WHERE id = {} "
        "AND player_guid = {} "
        "AND guild_id = {} "
        "AND turn_id = 0 LIMIT 1",
        sessionId,
        playerGuid,
        guildId);
    return static_cast<bool>(result);
}

bool QueueGuildLoginGreeting(
    Player* player,
    PendingGuildLoginGreeting const& pending)
{
    std::vector<Player*> bots =
        GetEligibleGuildBots(
            pending.guildId,
            player->GetTeamId(),
            "",
            sLLMChatterConfig
                ->_guildLoginGreetingMaxCandidates);
    if (bots.empty())
        return false;

    Guild* guild =
        sGuildMgr->GetGuildById(pending.guildId);
    std::string guildName =
        guild ? guild->GetName() : "the guild";
    std::string candidates =
        BuildGuildCandidatesJson(bots);
    char const* teamName =
        player->GetTeamId() == TEAM_ALLIANCE
            ? "Alliance" : "Horde";

    std::string extraData = fmt::format(
        R"({{"guild_id":{},)"
        R"("guild_name":"{}",)"
        R"("session_id":{},)"
        R"("turn_id":0,)"
        R"("player_guid":{},)"
        R"("player_name":"{}",)"
        R"("team":"{}",)"
        R"("initial_delay_seconds":{},)"
        R"("initial_delay_band":"{}",)"
        R"("candidates":{}}})",
        pending.guildId,
        JsonEscape(guildName),
        pending.sessionId,
        player->GetGUID().GetCounter(),
        JsonEscape(player->GetName()),
        teamName,
        pending.initialDelaySeconds,
        pending.initialDelayBand,
        candidates);

    QueueChatterEvent(
        "guild_login_greeting",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(
            "guild_login_greeting"),
        "",
        player->GetGUID().GetCounter(),
        player->GetName(),
        0, "", 0,
        EscapeString(extraData),
        0,
        120,
        false);

    NoteGuildPlayerInteraction(pending.guildId);
    LOG_DEBUG(
        "module",
        "LLMChatter: queued Guild login greeting "
        "player={} guild={} session={} candidates={}",
        player->GetName(),
        pending.guildId,
        pending.sessionId,
        bots.size());
    return true;
}

void ProcessPendingGuildLoginGreetings()
{
    static time_t lastUpdate = 0;
    time_t now = time(nullptr);
    if (now == lastUpdate)
        return;
    lastUpdate = now;

    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem
        || !sLLMChatterConfig->_guildChatterEnable
        || !sLLMChatterConfig
                ->_guildLoginGreetingEnable)
    {
        sPendingGuildLoginGreetings.clear();
        return;
    }

    for (auto it =
             sPendingGuildLoginGreetings.begin();
         it != sPendingGuildLoginGreetings.end();)
    {
        uint32 playerGuid = it->first;
        PendingGuildLoginGreeting& pending =
            it->second;

        if (now >= pending.expiresAt)
        {
            it = sPendingGuildLoginGreetings.erase(it);
            continue;
        }
        if (now < pending.dueAt)
        {
            ++it;
            continue;
        }

        ObjectGuid guid =
            ObjectGuid::Create<HighGuid::Player>(
                playerGuid);
        Player* player =
            ObjectAccessor::FindConnectedPlayer(guid);
        WorldSession* session =
            player ? player->GetSession() : nullptr;
        if (!player
            || IsPlayerBot(player)
            || !player->IsInWorld()
            || !session
            || session->PlayerLoading()
            || player->GetGuildId()
                != pending.guildId
            || !IsGuildLoginSessionCurrent(
                pending.sessionId,
                playerGuid,
                pending.guildId))
        {
            it = sPendingGuildLoginGreetings.erase(it);
            continue;
        }

        if (QueueGuildLoginGreeting(player, pending))
        {
            it = sPendingGuildLoginGreetings.erase(it);
            continue;
        }

        pending.dueAt =
            now + sLLMChatterConfig
                      ->_guildLoginGreetingRetryInterval;
        ++it;
    }
}

class LLMChatterGuildPlayerScript
    : public PlayerScript
{
public:
    LLMChatterGuildPlayerScript()
        : PlayerScript(
              "LLMChatterGuildPlayerScript",
              {PLAYERHOOK_ON_LOGIN,
               PLAYERHOOK_ON_LOGOUT,
               PLAYERHOOK_ON_BEFORE_SEND_CHAT_MESSAGE})
    {
    }

    void OnPlayerLogin(Player* player) override
    {
        if (!player || IsPlayerBot(player))
            return;

        bool playerRepliesEnabled =
            sLLMChatterConfig
            && sLLMChatterConfig
                   ->_guildPlayerRepliesEnable;
        bool loginGreetingEnabled =
            sLLMChatterConfig
            && sLLMChatterConfig->_useEventSystem
            && sLLMChatterConfig
                   ->_guildLoginGreetingEnable;
        if (sLLMChatterConfig
            && sLLMChatterConfig->IsEnabled()
            && sLLMChatterConfig->_guildChatterEnable
            && (playerRepliesEnabled
                || loginGreetingEnabled)
            && player->GetGuildId())
        {
            // StartGuildPlayerSession clears any stale
            // session first, making login a hard boundary.
            uint64 sessionId =
                StartGuildPlayerSession(player);
            if (sessionId)
            {
                ScheduleGuildLoginGreeting(
                    player, sessionId);
                return;
            }
        }

        // A login remains a new memory boundary when the
        // feature is disabled or the player is unguilded.
        CleanupGuildPlayerSession(
            player->GetGUID().GetCounter());
    }

    void OnPlayerLogout(Player* player) override
    {
        if (!player || IsPlayerBot(player))
            return;

        CleanupGuildPlayerSession(
            player->GetGUID().GetCounter());
    }

    void OnPlayerBeforeSendChatMessage(
        Player* player,
        uint32& type,
        uint32& language,
        std::string& message) override
    {
        HandleGuildPlayerMessage(
            player, type, language, message);
    }
};
}

void NoteGuildPlayerInteraction(uint32 guildId)
{
    if (!guildId)
        return;

    std::lock_guard<std::mutex> guard(
        sGuildActivityMutex);
    sLastGuildPlayerInteraction[guildId] =
        time(nullptr);
}

bool WasGuildPlayerInteractionRecent(
    uint32 guildId, uint32 seconds)
{
    if (!guildId || !seconds)
        return false;

    std::lock_guard<std::mutex> guard(
        sGuildActivityMutex);
    auto it =
        sLastGuildPlayerInteraction.find(guildId);
    if (it == sLastGuildPlayerInteraction.end())
        return false;

    return time(nullptr) - it->second
        < static_cast<time_t>(seconds);
}

void RecordDeliveredGuildLine(
    uint32 guildId,
    uint32 eventId,
    uint32 botGuid,
    std::string const& botName,
    std::string const& message)
{
    if (!guildId || message.empty())
        return;

    std::string sourceKind = "ambient";
    if (eventId)
    {
        QueryResult result = CharacterDatabase.Query(
            "SELECT event_type "
            "FROM llm_chatter_events "
            "WHERE id = {} LIMIT 1",
            eventId);
        std::string eventType = result
            ? result->Fetch()[0].Get<std::string>()
            : "";
        if (eventType == "guild_player_message"
            || eventType == "guild_login_greeting")
        {
            sourceKind = "reply";
            NoteGuildPlayerInteraction(guildId);
        }
    }

    CharacterDatabase.DirectExecute(
        "INSERT INTO llm_guild_session_history "
        "(session_id, guild_id, speaker_guid, "
        "speaker_name, is_bot, source_kind, "
        "source_event_id, message, delivered_at) "
        "SELECT id, guild_id, {}, '{}', 1, '{}', "
        "{}, '{}', NOW() "
        "FROM llm_guild_chat_sessions "
        "WHERE guild_id = {}",
        botGuid,
        EscapeString(botName),
        sourceKind,
        eventId,
        EscapeString(message),
        guildId);

    CharacterDatabase.DirectExecute(
        "UPDATE llm_guild_chat_sessions "
        "SET last_activity_at = NOW() "
        "WHERE guild_id = {}",
        guildId);

}

void UpdatePendingGuildLoginGreetings()
{
    ProcessPendingGuildLoginGreetings();
}

void AddLLMChatterGuildScripts()
{
    new LLMChatterGuildPlayerScript();
}
