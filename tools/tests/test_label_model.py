"""Calls can be routed to a second model by their label."""

import unittest

import test_persona_coherence  # dependency stubs and tools path
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


if __name__ == '__main__':
    unittest.main()
