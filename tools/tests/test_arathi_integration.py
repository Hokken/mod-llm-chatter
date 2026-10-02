#!/usr/bin/env python3
"""Execute handlers through real dispatch/prompts/reaction parsing.

Only external LLM and DB boundaries are replaced. This does not execute
the C++ final-send guard or prove live audibility.
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import unittest
from unittest.mock import patch

import test_battleground_carrier_messages  # dependency stubs/tools path
import chatter_battlegrounds as handlers
import chatter_shared as shared
from test_bg_delivery_contract import envelope
from test_arathi_batches import changes
from test_arathi_resource_race import context


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.config = {'LLMChatter.TalentInjectionChance': 0}
        self.mark = self.stack.enter_context(patch.object(handlers, '_mark_event'))
        self.insert = self.stack.enter_context(patch.object(
            shared, 'insert_chat_message', return_value=123))
        self.llm = self.stack.enter_context(patch.object(
            shared, 'call_llm', return_value='{"message":"Hold the base."}'))
        self.stack.enter_context(patch('chatter_raid_base.get_bot_traits',
            return_value={'bot_name': 'Observer', 'class': 'Warrior',
                          'race': 'Human'}))
        self.stack.enter_context(patch(
            'chatter_raid_base.get_lightweight_bot_data',
            return_value={'bot_name': 'Observer', 'class': 'Warrior',
                          'race': 'Human'}))
        self.stack.enter_context(patch(
            'chatter_bg_prompts.pick_personality_spices', return_value=[]))
        self.stack.enter_context(patch(
            'chatter_bg_prompts.build_environmental_context_lines',
            return_value=[]))
        self.gate = self.stack.enter_context(patch.object(
            handlers, 'should_defer_party_generation', return_value=False))

    def event(self, kind, event_id=99):
        extra = dict(envelope(), **context())
        extra.update(party_bot_guids=[100], raid_bot_guids=[200],
                     node_changes=changes(), ab_objective_status=True,
                     queue_type_id=32)
        return {'id': event_id, 'event_type': kind,
                'extra_data': json.dumps(extra)}

    def test_objective_handlers_keep_original_link_and_channel(self):
        for kind, handler in (
            ('bg_node_captured', handlers.process_bg_node_event),
            ('bg_score_milestone', handlers.process_bg_score_milestone_event),
            ('bg_idle_chatter', handlers.process_bg_idle_chatter_event),
        ):
            for mode in ('normal', 'roleplay'):
                with self.subTest(kind=kind, mode=mode):
                    self.insert.reset_mock()
                    event = self.event(kind)
                    original = event['extra_data']
                    self.config['LLMChatter.ChatterMode'] = mode
                    self.assertTrue(handler(None, None, self.config, event))
                    self.insert.assert_called_once()
                    call = self.insert.call_args
                    node = kind == 'bg_node_captured'
                    self.assertEqual(call.args[1], 200 if node else 100)
                    for key, value in dict(event_id=99, group_id=91,
                            channel='battleground' if node else 'party',
                            owner_subsystem='bg').items():
                        self.assertEqual(call.kwargs[key], value)
                    self.assertEqual(event['extra_data'], original)
                    if not node:
                        self.assertEqual(call.kwargs['delivery_reason'], kind)

    def test_all_ab_transitions_use_bg_channel_without_party_duplicate(self):
        for transition, previous, state in (
            ('claim', 0, 3), ('assault', 2, 3), ('counter_claim', 4, 3),
            ('defence', 4, 1), ('capture', 3, 1), ('state_update', 0, 1),
        ):
            for party, crowd in (([100], [200]), ([100], []), ([], [200])):
                with self.subTest(transition=transition, party=party, crowd=crowd):
                    self.insert.reset_mock()
                    event = self.event('bg_node_captured')
                    extra = json.loads(event['extra_data'])
                    extra['raid_bot_guids'] = crowd
                    extra['party_bot_guids'] = party
                    extra['node_changes'] = changes()[:1]
                    extra['node_changes'][0].update(
                        transition=transition, prev_state=previous, state=state)
                    event['extra_data'] = json.dumps(extra)
                    self.assertTrue(handlers.process_bg_node_event(
                        None, None, self.config, event))
                    self.insert.assert_called_once()
                    self.assertEqual(self.insert.call_args.kwargs['channel'],
                                     'battleground')
                    self.assertEqual(self.insert.call_args.args[1],
                                     200 if crowd else 100)

    def test_ab_node_without_any_bot_skips_generation(self):
        event = self.event('bg_node_captured')
        extra = json.loads(event['extra_data'])
        extra.update(party_bot_guids=[], raid_bot_guids=[])
        event['extra_data'] = json.dumps(extra)
        self.assertFalse(handlers.process_bg_node_event(
            None, None, self.config, event))
        self.llm.assert_not_called()
        self.insert.assert_not_called()

    def test_ey_nodes_keep_party_channel(self):
        event = self.event('bg_node_contested')
        extra = json.loads(event['extra_data'])
        extra.update(bg_type_id=7, bg_map_id=566, node_name='Mage Tower',
                     new_owner='Alliance')
        extra.pop('node_changes')
        extra.pop('ab_state')
        event['extra_data'] = json.dumps(extra)
        self.assertTrue(handlers.process_bg_node_event(
            None, None, self.config, event))
        self.insert.assert_called_once()
        self.assertEqual(self.insert.call_args.kwargs['channel'], 'party')

    def test_inflight_old_match_and_new_match_keep_distinct_event_links(self):
        entered, release = threading.Event(), threading.Event()
        old = self.event('bg_score_milestone', 101)
        new = self.event('bg_score_milestone', 102)
        data = json.loads(new['extra_data'])
        data.update(bg_match_token='lifetime-2', bg_observed_ms=9000,
                    group_id=92, player_subgroup=3, party_bot_guids=[101])
        new['extra_data'] = json.dumps(data)
        original = old['extra_data']

        def generate(*args, **kwargs):
            if '#101:' in kwargs['context']:
                entered.set()
                if not release.wait(5):
                    raise AssertionError('test failed to release generation')
            return '{"message":"Hold the base."}'

        self.llm.side_effect = generate
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(handlers.process_bg_score_milestone_event,
                                 None, None, self.config, old)
            try:
                self.assertTrue(entered.wait(5))
                self.assertTrue(handlers.process_bg_score_milestone_event(
                    None, None, self.config, new))
            finally:
                release.set()
            self.assertTrue(future.result(timeout=5))
        rows = [call.kwargs for call in self.insert.call_args_list]
        self.assertEqual([(r['event_id'], r['group_id']) for r in rows],
                         [(102, 92), (101, 91)])
        self.assertEqual(old['extra_data'], original)
        # Old output may be inserted, but is never retargeted to the new
        # match. C++ must reject it using its original event JSON.

    def test_idle_party_gate_defers_before_generation(self):
        self.gate.return_value = True
        with patch.object(handlers, 'defer_event_for_party_gate') as defer:
            self.assertFalse(handlers.process_bg_idle_chatter_event(
                None, None, self.config, self.event('bg_idle_chatter')))
            defer.assert_called_once()
        self.llm.assert_not_called()
        self.insert.assert_not_called()

    def test_missing_roster_and_invalid_envelope_never_generate(self):
        for change in ({'party_bot_guids': []}, {'bg_match_token': None},
                       {'raid_group_id': 92}):
            event = self.event('bg_score_milestone')
            extra = json.loads(event['extra_data'])
            extra.update(change)
            event['extra_data'] = json.dumps(extra)
            self.assertFalse(handlers.process_bg_score_milestone_event(
                None, None, self.config, event))
        self.llm.assert_not_called()
        self.insert.assert_not_called()

    def test_generation_and_insert_failure_do_not_mark_completed(self):
        event = self.event('bg_score_milestone')
        self.llm.return_value = None
        self.assertFalse(handlers.process_bg_score_milestone_event(
            None, None, self.config, event))
        self.mark.assert_called_with(None, 99, 'skipped')
        self.insert.assert_not_called()
        self.llm.return_value = '{"message":"Hold the base."}'
        self.insert.side_effect = RuntimeError('simulated DB failure')
        with self.assertLogs(shared.logger, level='ERROR'):
            self.assertFalse(handlers.process_bg_score_milestone_event(
                None, None, self.config, event))
        self.mark.assert_called_with(None, 99, 'skipped')

    def test_malformed_snapshot_reaches_only_conservative_score_prompt(self):
        for snapshot in (None, {}, {'nodes': []}, 'invalid'):
            event = self.event('bg_score_milestone')
            extra = json.loads(event['extra_data'])
            extra['ab_state'] = snapshot
            event['extra_data'] = json.dumps(extra)
            self.assertTrue(handlers.process_bg_score_milestone_event(
                None, None, self.config, event))
            prompt = self.llm.call_args.args[1]
            self.assertNotIn('crossed the', prompt)
            self.assertNotIn('observed base control:', prompt)
            self.assertNotIn('Match resource target:', prompt)


if __name__ == '__main__':
    unittest.main()
