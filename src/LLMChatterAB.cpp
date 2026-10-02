/* mod-llm-chatter - Arathi Basin observation and value snapshots */
#include "LLMChatterAB.h"
#include "LLMChatterABActor.h"
#include "LLMChatterABPending.h"
#include "LLMChatterABScore.h"
#include "LLMChatterBG.h"
#include "LLMChatterShared.h"
#include "Group.h"
#include "Player.h"
#include "Playerbots.h"
#include "ObjectAccessor.h"
#include "Random.h"
#include "Transaction.h"
#include "DatabaseEnv.h"
#include "LLMChatterConfig.h"
#include "LLMChatterJsonFields.h"
#include "Battleground.h"
#include "BattlegroundAB.h"
#include "Timer.h"
#include "GameObject.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "ScriptMgr.h"
#include "WorldStatePackets.h"
#include "WorldStateDefines.h"

#include <algorithm>
#include <cmath>
#include <array>
#include <mutex>
#include <memory>
#include <unordered_map>
#include <utility>

static char const* AB_NODE_NAMES[] = {
    "Stables", "Blacksmith", "Farm", "Lumber Mill", "Gold Mine"
};

struct ABNodeObservation
{
    bool initialized = false;
    bool captured = false;
    uint8 pendingChanges = 0;
    char const* transition = "state_update";
    uint8 state = BG_AB_NODE_STATE_NEUTRAL;
    uint8 prevState = BG_AB_NODE_STATE_NEUTRAL;
    uint32 observationGapMs = 0;
    uint64 revision = 0;
    bool estimateValid = false;
    uint64 contestObservedMs = 0;
    uint32 contestFirstAdvanceMs = 0;
    // Verified actor for the current pending revision (none if 0).
    uint8 actorKind = LLMChatterAB::ACTOR_NONE;
    LLMChatterAB::ActorRecord actor;
    LLMChatterAB::ActorCarry carry;
};

struct ABTracker
{
    std::array<ABNodeObservation, BG_AB_DYNAMIC_NODES_COUNT> abNodes{};
    LLMChatterAB::PendingNodes pending;
    std::vector<TransactionCallback> insertions;
    LLMChatterAB::ScoreTracker score;
    std::unique_ptr<TransactionCallback> scoreInsertion;
    LLMChatterAB::ObjectiveStatusClock objectiveStatus;
    uint64 recentNodeUntil = 0;
    uint32 abLastObservationMs = 0;
    uint64 elapsedMs = 0;
    bool inProgress = false;
    uint32 maxScore = BG_AB_MAX_TEAM_SCORE;
    uint32 warningScore = BG_AB_WARNING_NEAR_VICTORY_SCORE;
    bool maxScoreVerified = false;
};

// Observation and pending state are only touched on the world thread.
static std::unordered_map<uint32, ABTracker> _abTrackers;
// Map/player hooks only copy this immutable serialized value.
static std::mutex _abSnapshotsMutex;
static std::unordered_map<uint32, std::string> _abSnapshots;
// Verified banner clicks, written on BG map threads and consumed by the
// world-thread observer. Values only; no game object is retained.
static std::mutex _abActorMutex;
static std::unordered_map<uint32,
    std::array<LLMChatterAB::NodeEvidence, BG_AB_DYNAMIC_NODES_COUNT>>
    _abActorEvidence;

static char const* ClassifyABTransition(
    uint8 previous, uint8 current, bool wasCaptured, bool captured)
{
    bool contested = current == BG_AB_NODE_STATE_ALLY_CONTESTED
        || current == BG_AB_NODE_STATE_HORDE_CONTESTED;
    bool wasContested = previous == BG_AB_NODE_STATE_ALLY_CONTESTED
        || previous == BG_AB_NODE_STATE_HORDE_CONTESTED;
    if (contested && previous == BG_AB_NODE_STATE_NEUTRAL && !captured)
        return "claim";
    if (contested && (previous == BG_AB_NODE_STATE_ALLY_OCCUPIED
        || previous == BG_AB_NODE_STATE_HORDE_OCCUPIED)
        && current != previous + 2 && wasCaptured && captured)
        return "assault";
    if (contested && wasContested && previous != current
        && !wasCaptured && !captured)
        return "counter_claim";
    if (wasContested && (current == BG_AB_NODE_STATE_ALLY_OCCUPIED
        || current == BG_AB_NODE_STATE_HORDE_OCCUPIED) && captured)
    {
        if (previous == current + 2)
            return "capture";
        if (wasCaptured)
            return "defence";
    }
    return "state_update";
}

