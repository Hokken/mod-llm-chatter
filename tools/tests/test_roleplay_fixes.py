#!/usr/bin/env python3
"""Roleplay and chat fixes: playerbot broadcast suppression, slang ban,
in-world trade prices, level-up praise, link-safe cleanup, PvP factions,
bot visibility for guild world events and the frequency defaults.

Run directly from the module root:
  python tools/tests/test_roleplay_fixes.py
"""

import importlib
import json
import re
import sys
import types
from pathlib import Path


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
                "Anthropic" if module_name == "anthropic" else "OpenAI"
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
SRC = MODULE_DIR / 'src'
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_bg_prompts  # noqa: E402
import chatter_guild_world_events as world  # noqa: E402
import chatter_prompts  # noqa: E402
import chatter_themed_topics as themed  # noqa: E402
from chatter_group_prompts import (  # noqa: E402
    CLASS_GROWTH,
    build_levelup_reaction_prompt,
)
from chatter_shared import (  # noqa: E402
    cleanup_message,
    faction_war_line,
    format_price_words,
    number_to_words,
    replace_placeholders,
    spell_out_numbers,
)
from chatter_text import shorten_chat_message  # noqa: E402

RP = {'LLMChatter.ChatterMode': 'roleplay'}
SELLER = {
    'name': 'Annata', 'class': 'Warlock', 'race': 'Undead',
    'gender': 'female', 'zone': 'Tirisfal Glades',
}
POTION = {
    'item_name': 'Superior Mana Potion', 'item_quality': 1,
    'item_count': 10, 'sell_price': 400,
}
REACTOR = {
    'name': 'Kizia', 'race': 'Troll', 'class': 'Shaman',
    'gender': 'female',
}
FORTITUDE_LINK = '|cff71d5ff|Hspell:1243|h[Power Word: Fortitude]|h|r'


def _read(name: str) -> str:
    return (SRC / name).read_text(encoding='utf-8')


# -- Playerbot broadcasts and slang --------------------------------------

def test_roleplay_suppresses_playerbot_broadcasts():
    config = _read('LLMChatterConfig.cpp')
    assert '"LLMChatter.Roleplay.SuppressPlayerbotBroadcasts", true' in config
    world_src = _read('LLMChatterWorld.cpp')
    assert 'sPlayerbotAIConfig.enableBroadcasts' in world_src
    assert 'ApplyPlayerbotBroadcastPolicy' in world_src
    dist = (MODULE_DIR / 'conf' / 'mod_llm_chatter.conf.dist').read_text(
        encoding='utf-8')
    assert 'LLMChatter.Roleplay.SuppressPlayerbotBroadcasts = 1' in dist


def test_roleplay_guidelines_ban_player_slang():
    rp = chatter_prompts.build_dynamic_guidelines(config=RP, mode='roleplay')
    normal = chatter_prompts.build_dynamic_guidelines(config={}, mode='normal')
    assert any('bis' in g and 'Azeroth' in g for g in rp)
    assert not any('Never use player, trade' in g for g in normal)


# -- Trade --------------------------------------------------------------

def test_price_words():
    assert number_to_words(0) == 'zero'
    assert number_to_words(42) == 'forty-two'
    assert number_to_words(1015) == 'one thousand and fifteen'
    assert format_price_words(400) == 'four silver coins'
    assert format_price_words(12000) == 'one gold and twenty silver coins'
    assert format_price_words(10203) == (
        'one gold, two silver and three copper coins')
    assert format_price_words(0) == ''


def test_spell_out_numbers_keeps_links():
    link = '|cFFffffff|Hitem:1710:0:0:0:0:0:0:0|h[Greater Healing Potion]|h|r'
    assert spell_out_numbers(f'Ten {link} for 1g20s') == (
        f'Ten {link} for one gold and twenty silver')
    assert spell_out_numbers('2g 50s for 10 of them') == (
        'two gold and fifty silver for ten of them')
    assert spell_out_numbers('yours for 45 silver') == (
        'yours for forty-five silver')


