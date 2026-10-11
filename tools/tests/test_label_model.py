"""Calls can be routed to a second model by their label."""

import unittest
from unittest import mock

import test_persona_coherence  # dependency stubs and tools path
import chatter_healthcheck
import chatter_llm
from chatter_llm import label_model

ROUTED = {
    'LLMChatter.Provider': 'anthropic',
    'LLMChatter.Model': 'small-model',
    'LLMChatter.LabelModel': 'large-model',
    'LLMChatter.LabelModel.Labels': ' group_*, reaction_bg_?ode ,'
                                    'general_player_msg',
}


class _Block:
    text = 'ok'


class _Messages:
    def __init__(self):
        self.models = []

    def create(self, **kwargs):
        self.models.append(kwargs['model'])
        response = type('Response', (), {})()
        response.content = [_Block()]
        return response


class _Client:
    def __init__(self):
        self.messages = _Messages()


class LabelModelTests(unittest.TestCase):
    def test_patterns_match_labels(self):
        self.assertEqual(label_model('group_idle', ROUTED), 'large-model')
        self.assertEqual(
            label_model('reaction_bg_node', ROUTED), 'large-model'
        )
        self.assertEqual(
            label_model('general_player_msg', ROUTED), 'large-model'
        )
        self.assertIsNone(label_model('ambient_statement', ROUTED))
        self.assertIsNone(label_model('general_player_msg_x', ROUTED))
        self.assertIsNone(label_model('', ROUTED))

    def test_unconfigured_routes_nothing(self):
        self.assertIsNone(label_model('group_idle', {}))
        self.assertIsNone(label_model(
            'group_idle', {'LLMChatter.LabelModel.Labels': 'group_*'}
        ))
        self.assertIsNone(label_model(
            'group_idle', {'LLMChatter.LabelModel': 'large-model'}
        ))

    def test_call_llm_uses_the_routed_model(self):
        client = _Client()
        chatter_llm.call_llm(client, 'prompt', ROUTED, label='group_idle')
        chatter_llm.call_llm(
            client, 'prompt', ROUTED, label='ambient_statement'
        )
        self.assertEqual(
            client.messages.models, ['large-model', 'small-model']
        )


class _NotFound(Exception):
    status_code = 404


class LabelModelHealthCheckTests(unittest.TestCase):
    def _run(self, config, do_llm_probe=True, fail_model=None):
        probed = []

        def probe(_config, model, client=None):
            probed.append(model)
            if model == fail_model:
                raise _NotFound(f"model '{model}' not found")
            return 'OK'

        passed = {'status': 'pass'}
        with mock.patch.multiple(
            chatter_healthcheck,
            _check_config_file=lambda *_: passed,
            _check_module_enabled=lambda *_: passed,
            _check_provider_config=lambda *_: passed,
            _check_database=lambda *_: passed,
            _check_tables=lambda *_: passed,
            _probe_anthropic=probe,
        ):
            results = chatter_healthcheck.run_all_checks(
                config, do_llm_probe=do_llm_probe
            )
        return {r.get('id'): r for r in results}, probed

    def test_routed_model_gets_its_own_probe(self):
        results, probed = self._run(ROUTED)
        self.assertEqual(probed, ['small-model', 'large-model'])
        self.assertEqual(results['llm_probe']['status'], 'pass')
        label = results['label_model_probe']
        self.assertEqual(label['status'], 'pass')
        self.assertEqual(
            label['title'], 'LabelModel connectivity (live test)'
        )
        self.assertIn('large-model', label['message'])

    def test_bad_routed_model_fails_on_its_own_line(self):
        results, _ = self._run(ROUTED, fail_model='large-model')
        self.assertEqual(results['llm_probe']['status'], 'pass')
        label = results['label_model_probe']
        self.assertEqual(label['status'], 'fail')
        self.assertIn("'large-model'", label['message'])
        self.assertIn('LLMChatter.LabelModel', label['hint'])
        self.assertTrue(chatter_healthcheck.has_critical_failure(
            list(results.values())
        ))

    def test_unconfigured_routing_is_not_probed(self):
        for key in ('LLMChatter.LabelModel',
                    'LLMChatter.LabelModel.Labels'):
            config = dict(ROUTED, **{key: ' '})
            results, probed = self._run(config)
            self.assertEqual(probed, ['small-model'])
            self.assertNotIn('label_model_probe', results)

    def test_label_list_without_patterns_is_not_probed(self):
        # Nothing is routed, so LabelModel must not fail startup.
        config = dict(ROUTED, **{'LLMChatter.LabelModel.Labels': ' , ,'})
        self.assertIsNone(chatter_llm.label_model('group_idle', config))
        results, probed = self._run(config)
        self.assertEqual(probed, ['small-model'])
        self.assertNotIn('label_model_probe', results)

    def test_disabled_live_probe_skips_both(self):
        results, probed = self._run(ROUTED, do_llm_probe=False)
        self.assertEqual(probed, [])
        self.assertEqual(results['llm_probe']['status'], 'skip')
        self.assertNotIn('label_model_probe', results)


if __name__ == '__main__':
    unittest.main()
