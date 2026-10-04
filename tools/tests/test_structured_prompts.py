"""Contract plumbing and pinned legacy prompt/RNG regressions."""

import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import chatter_shared as shared
from chatter_structured import EMOTES, schema_for, structured_output_enabled
from chatter_threads import THREAD_REPORT_FIELD, THREAD_REPORT_OBJECT


def cases():
    singles = [
        {}, {'allow_action': False}, {'skip_emote': True},
        {'skip_action_rng': True}, {'message_only': True},
        {'allow_emote_only': True},
        {'message_only': True, 'allow_narrator_message': True},
        {'extra_field': THREAD_REPORT_FIELD,
         'extra_rule': 'Legacy thread rule.'},
    ]
    conversations = [
        {}, {'allow_action': False}, {'message_only': True},
        {'allow_emote_only': True},
        {'message_only': True, 'allow_narrator_messages': True},
        {'addressee_names': ['Alice', 'Bob']},
        {'trailing_object': THREAD_REPORT_OBJECT,
         'extra_rule': 'Legacy thread rule.'},
        {'message_only': True, 'trailing_object': THREAD_REPORT_OBJECT},
    ]
    for kind, variants in (('single', singles), ('conversation', conversations)):
        for index, kwargs in enumerate(variants):
            for draw in (0.0, 0.99):
                for language in ('', '\nUse French for all dialogue.'):
                    key = f'{kind}-{index}-{draw}-{bool(language)}'
                    yield key, kind, kwargs, draw, language


def make_prompt(kind, kwargs, draw, language, *, annotated=True):
    kwargs = dict(kwargs)
    if annotated and ('extra_field' in kwargs or 'trailing_object' in kwargs):
        kwargs.update(include_thread=True,
                      thread_speaker_names=('Alice', 'Bob'))
    with patch.object(shared.random, 'random', return_value=draw) as rng, \
            patch.object(shared, 'get_language_rule', return_value=language), \
            patch.object(shared, '_action_chance', 0.5), \
            patch.object(shared, '_emote_chance', 0.5), \
            patch.object(shared, '_action_disabled', False):
        prompt = (shared.append_json_instruction('Scene', **kwargs)
                  if kind == 'single' else
                  shared.append_conversation_json_instruction(
                      'Scene', ['Alice', 'Bob'], 3, **kwargs,
                  ))
        return prompt, rng.call_count