def test_roleplay_trade_prompts_speak_in_world():
    for prompt in (
        chatter_prompts.build_trade_statement_prompt(
            SELLER, POTION, config=RP),
        chatter_prompts.build_trade_conversation_prompt(
            [SELLER, dict(SELLER, name='Borin', race='Orc')], POTION,
            config=RP),
    ):
        assert 'Vendor sell price: four silver coins' in prompt
        assert 'Write every number as words' in prompt
        assert 'Trade abbreviations' not in prompt
        assert '1g20s' not in prompt
    normal = chatter_prompts.build_trade_statement_prompt(
        SELLER, POTION, config={})
    assert 'Vendor sell price: 4s' in normal
    assert 'Trade abbreviations encouraged' in normal


# -- Level-up ------------------------------------------------------------

def test_roleplay_levelup_praises_growth_without_levels():
    prompt = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Brand', 25, True, 'roleplay',
        leveler_race='Human', leveler_class='Warrior')
    assert CLASS_GROWTH['Warrior'] in prompt
    assert '25' not in prompt
    assert 'Never mention levels' in prompt
    normal = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Brand', 25, True, 'normal')
    assert 'level 25' in normal


def test_levelup_splits_shadow_and_light_priests():
    shadow = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Lyn', 30, True, 'roleplay',
        leveler_race='Blood Elf', leveler_class='Priest',
        leveler_style='Shadow Priest')
    assert 'merged deeper with the Void' in shadow
    assert 'shadows gather' in shadow
    light = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Lyn', 30, True, 'roleplay',
        leveler_race='Blood Elf', leveler_class='Priest')
    assert 'Holy Light flows' in light
    assert 'Void' not in light.split('Lyn, a')[1].split('\n')[0]


TELIRIAH_SPELLS = [15286, 15310, 15311, 15314, 15328, 15332, 15336, 15338,
                   15407, 15473, 33215, 33224, 33371, 63627]


class _TalentDb:
    """Answers the two queries get_character_talents() runs."""

    def __init__(self, active_spec, rows):
        self.active_spec = active_spec
        self.rows = rows

    def cursor(self, *args, **kwargs):
        db = self

        class Cursor:
            def execute(self, sql, params=()):
                self.sql, self.params = sql, params

            def fetchone(self):
                return {'activeTalentGroup': db.active_spec}

            def fetchall(self):
                spec = self.params[1]
                return [{'spell': spell} for spell, mask in db.rows
                        if mask & (1 << spec)]

        return Cursor()


def test_talent_data_covers_every_tree():
    from talent_data import TALENT_SPELLS, TALENT_TABS
    assert len(TALENT_TABS) == 33
    assert [TALENT_TABS[i]['name'] for i in (201, 202, 203)] == [
        'Discipline', 'Holy', 'Shadow']
    assert len(TALENT_SPELLS) > 2000
    assert TALENT_SPELLS[15407]['name'] == 'Mind Flay'
    assert not any('\\' in s['name'] for s in TALENT_SPELLS.values())


def test_talents_resolve_without_talent_dbc():
    import chatter_db
    import chatter_progression
    from talent_data import TALENT_SPELLS
    chatter_db._talent_cache.clear()
    chatter_progression.clear_caches()
    shadow_db = _TalentDb(0, [(s, 1) for s in TELIRIAH_SPELLS])
    talents = chatter_db.get_character_talents(shadow_db, 1091)
    assert talents['tree_totals'] == {'Shadow': 37}
    assert talents['talents'][0]['tree_name'] == 'Shadow'
    assert chatter_progression.priest_style(shadow_db, 1091) == (
        'Shadow Priest')

    holy = sorted(
        s for s, info in TALENT_SPELLS.items()
        if info['tab_id'] == 202 and info['rank'] == 1
    )[:8]
    holy_db = _TalentDb(0, [(s, 1) for s in holy])
    assert chatter_db.get_character_talents(holy_db, 2001)[
        'tree_totals'] == {'Holy': 8}
    assert chatter_progression.priest_style(holy_db, 2001) == (
        'Light Priest')

    # Shadow talents saved only in the second spec do not count while
    # the first spec is active.
    dual_db = _TalentDb(
        0, [(s, 2) for s in TELIRIAH_SPELLS] + [(s, 1) for s in holy])
    assert chatter_db.get_character_talents(dual_db, 2002)[
        'tree_totals'] == {'Holy': 8}
    dual_db.active_spec = 1
    assert chatter_db.get_character_talents(dual_db, 2002)[
        'tree_totals'] == {'Shadow': 37}


