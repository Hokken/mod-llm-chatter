/*
 * mod-llm-chatter - listener JSON for themed topics and rumors
 */

#include "LLMChatterThemedAudience.h"

#include "LLMChatterShared.h"

#include "Config.h"
#include "ModuleMgr.h"
#include "Player.h"
#include "StringFormat.h"

#include <string_view>

namespace
{
constexpr uint32 kProgressionQuestBase = 66000;
constexpr uint8 kProgressionMaxTier = 18;

bool IsIndividualProgressionActive()
{
    static bool const compiledIn = []
    {
        for (std::string_view name :
             Acore::Module::GetEnableModulesList())
        {
            if (name == "mod-individual-progression")
                return true;
        }
        return false;
    }();
    return compiledIn
        && sConfigMgr->GetOption<bool>(
            "IndividualProgression.Enable", false, false);
}

uint8 GetIndividualProgressionTier(Player* player)
{
    uint8 tier = 0;
    for (uint8 i = 1; i <= kProgressionMaxTier; ++i)
    {
        if (player->GetQuestRewardStatus(
                kProgressionQuestBase + i))
            tier = i;
    }
    return tier;
}
} // namespace

std::string BuildAudienceJson(Player* player)
{
    if (!player)
        return "";

    bool ipActive = IsIndividualProgressionActive();
    return fmt::format(
        R"({{"guid":{},"name":"{}","level":{},"team":"{}",)"
        R"("race":"{}","class":"{}","is_gm":{},)"
        R"("ip_active":{},"progression_tier":{},)"
        R"("progression_limit":{},"ip_zg_tier":{},)"
        R"("ip_za_tier":{}}})",
        player->GetGUID().GetCounter(),
        JsonEscape(player->GetName()),
        player->GetLevel(),
        player->GetTeamId() == TEAM_ALLIANCE ? "Alliance" : "Horde",
        GetRaceName(player->getRace()),
        GetChatterClassName(player->getClass()),
        player->IsGameMaster() ? "true" : "false",
        ipActive ? "true" : "false",
        ipActive ? GetIndividualProgressionTier(player) : 0,
        ipActive
            ? sConfigMgr->GetOption<uint32>(
                "IndividualProgression.ProgressionLimit", 0, false)
            : 0,
        ipActive
            ? sConfigMgr->GetOption<uint32>(
                "IndividualProgression.RequiredZulGurubProgression",
                3, false)
            : 3,
        ipActive
            ? sConfigMgr->GetOption<uint32>(
                "IndividualProgression.RequiredZulAmanProgression",
                12, false)
            : 12);
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