// World map updates precede BG updates; this hook follows AB PostUpdateImpl.
// Battleground::Update gates to 1000ms and advances timers by exactly that
// amount. Between observations, banner actions can alternate, but a reset
// 60s capture timer cannot expire in that single BG pass. Thus recognized
// pairs support net team transitions, not an exhaustive action/actor log.
// Wall-clock gaps and multiple pending changes still degrade to state-only.
static void ObserveNodes(
    Battleground* bg, ABTracker& tracker, uint32 diff)
{
    BattlegroundAB* ab = bg->ToBattlegroundAB();
    if (!ab)
        return;

    tracker.elapsedMs += diff;
    uint32 now = getMSTime();
    uint32 gap = getMSTimeDiff(tracker.abLastObservationMs, now);
    tracker.abLastObservationMs = now;
    // Verified clicks since the last observation, consumed exactly once.
    std::array<LLMChatterAB::NodeEvidence, BG_AB_DYNAMIC_NODES_COUNT> clicks{};
    {
        std::lock_guard<std::mutex> lock(_abActorMutex);
        auto it = _abActorEvidence.find(bg->GetInstanceID());
        if (it != _abActorEvidence.end())
        {
            clicks = it->second;
            it->second = {};
        }
    }
    for (uint8 i = 0; i < BG_AB_DYNAMIC_NODES_COUNT; ++i)
    {
        auto& node = tracker.abNodes[i];
        auto& pending = tracker.pending.nodes[i];
        auto const& info = ab->GetCapturePointInfo(i);
        uint8 state = info._state;
        if (state > BG_AB_NODE_STATE_HORDE_CONTESTED)
        {
            uint64 revision = node.revision + 1;
            node = {};
            pending = {};
            node.revision = revision;
            continue;
        }
        if (!node.initialized)
        {
            // Late enable/entry and invalid samples seed silently.
            if (!node.revision || node.state != state
                || node.captured != info._captured)
                ++node.revision;
            node.carry = {};
            node.actorKind = LLMChatterAB::ACTOR_NONE;
            node.state = state;
            node.captured = info._captured;
            node.initialized = true;
            continue;
        }
        uint32 maxGap = sLLMChatterConfig->_bgABTransitionMaxGapMs;
        bool gapOk = maxGap && gap <= maxGap;
        if (!maxGap || gap > maxGap)
            node.estimateValid = false;
        if (state == node.state)
        {
            LLMChatterAB::ActorRecord unused;
            LLMChatterAB::ResolveActor(node.carry, clicks[i], false,
                node.transition, node.state, state, gapOk, unused);
            // Verified clicks that left the sampled state unchanged (e.g. a
            // counter-claim and re-claim) rewrote this contest: advance the
            // revision so queued lines naming the earlier actor are rejected
            // at send, and drop that actor from any pending fact. A quiet
            // observation (no clicks, same captured bit) changes nothing.
            if (LLMChatterAB::InvalidatesRevision(
                    node.captured != info._captured, clicks[i].count))
            {
                ++node.revision;
                node.actorKind = LLMChatterAB::ACTOR_NONE;
                if (clicks[i].count)
                    node.transition = "state_update";
                tracker.pending.Record(i, node.state, node.captured, state,
                    info._captured, node.revision, GetTimeMS().count());
                node.estimateValid = false;
            }
            node.captured = info._captured;
            if (pending.active)
            {
                node.observationGapMs = std::max(node.observationGapMs, gap);
                if (!maxGap || gap > maxGap)
                {
                    node.transition = "state_update";
                    node.estimateValid = false;
                    node.actorKind = LLMChatterAB::ACTOR_NONE;
                }
            }
            continue;
        }

        if (!pending.active)
        {
            node.prevState = node.state;
            node.pendingChanges = 1;
            node.observationGapMs = gap;
            node.transition = ClassifyABTransition(
                node.state, state, node.captured, info._captured);
        }
        else
        {
            // Retain the window's first previous state and latest result.
            node.pendingChanges = 2; // saturated: more than one change
            node.observationGapMs = std::max(node.observationGapMs, gap);
        }
        if (!maxGap || gap > maxGap || node.pendingChanges > 1)
            node.transition = "state_update";
        // Only a verified click (or the verified contest it started) names
        // an actor; everything else publishes no name.
        node.actorKind = LLMChatterAB::ResolveActor(node.carry, clicks[i],
            true, node.transition, node.state, state, gapOk, node.actor);
        ++node.revision;
        node.estimateValid = state >= BG_AB_NODE_STATE_ALLY_CONTESTED
            && std::string(node.transition) != "state_update";
        node.contestObservedMs = tracker.elapsedMs;
        node.contestFirstAdvanceMs = diff;
        tracker.pending.Record(i, node.state, node.captured, state,
            info._captured, node.revision, GetTimeMS().count());
        node.state = state;
        node.captured = info._captured;
    }
}