def test_levelup_payload_carries_leveler_identity():
    source = _read('LLMChatterGroupCombat.cpp')
    for field in ('leveler_guid', 'leveler_class', 'leveler_race',
                  'leveler_gender'):
        assert f'\\"{field}\\":' in source


# -- Links ---------------------------------------------------------------

def test_prompts_use_single_brace_placeholders():
    source = (TOOLS_DIR / 'chatter_prompts.py').read_text(encoding='utf-8')
    assert '{{{{' not in source
    prompt = chatter_prompts.build_trade_statement_prompt(
        SELLER, POTION, config={})
    assert '{item:Superior Mana Potion}' in prompt
    assert '{{item:' not in prompt


def test_cleanup_keeps_links_with_colons():
    spell = {'spell_id': 1243, 'spell_name': 'Power Word: Fortitude'}
    for raw in (
        'Feeling the warmth from {{spell:Power Word: Fortitude}} is '
        'delightful! It lifts my spirit.',
        'Feeling the warmth from {spell:Power Word: Fortitude} is '
        'delightful! It lifts my spirit.',
    ):
        text = cleanup_message(replace_placeholders(raw, spell_data=spell))
        assert FORTITUDE_LINK in text
        assert text.endswith('It lifts my spirit.')
        assert '{' not in text
    assert cleanup_message(
        'Well fought today friends! Cylaea: Hold, do you smell that?'
    ) == 'Well fought today friends!'


def test_emojis_are_stripped_with_their_leftovers():
    from chatter_text import strip_emojis
    assert strip_emojis(
        'So bright, just like my smile! \u2728\ufe0f'
    ) == 'So bright, just like my smile!'
    assert strip_emojis('Hello \U0001F600!') == 'Hello!'
    assert strip_emojis(
        'Family \U0001F468\u200d\U0001F469\u200d\U0001F467 trip'
    ) == 'Family trip'
    assert strip_emojis('Go \U0001F1FA\U0001F1F8 go') == 'Go go'
    assert strip_emojis('Sun \u2600\ufe0f and \u2b50 stars') == (
        'Sun and stars')
    assert strip_emojis('Pick 1\ufe0f\u20e3 now') == 'Pick 1 now'
    kept = (f'Take {FORTITUDE_LINK}, friend\u2026 it\u2019s "free", '
            'Привет, 50 silver')
    assert strip_emojis(kept) == kept
    assert strip_emojis('\U0001F525\U0001F525') == ''
    assert cleanup_message('Well met! \U0001F44B\U0001F3FD') == 'Well met!'


def test_insert_skips_emoji_only_messages():
    import chatter_db

    class Cursor:
        def __init__(self, calls):
            self.calls = calls

        def execute(self, sql, params=()):
            self.calls.append(params)

    class Db:
        def __init__(self):
            self.calls = []

        def cursor(self, *args, **kwargs):
            return Cursor(self.calls)

        def commit(self):
            pass

    db = Db()
    chatter_db.insert_chat_message(db, 1, 'Kizia', '\U0001F525 \u2728',
                                   channel='say')
    assert db.calls == []
    chatter_db.insert_chat_message(db, 1, 'Kizia', 'Onward! \U0001F525',
                                   channel='say')
    assert 'Onward!' in db.calls[0]


