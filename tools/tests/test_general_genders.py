#!/usr/bin/env python3
"""Genders in General, ambient, world-event, loot and precache prompts.

Covers the guid lookup, the data sources that used to drop gender (queue
rows, bot candidate rows, gossip targets, precache lookups), the speaker
gender line in every multi-bot General conversation, the gossip subject,
zone intrusion, General replies to the player, and the Guild Master.

Run directly from the module root:
  python tools/tests/test_general_genders.py
"""

import ast
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_persona_coherence as persona_tests  # noqa: E402  stubs + path

import chatter_member_gender as gender  # noqa: E402
import chatter_prompts  # noqa: E402

GRUK = persona_tests.GRUK
MIRA = persona_tests.MIRA
RP = persona_tests.RP
NORMAL = persona_tests.NORMAL
TOOLS_DIR = Path(__file__).resolve().parents[1]

CHARACTERS = [
    {'guid': 101, 'name': 'Gruk', 'gender': 0},
    {'guid': 102, 'name': 'Mira', 'gender': 1},
    {'guid': 103, 'name': 'Lyn', 'gender': 1},
    {'guid': 104, 'name': 'Nul', 'gender': None},
]


class Cursor:
    """Answers characters lookups by guid or name; records queries."""

    def __init__(self, db):
        self.db = db
        self.rows = []
        self.row = None

    def execute(self, sql, params=None):
        self.db.queries.append(sql)
        if self.db.fail:
            raise RuntimeError('db down')
        params = tuple(params or ())
        if 'FROM llm_chatter_queue' in sql:
            self.row = self.db.request
            self.rows = [self.row] if self.row else []
        elif 'FROM characters' in sql and 'WHERE guid IN' in sql:
            self.rows = [c for c in CHARACTERS if c['guid'] in params]
        elif 'FROM characters' in sql and 'WHERE name IN' in sql:
            self.rows = [c for c in CHARACTERS if c['name'] in params]
        elif 'FROM characters' in sql:
            self.rows = list(self.db.rows)
            self.row = self.rows[0] if self.rows else None
        else:
            self.rows, self.row = [], None

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.row

    def close(self):
        pass


class DB:
    def __init__(self, rows=(), request=None, fail=False):
        self.rows = list(rows)
        self.request = request
        self.fail = fail
        self.queries = []

    def cursor(self, dictionary=False):
        return Cursor(self)

    def commit(self):
        pass


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


def _bare(bot):
    return {k: v for k, v in bot.items() if k != 'gender'}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def test_guid_lookup_contract():
    db = DB()
    assert gender.get_genders_by_guid(db, [101, 102, 104, 999, 'x', 0]) == {
        101: 'male', 102: 'female',
    }
    assert gender.get_genders_by_guid(DB(fail=True), [101]) == {}
    empty = DB()
    assert gender.get_genders_by_guid(empty, []) == {}
    assert empty.queries == []


def test_attach_fills_only_missing_genders():
    bots = [_bare(GRUK), dict(MIRA, gender='female'), {'guid': 104}]
    db = DB()
    gender.attach_bot_genders(db, bots)
    assert bots[0]['gender'] == 'male'
    assert bots[1]['gender'] == 'female'
    assert 'gender' not in bots[2]  # NULL stays unknown
    assert 'WHERE guid IN' in db.queries[0]


def test_formatter_never_states_unknown():
    assert gender.speaker_gender_line(
        [{'name': 'A', 'gender': ''}, {'name': 'B', 'gender': 'unknown'}],
    ) == ''
    line = gender.speaker_gender_line([GRUK, MIRA])
    assert 'Gruk is male' in line and 'Mira is female' in line


# ------------------------------------------------------------
# Multi-bot General conversations
# ------------------------------------------------------------
def _conversations(config):
    persona_tests._reset_mood()
    persona_tests._quiet_flavor()
    bots = [dict(GRUK), dict(MIRA)]
    item = {'item_name': 'Linen Cloth', 'item_entry': 2589,
            'quality': 1, 'count': 8}
    yield 'plain', chatter_prompts.build_plain_conversation_prompt(
        bots, config=config)
    yield 'event', chatter_prompts.build_event_conversation_prompt(
        bots, 'The rain starts.', config=config)
    yield 'trade', chatter_prompts.build_trade_conversation_prompt(
        bots, item, config=config)
    yield 'gossip', chatter_prompts.build_gossip_conversation_prompt(
        bots, dict(GRUK, name='Tova', gender='female'), 'bot', 17,
        config=config)


