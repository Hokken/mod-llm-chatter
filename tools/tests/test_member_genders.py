#!/usr/bin/env python3
"""Genders of other named characters reach party and BG prompts.

Covers the character lookup (found, missing, NULL, error), the gender
line, the party line on pipeline event reactions, BG subject names (only
player keys the prompt already shows), and the gender word in multi-bot
cast headers, including the never-default-to-male rule.

Run directly from the module root:
  python tools/tests/test_member_genders.py
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_party_backstory as backstory_tests  # noqa: E402  stubs + path

import chatter_handler_pipeline as pipeline  # noqa: E402
import chatter_member_gender as gender  # noqa: E402
from chatter_group_prompts import (  # noqa: E402
    _append_bots_with_rp,
    build_quest_complete_conversation_prompt,
)

GRUK = backstory_tests.GRUK
MIRA = backstory_tests.MIRA
RP = backstory_tests.RP


class FakeCursor:
    def __init__(self, rows, fail=False, members=()):
        self.rows = rows
        self.fail = fail
        self.members = list(members)
        self.params = None
        self.membership = False
        self.closed = False

    def execute(self, sql, params=None):
        if self.fail:
            raise RuntimeError('db down')
        self.membership = 'group_member' in sql
        assert self.membership or 'FROM characters' in sql
        self.params = params

    def fetchall(self):
        if self.membership:
            return [{'name': n} for n in self.members]
        wanted = set(self.params or ())
        return [r for r in self.rows if r['name'] in wanted]

    def close(self):
        self.closed = True


class FakeDB:
    def __init__(self, rows=(), fail=False, members=()):
        self.cursor_obj = FakeCursor(list(rows), fail, members)
        self.calls = 0

    def cursor(self, dictionary=False):
        self.calls += 1
        return self.cursor_obj


ROWS = [
    {'name': 'Ana', 'gender': 1},
    {'name': 'Dee', 'gender': 1},
    {'name': 'Gruk', 'gender': 0},
    {'name': 'Bo', 'gender': 0},
    {'name': 'Cat', 'gender': 1},
    {'name': 'Nul', 'gender': None},
]


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


# ------------------------------------------------------------
# Lookup and formatting
# ------------------------------------------------------------
def test_lookup_maps_found_rows_only():
    db = FakeDB(ROWS)
    found = gender.get_character_genders(
        db, ['Ana', 'Bo', 'Ghost', 'Nul', '', None],
    )
    assert found == {'Ana': 'female', 'Bo': 'male'}
    assert db.cursor_obj.closed


def test_lookup_failures_return_nothing():
    assert gender.get_character_genders(FakeDB(fail=True), ['Ana']) == {}
    assert gender.get_character_genders(None, ['Ana']) == {}
    empty = FakeDB(ROWS)
    assert gender.get_character_genders(empty, []) == {}
    assert empty.calls == 0


def test_gender_line_tags_player_and_skips_excluded():
    line = gender.format_gender_line(
        {'Ana': 'female', 'Bo': 'male', 'Cat': 'female'},
        player_name='Cat', exclude=('Bo',),
    )
    assert 'Ana is female' in line
    assert 'Cat (the player) is female' in line
    assert 'Bo' not in line
    assert 'pronouns' in line
    assert gender.format_gender_line({}) == ''
    assert gender.format_gender_line(
        {'Bo': 'male'}, exclude=('Bo',),
    ) == ''


def test_party_line_covers_bots_and_player():
    db = FakeDB(ROWS)
    with patch('chatter_group_state.get_group_members',
               return_value=['Ana', 'Bo']), \
            patch('chatter_group_state.get_group_player_name',
                  return_value='Cat'):
        line = gender.party_gender_line(db, 7, 'Bo')
    assert 'Ana is female' in line
    assert 'Cat (the player) is female' in line
    assert 'Bo is' not in line
    assert gender.party_gender_line(db, 0, 'Bo') == ''


# ------------------------------------------------------------
# Event reactions through the pipeline
# ------------------------------------------------------------
def _run_event(db, members, player):
    captured = {}

    def fake_reaction(db, client, cfg, prompt, **kwargs):
        captured['prompt'] = _text(prompt)
        return {'ok': True, 'message': 'Hm.', 'message_id': None}

    patches = [
        patch('chatter_group_state.get_group_members',
              return_value=members),
        patch('chatter_group_state.get_group_player_name',
              return_value=player),
        patch.object(pipeline, 'get_bot_traits', return_value={
            'traits': ['gruff'], 'tone': 'terse', 'backstory': None,
        }),
        patch.object(pipeline, 'build_gear_context', return_value=''),
        patch.object(pipeline, 'get_character_guild_name',
                     return_value=''),
        patch.object(pipeline, '_get_recent_chat', return_value=[]),
        patch.object(pipeline, '_maybe_talent_context',
                     return_value=None),
        patch.object(pipeline, 'run_single_reaction',
                     side_effect=fake_reaction),
        patch.object(pipeline, '_store_chat'),
        patch.object(pipeline, '_mark_event'),
        patch.object(pipeline, 'update_bot_mood'),
    ]
    for p in patches:
        p.start()
    try:
        pipeline.run_group_handler(
            db, None, backstory_tests.NORMAL, {'id': 1},
            event_type_label='bot_group_loot',
            extract_fields=lambda ed: {},
            build_prompt=lambda ctx: 'Ana looted a sword.',
            pre_parsed_extra={
                'bot_guid': 101, 'bot_name': 'Gruk', 'group_id': 7,
                'bot_class': 1, 'bot_race': 2,
            },
        )
    finally:
        for p in patches:
            p.stop()
        backstory_tests.chatter_threads.clear_all()
    return captured['prompt']


def test_loot_reaction_states_the_looters_gender():
    prompt = _run_event(FakeDB(ROWS), ['Gruk', 'Ana'], 'Cat')
    assert 'Ana is female' in prompt
    assert 'Cat (the player) is female' in prompt


def test_pipeline_unchanged_when_lookup_fails():
    prompt = _run_event(FakeDB(fail=True), ['Gruk', 'Ana'], 'Cat')
    assert 'Genders:' not in prompt
    assert pipeline.party_gender_line is gender.party_gender_line


def test_second_human_in_group_gets_a_gender():
    # Cat spoke last, so get_group_player_name picks Cat; Dee is the
    # other human, known only from group membership, and loots the item.
    db = FakeDB(ROWS, members=['Gruk', 'Ana', 'Cat', 'Dee'])
    prompt = _run_event(db, ['Gruk', 'Ana'], 'Cat')
    assert 'Dee is female' in prompt
    assert 'Cat (the player) is female' in prompt
    assert 'Dee (the player)' not in prompt
    assert 'Gruk is' not in prompt  # the speaker is never listed


def test_party_wrapper_keeps_structured_prompt_metadata():
    from chatter_llm import _split_prompt
    from chatter_shared import PromptParts, append_json_instruction
    from chatter_structured import structured_output_enabled

    base = append_json_instruction('Ana looted a sword.', allow_action=False)
    with patch('chatter_group_state.get_group_members',
               return_value=['Gruk', 'Ana']), \
            patch('chatter_group_state.get_group_player_name',
                  return_value='Cat'):
        wrapped = gender.with_party_genders(base, FakeDB(ROWS), 7, 'Gruk')
    assert isinstance(base, PromptParts) and isinstance(wrapped, PromptParts)
    assert 'Ana is female' in wrapped.user_prompt
    assert wrapped.response_contract == base.response_contract
    assert wrapped.structured_system_prompt == base.structured_system_prompt
    assert not wrapped.contract_conflict
    # Structured off: the request splits into the same system prompt.
    # Structured on: the same contract and structured system prompt apply.
    for flag in ('0', '1'):
        config = {'LLMChatter.StructuredOutput.Enable': flag}
        assert structured_output_enabled(config) == (flag == '1')
        sys_msg, user_msg = _split_prompt(wrapped)
        base_sys, _ = _split_prompt(base)
        assert sys_msg == base_sys
        assert 'Ana is female' in user_msg
    assert wrapped.response_contract is not None


# ------------------------------------------------------------
# Battleground subjects
# ------------------------------------------------------------
def test_bg_line_names_only_shown_player_subjects():
    db = FakeDB(ROWS)
    extra = {
        'carrier_name': 'Ana',
        'claimer_name': 'Cat',
        'target_name': 'Bo',  # can be a creature or pet: never looked up
    }
    prompt = 'Ana grabbed the enemy flag! Cheer them on by name (Ana).'
    line = gender.bg_subject_gender_line(db, extra, prompt, 'Gruk')
    assert line.startswith('Genders: Ana is female')
    assert 'Cat' not in line  # withheld from the prompt, so withheld here
    assert 'Bo' not in line
    assert gender.bg_subject_gender_line(
        db, {'carrier_name': 'Gruk'}, 'Gruk has the flag', 'Gruk',
    ) == ''
    # Casters, the fallen teammate and batched achievers are players.
    line = gender.bg_subject_gender_line(
        db,
        {'caster_name': 'Bo', 'dead_name': 'Ana',
         'achiever_name': 'Cat and Bo'},
        'Bo healed you. Your teammate Ana fell. Cat and Bo earned it.',
        'Gruk',
    )
    assert 'Ana is female' in line
    assert 'Bo is male' in line
    assert 'Cat is female' in line
    # Whole-word match only: "Ana" inside "Banana" is not a mention.
    assert gender.bg_subject_gender_line(
        db, {'carrier_name': 'Ana'}, 'Banana time', 'Gruk',
    ) == ''


BG_BOT = {'bot_name': 'Gruk', 'bot_guid': 100, 'race': 'Orc',
          'class': 'Warrior', 'gender': 'male', 'level': 40}


def _bg_extra():
    return dict(
        bg_type_id=2, bg_map_id=489, group_id=91, player_subgroup=2,
        team='Horde', is_battleground=True, raid_bot_guids=[100],
        real_players=[{'name': 'Ana', 'race': 'Orc'},
                      {'name': 'Cat', 'race': 'Troll'}],
    )


def _bg_idle(extra, bot):
    from chatter_bg_prompts import build_bg_idle_prompt
    with patch('chatter_bg_prompts.pick_personality_spices',
               return_value=[]), \
            patch('chatter_bg_prompts.build_environmental_context_lines',
                  return_value=[]):
        return build_bg_idle_prompt(extra, bot)


def test_bg_real_player_roster_gets_genders():
    extra = _bg_extra()
    prompt = _text(_bg_idle(extra, BG_BOT))
    assert 'Ana' in prompt and 'Cat' in prompt
    line = gender.bg_subject_gender_line(
        FakeDB(ROWS), extra, prompt, 'Gruk',
    )
    assert 'Ana is female' in line and 'Cat is female' in line
    # A roster name the prompt does not show stays out.
    assert gender.bg_subject_gender_line(
        FakeDB(ROWS), extra, 'Hold the flag room.', 'Gruk',
    ) == ''


def test_bg_raid_worker_sends_the_gender_line():
    import chatter_raid_base as raid
    captured = {}

    def fake_reaction(db, client, cfg, prompt, **kwargs):
        captured['prompt'] = _text(prompt)
        return {'ok': True}

    with patch.object(raid, 'get_lightweight_bot_data',
                      return_value=dict(BG_BOT)), \
            patch.object(raid, '_maybe_talent_context', return_value=''), \
            patch.object(raid, 'run_single_reaction',
                         side_effect=fake_reaction):
        raid.fire_raid_worker(
            FakeDB(ROWS), None, {}, {'id': 5}, _bg_extra(),
            prompt_fn=lambda ed, bd, is_raid_worker=False: _bg_idle(ed, bd),
        )
    assert 'Ana is female' in captured['prompt']


# ------------------------------------------------------------
# Multi-bot cast headers
# ------------------------------------------------------------
def test_cast_header_renders_gender_and_never_defaults():
    parts = []
    unknown = dict(GRUK, name='Zed', gender='')
    _append_bots_with_rp(parts, [MIRA, unknown], {}, is_rp=False)
    block = '\n'.join(parts)
    assert 'Mira is a level 40 female Human Mage' in block
    assert 'Zed is a level 40 Orc Warrior' in block
    assert gender.gender_prefix({}) == ''
    assert gender.gender_prefix({'gender': None}) == ''


def test_quest_conversation_header_carries_gender():
    prompt = _text(build_quest_complete_conversation_prompt(
        [GRUK, MIRA], {'Gruk': ['gruff'], 'Mira': ['curious']},
        'Mira', 'The Defias Brotherhood', 'roleplay',
    ))
    assert 'Mira is a level 40 female Human Mage' in prompt
    assert 'Gruk is a level 40 male Orc Warrior' in prompt


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} member gender checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