def test_shortening_never_splits_a_link():
    message = 'word ' * 45 + FORTITUDE_LINK + ' and more words after it'
    shortened = shorten_chat_message(message)
    assert len(shortened) <= 255
    assert '|H' not in shortened or FORTITUDE_LINK in shortened


# -- PvP factions --------------------------------------------------------

def test_faction_war_line():
    line = faction_war_line('Kizia', 'Horde', 'Brand', 'Alliance')
    assert 'Kizia fights for the Horde' in line
    assert 'Brand fights for the Alliance' in line
    assert 'long, bitter war for survival' in line
    assert faction_war_line('A', 'Horde', 'B', 'Horde') == ''
    assert faction_war_line('A', '', 'B', 'Alliance') == ''


def test_pvp_prompts_state_both_factions():
    extra = {
        'bot_name': 'Kizia', 'bot_team': 'Horde', 'victim_name': 'Brand',
        'victim_team': 'Alliance', 'killer_name': 'Brand',
        'killer_team': 'Alliance', 'zone_id': 17,
    }
    kill = '\n'.join(world._pvp_kill_scenario(extra, 'roleplay'))
    death = '\n'.join(world._pvp_death_scenario(extra, 'roleplay', 'guild'))
    for text in (kill, death):
        assert 'fights for the Horde' in text
        assert 'fights for the Alliance' in text
    group = world.build_group_pvp_kill_prompt({
        'bot': dict(REACTOR, level=30),
        'extra_data': {'victim_name': 'Brand', 'victim_team': 'Alliance',
                       'bot_team': 'Horde', 'killer_name': 'Ogg'},
        'mode': 'roleplay', 'traits': ['grim'], 'stored_tone': 'grim',
        'chat_hist': '',
    })
    assert 'You and your party fight for the Horde' in group
    bg = chatter_bg_prompts.build_bg_pvp_kill_prompt(
        {'victim_name': 'Brand', 'victim_class': 1, 'killer_name': 'Ogg',
         'killer_team': 'Horde', 'victim_team': 'Alliance'},
        REACTOR)
    assert 'You and your side fight for the Horde' in bg


def test_pvp_payloads_carry_teams():
    guild_world = _read('LLMChatterGuildWorld.cpp')
    assert '"{0}_team":"{8}"' in guild_world
    assert '"killer_team":"{}","bot_team":"{}"' in guild_world
    player = _read('LLMChatterPlayer.cpp')
    assert '\\"killer_team\\":' in player
    assert '\\"victim_team\\":' in player


# -- Guild bots and greetings -------------------------------------------

def test_guild_world_scans_include_playerbots():
    source = _read('LLMChatterGuildWorld.cpp')
    assert 'GetAllSessions' not in source
    assert source.count('ObjectAccessor::GetPlayers()') >= 2
    assert 'HoldBotForReply(bot, player, 10000)' in source
    assert 'void HoldBotForReply' in _read('LLMChatterShared.cpp')


def test_meet_greeting_is_an_unexpected_guild_encounter():
    source = (TOOLS_DIR / 'chatter_guild_world_events.py').read_text(
        encoding='utf-8')
    assert 'unexpected, chance encounter with a fellow member' in source
    assert 'warm, friendly greeting' in source


# -- Real player description and MOTD ------------------------------------

def test_player_description_roleplay_and_normal():
    import chatter_player_context as pc
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
    import chatter_player_context as pc
    original = pc.class_style
    try:
        pc.class_style = lambda db, guid, cls: 'Shadow Priest'
        shadow = '\n'.join(pc.player_character_lines(
            object(), 7, 'Lyn', 'roleplay',
            race='Blood Elf', class_name='Priest', gender='female'))
    finally:
        pc.class_style = original
    assert 'female Blood Elf Shadow Priest.' in shadow
    assert 'Shadow Priest calling:' in shadow
    light = '\n'.join(pc.player_character_lines(
        None, 0, 'Lyn', 'roleplay',
        race='Blood Elf', class_name='Priest', gender='female'))
    assert 'Light Priest calling:' in light
    assert 'Shadow' not in light


