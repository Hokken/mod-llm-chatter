/*
 * mod-llm-chatter - open-world PvP reactions
 *
 * A lone guild bot that kills an enemy-faction bot may comment in Guild
 * chat, and a bot killed by an enemy-faction bot may complain in Guild
 * chat or in its zone's General channel. Nothing is queued unless a
 * real player can read the line.
 *
 * The kill hook runs on a map thread, so it only records the facts of
 * the kill. The world update decides and queues the lines, because
 * that work reads players on other maps and the shared General
 * channels.
 */

#include "LLMChatterGuildPvP.h"

#include "LLMChatterAudience.h"
#include "LLMChatterConfig.h"
#include "LLMChatterGuild.h"
#include "LLMChatterShared.h"

#include "Guild.h"
#include "GuildMgr.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"

#include <ctime>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace
{
// Kills recorded within one world tick are few; the cap only guards
// against a burst if the world update stalls.
constexpr std::size_t MAX_PENDING_PVP_KILLS = 64;

struct PvpFighter
{
    uint32 guid = 0;
    std::string name;
    std::string race;
    std::string className;
    bool female = false;
    uint32 level = 0;
    TeamId team = TEAM_ALLIANCE;
    uint32 guildId = 0;
    uint32 zoneId = 0;
    uint32 areaId = 0;
    uint32 mapId = 0;
};

struct PendingPvpKill
{
    PvpFighter killer;
    PvpFighter killed;
};

std::mutex sPendingPvpKillsMutex;
std::vector<PendingPvpKill> sPendingPvpKills;

// Only the world update reads and writes the cooldowns.
std::unordered_map<uint32, time_t> sGuildPvpKillCooldowns;
std::unordered_map<uint32, time_t> sGuildPvpKillGuildCooldowns;
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
    return WasGuildPlayerConversationRecent(
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

PvpFighter CaptureFighter(Player* player)
{
    PvpFighter fighter;
    fighter.guid = player->GetGUID().GetCounter();
    fighter.name = player->GetName();
    fighter.race = GetRaceName(player->getRace());
    fighter.className = GetChatterClassName(player->getClass());
    fighter.female = player->getGender() == GENDER_FEMALE;
    fighter.level = player->GetLevel();
    fighter.team = player->GetTeamId();
    fighter.guildId = player->GetGuildId();
    fighter.zoneId = player->GetZoneId();
    fighter.areaId = player->GetAreaId();
    fighter.mapId = player->GetMapId();
    return fighter;
}

// The bot still in the world, lone (not grouped with a real player).
Player* FindLoneBot(PvpFighter const& fighter)
{
    Player* bot = ObjectAccessor::FindPlayer(
        ObjectGuid::Create<HighGuid::Player>(fighter.guid));
    if (!bot || !bot->IsInWorld() || !IsPlayerBot(bot)
        || IsGroupedWithRealPlayer(bot))
        return nullptr;
    return bot;
}

std::string FighterJson(PvpFighter const& fighter, char const* prefix)
{
    return fmt::format(
        R"("{0}_guid":{1},"{0}_name":"{2}","{0}_race":"{3}",)"
        R"("{0}_class":"{4}","{0}_gender":"{5}","{0}_level":{6},)"
        R"("{0}_is_bot":true,"{0}_team":"{7}")",
        prefix,
        fighter.guid,
        JsonEscape(fighter.name),
        fighter.race,
        fighter.className,
        fighter.female ? "female" : "male",
        fighter.level,
        TeamName(fighter.team));
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
    PvpFighter const& subject,
    PvpFighter const& target,
    std::string const& json)
{
    QueueChatterEvent(
        eventType,
        "player",
        subject.zoneId,
        subject.mapId,
        GetChatterEventPriority(eventType),
        "",
        subject.guid,
        subject.name,
        target.guid,
        target.name,
        0,
        EscapeString(json),
        0,
        120,
        false);
}

void QueueGuildPvpKill(PendingPvpKill const& kill, time_t now)
{
    LLMChatterConfig const* config = sLLMChatterConfig;
    PvpFighter const& killer = kill.killer;
    if (!GuildEventsAllowed() || !config->_guildPvpKillEnable
        || !killer.guildId)
        return;

    Guild* guild = sGuildMgr->GetGuildById(killer.guildId);
    if (!guild || !FindLoneBot(killer)
        || GuildConversationActive(killer.guildId)
        || !PickRealGuildMember(killer.guildId))
        return;

    if (!CooldownFree(sGuildPvpKillCooldowns, killer.guid,
            config->_guildPvpKillCooldown, now)
        || !CooldownFree(sGuildPvpKillGuildCooldowns, killer.guildId,
            config->_guildPvpKillGuildCooldown, now))
        return;
    if (urand(1, 100) > config->_guildPvpKillChance)
        return;
    sGuildPvpKillCooldowns[killer.guid] = now;
    sGuildPvpKillGuildCooldowns[killer.guildId] = now;

    std::string json = fmt::format(
        R"({{{},{},{},"zone_id":{},"area_id":{}}})",
        GuildFields(guild, killer.team),
        FighterJson(killer, "bot"),
        FighterJson(kill.killed, "victim"),
        killer.zoneId,
        killer.areaId);
    QueuePvpEvent("guild_pvp_kill", killer, kill.killed, json);
}

bool GuildDeathOpen(PvpFighter const& killed)
{
    LLMChatterConfig const* config = sLLMChatterConfig;
    return GuildEventsAllowed() && config->_guildPvpDeathEnable
        && killed.guildId
        && !GuildConversationActive(killed.guildId)
        && PickRealGuildMember(killed.guildId);
}

// Checked only when the General route is tried: it may join the bot
// to its zone's General channel.
bool ZoneDeathOpen(Player* bot, PvpFighter const& killed)
{
    LLMChatterConfig const* config = sLLMChatterConfig;
    return config->_generalChannelEnable
        && config->_generalPvpDeathEnable
        && bot->GetZoneId() == killed.zoneId
        && PickRealPlayerInZone(killed.zoneId, killed.team)
        && CanSpeakInGeneralChannel(bot);
}

void QueuePvpDeathComplaint(PendingPvpKill const& kill, time_t now)
{
    LLMChatterConfig const* config = sLLMChatterConfig;
    PvpFighter const& killed = kill.killed;
    Player* bot = FindLoneBot(killed);
    if (!bot
        || !CooldownFree(sPvpDeathVictimCooldowns, killed.guid,
            config->_pvpDeathVictimCooldown, now))
        return;

    Guild* guild = nullptr;
    if (GuildDeathOpen(killed)
        && CooldownFree(sGuildPvpDeathCooldowns, killed.guildId,
            config->_guildPvpDeathGuildCooldown, now)
        && urand(1, 100) <= config->_guildPvpDeathChance)
        guild = sGuildMgr->GetGuildById(killed.guildId);

    uint64 zoneKey = (static_cast<uint64>(killed.zoneId) << 1)
        | (killed.team == TEAM_ALLIANCE ? 0u : 1u);
    if (guild)
        sGuildPvpDeathCooldowns[killed.guildId] = now;
    else if (CooldownFree(sZonePvpDeathCooldowns, zoneKey,
                 config->_generalPvpDeathZoneCooldown, now)
        && urand(1, 100) <= config->_generalPvpDeathChance
        && ZoneDeathOpen(bot, killed))
        sZonePvpDeathCooldowns[zoneKey] = now;
    else
        return;
    sPvpDeathVictimCooldowns[killed.guid] = now;

    char const* eventType =
        guild ? "guild_pvp_death" : "zone_pvp_death";
    std::string head = guild
        ? GuildFields(guild, killed.team)
        : fmt::format(R"("team":"{}")", TeamName(killed.team));
    std::string json = fmt::format(
        R"({{{},{},{},"zone_id":{},"area_id":{}}})",
        head,
        FighterJson(killed, "bot"),
        FighterJson(kill.killer, "killer"),
        killed.zoneId,
        killed.areaId);
    QueuePvpEvent(eventType, killed, kill.killer, json);
}

bool PvpReactionsEnabled()
{
    return sLLMChatterConfig && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_useEventSystem;
}

void ProcessPendingPvpKills()
{
    std::vector<PendingPvpKill> pending;
    {
        std::lock_guard<std::mutex> guard(sPendingPvpKillsMutex);
        pending.swap(sPendingPvpKills);
    }
    if (pending.empty() || !PvpReactionsEnabled())
        return;

    time_t now = time(nullptr);
    for (PendingPvpKill const& kill : pending)
    {
        QueueGuildPvpKill(kill, now);
        QueuePvpDeathComplaint(kill, now);
    }
}

class LLMChatterGuildPvPWorldScript : public WorldScript
{
public:
    LLMChatterGuildPvPWorldScript()
        : WorldScript(
              "LLMChatterGuildPvPWorldScript",
              {WORLDHOOK_ON_UPDATE}) {}

    void OnUpdate(uint32 /*diff*/) override
    {
        ProcessPendingPvpKills();
    }
};
} // namespace

void HandleOpenWorldPvpKill(Player* killer, Player* killed)
{
    if (!PvpReactionsEnabled()
        || !killer || !killed || killer == killed
        || killer->InBattleground() || killer->InArena()
        || killer->GetTeamId() == killed->GetTeamId()
        || !IsPlayerBot(killer) || !IsPlayerBot(killed))
        return;

    // Both players are on this map thread's map, so reading them here
    // is safe; everything else waits for the world update.
    PendingPvpKill kill;
    kill.killer = CaptureFighter(killer);
    kill.killed = CaptureFighter(killed);

    std::lock_guard<std::mutex> guard(sPendingPvpKillsMutex);
    if (sPendingPvpKills.size() < MAX_PENDING_PVP_KILLS)
        sPendingPvpKills.push_back(std::move(kill));
}

bool IsPvpReactionEvent(std::string const& eventType)
{
    return eventType == "guild_pvp_kill"
        || eventType == "guild_pvp_death"
        || eventType == "zone_pvp_death";
}

char const* CheckPvpReactionDelivery(
    Player* bot, std::string const& eventType,
    uint32 guildId, uint32 zoneId)
{
    if (eventType == "zone_pvp_death")
    {
        if (!zoneId || bot->GetZoneId() != zoneId)
            return "pvp_zone_changed";
        if (!PickRealPlayerInZone(zoneId, bot->GetTeamId()))
            return "pvp_no_reader";
        return nullptr;
    }

    if (!guildId || bot->GetGuildId() != guildId)
        return "pvp_guild_changed";
    if (!PickRealGuildMember(guildId))
        return "pvp_no_reader";
    return nullptr;
}

void AddLLMChatterGuildPvPScripts()
{
    new LLMChatterGuildPvPWorldScript();
}
