#!/usr/bin/env python3
"""Persona coherence checks: nothing overrides a bot's identity.

Covers persona resolution precedence, deterministic fallbacks, the
cross-channel event mood, spice/twist gating, and the absence of
random tone/mood overrides in party, guild and General prompts.

Run directly from the module root:
  python tools/tests/test_persona_coherence.py
"""

import importlib
import re
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch


def _ensure_module(name):
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


for dependency in ('anthropic', 'openai'):
    try:
        importlib.import_module(dependency)
    except ModuleNotFoundError:
        module = _ensure_module(dependency)
        attribute = 'Anthropic' if dependency == 'anthropic' else 'OpenAI'
        setattr(module, attribute, type(attribute, (), {}))

try:
    importlib.import_module('mysql.connector')
except ModuleNotFoundError:
    mysql_module = _ensure_module('mysql')
    connector_module = _ensure_module('mysql.connector')
    setattr(mysql_module, 'connector', connector_module)

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_group_state  # noqa: E402
import chatter_persona  # noqa: E402
import chatter_prompts  # noqa: E402
from chatter_general import _build_general_response_prompt  # noqa: E402
from chatter_group import (  # noqa: E402
    build_idle_chatter_prompt,
    build_idle_conversation_prompt,
)
from chatter_group_prompts import (  # noqa: E402
    build_bot_greeting_prompt,
    build_player_msg_conversation_prompt,
    build_precache_combat_pull_prompt,
    build_precache_spell_offensive_prompt,
    build_precache_spell_support_prompt,
    build_precache_state_prompt,
)
from chatter_guild import (  # noqa: E402
    _build_guild_conversation_prompt,
    _build_guild_prompt,
    _query_speaker,
)
from chatter_persona import (  # noqa: E402
    Persona,
    fallback_identity,
    persona_from_fields,
    resolve_persona,
)
from chatter_prompts import (  # noqa: E402
    build_plain_conversation_prompt,
    build_plain_statement_prompt,
    configure_prompt_flavor,
)

RP = {'LLMChatter.ChatterMode': 'roleplay'}
NORMAL = {'LLMChatter.ChatterMode': 'normal'}

STORED_TONE = 'gruff, terse, with a buried warmth'
STORED_TRAITS = ['brooding', 'loyal', 'sardonic']
BACKSTORY = 'Once a Theramore guard who lost her post.'

GRUK = {
    'guid': 101, 'name': 'Gruk', 'race': 'Orc',
    'class': 'Warrior', 'level': 40, 'gender': 'male',
    'zone': 'Barrens',
}
MIRA = {
    'guid': 102, 'name': 'Mira', 'race': 'Human',
    'class': 'Mage', 'level': 40, 'gender': 'female',
    'zone': 'Barrens',
}


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


def _reset_mood():
    with chatter_group_state._bot_mood_scores_lock:
        chatter_group_state._bot_mood_scores.clear()


def _quiet_flavor(**overrides):
    config = {
        'LLMChatter.Persona.TwistChance': 0,
        'LLMChatter.Persona.SpiceChance': 0,
        'LLMChatter.PersonalitySpiceCount': 2,
    }
    config.update(overrides)
    configure_prompt_flavor(config)


class _Cursor:
    def __init__(self, db):
        self.db = db
        self.row = None

    def execute(self, query, params=None):
        self.db.queries.append(query)
        self.row = None
        if 'FROM llm_group_bot_traits' in query:
            if len(params) == 2:
                self.row = self.db.group_rows.get(tuple(params))
            else:
                # Active-group lookup by GUID alone.
                matches = [
                    row for (_, guid), row
                    in self.db.group_rows.items()
                    if guid == params[0]
                ]
                self.row = matches[-1] if matches else None
        elif 'FROM llm_bot_identities' in query:
            self.row = self.db.identity_rows.get(params[0])
        elif 'FROM characters' in query:
            self.row = self.db.characters.get(params[0])

    def fetchone(self):
        return self.row

    def fetchall(self):
        return [self.row] if self.row else []


class _DB:
    def __init__(self, group_rows=None, identity_rows=None,
                 characters=None):
        self.group_rows = group_rows or {}
        self.identity_rows = identity_rows or {}
        self.characters = characters or {}
        self.queries = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)


def _identity_row(traits, tone, backstory=''):
    return {
        'trait1': traits[0], 'trait2': traits[1],
        'trait3': traits[2], 'tone': tone,
        'backstory': backstory,
    }


