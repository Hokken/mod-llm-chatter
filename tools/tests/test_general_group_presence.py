#!/usr/bin/env python3
"""Group awareness in General chatter (issue #94, part 2).

Covers the `bot_groups` payload reader, the shared prompt helper
(byte-identical prompts without a grouped speaker), the three General
player-reply prompts (first reply, follow-up, extended conversation),
transport arrival statements and conversations, other world events
staying unchanged, and the C++ payload wiring.

Run directly from the module root:
  python tools/tests/test_general_group_presence.py
"""

import json
import random
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_persona_coherence  # noqa: E402,F401  stubs + path

import chatter_general as general  # noqa: E402
import chatter_party_presence as presence  # noqa: E402
import chatter_world_events as world  # noqa: E402
from chatter_persona import persona_from_fields  # noqa: E402
from test_party_presence import DB, NOW, group  # noqa: E402

MODULE_ROOT = Path(__file__).resolve().parents[2]
HEADER = 'What each speaker knows about their own group'
OFF = {'LLMChatter.GroupAwareness.Enable': '0'}


def payload(**groups):
    """extra_data with bot_groups keyed by guid string."""
    return {'bot_groups': {str(k[1:]): v for k, v in groups.items()}}


def with_presence(prompt, extra, speakers, config=None, player='Rob'):
    with patch.object(presence.time, 'time', return_value=NOW):
        return presence.with_group_presence(
            prompt, DB(), config or {}, extra, speakers,
            'the public General channel', player_name=player)


# ------------------------------------------------------------
# Payload reader and helper
# ------------------------------------------------------------
def test_candidate_group_reader():
    grp = group()
    extra = payload(g11=grp, g12='bad')
    assert presence.candidate_group(extra, 11) is grp
    assert presence.candidate_group(extra, '11') is grp
    assert presence.candidate_group(extra, 12) == {}
    assert presence.candidate_group(extra, 13) == {}
    assert presence.candidate_group(extra, 'x') == {}
    assert presence.candidate_group({}, 11) == {}
    assert presence.candidate_group({'bot_groups': []}, 11) == {}
    assert presence.candidate_group(None, 11) == {}


def test_helper_identical_without_grouped_speaker():
    base = 'PROMPT\nRespond in JSON.'
    assert with_presence(base, {}, [(11, 'Thalia')]) is base
    assert with_presence(base, payload(g12=group()),
                         [(11, 'Thalia')]) is base
    assert with_presence(base, payload(g11={'group_id': 0}),
                         [(11, 'Thalia')]) is base
    assert with_presence(base, payload(g11=group()),
                         [(11, 'Thalia')], config=OFF) is base


def test_helper_appends_block_for_grouped_speaker():
    base = 'PROMPT'
    text = with_presence(base, payload(g11=group()), [(11, 'Thalia')])
    assert text.startswith(base + '\n' + HEADER)
    assert 'in a party with Rob (the player, here)' in text
    assert 'never offers to group with them' in text
    assert 'This is the public General channel: others can hear.' in text
    # A single speaker has no outsider line.
    assert 'knows none of this' not in text


def test_helper_multi_speaker_names_outsiders():
    text = with_presence('P', payload(g11=group()),
                         [(11, 'Thalia'), (12, 'Jorin'), (13, 'Mira')])
    assert '- Thalia (Thunder Bluff, Mulgore): in a party' in text
    assert 'Jorin, Mira know none of this.' in text


# ------------------------------------------------------------
# General player replies
# ------------------------------------------------------------
def _general_patches(inserted, info):
    persona = persona_from_fields(info['name'], 'normal')
    return {
        '_get_bot_info': lambda *a: dict(info),
        'prepare_channel_persona': lambda *a, **kw: persona,
        '_get_general_chat_history': lambda *a, **kw: [],
        'insert_chat_message': lambda *a, **kw: inserted.append(a[3]),
        '_extend_zone_delivery_window': lambda *a: None,
        'maybe_queue_group_general_reaction': lambda *a, **kw: None,
        '_store_general_chat': lambda *a: None,
    }


