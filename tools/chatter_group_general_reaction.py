"""Group reactions to bot-authored General chat.

This module owns the cross-channel relay from General chat into party
chat. It intentionally keeps the feature out of the low-level message
insert helper so normal General and party delivery paths stay reusable.
"""

import json
import logging
import random
import time
from typing import Dict, List, Optional

from chatter_db import (
    get_real_player_guid_for_group,
    get_group_location,
    mark_event,
)
from chatter_group_state import (
    _get_recent_chat,
    _mark_event,
    _store_chat,
    format_chat_history,
    get_group_player_name,
)
from chatter_shared import (
    append_conversation_json_instruction,
    append_json_instruction,
    build_travel_state_from_row,
    calculate_dynamic_delay,
    call_llm,
    cleanup_message,
    format_travel_context,
    get_chatter_mode,
    get_class_name,
    get_dungeon_flavor,
    get_gender_label,
    get_race_name,
    get_subzone_lore,
    get_subzone_name,
    get_zone_flavor,
    get_zone_name,
    insert_chat_message,
    parse_conversation_response,
    parse_extra_data,
    parse_single_response,
    strip_conversation_actions,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)

EVENT_TYPE = 'bot_group_general_reaction'
PRIORITY_HIGH_LOCAL = 21


def _int_config(
    config: dict,
    key: str,
    default: int,
    minimum: int = 0,
    maximum: int = 100000,
) -> int:
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _relay_enabled(config: dict) -> bool:
    return str(config.get(
        'LLMChatter.GroupChatter.GeneralRelayEnable',
        '1',
    )).strip() == '1'


def _fetch_group_candidates(
    db,
    zone_id: int,
    map_id: int,
    source_bot_guid: int,
) -> List[Dict]:
    """Return active group candidates in the source zone."""
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.group_id, t.bot_guid, t.bot_name,
               t.trait1, t.trait2, t.trait3, t.tone,
               t.zone, t.area, t.map,
               t.travel_mode, t.travel_context,
               t.is_mounted, t.is_flying,
               t.is_taxi_flying, t.is_on_transport,
               t.mount_display_id, t.transport_name,
               c.class, c.race, c.level, c.gender
        FROM llm_group_bot_traits t
        JOIN characters c ON c.guid = t.bot_guid
        WHERE t.zone = %s
    """, (zone_id,))
    rows = cursor.fetchall()
    cursor.close()

    grouped = {}
    for row in rows:
        gid = int(row.get('group_id') or 0)
        if not gid:
            continue
        if map_id and int(row.get('map') or 0) not in (0, map_id):
            continue
        grouped.setdefault(gid, []).append(row)

    candidates = []
    for group_id, bots in grouped.items():
        responders = [
            b for b in bots
            if int(b.get('bot_guid') or 0) != source_bot_guid
        ]
        if responders:
            candidates.append({
                'group_id': group_id,
                'bots': responders,
            })
    return candidates


def _get_player_name_for_group(db, group_id: int) -> str:
    player_guid = get_real_player_guid_for_group(db, group_id)
    if player_guid:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT name FROM characters WHERE guid = %s",
            (player_guid,),
        )
        row = cursor.fetchone()
        cursor.close()
        if row and row.get('name'):
            return row['name']
    return get_group_player_name(db, group_id) or 'the player'


def _cooldown_active(
    db,
    group_id: int,
    cooldown_seconds: int,
) -> bool:
    if cooldown_seconds <= 0:
        return False
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT 1
        FROM llm_chatter_events
        WHERE event_type = %s
          AND cooldown_key = %s
          AND created_at > DATE_SUB(
              NOW(), INTERVAL %s SECOND
          )
        LIMIT 1
    """, (
        EVENT_TYPE,
        f"group_general_relay:{group_id}",
        cooldown_seconds,
    ))
    row = cursor.fetchone()
    cursor.close()
    return bool(row)


