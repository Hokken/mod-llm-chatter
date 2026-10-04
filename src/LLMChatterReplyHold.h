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

// Event extra-data field that carries a reply's hold id to delivery.
constexpr char const* LLM_CHATTER_REPLY_HOLD_KEY = "reply_hold_id";

// A fresh id for one queued reply; never 0.
uint32 NewReplyHoldId();
// ",\"reply_hold_id\":<replyId>" for the reply's event JSON.
std::string ReplyHoldJsonField(uint32 replyId);

// Keeps a stationary bot in place for the configured hold so it is
// still there when the reply queued with replyId arrives. A moving bot,
// or one IsSafeForChatterFacing() rejects, is left alone; with facing
// enabled the bot also turns toward the player. The hold only raises
// the bot's AI delay, never shortens it, and releasing it takes back
// only what the hold added. It ends early when the bot enters combat
// or a line of that reply is delivered or dropped for good. With
// replyId 0 no line ends it, only combat or its own expiry.
void HoldBotForReply(Player* bot, Player* player, uint32 replyId);
void ReleaseBotReplyHold(uint32 botGuid, uint32 replyId);
void AddLLMChatterReplyHoldScripts();

// Ends the row bot's hold when a delivery attempt returns, unless the
// row was put back on the queue for another attempt (Keep()).
class ReplyHoldDeliveryScope
{
public:
    ReplyHoldDeliveryScope(uint32 botGuid, uint32 replyId)
        : _botGuid(botGuid), _replyId(replyId)
    {
    }
    ~ReplyHoldDeliveryScope()
    {
        if (!_keep)
            ReleaseBotReplyHold(_botGuid, _replyId);
    }
    ReplyHoldDeliveryScope(ReplyHoldDeliveryScope const&) = delete;
    ReplyHoldDeliveryScope& operator=(ReplyHoldDeliveryScope const&) = delete;

    void Keep() { _keep = true; }

private:
    uint32 _botGuid;
    uint32 _replyId;
    bool _keep = false;
};

#endif
