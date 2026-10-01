/*
 * mod-llm-chatter - guild world events
 *
 * Open-world guild moments: a guild bot greeting a guildmate it meets,
 * a new member announcing the join in General, PvP kill comments
 * (guild chat for lone bots, party chat for the player's group), a bot
 * killed by an enemy bot complaining in Guild or zone General chat, and
 * a bot telling the guild about a friendly NPC near it.
 */

#include "LLMChatterGuild.h"
#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "CellImpl.h"
#include "Containers.h"
#include "Creature.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "Guild.h"
#include "GuildMgr.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "WorldSession.h"

#include <algorithm>
#include <ctime>
#include <list>
#include <mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace
{
constexpr uint32 kJoinAnnounceDelaySeconds = 8;
constexpr uint32 kJoinAnnounceExpireSeconds = 120;
constexpr uint32 kJoinAnnounceMaxResponders = 3;
constexpr uint32 kNpcPairCooldownSeconds = 6 * 3600;

struct PendingJoinAnnounce
{
    uint32 guildId = 0;
    uint32 memberGuid = 0;
    time_t dueAt = 0;
};

std::mutex sJoinAnnounceMutex;
std::vector<PendingJoinAnnounce> sPendingJoinAnnounces;

std::unordered_map<std::string, time_t> sMeetCooldowns;
std::unordered_map<std::string, time_t> sNpcPairCooldowns;
std::unordered_map<uint32, time_t> sGuildNpcCooldowns;
time_t sLastWorldScan = 0;

// PvP kill hooks run on map threads.
std::mutex sPvpCooldownMutex;
std::unordered_map<uint32, time_t> sGuildPvpKillCooldowns;
std::unordered_map<uint32, time_t> sPvpDeathVictimCooldowns;
std::unordered_map<uint32, time_t> sGuildPvpDeathCooldowns;
std::unordered_map<uint64, time_t> sZonePvpDeathCooldowns;

struct NearbyPlayerCheck
{
    WorldObject const* _obj;
    float _range;

    NearbyPlayerCheck(WorldObject const* obj, float range)
        : _obj(obj), _range(range) {}

    bool operator()(Player* other)
    {
        return other && other->IsInWorld()
            && _obj->IsWithinDistInMap(other, _range);
    }
};

struct NearbyNpcCheck
{
    WorldObject const* _obj;
    float _range;

    NearbyNpcCheck(WorldObject const* obj, float range)
        : _obj(obj), _range(range) {}

    WorldObject const& GetFocusObject() const
    {
        return *_obj;
    }

    bool operator()(Unit* unit)
    {
        return unit && unit->IsAlive() && unit->ToCreature()
            && _obj->IsWithinDistInMap(unit, _range);
    }
};

char const* TeamName(TeamId team)
{
    return team == TEAM_ALLIANCE ? "Alliance" : "Horde";
}

bool GuildEventsAllowed()
{
    return sLLMChatterConfig
        && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_useEventSystem
        && sLLMChatterConfig->_guildChatterEnable;
}

bool IsCalmInOpenWorld(Player* player)
{
    return player && player->IsInWorld() && player->IsAlive()
        && IsInOverworld(player) && !player->IsInCombat()
        && !player->IsInFlight() && !player->InBattleground();
}

bool OnCooldown(
    std::unordered_map<std::string, time_t>& cache,
    std::string const& key, uint32 seconds, time_t now)
{
    auto it = cache.find(key);
    return it != cache.end()
        && now - it->second < static_cast<time_t>(seconds);
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

void EvictExpired(
    std::unordered_map<std::string, time_t>& cache,
    uint32 seconds, time_t now)
{
    for (auto it = cache.begin(); it != cache.end();)
    {
        if (now - it->second >= static_cast<time_t>(seconds))
            it = cache.erase(it);
        else
            ++it;
    }
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

void QueueGuildWorldEvent(
    char const* eventType,
    Player* subject,
    uint32 targetGuid,
    std::string const& targetName,
    uint32 targetEntry,
    std::string const& cooldownKey,
    std::string const& json)
{
    QueueChatterEvent(
        eventType,
        "player",
        subject->GetZoneId(),
        subject->GetMapId(),
        GetChatterEventPriority(eventType),
        cooldownKey,
        subject->GetGUID().GetCounter(),
        subject->GetName(),
        targetGuid,
        targetName,
        targetEntry,
        EscapeString(json),
        0,
        120,
        false);
}

bool InSameGroup(Player* left, Player* right)
{
    Group* group = left->GetGroup();
    return group && group == right->GetGroup();
}

bool GroupHasRealMember(Group* group)
{
    for (GroupReference* itr = group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (member && !IsPlayerBot(member))
            return true;
    }
    return false;
}

Player* PickGroupBot(Group* group, Player* killer)
{
    if (IsPlayerBot(killer) && killer->IsInWorld())
        return killer;
    std::vector<Player*> bots;
    for (GroupReference* itr = group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (member && member->IsInWorld() && IsPlayerBot(member)
            && member->GetMap() == killer->GetMap())
            bots.push_back(member);
    }
    if (bots.empty())
        return nullptr;
    return bots[urand(0, bots.size() - 1)];
}

// ------------------------------------------------------------------
// Meet greeting
// ------------------------------------------------------------------

void ScanMeetGreetings(Player* player, time_t now)
{
    uint32 guildId = player->GetGuildId();
    Guild* guild = sGuildMgr->GetGuildById(guildId);
    if (!guild || !IsCalmInOpenWorld(player))
        return;

    float radius = static_cast<float>(
        sLLMChatterConfig->_guildMeetGreetingRadius);
    std::list<Player*> nearby;
    NearbyPlayerCheck check(player, radius);
    Acore::PlayerListSearcher<NearbyPlayerCheck>
        searcher(player, nearby, check);
    Cell::VisitObjects(player, searcher, radius);

    uint32 cooldown =
        sLLMChatterConfig->_guildMeetGreetingCooldownHours * 3600;
    for (Player* bot : nearby)
    {
        if (bot == player || !IsPlayerBot(bot)
            || bot->GetGuildId() != guildId
            || bot->GetTeamId() != player->GetTeamId()
            || InSameGroup(bot, player)
            || !IsCalmInOpenWorld(bot)
            || !player->CanSeeOrDetect(bot)
            || !player->IsWithinLOSInMap(bot))
            continue;

        std::string key = fmt::format(
            "guild_meet:{}:{}",
            bot->GetGUID().GetCounter(),
            player->GetGUID().GetCounter());
        if (OnCooldown(sMeetCooldowns, key, cooldown, now))
            continue;
        if (IsPersistedEventOnCooldown(key, cooldown))
        {
            sMeetCooldowns[key] = now - cooldown / 2;
            continue;
        }
        sMeetCooldowns[key] = now;

        std::string json = fmt::format(
            R"({{{},{},{},"zone_id":{},"area_id":{}}})",
            GuildFields(guild, player->GetTeamId()),
            PlayerJson(bot, "bot"),
            PlayerJson(player, "player"),
            bot->GetZoneId(),
            bot->GetAreaId());
        QueueGuildWorldEvent(
            "guild_meet_greeting", bot,
            player->GetGUID().GetCounter(), player->GetName(), 0,
            key, json);
        HoldBotForReply(bot, player, 10000);
        LOG_DEBUG("module",
            "LLMChatter: guild_meet_greeting bot={} player={}",
            bot->GetName(), player->GetName());
        return;
    }
}

// ------------------------------------------------------------------
// NPC encounter
// ------------------------------------------------------------------

bool IsFriendlyServiceNpc(Player* bot, Creature* creature)
{
    if (!creature || !creature->IsAlive() || !creature->GetSpawnId()
        || creature->IsPet() || creature->IsTotem()
        || creature->IsGuardian() || creature->IsInCombat()
        || IsLLMChatterInternalCreature(creature)
        || creature->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE)
        || !creature->IsFriendlyTo(bot))
        return false;
    uint32 flags = creature->GetUInt32Value(UNIT_NPC_FLAGS);
    return flags & (UNIT_NPC_FLAG_VENDOR | UNIT_NPC_FLAG_TRAINER
        | UNIT_NPC_FLAG_TRAINER_PROFESSION | UNIT_NPC_FLAG_INNKEEPER
        | UNIT_NPC_FLAG_FLIGHTMASTER | UNIT_NPC_FLAG_BANKER
        | UNIT_NPC_FLAG_REPAIR | UNIT_NPC_FLAG_AUCTIONEER
        | UNIT_NPC_FLAG_STABLEMASTER | UNIT_NPC_FLAG_QUESTGIVER);
}

bool TryNpcEncounter(
    Guild* guild, std::vector<Player*> const& bots, time_t now)
{
    auto guildIt = sGuildNpcCooldowns.find(guild->GetId());
    if (guildIt != sGuildNpcCooldowns.end()
        && now - guildIt->second
            < static_cast<time_t>(
                sLLMChatterConfig->_guildNpcEncounterCooldown))
        return false;
    if (urand(1, 100) > sLLMChatterConfig->_guildNpcEncounterChance)
        return false;

    std::vector<Player*> shuffled = bots;
    Acore::Containers::RandomShuffle(shuffled);
    float radius = static_cast<float>(
        sLLMChatterConfig->_guildNpcEncounterRadius);
    for (Player* bot : shuffled)
    {
        if (!IsCalmInOpenWorld(bot) || IsGroupedWithRealPlayer(bot))
            continue;

        std::list<Creature*> creatures;
        NearbyNpcCheck check(bot, radius);
        Acore::CreatureListSearcher<NearbyNpcCheck>
            searcher(bot, creatures, check);
        Cell::VisitObjects(bot, searcher, radius);

        std::vector<Creature*> options;
        for (Creature* creature : creatures)
        {
            if (!IsFriendlyServiceNpc(bot, creature))
                continue;
            std::string key = fmt::format(
                "{}:{}", bot->GetGUID().GetCounter(),
                creature->GetSpawnId());
            if (!OnCooldown(sNpcPairCooldowns, key,
                    kNpcPairCooldownSeconds, now))
                options.push_back(creature);
        }
        if (options.empty())
            continue;

        Creature* npc = options[urand(0, options.size() - 1)];
        sNpcPairCooldowns[fmt::format(
            "{}:{}", bot->GetGUID().GetCounter(),
            npc->GetSpawnId())] = now;
        sGuildNpcCooldowns[guild->GetId()] = now;

        CreatureTemplate const* tmpl = npc->GetCreatureTemplate();
        std::string json = fmt::format(
            R"({{{},{},"npc_name":"{}","npc_subname":"{}",)"
            R"("npc_role":"{}","npc_entry":{},"zone_id":{},)"
            R"("area_id":{}}})",
            GuildFields(guild, bot->GetTeamId()),
            PlayerJson(bot, "bot"),
            JsonEscape(npc->GetName()),
            JsonEscape(tmpl ? tmpl->SubName : ""),
            JsonEscape(GetCreatureRoleName(npc)),
            npc->GetEntry(),
            bot->GetZoneId(),
            bot->GetAreaId());
        QueueGuildWorldEvent(
            "guild_npc_encounter", bot, 0, npc->GetName(),
            npc->GetEntry(), "", json);
        return true;
    }
    return false;
}

// ------------------------------------------------------------------
// Join announcement in General
// ------------------------------------------------------------------

void FlushJoinAnnounce(PendingJoinAnnounce const& pending)
{
    if (urand(1, 100)
        > sLLMChatterConfig->_guildJoinZoneAnnounceChance)
        return;
    Guild* guild = sGuildMgr->GetGuildById(pending.guildId);
    Player* bot = ObjectAccessor::FindConnectedPlayer(
        ObjectGuid::Create<HighGuid::Player>(pending.memberGuid));
    if (!guild || !bot || !IsPlayerBot(bot)
        || bot->GetGuildId() != pending.guildId
        || !IsCalmInOpenWorld(bot)
        || IsGroupedWithRealPlayer(bot)
        || !CanSpeakInGeneralChannel(bot))
        return;

    uint32 zoneId = bot->GetZoneId();
    TeamId team = bot->GetTeamId();
    if (!PickRealPlayerInZone(zoneId, team))
        return;

    std::vector<Player*> responders;
    // Playerbot sessions are not registered with WorldSessionMgr.
    for (auto const& [guid, other] : ObjectAccessor::GetPlayers())
    {
        if (other && other != bot && IsPlayerBot(other)
            && other->IsInWorld() && other->GetZoneId() == zoneId
            && other->GetTeamId() == team
            && !IsGroupedWithRealPlayer(other)
            && CanSpeakInGeneralChannel(other))
            responders.push_back(other);
    }
    Acore::Containers::RandomShuffle(responders);
    if (responders.size() > kJoinAnnounceMaxResponders)
        responders.resize(kJoinAnnounceMaxResponders);

    std::string candidates;
    for (Player* other : responders)
    {
        candidates += fmt::format(
            R"({}{{"guid":{},"name":"{}","guild_id":{}}})",
            candidates.empty() ? "" : ",",
            other->GetGUID().GetCounter(),
            JsonEscape(other->GetName()),
            other->GetGuildId());
    }
    std::string json = fmt::format(
        R"({{{},{},"zone_id":{},"area_id":{},"candidates":[{}]}})",
        GuildFields(guild, team),
        PlayerJson(bot, "bot"),
        zoneId,
        bot->GetAreaId(),
        candidates);
    QueueGuildWorldEvent(
        "guild_join_zone_announce", bot, 0, "", 0, "", json);
}

void ProcessJoinAnnounces(time_t now)
{
    std::vector<PendingJoinAnnounce> due;
    {
        std::lock_guard<std::mutex> guard(sJoinAnnounceMutex);
        auto split = std::partition(
            sPendingJoinAnnounces.begin(),
            sPendingJoinAnnounces.end(),
            [now](PendingJoinAnnounce const& pending)
            {
                return pending.dueAt > now;
            });
        due.assign(split, sPendingJoinAnnounces.end());
        sPendingJoinAnnounces.erase(
            split, sPendingJoinAnnounces.end());
    }
    for (PendingJoinAnnounce const& pending : due)
    {
        if (now - pending.dueAt
            <= static_cast<time_t>(kJoinAnnounceExpireSeconds))
            FlushJoinAnnounce(pending);
    }
}

// ------------------------------------------------------------------
// PvP kills
// ------------------------------------------------------------------

bool QueueGroupPvpKill(Player* killer, Player* killed)
{
    // Fallback for when the GroupChatter.PvP system (LLMChatterGroupPvP.cpp)
    // is off; otherwise it already queues the party's kill reaction.
    if (!sLLMChatterConfig->_useGroupChatter
        || !sLLMChatterConfig->_groupPvpKillEnable
        || sLLMChatterConfig->_pvpChatterEnable)
        return false;
    Group* group = killer->GetGroup();
    if (!group || !GroupHasRealMember(group))
        return false;
    if (urand(1, 100) > sLLMChatterConfig->_groupPvpKillChance)
        return false;

    Player* reactor = PickGroupBot(group, killer);
    if (!reactor)
        return false;

    uint32 groupId = group->GetGUID().GetCounter();
    std::string json = "{" + BuildBotIdentityFields(reactor, true)
        + fmt::format(
            R"(,"group_id":{},{},"killer_name":"{}",)"
            R"("killer_team":"{}","bot_team":"{}",)"
            R"("killer_is_reactor":{},"killer_is_real_player":{},)"
            R"("zone_id":{},"area_id":{},)",
            groupId,
            PlayerJson(killed, "victim"),
            JsonEscape(killer->GetName()),
            TeamName(killer->GetTeamId()),
            TeamName(reactor->GetTeamId()),
            killer == reactor ? "true" : "false",
            IsPlayerBot(killer) ? "false" : "true",
            reactor->GetZoneId(),
            reactor->GetAreaId())
        + BuildBotStateJson(reactor) + "}";

    QueueChatterEvent(
        "bot_group_pvp_kill",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority("bot_group_pvp_kill"),
        "",
        reactor->GetGUID().GetCounter(),
        reactor->GetName(),
        killed->GetGUID().GetCounter(),
        killed->GetName(),
        0,
        EscapeString(json),
        GetReactionDelaySeconds("bot_group_kill"),
        120,
        false);
    return true;
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
    if (!guild || !PickRealGuildMember(guildId))
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
    QueueGuildWorldEvent(
        "guild_pvp_kill", killer,
        killed->GetGUID().GetCounter(), killed->GetName(), 0,
        "", json);
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
        && guildId && PickRealGuildMember(guildId))
        guild = sGuildMgr->GetGuildById(guildId);
    uint32 zoneId = killed->GetZoneId();
    TeamId team = killed->GetTeamId();
    bool zoneOpen = config->_generalChannelEnable
        && config->_generalPvpDeathEnable
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
    QueueGuildWorldEvent(
        eventType, killed,
        killer->GetGUID().GetCounter(), killer->GetName(), 0,
        "", json);
}
} // namespace

