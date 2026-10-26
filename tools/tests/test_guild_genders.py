#!/usr/bin/env python3
"""Genders in Guild chat prompts.

Covers the roleplay identity line (speaker and co-participants), the
gender line for guildmates, history speakers and lingering thread
speakers on idle Guild chatter, player-reply session context and the
session summary update (including speakers named only in the previous
summary), rank-change officers, newcomer replies and the meet post.

Run directly from the module root:
  python tools/tests/test_guild_genders.py
"""

import inspect
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_guild_conversations as conv_tests  # noqa: E402  stubs + path
import test_guild_player_replies as reply_tests  # noqa: E402

import chatter_guild  # noqa: E402
import chatter_guild_events  # noqa: E402
import chatter_guild_player  # noqa: E402
import chatter_guild_world_events  # noqa: E402
import chatter_threads as th  # noqa: E402

GENDERS = {'Aliss': 1, 'Bran': 0, 'Calia': 1, 'Cora': 1, 'Calwen': 1,
           'Brenna': 1, 'Zed': 0, 'Rytsen': 0}
GUIDS = {501: 1, 502: 0}


def _text(prompt):
    return getattr(prompt, 'user_prompt', prompt)


class GenderCursor:
    """Answers characters gender lookups; delegates everything else."""

    def __init__(self, inner, db):
        self.inner = inner
        self.db = db
        self.rows = None

    def execute(self, query, params=None):
        params = tuple(params or ())
        if 'FROM characters' in query and 'WHERE name IN' in query:
            self.rows = [{'name': n, 'gender': GENDERS[n]}
                         for n in params if n in GENDERS]
        elif 'FROM characters' in query and 'WHERE guid IN' in query:
            self.rows = [{'guid': g, 'gender': GUIDS[g]}
                         for g in params if g in GUIDS]
        elif 'SELECT DISTINCT speaker_name' in query:
            self.rows = [{'speaker_name': n}
                         for n in self.db.session_speakers]
        else:
            self.rows = None
            if self.inner is not None:
                self.inner.execute(query, params)

    def fetchall(self):
        if self.rows is not None:
            return list(self.rows)
        return self.inner.fetchall() if self.inner is not None else []

    def fetchone(self):
        if self.rows is not None:
            return self.rows[0] if self.rows else None
        return self.inner.fetchone() if self.inner is not None else None

    def close(self):
        pass


class GenderDB:
    def __init__(self, inner=None, session_speakers=()):
        self.inner = inner
        self.session_speakers = list(session_speakers)

    def cursor(self, *args, **kwargs):
        inner = self.inner.cursor(*args, **kwargs) if self.inner else None
        return GenderCursor(inner, self)

    def commit(self):
        if self.inner is not None and hasattr(self.inner, 'commit'):
            self.inner.commit()

    def __getattr__(self, name):
        return getattr(self.inner, name)


# ------------------------------------------------------------
# Identity
# ------------------------------------------------------------
def test_roleplay_identity_states_gender():
    speaker = {'race': 'Orc', 'class': 'Warrior', 'gender': 'female',
               'level': 80}
    line = chatter_guild._guild_identity('Aliss', speaker)
    assert line.startswith('You are Aliss, a female Orc Warrior')
    unknown = chatter_guild._guild_identity(
        'Aliss', dict(speaker, gender=''))
    assert 'female' not in unknown and ' male' not in unknown
    lines = chatter_guild._participant_identity_lines(
        {'name': 'Aliss', 'speaker': dict(speaker, traits=['calm'],
                                          tone='warm')},
        'roleplay',
    )
    assert 'a female Orc Warrior' in lines[0]


