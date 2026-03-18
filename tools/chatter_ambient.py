"""Ambient chatter runtime processors.

N9/N10 moved statement and conversation
processing from the bridge.
"""

import logging
import random
import time
from typing import List

from chatter_constants import (
    CAPITAL_CITY_ZONES,
    AMBIENT_CHAT_TOPICS,
    AMBIENT_CHAT_TOPICS_RP,
)
from chatter_shared import (
    zone_cache,
    parse_single_response,
    parse_conversation_response,
    extract_conversation_msg_count,
    can_class_use_item,
    query_zone_quests,
    query_zone_loot,
    query_zone_mobs,
    query_bot_spells,
    replace_placeholders,
    cleanup_message,
    strip_speaker_prefix,
    call_llm,
    insert_chat_message,
    get_recent_zone_messages,
    is_too_similar,
    get_action_chance,
    select_message_type,
    calculate_dynamic_delay,
    get_chatter_mode,
    _zone_last_delivery,
    _zone_delivery_delay,
    get_zone_name,
    get_zone_flavor,
    get_subzone_name,
    get_subzone_lore,
)
from chatter_shared import (
    build_talent_context,
    build_zone_metadata,
)
from chatter_prompts import (
    build_plain_statement_prompt,
    build_quest_statement_prompt,
    build_loot_statement_prompt,
    build_quest_reward_statement_prompt,
    build_spell_statement_prompt,
    build_trade_statement_prompt,
    build_plain_conversation_prompt,
    build_quest_conversation_prompt,
    build_loot_conversation_prompt,
    build_trade_conversation_prompt,
    build_spell_conversation_prompt,
)

logger = logging.getLogger(__name__)


def _build_zone_metadata(zone_id, area_id=0):
    """Build zone metadata dict for request logging.

    Thin wrapper around build_zone_metadata() that
    resolves zone/subzone names from IDs first.
    """
    return build_zone_metadata(
        zone_name=get_zone_name(zone_id) or '',
        zone_flavor=get_zone_flavor(zone_id) or '',
        subzone_name=(
            get_subzone_name(zone_id, area_id) or ''
        ),
        subzone_lore=(
            get_subzone_lore(zone_id, area_id) or ''
        ),
    )


