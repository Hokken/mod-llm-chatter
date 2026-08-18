/* mod-llm-chatter - private player/playerbot whisper ownership */

#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "DatabaseEnv.h"
#include "Player.h"
#include "PlayerbotAI.h"
#include "Playerbots.h"
#include "ScriptMgr.h"

#include <ctime>
#include <map>
#include <mutex>

namespace
{
std::map<std::pair<uint32, uint32>, time_t> whisperCooldowns;
std::mutex whisperCooldownsMutex;

uint32 AdvanceWhisperTurn(uint32 playerGuid, uint32 botGuid)
{
    CharacterDatabase.DirectExecute(
        "INSERT INTO llm_whisper_sessions (player_guid, bot_guid, turn_id, last_activity_at) "
        "VALUES ({}, {}, 1, NOW()) ON DUPLICATE KEY UPDATE turn_id = turn_id + 1, last_activity_at = NOW()",
        playerGuid, botGuid);
    QueryResult result = CharacterDatabase.Query(
        "SELECT turn_id FROM llm_whisper_sessions WHERE player_guid = {} AND bot_guid = {} LIMIT 1",
        playerGuid, botGuid);
    return result ? result->Fetch()[0].Get<uint32>() : 0;
}

void CancelSupersededWhisperReplies(uint32 playerGuid, uint32 botGuid, uint32 turnId)
{
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages m JOIN llm_chatter_events e ON e.id = m.event_id "
        "SET m.delivered = 1, m.delivered_at = NOW() WHERE m.delivered = 0 "
        "AND e.event_type = 'player_whisper_msg' "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(e.extra_data, '$.player_guid')) AS UNSIGNED) = {} "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(e.extra_data, '$.bot_guid')) AS UNSIGNED) = {} "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(e.extra_data, '$.turn_id')) AS UNSIGNED) < {}",
        playerGuid, botGuid, turnId);
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_events SET status = 'skipped', processed_at = NOW() "
        "WHERE status = 'pending' AND event_type = 'player_whisper_msg' "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(extra_data, '$.player_guid')) AS UNSIGNED) = {} "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(extra_data, '$.bot_guid')) AS UNSIGNED) = {} "
        "AND CAST(JSON_UNQUOTE(JSON_EXTRACT(extra_data, '$.turn_id')) AS UNSIGNED) < {}",
        playerGuid, botGuid, turnId);
}

bool IsPlayerbotWhisperCommand(Player* receiver, std::string const& message)
{
    PlayerbotAI* botAI = GET_PLAYERBOT_AI(receiver);
    return botAI && botAI->IsChatCommand(message);
}

class LLMChatterWhisperScript : public PlayerScript
{
public:
    LLMChatterWhisperScript() : PlayerScript("LLMChatterWhisperScript", {
        PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT }) { }

    bool OnPlayerCanUseChat(Player* player, uint32 type, uint32 language,
                            std::string& msg, Player* receiver) override
    {
        if (!sLLMChatterConfig || !sLLMChatterConfig->IsEnabled() ||
            !sConfigMgr->GetOption<bool>("LLMChatter.Whisper.Enable", true) ||
            type != CHAT_MSG_WHISPER || !player || !receiver ||
            IsPlayerBot(player) || !IsPlayerBot(receiver) ||
            language == LANG_ADDON || msg.empty())
            return true;

        if (sConfigMgr->GetOption<bool>("LLMChatter.Whisper.SkipPlayerbotCommands", true) &&
            IsPlayerbotWhisperCommand(receiver, msg))
            return true;

        std::string safeMsg = NormalizeChatTextForDb(msg, sLLMChatterConfig->_maxMessageLength);
        if (safeMsg.empty())
            return true;
        uint32 playerGuid = player->GetGUID().GetCounter();
        uint32 botGuid = receiver->GetGUID().GetCounter();
        CharacterDatabase.Execute(
            "INSERT INTO llm_whisper_history (player_guid, bot_guid, speaker_guid, is_bot, message) "
            "VALUES ({}, {}, {}, 0, '{}')", playerGuid, botGuid, playerGuid, EscapeString(safeMsg));
        CharacterDatabase.DirectExecute(
            "DELETE FROM llm_whisper_history WHERE player_guid = {} AND bot_guid = {} "
            "AND id NOT IN (SELECT id FROM (SELECT id FROM llm_whisper_history "
            "WHERE player_guid = {} AND bot_guid = {} ORDER BY id DESC LIMIT {}) AS keep)",
            playerGuid, botGuid, playerGuid, botGuid,
            sConfigMgr->GetOption<uint32>("LLMChatter.Whisper.HistoryLimit", 48));

        uint32 turnId = AdvanceWhisperTurn(playerGuid, botGuid);
        CancelSupersededWhisperReplies(playerGuid, botGuid, turnId);
        uint32 chance = sConfigMgr->GetOption<uint32>("LLMChatter.Whisper.Chance", 100);
        if (!chance || urand(1, 100) > chance)
            return true;
        uint32 cooldown = sConfigMgr->GetOption<uint32>("LLMChatter.Whisper.Cooldown", 8);
        time_t now = time(nullptr);
        std::pair<uint32, uint32> key(playerGuid, botGuid);
        {
            std::lock_guard<std::mutex> guard(whisperCooldownsMutex);
            auto it = whisperCooldowns.find(key);
            if (it != whisperCooldowns.end() && now - it->second < static_cast<time_t>(cooldown))
                return true;
            whisperCooldowns[key] = now;
        }

        std::string extraData = "{"
            "\"player_name\":\"" + JsonEscape(player->GetName()) + "\","
            "\"player_message\":\"" + JsonEscape(safeMsg) + "\","
            "\"player_guid\":" + std::to_string(playerGuid) + ","
            "\"bot_guid\":" + std::to_string(botGuid) + ","
            "\"turn_id\":" + std::to_string(turnId) + "}";
        QueueChatterEvent("player_whisper_msg", "player", player->GetZoneId(), player->GetMapId(),
            GetChatterEventPriority("player_whisper_msg"),
            "whisper:" + std::to_string(playerGuid) + ":" + std::to_string(botGuid),
            playerGuid, player->GetName(), botGuid, receiver->GetName(), 0,
            EscapeString(extraData), 0, 120, false);
        return true;
    }
};
}

void AddLLMChatterWhisperScripts()
{
    new LLMChatterWhisperScript();
}
