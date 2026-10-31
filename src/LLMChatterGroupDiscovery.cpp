/*
 * mod-llm-chatter - subzone discoveries for bot memories
 *
 * Owns:
 *   - watching the explored-area flags of real players
 *     grouped with bots, and the per-player snapshots
 *   - mapping a newly set flag back to its subzone
 *   - which party bots were near the player at that moment
 *   - the bot_group_discovery payload (player, level,
 *     zone, subzone, map, nearby bots)
 *
 * The core grants exploration XP only below the level cap,
 * so OnPlayerGiveXP misses discoveries at max level. The
 * explored flags (PLAYER_EXPLORED_ZONES_*) are set at every
 * level, so the world update compares them with the last
 * snapshot instead. A player seen for the first time only
 * sets the baseline. Only areas the client announces
 * ("Discovered: ...", area_level > 0) inside a zone count.
 * Only bots within kDiscoveryBotRange of the player found
 * the place with them; with none near, nothing is queued.
 * The bridge decides whether those bots remember the place
 * (levels, capital cities, subzone description). Battlegrounds and arenas are
 * excluded.
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroup.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "DBCStores.h"
#include "Group.h"
#include "Map.h"
#include "Player.h"
#include "World.h"
#include "WorldSessionMgr.h"

#include <array>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{

using ExploredFlags =
    std::array<uint32, PLAYER_EXPLORED_ZONES_SIZE>;

// Yards: a bot this close to the player discovered the place
// with them; one across the zone did not.
constexpr float kDiscoveryBotRange = 100.0f;

// Real player guid -> explored flags at the last scan.
std::map<uint64, ExploredFlags> _exploredSnapshots;

// exploreFlag -> announced subzone, built once from the DBC.
std::unordered_map<uint32, AreaTableEntry const*> const&
DiscoverableAreas()
{
    static std::unordered_map<uint32, AreaTableEntry const*> areas =
        []
        {
            std::unordered_map<uint32, AreaTableEntry const*> map;
            for (uint32 i = 0; i < sAreaTableStore.GetNumRows(); ++i)
            {
                AreaTableEntry const* area =
                    sAreaTableStore.LookupEntry(i);
                if (area && area->zone && area->area_level > 0)
                    map.emplace(area->exploreFlag, area);
            }
            return map;
        }();
    return areas;
}

ExploredFlags ReadExploredFlags(Player* player)
{
    ExploredFlags flags{};
    for (uint32 i = 0; i < PLAYER_EXPLORED_ZONES_SIZE; ++i)
        flags[i] = player->GetUInt32Value(PLAYER_EXPLORED_ZONES_1 + i);
    return flags;
}

std::vector<uint32> NearbyBotGuids(Player* player, Group* group)
{
    std::vector<uint32> guids;
    for (GroupReference* itr = group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (!member || member == player || !member->IsInWorld()
            || !IsPlayerBot(member))
            continue;
        if (player->IsWithinDistInMap(member, kDiscoveryBotRange))
            guids.push_back(member->GetGUID().GetCounter());
    }
    return guids;
}

void QueueDiscovery(
    Player* player, Group* group, AreaTableEntry const* area)
{
    std::vector<uint32> nearby = NearbyBotGuids(player, group);
    if (nearby.empty())
        return;

    std::string nearbyJson;
    for (uint32 guid : nearby)
    {
        if (!nearbyJson.empty())
            nearbyJson += ",";
        nearbyJson += std::to_string(guid);
    }

    std::string areaName = GetAreaNameForLocale(area->ID);
    std::string extraData = "{"
        "\"group_id\":"
            + std::to_string(group->GetGUID().GetCounter()) + ","
        "\"player_guid\":"
            + std::to_string(player->GetGUID().GetCounter()) + ","
        "\"player_name\":\"" + JsonEscape(player->GetName()) + "\","
        "\"player_level\":"
            + std::to_string(player->GetLevel()) + ","
        "\"zone_id\":" + std::to_string(area->zone) + ","
        "\"area_id\":" + std::to_string(area->ID) + ","
        "\"map_id\":" + std::to_string(player->GetMapId()) + ","
        "\"area_name\":\"" + JsonEscape(areaName) + "\","
        "\"nearby_bot_guids\":[" + nearbyJson + "]"
        "}";

    QueueChatterEvent(
        "bot_group_discovery",
        "player",
        area->zone,
        player->GetMapId(),
        GetChatterEventPriority("bot_group_discovery"),
        "",
        player->GetGUID().GetCounter(),
        player->GetName(),
        0,
        areaName,
        area->ID,
        EscapeString(extraData),
        0,
        300,
        false
    );
}

void ScanPlayer(
    Player* player, Group* group, std::set<uint64>& seen)
{
    uint64 guid = player->GetGUID().GetRawValue();
    seen.insert(guid);
    ExploredFlags current = ReadExploredFlags(player);

    auto it = _exploredSnapshots.find(guid);
    if (it == _exploredSnapshots.end())
    {
        // First sight (login, new group): baseline only.
        _exploredSnapshots.emplace(guid, current);
        return;
    }

    auto const& areas = DiscoverableAreas();
    for (uint32 i = 0; i < PLAYER_EXPLORED_ZONES_SIZE; ++i)
    {
        uint32 added = current[i] & ~it->second[i];
        for (uint32 bit = 0; added && bit < 32; ++bit)
        {
            if (!(added & (1u << bit)))
                continue;
            added &= ~(1u << bit);
            auto area = areas.find(i * 32 + bit);
            if (area != areas.end())
                QueueDiscovery(player, group, area->second);
        }
    }
    it->second = current;
}

} // namespace

void CheckGroupDiscoveries()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter
        || !sLLMChatterConfig->_memoryDiscoveryEnable)
    {
        _exploredSnapshots.clear();
        return;
    }

    std::set<uint64> seen;
    for (auto const& [id, session] :
         sWorldSessionMgr->GetAllSessions())
    {
        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld()
            || IsPlayerBot(player))
            continue;

        Group* group = player->GetGroup();
        if (!group || !CountBotsInGroup(group))
            continue;

        Map* map = player->GetMap();
        if (map && map->IsBattlegroundOrArena())
            continue;

        ScanPlayer(player, group, seen);
    }

    // Offline or ungrouped players re-baseline next time,
    // so flags set while unwatched never count as new.
    for (auto it = _exploredSnapshots.begin();
         it != _exploredSnapshots.end();)
    {
        if (seen.count(it->first))
            ++it;
        else
            it = _exploredSnapshots.erase(it);
    }
}