# ------------------------------------------------------------
# Idle Guild chatter
# ------------------------------------------------------------
def _run_idle_conversation(history_rows):
    names = ['Aliss', 'Bran']
    inner = conv_tests._DB()
    inner.history_session_id = 5
    inner.history_rows = history_rows
    db = GenderDB(inner)
    prompts = []

    def fake_call_llm(client, prompt, config, **kwargs):
        prompts.append(_text(prompt))
        return conv_tests._conversation_response(names)

    config = dict(conv_tests._config())
    config['LLMChatter.GuildChatter.HistoryContextChance'] = 100
    th.reset_settings()
    th.configure_threads({'LLMChatter.Threads.SurpriseChance': 0})
    th.clear_all()
    try:
        with patch.object(chatter_guild, '_query_speaker',
                          side_effect=lambda d, g: conv_tests._speaker(g)), \
                patch.object(chatter_guild, 'call_llm',
                             side_effect=fake_call_llm), \
                patch.object(chatter_guild, 'insert_chat_message'), \
                patch.object(chatter_guild,
                             'select_conversation_message_count',
                             return_value=4), \
                patch.object(chatter_guild, 'calculate_dynamic_delay',
                             return_value=5.0), \
                patch.object(chatter_guild.random, 'choice',
                             return_value='the long road home'), \
                patch.object(chatter_guild.random, 'randint',
                             return_value=100):
            chatter_guild.process_guild_idle_chatter_event(
                db, None, config, conv_tests._event(names))
    finally:
        th.clear_all()
        th.reset_settings()
    return prompts[0]


def test_idle_conversation_states_guildmate_and_history_genders():
    prompt = _run_idle_conversation([{
        'id': 1, 'speaker_name': 'Cora', 'is_bot': 1,
        'source_kind': 'ambient', 'message': 'The road is quiet.',
    }])
    assert 'Calia is female' in prompt   # online guildmate
    assert 'Cora is female' in prompt    # history speaker
    gender_line = [line for line in prompt.splitlines()
                   if line.startswith('Genders:')][0]
    assert 'Aliss' not in gender_line and 'Bran' not in gender_line


def test_idle_statement_states_guildmate_gender():
    inner = conv_tests._DB()
    db = GenderDB(inner)
    prompts = []
    event = conv_tests._event(['Aliss'])
    extra = json.loads(event['extra_data'])
    extra['mode'] = 'statement'
    event['extra_data'] = json.dumps(extra)

    def fake_call_llm(client, prompt, config, **kwargs):
        prompts.append(_text(prompt))
        return json.dumps({'message': 'Quiet night.'})

    with patch.object(chatter_guild, '_query_speaker',
                      side_effect=lambda d, g: conv_tests._speaker(g)), \
            patch.object(chatter_guild, 'call_llm',
                         side_effect=fake_call_llm), \
            patch.object(chatter_guild, 'insert_chat_message'), \
            patch.object(chatter_guild.random, 'randint',
                         return_value=100):
        chatter_guild.process_guild_idle_chatter_event(
            db, None, conv_tests._config(), event)
    assert prompts and 'Calia is female' in prompts[0]
    assert 'Aliss is' not in prompts[0]


def test_lingering_thread_speaker_gets_a_gender():
    th.reset_settings()
    th.configure_threads({'LLMChatter.Threads.SurpriseChance': 0})
    th.clear_all()
    try:
        key = th.guild_key(9)
        with th._lock:
            state = th._get(key, create=True)
            state.feelings['Brenna'] = ('uneasy', state.turn)
        extra = {'guild_id': 9}
        threaded = chatter_guild._with_guild_genders(
            'Base.', GenderDB(), extra, '', {}, True, ['Aliss'])
        assert 'Brenna is female' in threaded
        # No thread note rendered: its names are not added.
        assert chatter_guild._with_guild_genders(
            'Base.', GenderDB(), extra, '', {}, False, ['Aliss'],
        ) == 'Base.'
    finally:
        th.clear_all()
        th.reset_settings()


