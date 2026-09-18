#!/usr/bin/env python3
"""Regression checks for context-aware chatter mode resolution.

The configured ChatterMode is a default, not a verdict: a channel can
override it, and instanced group content overrides both. These tests pin
the resolution order and the shape of the voice contract it produces.
"""

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from chatter_mode import (  # noqa: E402
    CHANNEL_MODE_KEYS,
    GROUP_TASK_CHANNELS,
    build_player_chat_guidance,
    in_instanced_content,
    is_instance_map,
    is_instanced_register,
    is_raid_map,
    is_roleplay,
    normalize_chatter_mode,
    resolve_chatter_mode,
)

NORMAL = {'LLMChatter.ChatterMode': 'normal'}
ROLEPLAY = {'LLMChatter.ChatterMode': 'roleplay'}

DEADMINES = 36
MOLTEN_CORE = 409
WARSONG_GULCH = 489
NAGRAND_ARENA = 559
ELWYNN_FOREST_MAP = 0


def test_map_ids_classify_instanced_content():
    assert is_instance_map(DEADMINES)
    assert is_instance_map(MOLTEN_CORE)
    assert is_instance_map(WARSONG_GULCH)
    assert is_instance_map(NAGRAND_ARENA)
    assert not is_instance_map(ELWYNN_FOREST_MAP)
    assert not is_instance_map(1)      # Kalimdor
    assert not is_instance_map(None)
    assert not is_instance_map('nonsense')

    assert is_raid_map(MOLTEN_CORE)
    assert not is_raid_map(DEADMINES)


def test_server_flags_win_over_an_unknown_map():
    """A map ID we do not recognise still yields to an explicit flag."""
    assert in_instanced_content(map_id=99999, is_dungeon=True)
    assert in_instanced_content(map_id=99999, is_raid=True)
    assert in_instanced_content(map_id=99999, is_battleground=True)
    assert not in_instanced_content(map_id=99999)


def test_empty_config_is_normal():
    assert resolve_chatter_mode({}, 'party') == 'normal'
    assert resolve_chatter_mode(None, 'general') == 'normal'


def test_global_mode_applies_where_no_channel_overrides_it():
    for channel in CHANNEL_MODE_KEYS:
        assert resolve_chatter_mode(ROLEPLAY, channel) == 'roleplay'


def test_channel_override_beats_the_global_default():
    config = {
        'LLMChatter.ChatterMode': 'roleplay',
        'LLMChatter.ChatterMode.Party': 'normal',
    }
    assert resolve_chatter_mode(config, 'party') == 'normal'
    assert resolve_chatter_mode(config, 'general') == 'roleplay'
    assert resolve_chatter_mode(config, 'guild') == 'roleplay'


def test_blank_channel_override_inherits():
    config = {
        'LLMChatter.ChatterMode': 'roleplay',
        'LLMChatter.ChatterMode.Party': '',
        'LLMChatter.ChatterMode.Guild': 'inherit',
    }
    assert resolve_chatter_mode(config, 'party') == 'roleplay'
    assert resolve_chatter_mode(config, 'guild') == 'roleplay'


def test_roleplay_is_gated_inside_instanced_group_content():
    """The case this whole feature exists for.

    Zone chat stays in character; party chat in a dungeon does not.
    """
    assert resolve_chatter_mode(ROLEPLAY, 'general') == 'roleplay'
    assert resolve_chatter_mode(ROLEPLAY, 'guild') == 'roleplay'
    assert resolve_chatter_mode(ROLEPLAY, 'say') == 'roleplay'
    assert resolve_chatter_mode(ROLEPLAY, 'party') == 'roleplay'

    for channel, kwargs in (
        ('party', {'map_id': DEADMINES}),
        ('raid', {'map_id': MOLTEN_CORE}),
        ('raid', {'is_raid': True}),
        ('battleground', {'map_id': WARSONG_GULCH}),
        ('battleground', {'is_battleground': True}),
        ('party', {'is_dungeon': True}),
    ):
        mode = resolve_chatter_mode(ROLEPLAY, channel, **kwargs)
        assert not is_roleplay(mode), (channel, kwargs, mode)


def test_non_group_channels_are_never_gated():
    """Guild and zone chat are social wherever the speaker is standing."""
    for channel in ('general', 'guild', 'say', 'yell'):
        assert resolve_chatter_mode(
            ROLEPLAY, channel, map_id=DEADMINES
        ) == 'roleplay'
        assert channel not in GROUP_TASK_CHANNELS or channel == 'party'


def test_gate_can_be_disabled_for_rp_pve_servers():
    config = {
        **ROLEPLAY,
        'LLMChatter.Roleplay.SuppressInInstances': '0',
    }
    assert resolve_chatter_mode(
        config, 'party', map_id=DEADMINES
    ) == 'roleplay'
    assert resolve_chatter_mode(
        config, 'raid', is_raid=True
    ) == 'roleplay'


