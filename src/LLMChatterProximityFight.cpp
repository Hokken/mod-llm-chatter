/*
 * mod-llm-chatter - proximity duel and PvP onlooker domain
 *
 * Owns:
 *   - LLMChatterProximityFightPlayerScript (duel request,
 *     start, end, and overworld PvP kill hooks)
 *   - the duel-instance lifecycle and moment selection
 *   - one onlooker reaction per moment: proximity speech for
 *     bots the player can read (same faction), deterministic
 *     emotes for opposite-faction bots
 *   - delivery-time revalidation of fight scene lines
 *
 * Group duel and PvP reactions stay in LLMChatterDuel.cpp
 * and LLMChatterGroupPvP.cpp; this is the ungrouped,
 * local-scene counterpart built on the proximity helpers.
 *
 * Hooks run on map worker threads and only record state
 * under _fightMutex. ProcessPendingFightMoments() runs on the
 * world thread (WorldScript::OnUpdate), like proximity scenes.
 */

#include "LLMChatterProximityFight.h"

#include "LLMChatterConfig.h"
#include "LLMChatterJsonFields.h"
#include "LLMChatterProximity.h"
#include "LLMChatterShared.h"

#include "Containers.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <ctime>
#include <limits>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{

enum FightMomentBit : uint8
{
    MOMENT_BEFORE = 1,
    MOMENT_DURING = 2,
    MOMENT_AFTER = 4,
};

enum class DuelPhase : uint8
{
    Challenged,
    InProgress,
    Completed,
};

struct DuelInstance
{
    uint64 id = 0;
    uint32 challengerGuid = 0;
    uint32 targetGuid = 0;
    DuelPhase phase = DuelPhase::Challenged;
    bool started = false;
    time_t requestedAt = 0;
    time_t startedAt = 0;
    time_t completedAt = 0;
    bool rolled = false;
    uint8 selected = 0;
    // Moments already fired or dropped; never retried.
    uint8 done = 0;
    time_t duringDue = 0;
    uint32 winnerGuid = 0;
    uint32 loserGuid = 0;
    std::string outcome;
};

struct PendingKill
{
    uint32 killerGuid = 0;
    uint32 victimGuid = 0;
    time_t at = 0;
};

// One step of an opposite-faction emote reaction. A 2-3 bot
// exchange is several steps staggered by the proximity
// conversation line delay.
struct PendingEmote
{
    bool isDuel = false;
    uint64 instanceId = 0;
    uint8 moment = 0;
    uint32 guidA = 0;
    uint32 guidB = 0;
    time_t fightAt = 0;
    uint32 botGuid = 0;
    uint32 anchorGuid = 0;
    // Set when the anchor is a duellist (fight anchor rule).
    uint32 anchorOpponentGuid = 0;
    uint32 faceGuid = 0;
    uint32 emoteId = 0;
    time_t dueAt = 0;
};

std::mutex _fightMutex;
std::unordered_map<uint64, DuelInstance> _duels;
std::vector<PendingKill> _pendingKills;
std::vector<PendingEmote> _pendingEmotes;
std::unordered_map<std::string, time_t> _sceneCooldowns;
uint64 _nextDuelInstanceId = 1;

bool IsFightReactionsEnabled()
{
    return sLLMChatterConfig
        && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_proxChatterEnable
        && sLLMChatterConfig->_useEventSystem
        && sLLMChatterConfig->_proxFightEnable;
}

bool IsInstancedPvP(Player* player)
{
    return player
        && (player->InBattleground() || player->InArena());
}

uint64 PairKey(uint32 a, uint32 b)
{
    if (a > b)
        std::swap(a, b);
    return (static_cast<uint64>(a) << 32) | b;
}

Player* FindPlayerByCounter(uint32 guid)
{
    if (!guid)
        return nullptr;
    Player* player = ObjectAccessor::FindPlayer(
        ObjectGuid::Create<HighGuid::Player>(guid));
    return player && player->IsInWorld()
        ? player : nullptr;
}

// Live duel state between the pair, or -1 when they are not
// currently in a duel with each other.
int LiveDuelState(uint32 guidA, uint32 guidB)
{
    Player* a = FindPlayerByCounter(guidA);
    if (!a || !a->duel || !a->duel->Opponent)
        return -1;
    if (a->duel->Opponent->GetGUID().GetCounter() != guidB)
        return -1;
    return static_cast<int>(a->duel->State);
}