def test_every_conversation_states_speaker_genders():
    for config in (RP, NORMAL):
        for kind, prompt in _conversations(config):
            text = _text(prompt)
            assert 'Gruk is male' in text, (kind, config)
            assert 'Mira is female' in text, (kind, config)
    rp = dict(_conversations(RP))
    assert 'Mira is a female Human Mage' in _text(rp['plain'])


def test_unknown_speaker_gender_adds_nothing():
    persona_tests._quiet_flavor()
    text = _text(chatter_prompts.build_plain_conversation_prompt(
        [_bare(GRUK), _bare(MIRA)], config=RP))
    assert 'Genders:' not in text
    assert 'Mira is a Human Mage' in text
    assert 'male' not in text


def test_gossip_bot_target_carries_gender():
    target = dict(GRUK, name='Tova', gender='female')
    assert 'gender=female' in chatter_prompts._format_gossip_target(
        target, 'bot')
    assert 'gender=' not in chatter_prompts._format_gossip_target(
        _bare(target), 'bot')
    npc = {'name': 'Innkeeper Gryshka', 'function': 'innkeeper'}
    assert 'gender' not in chatter_prompts._format_gossip_target(npc, 'npc')


# ------------------------------------------------------------
# Data sources
# ------------------------------------------------------------
def test_candidate_rows_select_gender():
    import chatter_db
    for fn, args in (
        (chatter_db.get_zone_bot_candidates, ()),
        (chatter_db.get_zone_bot_candidates, (12,)),
        (chatter_db.get_bots_by_guid, ([101],)),
    ):
        db = DB()
        fn(db.cursor(), *args)
        assert 'c.gender as bot1_gender' in db.queries[0], fn
    rows = [{'guid': 7, 'name': 'Tova', 'class': 1, 'race': 2,
             'level': 20, 'zone': 17, 'gender': 1},
            {'guid': 8, 'name': 'Zed', 'class': 1, 'race': 2,
             'level': 20, 'zone': 17, 'gender': None}]
    db = DB(rows=rows)
    targets = chatter_db.query_zone_bot_gossip_targets(db.cursor(), 17)
    assert [t['gender'] for t in targets] == ['female', '']


def test_world_event_conversation_passes_gender():
    import chatter_world_events as events
    rows = [events._normalize_bot({
        'bot1_guid': 102, 'bot1_name': 'Mira', 'bot1_class': 8,
        'bot1_race': 1, 'bot1_level': 40, 'bot1_gender': 1,
        'zone_id': 17,
    }), events._normalize_bot({
        'bot1_guid': 101, 'bot1_name': 'Gruk', 'bot1_class': 1,
        'bot1_race': 2, 'bot1_level': 40, 'bot1_gender': 0,
        'zone_id': 17,
    })]
    assert rows[0]['bot1_gender'] == 'female'
    captured = {}
    real = events.build_event_conversation_prompt

    def capture(bots, *args, **kwargs):
        captured['prompt'] = _text(real(bots, *args, **kwargs))
        return captured['prompt']

    with patch.object(events, 'attach_speaker_gear'), \
            patch.object(events, 'prepare_channel_persona',
                         return_value=None), \
            patch.object(events, 'get_recent_zone_messages',
                         return_value=[]), \
            patch.object(events, 'build_event_context',
                         return_value='The rain starts.'), \
            patch.object(events, 'build_event_conversation_prompt',
                         side_effect=capture), \
            patch.object(events, 'call_llm', return_value=''):
        events._deliver_conversation(
            DB(), None, NORMAL, {'id': 1, 'event_type': 'weather_change'},
            rows, {}, 17,
        )
    assert 'Mira is female' in captured['prompt']