def _followup_prompt(extra):
    inserted = []
    info = {'name': 'Vex', 'race': 2, 'class': 1, 'level': 40,
            'gender': 0}
    random.seed(94)
    with ExitStack() as stack:
        for name, value in _general_patches(inserted, info).items():
            stack.enter_context(patch.object(general, name, value))
        stack.enter_context(patch.object(presence.time, 'time',
                                         return_value=NOW))
        stack.enter_context(patch.object(
            general, 'pick_general_reply_tier', return_value='short'))
        llm = stack.enter_context(patch.object(
            general, 'call_llm',
            return_value=json.dumps({'message': 'Heading out soon.'})))
        general._general_followup(
            DB(), None, {'LLMChatter.TalentInjectionChance': 0},
            1, 12, 'Barrens', [1, 2], 0, 1, 'One', 'Nice day.',
            'Rob', 'Anyone near the Crossroads?', 'normal', 1,
            extra_data=extra,
        )
    prompt = llm.call_args.args[1]
    return getattr(prompt, 'user_prompt', str(prompt))


def test_general_followup_without_group_is_unchanged():
    base = _followup_prompt(None)
    assert HEADER not in base
    assert _followup_prompt({'bot_groups': {}}) == base
    assert _followup_prompt(payload(g1=group())) == base


def test_general_followup_grouped_speaker_gets_block():
    base = _followup_prompt(None)
    text = _followup_prompt(payload(g2=group()))
    assert text.startswith(base)
    tail = text[len(base):]
    assert tail.startswith('\n' + HEADER)
    assert '- Vex (Thunder Bluff, Mulgore): in a party with Rob' in tail


def _extended_prompts(extra):
    inserted = []
    seen = []
    info = {'name': 'One', 'race': 2, 'class': 1, 'level': 40,
            'gender': 0}
    persona = persona_from_fields('One', 'normal')
    random.seed(94)

    def llm(client, prompt, *a, **kw):
        # PromptParts keeps the format rules in a system block; the
        # presence block belongs to the user part.
        seen.append(getattr(prompt, 'user_prompt', str(prompt)))
        return None

    with ExitStack() as stack:
        for name, value in _general_patches(inserted, info).items():
            stack.enter_context(patch.object(general, name, value))
        stack.enter_context(patch.object(general, '_extended_max_messages',
                                         3))
        stack.enter_context(patch.object(presence.time, 'time',
                                         return_value=NOW))
        stack.enter_context(patch.object(general.random, 'random',
                                         return_value=0))
        stack.enter_context(patch.object(general.random, 'randint',
                                         return_value=1))
        stack.enter_context(patch.object(general, 'call_llm',
                                         side_effect=llm))
        general._general_extended_conversation(
            DB(), None, {'LLMChatter.TalentInjectionChance': 0},
            1, 12, 'Barrens', [1, 2],
            1, 'One', persona, 'First line',
            2, 'Two', persona, 'Second line',
            'Rob', 'Anyone near the Crossroads?', 'normal', 1,
            extra_data=extra,
        )
    return seen


def test_general_extended_grouped_speaker_gets_block():
    base = _extended_prompts(None)
    assert base and HEADER not in base[0]
    grouped = _extended_prompts(payload(g1=group()))
    # The continuation prompt draws background feelings from its own
    # RNG, so compare the appended tail only: the block is last.
    head, _, block = grouped[0].partition('\n' + HEADER)
    assert head and block
    assert HEADER not in head
    assert block.splitlines()[1].startswith('- One (Thunder Bluff')
    assert block.rstrip().endswith('appear above.')


def _recent(guarded):
    from test_playtest_review_fixes import (
        _CHARACTERS, _CharactersDB, _HISTORY, _ZONE,
    )
    guids, names = [2001], ['Mira']
    general._add_recent_general_speakers(
        _CharactersDB(_CHARACTERS), _HISTORY, guids, names,
        _ZONE, 'Alliance', guarded=guarded,
    )
    return guids, names