# ------------------------------------------------------------
# Resolution precedence and the mode boundary
# ------------------------------------------------------------
def test_precedence_group_then_identity_then_fallback():
    group_row = _identity_row(
        ['calm', 'blunt', 'hopeful'], 'group tone', 'group story'
    )
    ident_row = _identity_row(
        STORED_TRAITS, STORED_TONE, BACKSTORY
    )
    db = _DB(
        group_rows={(7, 101): group_row},
        identity_rows={101: ident_row},
    )
    p = resolve_persona(db, 101, 'Gruk', 'roleplay', group_id=7)
    assert p.source == 'group' and p.tone == 'group tone'
    assert p.backstory == 'group story'

    # Without a group id the active group row still wins.
    p = resolve_persona(db, 101, 'Gruk', 'roleplay')
    assert p.source == 'group' and p.tone == 'group tone'

    # Ungrouped: the persistent identity row is used.
    db.group_rows.clear()
    p = resolve_persona(db, 101, 'Gruk', 'roleplay')
    assert p.source == 'identity'
    assert list(p.traits) == STORED_TRAITS
    assert p.tone == STORED_TONE and p.backstory == BACKSTORY

    p = resolve_persona(_DB(), 555, 'Nobody', 'roleplay')
    assert p.source == 'fallback'
    assert len(p.traits) == 3 and p.tone
    assert p.backstory == ''


def test_normal_mode_strips_backstory_and_rp_traits():
    db = _DB(identity_rows={
        101: _identity_row(STORED_TRAITS, STORED_TONE, BACKSTORY)
    })
    p = resolve_persona(db, 101, 'Gruk', 'normal')
    assert p.backstory == ''
    assert 'brooding' not in p.traits
    assert p.tone != STORED_TONE


def test_fallback_is_deterministic_across_calls_and_processes():
    first = fallback_identity(4242, 'Stable', 'roleplay')
    for _ in range(20):
        assert fallback_identity(4242, 'Stable', 'roleplay') == first
    assert fallback_identity(4243, 'Other', 'roleplay') != first
    code = (
        "import sys; sys.path.insert(0, r'%s');"
        "import types;"
        "[sys.modules.setdefault(n, types.ModuleType(n)) "
        " for n in ('mysql', 'mysql.connector')];"
        "sys.modules['mysql'].connector = "
        "sys.modules['mysql.connector'];"
        "from chatter_persona import fallback_identity;"
        "print(repr(fallback_identity(4242, 'Stable', 'roleplay')))"
    ) % TOOLS_DIR
    out = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert out == repr(first), (out, first)


def test_new_group_identity_and_mood_apply_immediately():
    _reset_mood()
    db = _DB()
    p1 = resolve_persona(db, 101, 'Gruk', 'roleplay')
    assert p1.source == 'fallback' and p1.mood == ''
    # The bot joins a group and wipes: both show up at once.
    db.group_rows[(7, 101)] = _identity_row(
        STORED_TRAITS, STORED_TONE
    )
    chatter_group_state.update_bot_mood(7, 101, 'wipe')
    p2 = resolve_persona(db, 101, 'Gruk', 'roleplay')
    assert p2.source == 'group' and p2.tone == STORED_TONE
    assert p2.mood == 'gloomy'
    _reset_mood()


def test_precache_mood_never_replaces_tone():
    """chatter_cache passes the raw event mood label ('neutral'
    included) to all four pre-cache builders; it must render as a
    separate mood line, never as the tone."""
    args = ('Gruk', 'Orc', 'Warrior', 40, STORED_TRAITS)
    builders = [
        lambda mood, mode, tone: build_precache_combat_pull_prompt(
            *args, mood, stored_tone=tone, mode=mode),
        lambda mood, mode, tone: build_precache_state_prompt(
            'low_health', *args, mood, stored_tone=tone,
            mode=mode),
        lambda mood, mode, tone: build_precache_spell_support_prompt(
            *args, mood, stored_tone=tone, mode=mode),
        lambda mood, mode, tone: build_precache_spell_offensive_prompt(
            *args, mood, stored_tone=tone, mode=mode),
    ]
    for mode in ('roleplay', 'normal'):
        fallback = fallback_identity(101, 'Gruk', mode)[1]
        for index, build in enumerate(builders):
            for tone, expected in ((None, fallback),
                                   (STORED_TONE, STORED_TONE)):
                neutral = _text(build('neutral', mode, tone))
                assert f'Your tone: {expected}' in neutral, (
                    mode, index, tone)
                assert 'Current mood' not in neutral
                gloomy = _text(build('gloomy', mode, tone))
                assert f'Your tone: {expected}' in gloomy, (
                    mode, index, tone)
                assert 'Your tone: gloomy' not in gloomy
                assert 'Current mood: gloomy' in gloomy