def test_loot_looter_gets_gender():
    import chatter_loot
    row = {'bot1_guid': 102, 'bot1_name': 'Mira', 'bot1_class': 8,
           'bot1_race': 1, 'bot1_level': 40, 'bot1_gender': 1,
           'zone_id': 17}
    with patch.object(chatter_loot, 'get_bots_by_guid', return_value=[row]):
        bot = chatter_loot._resolve_looter(DB(), 102)
    assert bot['gender'] == 'female'


def test_queue_requests_get_speaker_genders():
    import llm_chatter_bridge as bridge
    captured = {}
    base = {'id': 1, 'zone_id': 17, 'bot1_guid': 102, 'bot1_name': 'Mira',
            'bot1_class': 8, 'bot1_race': 1, 'bot1_level': 40,
            'bot1_zone': 17}
    conversation = dict(base, request_type='conversation', bot2_guid=101,
                        bot2_name='Gruk', bot2_class=1, bot2_race=2,
                        bot2_level=40)
    statement = dict(base, request_type='statement')

    def grab(kind):
        def run(db, cursor, client, config, request, bots):
            captured[kind] = bots
            return False
        return run

    with patch.object(bridge, 'stagger_if_needed'), \
            patch.object(bridge, 'get_character_guild_name',
                         return_value=''), \
            patch.object(bridge, 'process_statement',
                         side_effect=grab('statement')), \
            patch.object(bridge, 'process_conversation',
                         side_effect=grab('conversation')):
        bridge.process_pending_requests(DB(request=statement), None, {})
        bridge.process_pending_requests(DB(request=conversation), None, {})
    assert captured['statement']['gender'] == 'female'
    assert [b['gender'] for b in captured['conversation']] == [
        'female', 'male']


def test_zone_intrusion_states_both_genders():
    import chatter_events
    captured = {}

    def fake_reaction(db, client, config, prompt, **kwargs):
        captured['prompt'] = _text(prompt)
        return {'ok': True}

    extra = {'defender_guid': 102, 'defender_name': 'Mira',
             'defender_class': 8, 'defender_race': 1, 'defender_level': 40,
             'intruder_name': 'Lyn', 'intruder_class': 4,
             'intruder_race': 8, 'intruder_level': 30,
             'zone_name': 'Elwynn Forest'}
    event = {'id': 3, 'extra_data': extra}
    handler = next(
        getattr(chatter_events, n) for n in dir(chatter_events)
        if 'intrusion' in n and callable(getattr(chatter_events, n))
        and n.startswith('process')
    )
    with patch.object(chatter_events, 'run_single_reaction',
                      side_effect=fake_reaction):
        handler(DB(), None, RP, event)
    assert 'You are Mira' in captured['prompt']
    assert 'female' in captured['prompt'].split('SITUATION')[0]
    assert 'An enemy female Troll' in captured['prompt']


def test_precache_lookup_and_header_carry_gender():
    import chatter_cache
    from chatter_group_prompts import build_precache_combat_pull_prompt
    db = DB(rows=[{'race': 1, 'class': 8, 'level': 40, 'gender': 1}])
    info = chatter_cache._get_bot_race_class(db, 102)
    assert info[-1] == 'female' and 'gender' in db.queries[0]
    db = DB(rows=[{'race': 1, 'class': 8, 'level': 40, 'gender': None}])
    assert chatter_cache._get_bot_race_class(db, 102)[-1] == ''
    text = _text(build_precache_combat_pull_prompt(
        'Mira', 'Human', 'Mage', 40, ['curious'], 'neutral',
        mode='roleplay', gender='female',
    ))
    assert 'female' in text


# ------------------------------------------------------------
# General replies to the player
# ------------------------------------------------------------
def test_general_reply_wrapper_names_player_and_others():
    from chatter_general import _history_names
    from chatter_shared import append_json_instruction
    history = [{'speaker_name': 'Lyn', 'is_bot': 0, 'message': 'hi'},
               {'speaker_name': 'Gruk', 'is_bot': 1, 'message': 'lok'}]
    base = append_json_instruction('Reply to Lyn.', allow_action=False)
    prompt = gender.with_character_genders(
        base, DB(), _history_names(history) + ['Mira'],
        player_name='Lyn', exclude=('Gruk',),
    )
    text = _text(prompt)
    assert 'Lyn (the player) is female' in text
    assert 'Mira is female' in text
    assert 'Gruk is' not in text
    assert prompt.response_contract == base.response_contract
    assert gender.with_character_genders(
        base, DB(fail=True), ['Mira'], player_name='Lyn') is base


