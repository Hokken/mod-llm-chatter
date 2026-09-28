#!/usr/bin/env python3
"""Regression checks for proximity duel/PvP onlooker scenes.

Run directly from the module root:
  python tools/tests/test_proximity_fight_scene.py
"""

import re
import sys
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
TOOLS_DIR = MODULE_DIR / "tools"
SRC = MODULE_DIR / "src"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_proximity  # noqa: E402
from chatter_proximity import _fight_topic  # noqa: E402

BOT_LABEL = re.compile(r"\b(bot|npc)\b", re.IGNORECASE)


def fighter(name, is_player=False):
    return {
        "name": name, "race": 1, "class": 1, "level": 40,
        "faction": "Alliance", "is_player": is_player,
    }


def duel_extra(moment, **scene):
    data = {
        "kind": "duel",
        "moment": moment,
        "fighters": [fighter("Varian"), fighter("Jaina")],
    }
    data.update(scene)
    return {"fight_kind": "duel", "fight_scene": data}


def strip_rule(text):
    return text.replace(
        "never as a bot or NPC", "")


def fight_src():
    return (SRC / "LLMChatterProximityFight.cpp").read_text(
        encoding="utf-8")


# ---------------------------------------------------------
# Python topic seeds
# ---------------------------------------------------------

def test_non_fight_events_have_no_fight_topic():
    assert _fight_topic({}, "normal") is None
    assert _fight_topic({"fight_scene": "x"}, "normal") is None


def test_duel_moments():
    before = _fight_topic(duel_extra("before"), "normal")
    assert "about to duel" in before
    assert "Varian" in before and "Jaina" in before
    during = _fight_topic(duel_extra("during"), "roleplay")
    assert "underway" in during
    for text in (before, during):
        assert "nobody dies" in text
        assert not BOT_LABEL.search(strip_rule(text)), text


def test_duel_outcomes():
    won = _fight_topic(duel_extra(
        "after", outcome="won",
        winner_name="Varian", loser_name="Jaina"), "normal")
    assert "Varian just won the duel nearby against Jaina" in won
    fled = _fight_topic(duel_extra(
        "after", outcome="fled",
        winner_name="Varian", loser_name="Jaina"), "normal")
    assert "left the duel area" in fled
    interrupted = _fight_topic(duel_extra(
        "after", outcome="interrupted"), "normal")
    assert "without a clear result" in interrupted


def test_hidden_fighter_not_named():
    """C++ omits a fighter the speakers cannot perceive and
    leaves its winner/loser name empty."""
    extra = duel_extra(
        "after", outcome="won", winner_name="Varian",
        loser_name="")
    extra["fight_scene"]["fighters"] = [fighter("Varian")]
    text = _fight_topic(extra, "normal")
    assert "Varian" in text
    assert "Jaina" not in text


def test_player_fighter_may_be_addressed():
    extra = duel_extra("during")
    extra["fight_scene"]["fighters"][0]["is_player"] = True
    text = _fight_topic(extra, "normal")
    assert "Varian is the real player" in text


def test_pvp_kill_sides():
    base = {
        "kind": "pvp", "moment": "kill",
        "fighters": [fighter("Garrosh"), fighter("Varian")],
        "victor_name": "Garrosh", "fallen_name": "Varian",
    }
    won = _fight_topic({"fight_scene": dict(
        base, onlooker_side_won=True)}, "normal")
    assert "Garrosh just killed Varian" in won
    assert "Your side won" in won
    lost = _fight_topic({"fight_scene": dict(
        base, onlooker_side_won=False)}, "normal")
    assert "Your side lost" in lost
    assert "no slurs" in lost


def test_generate_single_line_prefers_fight_topic():
    source = Path(chatter_proximity.__file__).read_text(
        encoding="utf-8")
    assert re.search(
        r"topic\s*\n\s*or _fight_topic\(extra, get_chatter_mode"
        r"\(config or \{\}\)\)", source)
    assert re.search(
        r"fight_topic = _fight_topic\(extra, mode\)\s*"
        r"if fight_topic:\s*topic = fight_topic", source)


