#!/usr/bin/env python3
"""
LLM Chatter Bridge - Generates dynamic bot
conversations via LLM

Supports Anthropic (Claude), OpenAI (GPT), and
Ollama models.

This script:
1. Polls the database for pending chatter requests
2. Sends prompts to LLM API based on bot
   personalities and zone context
3. Supports diverse message types: plain, quest
   links, item drops, quest+rewards
4. Parses responses and inserts messages with
   dynamic timing delays
"""

import argparse
import json
import logging
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

import anthropic
import openai
import mysql.connector

from chatter_constants import (
    MSG_TYPE_PLAIN, MSG_TYPE_QUEST,
    MSG_TYPE_LOOT, MSG_TYPE_QUEST_REWARD,
    MSG_TYPE_TRADE, MSG_TYPE_SPELL,
    CAPITAL_CITY_ZONES,
)
from chatter_shared import (
    zone_cache,
    get_zone_name, get_class_name, get_race_name,
    get_chatter_mode, build_race_class_context,
    set_race_lore_chance,
    set_race_vocab_chance,
    set_action_chance,
    get_action_chance,
    append_json_instruction,
    parse_single_response,
    parse_config, get_db_connection,
    wait_for_database,
    get_zone_flavor,
    can_class_use_item,
    query_zone_quests, query_zone_loot,
    query_zone_mobs, query_bot_spells,
    replace_placeholders, cleanup_message,
    strip_speaker_prefix,
    select_message_type, calculate_dynamic_delay,
    call_llm,
    parse_conversation_response,
    extract_conversation_msg_count,
    insert_chat_message,
    pick_emote_for_statement,
    get_recent_zone_messages,
    is_too_similar,
)
from chatter_prompts import (
    pick_random_tone,
    get_environmental_context,
    build_plain_statement_prompt,
    build_quest_statement_prompt,
    build_loot_statement_prompt,
    build_quest_reward_statement_prompt,
    build_spell_statement_prompt,
    build_spell_conversation_prompt,
    build_plain_conversation_prompt,
    build_quest_conversation_prompt,
    build_loot_conversation_prompt,
    build_trade_statement_prompt,
    build_trade_conversation_prompt,
    build_event_conversation_prompt,
)
from chatter_events import (
    build_event_context,
    cleanup_expired_events,
    reset_stuck_processing_events,
)
from chatter_group import (
    init_group_config,
    process_group_event,
    process_group_kill_event,
    process_group_death_event,
    process_group_loot_event,
    process_group_combat_event,
    process_group_player_msg_event,
    process_group_levelup_event,
    process_group_quest_complete_event,
    process_group_quest_objectives_event,
    process_group_achievement_event,
    process_group_spell_cast_event,
    process_group_resurrect_event,
    process_group_zone_transition_event,
    process_group_quest_accept_event,
    process_group_discovery_event,
    process_group_dungeon_entry_event,
    process_group_wipe_event,
    process_group_corpse_run_event,
    process_group_low_health_event,
    process_group_oom_event,
    process_group_aggro_loss_event,
    check_idle_group_chatter,
)
from chatter_general import (
    init_general_config,
    process_general_player_msg_event,
)
from chatter_cache import refill_precache_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST PROCESSING
# =============================================================================
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
        emote = (
            parsed.get('emote')
            or pick_emote_for_statement(message)
        )
        insert_chat_message(
            db, bot['guid'], bot['name'], message,
            channel=channel,
            delay_seconds=0,
            queue_id=request['id'],
            sequence=0,
            emote=emote,
        )

        return True
    return False


