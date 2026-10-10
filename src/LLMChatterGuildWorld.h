/*
 * mod-llm-chatter - guild world events
 */

#ifndef MOD_LLM_CHATTER_GUILD_WORLD_H
#define MOD_LLM_CHATTER_GUILD_WORLD_H

#include "Define.h"

class Player;

// Delivery-time check for a meet greeting's /say line: nullptr when
// the bot may still greet the player, otherwise the drop reason. Both
// must still be members of the event's guild (guildId).
char const* CheckMeetGreetingDelivery(
    Player* bot, uint32 playerGuid, uint32 guildId);

// Reschedules a meet greeting whose check failed for a reason that can
// pass again moments later (range, visibility, line of sight), for up
// to a few seconds after the first failure. False once it should drop.
bool DeferMeetGreeting(uint32 messageId, char const* reason);

// Releases the held Guild follow-up of a meet greeting once the
// greeting was spoken, or cancels it when the greeting was dropped.
void SettleMeetGreetingFollowUp(uint32 eventId, bool greeted);

void AddLLMChatterGuildWorldScripts();

#endif
