#!/usr/bin/env python3
"""Group awareness in Guild chatter and the zone-intrusion defender
(issue #94, part 3).

Covers each outlet's prompt: unchanged without a grouped speaker, the
presence block for a grouped one. Outlets: guild player reply (single
and multi), guild login greeting (single and multi), guild member
events (commenters and the subject's reply), idle guild statement and
conversation, the guild meet greeting (/say greeting and guild post)
and the intrusion yell. Also checks the C++ payload wiring.

Run directly from the module root:
  python tools/tests/test_guild_group_presence.py
"""

import json
import random
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_guild_conversations as conv_tests  # noqa: E402  stubs + path
import test_guild_player_replies as reply_tests  # noqa: E402

import chatter_events  # noqa: E402
import chatter_guild  # noqa: E402
import chatter_guild_events  # noqa: E402
import chatter_guild_login  # noqa: E402
import chatter_guild_player  # noqa: E402
import chatter_guild_world_events  # noqa: E402
import chatter_party_presence as presence  # noqa: E402
import chatter_threads as th  # noqa: E402
from test_guild_genders import GenderDB  # noqa: E402
from test_party_presence import NOW, group  # noqa: E402

MODULE_ROOT = Path(__file__).resolve().parents[2]
HEADER = 'What each speaker knows about their own group'
GUILD_TAIL = 'This is guild chat: others can hear.'
# No real player in the group: the block needs no history queries.
GROUP = group(real=False)


def _text(prompt):
    return getattr(prompt, 'user_prompt', str(prompt))


def _groups(*guids):
    return {'bot_groups': {str(g): GROUP for g in guids}}


def _assert_block_tail(base, grouped, speaker):
    assert HEADER not in base
    assert grouped.startswith(base), 'block is appended, nothing else'
    tail = grouped[len(base):]
    assert tail.startswith('\n' + HEADER), tail[:80]
    assert f'- {speaker} (Thunder Bluff, Mulgore): in a party' in tail
    return tail


def _clock():
    return patch.object(presence.time, 'time', return_value=NOW)


# ------------------------------------------------------------
# Guild player replies
# ------------------------------------------------------------
def _player_reply_prompts(generator, participants, extra):
    random.seed(94)
    prompts = []

    def llm(client, prompt, *args, **kwargs):
        prompts.append(_text(prompt))
        return None

    args = (
        GenderDB(), None, {}, 77,
    )
    tail = (
        'Keepers', 'Alliance', 'Calwen', 'What became of the caravan?',
        '', False, False, False, {'guild_brief_casual': False},
    )
    with _clock(), patch.object(chatter_guild_player, 'call_llm',
                                side_effect=llm):
        if generator == 'single':
            chatter_guild_player._generate_single_reply(
                *args, participants[0], *tail, presence_extra=extra)
        else:
            chatter_guild_player._generate_multi_reply(
                *args, participants, 'chain', *tail,
                presence_extra=extra)
    return prompts


def test_guild_player_single_reply():
    aliss = reply_tests._candidate(101, 'Aliss')
    base = _player_reply_prompts('single', [aliss], None)
    assert _player_reply_prompts('single', [aliss], {}) == base
    assert _player_reply_prompts('single', [aliss], _groups(102)) == base
    grouped = _player_reply_prompts('single', [aliss], _groups(101))
    tail = _assert_block_tail(base[0], grouped[0], 'Aliss')
    assert GUILD_TAIL in tail
    # The repair prompt is built on the grouped prompt.
    assert len(grouped) == 2 and HEADER in grouped[1]


def test_guild_player_multi_reply_names_outsider():
    people = [reply_tests._candidate(101, 'Aliss'),
              reply_tests._candidate(102, 'Rytsen')]
    base = _player_reply_prompts('multi', people, None)
    grouped = _player_reply_prompts('multi', people, _groups(102))
    tail = _assert_block_tail(base[0], grouped[0], 'Rytsen')
    assert 'Aliss knows none of this.' in tail


