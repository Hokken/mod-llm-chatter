// Production policy integration; compile only with explicit authorization.
#include "LLMChatterABPending.h"
#include "LLMChatterABScore.h"
#include <cassert>

using namespace LLMChatterAB;

int main()
{
    PendingNodes nodes;
    ScoreTracker score;
    ObjectiveStatusClock status;
    auto percents = ParseMilestonePercents("30,60,90");
    score.Observe(1600, 1400, percents, {0, 0}, 0);
    nodes.Record(0, 0, false, 3, false, 1, 1000);
    score.Observe(1600, 1400, percents, {480, 0}, 1000);
    auto batch = nodes.Select(1000, 15000, 3);
    nodes.SetAudiences(batch, {10, 20});
    assert(score.TakeAttempt(1000, 30000, 60000));
    auto revision = score.pending.revision;
    assert(!status.TakeOpportunity(1000, 60000, true, 0));

    // An unresolved score transaction does not spend the node budget.
    // Partial node success does not acknowledge the independent score.
    nodes.Acknowledge(10, batch, true);
    nodes.Acknowledge(20, batch, false);
    auto retry = nodes.Select(16000, 15000, 3);
    assert(retry.size() == 1);
    assert(nodes.ForAudience(retry, 10).empty());
    assert(nodes.ForAudience(retry, 20).size() == 1);
    assert(score.pending.active && score.pending.revision == revision);
    assert(!score.TakeAttempt(16000, 30000, 60000));

    // New observations while BOTH callbacks are outstanding supersede
    // earlier facts. Reverse callback order must not erase the new facts.
    nodes.Record(0, 3, false, 1, true, 2, 17000);
    score.Observe(1600, 1400, percents, {960, 0}, 17000);
    nodes.Acknowledge(20, retry, true);
    score.Acknowledge(revision, true);
    assert(nodes.nodes[0].active && nodes.nodes[0].revision == 2);
    assert(score.pending.active && score.pending.threshold == 960);
    assert(!status.TakeOpportunity(17000, 60000, true, 0));

    // Independent cooldowns become available together without consuming
    // one another. A newly frozen audience cannot replay the old cohort.
    auto latest = nodes.Select(31000, 15000, 3);
    nodes.SetAudiences(latest, {30});
    assert(nodes.ForAudience(latest, 20).empty());
    assert(score.TakeAttempt(31000, 30000, 60000));
    nodes.Acknowledge(30, latest, true);
    score.Acknowledge(score.pending.revision, true);
    assert(!nodes.nodes[0].active && !score.pending.active);
    assert(!status.TakeOpportunity(31000, 60000, false, 46000));
    assert(status.TakeOpportunity(46000, 60000, false, 46000));
    assert(!status.TakeOpportunity(46000, 60000, false, 46000));

    // A stalled observation stream must not keep old pending facts alive.
    nodes.Record(1, 0, false, 4, false, 1, 47000);
    score.Observe(1600, 1400, percents, {1400, 0}, 47000);
    nodes.Expire(107001, 60000);
    assert(!nodes.nodes[1].active);
    assert(!score.TakeAttempt(107001, 30000, 60000));
    score.Observe(1600, 1400, percents, {1400, 0}, 108000);
    assert(!score.pending.active); // no replay of an expired crossing

    // Lifecycle owner destroys outstanding callbacks before resetting
    // these values; a fresh match seeds scores without historical speech.
    nodes = {};
    score = {};
    status = {};
    score.Observe(1000, 1400, percents, {900, 600}, 110000);
    assert(!score.pending.active);
    assert(nodes.Select(110000, 15000, 3).empty());
    assert(!status.TakeOpportunity(110000, 0, false, 0));
}