# ---------------------------------------------------------
# C++ source guards for the reviewed rules
# ---------------------------------------------------------

def test_rematch_replaces_instance_and_stale_ids_fail():
    src = fight_src()
    assert "duel.id = _nextDuelInstanceId++;" in src
    assert re.search(
        r"_duels\[PairKey\(\s*duel\.challengerGuid, "
        r"duel\.targetGuid\)\] = duel;", src)
    assert re.search(
        r"it->second\.id != instanceId\)\s*return false;", src)


def test_started_duel_rule_and_phase_checks():
    src = fight_src()
    assert re.search(
        r"loser->duel->StartTime != 0\s*"
        r"&& now >= loser->duel->StartTime", src)
    assert re.search(
        r"case MOMENT_BEFORE:\s*return duel\.phase == "
        r"DuelPhase::Challenged\s*&& \(state == "
        r"DUEL_STATE_CHALLENGED\s*\|\| state == "
        r"DUEL_STATE_COUNTDOWN\);", src)
    assert re.search(
        r"case MOMENT_DURING:\s*return duel\.phase == "
        r"DuelPhase::InProgress\s*&& state == "
        r"DUEL_STATE_IN_PROGRESS;", src)
    assert re.search(
        r"case MOMENT_AFTER:\s*return duel\.phase == "
        r"DuelPhase::Completed\s*&& duel\.started", src)


def test_live_duels_never_age_out():
    src = fight_src()
    retire = re.search(
        r"if \(duel\.phase == DuelPhase::Completed\s*"
        r"&& allDone && !pendingEmote\s*"
        r"&& now - duel\.completedAt >= retention\)", src)
    assert retire, "retirement must require completion"
    assert "requestedAt >=" not in src
    assert "now - duel.requestedAt" not in src


def test_one_reaction_per_moment():
    src = fight_src()
    body = re.search(
        r"void FireFightScene\((.*?)\n\}", src, re.S).group(1)
    # Speech returns before any emote scheduling.
    assert re.search(
        r"if \(useSpeech\)\s*\{\s*QueueProximityFightSpeech\("
        r".*?\);\s*return;\s*\}", body, re.S)
    assert body.count("ScheduleEmotes(") == 1
    # Conversations use 2-3 bots from one pool.
    assert "std::min<size_t>(pool.size(), urand(2, 3))" in src


def test_moment_probabilities_from_config():
    src = fight_src()
    assert re.search(
        r"_proxFightSecondMomentChance\)\s*\{\s*selected \|= "
        r"pool\[1\];\s*if \(urand\(1, 100\)\s*<= "
        r"sLLMChatterConfig\s*->_proxFightThirdMomentChance\)",
        src)


def prox_src():
    return (SRC / "LLMChatterProximity.cpp").read_text(
        encoding="utf-8")


def test_single_onlooker_policy_for_both_pools():
    """One policy covers both transports: fighters and the
    anchor's group are excluded for speech AND emotes."""
    body = re.search(
        r"bool IsProximityFightOnlookerEligible\((.*?)\n\}",
        prox_src(), re.S).group(1)
    assert "IsEligibleProximityBotAnyTeam(" in body
    assert "if (sameTeam != speech)" in body
    assert "IsProximityFightFighter(bot, fighters)" in body
    assert "IsSameGroup(bot, anchor->GetGroup())" in body
    assert "IsUnitPerceivableBy(anchor, bot)" in body
    assert re.search(
        r"speech\s*\? std::all_of\(.*?\)\s*: std::any_of\(",
        body, re.S)
    collect = re.search(
        r"void CollectProximityFightOnlookers\((.*?)\n\}",
        prox_src(), re.S).group(1)
    assert collect.count("IsProximityFightOnlookerEligible(") == 2


