#!/usr/bin/env python3
"""Guild and General conversation thread checks.

Covers channel-namespaced thread keys (party, guild, General per zone
and faction), per-channel toggles, the message-only report schemas,
and integration through the real General ambient and Guild idle
handlers, with delivery-confirmed adoption.

Run directly from the module root:
  python tools/tests/test_guild_general_threads.py
"""

import importlib
import itertools
import json
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

import chatter_ambient as ambient  # noqa: E402
import chatter_guild as guild  # noqa: E402
import chatter_threads as th  # noqa: E402
from chatter_general import _build_general_response_prompt  # noqa: E402
from chatter_shared import (  # noqa: E402
    append_conversation_json_instruction,
    append_json_instruction,
)

RP = {'LLMChatter.ChatterMode': 'roleplay'}
REPORT = {'topic': 'the old war', 'energy': 'high',
          'subject_changed': True, 'open_point': '',
          'feelings': {}}


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


def _reset(**overrides):
    th.reset_settings()
    config = {'LLMChatter.Threads.SurpriseChance': 0}
    config.update(overrides)
    th.configure_threads(config)
    th.clear_all()


class _Cursor:
    def __init__(self, db):
        self.db = db
        self.rows = []

    def execute(self, query, params=None):
        self.rows = []
        if 'FROM llm_chatter_messages' in query:
            self.rows = [
                {'id': mid, 'delivered': 1, 'drop_reason': None,
                 'delivered_at': 'sent', 'age_s': 0}
                for mid in params if mid in self.db.delivered
            ] + [
                {'id': mid, 'delivered': 0, 'drop_reason': None,
                 'delivered_at': None, 'age_s': None}
                for mid in params if mid not in self.db.delivered
            ]

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _DB:
    def __init__(self):
        self.ids = itertools.count(1)
        self.delivered = set()
        self.inserted = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def commit(self):
        pass

    def insert(self, *args, **kwargs):
        mid = next(self.ids)
        self.inserted.append((mid, kwargs.get('bot_name') or args[2]))
        return mid

    def deliver_all(self):
        self.delivered.update(mid for mid, _ in self.inserted)


def _sync(db, key):
    with th._lock:
        state = th._get(key, create=False)
        if state is not None:
            th._reconcile(db, state, th._now())


# ------------------------------------------------------------
# Keys, reconciliation, toggles
# ------------------------------------------------------------
def test_channel_keys_are_separate():
    _reset()
    ally = th.general_key(12, 'Alliance')
    horde = th.general_key(12, 'Horde')
    assert ally != horde and ally[0] == 'general'
    assert th.guild_key(5) == ('guild', 5)
    assert th.general_key(0, 'Alliance') is None
    assert th.general_key(12, '') is None
    assert th.guild_key(0) is None
    for key in (ally, horde, th.guild_key(5), 42):
        th.note_player_message(key, 'Calwen', 'hello')
    assert th.snapshot(ally) is not th.snapshot(horde)
    assert th.snapshot(42) is not None
    assert th.snapshot(('party', 42)) is not None


def test_party_reconcile_never_touches_guild_or_general():
    _reset()
    ally = th.general_key(12, 'Alliance')
    th.note_player_message(ally, 'Calwen', 'hi')
    th.note_player_message(th.guild_key(5), 'Calwen', 'hi')
    th.note_player_message(42, 'Calwen', 'hi')
    th.reconcile_active_groups([])
    assert th.snapshot(42) is None
    assert th.snapshot(ally) is not None
    assert th.snapshot(th.guild_key(5)) is not None


def test_per_channel_toggles():
    _reset(**{'LLMChatter.Threads.GuildEnable': 0})
    assert th.plan_idle_turn(th.guild_key(5), ['A']) is None
    assert th.plan_idle_turn(th.general_key(1, 'Horde'), ['A'])
    assert th.plan_idle_turn(42, ['A'])
    _reset(**{'LLMChatter.Threads.GeneralEnable': 0})
    assert th.plan_idle_turn(th.general_key(1, 'Horde'), ['A']) is None
    assert th.plan_idle_turn(th.guild_key(5), ['A'])
    _reset(**{'LLMChatter.Threads.Enable': 0})
    assert th.plan_idle_turn(th.guild_key(5), ['A']) is None
    assert th.plan_idle_turn(42, ['A']) is None


