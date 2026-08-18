"""Focused routing tests for compatible LLM provider APIs."""

import os
import sys
import unittest
from types import SimpleNamespace


TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

from chatter_healthcheck import _probe_openai_compatible
from chatter_llm import (
    _extract_responses_content,
    _call_openai_compatible,
    call_llm,
    quick_llm_analyze,
)
from chatter_provider import (
    get_openai_compatible_request_mode,
    get_openai_compatible_thinking_style,
)


class Recorder:
    """Minimal SDK create() recorder."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def chat_response(text='{"message":"ok"}'):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            message=SimpleNamespace(content=text),
            finish_reason='stop',
        )],
    )


def responses_response(text='{"message":"ok"}'):
    return SimpleNamespace(
        output_text='',
        output=[SimpleNamespace(
            type='message',
            content=[SimpleNamespace(
                type='output_text', text=text,
            )],
        )],
        status='completed',
        incomplete_details=None,
    )


def anthropic_response(text='{"message":"ok"}'):
    return SimpleNamespace(
        content=[
            SimpleNamespace(type='thinking', thinking='hidden'),
            SimpleNamespace(type='text', text=text),
        ],
        stop_reason='end_turn',
    )


def fake_openai_client(chat=None, responses=None):
    chat_recorder = Recorder(chat or chat_response())
    responses_recorder = Recorder(
        responses or responses_response()
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=chat_recorder,
        ),
        responses=responses_recorder,
    )
    return client, chat_recorder, responses_recorder


class ProviderRoutingTests(unittest.TestCase):
    def base_config(self):
        return {
            'LLMChatter.Provider': 'openrouter',
            'LLMChatter.Model': 'deepseek-v4-flash',
            'LLMChatter.OpenAICompatible.DisableThinking': '1',
        }

    def test_defaults_preserve_chat_and_thinking_payload(self):
        config = self.base_config()
        self.assertEqual(
            get_openai_compatible_request_mode(config), 'chat'
        )
        self.assertEqual(
            get_openai_compatible_thinking_style(config), 'thinking'
        )
        client, chat, responses = fake_openai_client()
        result = _call_openai_compatible(
            client, 'openrouter', 'deepseek-v4-flash', config,
            60, 0.1, 'system', 'user', 'test',
        )
        self.assertEqual(result, '{"message":"ok"}')
        self.assertEqual(len(chat.calls), 1)
        self.assertEqual(len(responses.calls), 0)
        self.assertEqual(
            chat.calls[0]['extra_body'],
            {'thinking': {'type': 'disabled'}},
        )
        self.assertEqual(chat.calls[0]['max_tokens'], 60)

    def test_go_deepseek_uses_nested_reasoning_in_chat(self):
        config = self.base_config()
        config.update({
            'LLMChatter.OpenAICompatible.RequestMode': 'chat',
            'LLMChatter.OpenAICompatible.DisableThinkingStyle': (
                'reasoning'
            ),
        })
        client, chat, responses = fake_openai_client()
        _call_openai_compatible(
            client, 'openrouter', 'deepseek-v4-flash', config,
            350, 0.1, None, 'user', 'test',
        )
        self.assertEqual(len(chat.calls), 1)
        self.assertEqual(len(responses.calls), 0)
        self.assertEqual(
            chat.calls[0]['extra_body'],
            {'reasoning': {'effort': 'none'}},
        )
        self.assertNotIn('reasoning_effort', chat.calls[0])

    def test_luna_uses_responses_api_and_native_reasoning(self):
        config = self.base_config()
        config.update({
            'LLMChatter.Model': 'gpt-5.6-luna',
            'LLMChatter.OpenAICompatible.RequestMode': 'responses',
            'LLMChatter.OpenAICompatible.DisableThinkingStyle': (
                'reasoning'
            ),
        })
        client, chat, responses = fake_openai_client()
        result = _call_openai_compatible(
            client, 'openrouter', 'gpt-5.6-luna', config,
            700, 0.1, 'system', 'user', 'test',
        )
        self.assertEqual(result, '{"message":"ok"}')
        self.assertEqual(len(chat.calls), 0)
        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[0]
        self.assertEqual(request['max_output_tokens'], 700)
        self.assertEqual(request['input'], 'user')
        self.assertEqual(request['instructions'], 'system')
        self.assertEqual(
            request['reasoning'], {'effort': 'none'}
        )
        self.assertNotIn('max_tokens', request)
        self.assertNotIn('temperature', request)

    def test_anthropic_disable_and_text_block_extraction(self):
        recorder = Recorder(anthropic_response())
        client = SimpleNamespace(
            messages=recorder,
        )
        config = {
            'LLMChatter.Provider': 'anthropic',
            'LLMChatter.Model': 'claude-haiku-4-5',
            'LLMChatter.Anthropic.DisableThinking': '1',
        }
        result = call_llm(
            client, 'user', config, max_tokens_override=60,
            label='test',
        )
        self.assertEqual(result, '{"message":"ok"}')
        self.assertEqual(
            recorder.calls[0]['thinking'], {'type': 'disabled'}
        )

    def test_quick_analyze_uses_same_go_chat_control(self):
        config = self.base_config()
        config.update({
            'LLMChatter.OpenAICompatible.RequestMode': 'chat',
            'LLMChatter.OpenAICompatible.DisableThinkingStyle': (
                'reasoning'
            ),
        })
        client, chat, _ = fake_openai_client()
        result = quick_llm_analyze(
            client, config, 'classify', max_tokens=60,
            label='test',
        )
        self.assertEqual(result, '{"message":"ok"}')
        self.assertEqual(chat.calls[0]['max_tokens'], 60)
        self.assertEqual(
            chat.calls[0]['extra_body'],
            {'reasoning': {'effort': 'none'}},
        )

    def test_healthcheck_uses_responses_route(self):
        config = self.base_config()
        config.update({
            'LLMChatter.OpenAICompatible.RequestMode': 'responses',
            'LLMChatter.OpenAICompatible.DisableThinkingStyle': (
                'reasoning'
            ),
        })
        client, chat, responses = fake_openai_client(
            responses=responses_response('OK')
        )
        result = _probe_openai_compatible(
            client, 'gpt-5.6-luna', config, 'openrouter'
        )
        self.assertEqual(result, 'OK')
        self.assertEqual(len(chat.calls), 0)
        self.assertEqual(
            responses.calls[0]['reasoning'],
            {'effort': 'none'},
        )

    def test_dict_shaped_responses_fallback(self):
        response = {
            'output_text': '',
            'output': [{
                'type': 'message',
                'content': [{
                    'type': 'output_text',
                    'text': '{"message":"dict"}',
                }],
            }],
            'status': 'completed',
        }
        self.assertEqual(
            _extract_responses_content(response, 'test'),
            '{"message":"dict"}',
        )


if __name__ == '__main__':
    unittest.main()