char const* MomentName(uint8 moment)
{
    switch (moment)
    {
        case MOMENT_BEFORE:
            return "before";
        case MOMENT_DURING:
            return "during";
        case MOMENT_AFTER:
            return "after";
        default:
            return "kill";
    }
}

uint8 MomentFromName(std::string const& name)
{
    if (name == "before")
        return MOMENT_BEFORE;
    if (name == "during")
        return MOMENT_DURING;
    if (name == "after")
        return MOMENT_AFTER;
    return 0;
}

// Roll the moment set once per duel: one moment, a second
// with SecondMomentChance, a third with ThirdMomentChance
// only after a second (defaults: 80% / 16% / 4%).
uint8 RollDuelMoments()
{
    std::vector<uint8> pool = {
        MOMENT_BEFORE, MOMENT_DURING, MOMENT_AFTER};
    Acore::Containers::RandomShuffle(pool);
    uint8 selected = pool[0];
    if (urand(1, 100)
        <= sLLMChatterConfig->_proxFightSecondMomentChance)
    {
        selected |= pool[1];
        if (urand(1, 100)
            <= sLLMChatterConfig
                   ->_proxFightThirdMomentChance)
            selected |= pool[2];
    }
    return selected;
}

bool TryReserveSceneCooldownLocked(
    std::string const& key, time_t now)
{
    time_t cooldown = static_cast<time_t>(
        sLLMChatterConfig->_proxFightSceneCooldownSeconds);
    for (auto it = _sceneCooldowns.begin();
         it != _sceneCooldowns.end(); )
    {
        if (now - it->second >= cooldown)
            it = _sceneCooldowns.erase(it);
        else
            ++it;
    }
    if (_sceneCooldowns.count(key))
        return false;
    _sceneCooldowns[key] = now;
    return true;
}

std::string LocationCellKey(Player* anchor)
{
    Map* map = anchor->GetMap();
    // A crowded hub within one cell counts as one scene.
    float cell = static_cast<float>(std::max<uint32>(1,
        sLLMChatterConfig->_proxFightSceneCellYards));
    int32 cellX = static_cast<int32>(
        std::floor(anchor->GetPositionX() / cell));
    int32 cellY = static_cast<int32>(
        std::floor(anchor->GetPositionY() / cell));
    return std::to_string(anchor->GetMapId()) + ":"
        + std::to_string(map ? map->GetInstanceId() : 0)
        + ":" + std::to_string(cellX)
        + ":" + std::to_string(cellY);
}

// Validity of a fight scene at firing or delivery time.
// Caller holds _fightMutex.
bool IsFightSceneValidLocked(
    bool isDuel, uint64 instanceId, uint8 moment,
    uint32 guidA, uint32 guidB, time_t fightAt,
    time_t now)
{
    if (!IsFightReactionsEnabled())
        return false;

    if (!isDuel)
    {
        return fightAt
            && now - fightAt
                <= static_cast<time_t>(
                    sLLMChatterConfig
                        ->_proxFightLineMaxAgeSeconds);
    }

    auto it = _duels.find(PairKey(guidA, guidB));
    if (it == _duels.end()
        || it->second.id != instanceId)
        return false;
    DuelInstance const& duel = it->second;
    int state = LiveDuelState(guidA, guidB);

    switch (moment)
    {
        case MOMENT_BEFORE:
            return duel.phase == DuelPhase::Challenged
                && (state == DUEL_STATE_CHALLENGED
                    || state == DUEL_STATE_COUNTDOWN);
        case MOMENT_DURING:
            return duel.phase == DuelPhase::InProgress
                && state == DUEL_STATE_IN_PROGRESS;
        case MOMENT_AFTER:
            return duel.phase == DuelPhase::Completed
                && duel.started
                && now - duel.completedAt
                    <= static_cast<time_t>(
                        sLLMChatterConfig
                            ->_proxFightCompletedRetentionSeconds);
        default:
            return false;
    }
}

// ---------------------------------------------------------
// Reaction building
// ---------------------------------------------------------

std::string FactionName(Player* player)
{
    return player->GetTeamId() == TEAM_ALLIANCE
        ? "Alliance" : "Horde";
}