def test_message_only_schemas_carry_the_optional_report():
    plain = append_json_instruction(
        'x', allow_action=False, message_only=True,
    ).system_prompt
    assert '"thread"' not in plain
    single = append_json_instruction(
        'x', allow_action=False, message_only=True,
        extra_field=th.THREAD_REPORT_FIELD,
        extra_rule=th.THREAD_REPORT_RULE,
    ).system_prompt
    assert '"message": "your spoken words here",' in single
    assert '"thread": {"topic"' in single
    conv = append_conversation_json_instruction(
        'x', ['A', 'B'], 2, message_only=True,
        trailing_object=th.THREAD_REPORT_OBJECT,
        extra_rule=th.THREAD_REPORT_RULE,
    ).system_prompt
    assert 'then one final object' in conv
    assert '{"thread": {"topic"' in conv


# ------------------------------------------------------------
# General channel
# ------------------------------------------------------------
_AMBIENT_REQUEST = {
    'id': 900, 'zone_id': 12, 'area_id': 12,
    'message_type': 'plain', 'bot1_race': 1,
}
_BOT = {'guid': 101, 'name': 'Aldric', 'class': 'Warrior',
        'race': 'Human', 'level': 20, 'zone': 'Elwynn Forest'}


def _ambient_patches(db, response, prompts):
    def fake_llm(client, prompt, config, **kwargs):
        prompts.append(_text(prompt))
        return response

    return [
        patch.object(ambient, 'call_llm', side_effect=fake_llm),
        patch.object(ambient, 'insert_chat_message',
                     side_effect=db.insert),
        patch.object(ambient, 'query_zone_mobs', return_value=[]),
        patch.object(ambient, 'get_recent_zone_messages',
                     return_value=[]),
        patch.object(ambient, 'build_gear_context', return_value=''),
        patch.object(ambient, 'resolve_persona',
                     side_effect=lambda db, g, n, m: None),
        patch.object(ambient, 'build_talent_context',
                     return_value=None),
        patch.object(ambient, 'maybe_queue_group_general_reaction'),
        patch.object(ambient, '_zone_delivery_delay', return_value=1),
        patch.object(ambient, '_reserve_zone_delivery_window',
                     return_value=1),
        patch.object(ambient, 'is_too_similar', return_value=False),
    ]


def _run(patches, fn):
    for p in patches:
        p.start()
    try:
        return fn()
    finally:
        for p in patches:
            p.stop()


def test_general_statement_follows_the_zone_thread():
    _reset()
    db = _DB()
    prompts = []
    response = json.dumps({'message': 'Anyone remember the war?',
                           'thread': REPORT})
    ok = _run(_ambient_patches(db, response, prompts), lambda: (
        ambient.process_statement(
            db, db.cursor(), None, RP, dict(_AMBIENT_REQUEST),
            dict(_BOT, persona=None),
        )
    ))
    assert ok and len(db.inserted) == 1
    assert '<conversation_thread>' in prompts[0]
    assert 'Topic:' not in prompts[0]
    key = th.general_key(12, 'Alliance')
    assert len(th.snapshot(key).pending) == 1
    db.deliver_all()
    _sync(db, key)
    assert th.snapshot(key).current.topic == 'the old war'
    assert th.snapshot(th.general_key(12, 'Horde')) is None


def test_general_conversation_records_complete_exchange_only():
    for lines, adopted in (
        ([('Aldric', 'Anyone remember the war?'),
          ('Mira', 'Every night.')], True),
        ([('Aldric', 'Anyone remember the war?'),
          ('Stranger', 'Who?')], False),
    ):
        _reset()
        db = _DB()
        prompts = []
        items = [{'speaker': s, 'message': m} for s, m in lines]
        items.append({'thread': REPORT})
        bots = [dict(_BOT), dict(_BOT, guid=102, name='Mira')]
        _run(_ambient_patches(db, json.dumps(items), prompts),
             lambda: ambient.process_conversation(
                 db, db.cursor(), None, RP,
                 dict(_AMBIENT_REQUEST), bots,
             ))
        assert '<conversation_thread>' in prompts[0]
        assert 'Topic hint' not in prompts[0]
        key = th.general_key(12, 'Alliance')
        db.deliver_all()
        _sync(db, key)
        current = th.snapshot(key).current
        assert (current is not None
                and current.topic == 'the old war') == adopted


