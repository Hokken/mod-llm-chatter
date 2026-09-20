#!/usr/bin/env python3
"""Source-contract checks for server-side player-chat prefix filtering.

Run directly from the module root:
  python tools/tests/test_player_chat_prefix_filter.py
"""

import re
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[2]
CONFIG_SOURCE = MODULE_DIR / "src" / "LLMChatterConfig.cpp"
CONFIG_HEADER = MODULE_DIR / "src" / "LLMChatterConfig.h"
CONFIG_TEMPLATE = MODULE_DIR / "conf" / "mod_llm_chatter.conf.dist"
GROUP_SOURCE = MODULE_DIR / "src" / "LLMChatterGroupCombat.cpp"
GENERAL_SOURCE = MODULE_DIR / "src" / "LLMChatterPlayer.cpp"
GUILD_SOURCE = MODULE_DIR / "src" / "LLMChatterGuild.cpp"
PROXIMITY_SOURCE = MODULE_DIR / "src" / "LLMChatterProximity.cpp"


def _function_body(source: str, signature: str) -> str:
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError(f"unterminated function: {signature}")


def _assert_filter_order(
    path: Path,
    signature: str,
    setup_patterns: tuple[str, ...],
    side_effect_patterns: tuple[str, ...],
) -> None:
    body = _function_body(path.read_text(encoding="utf-8"), signature)
    filter_match = re.search(r"IsPlayerChatPrefixIgnored\s*\(", body)
    assert filter_match is not None
    for pattern in setup_patterns:
        setup_match = re.search(pattern, body, flags=re.DOTALL)
        assert setup_match is not None
        assert setup_match.start() < filter_match.start()
    previous_at = filter_match.start()
    for pattern in side_effect_patterns:
        side_effect_match = re.search(
            pattern,
            body[previous_at:],
            flags=re.DOTALL,
        )
        assert side_effect_match is not None
        previous_at += side_effect_match.end()


def test_config_is_default_empty_and_reload_safe():
    template = CONFIG_TEMPLATE.read_text(encoding="utf-8")
    assert re.search(
        r"^LLMChatter\.PlayerChat\.IgnoredPrefixes\s*=\s*$",
        template,
        flags=re.MULTILINE,
    )

    header = CONFIG_HEADER.read_text(encoding="utf-8")
    source = CONFIG_SOURCE.read_text(encoding="utf-8")
    assert re.search(
        r"IsPlayerChatPrefixIgnored\s*\(",
        header,
    )
    load_body = _function_body(
        source,
        "void LLMChatterConfig::LoadConfig()",
    )
    assert re.search(
        r'GetChatterOption\s*<\s*std::string\s*>\s*\(\s*'
        r'"LLMChatter\.PlayerChat\.IgnoredPrefixes"\s*,\s*""\s*\)',
        load_body,
        flags=re.DOTALL,
    )
    assert re.search(
        r"atomic_store\s*\(\s*&_playerChatIgnoredPrefixes\s*,",
        load_body,
        flags=re.DOTALL,
    )
    match_body = _function_body(
        source,
        "bool LLMChatterConfig::IsPlayerChatPrefixIgnored(",
    )
    assert re.search(
        r"atomic_load\s*\(\s*&_playerChatIgnoredPrefixes\s*\)",
        match_body,
        flags=re.DOTALL,
    )


def test_all_player_chat_paths_filter_before_side_effects():
    _assert_filter_order(
        GROUP_SOURCE,
        "void HandleGroupPlayerBeforeSendChatMessageImpl(",
        (r"NormalizeChatTextForDb\s*\(",),
        (
            "INSERT INTO llm_group_chat_history",
            "_groupPlayerMsgCooldowns.find",
            r'QueueChatterEvent\s*\(\s*"bot_group_player_msg"',
        ),
    )
    _assert_filter_order(
        GENERAL_SOURCE,
        "bool OnPlayerCanUseChat(",
        (r"NormalizeChatTextForDb\s*\(",),
        (
            "INSERT INTO llm_general_chat_history",
            "_generalChatCooldowns.find",
            r'QueueChatterEvent\s*\(\s*"player_general_msg"',
        ),
    )
    _assert_filter_order(
        GUILD_SOURCE,
        "void HandleGuildPlayerMessage(",
        (),
        (
            r"CancelGuildLoginGreeting\s*\(",
            r"NormalizeChatTextForDb\s*\(",
            r"EnsureGuildPlayerSession\s*\(",
            r"StorePlayerGuildLine\s*\(",
        ),
    )
    _assert_filter_order(
        PROXIMITY_SOURCE,
        "void HandleProximityPlayerSay(",
        (r"TrimChatMessage\s*\(",),
        (
            r"HandleBossProximityPlayerSay\s*\(",
            r"QueueDirectedPlayerSayProximityEvent\s*\(",
        ),
    )


def main() -> int:
    test_config_is_default_empty_and_reload_safe()
    test_all_player_chat_paths_filter_before_side_effects()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
