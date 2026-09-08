#!/usr/bin/env python3
"""Regression checks for Playerbot command filtering.

Run directly from the module root:
  python tools/tests/test_playerbot_command_filter.py
"""

import re
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parents[1]
GROUP_SOURCE = MODULE_DIR / "src" / "LLMChatterGroup.cpp"
sys.path.insert(0, str(TOOLS_DIR))

import chatter_group


def test_playerbot_plain_commands():
    cases = [
        "attack",
        "cast Holy Light",
        "tank attack",
    ]

    for message in cases:
        assert chatter_group._is_playerbot_command(message) is True, message


def test_playerbot_at_commands_and_selectors():
    cases = [
        "@follow",
        "@tank attack",
        "@tank\tattack",
        "@TANK ATTACK",
        "@dps co +aoe",
        "@heal follow",
        "@priest follow",
        "@star attack",
        "@hpr follow",
        "@50 follow",
        "@45-50 follow",
        "@group1 follow",
        "@aura123 follow",
        "@aura 123 follow",
        "@noaura123 follow",
        "@aggroby 123 flee",
    ]

    for message in cases:
        assert chatter_group._is_playerbot_command(message) is True, message


def test_normal_conversation_is_not_filtered():
    cases = [
        "hello everyone",
        "@Rubberbean hello everyone",
        "@Aurabelle hi there",
        "@Groupie hello",
        "@Frost nice heals",
        "@tank nice save man",
        "@dps aoe",
        "@heal me",
        "@50-",
        "@-50 follow",
        "@group- follow",
        "@group, follow",
        "@",
        "@ follow",
        "@tankattack",
        "@\u00b2 follow",
    ]

    for message in cases:
        assert chatter_group._is_playerbot_command(message) is False, message


def test_cpp_python_selector_sets_match():
    source = GROUP_SOURCE.read_text(encoding="utf-8")
    match = re.search(
        r"selectorPrefixes\s*=\s*\{"
        r"(?P<body>.*?)\n\s*\};",
        source,
        flags=re.DOTALL,
    )
    assert match is not None
    cpp_selectors = set(re.findall(
        r'"(@[a-z]+)"', match.group("body")
    ))
    assert cpp_selectors == chatter_group.PLAYERBOT_SELECTOR_PREFIXES


def main() -> int:
    test_playerbot_plain_commands()
    test_playerbot_at_commands_and_selectors()
    test_normal_conversation_is_not_filtered()
    test_cpp_python_selector_sets_match()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