def test_general_threads_off_keep_the_random_topic():
    _reset(**{'LLMChatter.Threads.GeneralEnable': 0})
    db = _DB()
    prompts = []
    _run(_ambient_patches(db, '{"message": "hi"}', prompts), lambda: (
        ambient.process_statement(
            db, db.cursor(), None, RP, dict(_AMBIENT_REQUEST),
            dict(_BOT),
        )
    ))
    assert 'Topic:' in prompts[0]
    assert '<conversation_thread>' not in prompts[0]


def test_general_reply_sees_the_channel_thread():
    note = 'Before this message the bots were talking about the war.'
    common = ('Aldric', 'Human', 'Warrior', 20, 'male', ['stern'],
              'Calwen', 'what war?', 'Elwynn Forest', '', 'roleplay')
    prompt = _text(_build_general_response_prompt(
        *common, thread_context=note,
    ))
    assert note in prompt
    brief = _text(_build_general_response_prompt(
        *common, thread_context=note, brief_casual=True,
    ))
    assert note not in brief


# ------------------------------------------------------------
# Guild chat
# ------------------------------------------------------------
_SPEAKER = {'guid': 101, 'class': 'Warrior', 'race': 'Orc',
            'gender': 'male', 'level': 40, 'traits': ['gruff'],
            'tone': 'terse', 'backstory': '', 'mood': ''}


def _guild_patches(db, response, prompts):
    def fake_llm(client, prompt, config, **kwargs):
        prompts.append(_text(prompt))
        return response

    return [
        patch.object(guild, 'call_llm', side_effect=fake_llm),
        patch.object(guild, 'insert_chat_message',
                     side_effect=db.insert),
        patch.object(guild, '_query_speaker',
                     side_effect=lambda db, guid: dict(
                         _SPEAKER, guid=guid)),
        patch.object(guild, '_select_guild_history_context',
                     return_value=('', {})),
        patch.object(guild, '_mark_event'),
        patch.object(guild, 'calculate_dynamic_delay',
                     return_value=1),
    ]


def _guild_event(participants):
    return {
        'id': 77, 'subject_guid': participants[0][0],
        'subject_name': participants[0][1],
        'extra_data': json.dumps({
            'guild_id': 5, 'guild_name': 'Horde Heroes',
            'mode': 'conversation' if len(participants) > 1
            else 'statement',
            'participants': [
                {'guid': g, 'name': n} for g, n in participants
            ],
        }),
    }


def test_guild_statement_follows_the_guild_thread():
    _reset()
    db = _DB()
    prompts = []
    response = json.dumps({'message': 'Blood and thunder.',
                           'thread': REPORT})
    _run(_guild_patches(db, response, prompts), lambda: (
        guild.process_guild_idle_chatter_event(
            db, None, RP, _guild_event([(101, 'Gruk')]),
        )
    ))
    assert len(db.inserted) == 1
    assert '<conversation_thread>' in prompts[0]
    assert 'Topic idea' not in prompts[0]
    key = th.guild_key(5)
    db.deliver_all()
    _sync(db, key)
    assert th.snapshot(key).current.topic == 'the old war'


def test_guild_conversation_follows_the_guild_thread():
    _reset()
    db = _DB()
    prompts = []
    response = json.dumps([
        {'speaker': 'Gruk', 'message': 'The war never ended.'},
        {'speaker': 'Mira', 'message': 'It did for me.'},
        {'thread': REPORT},
    ])
    _run(_guild_patches(db, response, prompts), lambda: (
        guild.process_guild_idle_chatter_event(
            db, None, RP,
            _guild_event([(101, 'Gruk'), (102, 'Mira')]),
        )
    ))
    assert len(db.inserted) == 2
    assert '<conversation_thread>' in prompts[0]
    assert 'Shared subject for the whole exchange' not in prompts[0]
    key = th.guild_key(5)
    pending = th.snapshot(key).pending[0]
    assert pending.complete is True
    db.deliver_all()
    _sync(db, key)
    assert th.snapshot(key).current.topic == 'the old war'


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    th.reset_settings()
    th.clear_all()
    print(f"{len(tests)} guild/General thread checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
