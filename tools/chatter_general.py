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
import time

# Module-level config defaults (set by init_general_config)
_chat_history_limit = 10
_spice_count = 2
_extended_conv_chance = 40
_extended_max_messages = 3

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
    _zone_delivery_delay,
    _zone_last_delivery,
    get_zone_flavor,
    get_subzone_name,
    get_subzone_lore,
    build_zone_metadata,
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
from chatter_links import resolve_and_format_links
from chatter_shared import build_talent_context
from chatter_db import get_character_info_by_name

logger = logging.getLogger(__name__)


def init_general_config(config):
    """Initialize module-level config values."""
    global _chat_history_limit, _spice_count
    try:
        raw = config.get(
            'LLMChatter.GeneralChat.HistoryLimit',
            config.get(
                'LLMChatter.ChatHistoryLimit', 10
            )
        )
        val = int(raw)
    except (ValueError, TypeError):
        val = 10
    _chat_history_limit = max(1, min(val, 50))
    try:
        _spice_count = int(config.get(
            'LLMChatter.PersonalitySpiceCount', 2
        ))
        _spice_count = max(0, min(_spice_count, 5))
    except Exception:
        _spice_count = 2

    global _extended_conv_chance, _extended_max_messages
    try:
        _extended_conv_chance = int(config.get(
            'LLMChatter.GeneralChat.'
            'ExtendedConversationChance', 40
        ))
        _extended_conv_chance = max(
            0, min(_extended_conv_chance, 100)
        )
    except (ValueError, TypeError):
        _extended_conv_chance = 40
    try:
        _extended_max_messages = int(config.get(
            'LLMChatter.GeneralChat.'
            'ExtendedMaxMessages', 3
        ))
        _extended_max_messages = max(
            3, min(_extended_max_messages, 8)
        )
    except (ValueError, TypeError):
        _extended_max_messages = 3


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
    recent_messages=None, allow_action=True,
    link_context="",
    speaker_talent_context=None,
    target_talent_context=None,
    zone_flavor="",
    subzone_name="",
    subzone_lore="",
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
            "Reply as a regular WoW player in "
            "General chat — could be any age, "
            "mature and grounded. Talk about the "
            "game naturally, as a player not a "
            "character. Reference zones, classes, "
            "abilities, and creatures by name."
        )

    tod = get_time_of_day_context()

    prompt = (
        f"You are {bot_name}, a level "
        f"{bot_level} {bot_race} "
        f"{bot_class} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if target_talent_context:
        prompt += f"{target_talent_context}\n"
    prompt += (
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
    if is_rp and zone_flavor:
        prompt += f"\nZone context: {zone_flavor}"
    if is_rp and subzone_lore:
        prompt += (
            f"\nCurrent subzone: {subzone_lore}"
        )
    elif subzone_name:
        prompt += f"\nSubzone: {subzone_name}"
    prompt += (
        f"{rp_context}\n"
        f"{chat_history}\n\n"
    )
    if link_context:
        prompt += f"{link_context}\n\n"
    prompt += (
        f"{player_name} just said in General "
        f"channel:\n"
        f"\"{player_message}\"\n\n"
        f"{style}\n\n"
        f"Reply in General channel.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Prefer full words over internet slang — "
        f"use abbreviations sparingly, not in every "
        f"message (lol, omg, ngl are ok occasionally). "
        f"Basic WoW terms always fine (dps, tank, "
        f"healer, gg, buff, nerf)\n"
        f"- NEVER use brackets [] around creature, "
        f"NPC, zone, or faction names - write them "
        f"as plain text\n"
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
    recent_messages=None, allow_action=True,
    link_context="",
    speaker_talent_context=None,
    target_talent_context=None,
    zone_flavor="",
    subzone_name="",
    subzone_lore="",
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
            "Reply as a regular WoW player in "
            "General chat — could be any age, "
            "mature and grounded. Talk about the "
            "game naturally, as a player not a "
            "character. Reference zones, classes, "
            "abilities, and creatures by name."
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
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if target_talent_context:
        prompt += f"{target_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
        f"You are in {zone_name}."
    )
    if is_rp and zone_flavor:
        prompt += f"\nZone context: {zone_flavor}"
    if is_rp and subzone_lore:
        prompt += (
            f"\nCurrent subzone: {subzone_lore}"
        )
    elif subzone_name:
        prompt += f"\nSubzone: {subzone_name}"
    prompt += (
        f"{rp_context}\n"
        f"{chat_history}\n\n"
    )
    if link_context:
        prompt += f"{link_context}\n\n"
    prompt += (
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
        f"- Prefer full words over internet slang — "
        f"use abbreviations sparingly, not in every "
        f"message (lol, omg, ngl are ok occasionally). "
        f"Basic WoW terms always fine (dps, tank, "
        f"healer, gg, buff, nerf)\n"
        f"- NEVER use brackets [] around creature, "
        f"NPC, zone, or faction names - write them "
        f"as plain text\n"
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

    # Zone/subzone context for prompts and logging
    zone_flavor = get_zone_flavor(zone_id) or ''
    area_id = int(
        extra_data.get('area_id', zone_id)
    )
    subzone_name = (
        get_subzone_name(zone_id, area_id) or ''
    )
    subzone_lore = (
        get_subzone_lore(zone_id, area_id) or ''
    )
    zone_meta = build_zone_metadata(
        zone_name=(
            zone_name
            if zone_name != 'Unknown' else ''
        ),
        zone_flavor=zone_flavor,
        subzone_name=subzone_name,
        subzone_lore=subzone_lore,
    )

    if not zone_id or not player_message:
        _mark_event(db, event_id, 'skipped')
        return False

    # Parse and resolve WoW links in message
    link_context = ""
    player_message, link_context = (
        resolve_and_format_links(
            config, player_message
        )
    )

    if not bot_guids:
        _mark_event(db, event_id, 'skipped')
        return False


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
        addr_result = find_addressed_bot(
            player_message, bot_names,
            client=client, config=config,
            chat_history=chat_hist
        )
        addressed = addr_result.get('bot')
        # multi_addressed ignored for general channel
        # (has its own multi-bot conversation logic)
        bot1_idx = None
        if addressed:
            for i, name in enumerate(bot_names):
                if name == addressed:
                    bot1_idx = i
                    break
        if bot1_idx is None:
            bot1_idx = random.randint(
                0, len(bot_guids) - 1
            )
        bot1_guid = int(bot_guids[bot1_idx])
        bot1_info = _get_bot_info(db, bot1_guid)

        if not bot1_info:
            _mark_event(db, event_id, 'skipped')
            return False

        bot1_name = bot1_info['name']
        bot1_race = get_race_name(bot1_info['race'])
        bot1_class = get_class_name(
            bot1_info['class']
        )
        bot1_level = bot1_info['level']
        bot1_traits = _pick_random_traits()

        # Talent context injection
        speaker_talent = None
        target_talent = None
        talent_chance = int(config.get(
            'LLMChatter.TalentInjectionChance',
            '40',
        ))
        if (
            talent_chance > 0
            and random.randint(1, 100)
            <= talent_chance
        ):
            speaker_talent = build_talent_context(
                db, bot1_guid,
                bot1_info['class'],
                bot1_name,
                perspective='speaker',
            )
        if (
            talent_chance > 0
            and random.randint(1, 100)
            <= talent_chance
        ):
            pinfo = get_character_info_by_name(
                db, player_name,
            )
            if pinfo:
                target_talent = (
                    build_talent_context(
                        db, pinfo['guid'],
                        pinfo['class'],
                        player_name,
                        perspective='target',
                    )
                )

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
            link_context=link_context,
            speaker_talent_context=speaker_talent,
            target_talent_context=target_talent,
            zone_flavor=zone_flavor,
            subzone_name=subzone_name,
            subzone_lore=subzone_lore,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        if speaker_talent:
            zone_meta['speaker_talent'] = (
                speaker_talent
            )
        if target_talent:
            zone_meta['target_talent'] = (
                target_talent
            )
        response1 = call_llm(
            client, prompt1, config,
            max_tokens_override=max_tokens,
            context=(
                f"gen-msg:#{event_id}"
                f":{bot1_name}"
            ),
            label='general_player_msg',
            metadata=zone_meta,
        )

        if not response1:
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
            _mark_event(db, event_id, 'skipped')
            return False
        if len(msg1) > 255:
            msg1 = msg1[:252] + "..."


        # Queue first bot's message — responsive
        # since player is waiting for a reply.
        # Also enforce zone gap so player reactions
        # don't stack with ambient messages.
        zone_gap = _zone_delivery_delay(
            zone_id, config
        )
        delay1 = calculate_dynamic_delay(
            len(msg1), config, responsive=True,
        ) + zone_gap
        conv_label = "conv" if is_conversation else "stmt"
        logger.info(
            "[GEN-FLOW] player-react %s | "
            "bot=%s delay=%.1fs seq=0",
            conv_label, bot1_name, delay1,
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
                followup = _general_followup(
                    db, client, config,
                    event_id, zone_id, zone_name,
                    bot_guids, bot1_idx, bot1_guid,
                    bot1_name, msg1,
                    player_name, player_message,
                    mode, delay1,
                    recent_msgs=recent_msgs,
                    link_context=link_context,
                    speaker_talent_context=(
                        speaker_talent
                    ),
                    target_talent_context=(
                        target_talent
                    ),
                    zone_flavor=zone_flavor,
                    subzone_name=subzone_name,
                    subzone_lore=subzone_lore,
                    zone_meta=zone_meta,
                )
                # Extended conversation chance
                if (
                    followup
                    and _extended_conv_chance > 0
                    and random.randint(1, 100)
                    <= _extended_conv_chance
                ):
                    try:
                        _general_extended_conversation(
                            db, client, config,
                            event_id, zone_id,
                            zone_name,
                            bot_guids,
                            bot1_guid, bot1_name,
                            bot1_traits,
                            msg1,
                            followup['bot2_guid'],
                            followup['bot2_name'],
                            followup['bot2_traits'],
                            followup['bot2_response'],
                            player_name,
                            player_message,
                            mode,
                            followup['delay2'],
                            recent_msgs=recent_msgs,
                            link_context=link_context,
                            speaker_talent_context=(
                                speaker_talent
                            ),
                            target_talent_context=(
                                target_talent
                            ),
                            zone_flavor=zone_flavor,
                            subzone_name=subzone_name,
                            subzone_lore=subzone_lore,
                            zone_meta=zone_meta,
                        )
                    except Exception as e3:
                        logger.error(
                            "[GEN] extended conv "
                            "failed event=%s: %s",
                            event_id, e3,
                            exc_info=True
                        )
            except Exception as e2:
                logger.error(
                    "[GEN] followup failed "
                    "event=%s: %s",
                    event_id, e2,
                    exc_info=True
                )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
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
    link_context="",
    speaker_talent_context=None,
    target_talent_context=None,
    zone_flavor="",
    subzone_name="",
    subzone_lore="",
    zone_meta=None,
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

    # Recompute speaker talent for bot2
    bot2_speaker_talent = None
    talent_chance = int(config.get(
        'LLMChatter.TalentInjectionChance',
        '40',
    ))
    if (
        talent_chance > 0
        and random.randint(1, 100)
        <= talent_chance
    ):
        bot2_speaker_talent = build_talent_context(
            db, bot2_guid,
            bot2_info['class'],
            bot2_name,
            perspective='speaker',
        )

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
        link_context=link_context,
        speaker_talent_context=(
            bot2_speaker_talent
        ),
        target_talent_context=(
            target_talent_context
        ),
        zone_flavor=zone_flavor,
        subzone_name=subzone_name,
        subzone_lore=subzone_lore,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    if zone_meta is None:
        zone_meta = {}
    if bot2_speaker_talent:
        zone_meta['speaker_talent'] = (
            bot2_speaker_talent
        )
    if target_talent_context:
        zone_meta['target_talent'] = (
            target_talent_context
        )
    response2 = call_llm(
        client, prompt2, config,
        max_tokens_override=max_tokens,
        context=f"gen-followup:{bot2_name}",
        label='general_followup',
        metadata=zone_meta,
    )
    if not response2:
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


    # Stagger: first bot delay + responsive gap
    delay2 = delay1 + random.randint(2, 5)

    logger.info(
        "[GEN-FLOW] player-react followup | "
        "bot=%s delay=%.1fs seq=1 (gap=%.1fs)",
        bot2_name, delay2, delay2 - delay1,
    )
    # General channel: skip emotes
    insert_chat_message(
        db, bot2_guid, bot2_name, msg2,
        channel='general',
        delay_seconds=delay2,
        event_id=event_id,
        sequence=1,
    )

    # Push zone timestamp past bot2's delivery so
    # the gap enforced from the END of the exchange.
    _zone_last_delivery[zone_id] = (
        time.monotonic() + delay2
    )

    # Store in General chat history
    _store_general_chat(
        db, zone_id, bot2_name, True, msg2
    )

    return {
        'bot2_guid': bot2_guid,
        'bot2_name': bot2_name,
        'bot2_traits': bot2_traits,
        'bot2_response': msg2,
        'delay2': delay2,
    }


def _build_general_continuation_prompt(
    bot_name, bot_race, bot_class, bot_level,
    traits, conversation_thread,
    zone_name, chat_history, mode,
    recent_messages=None, allow_action=True,
    remaining_messages=3, link_context="",
    speaker_talent_context=None,
    target_talent_context=None,
    zone_flavor="",
    subzone_name="",
    subzone_lore="",
):
    """Build prompt for a continuation message in
    an extended General channel conversation.

    conversation_thread is a list of dicts:
      [{'name': str, 'message': str, 'is_bot': bool}]
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
            "Reply as a regular WoW player in "
            "General chat — could be any age, "
            "mature and grounded. Talk about the "
            "game naturally, as a player not a "
            "character. Reference zones, classes, "
            "abilities, and creatures by name."
        )

    # Format the conversation thread
    thread_lines = []
    for entry in conversation_thread:
        tag = "" if entry['is_bot'] else " (player)"
        thread_lines.append(
            f"  {entry['name']}{tag}: "
            f"{entry['message']}"
        )
    thread_text = "\n".join(thread_lines)

    # Pick someone to maybe address by name
    other_names = list(set(
        e['name'] for e in conversation_thread
        if e['name'] != bot_name
    ))
    address_hint = ""
    if other_names and random.random() < 0.4:
        target = random.choice(other_names)
        address_hint = (
            f"- You may address {target} by "
            f"name in your reply\n"
        )

    prompt = (
        f"You are {bot_name}, a level "
        f"{bot_level} {bot_race} "
        f"{bot_class} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if target_talent_context:
        prompt += f"{target_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
        f"You are in {zone_name}."
    )
    if is_rp and zone_flavor:
        prompt += f"\nZone context: {zone_flavor}"
    if is_rp and subzone_lore:
        prompt += (
            f"\nCurrent subzone: {subzone_lore}"
        )
    elif subzone_name:
        prompt += f"\nSubzone: {subzone_name}"
    prompt += (
        f"{rp_context}\n"
        f"{chat_history}\n\n"
    )
    if link_context:
        prompt += f"{link_context}\n\n"
    prompt += (
        f"A conversation is happening in "
        f"General channel:\n"
        f"{thread_text}\n\n"
        f"{style}\n"
        f"Continue the conversation naturally. "
        f"React to what was just said or add "
        f"your own perspective.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Prefer full words over internet slang — "
        f"use abbreviations sparingly, not in every "
        f"message (lol, omg, ngl are ok occasionally). "
        f"Basic WoW terms always fine (dps, tank, "
        f"healer, gg, buff, nerf)\n"
        f"- NEVER use brackets [] around creature, "
        f"NPC, zone, or faction names - write them "
        f"as plain text\n"
        f"- Don't repeat what others said\n"
        f"{address_hint}"
        f"- Keep it brief - General channel\n"
        f"- Reflect your personality traits"
    )
    if remaining_messages <= 2:
        prompt += (
            f"\n- The conversation should feel "
            f"like it's winding down naturally"
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


def _general_extended_conversation(
    db, client, config,
    event_id, zone_id, zone_name,
    bot_guids,
    bot1_guid, bot1_name, bot1_traits,
    bot1_response,
    bot2_guid, bot2_name, bot2_traits,
    bot2_response,
    player_name, player_message,
    mode, last_delay,
    recent_msgs=None,
    link_context="",
    speaker_talent_context=None,
    target_talent_context=None,
    zone_flavor="",
    subzone_name="",
    subzone_lore="",
    zone_meta=None,
):
    """Generate additional messages beyond the
    initial 2-message conversation in General
    channel. Bots alternate with diminishing
    continuation chance.
    """
    # Diminishing chances per additional message
    continuation_chances = [70, 50, 30]

    # Build conversation thread so far
    thread = [
        {
            'name': player_name,
            'message': player_message,
            'is_bot': False,
        },
        {
            'name': bot1_name,
            'message': bot1_response,
            'is_bot': True,
        },
        {
            'name': bot2_name,
            'message': bot2_response,
            'is_bot': True,
        },
    ]

    # Participating bots: bot1 and bot2 always,
    # optionally a 3rd joins
    participants = [
        {
            'guid': bot1_guid,
            'name': bot1_name,
            'traits': bot1_traits,
        },
        {
            'guid': bot2_guid,
            'name': bot2_name,
            'traits': bot2_traits,
        },
    ]

    # Maybe add a 3rd bot (50% chance if available)
    other_guids = [
        int(g) for i, g in enumerate(bot_guids)
        if int(g) not in (bot1_guid, bot2_guid)
    ]
    if other_guids and random.random() < 0.5:
        bot3_guid = random.choice(other_guids)
        bot3_info = _get_bot_info(db, bot3_guid)
        if bot3_info:
            participants.append({
                'guid': bot3_guid,
                'name': bot3_info['name'],
                'traits': _pick_random_traits(),
            })

    # Track who spoke last to avoid repeats
    last_speaker_guid = bot2_guid
    # Messages sent so far (bot1 + bot2 = 2)
    msg_count = 2
    current_delay = last_delay
    max_msgs = _extended_max_messages

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))

    # cont_turn tracks how many continuation
    # RNG rolls we've made (0-indexed).
    # First continuation (turn 0) is guaranteed.
    cont_turn = 0

    while msg_count < max_msgs:
        # First extra message is guaranteed;
        # subsequent ones use diminishing chance
        if cont_turn > 0:
            chance_idx = min(
                cont_turn - 1,
                len(continuation_chances) - 1,
            )
            roll = random.randint(1, 100)
            if roll > continuation_chances[chance_idx]:
                break

        # Pick next speaker (not the last one)
        eligible = [
            p for p in participants
            if p['guid'] != last_speaker_guid
        ]
        if not eligible:
            break
        speaker = random.choice(eligible)

        # Fetch bot info for prompt
        sp_info = _get_bot_info(
            db, speaker['guid']
        )
        if not sp_info:
            participants = [
                p for p in participants
                if p['guid'] != speaker['guid']
            ]
            # Don't consume a turn — retry
            continue

        sp_race = get_race_name(sp_info['race'])
        sp_class = get_class_name(sp_info['class'])
        sp_level = sp_info['level']

        # Recompute speaker talent for this bot
        sp_speaker_talent = None
        talent_chance = int(config.get(
            'LLMChatter.TalentInjectionChance',
            '40',
        ))
        if (
            talent_chance > 0
            and random.randint(1, 100)
            <= talent_chance
        ):
            sp_speaker_talent = (
                build_talent_context(
                    db, speaker['guid'],
                    sp_info['class'],
                    speaker['name'],
                    perspective='speaker',
                )
            )

        # Get updated history
        history = _get_general_chat_history(
            db, zone_id
        )
        chat_hist = _format_general_history(history)

        allow_action = (
            random.random() < get_action_chance()
        )
        # remaining after this message is sent
        remaining = max_msgs - (msg_count + 1)
        prompt = _build_general_continuation_prompt(
            speaker['name'], sp_race, sp_class,
            sp_level, speaker['traits'],
            thread, zone_name, chat_hist, mode,
            recent_messages=recent_msgs,
            allow_action=allow_action,
            remaining_messages=remaining,
            link_context=link_context,
            speaker_talent_context=(
                sp_speaker_talent
            ),
            target_talent_context=(
                target_talent_context
            ),
            zone_flavor=zone_flavor,
            subzone_name=subzone_name,
            subzone_lore=subzone_lore,
        )

        if zone_meta is None:
            zone_meta = {}
        if sp_speaker_talent:
            zone_meta['speaker_talent'] = (
                sp_speaker_talent
            )
        else:
            zone_meta.pop(
                'speaker_talent', None
            )
        if target_talent_context:
            zone_meta['target_talent'] = (
                target_talent_context
            )
        response = call_llm(
            client, prompt, config,
            max_tokens_override=max_tokens,
            context=(
                f"gen-extended:{speaker['name']}"
            ),
            label='general_conv',
            metadata=zone_meta,
        )
        if not response:
            break

        parsed = parse_single_response(response)
        msg = strip_speaker_prefix(
            parsed['message'], speaker['name']
        )
        msg = cleanup_message(
            msg, action=parsed.get('action')
        )
        if not msg:
            break
        if len(msg) > 255:
            msg = msg[:252] + "..."

        msg_count += 1
        prev_delay = current_delay
        current_delay += random.randint(2, 5)

        logger.info(
            "[GEN-FLOW] extended conv | "
            "bot=%s delay=%.1fs seq=%d "
            "(gap=%.1fs)",
            speaker['name'], current_delay,
            msg_count - 1,
            current_delay - prev_delay,
        )
        insert_chat_message(
            db, speaker['guid'],
            speaker['name'], msg,
            channel='general',
            delay_seconds=current_delay,
            event_id=event_id,
            sequence=msg_count - 1,
        )

        _store_general_chat(
            db, zone_id,
            speaker['name'], True, msg
        )

        # Update thread and last speaker
        thread.append({
            'name': speaker['name'],
            'message': msg,
            'is_bot': True,
        })
        last_speaker_guid = speaker['guid']
        cont_turn += 1

