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

import chatter_group_state  # noqa: E402
import chatter_constants
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


def test_ko_language_rule_is_available():
    chatter_shared.set_language("KO")
    rule = chatter_shared.get_language_rule()
    assert "Korean" in rule
    assert "message" in rule
    assert "action" in rule
    assert chatter_shared.get_language_label() == "Korean"
    assert chatter_shared.is_supported_language_code("KO")


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
    assert '"emote"' in conversation.system_prompt
    assert '"action"' in conversation.system_prompt
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


def test_shared_json_repair_prompt_includes_language_rule():
    chatter_shared.set_language("DE")
    prompt = chatter_shared.append_conversation_json_instruction(
        "Write a party exchange.",
        ["Aliss", "Rytsen"],
        2,
        allow_action=False,
    )

    repair_prompt = (
        chatter_shared.build_conversation_json_repair_prompt(
            prompt,
            ["Aliss", "Rytsen"],
        )
    )

    assert "German" in repair_prompt


def test_message_only_conversation_schema():
    chatter_shared.set_language("GB")
    prompt = chatter_shared.append_conversation_json_instruction(
        "Write a guild exchange.",
        ["Aliss", "Rytsen"],
        3,
        allow_action=False,
        message_only=True,
    )

    assert '"speaker"' in prompt.system_prompt
    assert '"message"' in prompt.system_prompt
    assert '"emote"' not in prompt.system_prompt
    assert '"action"' not in prompt.system_prompt


def test_conversation_message_count_bounds():
    original_randint = chatter_shared.random.randint
    calls = []

    def fake_randint(lower, upper):
        calls.append((lower, upper))
        return upper

    chatter_shared.random.randint = fake_randint
    try:
        count = (
            chatter_shared.select_conversation_message_count(
                3, 2, 4
            )
        )
    finally:
        chatter_shared.random.randint = original_randint

    assert count == 4
    assert calls == [(3, 4)]


def test_message_only_repair_schema():
    chatter_shared.set_language("DE")
    prompt = chatter_shared.append_conversation_json_instruction(
        "Write a guild exchange.",
        ["Aliss", "Rytsen"],
        2,
        message_only=True,
    )
    repair_prompt = (
        chatter_shared.build_conversation_json_repair_prompt(
            prompt,
            ["Aliss", "Rytsen"],
            message_only=True,
        )
    )

    assert "German" in repair_prompt
    assert '"speaker"' in repair_prompt
    assert '"message"' in repair_prompt


def test_race_speech_profiles_are_read_through_the_accessor():
    """Prompt builders must not read RACE_SPEECH_PROFILES directly.

    A direct dict read silently bypasses get_race_speech_profile(),
    which is the only thing that resolves the localized profile for
    the configured LLMChatter.Language. Bypassing it produces prompts
    that are localized everywhere except the race flavor words, which
    is exactly the bug this guards against -- and it is invisible in
    English, so only a source-level check catches it.
    """
    tools_dir = Path(__file__).resolve().parent.parent
    offenders = []
    for module in sorted(tools_dir.glob("chatter_*.py")):
        # The constants module defines the tables; the shared module
        # implements the accessor. Everything else must go through it.
        if module.name in ("chatter_constants.py", "chatter_shared.py"):
            continue
        for lineno, line in enumerate(
            module.read_text(encoding="utf-8").splitlines(), 1
        ):
            code = line.split("#", 1)[0]
            if "RACE_SPEECH_PROFILES" in code:
                offenders.append(f"{module.name}:{lineno}: {line.strip()}")

    assert not offenders, (
        "these read RACE_SPEECH_PROFILES directly instead of calling "
        "get_race_speech_profile(); localized flavor words will be "
        "dropped:\n  " + "\n  ".join(offenders)
    )


def test_localized_race_profile_is_returned_for_configured_language():
    """The accessor must actually return the localized profile."""
    chatter_shared.set_language("RU")
    try:
        profile = chatter_shared.get_race_speech_profile("Orc")
        assert profile is not None
        russian = chatter_constants.RACE_SPEECH_PROFILES_RU.get("Orc")
        assert russian is not None
        assert profile == russian, (
            "expected the ruRU profile, got the English one"
        )
    finally:
        chatter_shared.set_language("GB")

    # And an unmapped language must fall back to English, not to None.
    chatter_shared.set_language("GB")
    english = chatter_shared.get_race_speech_profile("Orc")
    assert english == chatter_constants.RACE_SPEECH_PROFILES.get("Orc")


def main() -> int:
    tests = [
        test_de_language_rule_is_available,
        test_ko_language_rule_is_available,
        test_anti_repetition_block_neutralizes_language,
        test_unknown_language_warns_and_falls_back,
        test_json_helpers_put_language_in_user_and_system_prompts,
        test_farewell_prompt_includes_language_rule,
        test_shared_json_repair_prompt_includes_language_rule,
        test_message_only_conversation_schema,
        test_conversation_message_count_bounds,
        test_message_only_repair_schema,
        test_race_speech_profiles_are_read_through_the_accessor,
        test_localized_race_profile_is_returned_for_configured_language,
    ]
    for test in tests:
        test()
    chatter_shared.set_language("GB")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
