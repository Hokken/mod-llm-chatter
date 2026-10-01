#!/usr/bin/env python3
"""Conversation thread checks for party idle chatter.

Covers thread state transitions, delivery-confirmed adoption
(pending, delivered, dropped, partial), stale-completion rejection,
the soft nudge weighting, lingering feelings, interruptions (player
and events), robustness of the optional thread report and of the
conversation parser, caller integration (idle paths, pipeline,
active-group reconciliation), retention limits, config validation,
the disable switch and concurrent access.

Run directly from the module root:
  python tools/tests/test_conversation_threads.py
"""

import importlib
import itertools
import json
import random
import sys
import threading
import types
from collections import Counter
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

import chatter_group  # noqa: E402
import chatter_handler_pipeline  # noqa: E402
import chatter_threads as th  # noqa: E402
from chatter_group import (  # noqa: E402
    build_idle_chatter_prompt,
    build_idle_conversation_prompt,
)
from chatter_group_prompts import (  # noqa: E402
    build_player_response_prompt,
)
from chatter_prompts import configure_prompt_flavor  # noqa: E402
from chatter_shared import (  # noqa: E402
    build_anti_repetition_context,
    parse_conversation_response,
)
from chatter_text import parse_single_response  # noqa: E402

GID = 42
NAMES = ['Gruk', 'Mira']
GRUK = {
    'guid': 101, 'name': 'Gruk', 'race': 'Orc',
    'class': 'Warrior', 'level': 40, 'gender': 'male',
    'tone': 'gruff and terse',
}
MIRA = {
    'guid': 102, 'name': 'Mira', 'race': 'Human',
    'class': 'Mage', 'level': 40, 'gender': 'female',
    'tone': 'bookish and warm',
}
TRAITS = {
    'Gruk': ['brooding', 'loyal', 'sardonic'],
    'Mira': ['wide-eyed', 'bookish', 'gentle'],
}


# ------------------------------------------------------------
# Fake database: chat rows with delivery state
# ------------------------------------------------------------
class _Cursor:
    def __init__(self, db):
        self.db = db
        self.rows = []
        self.lastrowid = None

    def execute(self, query, params=None):
        self.rows = []
        if 'FROM llm_chatter_messages' in query:
            self.db.status_queries += 1
            if self.db.fail_status:
                raise RuntimeError('db down')
            self.rows = [
                {'id': mid, 'delivered': st[0], 'drop_reason': st[1],
                 'delivered_at': st[2],
                 'age_s': (
                     self.db.ages.get(mid, 0)
                     if st[2] is not None else None
                 )}
                for mid, st in self.db.messages.items()
                if mid in set(params)
            ]
        elif 'FROM characters' in query:
            self.rows = [{
                'class': 1, 'race': 2, 'level': 40, 'gender': 0,
            }]
        elif 'DISTINCT group_id' in query:
            self.rows = [{'group_id': g} for g in self.db.groups]

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _DB:
    def __init__(self):
        # id -> (delivered, drop_reason, delivered_at), following the
        # real C++ transitions: claim sets delivered=1 only; a send
        # adds delivered_at; a drop adds delivered_at + drop_reason.
        self.messages = {}
        self.ages = {}
        self.ids = itertools.count(1)
        self.status_queries = 0
        self.fail_status = False
        self.groups = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def commit(self):
        pass

    def queue(self):
        mid = next(self.ids)
        self.messages[mid] = (0, None, None)
        return mid

    def claim(self, *ids):
        for mid in ids:
            self.messages[mid] = (1, None, None)

    def deliver(self, *ids, age=0):
        for mid in ids:
            self.messages[mid] = (1, None, 'sent')
            self.ages[mid] = age

    def drop(self, *ids):
        for mid in ids:
            self.messages[mid] = (1, 'expired_before_delivery', 'x')


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


def _reset(**overrides):
    th.reset_settings()
    config = {'LLMChatter.Threads.SurpriseChance': 0}
    config.update(overrides)
    th.configure_threads(config)
    th.clear_all()
    configure_prompt_flavor({
        'LLMChatter.Persona.TwistChance': 0,
        'LLMChatter.Persona.SpiceChance': 0,
    })


def _report(topic='treaties and trust', energy='high',
            changed=True, feelings=None, point=''):
    thread = {
        'topic': topic,
        'energy': energy,
        'subject_changed': changed,
        'open_point': point,
        'feelings': feelings or {},
    }
    thread = {k: v for k, v in thread.items() if v is not None}
    return json.dumps({
        'message': 'placeholder', 'emote': None, 'action': None,
        'thread': thread,
    })


def _sync(db):
    """Let the thread confirm deliveries (as the next plan does)."""
    with th._lock:
        state = th._get(GID, create=False)
        if state is not None:
            th._reconcile(db, state, th._now())


def _exchange(db, report, names=NAMES, outcome='delivered', lines=2,
              **plan_kwargs):
    """One idle exchange through plan -> queue -> record -> deliver."""
    turn = th.plan_idle_turn(GID, names, db=db, **plan_kwargs)
    ids = [db.queue() for _ in range(lines)]
    th.record_idle_exchange(turn, report, names, ids)
    if outcome == 'delivered':
        db.deliver(*ids)
    elif outcome == 'dropped':
        db.drop(*ids)
    elif outcome == 'partial':
        db.deliver(ids[0])
        db.drop(*ids[1:])
    _sync(db)
    return turn, ids


