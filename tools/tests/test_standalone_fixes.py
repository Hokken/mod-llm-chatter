#!/usr/bin/env python3
"""Standalone chat fixes: talents from client data, emoji stripping,
link-safe cleanup and shortening, the short reply hold, roleplay trade
prices (English only), roleplay level-up praise and the roleplay slang
ban.

Run directly from the module root:
  python tools/tests/test_standalone_fixes.py
"""

import importlib
import json
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

import chatter_prompts  # noqa: E402
from chatter_class_style import class_style, priest_style  # noqa: E402
from chatter_group_prompts import (  # noqa: E402
    CLASS_GROWTH,
    build_levelup_reaction_prompt,
)
from chatter_shared import (  # noqa: E402
    cleanup_message,
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


# -- Slang ---------------------------------------------------------------

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


def test_spell_out_numbers_reads_grouped_numbers_whole():
    assert spell_out_numbers('Selling for 1,500 gold') == (
        'Selling for one thousand five hundred gold')
    assert spell_out_numbers('all 2,000 of them') == (
        'all two thousand of them')
    assert spell_out_numbers('take 3.5 gold') == 'take 3.5 gold'
    assert spell_out_numbers('only 1,500g') == (
        'only one thousand five hundred gold')
    assert spell_out_numbers('1,500g20s each') == (
        'one thousand five hundred gold and twenty silver each')
    assert spell_out_numbers('worth 1,500.50 gold') == (
        'worth 1,500.50 gold')
    assert spell_out_numbers('about 12,5g') == 'about 12,5g'
    assert spell_out_numbers('1,234,567 gold') == '1,234,567 gold'


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

def test_roleplay_levelup_names_growth_without_levels():
    prompt = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Brand', 25, True, 'roleplay',
        leveler_race='Human', leveler_class='Warrior')
    assert CLASS_GROWTH['Warrior'] in prompt
    assert '25' not in prompt
    assert 'Never mention levels' in prompt
    # The persona decides the reaction; the prompt prescribes none.
    assert 'admiration' not in prompt
    assert 'Praise' not in prompt
    assert 'personality and tone decide' in prompt
    normal = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Brand', 25, True, 'normal')
    assert 'level 25' in normal


