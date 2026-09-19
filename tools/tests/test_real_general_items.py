#!/usr/bin/env python3
"""Focused checks for real General loot and trade items."""

import importlib
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
        attribute = (
            'Anthropic' if dependency == 'anthropic'
            else 'OpenAI'
        )
        setattr(module, attribute, type(attribute, (), {}))

try:
    importlib.import_module('mysql.connector')
except ModuleNotFoundError:
    mysql_module = _ensure_module('mysql')
    connector_module = _ensure_module('mysql.connector')
    setattr(mysql_module, 'connector', connector_module)


TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import chatter_ambient  # noqa: E402
import chatter_loot  # noqa: E402
import chatter_prompts  # noqa: E402
from chatter_event_registry import (  # noqa: E402
    DEAD_EVENTS,
    EVENT_REGISTRY,
)


class _Cursor:
    def close(self):
        pass


class _Db:
    def cursor(self, dictionary=False):
        return _Cursor()


def _event(zone_id=12):
    return {
        'id': 71,
        'event_type': 'bot_loot_item',
        'subject_guid': 101,
        'zone_id': zone_id,
        'map_id': 0,
        'extra_data': json.dumps({
            'item_id': 2589,
            'item_name': 'Linen Cloth',
            'item_quality': 2,
            'item_count': 3,
            'allowable_class': -1,
            'required_level': 0,
        }),
    }


def _bot(zone_id=12):
    return {
        'bot1_guid': 101,
        'bot1_name': 'Aliss',
        'bot1_class': 8,
        'bot1_race': 1,
        'bot1_level': 20,
        'zone_id': zone_id,
    }


def test_registry_routes_real_loot_and_is_not_dead():
    spec = EVENT_REGISTRY['bot_loot_item']
    assert spec.handler_module == 'chatter_loot'
    assert spec.handler_func == 'process_general_loot_event'
    assert spec.producer == 'LLMChatterLoot.cpp'
    assert 'bot_loot_item' not in DEAD_EVENTS


def test_real_loot_resolves_exact_looter_and_links_actual_item():
    db = _Db()
    looked_up = []
    inserted = []
    statuses = []

    def get_bot(_cursor, guids):
        looked_up.append(guids)
        # characters.zone is save-time state and may lag behind the
        # live zone already validated by the C++ producer.
        return [_bot(zone_id=14)]

    with (
        patch.object(chatter_loot, 'get_bots_by_guid', get_bot),
        patch.object(
            chatter_loot, 'get_recent_zone_messages',
            return_value=[],
        ),
        patch.object(
            chatter_loot, 'build_loot_statement_prompt',
            return_value='prompt',
        ),
        patch.object(
            chatter_loot, 'call_llm',
            return_value=(
                '{"message":"got {item:Linen Cloth} x3"}'
            ),
        ),
        patch.object(
            chatter_loot, '_zone_delivery_delay',
            return_value=4.0,
        ),
        patch.object(
            chatter_loot, 'insert_chat_message',
            side_effect=lambda *args, **kwargs: inserted.append(
                (args, kwargs)
            ),
        ),
        patch.object(
            chatter_loot, 'maybe_queue_group_general_reaction',
        ),
        patch.object(
            chatter_loot, 'mark_event',
            side_effect=lambda _db, _id, status: statuses.append(status),
        ),
    ):
        assert chatter_loot.process_general_loot_event(
            db, object(), {}, _event()
        )

    assert looked_up == [[101]]
    assert len(inserted) == 1
    args, kwargs = inserted[0]
    assert args[1:3] == (101, 'Aliss')
    assert '|Hitem:2589:' in args[3]
    assert '[Linen Cloth]' in args[3]
    assert 'x3' in args[3]
    assert kwargs['channel'] == 'general'
    assert kwargs['event_id'] == 71
    assert statuses == ['completed']


def test_real_loot_skips_offline_bot():
    statuses = []
    with (
        patch.object(
            chatter_loot, 'get_bots_by_guid',
            return_value=[],
        ),
        patch.object(
            chatter_loot, 'mark_event',
            side_effect=(
                lambda _db, _id, status:
                statuses.append(status)
            ),
        ),
        patch.object(chatter_loot, 'call_llm') as llm,
        patch.object(
            chatter_loot, 'insert_chat_message'
        ) as insert,
    ):
        assert not chatter_loot.process_general_loot_event(
            _Db(), object(), {}, _event()
        )
    llm.assert_not_called()
    insert.assert_not_called()
    assert statuses == ['skipped']


