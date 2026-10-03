"""Offline route/transport/prompt checks; not C++ or visible-speech proof."""

import json
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import screenshot_agent as agent
import screenshot_proximity as transport
import chatter_proximity as proximity

SCENE = {'environment': 'A low stone bridge', 'weather': 'foggy',
         'time_of_day': 'dusk', 'biome': 'unused biome'}
NPC = {'name': 'Guard Thomas', 'is_npc': True, 'npc_entry': 261,
       'npc_spawn_id': 123, 'role': 'Guard'}


class CaptureTests(unittest.TestCase):
    def cycle(self, group=True, ticket=True, duplicate=False,
              party_error=False, local_error=False, roll=1, enabled=True):
        with ExitStack() as stack:
            mocks = {}
            values = {
                'is_wow_foreground': True,
                'get_db_connection': MagicMock(),
                'get_bound_player_group': {'bot_name': 'Bot', 'zone': 12}
                    if group else None,
                'request_ticket': (1, 'a' * 32) if ticket else None,
                'capture_wow_window': MagicMock(),
                'crop_screenshot': MagicMock(),
                'compress_screenshot': b'image',
                'analyze_screenshot': SCENE,
                'is_duplicate': duplicate,
                'queue_screenshot_event': None,
                'publish_observation': True,
                'update_dedup_cache': None,
            }
            for name, value in values.items():
                mocks[name] = stack.enter_context(patch.object(
                    agent, name, return_value=value))
            stack.enter_context(patch.object(agent.random, 'randint',
                                             return_value=roll))
            if party_error:
                mocks['queue_screenshot_event'].side_effect = RuntimeError()
            if local_error:
                mocks['publish_observation'].side_effect = RuntimeError()
            config = agent.load_screenshot_config({})
            config.update(bound_account_id=1, proximity_enable=enabled)
            agent._do_capture_cycle(config, MagicMock())
            return mocks

    def test_both_routes_publish(self):
        m = self.cycle()
        m['queue_screenshot_event'].assert_called_once()
        m['publish_observation'].assert_called_once()
        m['analyze_screenshot'].assert_called_once()

    def test_solo_does_not_touch_party_dedup(self):
        m = self.cycle(group=False)
        m['publish_observation'].assert_called_once()
        m['is_duplicate'].assert_not_called()
        m['update_dedup_cache'].assert_not_called()

    def test_no_npcs_and_no_party_skips_capture(self):
        m = self.cycle(group=False, ticket=False)
        m['capture_wow_window'].assert_not_called()

    def test_party_duplicate_does_not_suppress_local(self):
        m = self.cycle(duplicate=True)
        m['queue_screenshot_event'].assert_not_called()
        m['publish_observation'].assert_called_once()

    def test_party_failure_does_not_suppress_local_or_update_cache(self):
        m = self.cycle(party_error=True)
        m['update_dedup_cache'].assert_not_called()
        m['publish_observation'].assert_called_once()

    def test_local_failure_does_not_suppress_party(self):
        m = self.cycle(local_error=True)
        m['queue_screenshot_event'].assert_called_once()
        m['update_dedup_cache'].assert_called_once()

    def test_local_roll_failure_keeps_party(self):
        m = self.cycle(roll=100)
        m['request_ticket'].assert_not_called()
        m['publish_observation'].assert_not_called()
        m['queue_screenshot_event'].assert_called_once()

    def test_disabled_preserves_party_only(self):
        m = self.cycle(enabled=False)
        m['request_ticket'].assert_not_called()
        m['queue_screenshot_event'].assert_called_once()

    def test_defaults_opt_out(self):
        c = agent.load_screenshot_config({})
        self.assertFalse(c['proximity_enable'])
        self.assertEqual(c['bound_account_id'], 0)
        self.assertEqual(c['proximity_chance'], 30)


class TransportTests(unittest.TestCase):
    def database(self, state='ready', rowcount=1):
        db = MagicMock()
        cursor = db.cursor.return_value
        cursor.rowcount = rowcount
        cursor.fetchone.return_value = {'state': state, 'player_guid': 42}
        return db, cursor

    def test_preflight_returns_only_server_ready_ticket(self):
        db, c = self.database()
        ticket = transport.request_ticket(db, 7, 5)
        self.assertEqual(ticket[0], 7)
        self.assertEqual(len(ticket[1]), 32)
        query, args = c.execute.call_args.args
        self.assertIn('request_token=%s', query)
        self.assertIn('expires_at>NOW()', query)
        self.assertEqual(args, ticket)
        self.assertEqual(db.commit.call_count, 2)
        c.close.assert_called_once()

    def test_rejected_preflight(self):
        db, _ = self.database('consumed')
        self.assertIsNone(transport.request_ticket(db, 7, 5))

    def test_busy_slot_is_not_replaced_or_polled(self):
        db, c = self.database(rowcount=0)
        self.assertIsNone(transport.request_ticket(db, 7, 5))
        c.fetchone.assert_not_called()
        self.assertIn("state='consumed' OR expires_at<=NOW()",
                      c.execute.call_args.args[0])

    def test_publication_is_token_state_expiry_guarded(self):
        db, c = self.database()
        ticket = (7, 'b' * 32)
        self.assertTrue(transport.publish_observation(db, ticket, SCENE))
        query, args = c.execute.call_args.args
        self.assertIn("state='ready' AND expires_at>NOW()", query)
        self.assertIn('account_id=%s AND request_token=%s', query)
        self.assertEqual(json.loads(args[0]), SCENE)
        self.assertEqual(args[1:], ticket)

    def test_lost_cas_race_is_not_retried(self):
        db, c = self.database(rowcount=0)
        self.assertFalse(transport.publish_observation(db, (7, 'b'*32), SCENE))
        c.execute.assert_called_once()

    def test_payload_byte_limit(self):
        db, c = self.database()
        self.assertFalse(transport.publish_observation(
            db, (7, 'b'*32), {'environment': '\u00e9' * 5000}))
        c.execute.assert_not_called()


