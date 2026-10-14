"""Wire validation fixtures; no SDK, network or database calls."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from itertools import product
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jsonschema import Draft202012Validator
from chatter_structured import (
    EMOTES, ResponseContract, StructuredOutputError,
    conversation_contract, render_structured_format, schema_for,
    statement_contract, validate_and_normalize,
)
from chatter_threads import parse_thread_report
from chatter_shared import count_conversation_items, parse_conversation_response


REPORT = {
    'topic': 'the road', 'energy': 'medium', 'subject_changed': False,
    'open_point': '', 'feelings': [
        {'speaker': ' aLiCe ', 'feeling': 'Uneasy about the ruins'},
        {'speaker': 'Unknown', 'feeling': 'Should be ignored'},
    ],
}


class ContractTests(unittest.TestCase):
    def normalize(self, data, contract):
        return json.loads(validate_and_normalize(json.dumps(data), contract))

    def reject(self, data, contract):
        with self.assertRaises(StructuredOutputError):
            self.normalize(data, contract)

    def test_real_variants_have_closed_valid_stable_schemas(self):
        for conversation, message_only, emote, action, thread in product(
            (False, True), repeat=5,
        ):
            options = dict(message_only=message_only, emote=emote,
                           action=action, thread=thread,
                           thread_speaker_names=('Alice', 'Bob'))
            contract = (conversation_contract(('Alice', 'Bob'), 3, **options)
                        if conversation else statement_contract(**options))
            name, schema = schema_for(contract)
            Draft202012Validator.check_schema(schema)
            self.assertLessEqual(len(name), 64)
            self.check_closed(schema)
            changed = replace(contract, speaker_names=('Other',),
                              message_count=10,
                              thread_speaker_names=('Other',))
            self.assertEqual((name, schema), schema_for(changed))
            schema['properties'].clear()
            self.assertTrue(schema_for(contract)[1]['properties'])
            rendered = render_structured_format(contract)
            start = rendered.index('{')
            example, _ = json.JSONDecoder().raw_decode(rendered[start:])
            Draft202012Validator(schema_for(contract)[1]).validate(example)
            self.normalize(example, contract)

    def check_closed(self, schema):
        if schema.get('type') == 'object':
            self.assertIs(schema['additionalProperties'], False)
            self.assertEqual(set(schema['required']),
                             set(schema['properties']))
        for value in schema.values():
            if isinstance(value, dict):
                self.check_closed(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.check_closed(item)

    def test_ordinary_policy_and_message_only(self):
        data = {'message': 'Hello', 'emote': None, 'action': None}
        contract = statement_contract()
        self.assertEqual(self.normalize(data, contract), data)
        for field, value in (('emote', 'nod'), ('action', 'waves')):
            self.reject({**data, field: value}, contract)
        self.reject({**data, 'extra': True}, contract)
        self.reject({'message': 'Hello'}, contract)
        self.reject({**data, 'message': None}, contract)
        self.reject({**data, 'emote': 'invented'},
                    statement_contract(emote=True))
        self.assertEqual(self.normalize(
            {**data, 'emote': 'nod', 'action': 'waves'},
            statement_contract(emote=True, action=True),
        )['emote'], 'nod')
        self.reject(data, statement_contract(message_only=True))
        self.assertEqual(self.normalize({'message': 'Hello'},
                                        statement_contract(message_only=True)),
                         {'message': 'Hello'})

    def test_conversation_action_and_directed_contract(self):
        contract = conversation_contract(
            ('Alice', 'Bob'), 2, action=True, emote=True,
            addressee_names=('Alice', 'Bob'),
        )
        data = {'messages': [{'speaker': 'Alice', 'message': 'Hello',
                              'emote': 'nod', 'action': 'waves',
                              'addressee': 'Bob'}]}
        result = self.normalize(data, contract)
        self.assertEqual(result, data['messages'])
        for key in ('action', 'addressee'):
            invalid = deepcopy(data)
            invalid['messages'][0][key] = None
            self.reject(invalid, contract)
        # Count and selected-speaker coverage belong to domain callers.
        self.assertEqual(self.normalize({'messages': []}, contract), [])
        rendered = render_structured_format(contract)
        example, _ = json.JSONDecoder().raw_decode(
            rendered[rendered.index('{'):],
        )
        self.normalize(example, contract)

    def test_empty_speech_requires_eligible_nonnull_emote(self):
        data = {'message': '', 'emote': 'nod', 'action': None}
        self.reject(data, statement_contract(emote=True))
        allowed = statement_contract(emote=True, emote_only=True)
        self.assertEqual(self.normalize(data, allowed), data)
        self.reject({**data, 'emote': None}, allowed)
        self.reject({**data, 'emote': 'none'}, allowed)
        self.reject({**data, 'message': '  ', 'emote': None}, allowed)
        self.reject({'message': ''}, statement_contract(message_only=True))

    def test_complete_json_only(self):
        contract = statement_contract(message_only=True)
        for raw in (
            '```json\n{"message":"Hi"}\n```',
            'Here: {"message":"Hi"}', '{"message":"Hi"} trailing',
            '{"message":"Hi", "message":"Bye"}',
            '{"message":NaN}', '{"message":Infinity}',
            '{"message":-Infinity}', '{"message":', 'null', '[]', '', None,
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(StructuredOutputError):
                    validate_and_normalize(raw, contract)

    def test_report_normalization_and_legacy_round_trip(self):
        contract = conversation_contract(
            ('Alice', 'Bob'), 2, message_only=True, thread=True,
            thread_speaker_names=('Alice', 'Bob'),
        )
        messages = [{'speaker': 'Alice', 'message': 'The ruins worry me.'},
                    {'speaker': 'Bob', 'message': 'We will be careful.'}]
        wire = {'messages': messages, 'thread': REPORT}
        text = validate_and_normalize(json.dumps(wire), contract)
        self.assertEqual(count_conversation_items(text), 2)
        self.assertEqual(len(parse_conversation_response(
            text, ['Alice', 'Bob'],
        )), 2)
        report = parse_thread_report(text, ('Alice', 'Bob'))
        self.assertEqual(report['feelings'],
                         {'Alice': 'Uneasy about the ruins'})
        self.assertIs(report['subject_changed'], False)
        for feelings, expected in (([], {}),
                                   ([{'speaker': 'Unknown', 'feeling': '?'}],
                                    {})):
            wire['thread'] = {**REPORT, 'feelings': feelings}
            self.assertEqual(self.normalize(wire, contract)[-1]['thread']
                             ['feelings'], expected)
        wire['thread'] = {**REPORT, 'feelings': [
            {'speaker': 'Alice', 'feeling': 'one'},
            {'speaker': 'ALICE', 'feeling': 'two'},
        ]}
        self.assertEqual(self.normalize(wire, contract), messages)
        wire['thread'] = None
        self.assertEqual(self.normalize(wire, contract), messages)
        for key, value in (('subject_changed', 'false'), ('energy', 'bad'),
                           ('feelings', {}), ('topic', None)):
            wire['thread'] = {**REPORT, key: value}
            self.reject(wire, contract)
        solo = statement_contract(message_only=True, thread=True,
                                  thread_speaker_names=('Alice',))
        self.assertEqual(self.normalize({'message': 'Hi', 'thread': REPORT},
                                        solo)['thread']['feelings'],
                         {'Alice': 'Uneasy about the ruins'})

    def test_bespoke_contracts(self):
        analysis = ResponseContract('analysis')
        data = dict(bot=None, multi_addressed=False,
                    brief_casual=True, requires_reply=True)
        self.assertEqual(self.normalize(data, analysis), data)
        self.reject({**data, 'requires_reply': 'true'}, analysis)
        self.reject({**data, 'bot': 12}, analysis)
        memory = ResponseContract('memory')
        self.normalize({'memory': 'We met.', 'emote': None}, memory)
        self.reject({'memory': 'We met.', 'emote': 'invented'}, memory)
        self.reject({'memory': 'We met.', 'emote': 'none'}, memory)
        self.reject({'message': 'Hi', 'emote': 'none', 'action': None},
                    statement_contract(emote=True))
        self.reject({'messages': [
            {'speaker': 'Alice', 'message': 'Hi',
             'emote': 'none', 'action': None},
        ]}, conversation_contract(('Alice',), 1, emote=True))
        vision = ResponseContract('vision')
        _, schema = schema_for(vision)
        data = dict.fromkeys(schema['properties'])
        self.assertEqual(self.normalize(data, vision), data)
        self.normalize({**data, 'weather': 'none'}, vision)
        self.reject({**data, 'weather': 'hurricane'}, vision)
        for contract in (analysis, memory, vision):
            Draft202012Validator.check_schema(schema_for(contract)[1])
            self.check_closed(schema_for(contract)[1])

    def test_contract_is_immutable_and_rejects_bad_options(self):
        contract = conversation_contract(['Alice'], 1)
        self.assertEqual(contract.speaker_names, ('Alice',))
        with self.assertRaises(FrozenInstanceError):
            contract.kind = 'memory'
        for kwargs in ({'kind': 'unknown'},
                       {'kind': 'memory', 'thread': True},
                       {'kind': 'statement', 'emote_only': True},
                       {'kind': 'statement', 'thread': True},
                       {'kind': 'statement', 'thread': True,
                        'thread_speaker_names': ('',)},
                       {'kind': 'statement', 'addressee': True}):
            with self.assertRaises(ValueError):
                ResponseContract(**kwargs)
        self.assertIsInstance(EMOTES, tuple)


if __name__ == '__main__':
    unittest.main()