def maybe_queue_group_general_reaction(
    db,
    config: dict,
    source_bot_guid: int,
    source_bot_name: str,
    message: str,
    zone_id: int,
    map_id: int = 0,
    source_event_id: Optional[int] = None,
    source_queue_id: Optional[int] = None,
    source_sequence: int = 0,
    source_delay_seconds: float = 0,
) -> bool:
    """Maybe queue a party reaction to a General bot line."""
    if not _relay_enabled(config):
        return False
    if not source_bot_guid or not source_bot_name:
        return False
    if not zone_id or not message or len(message.strip()) < 8:
        return False

    chance = _int_config(
        config,
        'LLMChatter.GroupChatter.GeneralRelayChance',
        15,
        maximum=100,
    )
    if chance <= 0 or random.randint(1, 100) > chance:
        return False

    candidates = _fetch_group_candidates(
        db, int(zone_id), int(map_id or 0),
        int(source_bot_guid),
    )
    if not candidates:
        return False

    random.shuffle(candidates)
    max_groups = _int_config(
        config,
        'LLMChatter.GroupChatter.GeneralRelayMaxGroups',
        1,
        minimum=1,
        maximum=5,
    )
    cooldown = _int_config(
        config,
        'LLMChatter.GroupChatter.GeneralRelayCooldown',
        120,
        maximum=3600,
    )
    min_lag = _int_config(
        config,
        'LLMChatter.GroupChatter.GeneralRelayMinLagSeconds',
        3,
        maximum=30,
    )
    max_lag = _int_config(
        config,
        'LLMChatter.GroupChatter.GeneralRelayMaxLagSeconds',
        6,
        minimum=min_lag,
        maximum=60,
    )

    queued = 0
    source_visible_at = (
        time.time() + max(0.0, float(source_delay_seconds or 0))
    )
    for candidate in candidates:
        group_id = int(candidate['group_id'])
        if _cooldown_active(db, group_id, cooldown):
            continue

        player_name = _get_player_name_for_group(db, group_id)
        extra_data = {
            'group_id': group_id,
            'zone_id': int(zone_id),
            'map_id': int(map_id or 0),
            'source_bot_guid': int(source_bot_guid),
            'source_bot_name': source_bot_name,
            'source_message': message[:500],
            'source_channel': 'general',
            'source_event_id': source_event_id,
            'source_queue_id': source_queue_id,
            'source_sequence': int(source_sequence or 0),
            'source_visible_at_epoch': source_visible_at,
            'relay_min_lag_seconds': min_lag,
            'relay_max_lag_seconds': max_lag,
            'player_name': player_name,
        }

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO llm_chatter_events
                (event_type, event_scope, zone_id, map_id,
                 priority, cooldown_key, subject_guid,
                 subject_name, target_guid, target_name,
                 extra_data, status, react_after, expires_at)
            VALUES (
                %s, 'player', %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, 'pending', NOW(),
                DATE_ADD(NOW(), INTERVAL 120 SECOND)
            )
        """, (
            EVENT_TYPE,
            int(zone_id),
            int(map_id or 0),
            PRIORITY_HIGH_LOCAL,
            f"group_general_relay:{group_id}",
            int(source_bot_guid),
            source_bot_name,
            group_id,
            player_name,
            json.dumps(extra_data),
        ))
        db.commit()
        cursor.close()
        queued += 1
        if queued >= max_groups:
            break

    if queued:
        logger.info(
            "[GEN-RELAY] queued %d group reaction(s) "
            "source=%s zone=%s",
            queued, source_bot_name, zone_id,
        )
    return queued > 0


def _row_to_bot(row: Dict) -> Dict:
    travel_state = build_travel_state_from_row(row)
    return {
        'guid': int(row['bot_guid']),
        'name': row['bot_name'],
        'class': get_class_name(row['class']),
        'race': get_race_name(row['race']),
        'level': int(row['level']),
        'gender': get_gender_label(row.get('gender')),
        'trait1': row.get('trait1') or '',
        'trait2': row.get('trait2') or '',
        'trait3': row.get('trait3') or '',
        'tone': row.get('tone') or '',
        'travel_state': travel_state,
        'travel_context': format_travel_context(travel_state),
    }


def _fetch_group_bots(db, group_id: int, source_bot_guid: int) -> List[Dict]:
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.bot_guid, t.bot_name,
               t.trait1, t.trait2, t.trait3, t.tone,
               t.travel_mode, t.travel_context,
               t.is_mounted, t.is_flying,
               t.is_taxi_flying, t.is_on_transport,
               t.mount_display_id, t.transport_name,
               c.class, c.race, c.level, c.gender
        FROM llm_group_bot_traits t
        JOIN characters c ON c.guid = t.bot_guid
        WHERE t.group_id = %s
          AND t.bot_guid <> %s
    """, (group_id, source_bot_guid))
    rows = cursor.fetchall()
    cursor.close()
    return [_row_to_bot(r) for r in rows]