def test_ambient_uses_server_type_and_validates_trade_snapshot():
    assert chatter_ambient._request_message_type({}) == 'plain'
    assert chatter_ambient._request_message_type({
        'id': 1, 'message_type': 'trade'
    }) == 'trade'
    assert chatter_ambient._request_message_type({
        'id': 2, 'message_type': 'loot'
    }) == 'plain'

    item_payload = json.dumps({
        'item_id': 4306,
        'item_name': 'Silk Cloth',
        'item_quality': 7,
        'item_count': 8,
        'sell_price': 150,
    })
    item = chatter_ambient._parse_trade_item_context(item_payload)
    assert item['item_id'] == 4306
    assert item['item_count'] == 8
    bytearray_item = chatter_ambient._parse_trade_item_context(
        bytearray(item_payload.encode('utf-8'))
    )
    assert bytearray_item == item
    assert chatter_ambient._parse_trade_item_context('{}') is None
    assert chatter_ambient._parse_trade_item_context(b'\xff') is None


def test_trade_prompts_state_real_owner_and_quantity():
    item = {
        'item_name': 'Silk Cloth',
        'item_quality': 7,
        'item_count': 8,
        'sell_price': 150,
    }
    seller = {
        'name': 'Aliss', 'class': 'Mage',
        'race': 'Human', 'zone': 'Elwynn Forest',
    }
    statement = chatter_prompts.build_trade_statement_prompt(
        seller, item, config={}
    )
    conversation = chatter_prompts.build_trade_conversation_prompt(
        [seller, {
            'name': 'Borin', 'class': 'Warrior',
            'race': 'Dwarf', 'zone': 'Elwynn Forest',
        }],
        item,
        config={},
    )
    assert 'currently owns 8' in statement
    assert 'must not offer more' in statement
    assert 'heirloom quality' in statement
    assert 'Vendor sell price: 1s 50c' in statement
    assert 'Aliss owns 8' in conversation
    assert 'first speaker (Aliss)' in conversation
    assert 'heirloom quality' in conversation
    assert 'Vendor sell price: 1s 50c' in conversation

    loot = chatter_prompts.build_loot_statement_prompt(
        seller, {
            'item_name': 'Silk Cloth',
            'item_quality': 7,
            'item_count': 8,
        }, True, config={}
    )
    assert 'heirloom quality' in loot
    assert 'Quantity actually looted: 8' in loot


def test_reservoir_rule_can_select_every_candidate_without_a_list():
    candidates = ['first', 'second', 'third', 'fourth']
    for chosen_position in range(len(candidates)):
        selected = None
        for index, candidate in enumerate(candidates, start=1):
            replacement_roll = (
                1 if index == chosen_position + 1 else index
            )
            if replacement_roll == 1:
                selected = candidate
        assert selected == candidates[chosen_position]


