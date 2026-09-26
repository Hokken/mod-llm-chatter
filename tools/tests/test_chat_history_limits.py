#!/usr/bin/env python3
"""Regression checks for Party and General history-limit configuration.

Run directly from the module root:
  python tools/tests/test_chat_history_limits.py
"""

import re
import sys
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
TOOLS_DIR = MODULE_DIR / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_general  # noqa: E402
import chatter_group  # noqa: E402
import chatter_group_state  # noqa: E402


CONFIG_TEMPLATES = (
    MODULE_DIR / "conf" / "mod_llm_chatter.conf.dist",
    MODULE_DIR / "conf" / "presets" / "mod_ll_chatter_quieter.conf.dist",
)
CONFIG_SOURCE = MODULE_DIR / "src" / "LLMChatterConfig.cpp"


def test_templates_expose_both_limits_once():
    for path in CONFIG_TEMPLATES:
        text = path.read_text(encoding="utf-8")
        assert len(re.findall(
            r"^LLMChatter\.ChatHistoryLimit\s*=\s*10\s*$",
            text,
            flags=re.MULTILINE,
        )) == 1, path
        assert len(re.findall(
            r"^LLMChatter\.GeneralChat\.HistoryLimit\s*=\s*15\s*$",
            text,
            flags=re.MULTILINE,
        )) == 1, path


def test_party_default_and_clamping():
    chatter_group.init_group_config({})
    assert chatter_group._chat_history_limit == 10
    assert chatter_group_state._chat_history_limit == 10

    chatter_group.init_group_config({
        "LLMChatter.ChatHistoryLimit": "0",
    })
    assert chatter_group._chat_history_limit == 1
    assert chatter_group_state._chat_history_limit == 1

    chatter_group.init_group_config({
        "LLMChatter.ChatHistoryLimit": "500",
    })
    assert chatter_group._chat_history_limit == 50
    assert chatter_group_state._chat_history_limit == 50


def test_general_override_fallback_and_clamping():
    chatter_general.init_general_config({
        "LLMChatter.ChatHistoryLimit": "24",
    })
    assert chatter_general._chat_history_limit == 24

    chatter_general.init_general_config({
        "LLMChatter.ChatHistoryLimit": "24",
        "LLMChatter.GeneralChat.HistoryLimit": "17",
    })
    assert chatter_general._chat_history_limit == 17

    chatter_general.init_general_config({
        "LLMChatter.GeneralChat.HistoryLimit": "0",
    })
    assert chatter_general._chat_history_limit == 1

    chatter_general.init_general_config({
        "LLMChatter.GeneralChat.HistoryLimit": "500",
    })
    assert chatter_general._chat_history_limit == 50


def test_server_uses_same_fallback_and_clamp():
    source = CONFIG_SOURCE.read_text(encoding="utf-8")
    assert re.search(
        r'uint32 chatHistoryLimit = std::clamp\(\s*'
        r'GetChatterOption<uint32>\(\s*'
        r'"LLMChatter\.ChatHistoryLimit",\s*10\s*\),\s*'
        r'1u,\s*50u\s*\);',
        source,
    )
    assert re.search(
        r'_generalChatHistoryLimit = std::clamp\(\s*'
        r'GetChatterOption<uint32>\(\s*'
        r'"LLMChatter\.GeneralChat\.HistoryLimit",\s*'
        r'chatHistoryLimit\s*\),\s*1u,\s*50u\s*\);',
        source,
    )


def main() -> int:
    test_templates_expose_both_limits_once()
    test_party_default_and_clamping()
    test_general_override_fallback_and_clamping()
    test_server_uses_same_fallback_and_clamp()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
