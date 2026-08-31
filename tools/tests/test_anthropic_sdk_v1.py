#!/usr/bin/env python3
"""Focused Anthropic SDK v1 request regression checks.

Run directly from the module root:
  python tools/tests/test_anthropic_sdk_v1.py
"""

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_llm  # noqa: E402


class _TextBlock:
    def __init__(self, text):
        self.text = text


class _Response:
    def __init__(self, text):
        self.content = [_TextBlock(text)]


class _Messages:
    def __init__(self, response_text):
        self.response_text = response_text
        self.calls = []

    def create(
        self,
        *,
        model,
        max_tokens,
        messages,
        extra_body,
        system=None,
    ):
        self.calls.append({
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "extra_body": extra_body,
            "system": system,
        })
        return _Response(self.response_text)


class _Client:
    def __init__(self, response_text):
        self.messages = _Messages(response_text)


def test_call_llm_uses_extra_body_for_temperature():
    client = _Client("  Lok'tar!  ")
    config = {
        "LLMChatter.Provider": "anthropic",
        "LLMChatter.Model": "claude-haiku-4-5-20251001",
        "LLMChatter.MaxTokens": 120,
        "LLMChatter.Temperature": 0.72,
    }
    original_split_prompt = chatter_llm._split_prompt
    chatter_llm._split_prompt = lambda prompt: (
        "System rules",
        str(prompt),
    )
    try:
        result = chatter_llm.call_llm(
            client,
            "User task",
            config,
            label="anthropic_v1_test",
        )
    finally:
        chatter_llm._split_prompt = original_split_prompt

    assert result == "Lok'tar!"
    assert client.messages.calls == [{
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 120,
        "messages": [{
            "role": "user",
            "content": "User task",
        }],
        "extra_body": {
            "temperature": 0.72,
        },
        "system": "System rules",
    }]


def test_quick_analyze_uses_extra_body_for_temperature():
    client = _Client("  analysis result  ")
    config = {
        "LLMChatter.Provider": "anthropic",
        "LLMChatter.QuickAnalyze.Model": (
            "claude-haiku-4-5-20251001"
        ),
    }
    original_split_prompt = chatter_llm._split_prompt
    chatter_llm._split_prompt = lambda prompt: (
        None,
        str(prompt),
    )
    try:
        result = chatter_llm.quick_llm_analyze(
            client,
            config,
            "Classify this",
            max_tokens=30,
            label="anthropic_v1_quick_test",
        )
    finally:
        chatter_llm._split_prompt = original_split_prompt

    assert result == "analysis result"
    assert client.messages.calls == [{
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 30,
        "messages": [{
            "role": "user",
            "content": "Classify this",
        }],
        "extra_body": {
            "temperature": 0.1,
        },
        "system": None,
    }]


def main() -> int:
    tests = [
        test_call_llm_uses_extra_body_for_temperature,
        test_quick_analyze_uses_extra_body_for_temperature,
    ]
    for test in tests:
        test()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
