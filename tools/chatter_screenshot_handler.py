"""Bridge handler for screenshot vision observations.

Stage 2: receives structured vision description from the host-side
screenshot agent, wraps it in bot personality and zone context, and
generates a natural in-character party chat comment.

Supports both single-bot statements and multi-bot conversations
using the same RNG-gated pattern as nearby object events.
"""

import random

from chatter_db import (
    fail_event,
    get_group_location,
    insert_chat_message,
)
from chatter_group_state import (
    _get_recent_chat,
    format_chat_history,
    get_group_members,
    _mark_event,
    _store_chat,
)
from chatter_llm import call_llm
from chatter_shared import (
    append_conversation_json_instruction,
    build_anti_repetition_context,
    build_bot_identity,
    calculate_dynamic_delay,
    get_class_name,
    get_dungeon_flavor,
    get_race_name,
    get_subzone_lore,
    get_subzone_name,
    get_zone_flavor,
    get_zone_name,
    parse_conversation_response,
    parse_extra_data,
    run_single_reaction,
    append_json_instruction,
    should_include_action,
)
from chatter_prompts import get_time_of_day_context
from chatter_text import cleanup_message, strip_speaker_prefix

# Varied reaction styles to avoid samey comments
_REACTION_STYLES = [
    "Ask a question about what you see.",
    "Express a feeling the scene gives you.",
    "Compare it to somewhere else you've been.",
    "Point out one small detail others might miss.",
    "Wonder aloud about something in the scene.",
    "Say whether this place feels safe or dangerous.",
    "React with awe, unease, or curiosity.",
    "Make a practical observation about the terrain.",
    "Comment on the mood or atmosphere.",
    "Notice something beautiful or unsettling.",
]


def handle_screenshot_observation(db, client, config, event):
    """Generate a bot comment from a vision-analyzed
    screenshot. May trigger a multi-bot conversation."""
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_screenshot_observation',
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid      = int(extra.get('bot_guid') or 0)
    bot_name      = extra.get('bot_name', 'Bot')
    group_id      = int(extra.get('group_id') or 0)
    weather       = extra.get('weather', 'none')
    time_of_day   = extra.get('time_of_day', 'unknown')
    atmosphere    = extra.get('atmosphere', '')
    environment   = extra.get('environment', '')
    creatures     = extra.get('creatures', '')

    # -- Resolve zone, subzone, flavor --
    zone_name = 'the area'
    subzone_name = ''
    zone_flavor = ''
    map_id = event.get('map_id') or 0
    if group_id:
        zone_id, area_id, _ = get_group_location(
            db, group_id)
        if zone_id:
            resolved = get_zone_name(zone_id)
            if resolved:
                zone_name = resolved
            zone_flavor = get_zone_flavor(zone_id) or ''
            sz_name = get_subzone_name(zone_id, area_id)
            if sz_name:
                subzone_name = sz_name
            sz_lore = get_subzone_lore(zone_id, area_id)
            if sz_lore:
                zone_flavor = sz_lore
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        zone_flavor = dungeon_flav

    # -- Build observation --
    observation_parts = []
    if environment:
        observation_parts.append(environment)
    if creatures:
        observation_parts.append(creatures)
    if atmosphere and not environment:
        observation_parts.append(atmosphere)

    if not observation_parts:
        _mark_event(db, event_id, 'skipped')
        return False

    observation = '. '.join(observation_parts)

    # -- Location context --
    if subzone_name:
        location_str = f"{zone_name} — {subzone_name}"
    else:
        location_str = zone_name
    _, time_desc = get_time_of_day_context()
    context_parts = [f"Location: {location_str}"]
    if weather and weather != 'none':
        context_parts.append(f"Weather: {weather}")
    context_parts.append(f"Time of day: {time_desc}")
    context_str = ', '.join(context_parts)

    # -- Recent chat + anti-repetition --
    history = _get_recent_chat(db, group_id)
    chat_block = format_chat_history(history)
    recent_bot_msgs = [
        m['message'] for m in history
        if m.get('is_bot')
    ]
    anti_rep = build_anti_repetition_context(
        recent_bot_msgs)

    # -- Decide: conversation or single statement? --
    members = get_group_members(db, group_id)
    conv_chance = int(config.get(
        'LLMChatter.Screenshot.ConversationChance',
        30,
    ))
    do_conversation = (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    )

    if do_conversation:
        try:
            return _screenshot_conversation(
                db, client, config, event_id,
                group_id, bot_guid, bot_name,
                members, observation, context_str,
                zone_flavor, chat_block, anti_rep,
            )
        except Exception:
            fail_event(
                db, event_id,
                'bot_group_screenshot_observation',
                'conversation handler error',
            )
            return False

    return _screenshot_single(
        db, client, config, event_id,
        group_id, bot_guid, bot_name,
        observation, context_str, zone_flavor,
        chat_block, anti_rep,
    )