def test_every_general_reply_build_is_wrapped():
    """Each General reply prompt is passed through with_character_genders
    right after it is built, excluding its own speaker."""
    tree = ast.parse((TOOLS_DIR / 'chatter_general.py').read_text(
        encoding='utf-8'))
    builders = {
        '_build_general_response_prompt',
        '_build_general_followup_prompt',
        '_build_general_continuation_prompt',
    }
    wrapped = set()
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if not isinstance(body, list):
            continue
        for first, second in zip(body, body[1:]):
            if not (isinstance(first, ast.Assign)
                    and isinstance(first.value, ast.Call)
                    and getattr(first.value.func, 'id', '') in builders):
                continue
            call = getattr(second, 'value', None)
            assert isinstance(call, ast.Call), first.value.func.id
            assert getattr(call.func, 'id', '') == 'with_character_genders'
            keywords = {k.arg for k in call.keywords}
            assert {'player_name', 'exclude'} <= keywords
            wrapped.add(first.value.func.id)
    assert wrapped == builders


def test_lingering_thread_speaker_gets_a_gender():
    """A speaker named only by the thread block (old feeling or an
    interruption) is outside the current cast and General history."""
    import chatter_ambient
    import chatter_threads as th
    th.reset_settings()
    th.configure_threads({'LLMChatter.Threads.SurpriseChance': 0})
    th.clear_all()
    try:
        request = {'bot1_race': 1}
        key = chatter_ambient._general_thread_key(request, 12)
        th.note_player_message(key, 'Mira', 'anyone seen the caravan?')
        with th._lock:
            state = th._get(key, create=True)
            state.feelings['Lyn'] = ('still wary of the road', state.turn)
            state.feelings['Nul'] = ('long gone', state.turn - 99)
        names = th.thread_names(key)
        assert 'Lyn' in names and 'Mira' in names
        assert 'Nul' not in names  # expired feelings are not rendered
        prompt = chatter_ambient._with_thread_genders(
            'Base prompt.', DB(), request, 12, ['Gruk'],
        )
        assert 'Lyn is female' in prompt and 'Mira is female' in prompt
        assert 'Gruk is' not in prompt
        assert chatter_ambient._with_thread_genders(
            'Base prompt.', DB(), request, 12, ['Lyn', 'Mira'],
        ) == 'Base prompt.'
    finally:
        th.clear_all()
        th.reset_settings()


def test_general_reply_includes_thread_names():
    source = (TOOLS_DIR / 'chatter_general.py').read_text(encoding='utf-8')
    assert 'thread_people = thread_names(thread_key)' in source
    assert '_history_names(history) + thread_people' in source
    # The thread names are read before the player's line is noted, and
    # only when a thread note is actually rendered.
    assert source.index('thread_people = thread_names') < source.index(
        'note_player_message(thread_key')


def test_guild_master_gender_in_general_praise():
    import chatter_ambient
    profile = {'id': 9, 'name': 'Keepers', 'info': '', 'motd': '',
               'leader': {'guid': 5, 'name': 'Varra', 'race': 'Orc',
                          'class': 'Warrior', 'gender': 'female'}}
    with patch.object(chatter_ambient, 'get_character_guild',
                      return_value={'id': 9, 'name': 'Keepers',
                                    'rank': 3}), \
            patch.object(chatter_ambient, 'get_guild_profile',
                         return_value=profile), \
            patch.object(chatter_ambient.random, 'randint', return_value=1):
        topic = chatter_ambient._guild_praise_topic(
            object(), {}, {'guid': 101, 'name': 'Aliss'})
    assert 'Guild Master Varra, a female Orc Warrior' in topic


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} General gender checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
