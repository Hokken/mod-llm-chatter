/*
 * mod-llm-chatter - open-world PvP reactions
 *
 * A lone guild bot that kills an enemy-faction bot may comment in Guild
 * chat, and a bot killed by an enemy-faction bot may complain in Guild
 * chat or in its zone's General channel. Nothing is queued unless a
 * real player can read the line.
 */

#include "LLMChatterGuildPvP.h"

#include "LLMChatterAudience.h"
#include "LLMChatterConfig.h"
#include "LLMChatterGuild.h"
#include "LLMChatterShared.h"

#include "Guild.h"
#include "GuildMgr.h"
#include "Player.h"
#include "Random.h"

#include <ctime>
#include <mutex>
#include <string>
#include <unordered_map>

namespace
{
// PvP kill hooks run on map threads.
std::mutex sPvpCooldownMutex;
std::unordered_map<uint32, time_t> sGuildPvpKillCooldowns;
std::unordered_map<uint32, time_t> sPvpDeathVictimCooldowns;
std::unordered_map<uint32, time_t> sGuildPvpDeathCooldowns;
std::unordered_map<uint64, time_t> sZonePvpDeathCooldowns;

char const* TeamName(TeamId team)
{
    return team == TEAM_ALLIANCE ? "Alliance" : "Horde";
}

bool GuildEventsAllowed()
{
    return sLLMChatterConfig->_guildChatterEnable;
}

bool GuildConversationActive(uint32 guildId)
{
    return WasGuildPlayerInteractionRecent(
        guildId,
        sLLMChatterConfig->_guildPlayerIdleSuppressionSeconds);
}

template <typename Key>
bool CooldownFree(
    std::unordered_map<Key, time_t> const& cache,
    Key key, uint32 seconds, time_t now)
{
    auto it = cache.find(key);
    return it == cache.end()
        || now - it->second >= static_cast<time_t>(seconds);
}

std::string PlayerJson(Player* player, char const* prefix)
{
    return fmt::format(
        R"("{0}_guid":{1},"{0}_name":"{2}","{0}_race":"{3}",)"
        R"("{0}_class":"{4}","{0}_gender":"{5}","{0}_level":{6},)"
        R"("{0}_is_bot":{7},"{0}_team":"{8}")",
        prefix,
        player->GetGUID().GetCounter(),
        JsonEscape(player->GetName()),
        GetRaceName(player->getRace()),
        GetChatterClassName(player->getClass()),
        player->getGender() == GENDER_FEMALE ? "female" : "male",
        player->GetLevel(),
        IsPlayerBot(player) ? "true" : "false",
        TeamName(player->GetTeamId()));
}

std::string GuildFields(Guild* guild, TeamId team)
{
    return fmt::format(
        R"("guild_id":{},"guild_name":"{}","team":"{}")",
        guild->GetId(),
        JsonEscape(guild->GetName()),
        TeamName(team));
}

void QueuePvpEvent(
    char const* eventType,
    Player* subject,
    Player* target,
    std::string const& json)
{
    QueueChatterEvent(
        eventType,
        "player",
        subject->GetZoneId(),
        subject->GetMapId(),
        GetChatterEventPriority(eventType),
        "",
        subject->GetGUID().GetCounter(),
        subject->GetName(),
        target->GetGUID().GetCounter(),
        target->GetName(),
        0,
        EscapeString(json),
        0,
        120,
        false);
}

void QueueGuildPvpKill(Player* killer, Player* killed)
{
    if (!GuildEventsAllowed() || !sLLMChatterConfig->_guildPvpKillEnable)
        return;
    if (!IsPlayerBot(killer) || !IsPlayerBot(killed)
        || IsGroupedWithRealPlayer(killer))
        return;

    uint32 guildId = killer->GetGuildId();
    Guild* guild = guildId ? sGuildMgr->GetGuildById(guildId) : nullptr;
    if (!guild || GuildConversationActive(guildId)
        || !PickRealGuildMember(guildId))
        return;

    time_t now = time(nullptr);
    uint32 killerGuid = killer->GetGUID().GetCounter();
    {
        std::lock_guard<std::mutex> guard(sPvpCooldownMutex);
        if (!CooldownFree(sGuildPvpKillCooldowns, killerGuid,
                sLLMChatterConfig->_guildPvpKillCooldown, now))
            return;
        if (urand(1, 100) > sLLMChatterConfig->_guildPvpKillChance)
            return;
        sGuildPvpKillCooldowns[killerGuid] = now;
    }

    std::string json = fmt::format(
        R"({{{},{},{},"zone_id":{},"area_id":{}}})",
        GuildFields(guild, killer->GetTeamId()),
        PlayerJson(killer, "bot"),
        PlayerJson(killed, "victim"),
        killer->GetZoneId(),
        killer->GetAreaId());
    QueuePvpEvent("guild_pvp_kill", killer, killed, json);
}

void QueuePvpDeathComplaint(Player* killer, Player* killed)
{
    if (!IsPlayerBot(killer) || !IsPlayerBot(killed)
        || IsGroupedWithRealPlayer(killed))
        return;

    LLMChatterConfig const* config = sLLMChatterConfig;
    uint32 guildId = killed->GetGuildId();
    Guild* guild = nullptr;
    if (GuildEventsAllowed() && config->_guildPvpDeathEnable
        && guildId && !GuildConversationActive(guildId)
        && PickRealGuildMember(guildId))
        guild = sGuildMgr->GetGuildById(guildId);
    uint32 zoneId = killed->GetZoneId();
    TeamId team = killed->GetTeamId();
    bool zoneOpen = config->_generalChannelEnable
        && config->_generalPvpDeathEnable
        && CanSpeakInGeneralChannel(killed)
        && PickRealPlayerInZone(zoneId, team);
    if (!guild && !zoneOpen)
        return;

    time_t now = time(nullptr);
    uint32 victimGuid = killed->GetGUID().GetCounter();
    uint64 zoneKey = (static_cast<uint64>(zoneId) << 1)
        | (team == TEAM_ALLIANCE ? 0u : 1u);
    bool toGuild = false;
    {
        std::lock_guard<std::mutex> guard(sPvpCooldownMutex);
        if (!CooldownFree(sPvpDeathVictimCooldowns, victimGuid,
                config->_pvpDeathVictimCooldown, now))
            return;
        if (guild
            && CooldownFree(sGuildPvpDeathCooldowns, guildId,
                config->_guildPvpDeathGuildCooldown, now)
            && urand(1, 100) <= config->_guildPvpDeathChance)
        {
            sGuildPvpDeathCooldowns[guildId] = now;
            toGuild = true;
        }
        else if (zoneOpen
            && CooldownFree(sZonePvpDeathCooldowns, zoneKey,
                config->_generalPvpDeathZoneCooldown, now)
            && urand(1, 100) <= config->_generalPvpDeathChance)
            sZonePvpDeathCooldowns[zoneKey] = now;
        else
            return;
        sPvpDeathVictimCooldowns[victimGuid] = now;
    }

    char const* eventType =
        toGuild ? "guild_pvp_death" : "zone_pvp_death";
    std::string head = toGuild
        ? GuildFields(guild, team)
        : fmt::format(R"("team":"{}")", TeamName(team));
    std::string json = fmt::format(
        R"({{{},{},{},"zone_id":{},"area_id":{}}})",
        head,
        PlayerJson(killed, "bot"),
        PlayerJson(killer, "killer"),
        zoneId,
        killed->GetAreaId());
    QueuePvpEvent(eventType, killed, killer, json);
}
} // namespace

void HandleOpenWorldPvpKill(Player* killer, Player* killed)
{
    if (!sLLMChatterConfig || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem
        || !killer || !killed || killer == killed
        || killer->InBattleground() || killer->InArena()
        || killer->GetTeamId() == killed->GetTeamId())
        return;

    QueueGuildPvpKill(killer, killed);
    QueuePvpDeathComplaint(killer, killed);
}