# ------------------------------------------------------------
# Delivery-confirmed adoption
# ------------------------------------------------------------
def test_report_waits_for_delivery_then_opens_thread():
    _reset()
    db = _DB()
    turn, ids = _exchange(db, _report(point='is a truce kept'),
                          outcome='pending')
    assert th.snapshot(GID).current is None
    assert th.render_for_player_reply(GID, db) == ''
    db.deliver(*ids)
    _sync(db)
    state = th.snapshot(GID)
    assert state.current.topic == 'treaties and trust'
    assert state.current.open_point == 'is a truce kept'
    assert state.current.exchanges == 1
    assert not state.pending


def test_dropped_exchange_leaves_no_trace():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Dalaran'))
    th.note_player_message(GID, 'Calwen', 'hello')
    before = th.snapshot(GID)
    _exchange(db, _report(topic='rain', changed=True,
                          feelings={'Gruk': 'irritated'}),
              outcome='dropped')
    after = th.snapshot(GID)
    assert after.current.topic == 'Dalaran'
    assert after.current.exchanges == before.current.exchanges
    assert 'Gruk' not in after.feelings
    # The player's line was never answered, so it stays visible.
    assert any(i['kind'] == 'player' for i in after.interruptions)


def test_partial_delivery_counts_without_adopting_report():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Dalaran', energy='high'))
    before = th.snapshot(GID).current
    _exchange(db, _report(topic='rain', changed=True,
                          feelings={'Gruk': 'irritated'}),
              outcome='partial', lines=3)
    after = th.snapshot(GID)
    assert after.current.topic == 'Dalaran'
    assert after.current.exchanges == before.exchanges + 1
    assert after.current.energy < before.energy
    assert 'Gruk' not in after.feelings


def test_empty_accepted_set_records_nothing():
    _reset()
    db = _DB()
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    th.record_idle_exchange(turn, _report(), NAMES, [])
    th.record_idle_exchange(turn, _report(), NAMES, [None])
    assert not th.snapshot(GID).pending


def test_pending_times_out_and_lookup_failure_waits():
    _reset(**{'LLMChatter.Threads.PendingTimeoutSeconds': 60})
    db = _DB()
    turn, ids = _exchange(db, _report(), outcome='pending')
    db.fail_status = True
    _sync(db)
    assert len(th.snapshot(GID).pending) == 1
    db.fail_status = False
    later = th._now() + 120
    with patch.object(th, '_now', return_value=later):
        _sync(db)
    state = th.snapshot(GID)
    assert not state.pending and state.current is None


def test_event_quote_only_after_delivery():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Dalaran'))
    mid = db.queue()
    th.note_event(GID, 'bot_group_kill', 'Gruk', 'One less boar.',
                  message_id=mid)
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Event: kill' in turn.prompt_block
    assert 'One less boar' not in turn.prompt_block
    db.deliver(mid)
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Gruk reacted: "One less boar."' in turn.prompt_block
    mid2 = db.queue()
    th.note_event(GID, 'bot_group_loot', 'Mira', 'Shiny.',
                  message_id=mid2)
    db.drop(mid2)
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Event: loot' in turn.prompt_block
    assert 'Shiny' not in turn.prompt_block


# ------------------------------------------------------------
# Stale completions
# ------------------------------------------------------------
def test_old_report_cannot_overwrite_a_later_wipe():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Dalaran'))
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    ids = [db.queue(), db.queue()]
    th.note_event(GID, 'bot_group_wipe', 'Mira', 'Ugh.')
    th.record_idle_exchange(
        turn, _report(topic='Dalaran libraries', changed=False),
        NAMES, ids,
    )
    db.deliver(*ids)
    _sync(db)
    state = th.snapshot(GID)
    assert state.current.topic == 'the wipe'
    assert [t.topic for t in state.history] == ['Dalaran']


def test_completion_after_clear_does_not_resurrect_session():
    for clear in (lambda: th.clear_group(GID), th.clear_all):
        _reset()
        db = _DB()
        turn = th.plan_idle_turn(GID, NAMES, db=db)
        clear()
        th.record_idle_exchange(turn, _report(), NAMES, [db.queue()])
        assert th.snapshot(GID) is None
        # A new session with the same group id ignores the old turn.
        fresh = th.plan_idle_turn(GID, NAMES, db=db)
        assert fresh.session != turn.session
        ids = [db.queue()]
        th.record_idle_exchange(turn, _report(topic='old'), NAMES,
                                ids)
        db.deliver(*ids)
        _sync(db)
        assert th.snapshot(GID).current is None


# ------------------------------------------------------------
# Partial / malformed reports
# ------------------------------------------------------------
def test_partial_reports_never_delete_the_subject():
    cases = [
        {'energy': 'high', 'subject_changed': True},
        {'topic': '', 'energy': 'low', 'subject_changed': True},
        {'topic': 5, 'feelings': {'Gruk': 'tired'},
         'subject_changed': True},
        {'feelings': {'Mira': 'amused'}},
    ]
    for case in cases:
        _reset()
        db = _DB()
        _exchange(db, _report(topic='Dalaran', energy='high'))
        before = th.snapshot(GID).current
        response = json.dumps({'message': 'x', 'thread': case})
        _exchange(db, response)
        after = th.snapshot(GID)
        assert after.current is not None, case
        assert after.current.topic == 'Dalaran', case
        assert after.current.exchanges == before.exchanges + 1
        for name, text in (case.get('feelings') or {}).items():
            assert after.feelings[name][0] == text


