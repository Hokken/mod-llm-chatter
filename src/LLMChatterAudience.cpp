/*
 * mod-llm-chatter - real players who can read a bot's line
 */

#include "LLMChatterAudience.h"

#include "LLMChatterShared.h"

#include "Containers.h"
#include "Player.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

std::vector<Player*> CollectRealPlayers(
    std::function<bool(Player*)> const& filter, std::size_t limit)
{
    std::vector<Player*> players;
    // Playerbot sessions are not registered with WorldSessionMgr, so
    // this walk only sees real players.
    for (auto const& pair : sWorldSessionMgr->GetAllSessions())
    {
        WorldSession* session = pair.second;
        if (!session || session->PlayerLoading())
            continue;
        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld() || IsPlayerBot(player))
            continue;
        if (filter(player))
            players.push_back(player);
    }
    Acore::Containers::RandomShuffle(players);
    if (limit && players.size() > limit)
        players.resize(limit);
    return players;
}

std::vector<Player*> CollectRealPlayersInZone(
    uint32 zoneId, TeamId team, std::size_t limit)
{
    return CollectRealPlayers(
        [zoneId, team](Player* player)
        {
            return player->GetZoneId() == zoneId
                && player->GetTeamId() == team;
        },
        limit);
}

std::vector<Player*> CollectRealGuildMembers(
    uint32 guildId, std::size_t limit)
{
    if (!guildId)
        return {};
    return CollectRealPlayers(
        [guildId](Player* player)
        {
            return player->GetGuildId() == guildId;
        },
        limit);
}

Player* PickRealPlayerInZone(uint32 zoneId, TeamId team)
{
    std::vector<Player*> players =
        CollectRealPlayersInZone(zoneId, team, 1);
    return players.empty() ? nullptr : players.front();
}

Player* PickRealGuildMember(uint32 guildId)
{
    std::vector<Player*> players = CollectRealGuildMembers(guildId, 1);
    return players.empty() ? nullptr : players.front();
}