def test_recent_speaker_needs_a_guard_on_new_payloads():
    # Older payload (no speaker_groups): unchanged behaviour.
    assert _recent(None) == ([2001, 3001], ['Mira', 'Zulrakka'])
    # New payload: C++ guards every bot that can speak in this
    # zone's General, so a guarded recent speaker is still added ...
    guards = {'2001': {'e': 'e1', 'g': 0},
              '3001': {'e': 'e1', 'g': 5, 'rev': 9, 'fp': 'x'}}
    assert _recent(guards) == ([2001, 3001], ['Mira', 'Zulrakka'])
    # ... and one C++ did not guard (not live here) is not.
    assert _recent({'2001': {'e': 'e1', 'g': 0}}) == ([2001], ['Mira'])
    assert general._speaker_guards({'speaker_groups': guards}) is guards
    assert general._speaker_guards({}) is None
    assert general._speaker_guards({'speaker_groups': []}) is None


def test_grouped_recent_speaker_outside_sample_gets_block():
    """A grouped bot outside the capped C++ sample, added from the
    General history, answers with its own group facts (its guard is
    in the same payload, so a later group change drops its line)."""
    extra = {'bot_guids': [2001], 'bot_names': ['Mira'],
             'bot_groups': {'3001': group()},
             'speaker_groups': {
                 '2001': {'e': 'e1', 'g': 0},
                 '3001': {'e': 'e1', 'g': 5, 'rev': 9, 'fp': 'x'}}}
    guids, names = _recent(general._speaker_guards(extra))
    assert 3001 in guids
    assert str(3001) in extra['speaker_groups']
    text = with_presence('P', extra, [(3001, 'Zulrakka')])
    assert '- Zulrakka (Thunder Bluff, Mulgore): in a party with Rob' \
        in text
    assert with_presence('P', extra, [(2001, 'Mira')]) == 'P'


def test_general_first_reply_wires_presence():
    """The first reply's prompt gets the helper with the event's
    extra_data and bot1 (source wiring; the handler itself needs a
    live database)."""
    source = (MODULE_ROOT / 'tools' / 'chatter_general.py').read_text(
        encoding='utf-8')
    assert ('prompt1 = with_group_presence(\n'
            '            prompt1, db, config, extra_data,\n'
            '            [(bot1_guid, bot1_name)]') in source
    assert source.count('extra_data=extra_data,') == 2


# ------------------------------------------------------------
# Transport arrivals
# ------------------------------------------------------------
TRANSPORT_EVENT = {'id': 7, 'event_type': 'transport_arrives',
                   'zone_id': 14, 'map_id': 1}
BOTS = [
    {'bot1_guid': 11, 'bot1_name': 'Thalia', 'bot1_class': 'Druid',
     'bot1_race': 'Tauren', 'bot1_level': 30, 'bot1_gender': 'female',
     'zone_id': 14},
    {'bot1_guid': 12, 'bot1_name': 'Jorin', 'bot1_class': 'Warrior',
     'bot1_race': 'Orc', 'bot1_level': 31, 'bot1_gender': 'male',
     'zone_id': 14},
]


def _world_patches():
    return {
        'prepare_channel_persona': lambda *a, **kw: 'persona',
        'build_event_context': lambda *a, **kw: 'The zeppelin docks.',
        'attach_speaker_gear': lambda *a, **kw: None,
        'get_recent_zone_messages': lambda *a, **kw: [],
        'build_event_statement_prompt':
            lambda *a, **kw: 'STATEMENT PROMPT',
        'build_event_conversation_prompt':
            lambda *a, **kw: 'CONVERSATION PROMPT',
        '_reserve_zone_delivery_window': lambda *a, **kw: 0.0,
    }