def test_feelings_only_report_on_a_new_move_keeps_state():
    _reset()
    db = _DB()
    _exchange(db, json.dumps({
        'message': 'x', 'thread': {'feelings': {'Gruk': 'restless'}},
    }))
    state = th.snapshot(GID)
    assert state.current is None
    assert state.feelings['Gruk'][0] == 'restless'


def test_missing_or_malformed_report_only_cools_the_thread():
    _reset()
    db = _DB()
    _exchange(db, _report(energy='high'))
    for bad in ('', 'not json at all', '{"message": "hi"}',
                '{"message": "hi", "thread": "oops"}',
                '[{"speaker": "Gruk", "message": "x"}, {"thread": '):
        before = th.snapshot(GID).current
        _exchange(db, bad)
        after = th.snapshot(GID).current
        assert after.topic == before.topic
        assert after.energy < before.energy
        assert after.exchanges == before.exchanges + 1


def test_string_false_is_not_a_boolean():
    parsed = th.parse_thread_report(
        '{"thread": {"topic": "x", "energy": "low", '
        '"subject_changed": "false"}}', NAMES,
    )
    assert parsed['subject_changed'] is None
    parsed = th.parse_thread_report(
        '{"thread": {"topic": "x", "subject_changed": false}}',
        NAMES,
    )
    assert parsed['subject_changed'] is False


# ------------------------------------------------------------
# Conversation parser robustness
# ------------------------------------------------------------
def test_broken_thread_tail_keeps_complete_dialogue():
    truncated = (
        '[{"speaker":"Gruk","message":"hello"},'
        '{"speaker":"Mira","message":"hi"},{"thread":{"topic":"oo'
    )
    messages = parse_conversation_response(truncated, NAMES)
    assert [m['message'] for m in messages] == ['hello', 'hi']
    assert th.parse_thread_report(truncated, NAMES) is None
    with_null = '[{"speaker":"Gruk","message":"hello"}, null]'
    assert [m['name'] for m in
            parse_conversation_response(with_null, NAMES)] == ['Gruk']
    # Broken dialogue itself is still rejected, as before.
    assert parse_conversation_response(
        '[{"speaker":"Gruk","message":"hi"},{"speaker":"Mira","me',
        NAMES,
    ) == []
    full = json.dumps([
        {'speaker': 'Gruk', 'message': 'a'},
        {'thread': {'topic': 'secret label', 'energy': 'high'}},
    ])
    parsed = parse_conversation_response(full, NAMES)
    assert all('secret label' not in m['message'] for m in parsed)
    assert parse_single_response(_report())['message'] == 'placeholder'


# ------------------------------------------------------------
# Caller integration
# ------------------------------------------------------------
_IDLE_CONFIG = {
    'LLMChatter.Memory.Enable': 0,
    'LLMChatter.Backstory.Enable': 0,
    'LLMChatter.ChatterMode': 'roleplay',
}


def _rows():
    return [
        {'bot_guid': 101, 'bot_name': 'Gruk', 'trait1': 'brooding',
         'trait2': 'loyal', 'trait3': 'sardonic', 'tone': 'gruff',
         'role': None, 'health': 1},
        {'bot_guid': 102, 'bot_name': 'Mira', 'trait1': 'wide-eyed',
         'trait2': 'bookish', 'trait3': 'gentle', 'tone': 'warm',
         'role': None, 'health': 1},
    ]


def _idle_patches(db, response, inserted):
    def fake_insert(*args, **kwargs):
        mid = db.queue()
        inserted.append(mid)
        return mid

    return [
        patch.object(chatter_group, 'call_llm',
                     return_value=response),
        patch.object(chatter_group, 'insert_chat_message',
                     side_effect=fake_insert),
        patch.object(chatter_group, '_store_chat'),
        patch.object(chatter_group, 'build_gear_context',
                     return_value=''),
        patch.object(chatter_group, 'attach_speaker_gear'),
        patch.object(chatter_group, 'get_recent_bot_messages',
                     return_value=[]),
        patch.object(chatter_group, '_maybe_talent_context',
                     return_value=None),
        patch.object(chatter_group, 'calculate_dynamic_delay',
                     return_value=1),
    ]


def _run_patched(patches, fn):
    for p in patches:
        p.start()
    try:
        return fn()
    finally:
        for p in patches:
            p.stop()


