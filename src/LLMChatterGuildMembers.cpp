/*
 * mod-llm-chatter - guild news
 *
 * Batches guild joins, debounced rank changes and MOTD changes, then
 * queues guild_member_join, guild_rank_change and guild_motd_comment
 * events for the bridge (chatter_guild_events.py). Guild sessions and
 * login greetings stay in LLMChatterGuild.cpp.
 */

#include "LLMChatterGuild.h"

#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "CharacterCache.h"
#include "DatabaseEnv.h"
#include "Guild.h"
#include "GuildMgr.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace
{
// Guild hooks can fire from map threads (playerbots manage their own
// guilds), so the buffers below are only touched under this mutex.
std::mutex sGuildEventMutex;

struct PendingGuildJoinBatch
{
    std::vector<uint32> memberGuids;
    time_t dueAt = 0;
};

struct PendingGuildRankChange
{
    uint32 memberGuid = 0;
    uint8 originalRank = 0;
    uint8 currentRank = 0;
    uint32 actorGuid = 0;
};

struct PendingGuildRankBatch
{
    std::vector<PendingGuildRankChange> changes;
    time_t lastChangeAt = 0;
};

struct PendingGuildMotd
{
    std::string motd;
    time_t dueAt = 0;
};

std::unordered_map<uint32, PendingGuildJoinBatch>
    sPendingGuildJoins;
std::unordered_map<uint32, PendingGuildRankBatch>
    sPendingGuildRankChanges;
std::unordered_map<uint32, PendingGuildMotd>
    sPendingGuildMotds;
std::vector<uint32> sPendingGuildSessionStarts;
std::unordered_map<uint32, time_t> sGuildJoinTimes;

bool GuildMemberEventsAllowed()
{
    return sLLMChatterConfig
        && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_useEventSystem
        && sLLMChatterConfig->_guildChatterEnable;
}

void NoteGuildMemberJoined(uint32 guildId, uint32 memberGuid)
{
    time_t now = time(nullptr);
    std::lock_guard<std::mutex> guard(sGuildEventMutex);
    sGuildJoinTimes[memberGuid] = now;
    sPendingGuildSessionStarts.push_back(memberGuid);

    if (!GuildMemberEventsAllowed()
        || !sLLMChatterConfig->_guildJoinGreetingEnable)
    {
        return;
    }

    PendingGuildJoinBatch& batch = sPendingGuildJoins[guildId];
    if (batch.memberGuids.empty())
        batch.dueAt = now
            + sLLMChatterConfig->_guildJoinGreetingBatchSeconds;
    if (std::find(
            batch.memberGuids.begin(),
            batch.memberGuids.end(),
            memberGuid) == batch.memberGuids.end())
    {
        batch.memberGuids.push_back(memberGuid);
    }
}

void NoteGuildRankChanged(
    uint32 guildId,
    uint32 actorGuid,
    uint32 memberGuid,
    uint8 newRank,
    bool promoted)
{
    if (!GuildMemberEventsAllowed()
        || !sLLMChatterConfig->_guildRankChangeEnable)
    {
        return;
    }

    // Rank 0 is the Guild Master: a promotion lowers the id by one.
    uint8 oldRank = promoted
        ? static_cast<uint8>(newRank + 1)
        : static_cast<uint8>(newRank ? newRank - 1 : 0);

    std::lock_guard<std::mutex> guard(sGuildEventMutex);
    PendingGuildRankBatch& batch =
        sPendingGuildRankChanges[guildId];
    batch.lastChangeAt = time(nullptr);
    auto it = std::find_if(
        batch.changes.begin(), batch.changes.end(),
        [memberGuid](PendingGuildRankChange const& change)
        {
            return change.memberGuid == memberGuid;
        });
    if (it == batch.changes.end())
    {
        batch.changes.push_back(
            {memberGuid, oldRank, newRank, actorGuid});
        return;
    }
    it->currentRank = newRank;
    it->actorGuid = actorGuid;
}

void NoteGuildMotdChanged(
    uint32 guildId, std::string const& motd)
{
    if (!GuildMemberEventsAllowed()
        || !sLLMChatterConfig->_guildMotdCommentEnable)
    {
        return;
    }

    std::lock_guard<std::mutex> guard(sGuildEventMutex);
    PendingGuildMotd& pending = sPendingGuildMotds[guildId];
    pending.motd = motd;
    pending.dueAt = time(nullptr)
        + sLLMChatterConfig->_guildMotdCommentDelaySeconds;
}

bool JoinedGuildRecently(
    uint32 guildId, uint32 memberGuid, time_t now)
{
    uint32 graceMinutes = sLLMChatterConfig
        ->_guildRankChangeNewMemberGraceMinutes;
    if (!graceMinutes)
        return false;
    time_t graceSeconds =
        static_cast<time_t>(graceMinutes) * 60;

    {
        std::lock_guard<std::mutex> guard(sGuildEventMutex);
        auto it = sGuildJoinTimes.find(memberGuid);
        if (it != sGuildJoinTimes.end())
            return now - it->second < graceSeconds;
    }

    // Joins from before this server start are only in the event log.
    QueryResult result = CharacterDatabase.Query(
        "SELECT MAX(TimeStamp) FROM guild_eventlog "
        "WHERE guildid = {} AND EventType = {} "
        "AND PlayerGuid1 = {}",
        guildId,
        static_cast<uint32>(GUILD_EVENT_LOG_JOIN_GUILD),
        memberGuid);
    if (!result || result->Fetch()[0].IsNull())
        return false;
    time_t joinedAt = static_cast<time_t>(
        result->Fetch()[0].Get<uint32>());
    return now - joinedAt < graceSeconds;
}

Player* FindOnlineRealGuildMember(uint32 guildId)
{
    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    for (auto const& pair : sessions)
    {
        WorldSession* session = pair.second;
        if (!session || session->PlayerLoading())
            continue;
        Player* player = session->GetPlayer();
        if (player && player->IsInWorld()
            && !IsPlayerBot(player)
            && player->GetGuildId() == guildId)
        {
            return player;
        }
    }
    return nullptr;
}

std::string GuildMemberName(uint32 memberGuid)
{
    ObjectGuid guid =
        ObjectGuid::Create<HighGuid::Player>(memberGuid);
    if (Player* player =
            ObjectAccessor::FindConnectedPlayer(guid))
        return player->GetName();
    std::string name;
    sCharacterCache->GetCharacterNameByGuid(guid, name);
    return name;
}

std::string BuildGuildMemberJson(uint32 memberGuid)
{
    std::string name = GuildMemberName(memberGuid);
    if (name.empty())
        return "";
    Player* member = ObjectAccessor::FindConnectedPlayer(
        ObjectGuid::Create<HighGuid::Player>(memberGuid));
    bool online = member && member->IsInWorld();
    return fmt::format(
        R"("guid":{},"name":"{}","online":{},)"
        R"("is_bot":{},"zone_id":{},"map_id":{})",
        memberGuid,
        JsonEscape(name),
        online ? "true" : "false",
        (member && IsPlayerBot(member)) ? "true" : "false",
        online ? member->GetZoneId() : 0,
        online ? member->GetMapId() : 0);
}

std::vector<Player*> GetGuildEventCommenters(
    uint32 guildId,
    Player* anchor,
    std::vector<uint32> const& excludedGuids)
{
    uint32 maxCandidates =
        sLLMChatterConfig->_guildMemberEventMaxCandidates;
    std::vector<Player*> bots = GetGuildEventBots(
        guildId,
        anchor,
        maxCandidates + static_cast<uint32>(excludedGuids.size()));
    bots.erase(
        std::remove_if(
            bots.begin(), bots.end(),
            [&excludedGuids](Player* bot)
            {
                return std::find(
                    excludedGuids.begin(),
                    excludedGuids.end(),
                    bot->GetGUID().GetCounter())
                    != excludedGuids.end();
            }),
        bots.end());
    if (bots.size() > maxCandidates)
        bots.resize(maxCandidates);
    return bots;
}

// No player spoke, so the queued event neither refreshes the guild's
// player-interaction timer nor counts as a reply when delivered.
void QueueGuildMemberEvent(
    char const* eventType,
    Guild* guild,
    Player* anchor,
    std::vector<Player*> const& bots,
    std::string const& payloadFields,
    uint32 subjectGuid,
    std::string const& subjectName)
{
    std::string extraData = fmt::format(
        R"({{"guild_id":{},"guild_name":"{}",)"
        R"("team":"{}",{},"candidates":{}}})",
        guild->GetId(),
        JsonEscape(guild->GetName()),
        anchor->GetTeamId() == TEAM_ALLIANCE
            ? "Alliance" : "Horde",
        payloadFields,
        BuildGuildEventCandidatesJson(bots));

    QueueChatterEvent(
        eventType,
        "player",
        anchor->GetZoneId(),
        anchor->GetMapId(),
        GetChatterEventPriority(eventType),
        "",
        subjectGuid,
        subjectName,
        0, "", 0,
        EscapeString(extraData),
        0,
        120,
        false);

    LOG_DEBUG(
        "module",
        "LLMChatter: queued {} guild={} anchor={} "
        "candidates={}",
        eventType,
        guild->GetId(),
        anchor->GetName(),
        bots.size());
}

void FlushGuildJoinBatch(
    uint32 guildId, std::vector<uint32> const& memberGuids)
{
    if (!sLLMChatterConfig->_guildJoinGreetingEnable
        || urand(1, 100)
            > sLLMChatterConfig->_guildJoinGreetingChance)
        return;

    Guild* guild = sGuildMgr->GetGuildById(guildId);
    Player* anchor = FindOnlineRealGuildMember(guildId);
    if (!guild || !anchor)
        return;

    std::string members;
    std::vector<uint32> present;
    for (uint32 memberGuid : memberGuids)
    {
        if (!guild->GetMember(
                ObjectGuid::Create<HighGuid::Player>(
                    memberGuid)))
            continue;
        std::string member = BuildGuildMemberJson(memberGuid);
        if (member.empty())
            continue;
        members += (members.empty() ? "{" : ",{")
            + member + "}";
        present.push_back(memberGuid);
    }
    if (present.empty())
        return;

    std::vector<Player*> bots =
        GetGuildEventCommenters(guildId, anchor, present);
    if (bots.empty())
        return;

    QueueGuildMemberEvent(
        "guild_member_join",
        guild,
        anchor,
        bots,
        fmt::format(R"("members":[{}])", members),
        present.front(),
        GuildMemberName(present.front()));
}

void FlushGuildRankBatch(
    uint32 guildId,
    std::vector<PendingGuildRankChange> const& changes)
{
    if (!sLLMChatterConfig->_guildRankChangeEnable
        || urand(1, 100)
            > sLLMChatterConfig->_guildRankChangeChance)
        return;

    Guild* guild = sGuildMgr->GetGuildById(guildId);
    Player* anchor = FindOnlineRealGuildMember(guildId);
    if (!guild || !anchor)
        return;

    time_t now = time(nullptr);
    std::string entries;
    std::vector<uint32> subjects;
    for (PendingGuildRankChange const& change : changes)
    {
        if (change.currentRank == change.originalRank)
            continue;
        auto const* member = guild->GetMember(
            ObjectGuid::Create<HighGuid::Player>(
                change.memberGuid));
        if (!member
            || member->GetRankId() != change.currentRank)
            continue;
        if (JoinedGuildRecently(
                guildId, change.memberGuid, now))
            continue;
        std::string memberJson =
            BuildGuildMemberJson(change.memberGuid);
        if (memberJson.empty())
            continue;
        entries += fmt::format(
            R"({}{{{},"old_rank":{},"new_rank":{},)"
            R"("direction":"{}","actor_guid":{},)"
            R"("actor_name":"{}"}})",
            entries.empty() ? "" : ",",
            memberJson,
            change.originalRank,
            change.currentRank,
            change.currentRank < change.originalRank
                ? "promotion" : "demotion",
            change.actorGuid,
            JsonEscape(GuildMemberName(change.actorGuid)));
        subjects.push_back(change.memberGuid);
    }
    if (subjects.empty())
        return;

    std::vector<Player*> bots =
        GetGuildEventCommenters(guildId, anchor, subjects);
    if (bots.empty())
        return;

    QueueGuildMemberEvent(
        "guild_rank_change",
        guild,
        anchor,
        bots,
        fmt::format(R"("changes":[{}])", entries),
        subjects.front(),
        GuildMemberName(subjects.front()));
}

void FlushGuildMotd(uint32 guildId, std::string const& motd)
{
    if (motd.empty()
        || !sLLMChatterConfig->_guildMotdCommentEnable
        || urand(1, 100)
            > sLLMChatterConfig->_guildMotdCommentChance)
        return;

    Guild* guild = sGuildMgr->GetGuildById(guildId);
    Player* anchor = FindOnlineRealGuildMember(guildId);
    if (!guild || !anchor || guild->GetMOTD() != motd)
        return;

    std::vector<Player*> bots =
        GetGuildEventCommenters(guildId, anchor, {});
    if (bots.empty())
        return;

    QueueGuildMemberEvent(
        "guild_motd_comment",
        guild,
        anchor,
        bots,
        fmt::format(
            R"("motd":"{}")",
            JsonEscape(NormalizeChatTextForDb(
                motd,
                sLLMChatterConfig->_maxMessageLength))),
        0,
        "");
}

void StartPendingGuildSessions(
    std::vector<uint32> const& memberGuids)
{
    bool sessionsWanted =
        sLLMChatterConfig->_guildPlayerRepliesEnable
        || (sLLMChatterConfig->_useEventSystem
            && sLLMChatterConfig->_guildLoginGreetingEnable);
    if (!sessionsWanted)
        return;

    for (uint32 memberGuid : memberGuids)
    {
        Player* player = ObjectAccessor::FindConnectedPlayer(
            ObjectGuid::Create<HighGuid::Player>(memberGuid));
        if (player && player->IsInWorld()
            && !IsPlayerBot(player)
            && player->GetGuildId())
        {
            EnsureGuildSessionForPlayer(player);
        }
    }
}

void ProcessPendingGuildMemberEvents()
{
    static time_t lastUpdate = 0;
    time_t now = time(nullptr);
    if (now == lastUpdate)
        return;
    lastUpdate = now;

    std::vector<uint32> sessionStarts;
    std::vector<std::pair<uint32, std::vector<uint32>>> joins;
    std::vector<std::pair<uint32,
        std::vector<PendingGuildRankChange>>> rankChanges;
    std::vector<std::pair<uint32, std::string>> motds;
    bool allowed = GuildMemberEventsAllowed();
    {
        std::lock_guard<std::mutex> guard(sGuildEventMutex);
        sessionStarts.swap(sPendingGuildSessionStarts);

        time_t graceSeconds = static_cast<time_t>(
            sLLMChatterConfig
                ? sLLMChatterConfig
                      ->_guildRankChangeNewMemberGraceMinutes
                : 0) * 60;
        for (auto it = sGuildJoinTimes.begin();
             it != sGuildJoinTimes.end();)
        {
            if (now - it->second >= graceSeconds)
                it = sGuildJoinTimes.erase(it);
            else
                ++it;
        }

        if (!allowed)
        {
            sPendingGuildJoins.clear();
            sPendingGuildRankChanges.clear();
            sPendingGuildMotds.clear();
        }

        for (auto it = sPendingGuildJoins.begin();
             it != sPendingGuildJoins.end();)
        {
            if (now < it->second.dueAt)
            {
                ++it;
                continue;
            }
            joins.emplace_back(
                it->first, std::move(it->second.memberGuids));
            it = sPendingGuildJoins.erase(it);
        }

        uint32 debounce = sLLMChatterConfig
            ? sLLMChatterConfig->_guildRankChangeDebounceSeconds
            : 30;
        for (auto it = sPendingGuildRankChanges.begin();
             it != sPendingGuildRankChanges.end();)
        {
            if (now - it->second.lastChangeAt
                < static_cast<time_t>(debounce))
            {
                ++it;
                continue;
            }
            rankChanges.emplace_back(
                it->first, std::move(it->second.changes));
            it = sPendingGuildRankChanges.erase(it);
        }

        for (auto it = sPendingGuildMotds.begin();
             it != sPendingGuildMotds.end();)
        {
            if (now < it->second.dueAt)
            {
                ++it;
                continue;
            }
            motds.emplace_back(
                it->first, std::move(it->second.motd));
            it = sPendingGuildMotds.erase(it);
        }
    }

    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_guildChatterEnable)
        return;

    StartPendingGuildSessions(sessionStarts);
    for (auto const& [guildId, members] : joins)
        FlushGuildJoinBatch(guildId, members);
    for (auto const& [guildId, changes] : rankChanges)
        FlushGuildRankBatch(guildId, changes);
    for (auto const& [guildId, motd] : motds)
        FlushGuildMotd(guildId, motd);
}

