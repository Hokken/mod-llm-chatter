"""
Chatter General - General channel reactions.

When a real player types in General channel, nearby
bots react with statements or conversations, making
the world feel alive and interactive.

Zone-scoped: history per zone, cooldowns per zone,
bot selection by zone.
"""

import logging
import random

# Module-level config defaults (set by init_general_config)
_chat_history_limit = 10
_spice_count = 2

from chatter_shared import (
    call_llm, cleanup_message, strip_speaker_prefix,
    get_chatter_mode, get_class_name, get_race_name,
    build_race_class_context, parse_extra_data,
    calculate_dynamic_delay,
    find_addressed_bot,
    insert_chat_message,
    build_anti_repetition_context,
    get_recent_zone_messages,
    append_json_instruction,
    parse_single_response,
    get_action_chance,
)
from chatter_prompts import (
    pick_random_tone,
    pick_random_mood,
    maybe_get_creative_twist,
    get_time_of_day_context,
    pick_personality_spices,
)
from chatter_constants import (
    RACE_SPEECH_PROFILES,
    LENGTH_HINTS, RP_LENGTH_HINTS,
)

logger = logging.getLogger(__name__)


def init_general_config(config):
    """Initialize module-level config values."""
    global _chat_history_limit, _spice_count
    try:
        val = int(
            config.get('LLMChatter.ChatHistoryLimit', 10)
        )
    except (ValueError, TypeError):
        logger.warning(
            "Invalid LLMChatter.ChatHistoryLimit, "
            "using default 10"
        )
        val = 10
    _chat_history_limit = max(1, min(val, 50))
    try:
        _spice_count = int(config.get(
            'LLMChatter.PersonalitySpiceCount', 2
        ))
        _spice_count = max(0, min(_spice_count, 5))
    except Exception:
        _spice_count = 2


# Same personality traits as group chatter
PERSONALITY_TRAITS = {
    'social': [
        'friendly', 'reserved', 'talkative',
        'shy', 'thoughtful', 'polite',
    ],
    'attitude': [
        'optimistic', 'cynical', 'cautious',
        'easygoing', 'stoic',
    ],
    'focus': [
        'combat-focused', 'loot-driven',
        'explorer', 'quest-obsessed',
        'socializer',
    ],
    'humor': [
        'sarcastic', 'deadpan', 'cheerful',
        'dry wit', 'warmhearted',
    ],
    'energy': [
        'eager', 'laid-back', 'steady',
        'drowsy', 'relaxed',
    ],
}


def _pick_random_traits():
    """Pick 3 random traits for a bot."""
    categories = random.sample(
        list(PERSONALITY_TRAITS.keys()), 3
    )
    return [
        random.choice(PERSONALITY_TRAITS[cat])
        for cat in categories
    ]


def _pick_length_hint(mode):
    """Pick a random length hint."""
    is_rp = (mode == 'roleplay')
    pool = RP_LENGTH_HINTS if is_rp else LENGTH_HINTS
    hint = random.choice(pool)
    long_chance = 15 if is_rp else 12
    if random.randint(1, 100) <= long_chance:
        return (
            f"Length: {hint}\n"
            f"Length mode: long allowed (up to "
            f"~200 chars) if it feels natural"
        )
    return (
        f"Length: {hint}\n"
        f"Length mode: short/medium only "
        f"(avoid long messages)"
    )


def _mark_event(db, event_id, status):
    """Mark an event with given status."""
    cursor = db.cursor()
    if status == 'completed':
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = 'completed', "
            "processed_at = NOW() "
            "WHERE id = %s",
            (event_id,)
        )
    else:
        cursor.execute(
            "UPDATE llm_chatter_events "
            "SET status = %s WHERE id = %s",
            (status, event_id)
        )
    db.commit()


