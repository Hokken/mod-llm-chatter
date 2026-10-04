"""Native adapters and strict request boundaries with mocked SDKs only."""

from concurrent.futures import ThreadPoolExecutor
import builtins
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chatter_llm as llm
import chatter_request_logger as request_log
from chatter_shared import append_json_instruction, PromptParts
from chatter_structured import ResponseContract, schema_for
from llm_compat import (reset_compatibility_cache, structured_rejection_category,
                        with_response_schema)


PROVIDERS = ('openai', 'google', 'openrouter', 'ollama', 'anthropic')


def completion(raw='{"message":"Hello"}', *, provider='openai', finish=None,
               refusal=None, tools=None):
    if provider == 'anthropic':
        return NS(content=[NS(type='text', text=raw)],
                  stop_reason=finish or 'end_turn',
                  usage=NS(input_tokens=20, output_tokens=10))
    return NS(choices=[NS(message=NS(content=raw, refusal=refusal,
                                    tool_calls=tools),
                          finish_reason=finish or 'stop')],
              usage=NS(prompt_tokens=20, completion_tokens=10, total_tokens=30))


def client_for(result):
    operation = Mock(return_value=result)
    return NS(chat=NS(completions=NS(create=operation)),
              messages=NS(create=operation)), operation


class Rejection(Exception):
    status_code = 400

    def __init__(self, param, code, message):
        super().__init__(message)
        self.body = dict(param=param, code=code, message=message)