static std::string ActorJson(ABNodeObservation const& node)
{
    if (node.actorKind == LLMChatterAB::ACTOR_NONE || node.actor.name.empty())
        return {};
    return ",\"actor_name\":\"" + JsonEscape(node.actor.name) + "\","
        "\"actor_is_real_player\":"
        + std::string(node.actor.isReal ? "true" : "false") + ","
        "\"actor_role\":\"" + LLMChatterAB::ActorRole(node.actorKind) + "\"";
}

static std::string NodeJson(uint8 i, ABNodeObservation const& node)
{
    std::string owner = "Neutral";
    if (node.state == BG_AB_NODE_STATE_ALLY_OCCUPIED
        || node.state == BG_AB_NODE_STATE_ALLY_CONTESTED)
        owner = "Alliance";
    else if (node.state == BG_AB_NODE_STATE_HORDE_OCCUPIED
        || node.state == BG_AB_NODE_STATE_HORDE_CONTESTED)
        owner = "Horde";
    bool sampled = std::string(node.transition) != "state_update";
    return "{\"node_name\":\"" + std::string(AB_NODE_NAMES[i]) + "\","
        "\"node_id\":" + std::to_string(i) + ","
        "\"node_revision\":" + std::to_string(node.revision) + ","
        "\"new_owner\":\"" + owner + "\","
        "\"prev_state\":" + std::to_string(node.prevState) + ","
        "\"state\":" + std::to_string(node.state) + ","
        "\"transition\":\"" + node.transition + "\","
        "\"evidence\":\"" + (sampled ? "sampled" : "ambiguous") + "\","
        "\"observation_gap_ms\":" + std::to_string(node.observationGapMs)
        + ActorJson(node) + "}";
}

static std::map<LLMChatterAB::Audience, Player*> ABListeners(
    Battleground* bg, bool subgroupOnly = true)
{
    std::map<LLMChatterAB::Audience, Player*> listeners;
    for (auto const& [guid, unused] : bg->GetPlayers())
    {
        Player* player = ObjectAccessor::FindPlayer(guid);
        if (!player || !player->IsInWorld() || IsPlayerBot(player)
            || player->GetBattleground() != bg)
            continue;
        Group* group = player->GetGroup();
        if (!group)
            continue;
        uint8 subgroup = group->GetMemberGroup(player->GetGUID());
        bool audibleBot = false;
        for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
        {
            Player* bot = ref->GetSource();
            if (bot && bot->IsInWorld() && IsPlayerBot(bot)
                && bot->GetBattleground() == bg && bot->GetMap() == player->GetMap()
                && bot->GetBgTeamId() == player->GetBgTeamId()
                && (!subgroupOnly
                    || group->GetMemberGroup(bot->GetGUID()) == subgroup))
            {
                audibleBot = true;
                break;
            }
        }
        if (!audibleBot)
            continue;
        uint64 key = (uint64(player->GetBgTeamId()) << 40)
            | (uint64(group->GetGUID().GetCounter()) << 8)
            | (subgroupOnly ? subgroup : 0);
        listeners.emplace(key, player);
    }
    return listeners;
}