def test_idle_conversation_path_records_only_delivered_lines():
    _reset()
    db = _DB()
    response = json.dumps([
        {'speaker': 'Gruk', 'message': 'Treaties are paper.',
         'emote': None, 'action': None},
        {'speaker': 'Mira', 'message': 'Paper holds.',
         'emote': None, 'action': None},
        {'thread': {'topic': 'treaties', 'energy': 'high',
                    'subject_changed': True,
                    'feelings': {'Gruk': 'prickly'}}},
    ])
    inserted = []
    random.seed(3)
    ok = _run_patched(
        _idle_patches(db, response, inserted),
        lambda: chatter_group._idle_conversation(
            db, None, _IDLE_CONFIG, GID, _rows(), 'roleplay',
            '', NAMES, th._now(),
        ),
    )
    assert ok and len(inserted) == 2
    state = th.snapshot(GID)
    assert state.current is None and len(state.pending) == 1
    db.deliver(*inserted)
    _sync(db)
    state = th.snapshot(GID)
    assert state.current.topic == 'treaties'
    assert state.feelings['Gruk'][0] == 'prickly'


def test_idle_conversation_with_broken_tail_still_delivers():
    _reset()
    db = _DB()
    response = (
        '[{"speaker":"Gruk","message":"Treaties are paper."},'
        '{"speaker":"Mira","message":"Paper holds."},'
        '{"thread":{"topic":"trea'
    )
    inserted = []
    ok = _run_patched(
        _idle_patches(db, response, inserted),
        lambda: chatter_group._idle_conversation(
            db, None, _IDLE_CONFIG, GID, _rows(), 'roleplay',
            '', NAMES, th._now(),
        ),
    )
    assert ok and len(inserted) == 2


def test_idle_single_path_records_against_its_row():
    _reset()
    db = _DB()
    inserted = []
    ok = _run_patched(
        _idle_patches(db, _report(topic='rain'), inserted),
        lambda: chatter_group._idle_single_statement(
            db, None, _IDLE_CONFIG, GID, _rows()[:1], 'roleplay',
            '', NAMES, th._now(),
        ),
    )
    assert ok and len(inserted) == 1
    assert th.snapshot(GID).pending[0].message_ids == tuple(inserted)
    db.deliver(*inserted)
    _sync(db)
    assert th.snapshot(GID).current.topic == 'rain'


def test_pipeline_notes_event_with_its_message_id():
    _reset()
    db = _DB()
    patches = [
        patch.object(chatter_handler_pipeline, 'get_bot_traits',
                     return_value={'traits': ['calm'], 'tone': 'x'}),
        patch.object(chatter_handler_pipeline, 'build_gear_context',
                     return_value=''),
        patch.object(chatter_handler_pipeline, '_get_recent_chat',
                     return_value=[]),
        patch.object(chatter_handler_pipeline, '_maybe_talent_context',
                     return_value=None),
        patch.object(chatter_handler_pipeline, 'run_single_reaction',
                     return_value={'ok': True, 'message': 'Ow.',
                                   'message_id': 77}),
        patch.object(chatter_handler_pipeline, '_store_chat'),
        patch.object(chatter_handler_pipeline, '_mark_event'),
        patch.object(chatter_handler_pipeline, 'update_bot_mood'),
    ]
    _run_patched(patches, lambda: chatter_handler_pipeline
                 .run_group_handler(
                     db, None, {}, {'id': 1},
                     event_type_label='bot_group_death',
                     extract_fields=lambda ed: {},
                     build_prompt=lambda ctx: 'prompt',
                     pre_parsed_extra={
                         'bot_guid': 101, 'bot_name': 'Gruk',
                         'group_id': GID, 'bot_class': 1,
                         'bot_race': 2,
                     },
                 ))
    state = th.snapshot(GID)
    event = state.interruptions[-1]
    assert event['message_id'] == 77 and event['quote'] == 'pending'
    assert state.current.topic == 'the death'


def test_idle_tick_forgets_ended_groups():
    _reset()
    db = _DB()
    th.note_player_message(GID, 'Calwen', 'hi')
    th.note_player_message(7, 'Other', 'hi')
    db.groups = [7]
    with patch.object(chatter_group.random, 'choice',
                      side_effect=lambda seq: seq[0]), \
            patch.object(chatter_group.random, 'randint',
                         return_value=100):
        chatter_group.check_idle_group_chatter(db, None, {
            'LLMChatter.GroupChatter.IdleChance': 0,
        })
    assert th.snapshot(GID) is None
    assert th.snapshot(7) is not None
    db.groups = []
    chatter_group.check_idle_group_chatter(db, None, {})
    assert th.snapshot(7) is None


# ------------------------------------------------------------
# Lingering feelings, interruptions, player replies
# ------------------------------------------------------------
def test_feelings_linger_across_subject_changes_then_fade():
    # A feeling stays visible for the next FeelingTurns exchanges.
    _reset(**{'LLMChatter.Threads.FeelingTurns': 2})
    db = _DB()
    _exchange(db, _report(feelings={'Gruk': 'stung by Mira'}))
    _exchange(db, _report(topic='food', changed=True))
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Gruk: stung by Mira' in turn.prompt_block
    ids = [db.queue()]
    th.record_idle_exchange(turn, _report(topic='rain'), NAMES, ids)
    db.deliver(*ids)
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'stung by Mira' not in turn.prompt_block


def test_minor_event_interrupts_and_thread_can_resume():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Dalaran', energy='high'))
    th.note_event(GID, 'bot_group_kill', 'Gruk', 'x')
    assert th.snapshot(GID).current.topic == 'Dalaran'
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Event: kill' in turn.prompt_block
    assert 'Current subject: Dalaran' in turn.prompt_block
    ids = [db.queue()]
    th.record_idle_exchange(turn, '', NAMES, ids)
    db.deliver(*ids)
    later = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Event: kill' not in later.prompt_block


