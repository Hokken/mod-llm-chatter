// Standalone policy tests. Compile only with explicit build authorization.
#include "LLMChatterABPending.h"
#include <cassert>

using namespace LLMChatterAB;

int main()
{
    PendingNodes pending;
    for (std::uint8_t id = 0; id < 5; ++id)
        pending.Record(id, 0, false, 3, false, 1, 1000);
    auto first = pending.Select(1000, 15000, 3);
    assert(first.size() == 3 && first[0].node == 0 && first[2].node == 2);
    // RNG failure: caller does not submit, but the attempt interval is spent.
    assert(pending.Select(1001, 15000, 3).empty());
    auto retry = pending.Select(16000, 15000, 3);
    assert(retry.size() == 3 && retry[0].node == 3 && retry[1].node == 4);
    // No audience does not erase candidates or freeze an empty cohort.
    pending.SetAudiences(retry, {});
    assert(pending.nodes[3].active && pending.nodes[3].receipts.empty());
    pending.SetAudiences(retry, {10, 10, 20});
    assert(pending.nodes[3].receipts.size() == 2);
    pending.Acknowledge(10, retry, true);
    pending.Acknowledge(20, retry, false);
    assert(pending.ForAudience(retry, 10).empty());
    assert(pending.ForAudience(retry, 20).size() == 3);
    // Late new subgroup cannot replay an old revision already sent elsewhere.
    pending.SetAudiences(retry, {10, 20, 30});
    assert(pending.ForAudience(retry, 30).empty());
    // New revisions replace old receipts. Old completions cannot clear them.
    pending.Record(3, 3, false, 4, false, 2, 17000);
    pending.Acknowledge(20, retry, true);
    assert(pending.nodes[3].active && pending.nodes[3].revision == 2);
    assert(!pending.nodes[4].active);
    pending.Expire(47001, 30000);
    for (auto const& node : pending.nodes)
        assert(!node.active);

    PendingNodes reversal;
    reversal.Record(0, 1, true, 4, true, 1, 1);
    reversal.Record(0, 4, true, 1, true, 2, 2);
    assert(!reversal.nodes[0].active); // obsolete unsent alarm cancelled
    reversal.Record(0, 1, true, 4, true, 3, 3);
    auto alarm = reversal.Select(3, 1000, 1);
    reversal.SetAudiences(alarm, {1, 2});
    reversal.Acknowledge(1, alarm, true);
    reversal.Record(0, 4, true, 1, true, 4, 4);
    assert(reversal.nodes[0].active); // submitted alarm needs a newer fact
    reversal.Acknowledge(2, alarm, true);
    assert(reversal.nodes[0].active);

    // Success clears exactly the queued revisions; other pending nodes survive.
    PendingNodes success;
    for (std::uint8_t id = 0; id < 5; ++id)
        success.Record(id, 0, false, 3, false, 1, 0);
    auto batch = success.Select(0, 15000, 3);
    success.SetAudiences(batch, {1});
    success.Acknowledge(1, batch, true);
    assert(!success.nodes[0].active && success.nodes[3].active);
    auto remaining = success.Select(15000, 15000, 3);
    assert(remaining.size() == 2 && remaining[0].node == 3);
    success = {}; // lifecycle reset also resets the attempt budget
    assert(success.Select(15001, 15000, 5).empty());
}
