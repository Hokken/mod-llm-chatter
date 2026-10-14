/*
 * mod-llm-chatter - listener JSON for themed topics and rumors
 */

#include "LLMChatterThemedAudience.h"

#include "LLMChatterShared.h"

#include "Player.h"
#include "StringFormat.h"

std::string BuildAudienceJson(Player* player)
{
    if (!player)
        return "";

    return fmt::format(
        R"({{"guid":{},"name":"{}","level":{},"team":"{}",)"
        R"("race":"{}","class":"{}"}})",
        player->GetGUID().GetCounter(),
        JsonEscape(player->GetName()),
        player->GetLevel(),
        player->GetTeamId() == TEAM_ALLIANCE ? "Alliance" : "Horde",
        GetRaceName(player->getRace()),
        GetChatterClassName(player->getClass()));
}

std::string BuildAudienceListJson(std::vector<Player*> const& players)
{
    std::string json = "[";
    for (Player* player : players)
    {
        std::string entry = BuildAudienceJson(player);
        if (entry.empty())
            continue;
        if (json.size() > 1)
            json += ",";
        json += entry;
    }
    return json + "]";
}
