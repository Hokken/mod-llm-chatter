#!/usr/bin/env python3
"""Build and run the standalone C++ test for
src/LLMChatterBotSource.h (General/Guild speaker sourcing, issue
#98), plus static wiring checks.

The C++ test is standard-library only and separate from the
server build. It needs a host C++ compiler (`CXX`, `c++`,
`g++`, or `clang++`); without one it is skipped and says so.
The static checks read the source; they do not prove that the
server compiles.

Run directly from the module root:
  python tools/tests/test_bot_source_cpp.py
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
SOURCE = MODULE_DIR / "tools" / "tests" / "cpp" / "test_bot_source.cpp"
INCLUDE = MODULE_DIR / "src"
CONF = MODULE_DIR / "conf" / "mod_llm_chatter.conf.dist"


def _src(name):
    return (INCLUDE / name).read_text(encoding="utf-8")


def _body(text, signature, end="\n}\n"):
    """Text of the function that starts at `signature`."""
    assert signature in text, signature
    return text.split(signature, 1)[1].split(end, 1)[0]


def find_compiler():
    candidates = [os.environ.get("CXX"), "c++", "g++", "clang++"]
    for name in candidates:
        if name and shutil.which(name):
            return shutil.which(name)
    return None


def test_only_the_shared_source_reads_the_random_registry():
    for path in sorted(INCLUDE.glob("*.cpp")):
        if path.name == "LLMChatterShared.cpp":
            continue
        assert "GetAllBots()" not in path.read_text(
            encoding="utf-8"), path.name


def test_chatter_bots_merge_random_and_alt_registries():
    body = _body(_src("LLMChatterShared.cpp"),
                 "std::vector<Player*> GetChatterBots()\n")
    assert "sRandomPlayerbotMgr.GetAllBots()" in body
    assert "_altBotsEnable" in body
    assert "GetAllSessions()" in body
    assert "IsPlayerBot(owner)" in body
    assert "GET_PLAYERBOT_MGR(owner)" in body
    assert "IsPlayerBot(it->second)" in body
    assert body.count("AppendUniqueBot(") == 2


def test_speaker_rule_uses_the_pure_policy():
    body = _body(_src("LLMChatterShared.cpp"),
                 "bool IsChatterSpeakerAllowed(")
    assert "ClassifySpeaker(" in body
    assert "IsPlayerBot(bot)" in body
    assert "sRandomPlayerbotMgr.IsRandomBot(bot)" in body
    assert "_altBotsEnable" in body


def test_selection_paths_use_chatter_bots():
    paths = (
        ("LLMChatterAmbient.cpp",
         "static std::vector<Player*> GetBotsInZone(", "\n}\n"),
        ("LLMChatterPlayer.cpp",
         "static std::vector<Player*> CollectGeneralGuardBots(", "\n}\n"),
        ("LLMChatterWorld.cpp",
         "std::vector<Player*> GetTransportBotsInZone(", "\n    }\n"),
        ("LLMChatterShared.cpp", "Player* FindNearbyDefenderBot(", "\n}\n"),
        ("LLMChatterGuild.cpp",
         "std::vector<Player*> GetEligibleGuildBots(", "\n}\n"),
    )
    for name, signature, end in paths:
        assert "GetChatterBots()" in _body(_src(name), signature, end), name
    # The General reply sample and guild idle chatter sit inside larger
    # functions; the file-wide GetAllBots() check covers them.
    assert _src("LLMChatterPlayer.cpp").count("GetChatterBots()") == 2
    world = _src("LLMChatterWorld.cpp")
    assert world.count("GetChatterBots()") == 2
    assert "byGuild[guildId].push_back(bot);" in world


def test_general_reply_samples_the_whole_pool():
    """The capped reply sample is drawn from every eligible bot, not
    from whichever registry comes first (issue #98 review)."""
    player = _src("LLMChatterPlayer.cpp")
    start = player.index("std::vector<Player*> zoneBots;")
    end = player.index("if (zoneBots.empty())", start)
    sample = player[start:end]
    assert "GetChatterBots()" in sample
    assert "GetAllSessions()" in sample
    assert "AppendUniqueBot(" in sample
    assert sample.count("_maxBotsPerZone") == 1  # only in SampleBots
    assert "break;" not in sample
    sampled = sample.index("SampleBots(")
    assert sampled > sample.index("for (Player* bot : GetChatterBots())")
    assert sampled < sample.index("CanSpeakInGeneralChannel(b)")


def test_grouped_rules_are_unchanged_per_path():
    ambient = _body(_src("LLMChatterAmbient.cpp"),
                    "static std::vector<Player*> GetBotsInZone(")
    assert "!IsGroupedWithRealPlayer(player)" in ambient
    transport = _body(_src("LLMChatterWorld.cpp"),
                      "std::vector<Player*> GetTransportBotsInZone(",
                      "\n    }\n")
    assert "IsGroupedWithRealPlayer" not in transport
    loot = _body(_src("LLMChatterLoot.cpp"), "void QueueFinalizedLoot(")
    assert "IsChatterSpeakerAllowed(bot)" in loot
    assert "IsGroupedWithRealPlayer(bot)" in loot
    guild = _body(_src("LLMChatterGuild.cpp"),
                  "std::vector<Player*> GetEligibleGuildBots(")
    assert "IsGroupedWithRealPlayer" not in guild


def test_delivery_rechecks_general_and_guild_speakers_only():
    delivery = _src("LLMChatterDelivery.cpp")
    assert delivery.count("IsChatterSpeakerAllowed(") == 1
    guard = delivery.split("char const* speakerDrop = nullptr;", 1)[1]
    guard = guard.split("\n    }\n", 1)[0]
    assert '(channel == "general" || channel == "guild")' in guard
    assert "IsChatterSpeakerAllowed(bot, &speakerDrop)" in guard
    assert "botUnavailable = true;" in guard
    assert "dropReason = speakerDrop;" in guard
    for other in ("party", "raid", "say", "yell"):
        assert f'"{other}"' not in guard, other


def test_config_key_is_loaded_and_documented():
    assert '"LLMChatter.AltBots.Enable", true' in _src(
        "LLMChatterConfig.cpp")
    assert "bool _altBotsEnable;" in _src("LLMChatterConfig.h")
    assert "LLMChatter.AltBots.Enable = 1" in CONF.read_text(
        encoding="utf-8")


def run_cpp_test() -> bool:
    compiler = find_compiler()
    if not compiler:
        print("SKIP: no host C++ compiler; C++ bot source test not run")
        return True
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "test_bot_source"
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
    test_only_the_shared_source_reads_the_random_registry()
    test_chatter_bots_merge_random_and_alt_registries()
    test_speaker_rule_uses_the_pure_policy()
    test_selection_paths_use_chatter_bots()
    test_general_reply_samples_the_whole_pool()
    test_grouped_rules_are_unchanged_per_path()
    test_delivery_rechecks_general_and_guild_speakers_only()
    test_config_key_is_loaded_and_documented()
    ok = run_cpp_test()
    if ok:
        print("OK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
