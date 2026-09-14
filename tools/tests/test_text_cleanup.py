#!/usr/bin/env python3
"""Focused Unicode cleanup regression checks.

Run directly from the module root:
  python tools/tests/test_text_cleanup.py
"""

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from chatter_text import (  # noqa: E402
    cleanup_message,
    shorten_chat_message,
    shorten_chat_question,
)


def test_hangul_and_cjk_text_are_preserved():
    message = "좋아, 이제 출발하자. 准备好了吗?"
    assert cleanup_message(message) == message


def test_actual_emoji_ranges_are_removed():
    message = "A\U000024C2B\U0001F201C\U0001F600D"
    assert cleanup_message(message) == "ABCD"


def test_overlong_chat_prefers_complete_sentence():
    message = (
        "Did you hear that pompous elf in general? Lylaellor preaching "
        "about Kaldorei superiority like we give a damn about their ten "
        "thousand years. All that history and they still can't keep their "
        "own forest from burning. Let's ignore the noise and focus on the "
        "hunt."
    )
    shortened = shorten_chat_message(message)
    assert shortened == (
        "Did you hear that pompous elf in general? Lylaellor preaching "
        "about Kaldorei superiority like we give a damn about their ten "
        "thousand years. All that history and they still can't keep their "
        "own forest from burning."
    )
    assert len(shortened) <= 255


def test_overlong_single_sentence_uses_word_boundary():
    message = "alpha beta gamma delta epsilon zeta"
    assert shorten_chat_message(message, 24) == "alpha beta gamma..."


def test_early_space_does_not_collapse_cjk_or_url_text():
    cjk = "好的 " + "界" * 300
    url = "See https://" + "a" * 300
    assert shorten_chat_message(cjk) == cjk[:252] + "..."
    assert shorten_chat_message(url) == url[:252] + "..."


def test_artificial_window_end_is_not_a_sentence_boundary():
    message = "x" * 253 + "3.5 gold"
    shortened = shorten_chat_message(message)
    assert shortened == message[:252] + "..."
    assert not shortened.endswith("3.")


def test_cjk_sentence_end_does_not_require_whitespace():
    sentence = "界" * 140 + "。"
    message = sentence + "後" * 200
    assert shorten_chat_message(message) == sentence


def test_exact_word_boundary_keeps_the_complete_word():
    message = "xyz" + "abcd " * 60
    assert shorten_chat_message(message) == message[:252] + "..."


def test_overlong_question_stays_within_limit():
    no_spaces = "Q" * 300 + "?"
    early_space = "Why " + "界" * 300 + "?"
    assert shorten_chat_question(no_spaces) == "Q" * 254 + "?"
    assert shorten_chat_question(early_space) == early_space[:254] + "?"
    assert len(shorten_chat_question(no_spaces)) == 255
    assert len(shorten_chat_question(early_space)) == 255


def main() -> int:
    test_hangul_and_cjk_text_are_preserved()
    test_actual_emoji_ranges_are_removed()
    test_overlong_chat_prefers_complete_sentence()
    test_overlong_single_sentence_uses_word_boundary()
    test_early_space_does_not_collapse_cjk_or_url_text()
    test_artificial_window_end_is_not_a_sentence_boundary()
    test_cjk_sentence_end_does_not_require_whitespace()
    test_exact_word_boundary_keeps_the_complete_word()
    test_overlong_question_stays_within_limit()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
