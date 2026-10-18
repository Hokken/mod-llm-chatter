#!/usr/bin/env python3
"""Generic openai_compatible provider routes, with mocked SDKs only.

Every config fills in the OpenRouter settings on purpose: none of them
may reach a generic OpenAI-compatible server.

Run directly from the module root:
  python tools/tests/test_openai_compatible_provider.py
"""

import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chatter_healthcheck as healthcheck  # noqa: E402
import chatter_llm as llm  # noqa: E402
from chatter_shared import append_json_instruction  # noqa: E402
from chatter_structured import ResponseContract  # noqa: E402
from llm_compat import (  # noqa: E402
    reset_compatibility_cache, with_response_schema,
)

BASE_URL = 'http://llm.local:8080/v1'
OPENROUTER_NOISE = {
    'LLMChatter.OpenRouter.ApiKey': 'sk-or-v1-real',
    'LLMChatter.OpenRouter.BaseUrl': 'https://openrouter.example/v1',
    'LLMChatter.OpenRouter.HttpReferer': 'https://example.org',
    'LLMChatter.OpenRouter.Title': 'Example',
    'LLMChatter.OpenRouter.ReasoningEffort': 'high',
    'LLMChatter.OpenRouter.ReasoningExclude': '1',
    'LLMChatter.OpenRouter.MaxTokensMultiplier': '5',
}
ANALYSIS = json.dumps(dict(bot=None, multi_addressed=False,
                           brief_casual=False, requires_reply=True))


def config(**overrides):
    values = {
        'LLMChatter.Provider': 'openai_compatible',
        'LLMChatter.Model': 'haiku',
        'LLMChatter.MaxTokens': 100,
        'LLMChatter.Temperature': 0.7,
        'LLMChatter.OpenAICompatible.BaseUrl': BASE_URL,
        'LLMChatter.OpenAICompatible.ApiKey': '',
        **OPENROUTER_NOISE,
    }
    values.update(overrides)
    return values


def completion(raw='Lok\'tar!'):
    return NS(choices=[NS(message=NS(content=raw, refusal=None,
                                    tool_calls=None),
                          finish_reason='stop')],
              usage=NS(prompt_tokens=20, completion_tokens=10,
                       total_tokens=30))


def client_for(raw='Lok\'tar!'):
    create = Mock(return_value=completion(raw))
    return NS(chat=NS(completions=NS(create=create)),
              messages=NS(create=create)), create