def test_guild_player_process_passes_extra():
    source = (MODULE_ROOT / 'tools' / 'chatter_guild_player.py'
              ).read_text(encoding='utf-8')
    assert source.count('presence_extra=extra,') == 3


# ------------------------------------------------------------
# Guild login greeting
# ------------------------------------------------------------
def _login_prompts(generator, participants, extra):
    random.seed(94)
    prompts = []

    def llm(client, prompt, *args, **kwargs):
        prompts.append(_text(prompt))
        return None

    tail = ('Keepers', 'Alliance', 'Calwen', False, 150, {})
    with _clock(), patch.object(chatter_guild_login, 'call_llm',
                                side_effect=llm):
        target = participants[0] if generator == 'single' else participants
        fn = (chatter_guild_login._generate_single
              if generator == 'single'
              else chatter_guild_login._generate_multi)
        fn(None, {}, 78, target, *tail, db=GenderDB(),
           presence_extra=extra)
    return prompts


def test_guild_login_greetings():
    aliss = reply_tests._candidate(101, 'Aliss')
    rytsen = reply_tests._candidate(102, 'Rytsen')
    base = _login_prompts('single', [aliss], None)
    assert _login_prompts('single', [aliss], _groups(102)) == base
    _assert_block_tail(
        base[0], _login_prompts('single', [aliss], _groups(101))[0],
        'Aliss')
    base = _login_prompts('multi', [aliss, rytsen], None)
    grouped = _login_prompts('multi', [aliss, rytsen], _groups(101))
    tail = _assert_block_tail(base[0], grouped[0], 'Aliss')
    assert 'Rytsen knows none of this.' in tail
    source = (MODULE_ROOT / 'tools' / 'chatter_guild_login.py'
              ).read_text(encoding='utf-8')
    assert source.count('presence_extra=extra,') == 3


# ------------------------------------------------------------
# Guild member events
# ------------------------------------------------------------
def test_guild_member_event_helper_and_subject_reply():
    speakers = [{'guid': 101, 'name': 'Aliss'},
                {'guid': 102, 'name': 'Bran'}]
    with _clock():
        assert chatter_guild_events._with_presence(
            'P', GenderDB(), {}, {}, speakers) == 'P'
        text = chatter_guild_events._with_presence(
            'P', GenderDB(), {}, _groups(102), speakers)
    _assert_block_tail('P', text, 'Bran')
    assert 'Aliss knows none of this.' in text

    captured = []

    def generate(client, config, event_id, event_type, prompt, *a):
        captured.append(_text(prompt))
        return []

    subject = {'name': 'Bran', 'guid': 102, 'is_bot': True,
               'online': True, 'speaker': {'race': 'Orc'}}
    messages = [{'name': 'Aliss', 'message': 'Welcome!'}]
    with ExitStack() as stack:
        stack.enter_context(_clock())
        for name, value in {
            '_speaker_faction': lambda *a: 'Horde',
            'prepare_guild_speakers': lambda d, c, cfg, s: s,
            'build_prompt': lambda *a, **kw: ('SUBJECT PROMPT', ['Bran']),
            'generate': generate,
        }.items():
            stack.enter_context(
                patch.object(chatter_guild_events, name, value))
        stack.enter_context(patch.object(
            chatter_guild_events.random, 'randint', return_value=1))
        for extra in ({'team': 'Horde'},
                      dict(_groups(102), team='Horde')):
            chatter_guild_events._subject_reply(
                GenderDB(), None, {}, 1, 'guild_member_join', extra,
                dict(subject), 'Bran joined.', messages, [],
                'JoinReplyChance', {},
            )
    assert captured[0] == 'SUBJECT PROMPT'
    _assert_block_tail(captured[0], captured[1], 'Bran')
    source = (MODULE_ROOT / 'tools' / 'chatter_guild_events.py'
              ).read_text(encoding='utf-8')
    assert source.count(
        'prompt = _with_presence(prompt, db, config, extra, '
        'responders)') == 2