// Fighter identity only for fighters every roster member
// can perceive, so a stealthed fighter is never named.
std::string BuildFightersJson(
    std::vector<Player*> const& fighters,
    std::vector<Player*> const& roster,
    Player* anchor,
    std::vector<uint32>& namedGuids)
{
    std::string json = "[";
    bool first = true;
    for (Player* fighter : fighters)
    {
        bool known = std::all_of(
            roster.begin(), roster.end(),
            [fighter](Player* bot)
            {
                return IsUnitPerceivableBy(bot, fighter);
            });
        if (!known)
            continue;
        namedGuids.push_back(
            fighter->GetGUID().GetCounter());
        if (!first)
            json += ",";
        first = false;
        json += "{\"name\":\""
            + JsonEscape(fighter->GetName())
            + "\",\"race\":"
            + std::to_string(fighter->getRace())
            + ",\"class\":"
            + std::to_string(fighter->getClass())
            + ",\"level\":"
            + std::to_string(fighter->GetLevel())
            + ",\"faction\":\"" + FactionName(fighter)
            + "\",\"is_player\":"
            + std::string(
                fighter == anchor ? "true" : "false")
            + "}";
    }
    return json + "]";
}

bool IsNamed(
    std::vector<uint32> const& namedGuids, uint32 guid)
{
    return std::find(
        namedGuids.begin(), namedGuids.end(), guid)
        != namedGuids.end();
}

// One reaction shape and one roster per moment. A
// conversation needs 2-3 bots from the same pool; with no
// pool large enough it downgrades to a statement.
std::vector<Player*> ChooseRoster(
    std::vector<Player*>& sameFaction,
    std::vector<Player*>& opposite,
    bool& useSpeech)
{
    bool conversation = urand(1, 100)
        <= sLLMChatterConfig->_proxFightConversationChance;
    size_t need = conversation ? 2 : 1;
    if (conversation
        && sameFaction.size() < 2 && opposite.size() < 2)
    {
        conversation = false;
        need = 1;
    }

    bool sameOk = sameFaction.size() >= need;
    bool oppositeOk = opposite.size() >= need;
    if (!sameOk && !oppositeOk)
        return {};
    useSpeech = sameOk && (!oppositeOk || urand(0, 1) == 0);

    std::vector<Player*>& pool =
        useSpeech ? sameFaction : opposite;
    Acore::Containers::RandomShuffle(pool);
    size_t count = conversation
        ? std::min<size_t>(pool.size(), urand(2, 3))
        : 1;
    return std::vector<Player*>(
        pool.begin(), pool.begin() + count);
}

std::vector<uint32> EmoteTable(
    uint8 moment, bool isDuel, bool sideWon)
{
    if (!isDuel)
    {
        if (sideWon)
            return {TEXT_EMOTE_CHEER, TEXT_EMOTE_LAUGH,
                TEXT_EMOTE_FLEX, TEXT_EMOTE_ROAR};
        return {TEXT_EMOTE_ANGRY, TEXT_EMOTE_THREATEN,
            TEXT_EMOTE_SIGH};
    }
    switch (moment)
    {
        case MOMENT_BEFORE:
            return {TEXT_EMOTE_CHEER, TEXT_EMOTE_APPLAUD,
                TEXT_EMOTE_SALUTE};
        case MOMENT_DURING:
            return {TEXT_EMOTE_CHEER, TEXT_EMOTE_GASP,
                TEXT_EMOTE_APPLAUD, TEXT_EMOTE_LAUGH};
        default:
            return {TEXT_EMOTE_APPLAUD, TEXT_EMOTE_CHEER,
                TEXT_EMOTE_BOW, TEXT_EMOTE_LAUGH};
    }
}

struct FightScene
{
    bool isDuel = false;
    uint64 instanceId = 0;
    uint8 moment = 0;
    uint32 guidA = 0;
    uint32 guidB = 0;
    time_t fightAt = 0;
    // Present fighters (A first when present).
    std::vector<Player*> fighters;
    // Duel end / PvP kill details.
    uint32 winnerGuid = 0;
    uint32 loserGuid = 0;
    std::string outcome;
};

