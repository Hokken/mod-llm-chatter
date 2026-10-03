/*
 * mod-llm-chatter - guild world events
 *
 * Open-world guild moments: a guild bot greeting a guildmate it meets,
 * a new member announcing the join in its zone's General channel, and
 * a bot telling the guild about a friendly NPC near it.
 */

#include "LLMChatterGuildWorld.h"

#include "LLMChatterAudience.h"
#include "LLMChatterConfig.h"
#include "LLMChatterGuild.h"
#include "LLMChatterReplyHold.h"
#include "LLMChatterShared.h"

#include "CellImpl.h"
#include "Containers.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "Guild.h"
#include "GuildMgr.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "WorldSession.h"

#include <algorithm>
#include <ctime>
#include <list>
#include <mutex>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace
{
constexpr uint32 kJoinAnnounceDelaySeconds = 8;
constexpr uint32 kJoinAnnounceExpireSeconds = 120;
constexpr uint32 kJoinAnnounceMaxResponders = 3;
constexpr uint32 kNpcPairCooldownSeconds = 6 * 3600;
constexpr uint32 kMeetFollowUpMinDelay = 8;
constexpr uint32 kMeetFollowUpMaxDelay = 15;
constexpr uint32 kHeldFollowUpTimeoutSeconds = 600;
constexpr uint32 kHeldFollowUpSweepSeconds = 300;
constexpr uint32 kMeetDeliveryRetrySeconds = 2;
constexpr time_t kMeetDeliveryGraceSeconds = 8;

constexpr NPCFlags kServiceNpcFlags = NPCFlags(
    UNIT_NPC_FLAG_VENDOR | UNIT_NPC_FLAG_TRAINER
    | UNIT_NPC_FLAG_TRAINER_PROFESSION | UNIT_NPC_FLAG_INNKEEPER
    | UNIT_NPC_FLAG_FLIGHTMASTER | UNIT_NPC_FLAG_BANKER
    | UNIT_NPC_FLAG_REPAIR | UNIT_NPC_FLAG_AUCTIONEER
    | UNIT_NPC_FLAG_STABLEMASTER | UNIT_NPC_FLAG_QUESTGIVER);

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
// Meet greeting message id -> time its delivery check first failed.
std::unordered_map<uint32, time_t> sMeetDeliveryRetries;
time_t sLastWorldScan = 0;
time_t sLastHeldFollowUpSweep = 0;

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

bool GuildConversationActive(uint32 guildId)
{
    return WasGuildPlayerConversationRecent(
        guildId,
        sLLMChatterConfig->_guildPlayerIdleSuppressionSeconds);
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

        // The /say greeting is always allowed; the optional Guild
        // follow-up gives way to a live player conversation.
        std::string json = fmt::format(
            R"({{{},{},{},"zone_id":{},"area_id":{},)"
            R"("guild_post_allowed":{}}})",
            GuildFields(guild, player->GetTeamId()),
            PlayerJson(bot, "bot"),
            PlayerJson(player, "player"),
            bot->GetZoneId(),
            bot->GetAreaId(),
            GuildConversationActive(guildId) ? "false" : "true");
        QueueGuildWorldEvent(
            "guild_meet_greeting", bot,
            player->GetGUID().GetCounter(), player->GetName(), 0,
            key, json);
        HoldBotForReply(bot, player, LLM_CHATTER_MAX_REPLY_HOLD_MS);
        LOG_DEBUG("module",
            "LLMChatter: guild_meet_greeting bot={} player={}",
            bot->GetName(), player->GetName());
        return;
    }
}

void SweepHeldFollowUps(time_t now)
{
    if (now - sLastHeldFollowUpSweep
        < static_cast<time_t>(kHeldFollowUpSweepSeconds))
        return;
    sLastHeldFollowUpSweep = now;
    // A greeting that expired in the queue never reaches delivery, so
    // its follow-up would otherwise stay held.
    CharacterDatabase.Execute(
        "UPDATE llm_chatter_messages m "
        "JOIN llm_chatter_events e ON e.id = m.event_id "
        "SET m.delivered = 1, m.delivered_at = NOW(), "
        "m.drop_reason = 'meet_greeting_not_delivered' "
        "WHERE m.delivered = 0 AND m.deliver_at IS NULL "
        "AND e.event_type = 'guild_meet_greeting' "
        "AND e.created_at < DATE_SUB(NOW(), INTERVAL {} SECOND)",
        kHeldFollowUpTimeoutSeconds);
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
    return creature->HasNpcFlag(kServiceNpcFlags)
        && bot->CanSeeOrDetect(creature)
        && bot->IsWithinLOSInMap(creature);
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
    if (GuildConversationActive(guild->GetId()))
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
    SweepHeldFollowUps(now);

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
} // namespace