def test_meet_greeting_prompt_describes_the_player():
    captured = {}
    patched = {
        '_config_enabled': lambda config, key: True,
        '_participant': lambda db, extra: {
            'guid': 5, 'name': 'Kizia', 'speaker': dict(REACTOR)},
        '_participant_identity_lines': lambda bot, mode: [],
        '_mark_event': lambda *args, **kwargs: None,
        'insert_chat_message': lambda *args, **kwargs: None,
        'get_zone_name': lambda zone_id: 'Durotar',
        'run_single_prompt': lambda client, config, prompt, *rest: (
            captured.setdefault('prompt', prompt)
            and [{'message': 'Lok\'tar, Lyn!'}]),
    }
    originals = {key: getattr(world, key) for key in patched}
    try:
        for key, value in patched.items():
            setattr(world, key, value)
        extra = {
            'player_guid': 9, 'player_name': 'Lyn', 'player_race': 'Orc',
            'player_class': 'Hunter', 'player_gender': 'female',
            'guild_name': 'Horde Heroes', 'zone_id': 14,
        }
        assert world.process_guild_meet_greeting_event(
            None, None, RP, {'id': 1, 'extra_data': json.dumps(extra)})
    finally:
        for key, value in originals.items():
            setattr(world, key, value)
    prompt = captured['prompt']
    assert 'About Lyn, the real player' in prompt
    assert 'female Orc Hunter' in prompt
    assert 'Hunter calling:' in prompt


def test_motd_idle_topic_is_a_casual_note_in_roleplay():
    import chatter_guild
    config = dict(RP, **{'LLMChatter.GuildChatter.MotdChance': 100})
    profile = {'motd': 'We must always protect our Light'}
    topic, used = chatter_guild._pick_guild_topic(config, 'roleplay', profile)
    assert used is True
    assert 'short note the guild\'s officers left' in topic
    assert '"We must always protect our Light"' in topic
    assert 'Message of the Day' not in topic.split('Never call')[0]
    assert 'sacred creed' in topic
    topic, _ = chatter_guild._pick_guild_topic(config, 'normal', profile)
    assert topic.startswith('the guild motd')
    assert 'capital-letter' in topic


# -- Frequencies ---------------------------------------------------------

def _conf_value(text: str, key: str) -> int:
    match = re.search(rf'^{re.escape(key)} = (\d+)', text, re.M)
    assert match, key
    return int(match.group(1))


def test_frequency_defaults():
    config = _read('LLMChatterConfig.cpp')
    assert '"LLMChatter.GroupChatter.KillChanceNormal", 13)' in config
    assert '"LLMChatter.GroupChatter.SpellCastChance", 10)' in config
    assert themed.CHANNEL_CHANCE['guild'][1] == 80
    assert themed.CHANNEL_CHANCE['general'][1] == 80
    assert themed.CHANNEL_CHANCE['party'][1] == 7
    conf = MODULE_DIR / 'conf'
    dist = (conf / 'mod_llm_chatter.conf.dist').read_text(encoding='utf-8')
    quiet = (conf / 'presets' / 'mod_ll_chatter_quieter.conf.dist').read_text(
        encoding='utf-8')
    expected = {
        'LLMChatter.GroupChatter.KillChanceNormal': (13, 5),
        'LLMChatter.GroupChatter.SpellCastChance': (10, 5),
        'LLMChatter.ThemedTopics.GuildChance': (80, 67),
        'LLMChatter.ThemedTopics.GeneralChance': (80, 67),
        'LLMChatter.ThemedTopics.PartyChance': (7, 4),
    }
    for key, (dist_value, quiet_value) in expected.items():
        assert _conf_value(dist, key) == dist_value, key
        assert _conf_value(quiet, key) == quiet_value, key


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} roleplay fix tests passed")