def _statement_prompt(extra, event=TRANSPORT_EVENT):
    captured = {}

    def reaction(db, client, config, **kw):
        captured['prompt'] = kw['prompt']
        return None

    with ExitStack() as stack:
        for name, value in _world_patches().items():
            stack.enter_context(patch.object(world, name, value))
        stack.enter_context(patch.object(world, 'run_single_reaction',
                                         side_effect=reaction))
        stack.enter_context(patch.object(world.random, 'choice',
                                         side_effect=lambda xs: xs[0]))
        stack.enter_context(patch.object(presence.time, 'time',
                                         return_value=NOW))
        world._deliver_statement(DB(), None, {}, dict(event), BOTS,
                                 extra, 14)
    return captured['prompt']


def _conversation_prompt(extra):
    captured = {}

    def llm(client, prompt, *a, **kw):
        captured['prompt'] = prompt
        return None

    with ExitStack() as stack:
        for name, value in _world_patches().items():
            stack.enter_context(patch.object(world, name, value))
        stack.enter_context(patch.object(world, 'call_llm',
                                         side_effect=llm))
        stack.enter_context(patch.object(presence.time, 'time',
                                         return_value=NOW))
        world._deliver_conversation(DB(), None, {}, dict(TRANSPORT_EVENT),
                                    BOTS, extra, 14)
    return captured['prompt']


def test_transport_statement_unchanged_without_group():
    assert _statement_prompt({'verified_bots': [11, 12]}) \
        == 'STATEMENT PROMPT'
    assert _statement_prompt({'verified_bots': [11, 12],
                              'bot_groups': {}}) == 'STATEMENT PROMPT'


def test_transport_statement_grouped_speaker_gets_block():
    text = _statement_prompt({'verified_bots': [11, 12],
                              'bot_groups': {'11': group()}})
    assert text.startswith('STATEMENT PROMPT\n' + HEADER)
    assert '- Thalia (' in text
    assert 'This is the public General channel' in text


def test_transport_conversation_names_outsiders():
    assert _conversation_prompt({'verified_bots': [11, 12]}) \
        == 'CONVERSATION PROMPT'
    text = _conversation_prompt({'verified_bots': [11, 12],
                                 'bot_groups': {'12': group()}})
    assert text.startswith('CONVERSATION PROMPT\n' + HEADER)
    assert '- Jorin (' in text
    assert 'Thalia knows none of this.' in text


def test_other_world_events_unchanged():
    weather = {'id': 8, 'event_type': 'weather_change', 'zone_id': 14,
               'map_id': 1}
    assert _statement_prompt({}, event=weather) == 'STATEMENT PROMPT'


# ------------------------------------------------------------
# C++ payload wiring
# ------------------------------------------------------------
def test_cpp_payload_wiring():
    src = MODULE_ROOT / 'src'
    player = (src / 'LLMChatterPlayer.cpp').read_text(encoding='utf-8')
    world_cpp = (src / 'LLMChatterWorld.cpp').read_text(encoding='utf-8')
    aware = (src / 'LLMChatterGroupAwareness.cpp').read_text(
        encoding='utf-8')
    for text in (player, world_cpp):
        assert '#include "LLMChatterGroupAwareness.h"' in text
    general_at = player.index('AppendCandidateGroups(extraData,\n'
                              '            CollectGeneralGuardBots(')
    assert player.index('"\\"bot_names\\":" + botNames') < general_at
    assert general_at < player.index('extraData = EscapeString(extraData)',
                                     general_at)
    transport_at = world_cpp.index(
        'AppendCandidateGroups(extraData, verifiedBots)')
    assert world_cpp.index('"\\"verified_bots\\":"') < transport_at
    assert transport_at < world_cpp.index('"transport_arrives"',
                                          transport_at)
    body = aware[aware.index('void AppendCandidateGroups'):]
    body = body[:body.index('\n}\n')]
    assert 'BuildBotGroupsField(candidates)' in body
    assert 'BuildSpeakerGroupsField(candidates)' in body
    groups = aware[aware.index('std::string BuildBotGroupsField'):]
    groups = groups[:groups.index('\n}\n')]
    assert '!bot->GetGroup()' in groups


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        presence.reset_state()
        test()
    print(f"{len(tests)} General group awareness checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