def test_levelup_splits_shadow_and_light_priests():
    shadow = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Lyn', 30, True, 'roleplay',
        leveler_race='Blood Elf', leveler_class='Priest',
        leveler_style='Shadow Priest')
    assert 'Blood Elf Shadow Priest' in shadow
    assert CLASS_GROWTH['Shadow Priest'] in shadow
    light = build_levelup_reaction_prompt(
        REACTOR, ['kind'], 'Lyn', 30, True, 'roleplay',
        leveler_race='Blood Elf', leveler_class='Priest')
    assert 'Blood Elf Light Priest' in light
    assert CLASS_GROWTH['Light Priest'] in light
    assert 'shadow' not in light.split('Lyn, a')[1].split('\n')[0]


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
    from talent_data import TALENT_SPELLS
    chatter_db._talent_cache.clear()
    shadow_db = _TalentDb(0, [(s, 1) for s in TELIRIAH_SPELLS])
    talents = chatter_db.get_character_talents(shadow_db, 1091)
    assert talents['tree_totals'] == {'Shadow': 37}
    assert talents['talents'][0]['tree_name'] == 'Shadow'
    assert priest_style(shadow_db, 1091) == (
        'Shadow Priest')

    holy = sorted(
        s for s, info in TALENT_SPELLS.items()
        if info['tab_id'] == 202 and info['rank'] == 1
    )[:8]
    holy_db = _TalentDb(0, [(s, 1) for s in holy])
    assert chatter_db.get_character_talents(holy_db, 2001)[
        'tree_totals'] == {'Holy': 8}
    assert priest_style(holy_db, 2001) == (
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
    for field in ('leveler_guid', 'leveler_class', 'leveler_race'):
        assert f'\\"{field}\\":' in source
    assert 'leveler_gender' not in source


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

def test_priest_style_follows_a_spec_switch():
    import chatter_db
    from talent_data import TALENT_SPELLS
    chatter_db._talent_cache.clear()
    holy = sorted(
        s for s, info in TALENT_SPELLS.items()
        if info['tab_id'] == 202 and info['rank'] == 1
    )[:8]
    db = _TalentDb(
        0, [(s, 2) for s in TELIRIAH_SPELLS] + [(s, 1) for s in holy])
    assert class_style(db, 3001, 'Priest') == 'Light Priest'
    db.active_spec = 1
    assert class_style(db, 3001, 'Priest') == 'Shadow Priest'
    assert class_style(db, 3001, 'Mage') == 'Mage'
    assert class_style(None, 0, 'Priest') == 'Light Priest'


def _trade_patches(lines, inserted):
    import chatter_ambient as ambient
    from unittest.mock import patch

    def fake_llm(client, prompt, config, **kwargs):
        return json.dumps(lines)

    def fake_insert(db, bot_guid, bot_name, message, **kwargs):
        inserted.append(message)
        return len(inserted)

    return [
        patch.object(ambient, 'call_llm', side_effect=fake_llm),
        patch.object(ambient, 'insert_chat_message',
                     side_effect=fake_insert),
        patch.object(ambient, 'get_recent_zone_messages', return_value=[]),
        patch.object(ambient, 'build_gear_context', return_value=''),
        patch.object(ambient, 'prepare_channel_persona', return_value=None),
        patch.object(ambient, 'build_talent_context', return_value=None),
        patch.object(ambient, 'maybe_queue_group_general_reaction'),
        patch.object(ambient, '_zone_delivery_delay', return_value=1),
        patch.object(ambient, '_reserve_zone_delivery_window',
                     return_value=1),
        patch.object(ambient, 'is_too_similar', return_value=False),
    ]


class _TradeDb:
    def cursor(self, *args, **kwargs):
        class Cursor:
            def execute(self, sql, params=()):
                pass

            def fetchone(self):
                return None

            def fetchall(self):
                return []

        return Cursor()

    def commit(self):
        pass


def _run_trade(language, lines, conversation):
    import chatter_ambient as ambient
    import chatter_shared
    import chatter_threads
    chatter_threads.configure_threads({'LLMChatter.Threads.Enable': 0})
    chatter_shared.set_language(language)
    request = {
        'id': 901, 'zone_id': 85, 'area_id': 85,
        'message_type': 'trade', 'bot1_race': 5,
        'item_context': json.dumps(dict(POTION, item_id=6149)),
    }
    bot = {'guid': 11, 'name': 'Annata', 'class': 'Warlock',
           'race': 'Undead', 'level': 40, 'zone': 'Tirisfal Glades'}
    inserted = []
    db = _TradeDb()
    patches = _trade_patches(lines, inserted)
    for p in patches:
        p.start()
    try:
        if conversation:
            ambient.process_conversation(
                db, db.cursor(), None, RP, request,
                [bot, dict(bot, guid=12, name='Borin', race='Orc')])
        else:
            ambient.process_statement(
                db, db.cursor(), None, RP, request, bot)
    finally:
        for p in patches:
            p.stop()
        chatter_shared.set_language('GB')
        chatter_threads.reset_settings()
    return inserted


def test_trade_prices_keep_a_non_english_language():
    french = 'Je vends 10 potions pour 50 pieces.'
    assert _run_trade('FR', {'message': french}, False) == [french]
    lines = [{'speaker': 'Annata', 'message': french},
             {'speaker': 'Borin', 'message': 'Pour 50 pieces, oui.'}]
    assert _run_trade('FR', lines, True) == [
        french, 'Pour 50 pieces, oui.']


def test_trade_prices_are_spelled_out_in_english():
    english = 'Ten potions for 50 silver.'
    assert _run_trade('GB', {'message': english}, False) == [
        'Ten potions for fifty silver.']
    lines = [{'speaker': 'Annata', 'message': english},
             {'speaker': 'Borin', 'message': 'I will take 2 of them.'}]
    assert _run_trade('GB', lines, True) == [
        'Ten potions for fifty silver.', 'I will take two of them.']


# -- Reply hold ----------------------------------------------------------

def _function(source: str, signature: str) -> str:
    start = source.index(signature)
    end = source.find('\n}\n', start)
    return source[start:end]


def test_reply_hold_leaves_moving_bots_alone():
    source = _read('LLMChatterReplyHold.cpp')
    hold = _function(source, 'void HoldBotForReply(')
    assert 'StopMoving' not in source
    assert 'GetMotionMaster' not in source
    assert '!IsSafeForChatterFacing(bot)' in hold
    facing = hold.index('SetFacingToObject(player)')
    assert hold.index('!IsSafeForChatterFacing(bot)') < facing
    assert hold.index('_facingEnable') < facing
    assert 'IsInCombat()' in hold


def test_reply_hold_duration_is_configurable():
    header = _read('LLMChatterReplyHold.h')
    hold = _function(_read('LLMChatterReplyHold.cpp'),
                     'void HoldBotForReply(')
    assert 'LLM_CHATTER_MAX_REPLY_HOLD_MS = 10000' in header
    assert '_proxChatterReplyHoldMs,\n        LLM_CHATTER_MAX_REPLY_HOLD_MS' \
        in hold
    assert hold.index('!holdMs') < hold.index('SetFacingToObject')
    assert '"ReplyHoldMs", 4000' in _read('LLMChatterConfig.cpp')
    for conf in ('mod_llm_chatter.conf.dist',
                 'presets/mod_ll_chatter_quieter.conf.dist'):
        text = (MODULE_DIR / 'conf' / conf).read_text(encoding='utf-8')
        block = text.split('#   LLMChatter.ProximityChatter.ReplyHoldMs')[1]
        block = block.split('\n\n')[0]
        assert '0 - Disabled' in block and 'Capped at 10000' in block
        assert block.rstrip().endswith(
            'LLMChatter.ProximityChatter.ReplyHoldMs = 4000'), conf


def test_reply_hold_never_shortens_other_ai_delays():
    source = _read('LLMChatterReplyHold.cpp')
    hold = _function(source, 'void HoldBotForReply(')
    release = _function(source, 'void ReleaseHold(')
    assert 'SetNextCheckDelay(0)' not in source
    assert hold.index('if (priorMs >= holdMs)') < hold.index(
        'ai->SetNextCheckDelay(holdMs)')
    assert 'if (current > hold.heldMs - elapsed + kReleaseSlackMs)' \
        in release
    assert release.index('kReleaseSlackMs)') < release.index(
        'ai->SetNextCheckDelay(priorLeft)')
    assert 'if (priorLeft < current)' in release


def test_reply_hold_rehold_keeps_a_delay_raised_from_outside():
    hold = _function(_read('LLMChatterReplyHold.cpp'),
                     'void HoldBotForReply(')
    assert 'uint32 priorMs = current;' in hold
    rehold = hold[hold.index('if (previous != _heldBots.end())'):
                  hold.index('if (priorMs >= holdMs)')]
    assert ('&& current <= previous->second.heldMs - elapsed\n'
            '                + kReleaseSlackMs)') in rehold
    assert rehold.index('kReleaseSlackMs)') < rehold.index(
        'priorMs = previous->second.priorMs')


def test_reply_hold_is_released_only_by_its_own_reply():
    source = _read('LLMChatterReplyHold.cpp')
    header = _read('LLMChatterReplyHold.h')
    release = _function(source, 'void ReleaseHold(')
    assert 'it->second.replyId != *replyId' in release
    assert 'eventType' not in source and 'eventType' not in header
    assert 'if (replyId)\n        ReleaseHold(botGuid, &replyId);' in source
    assert 'LLM_CHATTER_REPLY_HOLD_KEY = "reply_hold_id"' in header
    assert 'std::time(nullptr)' in source

    proximity = _read('LLMChatterProximity.cpp')
    emote = _function(proximity, 'bool HandleProximityPlayerbotEmote(')
    assert 'addressedSpeaks ? NewReplyHoldId() : 0' in emote
    assert 'isCustom, replyHoldId);' in emote
    assert 'if (queued && replyHoldId)\n' \
        '        HoldBotForReply(bot, player, replyHoldId);' in emote
    queue = _function(proximity, 'bool QueuePlayerEmoteProximityEvent(')
    assert queue.index('extra += ReplyHoldJsonField(replyHoldId);') \
        < queue.index('QueueChatterEvent(')
    # The mirror emote queues no reply, so no delivered line ends it.
    assert 'HoldBotForReply(targetBot, player, 0);' \
        in _read('LLMChatterGroupEmote.cpp')

    delivery = _read('LLMChatterDelivery.cpp')
    assert ('ReplyHoldDeliveryScope replyHold(botGuid, ExtractJsonUInt(\n'
            '        eventExtraData, LLM_CHATTER_REPLY_HOLD_KEY));') \
        in delivery
    finalize = _function(delivery, 'void FinalizeDroppedMessage(')
    assert 'JOIN llm_chatter_events e ON e.id = m.event_id' in finalize
    assert 'LLM_CHATTER_REPLY_HOLD_KEY' in finalize
    assert 'ReleaseHold(player->GetGUID().GetCounter(), nullptr)' in source
    assert 'AddLLMChatterReplyHoldScripts();' in _read('LLMChatterScript.cpp')


def test_reply_hold_ends_on_terminal_drops_but_not_on_retry():
    delivery = _read('LLMChatterDelivery.cpp')
    body = _function(delivery, 'void DeliverPendingMessagesImpl()')
    scope = body.index('ReplyHoldDeliveryScope replyHold(botGuid,')
    assert scope < body.index('FinalizeDroppedMessage(')
    retry = body.index('// Unclaim and reschedule for retry.')
    keep = body.index('replyHold.Keep();', retry)
    assert keep < body.index('"SET delivered = 0, "', retry)
    assert 'ReleaseBotReplyHold(botGuid)' not in delivery
    finalize = _function(delivery, 'void FinalizeDroppedMessage(')
    assert finalize.index('ReleaseBotReplyHold(') < finalize.index(
        "cancelled_after_directed_drop")
    header = _read('LLMChatterReplyHold.h')
    assert 'if (!_keep)\n            ReleaseBotReplyHold(' in header


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} standalone fix tests passed")
