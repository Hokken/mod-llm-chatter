// Standalone test for src/LLMChatterGroupGuard.h (standard
// library only; not part of the server build).
//
// Also covers src/LLMChatterSceneClosure.h.
//
// Built and run by tools/tests/test_group_guard_cpp.py when a
// C++ compiler is available:
//   c++ -std=c++17 -I src tools/tests/cpp/test_group_guard.cpp
//
// Covers the delivery guard for issue #94: a queued line drops
// when its speaker's (epoch, group, revision, fingerprint) no
// longer matches. Inputs mirror the MySQL JSON re-serialisation
// of extra_data (a space after every ':' and ',').

#include "LLMChatterGroupGuard.h"
#include "LLMChatterSceneClosure.h"

#include <cstdint>
#include <cstdio>
#include <ctime>
#include <string>

namespace
{

using LLMChatterGroupGuard::Fingerprint;
using LLMChatterGroupGuard::Guard;
using LLMChatterGroupGuard::GuardJson;
using LLMChatterGroupGuard::GuardMatches;
using LLMChatterGroupGuard::ReadResult;
using LLMChatterGroupGuard::ReadSpeakerGuard;

int failures = 0;

void Check(bool condition, char const* what)
{
    if (!condition)
    {
        std::printf("FAIL: %s\n", what);
        ++failures;
    }
}

Guard Make(char const* epoch, std::uint64_t g, std::uint64_t rev,
           std::string fp)
{
    Guard guard;
    guard.epoch = epoch;
    guard.groupId = g;
    guard.rev = rev;
    guard.fp = std::move(fp);
    return guard;
}

void TestReader()
{
    Guard out;
    std::string extra =
        "{\"player_guid\": 7, \"speaker_groups\": {\"11\": "
        "{\"e\": \"abc\", \"g\": 5, \"rev\": 9, \"fp\": \"ff\"}, "
        "\"12\": {\"e\": \"abc\", \"g\": 0}}}";
    Check(ReadSpeakerGuard(extra, 11, out) == ReadResult::Ok
            && out.epoch == "abc" && out.groupId == 5
            && out.rev == 9 && out.fp == "ff",
        "grouped entry read");
    Check(ReadSpeakerGuard(extra, 12, out) == ReadResult::Ok
            && out.groupId == 0,
        "ungrouped entry read");
    Check(ReadSpeakerGuard(extra, 13, out) == ReadResult::Absent,
        "missing bot is absent");
    Check(ReadSpeakerGuard("{\"x\": 1}", 11, out)
            == ReadResult::Absent,
        "old payload without speaker_groups is absent");
    Check(ReadSpeakerGuard("", 11, out) == ReadResult::Absent,
        "empty extra is absent");
    Check(ReadSpeakerGuard(
            "{\"speaker_groups\": {\"11\": {\"g\": 5}}}", 11, out)
            == ReadResult::Malformed,
        "entry without epoch is malformed");
    Check(ReadSpeakerGuard(
            "{\"speaker_groups\": {\"11\": {\"e\": \"a\", \"g\": 5}}}",
            11, out) == ReadResult::Malformed,
        "grouped entry without rev/fp is malformed");

    std::string compact = "{\"speaker_groups\":{\"11\":"
        + GuardJson(Make("abc", 5, 9, "ff")) + "}}";
    Check(ReadSpeakerGuard(compact, 11, out) == ReadResult::Ok
            && GuardMatches(out, Make("abc", 5, 9, "ff")),
        "GuardJson round-trips");
}

void TestTransitions()
{
    std::string const fp = Fingerprint({{1, 0}, {11, 0}, {12, 0}});
    Guard const queued = Make("e1", 5, 9, fp);

    Check(GuardMatches(queued, Make("e1", 5, 9, fp)),
        "14 unchanged membership delivers");
    Check(!GuardMatches(queued, Make("e1", 0, 0, "")),
        "1 leave drops");
    Check(!GuardMatches(Make("e1", 0, 0, ""), Make("e1", 5, 10, fp)),
        "2 join from ungrouped drops");
    Check(!GuardMatches(queued, Make("e1", 0, 0, "")),
        "3 disband drops");
    // Leave then rejoin the same group: two fresh revisions.
    Check(!GuardMatches(queued, Make("e1", 5, 11, fp)),
        "4 same-group leave and rejoin drops");
    Check(!GuardMatches(queued,
            Make("e1", 5, 10, Fingerprint({{1, 0}, {11, 0}}))),
        "5 another companion leaves drops");
    Check(!GuardMatches(queued, Make("e1", 5, 10,
            Fingerprint({{1, 0}, {11, 0}, {12, 0}, {13, 0}}))),
        "6 another companion joins drops");
    Check(!GuardMatches(queued,
            Make("e1", 5, 9, Fingerprint({{1, 0}, {11, 1}, {12, 0}}))),
        "7 subgroup move drops on fingerprint alone");
    // Restart: new epoch; a restored group observed lazily may
    // even draw the same small revision number.
    Check(!GuardMatches(queued, Make("e2", 5, 9, fp)),
        "8 restart drops even with equal rev");
    Check(!GuardMatches(Make("e1", 0, 0, ""), Make("e2", 0, 0, "")),
        "8 restart drops an ungrouped line");
    Check(!GuardMatches(queued, Make("e1", 5, 12, fp)),
        "9 disband then re-observed id drops");
    Check(GuardMatches(Make("e1", 0, 0, ""), Make("e1", 0, 0, "")),
        "ungrouped stays ungrouped delivers");
}

// Scene E: the guarded bot row (seq 0) is dropped because its group
// changed, so E is closed. The bridge then commits later rows of E
// one by one: an NPC line and an unchanged-group bot line. Neither
// may be spoken, nor a reply continuing E, and delivering must not
// recreate E. Other scenes are untouched.
void TestSceneClosureInterleaving()
{
    using LLMChatterSceneClosure::ClosedScenes;
    using LLMChatterSceneClosure::RowBelongsToClosedScene;

    ClosedScenes closed;
    std::uint32_t const E = 500;
    std::uint32_t const F = 501;
    std::uint32_t const replyEvent = 600;
    std::time_t const retention = 120;

    Check(!RowBelongsToClosedScene(closed, E, 0),
        "open scene rows are spoken (old behaviour)");

    // Group drop of a scene row closes the row's own event scene.
    closed.Close(E, 1000, retention);
    Check(RowBelongsToClosedScene(closed, E, 0),
        "late NPC row of the closed scene is dropped");
    Check(RowBelongsToClosedScene(closed, E, 0),
        "late unchanged-speaker row of the closed scene is dropped");
    Check(closed.IsClosed(E),
        "recording a row of the closed scene is refused");
    Check(RowBelongsToClosedScene(closed, replyEvent, E),
        "a reply continuing the closed scene is dropped");
    Check(!RowBelongsToClosedScene(closed, F, 0),
        "another scene is unaffected");
    Check(!RowBelongsToClosedScene(closed, replyEvent, F),
        "a reply to another scene is unaffected");
    Check(!RowBelongsToClosedScene(closed, 0, 0),
        "rows without an event id are never closed");

    // Group drop of a reply row closes both its own scene and the
    // scene it continued.
    closed.Close(replyEvent, 1010, retention);
    closed.Close(F, 1010, retention);
    Check(RowBelongsToClosedScene(closed, replyEvent, 0)
            && RowBelongsToClosedScene(closed, F, 0),
        "reply drop closes its scene and the continued one");

    // Retention covers the queued-event lifetime, then is forgotten.
    closed.Prune(1000 + retention, retention);
    Check(closed.IsClosed(E), "kept for the whole retention window");
    closed.Prune(1000 + retention + 1, retention);
    Check(!closed.IsClosed(E) && closed.IsClosed(F),
        "pruned after the retention window");
}

void TestFingerprint()
{
    Check(Fingerprint({{1, 0}, {2, 1}}) == Fingerprint({{2, 1}, {1, 0}}),
        "fingerprint ignores slot order");
    Check(Fingerprint({{1, 0}, {2, 1}}) != Fingerprint({{1, 1}, {2, 0}}),
        "fingerprint sees subgroups");
    Check(Fingerprint({}).size() == 16, "fingerprint is 16 hex digits");
}

// The event-row drop marker (any outlet: General, transport,
// guild). Mirrors the delivery order: seq 0 drops for a group change,
// the marker is written on the event, then the bridge commits seq 1
// for an unchanged speaker (a follow-up generated meanwhile).
void TestGroupDropMarkerInterleaving()
{
    using LLMChatterGroupGuard::RowFollowsGroupDrop;
    std::string const before =
        "{\"bot_guids\": [11, 12], \"speaker_groups\": "
        "{\"11\": {\"e\": \"e1\", \"g\": 5, \"rev\": 9, "
        "\"fp\": \"x\"}, \"12\": {\"e\": \"e1\", \"g\": 0}}}";
    Check(!RowFollowsGroupDrop(before, 0)
        && !RowFollowsGroupDrop(before, 1),
        "no marker: every row is judged on its own guard");

    // JSON_SET adds the key; MySQL re-serialises with spaces.
    std::string const after =
        "{\"bot_guids\": [11, 12], \"group_drop_seq\": 0, "
        "\"speaker_groups\": {\"11\": {\"e\": \"e1\", \"g\": 5, "
        "\"rev\": 9, \"fp\": \"x\"}, \"12\": {\"e\": \"e1\", "
        "\"g\": 0}}}";
    Check(!RowFollowsGroupDrop(after, 0),
        "the dropped row itself is not re-judged");
    Check(RowFollowsGroupDrop(after, 1),
        "late follow-up of an unchanged speaker is dropped");
    Check(RowFollowsGroupDrop(after, 4),
        "late extended turn is dropped");

    std::string const midway = "{\"group_drop_seq\": 2}";
    Check(!RowFollowsGroupDrop(midway, 1)
        && !RowFollowsGroupDrop(midway, 2)
        && RowFollowsGroupDrop(midway, 3),
        "earlier, already heard lines are unaffected");

    Check(!RowFollowsGroupDrop("", 3), "empty extra_data");
    Check(!RowFollowsGroupDrop("{\"group_drop_seq\": \"x\"}", 3),
        "non-numeric marker ignored");
    Check(!RowFollowsGroupDrop(
            "{\"player_message\": \"\\\"group_drop_seq\\\": 0\"}", 3),
        "marker text inside a string value is not a marker");
    Check(!RowFollowsGroupDrop(
            "{\"a\": {\"group_drop_seq\": 0}}", 3),
        "only a top-level marker counts");
}

} // namespace

int main()
{
    TestReader();
    TestTransitions();
    TestSceneClosureInterleaving();
    TestGroupDropMarkerInterleaving();
    TestFingerprint();
    if (failures)
    {
        std::printf("%d group guard check(s) failed\n", failures);
        return 1;
    }
    std::printf("group guard checks passed\n");
    return 0;
}
