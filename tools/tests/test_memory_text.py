#!/usr/bin/env python3
"""Focused bot memory length checks.

Run directly from the module root:
  python tools/tests/test_memory_text.py
"""

import importlib
import sys
import types
from pathlib import Path


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_non_strict_stubs() -> None:
    for module_name in ("anthropic", "openai"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            module = _ensure_module(module_name)
            class_name = (
                "Anthropic"
                if module_name == "anthropic"
                else "OpenAI"
            )
            setattr(
                module,
                class_name,
                type(class_name, (), {}),
            )

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module(
            "mysql.connector"
        )
        setattr(
            mysql_module,
            "connector",
            connector_module,
        )


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

_install_non_strict_stubs()

from chatter_memory import (  # noqa: E402
    MEMORY_HARD_CHARS,
    _clamp_memory_text,
    sanitize_memory_for_prompt,
)


def test_long_memory_is_sent_whole():
    memory = (
        "Escorted Vladimir through Farstrider Retreat "
        "and cleared the trolls camped on the ridge. "
    ) * 4
    memory = memory.strip()
    assert len(memory) > 200

    assert sanitize_memory_for_prompt(memory) == memory


def test_sanitize_still_cleans_control_chars():
    dirty = "Met\x00 Vladimir \x07in Goldshire.  Twice."
    assert sanitize_memory_for_prompt(dirty) == (
        "Met Vladimir in Goldshire. Twice."
    )


def test_short_memory_is_not_clamped():
    memory = "Met Vladimir and cleared the mine below Northshire."
    assert _clamp_memory_text(memory) == memory


def test_clamp_cuts_on_a_sentence_boundary():
    first = (
        "Held the line at Sentinel Hill while Vladimir "
        "pulled the Defias off the road."
    )
    second = (
        "We regrouped by the tower afterwards and counted "
        "what little was left of our reagents."
    )
    third = (
        "I have not seen the road that quiet since the "
        "harvest golems first went silent."
    )
    memory = f"{first} {second} {third}"
    assert len(memory) > MEMORY_HARD_CHARS

    clamped = _clamp_memory_text(memory)
    assert clamped == f"{first} {second}"
    assert len(clamped) <= MEMORY_HARD_CHARS


def test_clamp_never_splits_a_word():
    memory = "Vladimir " * 60
    clamped = _clamp_memory_text(memory.strip())
    assert len(clamped) <= MEMORY_HARD_CHARS + 1
    assert clamped.endswith("Vladimir.")


def main() -> int:
    test_long_memory_is_sent_whole()
    test_sanitize_still_cleans_control_chars()
    test_short_memory_is_not_clamped()
    test_clamp_cuts_on_a_sentence_boundary()
    test_clamp_never_splits_a_word()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