def _get_general_chat_history(
    db, zone_id, limit=None
):
    """Get recent General channel messages for a zone.
    Returns oldest-first for natural prompt reading.
    """
    if limit is None:
        limit = _chat_history_limit
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT speaker_name, is_bot, message
        FROM llm_general_chat_history
        WHERE zone_id = %s
        ORDER BY id DESC
        LIMIT %s
    """, (zone_id, limit))
    rows = cursor.fetchall()
    return list(reversed(rows))


def _format_general_history(history):
    """Format General chat history for prompts."""
    if not history:
        return ""
    lines = []
    for msg in history:
        name = msg['speaker_name']
        text = msg['message']
        if msg['is_bot']:
            lines.append(f"  {name}: {text}")
        else:
            lines.append(
                f"  {name} (player): {text}"
            )
    return (
        "\nRecent General channel chat:\n"
        + '\n'.join(lines)
    )


def _store_general_chat(
    db, zone_id, speaker_name, is_bot, message
):
    """Store a message in General chat history
    and prune old messages per zone.
    """
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO llm_general_chat_history
        (zone_id, speaker_name, is_bot, message)
        VALUES (%s, %s, %s, %s)
    """, (
        zone_id, speaker_name,
        1 if is_bot else 0, message[:500]
    ))
    db.commit()

    # Prune to keep recent messages per zone
    cursor.execute("""
        DELETE FROM llm_general_chat_history
        WHERE zone_id = %s AND id NOT IN (
            SELECT id FROM (
                SELECT id
                FROM llm_general_chat_history
                WHERE zone_id = %s
                ORDER BY id DESC
                LIMIT %s
            ) AS keep
        )
    """, (zone_id, zone_id, _chat_history_limit))
    db.commit()


def _get_bot_info(db, bot_guid):
    """Fetch bot class/race/level from characters."""
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    return cursor.fetchone()


def _build_general_response_prompt(
    bot_name, bot_race, bot_class, bot_level,
    traits, player_name, player_message,
    zone_name, chat_history, mode,
    recent_messages=None, allow_action=True
):
    """Build prompt for a bot responding to a
    player's General channel message.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot_race, bot_class
        )
        if ctx:
            rp_context = f"\n{ctx}"

        profile = RACE_SPEECH_PROFILES.get(bot_race)
        if profile:
            fw = profile.get('flavor_words', [])
            flavor = ', '.join(
                random.sample(fw, min(3, len(fw)))
            )
            if flavor:
                rp_context += (
                    f"\nRace flavor words you might "
                    f"use: {flavor}"
                )

    if is_rp:
        style = (
            "Reply in-character. Stay natural and "
            "grounded. Don't break character."
        )
    else:
        style = (
            "Reply naturally in General chat. "
            "Casual and conversational."
        )

    tod = get_time_of_day_context()

    prompt = (
        f"You are {bot_name}, a level "
        f"{bot_level} {bot_race} "
        f"{bot_class} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"

    # 40% chance to address the player by name
    address_hint = ""
    if random.random() < 0.4:
        address_hint = (
            f"- You may address {player_name} by "
            f"name in your reply\n"
        )

    prompt += (
        f"You are in {zone_name}."
    )
    if tod:
        prompt += f" {tod}"
    prompt += (
        f"{rp_context}\n"
        f"{chat_history}\n\n"
        f"{player_name} just said in General "
        f"channel:\n"
        f"\"{player_message}\"\n\n"
        f"{style}\n\n"
        f"Reply in General channel.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Respond to what {player_name} said\n"
        f"{address_hint}"
        f"- Reflect your personality traits\n"
        f"- Don't repeat what they said\n"
        f"- If there's chat history, stay "
        f"consistent with the conversation\n"
        f"- Keep it brief - this is General chat, "
        f"not a private conversation\n"
        f"- Keep your response proportional to "
        f"what was said. Simple statements or "
        f"questions only need brief replies"
    )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    anti_rep = build_anti_repetition_context(
        recent_messages
    )
    if anti_rep:
        prompt += f"\n{anti_rep}"
    prompt = append_json_instruction(
        prompt, allow_action, skip_emote=True
    )
    return prompt


def _build_general_followup_prompt(
    bot_name, bot_race, bot_class, bot_level,
    traits, first_bot_name, first_bot_response,
    player_name, player_message,
    zone_name, chat_history, mode,
    recent_messages=None, allow_action=True
):
    """Build prompt for a 2nd bot following up
    on the 1st bot's reaction in General channel.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot_race, bot_class
        )
        if ctx:
            rp_context = f"\n{ctx}"

        profile = RACE_SPEECH_PROFILES.get(bot_race)
        if profile:
            fw = profile.get('flavor_words', [])
            flavor = ', '.join(
                random.sample(fw, min(3, len(fw)))
            )
            if flavor:
                rp_context += (
                    f"\nRace flavor words you might "
                    f"use: {flavor}"
                )

    if is_rp:
        style = (
            "Reply in-character. Stay natural and "
            "grounded."
        )
    else:
        style = (
            "Reply naturally in General chat."
        )

    # 40% chance to address someone by name
    address_hint = ""
    if random.random() < 0.4:
        target = random.choice(
            [player_name, first_bot_name]
        )
        address_hint = (
            f"- You may address {target} by "
            f"name in your reply\n"
        )

    prompt = (
        f"You are {bot_name}, a level "
        f"{bot_level} {bot_race} "
        f"{bot_class} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
        f"You are in {zone_name}."
        f"{rp_context}\n"
        f"{chat_history}\n\n"
        f"{player_name} said in General channel:\n"
        f"\"{player_message}\"\n\n"
        f"Then {first_bot_name} responded:\n"
        f"\"{first_bot_response}\"\n\n"
        f"{style}\n"
        f"Add to the conversation - react to "
        f"{first_bot_name}'s response or add your "
        f"own take on what {player_name} said.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Don't repeat what others said\n"
        f"{address_hint}"
        f"- Keep it brief - General channel\n"
        f"- Reflect your personality traits"
    )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    anti_rep = build_anti_repetition_context(
        recent_messages
    )
    if anti_rep:
        prompt += f"\n{anti_rep}"
    prompt = append_json_instruction(
        prompt, allow_action, skip_emote=True
    )
    return prompt


