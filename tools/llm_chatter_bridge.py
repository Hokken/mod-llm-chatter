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
import time
from typing import List

import anthropic
import openai
import mysql.connector

from chatter_constants import (
    MSG_TYPE_PLAIN, MSG_TYPE_QUEST,
    MSG_TYPE_LOOT, MSG_TYPE_QUEST_REWARD,
    MSG_TYPE_TRADE, MSG_TYPE_SPELL,
    ZONE_TRANSPORT_COOLDOWN_SECONDS,
)
from chatter_shared import (
    _zone_transport_cooldowns,
    zone_cache,
    get_zone_name, get_class_name, get_race_name,
    get_chatter_mode, build_race_class_context,
    parse_config, get_db_connection,
    wait_for_database,
    get_zone_flavor,
    can_class_use_item,
    query_zone_quests, query_zone_loot,
    query_zone_mobs, query_bot_spells,
    replace_placeholders, cleanup_message,
    select_message_type, calculate_dynamic_delay,
    resolve_model, call_llm,
    parse_conversation_response,
    extract_conversation_msg_count,
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

    # Build appropriate prompt
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
            config, current_weather
        )
    elif msg_type == "quest":
        prompt = build_quest_statement_prompt(
            bot, quest_data, config, current_weather
        )
    elif msg_type == "loot":
        prompt = build_loot_statement_prompt(
            bot, item_data, item_can_use,
            config, current_weather
        )
    elif msg_type == "quest_reward":
        prompt = build_quest_reward_statement_prompt(
            bot, quest_data, config, current_weather
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
            bot, item_data, config, current_weather
        )
    elif msg_type == "spell":
        prompt = build_spell_statement_prompt(
            bot, spell_data, config, current_weather
        )
    else:
        prompt = build_plain_statement_prompt(
            bot, zone_id,
            config=config,
            current_weather=current_weather
        )

    # Call LLM
    response = call_llm(client, prompt, config)

    if response:
        # Clean and replace placeholders
        message = response.strip().strip('"').strip()
        message = replace_placeholders(
            message, quest_data, item_data,
            spell_data
        )
        message = cleanup_message(message)

        logger.info(
            f"Statement from {bot['name']} "
            f"[{msg_type}]: {message}"
        )

        # Insert for delivery
        cursor.execute("""
            INSERT INTO llm_chatter_messages
            (queue_id, sequence, bot_guid, bot_name,
             message, channel, deliver_at)
            VALUES (%s, 0, %s, %s, %s, %s, NOW())
        """, (
            request['id'], bot['guid'], bot['name'],
            message, channel
        ))
        db.commit()

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
        prompt = build_plain_conversation_prompt(
            bots, zone_id, zone_mobs,
            config, current_weather
        )
    elif msg_type == "quest":
        prompt = build_quest_conversation_prompt(
            bots, quest_data, config, current_weather
        )
    elif msg_type == "trade":
        prompt = build_trade_conversation_prompt(
            bots, item_data, config, current_weather
        )
    elif msg_type == "spell":
        prompt = build_spell_conversation_prompt(
            bots, spell_data, config, current_weather
        )
    else:  # loot
        prompt = build_loot_conversation_prompt(
            bots, item_data, config, current_weather
        )

    # Call LLM
    conversation_max_tokens = int(
        config.get(
            'LLMChatter.ConversationMaxTokens',
            config.get('LLMChatter.MaxTokens', 200)
        )
    )
    response = call_llm(
        client, prompt, config,
        max_tokens_override=conversation_max_tokens
    )

    if response:
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
                )
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
                final_message = cleanup_message(
                    final_message
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

                cursor.execute("""
                    INSERT INTO llm_chatter_messages
                    (queue_id, sequence, bot_guid,
                     bot_name, message, channel,
                     deliver_at)
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        DATE_ADD(NOW(),
                            INTERVAL %s SECOND)
                    )
                """, (
                    request['id'], i, bot_guid,
                    msg['name'], final_message,
                    channel, cumulative_delay
                ))

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
def process_pending_events(
    db, client, config
) -> bool:
    """Process pending events from
    llm_chatter_events table."""
    cursor = db.cursor(dictionary=True)

    # First, find where real players are located
    # (non-RNDBOT accounts)
    # Then prioritize events in those zones
    cursor.execute("""
        SELECT DISTINCT c.zone as player_zone
        FROM characters c
        JOIN acore_auth.account a
            ON c.account = a.id
        WHERE c.online = 1
          AND a.username NOT LIKE 'RNDBOT%%'
    """)
    player_zones = [
        row['player_zone']
        for row in cursor.fetchall()
    ]

    event = None

    # Prefer transport events in zones where real
    # players are
    if player_zones:
        cursor.execute("""
            SELECT e.*
            FROM llm_chatter_events e
            WHERE e.status = 'pending'
              AND e.event_type = 'transport_arrives'
              AND (e.react_after IS NULL
                   OR e.react_after <= NOW())
              AND (e.expires_at IS NULL
                   OR e.expires_at > NOW())
              AND e.zone_id IN (%s)
              AND EXISTS (
                  SELECT 1 FROM characters c
                  JOIN acore_auth.account a
                      ON c.account = a.id
                  WHERE c.online = 1
                    AND c.zone = e.zone_id
                    AND a.username LIKE 'RNDBOT%%%%'
              )
            ORDER BY e.priority ASC,
                     e.created_at ASC
            LIMIT 1
        """ % ','.join(
            ['%s'] * len(player_zones)
        ), tuple(player_zones))
        event = cursor.fetchone()

    if event:
        logger.info(
            f"Prioritizing transport event "
            f"#{event['id']} in zone "
            f"{event.get('zone_id')} "
            f"(player present)"
        )
    else:
        # Get pending events that are ready, but only
        # if they have bots + real player in-zone
        # Uses account-based detection:
        #   RNDBOT% = bot, non-RNDBOT% = real player
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
            ORDER BY e.priority ASC,
                     e.created_at ASC
            LIMIT 1
        """)
        event = cursor.fetchone()

    if not event:
        return False

    event_id = event['id']
    event_type = event['event_type']
    zone_id = event.get('zone_id')

    # Transport events have a chance-based filter
    # (not every arrival should trigger chat)
    if event_type == 'transport_arrives':
        transport_chance = int(config.get(
            'LLMChatter.TransportEventChance', 30
        ))
        roll = random.randint(1, 100)
        if roll > transport_chance:
            # Skip this transport event but don't
            # mark it as failed
            cursor.execute(
                "UPDATE llm_chatter_events "
                "SET status = 'skipped' "
                "WHERE id = %s",
                (event_id,)
            )
            db.commit()
            logger.info(
                f"Transport event #{event_id} "
                f"skipped: chance roll {roll} > "
                f"{transport_chance}%"
            )
            return False

        # Zone-level transport cooldown (prevents
        # multiple boat announcements in same zone)
        if zone_id:
            now = time.time()
            last_transport = (
                _zone_transport_cooldowns.get(
                    zone_id, 0
                )
            )
            if (
                now - last_transport
                < ZONE_TRANSPORT_COOLDOWN_SECONDS
            ):
                remaining = int(
                    ZONE_TRANSPORT_COOLDOWN_SECONDS
                    - (now - last_transport)
                )
                cursor.execute(
                    "UPDATE llm_chatter_events "
                    "SET status = 'skipped' "
                    "WHERE id = %s",
                    (event_id,)
                )
                db.commit()
                logger.info(
                    f"Transport event #{event_id} "
                    f"skipped: zone {zone_id} on "
                    f"cooldown ({remaining}s "
                    f"remaining)"
                )
                return False
            # Update zone cooldown
            _zone_transport_cooldowns[zone_id] = now

    logger.info(
        f"Processing event #{event_id}: {event_type}"
    )

    # Mark as processing
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = 'processing' WHERE id = %s",
        (event_id,)
    )
    db.commit()

    try:
        # Build event context
        event_context = build_event_context(event)

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

        # Check zone fatigue (if zone-specific event)
        # Transport events bypass zone fatigue to
        # ensure they can always fire
        if (
            zone_id
            and event_type != 'transport_arrives'
        ):
            fatigue_threshold = int(config.get(
                'LLMChatter.ZoneFatigueThreshold', 3
            ))
            fatigue_cooldown = int(config.get(
                'LLMChatter.ZoneFatigueCooldownSeconds',
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
                and result['cnt'] >= fatigue_threshold
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
                    f"({fatigue_threshold}) reached"
                )
                return False

        # Decide: statement vs conversation
        # (configurable, default 60% conversation)
        # Conversations require at least 2 bots
        event_conv_chance = int(config.get(
            'LLMChatter.EventConversationChance', 60
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

            bot_names = [b['name'] for b in bots]
            bot_guids = {
                b['name']: b['guid'] for b in bots
            }

            logger.info(
                f"Event #{event_id} triggering "
                f"{num_bots}-bot conversation: "
                f"{', '.join(bot_names)}"
            )

            # Get weather from event extra_data
            extra_data = event.get('extra_data', {})
            if isinstance(extra_data, str):
                try:
                    extra_data = json.loads(extra_data)
                except Exception:
                    extra_data = {}
            current_weather = extra_data.get(
                'current_weather', 'clear'
            )

            # Build event conversation prompt
            prompt = build_event_conversation_prompt(
                bots, event_context, zone_id,
                config, current_weather
            )

            # Call LLM
            response = call_llm(
                client, prompt, config
            )

            if response:
                messages = (
                    parse_conversation_response(
                        response, bot_names
                    )
                )

                if messages:
                    logger.info(
                        f"Event conversation with "
                        f"{len(messages)} messages:"
                    )

                    cumulative_delay = 0.0
                    for i, msg in enumerate(messages):
                        bot_guid = bot_guids.get(
                            msg['name'],
                            bots[0]['guid']
                        )
                        final_message = (
                            cleanup_message(
                                msg['message']
                            )
                        )

                        if i > 0:
                            delay = (
                                calculate_dynamic_delay(
                                    len(final_message),
                                    config
                                )
                            )
                            cumulative_delay += delay

                        cursor.execute("""
                            INSERT INTO
                                llm_chatter_messages
                            (event_id, sequence,
                             bot_guid, bot_name,
                             message, channel,
                             delivered, deliver_at)
                            VALUES (
                                %s, %s, %s, %s, %s,
                                'general', 0,
                                DATE_ADD(NOW(),
                                    INTERVAL %s
                                    SECOND)
                            )
                        """, (
                            event_id, i, bot_guid,
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
                        "UPDATE llm_chatter_events "
                        "SET status = 'completed', "
                        "processed_at = NOW() "
                        "WHERE id = %s",
                        (event_id,)
                    )
                    db.commit()
                    return True

            # Fallback to statement if conversation
            # failed
            logger.warning(
                "Event conversation failed, falling "
                "back to statement"
            )
            use_conversation = False

        # Statement mode (single bot)
        if not use_conversation:
            bot = dict(
                random.choice(list(recent_bots))
            )
            is_transport_event = (
                event_type == 'transport_arrives'
            )

            # Transport events bypass cooldown -
            # they're high priority
            if not is_transport_event:
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
                      AND delivered_at > DATE_SUB(
                          NOW(), INTERVAL %s SECOND
                      )
                """, (bot['bot1_guid'], cooldown))
                result = cursor.fetchone()
                if result and result['cnt'] > 0:
                    cursor.execute(
                        "UPDATE llm_chatter_events "
                        "SET status = 'skipped' "
                        "WHERE id = %s",
                        (event_id,)
                    )
                    db.commit()
                    logger.info(
                        f"Event #{event_id} skipped:"
                        f" bot {bot['bot1_name']} "
                        f"on cooldown"
                    )
                    return False
            else:
                logger.info(
                    f"Transport event #{event_id}: "
                    f"bypassing cooldown for bot "
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
                or 'zeppelin' in event_context.lower()
                or 'turtle' in event_context.lower()
            )
            if is_transport:
                event_instruction = (
                    "Comment on this transport "
                    "arrival! Use the specific type "
                    "(boat/zeppelin/turtle), NOT "
                    "'transport'.\n"
                    "Mention the destination if "
                    "known. Be creative and original"
                    " - no canned phrases."
                )
            else:
                event_instruction = (
                    "You may naturally reference this"
                    " event in your message, or you "
                    "may chat about something else "
                    "entirely.\n"
                    "The event provides atmosphere - "
                    "you don't HAVE to mention it "
                    "explicitly."
                )

            # Environmental context
            extra_data = event.get('extra_data', {})
            if isinstance(extra_data, str):
                try:
                    extra_data = json.loads(extra_data)
                except Exception:
                    extra_data = {}
            weather_for_context = None
            if 'weather' not in event_context.lower():
                weather_for_context = extra_data.get(
                    'current_weather', 'clear'
                )

            env_context = get_environmental_context(
                weather_for_context
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
                rp_ctx = build_race_class_context(
                    bot['bot1_race'],
                    bot['bot1_class']
                )
                if rp_ctx:
                    rp_personality = f"\n{rp_ctx}"
                rp_style = (
                    "\nStay in character but keep it "
                    "natural and conversational. No "
                    "game terms or OOC references, "
                    "but don't be overly dramatic or "
                    "theatrical either."
                )

            system_prompt = (
                f"You are {bot['bot1_name']}, a "
                f"{bot['bot1_race']} "
                f"{bot['bot1_class']} adventurer in "
                f"World of Warcraft.\n"
                f"You are level {bot['bot1_level']} "
                f"and currently in {zone_name}."
                f"{env_lines}{rp_personality}\n\n"
                f"CONTEXT: {event_context}\n\n"
                f"{event_instruction}\n\n"
                f"Your current mood: {tone}"
                f"{rp_style}\n\n"
                f"Respond with a single short "
                f"sentence (under 100 characters) "
                f"that a player might say in General "
                f"chat.\n"
                f"Be "
                f"{'authentic and in-character' if is_rp else 'casual and authentic'}"
                f". No quotes. No asterisks. "
                f"No emotes."
            )

            # Call LLM
            provider = config.get(
                'LLMChatter.Provider', 'anthropic'
            ).lower()
            model = resolve_model(config.get(
                'LLMChatter.Model', 'haiku'
            ))
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
                # Ollama uses OpenAI-compatible API
                context_size = int(config.get(
                    'LLMChatter.Ollama.ContextSize',
                    2048
                ))
                response = (
                    client.chat.completions.create(
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
                                    "Say something "
                                    "in General chat."
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
                    client.chat.completions.create(
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
                                    "Say something "
                                    "in General chat."
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
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content":
                            "Say something in "
                            "General chat."
                    }]
                )
                message = (
                    response.content[0].text.strip()
                )

            # Clean up message
            message = message.strip('"').strip()
            message = cleanup_message(message)
            if len(message) > 255:
                message = message[:252] + "..."

            # Insert message for delivery
            delay_min = int(config.get(
                'LLMChatter.MessageDelayMin', 1000
            ))
            delay_max = int(config.get(
                'LLMChatter.MessageDelayMax', 30000
            ))
            delay_ms = random.randint(
                delay_min, delay_max
            )

            cursor.execute("""
                INSERT INTO llm_chatter_messages
                (event_id, sequence, bot_guid,
                 bot_name, message, channel,
                 delivered, deliver_at)
                VALUES (
                    %s, 0, %s, %s, %s, 'general', 0,
                    DATE_ADD(NOW(),
                        INTERVAL %s SECOND)
                )
            """, (
                event_id, bot['bot1_guid'],
                bot['bot1_name'], message,
                delay_ms // 1000
            ))

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
            f"Error processing event "
            f"#{event_id}: {e}"
        )
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = 'skipped' "
            "WHERE id = %s",
            (event_id,)
        )
        db.commit()
        return False


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

    # Get provider and initialize appropriate client
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()
    model_alias = config.get(
        'LLMChatter.Model', 'haiku'
    )
    model = resolve_model(model_alias)

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

    # Check event system config
    use_event_system = (
        config.get(
            'LLMChatter.UseEventSystem', '1'
        ) == '1'
    )

    chatter_mode = get_chatter_mode(config)

    logger.info("=" * 60)
    logger.info("LLM Chatter Bridge v3.6")
    logger.info("=" * 60)
    logger.info(f"ChatterMode: {chatter_mode}")
    logger.info(f"Provider: {provider}")
    logger.info(
        f"Model: {model} (alias: {model_alias})"
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
    logger.info("Chatter settings (from config):")
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
        f"  BotSpeakerCooldownSeconds: "
        f"{config.get('LLMChatter.BotSpeakerCooldownSeconds', 900)}"
    )
    logger.info(
        f"  ZoneFatigueThreshold: "
        f"{config.get('LLMChatter.ZoneFatigueThreshold', 3)}"
    )
    logger.info("-" * 60)
    logger.info("Transport settings:")
    logger.info(
        f"  TransportEventChance: "
        f"{config.get('LLMChatter.TransportEventChance', 30)}%"
    )
    logger.info(
        f"  TransportCooldownSeconds (C++): "
        f"{config.get('LLMChatter.TransportCooldownSeconds', 300)}"
    )
    logger.info(
        f"  ZoneTransportCooldown (Python): "
        f"{ZONE_TRANSPORT_COOLDOWN_SECONDS}s"
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
        try:
            db = get_db_connection(config)
            reset_stuck_processing_events(db)
            db.close()
        except Exception as e:
            logger.warning(
                f"Could not reset stuck events on "
                f"startup: {e}"
            )

    # Main loop
    last_cleanup = 0
    cleanup_interval = 60  # every 60 seconds

    while True:
        try:
            db = get_db_connection(config)

            # Periodic cleanup of expired events
            current_time = time.time()
            if (
                use_event_system
                and current_time - last_cleanup
                >= cleanup_interval
            ):
                cleanup_expired_events(db)
                last_cleanup = current_time

            # Process regular chatter requests
            processed_request = (
                process_pending_requests(
                    db, client, config
                )
            )

            # Process event-driven chatter
            # (if enabled)
            processed_event = False
            if use_event_system:
                processed_event = (
                    process_pending_events(
                        db, client, config
                    )
                )

            db.close()

            # Only sleep if nothing was processed
            if (
                not processed_request
                and not processed_event
            ):
                time.sleep(poll_interval)

        except mysql.connector.Error as e:
            logger.error(f"Database error: {e}")
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(poll_interval)


if __name__ == '__main__':
    main()
