#!/usr/bin/env python3
"""Focused language prompt-routing checks.

Run directly from the module root:
  python tools/tests/test_language_prompt_routing.py
"""

import importlib
import logging
import sys
import types
from pathlib import Path


def _ensure_module(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


def _install_non_strict_stubs() -> None:
    """Install minimal stubs for optional provider/database deps."""
    for mod_name in ("anthropic", "openai"):
        try:
            importlib.import_module(mod_name)
        except ModuleNotFoundError:
            mod = _ensure_module(mod_name)
            if mod_name == "anthropic":
                setattr(mod, "Anthropic", type("Anthropic", (), {}))
            else:
                setattr(mod, "OpenAI", type("OpenAI", (), {}))

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_mod = _ensure_module("mysql")
        connector_mod = _ensure_module("mysql.connector")
        setattr(mysql_mod, "connector", connector_mod)


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_ambient  # noqa: E402
import chatter_group_state  # noqa: E402
import chatter_shared  # noqa: E402


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class _Cursor:
    def execute(self, *args, **kwargs):
        pass

    def fetchone(self):
        return None


class _DB:
    def cursor(self, *args, **kwargs):
        return _Cursor()

    def commit(self):
        pass


def test_de_language_rule_is_available():
    chatter_shared.set_language("DE")
    rule = chatter_shared.get_language_rule()
    assert "German" in rule
    assert "message" in rule
    assert "action" in rule
    assert chatter_shared.get_language_label() == "German"
    assert chatter_shared.is_supported_language_code("DE")
    # Rule must neutralize the language of injected prior
    # context (anti-repetition, chat history, memories).
    assert "never as a guide" in rule


def test_ar_language_preserves_localized_server_names():
    chatter_shared.set_language("AR")
    rule = chatter_shared.get_language_rule()
    assert "Arabic" in rule
    assert "exactly as it appears" in rule
    assert "already be localized into Arabic" in rule
    assert chatter_shared.get_language_label() == "Arabic"
    assert chatter_shared.is_supported_language_code("AR")
    assert "never as a guide" in rule


def test_anti_repetition_block_neutralizes_language():
    chatter_shared.set_language("DE")
    block = chatter_shared.build_anti_repetition_context(
        ["Schon wieder Regen", "Anyone seen the bank?"]
    )
    assert "German" in block
    assert "any language" in block

    # English default emits no caveat (no extra tokens).
    chatter_shared.set_language("GB")
    block_en = chatter_shared.build_anti_repetition_context(
        ["hello there"]
    )
    assert "any language" not in block_en


def test_unknown_language_warns_and_falls_back():
    handler = _ListHandler()
    logger = logging.getLogger("chatter_shared")
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    try:
        chatter_shared.set_language("ZZ")
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)

    assert chatter_shared.get_language_rule() == ""
    assert chatter_shared.get_language_label() == "English"
    assert not chatter_shared.is_supported_language_code("ZZ")
    assert any(
        "Unknown LLMChatter.Language=ZZ" in record.getMessage()
        for record in handler.records
    )


def test_json_helpers_put_language_in_user_and_system_prompts():
    chatter_shared.set_language("DE")
    chatter_shared.set_emote_chance(0)
    chatter_shared.set_action_chance(100, mode="roleplay")

    single = chatter_shared.append_json_instruction(
        "Write one line.",
        allow_action=False,
        skip_emote=True,
    )
    assert "German" in single.user_prompt
    assert "German" in single.system_prompt

    conversation = chatter_shared.append_conversation_json_instruction(
        "Write a party exchange.",
        ["Aliss", "Rytsen"],
        2,
        allow_action=True,
    )
    assert "German" in conversation.user_prompt
    assert "German" in conversation.system_prompt
    assert "leans against the wall" not in conversation.system_prompt
    assert "configured language" in conversation.system_prompt


def test_farewell_prompt_includes_language_rule():
    chatter_shared.set_language("DE")
    captured = {}

    def fake_call_llm(client, prompt, config, **kwargs):
        captured["prompt"] = prompt
        return "Bis dann"

    original_call_llm = chatter_group_state.call_llm
    chatter_group_state.call_llm = fake_call_llm
    try:
        chatter_group_state._generate_farewell(
            _DB(), None,
            {
                "LLMChatter.Memory.Enable": 0,
            },
            "Aliss", "Human", "Mage", "female",
            ["curious"], "roleplay", 1, 2,
        )
    finally:
        chatter_group_state.call_llm = original_call_llm

    assert "German" in captured["prompt"]


def test_ambient_json_repair_prompt_includes_language_rule():
    chatter_shared.set_language("DE")
    prompt = chatter_shared.append_conversation_json_instruction(
        "Write a party exchange.",
        ["Aliss", "Rytsen"],
        2,
        allow_action=False,
    )

    repair_prompt = chatter_ambient._build_json_repair_prompt(
        prompt,
        ["Aliss", "Rytsen"],
    )

    assert "German" in repair_prompt


def main() -> int:
    tests = [
        test_de_language_rule_is_available,
        test_anti_repetition_block_neutralizes_language,
        test_unknown_language_warns_and_falls_back,
        test_json_helpers_put_language_in_user_and_system_prompts,
        test_farewell_prompt_includes_language_rule,
        test_ambient_json_repair_prompt_includes_language_rule,
    ]
    for test in tests:
        test()
    chatter_shared.set_language("GB")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
