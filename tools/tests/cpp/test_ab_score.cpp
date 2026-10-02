// Standalone production-policy tests; compile only with build authorization.
#include "LLMChatterABScore.h"
#include <cassert>

using namespace LLMChatterAB;

int main()
{
    std::vector<std::uint32_t> defaults{30, 60, 90};
    assert(ParseMilestonePercents("90, 30,30,60") == defaults);
    for (auto bad : {"", "0,30", "100", "30,", "-1", "3x", ",30", "1.5"})
        assert(ParseMilestonePercents(bad) == defaults);
    auto normal = ScoreThresholds(1600, 1400, defaults);
    assert(normal.size() == 4 && normal.count(480) && normal.count(960));
    assert(normal.at(1400) && !normal.at(1440));
    auto custom = ScoreThresholds(1500, 1400, defaults);
    assert(custom.size() == 4 && custom.count(450) && custom.count(1350));
    auto small = ScoreThresholds(1000, 1400, defaults);
    assert(small.size() == 3 && !small.count(1400) && small.count(900));
    assert(!ScoreThresholds(1400, 1400, defaults).count(1400));
    assert(ScoreThresholds(1000, 900, defaults).at(900));
    assert(ScoreThresholds(1, 1400, defaults).empty());
    auto tiny = ScoreThresholds(2, 1400, defaults);
    assert(tiny.size() == 1 && tiny.count(1));
    assert(ScoreThresholds(3, 1400, defaults).count(2)); // ceil(1.8)

    ScoreTracker score;
    score.Observe(1600, 1400, defaults, {0, 0}, 0);
    score.Observe(1600, 1400, defaults, {1000, 0}, 1);
    assert(score.pending.active && score.pending.threshold == 960);
    auto old = score.pending.revision;
    assert(score.TakeAttempt(1, 1000, 30000));
    // Chance zero/failure spends attempt budget but does not undo reached state.
    assert(!score.TakeAttempt(2, 1000, 30000));
    score.Observe(1600, 1400, defaults, {1010, 0}, 500);
    assert(score.pending.revision == old);
    assert(score.TakeAttempt(1001, 1000, 30000));
    score.Acknowledge(old, false);
    assert(score.pending.active);
    score.Observe(1600, 1400, defaults, {1410, 0}, 1002);
    assert(score.pending.warning && score.pending.threshold == 1400);
    score.Acknowledge(old, true); // old DB result cannot consume newer crossing
    assert(score.pending.active);
    score.Acknowledge(score.pending.revision, true);
    score.Observe(1600, 1400, defaults, {1420, 0}, 1003);
    assert(!score.pending.active); // no replay of earlier thresholds
    score.Observe(1600, 1400, defaults, {1450, 1000}, 1004);
    assert(score.pending.threshold == 1440); // highest same-observation crossing
    assert(!score.TakeAttempt(31005, 1000, 30000));
    assert(!score.pending.active); // bounded expiry
    score.Observe(1600, 1400, defaults, {1600, 1450}, 31006);
    assert(!score.pending.active); // end score discards pending milestone

    ScoreTracker late;
    late.Observe(1000, 1400, defaults, {800, 0}, 0);
    assert(!late.pending.active); // late enable seeds silently
    late.Observe(1000, 1400, defaults, {900, 0}, 1);
    auto oldConfigRevision = late.pending.revision;
    late.Observe(1000, 1400, {95}, {900, 0}, 2);
    assert(!late.pending.active);
    late.Observe(1000, 1400, {95}, {960, 0}, 3);
    late.Acknowledge(oldConfigRevision, true);
    assert(late.pending.active); // config reseed preserves serial uniqueness

    ObjectiveStatusClock status;
    assert(!status.TakeOpportunity(0, 0, false, 0));
    assert(!status.TakeOpportunity(0, 60000, true, 0));
    assert(!status.TakeOpportunity(0, 60000, false, 15000));
    assert(status.TakeOpportunity(15000, 60000, false, 15000));
    // Failed status chance leaves ordinary idle available, but no reroll flood.
    assert(!status.TakeOpportunity(15001, 60000, false, 0));
    assert(status.TakeOpportunity(75000, 60000, false, 0));
}