class PromptTests(unittest.TestCase):
    def test_screenshot_conversation_uses_existing_parse_and_pacing(self):
        speakers = [NPC, {**NPC, 'name': 'Guard Two', 'npc_spawn_id': 124}]
        extra = {'screenshot_observation': SCENE, 'participants': speakers,
                 'player_guid': 42, 'max_lines': 2}
        response = json.dumps({'messages': [
            {'speaker': 'Guard Thomas', 'message': 'Fog makes this watch long.'},
            {'speaker': 'Guard Two', 'message': 'At least the bridge is quiet.'},
        ]})
        with patch.object(proximity, 'call_llm', return_value=response), \
                patch.object(proximity, '_mark_event'), \
                patch.object(proximity, '_insert_proximity_line',
                             return_value=True) as insert, \
                patch.object(proximity, 'proximity_line_delays',
                             return_value=[0, 7]) as pacing:
            self.assertTrue(proximity.handle_proximity_conversation(
                None, None, {}, {'id': 99, 'extra_data': json.dumps(extra)}))
        pacing.assert_called_once()
        self.assertEqual([c.args[5] for c in insert.call_args_list], [0, 7])
        self.assertTrue(all(c.args[2]['is_npc'] for c in insert.call_args_list))

    def test_npc_scene_replaces_random_topic_and_live_environment(self):
        extra = {'screenshot_observation': SCENE, 'zone_id': 12,
                 'map_id': 0, 'player_name': 'Player', 'max_lines': 2}
        config = {'LLMChatter.ChatterMode': 'normal'}
        with patch.object(proximity, '_environment_lines') as environment, \
                patch.object(proximity, '_pick_topic') as topic:
            single = proximity._single_prompt(
                None, extra, NPC, 'unrelated seed', config=config).user_prompt
            convo = proximity._conversation_prompt(
                None, extra, [NPC, {**NPC, 'name': 'Guard Two'}],
                config=config).user_prompt
        environment.assert_not_called()
        topic.assert_not_called()
        for prompt in (single, convo):
            self.assertIn('A low stone bridge', prompt)
            self.assertIn('foggy', prompt)
            self.assertIn('supplied NPCs living in Azeroth', prompt)
            self.assertNotIn('unused biome', prompt)
            self.assertNotIn('Topic seed:', prompt)

    def test_ordinary_environment_still_used(self):
        with patch.object(proximity, '_environment_lines',
                          return_value=['ordinary environment']) as environment:
            result = proximity._location_lines({}, 'normal', [NPC])
        environment.assert_called_once()
        self.assertIn('ordinary environment', result)


class SourceWiringTests(unittest.TestCase):
    def test_server_owns_snapshot_and_delivery_gate(self):
        # Static wiring only: compilation and live lifecycle proof are separate.
        src = Path(__file__).resolve().parents[2] / 'src'
        coordinator = (src / 'LLMChatterScreenshot.cpp').read_text()
        delivery = (src / 'LLMChatterDelivery.cpp').read_text()
        self.assertIn('GetCreateTime().count()', coordinator)
        self.assertIn('player->GetInstanceId() != capture.instance', coordinator)
        self.assertIn('dx * dx + dy * dy + dz * dz <= radius * radius', coordinator)
        self.assertLess(coordinator.index('Finish(account, token);\n    auto capture'),
                        coordinator.index('if (QueueScreenshotProximity(player'))
        self.assertIn('IsScreenshotProximityCurrent(', delivery)
        self.assertIn('proximityRadius = sLLMChatterConfig->_proxChatterScanRadius',
                      delivery)
        roster = (src / 'LLMChatterProximity.cpp').read_text().split(
            'bool CanQueueScreenshotProximity', 1)[1].split(
            'bool IsProximityFightOnlookerEligible', 1)[0]
        self.assertEqual(roster.count('_proxChatterEntityCooldown, false)'), 2)
        self.assertNotIn('_proxChatterEntityCooldown, true)', roster)


if __name__ == '__main__':
    unittest.main()
