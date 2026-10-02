/*
 * mod-llm-chatter - guild world events
 */

#ifndef MOD_LLM_CHATTER_GUILD_WORLD_H
#define MOD_LLM_CHATTER_GUILD_WORLD_H

#include "Define.h"

class Player;

// Delivery-time check for a meet greeting's /say line: nullptr when
// the bot may still greet the player, otherwise the drop reason.
char const* CheckMeetGreetingDelivery(Player* bot, uint32 playerGuid);

// Releases the held Guild follow-up of a meet greeting once the
// greeting was spoken, or cancels it when the greeting was dropped.
void SettleMeetGreetingFollowUp(uint32 eventId, bool greeted);

void AddLLMChatterGuildWorldScripts();

#endif
