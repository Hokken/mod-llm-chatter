/*
 * mod-llm-chatter - real players who can read a bot's line
 */

#ifndef MOD_LLM_CHATTER_AUDIENCE_H
#define MOD_LLM_CHATTER_AUDIENCE_H

#include "Define.h"
#include "SharedDefines.h"

#include <cstddef>
#include <functional>
#include <vector>

class Player;

// Online real players (never playerbots) matching `filter`, in random
// order. A `limit` of 0 returns all of them.
std::vector<Player*> CollectRealPlayers(
    std::function<bool(Player*)> const& filter, std::size_t limit = 0);
std::vector<Player*> CollectRealPlayersInZone(
    uint32 zoneId, TeamId team, std::size_t limit = 0);
std::vector<Player*> CollectRealGuildMembers(
    uint32 guildId, std::size_t limit = 0);

// One random match, or nullptr.
Player* PickRealPlayerInZone(uint32 zoneId, TeamId team);
Player* PickRealGuildMember(uint32 guildId);

#endif