def _fetch_source_bot_info(db, source_bot_guid: int) -> Dict:
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, class, race, level, gender
        FROM characters
        WHERE guid = %s
    """, (source_bot_guid,))
    row = cursor.fetchone()
    cursor.close()
    if not row:
        return {}
    return {
        'name': row.get('name') or '',
        'class': get_class_name(row.get('class')),
        'race': get_race_name(row.get('race')),
        'level': int(row.get('level') or 0),
        'gender': get_gender_label(row.get('gender')),
    }


def _source_name_in_message(message: str, source_name: str) -> bool:
    return (
        bool(message)
        and bool(source_name)
        and source_name.lower() in message.lower()
    )


def _ensure_source_name(
    message: str,
    source_name: str,
) -> str:
    if _source_name_in_message(message, source_name):
        return message
    return f"{source_name} in General... {message}"


def _clamp_message(message: str) -> str:
    if len(message) > 255:
        return message[:252] + "..."
    return message


def _first_delay(extra_data: Dict) -> float:
    visible_at = float(
        extra_data.get('source_visible_at_epoch') or time.time()
    )
    min_lag = int(extra_data.get('relay_min_lag_seconds') or 3)
    max_lag = int(extra_data.get('relay_max_lag_seconds') or 6)
    max_lag = max(min_lag, max_lag)
    target_at = visible_at + random.uniform(min_lag, max_lag)
    return max(0.0, target_at - time.time())


def _location_context(db, group_id: int) -> Dict:
    zone_id, area_id, map_id = get_group_location(db, group_id)
    dungeon = get_dungeon_flavor(map_id)
    return {
        'zone_id': zone_id,
        'area_id': area_id,
        'map_id': map_id,
        'zone_name': get_zone_name(zone_id) or '',
        'zone_flavor': get_zone_flavor(zone_id) or '',
        'subzone_name': get_subzone_name(zone_id, area_id) or '',
        'subzone_lore': get_subzone_lore(zone_id, area_id) or '',
        'dungeon_flavor': dungeon or '',
    }


def _build_statement_prompt(
    bot: Dict,
    source_bot: Dict,
    source_message: str,
    player_name: str,
    chat_hist: str,
    mode: str,
    loc: Dict,
) -> str:
    is_rp = (mode == 'roleplay')
    traits = ', '.join(
        t for t in [
            bot.get('trait1'),
            bot.get('trait2'),
            bot.get('trait3'),
        ] if t
    )
    prompt = (
        f"{bot['name']} is a level {bot['level']} "
        f"{bot['race']} {bot['class']} in a party "
        f"with {player_name}.\n"
    )
    if traits:
        prompt += f"Personality traits: {traits}.\n"
    if bot.get('travel_context'):
        prompt += f"{bot['travel_context']}\n"
    if loc.get('dungeon_flavor'):
        prompt += f"Dungeon context: {loc['dungeon_flavor']}\n"
    elif loc.get('zone_flavor'):
        prompt += f"Zone context: {loc['zone_flavor']}\n"
    if loc.get('subzone_lore'):
        prompt += f"Subzone context: {loc['subzone_lore']}\n"
    if chat_hist:
        prompt += f"{chat_hist}\n"

    source_desc = source_bot.get('name') or 'the bot'
    source_bits = [
        source_bot.get('race', ''),
        source_bot.get('class', ''),
    ]
    source_detail = ' '.join(b for b in source_bits if b)
    if source_detail:
        source_desc += f" ({source_detail})"

    prompt += (
        f"\nA bot named {source_desc} just said in "
        f"General chat:\n\"{source_message}\"\n\n"
        "Generate one party chat reaction from "
        f"{bot['name']} to {player_name}. "
        "This is private party chat, not another "
        "General reply.\n"
        f"HARD RULE: The message text must mention "
        f"{source_bot['name']} by name.\n"
    )
    if is_rp:
        prompt += (
            "Stay in character for race and class. "
            "Keep it natural, brief, and grounded.\n"
        )
    else:
        prompt += (
            "Sound like a normal WoW player. Keep it "
            "brief and casual.\n"
        )
    return append_json_instruction(
        prompt,
        allow_action=is_rp,
    )


def _build_conversation_prompt(
    bots: List[Dict],
    source_bot: Dict,
    source_message: str,
    player_name: str,
    chat_hist: str,
    mode: str,
    loc: Dict,
) -> str:
    is_rp = (mode == 'roleplay')
    names = [b['name'] for b in bots]
    prompt = (
        "Generate a short party chat exchange between "
        f"{len(bots)} grouped bots reacting to something "
        "they just heard in General chat.\n"
    )
    prompt += (
        f"\nA bot named {source_bot['name']} just said "
        f"in General chat:\n\"{source_message}\"\n"
    )
    prompt += (
        f"\nThe first party line must mention "
        f"{source_bot['name']} by name. This is private "
        "party chat, not another General reply.\n"
    )
    if loc.get('dungeon_flavor'):
        prompt += f"Dungeon context: {loc['dungeon_flavor']}\n"
    elif loc.get('zone_flavor'):
        prompt += f"Zone context: {loc['zone_flavor']}\n"
    if loc.get('subzone_lore'):
        prompt += f"Subzone context: {loc['subzone_lore']}\n"

    prompt += "\nSpeakers:\n"
    for bot in bots:
        traits = ', '.join(
            t for t in [
                bot.get('trait1'),
                bot.get('trait2'),
                bot.get('trait3'),
            ] if t
        )
        line = (
            f"- {bot['name']}: level {bot['level']} "
            f"{bot['race']} {bot['class']}"
        )
        if traits:
            line += f"; traits: {traits}"
        if bot.get('travel_context'):
            line += f"; {bot['travel_context']}"
        prompt += line + "\n"

    if chat_hist:
        prompt += f"\n{chat_hist}\n"

    if is_rp:
        prompt += (
            "\nGuidelines: Stay in character for race "
            "and class; keep it grounded and brief.\n"
        )
    else:
        prompt += (
            "\nGuidelines: Sound like normal people "
            "chatting in a game; keep it brief.\n"
        )
    prompt += (
        f"- {names[0]} speaks first and mentions "
        f"{source_bot['name']} by name\n"
        "- Later speakers build on that party reaction\n"
        "- Each bot speaks exactly once\n"
        f"- {player_name} is listening in the party\n"
    )
    return append_conversation_json_instruction(
        prompt,
        names,
        len(bots),
        allow_action=is_rp,
    )


def _insert_statement(
    db,
    client,
    config: dict,
    event_id: int,
    group_id: int,
    bot: Dict,
    source_bot: Dict,
    source_message: str,
    player_name: str,
    chat_hist: str,
    mode: str,
    loc: Dict,
    first_delay: float,
) -> bool:
    prompt = _build_statement_prompt(
        bot, source_bot, source_message,
        player_name, chat_hist, mode, loc,
    )
    response = call_llm(
        client, prompt, config,
        context=(
            f"general-relay:#{event_id}:"
            f"{bot['name']}"
        ),
        label='group_general_relay',
    )
    if not response:
        return False
    parsed = parse_single_response(response)
    text = strip_speaker_prefix(
        parsed['message'], bot['name']
    )
    text = cleanup_message(
        text, action=parsed.get('action')
    )
    text = _clamp_message(
        _ensure_source_name(text, source_bot['name'])
    )
    if not text:
        return False

    insert_chat_message(
        db, bot['guid'], bot['name'], text,
        channel='party',
        delay_seconds=first_delay,
        event_id=event_id,
        sequence=0,
        emote=parsed.get('emote'),
        config=config,
        group_id=group_id,
        delivery_policy='bypass',
        delivery_reason=EVENT_TYPE,
    )
    _store_chat(
        db, group_id, bot['guid'],
        bot['name'], True, text,
    )
    return True


def _insert_conversation(
    db,
    client,
    config: dict,
    event_id: int,
    group_id: int,
    bots: List[Dict],
    source_bot: Dict,
    source_message: str,
    player_name: str,
    chat_hist: str,
    mode: str,
    loc: Dict,
    first_delay: float,
) -> bool:
    prompt = _build_conversation_prompt(
        bots, source_bot, source_message,
        player_name, chat_hist, mode, loc,
    )
    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200,
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=min(max_tokens * (1 + len(bots)), 1000),
        context=(
            f"general-relay-conv:#{event_id}:"
            f"{','.join(b['name'] for b in bots)}"
        ),
        label='group_general_relay_conv',
    )
    if not response:
        return False

    bot_names = [b['name'] for b in bots]
    bot_guids = {b['name']: b['guid'] for b in bots}
    messages = parse_conversation_response(response, bot_names)
    if not messages:
        return False

    strip_conversation_actions(
        messages, label='group_general_relay_conv',
    )
    cumulative_delay = first_delay
    prev_len = 0
    inserted = 0
    for seq, msg in enumerate(messages):
        name = msg['name']
        text = strip_speaker_prefix(
            msg['message'], name
        )
        text = cleanup_message(
            text, action=msg.get('action')
        )
        if seq == 0:
            text = _ensure_source_name(
                text, source_bot['name']
            )
        text = _clamp_message(text)
        if not text:
            continue

        if seq > 0:
            cumulative_delay += calculate_dynamic_delay(
                len(text), config,
                prev_message_length=prev_len,
                responsive=True,
            )
        prev_len = len(text)
        policy = 'bypass' if seq == 0 else 'responsive'
        speaker_guid = bot_guids.get(name)
        if not speaker_guid:
            continue
        insert_chat_message(
            db, speaker_guid, name, text,
            channel='party',
            delay_seconds=cumulative_delay,
            event_id=event_id,
            sequence=seq,
            emote=msg.get('emote'),
            config=config,
            group_id=group_id,
            delivery_policy=policy,
            delivery_reason=EVENT_TYPE,
        )
        _store_chat(
            db, group_id, speaker_guid,
            name, True, text,
        )
        inserted += 1
    return inserted > 0


def process_group_general_reaction_event(
    db,
    client,
    config: dict,
    event,
) -> bool:
    """Handle a party reaction to a General bot message."""
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        EVENT_TYPE,
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    group_id = int(extra.get('group_id') or 0)
    source_bot_guid = int(extra.get('source_bot_guid') or 0)
    source_bot_name = extra.get('source_bot_name') or ''
    source_message = extra.get('source_message') or ''
    player_name = extra.get('player_name') or 'the player'
    if (
        not group_id or not source_bot_guid
        or not source_bot_name or not source_message
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    bots = _fetch_group_bots(db, group_id, source_bot_guid)
    if not bots:
        _mark_event(db, event_id, 'skipped')
        return False
    random.shuffle(bots)

    source_bot = _fetch_source_bot_info(db, source_bot_guid)
    if not source_bot:
        source_bot = {'name': source_bot_name}
    source_bot['name'] = source_bot_name

    mode = get_chatter_mode(config)
    chat_hist = format_chat_history(
        _get_recent_chat(db, group_id)
    )
    loc = _location_context(db, group_id)
    first_delay = _first_delay(extra)

    use_conversation = False
    if len(bots) >= 2:
        chance = _int_config(
            config,
            'LLMChatter.GroupChatter.'
            'GeneralRelayConversationChance',
            75,
            maximum=100,
        )
        use_conversation = (
            chance > 0 and random.randint(1, 100) <= chance
        )

    try:
        if use_conversation:
            picked = bots[:random.randint(2, min(3, len(bots)))]
            ok = _insert_conversation(
                db, client, config, event_id,
                group_id, picked, source_bot,
                source_message, player_name,
                chat_hist, mode, loc, first_delay,
            )
            if ok:
                mark_event(db, event_id, 'completed')
                return True

        ok = _insert_statement(
            db, client, config, event_id,
            group_id, bots[0], source_bot,
            source_message, player_name,
            chat_hist, mode, loc, first_delay,
        )
        mark_event(
            db, event_id,
            'completed' if ok else 'skipped',
        )
        return ok
    except Exception:
        logger.error(
            "process_group_general_reaction_event "
            "failed event=%s",
            event_id,
            exc_info=True,
        )
        _mark_event(db, event_id, 'skipped')
        return False