def test_player_message_blends_in():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='treaties', energy='high',
                          feelings={'Gruk': 'prickly'}))
    th.note_player_message(GID, 'Calwen', 'never trust the Alliance')
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Calwen (the player) said' in turn.prompt_block
    note = th.render_for_player_reply(GID, db)
    assert 'treaties' in note and 'weave it in' in note
    assert 'prickly' in note
    prompt = _text(build_player_response_prompt(
        GRUK, TRAITS['Gruk'], 'Calwen', 'never trust them',
        'roleplay', thread_context=note,
    ))
    assert 'weave it in' in prompt
    brief = _text(build_player_response_prompt(
        GRUK, TRAITS['Gruk'], 'Calwen', 'lol', 'roleplay',
        thread_context=note, brief_casual=True,
    ))
    assert 'weave it in' not in brief


def test_cold_thread_is_not_offered_to_player_replies():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='treaties', energy='spent'))
    assert th.render_for_player_reply(GID, db) == ''


# ------------------------------------------------------------
# Nudges: weighted, soft, never scripted
# ------------------------------------------------------------
def _moves(energy_label, samples=600, history=True):
    counts = Counter()
    for seed in range(samples):
        _reset()
        db = _DB()
        if history:
            _exchange(db, _report(topic='older', changed=True))
        _exchange(db, _report(topic='now', energy=energy_label,
                              changed=True))
        random.seed(seed)
        counts[th.plan_idle_turn(GID, NAMES, db=db).kind] += 1
    return counts


def test_energy_steers_but_never_dictates():
    high = _moves('high')
    low = _moves('spent')
    assert high['continue'] > high['new'] * 3
    assert low['new'] > low['continue']
    for counts in (high, low):
        assert set(counts) == {'continue', 'drift', 'callback', 'new'}


def test_callback_needs_history():
    assert _moves('spent', history=False)['callback'] == 0


def test_silence_cools_a_thread():
    _reset(**{'LLMChatter.Threads.CoolMinutes': 10})
    db = _DB()
    _exchange(db, _report(energy='high'))
    later = th._now() + 60 * 60
    with patch.object(th, '_now', return_value=later):
        state = th.snapshot(GID)
        assert th._effective_energy(state.current, later) < 0.1
        assert th.render_for_player_reply(GID, db) == ''


def test_new_subjects_favour_persona_and_pool_stays_out_of_instances():
    sources = Counter()
    for seed in range(600):
        _reset()
        random.seed(seed)
        sources[th.plan_idle_turn(
            GID, NAMES, topic_pool=['rain']).source] += 1
    assert sources['persona'] > sources['surroundings'] > 0
    assert sources['pool'] > 0
    for seed in range(200):
        _reset()
        random.seed(seed)
        turn = th.plan_idle_turn(
            GID, NAMES, in_instance=True, topic_pool=['rain'],
        )
        assert turn.source != 'pool' and turn.pool_topic is None


def test_prompt_block_is_a_nudge_with_no_scripted_lines():
    _reset(**{'LLMChatter.Threads.SurpriseChance': 100})
    db = _DB()
    _exchange(db, _report())
    block = th.plan_idle_turn(GID, NAMES, db=db).prompt_block
    assert 'a nudge, not a script' in block
    assert 'Room for surprise' in block
    assert 'believable for who they are' in block
    assert 'Disagreement is welcome but stays friendly' in block
    assert '"' not in block
    _reset(**{'LLMChatter.Threads.SurpriseChance': 0})
    assert 'Room for surprise' not in th.plan_idle_turn(
        GID, NAMES).prompt_block


def _forced_turn(db, move):
    with patch.object(th, '_pick_move', return_value=move):
        return th.plan_idle_turn(GID, NAMES, db=db)


def test_callbacks_and_continuations_relax_the_theme_ban():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='older', changed=True))
    _exchange(db, _report(topic='treaties', energy='high',
                          changed=True))
    recent = ['Treaties are paper.']
    for move in ('continue', 'drift', 'callback'):
        turn = _forced_turn(db, move)
        assert turn.builds_on_subject, move
        single = _text(build_idle_chatter_prompt(
            GRUK, TRAITS['Gruk'], 'roleplay',
            stored_tone=GRUK['tone'], thread_turn=turn,
            recent_messages=recent,
        ))
        conv = _text(build_idle_conversation_prompt(
            [GRUK, MIRA], TRAITS, 'roleplay', None,
            thread_turn=turn, recent_messages=recent,
        ))
        for prompt in (single, conv):
            assert 'current or an earlier' in prompt, move
            assert 'themes already said' not in prompt, move
            assert 'completely different' not in prompt, move
            assert 'MUST NOT repeat' in prompt, move
    turn = _forced_turn(db, 'new')
    assert not turn.builds_on_subject
    single = _text(build_idle_chatter_prompt(
        GRUK, TRAITS['Gruk'], 'roleplay', stored_tone=GRUK['tone'],
        thread_turn=turn, recent_messages=recent,
    ))
    assert 'themes already said' in single
    assert 'completely different' in single