class RequestTests(unittest.TestCase):
    def setUp(self):
        reset_compatibility_cache()
        llm.reset_structured_diagnostics()
        self.prompt = append_json_instruction('Scene', message_only=True)

    def config(self, provider='openai', enabled='1'):
        return {'LLMChatter.Provider': provider,
                'LLMChatter.Model': 'a-future-model',
                'LLMChatter.StructuredOutput.Enable': enabled}

    def test_all_providers_use_native_schema_and_preserve_off_kwargs(self):
        for provider in PROVIDERS:
            for finish in (('end_turn', 'END_TURN') if provider == 'anthropic'
                           else ('stop', 'STOP')):
                with self.subTest(provider=provider, finish=finish):
                    client, create = client_for(completion(
                        provider=provider, finish=finish,
                    ))
                    config = self.config(provider)
                    config.update({
                        'LLMChatter.Google.ThinkingBudget': '0',
                        'LLMChatter.OpenRouter.ReasoningEffort': 'low',
                        'LLMChatter.OpenRouter.ReasoningExclude': '1',
                    })
                    self.assertEqual(json.loads(llm.call_llm(
                        client, self.prompt, config,
                    )), {'message': 'Hello'})
                    on = deepcopy(create.call_args.kwargs)
                    self.assertEqual(on['model'], 'a-future-model')
                    key = ('output_config' if provider == 'anthropic'
                           else 'response_format')
                    self.assertIn(key, on)
                    config['LLMChatter.StructuredOutput.Enable'] = '0'
                    llm.call_llm(client, self.prompt, config)
                    off = create.call_args.kwargs
                    self.assertNotIn(key, off)
                    on.pop(key)
                    if provider == 'openrouter':
                        self.assertTrue(on['extra_body']['provider']
                                        ['require_parameters'])
                        on['extra_body'].pop('provider')
                    # Prompt format is the only other deliberate difference.
                    if provider == 'anthropic':
                        on['system'] = off['system']
                    else:
                        on['messages'] = off['messages']
                    self.assertEqual(on, off)

    def test_schema_adapter_copies_only_owned_nested_options(self):
        base = {'extra_body': {'reasoning': {'effort': 'low'},
                               'provider': {'order': ['local']}}}
        original = deepcopy(base)
        name, schema = schema_for(self.prompt.response_contract)
        result = with_response_schema(base, 'openrouter', name, schema)
        result['extra_body']['provider']['order'].append('remote')
        result['response_format']['json_schema']['schema']['properties'].clear()
        self.assertEqual(base, original)
        self.assertTrue(schema['properties'])

    def test_rejects_incomplete_refused_and_malformed_without_raw_fallback(self):
        bad = [completion(finish=finish) for finish in (
            'length', 'content_filter', 'tool_calls', 'unknown',
        )] + [completion(refusal='Refused'), completion(tools=[{}]),
              completion(raw='Here is {"message":"Hi"}'),
              completion(raw='{"message":"Hi","extra":1}'),
              completion(raw='{"message":"Hi"} trailing'),
              completion(raw=''), NS(choices=[])]
        missing = completion()
        missing.choices[0].finish_reason = None
        bad.append(missing)
        for response in bad:
            client, create = client_for(response)
            self.assertIsNone(llm.call_llm(client, self.prompt, self.config()))
            create.assert_called_once()
        for reason in ('max_tokens', 'refusal', 'tool_use', 'unknown'):
            client, _ = client_for(completion(provider='anthropic', finish=reason))
            self.assertIsNone(llm.call_llm(
                client, self.prompt, self.config('anthropic'),
            ))

    def test_anthropic_joins_text_blocks_and_ignores_thinking(self):
        response = completion(provider='anthropic')
        response.content = [NS(type='thinking', thinking='internal'),
                            NS(type='text', text='{"message":'),
                            NS(type='text', text='"Hi"}')]
        client, _ = client_for(response)
        self.assertEqual(json.loads(llm.call_llm(
            client, self.prompt, self.config('anthropic'),
        )), {'message': 'Hi'})

    def test_off_and_plain_text_keep_legacy_extraction(self):
        client, create = client_for(completion(raw='plain prose', finish='length'))
        self.assertEqual(llm.call_llm(client, self.prompt,
                                     self.config(enabled='0')), 'plain prose')
        self.assertEqual(llm.call_llm(client, 'Write a farewell', self.config(),
                                     free_text=True),
                         'plain prose')
        self.assertNotIn('response_format', create.call_args.kwargs)

    def test_contract_error_makes_no_request_and_never_becomes_text(self):
        invalid = PromptParts('Scene', 'Legacy', contract_conflict=True)
        client, create = client_for(completion())
        for prompt, explicit in ((invalid, None),
                                 (str(self.prompt), None),
                                 (self.prompt, ResponseContract('memory'))):
            with patch.object(request_log, 'log_request') as log:
                self.assertIsNone(llm.call_llm(
                    client, prompt, self.config(), response_contract=explicit,
                ))
                self.assertEqual(log.call_args.kwargs['metadata']
                                 ['structured_output']['validation'],
                                 'contract_error')
        create.assert_not_called()

    def test_unsupported_format_is_not_retried_without_schema(self):
        client, create = client_for(None)
        create.side_effect = Rejection('response_format', 'unsupported_parameter',
                                      'response_format is not supported')
        with patch.object(llm.logger, 'log') as log:
            for _ in range(2):
                self.assertIsNone(llm.call_llm(client, self.prompt, self.config()))
            self.assertEqual([c.args[0] for c in log.call_args_list], [30, 10])
        self.assertEqual(create.call_count, 2)
        self.assertTrue(all('response_format' in c.kwargs
                            for c in create.call_args_list))

    def test_schema_and_generic_rejections_are_not_capability_claims(self):
        invalid = Rejection('response_format.json_schema.schema',
                            'invalid_json_schema', 'Invalid schema')
        self.assertEqual(structured_rejection_category(invalid, 'openai'),
                         'schema_rejected')
        generic = Rejection(None, None, 'No eligible provider route')
        self.assertEqual(structured_rejection_category(generic, 'openrouter'),
                         'request_rejected')
        generic.status_code = 401
        self.assertIsNone(structured_rejection_category(generic, 'openai'))

    def test_failure_details_and_periodic_repeat_warning(self):
        output = Mock()
        diagnostics = dict(finish_reason='length', token_budget=1234)
        with patch.object(llm.time, 'monotonic', side_effect=[0, 1, 2, 300]):
            for _ in range(4):
                llm.log_structured_failure(
                    'openai', 'model', 'schema', 'incomplete_or_refused',
                    output, diagnostics=diagnostics,
                )
        calls = output.log.call_args_list
        self.assertEqual([c.args[0] for c in calls], [30, 10, 10, 30])
        rendered = calls[-1].args[1] % calls[-1].args[2:]
        self.assertIn('finish_reason=length token_budget=1234', rendered)
        self.assertIn('3 repeats since last warning', rendered)
        self.assertNotIn('disable', rendered)
        output.reset_mock()
        for label in ('site_a', 'site_b', 'site_a'):
            llm.log_structured_failure('openai', 'model', None,
                                       'contract_error', output, label=label)
        self.assertEqual([c.args[0] for c in output.log.call_args_list],
                         [30, 30, 10])
        self.assertIn('site_b', str(output.log.call_args_list[1]))
        llm.log_structured_failure(
            'openai', 'model', 'schema', 'request_rejected', output,
            error=Rejection(None, None, 'Context too long\nBearer sk-secret'),
        )
        rendered = output.log.call_args.args[1] % output.log.call_args.args[2:]
        self.assertIn('Context too long', rendered)
        self.assertNotIn('sk-secret', rendered)

    def test_compatibility_retry_keeps_schema_and_logs_effective_budget(self):
        client, create = client_for(None)
        create.side_effect = [Rejection('max_tokens', 'unsupported_parameter',
                                       'max_tokens is not supported'),
                              completion()]
        config = self.config('ollama')
        with patch.object(request_log, 'log_request') as log:
            self.assertIsNotNone(llm.call_llm(client, self.prompt, config))
            diagnostics = log.call_args.kwargs['metadata']['structured_output']
        self.assertEqual(diagnostics['token_field'], 'max_completion_tokens')
        self.assertEqual(diagnostics['token_budget'], 350)
        self.assertEqual(create.call_count, 2)
        self.assertEqual(create.call_args_list[0].kwargs['response_format'],
                         create.call_args_list[1].kwargs['response_format'])

    def test_raw_logging_and_caller_metadata_isolation(self):
        raw = '  {"message":"Bonjour"} \n'
        client, _ = client_for(completion(raw=raw))
        metadata = {'role': 'test', 'nested': {'unchanged': True}}
        with patch.object(request_log, 'log_request') as log:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: llm.call_llm(
                    client, self.prompt, self.config(), metadata=metadata,
                ), range(8)))
        self.assertTrue(all(json.loads(r)['message'] == 'Bonjour' for r in results))
        self.assertEqual(metadata, {'role': 'test', 'nested': {'unchanged': True}})
        self.assertTrue(all(c.args[2] == raw for c in log.call_args_list))
        self.assertTrue(all(c.kwargs['system_prompt'] ==
                            self.prompt.structured_system_prompt
                            for c in log.call_args_list))

    def test_reasoning_rejection_retains_schema_and_reports_expanded_budget(self):
        client, create = client_for(None)
        create.side_effect = [
            Rejection('reasoning_effort', 'unsupported_parameter',
                      'reasoning_effort is not supported'), completion(),
        ]
        config = {**self.config(), 'LLMChatter.Model': 'gpt-6-luna',
                  'LLMChatter.OpenAI.ReasoningEffort': 'none'}
        with patch.object(request_log, 'log_request') as log:
            self.assertIsNotNone(llm.call_llm(client, self.prompt, config))
            diagnostics = log.call_args.kwargs['metadata']['structured_output']
        self.assertEqual(diagnostics['token_budget'], 1400)
        self.assertNotIn('reasoning_effort', create.call_args.kwargs)
        self.assertTrue(all('response_format' in c.kwargs
                            for c in create.call_args_list))

    def test_quick_analysis_uses_actual_auxiliary_target(self):
        raw = json.dumps(dict(bot=None, multi_addressed=False,
                              brief_casual=False, requires_reply=True))
        client, create = client_for(completion(raw=raw, provider='anthropic'))
        with patch.object(llm, '_get_quick_analyze_client',
                          return_value=(client, 'anthropic')):
            config = self.config()
            config['LLMChatter.QuickAnalyze.Model'] = 'future-aux-model'
            self.assertIsNotNone(llm.quick_llm_analyze(
                None, config, 'Analyze', response_contract=ResponseContract('analysis'),
            ))
        self.assertEqual(create.call_args.kwargs['model'], 'future-aux-model')
        self.assertIn('output_config', create.call_args.kwargs)

    def test_target_logs_use_resolved_roles_and_reset(self):
        client, _ = client_for(completion('{"memory":"We met.","emote":null}'))
        with patch.object(llm.logger, 'info') as log:
            for _ in range(2):
                llm.call_llm(client, 'Remember', self.config(),
                             response_contract=ResponseContract('memory'))
            self.assertEqual(log.call_count, 1)
            self.assertEqual(log.call_args.args[2:],
                             ('memory', 'openai', 'a-future-model'))
            llm.reset_structured_diagnostics()
            llm.call_llm(client, 'Remember', self.config(),
                         response_contract=ResponseContract('memory'))
            self.assertEqual(log.call_count, 2)

    def test_host_startup_uses_normal_log_without_bridge_jsonl_or_api_probe(self):
        import screenshot_agent as vision
        raw = {'LLMChatter.Screenshot.Enable': '1',
               'LLMChatter.OpenAI.ApiKey': 'test-placeholder',
               'LLMChatter.Screenshot.VisionModel': 'actual-host-target',
               'LLMChatter.StructuredOutput.Enable': '1',
               'LLMChatter.RequestLog.Enable': '1',
               'LLMChatter.RequestLog.Path': '/logs/llm_requests.jsonl'}
        with patch.object(sys, 'argv', ['agent', '--config', 'unused']), \
                patch.object(vision, 'parse_config', return_value=raw), \
                patch.object(request_log, 'init_request_logger') as init, \
                patch.object(vision, '_create_vision_client') as create, \
                patch.object(vision.time, 'sleep', side_effect=KeyboardInterrupt), \
                patch.object(vision, 'log_structured_target') as target, \
                patch.object(vision, 'reset_structured_diagnostics') as reset:
            vision.main()
        init.assert_not_called()
        reset.assert_called_once()
        target.assert_called_once_with('vision', 'openai', 'actual-host-target',
                                       True, vision.log)
        self.assertFalse(create.return_value.mock_calls)

    def test_missing_dependency_startup_is_clear_and_off_needs_no_import(self):
        import screenshot_agent as vision
        log = Mock()
        with patch.object(llm.importlib.util, 'find_spec', return_value=None) as find:
            self.assertTrue(llm.check_structured_dependencies(False, log))
            find.assert_not_called()
            self.assertFalse(llm.check_structured_dependencies(True, log))
            self.assertIn('tools/requirements.txt', log.error.call_args.args[0])
            with patch.object(vision, '_create_vision_client') as create:
                with self.assertRaises(SystemExit) as stopped:
                    vision.run_agent({'structured_output': True})
                self.assertEqual(stopped.exception.code, 1)
                create.assert_not_called()

    def test_missing_validator_import_is_fail_closed_and_deduplicated(self):
        import screenshot_agent as vision
        original_import = builtins.__import__

        def missing(name, *args, **kwargs):
            if name == 'jsonschema':
                raise ModuleNotFoundError('jsonschema')
            return original_import(name, *args, **kwargs)

        client, create = client_for(completion())
        with patch.object(builtins, '__import__', side_effect=missing), \
                patch.object(llm.logger, 'log') as log:
            for _ in range(2):
                self.assertIsNone(llm.call_llm(client, self.prompt, self.config()))
            self.assertEqual([c.args[0] for c in log.call_args_list], [30, 10])
            self.assertIn('dependency_missing', str(log.call_args))
            self.assertIn('tools/requirements.txt', str(log.call_args))
            with patch.object(vision.log, 'log') as host_log:
                self.assertIsNone(vision.analyze_screenshot(
                    b'image', client, 'host-model', structured_output=True,
                ))
                self.assertIn('dependency_missing', str(host_log.call_args))
        self.assertEqual(create.call_count, 3)
        self.assertTrue(all('response_format' in c.kwargs
                            for c in create.call_args_list))

    def test_vision_global_flag_and_all_existing_transports(self):
        import screenshot_agent as vision
        data = dict.fromkeys(schema_for(ResponseContract('vision'))[1]['properties'])
        data['environment'] = 'Stone bridge over a stream.'
        for provider in PROVIDERS[:-2] + ('anthropic',):
            client, create = client_for(completion(json.dumps(data), provider=provider))
            self.assertEqual(vision.analyze_screenshot(
                b'image', client, 'future-vision', provider,
                structured_output=True,
            ), data)
            key = 'output_config' if provider == 'anthropic' else 'response_format'
            self.assertIn(key, create.call_args.kwargs)
            if provider == 'openrouter':
                self.assertTrue(create.call_args.kwargs['extra_body']['provider']
                                ['require_parameters'])
        client, _ = client_for(completion('prose ' + json.dumps(data)))
        with patch.object(vision.re, 'search', side_effect=AssertionError('regex')):
            self.assertIsNone(vision.analyze_screenshot(
                b'image', client, 'future-vision', structured_output=True,
            ))
        for value, expected in (('1', True), ('0', False)):
            config = vision.load_screenshot_config(
                {'LLMChatter.StructuredOutput.Enable': value},
            )
            self.assertEqual(config['structured_output'], expected)


if __name__ == '__main__':
    unittest.main()