void QueueABNodeBatch(Battleground* bg)
{
    auto it = _abTrackers.find(bg->GetInstanceID());
    if (it == _abTrackers.end() || !sLLMChatterConfig->_bgABEnable
        || bg->GetStatus() != STATUS_IN_PROGRESS)
        return;
    auto& tracker = it->second;
    // An unacknowledged DB operation must not create another copy on retry.
    // At most one batch of per-audience transactions is outstanding per match.
    if (!tracker.insertions.empty())
        return;
    auto selected = tracker.pending.Select(GetTimeMS().count(),
        uint64(sLLMChatterConfig->_bgABNodeBatchCooldownSec) * 1000,
        sLLMChatterConfig->_bgABMaxNodesPerBatch);
    if (selected.empty() || urand(1, 100) > sLLMChatterConfig->_bgNodeEventChance)
        return;

    // Node reactions are BG-wide: humans in different subgroups of the
    // same raid must not produce duplicate broadcasts of the same revision.
    auto listeners = ABListeners(bg, false);
    std::vector<LLMChatterAB::Audience> audiences;
    for (auto const& [key, player] : listeners)
        audiences.push_back(key);
    tracker.pending.SetAudiences(selected, audiences);
    for (auto const& [audience, player] : listeners)
    {
        auto items = tracker.pending.ForAudience(selected, audience);
        if (items.empty())
            continue;
        std::string json = "{\"node_changes\":[";
        for (auto item : items)
        {
            if (json.back() != '[')
                json += ",";
            json += NodeJson(item.node, tracker.abNodes[item.node]);
        }
        json += "]}";
        AppendBGContext(bg, player, json);
        AppendABContext(bg->GetInstanceID(), json);
        auto trans = CharacterDatabase.BeginTransaction();
        // The transport name does not label every item as captured. Each
        // item carries its own observed transition, including contested ones.
        std::string const event = "bg_node_captured";
        AppendChatterEvent(trans, event, "player", player->GetZoneId(),
            player->GetMapId(), GetChatterEventPriority(event), "",
            player->GetGUID().GetCounter(), player->GetName(), 0, "", 0,
            EscapeString(json), GetReactionDelaySeconds(event), 120, true);
        auto callback = CharacterDatabase.AsyncCommitTransaction(trans);
        // Owned and polled by this tracker on the world thread. Destroy/reset
        // drops callbacks; no live game object or cross-lifetime reference.
        callback.AfterComplete([&tracker, audience, items](bool success)
        {
            tracker.pending.Acknowledge(audience, items, success);
        });
        tracker.insertions.push_back(std::move(callback));
        tracker.recentNodeUntil = GetTimeMS().count()
            + uint64(sLLMChatterConfig->_bgABNodeBatchCooldownSec) * 1000;
    }
}

void QueueABScoreMilestone(Battleground* bg)
{
    auto it = _abTrackers.find(bg->GetInstanceID());
    if (it == _abTrackers.end() || !sLLMChatterConfig->_bgABEnable
        || bg->GetStatus() != STATUS_IN_PROGRESS)
        return;
    auto& tracker = it->second;
    if (!tracker.maxScoreVerified || tracker.scoreInsertion
        || !tracker.score.TakeAttempt(GetTimeMS().count(),
            uint64(sLLMChatterConfig->_bgABScoreCooldownSec) * 1000,
            uint64(sLLMChatterConfig->_bgABPendingMaxAgeSec) * 1000)
        || urand(1, 100) > std::min<uint32>(100,
            sLLMChatterConfig->_bgScoreMilestoneChance))
        return;
    auto listeners = ABListeners(bg);
    if (listeners.empty())
        return;
    auto pending = tracker.score.pending;
    auto trans = CharacterDatabase.BeginTransaction();
    std::string const event = "bg_score_milestone";
    for (auto const& [audience, player] : listeners)
    {
        std::string json = "{\"milestone_team\":\""
            + std::string(pending.team == TEAM_ALLIANCE ? "Alliance" : "Horde")
            + "\",\"milestone_value\":" + std::to_string(pending.threshold)
            + ",\"milestone_kind\":\""
            + (pending.warning ? "core_warning" : "percentage") + "\"}";
        AppendBGContext(bg, player, json);
        AppendABContext(bg->GetInstanceID(), json);
        AppendChatterEvent(trans, event, "player", player->GetZoneId(),
            player->GetMapId(), GetChatterEventPriority(event), "",
            player->GetGUID().GetCounter(), player->GetName(), 0, "", 0,
            EscapeString(json), GetReactionDelaySeconds(event), 120, true);
    }
    // Atomic cohort insertion: either all audience rows commit or none do.
    // Score acknowledgements never delay the independent node insertion path.
    auto callback = CharacterDatabase.AsyncCommitTransaction(trans);
    callback.AfterComplete([&tracker, revision = pending.revision](bool success)
    {
        tracker.score.Acknowledge(revision, success);
    });
    tracker.scoreInsertion = std::make_unique<TransactionCallback>(std::move(callback));
}

bool TryABObjectiveStatus(Battleground* bg)
{
    auto it = _abTrackers.find(bg->GetInstanceID());
    if (it == _abTrackers.end() || !sLLMChatterConfig->_bgABEnable
        || bg->GetStatus() != STATUS_IN_PROGRESS)
        return false;
    auto& tracker = it->second;
    bool pending = !tracker.insertions.empty()
        || std::any_of(tracker.pending.nodes.begin(), tracker.pending.nodes.end(),
            [](auto const& node) { return node.active; });
    return tracker.objectiveStatus.TakeOpportunity(GetTimeMS().count(),
        uint64(sLLMChatterConfig->_bgABObjectiveStatusIntervalSec) * 1000,
        pending, tracker.recentNodeUntil)
        && urand(1, 100) <= sLLMChatterConfig->_bgABObjectiveStatusChance;
}

