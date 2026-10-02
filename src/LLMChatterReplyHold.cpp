/*
 * mod-llm-chatter - short reply holds for ungrouped playerbots
 */

#include "LLMChatterReplyHold.h"

#include "LLMChatterShared.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "ScriptMgr.h"

#include <algorithm>
#include <chrono>
#include <mutex>
#include <unordered_map>

namespace
{
using HoldClock = std::chrono::steady_clock;

std::mutex _holdMutex;
std::unordered_map<uint32, HoldClock::time_point> _heldBots;

// Removes the bot's hold; true when it had not run out yet.
bool TakeActiveHold(uint32 botGuid)
{
    std::lock_guard<std::mutex> guard(_holdMutex);
    auto it = _heldBots.find(botGuid);
    if (it == _heldBots.end())
        return false;
    bool active = HoldClock::now() < it->second;
    _heldBots.erase(it);
    return active;
}
} // namespace

void HoldBotForReply(Player* bot, Player* player, uint32 holdMs)
{
    if (!bot || !player || !bot->IsInWorld() || bot->IsInCombat()
        || bot->IsInFlight() || !IsPlayerBot(bot))
        return;
    PlayerbotAI* ai = GET_PLAYERBOT_AI(bot);
    if (!ai)
        return;

    holdMs = std::min(holdMs, LLM_CHATTER_MAX_REPLY_HOLD_MS);
    bot->StopMoving();
    bot->SetFacingToObject(player);
    ai->SetNextCheckDelay(holdMs);

    HoldClock::time_point now = HoldClock::now();
    std::lock_guard<std::mutex> guard(_holdMutex);
    for (auto it = _heldBots.begin(); it != _heldBots.end();)
    {
        if (it->second <= now)
            it = _heldBots.erase(it);
        else
            ++it;
    }
    _heldBots[bot->GetGUID().GetCounter()] =
        now + std::chrono::milliseconds(holdMs);
}

void ReleaseBotReplyHold(uint32 botGuid)
{
    if (!botGuid || !TakeActiveHold(botGuid))
        return;
    Player* bot = ObjectAccessor::FindPlayer(
        ObjectGuid::Create<HighGuid::Player>(botGuid));
    if (!bot || !bot->IsInWorld())
        return;
    if (PlayerbotAI* ai = GET_PLAYERBOT_AI(bot))
        ai->SetNextCheckDelay(0);
}

class LLMChatterReplyHoldPlayerScript : public PlayerScript
{
public:
    LLMChatterReplyHoldPlayerScript()
        : PlayerScript("LLMChatterReplyHoldPlayerScript",
              {PLAYERHOOK_ON_PLAYER_ENTER_COMBAT})
    {
    }

    void OnPlayerEnterCombat(Player* player, Unit* /*enemy*/) override
    {
        if (player)
            ReleaseBotReplyHold(player->GetGUID().GetCounter());
    }
};

void AddLLMChatterReplyHoldScripts()
{
    new LLMChatterReplyHoldPlayerScript();
}
