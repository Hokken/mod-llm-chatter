"""Reviewed call-site inventory plus real caller/boundary regressions."""

import ast
from collections import Counter
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import chatter_llm as llm
import chatter_shared as shared
from test_structured_requests import client_for, completion


def inventory():
    entries = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self, filename):
            self.filename = filename
            self.owner = []
            self.ordinals = Counter()

        def visit_FunctionDef(self, node):
            self.owner.append(node.name)
            self.generic_visit(node)
            self.owner.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node):
            called = ast.unparse(node.func)
            keywords = {k.arg: k.value for k in node.keywords}
            kind = None
            if called in ('call_llm', 'quick_llm_analyze'):
                kind = 'generation'
            elif called == 'build_conversation_json_repair_prompt':
                kind = 'repair'
            elif 'include_thread' in keywords:
                kind = 'thread'
            elif (called in ('create_chat_completion', 'structured_completion')
                  or called.endswith(('.messages.create',
                                      '.chat.completions.create'))
                  or (self.filename in ('chatter_llm.py', 'llm_compat.py')
                      and called in ('operation', 'observed_operation'))):
                kind = 'transport'
            if kind:
                base = ':'.join((self.filename, '.'.join(self.owner), called))
                self.ordinals[base] += 1
                entries[f'{base}:{self.ordinals[base]}'] = (kind, node)
            self.generic_visit(node)

    for path in sorted(TOOLS.glob('*.py')):
        Visitor(path.name).visit(ast.parse(path.read_text(encoding='utf-8')))
    return entries


