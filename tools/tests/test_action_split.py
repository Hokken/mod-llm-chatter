#!/usr/bin/env python3
"""Regression checks for the action/speech split.

cleanup_message() inlines the LLM's action field as a
leading *asterisk* prefix; split_action_prefix() pulls it
back out at queue time so delivery can send it as /e.

Run directly from the module root:
  python tools/tests/test_action_split.py
"""

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from chatter_text import (  # noqa: E402
    cleanup_message,
    split_action_prefix,
)


def test_round_trip_matches_the_llm_fields():
    """The exact case from the bug report."""
    action = "scans the treeline, bow already drawn"
    spoken = (
        "Fairbreeze burning again? At least dying for "
        "Defending Fairbreeze Village smells better "
        "than the last village."
    )
    combined = cleanup_message(spoken, action=action)
    assert combined.startswith("*")

    message, split = split_action_prefix(combined)
    assert split == action
    assert message == spoken


def test_message_without_action_is_untouched():
    message, action = split_action_prefix(
        "Just words, no narration."
    )
    assert action is None
    assert message == "Just words, no narration."


def test_action_only_message_is_left_inline():
    """Splitting would leave an empty chat line."""
    message, action = split_action_prefix("*nods slowly*")
    assert action is None
    assert message == "*nods slowly*"


def test_mid_message_asterisks_are_not_an_action():
    text = "I said *no* and I meant it."
    message, action = split_action_prefix(text)
    assert action is None
    assert message == text


def test_empty_and_non_string_inputs_are_safe():
    assert split_action_prefix("") == ("", None)
    assert split_action_prefix(None) == (None, None)


def test_overlong_prefix_stays_inline():
    """Beyond the 80 char action cap, treat it as prose."""
    long_prefix = "x" * 81
    text = f"*{long_prefix}* hello"
    message, action = split_action_prefix(text)
    assert action is None
    assert message == text


def main() -> int:
    test_round_trip_matches_the_llm_fields()
    test_message_without_action_is_untouched()
    test_action_only_message_is_left_inline()
    test_mid_message_asterisks_are_not_an_action()
    test_empty_and_non_string_inputs_are_safe()
    test_overlong_prefix_stays_inline()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