// The roster is already off its proximity entity cooldown
// (filtered at collection), so every member is scheduled and
// all cooldowns are marked together: no partial exchanges.
void ScheduleEmotes(
    FightScene const& scene,
    std::vector<Player*> const& roster,
    Player* anchor, uint32 anchorOpponentGuid,
    bool sideWon, uint32 faceGuid, time_t now)
{
    std::vector<uint32> table = EmoteTable(
        scene.moment, scene.isDuel, sideWon);
    if (roster.empty() || roster.size() > table.size())
        return;
    Acore::Containers::RandomShuffle(table);
    uint32 delay = sLLMChatterConfig
        ->_proxChatterConversationLineDelay;
    for (size_t slot = 0; slot < roster.size(); ++slot)
    {
        PendingEmote step;
        step.isDuel = scene.isDuel;
        step.instanceId = scene.instanceId;
        step.moment = scene.moment;
        step.guidA = scene.guidA;
        step.guidB = scene.guidB;
        step.fightAt = scene.fightAt;
        step.botGuid = roster[slot]->GetGUID().GetCounter();
        step.anchorGuid = anchor->GetGUID().GetCounter();
        step.anchorOpponentGuid = anchorOpponentGuid;
        step.faceGuid = faceGuid;
        step.emoteId = table[slot];
        step.dueAt = now + 1
            + static_cast<time_t>(slot * delay);
        _pendingEmotes.push_back(step);
    }
    MarkProximityFightBotCooldowns(anchor, roster);
    NoteProximityFightTrigger(anchor);
}

std::string BuildFightFields(
    FightScene const& scene,
    std::vector<Player*> const& roster,
    Player* anchor, uint32 anchorOpponentGuid,
    bool sideWon)
{
    std::vector<uint32> named;
    std::string fighters = BuildFightersJson(
        scene.fighters, roster, anchor, named);
    char const* kind = scene.isDuel ? "duel" : "pvp";
    char const* moment = MomentName(scene.moment);

    std::string json =
        "\"fight_kind\":\"" + std::string(kind) + "\""
        + ",\"fight_moment\":\"" + moment + "\""
        + ",\"fight_instance_id\":"
        + std::to_string(scene.instanceId)
        + ",\"fight_a_guid\":"
        + std::to_string(scene.guidA)
        + ",\"fight_b_guid\":"
        + std::to_string(scene.guidB)
        + ",\"fight_at\":"
        + std::to_string(static_cast<uint64>(scene.fightAt));
    if (anchorOpponentGuid)
        json += ",\"fight_opponent_guid\":"
            + std::to_string(anchorOpponentGuid);

    json += ",\"fight_scene\":{\"kind\":\""
        + std::string(kind)
        + "\",\"moment\":\"" + moment
        + "\",\"fighters\":" + fighters
        + ",\"player_is_fighter\":"
        + std::string(anchorOpponentGuid ? "true" : "false");

    auto nameOf = [&scene, &named](uint32 guid)
    {
        if (!guid || !IsNamed(named, guid))
            return std::string();
        for (Player* fighter : scene.fighters)
            if (fighter->GetGUID().GetCounter() == guid)
                return fighter->GetName();
        return std::string();
    };
    if (scene.isDuel && scene.moment == MOMENT_AFTER)
    {
        json += ",\"outcome\":\""
            + JsonEscape(scene.outcome) + "\""
            + ",\"winner_name\":\""
            + JsonEscape(nameOf(scene.winnerGuid)) + "\""
            + ",\"loser_name\":\""
            + JsonEscape(nameOf(scene.loserGuid)) + "\"";
    }
    if (!scene.isDuel)
    {
        json += ",\"victor_name\":\""
            + JsonEscape(nameOf(scene.winnerGuid)) + "\""
            + ",\"fallen_name\":\""
            + JsonEscape(nameOf(scene.loserGuid)) + "\""
            + ",\"onlooker_side_won\":"
            + std::string(sideWon ? "true" : "false");
    }
    return json + "}";
}

