#!/usr/bin/env python3
"""Rumors in proximity scenes: an addressed rumor in an NPC-only
conversation, scenes queued only for a fresh rumor, and the worldserver
side of the fresh-rumor check.
Run directly from the module root:
  python tools/tests/test_rumor_scenes.py
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_persona_coherence  # noqa: E402,F401  stubs + path
import chatter_player_context  # noqa: E402
import chatter_proximity as prox  # noqa: E402
from chatter_reactive_rumors import RumorTopic  # noqa: E402
from test_proximity_genders import DB, NPC, _text  # noqa: E402

RP = {'LLMChatter.ChatterMode': 'roleplay'}
SRC = Path(__file__).resolve().parents[2] / 'src'
NEVER = 'never address, mention or tell stories about any passing traveller'


def _rumor(addressed):
    topic = RumorTopic(
        'Calwen killed Hogger.' if addressed
        else 'Someone killed Hogger.'
    )
    topic.kind = 'quest'
    topic.key = 'q176'
    topic.addressed = addressed
    topic.notes = ''
    return topic


def _npc_scene(rumor):
    # The player description is cached by guid; earlier tests may have
    # cached another answer for this one.
    chatter_player_context.clear_cache()
    extra = {
        'player_name': 'Calwen', 'player_guid': 7,
        'player_addressed': rumor.addressed,
        'nearby_names': [], 'nearby_npc_names': [],
    }
    npcs = [dict(NPC), dict(NPC, name='Guard Ellis')]
    return _text(prox._conversation_prompt(
        DB(), extra, npcs, config=RP, rumor=rumor,
    ))


def test_addressed_rumor_lets_npcs_speak_to_the_player():
    text = _npc_scene(_rumor(True))
    assert 'You recognise Calwen' in text
    assert NEVER not in text
    # The player's own lines are given, so the speakers know who it is.
    assert 'Calwen is a female Human' in text


def test_recounted_rumor_keeps_npcs_among_themselves():
    text = _npc_scene(_rumor(False))
    assert NEVER in text
    assert 'Calwen is a female Human' not in text


def _say_event(forced):
    extra = {
        'player_guid': 7, 'player_name': 'Calwen', 'zone_id': 12,
        'participants': [dict(NPC)],
    }
    if forced:
        extra['rumor_forced'] = True
    return {'id': 5, 'extra_data': extra}


def test_refused_forced_scene_is_skipped_without_a_call():
    marks = []
    with patch.object(prox, 'parse_extra_data',
                      side_effect=lambda raw, *a: raw), \
            patch.object(prox, 'pick_rumor', return_value=None), \
            patch.object(prox, '_mark_event',
                         side_effect=lambda db, i, s: marks.append(s)), \
            patch.object(prox, '_generate_single_line') as generate:
        assert prox.handle_proximity_say(DB(), None, RP, _say_event(True)) \
            is False
    generate.assert_not_called()
    assert marks == ['skipped']


def test_unforced_scene_still_chats_without_a_rumor():
    marks = []
    with patch.object(prox, 'parse_extra_data',
                      side_effect=lambda raw, *a: raw), \
            patch.object(prox, 'pick_rumor', return_value=None), \
            patch.object(prox, '_mark_event',
                         side_effect=lambda db, i, s: marks.append(s)), \
            patch.object(prox, '_generate_single_line',
                         return_value=True) as generate:
        assert prox.handle_proximity_say(DB(), None, RP, _say_event(False))
    generate.assert_called_once()
    assert marks == ['completed']


def test_worldserver_never_waits_on_the_database_for_rumors():
    src = (SRC / 'LLMChatterReactivity.cpp').read_text()
    body = src[src.index('bool HasFreshRumorHere'):]
    body = body[:body.index('\n}\n')]
    assert 'CharacterDatabase' not in body
    assert 'CharacterDatabase.AsyncQuery(' in src


def test_no_rumor_bypass_inside_instances():
    src = (SRC / 'LLMChatterProximity.cpp').read_text()
    assert '!scanMap->Instanceable()' in src
    assert '"\\"rumor_forced\\":true"' in src


if __name__ == '__main__':
    for name, func in sorted(globals().items()):
        if name.startswith('test_') and callable(func):
            func()
            print(f'ok {name}')