def test_normal_mode_never_leaks_a_stored_rp_tone():
    rp_tone = 'devout servant of the Light'
    expected = chatter_persona.resolve_player_personality(
        'Gruk', mode='normal'
    )[1]
    for traits in (None, [], ['', ' '], (None, None, None),
                   STORED_TRAITS):
        p = persona_from_fields(
            'Gruk', 'normal', 101, traits=traits, tone=rp_tone,
            backstory=BACKSTORY,
        )
        assert p.tone == expected, (traits, p.tone)
        assert p.backstory == ''
        assert 'brooding' not in p.traits


def test_group_only_identity_is_shared_across_channels():
    """A grouped bot with no persistent identity row (memory
    disabled) keeps its Party identity in Guild and General."""
    _reset_mood()
    _quiet_flavor()
    db = _DB(
        group_rows={(7, 101): _identity_row(
            STORED_TRAITS, STORED_TONE, BACKSTORY
        )},
        characters={
            101: {'name': 'Gruk', 'class': 1, 'race': 2,
                  'gender': 0, 'level': 40},
        },
    )
    party = resolve_persona(db, 101, 'Gruk', 'roleplay', group_id=7)
    general = resolve_persona(db, 101, 'Gruk', 'roleplay')
    assert party == general
    assert general.tone == STORED_TONE
    speaker = _query_speaker(db, 101)
    assert speaker['tone'] == STORED_TONE
    assert speaker['traits'] == STORED_TRAITS
    guild = _build_guild_prompt(
        'Gruk', speaker, 'Horde Heroes', '', config=RP,
    )
    assert STORED_TONE in guild
    reply = _build_general_response_prompt(
        'Gruk', 'Orc', 'Warrior', 40, 'male', general,
        'Player', 'hello there', 'Barrens', '', 'roleplay',
    )
    assert STORED_TONE in reply


def test_missing_tone_bot_sounds_the_same_in_every_builder():
    """A bot with no stored tone gets one stable fallback tone
    across Party single/idle/pre-cache builders, Guild and General,
    in both modes."""
    _reset_mood()
    _quiet_flavor()
    db = _DB(characters={
        101: {'name': 'Gruk', 'class': 1, 'race': 2,
              'gender': 0, 'level': 40},
    })
    for mode in ('roleplay', 'normal'):
        expected = fallback_identity(101, 'Gruk', mode)[1]
        greeting = _text(build_bot_greeting_prompt(
            GRUK, STORED_TRAITS, mode,
        ))
        idle = _text(build_idle_chatter_prompt(
            GRUK, STORED_TRAITS, mode,
        ))
        precache = _text(build_precache_combat_pull_prompt(
            'Gruk', 'Orc', 'Warrior', 40, STORED_TRAITS, 'neutral',
            mode=mode,
        ))
        general = resolve_persona(db, 101, 'Gruk', mode)
        speaker = _query_speaker(db, 101)
        guild = _build_guild_prompt(
            'Gruk', speaker, 'Horde Heroes', '',
            config={'LLMChatter.ChatterMode': mode},
        )
        for label, prompt in (
            ('greeting', greeting), ('idle', idle),
            ('precache', precache), ('guild', guild),
        ):
            assert expected in prompt, (mode, label, expected)
        assert general.tone == expected, (mode, general.tone)