def _fetch_loot_data(config, zone_id, level):
    """Fetch and select a loot item for the zone.

    Handles: query_zone_loot, cooldown filter,
    quality weights, random.choices, mark_loot_seen.

    Returns item_data dict or None if no loot found.
    """
    loot = query_zone_loot(config, zone_id, level)
    if not loot:
        return None
    cooldown = int(config.get(
        'LLMChatter.LootRecentCooldownSeconds', 0
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
    if cooldown > 0 and item_data.get('item_id'):
        zone_cache.mark_loot_seen(
            zone_id, item_data['item_id']
        )
    return item_data


def process_statement(
    db, cursor, client, config, request, bot: dict
):
    """Process a single statement request."""
    channel = 'general'

    # Select message type
    zone_id = request.get('zone_id', 0)
    area_id = request.get('area_id', zone_id)
    current_weather = request.get('weather', 'clear')
    mode = get_chatter_mode(config)

    # Zone metadata for request logging
    zone_meta = _build_zone_metadata(
        zone_id, area_id
    )
    msg_type = select_message_type()

    # Skip loot/trade in capital cities (no zone
    # creatures to reference, causes empty queries)
    if (
        msg_type in ("loot", "trade")
        and zone_id in CAPITAL_CITY_ZONES
    ):
        msg_type = "plain"


    # Get zone data if needed
    quest_data = None
    item_data = None
    item_can_use = False
    spell_data = None

    if msg_type == "quest" or msg_type == "quest_reward":
        quests = query_zone_quests(
            config, zone_id, bot['level']
        )
        if quests:
            quest_data = random.choice(quests)
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "loot":
        item_data = _fetch_loot_data(
            config, zone_id, bot['level']
        )
        if item_data:
            # Check if bot's class can use the item
            item_can_use = can_class_use_item(
                bot['class'],
                item_data.get('allowable_class', -1)
            )
            quality_names = {
                0: "gray", 1: "white", 2: "green",
                3: "blue", 4: "epic"
            }
        else:
            msg_type = "plain"  # Fallback

    if msg_type == "trade":
        item_data = _fetch_loot_data(
            config, zone_id, bot['level']
        )
        if not item_data:
            msg_type = "plain"  # Fallback

    if msg_type == "spell":
        spells = query_bot_spells(
            config, bot['class'], bot['level']
        )
        if spells:
            spell_data = random.choice(spells)
        else:
            msg_type = "plain"  # Fallback

    # Fetch recent zone messages for anti-repetition
    recent_msgs = get_recent_zone_messages(
        db, zone_id
    )

    # Talent context injection (speaker only)
    speaker_talent = None
    talent_chance = int(config.get(
        'LLMChatter.TalentInjectionChance', '40',
    ))
    if (
        talent_chance > 0
        and random.randint(1, 100)
        <= talent_chance
    ):
        speaker_talent = build_talent_context(
            db, bot['guid'], bot['class'],
            bot['name'], perspective='speaker',
        )

    # Build appropriate prompt
    allow_action = (
        random.random() < get_action_chance()
    )
    chosen_topic = ""
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
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        topic = random.choice(topic_pool)
        chosen_topic = topic
        prompt = build_plain_statement_prompt(
            bot, zone_id, zone_mobs,
            config, current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            speaker_talent_context=speaker_talent,
            topic=topic,
            area_id=area_id,
        )
    elif msg_type == "quest":
        prompt = build_quest_statement_prompt(
            bot, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            speaker_talent_context=speaker_talent,
        )
    elif msg_type == "loot":
        prompt = build_loot_statement_prompt(
            bot, item_data, item_can_use,
            config, current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            speaker_talent_context=speaker_talent,
        )
    elif msg_type == "quest_reward":
        prompt = build_quest_reward_statement_prompt(
            bot, quest_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            speaker_talent_context=speaker_talent,
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
            speaker_talent_context=speaker_talent,
        )
    elif msg_type == "spell":
        prompt = build_spell_statement_prompt(
            bot, spell_data, config,
            current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            speaker_talent_context=speaker_talent,
        )
    else:
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        topic = random.choice(topic_pool)
        prompt = build_plain_statement_prompt(
            bot, zone_id,
            config=config,
            current_weather=current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            speaker_talent_context=speaker_talent,
            topic=topic,
            area_id=area_id,
        )

    # Call LLM
    if speaker_talent:
        zone_meta['speaker_talent'] = (
            speaker_talent
        )
    response = call_llm(
        client, prompt, config,
        context=f"ambient:{bot['name']}",
        label='ambient_statement',
        metadata=zone_meta,
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
            return True


        # Insert for delivery — enforce zone gap
        extra = _zone_delivery_delay(zone_id, config)
        topic_label = (
            f" topic={chosen_topic}"
            if chosen_topic else ""
        )
        logger.info(
            "[GEN-FLOW] ambient statement | "
            "type=%s%s bot=%s delay=%.1fs seq=0",
            msg_type, topic_label, bot['name'],
            extra,
        )
        insert_chat_message(
            db, bot['guid'], bot['name'], message,
            channel=channel,
            delay_seconds=extra,
            queue_id=request['id'],
            sequence=0,
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


    zone_id = request.get('zone_id', 0)
    area_id = request.get('area_id', zone_id)
    current_weather = request.get('weather', 'clear')
    mode = get_chatter_mode(config)

    # Zone metadata for request logging
    zone_meta = _build_zone_metadata(
        zone_id, area_id
    )

    # Fetch recent zone messages for anti-repetition
    recent_msgs = get_recent_zone_messages(
        db, zone_id
    )

    # Talent context injection (speaker only,
    # uses first bot as representative)
    speaker_talent = None
    talent_chance = int(config.get(
        'LLMChatter.TalentInjectionChance', '40',
    ))
    if (
        talent_chance > 0
        and random.randint(1, 100)
        <= talent_chance
    ):
        speaker_talent = build_talent_context(
            db, bots[0]['guid'],
            bots[0]['class'],
            bots[0]['name'],
            perspective='speaker',
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
        else:
            msg_type = "plain"

    if msg_type == "loot":
        item_data = _fetch_loot_data(
            config, zone_id, bots[0]['level']
        )
        if not item_data:
            msg_type = "plain"

    if msg_type == "trade":
        item_data = _fetch_loot_data(
            config, zone_id, bots[0]['level']
        )
        if not item_data:
            msg_type = "plain"

    if msg_type == "spell":
        spells = query_bot_spells(
            config, bots[0]['class'],
            bots[0]['level']
        )
        if spells:
            spell_data = random.choice(spells)
        else:
            msg_type = "plain"

    # Build prompt
    chosen_topic = ""
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
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        topic = random.choice(topic_pool)
        chosen_topic = topic
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_plain_conversation_prompt(
            bots, zone_id, zone_mobs,
            config, current_weather,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            speaker_talent_context=speaker_talent,
            topic=topic,
            area_id=area_id,
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
            speaker_talent_context=speaker_talent,
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
            speaker_talent_context=speaker_talent,
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
            speaker_talent_context=speaker_talent,
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
            speaker_talent_context=speaker_talent,
        )

    # Call LLM
    conversation_max_tokens = int(
        config.get(
            'LLMChatter.ConversationMaxTokens',
            config.get('LLMChatter.MaxTokens', 200)
        )
    )
    if speaker_talent:
        zone_meta['speaker_talent'] = (
            speaker_talent
        )
    bot_names_ctx = ','.join(bot_names)
    response = call_llm(
        client, prompt, config,
        max_tokens_override=conversation_max_tokens,
        context=f"ambient-conv:{bot_names_ctx}",
        label='ambient_conv',
        metadata=zone_meta,
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
                ),
                context="json-repair",
                label='ambient_conv',
                metadata=zone_meta,
            )
            if response:
                messages = (
                    parse_conversation_response(
                        response, bot_names
                    )
                )

        if messages:
            # Zone gap applies to first message only;
            # conversation followups stagger on top
            base_delay = _zone_delivery_delay(
                zone_id, config
            )
            cumulative_delay = base_delay
            prev_msg_len = 0
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
                        len(final_message), config,
                        prev_message_length=prev_msg_len,
                    )
                    cumulative_delay += delay
                prev_msg_len = len(final_message)

                topic_label = (
                    f" topic={chosen_topic}"
                    if chosen_topic else ""
                )
                logger.info(
                    "[GEN-FLOW] ambient conv | "
                    "type=%s%s bot=%s delay=%.1fs "
                    "seq=%d/%d",
                    msg_type, topic_label,
                    msg['name'],
                    cumulative_delay, i,
                    len(messages),
                )
                insert_chat_message(
                    db, bot_guid,
                    msg['name'], final_message,
                    channel=channel,
                    delay_seconds=cumulative_delay,
                    queue_id=request['id'],
                    sequence=i,
                )


            # Push zone timestamp to after the last
            # message so the gap applies from the END
            # of the conversation, not the start
            _zone_last_delivery[zone_id] = (
                time.monotonic() + cumulative_delay
            )
            db.commit()
            return True
    return False
