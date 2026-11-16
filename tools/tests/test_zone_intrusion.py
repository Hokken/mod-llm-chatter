#!/usr/bin/env python3
"""Zone intrusion yells: the place, both characters, the speaker's voice,
and "city" only for real cities.
Run directly from the module root:
  python tools/tests/test_zone_intrusion.py
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_persona_coherence as persona_tests  # noqa: E402  stubs + path
import chatter_events  # noqa: E402
from chatter_persona import Persona  # noqa: E402
from chatter_prompts import build_zone_intrusion_prompt  # noqa: E402

RP = persona_tests.RP
NORMAL = persona_tests.NORMAL
DUROTAR, ORGRIMMAR, RAZOR_HILL = 14, 1637, 362

EXTRA = {
    'defender_guid': 102, 'defender_name': 'Mira',
    'defender_class': 3, 'defender_race': 2, 'defender_level': 20,
    'intruder_name': 'Lyn', 'intruder_class': 4,
    'intruder_race': 1, 'intruder_level': 18,
    'zone_name': 'Durotar',
}
LORE = {
    'defender': ['Hunter calling: trackers of the wild.'],
    'intruder': ['Rogue calling: blades in the shadows.'],
}


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


def _situation(prompt):
    """The SITUATION line; place lore may name a capital."""
    return prompt.split('SITUATION')[1].split('\n')[0].lower()


def _prompt(config, zone_id, **extra):
    return _text(build_zone_intrusion_prompt(
        {**EXTRA, **extra}, config, zone_id=zone_id,
        persona_block='Your tone: gruff and short', lore=LORE,
    ))


def test_an_ordinary_zone_is_territory_never_a_city():
    for config in (RP, NORMAL):
        prompt = _prompt(config, DUROTAR)
        assert "your faction's territory!" in prompt
        assert 'city' not in _situation(prompt)
        assert 'capital' not in _situation(prompt)


def test_only_a_real_city_is_called_a_city():
    prompt = _prompt(RP, ORGRIMMAR, zone_name='Orgrimmar')
    assert "your faction's city!" in prompt
    assert 'capital' not in _situation(prompt)


def test_payload_capital_flag_is_ignored():
    # A bot intruder's payload always claimed a capital.
    prompt = _prompt(RP, DUROTAR, is_capital=True)
    assert "your faction's territory!" in prompt


def test_roleplay_describes_place_and_both_characters():
    prompt = _prompt(RP, DUROTAR)
    assert 'Zone context: Durotar' in prompt
    assert 'About you:\nHunter calling' in prompt
    assert 'About the enemy, Lyn:\nRogue calling' in prompt
    assert 'Your tone: gruff and short' in prompt


def test_roleplay_never_hears_the_enemy_level():
    assert 'level 18' not in _situation(_prompt(RP, DUROTAR))
    assert 'level 18' in _situation(_prompt(NORMAL, DUROTAR))


def test_normal_mode_keeps_names_and_voice_only():
    prompt = _prompt(NORMAL, DUROTAR)
    assert 'Zone: Durotar' in prompt
    assert 'Zone context' not in prompt
    assert 'About you' not in prompt
    assert 'About the enemy' not in prompt
    assert 'Your tone: gruff and short' in prompt


def test_subzone_is_named_when_the_worldserver_sends_it():
    prompt = _prompt(
        RP, DUROTAR, area_id=RAZOR_HILL, subzone_name='Razor Hill',
    )
    assert 'Subzone: Razor Hill' in prompt
    # An older payload has neither field and still works.
    assert 'Subzone' not in _prompt(RP, DUROTAR)


def test_handler_passes_persona_lore_and_zone():
    captured = {}

    def fake_reaction(db, client, config, prompt, **kwargs):
        captured['prompt'] = _text(prompt)
        return {'ok': True}

    persona = Persona(
        name='Mira', traits=('stubborn',), tone='clipped and wary',
    )
    event = {
        'id': 7, 'zone_id': DUROTAR, 'subject_guid': 103,
        'extra_data': dict(EXTRA),
    }
    with patch.object(chatter_events, 'run_single_reaction',
                      side_effect=fake_reaction), \
            patch.object(chatter_events, 'prepare_channel_persona',
                         return_value=persona), \
            patch.object(chatter_events, 'get_genders_by_guid',
                         return_value={}), \
            patch.object(chatter_events, 'get_character_genders',
                         return_value={}):
        chatter_events.process_zone_intrusion_event(
            None, None, RP, event,
        )
    prompt = captured['prompt']
    assert 'Your personality: stubborn' in prompt
    assert 'Your tone: clipped and wary' in prompt
    assert 'About the enemy, Lyn:' in prompt
    assert 'Rogue calling' in prompt
    assert "your faction's territory!" in prompt


def test_world_event_context_calls_only_cities_cities():
    base = {'event_type': 'player_enters_zone', 'extra_data': json.dumps({
        'intruder_name': 'Lyn', 'intruder_level': 18,
        'zone_name': 'Durotar', 'is_capital': True,
    })}
    text = chatter_events.build_event_context(
        {**base, 'zone_id': DUROTAR}
    )
    assert 'city' not in text and 'capital' not in text
    text = chatter_events.build_event_context(
        {**base, 'zone_id': ORGRIMMAR}
    )
    assert '(a city)' in text and 'capital' not in text


if __name__ == '__main__':
    for name, func in sorted(globals().items()):
        if name.startswith('test_') and callable(func):
            func()
            print(f'ok {name}')