class LLMChatterGuildMemberEventScript : public GuildScript
{
public:
    LLMChatterGuildMemberEventScript()
        : GuildScript(
              "LLMChatterGuildMemberEventScript",
              {GUILDHOOK_ON_MOTD_CHANGED,
               GUILDHOOK_ON_EVENT})
    {
    }

    void OnMOTDChanged(
        Guild* guild, std::string const& newMotd) override
    {
        if (guild)
            NoteGuildMotdChanged(guild->GetId(), newMotd);
    }

    // GM rank commands (.guild rank) change ranks without logging an
    // event, so only in-game promote and demote reach this hook.
    void OnEvent(
        Guild* guild,
        uint8 eventType,
        ObjectGuid::LowType playerGuid1,
        ObjectGuid::LowType playerGuid2,
        uint8 newRank) override
    {
        if (!guild)
            return;

        switch (eventType)
        {
            case GUILD_EVENT_LOG_JOIN_GUILD:
                NoteGuildMemberJoined(
                    guild->GetId(), playerGuid1);
                break;
            case GUILD_EVENT_LOG_PROMOTE_PLAYER:
            case GUILD_EVENT_LOG_DEMOTE_PLAYER:
                NoteGuildRankChanged(
                    guild->GetId(),
                    playerGuid1,
                    playerGuid2,
                    newRank,
                    eventType
                        == GUILD_EVENT_LOG_PROMOTE_PLAYER);
                break;
            default:
                break;
        }
    }
};

class LLMChatterGuildMemberWorldScript : public WorldScript
{
public:
    LLMChatterGuildMemberWorldScript()
        : WorldScript(
              "LLMChatterGuildMemberWorldScript",
              {WORLDHOOK_ON_UPDATE})
    {
    }

    void OnUpdate(uint32 /*diff*/) override
    {
        ProcessPendingGuildMemberEvents();
    }
};
}

void AddLLMChatterGuildMemberScripts()
{
    new LLMChatterGuildMemberEventScript();
    new LLMChatterGuildMemberWorldScript();
}