def _build_location_block(
    bot_name, context_str, zone_flavor,
):
    """Build the location/flavor header for prompts."""
    block = (
        f"You are {bot_name}, travelling through "
        f"{context_str} with your group.\n")
    if zone_flavor:
        block += f"About this place: {zone_flavor}\n"
    return block


def _get_bot_identity(db, bot_guid, bot_name):
    """Fetch race/class for a bot and build identity."""
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return build_bot_identity(
            bot_name,
            get_race_name(row['race']),
            get_class_name(row['class']),
        )
    return f"You are {bot_name}."


def _screenshot_single(
    db, client, config, event_id,
    group_id, bot_guid, bot_name,
    observation, context_str, zone_flavor,
    chat_block, anti_rep,
):
    """Single-bot statement about the screenshot."""
    style = random.choice(_REACTION_STYLES)
    identity = _get_bot_identity(db, bot_guid, bot_name)

    # Fetch personality traits
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT trait1, trait2, trait3
        FROM llm_group_bot_traits
        WHERE group_id = %s AND bot_name = %s
    """, (group_id, bot_name))
    traits_row = cursor.fetchone()
    cursor.close()
    traits = ''
    if traits_row:
        t = [traits_row[k] for k in
             ('trait1', 'trait2', 'trait3') if traits_row[k]]
        if t:
            traits = f"Your personality: {', '.join(t)}\n"

    location_block = _build_location_block(
        bot_name, context_str, zone_flavor)

    prompt = (
        f"{identity} {traits}"
        f"Travelling through {context_str} "
        f"with your group.\n"
        + (f"About this place: {zone_flavor}\n"
           if zone_flavor else '')
        + f"\nYou look around and notice:\n"
        f"{observation}\n\n"
        f"Style: {style}\n"
        "One or two sentences, 80-150 characters.\n\n"
        "DO NOT:\n"
        "- Narrate or describe actions "
        "(no *looks around*)\n"
        "- Mention any people, players, or "
        "humanoid NPCs\n"
        "- Recite lore or history unless it comes "
        "naturally\n"
        "- Comment on UI, health bars, or game "
        "mechanics\n"
        "You are physically in the scene — convey "
        "what stands out to you as if you were really "
        "there. You can connect what you see to what "
        "you know about this place. "
        "Speak naturally and briefly.\n"
    )
    if chat_block:
        prompt += chat_block + '\n'
    if anti_rep:
        prompt += anti_rep + '\n'
    prompt = append_json_instruction(
        prompt, allow_action=False)

    result = run_single_reaction(
        db, client, config,
        prompt=prompt,
        speaker_name=bot_name,
        bot_guid=bot_guid,
        channel='party',
        delay_seconds=2,
        event_id=event_id,
        allow_emote_fallback=False,
        context=(
            f"screenshot:#{event_id}:{bot_name}"
        ),
        label='screenshot_vision',
        max_tokens_override=120,
    )
    if not result['ok']:
        _mark_event(db, event_id, 'skipped')
        return False

    _store_chat(
        db, group_id, bot_guid,
        bot_name, True, result['message'],
    )
    _mark_event(db, event_id, 'completed')
    return True


def _screenshot_conversation(
    db, client, config, event_id,
    group_id, bot_guid, bot_name,
    members, observation, context_str,
    zone_flavor, chat_block, anti_rep,
):
    """Multi-bot conversation about the screenshot.
    Follows the same pattern as nearby object
    conversations."""

    # Pick 2-3 random bots, ensure triggering bot
    # is included
    num_pick = random.randint(2, min(len(members), 3))
    other_names = [m for m in members if m != bot_name]
    random.shuffle(other_names)
    picked = [bot_name] + other_names[:num_pick - 1]
    random.shuffle(picked)

    # Gather traits and character info
    bots = []
    bot_guids = {}
    traits_map = {}
    for name in picked:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT bot_guid, trait1, trait2, trait3
            FROM llm_group_bot_traits
            WHERE group_id = %s AND bot_name = %s
        """, (group_id, name))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            continue
        guid = int(row['bot_guid'])
        bot_guids[name] = guid
        traits_map[name] = [
            row['trait1'], row['trait2'], row['trait3'],
        ]
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT class, race, level
            FROM characters WHERE guid = %s
        """, (guid,))
        char = cursor.fetchone()
        cursor.close()
        if not char:
            continue
        bots.append({
            'name': name,
            'class': get_class_name(char['class']),
            'race': get_race_name(char['race']),
            'level': char['level'],
        })

    if len(bots) < 2:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_names = [b['name'] for b in bots]

    # Build bot identity descriptions
    bot_lines = []
    for b in bots:
        traits = traits_map.get(b['name'], [])
        trait_str = ', '.join(
            t for t in traits if t) or 'adventurous'
        bot_lines.append(
            f"- {b['name']}: {b['race']} {b['class']}, "
            f"personality: {trait_str}")
    bot_block = '\n'.join(bot_lines)

    # Build conversation prompt
    location_block = _build_location_block(
        bot_names[0], context_str, zone_flavor)

    prompt = (
        f"The following party members are travelling "
        f"through {context_str}:\n{bot_block}\n\n"
    )
    if zone_flavor:
        prompt += f"About this place: {zone_flavor}\n\n"
    prompt += (
        f"They look around and notice:\n"
        f"{observation}\n\n"
        "Write a short conversation (2-4 lines) where "
        "the party members react to what they see. "
        "Each character should respond differently "
        "based on their personality and background.\n\n"
        "Rules:\n"
        "- Each line: 40-80 characters\n"
        "- No narrator actions (no *looks around*)\n"
        "- No mentions of people, players, or "
        "humanoid NPCs\n"
        "- Focus on the world: terrain, sky, "
        "buildings, wildlife\n"
        "- Each bot speaks once, naturally\n"
    )
    if chat_block:
        prompt += chat_block + '\n'
    if anti_rep:
        prompt += anti_rep + '\n'

    num_bots = len(bots)

    # JSON format for conversation
    prompt = append_conversation_json_instruction(
        prompt, bot_names, num_bots,
        allow_action=False,
    )

    max_tokens = min(80 * num_bots, 400)

    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"screenshot-conv:{','.join(bot_names)}",
        label='screenshot_vision',
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    messages = parse_conversation_response(
        response, bot_names)
    if not messages:
        _mark_event(db, event_id, 'skipped')
        return False

    # Deliver with staggered delays
    cumulative_delay = 2.0
    prev_len = 0
    for seq, msg in enumerate(messages):
        text = strip_speaker_prefix(
            msg['message'], msg['name'])
        text = cleanup_message(text, action=None)
        if not text:
            continue
        if len(text) > 255:
            text = text[:252] + "..."

        speaker_guid = bot_guids.get(msg['name'])
        if not speaker_guid:
            continue

        if seq > 0:
            delay = calculate_dynamic_delay(
                len(text), config,
                prev_message_length=prev_len,
            )
            cumulative_delay += delay

        insert_chat_message(
            db,
            bot_guid=speaker_guid,
            bot_name=msg['name'],
            message=text,
            channel='party',
            delay_seconds=cumulative_delay,
            event_id=event_id,
        )
        _store_chat(
            db, group_id, speaker_guid,
            msg['name'], True, text,
        )
        prev_len = len(text)

    _mark_event(db, event_id, 'completed')
    return True