class OpenAICompatibleTests(unittest.TestCase):
    def setUp(self):
        reset_compatibility_cache()
        llm.reset_structured_diagnostics()
        llm._quick_analyze_client = None
        llm._quick_analyze_provider = None
        llm._main_client = None
        llm._main_client_provider = None

    def assert_generic_request(self, kwargs, model):
        self.assertEqual(kwargs['model'], model)
        self.assertEqual(kwargs['temperature'], 0.7)
        self.assertIn('max_tokens', kwargs)
        self.assertNotIn('extra_body', kwargs)
        self.assertNotIn('reasoning_effort', kwargs)
        self.assertNotIn('extra_headers', kwargs)

    def test_main_route_sends_verbatim_model_and_no_vendor_extras(self):
        client, create = client_for()
        self.assertEqual(
            llm.call_llm(client, 'Say hi', config(), label='ambient'),
            "Lok'tar!",
        )
        kwargs = create.call_args.kwargs
        # "haiku" is the server's own ID, not the Anthropic alias.
        self.assert_generic_request(kwargs, 'haiku')
        self.assertEqual(kwargs['max_tokens'], 100)

    def test_label_model_route_uses_second_model_on_same_client(self):
        client, create = client_for()
        cfg = config(**{
            'LLMChatter.LabelModel': 'big-local-model',
            'LLMChatter.LabelModel.Labels': 'group_*',
        })
        llm.call_llm(client, 'Say hi', cfg, label='group_idle')
        self.assert_generic_request(create.call_args.kwargs,
                                    'big-local-model')
        llm.call_llm(client, 'Say hi', cfg, label='general_ambient')
        self.assert_generic_request(create.call_args.kwargs, 'haiku')

    def test_structured_route_uses_plain_json_schema(self):
        client, create = client_for('{"message":"Hello"}')
        cfg = config(**{'LLMChatter.StructuredOutput.Enable': '1'})
        prompt = append_json_instruction('Scene', message_only=True)
        self.assertEqual(json.loads(llm.call_llm(client, prompt, cfg)),
                         {'message': 'Hello'})
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs['response_format']['type'], 'json_schema')
        self.assert_generic_request(kwargs, 'haiku')

    def test_schema_adapter_adds_no_provider_routing(self):
        result = with_response_schema(
            {'model': 'm'}, 'openai_compatible', 'n', {'type': 'object'},
        )
        self.assertIn('response_format', result)
        self.assertNotIn('extra_body', result)

    def test_quick_analysis_on_main_provider_inherits_main_model(self):
        client, create = client_for(ANALYSIS)
        llm.quick_llm_analyze(client, config(), 'Analyze',
                              label='quick_test')
        self.assert_generic_request_quick(create.call_args.kwargs, 'haiku')
        self.assertEqual(create.call_args.kwargs['temperature'], 0.1)

    def assert_generic_request_quick(self, kwargs, model):
        self.assertEqual(kwargs['model'], model)
        self.assertNotIn('extra_body', kwargs)
        self.assertNotIn('reasoning_effort', kwargs)

    def test_quick_analysis_model_override_on_main_provider(self):
        client, create = client_for(ANALYSIS)
        cfg = config(**{'LLMChatter.QuickAnalyze.Model': 'tiny'})
        llm.quick_llm_analyze(client, cfg, 'Analyze')
        self.assert_generic_request_quick(create.call_args.kwargs, 'tiny')

    def independent(self, **overrides):
        values = {
            'LLMChatter.Provider': 'anthropic',
            'LLMChatter.Model': 'claude-haiku-4-5-20251001',
            'LLMChatter.QuickAnalyze.Provider': 'openai_compatible',
            'LLMChatter.QuickAnalyze.Model': 'haiku',
            'LLMChatter.StructuredOutput.Enable': '1',
        }
        values.update(overrides)
        return config(**values)

    def test_independent_quick_target_uses_its_own_server(self):
        qa_client, qa_create = client_for(ANALYSIS)
        main_client, main_create = client_for(ANALYSIS)
        with patch('openai.OpenAI', return_value=qa_client) as factory:
            result = llm.quick_llm_analyze(
                main_client, self.independent(), 'Analyze',
                response_contract=ResponseContract('analysis'),
            )
        self.assertIsNotNone(result)
        factory.assert_called_once_with(base_url=BASE_URL,
                                        api_key='not-needed')
        kwargs = qa_create.call_args.kwargs
        self.assert_generic_request_quick(kwargs, 'haiku')
        self.assertEqual(kwargs['response_format']['type'], 'json_schema')
        main_create.assert_not_called()

    def test_independent_quick_target_never_falls_back(self):
        for missing in ('LLMChatter.OpenAICompatible.BaseUrl',
                        'LLMChatter.QuickAnalyze.Model'):
            with self.subTest(missing=missing):
                self.setUp()
                main_client, main_create = client_for(ANALYSIS)
                with patch('openai.OpenAI') as factory, \
                        patch.object(llm.logger, 'error') as error:
                    result = llm.quick_llm_analyze(
                        main_client, self.independent(**{missing: ''}),
                        'Analyze',
                    )
                self.assertIsNone(result)
                factory.assert_not_called()
                main_create.assert_not_called()
                self.assertIn(missing, str(error.call_args))

    def test_client_kwargs_and_target_validation(self):
        self.assertEqual(llm.openai_compatible_client_kwargs(config()),
                         {'base_url': BASE_URL, 'api_key': 'not-needed'})
        keyed = config(**{'LLMChatter.OpenAICompatible.ApiKey': ' k '})
        self.assertEqual(
            llm.openai_compatible_client_kwargs(keyed)['api_key'], 'k',
        )
        self.assertIsNone(llm.openai_compatible_target_error(config()))
        self.assertIn('BaseUrl', llm.openai_compatible_target_error(
            config(**{'LLMChatter.OpenAICompatible.BaseUrl': ' '})))
        self.assertIn('LLMChatter.Model', llm.openai_compatible_target_error(
            config(**{'LLMChatter.Model': ''})))

    def test_model_aliases_apply_to_other_providers_only(self):
        self.assertEqual(llm.resolve_model(' haiku ', 'openai_compatible'),
                         'haiku')
        self.assertEqual(llm.resolve_model('haiku', 'anthropic'),
                         llm.DEFAULT_ANTHROPIC_MODEL)
        self.assertEqual(
            healthcheck._resolved_model(config(), 'openai_compatible'),
            'haiku',
        )
        self.assertEqual(
            healthcheck._resolved_model(
                {'LLMChatter.Provider': 'openai_compatible'},
                'openai_compatible',
            ),
            '',
        )

    def test_healthcheck_provider_config(self):
        self.assertIn('openai_compatible', healthcheck._VALID_PROVIDERS)
        ok = healthcheck._check_provider_config(config())
        self.assertEqual(ok['status'], 'pass')
        self.assertIn(BASE_URL, ok['message'])
        self.assertIn('no API key', ok['message'])
        for key in ('LLMChatter.OpenAICompatible.BaseUrl',
                    'LLMChatter.Model'):
            with self.subTest(missing=key):
                bad = healthcheck._check_provider_config(
                    config(**{key: ''}))
                self.assertEqual(bad['status'], 'fail')
                self.assertIn(key, bad['message'])
        self.assertEqual(
            healthcheck.format_llm_target(config()),
            f'openai_compatible haiku @ {BASE_URL}',
        )

    def test_healthcheck_quick_analyze_target(self):
        self.assertIsNone(healthcheck._check_quick_analyze_target(config()))
        self.assertIsNone(healthcheck._check_quick_analyze_target(config(
            **{'LLMChatter.QuickAnalyze.Provider': 'openai_compatible'})))
        good = healthcheck._check_quick_analyze_target(self.independent())
        self.assertEqual(good['status'], 'pass')
        bad = healthcheck._check_quick_analyze_target(self.independent(
            **{'LLMChatter.QuickAnalyze.Model': ''}))
        self.assertEqual(bad['status'], 'fail')
        self.assertIn('LLMChatter.QuickAnalyze.Model', bad['message'])

    def test_healthcheck_probe_uses_configured_server(self):
        client, create = client_for('OK')
        with patch('openai.OpenAI', return_value=client) as factory:
            result = healthcheck._check_llm_probe(config())
        self.assertEqual(result['status'], 'pass')
        factory.assert_called_once_with(base_url=BASE_URL,
                                        api_key='not-needed')
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs['model'], 'haiku')
        self.assertNotIn('extra_body', kwargs)
        self.assertNotIn('reasoning_effort', kwargs)


if __name__ == '__main__':
    unittest.main()
