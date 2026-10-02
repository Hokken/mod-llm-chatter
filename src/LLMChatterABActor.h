#ifndef MOD_LLM_CHATTER_AB_ACTOR_H
#define MOD_LLM_CHATTER_AB_ACTOR_H

#include <array>
#include <cstdint>
#include <string>

// Value-only attribution policy for AB banner interactions. No game objects,
// SQL or locks, so a standalone harness can include it.
namespace LLMChatterAB
{
// Same spell playerbots uses (BattleGroundTactics.h SPELL_CAPTURE_BANNER).
constexpr std::uint32_t CAPTURE_BANNER_SPELL = 21651;

// Core node states (BattlegroundAB.h BG_AB_NodeStatus).
constexpr std::uint8_t NODE_NEUTRAL = 0;
constexpr std::uint8_t NODE_ALLY_OCCUPIED = 1;
constexpr std::uint8_t NODE_ALLY_CONTESTED = 3;

enum ActorKind : std::uint8_t
{
    ACTOR_NONE = 0,
    ACTOR_CLAIM,
    ACTOR_ASSAULT,
    ACTOR_COUNTER_CLAIM,
    ACTOR_DEFENCE,
    ACTOR_FLAG_HELD,
};

inline char const* ActorRole(std::uint8_t kind)
{
    switch (kind)
    {
        case ACTOR_CLAIM: return "claim";
        case ACTOR_ASSAULT: return "assault";
        case ACTOR_COUNTER_CLAIM: return "counter_claim";
        case ACTOR_DEFENCE: return "defence";
        case ACTOR_FLAG_HELD: return "flag_held";
        default: return "";
    }
}

// The node change this caster's successful click produces, mirroring
// BattlegroundAB::EventPlayerClickedOnFlag. team: 0 Alliance, 1 Horde.
// Anything else (no change, an unexpected pair) is not a verified click.
inline std::uint8_t ClickTransition(std::uint8_t pre, bool preCaptured,
    std::uint8_t post, std::uint8_t team)
{
    if (team > 1)
        return ACTOR_NONE;
    std::uint8_t teamContested = NODE_ALLY_CONTESTED + team;
    std::uint8_t teamOccupied = NODE_ALLY_OCCUPIED + team;
    bool preOccupied = pre == 1 || pre == 2;
    bool preContested = pre == 3 || pre == 4;
    if (pre == NODE_NEUTRAL && post == teamContested)
        return ACTOR_CLAIM;
    if (preOccupied && pre != teamOccupied && post == teamContested)
        return ACTOR_ASSAULT;
    if (preContested && pre != teamContested && !preCaptured
        && post == teamContested)
        return ACTOR_COUNTER_CLAIM;
    if (preContested && pre != teamContested && preCaptured
        && post == teamOccupied)
        return ACTOR_DEFENCE;
    return ACTOR_NONE;
}

// Observer transition label for a verified click kind.
inline char const* ClickLabel(std::uint8_t kind)
{
    return kind == ACTOR_FLAG_HELD ? "capture" : ActorRole(kind);
}

struct ActorRecord
{
    std::uint32_t guid = 0;
    std::string name;
    std::uint8_t team = 0;
    bool isReal = false;
    std::uint8_t kind = ACTOR_NONE;
};

// Verified clicks on one node since the last observation. Fixed size: the
// count is capped at 2, so saturation can only make it ambiguous.
struct NodeEvidence
{
    std::uint32_t count = 0; // capped at 2: none / unique / ambiguous
    ActorRecord first;

    void Add(ActorRecord const& record)
    {
        if (!count)
            first = record;
        if (count < 2)
            ++count;
    }
};

// An unchanged sampled state still invalidates the published revision when
// verified clicks rewrote the contest or the captured bit changed.
inline bool InvalidatesRevision(bool capturedChanged, std::uint32_t clicks)
{
    return capturedChanged || clicks > 0;
}

// Pre-cast snapshots keyed by the casting Spell. Bounded; a reused pointer
// replaces its old slot before the new snapshot is stored.
struct PreCast
{
    void const* spell = nullptr;
    std::uint32_t instance = 0;
    std::uint32_t caster = 0;
    std::uint8_t node = 0;
    std::uint8_t state = 0;
    bool captured = false;
};

class PreCastRing
{
public:
    void Put(PreCast const& snapshot)
    {
        Cancel(snapshot.spell);
        _slots[_next] = snapshot;
        _next = (_next + 1) % _slots.size();
    }

    bool Take(void const* spell, PreCast& out)
    {
        for (auto& slot : _slots)
            if (spell && slot.spell == spell)
            {
                out = slot;
                slot = {};
                return true;
            }
        return false;
    }

    void Cancel(void const* spell)
    {
        for (auto& slot : _slots)
            if (spell && slot.spell == spell)
                slot = {};
    }

private:
    std::array<PreCast, 8> _slots{};
    std::size_t _next = 0;
};

// A verified contest actor, carried until the contest it started completes.
struct ActorCarry
{
    bool active = false;
    ActorRecord actor;
    std::uint8_t contestState = 0; // the contested state the actor set
};

// Decide the actor for one observation of one node and update the carry.
// transition: the observer's label after gap/window downgrades.
// Returns ACTOR_NONE or the kind to publish, with `out` filled.
inline std::uint8_t ResolveActor(ActorCarry& carry, NodeEvidence const& seen,
    bool stateChanged, std::string const& transition, std::uint8_t prevState,
    std::uint8_t newState, bool gapOk, ActorRecord& out)
{
    if (!gapOk || seen.count > 1)
    {
        carry = {}; // missed or ambiguous evidence ends the contest credit
        return ACTOR_NONE;
    }
    if (!stateChanged)
    {
        // A quiet unchanged observation keeps the verified actor; a click
        // without a visible change means something was missed.
        if (seen.count)
            carry = {};
        return ACTOR_NONE;
    }
    std::uint8_t newTeam = (newState == 1 || newState == 3) ? 0 : 1;
    if (seen.count == 1 && seen.first.team == newTeam
        && transition == ClickLabel(seen.first.kind))
    {
        out = seen.first;
        if (out.kind == ACTOR_DEFENCE)
            carry = {};
        else
            carry = {true, out, newState};
        return out.kind;
    }
    if (seen.count == 0 && transition == "capture" && carry.active
        && carry.contestState == prevState && carry.actor.team == newTeam)
    {
        out = carry.actor;
        out.kind = ACTOR_FLAG_HELD;
        carry = {};
        return ACTOR_FLAG_HELD;
    }
    // A change with no matching record (timer, unknown cause, mismatch).
    carry = {};
    return ACTOR_NONE;
}
}

#endif
