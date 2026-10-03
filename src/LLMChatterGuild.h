#ifndef MOD_LLM_CHATTER_GUILD_H
#define MOD_LLM_CHATTER_GUILD_H

#include "Define.h"

#include <string>

void AddLLMChatterGuildScripts();

void NoteGuildPlayerInteraction(uint32 guildId);

bool WasGuildPlayerInteractionRecent(
    uint32 guildId, uint32 seconds);

// A real player's own Guild message, or a delivered reply to one. The
// login welcome counts as interaction above but not as conversation.
void NoteGuildPlayerConversation(uint32 guildId);

bool WasGuildPlayerConversationRecent(
    uint32 guildId, uint32 seconds);

void UpdatePendingGuildLoginGreetings();

void RecordDeliveredGuildLine(
    uint32 guildId,
    uint32 eventId,
    uint32 botGuid,
    std::string const& botName,
    std::string const& message);

#endif