// Fire one moment: exactly one reaction (speech or emotes,
// never both). Caller holds _fightMutex.
void FireFightScene(
    FightScene const& scene, Player* anchor,
    uint32 anchorOpponentGuid, time_t now)
{
    uint32 baseChance = scene.isDuel
        ? sLLMChatterConfig->_proxFightDuelChance
        : sLLMChatterConfig->_proxFightPvPChance;
    uint32 chance =
        ComputeProximityFightChance(anchor, baseChance);
    if (chance == 0 || urand(1, 100) > chance)
        return;

    std::vector<Unit*> fighterUnits(
        scene.fighters.begin(), scene.fighters.end());
    std::vector<Player*> sameFaction;
    std::vector<Player*> opposite;
    CollectProximityFightOnlookers(
        anchor, fighterUnits, sameFaction, opposite);

    bool useSpeech = false;
    std::vector<Player*> roster =
        ChooseRoster(sameFaction, opposite, useSpeech);
    if (roster.empty())
        return;

    // PvP: did the reacting side win? The roster is one team.
    Player* winner = FindPlayerByCounter(scene.winnerGuid);
    bool sideWon = !scene.isDuel && winner
        && roster.front()->GetTeamId()
            == winner->GetTeamId();

    if (useSpeech)
    {
        QueueProximityFightSpeech(
            anchor, roster,
            BuildFightFields(
                scene, roster, anchor,
                anchorOpponentGuid, sideWon));
        return;
    }

    uint32 faceGuid = scene.isDuel
        ? (scene.winnerGuid ? scene.winnerGuid
                            : scene.guidA)
        : (sideWon ? scene.loserGuid
                   : scene.winnerGuid);
    ScheduleEmotes(
        scene, roster, anchor, anchorOpponentGuid,
        sideWon, faceGuid, now);
}

// Anchor for a duel moment: a real-player duellist when
// eligible (duel combat allowed), else the nearest onlooking
// real player.
Player* SelectDuelAnchor(
    std::vector<Player*> const& fighters,
    uint32& anchorOpponentGuid)
{
    anchorOpponentGuid = 0;
    for (Player* fighter : fighters)
    {
        if (IsPlayerBot(fighter))
            continue;
        Player* other = nullptr;
        for (Player* f : fighters)
            if (f != fighter)
                other = f;
        uint32 otherGuid = other
            ? other->GetGUID().GetCounter() : 0;
        if (otherGuid
            && IsProximityFightAnchorEligible(
                fighter, otherGuid))
        {
            anchorOpponentGuid = otherGuid;
            return fighter;
        }
    }
    if (fighters.empty())
        return nullptr;
    std::vector<Unit*> units(
        fighters.begin(), fighters.end());
    return FindProximityFightAnchor(
        fighters.front(), units);
}

std::vector<Player*> PresentDuellists(
    DuelInstance const& duel)
{
    std::vector<Player*> out;
    if (Player* a = FindPlayerByCounter(
            duel.challengerGuid))
        out.push_back(a);
    if (Player* b = FindPlayerByCounter(
            duel.targetGuid))
        out.push_back(b);
    return out;
}

void FireDuelMomentLocked(
    DuelInstance const& duel, uint8 moment, time_t now)
{
    FightScene scene;
    scene.isDuel = true;
    scene.instanceId = duel.id;
    scene.moment = moment;
    scene.guidA = duel.challengerGuid;
    scene.guidB = duel.targetGuid;
    scene.fighters = PresentDuellists(duel);
    scene.winnerGuid = duel.winnerGuid;
    scene.loserGuid = duel.loserGuid;
    scene.outcome = duel.outcome;
    if (scene.fighters.empty())
        return;

    uint32 anchorOpponentGuid = 0;
    Player* anchor =
        SelectDuelAnchor(scene.fighters, anchorOpponentGuid);
    if (!anchor)
        return;
    FireFightScene(scene, anchor, anchorOpponentGuid, now);
}

// Roll the moment set once, with repeat throttling between
// duel instances keyed by anchor and location cell. It is
// never re-checked for later moments of the same duel.
void RollDuelLocked(DuelInstance& duel, time_t now)
{
    duel.rolled = true;
    std::vector<Player*> fighters = PresentDuellists(duel);
    uint32 anchorOpponentGuid = 0;
    Player* anchor =
        SelectDuelAnchor(fighters, anchorOpponentGuid);
    if (!anchor)
        return;
    std::string key = "duel:"
        + std::to_string(anchor->GetGUID().GetCounter())
        + ":" + LocationCellKey(anchor);
    if (!TryReserveSceneCooldownLocked(key, now))
        return;
    duel.selected = RollDuelMoments();
}

