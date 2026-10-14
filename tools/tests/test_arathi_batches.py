#!/usr/bin/env python3
"""Execute batch parsing/prompt/dispatch tests; C++ checks are source-only."""
import json
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

import test_battleground_carrier_messages  # stubs/tools import path
from chatter_ab import normalize_ab_node_changes, NODE_NAMES
from chatter_bg_prompts import build_bg_node_prompt
import chatter_battlegrounds as handlers
from test_bg_delivery_contract import envelope

ROOT = Path(__file__).resolve().parents[2]


def changes():
    return [dict(node_id=i, node_revision=1, node_name=NODE_NAMES[i],
                 state=3, prev_state=0, transition='claim', evidence='sampled',
                 observation_gap_ms=1000) for i in range(5)]


class BatchTests(unittest.TestCase):
    def test_five_claims_canonical_names_and_no_input_mutation(self):
        raw = changes()
        raw[0]['node_name'] = 'invented actor'
        result = normalize_ab_node_changes(raw)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]['node_name'], 'Stables')
        self.assertEqual(raw[0]['node_name'], 'invented actor')

    def test_malformed_batch_rejected_as_a_whole(self):
        bads = [None, {}, [], changes() + [changes()[0]],
                [changes()[0], changes()[0]]]
        for key, value in [('node_id', True), ('node_revision', 0),
                           ('node_revision', 2**64), ('state', '3'),
                           ('state', 5)]:
            bad = changes()
            bad[-1][key] = value
            bads.append(bad)
        for bad in bads:
            self.assertIsNone(normalize_ab_node_changes(bad))

    def test_mixed_transitions_do_not_inherit_transport_capture_label(self):
        raw = changes()[:2]
        raw[1].update(state=2, prev_state=4, transition='capture')
        for mode in ('normal', 'roleplay'):
            extra = dict(envelope(), node_changes=raw,
                         event_type='bg_node_captured',
                         _config={'LLMChatter.ChatterMode': mode})
            with patch('chatter_bg_prompts.pick_personality_spices', return_value=[]), \
                    patch('chatter_bg_prompts.build_environmental_context_lines',
                          return_value=[]):
                prompt = build_bg_node_prompt(extra, {'bot_name': 'Observer'})
            self.assertIn('claiming the neutral Stables', prompt)
            self.assertIn('The enemy (Horde) now holds Blacksmith', prompt)
            self.assertIn('one brief reaction', prompt)
            # The constraint is stated once for the whole batch.
            self.assertEqual(prompt.count('Credit only a player named in these observations'), 1)
            self.assertEqual(prompt.count('\n- '), 2)
            self.assertNotIn('observed base control:', prompt)

    def test_one_bg_wide_dispatch_preserves_event_link_and_batch(self):
        for queue in (3, 32):
            extra = dict(envelope(), node_changes=changes(), queue_type_id=queue)
            event = {'id': 99, 'event_type': 'bg_node_captured',
                     'extra_data': json.dumps(extra)}
            with patch.object(handlers, '_mark_event') as mark, \
                    patch.object(handlers, 'dual_worker_dispatch',
                                 return_value=True) as dispatch:
                self.assertTrue(handlers.process_bg_node_event(None, None, {}, event))
                self.assertEqual(dispatch.call_count, 1)
                self.assertEqual(dispatch.call_args.args[3]['id'], 99)
                self.assertEqual(len(dispatch.call_args.args[4]['node_changes']), 5)
                self.assertEqual(dispatch.call_args.kwargs['dispatch_mode'],
                                 handlers.DISPATCH_RAID_ONLY)
                self.assertIs(dispatch.call_args.kwargs['raid_prompt_fn'],
                              build_bg_node_prompt)
                mark.assert_called_once_with(None, 99, 'completed')
            bad = deepcopy(event)
            extra['node_changes'] = []
            bad['extra_data'] = json.dumps(extra)
            with patch.object(handlers, '_mark_event'), \
                    patch.object(handlers, 'dual_worker_dispatch') as dispatch:
                self.assertFalse(handlers.process_bg_node_event(None, None, {}, bad))
                dispatch.assert_not_called()

    def test_cpp_batch_guard_and_queue_source_contract(self):
        source = (ROOT / 'src/LLMChatterAB.cpp').read_text()
        batch = source.split('void QueueABNodeBatch(', 1)[1].split(
            'static void ReadMatchTarget(', 1)[0]
        listeners = source.split('static std::map<LLMChatterAB::Audience, Player*> ABListeners(', 1)[1].split(
            'void QueueABNodeBatch(', 1)[0]
        self.assertIn('listeners.emplace(key, player)', listeners)
        self.assertIn('GetMemberGroup(bot->GetGUID()) == subgroup', listeners)
        self.assertIn('auto listeners = ABListeners(bg, false)', batch)
        self.assertIn('!subgroupOnly', listeners)
        self.assertIn('(subgroupOnly ? subgroup : 0)', listeners)
        score = source.split('void QueueABScoreMilestone(', 1)[1].split(
            'bool TryABObjectiveStatus(', 1)[0]
        self.assertIn('auto listeners = ABListeners(bg)', score)
        self.assertIn('tracker.pending.ForAudience(selected, audience)', batch)
        self.assertIn('AsyncCommitTransaction(trans)', batch)
        self.assertIn('tracker.pending.Acknowledge(audience, items, success)', batch)
        self.assertNotIn('TryQueueBGBigEvent', batch)
        self.assertIn('if (!tracker.insertions.empty())', batch)
        guard = source.split('bool IsABNodeEventCurrent(', 1)[1].split(
            'bool IsABSnapshotCurrent(', 1)[0]
        self.assertIn('changes.size() > BG_AB_DYNAMIC_NODES_COUNT', guard)
        self.assertIn('(seen & (1u << id))', guard)
        self.assertIn('!validate(fields)', guard)
        self.assertIn('return validate(root)', guard)


if __name__ == '__main__':
    unittest.main()
