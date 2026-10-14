#!/usr/bin/env python3
"""Transport execution tests and explicitly source-only C++ guard checks."""
import json
import re
from pathlib import Path
import unittest
from unittest.mock import patch

import test_battleground_carrier_messages  # dependency stubs and tools path
from chatter_bg_delivery import AB_SNAPSHOT_EVENTS, normalize_bg_transport
from chatter_shared import parse_extra_data
import chatter_raid_base as raid
from chatter_bg_prompts import build_bg_node_prompt
from test_arathi_snapshot import snapshot, BOT

ROOT = Path(__file__).resolve().parents[2]

# Every literal group producer is classified by payload, not map location.
# With BG metadata it is guarded; without it ordinary delivery is preserved.
# A new event requires this inventory to be reviewed explicitly.
PARTY_PRODUCERS = {
    'achievement', 'combat', 'corpse_run', 'death', 'dungeon_entry',
    'emote_observer', 'emote_reaction', 'farewell', 'join', 'join_batch',
    'kill', 'levelup', 'loot', 'nearby_object', 'player_msg', 'quest_accept',
    'quest_accept_batch', 'quest_complete', 'quest_objectives', 'resurrect',
    'spell_cast', 'subzone_change', 'wipe', 'zone_transition',
}


def envelope():
    return dict(bg_match_token='lifetime-1', bg_observed_ms=1234,
                bg_recipient_guid=42, bg_instance_id=7, bg_type_id=3,
                bg_map_id=529, group_id=91, player_subgroup=2,
                team='Alliance', is_battleground=True,
                ab_state={'observed_at_ms': 1000, 'nodes': []})


class TransportTests(unittest.TestCase):
    def test_original_facts_and_identity_survive_parse(self):
        data = envelope()
        self.assertEqual(parse_extra_data(
            json.dumps(data), event_type='bg_idle_chatter'), data)
        self.assertIs(normalize_bg_transport(
            data, 'bg_idle_chatter')['ab_state'], data['ab_state'])

    def test_only_objective_events_keep_base_snapshot(self):
        self.assertEqual(AB_SNAPSHOT_EVENTS, {
            'bg_node_captured', 'bg_node_contested', 'bg_idle_chatter',
            'bg_score_milestone'})
        events = set(AB_SNAPSHOT_EVENTS) | {
            'bg_match_start', 'bg_match_end', 'bg_pvp_kill',
            'bg_score_milestone', 'bot_group_low_health', 'bot_group_oom',
        } | {'bot_group_' + name for name in PARTY_PRODUCERS}
        for event in events:
            data = envelope()
            parsed = parse_extra_data(json.dumps(data), event_type=event)
            self.assertEqual('ab_state' in parsed, event in AB_SNAPSHOT_EVENTS)
            self.assertIn('ab_state', data)  # never mutate the original
            for key in ('bg_match_token', 'bg_observed_ms', 'bg_recipient_guid',
                        'group_id', 'player_subgroup'):
                self.assertEqual(parsed[key], data[key])

    def test_group_alias_and_conflicts(self):
        data = envelope()
        del data['group_id']
        data['raid_group_id'] = 91
        self.assertEqual(normalize_bg_transport(data)['group_id'], 91)
        data['group_id'] = 92
        self.assertEqual(parse_extra_data(json.dumps(data)), {})

    def test_malformed_identity(self):
        for key, bad in [('bg_observed_ms', -1), ('bg_observed_ms', True),
                         ('bg_instance_id', '7'), ('bg_instance_id', 0),
                         ('bg_recipient_guid', 2**32), ('player_subgroup', 8),
                         ('team', 'Neutral'), ('bg_match_token', None)]:
            with self.subTest(key=key, bad=bad):
                data = envelope()
                data[key] = bad
                self.assertEqual(normalize_bg_transport(data), {})

    def test_legacy_generation_and_non_bg_are_preserved(self):
        legacy = {'bg_type_id': 2, 'raid_group_id': 91}
        self.assertEqual(normalize_bg_transport(legacy)['group_id'], 91)
        ordinary = {'group_id': 'legacy-value', 'player_message': 'Hi'}
        self.assertIs(normalize_bg_transport(ordinary), ordinary)

    def test_party_producer_policy_inventory(self):
        actual = set()
        for path in (ROOT / 'src').glob('*.cpp'):
            source = re.sub(r'"\s*\n\s*"', '', path.read_text(encoding='utf-8'))
            actual.update(re.findall(
                r'QueueChatterEvent\(\s*"bot_group_([^"]+)"', source))
        self.assertEqual(actual, PARTY_PRODUCERS)
        for name in PARTY_PRODUCERS | {'low_health', 'oom', 'aggro'}:
            event_type = 'bot_group_' + name
            ordinary = {'group_id': 91, 'map': 529}
            self.assertIs(normalize_bg_transport(ordinary, event_type), ordinary)
            bg = envelope()
            bg['raid_group_id'] = 92
            self.assertEqual(normalize_bg_transport(bg, event_type), {})

    def test_node_prompt_only_exposes_referenced_objective(self):
        data = envelope()
        data.update(ab_state=snapshot(), node_name='Stables', node_id=0,
                    node_revision=1, state=1, prev_state=3,
                    transition='capture', evidence='sampled',
                    observation_gap_ms=1000, event_type='bg_node_captured')
        with patch('chatter_bg_prompts.pick_personality_spices', return_value=[]), \
                patch('chatter_bg_prompts.build_environmental_context_lines',
                      return_value=[]):
            prompt = build_bg_node_prompt(data, BOT)
        self.assertIn('now holds Stables', prompt)
        self.assertNotIn('Observed income:', prompt)
        self.assertNotIn('Arathi Basin observed base control:', prompt)
        self.assertEqual(data['ab_state'], snapshot())

    def test_crowd_keeps_event_link_and_group_for_all_bg_types(self):
        for bg_type, map_id in [(2, 489), (3, 529), (7, 566)]:
            data = envelope()
            data.update(bg_type_id=bg_type, bg_map_id=map_id,
                        queue_type_id=32, raid_bot_guids=[100])
            with patch.object(raid, 'get_lightweight_bot_data', return_value={
                    'bot_name': 'Bot', 'class': 'Warrior'}), \
                    patch.object(raid, '_maybe_talent_context', return_value=''), \
                    patch.object(raid, 'run_single_reaction',
                                 return_value={'ok': True}) as run:
                result = raid.fire_raid_worker(None, None, {}, {'id': 123},
                                              data, prompt_fn=lambda *a, **k: 'p')
                self.assertEqual(result, {'used_guids': [100]})
                self.assertEqual(run.call_args.kwargs['event_id'], 123)
                self.assertEqual(run.call_args.kwargs['group_id'], 91)
                self.assertEqual(run.call_args.kwargs['channel'], 'battleground')