char const* CheckMeetGreetingDelivery(Player* bot, uint32 playerGuid)
{
    Player* player = playerGuid
        ? ObjectAccessor::FindConnectedPlayer(
            ObjectGuid::Create<HighGuid::Player>(playerGuid))
        : nullptr;
    if (!player || !player->IsInWorld())
        return "meet_player_gone";
    if (!bot || !bot->IsInWorld() || !bot->IsAlive()
        || bot->IsInCombat())
        return "meet_bot_unavailable";
    if (bot->GetMap() != player->GetMap())
        return "meet_other_map";
    float radius = sLLMChatterConfig
        ? static_cast<float>(sLLMChatterConfig->_guildMeetGreetingRadius)
        : 25.0f;
    if (!bot->IsWithinDistInMap(player, radius))
        return "meet_out_of_range";
    if (!player->CanSeeOrDetect(bot))
        return "meet_not_visible";
    if (!player->IsWithinLOSInMap(bot))
        return "meet_no_line_of_sight";
    return nullptr;
}

bool DeferMeetGreeting(uint32 messageId, char const* reason)
{
    time_t now = time(nullptr);
    for (auto it = sMeetDeliveryRetries.begin();
         it != sMeetDeliveryRetries.end();)
    {
        if (now - it->second > 2 * kMeetDeliveryGraceSeconds)
            it = sMeetDeliveryRetries.erase(it);
        else
            ++it;
    }

    std::string_view why = reason ? reason : "";
    bool transient = why == "meet_out_of_range"
        || why == "meet_not_visible"
        || why == "meet_no_line_of_sight";
    auto [entry, first] = sMeetDeliveryRetries.try_emplace(messageId, now);
    if (!transient
        || (!first && now - entry->second >= kMeetDeliveryGraceSeconds))
    {
        sMeetDeliveryRetries.erase(entry);
        return false;
    }

    LOG_DEBUG("module",
        "LLMChatter: guild_meet_greeting message {} deferred: {}",
        messageId, why);
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 0, drop_reason = NULL, "
        "deliver_at = DATE_ADD(NOW(), INTERVAL {} SECOND) "
        "WHERE id = {}",
        kMeetDeliveryRetrySeconds, messageId);
    return true;
}

void SettleMeetGreetingFollowUp(uint32 eventId, bool greeted)
{
    if (!eventId)
        return;
    if (greeted)
    {
        CharacterDatabase.DirectExecute(
            "UPDATE llm_chatter_messages "
            "SET deliver_at = DATE_ADD(NOW(), INTERVAL {} SECOND) "
            "WHERE event_id = {} AND delivered = 0 "
            "AND deliver_at IS NULL",
            urand(kMeetFollowUpMinDelay, kMeetFollowUpMaxDelay),
            eventId);
        return;
    }
    CharacterDatabase.DirectExecute(
        "UPDATE llm_chatter_messages "
        "SET delivered = 1, delivered_at = NOW(), "
        "drop_reason = 'meet_greeting_not_delivered' "
        "WHERE event_id = {} AND delivered = 0 "
        "AND deliver_at IS NULL",
        eventId);
}

class LLMChatterGuildWorldGuildScript : public GuildScript
{
public:
    LLMChatterGuildWorldGuildScript()
        : GuildScript("LLMChatterGuildWorldGuildScript",
              {GUILDHOOK_ON_ADD_MEMBER})
    {
    }

    void OnAddMember(
        Guild* guild, Player* player, uint8& /*plRank*/) override
    {
        if (guild && player && IsPlayerBot(player))
            NoteGuildJoinForZoneAnnounce(
                guild->GetId(), player->GetGUID().GetCounter());
    }
};

class LLMChatterGuildWorldWorldScript : public WorldScript
{
public:
    LLMChatterGuildWorldWorldScript()
        : WorldScript("LLMChatterGuildWorldWorldScript",
              {WORLDHOOK_ON_UPDATE})
    {
    }

    void OnUpdate(uint32 /*diff*/) override
    {
        UpdateGuildWorldEvents();
    }
};

void AddLLMChatterGuildWorldScripts()
{
    new LLMChatterGuildWorldGuildScript();
    new LLMChatterGuildWorldWorldScript();
}