class CoverageTests(unittest.TestCase):
    def test_global_config_defaults_match_templates_and_host(self):
        import screenshot_agent as vision
        from chatter_structured import structured_output_enabled
        key = 'LLMChatter.StructuredOutput.Enable'
        configs = [{}, {key: '0'}, {key: '1'}]
        for relative in ('conf/mod_llm_chatter.conf.dist',
                         'conf/presets/mod_ll_chatter_quieter.conf.dist'):
            config = shared.parse_config(str(TOOLS.parent / relative))
            self.assertEqual(config[key], '0')
            configs.append(config)
        for config in configs:
            expected = config.get(key) == '1'
            self.assertEqual(structured_output_enabled(config), expected)
            self.assertEqual(vision.load_screenshot_config(config)
                             ['structured_output'], expected)

    def config(self):
        return {'LLMChatter.Provider': 'openai',
                'LLMChatter.Model': 'future-model',
                'LLMChatter.StructuredOutput.Enable': '1'}

    def test_reviewed_inventory_has_no_new_or_missing_routes(self):
        expected = json.loads((Path(__file__).parent / 'fixtures' /
                               'structured_callers.json').read_text())
        actual = inventory()
        self.assertEqual(set(expected), set(actual))
        allowed = {'annotated', 'explicit', 'text', 'probe', 'offline',
                   'transport', 'repair', 'thread'}
        for key, category in expected.items():
            self.assertIn(category, allowed)
            kind, node = actual[key]
            if category == 'explicit':
                self.assertIn('response_contract', {k.arg for k in node.keywords})
            text_marker = next((k.value for k in node.keywords
                                if k.arg == 'free_text'), None)
            if category == 'text':
                self.assertIsInstance(text_marker, ast.Constant)
                self.assertIs(text_marker.value, True)
            else:
                self.assertIsNone(text_marker, key)
            if kind in ('thread', 'repair'):
                self.assertEqual(category, kind)
        self.assertEqual(sum(kind == 'thread' for kind, _ in actual.values()), 6)
        self.assertEqual(sum(kind == 'repair' for kind, _ in actual.values()), 5)

    def test_ambient_enabled_repair_reaches_real_shared_boundary(self):
        import test_guild_general_threads as fixture
        fixture._reset()
        db = fixture._DB()
        prompts = []
        client, operation = client_for(None)
        config = {**fixture.RP, **self.config()}

        def call(client, prompt, config, **kwargs):
            prompts.append(prompt)
            contract = prompt.response_contract
            self.assertEqual(contract.kind, 'conversation')
            names = ['Stranger'] if len(prompts) == 1 else ['Aldric', 'Mira']
            messages = []
            for name in names:
                item = {'speaker': name, 'message': 'The road is quiet.'}
                if not contract.message_only:
                    item.update(emote=None, action=(
                        'looks around' if contract.action == 'required' else None
                    ))
                messages.append(item)
            wire = {'messages': messages}
            if contract.thread:
                wire['thread'] = None
            operation.return_value = completion(json.dumps(wire))
            return llm.call_llm(client, prompt, config, **kwargs)

        patches = fixture._ambient_patches(db, '', [])
        patches[0] = patch.object(fixture.ambient, 'call_llm', side_effect=call)
        bots = [dict(fixture._BOT), dict(fixture._BOT, guid=102, name='Mira')]
        fixture._run(patches, lambda: fixture.ambient.process_conversation(
            db, db.cursor(), client, config, dict(fixture._AMBIENT_REQUEST), bots,
        ))
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[1].response_contract, prompts[0].response_contract)
        self.assertEqual(len(db.inserted), 2)
        self.assertTrue(all('response_format' in call.kwargs
                            for call in operation.call_args_list))

    def test_ambient_invalid_wire_queues_nothing_and_adopts_no_report(self):
        import test_guild_general_threads as fixture
        fixture._reset()
        db = fixture._DB()
        client, _ = client_for(completion('metadata: {"message":"leaked"}'))
        patches = fixture._ambient_patches(db, '', [])
        patches[0] = patch.object(fixture.ambient, 'call_llm', wraps=llm.call_llm)
        fixture._run(patches, lambda: fixture.ambient.process_statement(
            db, db.cursor(), client, {**fixture.RP, **self.config()},
            dict(fixture._AMBIENT_REQUEST), dict(fixture._BOT, persona=None),
        ))
        self.assertEqual(len(db.inserted), 0)
        state = fixture.th.snapshot(fixture.th.general_key(12, 'Alliance'))
        self.assertTrue(state is None or not state.pending)

    def test_memory_and_analysis_failure_keep_existing_fallbacks(self):
        import chatter_memory as memory
        client, operation = client_for(completion('not JSON'))
        with patch.object(memory, 'get_llm_client', return_value=client):
            self.assertEqual(memory._call_llm_for_memory(
                self.config(), bot_name='Alice', bot_class='Mage',
                bot_race='Human', location='Elwynn Forest',
            ), (None, None))
        self.assertIn('memory', operation.call_args.kwargs['response_format']
                      ['json_schema']['schema']['properties'])
        with patch.object(llm, '_get_quick_analyze_client',
                          return_value=(None, 'openai')):
            result = shared.find_addressed_bot(
                'Alice, can you help?', ['Alice', 'Bob'], client, self.config(),
            )
        self.assertEqual(result['bot'], 'Alice')
        self.assertFalse(result['reply_optional'])
        self.assertIn('requires_reply', operation.call_args.kwargs['response_format']
                      ['json_schema']['schema']['properties'])

    def test_real_free_text_owners_do_not_request_schema(self):
        import chatter_group_state as state
        import chatter_identity as identity
        client, operation = client_for(completion('Farewell, friends.'))
        db = Mock()
        state._generate_farewell(
            db, client, self.config(), 'Alice', 'Human', 'Mage', 'female',
            ['warm'], 'normal', 1, 1,
        )
        self.assertNotIn('response_format', operation.call_args.kwargs)
        operation.reset_mock()
        traits = ('warm', 'steady', 'curious')
        row = dict(zip(identity._FIELDS[:3], traits))
        with patch.object(identity, '_read_identity', return_value=row), \
                patch.object(identity, 'get_llm_client', return_value=client), \
                patch.object(identity, '_cooling_down', return_value=False):
            identity._generate_field(
                db, self.config(), 1, 0, 'Alice', 'tone', traits,
                'Describe a tone', 60, 80,
            )
        operation.assert_called_once()
        self.assertNotIn('response_format', operation.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
