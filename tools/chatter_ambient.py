"""Ambient chatter runtime processors.

N9 moved statement processing from the bridge.
N10 will move conversation processing.
"""

import logging
import random

from chatter_constants import CAPITAL_CITY_ZONES
from chatter_shared import (
    zone_cache,
    parse_single_response,
    get_zone_flavor,
    can_class_use_item,
    query_zone_quests,
    query_zone_loot,
    query_zone_mobs,
    query_bot_spells,
    replace_placeholders,
    cleanup_message,
    call_llm,
    insert_chat_message,
    get_recent_zone_messages,
    is_too_similar,
    get_action_chance,
    select_message_type,
)
from chatter_prompts import (
    build_plain_statement_prompt,
    build_quest_statement_prompt,
    build_loot_statement_prompt,
    build_quest_reward_statement_prompt,
    build_spell_statement_prompt,
    build_trade_statement_prompt,
)

logger = logging.getLogger(__name__)


def process_statement(
    db, cursor, client, config, request, bot: dict
):
    """Process a single statement request."""
    channel = 'general'

    # Select message type
    zone_id = request.get('zone_id', 0)
    current_weather = request.get('weather', 'clear')
    msg_type = select_message_type()

    # Skip loot/trade in capital cities (no zone
    # creatures to reference, causes empty queries)
    if (
        msg_type in ("loot", "trade")
        and zone_id in CAPITAL_CITY_ZONES
    ):
        msg_type = "plain"

    logger.info(f"Statement type: {msg_type}")

    # Get zone data if needed
    quest_data = None
    item_data = None
    spell_data = None

    if msg_type == "quest" or msg_type == "quest_reward":
        quests = query_zone_quests(
            config, zone_id, bot['level']
        )
        if quests:
            quest_data = random.choice(quests)
            logger.info(
                f"Selected quest: "
                f"{quest_data['quest_name']}"
            )
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "loot":
        loot = query_zone_loot(
            config, zone_id, bot['level']
        )
        if loot:
            cooldown = int(config.get(
                'LLMChatter.LootRecentCooldownSeconds',
                0
            ))
            if cooldown > 0:
                recent_ids = (
                    zone_cache.get_recent_loot_ids(
                        zone_id, cooldown
                    )
                )
                filtered = [
                    item for item in loot
                    if item.get('item_id')
                    not in recent_ids
                ]
                if filtered:
                    loot = filtered
            # Weight selection by quality
            # Quality: 0=gray, 1=white, 2=green,
            #          3=blue, 4=epic
            quality_weights = {
                0: 35, 1: 30, 2: 22, 3: 10, 4: 3
            }
            weights = [
                quality_weights.get(
                    item.get('item_quality', 2), 10
                )
                for item in loot
            ]
            item_data = random.choices(
                loot, weights=weights, k=1
            )[0]
            if (
                cooldown > 0
                and item_data.get('item_id')
            ):
                zone_cache.mark_loot_seen(
                    zone_id, item_data['item_id']
                )
            # Check if bot's class can use the item
            item_can_use = can_class_use_item(
                bot['class'],
                item_data.get('allowable_class', -1)
            )
            quality_names = {
                0: "gray", 1: "white", 2: "green",
                3: "blue", 4: "epic"
            }
            logger.info(
                f"Selected loot: "
                f"{item_data['item_name']} "
                f"({quality_names.get(item_data.get('item_quality', 2), 'unknown')}) "
                f"- {bot['class']} can use: "
                f"{item_can_use}"
            )
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "trade":
        loot = query_zone_loot(
            config, zone_id, bot['level']
        )
        if loot:
            cooldown = int(config.get(
                'LLMChatter.LootRecentCooldownSeconds',
                0
            ))
            if cooldown > 0:
                recent_ids = (
                    zone_cache.get_recent_loot_ids(
                        zone_id, cooldown
                    )
                )
                filtered = [
                    item for item in loot
                    if item.get('item_id')
                    not in recent_ids
                ]
                if filtered:
                    loot = filtered
            quality_weights = {
                0: 35, 1: 30, 2: 22, 3: 10, 4: 3
            }
            weights = [
                quality_weights.get(
                    item.get('item_quality', 2), 10
                )
                for item in loot
            ]
            item_data = random.choices(
                loot, weights=weights, k=1
            )[0]
            if (
                cooldown > 0
                and item_data.get('item_id')
            ):
                zone_cache.mark_loot_seen(
                    zone_id, item_data['item_id']
                )
            logger.info(
                f"Selected trade item: "
                f"{item_data['item_name']}"
            )
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "spell":
        spells = query_bot_spells(
            config, bot['class'], bot['level']
        )
        if spells:
            spell_data = random.choice(spells)
            logger.info(
                f"Selected spell: "
                f"{spell_data['spell_name']} "
                f"(id={spell_data['spell_id']}, "
                f"req_level="
                f"{spell_data['req_level']})"
            )
        else:
            msg_type = "plain"  # Fallback

    # Fetch recent zone messages for anti-repetition
    recent_msgs = get_recent_zone_messages(
        db, zone_id
    )

    # Build appropriate prompt
    allow_action = (
        random.random() < get_action_chance()
    )
    if msg_type == "plain":
        # Get zone mobs for context
        zone_mobs = []
        mobs = query_zone_mobs(
            config, zone_id, bot['level']
        )
        if mobs:
            zone_mobs = random.sample(
                mobs, min(10, len(mobs))
            )
        # Log zone context being used
        zone_flavor = get_zone_flavor(zone_id)
        logger.info(
            f"Zone context: id={zone_id}, "
            f"flavor={'yes' if zone_flavor else 'no'}"
            f", mobs={len(zone_mobs)}, "
            f"weather={current_weather}"
        )
        prompt = build_plain_statement_prompt(
            bot, zone_id, zone_mobs,
            config, current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    elif msg_type == "quest":
        prompt = build_quest_statement_prompt(
            bot, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    elif msg_type == "loot":
        prompt = build_loot_statement_prompt(
            bot, item_data, item_can_use,
            config, current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    elif msg_type == "quest_reward":
        prompt = build_quest_reward_statement_prompt(
            bot, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
        # Also set item_data for replacement
        if quest_data and quest_data.get('item1_name'):
            item_data = {
                'item_id': quest_data['item1_id'],
                'item_name': quest_data['item1_name'],
                'item_quality': quest_data.get(
                    'item1_quality', 2
                )
            }
    elif msg_type == "trade":
        prompt = build_trade_statement_prompt(
            bot, item_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    elif msg_type == "spell":
        prompt = build_spell_statement_prompt(
            bot, spell_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    else:
        prompt = build_plain_statement_prompt(
            bot, zone_id,
            config=config,
            current_weather=current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )

    # Call LLM
    response = call_llm(
        client, prompt, config,
        context=f"ambient:{bot['name']}"
    )

    if response:
        parsed = parse_single_response(response)
        message = parsed['message']
        message = replace_placeholders(
            message, quest_data, item_data,
            spell_data
        )
        message = cleanup_message(
            message, action=parsed.get('action')
        )

        if is_too_similar(message, recent_msgs):
            logger.info(
                f"Anti-repetition: dropped "
                f"statement from {bot['name']}"
            )
            return True

        logger.info(
            f"Statement from {bot['name']} "
            f"[{msg_type}]: {message}"
        )

        # Insert for delivery
        insert_chat_message(
            db, bot['guid'], bot['name'], message,
            channel=channel,
            delay_seconds=0,
            queue_id=request['id'],
            sequence=0,
        )

        return True
    return False


def process_conversation(*args, **kwargs):
    """Placeholder for N10 extraction."""
    raise NotImplementedError(
        "process_conversation is not moved yet"
    )