def process_conversation(
    db, cursor, client, config,
    request, bots: List[dict]
):
    """Process a conversation request with 2-4 bots.

    Args:
        db: Database connection
        cursor: Database cursor
        client: LLM client (Anthropic or OpenAI)
        config: Configuration dict
        request: Queue request row
        bots: List of 2-4 bot dicts with guid, name,
              class, race, level, zone
    """
    channel = 'general'
    bot_count = len(bots)
    bot_names = [b['name'] for b in bots]

    # Create guid lookup for message insertion
    bot_guids = {b['name']: b['guid'] for b in bots}

    logger.info(
        f"Processing {bot_count}-bot conversation: "
        f"{', '.join(bot_names)}"
    )

    zone_id = request.get('zone_id', 0)
    current_weather = request.get('weather', 'clear')

    # Fetch recent zone messages for anti-repetition
    recent_msgs = get_recent_zone_messages(
        db, zone_id
    )

    # Select message type
    # (conversations: 45% plain, 20% quest,
    #  15% loot, 10% trade, 10% spell)
    roll = random.randint(1, 100)
    if roll <= 45:
        msg_type = "plain"
    elif roll <= 65:
        msg_type = "quest"
    elif roll <= 80:
        msg_type = "loot"
    elif roll <= 90:
        msg_type = "trade"
    else:
        msg_type = "spell"

    # Get quest/loot/spell data if needed
    quest_data = None
    item_data = None
    spell_data = None

    if msg_type == "quest":
        quests = query_zone_quests(
            config,
            request.get('zone_id', 0),
            bots[0]['level']
        )
        if quests:
            quest_data = random.choice(quests)
            logger.info(
                f"Selected quest: "
                f"{quest_data['quest_name']}"
            )
        else:
            msg_type = "plain"

    if msg_type == "loot":
        loot = query_zone_loot(
            config,
            request.get('zone_id', 0),
            bots[0]['level']
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
                0: 30, 1: 30, 2: 25, 3: 12, 4: 3
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
                f"Selected loot for conversation: "
                f"{item_data['item_name']}"
            )
        else:
            msg_type = "plain"

    if msg_type == "trade":
        loot = query_zone_loot(
            config,
            request.get('zone_id', 0),
            bots[0]['level']
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
                0: 30, 1: 30, 2: 25, 3: 12, 4: 3
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
                f"Selected trade item for "
                f"conversation: "
                f"{item_data['item_name']}"
            )
        else:
            msg_type = "plain"

    if msg_type == "spell":
        spells = query_bot_spells(
            config, bots[0]['class'],
            bots[0]['level']
        )
        if spells:
            spell_data = random.choice(spells)
            logger.info(
                f"Selected spell for conversation: "
                f"{spell_data['spell_name']} "
                f"(id={spell_data['spell_id']})"
            )
        else:
            msg_type = "plain"

    # Build prompt
    if msg_type == "plain":
        # Get zone mobs for context
        zone_mobs = []
        mobs = query_zone_mobs(
            config, zone_id, bots[0]['level']
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
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_plain_conversation_prompt(
            bots, zone_id, zone_mobs,
            config, current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    elif msg_type == "quest":
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_quest_conversation_prompt(
            bots, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    elif msg_type == "trade":
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_trade_conversation_prompt(
            bots, item_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    elif msg_type == "spell":
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_spell_conversation_prompt(
            bots, spell_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )
    else:  # loot
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_loot_conversation_prompt(
            bots, item_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )

    # Call LLM
    conversation_max_tokens = int(
        config.get(
            'LLMChatter.ConversationMaxTokens',
            config.get('LLMChatter.MaxTokens', 200)
        )
    )
    bot_names_ctx = ','.join(bot_names)
    response = call_llm(
        client, prompt, config,
        max_tokens_override=conversation_max_tokens,
        context=f"ambient-conv:{bot_names_ctx}"
    )

    if response:
        logger.info(
            f"LLM raw response "
            f"(len={len(response)}):\n{response}"
        )
        messages = parse_conversation_response(
            response, bot_names
        )

        if not messages:
            msg_count = extract_conversation_msg_count(
                prompt
            )
            repair_prompt = (
                "Your previous output was invalid "
                "JSON. Output ONLY a JSON array of "
                f"{msg_count if msg_count else 'the required number of'} "
                f"messages with the speakers: "
                f"{', '.join(bot_names)}. Use double "
                "quotes, escape quotes/newlines, "
                "no trailing commas, no code fences."
            )
            response = call_llm(
                client, repair_prompt, config,
                max_tokens_override=(
                    conversation_max_tokens
                ),
                context="json-repair"
            )
            if response:
                messages = (
                    parse_conversation_response(
                        response, bot_names
                    )
                )

        if messages:
            logger.info(
                f"Conversation in {bots[0]['zone']} "
                f"with {len(messages)} messages "
                f"({bot_count} participants):"
            )

            cumulative_delay = 0.0
            for i, msg in enumerate(messages):
                bot_guid = bot_guids.get(
                    msg['name'], bots[0]['guid']
                )

                # Replace placeholders and cleanup
                final_message = replace_placeholders(
                    msg['message'], quest_data,
                    item_data, spell_data
                )
                final_message = strip_speaker_prefix(
                    final_message, msg['name']
                )
                final_message = cleanup_message(
                    final_message,
                    action=msg.get('action'),
                )

                if i > 0:
                    delay = calculate_dynamic_delay(
                        len(final_message), config
                    )
                    cumulative_delay += delay
                    logger.info(
                        f"    Delay calc: "
                        f"msg_len={len(final_message)}"
                        f", delay={delay:.1f}s"
                    )

                insert_chat_message(
                    db, bot_guid,
                    msg['name'], final_message,
                    channel=channel,
                    delay_seconds=cumulative_delay,
                    queue_id=request['id'],
                    sequence=i,
                    emote=msg.get('emote'),
                )

                logger.info(
                    f"  [{i}] +{cumulative_delay:.1f}s"
                    f" {msg['name']}: {final_message}"
                )

            db.commit()
            return True
    return False


def process_pending_requests(
    db, client: anthropic.Anthropic, config: dict
):
    """Process all pending chatter requests."""
    cursor = db.cursor(dictionary=True)

    # Get pending requests
    cursor.execute("""
        SELECT * FROM llm_chatter_queue
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT 1
    """)
    request = cursor.fetchone()

    if not request:
        return False

    request_id = request['id']
    request_type = request['request_type']

    logger.info(
        f"Processing {request_type} request "
        f"#{request_id}"
    )

    # Mark as processing
    cursor.execute(
        "UPDATE llm_chatter_queue "
        "SET status = 'processing' WHERE id = %s",
        (request_id,)
    )
    db.commit()

    try:
        # Get zone_id from the request
        zone_id = request.get('zone_id', 0)
        request['zone_id'] = zone_id if zone_id else 0

        if request_type == 'statement':
            raw_class = request['bot1_class']
            raw_race = request['bot1_race']
            bot = {
                'guid': request['bot1_guid'],
                'name': request['bot1_name'],
                'class': (
                    get_class_name(raw_class)
                    if isinstance(raw_class, int)
                    else raw_class
                ),
                'race': (
                    get_race_name(raw_race)
                    if isinstance(raw_race, int)
                    else raw_race
                ),
                'level': request['bot1_level'],
                'zone': request['bot1_zone']
            }
            success = process_statement(
                db, cursor, client,
                config, request, bot
            )
        else:
            # Build list of 2-4 bots from request
            bots = []

            # Helper to build a bot dict with
            # text race/class
            def _make_bot(
                prefix, zone_override=None
            ):
                rc = request[f'{prefix}_class']
                rr = request[f'{prefix}_race']
                zone_key = f'{prefix}_zone'
                if zone_override:
                    zone = zone_override
                elif zone_key in request:
                    zone = request[zone_key]
                else:
                    zone = request['bot1_zone']
                return {
                    'guid': request[
                        f'{prefix}_guid'
                    ],
                    'name': request[
                        f'{prefix}_name'
                    ],
                    'class': (
                        get_class_name(rc)
                        if isinstance(rc, int)
                        else rc
                    ),
                    'race': (
                        get_race_name(rr)
                        if isinstance(rr, int)
                        else rr
                    ),
                    'level': request[
                        f'{prefix}_level'
                    ],
                    'zone': zone,
                }

            # Bot 1 (always present)
            bots.append(_make_bot('bot1'))

            # Bot 2 (always present for conversations)
            if request.get('bot2_guid'):
                bots.append(_make_bot(
                    'bot2', request['bot1_zone']
                ))

            # Bot 3 (optional)
            if request.get('bot3_guid'):
                bots.append(_make_bot(
                    'bot3', request['bot1_zone']
                ))

            # Bot 4 (optional)
            if request.get('bot4_guid'):
                bots.append(_make_bot(
                    'bot4', request['bot1_zone']
                ))

            success = process_conversation(
                db, cursor, client,
                config, request, bots
            )

        # Mark as completed only if processing
        # succeeded
        if success:
            cursor.execute(
                "UPDATE llm_chatter_queue "
                "SET status = 'completed', "
                "processed_at = NOW() "
                "WHERE id = %s",
                (request_id,)
            )
            db.commit()
            return True
        else:
            logger.warning(
                f"Request #{request_id} processing "
                f"returned failure, marking as failed"
            )
            cursor.execute(
                "UPDATE llm_chatter_queue "
                "SET status = 'failed' "
                "WHERE id = %s",
                (request_id,)
            )
            db.commit()
            return False

    except Exception as e:
        logger.error(
            f"Error processing request "
            f"#{request_id}: {e}"
        )
        cursor.execute(
            "UPDATE llm_chatter_queue "
            "SET status = 'failed' WHERE id = %s",
            (request_id,)
        )
        db.commit()
        return False


# =============================================================================
# EVENT PROCESSING
# =============================================================================
def fetch_pending_events(db, config, max_count):
    """Fetch and atomically claim up to max_count
    pending events for parallel processing.

    Returns list of claimed event dicts, each with
    an added '_group_id' key for group serialization.
    """
    cursor = db.cursor(dictionary=True)

    # Single unified query — parallel processing
    # makes transport-specific priority redundant
    cursor.execute("""
        SELECT e.*
        FROM llm_chatter_events e
        WHERE e.status = 'pending'
          AND (e.react_after IS NULL
               OR e.react_after <= NOW())
          AND (e.expires_at IS NULL
               OR e.expires_at > NOW())
          AND (
              e.zone_id IS NULL
              OR e.zone_id = 0
              OR e.event_type LIKE 'bot_group%%'
              OR (
                  EXISTS (
                      SELECT 1 FROM characters c
                      JOIN acore_auth.account a
                          ON c.account = a.id
                      WHERE c.online = 1
                        AND c.zone = e.zone_id
                        AND a.username
                            LIKE 'RNDBOT%%%%'
                  )
                  AND EXISTS (
                      SELECT 1 FROM characters rp
                      JOIN acore_auth.account a
                          ON rp.account = a.id
                      WHERE rp.online = 1
                        AND rp.zone = e.zone_id
                        AND a.username
                            NOT LIKE 'RNDBOT%%%%'
                  )
              )
          )
        ORDER BY e.priority DESC,
                 e.created_at ASC
        LIMIT %s
    """, (max_count,))
    candidates = cursor.fetchall()

    claimed = []
    for event in candidates:
        # Atomic claim via CAS
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = 'processing', "
            "processed_at = NOW() "
            "WHERE id = %s AND status = 'pending'",
            (event['id'],)
        )
        db.commit()
        if cursor.rowcount == 1:
            # Extract group_id for serialization
            group_id = None
            if event.get('event_type', '').startswith(
                'bot_group'
            ):
                try:
                    extra = event.get('extra_data')
                    if isinstance(extra, str):
                        extra = json.loads(extra)
                    if isinstance(extra, dict):
                        group_id = extra.get(
                            'group_id'
                        )
                except Exception:
                    pass
            event['_group_id'] = group_id
            claimed.append(event)

    return claimed


def process_single_event(event, client, config):
    """Process a single claimed event with its own
    DB connection. Designed for concurrent execution
    in a ThreadPoolExecutor.
    """
    event_id = event['id']
    event_type = event['event_type']
    zone_id = event.get('zone_id')
    db = None
    try:
        db = get_db_connection(config)
        cursor = db.cursor(dictionary=True)

        # Group events bypass all zone/bot checks
        # NOTE: Using logger.warning so group events
        # remain visible when log level is WARNING
        if event_type == 'bot_group_join':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_event(
                db, client, config, event
            )
        if event_type == 'bot_group_kill':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_kill_event(
                db, client, config, event
            )
        if event_type == 'bot_group_death':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_death_event(
                db, client, config, event
            )
        if event_type == 'bot_group_loot':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_loot_event(
                db, client, config, event
            )
        if event_type == 'bot_group_combat':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_combat_event(
                db, client, config, event
            )
        if event_type == 'bot_group_player_msg':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_player_msg_event(
                db, client, config, event
            )
        if event_type == 'bot_group_levelup':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_levelup_event(
                db, client, config, event
            )
        if event_type == 'bot_group_quest_complete':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_quest_complete_event(
                db, client, config, event
            )
        if event_type == 'bot_group_quest_objectives':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return (
                process_group_quest_objectives_event(
                    db, client, config, event
                )
            )
        if event_type == 'bot_group_achievement':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_achievement_event(
                db, client, config, event
            )
        if event_type == 'bot_group_spell_cast':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_spell_cast_event(
                db, client, config, event
            )
        if event_type == 'bot_group_resurrect':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_resurrect_event(
                db, client, config, event
            )
        if event_type == 'bot_group_zone_transition':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return (
                process_group_zone_transition_event(
                    db, client, config, event
                )
            )
        if event_type == 'bot_group_quest_accept':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_quest_accept_event(
                db, client, config, event
            )
        if event_type == 'bot_group_discovery':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_discovery_event(
                db, client, config, event
            )
        if event_type == 'bot_group_dungeon_entry':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_dungeon_entry_event(
                db, client, config, event
            )
        if event_type == 'bot_group_wipe':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_wipe_event(
                db, client, config, event
            )
        if event_type == 'bot_group_corpse_run':
            logger.warning(
                f"Group event #{event_id}: "
                f"{event_type}")
            return process_group_corpse_run_event(
                db, client, config, event
            )
        if event_type == 'bot_group_low_health':
            logger.warning(
                f"State callout #{event_id}: "
                f"{event_type}")
            return process_group_low_health_event(
                db, client, config, event
            )
        if event_type == 'bot_group_oom':
            logger.warning(
                f"State callout #{event_id}: "
                f"{event_type}")
            return process_group_oom_event(
                db, client, config, event
            )
        if event_type == 'bot_group_aggro_loss':
            logger.warning(
                f"State callout #{event_id}: "
                f"{event_type}")
            return process_group_aggro_loss_event(
                db, client, config, event
            )

        # General channel player message reaction
        if event_type == 'player_general_msg':
            logger.warning(
                f"General chat event #{event_id}: "
                f"{event_type}")
            return process_general_player_msg_event(
                event, db, client, config
            )

        logger.info(
            f"Processing event #{event_id}: "
            f"{event_type}"
        )

        # Event already claimed as 'processing' by
        # fetch_pending_events — no need to mark again

        # Build event context
        event_context = build_event_context(event)

        # Parse extra_data early (needed for
        # verified_bots filtering below)
        extra_data = event.get('extra_data')
        if isinstance(extra_data, str):
            try:
                extra_data = json.loads(extra_data)
            except Exception:
                extra_data = {}
        if not isinstance(extra_data, dict):
            extra_data = {}

        # Find bots in the zone (if zone-specific)
        # Uses account-based detection:
        #   RNDBOT% accounts = bots
        # Excludes bots grouped with real players
        #   (immersion breaking)
        if zone_id:
            # Get online bots (RNDBOT accounts)
            # currently in this zone
            # Exclude bots grouped with real players
            cursor.execute("""
                SELECT DISTINCT
                    c.guid as bot1_guid,
                    c.name as bot1_name,
                    c.class as bot1_class,
                    c.race as bot1_race,
                    c.level as bot1_level,
                    c.zone as zone_id
                FROM characters c
                JOIN acore_auth.account a
                    ON c.account = a.id
                WHERE c.online = 1
                  AND c.zone = %s
                  AND a.username LIKE 'RNDBOT%%%%'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM group_member gm1
                      JOIN group_member gm2
                          ON gm1.guid = gm2.guid
                      JOIN characters c2
                          ON gm2.memberGuid = c2.guid
                      JOIN acore_auth.account a2
                          ON c2.account = a2.id
                      WHERE gm1.memberGuid = c.guid
                        AND gm2.memberGuid != c.guid
                        AND a2.username
                            NOT LIKE 'RNDBOT%%%%'
                  )
                ORDER BY RAND()
                LIMIT 10
            """, (zone_id,))
            recent_bots = cursor.fetchall()

            if not recent_bots:
                # No bots found, skip event
                cursor.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
                logger.info(
                    f"Event #{event_id} skipped: "
                    f"no bots in zone {zone_id}"
                )
                return False

            # Convert numeric class/race to names
            for bot in recent_bots:
                if isinstance(
                    bot.get('bot1_class'), int
                ):
                    bot['bot1_class'] = (
                        get_class_name(
                            bot['bot1_class']
                        )
                    )
                if isinstance(
                    bot.get('bot1_race'), int
                ):
                    bot['bot1_race'] = (
                        get_race_name(
                            bot['bot1_race']
                        )
                    )
        else:
            # Global event - find any online bot
            # (RNDBOT account)
            # Exclude bots grouped with real players
            cursor.execute("""
                SELECT DISTINCT
                    c.guid as bot1_guid,
                    c.name as bot1_name,
                    c.class as bot1_class,
                    c.race as bot1_race,
                    c.level as bot1_level,
                    c.zone as zone_id
                FROM characters c
                JOIN acore_auth.account a
                    ON c.account = a.id
                WHERE c.online = 1
                  AND a.username LIKE 'RNDBOT%%%%'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM group_member gm1
                      JOIN group_member gm2
                          ON gm1.guid = gm2.guid
                      JOIN characters c2
                          ON gm2.memberGuid = c2.guid
                      JOIN acore_auth.account a2
                          ON c2.account = a2.id
                      WHERE gm1.memberGuid = c.guid
                        AND gm2.memberGuid != c.guid
                        AND a2.username
                            NOT LIKE 'RNDBOT%%%%'
                  )
                ORDER BY RAND()
                LIMIT 20
            """)
            recent_bots = cursor.fetchall()

            if not recent_bots:
                cursor.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
                logger.info(
                    f"Event #{event_id} skipped: "
                    f"no online bots found"
                )
                return False

            # Convert numeric class/race to names
            for bot in recent_bots:
                if isinstance(
                    bot.get('bot1_class'), int
                ):
                    bot['bot1_class'] = (
                        get_class_name(
                            bot['bot1_class']
                        )
                    )
                if isinstance(
                    bot.get('bot1_race'), int
                ):
                    bot['bot1_race'] = (
                        get_race_name(
                            bot['bot1_race']
                        )
                    )

        # If C++ provided verified bot GUIDs
        # (bots confirmed in General channel),
        # filter to only those bots.
        # Empty list [] is authoritative: means
        # C++ found zero bots in channel -> skip.
        verified = extra_data.get('verified_bots')
        if isinstance(verified, list):
            if not verified:
                cursor.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
                logger.info(
                    f"Event #{event_id} skipped: "
                    f"C++ found no bots in General"
                )
                return False
            verified_set = set(
                int(g) for g in verified
            )
            recent_bots = [
                b for b in recent_bots
                if int(b['bot1_guid'])
                in verified_set
            ]
            if not recent_bots:
                cursor.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
                logger.info(
                    f"Event #{event_id} skipped: "
                    f"no verified bots remaining"
                )
                return False
            logger.info(
                f"Filtered to {len(recent_bots)} "
                f"verified bots (of "
                f"{len(verified_set)} GUIDs)"
            )

        # Check zone fatigue (if zone-specific event)
        # Transport and weather_change events bypass
        # zone fatigue — they are rare moments that
        # should always fire
        if (
            zone_id
            and event_type != 'transport_arrives'
            and event_type != 'weather_change'
        ):
            fatigue_threshold = int(config.get(
                'LLMChatter.ZoneFatigueThreshold',
                3
            ))
            fatigue_cooldown = int(config.get(
                'LLMChatter.'
                'ZoneFatigueCooldownSeconds',
                900
            ))
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM llm_chatter_events
                WHERE zone_id = %s
                  AND status = 'completed'
                  AND processed_at > DATE_SUB(
                      NOW(), INTERVAL %s SECOND
                  )
            """, (zone_id, fatigue_cooldown))
            result = cursor.fetchone()
            if (
                result
                and result['cnt']
                >= fatigue_threshold
            ):
                cursor.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
                logger.info(
                    f"Event #{event_id} skipped: "
                    f"zone {zone_id} fatigue "
                    f"threshold "
                    f"({fatigue_threshold}) "
                    f"reached"
                )
                return False

        # Decide: statement vs conversation
        # (configurable, default 60% conversation)
        # Conversations require at least 2 bots
        event_conv_chance = int(config.get(
            'LLMChatter.EventConversationChance',
            60
        ))
        use_conversation = (
            len(recent_bots) >= 2
            and random.randint(1, 100)
            <= event_conv_chance
        )

        if use_conversation:
            # Select 2-4 bots for conversation
            num_bots = min(
                random.randint(2, 4),
                len(recent_bots)
            )
            selected_bots = random.sample(
                list(recent_bots), num_bots
            )

            # Format bots for conversation prompt
            bots = []
            for b in selected_bots:
                bots.append({
                    'guid': b['bot1_guid'],
                    'name': b['bot1_name'],
                    'class': b['bot1_class'],
                    'race': b['bot1_race'],
                    'level': b['bot1_level'],
                    'zone': get_zone_name(
                        b.get('zone_id', zone_id)
                    )
                })

            bot_names = [
                b['name'] for b in bots
            ]
            bot_guids = {
                b['name']: b['guid']
                for b in bots
            }

            logger.info(
                f"Event #{event_id} triggering "
                f"{num_bots}-bot conversation: "
                f"{', '.join(bot_names)}"
            )

            # Get weather from event extra_data
            # (already parsed at top of try block)
            current_weather = extra_data.get(
                'current_weather', 'clear'
            )

            # Fetch recent messages for
            # anti-repetition
            recent_msgs = (
                get_recent_zone_messages(
                    db, zone_id
                )
            )

            # Build event conversation prompt
            allow_action = (
                random.random()
                < get_action_chance()
            )
            prompt = (
                build_event_conversation_prompt(
                    bots, event_context, zone_id,
                    config, current_weather,
                    recent_messages=recent_msgs,
                    allow_action=allow_action,
                )
            )

            # Call LLM
            evt_names = ','.join(bot_names)
            response = call_llm(
                client, prompt, config,
                context=(
                    f"event-conv:#{event_id}"
                    f":{evt_names}"
                )
            )

            if response:
                logger.info(
                    f"LLM raw response "
                    f"(len={len(response)}):"
                    f"\n{response}"
                )
                messages = (
                    parse_conversation_response(
                        response, bot_names
                    )
                )

                if messages:
                    logger.info(
                        f"Event conversation "
                        f"with {len(messages)} "
                        f"messages:"
                    )

                    cumulative_delay = 0.0
                    for i, msg in enumerate(
                        messages
                    ):
                        bot_guid = bot_guids.get(
                            msg['name'],
                            bots[0]['guid']
                        )
                        final_message = (
                            strip_speaker_prefix(
                                msg['message'],
                                msg['name'],
                            )
                        )
                        final_message = (
                            cleanup_message(
                                final_message,
                                action=msg.get(
                                    'action'
                                ),
                            )
                        )

                        if i > 0:
                            delay = (
                                calculate_dynamic_delay(
                                    len(
                                        final_message
                                    ),
                                    config
                                )
                            )
                            cumulative_delay += (
                                delay
                            )

                        cursor.execute("""
                            INSERT INTO
                                llm_chatter_messages
                            (event_id, sequence,
                             bot_guid, bot_name,
                             message, channel,
                             delivered,
                             deliver_at)
                            VALUES (
                                %s, %s, %s, %s,
                                %s, 'general', 0,
                                DATE_ADD(NOW(),
                                    INTERVAL %s
                                    SECOND)
                            )
                        """, (
                            event_id, i,
                            bot_guid,
                            msg['name'],
                            final_message,
                            cumulative_delay
                        ))

                        logger.info(
                            f"  [{i}] "
                            f"+{cumulative_delay:.1f}s"
                            f" {msg['name']}: "
                            f"{final_message}"
                        )

                    # Mark event completed
                    cursor.execute(
                        "UPDATE "
                        "llm_chatter_events "
                        "SET status = "
                        "'completed', "
                        "processed_at = NOW() "
                        "WHERE id = %s",
                        (event_id,)
                    )
                    db.commit()
                    return True

            # Fallback to statement if conversation
            # failed
            logger.warning(
                "Event conversation failed, "
                "falling back to statement"
            )
            use_conversation = False

        # Statement mode (single bot)
        if not use_conversation:
            bot = dict(
                random.choice(list(recent_bots))
            )
            bypass_cooldown = event_type in (
                'transport_arrives',
                'weather_change',
            )

            # Transport and weather events bypass
            # cooldown — rare moments that should
            # always fire
            if not bypass_cooldown:
                # Check bot speaker cooldown for
                # non-transport events
                cooldown = int(config.get(
                    'LLMChatter.'
                    'BotSpeakerCooldownSeconds',
                    900
                ))
                cursor.execute("""
                    SELECT COUNT(*) as cnt
                    FROM llm_chatter_messages
                    WHERE bot_guid = %s
                      AND delivered = 1
                      AND delivered_at
                          > DATE_SUB(
                              NOW(),
                              INTERVAL %s SECOND
                          )
                """, (
                    bot['bot1_guid'], cooldown
                ))
                result = cursor.fetchone()
                if result and result['cnt'] > 0:
                    cursor.execute(
                        "UPDATE "
                        "llm_chatter_events "
                        "SET status = 'skipped' "
                        "WHERE id = %s",
                        (event_id,)
                    )
                    db.commit()
                    logger.info(
                        f"Event #{event_id} "
                        f"skipped: bot "
                        f"{bot['bot1_name']} "
                        f"on cooldown"
                    )
                    return False
            else:
                logger.info(
                    f"{event_type} event "
                    f"#{event_id}: bypassing "
                    f"cooldown for bot "
                    f"{bot['bot1_name']}"
                )

            # Get zone name
            zone_name = (
                get_zone_name(
                    bot.get('zone_id', zone_id)
                )
                or "the world"
            )

            # Build prompt for event-triggered
            # statement
            mode = get_chatter_mode(config)
            is_rp = (mode == 'roleplay')
            tone = pick_random_tone(mode)

            # Transport events get more direct
            # instructions
            is_transport = (
                'boat' in event_context.lower()
                or 'zeppelin'
                in event_context.lower()
                or 'turtle'
                in event_context.lower()
            )
            is_holiday = (
                event.get('event_type', '')
                    .startswith('holiday')
            )
            if is_transport:
                event_instruction = (
                    "Comment on this transport "
                    "arrival! Use the specific "
                    "type (boat/zeppelin/"
                    "turtle), NOT 'transport'."
                    "\nMention the destination "
                    "if known. Be creative and "
                    "original - no canned "
                    "phrases."
                )
            elif is_holiday:
                event_instruction = (
                    "React to this event! "
                    "Mention the event by name "
                    "and share your character's "
                    "opinion or feelings about "
                    "it."
                )
            else:
                event_instruction = (
                    "You may naturally reference"
                    " this event in your "
                    "message, or you may chat "
                    "about something else "
                    "entirely.\nThe event "
                    "provides atmosphere - you "
                    "don't HAVE to mention it "
                    "explicitly."
                )

            # Environmental context
            # (extra_data already parsed at top
            # of try block)
            weather_for_context = None
            if (
                'weather'
                not in event_context.lower()
            ):
                weather_for_context = (
                    extra_data.get(
                        'current_weather',
                        'clear'
                    )
                )

            env_context = (
                get_environmental_context(
                    weather_for_context
                )
            )
            env_lines = ""
            if env_context['time']:
                env_lines += (
                    f"\nTime of day: "
                    f"{env_context['time']}"
                )
            if env_context['weather']:
                env_lines += (
                    f"\nCurrent weather: "
                    f"{env_context['weather']}"
                )

            # Build RP personality context if in
            # roleplay mode
            rp_personality = ""
            rp_style = ""
            if is_rp:
                rp_ctx = (
                    build_race_class_context(
                        bot['bot1_race'],
                        bot['bot1_class']
                    )
                )
                if rp_ctx:
                    rp_personality = (
                        f"\n{rp_ctx}"
                    )
                rp_style = (
                    "\nStay in character but "
                    "keep it natural and "
                    "conversational. No game "
                    "terms or OOC references, "
                    "but don't be overly "
                    "dramatic or theatrical "
                    "either."
                )

            system_prompt = (
                f"You are {bot['bot1_name']}, "
                f"a {bot['bot1_race']} "
                f"{bot['bot1_class']} "
                f"adventurer in World of "
                f"Warcraft.\n"
                f"You are level "
                f"{bot['bot1_level']} "
                f"and currently in "
                f"{zone_name}."
                f"{env_lines}"
                f"{rp_personality}\n\n"
                f"CONTEXT: {event_context}\n\n"
                f"{event_instruction}\n\n"
                f"Your current mood: {tone}"
                f"{rp_style}\n\n"
                f"Respond with a single short "
                f"sentence (under 100 "
                f"characters) that a player "
                f"might say in General chat.\n"
                f"Be "
                f"{'authentic and in-character' if is_rp else 'casual and authentic'}"
                f"."
            )

            # Append JSON format instruction
            allow_action = (
                random.random()
                < get_action_chance()
            )
            system_prompt = (
                append_json_instruction(
                    system_prompt, allow_action
                )
            )

            # Call LLM
            provider = config.get(
                'LLMChatter.Provider',
                'anthropic'
            ).lower()
            model = config.get(
                'LLMChatter.Model',
                'claude-haiku-4-5-20251001'
            )
            max_tokens = int(config.get(
                'LLMChatter.MaxTokens', 200
            ))
            temperature = float(config.get(
                'LLMChatter.Temperature', 0.8
            ))

            logger.info(
                f"Event statement prompt "
                f"({provider}/{model}):\n"
                f"{system_prompt}"
            )

            if provider == 'ollama':
                # Ollama uses OpenAI-compat API
                context_size = int(config.get(
                    'LLMChatter.'
                    'Ollama.ContextSize',
                    2048
                ))
                response = (
                    client.chat
                    .completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content":
                                    system_prompt
                            },
                            {
                                "role": "user",
                                "content":
                                    "Say something"
                                    " in General "
                                    "chat."
                            }
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        extra_body={
                            "options": {
                                "num_ctx":
                                    context_size
                            }
                        }
                    )
                )
                message = (
                    response.choices[0]
                    .message.content.strip()
                )
            elif provider == 'openai':
                response = (
                    client.chat
                    .completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content":
                                    system_prompt
                            },
                            {
                                "role": "user",
                                "content":
                                    "Say something"
                                    " in General "
                                    "chat."
                            }
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                )
                message = (
                    response.choices[0]
                    .message.content.strip()
                )
            else:
                # Anthropic (default)
                response = (
                    client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_prompt,
                        messages=[{
                            "role": "user",
                            "content":
                                "Say something "
                                "in General "
                                "chat."
                        }]
                    )
                )
                message = (
                    response.content[0]
                    .text.strip()
                )

            # Parse structured JSON response
            parsed = parse_single_response(
                message
            )
            message = parsed['message']
            message = cleanup_message(
                message,
                action=parsed.get('action'),
            )
            if len(message) > 255:
                message = message[:252] + "..."

            # Insert message for delivery
            delay_min = int(config.get(
                'LLMChatter.MessageDelayMin',
                1000
            ))
            delay_max = int(config.get(
                'LLMChatter.MessageDelayMax',
                30000
            ))
            delay_ms = random.randint(
                delay_min, delay_max
            )

            emote = (
                parsed.get('emote')
                or pick_emote_for_statement(
                    message
                )
            )
            insert_chat_message(
                db, bot['bot1_guid'],
                bot['bot1_name'], message,
                channel='general',
                delay_seconds=delay_ms // 1000,
                event_id=event_id,
                sequence=0,
                emote=emote,
            )

            # Mark event completed
            cursor.execute(
                "UPDATE llm_chatter_events "
                "SET status = 'completed', "
                "processed_at = NOW() "
                "WHERE id = %s",
                (event_id,)
            )
            db.commit()

            logger.info(
                f"Event #{event_id} processed: "
                f"{bot['bot1_name']} will say: "
                f"{message[:50]}..."
            )
            return True

    except Exception as e:
        logger.error(
            f"Worker error processing event "
            f"#{event_id}: {e}"
        )
        # Try to mark as skipped
        try:
            if db:
                c = db.cursor()
                c.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
        except Exception:
            pass
        return False
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass


def _run_with_group_lock(lock, fn, *args, **kwargs):
    """Execute fn while holding a per-group lock.
    Serializes events for the same group."""
    with lock:
        return fn(*args, **kwargs)


def _run_in_worker(fn_name, fn, client, config):
    """Run a function in a worker thread with its
    own DB connection. Follows process_single_event
    pattern."""
    db = None
    try:
        db = get_db_connection(config)
        fn(db, client, config)
    except Exception:
        logger.exception(
            f"{fn_name} worker failed"
        )
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass


# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description='LLM Chatter Bridge'
    )
    parser.add_argument(
        '--config', required=True,
        help='Path to config file'
    )
    args = parser.parse_args()

    # Load config
    config = parse_config(args.config)

    # Check if enabled - if disabled, wait and check
    # periodically
    while config.get('LLMChatter.Enable', '0') != '1':
        logger.info(
            "LLMChatter is disabled in config. "
            "Waiting... (checking every 60s)"
        )
        time.sleep(60)
        config = parse_config(args.config)

    # Apply config-driven settings to shared module
    set_race_lore_chance(int(config.get(
        'LLMChatter.RaceLoreChance', 15
    )))
    set_race_vocab_chance(int(config.get(
        'LLMChatter.RaceVocabChance', 15
    )))
    set_action_chance(int(config.get(
        'LLMChatter.ActionChance', 10
    )), mode=config.get(
        'LLMChatter.ChatterMode', 'normal'
    ).lower())
    init_group_config(config)
    init_general_config(config)

    # Get provider and initialize appropriate client
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()
    model = config.get(
        'LLMChatter.Model',
        'claude-haiku-4-5-20251001'
    )

    if provider == 'ollama':
        # Ollama runs locally - no API key needed
        # Uses OpenAI-compatible API endpoint
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://localhost:11434'
        )
        # Ollama's OpenAI-compatible endpoint is
        # at /v1
        ollama_api_url = (
            f"{base_url.rstrip('/')}/v1"
        )
        client = openai.OpenAI(
            base_url=ollama_api_url,
            api_key="ollama"
        )
        logger.info(f"Using Ollama at {base_url}")
    elif provider == 'openai':
        api_key = config.get(
            'LLMChatter.OpenAI.ApiKey', ''
        )
        if not api_key:
            logger.error(
                "No OpenAI API key configured!"
            )
            sys.exit(1)
        client = openai.OpenAI(api_key=api_key)
    else:
        # Anthropic (default)
        api_key = config.get(
            'LLMChatter.Anthropic.ApiKey', ''
        )
        if not api_key:
            logger.error(
                "No Anthropic API key configured!"
            )
            sys.exit(1)
        client = anthropic.Anthropic(api_key=api_key)

    # Get poll interval
    poll_interval = int(config.get(
        'LLMChatter.Bridge.PollIntervalSeconds', 3
    ))

    # Max concurrent event workers
    try:
        max_concurrent = max(1, min(int(
            config.get(
                'LLMChatter.Bridge.MaxConcurrent',
                '3'
            )
        ), 10))
    except (ValueError, TypeError):
        max_concurrent = 3

    # Check event system config
    use_event_system = (
        config.get(
            'LLMChatter.UseEventSystem', '1'
        ) == '1'
    )

    chatter_mode = get_chatter_mode(config)

    logger.info("=" * 60)
    logger.info("LLM Chatter Bridge v4.0")
    logger.info("=" * 60)
    logger.info(f"ChatterMode: {chatter_mode}")
    logger.info(f"Provider: {provider}")
    logger.info(
        f"Model: {model}"
    )
    if provider == 'ollama':
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://localhost:11434'
        )
        context_size = config.get(
            'LLMChatter.Ollama.ContextSize', 2048
        )
        disable_thinking = (
            config.get(
                'LLMChatter.Ollama.DisableThinking',
                '1'
            ) == '1'
        )
        logger.info(f"Ollama URL: {base_url}")
        logger.info(f"Context size: {context_size}")
        logger.info(
            f"Thinking mode: "
            f"{'disabled (/no_think)' if disable_thinking else 'enabled'}"
        )
    logger.info(f"Poll interval: {poll_interval}s")
    logger.info(
        f"Max concurrent: {max_concurrent}"
    )
    base_max = config.get(
        'LLMChatter.MaxTokens', 200
    )
    convo_max = config.get(
        'LLMChatter.ConversationMaxTokens', base_max
    )
    logger.info(
        f"Max tokens (statements): {base_max}"
    )
    logger.info(
        f"Max tokens (conversations): {convo_max}"
    )
    logger.info(
        f"Event system: "
        f"{'enabled' if use_event_system else 'disabled'}"
    )
    logger.info(
        f"Message type distribution: "
        f"{MSG_TYPE_PLAIN}% plain, "
        f"{MSG_TYPE_QUEST - MSG_TYPE_PLAIN}% quest, "
        f"{MSG_TYPE_LOOT - MSG_TYPE_QUEST}% loot, "
        f"{MSG_TYPE_QUEST_REWARD - MSG_TYPE_LOOT}% "
        f"quest+reward, "
        f"{MSG_TYPE_TRADE - MSG_TYPE_QUEST_REWARD}% "
        f"trade, "
        f"{MSG_TYPE_SPELL - MSG_TYPE_TRADE}% spell"
    )
    logger.info("-" * 60)
    logger.info("Core settings:")
    logger.info(
        f"  Enable: "
        f"{config.get('LLMChatter.Enable', 1)}"
        f"  ChatterMode: "
        f"{config.get('LLMChatter.ChatterMode', 'roleplay')}"
    )
    logger.info(
        f"  Provider: "
        f"{config.get('LLMChatter.Provider', 'anthropic')}"
        f"  Model: "
        f"{config.get('LLMChatter.Model', '(default)')}"
    )
    logger.info(
        f"  MaxTokens: "
        f"{config.get('LLMChatter.MaxTokens', 350)}"
        f"  ConversationMaxTokens: "
        f"{config.get('LLMChatter.ConversationMaxTokens', 700)}"
    )
    logger.info(
        f"  UseEventSystem: "
        f"{config.get('LLMChatter.UseEventSystem', 1)}"
        f"  EnableVerboseLogging: "
        f"{config.get('LLMChatter.EnableVerboseLogging', 0)}"
    )
    logger.info(
        f"  DeliveryPollMs: "
        f"{config.get('LLMChatter.DeliveryPollMs', 1000)}"
        f"  Bridge.PollIntervalSeconds: "
        f"{config.get('LLMChatter.Bridge.PollIntervalSeconds', 3)}"
    )
    logger.info("-" * 60)
    logger.info("Chatter settings:")
    logger.info(
        f"  TriggerIntervalSeconds: "
        f"{config.get('LLMChatter.TriggerIntervalSeconds', 60)}"
    )
    logger.info(
        f"  TriggerChance: "
        f"{config.get('LLMChatter.TriggerChance', 30)}%"
    )
    logger.info(
        f"  ConversationChance: "
        f"{config.get('LLMChatter.ConversationChance', 50)}%"
    )
    logger.info(
        f"  EventConversationChance: "
        f"{config.get('LLMChatter.EventConversationChance', 60)}%"
    )
    logger.info(
        f"  Temperature: "
        f"{config.get('LLMChatter.Temperature', 0.8)}"
    )
    logger.info(
        f"  LongMessageChance: "
        f"{config.get('LLMChatter.LongMessageChance', 15)}%"
    )
    logger.info(
        f"  PersonalitySpiceCount: "
        f"{config.get('LLMChatter.PersonalitySpiceCount', 2)}"
    )
    logger.info(
        f"  CityChatterMultiplier: "
        f"{config.get('LLMChatter.CityChatterMultiplier', 2)}"
    )
    logger.info(
        f"  MaxPendingRequests: "
        f"{config.get('LLMChatter.MaxPendingRequests', 5)}"
    )
    logger.info(
        f"  MessageDelayMin: "
        f"{config.get('LLMChatter.MessageDelayMin', 1000)}ms"
        f"  MessageDelayMax: "
        f"{config.get('LLMChatter.MessageDelayMax', 30000)}ms"
    )
    logger.info(
        f"  BotSpeakerCooldownSeconds: "
        f"{config.get('LLMChatter.BotSpeakerCooldownSeconds', 900)}"
    )
    logger.info(
        f"  ZoneFatigueThreshold: "
        f"{config.get('LLMChatter.ZoneFatigueThreshold', 3)}"
        f"  ZoneFatigueCooldownSeconds: "
        f"{config.get('LLMChatter.ZoneFatigueCooldownSeconds', 900)}"
    )
    logger.info(
        f"  LootRecentCooldownSeconds: "
        f"{config.get('LLMChatter.LootRecentCooldownSeconds', 1200)}"
    )
    logger.info(
        f"  GlobalMessageCap: "
        f"{config.get('LLMChatter.GlobalMessageCap', 8)}"
        f"  GlobalCapWindowSeconds: "
        f"{config.get('LLMChatter.GlobalCapWindowSeconds', 300)}"
    )
    logger.info("-" * 60)
    logger.info("Event settings:")
    logger.info(
        f"  EnvironmentCheckSeconds: "
        f"{config.get('LLMChatter.EnvironmentCheckSeconds', 60)}"
    )
    logger.info(
        f"  EventReactionChance: "
        f"{config.get('LLMChatter.EventReactionChance', 15)}%"
    )
    logger.info(
        f"  EventExpirationSeconds: "
        f"{config.get('LLMChatter.EventExpirationSeconds', 600)}"
    )
    logger.info(
        f"  Holidays: "
        f"{config.get('LLMChatter.Events.Holidays', 1)}"
        f"  DayNight: "
        f"{config.get('LLMChatter.Events.DayNight', 1)}"
        f"  Weather: "
        f"{config.get('LLMChatter.Events.Weather', 1)}"
        f"  Transports: "
        f"{config.get('LLMChatter.Events.Transports', 1)}"
    )
    logger.info(
        f"  MinorEvents: "
        f"{config.get('LLMChatter.Events.MinorEvents', 1)}"
        f"  MinorEventChance: "
        f"{config.get('LLMChatter.Events.MinorEventChance', 20)}%"
    )
    logger.info(
        f"  TransportEventChance: "
        f"{config.get('LLMChatter.TransportEventChance', 0)}%"
    )
    logger.info("-" * 60)
    logger.info("Transport settings:")
    logger.info(
        f"  TransportCooldownSeconds: "
        f"{config.get('LLMChatter.TransportCooldownSeconds', 600)}"
        f"  TransportCheckSeconds: "
        f"{config.get('LLMChatter.TransportCheckSeconds', 5)}"
    )
    logger.info(
        f"  TransportBypassGlobalCap: "
        f"{config.get('LLMChatter.TransportBypassGlobalCap', 0)}"
    )
    logger.info("-" * 60)
    logger.info("Weather/DayNight settings:")
    logger.info(
        f"  WeatherCooldownSeconds: "
        f"{config.get('LLMChatter.WeatherCooldownSeconds', 1800)}"
        f"  DayNightCooldownSeconds: "
        f"{config.get('LLMChatter.DayNightCooldownSeconds', 7200)}"
    )
    logger.info("-" * 60)
    logger.info("Holiday settings:")
    logger.info(
        f"  HolidayCityChance: "
        f"{config.get('LLMChatter.HolidayCityChance', 10)}%"
        f"  HolidayZoneChance: "
        f"{config.get('LLMChatter.HolidayZoneChance', 5)}%"
    )
    logger.info(
        f"  HolidayCooldownSeconds: "
        f"{config.get('LLMChatter.HolidayCooldownSeconds', 1800)}"
    )
    logger.info("-" * 60)
    logger.info("Group chatter settings:")
    logger.info(
        f"  Enable: "
        f"{config.get('LLMChatter.GroupChatter.Enable', 1)}"
    )
    logger.info(
        f"  KillChanceNormal: "
        f"{config.get('LLMChatter.GroupChatter.KillChanceNormal', 20)}%"
    )
    logger.info(
        f"  DeathChance: "
        f"{config.get('LLMChatter.GroupChatter.DeathChance', 40)}%"
    )
    logger.info(
        f"  LootChanceGreen: "
        f"{config.get('LLMChatter.GroupChatter.LootChanceGreen', 20)}%"
        f"  Blue: "
        f"{config.get('LLMChatter.GroupChatter.LootChanceBlue', 50)}%"
    )
    logger.info(
        f"  QuestObjectiveChance: "
        f"{config.get('LLMChatter.GroupChatter.QuestObjectiveChance', 50)}%"
    )
    logger.info(
        f"  SpellCastChance: "
        f"{config.get('LLMChatter.GroupChatter.SpellCastChance', 10)}%"
    )
    logger.info(
        f"  KillCooldown: "
        f"{config.get('LLMChatter.GroupChatter.KillCooldown', 120)}s"
        f"  DeathCooldown: "
        f"{config.get('LLMChatter.GroupChatter.DeathCooldown', 30)}s"
        f"  LootCooldown: "
        f"{config.get('LLMChatter.GroupChatter.LootCooldown', 60)}s"
    )
    logger.info(
        f"  PlayerMsgCooldown: "
        f"{config.get('LLMChatter.GroupChatter.PlayerMsgCooldown', 15)}s"
    )
    logger.info(
        f"  IdleChance: "
        f"{config.get('LLMChatter.GroupChatter.IdleChance', 10)}%"
        f"  IdleCheckInterval: "
        f"{config.get('LLMChatter.GroupChatter.IdleCheckInterval', 60)}s"
    )
    logger.info(
        f"  IdleCooldown: "
        f"{config.get('LLMChatter.GroupChatter.IdleCooldown', 30)}s"
        f"  ConversationBias: "
        f"{config.get('LLMChatter.GroupChatter.ConversationBias', 50)}%"
    )
    logger.info(
        f"  IdleHistoryLimit: "
        f"{config.get('LLMChatter.GroupChatter.IdleHistoryLimit', 5)}"
        f"  QuestObjectiveCooldown: "
        f"{config.get('LLMChatter.GroupChatter.QuestObjectiveCooldown', 30)}s"
    )
    logger.info(
        f"  ResurrectChance: "
        f"{config.get('LLMChatter.GroupChatter.ResurrectChance', 100)}%"
        f"  ResurrectCooldown: "
        f"{config.get('LLMChatter.GroupChatter.ResurrectCooldown', 30)}s"
    )
    logger.info(
        f"  ZoneTransitionChance: "
        f"{config.get('LLMChatter.GroupChatter.ZoneTransitionChance', 100)}%"
        f"  ZoneTransitionCooldown: "
        f"{config.get('LLMChatter.GroupChatter.ZoneTransitionCooldown', 120)}s"
    )
    logger.info(
        f"  DungeonEntryChance: "
        f"{config.get('LLMChatter.GroupChatter.DungeonEntryChance', 100)}%"
        f"  DungeonEntryCooldown: "
        f"{config.get('LLMChatter.GroupChatter.DungeonEntryCooldown', 300)}s"
    )
    logger.info(
        f"  WipeChance: "
        f"{config.get('LLMChatter.GroupChatter.WipeChance', 100)}%"
        f"  WipeCooldown: "
        f"{config.get('LLMChatter.GroupChatter.WipeCooldown', 120)}s"
    )
    logger.info(
        f"  CorpseRunChance: "
        f"{config.get('LLMChatter.GroupChatter.CorpseRunChance', 80)}%"
        f"  CorpseRunCooldown: "
        f"{config.get('LLMChatter.GroupChatter.CorpseRunCooldown', 120)}s"
    )
    logger.info(
        f"  FarewellEnable: "
        f"{config.get('LLMChatter.GroupChatter.FarewellEnable', 1)}"
    )
    logger.info(
        f"  CompositionCommentChance: "
        f"{config.get('LLMChatter.GroupChatter.CompositionCommentChance', 10)}%"
    )
    logger.info(
        f"  RaceLoreChance: "
        f"{config.get('LLMChatter.RaceLoreChance', 15)}%"
    )
    logger.info(
        f"  RaceVocabChance: "
        f"{config.get('LLMChatter.RaceVocabChance', 15)}%"
    )
    logger.info(
        f"  ActionChance: "
        f"{config.get('LLMChatter.ActionChance', 10)}%"
    )
    logger.info("-" * 60)
    qa_prov = config.get(
        'LLMChatter.QuickAnalyze.Provider', ''
    ).strip()
    qa_model = config.get(
        'LLMChatter.QuickAnalyze.Model', ''
    ).strip()
    logger.info("Quick analyze settings:")
    logger.info(
        f"  Provider: "
        f"{qa_prov if qa_prov else '(main)'}"
    )
    logger.info(
        f"  Model: "
        f"{qa_model if qa_model else '(auto)'}"
    )
    logger.info("-" * 60)
    precache_enabled = config.get(
        'LLMChatter.GroupChatter.PreCacheEnable',
        '1'
    ) == '1'
    logger.info("Pre-cache settings:")
    logger.info(
        f"  Enable: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheEnable', 1)}"
    )
    logger.info(
        f"  CombatEnable: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheCombatEnable', 1)}"
        f"  StateEnable: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheStateEnable', 1)}"
        f"  SpellEnable: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheSpellEnable', 1)}"
    )
    logger.info(
        f"  DepthCombat: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheDepthCombat', 2)}"
        f"  DepthState: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheDepthState', 2)}"
        f"  DepthSpell: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheDepthSpell', 2)}"
    )
    logger.info(
        f"  TTL: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheTTLSeconds', 3600)}s"
        f"  GeneratePerLoop: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheGeneratePerLoop', 3)}"
    )
    logger.info(
        f"  FallbackToLive: "
        f"{config.get('LLMChatter.GroupChatter.PreCacheFallbackToLive', 1)}"
    )
    logger.info("-" * 60)
    logger.info("State callout settings:")
    logger.info(
        f"  Enable: "
        f"{config.get('LLMChatter.GroupChatter.StateCalloutEnable', 1)}"
        f"  Chance: "
        f"{config.get('LLMChatter.GroupChatter.StateCalloutChance', 60)}%"
        f"  Cooldown: "
        f"{config.get('LLMChatter.GroupChatter.StateCalloutCooldown', 60)}s"
    )
    logger.info(
        f"  LowHealth: "
        f"{config.get('LLMChatter.GroupChatter.StateCalloutLowHealth', 1)}"
        f"  Oom: "
        f"{config.get('LLMChatter.GroupChatter.StateCalloutOom', 1)}"
        f"  Aggro: "
        f"{config.get('LLMChatter.GroupChatter.StateCalloutAggro', 1)}"
    )
    logger.info("-" * 60)
    logger.info("General chat settings:")
    logger.info(
        f"  Enable: "
        f"{config.get('LLMChatter.GeneralChat.Enable', 1)}"
        f"  ReactionChance: "
        f"{config.get('LLMChatter.GeneralChat.ReactionChance', 40)}%"
    )
    logger.info(
        f"  QuestionChance: "
        f"{config.get('LLMChatter.GeneralChat.QuestionChance', 80)}%"
        f"  Cooldown: "
        f"{config.get('LLMChatter.GeneralChat.Cooldown', 30)}s"
    )
    logger.info(
        f"  ConversationChance: "
        f"{config.get('LLMChatter.GeneralChat.ConversationChance', 30)}%"
    )
    logger.info("-" * 60)
    logger.info("Shared settings:")
    from chatter_group import _chat_history_limit
    logger.info(
        f"  Chat history limit: "
        f"{_chat_history_limit}"
    )
    logger.info("-" * 60)
    logger.info("Ollama settings:")
    logger.info(
        f"  BaseUrl: "
        f"{config.get('LLMChatter.Ollama.BaseUrl', 'http://localhost:11434')}"
    )
    logger.info(
        f"  ContextSize: "
        f"{config.get('LLMChatter.Ollama.ContextSize', 2048)}"
        f"  DisableThinking: "
        f"{config.get('LLMChatter.Ollama.DisableThinking', 1)}"
    )
    logger.info("=" * 60)

    # Wait for database to be ready
    # (handles Docker startup order)
    if not wait_for_database(config):
        logger.error(
            "Could not connect to database. Exiting."
        )
        sys.exit(1)

    # Startup cleanup: reset any events stuck in
    # 'processing' from previous crash
    if use_event_system:
        db = None
        try:
            db = get_db_connection(config)
            reset_stuck_processing_events(db)
        except Exception as e:
            logger.warning(
                f"Could not reset stuck events on "
                f"startup: {e}"
            )
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass

    # Main loop
    last_cleanup = 0
    cleanup_interval = 60  # every 60 seconds
    last_idle_check = 0
    idle_check_interval = int(config.get(
        'LLMChatter.GroupChatter.IdleCheckInterval',
        60
    ))
    last_cache_refill = 0
    cache_refill_interval = 30  # every 30 seconds

    executor = ThreadPoolExecutor(
        max_workers=max_concurrent + 3
    )
    active_futures = []
    active_event_ids = set()
    group_locks = {}
    group_locks_lock = threading.Lock()
    legacy_backoff = 0

    # Background task futures
    precache_future = None
    idle_chatter_future = None
    legacy_future = None

    def _harvest_future(f, name):
        """Log any unexpected worker failure."""
        try:
            f.result()
        except Exception:
            logger.exception(
                f"{name} worker failed"
            )

    while True:
        try:
            # Prune completed event futures
            still_active = []
            for f in active_futures:
                if f.done():
                    active_event_ids.discard(
                        f.event_id
                    )
                    try:
                        f.result()
                    except Exception:
                        logger.exception(
                            "Worker failed"
                        )
                else:
                    still_active.append(f)
            active_futures = still_active

            # Prune background task futures
            if (
                precache_future
                and precache_future.done()
            ):
                _harvest_future(
                    precache_future, "pre-cache"
                )
                precache_future = None
            if (
                idle_chatter_future
                and idle_chatter_future.done()
            ):
                _harvest_future(
                    idle_chatter_future,
                    "idle-chatter"
                )
                idle_chatter_future = None
            if (
                legacy_future
                and legacy_future.done()
            ):
                _harvest_future(
                    legacy_future,
                    "legacy-requests"
                )
                legacy_future = None

            # DB connection with proper lifecycle
            db = None
            try:
                db = get_db_connection(config)
                current_time = time.time()

                # Periodic cleanup (fast SQL,
                # stays on main thread)
                if (
                    use_event_system
                    and current_time
                    - last_cleanup
                    >= cleanup_interval
                ):
                    cleanup_expired_events(
                        db, active_event_ids
                    )
                    last_cleanup = current_time

                # Legacy requests -> worker pool
                legacy_backoff += 1
                if (
                    not legacy_future
                    and (
                        not active_futures
                        or legacy_backoff >= 10
                    )
                ):
                    legacy_future = (
                        executor.submit(
                            _run_in_worker,
                            "legacy-requests",
                            process_pending_requests,
                            client, config
                        )
                    )
                    legacy_backoff = 0

                # Fetch + dispatch events
                dispatched = 0
                if use_event_system:
                    available = (
                        max_concurrent
                        - len(active_futures)
                    )
                    if available > 0:
                        events = (
                            fetch_pending_events(
                                db, config,
                                available
                            )
                        )
                        for event in events:
                            gid = event.get(
                                '_group_id'
                            )
                            if gid:
                                with (
                                    group_locks_lock
                                ):
                                    if (
                                        gid
                                        not in
                                        group_locks
                                    ):
                                        group_locks[
                                            gid
                                        ] = (
                                            threading
                                            .Lock()
                                        )
                                    glock = (
                                        group_locks[
                                            gid
                                        ]
                                    )
                                future = (
                                    executor
                                    .submit(
                                        _run_with_group_lock,
                                        glock,
                                        process_single_event,
                                        event,
                                        client,
                                        config
                                    )
                                )
                            else:
                                future = (
                                    executor
                                    .submit(
                                        process_single_event,
                                        event,
                                        client,
                                        config
                                    )
                                )
                            future.event_id = (
                                event['id']
                            )
                            active_event_ids.add(
                                event['id']
                            )
                            active_futures.append(
                                future
                            )
                            dispatched += 1

                # Idle chatter -> worker pool
                if (
                    use_event_system
                    and not idle_chatter_future
                    and current_time
                    - last_idle_check
                    >= idle_check_interval
                ):
                    last_idle_check = current_time
                    idle_chatter_future = (
                        executor.submit(
                            _run_in_worker,
                            "idle-chatter",
                            check_idle_group_chatter,
                            client, config
                        )
                    )

                # Pre-cache -> worker pool
                if (
                    precache_enabled
                    and not precache_future
                    and current_time
                    - last_cache_refill
                    >= cache_refill_interval
                ):
                    last_cache_refill = (
                        current_time
                    )
                    precache_future = (
                        executor.submit(
                            _run_in_worker,
                            "pre-cache",
                            refill_precache_pool,
                            client, config
                        )
                    )

            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass

            # Adaptive sleep
            if (
                dispatched > 0
                or active_futures
            ):
                time.sleep(0.5)
            else:
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
            executor.shutdown(wait=False)
            break
        except Exception as e:
            logger.error(
                f"Main loop error: {e}"
            )
            time.sleep(poll_interval)


if __name__ == '__main__':
    main()
