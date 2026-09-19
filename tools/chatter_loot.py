"""Real bot-loot announcements for General chat.

The C++ producer captures an item from an actual loot callback. This
consumer resolves only that bot and turns the captured value snapshot
into one General-channel message.
"""

import logging

from chatter_db import (
    get_bots_by_guid,
    get_recent_zone_messages,
    insert_chat_message,
    mark_event,
)
from chatter_group_general_reaction import (
    maybe_queue_group_general_reaction,
)
from chatter_prompts import build_loot_statement_prompt
from chatter_shared import (
    _zone_delivery_delay,
    call_llm,
    can_class_use_item,
    cleanup_message,
    get_class_name,
    get_race_name,
    get_zone_name,
    parse_extra_data,
    parse_single_response,
    replace_placeholders,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)


def _skip(db, event_id, reason):
    logger.info(
        "[GEN-LOOT] event=%s skipped: %s",
        event_id, reason,
    )
    mark_event(db, event_id, 'skipped')
    return False


def _parse_item(extra_data):
    """Validate the value-only item snapshot from C++."""
    if not isinstance(extra_data, dict):
        return None

    required_ints = (
        'item_id', 'item_quality', 'item_count',
        'allowable_class', 'required_level',
    )
    for key in required_ints:
        value = extra_data.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            return None

    item_name = extra_data.get('item_name')
    if not isinstance(item_name, str) or not item_name.strip():
        return None

    if (
        extra_data['item_id'] <= 0
        or not 0 <= extra_data['item_quality'] <= 7
        or extra_data['item_count'] <= 0
        or extra_data['required_level'] < 0
    ):
        return None

    return {
        'item_id': extra_data['item_id'],
        'item_name': item_name.strip(),
        'item_quality': extra_data['item_quality'],
        'item_count': extra_data['item_count'],
        'allowable_class': extra_data['allowable_class'],
        'required_level': extra_data['required_level'],
    }


def _resolve_looter(db, subject_guid):
    """Resolve exactly one online random bot by its event GUID."""
    cursor = db.cursor(dictionary=True)
    try:
        bots = get_bots_by_guid(cursor, [subject_guid])
    finally:
        cursor.close()

    if len(bots) != 1:
        return None

    row = bots[0]
    bot_class = row.get('bot1_class')
    bot_race = row.get('bot1_race')
    if isinstance(bot_class, int):
        bot_class = get_class_name(bot_class)
    if isinstance(bot_race, int):
        bot_race = get_race_name(bot_race)

    return {
        'guid': int(row['bot1_guid']),
        'name': row['bot1_name'],
        'class': bot_class,
        'race': bot_race,
        'level': int(row['bot1_level']),
    }


def process_general_loot_event(db, client, config, event):
    """Publish one actual bot loot item to General chat."""
    event_id = event['id']
    try:
        subject_guid = int(event.get('subject_guid') or 0)
        zone_id = int(event.get('zone_id') or 0)
    except (TypeError, ValueError):
        return _skip(db, event_id, 'invalid bot or zone GUID')

    if subject_guid <= 0 or zone_id <= 0:
        return _skip(db, event_id, 'missing bot or zone GUID')

    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        event.get('event_type', ''),
    )
    item = _parse_item(extra_data)
    if not item:
        return _skip(db, event_id, 'invalid item snapshot')

    bot = _resolve_looter(db, subject_guid)
    if not bot:
        return _skip(db, event_id, 'looter is offline or not a bot')

    bot['zone'] = get_zone_name(zone_id) or 'the world'
    can_use = can_class_use_item(
        bot['class'], item['allowable_class']
    )
    recent_messages = get_recent_zone_messages(db, zone_id)
    prompt = build_loot_statement_prompt(
        bot,
        item,
        can_use,
        config=config,
        recent_messages=recent_messages,
        zone_id=zone_id,
    )

    response = call_llm(
        client,
        prompt,
        config,
        context=f"general-loot:{bot['name']}",
        label='general_loot',
    )
    if not response:
        return _skip(db, event_id, 'empty LLM response')

    parsed = parse_single_response(response)
    if not isinstance(parsed, dict):
        return _skip(db, event_id, 'invalid parsed response')
    raw_message = parsed.get('message', '')
    if not isinstance(raw_message, str):
        return _skip(db, event_id, 'invalid parsed message')
    message = replace_placeholders(
        raw_message, item_data=item
    )
    message = strip_speaker_prefix(message, bot['name'])
    message = cleanup_message(
        message, action=parsed.get('action')
    )
    if not message:
        return _skip(db, event_id, 'empty parsed message')

    delay = _zone_delivery_delay(zone_id, config)
    insert_chat_message(
        db,
        bot['guid'],
        bot['name'],
        message,
        channel='general',
        delay_seconds=delay,
        event_id=event_id,
        sequence=0,
    )
    maybe_queue_group_general_reaction(
        db,
        config,
        bot['guid'],
        bot['name'],
        message,
        zone_id,
        int(event.get('map_id') or 0),
        source_event_id=event_id,
        source_sequence=0,
        source_delay_seconds=delay,
    )
    mark_event(db, event_id, 'completed')
    return True