def fingerprint(prompt, draws):
    text = json.dumps([str(prompt), prompt.user_prompt,
                       prompt.system_prompt], ensure_ascii=False)
    return {'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'draws': draws}


class PromptTests(unittest.TestCase):
    def test_legacy_bytes_and_rng_match_preimplementation_baseline(self):
        baseline = json.loads((Path(__file__).parent / 'fixtures' /
                               'structured_legacy_prompts.json').read_text())
        for key, kind, kwargs, draw, language in cases():
            with self.subTest(key=key):
                prompt, draws = make_prompt(kind, kwargs, draw, language)
                self.assertEqual(fingerprint(prompt, draws), baseline[key])
                self.assertIsNotNone(prompt.response_contract)
                self.assertTrue(prompt.structured_system_prompt)
                enabled = prompt.structured_system_prompt
                example, _ = json.JSONDecoder().raw_decode(
                    enabled[enabled.index('{'):],
                )
                Draft202012Validator(
                    schema_for(prompt.response_contract)[1],
                ).validate(example)
                self.assertNotIn('true|false', enabled)
                self.assertNotIn('ONLY the JSON array', enabled)
                if prompt.response_contract.emote:
                    self.assertIn(', '.join(EMOTES), enabled)
                if prompt.response_contract.action == 'optional':
                    self.assertIsNotNone(example['action'])
                if language:
                    self.assertIn(language, prompt.structured_system_prompt)

    def test_concat_preserves_selected_metadata_and_conflicts(self):
        prompt = shared.append_json_instruction('Scene', message_only=True)
        for result in (prompt + ' suffix', 'prefix ' + prompt):
            self.assertEqual(result.response_contract, prompt.response_contract)
            self.assertEqual(result.structured_system_prompt,
                             prompt.structured_system_prompt)
        result = prompt
        result += ' more'
        self.assertEqual(result.user_prompt, 'Scene more')
        other = shared.append_conversation_json_instruction(
            'Other', ['Alice'], 1, message_only=True,
        )
        mixed = prompt + other
        self.assertTrue(mixed.contract_conflict)
        self.assertEqual(mixed.response_contract, prompt.response_contract)
        self.assertEqual(mixed.system_prompt, prompt.system_prompt)
        no_system = shared.PromptParts('Prefix', '')
        self.assertEqual((no_system + other).response_contract,
                         other.response_contract)

    def test_metadata_error_preserves_legacy_and_marks_enabled_failure(self):
        options = dict(message_only=True, extra_field=THREAD_REPORT_FIELD)
        legacy = shared.append_json_instruction('Scene', **options)
        invalid = shared.append_json_instruction(
            'Scene', **options, include_thread=True, thread_speaker_names=('',),
        )
        self.assertEqual(str(invalid), str(legacy))
        self.assertEqual(invalid.system_prompt, legacy.system_prompt)
        self.assertEqual(invalid.user_prompt, legacy.user_prompt)
        self.assertTrue(invalid.contract_conflict)
        self.assertTrue((invalid + 'repair').contract_conflict)

    def test_global_flag_uses_shared_string_convention(self):
        for value in ('1', '1 ', 1):
            self.assertTrue(structured_output_enabled({
                'LLMChatter.StructuredOutput.Enable': value,
            }))
        for value in ('0', 0, '', None):
            self.assertFalse(structured_output_enabled({
                'LLMChatter.StructuredOutput.Enable': value,
            }))
        self.assertFalse(structured_output_enabled({}))

    def test_repairs_retain_contract_without_array_instruction(self):
        prompt = shared.append_conversation_json_instruction(
            'Original context', ['Alice', 'Bob'], 3, message_only=True,
        )
        legacy = shared.build_conversation_json_repair_prompt(
            prompt, ['Alice', 'Bob'], message_only=True,
        )
        self.assertIn('JSON array', legacy)
        self.assertNotIsInstance(legacy, shared.PromptParts)
        repaired = shared.build_conversation_json_repair_prompt(
            prompt, ['Alice', 'Bob'], message_only=True,
            structured_output=True,
        )
        self.assertEqual(repaired.response_contract, prompt.response_contract)
        self.assertEqual(repaired.user_prompt.count('Original context'), 1)
        self.assertNotIn('JSON array', repaired.user_prompt)
        self.assertNotIn('JSON array', repaired.structured_system_prompt)
        brief = shared.build_brief_casual_repair_prompt(prompt)
        self.assertEqual(brief.response_contract, prompt.response_contract)
        self.assertEqual(schema_for(brief.response_contract),
                         schema_for(prompt.response_contract))

    def test_thread_declarations_have_matching_typed_flags(self):
        count = 0
        for path in TOOLS.glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if not isinstance(node, ast.Call):
                    continue
                kwargs = {k.arg: k.value for k in node.keywords}
                legacy = any(isinstance(value, ast.Name) and value.id in (
                    'THREAD_REPORT_FIELD', 'THREAD_REPORT_OBJECT',
                ) for value in kwargs.values())
                flag = kwargs.get('include_thread')
                typed = isinstance(flag, ast.Constant) and flag.value is True
                self.assertEqual(legacy, typed, f'{path.name}:{node.lineno}')
                if legacy:
                    count += 1
                    self.assertIn('thread_speaker_names', kwargs)
        self.assertEqual(count, 6)

    def test_standalone_guild_repairs_preserve_actual_builder_contract(self):
        import chatter_guild_login as login
        import chatter_guild_player as player
        participants = [
            {'guid': i + 1, 'name': name, 'zone_id': 12, 'map_id': 0,
             'speaker': {'class': 'Mage', 'race': 'Human', 'gender': 'female',
                         'level': 80, 'traits': ['steadfast'], 'tone': 'warm',
                         'backstory': ''}}
            for i, name in enumerate(('Alice', 'Bob'))
        ]
        config = {'LLMChatter.StructuredOutput.Enable': '1',
                  'LLMChatter.ChatterMode': 'normal'}
        response = json.dumps([
            {'speaker': name, 'message': 'Good to see you.'}
            for name in ('Alice', 'Bob')
        ])
        for module in (login, player):
            prompts = []

            def completion(client, prompt, config, **kwargs):
                prompts.append(prompt)
                return None if len(prompts) == 1 else response

            with patch.object(module, 'call_llm', side_effect=completion):
                if module is login:
                    result = login._generate_multi(
                        None, config, 1, participants, 'Keepers', 'Alliance',
                        'Calwen', False, 100, {},
                    )
                else:
                    result = player._generate_multi_reply(
                        None, None, config, 1, participants, 'multi_reply',
                        'Keepers', 'Alliance', 'Calwen', 'Hello everyone.', '',
                        False, False, False, {},
                    )
            self.assertEqual(len(result), 2)
            self.assertEqual(len(prompts), 2)
            self.assertEqual(prompts[1].response_contract,
                             prompts[0].response_contract)
            self.assertEqual(prompts[1].response_contract.message_count, 2)
            self.assertEqual(prompts[1].response_contract.kind, 'conversation')
            self.assertFalse(prompts[1].contract_conflict)


if __name__ == '__main__':
    unittest.main()
