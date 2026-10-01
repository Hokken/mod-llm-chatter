"""Intent-first scope and preserved channel bounds; no live LLM calls."""
import json
import unittest
from unittest.mock import patch

import test_guild_player_replies as fixtures
import chatter_shared as shared
import chatter_group_prompts as party
import chatter_guild_player as guild


class SemanticReplyScope(unittest.TestCase):
    def analyze(self, message, brief, required):
        with patch.object(shared, 'quick_llm_analyze', return_value=json.dumps({
            'bot': None, 'multi_addressed': False,
            'brief_casual': brief, 'requires_reply': required,
        })) as call:
            result = shared.find_addressed_bot(
                message, ['Gruk'], object(), {'enabled': 1},
                chat_history='Gruk: I have something to explain.',
            )
        self.assertIn(message, call.call_args.args[2])
        self.assertIn('I have something to explain.', call.call_args.args[2])
        self.assertEqual(call.call_args.kwargs['max_tokens'], 80)
        return result, call.call_args.args[2]

    def test_short_invitation_uses_model_decision_without_silence(self):
        result, prompt = self.analyze('any news?', False, True)
        self.assertFalse(result['brief_casual'])
        with patch.object(shared.random, 'randint') as roll:
            self.assertTrue(shared.should_reply_to_optional_casual({}, result))
            roll.assert_not_called()
        instructions = prompt.split('Rules:', 1)[1]
        self.assertNotIn('any news?', instructions)
        self.assertIn('minimal social response', instructions)
        self.assertIn('Use recent history', instructions)
        self.assertIn('substantive request', instructions)

    def test_required_social_and_optional_acknowledgment_stay_distinct(self):
        for message, required in [('Good evening', True), ('Thank you', False)]:
            result, _ = self.analyze(message, True, required)
            self.assertEqual(result['reply_optional'], not required)
            config = {'LLMChatter.PlayerChat.OptionalCasualReplyChance': 0}
            self.assertEqual(
                shared.should_reply_to_optional_casual(config, result),
                required,
            )

    def test_missing_analysis_does_not_enable_silence(self):
        for response in (None, 'not json', '{}'):
            with patch.object(shared, 'quick_llm_analyze', return_value=response):
                result = shared.find_addressed_bot(
                    'Why?', ['Gruk'], object(), {'enabled': 1},
                )
            self.assertFalse(result['brief_casual'])
            self.assertFalse(result['reply_optional'])

    def test_party_and_guild_keep_their_own_length_hints(self):
        bot = dict(name='Gruk', race='Human', **{'class': 'Mage'},
                   level=20, gender='male')
        for mode in ('normal', 'roleplay'):
            with patch.object(party, '_pick_length_hint', return_value='PARTY_LIMIT'):
                party_prompt = str(party.build_player_response_prompt(
                    bot, ['curious'], 'Player', 'Why?', mode,
                ))
            with patch.object(guild, '_pick_length_hint', return_value='GUILD_LIMIT'):
                guild_prompt = str(guild._build_single_prompt(
                    fixtures._candidate(1, 'Gruk'), 'Keepers', 'Alliance',
                    'Player', 'Why?', '', False, False, False, mode=mode,
                ))
            for prompt, marker in ((party_prompt, 'PARTY_LIMIT'),
                                   (guild_prompt, 'GUILD_LIMIT')):
                self.assertIn(marker, prompt)
                self.assertIn("Within this channel's length guidance", prompt)
                self.assertNotIn('overrides generic', prompt)
        brief = shared.build_conversational_scale_guidance(force_brief=True)
        self.assertIn('overrides generic', brief)
        self.assertIn('Use 2-8 words and no more than 50 characters', brief)


if __name__ == '__main__':
    unittest.main()