def test_explicit_channel_mode_is_taken_at_its_word():
    """An admin naming a channel's mode outranks the instance gate."""
    config = {
        'LLMChatter.ChatterMode': 'normal',
        'LLMChatter.ChatterMode.Raid': 'roleplay',
    }
    assert resolve_chatter_mode(
        config, 'raid', map_id=MOLTEN_CORE
    ) == 'roleplay'
    # ...but an inherited roleplay is still gated
    assert resolve_chatter_mode(
        ROLEPLAY, 'raid', map_id=MOLTEN_CORE
    ) == 'instanced'


def test_instanced_register_is_separate_from_voice():
    assert resolve_chatter_mode(
        NORMAL, 'party', map_id=DEADMINES
    ) == 'instanced'
    assert resolve_chatter_mode(NORMAL, 'party') == 'normal'

    off = {**NORMAL, 'LLMChatter.Instance.TacticalChat': '0'}
    assert resolve_chatter_mode(
        off, 'party', map_id=DEADMINES
    ) == 'normal'


def test_instanced_mode_reads_as_a_player_voice_everywhere():
    """Nothing downstream may mistake 'instanced' for roleplay."""
    assert not is_roleplay('instanced')
    assert is_instanced_register('instanced')
    assert not is_instanced_register('normal')
    assert normalize_chatter_mode('instanced') == 'instanced'
    assert normalize_chatter_mode('nonsense') == 'normal'


def test_instanced_party_chat_uses_the_working_register():
    social = build_player_chat_guidance('normal', 'party')
    working = build_player_chat_guidance('instanced', 'party')

    assert 'CHAT MODE: NORMAL' in social
    assert 'CHAT MODE: NORMAL' in working
    assert 'casual party chat' in social
    assert 'casual party chat' not in working
    assert 'concise dungeon party chat' in working
    assert 'Keep idle chatter short' in working

    # The explicit flag is equivalent, for callers that resolved the mode
    # before they knew where the group was.
    assert build_player_chat_guidance(
        'normal', 'party', instanced=True
    ) == working


def test_raid_and_bg_keep_their_own_channel_notes():
    raid = build_player_chat_guidance('instanced', 'raid')
    bg = build_player_chat_guidance('instanced', 'battleground')
    assert 'concise raid chat' in raid
    assert 'concise dungeon party chat' not in raid
    assert 'battleground team chat' in bg


def test_mixed_rolls_both_ways_and_is_stable_per_seed():
    mixed = {
        'LLMChatter.ChatterMode': 'mixed',
        'LLMChatter.MixedRoleplayChance': '0.5',
    }
    rolled = {
        resolve_chatter_mode(mixed, 'general')
        for _ in range(200)
    }
    assert rolled == {'normal', 'roleplay'}

    # A seeded roll never flips mid-conversation.
    for seed in ('Aliss', 'Kaelthar', 'Brann'):
        picks = {
            resolve_chatter_mode(mixed, 'general', roll_seed=seed)
            for _ in range(50)
        }
        assert len(picks) == 1, (seed, picks)

    # Different bots do not all land on the same voice.
    names = [f'bot{index}' for index in range(60)]
    spread = {
        resolve_chatter_mode(mixed, 'general', roll_seed=name)
        for name in names
    }
    assert spread == {'normal', 'roleplay'}


def test_mixed_chance_bounds_are_respected():
    never = {
        'LLMChatter.ChatterMode': 'mixed',
        'LLMChatter.MixedRoleplayChance': '0',
    }
    always = {
        'LLMChatter.ChatterMode': 'mixed',
        'LLMChatter.MixedRoleplayChance': '1',
    }
    broken = {
        'LLMChatter.ChatterMode': 'mixed',
        'LLMChatter.MixedRoleplayChance': 'not a number',
    }
    assert {
        resolve_chatter_mode(never, 'general') for _ in range(50)
    } == {'normal'}
    assert {
        resolve_chatter_mode(always, 'general') for _ in range(50)
    } == {'roleplay'}
    # A malformed value falls back to the documented 0.5 default
    assert {
        resolve_chatter_mode(broken, 'general') for _ in range(200)
    } == {'normal', 'roleplay'}


def test_mixed_roleplay_is_gated_in_instances_too():
    mixed = {
        'LLMChatter.ChatterMode': 'mixed',
        'LLMChatter.MixedRoleplayChance': '1',
    }
    for _ in range(50):
        mode = resolve_chatter_mode(mixed, 'party', map_id=DEADMINES)
        assert not is_roleplay(mode), mode


def test_shipped_config_documents_every_channel_key():
    text = (
        MODULE_DIR / 'conf' / 'mod_llm_chatter.conf.dist'
    ).read_text(encoding='utf-8')
    for key in set(CHANNEL_MODE_KEYS.values()):
        assert f'{key} =' in text, key
    assert 'LLMChatter.Roleplay.SuppressInInstances = 1' in text
    assert 'LLMChatter.Instance.TacticalChat = 1' in text


def main():
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f'{len(tests)} chatter-mode resolution tests passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