static void ReadMatchTarget(BattlegroundAB* ab, ABTracker& tracker)
{
    if (tracker.maxScoreVerified)
        return;
    WorldPackets::WorldState::InitWorldStates packet;
    ab->FillInitialWorldStates(packet);
    uint32 maximum = 0;
    for (auto const& entry : packet.Worldstates)
    {
        if (entry.VariableID == WORLD_STATE_BATTLEGROUND_AB_RESOURCES_MAX
            && entry.Value > 0)
            maximum = static_cast<uint32>(entry.Value);
        if (entry.VariableID == WORLD_STATE_BATTLEGROUND_AB_RESOURCES_WARNING
            && entry.Value > 0)
            tracker.warningScore = static_cast<uint32>(entry.Value);
    }
    if (maximum)
    {
        tracker.maxScore = maximum;
        tracker.maxScoreVerified = true;
    }
    // Failed/invalid reads retain a marked fallback and retry next update.
}

static std::string BuildSnapshot(ABTracker const& tracker)
{
    std::array<uint8, 2> occupied{};
    std::string nodes = "[";
    for (uint8 i = 0; i < BG_AB_DYNAMIC_NODES_COUNT; ++i)
    {
        auto const& node = tracker.abNodes[i];
        if (!node.initialized)
            return {}; // Do not publish a partial five-node picture.
        if (i)
            nodes += ",";
        std::string owner = "null";
        std::string claimant = "null";
        if (node.state == BG_AB_NODE_STATE_ALLY_OCCUPIED)
        {
            owner = "\"Alliance\"";
            ++occupied[TEAM_ALLIANCE];
        }
        else if (node.state == BG_AB_NODE_STATE_HORDE_OCCUPIED)
        {
            owner = "\"Horde\"";
            ++occupied[TEAM_HORDE];
        }
        else if (node.state == BG_AB_NODE_STATE_ALLY_CONTESTED)
            claimant = "\"Alliance\"";
        else if (node.state == BG_AB_NODE_STATE_HORDE_CONTESTED)
            claimant = "\"Horde\"";

        nodes += "{\"id\":" + std::to_string(i)
            + ",\"name\":\"" + AB_NODE_NAMES[i] + "\",\"state\":"
            + std::to_string(node.state) + ",\"owner\":" + owner
            + ",\"claimant\":" + claimant + ",\"captured\":"
            + (node.captured ? "true" : "false") + ",\"revision\":"
            + std::to_string(node.revision);

        // Internal bounds use the BG event clock, not a wall-clock ETA.
        // A hidden same-state re-claim may reset the timer, so the upper
        // bound stays at the full duration. The widening interval quickly
        // becomes unusable; never present it as an exact countdown.
        uint64 duration = BG_AB_FLAG_CAPTURING_TIME.count();
        uint64 elapsed = tracker.elapsedMs - node.contestObservedMs
            + node.contestFirstAdvanceMs;
        uint64 uncertainty = uint64(sLLMChatterConfig
            ->_bgABTimerEstimateMaxUncertaintySec) * 1000;
        if (node.estimateValid && uncertainty && elapsed < duration
            && elapsed <= uncertainty)
        {
            nodes += ",\"contest_estimate\":{\"basis\":\"bg_update_time\","
                "\"remaining_min_ms\":" + std::to_string(duration - elapsed)
                + ",\"remaining_max_ms\":" + std::to_string(duration) + "}";
        }
        nodes += "}";
    }
    nodes += "]";
    auto income = [](uint8 count)
    {
        return "{\"points\":" + std::to_string(BG_AB_TickPoints[count])
            + ",\"interval_ms\":"
            + std::to_string(BG_AB_TickIntervals[count].count()) + "}";
    };
    return "{\"observed_at_ms\":" + std::to_string(GetTimeMS().count())
        + ",\"nodes\":" + nodes + ",\"occupied_alliance\":"
        + std::to_string(occupied[TEAM_ALLIANCE]) + ",\"occupied_horde\":"
        + std::to_string(occupied[TEAM_HORDE]) + ",\"income_alliance\":"
        + income(occupied[TEAM_ALLIANCE]) + ",\"income_horde\":"
        + income(occupied[TEAM_HORDE]) + ",\"max_score\":"
        + std::to_string(tracker.maxScore) + ",\"max_score_verified\":"
        + (tracker.maxScoreVerified ? "true" : "false")
        + ",\"warning_score\":" + std::to_string(tracker.warningScore) + "}";
}