void ProcessDuelsLocked(time_t now)
{
    time_t expiry = static_cast<time_t>(
        sLLMChatterConfig->_proxFightPendingExpirySeconds);
    time_t retention = static_cast<time_t>(
        sLLMChatterConfig
            ->_proxFightCompletedRetentionSeconds);

    for (auto it = _duels.begin(); it != _duels.end(); )
    {
        DuelInstance& duel = it->second;

        // Safety sweep for a missed hook: a live instance
        // whose pair is no longer dueling is completed.
        if (duel.phase != DuelPhase::Completed
            && LiveDuelState(
                   duel.challengerGuid, duel.targetGuid)
                < 0)
        {
            duel.phase = DuelPhase::Completed;
            duel.completedAt = now;
            if (duel.outcome.empty())
                duel.outcome = "interrupted";
        }

        if (!duel.rolled)
        {
            if (duel.phase == DuelPhase::Completed)
                duel.rolled = true;
            else
                RollDuelLocked(duel, now);
        }

        // before: due ChallengeDelaySeconds after request.
        if ((duel.selected & MOMENT_BEFORE)
            && !(duel.done & MOMENT_BEFORE))
        {
            time_t due = duel.requestedAt
                + static_cast<time_t>(
                    sLLMChatterConfig
                        ->_proxFightChallengeDelaySeconds);
            if (duel.phase != DuelPhase::Challenged)
                duel.done |= MOMENT_BEFORE;
            else if (now >= due)
            {
                duel.done |= MOMENT_BEFORE;
                if (now - due <= expiry
                    && IsFightSceneValidLocked(
                        true, duel.id, MOMENT_BEFORE,
                        duel.challengerGuid,
                        duel.targetGuid, 0, now))
                    FireDuelMomentLocked(
                        duel, MOMENT_BEFORE, now);
            }
        }

        // during: scheduled once the duel has started.
        if ((duel.selected & MOMENT_DURING)
            && !(duel.done & MOMENT_DURING))
        {
            if (duel.phase == DuelPhase::Completed)
                duel.done |= MOMENT_DURING;
            else if (duel.phase == DuelPhase::InProgress)
            {
                if (!duel.duringDue)
                {
                    duel.duringDue = duel.startedAt
                        + static_cast<time_t>(urand(
                            sLLMChatterConfig
                                ->_proxFightMidDelayMinSeconds,
                            sLLMChatterConfig
                                ->_proxFightMidDelayMaxSeconds));
                }
                if (now >= duel.duringDue)
                {
                    duel.done |= MOMENT_DURING;
                    if (now - duel.duringDue <= expiry
                        && IsFightSceneValidLocked(
                            true, duel.id, MOMENT_DURING,
                            duel.challengerGuid,
                            duel.targetGuid, 0, now))
                        FireDuelMomentLocked(
                            duel, MOMENT_DURING, now);
                }
            }
        }

        // after: only for a duel that actually started.
        if ((duel.selected & MOMENT_AFTER)
            && !(duel.done & MOMENT_AFTER)
            && duel.phase == DuelPhase::Completed)
        {
            duel.done |= MOMENT_AFTER;
            if (duel.started
                && now - duel.completedAt <= expiry
                && IsFightSceneValidLocked(
                    true, duel.id, MOMENT_AFTER,
                    duel.challengerGuid,
                    duel.targetGuid, 0, now))
                FireDuelMomentLocked(
                    duel, MOMENT_AFTER, now);
        }

        // Retire only completed instances with no pending
        // work, after the retention window that covers LLM
        // and delivery latency. Live duels never age out.
        bool pendingEmote = std::any_of(
            _pendingEmotes.begin(), _pendingEmotes.end(),
            [&duel](PendingEmote const& step)
            {
                return step.isDuel
                    && step.instanceId == duel.id;
            });
        bool allDone =
            (duel.selected & ~duel.done) == 0;
        if (duel.phase == DuelPhase::Completed
            && allDone && !pendingEmote
            && now - duel.completedAt >= retention)
            it = _duels.erase(it);
        else
            ++it;
    }
}

void ProcessKillsLocked(time_t now)
{
    time_t expiry = static_cast<time_t>(
        sLLMChatterConfig->_proxFightPendingExpirySeconds);
    std::vector<PendingKill> kills;
    kills.swap(_pendingKills);

    for (PendingKill const& kill : kills)
    {
        if (now - kill.at > expiry)
            continue;

        Player* killer = FindPlayerByCounter(kill.killerGuid);
        Player* victim = FindPlayerByCounter(kill.victimGuid);
        FightScene scene;
        scene.isDuel = false;
        scene.moment = 0;
        scene.guidA = kill.killerGuid;
        scene.guidB = kill.victimGuid;
        scene.fightAt = kill.at;
        scene.winnerGuid = kill.killerGuid;
        scene.loserGuid = kill.victimGuid;
        if (killer)
            scene.fighters.push_back(killer);
        if (victim)
            scene.fighters.push_back(victim);
        if (scene.fighters.empty())
            continue;

        WorldObject* center = victim
            ? static_cast<WorldObject*>(victim)
            : static_cast<WorldObject*>(killer);
        std::vector<Unit*> units(
            scene.fighters.begin(), scene.fighters.end());
        Player* anchor =
            FindProximityFightAnchor(center, units);
        if (!anchor)
            continue;

        std::string key = "pvp:"
            + std::to_string(
                anchor->GetGUID().GetCounter())
            + ":" + std::to_string(kill.killerGuid)
            + ":" + std::to_string(kill.victimGuid);
        if (!TryReserveSceneCooldownLocked(key, now))
            continue;

        FireFightScene(scene, anchor, 0, now);
    }
}

