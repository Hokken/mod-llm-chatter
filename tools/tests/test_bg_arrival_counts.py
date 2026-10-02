"""Exercise independent arrival rolls and actual handler channel insertion."""
import json
import unittest
from collections import Counter
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import test_battleground_carrier_messages  # dependency stubs and tools path
import chatter_group as group


class ArrivalTests(unittest.TestCase):
    bots = [dict(bot_guid=i, bot_name=f'Bot{i}', bot_class=1,
                 bot_race=1, bot_level=80) for i in range(1, 5)]

    def test_exact_default_distribution(self):
        totals = Counter()
        for second_roll in range(1, 101):
            for party_roll in range(4):
                with patch.object(group.random, 'randint',
                                  side_effect=[second_roll, party_roll]):
                    plan = group._select_bg_arrival_greetings(self.bots, {})
                counts = Counter(channel for _, channel in plan)
                totals[counts['battleground'], counts['party']] += 1
                for channel in ('party', 'battleground'):
                    ids = [bot['bot_guid'] for bot, ch in plan if ch == channel]
                    self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(totals, Counter({(r, p): 50
                         for r in (1, 2) for p in range(4)}))

    def test_empty_disabled_and_small_roster(self):
        self.assertEqual(group._select_bg_arrival_greetings([], {}), [])
        self.assertEqual(group._select_bg_arrival_greetings(self.bots,
            {'LLMChatter.BGChatter.ArrivalGreetings.Enable': 0}), [])
        with patch.object(group.random, 'randint', side_effect=[1, 1]):
            plan = group._select_bg_arrival_greetings(self.bots[:1], {})
        self.assertEqual([ch for _, ch in plan], ['battleground', 'party'])

    def test_handler_preserves_channels_after_generation_failure(self):
        event = {'id': 901, 'extra_data': json.dumps(dict(
            group_id=42, player_name='Tester', bg_type='Arathi Basin',
            bg_type_id=3, bots=self.bots))}
        for fail_first in (False, True):
            with self.subTest(fail_first=fail_first), ExitStack() as stack:
                for name, value in {
                    '_has_recent_join_greeting': False,
                    'assign_bot_traits': {'traits': ['patient'], 'tone': None},
                    'get_player_zone': (0, 0), 'build_gear_context': '',
                    '_get_recent_chat': [], 'get_group_members': [],
                    '_maybe_talent_context': None, 'build_bg_arrival_prompt': 'hi',
                    '_store_chat': None, '_mark_event': None,
                }.items():
                    stack.enter_context(patch.object(group, name, return_value=value))
                stack.enter_context(patch.object(group.random, 'randint',
                                                 side_effect=[1, 3]))
                responses = ['{"message":"Ready for battle."}'] * 5
                if fail_first:
                    responses[0] = None
                stack.enter_context(patch.object(group, 'call_llm',
                                                 side_effect=responses))
                insert = stack.enter_context(patch.object(group, 'insert_chat_message'))
                group.process_group_join_batch_event(MagicMock(), None,
                    {'LLMChatter.Memory.Enable': 0}, event)
                channels = Counter(c.kwargs['channel'] for c in insert.call_args_list)
                self.assertEqual(channels, {'battleground': 1 if fail_first else 2,
                                            'party': 3})
                self.assertTrue(all(c.kwargs['event_id'] == 901
                                    for c in insert.call_args_list))


if __name__ == '__main__':
    unittest.main()
