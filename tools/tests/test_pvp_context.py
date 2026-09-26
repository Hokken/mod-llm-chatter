#!/usr/bin/env python3
"""Regression checks for overworld PvP prompt context.

Run directly from the module root:
  python tools/tests/test_pvp_context.py
"""

import re
import sys
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
TOOLS_DIR = MODULE_DIR / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_shared  # noqa: E402
from chatter_shared import (  # noqa: E402
    build_bot_state_context,
    build_pvp_enemy_context,
    is_pvp_enemy,
    is_pvp_identity_known,
)
from chatter_group_prompts import (  # noqa: E402
    build_aggro_loss_callout_prompt,
    build_combat_reaction_prompt,
    build_death_reaction_prompt,
    build_kill_reaction_prompt,
    build_spell_cast_reaction_prompt,
)


BOT = {
    "name": "Thrall",
    "class": "Shaman",
    "race": "Orc",
    "level": 40,
    "gender": "male",
}
TRAITS = ["brave", "blunt", "loyal"]
FORBIDDEN_LABELS = re.compile(r"\b(bot|npc|monster)\b", re.IGNORECASE)


def known_enemy(**overrides):
    data = {
        "enemy_kind": "player",
        "enemy_identity_known": True,
        "enemy_guid": 42,
        "enemy_name": "Shadowfang",
        "enemy_race": 5,       # Undead
        "enemy_class": 4,      # Rogue
        "enemy_gender": 0,
        "enemy_level": 40,
        "enemy_faction": "Horde",
        "enemy_is_bot": True,
        "level_gap": 0,
        "is_gray_kill": False,
        "via_pet": False,
        "initiator": "enemy",
        "bot_state": {"role": "dps", "target": "Shadowfang"},
    }
    data.update(overrides)
    return data


def anonymous_enemy(**overrides):
    # C++ BuildBotStateJson omits a target the bot cannot
    # perceive, so an anonymous enemy never appears there.
    data = {
        "enemy_kind": "player",
        "enemy_identity_known": False,
        "via_pet": False,
        "initiator": "unknown",
        "bot_state": {"role": "dps"},
    }
    data.update(overrides)
    return data


def strip_rules_about_labels(text):
    """The guidance itself names the forbidden labels;
    drop that one sentence before scanning."""
    return text.replace(
        "Never call them a bot, NPC, mob, or monster.", "")


def test_detection_helpers():
    assert not is_pvp_enemy(None)
    assert not is_pvp_enemy({"creature_name": "Hogger"})
    assert is_pvp_enemy(known_enemy())
    assert is_pvp_identity_known(known_enemy())
    assert not is_pvp_identity_known(anonymous_enemy())
    # Tolerate string/int booleans from payloads.
    assert is_pvp_identity_known(
        known_enemy(enemy_identity_known="true"))
    assert not is_pvp_identity_known(
        known_enemy(enemy_identity_known=0))


def test_known_enemy_renders_identity():
    ctx = build_pvp_enemy_context(known_enemy(), "normal")
    assert "Shadowfang" in ctx
    assert "Undead" in ctx and "Rogue" in ctx
    assert "level 40" in ctx
    assert "Horde" in ctx
    assert "attacked your group first" in ctx
    assert "no slurs" in ctx
    assert not FORBIDDEN_LABELS.search(
        strip_rules_about_labels(ctx)), ctx


def test_enemy_is_bot_never_rendered():
    for mode in ("normal", "roleplay"):
        ctx = build_pvp_enemy_context(
            known_enemy(enemy_is_bot=True), mode)
        assert "enemy_is_bot" not in ctx
        assert not FORBIDDEN_LABELS.search(
            strip_rules_about_labels(ctx)), ctx