def test_cooldown_filtered_before_shape():
    collect = re.search(
        r"void CollectProximityFightOnlookers\((.*?)\n\}",
        prox_src(), re.S).group(1)
    # Off-cooldown filtering happens during collection, i.e.
    # before ChooseRoster() picks statement vs conversation.
    assert re.search(
        r"if \(IsProximityFightBotOnCooldown\(anchor, bot\)\)"
        r"\s*continue;", collect)
    body = re.search(
        r"bool IsProximityFightBotOnCooldown\((.*?)\n\}",
        prox_src(), re.S).group(1)
    assert "_entityCooldowns" in body
    assert "_proxChatterEntityCooldown" in body
    emotes = re.search(
        r"void ScheduleEmotes\((.*?)\n\}", fight_src(), re.S
    ).group(1)
    # All-or-nothing: every roster member is scheduled and
    # all cooldowns are marked together.
    assert "TryReserve" not in emotes
    assert "continue;" not in emotes
    assert "MarkProximityFightBotCooldowns(anchor, roster);" in (
        emotes
    )
    assert '"fight:"' not in prox_src()


def test_delayed_emotes_reapply_policy():
    body = re.search(
        r"void ProcessEmotesLocked\((.*?)\n\}", fight_src(), re.S
    ).group(1)
    assert "IsProximityFightAnchorEligible(" in body
    assert "IsProximityAnchorEligible(anchor)" in body
    assert re.search(
        r"IsProximityFightOnlookerEligible\(\s*anchor, bot, "
        r"fighters, false\)", body)
    assert "FindPlayerByCounter(step.botGuid)" in body


def test_core_rng_and_config_tunables():
    src = fight_src()
    assert "<random>" not in src
    assert "std::mt19937" not in src
    assert "std::shuffle" not in src
    assert "Acore::Containers::RandomShuffle(" in src
    assert "_proxFightSceneCellYards" in src
    world = (SRC / "LLMChatterWorld.cpp").read_text(
        encoding="utf-8")
    # Driven by the existing delivery poll; no new interval.
    assert re.search(
        r"DeliverPendingMessages\(\);.*?"
        r"ProcessPendingFightMoments\(\);", world, re.S)
    assert "_lastFightMomentTime" not in world


def test_fight_anchor_combat_rule():
    prox = (SRC / "LLMChatterProximity.cpp").read_text(
        encoding="utf-8")
    body = re.search(
        r"bool IsProximityFightAnchorEligible\((.*?)\n\}",
        prox, re.S).group(1)
    assert "GetPvECombatRefs().empty()" in body
    assert "GetPvPCombatRefs()" in body
    assert "!= opponentGuid" in body


def test_delivery_fight_guards():
    delivery = (SRC / "LLMChatterDelivery.cpp").read_text(
        encoding="utf-8")
    assert re.search(
        r'bool fightRow =\s*HasNonEmptyJsonString\('
        r'eventExtraData, "fight_kind"\);', delivery)
    assert re.search(
        r'if \(ownerSubsystem != "proximity"\s*'
        r'\|\| channel != "say"\)', delivery)
    assert '"fight_scene_channel"' in delivery
    assert re.search(
        r"if \(!IsProximityFightLineStillValid\("
        r"eventExtraData\)\)", delivery)
    assert '"fight_scene_stale"' in delivery
    assert re.search(
        r"bool anchorEligible = fightOpponentGuid\s*"
        r"\? IsProximityFightAnchorEligible\(", delivery)


def main() -> int:
    test_non_fight_events_have_no_fight_topic()
    test_duel_moments()
    test_duel_outcomes()
    test_hidden_fighter_not_named()
    test_player_fighter_may_be_addressed()
    test_pvp_kill_sides()
    test_generate_single_line_prefers_fight_topic()
    test_rematch_replaces_instance_and_stale_ids_fail()
    test_started_duel_rule_and_phase_checks()
    test_live_duels_never_age_out()
    test_one_reaction_per_moment()
    test_moment_probabilities_from_config()
    test_single_onlooker_policy_for_both_pools()
    test_cooldown_filtered_before_shape()
    test_delayed_emotes_reapply_policy()
    test_core_rng_and_config_tunables()
    test_fight_anchor_combat_rule()
    test_delivery_fight_guards()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