void ProcessEmotesLocked(time_t now)
{
    time_t expiry = static_cast<time_t>(
        sLLMChatterConfig->_proxFightPendingExpirySeconds);
    for (auto it = _pendingEmotes.begin();
         it != _pendingEmotes.end(); )
    {
        PendingEmote const& step = *it;
        if (now < step.dueAt)
        {
            ++it;
            continue;
        }

        bool play = now - step.dueAt <= expiry
            && IsFightSceneValidLocked(
                step.isDuel, step.instanceId, step.moment,
                step.guidA, step.guidB, step.fightAt, now);
        Player* bot = play
            ? FindPlayerByCounter(step.botGuid) : nullptr;
        Player* anchor = play
            ? FindPlayerByCounter(step.anchorGuid) : nullptr;

        // Re-apply the anchor rule and the shared onlooker
        // policy at execution time: during the stagger the
        // anchor may die, fight, or leave, and the bot may
        // mount, join the anchor's group, or lose the fight.
        std::vector<Unit*> fighters;
        if (Player* a = FindPlayerByCounter(step.guidA))
            fighters.push_back(a);
        if (Player* b = FindPlayerByCounter(step.guidB))
            fighters.push_back(b);
        bool anchorOk = anchor
            && (step.anchorOpponentGuid
                ? IsProximityFightAnchorEligible(
                    anchor, step.anchorOpponentGuid)
                : IsProximityAnchorEligible(anchor));
        if (bot && anchorOk && !fighters.empty()
            && IsProximityFightOnlookerEligible(
                anchor, bot, fighters, false))
        {
            Player* face =
                FindPlayerByCounter(step.faceGuid);
            if (face && sLLMChatterConfig->_facingEnable
                && IsSafeForChatterFacing(bot)
                && IsUnitPerceivableBy(bot, face))
                bot->SetFacingToObject(face);
            SendBotTextEmote(bot, step.emoteId);
        }
        it = _pendingEmotes.erase(it);
    }
}

} // namespace

// ============================================================
// World-thread driver and delivery validation
// ============================================================

void ProcessPendingFightMoments()
{
    std::lock_guard<std::mutex> lock(_fightMutex);
    if (!IsFightReactionsEnabled())
    {
        _pendingKills.clear();
        _pendingEmotes.clear();
        return;
    }
    time_t now = time(nullptr);
    ProcessDuelsLocked(now);
    ProcessKillsLocked(now);
    ProcessEmotesLocked(now);
}

bool IsProximityFightLineStillValid(
    std::string const& eventExtraData)
{
    // The row's extra_data comes back from a MySQL JSON
    // column (`"key": value`), so use the whitespace-tolerant
    // readers shared with tools/tests/cpp/test_json_fields.cpp.
    std::string kind;
    if (!LLMChatterJson::ReadString(
            eventExtraData, "fight_kind", kind))
        return false;
    bool isDuel = kind == "duel";
    if (!isDuel && kind != "pvp")
        return false;

    uint8 momentBit = 0;
    if (isDuel)
    {
        std::string moment;
        if (!LLMChatterJson::ReadString(
                eventExtraData, "fight_moment", moment))
            return false;
        momentBit = MomentFromName(moment);
        if (!momentBit)
            return false;
    }

    std::uint64_t instanceId = 0;
    std::uint64_t guidA = 0;
    std::uint64_t guidB = 0;
    std::uint64_t fightAt = 0;
    if (!LLMChatterJson::ReadUInt64(
            eventExtraData, "fight_a_guid", guidA)
        || !LLMChatterJson::ReadUInt64(
            eventExtraData, "fight_b_guid", guidB)
        || guidA > std::numeric_limits<uint32>::max()
        || guidB > std::numeric_limits<uint32>::max())
        return false;
    if (isDuel
        && !LLMChatterJson::ReadUInt64(
            eventExtraData, "fight_instance_id", instanceId))
        return false;
    if (!isDuel
        && !LLMChatterJson::ReadUInt64(
            eventExtraData, "fight_at", fightAt))
        return false;

    std::lock_guard<std::mutex> lock(_fightMutex);
    return IsFightSceneValidLocked(
        isDuel, instanceId, momentBit,
        static_cast<uint32>(guidA),
        static_cast<uint32>(guidB),
        static_cast<time_t>(fightAt),
        time(nullptr));
}