def test_idle_builders_carry_thread_and_report_schema():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='treaties', energy='high'))
    turn = _forced_turn(db, 'continue')
    conv = build_idle_conversation_prompt(
        [GRUK, MIRA], TRAITS, 'roleplay', None, thread_turn=turn,
    )
    assert '<conversation_thread>' in _text(conv)
    assert '"thread": {"topic"' in str(conv)
    assert 'then one final object' in str(conv)
    single = build_idle_chatter_prompt(
        GRUK, TRAITS['Gruk'], 'roleplay',
        stored_tone=GRUK['tone'], thread_turn=turn,
    )
    assert '"thread": {"topic"' in str(single)
    plain = build_idle_chatter_prompt(
        GRUK, TRAITS['Gruk'], 'roleplay', stored_tone=GRUK['tone'],
    )
    assert '<conversation_thread>' not in str(plain)
    assert '"thread"' not in str(plain)
    strict = build_anti_repetition_context(['Treaties are paper.'])
    assert 'completely different' in strict


# ------------------------------------------------------------
# Retention, config, switch, concurrency
# ------------------------------------------------------------
def test_small_store_expires_on_lookup():
    _reset(**{'LLMChatter.Threads.IdleTTLMinutes': 30})
    db = _DB()
    _exchange(db, _report())
    later = th._now() + 31 * 60
    with patch.object(th, '_now', return_value=later):
        assert th.render_for_player_reply(GID, db) == ''
        turn = th.plan_idle_turn(GID, NAMES, db=db)
        assert 'Current subject' not in turn.prompt_block
        assert th.snapshot(GID).current is None


def test_store_is_capped_by_least_recent_use():
    _reset(**{'LLMChatter.Threads.MaxGroups': 3})
    for gid in range(1, 6):
        th.note_player_message(gid, 'P', 'hi')
    th.note_player_message(3, 'P', 'again')
    th.note_player_message(9, 'P', 'hi')
    with th._lock:
        assert list(th._store) == [
            ('party', 5), ('party', 3), ('party', 9),
        ]


def test_config_bounds_and_invalid_values():
    _reset(**{
        'LLMChatter.Threads.HighEnergyMoveWeights': '0,0,0,0',
        'LLMChatter.Threads.MidEnergyMoveWeights': '1,2,3',
        'LLMChatter.Threads.LowEnergyMoveWeights': '0,0,0,100',
        'LLMChatter.Threads.HighEnergyThreshold': 20,
        'LLMChatter.Threads.LowEnergyThreshold': 40,
        'LLMChatter.Threads.MaxGroups': 0,
        'LLMChatter.Threads.ReportTokens': 'lots',
        'LLMChatter.Threads.MaxInterruptions': 99,
    })
    s = th._settings
    assert s['weights']['high'] == th._DEFAULT_WEIGHTS['high']
    assert s['weights']['mid'] == th._DEFAULT_WEIGHTS['mid']
    assert s['weights']['low'] == (0, 0, 0, 100)
    assert (s['high_threshold'], s['low_threshold']) == (0.6, 0.3)
    assert s['max_groups'] == 1
    assert th.report_tokens() == 90
    assert s['max_interruptions'] == 10
    db = _DB()
    _exchange(db, _report(topic='x', energy='spent'))
    for seed in range(50):
        random.seed(seed)
        assert th.plan_idle_turn(GID, NAMES, db=db).kind == 'new'


def test_disabled_threads_change_nothing():
    _reset(**{'LLMChatter.Threads.Enable': 0})
    assert th.plan_idle_turn(GID, NAMES) is None
    th.note_event(GID, 'bot_group_wipe', 'Gruk', 'x')
    th.note_player_message(GID, 'Calwen', 'hi')
    th.record_idle_exchange(None, _report(), NAMES, [1])
    assert th.snapshot(GID) is None
    assert th.render_for_player_reply(GID) == ''


def test_concurrent_access_is_safe():
    _reset()
    db = _DB()
    errors = []
    db_lock = threading.Lock()

    def worker(n):
        try:
            for i in range(150):
                if i % 3 == 0:
                    th.note_event(GID, 'bot_group_kill', 'Gruk', 'x')
                elif i % 3 == 1:
                    th.note_player_message(GID, 'Calwen', f'{n}-{i}')
                else:
                    with db_lock:
                        turn = th.plan_idle_turn(GID, NAMES, db=db)
                        mid = db.queue()
                        db.deliver(mid)
                    th.record_idle_exchange(
                        turn, _report(topic=f't{n}-{i}',
                                      changed=bool(i % 2)),
                        NAMES, [mid],
                    )
                with db_lock:
                    th.render_for_player_reply(GID, db)
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    workers = [
        threading.Thread(target=worker, args=(n,)) for n in range(6)
    ]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    assert not errors, errors
    state = th.snapshot(GID)
    assert len(state.interruptions) <= th._settings['max_interruptions']
    assert len(state.history) <= th._settings['history_size']


