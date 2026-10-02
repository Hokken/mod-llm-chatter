#!/usr/bin/env python3
"""Guild identity and context checks: guild profile, guild names in
prompts, guildmate notes, the real player's description, MOTD and zone
topics in Guild chat, and guild talk in General.

Run directly from the module root:
  python tools/tests/test_guild_identity.py
"""

import importlib
import json
import re
import sys
import types
from pathlib import Path
from unittest.mock import patch


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_non_strict_stubs() -> None:
    for module_name in ("anthropic", "openai"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            module = _ensure_module(module_name)
            class_name = (
                "Anthropic"
                if module_name == "anthropic"
                else "OpenAI"
            )
            setattr(module, class_name, type(class_name, (), {}))

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module("mysql.connector")
        setattr(mysql_module, "connector", connector_module)


TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_guild  # noqa: E402
import chatter_guild_profile  # noqa: E402
import chatter_player_context as pc  # noqa: E402
from chatter_threads import IdleTurn  # noqa: E402

RP = {'LLMChatter.ChatterMode': 'roleplay'}


def _turn(source, pool_topic=None, prompt_block=''):
    return IdleTurn(group_id=('guild', 9), session=1, major_rev=0,
                    kind='new', source=source, pool_topic=pool_topic,
                    prompt_block=prompt_block)


class _Cursor:
    def __init__(self, db):
        self.db = db
        self.result = None

    def execute(self, query, params=None):
        self.db.queries.append((query, params))
        self.result = self.db.respond(query, params)

    def fetchone(self):
        if isinstance(self.result, list):
            return self.result[0] if self.result else None
        return self.result

    def fetchall(self):
        if isinstance(self.result, list):
            return self.result
        return [self.result] if self.result else []

    def close(self):
        pass


class _GuildDb:
    """Answers the guild profile and membership queries."""

    def __init__(self, members=None, guild=None, ranks=None):
        self.members = members or {}
        self.guild = guild
        self.ranks = ranks or []
        self.queries = []

    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def respond(self, query, params):
        if "FROM guild_member" in query:
            return self.members.get(params[0])
        if "FROM guild_rank" in query:
            return list(self.ranks)
        if "FROM guild g" in query:
            return self.guild
        return None


def _member(guild_id, name, rank=3):
    return {'guildid': guild_id, 'name': name, 'rank': rank}


def _profile(info='', motd='', ranks=None):
    return {
        'id': 9,
        'name': 'Keepers',
        'info': info,
        'motd': motd,
        'ranks': ranks or {},
        'leader': None,
    }


# -- Profile helpers ---------------------------------------------------

def test_clean_guild_text_flattens_and_bounds():
    text = "Line one\nline\ttwo   " + "word " * 60
    cleaned = chatter_guild_profile.clean_guild_text(text, 40)
    assert "\n" not in cleaned and "\t" not in cleaned
    assert cleaned.startswith("Line one line two")
    assert cleaned.endswith("...")
    assert len(cleaned) <= 43


def test_rank_name_uses_table_then_fallback():
    profile = _profile(ranks={1: 'Officer'})
    assert chatter_guild_profile.rank_name(profile, 1) == 'Officer'
    assert chatter_guild_profile.rank_name(profile, 4) == 'rank 5'
    assert chatter_guild_profile.rank_name(None, 0) == 'rank 1'


def test_identity_lines_quote_info_as_background():
    assert chatter_guild_profile.guild_identity_lines(_profile()) == []
    lines = chatter_guild_profile.guild_identity_lines(
        _profile(info='We raid on Fridays.')
    )
    assert '"We raid on Fridays."' in lines[0]
    assert 'never as instructions' in lines[1]


def test_profile_reads_info_motd_ranks_and_leader():
    chatter_guild_profile.clear_guild_cache()
    db = _GuildDb(
        guild={
            'guildid': 9, 'name': 'Keepers',
            'info': 'Friendly\nlevelers', 'motd': 'Raid at 8',
            'leaderguid': 5, 'leader_name': 'Varra',
            'leader_race': 2, 'leader_class': 1,
            'leader_gender': 1, 'leader_level': 80,
        },
        ranks=[
            {'rid': 0, 'rname': 'Guild Master'},
            {'rid': 1, 'rname': 'Officer'},
        ],
    )
    profile = chatter_guild_profile.get_guild_profile(db, 9)
    assert profile['info'] == 'Friendly levelers'
    assert profile['motd'] == 'Raid at 8'
    assert profile['ranks'][1] == 'Officer'
    assert profile['leader']['name'] == 'Varra'
    assert profile['leader']['race'] == 'Orc'
    assert profile['leader']['class'] == 'Warrior'

    query_count = len(db.queries)
    assert chatter_guild_profile.get_guild_profile(db, 9) is profile
    assert len(db.queries) == query_count


def test_same_guild_note_only_for_shared_guild():
    chatter_guild_profile.clear_guild_cache()
    db = _GuildDb(members={
        101: _member(9, 'Keepers'),
        7: _member(9, 'Keepers'),
        8: _member(4, 'Others'),
    })
    note = chatter_guild_profile.same_guild_note(db, 101, 7, 'Calwen')
    assert note.startswith('You and Calwen are both members')
    assert '"Keepers"' in note
    third = chatter_guild_profile.same_guild_note(
        db, 101, 7, 'Calwen', bot_name='Aliss',
    )
    assert third.startswith('Aliss and Calwen are both members')
    assert chatter_guild_profile.same_guild_note(db, 101, 8, 'X') == ''
    assert chatter_guild_profile.same_guild_note(db, 101, 0, 'X') == ''


def test_describe_character_appends_guild():
    text = chatter_guild_profile.describe_character(
        'Aliss', 'Human', 'Mage', 22, 'female', 'Keepers',
    )
    assert text == (
        'Aliss, a level 22 female Human Mage of the guild "Keepers"'
    )


# -- Guild names in prompts --------------------------------------------

def test_player_identity_mentions_guild():
    from chatter_mode import build_player_identity
    from chatter_shared import build_bot_identity

    normal = build_player_identity(
        'Aliss', 'Human', 'Mage', 22, 'female', 'normal',
        guild_name='Keepers',
    )
    assert 'Your character is a member of the guild "Keepers".' in normal
    roleplay = build_player_identity(
        'Aliss', 'Human', 'Mage', 22, 'female', 'roleplay',
        guild_name='Keepers',
    )
    assert 'You are a member of the guild "Keepers".' in roleplay
    assert 'guild' not in build_player_identity(
        'Aliss', 'Human', 'Mage', 22, 'female', 'normal',
    )
    assert 'member of the guild "Keepers"' in build_bot_identity(
        'Aliss', 'Human', 'Mage', 'female', guild_name='Keepers',
    )


def test_party_reply_prompt_carries_same_guild_note():
    from chatter_group_prompts import build_player_response_prompt

    bot = {
        'name': 'Aliss', 'class': 'Mage', 'race': 'Human',
        'level': 22, 'gender': 'female', 'guild_name': 'Keepers',
    }
    prompt = build_player_response_prompt(
        bot, ['steadfast'], 'Calwen', 'hi all', 'normal',
        guild_note='You and Calwen are both members of the guild.',
    )
    text = getattr(prompt, 'user_prompt', prompt)
    assert 'You and Calwen are both members of the guild.' in text
    assert 'member of the guild "Keepers"' in text


def test_proximity_same_guild_lines_skip_npcs():
    import chatter_proximity

    with patch.object(
        chatter_proximity, 'same_guild_note',
        side_effect=lambda db, bot, player, name, bot_name='':
            f"{bot_name or 'You'} and {name} share a guild.",
    ):
        lines = chatter_proximity._same_guild_lines(
            object(),
            {'player_guid': 7, 'player_name': 'Calwen'},
            [
                {'bot_guid': 101, 'name': 'Aliss'},
                {'is_npc': True, 'name': 'Guard'},
            ],
            third_person=True,
        )
    assert lines == ['Aliss and Calwen share a guild.']


def _ambient_prompt_text(build):
    import chatter_proximity as prox

    def note(db, bot, player, name, bot_name=''):
        return f"{bot_name or 'You'} and {name} share a guild."

    with patch.object(prox, 'same_guild_note', side_effect=note), \
            patch.object(prox, '_query_bot_traits', return_value={}), \
            patch.object(prox, '_query_bot_identity', return_value={}), \
            patch.object(prox, '_environment_lines', return_value=[]), \
            patch.object(prox, '_player_context_line',
                         return_value='The player Calwen is a level 30 '
                                      'female Orc Hunter.'), \
            patch.object(prox, '_player_lines',
                         return_value=['About Calwen: a female Orc '
                                       'Hunter.']):
        prompt = build(prox)
    return getattr(prompt, 'user_prompt', prompt)


SPEAKER = {'bot_guid': 101, 'name': 'Aliss', 'race': 'Orc',
           'class': 'Warrior', 'level': 30, 'gender': 'male'}


def test_ambient_proximity_say_notes_guildmate_and_player():
    extra = {'player_guid': 7, 'player_name': 'Calwen', 'zone_id': 0}
    quiet = _ambient_prompt_text(lambda prox: prox._single_prompt(
        object(), dict(extra), SPEAKER, 'the weather', config=RP))
    assert 'You and Calwen share a guild.' in quiet
    assert 'female Orc Hunter' in quiet
    assert 'About Calwen' not in quiet

    addressed = _ambient_prompt_text(lambda prox: prox._single_prompt(
        object(), dict(extra, player_addressed=True), SPEAKER,
        'the weather', config=RP))
    assert 'You and Calwen share a guild.' in addressed
    assert 'About Calwen: a female Orc Hunter.' in addressed


def test_ambient_proximity_conversation_notes_guildmate():
    extra = {'player_guid': 7, 'player_name': 'Calwen', 'zone_id': 0,
             'player_addressed': True}
    other = dict(SPEAKER, bot_guid=102, name='Brakk')
    text = _ambient_prompt_text(lambda prox: prox._conversation_prompt(
        object(), extra, [SPEAKER, other], config=RP))
    assert 'Aliss and Calwen share a guild.' in text
    assert 'Brakk and Calwen share a guild.' in text
    assert 'About Calwen: a female Orc Hunter.' in text


# -- The real player's description -------------------------------------

def test_player_description_roleplay_and_normal():
    rp = pc.player_character_lines(
        None, 0, 'Lyn', 'roleplay',
        race='Orc', class_name='Hunter', gender='female')
    text = '\n'.join(rp)
    assert rp[0].startswith('About Lyn, the real player')
    assert 'a female Orc Hunter.' in rp[0]
    assert 'Orc outlook:' in text
    assert 'Hunter calling:' in text
    assert 'never recite it' in text
    normal = pc.player_character_lines(
        None, 0, 'Lyn', 'normal', race='Undead', class_name='Mage')
    assert normal == ['Lyn (the real player) plays an Undead Mage.']
    assert pc.player_character_lines(
        None, 0, 'Lyn', 'roleplay', race='Unknown', class_name='Mage') == []
    assert pc.player_character_lines(
        None, 0, 'Lyn', 'roleplay', race='Orc', class_name='') == []
    assert pc.player_character_lines(
        None, 0, '', 'roleplay', race='Orc', class_name='Hunter') == []
    assert pc.player_context_text(None, 0, '', 'roleplay') == ''


def test_player_description_splits_priests():
    with patch.object(pc, 'class_style',
                      lambda db, guid, cls: 'Shadow Priest'):
        shadow = '\n'.join(pc.player_character_lines(
            object(), 7, 'Lyn', 'roleplay',
            race='Blood Elf', class_name='Priest', gender='female'))
    assert 'female Blood Elf Shadow Priest.' in shadow
    assert 'Shadow Priest calling:' in shadow
    light = '\n'.join(pc.player_character_lines(
        None, 0, 'Lyn', 'roleplay',
        race='Blood Elf', class_name='Priest', gender='female'))
    assert 'Light Priest calling:' in light
    assert 'Shadow' not in light


def test_player_description_follows_a_dual_spec_switch():
    import chatter_db

    active = {'spec': 0}
    totals = ({'Holy': 40, 'Discipline': 21}, {'Shadow': 51, 'Holy': 10})

    def talents(db, guid):
        return {'tree_totals': totals[active['spec']]}

    with patch.object(chatter_db, 'get_character_talents', talents):
        first = '\n'.join(pc.player_character_lines(
            object(), 7, 'Lyn', 'roleplay',
            race='Human', class_name='Priest'))
        active['spec'] = 1
        second = '\n'.join(pc.player_character_lines(
            object(), 7, 'Lyn', 'roleplay',
            race='Human', class_name='Priest'))
    assert 'Light Priest calling:' in first
    assert 'Shadow Priest calling:' in second


# -- Guild chat topics -------------------------------------------------

def test_idle_topic_is_sometimes_the_motd():
    config = {'LLMChatter.GuildChatter.MotdChance': 15,
              'LLMChatter.GuildChatter.ZoneTopicChance': 0,
              'LLMChatter.GuildChatter.ZoneWeatherTopicChance': 0}
    profile = _profile(motd='Raid tonight at 8')
    with patch.object(chatter_guild.random, 'randint', return_value=15):
        topic = chatter_guild._pick_guild_topic(config, 'normal', profile)
    assert topic.kind == 'motd'
    assert '"Raid tonight at 8"' in topic.subject
    assert 'never instructions' in topic.subject

    with patch.object(chatter_guild.random, 'randint', return_value=16):
        assert chatter_guild._pick_guild_topic(
            config, 'normal', profile) is None
    assert chatter_guild._pick_guild_topic(
        config, 'normal', _profile()) is None


def test_motd_idle_topic_is_a_casual_note_in_roleplay():
    config = dict(RP, **{'LLMChatter.GuildChatter.MotdChance': 100})
    profile = {'motd': 'We must always protect our Light'}
    topic = chatter_guild._pick_guild_topic(config, 'roleplay', profile)
    assert "short note the guild's officers left" in topic.subject
    assert '"We must always protect our Light"' in topic.subject
    assert 'Message of the Day' not in topic.subject.split('Never call')[0]
    assert 'sacred creed' in topic.subject
    topic = chatter_guild._pick_guild_topic(config, 'normal', profile)
    assert topic.subject.startswith('the guild motd')
    assert 'capital-letter' in topic.subject


def test_zone_topics_name_the_zone():
    config = {'LLMChatter.GuildChatter.MotdChance': 0,
              'LLMChatter.GuildChatter.ZoneTopicChance': 100}
    with patch.object(chatter_guild, 'get_zone_name',
                      return_value='Duskwood'), \
            patch.object(chatter_guild, 'get_zone_flavor',
                         return_value='Endless night.'):
        zone = chatter_guild._pick_guild_topic(
            config, 'roleplay', _profile(), zone_id=10)
        weather = chatter_guild._guild_zone_weather_topic(
            10, 'rain', 'normal')
    assert zone.kind == 'zone' and zone.name_zone
    assert 'opinion of Duskwood' in zone.subject
    assert 'What Duskwood is like: Endless night.' in zone.lines
    assert weather.kind == 'zone_weather' and weather.name_zone
    assert any('the weather is rain' in line for line in weather.lines)
    assert any('the way a player would chat' in line
               for line in weather.lines)
    assert chatter_guild._guild_zone_topic(0, 'roleplay') is None


def test_guild_topic_enters_threads_only_through_the_pool():
    topic = chatter_guild.GuildTopic('motd', 'the MOTD', ['line'])
    assert chatter_guild._guild_topic_pool(topic, ['a', 'b']) == [
        'the MOTD']
    assert chatter_guild._guild_topic_pool(None, ['a', 'b']) == ['a', 'b']
    pool_turn = _turn('pool', 'the MOTD', '')
    persona_turn = _turn('persona', prompt_block='')
    assert chatter_guild._thread_used_topic(pool_turn, topic)
    assert not chatter_guild._thread_used_topic(persona_turn, topic)
    assert not chatter_guild._thread_used_topic(pool_turn, None)


def _run_statement(thread_turn, config):
    captured = {}

    def fake_llm(client, prompt, config, **kwargs):
        captured['prompt'] = prompt
        captured['metadata'] = kwargs.get('metadata')
        return None

    def fake_plan(key, names, topic_pool=None, db=None, **kwargs):
        captured['pool'] = list(topic_pool)
        return thread_turn

    speaker = {'race': 1, 'class': 8, 'level': 30, 'gender': 1,
               'traits': ['steadfast'], 'tone': 'dry'}
    event = {
        'id': 3, 'subject_guid': 11, 'subject_name': 'Aliss',
        'extra_data': json.dumps({
            'guild_id': 9, 'guild_name': 'Keepers', 'zone_id': 0,
        }),
    }
    with patch.object(chatter_guild, '_query_speaker',
                      return_value=dict(speaker)), \
            patch.object(chatter_guild, 'prepare_guild_speakers',
                         side_effect=lambda db, c, cfg, parts, prep:
                         parts), \
            patch.object(chatter_guild, 'get_guild_profile',
                         return_value=_profile(info='Friends first.',
                                               motd='Raid at 8')), \
            patch.object(chatter_guild, 'plan_idle_turn', fake_plan), \
            patch.object(chatter_guild, '_select_guild_history_context',
                         return_value=('', {})), \
            patch.object(chatter_guild, 'call_llm', fake_llm), \
            patch.object(chatter_guild, '_mark_event'):
        chatter_guild._process_guild_statement_event(
            object(), None, config, event)
    return captured


def test_statement_with_threads_uses_motd_only_from_the_pool():
    config = {'LLMChatter.ChatterMode': 'normal',
              'LLMChatter.GuildChatter.MotdChance': 100}
    motd_subject = chatter_guild._motd_topic(
        config, _profile(motd='Raid at 8'), 'normal')
    persona = _turn('persona', prompt_block='THREAD BLOCK')
    captured = _run_statement(persona, config)
    assert captured['pool'] == [motd_subject]
    assert 'THREAD BLOCK' in captured['prompt']
    assert 'Raid at 8' not in captured['prompt']
    assert captured['metadata']['guild_motd_topic'] is False
    assert '"Friends first."' in captured['prompt']

    pool = _turn('pool', motd_subject, 'POOL BLOCK')
    captured = _run_statement(pool, config)
    assert captured['metadata']['guild_motd_topic'] is True


def test_statement_without_threads_uses_the_motd_directly():
    config = {'LLMChatter.ChatterMode': 'normal',
              'LLMChatter.GuildChatter.MotdChance': 100}
    captured = _run_statement(None, config)
    assert 'Raid at 8' in captured['prompt']
    assert captured['metadata']['guild_motd_topic'] is True
    assert captured['metadata']['guild_info_included'] is True


def test_guild_statement_prompt_includes_info():
    prompt = chatter_guild._build_guild_prompt(
        'Aliss',
        {'race': 'Human', 'class': 'Mage', 'level': 22},
        'Keepers',
        '',
        {'LLMChatter.ChatterMode': 'normal'},
        topic='weather',
        guild_context=chatter_guild_profile.guild_identity_lines(
            _profile(info='We raid on Fridays.')
        ),
    )
    text = getattr(prompt, 'user_prompt', prompt)
    assert '"We raid on Fridays."' in text


# -- General channel ---------------------------------------------------

def test_general_praise_can_include_guild_master():
    import chatter_ambient

    profile = _profile(info='Friends first.')
    profile['leader'] = {
        'guid': 5, 'name': 'Varra', 'race': 'Orc', 'class': 'Warrior',
    }
    with (
        patch.object(
            chatter_ambient, 'get_character_guild',
            return_value={'id': 9, 'name': 'Keepers', 'rank': 3},
        ),
        patch.object(
            chatter_ambient, 'get_guild_profile', return_value=profile,
        ),
        patch.object(chatter_ambient.random, 'randint', return_value=1),
    ):
        topic = chatter_ambient._guild_praise_topic(
            object(), {}, {'guid': 101, 'name': 'Aliss'},
        )
        own_leader = chatter_ambient._guild_praise_topic(
            object(), {}, {'guid': 5, 'name': 'Varra'},
        )
    assert 'praising your own guild "Keepers"' in topic
    assert 'Guild Master Varra, an Orc Warrior' in topic
    assert '"Friends first."' in topic
    assert 'Guild Master' not in own_leader

    with patch.object(chatter_ambient.random, 'randint', return_value=9):
        assert chatter_ambient._guild_praise_topic(
            object(), {}, {'guid': 101},
        ) == ''


def test_general_discussion_needs_two_guilded_speakers():
    import chatter_ambient

    bots = [
        {'guid': 1, 'name': 'Aliss', 'guild_name': 'Keepers'},
        {'guid': 2, 'name': 'Bran', 'guild_name': 'Wardens'},
        {'guid': 3, 'name': 'Cato', 'guild_name': ''},
    ]
    with patch.object(chatter_ambient.random, 'randint', return_value=1):
        topic = chatter_ambient._guild_discussion_topic(
            object(), {}, bots,
        )
        lonely = chatter_ambient._guild_discussion_topic(
            object(), {}, bots[1:],
        )
    assert 'Aliss belongs to "Keepers"' in topic
    assert 'Bran belongs to "Wardens"' in topic
    assert 'Cato has no guild' in topic
    assert lonely == ''


def test_general_guild_topic_respects_thread_sources():
    import chatter_ambient

    pool = _turn('pool', 'praise', '')
    persona = _turn('persona', prompt_block='')
    assert chatter_ambient._guild_topic_used('praise', None)
    assert chatter_ambient._guild_topic_used('praise', pool)
    assert not chatter_ambient._guild_topic_used('praise', persona)
    assert not chatter_ambient._guild_topic_used('', None)


# -- Wiring ------------------------------------------------------------

def test_cpp_sends_guids_and_weather():
    emote = (MODULE_DIR / 'src' / 'LLMChatterGroupEmote.cpp').read_text(
        encoding='utf-8')
    assert emote.count('\\"player_guid\\":') >= 2
    assert '\\"target_guid\\":' in emote
    world = (MODULE_DIR / 'src' / 'LLMChatterWorld.cpp').read_text(
        encoding='utf-8')
    assert 'R"("weather":"{}"}})"' in world
    assert 'GetZoneWeatherName(' in world


def test_config_defaults():
    conf = MODULE_DIR / 'conf'
    dist = (conf / 'mod_llm_chatter.conf.dist').read_text(encoding='utf-8')
    quiet = (conf / 'presets' / 'mod_ll_chatter_quieter.conf.dist').read_text(
        encoding='utf-8')
    expected = {
        'LLMChatter.GuildChatter.MotdChance': (15, 15),
        'LLMChatter.GuildChatter.ZoneTopicChance': (10, 10),
        'LLMChatter.GuildChatter.ZoneWeatherTopicChance': (8, 8),
        'LLMChatter.GuildChatter.GeneralDiscussionChance': (10, 5),
        'LLMChatter.GuildChatter.GeneralPraiseChance': (8, 4),
        'LLMChatter.GuildChatter.GeneralPraiseMasterChance': (50, 50),
    }
    for key, (dist_value, quiet_value) in expected.items():
        for text, value in ((dist, dist_value), (quiet, quiet_value)):
            match = re.search(rf'^{re.escape(key)} = (\d+)', text, re.M)
            assert match and int(match.group(1)) == value, key


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} guild identity tests passed")