class SourceOnlyGuardTests(unittest.TestCase):
    def test_guard_precedes_visible_side_effects(self):
        source = (ROOT / 'src/LLMChatterDelivery.cpp').read_text()
        guard = source.index('std::string bgDrop = ValidateBGDelivery(')
        for visible in ('auto emitAction', 'SendBotTextEmote(',
                        'bot->SetFacingToObject('):
            self.assertGreater(source.index(visible), guard, visible)
        drop = source[guard:source.index('if (bot && eventSubjectGuid', guard)]
        self.assertIn('FinalizeDroppedMessage(', drop)
        self.assertIn('return;', drop)

    def test_every_sequence_rechecks_age_and_map_alone_does_not_guard(self):
        source = (ROOT / 'src/LLMChatterBGDelivery.cpp').read_text()
        self.assertIn('now - observed > uint64(ageSec) * 1000', source)
        self.assertNotIn('sequence', source)
        classification = source.split('bool bgRow =', 1)[1].split('if (!bgRow)', 1)[0]
        self.assertNotIn('eventMapId', classification)
        self.assertIn('fields.count("ab_state")', classification)
        node_guard = source.index('IsABNodeEventCurrent(bg, json)')
        self.assertLess(node_guard, source.index('IsABSnapshotCurrent(bg,'))
        policy = source.split('bool BGEventUsesABSnapshot(', 1)[1].split(
            'void EnsureBGDeliveryLifetime(', 1)[0]
        self.assertEqual(set(re.findall(r'eventType == "([^"]+)"', policy)),
                         AB_SNAPSHOT_EVENTS)
        self.assertIn('bg_ab_context_unexpected', source)
        self.assertEqual(classification.count('fields.count("ab_state")'), 1)

    def test_age_budget_is_selected_by_snapshot_content(self):
        source = (ROOT / 'src/LLMChatterBGDelivery.cpp').read_text()
        budget = source.split('uint64 now = GetTimeMS().count();', 1)[1]
        budget = budget.split('return "bg_facts_expired";', 1)[0]
        # The AB budget requires both AB and a carried snapshot.
        self.assertIn('type == BATTLEGROUND_AB && fields.count("ab_state")',
                      budget)
        self.assertIn('abSnapshot ? sLLMChatterConfig->_bgABFactualMaxAgeSec',
                      budget)
        self.assertNotIn('type == BATTLEGROUND_AB ? ', budget)
        self.assertLess(budget.index('_bgMatchEndMaxAgeSec'),
                        budget.index('_bgABFactualMaxAgeSec'))
        config = (ROOT / 'src/LLMChatterConfig.cpp').read_text()
        self.assertIn('"LLMChatter.BGChatter.AB.FactualMaxAgeSec", 45)',
                      config)
        dist = (ROOT / 'conf/mod_llm_chatter.conf.dist').read_text()
        self.assertIn('LLMChatter.BGChatter.AB.FactualMaxAgeSec = 45', dist)

    def test_live_match_audience_and_age_checks_exist(self):
        source = (ROOT / 'src/LLMChatterBGDelivery.cpp').read_text()
        for condition in ('it->second.token != token', 'observed > now',
                          'recipient->GetBattleground() != bg',
                          'speaker->GetMap()->GetInstanceId() != instance',
                          'speaker->GetBgTeamId() != expectedTeam',
                          'recipient->GetBgTeamId() != expectedTeam',
                          'group != recipient->GetGroup()',
                          'group->GetMemberGroup(speaker->GetGUID()) != subgroup',
                          'group->GetMemberGroup(recipient->GetGUID()) != subgroup',
                          'STATUS_WAIT_LEAVE', 'STATUS_WAIT_JOIN',
                          'bg_contract_missing', 'IsABSnapshotCurrent('):
            self.assertIn(condition, source)
        ab = (ROOT / 'src/LLMChatterAB.cpp').read_text()
        self.assertIn('live._state != state', ab)
        self.assertIn('cached.revision != revision', ab)
        self.assertIn('nodes.size() != BG_AB_DYNAMIC_NODES_COUNT', ab)


if __name__ == '__main__':
    unittest.main()
