/*
 * mod-llm-chatter - short reply holds for ungrouped playerbots
 */

#include "LLMChatterReplyHold.h"

#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "ScriptMgr.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <ctime>
#include <limits>
#include <mutex>
#include <unordered_map>

namespace
{
using HoldClock = std::chrono::steady_clock;

// The bot's AI delay counts down with world updates, so it can trail
// the steady clock a little without anything else having raised it.
constexpr uint32 kReleaseSlackMs = 1000;

struct ReplyHold
{
    HoldClock::time_point start;
    uint32 heldMs = 0;
    // AI delay the bot already had when the hold started.
    uint32 priorMs = 0;
    uint32 replyId = 0;
};

std::mutex _holdMutex;
std::unordered_map<uint32, ReplyHold> _heldBots;

// Seeded from the clock so ids still queued from before a restart do
// not match the holds of the new run.
std::atomic<uint32> _nextReplyId{static_cast<uint32>(std::time(nullptr))};

// PlayerbotAIBase keeps the delay protected and has no getter.
struct AICheckDelayAccess : PlayerbotAIBase
{
    static uint32 Get(PlayerbotAIBase const& ai)
    {
        return ai.*(&AICheckDelayAccess::nextAICheckDelay);
    }
};

uint32 ElapsedMs(HoldClock::time_point since, HoldClock::time_point now)
{
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - since).count();
    return ms <= 0 ? 0 : static_cast<uint32>(std::min<int64>(
        ms, std::numeric_limits<uint32>::max()));
}

// replyId nullptr releases whatever the bot is held for.
void ReleaseHold(uint32 botGuid, uint32 const* replyId)
{
    if (!botGuid)
        return;

    ReplyHold hold;
    {
        std::lock_guard<std::mutex> guard(_holdMutex);
        auto it = _heldBots.find(botGuid);
        if (it == _heldBots.end()
            || (replyId && it->second.replyId != *replyId))
            return;
        hold = it->second;
        _heldBots.erase(it);
    }

    uint32 elapsed = ElapsedMs(hold.start, HoldClock::now());
    if (elapsed >= hold.heldMs)
        return;
    Player* bot = ObjectAccessor::FindPlayer(
        ObjectGuid::Create<HighGuid::Player>(botGuid));
    if (!bot || !bot->IsInWorld())
        return;
    PlayerbotAI* ai = GET_PLAYERBOT_AI(bot);
    if (!ai)
        return;

    uint32 current = AICheckDelayAccess::Get(*ai);
    // Something else raised the delay after the hold set it.
    if (current > hold.heldMs - elapsed + kReleaseSlackMs)
        return;
    uint32 priorLeft =
        hold.priorMs > elapsed ? hold.priorMs - elapsed : 0;
    if (priorLeft < current)
        ai->SetNextCheckDelay(priorLeft);
}
} // namespace

uint32 NewReplyHoldId()
{
    uint32 id = _nextReplyId.fetch_add(1);
    return id ? id : _nextReplyId.fetch_add(1);
}

std::string ReplyHoldJsonField(uint32 replyId)
{
    return std::string(",\"") + LLM_CHATTER_REPLY_HOLD_KEY + "\":"
        + std::to_string(replyId);
}

void HoldBotForReply(Player* bot, Player* player, uint32 replyId)
{
    uint32 holdMs = std::min(
        sLLMChatterConfig->_proxChatterReplyHoldMs,
        LLM_CHATTER_MAX_REPLY_HOLD_MS);
    if (!holdMs || !bot || !player || !bot->IsInWorld()
        || bot->IsInCombat() || bot->IsInFlight() || !IsPlayerBot(bot)
        || !IsSafeForChatterFacing(bot))
        return;
    PlayerbotAI* ai = GET_PLAYERBOT_AI(bot);
    if (!ai)
        return;

    if (sLLMChatterConfig->_facingEnable)
        bot->SetFacingToObject(player);

    uint32 botGuid = bot->GetGUID().GetCounter();
    HoldClock::time_point now = HoldClock::now();
    std::lock_guard<std::mutex> guard(_holdMutex);
    uint32 current = AICheckDelayAccess::Get(*ai);
    uint32 priorMs = current;
    auto previous = _heldBots.find(botGuid);
    if (previous != _heldBots.end())
    {
        // Still held and not raised since: the current delay is partly
        // the old hold's own. A longer one was set by something else.
        uint32 elapsed = ElapsedMs(previous->second.start, now);
        if (elapsed < previous->second.heldMs
            && current <= previous->second.heldMs - elapsed
                + kReleaseSlackMs)
            priorMs = previous->second.priorMs > elapsed
                ? previous->second.priorMs - elapsed : 0;
    }
    if (priorMs >= holdMs)
        return;

    for (auto it = _heldBots.begin(); it != _heldBots.end();)
    {
        if (ElapsedMs(it->second.start, now) >= it->second.heldMs)
            it = _heldBots.erase(it);
        else
            ++it;
    }
    ai->SetNextCheckDelay(holdMs);
    _heldBots[botGuid] = ReplyHold{now, holdMs, priorMs, replyId};
}

void ReleaseBotReplyHold(uint32 botGuid, uint32 replyId)
{
    if (replyId)
        ReleaseHold(botGuid, &replyId);
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
            ReleaseHold(player->GetGUID().GetCounter(), nullptr);
    }
};

void AddLLMChatterReplyHoldScripts()
{
    new LLMChatterReplyHoldPlayerScript();
}
