// Verified AB banner actor policy (LLMChatterABActor.h). Compile only with
// the user's authorized build, assertions enabled:
//   g++ -std=c++17 -I../../../src test_ab_actor.cpp && ./a.out
#include "LLMChatterABActor.h"
#include "LLMChatterABPending.h"
#include <cassert>

using namespace LLMChatterAB;

static ActorRecord Actor(char const* name, std::uint8_t team,
    std::uint8_t kind, bool real = true)
{
    ActorRecord record;
    record.guid = name[0];
    record.name = name;
    record.team = team;
    record.isReal = real;
    record.kind = kind;
    return record;
}

int main()
{
    // Click transitions mirror EventPlayerClickedOnFlag for both teams.
    assert(ClickTransition(0, false, 3, 0) == ACTOR_CLAIM);
    assert(ClickTransition(0, false, 4, 1) == ACTOR_CLAIM);
    assert(ClickTransition(2, true, 3, 0) == ACTOR_ASSAULT);
    assert(ClickTransition(4, false, 3, 0) == ACTOR_COUNTER_CLAIM);
    assert(ClickTransition(4, true, 1, 0) == ACTOR_DEFENCE);
    // No-op / rejected interaction: unchanged or impossible pairs.
    assert(ClickTransition(3, false, 3, 0) == ACTOR_NONE);
    assert(ClickTransition(1, true, 1, 0) == ACTOR_NONE);
    assert(ClickTransition(4, false, 1, 0) == ACTOR_NONE); // !captured defence
    assert(ClickTransition(0, false, 3, 1) == ACTOR_NONE); // wrong team

    // CheckCast rejection: a pre snapshot without its post is never taken.
    PreCastRing ring;
    int spellA = 0, spellB = 0;
    ring.Put({&spellA, 7, 1, 2, 0, false});
    PreCast out;
    assert(!ring.Take(&spellB, out));
    // A reused Spell pointer replaces its old slot before matching.
    ring.Put({&spellA, 7, 1, 3, 4, true});
    assert(ring.Take(&spellA, out) && out.node == 3 && out.state == 4);
    assert(!ring.Take(&spellA, out));
    ring.Put({&spellB, 7, 2, 1, 0, false});
    ring.Cancel(&spellB);
    assert(!ring.Take(&spellB, out));

    // Rejected old pre -> reused pointer -> new pre rejected -> post: the
    // pre hook cancels any stale slot before its eligibility exits, so the
    // post hook finds nothing for this invocation.
    ring.Put({&spellA, 7, 1, 2, 0, false}); // CheckCast rejected: no post/cancel
    ring.Cancel(&spellA);                   // new pre, then an early return
    assert(!ring.Take(&spellA, out));

    // Same-state interactions invalidate the published revision; a quiet
    // observation does not.
    assert(!InvalidatesRevision(false, 0));
    assert(InvalidatesRevision(false, 1));
    assert(InvalidatesRevision(false, 2));
    assert(InvalidatesRevision(true, 0));
    {
        // Queued case: A's claim (rev 1) was queued to audience 10; B and C
        // then rewrite the contest without changing the sampled state. The
        // observer records rev 2: nothing new is spoken (baseline is the
        // current state), and the queued rev-1 line is rejected at send by
        // the node revision check. A late ack for rev 1 changes nothing.
        PendingNodes pending;
        pending.Record(2, 0, false, 3, false, 1, 1000);
        auto batch = pending.Select(1000, 15000, 3);
        pending.SetAudiences(batch, {10});
        pending.Record(2, 3, false, 3, false, 2, 2000);
        assert(!pending.nodes[2].active && pending.nodes[2].receipts.empty());
        pending.Acknowledge(10, batch, true);
        assert(!pending.nodes[2].active);
    }
    {
        // Unqueued case: the claim is still pending when the rewrite happens.
        // It stays pending (still a claim on net) under rev 2; the observer
        // has already dropped the actor and downgraded the label.
        PendingNodes pending;
        pending.Record(2, 0, false, 3, false, 1, 1000);
        pending.Record(2, 3, false, 3, false, 2, 2000);
        assert(pending.nodes[2].active && pending.nodes[2].revision == 2);
        assert(pending.nodes[2].baseline == 0);
    }

    // A clean verified claim names the caster and starts the contest carry.
    ActorCarry carry;
    NodeEvidence seen;
    seen.Add(Actor("Karaez", 0, ACTOR_CLAIM));
    ActorRecord who;
    assert(ResolveActor(carry, seen, true, "claim", 0, 3, true, who)
        == ACTOR_CLAIM && who.name == "Karaez");
    // Quiet unchanged observations keep the verified actor.
    assert(ResolveActor(carry, NodeEvidence{}, false, "claim", 3, 3, true, who)
        == ACTOR_NONE && carry.active);
    // The timer capture of that exact contest credits the flag.
    assert(ResolveActor(carry, NodeEvidence{}, true, "capture", 3, 1, true, who)
        == ACTOR_FLAG_HELD && who.name == "Karaez" && !carry.active);

    // A different player's successful click: only their record is used.
    carry = {};
    seen = {};
    seen.Add(Actor("Hodangoba", 1, ACTOR_ASSAULT));
    assert(ResolveActor(carry, seen, true, "assault", 1, 4, true, who)
        == ACTOR_ASSAULT && who.name == "Hodangoba");

    // Same-state change-and-return: two verified clicks, no visible change.
    seen = {};
    seen.Add(Actor("Kilco", 0, ACTOR_COUNTER_CLAIM));
    seen.Add(Actor("Hodangoba", 1, ACTOR_COUNTER_CLAIM));
    assert(ResolveActor(carry, seen, false, "assault", 4, 4, true, who)
        == ACTOR_NONE && !carry.active);
    // ...so the timer capture after it names nobody.
    assert(ResolveActor(carry, NodeEvidence{}, true, "capture", 4, 2, true, who)
        == ACTOR_NONE);

    // A long observation gap before the timer completes clears the carry.
    carry = {};
    seen = {};
    seen.Add(Actor("Karaez", 0, ACTOR_ASSAULT));
    assert(ResolveActor(carry, seen, true, "assault", 2, 3, true, who)
        == ACTOR_ASSAULT && carry.active);
    assert(ResolveActor(carry, NodeEvidence{}, false, "assault", 3, 3, false, who)
        == ACTOR_NONE && !carry.active);
    assert(ResolveActor(carry, NodeEvidence{}, true, "capture", 3, 1, true, who)
        == ACTOR_NONE);

    // Saturation: many casts (distinct or the same actor) are never unique.
    for (int repeat = 0; repeat < 2; ++repeat)
    {
        carry = {};
        seen = {};
        for (int i = 0; i < 50; ++i)
            seen.Add(Actor(repeat ? "Karaez" : (i % 2 ? "Kilco" : "Karaez"), 0,
                ACTOR_CLAIM));
        assert(seen.count == 2); // capped: none / unique / ambiguous
        assert(ResolveActor(carry, seen, true, "claim", 0, 3, true, who)
            == ACTOR_NONE);
    }

    // A transition with no matching record (timer/unknown) clears the carry.
    carry = {true, Actor("Karaez", 0, ACTOR_CLAIM), 3};
    assert(ResolveActor(carry, NodeEvidence{}, true, "state_update", 3, 4, true,
        who) == ACTOR_NONE && !carry.active);
    // Team or label mismatch never names anyone.
    seen = {};
    seen.Add(Actor("Karaez", 0, ACTOR_CLAIM));
    assert(ResolveActor(carry, seen, true, "claim", 0, 4, true, who) == ACTOR_NONE);
    assert(ResolveActor(carry, seen, true, "assault", 2, 3, true, who)
        == ACTOR_NONE);
    // A verified defence ends the contest: no later flag credit.
    seen = {};
    seen.Add(Actor("Karaez", 0, ACTOR_DEFENCE));
    assert(ResolveActor(carry, seen, true, "defence", 4, 1, true, who)
        == ACTOR_DEFENCE && !carry.active);
    return 0;
}
