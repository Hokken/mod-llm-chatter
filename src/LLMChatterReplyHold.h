/*
 * mod-llm-chatter - short reply holds for ungrouped playerbots
 */

#ifndef MOD_LLM_CHATTER_REPLY_HOLD_H
#define MOD_LLM_CHATTER_REPLY_HOLD_H

#include "Define.h"

#include <string>

class Player;

// Upper bound for LLMChatter.ProximityChatter.ReplyHoldMs.
constexpr uint32 LLM_CHATTER_MAX_REPLY_HOLD_MS = 10000;

// Keeps a stationary bot in place for the configured hold so it is
// still there when its eventType reply arrives. A moving bot, or one
// IsSafeForChatterFacing() rejects, is left alone; with facing
// enabled the bot also turns toward the player. The hold only raises
// the bot's AI delay, never shortens it, and releasing it takes back
// only what the hold added. It ends early when the bot enters combat
// or one of its eventType lines is delivered or dropped for good.
void HoldBotForReply(
    Player* bot, Player* player, std::string const& eventType);
void ReleaseBotReplyHold(uint32 botGuid, std::string const& eventType);
void AddLLMChatterReplyHoldScripts();

// Ends the row bot's hold when a delivery attempt returns, unless the
// row was put back on the queue for another attempt (Keep()).
class ReplyHoldDeliveryScope
{
public:
    ReplyHoldDeliveryScope(uint32 botGuid, std::string const& eventType)
        : _botGuid(botGuid), _eventType(eventType)
    {
    }
    ~ReplyHoldDeliveryScope()
    {
        if (!_keep)
            ReleaseBotReplyHold(_botGuid, _eventType);
    }
    ReplyHoldDeliveryScope(ReplyHoldDeliveryScope const&) = delete;
    ReplyHoldDeliveryScope& operator=(ReplyHoldDeliveryScope const&) = delete;

    void Keep() { _keep = true; }

private:
    uint32 _botGuid;
    std::string _eventType;
    bool _keep = false;
};

#endif