# ------------------------------------------------------------
# Idle guild chatter
# ------------------------------------------------------------
def _idle_prompts(names, bot_groups, mode='conversation'):
    random.seed(94)
    event = conv_tests._event(names)
    extra = json.loads(event['extra_data'])
    extra['mode'] = mode
    extra.update(bot_groups)
    event['extra_data'] = json.dumps(extra)
    prompts = []

    def llm(client, prompt, config, **kwargs):
        prompts.append(_text(prompt))
        if mode == 'statement':
            return json.dumps({'message': 'Quiet night.'})
        return conv_tests._conversation_response(names)

    th.reset_settings()
    th.configure_threads({'LLMChatter.Threads.SurpriseChance': 0})
    th.clear_all()
    try:
        with ExitStack() as stack:
            stack.enter_context(_clock())
            stack.enter_context(patch.object(
                chatter_guild, '_query_speaker',
                side_effect=lambda d, g: conv_tests._speaker(g)))
            stack.enter_context(patch.object(
                chatter_guild, 'call_llm', side_effect=llm))
            stack.enter_context(patch.object(
                chatter_guild, 'insert_chat_message'))
            stack.enter_context(patch.object(
                chatter_guild, 'select_conversation_message_count',
                return_value=2))
            stack.enter_context(patch.object(
                chatter_guild, 'calculate_dynamic_delay',
                return_value=5.0))
            stack.enter_context(patch.object(
                chatter_guild.random, 'choice',
                side_effect=lambda xs: list(xs)[0]))
            stack.enter_context(patch.object(
                chatter_guild.random, 'randint', return_value=100))
            stack.enter_context(patch.object(
                chatter_guild.random, 'random', return_value=0.99))
            chatter_guild.process_guild_idle_chatter_event(
                GenderDB(conv_tests._DB()), None, conv_tests._config(),
                event)
    finally:
        th.clear_all()
        th.reset_settings()
    return prompts


def test_idle_statement_and_conversation():
    base = _idle_prompts(['Aliss'], {}, mode='statement')
    grouped = _idle_prompts(['Aliss'], _groups(100), mode='statement')
    _assert_block_tail(base[0], grouped[0], 'Aliss')
    base = _idle_prompts(['Aliss', 'Bran'], {})
    assert _idle_prompts(['Aliss', 'Bran'], {'bot_groups': {}}) == base
    grouped = _idle_prompts(['Aliss', 'Bran'], _groups(101))
    tail = _assert_block_tail(base[0], grouped[0], 'Bran')
    assert 'Aliss knows none of this.' in tail


# ------------------------------------------------------------
# Meet greeting
# ------------------------------------------------------------
MEET_EXTRA = {
    'guild_id': 9, 'guild_name': 'Keepers', 'team': 'Alliance',
    'bot_guid': 101, 'bot_name': 'Aliss', 'player_guid': 7,
    'player_name': 'Calwen', 'zone_id': 12,
}


def _meet_prompts(extra):
    random.seed(94)
    prompts = []

    def run(client, config, prompt, *args, **kwargs):
        prompts.append(_text(prompt))
        return []

    with ExitStack() as stack:
        stack.enter_context(_clock())
        for name, value in {
            '_config_enabled': lambda *a: True,
            '_participant': lambda db, extra, prefix='bot': {
                'guid': 101, 'name': 'Aliss', 'zone_id': 12,
                'map_id': 0, 'speaker': conv_tests._speaker(101)},
            '_prepared': lambda db, c, cfg, bot, *a: bot,
            'build_meet_greeting_prompt': lambda *a: 'GREETING PROMPT',
            'run_single_prompt': run,
            '_mark_event': lambda *a: None,
        }.items():
            stack.enter_context(
                patch.object(chatter_guild_world_events, name, value))
        chatter_guild_world_events.process_guild_meet_greeting_event(
            GenderDB(), None, {},
            {'id': 5, 'extra_data': json.dumps(extra)})
        chatter_guild_world_events._meet_follow_up_text(
            GenderDB(), None, {}, 5, extra,
            {'guid': 101, 'name': 'Aliss', 'speaker':
             conv_tests._speaker(101)}, 'roleplay', 'Well met!')
    return prompts


