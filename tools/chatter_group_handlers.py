"""Group reaction handlers extracted from chatter_group (N6 batch 1)."""

import logging
import random
import re

from chatter_shared import (
    parse_extra_data,
    get_class_name,
    get_race_name,
    get_chatter_mode,
    query_quest_turnin_npc,
    get_dungeon_flavor,
    get_dungeon_bosses,
    format_item_link,
    get_action_chance,
    run_single_reaction,
)
from chatter_group_state import (
    _has_recent_event,
    _mark_event,
    _store_chat,
    _get_recent_chat,
    format_chat_history,
    get_group_members,
    get_bot_traits,
    get_other_group_bot,
    get_bot_mood_label,
    update_bot_mood,
)
from chatter_group_prompts import (
    build_kill_reaction_prompt,
    build_loot_reaction_prompt,
    build_combat_reaction_prompt,
    build_death_reaction_prompt,
    build_levelup_reaction_prompt,
    build_quest_complete_reaction_prompt,
    build_quest_objectives_reaction_prompt,
    build_achievement_reaction_prompt,
    build_spell_cast_reaction_prompt,
)

logger = logging.getLogger(__name__)

def process_group_kill_event(
    db, client, config, event
):
    """Handle a bot_group_kill event.

    The killing bot reacts to a boss/rare kill
    in party chat.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_kill'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get('bot_name', 'Unknown')
    creature_name = extra_data.get(
        'creature_name', 'something'
    )
    is_boss = bool(int(
        extra_data.get('is_boss', 0)
    ))
    is_rare = bool(int(
        extra_data.get('is_rare', 0)
    ))
    group_id = int(extra_data.get('group_id', 0))

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Get bot traits (must have joined group first)
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Kill event #{event_id}: no traits "
            f"for {bot_name}, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    # Get bot class/race from extra_data
    bot_class_id = int(
        extra_data.get('bot_class', 0)
    )
    bot_race_id = int(
        extra_data.get('bot_race', 0)
    )
    bot_level = int(
        extra_data.get('bot_level', 1)
    )
    bot_class = get_class_name(bot_class_id)
    bot_race = get_race_name(bot_race_id)

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': bot_class,
        'race': bot_race,
        'level': bot_level,
    }

    logger.info(
        f"Processing group kill reaction: "
        f"{bot_name} killed {creature_name} "
        f"(boss={is_boss}, rare={is_rare})"
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_kill_reaction_prompt(
            bot, traits, creature_name,
            is_boss, is_rare, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            allow_action=allow_action,
        )
        mood_label = get_bot_mood_label(
            group_id, bot_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot_guid,
            channel='party',
            delay_seconds=3,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-kill:#{event_id}:{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group kill #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Kill reaction from {bot_name}: "
            f"{message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        update_bot_mood(
            group_id, bot_guid,
            'boss_kill' if is_boss else 'kill'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing kill event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_loot_event(
    db, client, config, event
):
    """Handle a bot_group_loot event.

    The looting bot reacts to picking up an item
    in party chat. Excitement scales with quality.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_loot'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    # C++ pre-selects the reactor (bot_guid/name)
    # and provides the actual looter separately.
    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    looter_name = extra_data.get(
        'looter_name',
        extra_data.get('bot_name', 'Unknown')
    )
    item_name = extra_data.get(
        'item_name', 'something'
    )
    item_quality = int(
        extra_data.get('item_quality', 2)
    )
    group_id = int(extra_data.get('group_id', 0))

    if not reactor_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    trait_data = get_bot_traits(
        db, group_id, reactor_guid
    )
    if not trait_data:
        logger.info(
            f"Loot event #{event_id}: no traits "
            f"for {reactor_name}, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    bot_class_id = int(
        extra_data.get('bot_class', 0)
    )
    bot_race_id = int(
        extra_data.get('bot_race', 0)
    )
    bot_level = int(
        extra_data.get('bot_level', 1)
    )
    bot = {
        'guid': reactor_guid,
        'name': reactor_name,
        'class': get_class_name(bot_class_id),
        'race': get_race_name(bot_race_id),
        'level': bot_level,
    }
    # If reactor != looter, pass looter_name
    # so the prompt says "X looted Y" not "you"
    is_self_loot = (reactor_name == looter_name)
    prompt_looter_name = (
        None if is_self_loot else looter_name
    )

    logger.info(
        f"Processing group loot reaction: "
        f"{looter_name} looted {item_name} "
        f"(quality={item_quality}, "
        f"reactor={bot['name']})"
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_loot_reaction_prompt(
            bot, traits, item_name,
            item_quality, mode,
            chat_history=chat_hist,
            looter_name=prompt_looter_name,
            extra_data=extra_data,
            allow_action=allow_action,
        )
        mood_label = get_bot_mood_label(
            group_id, bot['guid']
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

        item_entry = int(
            extra_data.get('item_entry', 0)
        )
        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))

        def _loot_message_transform(raw_message):
            """Inject clickable item link into the
            first matching item-name occurrence."""
            message = raw_message
            if item_entry and item_name:
                link = format_item_link(
                    item_entry, item_quality, item_name
                )
                message = re.sub(
                    re.escape(item_name), link,
                    message, count=1, flags=re.IGNORECASE
                )
            return message

        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot['name'],
            bot_guid=bot['guid'],
            channel='party',
            delay_seconds=3,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-loot:#{event_id}"
                f":{bot['name']}"
            ),
            message_transform=_loot_message_transform,
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group loot #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Loot reaction from {bot['name']}: "
            f"{message}"
        )

        _store_chat(
            db, group_id, bot['guid'],
            bot['name'], True, message
        )

        update_bot_mood(
            group_id, bot['guid'],
            'epic_loot'
            if 4 <= item_quality < 200
            else 'loot'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing loot event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_combat_event(
    db, client, config, event
):
    """Handle a bot_group_combat event.

    A bot shouts a short battle cry when engaging
    an elite or boss creature.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_combat'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get('bot_name', 'Unknown')
    creature_name = extra_data.get(
        'creature_name', 'something'
    )
    is_boss = bool(int(
        extra_data.get('is_boss', 0)
    ))
    is_elite = bool(int(
        extra_data.get('is_elite', 0)
    ))
    group_id = int(extra_data.get('group_id', 0))

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Dedup: skip if recent combat event
    if _has_recent_event(
        db, 'bot_group_combat', bot_guid,
        seconds=60, exclude_id=event_id
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    # Get bot traits
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Combat event #{event_id}: no traits "
            f"for {bot_name}, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    bot_class_id = int(
        extra_data.get('bot_class', 0)
    )
    bot_race_id = int(
        extra_data.get('bot_race', 0)
    )
    bot_level = int(
        extra_data.get('bot_level', 1)
    )

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(bot_class_id),
        'race': get_race_name(bot_race_id),
        'level': bot_level,
    }

    logger.info(
        f"Processing combat reaction: "
        f"{bot_name} engaging {creature_name} "
        f"(boss={is_boss})"
    )

    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = 'processing' WHERE id = %s",
        (event_id,)
    )
    db.commit()

    try:
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_combat_reaction_prompt(
            bot, traits, creature_name,
            is_boss, mode,
            chat_history=chat_hist,
            is_elite=is_elite,
            extra_data=extra_data,
            allow_action=allow_action,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot['guid'],
            channel='party',
            delay_seconds=1,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=min(
                max_tokens, 60
            ),
            context=(
                f"grp-combat:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group combat #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty combat msg after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Combat cry from {bot_name}: "
            f"{message}"
        )

        _store_chat(
            db, group_id, bot['guid'],
            bot['name'], True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing combat event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_death_event(
    db, client, config, event
):
    """Handle a bot_group_death event.

    A DIFFERENT bot from the dead one reacts in
    party chat. If no other bot has traits, skip.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_death'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    # C++ now pre-selects the reactor and includes
    # their info in extra_data (bot_guid/bot_name =
    # reactor, dead_name/dead_guid = dead player)
    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'someone'
    )
    dead_name = extra_data.get(
        'dead_name',
        extra_data.get('bot_name', 'someone')
    )
    dead_guid = int(
        extra_data.get('dead_guid', 0)
    )
    killer_name = extra_data.get('killer_name', '')
    group_id = int(extra_data.get('group_id', 0))
    is_player_death = extra_data.get(
        'is_player_death', False
    )

    if not reactor_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Get reactor traits from traits table
    trait_data = get_bot_traits(
        db, group_id, reactor_guid
    )
    if not trait_data:
        # Fallback: try get_other_group_bot (legacy)
        reactor_data = get_other_group_bot(
            db, group_id, dead_guid or reactor_guid
        )
        if not reactor_data:
            logger.info(
                f"Death event #{event_id}: no "
                f"traits for reactor {reactor_name}"
            )
            _mark_event(db, event_id, 'skipped')
            return False
        reactor_guid = reactor_data['guid']
        reactor_name = reactor_data['name']
        reactor_traits = reactor_data['traits']
        # Need class/race from characters table
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT class, race, level
            FROM characters WHERE guid = %s
        """, (reactor_guid,))
        char_row = cursor.fetchone()
        if not char_row:
            _mark_event(db, event_id, 'skipped')
            return False
        reactor = {
            'guid': reactor_guid,
            'name': reactor_name,
            'class': get_class_name(
                char_row['class']
            ),
            'race': get_race_name(
                char_row['race']
            ),
            'level': char_row['level'],
        }
    else:
        reactor_traits = trait_data['traits']
        # Use class/race from extra_data (C++)
        bot_class_id = int(
            extra_data.get('bot_class', 0)
        )
        bot_race_id = int(
            extra_data.get('bot_race', 0)
        )
        bot_level = int(
            extra_data.get('bot_level', 1)
        )
        reactor = {
            'guid': reactor_guid,
            'name': reactor_name,
            'class': get_class_name(bot_class_id),
            'race': get_race_name(bot_race_id),
            'level': bot_level,
        }

    logger.info(
        f"Processing group death reaction: "
        f"{reactor_name} reacts to {dead_name} "
        f"dying"
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_death_reaction_prompt(
            reactor, reactor_traits, dead_name,
            killer_name, mode,
            chat_history=chat_hist,
            is_player_death=is_player_death,
            extra_data=extra_data,
            allow_action=allow_action,
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=reactor_name,
            bot_guid=reactor_guid,
            channel='party',
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-death:#{event_id}"
                f":{reactor_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group death #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Death reaction from "
            f"{reactor_name}: {message}"
        )

        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'death'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing death event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_levelup_event(
    db, client, config, event
):
    """Handle a bot_group_levelup event.

    A DIFFERENT bot congratulates the one who
    leveled up. If no other bot exists in the
    group, the leveling bot itself reacts.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_levelup'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    leveler_guid = int(
        extra_data.get('bot_guid', 0)
    )
    leveler_name = extra_data.get(
        'leveler_name',
        extra_data.get('bot_name', 'someone')
    )
    new_level = int(
        extra_data.get('bot_level', 1)
    )
    is_bot = bool(int(
        extra_data.get('is_bot', 1)
    ))
    group_id = int(
        extra_data.get('group_id', 0)
    )

    if not leveler_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Pick a different bot to react
    reactor_data = get_other_group_bot(
        db, group_id, leveler_guid
    )
    if reactor_data:
        reactor_guid = reactor_data['guid']
        reactor_name = reactor_data['name']
        reactor_traits = reactor_data['traits']
    else:
        # No other bot — use the leveling bot
        trait_data = get_bot_traits(
            db, group_id, leveler_guid
        )
        if not trait_data:
            logger.info(
                f"Levelup event #{event_id}: "
                f"no traits for {leveler_name}"
            )
            _mark_event(db, event_id, 'skipped')
            return False
        reactor_guid = leveler_guid
        reactor_name = leveler_name
        reactor_traits = trait_data['traits']

    # Get reactor's class/race from characters
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (reactor_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        logger.info(
            f"Levelup event #{event_id}: "
            f"reactor {reactor_name} not found "
            f"in characters table"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    reactor = {
        'guid': reactor_guid,
        'name': reactor_name,
        'class': get_class_name(
            char_row['class']
        ),
        'race': get_race_name(
            char_row['race']
        ),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing group levelup reaction: "
        f"{reactor_name} reacts to "
        f"{leveler_name} reaching L{new_level}"
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_levelup_reaction_prompt(
            reactor, reactor_traits,
            leveler_name, new_level, is_bot,
            mode, chat_history=chat_hist,
            allow_action=allow_action,
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=reactor_name,
            bot_guid=reactor_guid,
            channel='party',
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-levelup:#{event_id}"
                f":{reactor_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group levelup #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Levelup reaction from "
            f"{reactor_name}: {message}"
        )

        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'levelup'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing levelup event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_quest_complete_event(
    db, client, config, event
):
    """Handle a bot_group_quest_complete event.

    A DIFFERENT bot reacts to the quest completion.
    If no other bot exists, the completing bot
    itself reacts.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_quest_complete'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    # C++ pre-selects the reactor (bot_guid/name)
    # and provides the completer separately.
    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    completer_name = extra_data.get(
        'completer_name',
        extra_data.get('bot_name', 'someone')
    )
    quest_name = extra_data.get(
        'quest_name', 'a quest'
    )
    group_id = int(
        extra_data.get('group_id', 0)
    )

    if not reactor_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    trait_data = get_bot_traits(
        db, group_id, reactor_guid
    )
    if not trait_data:
        logger.info(
            f"Quest complete event "
            f"#{event_id}: no traits for "
            f"{reactor_name}"
        )
        _mark_event(db, event_id, 'skipped')
        return False
    reactor_traits = trait_data['traits']

    bot_class_id = int(
        extra_data.get('bot_class', 0)
    )
    bot_race_id = int(
        extra_data.get('bot_race', 0)
    )
    bot_level = int(
        extra_data.get('bot_level', 1)
    )

    reactor = {
        'guid': reactor_guid,
        'name': reactor_name,
        'class': get_class_name(bot_class_id),
        'race': get_race_name(bot_race_id),
        'level': bot_level,
    }

    logger.info(
        f"Processing quest complete reaction: "
        f"{reactor_name} reacts to "
        f"{completer_name} finishing "
        f"\"{quest_name}\""
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        # Look up turn-in NPC name
        quest_id = int(
            extra_data.get('quest_id', 0)
        )
        turnin_npc = None
        if quest_id:
            turnin_npc = query_quest_turnin_npc(
                config, quest_id
            )
        allow_action = (
            random.random() < get_action_chance()
        )
        quest_details = extra_data.get(
            'quest_details', ''
        )
        quest_objectives = extra_data.get(
            'quest_objectives', ''
        )
        prompt = (
            build_quest_complete_reaction_prompt(
                reactor, reactor_traits,
                completer_name, quest_name,
                mode,
                chat_history=chat_hist,
                turnin_npc=turnin_npc,
                allow_action=allow_action,
                quest_details=quest_details,
                quest_objectives=quest_objectives,
            )
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=reactor_name,
            bot_guid=reactor_guid,
            channel='party',
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-quest:#{event_id}"
                f":{reactor_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group quest #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Quest complete reaction from "
            f"{reactor_name}: {message}"
        )

        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'quest'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing quest complete "
            f"event #{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_quest_objectives_event(
    db, client, config, event
):
    """Handle a bot_group_quest_objectives event.

    A DIFFERENT bot reacts to quest objectives
    being completed. If no other bot exists, the
    completing bot itself reacts. This fires
    BEFORE the quest turn-in.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_quest_objectives'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    completer_guid = int(
        extra_data.get('bot_guid', 0)
    )
    completer_name = extra_data.get(
        'completer_name',
        extra_data.get('bot_name', 'someone')
    )
    quest_name = extra_data.get(
        'quest_name', 'a quest'
    )
    group_id = int(
        extra_data.get('group_id', 0)
    )

    if not completer_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Dedup: skip if recent quest objectives
    # event for this bot within 60 seconds
    if _has_recent_event(
        db, 'bot_group_quest_objectives',
        completer_guid, 60,
        exclude_id=event_id
    ):
        logger.info(
            f"Quest objectives event "
            f"#{event_id}: dedup - recent "
            f"objectives reaction for "
            f"{completer_name}, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    # Pick a different bot to react
    reactor_data = get_other_group_bot(
        db, group_id, completer_guid
    )
    if reactor_data:
        reactor_guid = reactor_data['guid']
        reactor_name = reactor_data['name']
        reactor_traits = reactor_data['traits']
    else:
        # No other bot — use the completing bot
        trait_data = get_bot_traits(
            db, group_id, completer_guid
        )
        if not trait_data:
            logger.info(
                f"Quest objectives event "
                f"#{event_id}: no traits for "
                f"{completer_name}"
            )
            _mark_event(db, event_id, 'skipped')
            return False
        reactor_guid = completer_guid
        reactor_name = completer_name
        reactor_traits = trait_data['traits']

    # Get reactor's class/race from characters
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (reactor_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        logger.info(
            f"Quest objectives event "
            f"#{event_id}: reactor "
            f"{reactor_name} not found "
            f"in characters table"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    reactor = {
        'guid': reactor_guid,
        'name': reactor_name,
        'class': get_class_name(
            char_row['class']
        ),
        'race': get_race_name(
            char_row['race']
        ),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing quest objectives "
        f"reaction: {reactor_name} reacts to "
        f"objectives completed for "
        f"\"{quest_name}\""
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        allow_action = (
            random.random() < get_action_chance()
        )
        quest_details = extra_data.get(
            'quest_details', ''
        )
        quest_objectives = extra_data.get(
            'quest_objectives', ''
        )
        prompt = (
            build_quest_objectives_reaction_prompt(
                reactor, reactor_traits,
                quest_name, completer_name,
                mode,
                chat_history=chat_hist,
                allow_action=allow_action,
                quest_details=quest_details,
                quest_objectives=quest_objectives,
            )
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=reactor_name,
            bot_guid=reactor_guid,
            channel='party',
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-objectives:#{event_id}"
                f":{reactor_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group objectives #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Quest objectives reaction from "
            f"{reactor_name}: {message}"
        )

        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing quest objectives "
            f"event #{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_achievement_event(
    db, client, config, event
):
    """Handle a bot_group_achievement event.

    A DIFFERENT bot reacts to the achievement.
    Achievements are special — more excited than
    regular events. If no other bot exists, the
    achieving bot itself reacts.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_achievement'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    achiever_guid = int(
        extra_data.get('bot_guid', 0)
    )
    achiever_name = extra_data.get(
        'achiever_name',
        extra_data.get('bot_name', 'someone')
    )
    achievement_name = extra_data.get(
        'achievement_name', 'an achievement'
    )
    is_bot = bool(int(
        extra_data.get('is_bot', 1)
    ))
    group_id = int(
        extra_data.get('group_id', 0)
    )

    if not achiever_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Pick a different bot to react
    reactor_data = get_other_group_bot(
        db, group_id, achiever_guid
    )
    if reactor_data:
        reactor_guid = reactor_data['guid']
        reactor_name = reactor_data['name']
        reactor_traits = reactor_data['traits']
    else:
        # No other bot — use the achieving bot
        trait_data = get_bot_traits(
            db, group_id, achiever_guid
        )
        if not trait_data:
            logger.info(
                f"Achievement event #{event_id}: "
                f"no traits for {achiever_name}"
            )
            _mark_event(db, event_id, 'skipped')
            return False
        reactor_guid = achiever_guid
        reactor_name = achiever_name
        reactor_traits = trait_data['traits']

    # Get reactor's class/race from characters
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (reactor_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        logger.info(
            f"Achievement event #{event_id}: "
            f"reactor {reactor_name} not found "
            f"in characters table"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    reactor = {
        'guid': reactor_guid,
        'name': reactor_name,
        'class': get_class_name(
            char_row['class']
        ),
        'race': get_race_name(
            char_row['race']
        ),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing achievement reaction: "
        f"{reactor_name} reacts to "
        f"{achiever_name} earning "
        f"\"{achievement_name}\""
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_achievement_reaction_prompt(
            reactor, reactor_traits,
            achiever_name, achievement_name,
            is_bot, mode,
            chat_history=chat_hist,
            allow_action=allow_action,
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=reactor_name,
            bot_guid=reactor_guid,
            channel='party',
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-achieve:#{event_id}"
                f":{reactor_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group achievement #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Achievement reaction from "
            f"{reactor_name}: {message}"
        )

        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'achievement'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing achievement event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_spell_cast_event(
    db, client, config, event
):
    """Handle a bot_group_spell_cast event.

    A bot reacts to a notable spell cast (heal, cc,
    resurrect, shield) in party chat.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_spell_cast'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    bot_class_id = int(
        extra_data.get('bot_class', 0)
    )
    bot_race_id = int(
        extra_data.get('bot_race', 0)
    )
    bot_level = int(
        extra_data.get('bot_level', 1)
    )
    caster_name = extra_data.get(
        'caster_name', 'someone'
    )
    spell_name = extra_data.get(
        'spell_name', 'a spell'
    )
    spell_category = extra_data.get(
        'spell_category', 'heal'
    )
    target_name = extra_data.get(
        'target_name', 'someone'
    )
    group_id = int(extra_data.get('group_id', 0))

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Get bot traits (must have joined group first)
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Spell cast event #{event_id}: "
            f"no traits for {bot_name}, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    bot_class = get_class_name(bot_class_id)
    bot_race = get_race_name(bot_race_id)

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': bot_class,
        'race': bot_race,
        'level': bot_level,
    }

    logger.info(
        f"Processing spell cast reaction: "
        f"{bot_name} reacts to {caster_name} "
        f"casting {spell_name} "
        f"({spell_category}) on {target_name}"
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
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        members = get_group_members(db, group_id)

        # Get zone/map for dungeon boss context
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT zone, map
            FROM characters WHERE guid = %s
        """, (bot_guid,))
        loc_row = cursor.fetchone()
        map_id = (
            int(loc_row['map'])
            if loc_row else 0
        )

        # Get dungeon bosses if in a dungeon
        in_dungeon = (
            get_dungeon_flavor(map_id) is not None
        )
        dungeon_bosses = (
            get_dungeon_bosses(db, map_id)
            if in_dungeon else None
        )

        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_spell_cast_reaction_prompt(
            bot, traits, caster_name,
            spell_name, spell_category,
            target_name, mode,
            chat_history=chat_hist,
            members=members,
            dungeon_bosses=dungeon_bosses,
            extra_data=extra_data,
            allow_action=allow_action,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        delay = random.randint(2, 3)
        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot_guid,
            channel='party',
            delay_seconds=delay,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-spell:#{event_id}"
                f":{bot['name']}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group spell #{event_id}: "
                    f"LLM returned no response"
                )
            elif result['error_reason'] == 'empty_message':
                logger.warning(
                    "Empty message after cleanup"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Spell cast reaction from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        logger.info(
            f"Spell cast reaction delivered: "
            f"{bot_name} reacted to "
            f"{spell_category} ({spell_name})"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error processing spell cast event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False