# ------------------------------------------------------------
# Cross-channel real event mood
# ------------------------------------------------------------
def test_event_mood_reaches_party_guild_and_general():
    _reset_mood()
    _quiet_flavor()
    chatter_group_state.update_bot_mood(9, 101, 'wipe')

    # Party: idle chatter for Gruk (who wiped) and Mira.
    gruk_party = _text(build_idle_chatter_prompt(
        GRUK, STORED_TRAITS, 'roleplay',
        stored_tone=STORED_TONE,
    ))
    mira_party = _text(build_idle_chatter_prompt(
        MIRA, ['calm', 'kind', 'curious'], 'roleplay',
        stored_tone='soft and warm',
    ))
    assert 'Current mood: gloomy' in gruk_party
    assert 'Current mood' not in mira_party

    # Guild: speaker loaded from the DB like the handler does.
    db = _DB(
        identity_rows={
            101: _identity_row(STORED_TRAITS, STORED_TONE),
        },
        characters={
            101: {'name': 'Gruk', 'class': 1, 'race': 2,
                  'gender': 0, 'level': 40},
            102: {'name': 'Mira', 'class': 8, 'race': 1,
                  'gender': 1, 'level': 40},
        },
    )
    gruk_speaker = _query_speaker(db, 101)
    mira_speaker = _query_speaker(db, 102)
    assert gruk_speaker['mood'] == 'gloomy'
    assert mira_speaker['mood'] == ''
    guild = _build_guild_prompt(
        'Gruk', gruk_speaker, 'Horde Heroes', '', config=RP,
    )
    assert 'Current mood: gloomy' in guild
    assert STORED_TONE in guild
    conv = _build_guild_conversation_prompt(
        [{'name': 'Gruk', 'speaker': gruk_speaker},
         {'name': 'Mira', 'speaker': mira_speaker}],
        'Horde Heroes', '', 'old wars', '', False, 3,
    )
    assert 'Gruk current mood gloomy' in conv
    assert 'Mira current mood' not in conv

    # General: persona resolved like the ambient/reply paths.
    gruk_general = resolve_persona(db, 101, 'Gruk', 'roleplay')
    reply = _build_general_response_prompt(
        'Gruk', 'Orc', 'Warrior', 40, 'male', gruk_general,
        'Player', 'hello there', 'Barrens', '', 'roleplay',
    )
    assert 'Current mood: gloomy' in reply
    ambient = _text(build_plain_statement_prompt(
        {**MIRA, 'persona': resolve_persona(
            db, 102, 'Mira', 'roleplay')},
        config=RP,
    ))
    assert 'Current mood' not in ambient
    _reset_mood()


def test_stale_mood_expires_and_no_events_means_no_mood():
    _reset_mood()
    chatter_group_state.update_bot_mood(9, 101, 'wipe')
    assert chatter_persona.resolve_mood(101) == 'gloomy'
    later = (
        chatter_group_state.time.time()
        + chatter_group_state._MOOD_STALE_SECONDS + 1
    )
    with patch.object(
        chatter_group_state.time, 'time', return_value=later
    ):
        assert chatter_persona.resolve_mood(101) == ''
    _reset_mood()
    assert chatter_persona.resolve_mood(101) == ''
    assert chatter_persona.resolve_mood(0) == ''


def test_mood_uses_the_most_recent_group_entry():
    _reset_mood()
    now = chatter_group_state.time.time()
    with patch.object(
        chatter_group_state.time, 'time', return_value=now
    ):
        chatter_group_state.update_bot_mood(1, 101, 'wipe')
    with patch.object(
        chatter_group_state.time, 'time', return_value=now + 5
    ):
        # levelup +2.0 in group 2 -> cheerful
        chatter_group_state.update_bot_mood(2, 101, 'levelup')
        assert chatter_persona.resolve_mood(101) == 'cheerful'
    _reset_mood()


# ------------------------------------------------------------
# No overrides: stored tone wins, no random mood sequences
# ------------------------------------------------------------
def test_party_conversations_carry_each_speakers_tone():
    _reset_mood()
    _quiet_flavor()
    bots = [
        {**GRUK, 'tone': STORED_TONE},
        {**MIRA, 'tone': 'soft and warm'},
    ]
    traits_map = {
        'Gruk': STORED_TRAITS, 'Mira': ['calm', 'kind', 'curious'],
    }
    for mode in ('roleplay', 'normal'):
        idle = _text(build_idle_conversation_prompt(
            bots, traits_map, mode, 'the weather',
            backstory_map={'Gruk': BACKSTORY},
        ))
        reply = _text(build_player_msg_conversation_prompt(
            bots, traits_map, 'Player', 'what now?', mode,
        ))
        for prompt in (idle, reply):
            assert 'Overall tone' not in prompt
            assert 'mood=' not in prompt
            assert 'Speaker personalities:' in prompt
            assert 'length=' in prompt
        if mode == 'roleplay':
            assert STORED_TONE in idle and 'soft and warm' in idle
            assert BACKSTORY in idle
            assert STORED_TONE in reply
        else:
            # Normal mode never sees roleplay identity data.
            assert BACKSTORY not in idle
            assert 'brooding' not in idle


def test_general_conversation_uses_personas_not_dice():
    _reset_mood()
    _quiet_flavor()
    bots = [
        {**GRUK, 'persona': persona_from_fields(
            'Gruk', 'roleplay', 101, STORED_TRAITS, STORED_TONE,
        )},
        dict(MIRA),
    ]
    prompt = _text(build_plain_conversation_prompt(bots, config=RP))
    assert 'Overall tone' not in prompt
    assert 'mood=' not in prompt
    assert STORED_TONE in prompt
    mira_tone = fallback_identity(102, 'Mira', 'roleplay')[1]
    assert mira_tone in prompt


