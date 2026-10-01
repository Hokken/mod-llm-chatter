#!/usr/bin/env python3
"""Regression checks for duel events and prompts.

Run directly from the module root:
  python tools/tests/test_duel_events.py
"""

import re
import sys
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
TOOLS_DIR = MODULE_DIR / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_duel  # noqa: E402
from chatter_event_registry import (  # noqa: E402
    EVENT_REGISTRY,
    build_handler_map,
)


BOT = {
    "name": "Varian",
    "class": "Warrior",
    "race": "Human",
    "level": 40,
    "gender": "male",
}
TRAITS = ["proud", "competitive", "loyal"]
BOT_LABEL = re.compile(r"\b(bot|npc)\b", re.IGNORECASE)
BASE_SQL = (
    MODULE_DIR / "data" / "sql" / "characters" / "base"
    / "00000000_llm_chatter_tables.sql"
)
MIGRATION_SQL = (
    MODULE_DIR / "data" / "sql" / "characters" / "updates"
    / "20260926_duel_events.sql"
)


def duellist(prefix, guid, name, **extra):
    data = {
        f"{prefix}_guid": guid,
        f"{prefix}_name": name,
        f"{prefix}_race": 1,
        f"{prefix}_class": 1,
        f"{prefix}_level": 40,
        f"{prefix}_in_group": True,
        f"{prefix}_is_real_player": False,
    }
    data.update({f"{prefix}_{k}": v for k, v in extra.items()})
    return data


def test_registry_routes_duel_events():
    handlers = build_handler_map()
    assert (handlers["bot_group_duel_start"]
            is chatter_duel.process_duel_start_event)
    assert (handlers["bot_group_duel_end"]
            is chatter_duel.process_duel_end_event)
    assert EVENT_REGISTRY["bot_group_duel_end"].priority == "high"


def test_schema_contains_duel_events():
    for path in (BASE_SQL, MIGRATION_SQL):
        text = path.read_text(encoding="utf-8")
        assert "'bot_group_duel_start'" in text, path
        assert "'bot_group_duel_end'" in text, path


def test_start_prompt_as_duellist():
    data = {"bot_guid": 10, "reactor_role": "duellist",
            "initiator_name": "Jaina"}
    data.update(duellist("duellist_a", 10, "Varian"))
    data.update(duellist(
        "duellist_b", 20, "Jaina", is_real_player=True))
    prompt = chatter_duel.build_duel_start_prompt(
        BOT, TRAITS, data, "normal")
    assert "You just started a duel against Jaina" in prompt
    assert "the real player in your party" in prompt
    assert "Jaina issued the challenge" in prompt
    assert "nobody dies" in prompt
    assert not BOT_LABEL.search(prompt), prompt


def test_start_prompt_as_spectator_outsider():
    data = {"bot_guid": 30, "reactor_role": "spectator"}
    data.update(duellist("duellist_a", 20, "Jaina",
                         is_real_player=True))
    data.update(duellist("duellist_b", 99, "Garrosh",
                         in_group=False))
    prompt = chatter_duel.build_duel_start_prompt(
        BOT, TRAITS, data, "roleplay")
    assert "You are watching" in prompt
    assert "from outside your party" in prompt
    assert not BOT_LABEL.search(prompt), prompt


def test_end_prompt_roles_and_outcomes():
    base = {"bot_guid": 10}
    base.update(duellist("winner", 10, "Varian"))
    base.update(duellist("loser", 20, "Jaina"))

    won = dict(base, reactor_role="winner", outcome="won")
    assert "You just won a duel against Jaina" in (
        chatter_duel.build_duel_end_prompt(
            BOT, TRAITS, won, "normal"))

    fled = dict(base, reactor_role="winner", outcome="fled")
    assert "fled the duel area" in (
        chatter_duel.build_duel_end_prompt(
            BOT, TRAITS, fled, "normal"))

    lost = {"bot_guid": 20, "reactor_role": "loser",
            "outcome": "won"}
    lost.update(duellist("winner", 10, "Varian"))
    lost.update(duellist("loser", 20, "Jaina"))
    assert "You just lost a duel to Varian" in (
        chatter_duel.build_duel_end_prompt(
            BOT, TRAITS, lost, "normal"))

    watched = dict(base, bot_guid=30,
                   reactor_role="spectator", outcome="won")
    prompt = chatter_duel.build_duel_end_prompt(
        BOT, TRAITS, watched, "normal")
    assert "You watched a duel" in prompt
    assert "Varian" in prompt and "Jaina" in prompt

    interrupted = dict(base, bot_guid=30,
                       reactor_role="spectator",
                       outcome="interrupted")
    assert "interrupted" in chatter_duel.build_duel_end_prompt(
        BOT, TRAITS, interrupted, "normal")


def test_hidden_outsider_is_not_identified():
    """A spectator sees its party member, but the
    outside opponent is stealthed: C++ omits the
    outsider's identity and Python must not invent one.
    """
    data = {"bot_guid": 30, "reactor_role": "spectator",
            "outcome": "won"}
    data.update(duellist("winner", 20, "Jaina",
                         is_real_player=True,
                         identity_known=True))
    data.update({
        "loser_guid": 99,
        "loser_in_group": False,
        "loser_is_real_player": False,
        "loser_identity_known": False,
    })
    prompt = chatter_duel.build_duel_end_prompt(
        BOT, TRAITS, data, "normal")
    assert "Jaina" in prompt
    assert "cannot see clearly" in prompt
    assert "someone (" not in prompt


def test_cpp_duel_guards():
    src = (MODULE_DIR / "src" / "LLMChatterDuel.cpp").read_text(
        encoding="utf-8")
    # Declined/unaccepted (StartTime 0) and countdown
    # cancellations never produce an end reaction.
    assert re.search(
        r"!loser->duel\s*\|\|\s*loser->duel->StartTime == 0"
        r"\s*\|\|\s*time\(nullptr\) < loser->duel->StartTime",
        src,
    )
    # Each duellist identity is gated per reactor.
    assert "IsDuellistKnownTo(reactor, duellist, group)" in src
    assert "IsDuellistKnownTo(reactor, initiator, group)" in src


def main() -> int:
    test_registry_routes_duel_events()
    test_schema_contains_duel_events()
    test_start_prompt_as_duellist()
    test_start_prompt_as_spectator_outsider()
    test_end_prompt_roles_and_outcomes()
    test_hidden_outsider_is_not_identified()
    test_cpp_duel_guards()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
