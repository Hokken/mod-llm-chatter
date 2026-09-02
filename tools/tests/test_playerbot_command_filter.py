import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import chatter_group


def test_playerbot_plain_commands():
    cases = [
        "attack",
        "cast Holy Light",
        "tank attack",
    ]

    for message in cases:
        assert chatter_group._is_playerbot_command(message) is True


def test_playerbot_at_commands_and_selectors():
    cases = [
        "@follow",
        "@tank attack",
        "@dps aoe",
        "@heal me",
        "@priest follow",
        "@star attack",
        "@hpr follow",
        "@50 follow",
        "@45-50 follow",
        "@group1 follow",
        "@aura123 follow",
        "@noaura123 follow",
        "@aggroby 123 flee",
    ]

    for message in cases:
        assert chatter_group._is_playerbot_command(message) is True


def test_normal_conversation_is_not_filtered():
    cases = [
        "hello everyone",
        "@Rubberbean hello everyone",
    ]

    for message in cases:
        assert chatter_group._is_playerbot_command(message) is False
