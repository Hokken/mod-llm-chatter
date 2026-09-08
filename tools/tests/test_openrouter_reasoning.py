#!/usr/bin/env python3
"""Focused OpenRouter reasoning request regression checks.

Run directly from the module root:
  python tools/tests/test_openrouter_reasoning.py
"""

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_llm  # noqa: E402


class _Message:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Message(content)
        self.finish_reason = 'stop'


class _Response:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _Response('  Lok\'tar!  ')


class _Chat:
    def __init__(self):
        self.completions = _Completions()


class _Client:
    def __init__(self):
        self.chat = _Chat()


def _base_config():
    return {
        'LLMChatter.Provider': 'openrouter',
        'LLMChatter.Model': 'deepseek/deepseek-v4-flash',
        'LLMChatter.MaxTokens': 100,
        'LLMChatter.Temperature': 0.7,
        'LLMChatter.OpenRouter.ReasoningEffort': '',
        'LLMChatter.OpenRouter.ReasoningExclude': '0',
        'LLMChatter.OpenRouter.MaxTokensMultiplier': '1',
    }


def _run_call(config):
    client = _Client()
    original_split_prompt = chatter_llm._split_prompt
    chatter_llm._split_prompt = lambda prompt: (
        'System rules', str(prompt)
    )
    try:
        result = chatter_llm.call_llm(
            client,
            'User task',
            config,
            label='openrouter_reasoning_test',
        )
    finally:
        chatter_llm._split_prompt = original_split_prompt
    assert result == "Lok'tar!"
    return client.chat.completions.calls[0]


def _run_quick_call(config):
    client = _Client()
    original_split_prompt = chatter_llm._split_prompt
    chatter_llm._split_prompt = lambda prompt: (
        'System rules', str(prompt)
    )
    try:
        result = chatter_llm.quick_llm_analyze(
            client,
            config,
            'User task',
            max_tokens=50,
            label='openrouter_quick_reasoning_test',
        )
    finally:
        chatter_llm._split_prompt = original_split_prompt
    assert result == "Lok'tar!"
    return client.chat.completions.calls[0]


def _expected_request(max_tokens, temperature):
    return {
        'model': 'deepseek/deepseek-v4-flash',
        'max_tokens': max_tokens,
        'temperature': temperature,
        'messages': [{
            'role': 'system',
            'content': 'System rules',
        }, {
            'role': 'user',
            'content': 'User task',
        }],
    }


def _assert_request_shapes(
    run_request, base_max_tokens, temperature
):
    config = _base_config()
    config.update({
        'LLMChatter.OpenRouter.ReasoningExclude': '1',
        'LLMChatter.OpenRouter.MaxTokensMultiplier': '8',
    })
    request = run_request(config)
    assert request == _expected_request(
        base_max_tokens, temperature
    )

    config['LLMChatter.OpenRouter.ReasoningEffort'] = 'NoNe'
    request = run_request(config)
    expected = _expected_request(base_max_tokens, temperature)
    expected['extra_body'] = {
        'reasoning': {
            'effort': 'none',
            'exclude': True,
        },
    }
    assert request == expected

    config.update({
        'LLMChatter.OpenRouter.ReasoningEffort': 'high',
        'LLMChatter.OpenRouter.ReasoningExclude': '0',
        'LLMChatter.OpenRouter.MaxTokensMultiplier': '5',
    })
    request = run_request(config)
    expected = _expected_request(
        base_max_tokens * 5, temperature
    )
    expected['extra_body'] = {
        'reasoning': {'effort': 'high'},
    }
    assert request == expected


def test_call_llm_openrouter_reasoning_options():
    _assert_request_shapes(_run_call, 100, 0.7)


def test_quick_analyze_openrouter_reasoning_options():
    _assert_request_shapes(_run_quick_call, 50, 0.1)


def main() -> int:
    test_call_llm_openrouter_reasoning_options()
    test_quick_analyze_openrouter_reasoning_options()
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
