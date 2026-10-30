#!/usr/bin/env python3
"""Tone, backstory, greeting and farewell generation see the whole character.

Both prompts carry the gender, the race outlook and history, the class
calling and the race+class note, so a generated tone or backstory fits
the character's people and calling. The roleplay greeting and farewell
carry the race+class note.

Run directly from the module root:
  python tools/tests/test_identity_prompts.py
"""

import unittest
from pathlib import Path
from unittest.mock import patch

import test_persona_coherence  # noqa: F401  dependency stubs, tools path

import chatter_group_prompts as group_prompts
import chatter_group_state as group_state
import chatter_identity as identity
import chatter_shared


def _prompt(fn, *args, **kwargs):
    with patch.object(identity, '_generate_field',
                      return_value='x') as field:
        fn(None, {}, 101, None, *args, **kwargs)
    return field.call_args.args[7]


class IdentityPromptTests(unittest.TestCase):
    TRAITS = ['wry', 'loyal', 'curious']

    def _check_lore(self, prompt):
        self.assertIn('Blood Elf outlook:', prompt)
        self.assertIn('Blood Elf history:', prompt)
        self.assertIn('Hunter calling:', prompt)
        self.assertIn(
            "Melindra's people and calling (Blood Elf Hunter):", prompt)

    def test_tone_prompt_has_gender_and_lore(self):
        prompt = _prompt(
            identity._generate_bot_tone, 'Melindra', 'Hunter',
            'Blood Elf', self.TRAITS, bot_gender='female')
        self.assertIn('Bot: Melindra (female Blood Elf Hunter)', prompt)
        self._check_lore(prompt)

    def test_backstory_prompt_has_gender_and_lore(self):
        prompt = _prompt(
            identity._generate_bot_backstory, 'Melindra', 'Hunter',
            'Blood Elf', self.TRAITS, 'dry and watchful',
            bot_gender='female')
        self.assertIn('Character: Melindra, a female Blood Elf Hunter.',
                      prompt)
        self._check_lore(prompt)

    def test_race_class_note_follows_its_toggle(self):
        chatter_shared.set_race_class_notes_enabled(False)
        try:
            prompt = _prompt(
                identity._generate_bot_tone, 'Melindra', 'Hunter',
                'Blood Elf', self.TRAITS)
        finally:
            chatter_shared.set_race_class_notes_enabled(True)
        self.assertNotIn('calling (Blood Elf Hunter):', prompt)
        self.assertIn('Hunter calling:', prompt)
        self.assertIn('Bot: Melindra (Blood Elf Hunter)', prompt)

    def test_every_tone_caller_passes_the_gender(self):
        for rel in ('chatter_identity.py', 'chatter_group_state.py'):
            text = (Path(identity.__file__).parent / rel).read_text(
                encoding='utf-8')
            calls = text.split('tone = _generate_bot_tone(')[1:]
            self.assertTrue(calls, rel)
            for call in calls:
                self.assertIn('gender', call.split(')\n')[0], rel)


class FarewellPromptTests(unittest.TestCase):
    def _prompt(self, mode='roleplay'):
        with patch.object(group_state, 'call_llm',
                          return_value='') as llm:
            group_state._generate_farewell(
                None, None, {}, 'Kratumm', 'Orc', 'Warlock', 'male',
                ['calm', 'wanderer', 'ruthless'], mode, 7, 101)
        return llm.call_args.args[1]

    def test_roleplay_farewell_has_race_class_note(self):
        self.assertIn('Your people and calling (Orc Warlock):',
                      self._prompt())

    def test_normal_farewell_and_disabled_notes_have_none(self):
        self.assertNotIn('people and calling', self._prompt('normal'))
        chatter_shared.set_race_class_notes_enabled(False)
        try:
            self.assertNotIn('people and calling', self._prompt())
        finally:
            chatter_shared.set_race_class_notes_enabled(True)


class GreetingPromptTests(unittest.TestCase):
    BOT = {'guid': 101, 'name': 'Veliana', 'class': 'Priest',
           'race': 'Blood Elf', 'level': 35, 'gender': 'female'}

    def _prompt(self, mode='roleplay', style=None):
        return group_prompts.build_bot_greeting_prompt(
            self.BOT, ['playful', 'devout', 'curious'], mode,
            class_style=style)

    def test_roleplay_greeting_has_race_class_note(self):
        self.assertIn('Your people and calling (Blood Elf Shadow Priest):',
                      self._prompt(style='Shadow Priest'))
        # No style known: a priest gets the Light note.
        self.assertIn('(Blood Elf Light Priest):', self._prompt())

    def test_normal_greeting_has_none(self):
        self.assertNotIn('people and calling', self._prompt('normal'))

    def test_both_greeting_paths_pass_the_style(self):
        source = (Path(group_prompts.__file__).parent
                  / 'chatter_group.py').read_text(encoding='utf-8')
        calls = source.split('prompt = build_bot_greeting_prompt(')[1:]
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertIn('class_style=class_style(',
                          call.split('prompt = with_party_genders(')[0])


if __name__ == '__main__':
    unittest.main()