def test_meet_greeting_and_guild_post():
    base = _meet_prompts(MEET_EXTRA)
    assert base[0] == 'GREETING PROMPT'
    grouped = _meet_prompts(dict(MEET_EXTRA, **_groups(101)))
    tail = _assert_block_tail(base[0], grouped[0], 'Aliss')
    assert 'This is open /say: others can hear.' in tail
    tail = _assert_block_tail(base[1], grouped[1], 'Aliss')
    assert GUILD_TAIL in tail


# ------------------------------------------------------------
# Zone intrusion defender
# ------------------------------------------------------------
def _intrusion_prompt(extra):
    captured = {}

    def reaction(db, client, config, **kwargs):
        captured['prompt'] = _text(kwargs['prompt'])
        return {'ok': True}

    with ExitStack() as stack:
        stack.enter_context(_clock())
        stack.enter_context(patch.object(
            chatter_events, 'build_zone_intrusion_prompt',
            return_value='YELL PROMPT'))
        stack.enter_context(patch.object(
            chatter_events, 'run_single_reaction', side_effect=reaction))
        chatter_events.process_zone_intrusion_event(
            GenderDB(), None, {}, {'id': 9, 'extra_data': json.dumps(
                dict({'defender_guid': 501, 'defender_name': 'Aliss',
                      'intruder_name': 'Zed'}, **extra))})
    return captured['prompt']


def test_intrusion_defender():
    assert _intrusion_prompt({}) == 'YELL PROMPT'
    assert _intrusion_prompt(_groups(502)) == 'YELL PROMPT'
    tail = _assert_block_tail(
        'YELL PROMPT', _intrusion_prompt(_groups(501)), 'Aliss')
    assert 'This is a yell across the zone: others can hear.' in tail


# ------------------------------------------------------------
# C++ payload wiring
# ------------------------------------------------------------
def _src(name):
    return (MODULE_ROOT / 'src' / name).read_text(encoding='utf-8')


def test_cpp_payload_wiring():
    guild = _src('LLMChatterGuild.cpp')
    assert guild.count('AppendCandidateGroups(extraData, bots);') == 2
    members = _src('LLMChatterGuildMembers.cpp')
    queue = members.split('void QueueGuildMemberEvent(', 1)[1]
    queue = queue.split('\n}\n', 1)[0]
    assert 'AppendCandidateGroups(extraData, speakers);' in queue
    assert 'IsPlayerBot(subject)' in queue
    assert queue.index('BuildGuildEventCandidatesJson(bots)') \
        < queue.index('AppendCandidateGroups(extraData, speakers)') \
        < queue.index('EscapeString(extraData)')
    assert 'GuildMemberName(present.front()),\n        present);' in members
    assert ('GuildMemberName(subjects.front()),\n        subjects);'
            in members)
    world = _src('LLMChatterWorld.cpp')
    idle = world.index('AppendCandidateGroups(json, participants);')
    assert idle < world.index('"guild_idle_chatter",', idle)
    meet = _src('LLMChatterGuildWorld.cpp')
    at = meet.index('AppendCandidateGroups(json, {bot});')
    assert at < meet.index('"guild_meet_greeting", bot,', at)
    player = _src('LLMChatterPlayer.cpp')
    assert player.count('AppendCandidateGroups(extraData, {defender});') \
        == 2
    for text in (guild, members, meet, player, world):
        assert '#include "LLMChatterGroupAwareness.h"' in text


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        presence.reset_state()
        test()
    print(f"{len(tests)} Guild group awareness checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