def test_history_metadata_lists_speakers():
    inner = conv_tests._DB()
    inner.history_session_id = 5
    inner.history_rows = [
        {'id': 1, 'speaker_name': 'Cora', 'is_bot': 1, 'message': 'a'},
        {'id': 2, 'speaker_name': 'Calwen', 'is_bot': 0, 'message': 'b'},
        {'id': 3, 'speaker_name': 'Cora', 'is_bot': 1, 'message': 'c'},
    ]
    config = dict(conv_tests._config())
    config['LLMChatter.GuildChatter.HistoryContextChance'] = 100
    with patch.object(chatter_guild.random, 'randint', return_value=1):
        _, metadata = chatter_guild._select_guild_history_context(
            inner, config, 9)
    assert metadata['guild_history_speakers'] == ['Cora', 'Calwen']


# ------------------------------------------------------------
# Player replies and the session summary
# ------------------------------------------------------------
def test_reply_context_names_summary_only_speaker():
    event = reply_tests._event()
    extra = json.loads(event['extra_data'])
    extra['candidates'] = [reply_tests._candidate(101, 'Aliss')]
    event['extra_data'] = json.dumps(extra)
    captured = {}
    params = list(inspect.signature(
        chatter_guild_player._generate_single_reply).parameters)

    def capture(*args, **kwargs):
        bound = dict(zip(params, args))
        bound.update(kwargs)
        captured['context'] = bound['session_context']
        return [{'name': 'Aliss', 'message': 'Still out there.'}]

    db = GenderDB(None, session_speakers=['Brenna', 'Zed', 'Aliss'])
    with patch.object(chatter_guild_player, '_session_is_current',
                      return_value=True), \
            patch.object(chatter_guild_player, '_fetch_session_context',
                         return_value=(
                             'Brenna swore to find the lost caravan.',
                             [{'speaker_name': 'Rytsen', 'is_bot': 1,
                               'source_kind': 'reply',
                               'message': 'No sign of it.'}],
                         )), \
            patch.object(chatter_guild_player, 'find_addressed_bot',
                         return_value={'bot': 'Aliss',
                                       'multi_addressed': False,
                                       'brief_casual': False}), \
            patch.object(chatter_guild_player, '_generate_single_reply',
                         side_effect=capture), \
            patch.object(chatter_guild_player, '_reply_delays',
                         return_value=[0.0]), \
            patch.object(chatter_guild_player, 'insert_chat_message'), \
            patch.object(chatter_guild_player, '_mark_event'), \
            patch.object(chatter_guild_player, '_maybe_summarize_session',
                         return_value=False):
        chatter_guild_player.process_guild_player_message_event(
            db, object(), {}, event)
    context = captured['context']
    assert 'Brenna is female' in context        # only in the summary
    assert 'Rytsen is male' in context          # recent transcript
    assert 'Calwen (the player) is female' in context
    assert 'Zed' not in context                 # spoke, not mentioned
    assert 'Aliss is' not in context            # responder excluded


def test_session_speaker_lookup_closes_its_cursor():
    closed = []

    class Cursor(GenderCursor):
        def close(self):
            closed.append(True)

    class FailingCursor(Cursor):
        def execute(self, query, params=None):
            raise RuntimeError('db down')

    for cursor_cls, expected in ((Cursor, ['Brenna']), (FailingCursor, [])):
        db = GenderDB(None, session_speakers=['Brenna'])
        db.cursor = lambda *a, cls=cursor_cls, d=db, **k: cls(None, d)
        closed.clear()
        assert chatter_guild_player._session_speaker_names(
            db, 41, 'Brenna swore an oath.') == expected
        assert closed == [True]