# ------------------------------------------------------------
# Claim vs send, accepted set, outage expiry, event sessions
# ------------------------------------------------------------
def test_claimed_rows_are_not_spoken_yet():
    _reset()
    db = _DB()
    turn, ids = _exchange(db, _report(topic='Dalaran'),
                          outcome='pending')
    db.claim(*ids)
    _sync(db)
    assert th.snapshot(GID).current is None
    assert len(th.snapshot(GID).pending) == 1
    db.deliver(*ids)
    _sync(db)
    assert th.snapshot(GID).current.topic == 'Dalaran'


def test_claim_then_drop_leaves_no_trace():
    _reset()
    db = _DB()
    turn, ids = _exchange(db, _report(topic='Dalaran'),
                          outcome='pending')
    db.claim(*ids)
    db.drop(*ids)
    _sync(db)
    state = th.snapshot(GID)
    assert state.current is None and not state.pending


def test_event_quote_waits_for_the_send_not_the_claim():
    _reset()
    db = _DB()
    mid = db.queue()
    th.note_event(GID, 'bot_group_kill', 'Gruk', 'One less boar.',
                  message_id=mid)
    db.claim(mid)
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'One less boar' not in turn.prompt_block
    db.deliver(mid)
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Gruk reacted: "One less boar."' in turn.prompt_block
    mid2 = db.queue()
    th.note_event(GID, 'bot_group_loot', 'Mira', 'Shiny.',
                  message_id=mid2)
    db.claim(mid2)
    db.drop(mid2)
    turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Shiny' not in turn.prompt_block


def test_thread_time_comes_from_the_actual_delivery():
    _reset(**{'LLMChatter.Threads.CoolMinutes': 10})
    db = _DB()
    turn, ids = _exchange(db, _report(topic='Dalaran', energy='high'),
                          outcome='pending')
    db.deliver(*ids, age=40 * 60)
    _sync(db)
    state = th.snapshot(GID)
    now = th._now()
    assert now - state.current.updated_at >= 40 * 60 - 5
    assert th._effective_energy(state.current, now) < 0.1
    assert th.render_for_player_reply(GID, db) == ''


def test_filtered_dialogue_line_blocks_report_adoption():
    _reset()
    db = _DB()
    response = json.dumps([
        {'speaker': 'Gruk', 'message': 'Hello.', 'emote': None,
         'action': None},
        {'speaker': 'Mira', 'message': '', 'emote': None,
         'action': None},
        {'thread': {'topic': 'Mira confesses a secret',
                    'energy': 'high', 'subject_changed': True,
                    'feelings': {'Mira': 'relieved after confessing',
                                 'Gruk': 'curious'}}},
    ])
    inserted = []
    ok = _run_patched(
        _idle_patches(db, response, inserted),
        lambda: chatter_group._idle_conversation(
            db, None, _IDLE_CONFIG, GID, _rows(), 'roleplay',
            '', NAMES, th._now(),
        ),
    )
    # The good line is still delivered...
    assert ok and len(inserted) == 1
    pending = th.snapshot(GID).pending[0]
    assert pending.speakers == ('Gruk',)
    assert pending.complete is False
    db.deliver(*inserted)
    _sync(db)
    state = th.snapshot(GID)
    # ...but a report describing more than was said is not adopted.
    assert state.current is None
    assert 'Mira' not in state.feelings
    assert 'Gruk' not in state.feelings


def test_lookup_outage_still_expires_old_proposals():
    _reset(**{'LLMChatter.Threads.PendingTimeoutSeconds': 60,
              'LLMChatter.Threads.MaxPending': 3})
    db = _DB()
    _exchange(db, _report(topic='Dalaran'))
    confirmed = th.snapshot(GID).current.topic
    mid = db.queue()
    th.note_event(GID, 'bot_group_kill', 'Gruk', 'x', message_id=mid)
    _exchange(db, _report(topic='rain'), outcome='pending')
    db.fail_status = True
    later = th._now() + 120
    with patch.object(th, '_now', return_value=later):
        _sync(db)
        state = th.snapshot(GID)
        assert not state.pending
        assert state.interruptions[-1]['quote'] == 'dropped'
        assert state.current.topic == confirmed
        # Repeated failures while new work keeps arriving stay bounded.
        for _ in range(10):
            turn = th.plan_idle_turn(GID, NAMES, db=db)
            th.record_idle_exchange(turn, _report(), NAMES,
                                    [db.queue()])
        assert len(th.snapshot(GID).pending) <= 3


def _pipeline_patches(reaction_side_effect):
    return [
        patch.object(chatter_handler_pipeline, 'get_bot_traits',
                     return_value={'traits': ['calm'], 'tone': 'x'}),
        patch.object(chatter_handler_pipeline, 'build_gear_context',
                     return_value=''),
        patch.object(chatter_handler_pipeline, '_get_recent_chat',
                     return_value=[]),
        patch.object(chatter_handler_pipeline, '_maybe_talent_context',
                     return_value=None),
        patch.object(chatter_handler_pipeline, 'run_single_reaction',
                     side_effect=reaction_side_effect),
        patch.object(chatter_handler_pipeline, '_store_chat'),
        patch.object(chatter_handler_pipeline, '_mark_event'),
        patch.object(chatter_handler_pipeline, 'update_bot_mood'),
    ]