def test_level_gap_tiers():
    gray = build_pvp_enemy_context(
        known_enemy(is_gray_kill=True, level_gap=-15))
    assert "earns no honour" in gray
    skull = build_pvp_enemy_context(known_enemy(level_gap=12))
    assert "very dangerous" in skull
    higher = build_pvp_enemy_context(known_enemy(level_gap=5))
    assert "higher level" in higher
    lower = build_pvp_enemy_context(known_enemy(level_gap=-5))
    assert "lower level" in lower
    even = build_pvp_enemy_context(known_enemy(level_gap=1))
    assert "even match" in even


def test_anonymous_enemy_has_no_identity():
    data = anonymous_enemy()
    ctx = build_pvp_enemy_context(data, "normal")
    assert "unseen" in ctx
    assert "do not name" in ctx
    for leaked in ("Shadowfang", "Undead", "Rogue", "level 40"):
        assert leaked not in ctx, leaked

    state = build_bot_state_context(data, "normal")
    assert "Shadowfang" not in state, state
    assert "currently fighting" not in state, state


def test_visible_pet_with_hidden_owner():
    data = anonymous_enemy(
        via_pet=True, enemy_pet_name="Fangtooth")
    ctx = build_pvp_enemy_context(data, "normal")
    assert "Fangtooth" in ctx
    assert "master" in ctx
    assert "Shadowfang" not in ctx


def test_creature_payload_unchanged():
    creature = {
        "creature_name": "Hogger",
        "bot_state": {"role": "tank", "target": "Hogger"},
    }
    assert build_pvp_enemy_context(creature) == ""
    state = build_bot_state_context(creature, "normal")
    assert "Hogger" in state
    assert "opposing faction" not in state


def test_kill_prompt_pvp_and_creature():
    pvp = build_kill_reaction_prompt(
        BOT, TRAITS, "Shadowfang", False, False, "normal",
        extra_data=known_enemy())
    assert "opposing faction" in pvp
    assert "regular mob" not in pvp
    assert "Can mention the enemy by name" in pvp

    hidden = build_kill_reaction_prompt(
        BOT, TRAITS, "", False, False, "normal",
        extra_data=anonymous_enemy())
    assert "an enemy adventurer" in hidden
    assert "Do not name or describe the enemy" in hidden

    creature = build_kill_reaction_prompt(
        BOT, TRAITS, "Hogger", False, False, "normal",
        extra_data={"bot_state": {"role": "tank"}})
    assert "regular mob" in creature
    assert "Can mention the creature by name" in creature
    assert "opposing faction" not in creature


def test_combat_prompt_pvp():
    pvp = build_combat_reaction_prompt(
        BOT, TRAITS, "Shadowfang", False, "normal",
        extra_data=known_enemy())
    assert "opposing faction" in pvp
    assert "Just a regular mob" not in pvp


def test_death_prompt_anonymous_killer():
    data = anonymous_enemy(dead_name="Jaina")
    prompt = build_death_reaction_prompt(
        BOT, TRAITS, "Jaina", "", "normal",
        extra_data=data)
    assert "killed by" not in prompt
    assert "unseen" in prompt


def test_spell_prompt_creature_target_stays_creature():
    prompt = build_spell_cast_reaction_prompt(
        BOT, TRAITS, "Thrall", "Frost Shock", "offensive",
        "Hogger", "normal",
        extra_data={"bot_state": {"role": "dps"}})
    assert "opposing faction" not in prompt


def test_aggro_prompt_pvp_target_switch():
    data = known_enemy(callout_kind="pvp_target_switch")
    prompt = build_aggro_loss_callout_prompt(
        BOT, TRAITS, "Shadowfang", "Jaina", "normal",
        extra_data=data)
    assert "switched targets" in prompt
    assert "mob's attention" not in prompt

    hidden = build_aggro_loss_callout_prompt(
        BOT, TRAITS, "", "Jaina", "normal",
        extra_data=anonymous_enemy(
            callout_kind="pvp_target_switch"))
    assert "An unseen enemy" in hidden
    assert "do not name the enemy" in hidden

    creature = build_aggro_loss_callout_prompt(
        BOT, TRAITS, "Hogger", "Jaina", "normal",
        extra_data={"bot_state": {"role": "tank"}})
    assert "mob's attention" in creature


