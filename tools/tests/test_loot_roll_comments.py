#!/usr/bin/env python3
"""Party bots explain their Need or Greed roll: item type naming, the
prompt, routing, and the C++, SQL and conf wiring.

Run directly from the module root:
  python tools/tests/test_loot_roll_comments.py
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
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_group_handlers as handlers  # noqa: E402
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402
from chatter_group_prompts import build_loot_roll_prompt  # noqa: E402
from chatter_shared import describe_item_type, loot_roll_motive  # noqa: E402

BOT = {'name': 'Grom', 'class': 'Warrior', 'race': 'Orc',
       'level': 30, 'gender': 'male'}


def _src(name: str) -> str:
    return (MODULE_DIR / 'src' / name).read_text(encoding='utf-8')


def _prompt(vote, mode='roleplay', item_type='weapon: two-handed sword',
            motive='use'):
    return str(build_loot_roll_prompt(
        BOT, ['blunt'], 'Ravager', 3, mode, vote, item_type,
        motive=motive,
    ))


# -- Item type naming --------------------------------------------------

def test_item_type_names_type_and_subtype():
    cases = {
        (2, 8, 17): 'weapon: two-handed sword',
        (2, 7, 21): 'weapon: one-handed sword (main hand)',
        (2, 15, 13): 'weapon: dagger',
        (2, 19, 26): 'weapon: wand',
        (4, 4, 5): 'armor: plate chest piece',
        (4, 2, 10): 'armor: leather gloves',
        (4, 1, 20): 'armor: cloth robe',
        (4, 1, 16): 'armor: cloak',
        (4, 0, 2): 'armor: necklace',
        (4, 0, 11): 'armor: ring',
        (4, 0, 12): 'armor: trinket',
        (4, 0, 23): 'armor: off-hand item',
        (4, 6, 14): 'armor: shield',
        (4, 7, 28): 'armor: libram',
        (0, 1, 0): 'consumable: potion',
        (1, 0, 18): 'container: bag',
        (3, 6, 0): 'gem: meta gem',
        (7, 5, 0): 'trade goods: cloth',
        (9, 2, 0): 'recipe: tailoring pattern',
        (16, 8, 0): 'glyph: mage glyph',
        (12, 0, 0): 'quest item',
    }
    for args, expected in cases.items():
        assert describe_item_type(*args) == expected, (args, expected)


def test_item_type_falls_back_to_the_class():
    assert describe_item_type(2, 14, 13) == 'weapon'
    assert describe_item_type(4, 4, 0) == 'armor'
    assert describe_item_type(99, 0, 0) == 'item'
    assert describe_item_type('x', None, 0) == 'item'


# -- Prompt ------------------------------------------------------------

def test_need_and_greed_share_the_personal_subject():
    # Playerbots roll Greed even on items they would use, so both
    # votes say the bot wants the item for itself; Need only adds
    # one line on top.
    need = _prompt('need')
    greed = _prompt('greed')
    shared = ('You rolled on it because you want it for yourself: '
              'you would use it.')
    for text in (need, greed):
        assert 'Ravager, a rare (blue) item' in text
        assert 'Item type: weapon: two-handed sword.' in text
        assert shared in text
        assert 'why you want it for yourself' in text
        assert '{item}' in text
        assert 'never claim you won the item' in text
    need_line = ('You rolled Need: you really need it, more than a '
                 'passing wish.\n')
    assert need_line in need and need_line not in greed

    def roll_section(text):
        start = text.index('An item dropped')
        return text[start:text.index('for yourself.', start)]

    # The rest of the prompt has random parts (twist, length hint).
    assert roll_section(need).replace(need_line, '') == roll_section(greed)
    assert 'greed' not in greed.lower()
    assert 'reason of your own' not in greed


def test_prompt_gives_no_ready_made_reasons():
    lowered = (_prompt('need') + _prompt('greed')).lower()
    for phrase in ('upgrade', 'vendor', 'sell it', 'disenchant',
                   'for example', 'e.g.'):
        assert phrase not in lowered, phrase


def test_prompt_follows_the_chat_mode():
    assert 'Speak in-character' in _prompt('need', 'roleplay')
    normal = _prompt('need', 'normal')
    assert 'Speak like a player explaining a roll' in normal
    assert 'Speak in-character' not in normal


def test_motive_follows_the_item_kind():
    # Equipment (anything with a slot, bags included) is for use.
    assert loot_roll_motive(4, 4, True) == 'use'
    assert loot_roll_motive(1, 0, True) == 'use'
    # Gems and keepsake-like miscellaneous items are for their looks.
    for cls, sub in ((3, 0), (3, 6), (15, 2), (15, 3), (15, 4), (15, 5)):
        assert loot_roll_motive(cls, sub, False) == 'beauty', (cls, sub)
    # Everything else is for its price.
    for cls, sub in ((7, 6), (0, 1), (9, 2), (5, 0), (16, 8), (15, 0)):
        assert loot_roll_motive(cls, sub, False) == 'sell', (cls, sub)
    assert loot_roll_motive('x', None, False) == 'sell'


def test_sell_and_beauty_prompts():
    sell = _prompt('greed', item_type='trade goods: leather', motive='sell')
    assert ('You rolled on it because you would like to sell it: it '
            'would fetch a fair price.') in sell
    assert 'why you would like to sell it' in sell
    assert 'you would use it' not in sell
    assert 'how you fight' not in sell
    beauty = _prompt('greed', item_type='gem: green gem', motive='beauty')
    assert ('You rolled on it because it is beautiful and you would like '
            'to keep it for how it looks.') in beauty
    assert 'what you find beautiful about it' in beauty
    assert 'sell' not in beauty
    for text in (sell, beauty):
        assert '{item}' in text
        assert 'never claim you won the item' in text
        assert 'You rolled Need' not in text
        for phrase in ('for example', 'e.g.'):
            assert phrase not in text.lower(), phrase
    # Need adds how much, in the motive's own words.
    assert ('You rolled Need: you really want the coin it would bring.'
            in _prompt('need', motive='sell'))
    assert ('You rolled Need: you really want it, more than a passing '
            'wish.' in _prompt('need', motive='beauty'))
    # Equipment keeps the fighting angle.
    assert 'how you fight' in _prompt('greed')


# -- Routing -----------------------------------------------------------

def test_registry_routes_the_roll_event():
    spec = EVENT_REGISTRY['bot_group_loot_roll']
    assert spec.handler_module == 'chatter_group_handlers'
    assert spec.producer == 'LLMChatterGroupLootRoll.cpp'
    assert callable(getattr(handlers, spec.handler_func))
    for field in ('roll_vote', 'item_name', 'item_entry', 'item_quality',
                  'item_class', 'item_subclass', 'item_inventory_type'):
        assert field in spec.payload_fields, field


def test_handler_builds_the_prompt_from_the_payload():
    captured = {}

    def fake_run(db, client, config, event, **kwargs):
        extra = json.loads(event['extra_data'])
        fields = kwargs['extract_fields'](extra)
        captured.update(fields)
        ctx = dict(fields, bot=BOT, traits=['blunt'], mode='roleplay',
                   chat_hist='', extra_data=extra, speaker_talent=None,
                   stored_tone=None, map_id=0)
        captured['prompt'] = str(kwargs['build_prompt'](ctx))
        captured['label'] = kwargs['label']
        return True

    extra = {'bot_guid': 5, 'bot_name': 'Grom', 'group_id': 9,
             'roll_vote': 'greed', 'item_name': 'Lionheart Helm',
             'item_entry': 12640, 'item_quality': 4, 'item_class': 4,
             'item_subclass': 4, 'item_inventory_type': 1, 'is_bot': 1}
    with patch.object(handlers, 'run_group_handler',
                      side_effect=fake_run), \
            patch.object(handlers, 'localize_item_name',
                         side_effect=lambda db, name, entry: name):
        assert handlers.process_group_loot_roll_event(
            None, None, {}, {'id': 1, 'extra_data': json.dumps(extra)})
    assert captured['roll_vote'] == 'greed'
    assert captured['item_type'] == 'armor: plate helm'
    assert 'Item type: armor: plate helm.' in captured['prompt']
    assert captured['label'] == 'reaction_loot_roll'
    # No item_is_equipment (older payload): the slot decides.
    assert captured['motive'] == 'use'

    for flag, cls, sub, inv, motive in ((0, 7, 6, 0, 'sell'),
                                        (0, 3, 0, 0, 'beauty'),
                                        (1, 1, 0, 18, 'use')):
        captured.clear()
        payload = dict(extra, item_class=cls, item_subclass=sub,
                       item_inventory_type=inv, item_is_equipment=flag)
        with patch.object(handlers, 'run_group_handler',
                          side_effect=fake_run), \
                patch.object(handlers, 'localize_item_name',
                             side_effect=lambda db, name, entry: name):
            handlers.process_group_loot_roll_event(
                None, None, {},
                {'id': 1, 'extra_data': json.dumps(payload)})
        assert captured['motive'] == motive, (cls, sub, motive)


# -- C++, SQL and conf -------------------------------------------------

def test_cpp_polls_rolls_for_need_and_greed_only():
    source = _src('LLMChatterGroupLootRoll.cpp')
    assert 'group->GetRolls()' in source
    assert 'vote != NEED && vote != GREED' in source
    assert 'IsBattlegroundOrArena()' in source
    assert 'GroupHasRealPlayer(group)' in source
    assert 'state.queued >= maxPerItem' in source
    assert '_lootRollCommentMaxPerItem' in source
    for field in ('roll_vote', 'item_class', 'item_subclass',
                  'item_inventory_type', 'item_quality',
                  'item_is_equipment'):
        assert f'\\"{field}\\":' in source, field
    world = _src('LLMChatterWorld.cpp')
    assert 'CheckGroupLootRolls();' in world


def test_cpp_switches_filter_before_queueing():
    source = _src('LLMChatterGroupLootRoll.cpp')
    assert 'tmpl->InventoryType != INVTYPE_NON_EQUIP' in source
    for field in ('_lootRollCommentNeedEnable', '_lootRollCommentGreedEnable',
                  '_lootRollCommentEquipmentEnable',
                  '_lootRollCommentOtherEnable'):
        assert field in source, field
    # A skipped vote is still marked handled, so it is not reconsidered.
    loop = source[source.index('state.handledVoters.insert(rawGuid);'):]
    assert loop.index('if (!kindEnabled || !VoteCommentEnabled(vote))') < 80
    shared = _src('LLMChatterShared.cpp')
    assert '{"bot_group_loot_roll",     PRIORITY_HIGH}' in shared
    assert '&LLMChatterConfig::_reactDelayLootRoll' in shared


def test_sql_adds_the_event_type_additively():
    base = (MODULE_DIR / 'data/sql/characters/base/'
            '00000000_llm_chatter_tables.sql').read_text(encoding='utf-8')
    enum = base[base.index('`event_type` ENUM('):]
    enum = enum[:enum.index(') NOT NULL')]
    assert "'bot_group_loot_roll'" in enum
    name = '20261022_loot_roll_comments.sql'
    update = (MODULE_DIR / 'data/sql/characters/updates' / name
              ).read_text(encoding='utf-8')
    assert "LIKE '%''bot_group_loot_roll''%'" in update
    assert "LEFT(@event_type, CHAR_LENGTH(@event_type) - 1)" in update
    readme = (MODULE_DIR / 'README.md').read_text(encoding='utf-8')
    assert readme.count(name) == 2


def test_conf_keys_are_documented_and_loaded():
    loads = _src('LLMChatterConfig.cpp')
    for name in ('conf/mod_llm_chatter.conf.dist',
                 'conf/presets/mod_ll_chatter_quieter.conf.dist'):
        text = (MODULE_DIR / name).read_text(encoding='utf-8')
        for key, default in (('LootRollComment.Enable', '1'),
                             ('LootRollComment.MaxPerItem', '3'),
                             ('LootRollComment.NeedEnable', '1'),
                             ('LootRollComment.GreedEnable', '1'),
                             ('LootRollComment.EquipmentEnable', '1'),
                             ('LootRollComment.OtherEnable', '1')):
            full = f'LLMChatter.GroupChatter.{key}'
            assert re.search(rf'^{re.escape(full)} = {default}$', text,
                             re.M), (name, key)
            assert f'"{key}"' in loads, key


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} loot roll comment tests passed")