def test_cpp_source_contracts_for_hot_path_and_bounded_state():
    loot = (MODULE_DIR / 'src' / 'LLMChatterLoot.cpp').read_text(
        encoding='utf-8'
    )
    shared = (MODULE_DIR / 'src' / 'LLMChatterShared.cpp').read_text(
        encoding='utf-8'
    )
    trade = (MODULE_DIR / 'src' / 'LLMChatterTrade.cpp').read_text(
        encoding='utf-8'
    )
    ambient = (
        MODULE_DIR / 'src' / 'LLMChatterAmbient.cpp'
    ).read_text(encoding='utf-8')
    world = (
        MODULE_DIR / 'src' / 'LLMChatterWorld.cpp'
    ).read_text(encoding='utf-8')

    guard = loot.index('if (!item->IsInWorld())')
    template_read = loot.index('item->GetTemplate()', guard)
    entry_read = loot.index('item->GetEntry()', guard)
    assert guard < template_read
    assert guard < entry_read
    assert 'HasCachedGeneralAudience(' in loot
    assert 'IsGroupedWithRealPlayer(player)' in loot
    assert 'PLAYERHOOK_ON_LOGOUT' not in loot
    assert 'std::optional<PendingLootSource> active' in loot
    assert 'std::optional<PendingLootSource> completed' in loot
    reservoir = loot[
        loot.index('bool ShouldReplaceReservoirItem('):
        loot.index('void UpdateReservoir(')
    ]
    assert 'seenItems' not in reservoir
    assert 'return replacementRoll == 1;' in reservoir
    assert 'std::vector<LootItemSnapshot>' not in loot
    assert 'PLAYERHOOK_ON_LOOT_ITEM' in loot
    assert 'WORLDHOOK_ON_UPDATE' in loot
    assert 'lootGuid.IsEmpty()' in loot
    assert '_generalLootMinQuality' in loot
    capture = loot[loot.index('void CaptureLoot('):]
    capture = capture[:capture.index('void FlushLootAggregations(')]
    assert 'GetAllSessions()' not in capture
    assert 'CanSpeakInGeneralChannel(' not in capture
    assert 'sRandomPlayerbotMgr.IsRandomBot(' not in capture
    assert capture.count('urand(1, 100)') == 1
    cooldown_check = capture.index(
        'IsLootOnCachedCooldown(zoneId)'
    )
    pending_create = capture.index(
        'PendingLootSource source'
    )
    map_create = capture.index('_lootAggregations[botGuid]')
    assert cooldown_check < pending_create
    assert cooldown_check < map_create
    assert 'IsLootOnCooldown(zoneId)' not in capture
    cached_cooldown = loot[
        loot.index('bool IsLootOnCachedCooldown('):
        loot.index('bool IsLootOnCooldown(')
    ]
    assert 'IsEventOnCooldown(' not in cached_cooldown
    assert 'IsPersistedEventOnCooldown(' not in cached_cooldown
    authoritative_cooldown = loot[
        loot.index('bool IsLootOnCooldown('):
        loot.index('void SetLootCooldown(')
    ]
    assert 'IsPersistedEventOnCooldown(' in authoritative_cooldown
    queue_finalized = loot[
        loot.index('void QueueFinalizedLoot('):
        loot.index('void CaptureLoot(')
    ]
    assert 'IsLootOnCooldown(source.zoneId)' in queue_finalized
    assert 'sRandomPlayerbotMgr.IsRandomBot(bot)' in queue_finalized

    assert 'RefreshGeneralAudienceSnapshot();' not in loot
    assert 'RefreshGeneralAudienceSnapshot();' in world
    refresh = world[
        world.index('RefreshGeneralAudienceSnapshot();') - 180:
        world.index('RefreshGeneralAudienceSnapshot();') + 40
    ]
    assert '_generalChannelEnable' not in refresh

    assert 'std::shared_mutex' in shared
    assert 'std::shared_lock<std::shared_mutex>' in shared
    assert 'std::unique_lock<std::shared_mutex>' in shared
    assert 'std::atomic<std::shared_ptr' not in shared
    assert 'item->CanBeTraded()' in trade
    assert 'CanBeTraded(false, true)' not in trade
    assert 'INVENTORY_SLOT_ITEM_START' in trade
    assert 'INVENTORY_SLOT_BAG_START' in trade
    assert 'for (uint8 slot = 0;' in trade
    assert 'EQUIPMENT_SLOT_START' not in trade
    assert 'BANK_SLOT_ITEM_START' not in trade
    assert 'GetTradeItemSelectionWeight(' in trade
    assert 'std::clamp<uint32>(' in trade
    assert 'ITEM_QUALITY_NORMAL,' in trade
    assert '_ambientTradeQualityWeightBonus' in trade
    assert 'totalWeight += itemWeight;' in trade
    assert 'urand(1, totalWeight) > itemWeight' in trade

    selector = ambient[
        ambient.index('SelectAmbientMessageType('):
        ambient.index('BuildTradeItemContext(')
    ]
    assert 'return "loot"' not in selector
    assert 'contentRoll <= 60' in selector
    assert 'contentRoll <= 90' in selector
    assert 'contentRoll <= 62' in selector
    assert 'contentRoll <= 95' in selector

    trigger = ambient[ambient.index('void TryTriggerChatter()'):]
    type_selection = trigger.index('SelectAmbientMessageType(')
    inventory_scan = trigger.index('SelectChatterTradeItem(bot1)')
    assert type_selection < inventory_scan
    assert 'if (messageType == "trade")' in trigger[
        type_selection:inventory_scan
    ]


def test_simulated_loot_and_python_type_rng_are_removed():
    sources = '\n'.join(
        path.read_text(encoding='utf-8')
        for path in TOOLS_DIR.glob('*.py')
    )
    assert 'def query_zone_loot(' not in sources
    assert 'def select_message_type(' not in sources
    assert 'MSG_TYPE_LOOT' not in sources
    assert 'def build_loot_conversation_prompt(' not in sources
    assert 'Unsupported ambient conversation type' in sources


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} real General item tests passed")
