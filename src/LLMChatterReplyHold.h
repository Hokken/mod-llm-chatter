/*
 * mod-llm-chatter - short reply holds for ungrouped playerbots
 */

#ifndef MOD_LLM_CHATTER_REPLY_HOLD_H
#define MOD_LLM_CHATTER_REPLY_HOLD_H

#include "Define.h"

class Player;

// Upper bound for a hold; longer requests are clamped.
constexpr uint32 LLM_CHATTER_MAX_REPLY_HOLD_MS = 4000;

// Stops the bot and turns it toward the player for up to holdMs
// (clamped to LLM_CHATTER_MAX_REPLY_HOLD_MS) so it is still there
// when its reply arrives. The motion master is left alone, so the
// bot resumes what it was doing. The hold ends early when the bot
// enters combat or one of its lines is delivered or dropped.
void HoldBotForReply(Player* bot, Player* player, uint32 holdMs);
void ReleaseBotReplyHold(uint32 botGuid);
void AddLLMChatterReplyHoldScripts();

#endif
