"""General reply length distribution, prompt scope and continuation state."""

import json
import random
import unittest
from contextlib import ExitStack
from unittest.mock import patch

import test_persona_coherence  # dependency stubs and tools path
import chatter_general as general
import chatter_general_length as lengths
import chatter_guild as guild
from chatter_persona import persona_from_fields


class ReplyLengths(unittest.TestCase):
    def test_weighted_bands_and_adjacent_avoidance(self):
        random.seed(42)
        seen = set()
        previous = None
        for _ in range(150):
            tier = lengths.pick_general_reply_tier({}, avoid=previous)
            self.assertNotEqual(tier, previous)
            seen.add(tier)
            previous = tier
        self.assertEqual(seen, {'short', 'medium', 'developed'})

    def test_single_band_configuration_is_respected(self):
        for index, tier in enumerate(('short', 'medium', 'developed')):
            weights = ['0', '0', '0']
            weights[index] = '100'
            config = {'LLMChatter.GeneralChat.PlayerReplyLengthWeights':
                      ','.join(weights)}
            self.assertEqual(lengths.pick_general_reply_tier(config, tier), tier)

    def test_invalid_config_falls_back_to_defaults(self):
        for raw in ('', 'bad', '1,2', '0,0,0', '-1,3,4'):
            with patch.object(lengths.random, 'choices', return_value=['medium']) as choose:
                lengths.pick_general_reply_tier({
                    'LLMChatter.GeneralChat.PlayerReplyLengthWeights': raw,
                })
                self.assertEqual(choose.call_args.kwargs['weights'], (35, 45, 20))
        for raw in ('', 'bad', '5,10', '100,50,240', '0,150,240', '75,150,256'):
            hint = lengths.general_reply_length_line({
                'LLMChatter.GeneralChat.PlayerReplyLengthMaxima': raw,
            }, 'developed')
            self.assertIn('151-240', hint)

    def test_custom_maxima(self):
        hint = lengths.general_reply_length_line({
            'LLMChatter.GeneralChat.PlayerReplyLengthMaxima': '40,100,220',
        }, 'medium')
        self.assertIn('41-100', hint)
        self.assertIn('HARD LIMIT: 255', hint)

    def prompts(self, mode, **kwargs):
        persona = persona_from_fields(
            'Gruk', mode, traits=['loyal', 'curious', 'patient'],
            tone='warm and direct', backstory='Raised in Durotar.',
        )
        common = ('Gruk', 'Orc', 'Warrior', 40, 'male', persona)
        yield str(general._build_general_response_prompt(
            *common, 'Player', 'What led you here?', 'Barrens', '', mode,
            allow_action=False, **kwargs,
        ))
        yield str(general._build_general_followup_prompt(
            *common, 'Other', 'I used to patrol here.', 'Player',
            'What led you here?', 'Barrens', '', mode,
            allow_action=False, **kwargs,
        ))
        if not kwargs.get('brief_casual'):
            yield str(general._build_general_continuation_prompt(
                *common, [{'name': 'Player', 'message': 'What led you here?',
                           'is_bot': False}], 'Barrens', '', mode,
                allow_action=False, **kwargs,
            ))

    def test_all_substantive_builders_preserve_voice_and_new_hint(self):
        hint = lengths.general_reply_length_line({}, 'developed')
        for mode in ('normal', 'roleplay'):
            for prompt in self.prompts(mode, reply_length_hint=hint):
                self.assertIn('151-240', prompt)
                self.assertIn('HARD LIMIT: 255', prompt)
                self.assertNotIn('Never exceed 150', prompt)
                self.assertNotIn('Keep it brief', prompt)
                self.assertIn('Your personality:', prompt)
                self.assertIn('Your tone:', prompt)
                self.assertEqual('Raised in Durotar.' in prompt, mode == 'roleplay')

    def test_direct_builders_default_medium_and_brief_stays_brief(self):
        for prompt in self.prompts('roleplay'):
            self.assertIn('medium, around 76-150', prompt)
            self.assertIn('HARD LIMIT: 255', prompt)
        for prompt in self.prompts('roleplay', brief_casual=True, brief_tier='tiny'):
            self.assertIn('1-4 words', prompt)
            self.assertIn('30 characters', prompt)
            self.assertNotIn('Length suggestion:', prompt)

    def test_guild_keeps_legacy_helper(self):
        self.assertIs(guild._pick_length_hint, general._pick_length_hint)
        self.assertIn('Never exceed 150', guild._pick_length_hint('roleplay'))

    def test_followup_carries_band_and_can_deliver_more_than_150_chars(self):
        inserted = []
        message = (
            'I came here to find the scout who taught me these roads. '
            'He used to leave a small stone beside every safe crossing, '
            'and I still catch myself looking for those markers whenever '
            'we pass through the dry riverbeds.'
        )
        persona = persona_from_fields('Two', 'roleplay')
        patches = {
            '_get_bot_info': lambda *a: {
                'name': 'Two', 'race': 2, 'class': 1, 'level': 40, 'gender': 0,
            },
            'prepare_channel_persona': lambda *a: persona,
            '_get_general_chat_history': lambda *a, **kw: [],
            'insert_chat_message': lambda *a, **kw: inserted.append(a[3]),
            '_extend_zone_delivery_window': lambda *a: None,
            'maybe_queue_group_general_reaction': lambda *a, **kw: None,
            '_store_general_chat': lambda *a: None,
        }
        with ExitStack() as stack:
            for name, value in patches.items():
                stack.enter_context(patch.object(general, name, value))
            choose = stack.enter_context(patch.object(
                general, 'pick_general_reply_tier',
                wraps=lengths.pick_general_reply_tier,
            ))
            llm = stack.enter_context(patch.object(
                general, 'call_llm', return_value=json.dumps({'message': message}),
            ))
            result = general._general_followup(
                None, None, {
                    'LLMChatter.TalentInjectionChance': 0,
                    'LLMChatter.GeneralChat.PlayerReplyLengthWeights': '0,0,1',
                }, 1, 12, 'Barrens', [1, 2], 0, 1, 'One', 'I patrolled here.',
                'Player', 'What led you here?', 'roleplay', 1,
                reply_tier_avoid='medium',
            )
        self.assertEqual(choose.call_args.kwargs['avoid'], 'medium')
        self.assertEqual(result['reply_tier'], 'developed')
        self.assertIn('151-240', str(llm.call_args.args[1]))
        self.assertEqual(inserted, [message])
        self.assertTrue(150 < len(inserted[0]) <= 255)

    def test_continuation_skips_without_advancing_band_and_tracks_success(self):
        inserted = []
        seen = []
        info = {'name': 'Three', 'race': 2, 'class': 1, 'level': 40, 'gender': 0}
        persona = persona_from_fields('One', 'roleplay')

        def bot_info(db, guid):
            return None if guid == 1 else info

        def pick(config, avoid=None):
            seen.append((avoid, len(inserted)))
            return 'short' if len(seen) == 1 else 'developed'

        patches = {
            '_extended_max_messages': 5,
            '_get_bot_info': bot_info,
            'prepare_channel_persona': lambda *a, **kw: persona,
            '_get_general_chat_history': lambda *a, **kw: [],
            'pick_general_reply_tier': pick,
            'insert_chat_message': lambda *a, **kw: inserted.append(a[3]),
            '_extend_zone_delivery_window': lambda *a: None,
            'maybe_queue_group_general_reaction': lambda *a, **kw: None,
            '_store_general_chat': lambda *a: None,
        }
        with ExitStack() as stack:
            for name, value in patches.items():
                stack.enter_context(patch.object(general, name, value))
            stack.enter_context(patch.object(general.random, 'random', return_value=0))
            stack.enter_context(patch.object(general.random, 'randint', return_value=1))
            stack.enter_context(patch.object(general.random, 'choice', side_effect=lambda xs: xs[0]))
            stack.enter_context(patch.object(general, 'call_llm', side_effect=[
                json.dumps({'message': 'I remember that patrol.', 'action': None}),
                None,
            ]))
            general._general_extended_conversation(
                None, None, {'LLMChatter.TalentInjectionChance': 0},
                1, 12, 'Barrens', [1, 2, 3],
                1, 'One', persona, 'First line',
                2, 'Two', persona, 'Second line',
                'Player', 'What led you here?', 'roleplay', 1,
                previous_reply_tier='medium',
            )
        self.assertEqual(seen, [('medium', 0), ('short', 1)])
        self.assertEqual(len(inserted), 1)


if __name__ == '__main__':
    unittest.main()