SRC = MODULE_DIR / "src"


def test_bot_state_target_is_visibility_gated_in_cpp():
    """bot_state.target comes from the reactor's own
    victim, which can differ from the event's enemy.
    It must be gated on that victim, not inferred from
    the event's enemy_identity_known."""
    shared = (SRC / "LLMChatterShared.cpp").read_text(
        encoding="utf-8")
    assert re.search(
        r"Unit\* victim = player->GetVictim\(\);\s*"
        r"if \(victim && IsUnitPerceivableBy\(player, victim\)\)"
        r"\s*targetName = victim->GetName\(\);",
        shared,
    )

    # The shared gate is complete: world, map/instance,
    # visibility range, and distance-aware detection.
    # A bare CanSeeOrDetect(unit) skips the sight range.
    body = re.search(
        r"bool IsUnitPerceivableBy\(Player\* viewer, Unit\* unit\)"
        r"\s*\{(.*?)\n\}",
        shared, re.S,
    )
    assert body, "IsUnitPerceivableBy not found"
    gate = body.group(1)
    assert "IsInWorld()" in gate
    assert "viewer->IsInMap(unit)" in gate
    assert re.search(
        r"IsWithinDistInMap\(\s*unit, viewer->GetVisibilityRange\(\)\)",
        gate)
    assert "CanSeeOrDetect(unit, false, true)" in gate

    # Every identity gate uses the same helper.
    combat = (SRC / "LLMChatterGroupCombat.cpp").read_text(
        encoding="utf-8")
    assert "if (victim && IsUnitPerceivableBy(bot, victim))" in combat
    pvp = (SRC / "LLMChatterGroupPvP.cpp").read_text(
        encoding="utf-8")
    assert re.search(
        r"bool IsPvPEnemyPerceivable\(\s*Player\* reactor, Unit\* unit\)"
        r"\s*\{\s*return IsUnitPerceivableBy\(reactor, unit\);",
        pvp)
    for text in (shared, combat, pvp):
        assert not re.search(
            r"CanSeeOrDetect\(\s*(victim|unit)\s*\)", text)
    # Python renders the C++-gated target as-is; it must
    # not re-derive visibility from the event's enemy.
    known_b = known_enemy(bot_state={"role": "dps"})
    state = build_bot_state_context(known_b, "normal")
    assert "currently fighting" not in state, state


def test_state_callouts_never_fall_back_when_pvp_disabled():
    combat = (SRC / "LLMChatterGroupCombat.cpp").read_text(
        encoding="utf-8")
    assert re.search(
        r"bool isPvP = \(pvpEnemy\.enemy != nullptr\);\s*"
        r"if \(isPvP && !sLLMChatterConfig->_pvpChatterEnable\)"
        r"\s*return;",
        combat,
    )
    assert re.search(
        r"pvpSwitchMuted =\s*ResolveOpposingFactionPlayer\(\s*"
        r"bot, victim\)\s*&& \(!sLLMChatterConfig\s*"
        r"->_pvpChatterEnable",
        combat,
    )


def main() -> int:
    test_detection_helpers()
    test_known_enemy_renders_identity()
    test_enemy_is_bot_never_rendered()
    test_level_gap_tiers()
    test_anonymous_enemy_has_no_identity()
    test_visible_pet_with_hidden_owner()
    test_creature_payload_unchanged()
    test_kill_prompt_pvp_and_creature()
    test_combat_prompt_pvp()
    test_death_prompt_anonymous_killer()
    test_spell_prompt_creature_target_stays_creature()
    test_aggro_prompt_pvp_target_switch()
    test_bot_state_target_is_visibility_gated_in_cpp()
    test_state_callouts_never_fall_back_when_pvp_disabled()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
