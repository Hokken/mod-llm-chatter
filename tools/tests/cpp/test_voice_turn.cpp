// Standalone test for the turn-away bookkeeping (no game headers).
// Build: g++ -std=c++17 -I../../../src test_voice_turn.cpp && ./a.out
#include "LLMChatterVoiceTurn.h"

#include <cassert>
#include <cmath>
#include <cstdio>

using namespace LLMChatterVoice;

namespace
{
TurnNote Note(std::uint32_t msg, std::uint32_t bot, std::uint64_t gen = 7,
    std::uint64_t at = 1000, float o = 1.0f)
{
    return {msg, bot, o, gen, at};
}

void TwoSequentialLines()
{
    TurnNotes notes;
    notes.Note(Note(1, 55), 8);
    notes.Note(Note(2, 55), 8);  // supersedes line 1
    assert(!notes.OnTerminal(1, true, 7, 55));  // first ends: no turn
    assert(notes.OnTerminal(2, true, 7, 55));   // last ends: turn
    assert(notes.Empty());
}

void SecondWaitingThenPlayed()
{
    TurnNotes notes;
    notes.Note(Note(1, 55), 8);
    notes.Note(Note(2, 55), 8);
    // Line 2 is still waiting: nothing terminal for it yet.
    assert(notes.Size() == 1);
    assert(notes.OnTerminal(2, true, 7, 55));
}

void SecondDropped()
{
    TurnNotes notes;
    notes.Note(Note(1, 55), 8);
    notes.Note(Note(2, 55), 8);
    assert(!notes.OnTerminal(2, false, 7, 55));  // expired: no turn
    assert(!notes.OnTerminal(1, true, 7, 55));   // superseded
    assert(notes.Empty());
}

void ExactlyOnceWhateverTheOrder()
{
    TurnNotes notes;
    notes.Note(Note(3, 9), 8);
    assert(notes.OnTerminal(3, true, 7, 9));
    // The same terminal row seen again in a later snapshot.
    assert(!notes.OnTerminal(3, true, 7, 9));
}

void GenerationAndBotMismatch()
{
    TurnNotes notes;
    notes.Note(Note(4, 9, 7), 8);
    assert(!notes.OnTerminal(4, true, 8, 9));
    notes.Note(Note(5, 9, 7), 8);
    assert(!notes.OnTerminal(5, true, 7, 10));
    assert(notes.Empty());
}

void PruneAndCap()
{
    TurnNotes notes;
    notes.Note(Note(1, 1, 7, 1000), 2);
    notes.Note(Note(2, 2, 7, 2000), 2);
    notes.Note(Note(3, 3, 7, 3000), 2);  // evicts message 1
    assert(notes.Size() == 2 && notes.Ids()[0] == 2);
    notes.Prune(32000, 30000, 7);        // message 2 aged out
    assert(notes.Size() == 1 && notes.Ids()[0] == 3);
    notes.Prune(32000, 30000, 8);        // generation moved on
    assert(notes.Empty());
}

void TwoQueuedLinesSameBotDifferentTargets()
{
    PendingFacings pending;
    pending.Add({10, 55, 0xAAAA, 7, 1000}, 8);  // line A -> target A
    pending.Add({11, 55, 0xBBBB, 7, 1100}, 8);  // line B -> target B
    // Nothing supersedes: each applies at its own audio start.
    auto a = pending.Take(10);
    assert(a && a->targetRaw == 0xAAAA);
    auto b = pending.Take(11);
    assert(b && b->targetRaw == 0xBBBB);
    assert(!pending.Take(10));  // exactly once
    assert(pending.Empty());
}

void PendingPruneAndCap()
{
    PendingFacings pending;
    pending.Add({1, 1, 1, 7, 1000}, 2);
    pending.Add({2, 2, 2, 7, 2000}, 2);
    pending.Add({3, 3, 3, 7, 3000}, 2);  // evicts message 1
    assert(pending.Size() == 2 && pending.Ids()[0] == 2);
    pending.Prune(11000, 9000, 7);       // message 2 aged out
    assert(pending.Size() == 1 && pending.Ids()[0] == 3);
    pending.Prune(11000, 9000, 8);       // generation moved on
    assert(pending.Empty());
}

void NoteKeepsRequestedAngle()
{
    // The bot was at 0.2 rad and was told to turn to 2.5 rad. The note
    // must hold 2.5: once the spline finished, the bot is at 2.5 and
    // still facing what delivery chose; the stale 0.2 would reject it.
    float before = 0.2f;
    float requested = 2.5f;
    float afterSpline = 2.5f;
    float tolerance = 3.0f * TWO_PI / 360.0f;
    assert(StillFacing(afterSpline, requested, tolerance));
    assert(!StillFacing(afterSpline, before, tolerance));
}

void FacingAndTurn()
{
    assert(StillFacing(0.02f, TWO_PI - 0.02f, 0.05f));  // across 0
    assert(!StillFacing(1.0f, 1.2f, 0.05f));
    float left = TurnAwayOrientation(6.0f, 0.5f, 1.0f, 1.0f, true);
    assert(std::fabs(left - (7.0f - TWO_PI)) < 1e-4f);  // wrapped
    float right = TurnAwayOrientation(0.2f, 1.0f, 0.5f, 0.0f, false);
    assert(std::fabs(right - (0.2f - 0.5f + TWO_PI)) < 1e-4f);
}
}  // namespace

int main()
{
    TwoSequentialLines();
    SecondWaitingThenPlayed();
    SecondDropped();
    ExactlyOnceWhateverTheOrder();
    GenerationAndBotMismatch();
    PruneAndCap();
    FacingAndTurn();
    TwoQueuedLinesSameBotDifferentTargets();
    PendingPruneAndCap();
    NoteKeepsRequestedAngle();
    std::puts("test_voice_turn: OK");
    return 0;
}