void ObserveABContext(Battleground* bg, uint32 diff)
{
    BattlegroundAB* ab = bg->ToBattlegroundAB();
    if (!ab)
        return;
    uint32 id = bg->GetInstanceID();
    if (!sLLMChatterConfig->_bgABEnable)
    {
        ResetABContext(id);
        return;
    }
    auto& tracker = _abTrackers[id];
    bool inProgress = bg->GetStatus() == STATUS_IN_PROGRESS;
    if (tracker.inProgress != inProgress)
    {
        tracker.pending = {};
        tracker.insertions.clear();
        tracker.score = {};
        tracker.scoreInsertion.reset();
        tracker.recentNodeUntil = 0;
        tracker.objectiveStatus.nextMs = GetTimeMS().count()
            + uint64(sLLMChatterConfig->_bgABObjectiveStatusIntervalSec) * 1000;
        for (auto& node : tracker.abNodes)
        {
            node.initialized = false;
            node.estimateValid = false;
        }
    }
    tracker.inProgress = inProgress;
    for (auto it = tracker.insertions.begin(); it != tracker.insertions.end();)
        if (it->InvokeIfReady())
            it = tracker.insertions.erase(it);
        else
            ++it;
    tracker.pending.Expire(GetTimeMS().count(),
        uint64(sLLMChatterConfig->_bgABPendingMaxAgeSec) * 1000);
    if (tracker.scoreInsertion && tracker.scoreInsertion->InvokeIfReady())
        tracker.scoreInsertion.reset();
    ReadMatchTarget(ab, tracker);
    if (inProgress && tracker.maxScoreVerified)
        tracker.score.Observe(tracker.maxScore, tracker.warningScore,
            sLLMChatterConfig->_bgABScoreMilestonePercents,
            {bg->GetTeamScore(TEAM_ALLIANCE), bg->GetTeamScore(TEAM_HORDE)},
            GetTimeMS().count());
    ObserveNodes(bg, tracker, diff);
    if (!inProgress)
    {
        tracker.pending = {};
        for (auto& node : tracker.abNodes)
            node.estimateValid = false;
    }
    std::string snapshot = BuildSnapshot(tracker);
    std::lock_guard<std::mutex> lock(_abSnapshotsMutex);
    if (snapshot.empty())
        _abSnapshots.erase(id);
    else
        _abSnapshots[id] = std::move(snapshot);
}

void ResetABContext(uint32 instanceId)
{
    _abTrackers.erase(instanceId);
    {
        std::lock_guard<std::mutex> lock(_abActorMutex);
        _abActorEvidence.erase(instanceId);
    }
    std::lock_guard<std::mutex> lock(_abSnapshotsMutex);
    _abSnapshots.erase(instanceId);
}

void AppendABContext(uint32 instanceId, std::string& json)
{
    if (!sLLMChatterConfig || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_bgChatterEnable
        || !sLLMChatterConfig->_bgABEnable)
        return;
    std::string snapshot;
    {
        std::lock_guard<std::mutex> lock(_abSnapshotsMutex);
        auto it = _abSnapshots.find(instanceId);
        if (it == _abSnapshots.end())
            return;
        snapshot = it->second;
    }
    if (!json.empty() && json.back() == '}')
    {
        json.pop_back();
        if (json.size() > 1)
            json += ",";
        json += "\"ab_state\":" + snapshot + "}";
    }
}

bool IsABNodeEventCurrent(Battleground* bg, std::string_view json)
{
    using namespace LLMChatterJson;
    Members root;
    BattlegroundAB* ab = bg->ToBattlegroundAB();
    auto tracker = _abTrackers.find(bg->GetInstanceID());
    if (!ab || tracker == _abTrackers.end() || !ReadObject(json, root))
        return false;
    uint32 seen = 0;
    auto validate = [&](Members const& fields)
    {
        uint64 id = 0, state = 0, revision = 0;
        std::string name;
        if (!UInt(fields, "node_id", id) || id >= BG_AB_DYNAMIC_NODES_COUNT
            || (seen & (1u << id)) || !UInt(fields, "state", state)
            || !UInt(fields, "node_revision", revision)
            || !String(fields, "node_name", name) || name != AB_NODE_NAMES[id])
            return false;
        seen |= 1u << id;
        auto const& cached = tracker->second.abNodes[id];
        auto const& live = ab->GetCapturePointInfo(static_cast<uint8>(id));
        return cached.initialized && cached.revision == revision
            && cached.state == state && live._state == state
            && cached.captured == live._captured;
    };
    auto batch = root.find("node_changes");
    if (batch == root.end())
        return validate(root); // legacy single-node contract
    std::vector<std::string_view> changes;
    if (!ReadArray(batch->second, changes) || changes.empty()
        || changes.size() > BG_AB_DYNAMIC_NODES_COUNT)
        return false;
    for (auto change : changes)
    {
        Members fields;
        if (!ReadObject(change, fields) || !validate(fields))
            return false;
    }
    return true;
}