def _run_death_event(db, side_effect):
    return _run_patched(
        _pipeline_patches(side_effect),
        lambda: chatter_handler_pipeline.run_group_handler(
            db, None, {}, {'id': 1},
            event_type_label='bot_group_death',
            extract_fields=lambda ed: {},
            build_prompt=lambda ctx: 'prompt',
            pre_parsed_extra={
                'bot_guid': 101, 'bot_name': 'Gruk',
                'group_id': GID, 'bot_class': 1, 'bot_race': 2,
            },
        ),
    )


def test_event_completion_cannot_resurrect_a_cleared_group():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Dalaran'))

    def cleared_during_llm(*args, **kwargs):
        th.clear_group(GID)
        return {'ok': True, 'message': 'Ow.', 'message_id': 5}

    _run_death_event(db, cleared_during_llm)
    assert th.snapshot(GID) is None


def test_event_completion_cannot_touch_a_new_session():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Dalaran'))

    def replaced_during_llm(*args, **kwargs):
        th.clear_group(GID)
        th.note_player_message(GID, 'Calwen', 'new party')
        return {'ok': True, 'message': 'Ow.', 'message_id': 5}

    _run_death_event(db, replaced_during_llm)
    state = th.snapshot(GID)
    assert state.current is None
    assert [i['kind'] for i in state.interruptions] == ['player']


def test_first_event_may_start_a_thread():
    _reset()
    db = _DB()
    _run_death_event(db, lambda *a, **k: {
        'ok': True, 'message': 'Ow.', 'message_id': 5,
    })
    assert th.snapshot(GID).current.topic == 'the death'

def test_first_event_cleared_during_llm_is_rejected():
    """No thread state before the event: a clear during the LLM
    wait must still reject the completion."""
    _reset()
    db = _DB()
    assert th.snapshot(GID) is None

    def cleared_during_llm(*args, **kwargs):
        th.clear_group(GID)
        return {'ok': True, 'message': 'Ow.', 'message_id': 5}

    _run_death_event(db, cleared_during_llm)
    assert th.snapshot(GID) is None


def test_first_event_replaced_during_llm_leaves_new_session_alone():
    _reset()
    db = _DB()
    assert th.snapshot(GID) is None

    def replaced_during_llm(*args, **kwargs):
        th.clear_group(GID)
        th.note_player_message(GID, 'Calwen', 'new party')
        return {'ok': True, 'message': 'Ow.', 'message_id': 5}

    _run_death_event(db, replaced_during_llm)
    state = th.snapshot(GID)
    assert state.current is None
    assert [i['kind'] for i in state.interruptions] == ['player']


def test_session_guard_with_clear_all_and_disabled_threads():
    _reset()
    db = _DB()

    def wiped_during_llm(*args, **kwargs):
        th.clear_all()
        return {'ok': True, 'message': 'Ow.', 'message_id': 5}

    _run_death_event(db, wiped_during_llm)
    assert th.snapshot(GID) is None
    _reset(**{'LLMChatter.Threads.Enable': 0})
    assert th.capture_session(GID) is None
    _run_death_event(db, lambda *a, **k: {
        'ok': True, 'message': 'Ow.', 'message_id': 5,
    })
    assert th.snapshot(GID) is None


def test_fresh_topic_supplies_only_new_subjects():
    _reset()
    db = _DB()
    calls = []

    def fresh():
        calls.append(1)
        return 'the price of Thorium'

    with patch.object(th, '_pick_move', return_value='new'):
        turn = th.plan_idle_turn(GID, NAMES, db=db, fresh_topic=fresh)
    assert (turn.source, turn.pool_topic) == (
        'topic', 'the price of Thorium')
    assert 'New subject for this exchange: the price of Thorium.' in (
        turn.prompt_block)
    assert 'a nudge, not a script' not in turn.prompt_block

    with patch.object(th, '_pick_move', return_value='new'):
        turn = th.plan_idle_turn(
            GID, NAMES, db=db, fresh_topic=lambda: None)
    assert turn.source in ('persona', 'surroundings', 'pool')

    _exchange(db, _report())
    calls.clear()
    with patch.object(th, '_pick_move', return_value='continue'):
        turn = th.plan_idle_turn(GID, NAMES, db=db, fresh_topic=fresh)
    assert turn.kind == 'continue' and not calls


def test_fresh_subject_leaves_the_old_one_behind():
    _reset()
    db = _DB()
    _exchange(db, _report(topic='Guild Motto Reflection',
                          point='What makes it resonate?'))
    with patch.object(th, '_pick_move', return_value='new'):
        turn = th.plan_idle_turn(
            GID, NAMES, db=db, fresh_topic=lambda: 'orcs never bathe')
    block = turn.prompt_block
    assert 'Current subject' not in block
    assert 'Open point' not in block
    assert 'Previous subject (finished, leave it behind): ' \
        'Guild Motto Reflection' in block
    assert 'New subject for this exchange: orcs never bathe.' in block

    with patch.object(th, '_pick_move', return_value='continue'):
        turn = th.plan_idle_turn(GID, NAMES, db=db)
    assert 'Current subject: Guild Motto Reflection' in turn.prompt_block
    assert 'Open point: What makes it resonate?' in turn.prompt_block


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    th.reset_settings()
    th.clear_all()
    print(f"{len(tests)} conversation thread checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