// ============================================================
// Hooks (map worker threads): record state only
// ============================================================

class LLMChatterProximityFightPlayerScript
    : public PlayerScript
{
public:
    LLMChatterProximityFightPlayerScript()
        : PlayerScript(
              "LLMChatterProximityFightPlayerScript",
              {PLAYERHOOK_ON_DUEL_REQUEST,
               PLAYERHOOK_ON_DUEL_START,
               PLAYERHOOK_ON_DUEL_END,
               PLAYERHOOK_ON_PVP_KILL}) {}

    void OnPlayerDuelRequest(
        Player* target, Player* challenger) override
    {
        if (!IsFightReactionsEnabled()
            || !target || !challenger
            || IsInstancedPvP(target)
            || IsInstancedPvP(challenger))
            return;

        std::lock_guard<std::mutex> lock(_fightMutex);
        DuelInstance duel;
        duel.id = _nextDuelInstanceId++;
        duel.challengerGuid =
            challenger->GetGUID().GetCounter();
        duel.targetGuid = target->GetGUID().GetCounter();
        duel.requestedAt = time(nullptr);
        // A rematch replaces the pair's earlier instance, so
        // its pending moments and lines become stale.
        _duels[PairKey(
            duel.challengerGuid, duel.targetGuid)] = duel;
    }

    void OnPlayerDuelStart(
        Player* player1, Player* player2) override
    {
        if (!player1 || !player2)
            return;
        std::lock_guard<std::mutex> lock(_fightMutex);
        auto it = _duels.find(PairKey(
            player1->GetGUID().GetCounter(),
            player2->GetGUID().GetCounter()));
        if (it == _duels.end()
            || it->second.phase != DuelPhase::Challenged)
            return;
        it->second.phase = DuelPhase::InProgress;
        it->second.started = true;
        it->second.startedAt = time(nullptr);
    }

    void OnPlayerDuelEnd(
        Player* winner, Player* loser,
        DuelCompleteType type) override
    {
        if (!winner || !loser)
            return;
        time_t now = time(nullptr);
        // StartTime is 0 for a declined challenge and in the
        // future during the countdown.
        bool started = loser->duel
            && loser->duel->StartTime != 0
            && now >= loser->duel->StartTime;

        std::lock_guard<std::mutex> lock(_fightMutex);
        auto it = _duels.find(PairKey(
            winner->GetGUID().GetCounter(),
            loser->GetGUID().GetCounter()));
        if (it == _duels.end()
            || it->second.phase == DuelPhase::Completed)
            return;
        DuelInstance& duel = it->second;
        duel.phase = DuelPhase::Completed;
        duel.started = started;
        duel.completedAt = now;
        duel.winnerGuid = winner->GetGUID().GetCounter();
        duel.loserGuid = loser->GetGUID().GetCounter();
        duel.outcome = type == DUEL_WON ? "won"
            : type == DUEL_FLED ? "fled" : "interrupted";
    }

    void OnPlayerPVPKill(
        Player* killer, Player* killed) override
    {
        if (!IsFightReactionsEnabled()
            || !killer || !killed || killer == killed
            || killer->GetTeamId() == killed->GetTeamId()
            || IsInstancedPvP(killer)
            || IsInstancedPvP(killed))
            return;

        std::lock_guard<std::mutex> lock(_fightMutex);
        PendingKill kill;
        kill.killerGuid = killer->GetGUID().GetCounter();
        kill.victimGuid = killed->GetGUID().GetCounter();
        kill.at = time(nullptr);
        _pendingKills.push_back(kill);
    }
};

void AddLLMChatterProximityFightScripts()
{
    new LLMChatterProximityFightPlayerScript();
}