bool IsABSnapshotCurrent(Battleground* bg, std::string_view snapshot,
    uint64 nowMs, uint32 maxAgeSec)
{
    using namespace LLMChatterJson;
    BattlegroundAB* ab = bg->ToBattlegroundAB();
    auto tracker = _abTrackers.find(bg->GetInstanceID());
    Members root;
    uint64 observed = 0;
    if (!ab || tracker == _abTrackers.end() || !ReadObject(snapshot, root)
        || !UInt(root, "observed_at_ms", observed) || observed > nowMs
        || nowMs - observed > uint64(maxAgeSec) * 1000)
        return false;
    auto nodesField = root.find("nodes");
    std::vector<std::string_view> nodes;
    if (nodesField == root.end() || !ReadArray(nodesField->second, nodes)
        || nodes.size() != BG_AB_DYNAMIC_NODES_COUNT)
        return false;
    uint32 seen = 0;
    std::array<uint32, 2> occupied{};
    for (auto node : nodes)
    {
        Members fields;
        uint64 id = 0, state = 0, revision = 0;
        if (!ReadObject(node, fields) || !UInt(fields, "id", id)
            || id >= BG_AB_DYNAMIC_NODES_COUNT || (seen & (1u << id))
            || !UInt(fields, "state", state) || !UInt(fields, "revision", revision))
            return false;
        seen |= 1u << id;
        auto const& live = ab->GetCapturePointInfo(static_cast<uint8>(id));
        auto const& cached = tracker->second.abNodes[id];
        if (!cached.initialized || cached.revision != revision
            || live._state != state || !fields.count("captured")
            || fields.at("captured") != (live._captured ? "true" : "false"))
            return false;
        std::string_view owner = "null", claimant = "null";
        if (state == BG_AB_NODE_STATE_ALLY_OCCUPIED)
        {
            owner = "\"Alliance\"";
            ++occupied[TEAM_ALLIANCE];
        }
        else if (state == BG_AB_NODE_STATE_HORDE_OCCUPIED)
        {
            owner = "\"Horde\"";
            ++occupied[TEAM_HORDE];
        }
        else if (state == BG_AB_NODE_STATE_ALLY_CONTESTED)
            claimant = "\"Alliance\"";
        else if (state == BG_AB_NODE_STATE_HORDE_CONTESTED)
            claimant = "\"Horde\"";
        if (!fields.count("owner") || !fields.count("claimant")
            || fields.at("owner") != owner || fields.at("claimant") != claimant)
            return false;
    }
    for (TeamId team : {TEAM_ALLIANCE, TEAM_HORDE})
    {
        char const* countKey = team == TEAM_ALLIANCE
            ? "occupied_alliance" : "occupied_horde";
        char const* incomeKey = team == TEAM_ALLIANCE
            ? "income_alliance" : "income_horde";
        uint64 count = 0, points = 0, interval = 0;
        Members rate;
        if (!UInt(root, countKey, count) || count != occupied[team]
            || !root.count(incomeKey) || !ReadObject(root.at(incomeKey), rate)
            || !UInt(rate, "points", points) || !UInt(rate, "interval_ms", interval)
            || points != BG_AB_TickPoints[count]
            || interval != uint64(BG_AB_TickIntervals[count].count()))
            return false;
    }
    if (!root.count("max_score_verified"))
        return false;
    if (root.at("max_score_verified") == "true")
    {
        uint64 maximum = 0;
        if (!tracker->second.maxScoreVerified || !UInt(root, "max_score", maximum)
            || maximum != tracker->second.maxScore)
            return false;
    }
    else if (root.at("max_score_verified") != "false")
        return false;
    return true;
}

// ---------------------------------------------------------------------------
// Verified banner interactions (map threads).
//
// OnPlayerSpellCast runs at cast completion, before CheckCast(false) and
// before effects (Spell::_cast). AllSpellScript::OnSpellCast runs after
// handle_immediate(), where the open-lock effect calls
// BattlegroundAB::EventPlayerClickedOnFlag. A cast rejected by CheckCast
// never reaches the post hook. Within one map update spells run
// sequentially, so a node change between this spell's pre and post
// snapshots is this caster's click.

