#ifndef MOD_LLM_CHATTER_GUILD_H
#define MOD_LLM_CHATTER_GUILD_H

#include "Define.h"

#include <string>
#include <vector>

class Player;

void AddLLMChatterGuildScripts();
void AddLLMChatterGuildMemberScripts();

void NoteGuildPlayerInteraction(uint32 guildId);

bool WasGuildPlayerInteractionRecent(
    uint32 guildId, uint32 seconds);

void UpdatePendingGuildLoginGreetings();

void RecordDeliveredGuildLine(
    uint32 guildId,
    uint32 eventId,
    uint32 botGuid,
    std::string const& botName,
    std::string const& message);

// Guild event producers reuse the Guild candidate selection and sessions
// owned by LLMChatterGuild.cpp.
std::vector<Player*> GetGuildEventBots(
    uint32 guildId, Player* anchor, uint32 maxCandidates);
std::string BuildGuildEventCandidatesJson(
    std::vector<Player*> const& bots);
void EnsureGuildSessionForPlayer(Player* player);

#endif