void NoteGuildJoinForZoneAnnounce(uint32 guildId, uint32 memberGuid)
{
    if (!GuildEventsAllowed()
        || !sLLMChatterConfig->_guildJoinZoneAnnounceEnable)
        return;
    std::lock_guard<std::mutex> guard(sJoinAnnounceMutex);
    sPendingJoinAnnounces.push_back(
        {guildId, memberGuid,
         time(nullptr) + kJoinAnnounceDelaySeconds});
}

void HandleOpenWorldPvpKill(Player* killer, Player* killed)
{
    if (!sLLMChatterConfig || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem
        || !killer || !killed || killer == killed
        || killer->InBattleground() || killer->InArena()
        || killer->GetTeamId() == killed->GetTeamId())
        return;

    if (!QueueGroupPvpKill(killer, killed))
        QueueGuildPvpKill(killer, killed);
    QueuePvpDeathComplaint(killer, killed);
}

void UpdateGuildWorldEvents()
{
    if (!GuildEventsAllowed())
        return;

    time_t now = time(nullptr);
    ProcessJoinAnnounces(now);
    if (now - sLastWorldScan
        < static_cast<time_t>(
            sLLMChatterConfig->_guildWorldScanInterval))
        return;
    sLastWorldScan = now;

    bool meet = sLLMChatterConfig->_guildMeetGreetingEnable;
    bool npc = sLLMChatterConfig->_guildNpcEncounterEnable;
    if (!meet && !npc)
        return;

    std::vector<Player*> realPlayers;
    std::unordered_map<uint32, std::vector<Player*>> guildBots;
    // Playerbot sessions are not registered with WorldSessionMgr.
    for (auto const& [guid, player] : ObjectAccessor::GetPlayers())
    {
        if (!player || !player->IsInWorld() || !player->GetGuildId()
            || !player->GetSession() || player->GetSession()->PlayerLoading())
            continue;
        if (IsPlayerBot(player))
            guildBots[player->GetGuildId()].push_back(player);
        else
            realPlayers.push_back(player);
    }

    std::unordered_set<uint32> npcGuildsTried;
    for (Player* player : realPlayers)
    {
        uint32 guildId = player->GetGuildId();
        auto botsIt = guildBots.find(guildId);
        if (botsIt == guildBots.end())
            continue;
        if (meet)
            ScanMeetGreetings(player, now);
        if (npc && npcGuildsTried.insert(guildId).second)
            if (Guild* guild = sGuildMgr->GetGuildById(guildId))
                TryNpcEncounter(guild, botsIt->second, now);
    }

    EvictExpired(sMeetCooldowns,
        sLLMChatterConfig->_guildMeetGreetingCooldownHours * 3600, now);
    EvictExpired(sNpcPairCooldowns, kNpcPairCooldownSeconds, now);
}