static bool ABActorTrackingEnabled()
{
    return sLLMChatterConfig && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_bgChatterEnable
        && sLLMChatterConfig->_bgABEnable;
}

static thread_local LLMChatterAB::PreCastRing _abPreCasts;

static int ABBannerNode(GameObject const* go)
{
    if (!go)
        return -1;
    for (uint8 i = 0; i < BG_AB_DYNAMIC_NODES_COUNT; ++i)
        if (std::hypot(go->GetPositionX() - BG_AB_NodePositions[i][0],
                go->GetPositionY() - BG_AB_NodePositions[i][1]) < 10.0f)
            return i;
    return -1;
}

class LLMChatterABActorPlayerScript : public PlayerScript
{
public:
    LLMChatterABActorPlayerScript()
        : PlayerScript("LLMChatterABActorPlayerScript",
              {PLAYERHOOK_ON_SPELL_CAST}) { }

    void OnPlayerSpellCast(Player* player, Spell* spell, bool) override
    {
        if (!spell || !spell->GetSpellInfo()
            || spell->GetSpellInfo()->Id != LLMChatterAB::CAPTURE_BANNER_SPELL)
            return;
        // A CheckCast(false) rejection ends in finish(false) without a cancel
        // hook, so a reused Spell address may still own a stale slot. Clear
        // it before any eligibility exit: the post hook may only consume a
        // snapshot created by this invocation.
        _abPreCasts.Cancel(spell);
        if (!player || !ABActorTrackingEnabled())
            return;
        Battleground* bg = player->GetBattleground();
        if (!bg || bg->GetBgTypeID(true) != BATTLEGROUND_AB
            || bg->GetStatus() != STATUS_IN_PROGRESS)
            return;
        BattlegroundAB* ab = bg->ToBattlegroundAB();
        GameObject* go = spell->m_targets.GetGOTarget();
        int node = ABBannerNode(go);
        if (!ab || node < 0 || go->GetMap() != player->GetMap())
            return;
        auto const& info = ab->GetCapturePointInfo(static_cast<uint8>(node));
        LLMChatterAB::PreCast snapshot;
        snapshot.spell = spell;
        snapshot.instance = bg->GetInstanceID();
        snapshot.caster = player->GetGUID().GetCounter();
        snapshot.node = static_cast<uint8>(node);
        snapshot.state = info._state;
        snapshot.captured = info._captured;
        _abPreCasts.Put(snapshot);
    }
};

class LLMChatterABActorSpellScript : public AllSpellScript
{
public:
    LLMChatterABActorSpellScript()
        : AllSpellScript("LLMChatterABActorSpellScript",
              {ALLSPELLHOOK_ON_CAST, ALLSPELLHOOK_ON_CAST_CANCEL}) { }

    void OnSpellCast(Spell* spell, Unit* caster, SpellInfo const* spellInfo,
        bool) override
    {
        if (!spellInfo || spellInfo->Id != LLMChatterAB::CAPTURE_BANNER_SPELL)
            return;
        LLMChatterAB::PreCast before;
        if (!_abPreCasts.Take(spell, before))
            return;
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !ABActorTrackingEnabled()
            || player->GetGUID().GetCounter() != before.caster)
            return;
        Battleground* bg = player->GetBattleground();
        BattlegroundAB* ab = bg ? bg->ToBattlegroundAB() : nullptr;
        if (!ab || bg->GetInstanceID() != before.instance)
            return;
        uint8 after = ab->GetCapturePointInfo(before.node)._state;
        uint8 team = player->GetBgTeamId() == TEAM_ALLIANCE ? 0 : 1;
        uint8 kind = LLMChatterAB::ClickTransition(
            before.state, before.captured, after, team);
        if (kind == LLMChatterAB::ACTOR_NONE)
            return; // no-op or rejected interaction: never a name
        LLMChatterAB::ActorRecord record;
        record.guid = before.caster;
        record.name = player->GetName();
        record.team = team;
        record.isReal = !IsPlayerBot(player);
        record.kind = kind;
        std::lock_guard<std::mutex> lock(_abActorMutex);
        _abActorEvidence[before.instance][before.node].Add(record);
    }

    void OnSpellCastCancel(Spell* spell, Unit*, SpellInfo const* spellInfo,
        bool) override
    {
        if (spellInfo && spellInfo->Id == LLMChatterAB::CAPTURE_BANNER_SPELL)
            _abPreCasts.Cancel(spell);
    }
};

void AddLLMChatterABScripts()
{
    new LLMChatterABActorPlayerScript();
    new LLMChatterABActorSpellScript();
}
