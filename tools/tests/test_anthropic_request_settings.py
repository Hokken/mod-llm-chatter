#!/usr/bin/env python3
"""Anthropic thinking/budget settings reach every Anthropic caller.

Covers the bridge (call_llm), the startup health probe and the host
screenshot agent, with structured output on and off.
"""

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_healthcheck  # noqa: E402
import chatter_llm  # noqa: E402
from chatter_structured import ResponseContract, schema_for  # noqa: E402
from llm_compat import reset_compatibility_cache  # noqa: E402


SETTINGS = {
    'LLMChatter.Anthropic.Thinking': 'disabled',
    'LLMChatter.Anthropic.MaxTokensMultiplier': '1.5',
}


class ProviderError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code
        self.body = {}


def _response(text, thinking_first=True):
    blocks = [SimpleNamespace(type='text', text=text)]
    if thinking_first:
        blocks.insert(0, SimpleNamespace(type='thinking', thinking=''))
    return SimpleNamespace(
        content=blocks,
        stop_reason='end_turn',
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
    )


class _Client:
    """Captures Anthropic create() kwargs; replays queued outcomes."""

    def __init__(self, *outcomes):
        self.calls = []
        self.outcomes = list(outcomes)
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class AnthropicRequestSettingsTests(unittest.TestCase):
    def setUp(self):
        reset_compatibility_cache()

    def test_call_llm_applies_thinking_and_multiplier(self):
        client = _Client(_response('Hail'))
        config = dict(SETTINGS, **{
            'LLMChatter.Provider': 'anthropic',
            'LLMChatter.Model': 'claude-new',
            'LLMChatter.MaxTokens': '100',
        })
        self.assertEqual(
            chatter_llm.call_llm(client, 'Say hi', config, free_text=True),
            'Hail',
        )
        request = client.calls[0]
        self.assertEqual(request['max_tokens'], 150)
        self.assertEqual(request['extra_body']['thinking'],
                         {'type': 'disabled'})

    def test_health_probe_uses_production_settings(self):
        client = _Client(_response('OK'))
        config = dict(SETTINGS, **{'LLMChatter.MaxTokens': '100'})
        self.assertEqual(chatter_healthcheck._probe_anthropic(
            config, 'claude-new', client,
        ), 'OK')
        request = client.calls[0]
        # Bounded probe budget (min 128) times the 1.5 multiplier.
        self.assertEqual(request['max_tokens'], 192)
        self.assertEqual(request['extra_body']['thinking'],
                         {'type': 'disabled'})
        self.assertIn('temperature', request['extra_body'])

    def test_health_probe_recovers_from_rejected_temperature(self):
        client = _Client(
            ProviderError('`temperature` is deprecated for this model.'),
            _response('OK'),
        )
        self.assertEqual(chatter_healthcheck._probe_anthropic(
            dict(SETTINGS), 'claude-new', client,
        ), 'OK')
        self.assertNotIn('temperature', client.calls[1]['extra_body'])
        self.assertEqual(client.calls[1]['extra_body']['thinking'],
                         {'type': 'disabled'})

    def test_screenshot_config_carries_anthropic_settings(self):
        import screenshot_agent as vision
        config = vision.load_screenshot_config(dict(SETTINGS))
        self.assertEqual(config['anthropic_options'], SETTINGS)
        self.assertEqual(
            vision.load_screenshot_config({})['anthropic_options'], {},
        )

    def test_screenshot_requests_apply_settings_both_modes(self):
        import screenshot_agent as vision
        data = dict.fromkeys(
            schema_for(ResponseContract('vision'))[1]['properties']
        )
        data['environment'] = 'Stone bridge over a stream.'
        for structured in (False, True):
            client = _Client(_response(json.dumps(data)))
            self.assertIsNotNone(vision.analyze_screenshot(
                b'image', client, 'claude-new', 'anthropic',
                structured_output=structured,
                anthropic_options=dict(SETTINGS),
            ))
            request = client.calls[0]
            self.assertEqual(request['max_tokens'], 450)
            self.assertEqual(request['extra_body'],
                             {'thinking': {'type': 'disabled'}})
            self.assertEqual(request['system'], vision.VISION_SYSTEM)
            content = request['messages'][0]['content']
            self.assertEqual(content[0]['type'], 'image')
            self.assertEqual(content[0]['source']['media_type'],
                             'image/jpeg')
            self.assertEqual(structured, 'output_config' in request)

    def test_screenshot_without_settings_keeps_older_behavior(self):
        import screenshot_agent as vision
        data = dict.fromkeys(
            schema_for(ResponseContract('vision'))[1]['properties']
        )
        data['environment'] = 'Quiet road.'
        client = _Client(_response(json.dumps(data), thinking_first=False))
        self.assertIsNotNone(vision.analyze_screenshot(
            b'image', client, 'claude-haiku-4-5', 'anthropic',
        ))
        request = client.calls[0]
        self.assertEqual(request['max_tokens'], 300)
        self.assertEqual(request['extra_body'], {})


if __name__ == '__main__':
    unittest.main()