def process_general_player_msg_event(
    event, db, client, config
):
    """Handle a player_general_msg event.

    A real player said something in General channel.
    Pick 1-2 bots from the zone to respond.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'player_general_msg'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    player_name = extra_data.get(
        'player_name', 'someone'
    )
    player_message = extra_data.get(
        'player_message', ''
    )
    zone_id = int(extra_data.get('zone_id', 0))
    zone_name = extra_data.get(
        'zone_name', 'Unknown'
    )
    bot_guids = extra_data.get('bot_guids', [])
    bot_names = extra_data.get('bot_names', [])

    if not zone_id or not player_message:
        _mark_event(db, event_id, 'skipped')
        return False

    if not bot_guids:
        logger.info(
            f"General msg #{event_id}: no bots "
            f"available in zone {zone_name}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    logger.warning(
        f"Processing General channel reaction: "
        f"{player_name} said \"{player_message}\" "
        f"in {zone_name} "
        f"({len(bot_guids)} bot candidates)"
    )

    # Mark as processing
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = 'processing' WHERE id = %s",
        (event_id,)
    )
    db.commit()

    try:
        mode = get_chatter_mode(config)

        # Fetch recent messages for anti-repetition
        recent_msgs = get_recent_zone_messages(
            db, zone_id
        )

        # Fetch chat history for this zone
        history = _get_general_chat_history(
            db, zone_id
        )
        chat_hist = _format_general_history(history)

        # Decide: conversation vs single statement
        conv_chance = int(config.get(
            'LLMChatter.GeneralChat.'
            'ConversationChance', 30
        ))
        is_conversation = (
            len(bot_guids) >= 2
            and random.randint(1, 100) <= conv_chance
        )

        # Pick bot: prefer addressed bot, else random
        addressed = find_addressed_bot(
            player_message, bot_names,
            client=client, config=config,
            chat_history=chat_hist
        )
        bot1_idx = None
        if addressed:
            for i, name in enumerate(bot_names):
                if name == addressed:
                    bot1_idx = i
                    break
            if bot1_idx is not None:
                logger.info(
                    f"General msg: player addressed "
                    f"{addressed}, selecting them"
                )
        if bot1_idx is None:
            bot1_idx = random.randint(
                0, len(bot_guids) - 1
            )
        bot1_guid = int(bot_guids[bot1_idx])
        bot1_info = _get_bot_info(db, bot1_guid)

        if not bot1_info:
            logger.info(
                f"General msg #{event_id}: bot "
                f"guid {bot1_guid} not in DB"
            )
            _mark_event(db, event_id, 'skipped')
            return False

        bot1_name = bot1_info['name']
        bot1_race = get_race_name(bot1_info['race'])
        bot1_class = get_class_name(
            bot1_info['class']
        )
        bot1_level = bot1_info['level']
        bot1_traits = _pick_random_traits()

        # Build and send first bot prompt
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt1 = _build_general_response_prompt(
            bot1_name, bot1_race, bot1_class,
            bot1_level, bot1_traits,
            player_name, player_message,
            zone_name, chat_hist, mode,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        response1 = call_llm(
            client, prompt1, config,
            max_tokens_override=max_tokens,
            context=(
                f"gen-msg:#{event_id}"
                f":{bot1_name}"
            )
        )

        if not response1:
            logger.warning(
                f"General msg #{event_id}: "
                f"LLM returned no response"
            )
            _mark_event(db, event_id, 'skipped')
            return False

        parsed1 = parse_single_response(response1)
        msg1 = strip_speaker_prefix(
            parsed1['message'], bot1_name
        )
        msg1 = cleanup_message(
            msg1, action=parsed1.get('action')
        )
        if not msg1:
            logger.warning(
                "Empty message after cleanup"
            )
            _mark_event(db, event_id, 'skipped')
            return False
        if len(msg1) > 255:
            msg1 = msg1[:252] + "..."

        logger.warning(
            f"General response from {bot1_name}: "
            f"{msg1}"
        )

        # Queue first bot's message
        delay1 = calculate_dynamic_delay(
            len(msg1), config
        )
        # General channel: skip emotes
        # (proximity-based, not visible
        #  to zone-wide recipients)
        insert_chat_message(
            db, bot1_guid, bot1_name, msg1,
            channel='general',
            delay_seconds=delay1,
            event_id=event_id,
            sequence=0,
        )

        # Store in General chat history
        _store_general_chat(
            db, zone_id, bot1_name, True, msg1
        )

        # Conversation mode: second bot follows up
        if is_conversation:
            try:
                _general_followup(
                    db, client, config,
                    event_id, zone_id, zone_name,
                    bot_guids, bot1_idx, bot1_guid,
                    bot1_name, msg1,
                    player_name, player_message,
                    mode, delay1,
                    recent_msgs=recent_msgs,
                )
            except Exception as e2:
                logger.warning(
                    f"General followup failed: {e2}"
                )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing general msg event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def _general_followup(
    db, client, config,
    event_id, zone_id, zone_name,
    bot_guids, bot1_idx, bot1_guid,
    bot1_name, bot1_response,
    player_name, player_message,
    mode, delay1,
    recent_msgs=None,
):
    """Generate a second bot's followup response
    in General channel conversation mode.
    """
    # Pick a different bot
    other_guids = [
        int(g) for i, g in enumerate(bot_guids)
        if i != bot1_idx
    ]
    if not other_guids:
        return

    bot2_guid = random.choice(other_guids)
    bot2_info = _get_bot_info(db, bot2_guid)
    if not bot2_info:
        return

    bot2_name = bot2_info['name']
    bot2_race = get_race_name(bot2_info['race'])
    bot2_class = get_class_name(bot2_info['class'])
    bot2_level = bot2_info['level']
    bot2_traits = _pick_random_traits()

    # Get updated history (includes first response)
    history = _get_general_chat_history(db, zone_id)
    chat_hist = _format_general_history(history)

    allow_action = (
        random.random() < get_action_chance()
    )
    prompt2 = _build_general_followup_prompt(
        bot2_name, bot2_race, bot2_class,
        bot2_level, bot2_traits,
        bot1_name, bot1_response,
        player_name, player_message,
        zone_name, chat_hist, mode,
        recent_messages=recent_msgs,
        allow_action=allow_action,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response2 = call_llm(
        client, prompt2, config,
        max_tokens_override=max_tokens,
        context=f"gen-followup:{bot2_name}"
    )
    if not response2:
        logger.warning(
            f"General followup ({bot2_name}): "
            f"LLM returned no response"
        )
        return

    parsed2 = parse_single_response(response2)
    msg2 = strip_speaker_prefix(
        parsed2['message'], bot2_name
    )
    msg2 = cleanup_message(
        msg2, action=parsed2.get('action')
    )
    if not msg2:
        return
    if len(msg2) > 255:
        msg2 = msg2[:252] + "..."

    logger.warning(
        f"General followup from {bot2_name}: "
        f"{msg2}"
    )

    # Stagger: first bot delay + extra 4-8 seconds
    delay2 = delay1 + random.randint(4, 8)

    # General channel: skip emotes
    insert_chat_message(
        db, bot2_guid, bot2_name, msg2,
        channel='general',
        delay_seconds=delay2,
        event_id=event_id,
        sequence=1,
    )

    # Store in General chat history
    _store_general_chat(
        db, zone_id, bot2_name, True, msg2
    )
