#!/usr/bin/env python3
"""Build and run the standalone C++ test for
src/LLMChatterGroupGuard.h (the speaker group guard checked at
delivery, issue #94), plus static wiring checks.

The C++ test is standard-library only and separate from the
server build. It needs a host C++ compiler (`CXX`, `c++`,
`g++`, or `clang++`); without one it is skipped and says so.

Run directly from the module root:
  python tools/tests/test_group_guard_cpp.py
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
SOURCE = MODULE_DIR / "tools" / "tests" / "cpp" / "test_group_guard.cpp"
INCLUDE = MODULE_DIR / "src"


def _src(name):
    return (INCLUDE / name).read_text(encoding="utf-8")


def find_compiler():
    candidates = [os.environ.get("CXX"), "c++", "g++", "clang++"]
    for name in candidates:
        if name and shutil.which(name):
            return shutil.which(name)
    return None


def test_bookkeeping_runs_before_hook_gates():
    """Membership bookkeeping is the first statement of each group
    hook, before the IsEnabled/_useGroupChatter/bot/real-player
    gates, so bot-only groups and disabled party chatter still
    invalidate queued lines."""
    join = _src("LLMChatterGroupJoin.cpp")
    for hook, call in (
        ("void OnAddMember(", "NoteGroupMemberAdded(group, guid);"),
        ("void OnRemoveMember(", "NoteGroupMemberRemoved(group, guid);"),
        ("void OnDisband(", "NoteGroupDisbanded(group);"),
    ):
        body = join.split(hook, 1)[1]
        body = body.split("{", 1)[1]
        first = [line.strip() for line in body.splitlines()
                 if line.strip() and not line.strip().startswith("//")]
        assert first[0] == call, (hook, first[0])


def test_delivery_wires_guard_cascade_and_scene_closure():
    delivery = _src("LLMChatterDelivery.cpp")
    assert "SpeakerGroupDropReason(eventExtraData, botGuid, bot)" \
        in delivery
    assert '"scene_closed"' in delivery
    assert "CloseProximityScene(" in delivery
    # Every proximity row (not only replies) checks its scene.
    assert ('ownerSubsystem == "proximity"\n'
            '        && IsProximityRowInClosedScene(eventId, originSceneId)'
            in delivery)
    assert "IsProximitySceneClosed" not in delivery
    assert "cancelled_after_group_drop" in delivery
    finalize = delivery.split("void FinalizeDroppedMessage(", 1)[1]
    finalize = finalize.split("\n}\n", 1)[0]
    assert "groupDrop" in finalize
    # Hold release and facing reset stay on the shared cascade path.
    assert "ReleaseBotReplyHold(" in finalize
    assert "ScheduleSceneFacingResets(" in finalize


def test_group_drop_marker_stops_late_rows_of_any_event():
    delivery = _src("LLMChatterDelivery.cpp")
    finalize = delivery.split("void FinalizeDroppedMessage(", 1)[1]
    finalize = finalize.split("\n}\n", 1)[0]
    # A late row's own drop counts as a group drop (cascade again).
    assert '"cancelled_after_group_drop");' in finalize
    # The marker is written before the cancel of already-queued rows,
    # so a row committed in between is caught at its delivery.
    marker = finalize.index("UPDATE llm_chatter_events")
    cancel = finalize.index("WHERE event_id = {} AND sequence > {} ")
    assert marker < cancel
    assert "JSON_SET(extra_data" in finalize
    assert "LEAST(" in finalize
    assert "kGroupDropSeqKey" in finalize
    # The check covers every subsystem (not gated on proximity) and
    # runs before the speaker guard.
    check = delivery.index(
        "LLMChatterGroupGuard::RowFollowsGroupDrop(\n"
        "            eventExtraData, sequence)")
    condition = delivery[:check].rsplit("\n", 1)[1]
    assert condition.strip() == "if (eventId &&", condition
    assert check < delivery.index(
        "SpeakerGroupDropReason(eventExtraData, botGuid, bot)")
    guard = _src("LLMChatterGroupGuard.h")
    assert 'kGroupDropSeqKey = "group_drop_seq"' in guard


def test_general_guards_cover_every_eligible_speaker():
    player = _src("LLMChatterPlayer.cpp")
    assert ("AppendCandidateGroups(extraData,\n"
            "            CollectGeneralGuardBots(zoneId, "
            "player->GetTeamId()));") in player
    collect = player.split("CollectGeneralGuardBots(\n", 1)[1]
    collect = collect.split("\n}\n", 1)[0]
    # Uncapped, both bot sources, same filters as the reply sample.
    assert "_maxBotsPerZone" not in collect
    assert "GetAllSessions()" in collect
    assert "GetAllBots()" in collect
    for gate in ("IsPlayerBot(bot)", "GetZoneId() != zoneId",
                 "GetTeamId() != teamId", "CanSpeakInGeneralChannel(bot)"):
        assert gate in collect, gate


def test_every_proximity_payload_carries_guard():
    prox = _src("LLMChatterProximity.cpp")
    base = prox.split("std::string BuildBaseEventJson(", 1)[1]
    base = base.split("\n}\n", 1)[0]
    assert "BuildSpeakerGroupsField(SpeakerBots(speakers))" in base
    assert '\\"responder_group\\":' in prox
    assert "BuildSpeakerGroupJson(bot)" in prox
    record = prox.split("void RecordDeliveredProximityLine(", 1)[1]
    record = record.split("\n}\n", 1)[0]
    assert "_closedScenes.IsClosed(eventId)" in record


def test_awareness_uses_core_random():
    awareness = _src("LLMChatterGroupAwareness.cpp")
    assert "#include <random>" not in awareness
    assert "random_device" not in awareness
    assert "rand32()" in awareness
    assert re.search(r"_groupRev\[groupId\] = \+\+_nextRev", awareness)


def run_cpp_test() -> bool:
    compiler = find_compiler()
    if not compiler:
        print("SKIP: no host C++ compiler; C++ guard test not run")
        return True
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "test_group_guard"
        build = subprocess.run(
            [compiler, "-std=c++17", "-Wall", "-Wextra",
             "-I", str(INCLUDE), str(SOURCE), "-o", str(exe)],
            capture_output=True, text=True,
        )
        if build.returncode != 0:
            print(build.stdout + build.stderr)
            return False
        run = subprocess.run(
            [str(exe)], capture_output=True, text=True)
        print(run.stdout.strip())
        return run.returncode == 0


def main() -> int:
    test_bookkeeping_runs_before_hook_gates()
    test_delivery_wires_guard_cascade_and_scene_closure()
    test_every_proximity_payload_carries_guard()
    test_group_drop_marker_stops_late_rows_of_any_event()
    test_general_guards_cover_every_eligible_speaker()
    test_awareness_uses_core_random()
    ok = run_cpp_test()
    if ok:
        print("OK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
