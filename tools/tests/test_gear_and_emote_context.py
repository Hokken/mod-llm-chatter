#!/usr/bin/env python3
"""Gear/pet prompt context and emote prompt awareness.

Run directly from the module root:
  python tools/tests/test_gear_and_emote_context.py
"""

import importlib
import sys
import types
from pathlib import Path


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_non_strict_stubs() -> None:
    for module_name in ("anthropic", "openai"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            module = _ensure_module(module_name)
            class_name = (
                "Anthropic"
                if module_name == "anthropic"
                else "OpenAI"
            )
            setattr(
                module,
                class_name,
                type(class_name, (), {}),
            )

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module(
            "mysql.connector"
        )
        setattr(
            mysql_module,
            "connector",
            connector_module,
        )


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

_install_non_strict_stubs()

from chatter_emote_observer import (  # noqa: E402
    _build_player_prompt,
    _describe_target_player,
)
from chatter_emote_reaction import (  # noqa: E402
    _build_reaction_prompt,
)
from chatter_group_state import (  # noqa: E402
    build_party_context,
)
from chatter_mode import (  # noqa: E402
    build_player_identity,
)
from chatter_group_prompts import (  # noqa: E402
    _append_bots_with_rp,
)
from chatter_db import (  # noqa: E402
    _pet_cache,
    get_character_pet,
)
from chatter_shared import (  # noqa: E402
    append_speaker_gear,
    attach_speaker_gear,
    build_gear_context,
    format_pet_phrase,
    format_weapon_list,
)


class FakeCursor:
    """Answers only the queries these helpers issue."""

    def __init__(self, data):
        self.data = data
        self.rows = []

    def execute(self, sql, params=None):
        if 'character_inventory' in sql:
            self.rows = self.data.get('weapons', [])
        elif 'character_pet' in sql:
            self.rows = self._pet_rows(sql)
        elif 'llm_group_bot_traits' in sql:
            self.rows = [
                {'bot_name': name}
                for name in self.data.get('members', [])
            ]
        elif 'is_bot = 0' in sql:
            player = self.data.get('player')
            self.rows = (
                [{'speaker_name': player}] if player else []
            )
        elif 'llm_group_chat_history' in sql:
            self.rows = self.data.get('history', [])
        else:
            self.rows = []

    def _pet_rows(self, sql):
        """Pet rows, honouring the slot filter the real query
        applies. Test data carries a `slot` the way the table
        does; the query never selects it, so it is dropped
        from what comes back.
        """
        rows = self.data.get('pet', [])
        # The whole point is that the slot is filtered in the
        # WHERE clause, so match that and not a mention of
        # the column anywhere in the statement.
        if 'AND cp.slot = 0' in sql:
            rows = [
                row for row in rows
                if int(row.get('slot', 0)) == 0
            ]
        return [
            {
                key: value for key, value in row.items()
                if key != 'slot'
            }
            for row in rows
        ]

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class FakeDb:
    def __init__(self, **data):
        self.data = data

    def cursor(self, dictionary=False):
        return FakeCursor(self.data)


def test_weapons_render_as_name_and_type():
    weapons = [
        {'name': 'Troll Butcherer', 'kind': 'two-handed sword'},
        {'name': 'Mark "S" Boomstick', 'kind': 'gun'},
    ]
    assert format_weapon_list(weapons) == (
        'Troll Butcherer (two-handed sword), '
        'Mark "S" Boomstick (gun)'
    )


def test_pet_named_after_its_species_is_not_repeated():
    assert format_pet_phrase(
        {'name': 'Kreenum', 'species': 'Felhunter'}
    ) == 'Kreenum, a Felhunter'
    # Bots often name a pet after its species.
    assert format_pet_phrase(
        {'name': 'Sporebat', 'species': 'Sporebat'}
    ) == 'Sporebat'
    assert format_pet_phrase(None) == ''
    # Imp, Owl and friends need "an", and the model
    # copies whatever article the prompt uses.
    assert format_pet_phrase(
        {'name': 'Zeprot', 'species': 'Imp'}
    ) == 'Zeprot, an Imp'


def test_hunter_context_names_weapons_and_pet():
    db = FakeDb(
        weapons=[{
            'slot': 15,
            'item_name': 'Huntsman\'s Harpoon',
            'item_class': 2,
            'item_subclass': 6,
        }],
        pet=[{
            'pet_name': 'Krenas',
            'species': 'Springpaw Stalker',
            'slot': 0,
        }],
    )
    context = build_gear_context(db, 9001, 'Hunter')
    assert "Huntsman's Harpoon (polearm)" in context
    assert 'Krenas, a Springpaw Stalker' in context
    assert 'not a stranger' in context


def test_only_a_summoned_pet_counts_as_a_companion():
    # AzerothCore stores the pet actually out as slot 0.
    # Slots 1-4 are the stable and 100 is owned but
    # dismissed: those animals are not at the hunter's side,
    # and a bot told about one would talk to thin air.
    for slot, present in (
        (0, True), (1, False), (4, False), (100, False),
    ):
        _pet_cache.clear()
        db = FakeDb(pet=[{
            'pet_name': 'Krenas',
            'species': 'Springpaw Stalker',
            'slot': slot,
        }])
        pet = get_character_pet(db, 9010 + slot)
        assert (pet is not None) == present, slot
        if present:
            assert pet == {
                'name': 'Krenas',
                'species': 'Springpaw Stalker',
            }


def test_a_hunter_between_pets_is_described_alone():
    _pet_cache.clear()
    db = FakeDb(
        weapons=[{
            'slot': 15,
            'item_name': 'Huntsman\'s Harpoon',
            'item_class': 2,
            'item_subclass': 6,
        }],
        pet=[{
            'pet_name': 'Krenas',
            'species': 'Springpaw Stalker',
            'slot': 1,
        }],
    )
    context = build_gear_context(db, 9011, 'Hunter')
    assert "Huntsman's Harpoon (polearm)" in context
    assert 'Krenas' not in context
    assert 'pet' not in context.lower()


def test_petless_class_gets_weapons_only():
    db = FakeDb(
        weapons=[{
            'slot': 15,
            'item_name': 'Sky Breaker',
            'item_class': 2,
            'item_subclass': 4,
        }],
        pet=[{'pet_name': 'Ghost', 'species': 'Imp'}],
    )
    context = build_gear_context(db, 9002, 'Warrior')
    assert 'Sky Breaker (one-handed mace)' in context
    # A warrior has no pet, so the row must be ignored.
    assert 'Imp' not in context


def test_shield_and_relic_slots_are_described():
    db = FakeDb(weapons=[
        {
            'slot': 16,
            'item_name': 'Silvermoon Crest Shield',
            'item_class': 4,
            'item_subclass': 6,
        },
        {
            'slot': 17,
            'item_name': 'Libram of Avengement',
            'item_class': 4,
            'item_subclass': 7,
        },
    ])
    context = build_gear_context(db, 9003, 'Paladin')
    assert 'Silvermoon Crest Shield (shield)' in context
    assert 'Libram of Avengement (libram)' in context


def test_gear_context_can_be_switched_off():
    db = FakeDb(weapons=[{
        'slot': 15,
        'item_name': 'Sky Breaker',
        'item_class': 2,
        'item_subclass': 4,
    }])
    context = build_gear_context(
        db, 9004, 'Warrior',
        {'LLMChatter.GearContext.Enable': '0'},
    )
    assert context == ''


def test_identity_carries_gear_when_present():
    plain = build_player_identity(
        'Miranda', 'Human', 'Paladin', 12,
        mode='roleplay',
    )
    assert plain.endswith('World of Warcraft.')

    armed = build_player_identity(
        'Miranda', 'Human', 'Paladin', 12,
        mode='roleplay',
        gear='You are wielding Sky Breaker (one-handed mace).',
    )
    assert 'Sky Breaker (one-handed mace)' in armed
    assert armed.startswith(plain)


def test_party_context_lists_members_and_recent_chat():
    db = FakeDb(
        members=['Miranda', 'Veliana', 'Erodora'],
        player='Vladimir',
        history=[
            {
                'speaker_name': 'Vladimir',
                'is_bot': 0,
                'message': 'watch the ridge',
            },
            {
                'speaker_name': 'Veliana',
                'is_bot': 1,
                'message': 'on it',
            },
        ],
    )
    context = build_party_context(db, 42, 'Miranda')

    # The speaker is not listed among their own party.
    assert 'Miranda' not in context.split('\n')[0]
    assert 'Veliana' in context
    assert 'Erodora' in context
    assert 'Vladimir (player)' in context
    assert 'watch the ridge' in context
    assert 'on it' in context


def test_party_context_empty_without_a_group():
    assert build_party_context(FakeDb(), 0, 'Miranda') == ''


def test_emote_reaction_prompt_carries_context():
    prompt = _build_reaction_prompt(
        'Miranda', 'Human', 'Paladin', 'female',
        'Vladimir', 'point', 'greeting',
        traits=['steady'],
        gear='You are wielding Sky Breaker (one-handed mace).',
        party_context=(
            'Party members: Veliana, Vladimir (player)\n'
            'Recent party chat:\n  Vladimir: watch the ridge'
        ),
    )
    assert 'Sky Breaker' in prompt
    assert 'Party members: Veliana, Vladimir (player)' in prompt
    assert 'watch the ridge' in prompt
    assert 'just /point at you' in prompt


def test_observer_prompt_describes_a_player_target():
    described = _describe_target_player({
        'target_level': 24,
        'target_race': 2,
        'target_class': 3,
    })
    assert described == 'level 24 Orc Hunter'

    prompt = _build_player_prompt(
        'Miranda', 'Human', 'Paladin', 'female',
        'Vladimir', 'point', 'Thrall', 'greeting',
        target_desc=described,
        party_context='Party members: Veliana',
    )
    assert 'Thrall, a level 24 Orc Hunter' in prompt
    assert 'Party members: Veliana' in prompt


def test_observer_prompt_describes_a_gendered_target():
    described = _describe_target_player({
        'target_level': 28,
        'target_race': 8,
        'target_class': 1,
        'target_gender': 1,
    })
    assert described == 'level 28 female Troll Warrior'

    prompt = _build_player_prompt(
        'Miranda', 'Human', 'Paladin', 'female',
        'Vladimir', 'hello', 'Soza', 'greeting',
        target_desc=described,
    )
    assert (
        'Soza, a level 28 female Troll Warrior '
        'from outside the group' in prompt
    )


def test_observer_target_gender_defaults_to_male():
    # gender 0 is the enum's male, not "absent" -- must not be
    # confused with a target payload that omitted the field.
    described = _describe_target_player({
        'target_level': 24,
        'target_race': 2,
        'target_class': 3,
        'target_gender': 0,
    })
    assert described == 'level 24 male Orc Hunter'


def test_observer_target_gender_omitted_from_older_payloads():
    # A payload built before target_gender existed must still
    # describe race/class/level without inventing a gender.
    described = _describe_target_player({
        'target_level': 24,
        'target_race': 2,
        'target_class': 3,
    })
    assert described == 'level 24 Orc Hunter'
    assert 'male' not in described


def test_observer_gender_alone_describes_nothing():
    # Gender with no race or class conveys nothing useful and
    # must not render as a bare "a female".
    assert _describe_target_player({'target_gender': 1}) == ''


def test_observer_falls_back_when_target_unknown():
    assert _describe_target_player({}) == ''

    prompt = _build_player_prompt(
        'Miranda', 'Human', 'Paladin', 'female',
        'Vladimir', 'point', 'Thrall', 'greeting',
    )
    assert 'Thrall, a stranger outside the group' in prompt


def test_named_subject_switches_gear_to_third_person():
    db = FakeDb(
        weapons=[{
            'slot': 15,
            'item_name': 'Staff of the Sun',
            'item_class': 2,
            'item_subclass': 10,
        }],
        pet=[{
            'pet_name': 'Kreenum',
            'species': 'Felhunter',
        }],
    )
    solo = build_gear_context(db, 9101, 'Warlock')
    assert solo.startswith('You are wielding')
    assert 'Your pet is Kreenum, a Felhunter' in solo

    listed = build_gear_context(
        db, 9101, 'Warlock', subject='Samik',
    )
    assert listed.startswith(
        'Samik wields Staff of the Sun (staff).'
    )
    assert "Samik's pet is Kreenum, a Felhunter" in listed
    # Second person would misattribute the gear to whoever
    # the model is speaking as.
    assert 'You are' not in listed
    assert 'Your pet' not in listed


def test_attach_speaker_gear_fills_every_speaker():
    db = FakeDb(weapons=[{
        'slot': 15,
        'item_name': 'Outlaw Sabre',
        'item_class': 2,
        'item_subclass': 7,
    }])
    bots = [
        {'guid': 1003, 'name': 'Erodora', 'class': 'Paladin'},
        {'guid': 1004, 'name': 'Veliana', 'class': 'Priest'},
    ]
    attach_speaker_gear(db, bots, None)
    assert bots[0]['gear_third'].startswith('Erodora wields')
    assert bots[1]['gear_third'].startswith('Veliana wields')


def test_attach_speaker_gear_skips_incomplete_speakers():
    db = FakeDb(weapons=[{
        'slot': 15,
        'item_name': 'Outlaw Sabre',
        'item_class': 2,
        'item_subclass': 7,
    }])
    # A nameless or guidless speaker would render as
    # " wields ...", so it must be left alone.
    bots = [
        {'name': 'Erodora', 'class': 'Paladin'},
        {'guid': 1004, 'class': 'Priest'},
    ]
    attach_speaker_gear(db, bots, None)
    assert 'gear_third' not in bots[0]
    assert 'gear_third' not in bots[1]


def test_append_speaker_gear_only_emits_real_lines():
    parts = []
    append_speaker_gear(parts, {'gear_third': 'Erodora wields X.'})
    append_speaker_gear(parts, {'gear_third': ''})
    append_speaker_gear(parts, {})
    assert parts == ['  Erodora wields X.']


def test_multi_speaker_block_introduces_each_bots_gear():
    parts = []
    bots = [
        {
            'name': 'Erodora', 'level': 26,
            'race': 'Blood Elf', 'class': 'Paladin',
            'gear_third': (
                'Erodora wields Outlaw Sabre '
                '(one-handed sword).'
            ),
        },
        {
            'name': 'Veliana', 'level': 26,
            'race': 'Blood Elf', 'class': 'Priest',
            'gear_third': (
                'Veliana wields Staff of the Sun (staff).'
            ),
        },
    ]
    _append_bots_with_rp(
        parts, bots,
        {'Erodora': ['serious'], 'Veliana': ['playful']},
        is_rp=True,
    )
    block = '\n'.join(parts)
    assert 'Erodora wields Outlaw Sabre' in block
    assert 'Veliana wields Staff of the Sun' in block
    # Each gear line must follow its own speaker.
    assert block.index('Erodora is a level') < block.index(
        'Erodora wields'
    ) < block.index('Veliana is a level')


def main() -> int:
    test_weapons_render_as_name_and_type()
    test_pet_named_after_its_species_is_not_repeated()
    test_hunter_context_names_weapons_and_pet()
    test_only_a_summoned_pet_counts_as_a_companion()
    test_a_hunter_between_pets_is_described_alone()
    test_petless_class_gets_weapons_only()
    test_shield_and_relic_slots_are_described()
    test_gear_context_can_be_switched_off()
    test_identity_carries_gear_when_present()
    test_party_context_lists_members_and_recent_chat()
    test_party_context_empty_without_a_group()
    test_emote_reaction_prompt_carries_context()
    test_observer_prompt_describes_a_player_target()
    test_observer_prompt_describes_a_gendered_target()
    test_observer_target_gender_defaults_to_male()
    test_observer_target_gender_omitted_from_older_payloads()
    test_observer_gender_alone_describes_nothing()
    test_observer_falls_back_when_target_unknown()
    test_named_subject_switches_gear_to_third_person()
    test_attach_speaker_gear_fills_every_speaker()
    test_attach_speaker_gear_skips_incomplete_speakers()
    test_append_speaker_gear_only_emits_real_lines()
    test_multi_speaker_block_introduces_each_bots_gear()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