def test_summary_update_names_previous_summary_speaker():
    inner = reply_tests._SummaryDb()

    class Cursor(reply_tests._SummaryCursor):
        def execute(self, query, params=None):
            super().execute(query, params)
            if 'SELECT summary' in query:
                self.one = {'summary': 'Brenna swore to find the caravan.',
                            'summarized_through_id': 0}

    inner.cursor = lambda *a, **k: Cursor(inner)
    db = GenderDB(inner, session_speakers=['Brenna', 'Zed'])
    prompts = []
    config = {
        'LLMChatter.GuildChatter.SessionMemory.Enable': '1',
        'LLMChatter.GuildChatter.SessionMemory.KeepRecentMessages': 4,
        'LLMChatter.GuildChatter.SessionMemory.SummaryThresholdChars': 500,
        'LLMChatter.GuildChatter.SessionMemory.SummaryMaxInputChars': 500,
    }

    def fake_call(client, prompt, cfg, **kwargs):
        prompts.append(_text(prompt))
        return json.dumps({'message': 'Brenna and Calwen seek it.'})

    with patch.object(chatter_guild_player, 'call_llm',
                      side_effect=fake_call):
        chatter_guild_player._maybe_summarize_session(
            db, object(), config, 41)
    assert 'Brenna is female' in prompts[0]
    assert 'Calwen is female' in prompts[0]
    assert 'Zed' not in prompts[0]


# ------------------------------------------------------------
# Guild events
# ------------------------------------------------------------
def test_rank_officer_gender_by_guid():
    subject = {'name': 'Bran', 'guid': 102, 'is_bot': True,
               'online': True, 'speaker': {'race': 'Orc',
                                           'class': 'Warrior',
                                           'gender': 'male'}}
    extra = {'changes': [{'member_guid': 102, 'old_rank': 4,
                          'new_rank': 3, 'direction': 'promotion',
                          'actor_guid': 501, 'actor_name': 'Calia'}]}
    with patch.object(chatter_guild_events, '_load_subject',
                      return_value=subject), \
            patch.object(chatter_guild_events, '_real_player_lines',
                         return_value=[]), \
            patch.object(chatter_guild_events, 'rank_name',
                         side_effect=lambda p, r: f"Rank {r}"):
        scenario = chatter_guild_events._rank_scenario(
            GenderDB(), extra, {}, 'roleplay')[0]
    assert any('Calia is female' in line for line in scenario)


def test_newcomer_reply_states_heard_speakers():
    captured = {}

    def fake_build(speakers, *args, **kwargs):
        captured['scenario'] = args[4]
        return 'prompt', ['Bran']

    subject = {'name': 'Bran', 'guid': 102, 'is_bot': True,
               'online': True, 'speaker': {'race': 'Orc', 'team': 'Horde'}}
    messages = [{'name': 'Aliss', 'message': 'Welcome!'},
                {'name': 'Bran', 'message': 'Thanks.'}]
    with patch.object(chatter_guild_events, '_speaker_faction',
                      return_value='Horde'), \
            patch.object(chatter_guild_events.random, 'randint',
                         return_value=1), \
            patch.object(chatter_guild_events, 'prepare_guild_speakers',
                         side_effect=lambda d, c, cfg, s: s), \
            patch.object(chatter_guild_events, 'build_prompt',
                         side_effect=fake_build), \
            patch.object(chatter_guild_events, 'generate',
                         return_value=[]):
        chatter_guild_events._subject_reply(
            GenderDB(), None, {}, 1, 'guild_member_join',
            {'team': 'Horde'}, subject, 'Bran joined.', messages, [],
            'JoinReplyChance', {},
        )
    assert any('Aliss is female' in line for line in captured['scenario'])
    assert not any('Bran is' in line for line in captured['scenario'])


def test_meet_post_states_player_gender():
    lines = chatter_guild_world_events._meet_guild_scenario(
        {'bot_name': 'Aliss', 'player_name': 'Calwen',
         'player_gender': 'female'}, 'Well met!')
    assert 'Genders: Calwen is female.' in ' '.join(lines)
    plain = chatter_guild_world_events._meet_guild_scenario(
        {'bot_name': 'Aliss', 'player_name': 'Calwen'}, 'Well met!')
    assert 'Genders' not in ' '.join(plain)


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} Guild gender checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