def test_single_speaker_fallback_tone_is_stable():
    _quiet_flavor()
    first = _text(build_bot_greeting_prompt(
        GRUK, STORED_TRAITS, 'roleplay'
    ))
    tone = re.search(r'Your tone: ([^\n]+)', first).group(1)
    for _ in range(10):
        again = _text(build_bot_greeting_prompt(
            GRUK, STORED_TRAITS, 'roleplay'
        ))
        assert f'Your tone: {tone}' in again


def test_no_random_tone_or_mood_calls_in_scoped_builders():
    scoped = [
        'chatter_prompts.py', 'chatter_general.py',
        'chatter_group.py', 'chatter_group_prompts.py',
        'chatter_guild.py', 'chatter_guild_player.py',
        'chatter_ambient.py', 'chatter_world_events.py',
        'chatter_loot.py', 'chatter_handler_pipeline.py',
    ]
    banned = re.compile(
        r'pick_random_tone\(|pick_random_mood\(|'
        r'generate_conversation_mood_sequence|_pick_random_traits'
        r'|mood=\{'
    )
    for name in scoped:
        source = (TOOLS_DIR / name).read_text(encoding='utf-8')
        if name == 'chatter_prompts.py':
            # The definition itself may remain for out-of-scope
            # callers (duel); no builder may call it.
            source = source.replace(
                'def pick_random_tone(', 'def _defined_tone('
            )
        match = banned.search(source)
        assert not match, f"{name}: {match.group(0)}"


# ------------------------------------------------------------
# Flavor gating: spices and twists
# ------------------------------------------------------------
def _spice_lines(prompt):
    return [
        line for line in prompt.splitlines()
        if 'Background feelings' in line
    ]


def test_spice_chance_zero_never_adds_spices():
    _quiet_flavor(**{'LLMChatter.Persona.SpiceChance': 0})
    for _ in range(200):
        prompt = _text(build_idle_chatter_prompt(
            GRUK, STORED_TRAITS, 'roleplay',
            stored_tone=STORED_TONE,
        ))
        assert not _spice_lines(prompt)


def test_spice_chance_full_uses_count_and_subordinate_wording():
    _quiet_flavor(**{
        'LLMChatter.Persona.SpiceChance': 100,
        'LLMChatter.PersonalitySpiceCount': 2,
    })
    for _ in range(50):
        prompt = _text(build_idle_chatter_prompt(
            GRUK, STORED_TRAITS, 'roleplay',
            stored_tone=STORED_TONE,
        ))
        lines = _spice_lines(prompt)
        assert len(lines) == 1
        assert 'fit your personality' in lines[0]
        items = lines[0].split('): ', 1)[1].split('; ')
        assert len(items) == 2, items


def test_spice_count_zero_disables_spices():
    _quiet_flavor(**{
        'LLMChatter.Persona.SpiceChance': 100,
        'LLMChatter.PersonalitySpiceCount': 0,
    })
    for _ in range(50):
        prompt = _text(build_idle_chatter_prompt(
            GRUK, STORED_TRAITS, 'roleplay',
            stored_tone=STORED_TONE,
        ))
        assert not _spice_lines(prompt)
    assert chatter_prompts.maybe_pick_personality_spices() == []


def test_twist_chance_gates_and_labels_twists():
    _quiet_flavor(**{'LLMChatter.Persona.TwistChance': 0})
    for _ in range(100):
        prompt = _text(build_bot_greeting_prompt(
            GRUK, STORED_TRAITS, 'roleplay',
            stored_tone=STORED_TONE,
        ))
        assert 'Optional angle' not in prompt
        assert 'Creative twist' not in prompt
    _quiet_flavor(**{'LLMChatter.Persona.TwistChance': 100})
    prompt = _text(build_bot_greeting_prompt(
        GRUK, STORED_TRAITS, 'roleplay', stored_tone=STORED_TONE,
    ))
    assert 'Optional angle (use only if it fits your personality)' \
        in prompt


def test_persona_block_states_priority_rule():
    block = chatter_persona.build_persona_block(
        Persona('Gruk', tuple(STORED_TRAITS), STORED_TONE,
                BACKSTORY, 'gloomy'),
        'roleplay',
    )
    assert 'never let them change who you are' in block
    assert BACKSTORY in block
    normal = chatter_persona.build_persona_block(
        Persona('Gruk', ('friendly',), 'warm', BACKSTORY),
        'normal',
    )
    assert BACKSTORY not in normal


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    _quiet_flavor(**{
        'LLMChatter.Persona.TwistChance': 25,
        'LLMChatter.Persona.SpiceChance': 30,
    })
    print(f"{len(tests)} persona coherence checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
