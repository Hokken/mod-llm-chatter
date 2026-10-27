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
from chatter_shared import (  # noqa: E402
    describe_item_type,
    loot_roll_states_use,
    loot_roll_use_ideas,
)

BOT = {'name': 'Grom', 'class': 'Warrior', 'race': 'Orc',
       'level': 30, 'gender': 'male'}


def _src(name: str) -> str:
    return (MODULE_DIR / 'src' / name).read_text(encoding='utf-8')


def _prompt(vote, mode='roleplay', item_type='weapon: two-handed sword',
            item_use='yes', required_level=0, use_ideas=()):
    return str(build_loot_roll_prompt(
        BOT, ['blunt'], 'Ravager', 3, mode, vote, item_type,
        item_use=item_use, required_level=required_level,
        use_ideas=use_ideas,
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

def test_prompt_states_facts_not_a_motive():
    # The persona decides why: no motive, no feeling, no claim about
    # the roll's outcome; Need and Greed differ only in the vote fact.
    need = _prompt('need')
    greed = _prompt('greed')
    for text, vote in ((need, 'Need'), (greed, 'Greed')):
        assert 'Ravager, a rare (blue) item' in text
        assert 'Item type: weapon: two-handed sword.' in text
        assert f'You voted {vote} on it.' in text
        assert 'You can use it yourself.' in text
        assert 'why, in your own words' in text
        assert '{item}' in text
        assert 'never claim you won it' in text
        lowered = text.lower()
        for phrase in ('because', 'really need', 'beautiful',
                       'not decided', 'still open', 'fair price',
                       'how you fight'):
            assert phrase not in lowered, phrase

    def roll_section(text):
        start = text.index('An item dropped')
        return text[start:text.index('own words.', start)]

    assert roll_section(need).replace('Need', 'X') == (
        roll_section(greed).replace('Greed', 'X'))


def test_prompt_states_whether_the_bot_can_use_it():
    cases = {
        'class': 'it is not made for your class, race or faction',
        'proficiency': 'not trained to wear or wield this kind',
        'skill': 'lack the skill it requires',
        'no': 'cannot use it yourself right now',
    }
    for item_use, fact in cases.items():
        assert fact in _prompt('need', item_use=item_use), item_use
    assert 'It requires level 42; you are below that.' in _prompt(
        'need', item_use='level', required_level=42)
    # Unknown (older payload or a kind where use means nothing).
    plain = _prompt('need', item_use=None)
    assert 'use it yourself' not in plain
    assert 'cannot use' not in plain


def test_ideas_are_offered_only_as_ideas():
    text = _prompt('greed', use_ideas=['to sell it', 'for crafting'])
    assert 'only as ideas:' in text
    assert 'Your reason may be one of them or your own.' in text
    assert 'to sell it' in text and 'for crafting' in text
    assert 'only as ideas' not in _prompt('greed')


def test_prompt_follows_the_chat_mode():
    assert 'Speak in-character' in _prompt('need', 'roleplay')
    normal = _prompt('need', 'normal')
    assert 'Speak like a player in party chat' in normal
    assert 'Speak in-character' not in normal


def test_use_ideas_follow_the_facts():
    usable = loot_roll_use_ideas(4, 4, True, 'yes')
    assert 'to wear or wield it yourself' in usable
    for blocked in ('class', 'proficiency', 'skill', 'no'):
        ideas = loot_roll_use_ideas(4, 4, True, blocked)
        assert 'to wear or wield it yourself' not in ideas, blocked
        assert 'to pass it to an ally or friend who can use it' in ideas
    assert 'to use it once you reach level 45' in loot_roll_use_ideas(
        2, 8, True, 'level', 45)
    assert 'to carry more in it' in loot_roll_use_ideas(1, 0, True, 'yes')
    assert 'to set it into your gear' in loot_roll_use_ideas(3, 2, False)
    assert loot_roll_use_ideas(9, 2, False, 'yes')[0] == 'to learn it'
    assert 'to learn it' not in loot_roll_use_ideas(9, 2, False, 'skill')
    assert 'for crafting' in loot_roll_use_ideas(7, 6, False)
    assert 'to keep it' in loot_roll_use_ideas(15, 2, False)
    for ideas in (usable, loot_roll_use_ideas('x', None, False)):
        assert 'to sell it' in ideas


def test_use_is_stated_only_where_it_means_something():
    assert loot_roll_states_use(4, 4, True)
    for cls, sub in ((0, 1), (9, 2), (16, 8), (15, 2), (15, 5)):
        assert loot_roll_states_use(cls, sub, False), (cls, sub)
    for cls, sub in ((7, 6), (5, 0), (3, 2), (15, 0), (12, 0), (13, 0)):
        assert not loot_roll_states_use(cls, sub, False), (cls, sub)


# -- Routing -----------------------------------------------------------

def test_registry_routes_the_roll_event():
    spec = EVENT_REGISTRY['bot_group_loot_roll']
    assert spec.handler_module == 'chatter_group_handlers'
    assert spec.producer == 'LLMChatterGroupLootRoll.cpp'
    assert callable(getattr(handlers, spec.handler_func))
    for field in ('roll_vote', 'item_name', 'item_entry', 'item_quality',
                  'item_class', 'item_subclass', 'item_inventory_type',
                  'item_use', 'item_required_level', 'roll_source_guid',
                  'roll_slot'):
        assert field in spec.payload_fields, field


def _run_handler(payload):
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

    with patch.object(handlers, 'run_group_handler',
                      side_effect=fake_run), \
            patch.object(handlers, 'localize_item_name',
                         side_effect=lambda db, name, entry: name):
        assert handlers.process_group_loot_roll_event(
            None, None, {}, {'id': 1, 'extra_data': json.dumps(payload)})
    return captured


def test_handler_builds_the_prompt_from_the_payload():
    extra = {'bot_guid': 5, 'bot_name': 'Grom', 'group_id': 9,
             'roll_vote': 'greed', 'item_name': 'Lionheart Helm',
             'item_entry': 12640, 'item_quality': 4, 'item_class': 4,
             'item_subclass': 4, 'item_inventory_type': 1, 'is_bot': 1,
             'item_use': 'level', 'item_required_level': 50,
             'roll_source_guid': 17370386536034419712, 'roll_slot': 2}
    captured = _run_handler(extra)
    assert captured['roll_vote'] == 'greed'
    assert captured['item_type'] == 'armor: plate helm'
    assert captured['item_use'] == 'level'
    assert captured['required_level'] == 50
    assert 'to use it once you reach level 50' in captured['use_ideas']
    assert 'Item type: armor: plate helm.' in captured['prompt']
    assert 'It requires level 50; you are below that.' in captured['prompt']
    assert captured['label'] == 'reaction_loot_roll'

    # Trade goods: usability means nothing, so it is not stated.
    leather = _run_handler(dict(
        extra, item_class=7, item_subclass=6, item_inventory_type=0,
        item_is_equipment=0, item_use='yes'))
    assert leather['item_use'] is None
    assert 'use it yourself' not in leather['prompt']
    assert 'for crafting' in leather['use_ideas']

    # An older payload without item_use states nothing about use.
    old = {k: v for k, v in extra.items()
           if k not in ('item_use', 'item_required_level',
                        'roll_source_guid', 'roll_slot')}
    captured = _run_handler(old)
    assert captured['item_use'] is None
    assert 'use it yourself' not in captured['prompt']
    assert 'requires level' not in captured['prompt']


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
                  'item_is_equipment', 'item_use', 'item_required_level',
                  'roll_source_guid', 'roll_slot'):
        assert f'\\"{field}\\":' in source, field
    world = _src('LLMChatterWorld.cpp')
    assert 'CheckGroupLootRolls();' in world


def test_cpp_switches_and_chance_filter_before_queueing():
    source = _src('LLMChatterGroupLootRoll.cpp')
    assert 'tmpl->InventoryType != INVTYPE_NON_EQUIP' in source
    for field in ('_lootRollCommentNeedEnable', '_lootRollCommentGreedEnable',
                  '_lootRollCommentEquipmentEnable',
                  '_lootRollCommentOtherEnable',
                  '_lootRollCommentNeedChance', '_lootRollCommentGreedChance',
                  '_lootRollCommentNeedCooldown',
                  '_lootRollCommentGreedCooldown'):
        assert field in source, field
    # A skipped vote is still marked handled, so it is not reconsidered.
    loop = source[source.index('state.handledVoters.insert(rawGuid);'):]
    assert loop.index('if (!kindEnabled || !VoteCommentEnabled(vote))') < 80
    assert loop.index('if (urand(1, 100) > VoteCommentChance(vote))') < 200
    shared = _src('LLMChatterShared.cpp')
    assert '{"bot_group_loot_roll",     PRIORITY_HIGH}' in shared
    assert '&LLMChatterConfig::_reactDelayLootRoll' in shared


def test_cpp_cooldown_holds_back_other_rolls_only():
    # Need and Greed keep separate per-group cooldowns, checked only
    # for the first comment on a roll.
    source = _src('LLMChatterGroupLootRoll.cpp')
    assert 'std::map<uint32, time_t> _needCommentCooldowns;' in source
    assert 'std::map<uint32, time_t> _greedCommentCooldowns;' in source
    gate = source[source.index('if (state.queued == 0)\n            {'):]
    gate = gate[:500]
    assert 'VoteCommentCooldowns(bv.vote)' in gate
    assert '< VoteCommentCooldown(bv.vote)' in gate
    assert 'cooldowns[groupId] = now;' in gate
    assert 'PruneCommentCooldowns(NEED, now);' in source
    assert 'PruneCommentCooldowns(GREED, now);' in source


def test_cpp_checks_whether_the_bot_can_use_the_item():
    source = _src('LLMChatterGroupLootRoll.cpp')
    assert 'bot->CanUseItem(tmpl)' in source
    assert 'tmpl->GetSkill()' in source
    assert 'bot->GetSkillValue(skill) == 0' in source
    for value in ('"yes"', '"class"', '"proficiency"', '"skill"',
                  '"level"', '"no"'):
        assert value in source, value


def test_closed_rolls_are_never_commented_late():
    source = _src('LLMChatterGroupLootRoll.cpp')
    cleanup = source[source.index('// Forget rolls that have ended.'):]
    assert "SET status = 'cancelled'" in cleanup
    assert "event_type = 'bot_group_loot_roll'" in cleanup
    assert "AND status = 'pending'" in cleanup
    assert "'$.roll_source_guid'" in cleanup
    assert 'char const* LootRollCommentDropReason(' in source
    assert 'LLMChatterJson::ReadUInt64' in source
    assert 'sGroupMgr->GetGroupByGUID' in source
    header = _src('LLMChatterGroup.h')
    assert 'char const* LootRollCommentDropReason(' in header
    delivery = _src('LLMChatterDelivery.cpp')
    assert 'eventType == "bot_group_loot_roll"' in delivery
    assert 'LootRollCommentDropReason(eventExtraData, botGuid)' in delivery
    gate = delivery[delivery.index(
        'LootRollCommentDropReason(eventExtraData, botGuid)'):][:300]
    assert 'eventType, reason);' in gate


def _drop_reason_body():
    source = _src('LLMChatterGroupLootRoll.cpp')
    start = source.index('char const* LootRollCommentDropReason(')
    return source[start:source.index('\n}\n', start)]


def test_comment_stays_with_its_group_and_vote():
    # A bot that leaves keeps the roll open for the others (only its
    # vote is removed), and party lines go to bot->GetGroup(), so the
    # guard checks the speaker's group and its vote on the roll.
    body = _drop_reason_body()
    assert 'ReadString(\n            eventExtraData, "roll_vote", voteName)' in body
    assert 'ObjectGuid::Create<HighGuid::Player>(botGuid)' in body
    assert 'bot->GetGroup() != group' in body
    assert 'roll->playerVote.find(bot->GetGUID())' in body
    assert 'voted->second != vote' in body
    assert body.count('return "loot_roll_speaker_left";') == 2
    assert '"loot_roll_closed"' in body


def test_guard_fails_closed():
    body = _drop_reason_body()
    fields = body[body.index('if (!LLMChatterJson::ReadUInt64('):]
    assert fields[:fields.index(';')].endswith(
        'voteName))\n        return "loot_roll_closed"')
    assert 'keep the old behaviour' not in body
    assert 'return true;' not in body
    # The only success path is a matching roll with the bot's vote.
    assert body.count('return nullptr;') == 1


def test_a_vote_is_not_scored_like_a_win():
    import inspect
    source = inspect.getsource(handlers.process_group_loot_roll_event)
    assert 'mood_key' not in source
    shared = (TOOLS_DIR / 'chatter_shared.py').read_text(encoding='utf-8')
    assert 'keeps for their looks' not in shared


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


def _conf_value(text, key):
    match = re.search(
        rf'^LLMChatter\.GroupChatter\.{re.escape(key)} = (\d+)$',
        text, re.M)
    assert match, key
    return int(match.group(1))


def test_conf_keys_are_documented_and_loaded():
    loads = _src('LLMChatterConfig.cpp')
    default = (MODULE_DIR / 'conf/mod_llm_chatter.conf.dist').read_text(
        encoding='utf-8')
    quiet = (MODULE_DIR / 'conf/presets/mod_ll_chatter_quieter.conf.dist'
             ).read_text(encoding='utf-8')
    expected = {
        'LootRollComment.Enable': (1, 1),
        'LootRollComment.NeedChance': (50, 25),
        'LootRollComment.GreedChance': (25, 10),
        'LootRollComment.NeedCooldown': (90, 180),
        'LootRollComment.GreedCooldown': (180, 360),
        'LootRollComment.MaxPerItem': (2, 1),
        'LootRollComment.NeedEnable': (1, 1),
        'LootRollComment.GreedEnable': (1, 1),
        'LootRollComment.EquipmentEnable': (1, 1),
        'LootRollComment.OtherEnable': (1, 1),
    }
    for key, (value, quieter) in expected.items():
        assert _conf_value(default, key) == value, key
        assert _conf_value(quiet, key) == quieter, key
        assert f'"{key}"' in loads, key
    # The C++ defaults match the template.
    assert '"LootRollComment.NeedChance", 50)' in loads
    assert '"LootRollComment.GreedChance", 25)' in loads
    assert '"LootRollComment.NeedCooldown", 90)' in loads
    assert '"LootRollComment.GreedCooldown", 180)' in loads
    assert '"LootRollComment.MaxPerItem", 2)' in loads
    assert '"LootRollComment.GreedEnable", true)' in loads
    # Greed is rarer than Need: lower chance, longer cooldown.
    for text in (default, quiet):
        assert (_conf_value(text, 'LootRollComment.GreedChance')
                < _conf_value(text, 'LootRollComment.NeedChance'))
        assert (_conf_value(text, 'LootRollComment.GreedCooldown')
                > _conf_value(text, 'LootRollComment.NeedCooldown'))
    # Coverage is described as bounded, not as every vote.
    for text in (default, quiet):
        assert 'Coverage is bounded' in text
        assert 'while the roll is open' in text


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} loot roll comment tests passed")
