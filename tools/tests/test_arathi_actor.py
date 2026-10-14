#!/usr/bin/env python3
"""Verified AB banner actor rendering (#15/#16); C++ policy is in cpp/.

Run from the module root:
  python tools/tests/test_arathi_actor.py
"""
import unittest
from unittest.mock import patch

import test_battleground_carrier_messages  # noqa: F401 - stubs/tools path
from chatter_ab import normalize_ab_node_changes, NODE_NAMES
from chatter_bg_prompts import build_bg_node_prompt
from test_bg_delivery_contract import envelope

BOT = {'bot_name': 'Grogum'}


def change(node=2, prev=0, state=3, transition='claim', **actor):
    item = dict(node_id=node, node_revision=2, node_name=NODE_NAMES[node],
                prev_state=prev, state=state, transition=transition,
                evidence='sampled', observation_gap_ms=1000)
    item.update(actor)
    return item


def prompt(items, team='Alliance', **extra):
    data = dict(envelope(), node_changes=items, team=team,
                real_players=[{'name': 'Karaez', 'race': 'Night Elf'}],
                event_type='bg_node_captured')
    data.update(extra)
    with patch('chatter_bg_prompts.pick_personality_spices', return_value=[]), \
            patch('chatter_bg_prompts.build_environmental_context_lines',
                  return_value=[]):
        return build_bg_node_prompt(data, BOT)


def karaez(role='claim', real=True):
    return dict(actor_name='Karaez', actor_is_real_player=real, actor_role=role)


class ActorTests(unittest.TestCase):
    def test_real_player_claim_is_praised_by_name(self):
        text = prompt([change(**karaez())])
        self.assertIn('Karaez took that banner personally.', text)
        self.assertIn('Acknowledge Karaez by name, warmly and positively.', text)

    def test_every_verified_role_for_our_team(self):
        cases = (
            (change(prev=0, state=3, transition='claim', **karaez('claim')),
             'took that banner personally'),
            (change(prev=2, state=3, transition='assault', **karaez('assault')),
             'took that banner personally'),
            (change(prev=4, state=3, transition='counter_claim',
                    **karaez('counter_claim')), 'took that banner personally'),
            (change(prev=4, state=1, transition='defence', **karaez('defence')),
             'took that banner personally'),
            (change(prev=3, state=1, transition='capture', **karaez('flag_held')),
             "Karaez's flag on Farm held."),
        )
        for item, expected in cases:
            text = prompt([item])
            self.assertIn(expected, text, item['transition'])
            self.assertIn('Acknowledge Karaez by name', text)

    def test_bot_teammate_named_lightly_enemy_named_neutrally(self):
        text = prompt([change(**karaez(real=False))])
        self.assertIn('You may mention Karaez briefly.', text)
        self.assertNotIn('warmly', text)
        enemy = change(state=4, **dict(karaez(), actor_name='Hodangoba'))
        text = prompt([enemy])
        self.assertIn('The enemy player who did it was Hodangoba.', text)
        self.assertNotIn('Acknowledge Hodangoba', text)

    def test_no_name_without_verified_actor_or_roster(self):
        # #16: the roster line must not let the model guess node credit.
        text = prompt([change()])
        self.assertNotIn('Karaez', text)
        self.assertNotIn('Real players on your team', text)
        self.assertIn('Credit only a player named in these observations', text)

    def test_role_transition_mismatch_or_ambiguity_gives_no_name(self):
        for item in (
            change(**karaez('assault')),                        # role != claim
            change(prev=3, state=1, transition='capture', **karaez('claim')),
            dict(change(**karaez()), evidence='ambiguous',
                 transition='state_update'),
        ):
            self.assertNotIn('Karaez', prompt([item]))

    def test_malformed_actor_drops_only_the_actor(self):
        for bad in (dict(actor_name='Kar aez'), dict(actor_name=''),
                    dict(actor_name='K' * 13), dict(actor_is_real_player='yes'),
                    dict(actor_role='stole_it'), dict(actor_name=7),
                    dict(actor_role=None), dict(actor_role=['claim']),
                    dict(actor_role={'claim': 1})):
            item = dict(change(**karaez()), **bad)
            result = normalize_ab_node_changes([item])
            self.assertEqual(len(result), 1)
            self.assertNotIn('actor_name', result[0])
            self.assertEqual(result[0]['transition'], 'claim')
            self.assertNotIn('Acknowledge', prompt([item]))

    def test_same_state_interactions_invalidate_published_actor(self):
        """Source contract (no C++ execution): unchanged-state verified clicks
        advance the revision and drop the pending actor."""
        from pathlib import Path
        source = (Path(__file__).resolve().parents[2]
                  / 'src/LLMChatterAB.cpp').read_text(encoding='utf-8')
        branch = source.split('if (state == node.state)', 1)[1]
        branch = branch.split('continue;', 1)[0]
        guard = branch.index('InvalidatesRevision(')
        for needle in ('++node.revision;',
                       'node.actorKind = LLMChatterAB::ACTOR_NONE;',
                       'node.transition = "state_update";',
                       'tracker.pending.Record('):
            self.assertGreater(branch.index(needle), guard, needle)
        pre = source.split('void OnPlayerSpellCast(', 1)[1].split('};', 1)[0]
        self.assertLess(pre.index('_abPreCasts.Cancel(spell);'),
                        pre.index('ABActorTrackingEnabled()'))

    def test_batch_names_only_the_attributed_base(self):
        items = [change(node=2, **karaez()), change(node=4)]
        text = prompt(items)
        self.assertEqual(text.count('Karaez'), 2)  # fact + acknowledgement
        self.assertIn('Gold Mine. Nobody held it before', text)


if __name__ == '__main__':
    unittest.main()
