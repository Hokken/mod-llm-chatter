#!/usr/bin/env python3
"""Focused DeepSeek and Ollama request regression checks.

Run directly from the module root:
  python tools/tests/test_provider_requests.py
"""

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_llm  # noqa: E402
import chatter_healthcheck  # noqa: E402


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
        'LLMChatter.Provider': 'deepseek',
        'LLMChatter.Model': 'deepseek-flash',
        'LLMChatter.MaxTokens': 100,
        'LLMChatter.Temperature': 0.7,
        'LLMChatter.DeepSeek.ReasoningEffort': 'none',
        'LLMChatter.DeepSeek.MaxTokensMultiplier': '1',
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
            label='deepseek_test',
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
            label='deepseek_quick_test',
        )
    finally:
        chatter_llm._split_prompt = original_split_prompt
    assert result == "Lok'tar!"
    return client.chat.completions.calls[0]


def _expected_request(max_tokens, temperature=None):
    request = {
        'model': 'deepseek-flash',
        'max_tokens': max_tokens,
        'messages': [{
            'role': 'system',
            'content': 'System rules',
        }, {
            'role': 'user',
            'content': 'User task',
        }],
    }
    if temperature is not None:
        request['temperature'] = temperature
    return request


def _assert_request_shapes(
    run_request, base_max_tokens, temperature
):
    # Thinking off: temperature survives, thinking is disabled
    # explicitly because the API enables it by default.
    config = _base_config()
    config['LLMChatter.DeepSeek.MaxTokensMultiplier'] = '8'
    request = run_request(config)
    expected = _expected_request(base_max_tokens, temperature)
    expected['reasoning_effort'] = 'none'
    expected['extra_body'] = {'thinking': {'type': 'disabled'}}
    assert request == expected

    # An empty setting must not fall back to the DeepSeek
    # default (thinking enabled).
    config['LLMChatter.DeepSeek.ReasoningEffort'] = '  '
    assert run_request(config) == expected

    # Thinking on: budget multiplier applies and temperature is
    # dropped because DeepSeek ignores it in thinking mode.
    config.update({
        'LLMChatter.DeepSeek.ReasoningEffort': 'HIGH',
        'LLMChatter.DeepSeek.MaxTokensMultiplier': '5',
    })
    request = run_request(config)
    expected = _expected_request(base_max_tokens * 5)
    expected['reasoning_effort'] = 'high'
    expected['extra_body'] = {'thinking': {'type': 'enabled'}}
    assert request == expected


def test_call_llm_deepseek_thinking_options():
    _assert_request_shapes(_run_call, 100, 0.7)


def test_quick_analyze_deepseek_thinking_options():
    _assert_request_shapes(_run_quick_call, 50, 0.1)


def test_deepseek_defaults_to_flash_model():
    config = _base_config()
    del config['LLMChatter.Model']
    request = _run_call(config)
    assert request['model'] == 'deepseek-flash'


def test_deepseek_model_aliases_resolve():
    assert chatter_llm.resolve_model(
        'deepseek'
    ) == 'deepseek-flash'
    assert chatter_llm.resolve_model(
        'deepseek-v4-flash'
    ) == 'deepseek-flash'
    assert chatter_llm.resolve_model(
        'DeepSeek-Pro'
    ) == 'deepseek-v4-pro'


def test_health_probe_uses_production_deepseek_options():
    client = _Client()
    config = {
        'LLMChatter.MaxTokens': '100',
        'LLMChatter.Temperature': '0.7',
        'LLMChatter.DeepSeek.ReasoningEffort': 'none',
        'LLMChatter.DeepSeek.MaxTokensMultiplier': '1',
    }
    result = chatter_healthcheck._probe_openai_compatible(
        client, 'deepseek-flash', 'deepseek', config
    )
    assert result == "Lok'tar!"
    request = client.chat.completions.calls[0]
    # The probe floor is 128 and thinking-off adds no multiplier.
    assert request['max_tokens'] == 128
    assert request['temperature'] == 0.7
    assert request['reasoning_effort'] == 'none'
    assert request['extra_body'] == {
        'thinking': {'type': 'disabled'},
    }


def test_healthcheck_accepts_deepseek_provider():
    config = {
        'LLMChatter.Provider': 'deepseek',
        'LLMChatter.Model': 'deepseek-flash',
        'LLMChatter.DeepSeek.ApiKey': 'sk-real-key',
    }
    result = chatter_healthcheck._check_provider_config(config)
    assert result['status'] == 'pass', result
    assert chatter_healthcheck.format_llm_target(config) == (
        'deepseek deepseek-flash @ https://api.deepseek.com'
    )


def test_healthcheck_flags_placeholder_deepseek_key():
    config = {
        'LLMChatter.Provider': 'deepseek',
        'LLMChatter.DeepSeek.ApiKey': 'sk-xxxxx',
    }
    result = chatter_healthcheck._check_provider_config(config)
    assert result['status'] == 'fail', result


def test_healthcheck_rejects_removed_providers():
    for provider in (
        'anthropic', 'openai', 'google', 'openrouter'
    ):
        result = chatter_healthcheck._check_provider_config({
            'LLMChatter.Provider': provider,
        })
        assert result['status'] == 'fail', provider
        assert 'Unknown provider' in result['message'], provider


def _ollama_config():
    return {
        'LLMChatter.Provider': 'ollama',
        'LLMChatter.Model': 'qwen3:8b',
        'LLMChatter.Ollama.DisableThinking': '1',
        'LLMChatter.MaxTokens': 100,
        'LLMChatter.Temperature': 0.7,
    }


def test_ollama_uses_compatible_request_layer():
    request = _run_call(_ollama_config())
    assert request['model'] == 'qwen3:8b'
    assert request['max_tokens'] == 100
    assert request['temperature'] == 0.7
    assert request['reasoning_effort'] == 'none'
    assert request['messages'][1]['content'] == '/no_think User task'
    # The DeepSeek thinking object must not leak into Ollama.
    assert 'extra_body' not in request


def test_quick_ollama_uses_compatible_request_layer():
    request = _run_quick_call(_ollama_config())
    assert request['max_tokens'] == 50
    assert request['temperature'] == 0.1
    assert request['reasoning_effort'] == 'none'
    assert request['messages'][1]['content'] == '/no_think User task'


def test_ollama_thinking_can_be_left_on():
    config = _ollama_config()
    config['LLMChatter.Ollama.DisableThinking'] = '0'
    request = _run_call(config)
    assert 'reasoning_effort' not in request
    assert request['messages'][1]['content'] == 'User task'


def test_ollama_model_tags_are_not_rewritten():
    assert chatter_llm.resolve_model('qwen3:8b') == 'qwen3:8b'
    assert chatter_llm.resolve_model(
        'llama3.2:3b'
    ) == 'llama3.2:3b'


def main() -> int:
    test_call_llm_deepseek_thinking_options()
    test_quick_analyze_deepseek_thinking_options()
    test_deepseek_defaults_to_flash_model()
    test_deepseek_model_aliases_resolve()
    test_health_probe_uses_production_deepseek_options()
    test_healthcheck_accepts_deepseek_provider()
    test_healthcheck_flags_placeholder_deepseek_key()
    test_healthcheck_rejects_removed_providers()
    test_ollama_uses_compatible_request_layer()
    test_quick_ollama_uses_compatible_request_layer()
    test_ollama_thinking_can_be_left_on()
    test_ollama_model_tags_are_not_rewritten()
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
