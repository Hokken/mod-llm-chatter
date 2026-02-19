"""
Chatter Group - Group chatter logic for bots
grouped with real players.

Handles:
- bot_group_join: personality traits + LLM greeting
- bot_group_kill: reactions to kills (boss/rare/normal)
- bot_group_death: reactions when groupmate dies
- bot_group_loot: reactions to looting items
- bot_group_player_msg: contextual response to player
- bot_group_combat: battle cry when engaging elites/bosses
- bot_group_levelup: congrats when someone levels up
- bot_group_quest_complete: reaction to quest completion
- bot_group_quest_objectives: reaction to quest objectives done
- bot_group_achievement: reaction to achievement earned
- bot_group_spell_cast: reaction to notable spells
- bot_group_resurrect: gratitude when rezzed
- bot_group_zone_transition: comment on new zone
- bot_group_quest_accept: reaction to quest acceptance
- bot_group_discovery: reaction to area discovery
- bot_group_dungeon_entry: reaction to dungeon/raid
- bot_group_wipe: reaction to total party wipe
- idle chatter: periodic casual party chat during lulls
  (2 to N bot conversations)

Imports from chatter_constants, chatter_shared,
and chatter_prompts.
"""

import logging
import random
import re
import threading
import time

# Module-level config defaults (set by init_group_config)
_chat_history_limit = 10
_spice_count = 2

from chatter_shared import (
    call_llm, cleanup_message, strip_speaker_prefix,
    get_chatter_mode, get_class_name, get_race_name,
    get_db_connection, build_race_class_context,
    parse_extra_data, get_zone_flavor,
    get_dungeon_flavor, get_dungeon_bosses,
    parse_conversation_response,
    calculate_dynamic_delay,
    format_item_link,
    find_addressed_bot,
    insert_chat_message,
    pick_emote_for_statement,
    detect_item_links,
    query_item_details,
    format_item_context,
    build_anti_repetition_context,
    get_recent_bot_messages,
    build_bot_state_context,
    query_quest_turnin_npc,
    append_json_instruction,
    parse_single_response,
    get_action_chance,
    run_single_reaction,
)
from chatter_prompts import (
    pick_random_tone,
    pick_random_mood,
    maybe_get_creative_twist,
    get_environmental_context,
    generate_conversation_mood_sequence,
    generate_conversation_length_sequence,
    pick_personality_spices,
)
from chatter_group_state import (
    set_group_chat_history_limit,
    update_bot_mood,
    get_bot_mood_label,
    cleanup_group_moods,
    assign_bot_traits,
    get_bot_traits,
    get_other_group_bot,
    _generate_farewell,
    _has_recent_event,
    _mark_event,
    _store_chat,
    _get_recent_chat,
    format_chat_history,
    get_group_members,
)
from chatter_group_handlers import (
    process_group_kill_event,
    process_group_loot_event,
    process_group_combat_event,
    process_group_death_event,
    process_group_levelup_event,
    process_group_quest_complete_event,
    process_group_quest_objectives_event,
    process_group_achievement_event,
    process_group_spell_cast_event,
)
from chatter_group_prompts import (
    set_prompt_spice_count,
    _pick_length_hint,
    build_bot_greeting_prompt,
    build_bot_welcome_prompt,
    build_kill_reaction_prompt,
    build_loot_reaction_prompt,
    build_combat_reaction_prompt,
    build_death_reaction_prompt,
    build_levelup_reaction_prompt,
    build_quest_complete_reaction_prompt,
    build_quest_objectives_reaction_prompt,
    build_achievement_reaction_prompt,
    build_spell_cast_reaction_prompt,
    build_player_response_prompt,
)
from chatter_constants import (
    RACE_SPEECH_PROFILES,
    EMOTE_LIST_STR,
    CLASS_ROLE_MAP,
)

logger = logging.getLogger(__name__)

# N3 compatibility note:
# keep this module as the stable import surface while
# split skeleton modules are introduced incrementally.


def init_group_config(config):
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
    # Keep moved prompt builders in sync.
    set_prompt_spice_count(_spice_count)
    # Keep shared group helper state in sync.
    set_group_chat_history_limit(_chat_history_limit)


# ============================================================
# PLAYERBOT COMMAND FILTER
# ============================================================
# Commands players type in party chat to control
# bots. If the entire message matches one of these
# (case-insensitive), skip LLM response.
# Source: mod-playerbots ChatCommandHandlerStrategy.cpp
#         and ChatTriggerContext.h
PLAYERBOT_COMMANDS = {
    # Short aliases
    'u', 'c', 'e', 's', 'b', 'r', 't', 'q',
    'll', 'ss', 'co', 'nc', 'de', 'ra', 'gb',
    'nt', 'qi',
    # Movement / position
    'follow', 'stay', 'flee', 'runaway', 'warning',
    'grind', 'go', 'home', 'disperse',
    'move from group',
    # Combat
    'attack', 'max dps', 'tank attack',
    'pet attack', 'do attack my target',
    # Inventory / items
    'use', 'items', 'inventory', 'inv',
    'equip', 'unequip', 'sell', 'buy',
    'open items', 'unlock items',
    'unlock traded item', 'loot all',
    'add all loot', 'destroy',
    # Quests
    'quests', 'accept', 'drop', 'reward',
    'share', 'rpg status', 'rpg do quest',
    'query item usage',
    # Spells / skills
    'cast', 'castnc', 'spell', 'spells',
    'trainer', 'talent', 'talents',
    'buff', 'glyphs', 'glyph equip',
    'remove glyph', 'pet', 'tame',
    # Trading / interaction
    'trade', 'nontrade', 'craft', 'flag',
    'mail', 'sendmail', 'bank', 'gbank',
    'talk', 'emote', 'enter vehicle',
    'leave vehicle',
    # Status / information
    'stats', 'reputation', 'rep', 'pvp stats',
    'dps', 'who', 'position', 'aura',
    'attackers', 'target', 'help', 'log', 'los',
    # Group / raid
    'ready', 'ready check', 'leave', 'invite',
    'summon', 'formation', 'stance',
    'give leader', 'wipe', 'roll',
    # Maintenance / config
    'repair', 'maintenance', 'release', 'revive',
    'autogear', 'equip upgrade', 'save mana',
    'reset botai', 'teleport', 'taxi',
    'outline', 'rti', 'range', 'wts', 'cs',
    'cdebug', 'debug', 'cheat', 'calc', 'drink',
    'honor', 'outdoors',
    # Guild
    'ginvite', 'guild promote', 'guild demote',
    'guild remove', 'guild leave', 'lfg',
    # Chat / loot
    'chat', 'loot',
}


def _is_playerbot_command(message: str) -> bool:
    """Check if a message is a playerbot command.
    Returns True if the full message (stripped,
    lowered) matches a known command, or if it
    starts with a known command followed by a space
    (e.g. 'cast Holy Light', 'summon Hokken').
    """
    msg = message.strip().lower()
    if not msg:
        return False

    # Exact match (e.g. "follow", "stay", "ss")
    if msg in PLAYERBOT_COMMANDS:
        return True

    # Command + argument (e.g. "cast Holy Light")
    first_word = msg.split()[0]
    if first_word in PLAYERBOT_COMMANDS:
        return True

    # Multi-word command + argument
    # (e.g. "max dps on" or "tank attack now")
    for cmd in PLAYERBOT_COMMANDS:
        if ' ' in cmd and msg.startswith(cmd):
            return True

    return False


# ============================================================
# DEDUPLICATION
# ============================================================


# ============================================================
# PROMPT BUILDERS
# ============================================================
def process_group_event(db, client, config, event):
    """Handle a bot_group_join event.

    1. Check for duplicate greeting (dedup)
    2. Parse event extra_data for bot info
    3. Assign personality traits
    4. Generate LLM greeting
    5. Insert message for party delivery
    6. Mark event completed
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_join'
    )

    if not extra_data:
        logger.warning(
            f"Group event #{event_id}: "
            f"no extra_data, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get('bot_name', 'Unknown')
    bot_class_id = int(
        extra_data.get('bot_class', 0)
    )
    bot_race_id = int(
        extra_data.get('bot_race', 0)
    )
    bot_level = int(
        extra_data.get('bot_level', 1)
    )
    group_id = int(extra_data.get('group_id', 0))
    player_name = extra_data.get('player_name', '')
    group_size = int(
        extra_data.get('group_size', 0)
    )

    if not bot_guid or not group_id:
        logger.warning(
            f"Group event #{event_id}: "
            f"missing bot_guid or group_id"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    # Dedup check: skip if ANOTHER recent greeting
    # exists (exclude current event to avoid self-match)
    if _has_recent_event(
        db, 'bot_group_join', bot_guid, 60,
        exclude_id=event_id
    ):
        logger.info(
            f"Group event #{event_id}: "
            f"dedup - recent greeting for "
            f"{bot_name}, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    # Convert numeric class/race to names
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
        f"Processing group greeting for "
        f"{bot_name} ({bot_race} {bot_class} "
        f"L{bot_level}) in group {group_id}"
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
        # 1. Assign traits (with role from C++)
        bot_role = extra_data.get('role')
        traits = assign_bot_traits(
            db, group_id, bot_guid, bot_name,
            role=bot_role
        )

        # 2. Build prompt with chat history
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        members = get_group_members(db, group_id)
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_bot_greeting_prompt(
            bot, traits, mode,
            chat_history=chat_hist,
            members=members,
            player_name=player_name,
            group_size=group_size,
            allow_action=allow_action,
        )

        # 3. Call LLM
        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        response = call_llm(
            client, prompt, config,
            max_tokens_override=max_tokens,
            context=f"grp-join:#{event_id}:{bot_name}"
        )

        if not response:
            logger.warning(
                f"Group event #{event_id}: "
                f"LLM returned no response"
            )
            _mark_event(db, event_id, 'skipped')
            return False

        # 4. Clean up response
        parsed = parse_single_response(response)
        message = strip_speaker_prefix(
            parsed['message'], bot_name
        )
        message = cleanup_message(
            message, action=parsed.get('action')
        )
        if not message:
            logger.warning("Empty message after cleanup")
            _mark_event(db, event_id, 'skipped')
            return False
        if len(message) > 255:
            message = message[:252] + "..."

        logger.info(
            f"Group greeting from {bot_name}: "
            f"{message}"
        )

        # 5. Insert message for delivery via party
        emote = (
            parsed.get('emote')
            or pick_emote_for_statement(message)
        )
        insert_chat_message(
            db, bot_guid, bot_name, message,
            channel='party', delay_seconds=2,
            event_id=event_id, emote=emote,
        )

        # 6. Store in chat history
        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        # 7. Have existing bot welcome the newcomer
        _welcome_from_existing_bot(
            db, client, config, group_id,
            bot_guid, bot_name,
            mode, event_id
        )

        # 7b. Maybe comment on group composition
        try:
            _maybe_comment_on_composition(
                db, client, config, group_id,
                bot, traits, mode, event_id,
                player_name=player_name,
            )
        except Exception as e:
            logger.warning(
                f"Composition comment failed: {e}"
            )

        # 8. Pre-generate farewell message
        try:
            _generate_farewell(
                db, client, config,
                bot_name, bot_race, bot_class,
                traits, mode, group_id, bot_guid,
            )
        except Exception as e:
            logger.warning(
                f"Farewell generation failed: {e}"
            )

        # 9. Mark event completed
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing group event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False










def process_group_player_msg_event(
    db, client, config, event
):
    """Handle a bot_group_player_msg event.

    A real player said something in party chat.
    Pick a random bot from the group to respond
    contextually.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_player_msg'
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
    group_id = int(extra_data.get('group_id', 0))

    if not group_id or not player_message:
        _mark_event(db, event_id, 'skipped')
        return False

    # Skip playerbot commands (follow, stay, etc.)
    if _is_playerbot_command(player_message):
        logger.info(
            f"Player msg #{event_id}: skipped "
            f"playerbot command: "
            f"{player_message[:40]}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    # Get all bots in group for name matching
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT bot_guid, bot_name,
               trait1, trait2, trait3
        FROM llm_group_bot_traits
        WHERE group_id = %s
    """, (group_id,))
    all_bots = cursor.fetchall()

    if not all_bots:
        logger.info(
            f"Player msg event #{event_id}: "
            f"no bots with traits in group "
            f"{group_id}, skipping"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    # Fetch chat history early for LLM bot matching
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)

    # Prefer addressed bot, else random
    bot_row = None
    all_names = [b['bot_name'] for b in all_bots]
    addressed = find_addressed_bot(
        player_message, all_names,
        client=client, config=config,
        chat_history=chat_hist
    )
    if addressed:
        for b in all_bots:
            if b['bot_name'] == addressed:
                bot_row = b
                logger.info(
                    f"Player msg: addressed "
                    f"{addressed}, selecting them"
                )
                break
    if not bot_row:
        bot_row = random.choice(all_bots)

    bot_guid = bot_row['bot_guid']
    bot_name = bot_row['bot_name']
    traits = [
        bot_row['trait1'],
        bot_row['trait2'],
        bot_row['trait3'],
    ]

    # Get bot class/race from characters table
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        logger.info(
            f"Player msg event #{event_id}: "
            f"bot {bot_name} not found in "
            f"characters table"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing player message response: "
        f"{bot_name} replying to {player_name}: "
        f"\"{player_message}\""
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
        # history/chat_hist fetched above for
        # bot selection — reuse here
        members = get_group_members(db, group_id)

        # Check for item links in player message
        item_context = ""
        linked_items = detect_item_links(
            player_message
        )
        if linked_items:
            items_info = []
            world_db = None
            try:
                world_db = get_db_connection(
                    config, 'acore_world'
                )
                for entry, name in linked_items:
                    details = query_item_details(
                        world_db, entry
                    )
                    if details:
                        items_info.append(details)
            except Exception as e:
                logger.warning(
                    f"Item link query failed: {e}"
                )
            finally:
                if world_db:
                    try:
                        world_db.close()
                    except Exception:
                        pass
            if items_info:
                item_context = format_item_context(
                    items_info, bot['class']
                )
                logger.info(
                    f"Item links detected: "
                    f"{item_context}"
                )

        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_player_response_prompt(
            bot, traits, player_name,
            player_message, mode,
            chat_history=chat_hist,
            members=members,
            item_context=item_context,
            allow_action=allow_action,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        response = call_llm(
            client, prompt, config,
            max_tokens_override=max_tokens,
            context=(
                f"grp-msg:#{event_id}"
                f":{bot_name}"
            )
        )

        if not response:
            logger.warning(
                f"Group player_msg #{event_id}: "
                f"LLM returned no response"
            )
            _mark_event(db, event_id, 'skipped')
            return False

        parsed = parse_single_response(response)
        message = strip_speaker_prefix(
            parsed['message'], bot_name
        )
        message = cleanup_message(
            message, action=parsed.get('action')
        )
        if not message:
            logger.warning("Empty message after cleanup")
            _mark_event(db, event_id, 'skipped')
            return False
        if len(message) > 255:
            message = message[:252] + "..."

        logger.info(
            f"Player response from {bot_name}: "
            f"{message}"
        )

        emote = (
            parsed.get('emote')
            or pick_emote_for_statement(message)
        )
        insert_chat_message(
            db, bot_guid, bot_name, message,
            channel='party', delay_seconds=3,
            event_id=event_id, emote=emote,
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        # 25% chance a second bot also chimes in
        if random.randint(1, 100) <= 25:
            try:
                _try_second_bot_response(
                    db, client, config, group_id,
                    bot_guid, player_name,
                    player_message, mode,
                    event_id,
                )
            except Exception as e2:
                logger.warning(
                    f"Second bot response "
                    f"failed: {e2}"
                )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing player msg event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False












def process_group_resurrect_event(
    db, client, config, event
):
    """Handle a bot_group_resurrect event.

    The resurrected bot itself reacts with gratitude
    or relief in party chat.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_resurrect'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'someone'
    )
    group_id = int(extra_data.get('group_id', 0))

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # The rezzed bot itself reacts
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Event #{event_id}: no traits for "
            f"bot {bot_name} in group {group_id}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    # Get class/race from characters table
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing group resurrect: "
        f"{bot_name} reacting to being rezzed"
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
        prompt = build_resurrect_reaction_prompt(
            bot, traits, mode,
            chat_history=chat_hist,
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
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-resurrect:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group resurrect #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Resurrect reaction from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        update_bot_mood(
            group_id, bot_guid, 'resurrect'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing resurrect event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_zone_transition_event(
    db, client, config, event
):
    """Handle a bot_group_zone_transition event.

    The bot that entered a new zone comments on
    the arrival in party chat.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_zone_transition'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'someone'
    )
    group_id = int(extra_data.get('group_id', 0))
    zone_id = int(extra_data.get('zone_id', 0))
    zone_name = extra_data.get(
        'zone_name', 'somewhere'
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # The bot that entered the zone reacts
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Event #{event_id}: no traits for "
            f"bot {bot_name} in group {group_id}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    # Get class/race from characters table
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing zone transition: "
        f"{bot_name} entering {zone_name}"
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
        prompt = build_zone_transition_prompt(
            bot, traits, zone_name, zone_id,
            mode,
            chat_history=chat_hist,
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
            bot_guid=bot_guid,
            channel='party',
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-zone:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group zone #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Zone transition reaction from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing zone transition "
            f"event #{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_quest_accept_event(
    db, client, config, event
):
    """Handle a bot_group_quest_accept event.

    A bot reacts to the group accepting a new quest.
    The C++ hook pre-selects the reactor bot.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_quest_accept'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    # C++ pre-selects the reactor (bot_guid/name)
    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    acceptor_name = extra_data.get(
        'acceptor_name',
        extra_data.get('bot_name', 'someone')
    )
    quest_name = extra_data.get(
        'quest_name', 'a quest'
    )
    quest_level = int(
        extra_data.get('quest_level', 0)
    )
    zone_name = extra_data.get(
        'zone_name', 'somewhere'
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
            f"Quest accept event "
            f"#{event_id}: no traits for "
            f"{reactor_name}"
        )
        _mark_event(db, event_id, 'skipped')
        return False
    reactor_traits = trait_data['traits']

    bot_class_id = int(extra_data.get(
        'bot_class', 1
    ))
    bot_race_id = int(extra_data.get(
        'bot_race', 1
    ))
    bot_class = get_class_name(bot_class_id)
    bot_race = get_race_name(bot_race_id)
    bot_level = int(
        extra_data.get('bot_level', 1)
    )

    reactor = {
        'guid': reactor_guid,
        'name': reactor_name,
        'class': bot_class,
        'race': bot_race,
        'level': bot_level,
    }

    logger.info(
        f"Processing quest accept reaction: "
        f"{reactor_name} reacts to "
        f"{acceptor_name} accepting "
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
            build_quest_accept_reaction_prompt(
                reactor, reactor_traits,
                acceptor_name, quest_name,
                quest_level,
                zone_name, mode,
                chat_history=chat_hist,
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
                f"grp-qacc:#{event_id}"
                f":{reactor_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group quest accept #{event_id}: "
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
            f"Quest accept reaction from "
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
            f"Error processing quest accept "
            f"event #{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_discovery_event(
    db, client, config, event
):
    """Handle a bot_group_discovery event.

    A bot reacts to the group discovering a new area.
    The C++ hook pre-selects the reactor bot.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_discovery'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'someone'
    )
    group_id = int(extra_data.get('group_id', 0))
    area_name = extra_data.get(
        'area_name', 'somewhere new'
    )
    xp_amount = int(
        extra_data.get('xp_amount', 0)
    )
    player_name = extra_data.get(
        'player_name', 'someone'
    )
    player_class = extra_data.get(
        'player_class', 'adventurer'
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Discovery event #{event_id}: "
            f"no traits for bot {bot_name} "
            f"in group {group_id}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    bot_class = extra_data.get(
        'bot_class', 'Warrior'
    )
    bot_race = extra_data.get(
        'bot_race', 'Human'
    )
    bot_level = int(
        extra_data.get('bot_level', 1)
    )

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': bot_class,
        'race': bot_race,
        'level': bot_level,
    }

    logger.info(
        f"Processing discovery reaction: "
        f"{bot_name} discovers {area_name}"
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
        prompt = build_discovery_reaction_prompt(
            bot, traits, area_name, player_name,
            player_class, xp_amount, mode,
            chat_history=chat_hist,
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
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-disc:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group discovery #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Discovery reaction from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing discovery "
            f"event #{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_dungeon_entry_event(
    db, client, config, event
):
    """Handle a bot_group_dungeon_entry event.

    The bot that entered a dungeon or raid instance
    reacts in party chat.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_dungeon_entry'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'someone'
    )
    group_id = int(extra_data.get('group_id', 0))
    map_id = int(extra_data.get('map_id', 0))
    map_name = extra_data.get(
        'map_name', 'a dungeon'
    )
    is_raid = bool(
        int(extra_data.get('is_raid', 0))
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # The bot that entered reacts
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Event #{event_id}: no traits for "
            f"bot {bot_name} in group {group_id}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    # Get class/race from characters table
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing dungeon entry: "
        f"{bot_name} entering {map_name}"
        f"{' (raid)' if is_raid else ''}"
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
        prompt = build_dungeon_entry_prompt(
            db, bot, traits, map_name, is_raid,
            map_id, mode,
            chat_history=chat_hist,
            allow_action=allow_action,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        delay = random.randint(2, 4)
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
                f"grp-dungeon:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group dungeon #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Dungeon entry reaction from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing dungeon entry "
            f"event #{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_wipe_event(
    db, client, config, event
):
    """Handle a bot_group_wipe event.

    The designated bot reacts to a total party wipe
    in party chat.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_wipe'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'someone'
    )
    group_id = int(extra_data.get('group_id', 0))
    killer_name = extra_data.get(
        'killer_name', ''
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # The designated bot reacts
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Event #{event_id}: no traits for "
            f"bot {bot_name} in group {group_id}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    # Get class/race from characters table
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing group wipe: "
        f"{bot_name} reacting"
        f"{' to ' + killer_name if killer_name else ''}"
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
        prompt = build_wipe_reaction_prompt(
            bot, traits, killer_name, mode,
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
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-wipe:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group wipe #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Wipe reaction from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        update_bot_mood(
            group_id, bot_guid, 'wipe'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing wipe event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_corpse_run_event(
    db, client, config, event
):
    """Handle a bot_group_corpse_run event.

    A bot comments on a corpse run — either
    their own or the real player's. Humorous,
    philosophical, or resigned depending on
    personality.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_corpse_run'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'someone'
    )
    group_id = int(extra_data.get('group_id', 0))
    zone_name = extra_data.get('zone_name', '')
    dead_name = extra_data.get(
        'dead_name', bot_name
    )
    is_player_death = extra_data.get(
        'is_player_death', False
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        logger.info(
            f"Event #{event_id}: no traits for "
            f"bot {bot_name} in group {group_id}"
        )
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    logger.info(
        f"Processing corpse run: "
        f"{dead_name} died"
        f"{' (player)' if is_player_death else ''}"
        f", {bot_name} reacting"
        f"{' in ' + zone_name if zone_name else ''}"
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
        prompt = build_corpse_run_reaction_prompt(
            bot, traits, zone_name, mode,
            chat_history=chat_hist,
            dead_name=dead_name,
            is_player_death=is_player_death,
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
            bot_guid=bot_guid,
            channel='party',
            delay_seconds=2,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=max_tokens,
            context=(
                f"grp-corpse:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group corpse #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Corpse run from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing corpse run event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


# ============================================================
# STATE-TRIGGERED CALLOUT PROCESSORS (Phase 2C)
# ============================================================
def process_group_low_health_event(
    db, client, config, event
):
    """Handle bot_group_low_health callout."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_low_health'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    group_id = int(extra_data.get('group_id', 0))
    target_name = extra_data.get(
        'target_name', ''
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    # Get class/race from characters
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()
    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

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
        prompt = build_low_health_callout_prompt(
            bot, traits, target_name, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            allow_action=allow_action,
        )

        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot_guid,
            channel='party',
            delay_seconds=1,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=60,
            context=(
                f"grp-lowHP:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group low_health #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Low health callout from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing low health event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_oom_event(
    db, client, config, event
):
    """Handle bot_group_oom callout."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_oom'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    group_id = int(extra_data.get('group_id', 0))
    target_name = extra_data.get(
        'target_name', ''
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()
    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

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
        prompt = build_oom_callout_prompt(
            bot, traits, target_name, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            allow_action=allow_action,
        )

        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot_guid,
            channel='party',
            delay_seconds=1,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=60,
            context=(
                f"grp-oom:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group oom #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"OOM callout from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing OOM event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_aggro_loss_event(
    db, client, config, event
):
    """Handle bot_group_aggro_loss callout."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_aggro_loss'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    group_id = int(extra_data.get('group_id', 0))
    target_name = extra_data.get(
        'target_name', ''
    )
    aggro_target = extra_data.get(
        'aggro_target', 'someone'
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()
    if not char_row:
        _mark_event(db, event_id, 'skipped')
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

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
        prompt = build_aggro_loss_callout_prompt(
            bot, traits, target_name,
            aggro_target, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            allow_action=allow_action,
        )

        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot_guid,
            channel='party',
            delay_seconds=1,
            event_id=event_id,
            allow_emote_fallback=True,
            max_tokens_override=60,
            context=(
                f"grp-aggro:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            if result['error_reason'] == 'no_response':
                logger.warning(
                    f"Group aggro_loss #{event_id}: "
                    f"LLM returned no response"
                )
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        logger.info(
            f"Aggro loss callout from "
            f"{bot_name}: {message}"
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            f"Error processing aggro loss event "
            f"#{event_id}: {e}"
        )
        _mark_event(db, event_id, 'skipped')
        return False


def _try_second_bot_response(
    db, client, config, group_id,
    first_bot_guid, player_name,
    player_message, mode, event_id
):
    """Maybe generate a second bot response to a
    player message, for more natural group feel.
    Uses a different bot with a 5s stagger.
    """
    second = get_other_group_bot(
        db, group_id, first_bot_guid
    )
    if not second:
        return

    bot2_guid = second['guid']
    bot2_name = second['name']
    bot2_traits = second['traits']

    # Get class/race for second bot
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot2_guid,))
    char_row = cursor.fetchone()
    if not char_row:
        return

    bot2 = {
        'guid': bot2_guid,
        'name': bot2_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    # Get updated history (includes first bot's msg)
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)
    members = get_group_members(db, group_id)

    allow_action = (
        random.random() < get_action_chance()
    )
    prompt = build_player_response_prompt(
        bot2, bot2_traits, player_name,
        player_message, mode,
        chat_history=chat_hist,
        members=members,
        allow_action=allow_action,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"2nd-reply:{bot2_name}"
    )
    if not response:
        logger.warning(
            f"Second bot reply ({bot2_name}): "
            f"LLM returned no response"
        )
        return

    parsed = parse_single_response(response)
    msg2 = strip_speaker_prefix(
        parsed['message'], bot2_name
    )
    msg2 = cleanup_message(
        msg2, action=parsed.get('action')
    )
    if not msg2:
        return
    if len(msg2) > 255:
        msg2 = msg2[:252] + "..."

    logger.info(
        f"Second bot response from "
        f"{bot2_name}: {msg2}"
    )

    emote = (
        parsed.get('emote')
        or pick_emote_for_statement(msg2)
    )
    insert_chat_message(
        db, bot2_guid, bot2_name, msg2,
        channel='party', delay_seconds=6,
        event_id=event_id, sequence=1,
        emote=emote,
    )

    _store_chat(
        db, group_id, bot2_guid,
        bot2_name, True, msg2
    )


def _welcome_from_existing_bot(
    db, client, config, group_id,
    new_bot_guid, new_bot_name,
    mode, event_id
):
    """Have an existing bot welcome a new group
    member. Finds a bot already in the group and
    generates a welcome message with a 5s delay
    (staggered after the 2s greeting).
    """
    other = get_other_group_bot(
        db, group_id, new_bot_guid
    )
    if not other:
        logger.info(
            "No existing bot to welcome "
            f"{new_bot_name} in group {group_id}"
        )
        return

    wb_guid = other['guid']
    wb_name = other['name']
    wb_traits = other['traits']

    # Get class/race/level for the welcoming bot
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (wb_guid,))
    char_row = cursor.fetchone()
    if not char_row:
        logger.warning(
            f"Welcome bot {wb_name} (guid "
            f"{wb_guid}) not found in characters"
        )
        return

    wb = {
        'guid': wb_guid,
        'name': wb_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    # Build context
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)
    members = get_group_members(db, group_id)

    allow_action = (
        random.random() < get_action_chance()
    )
    prompt = build_bot_welcome_prompt(
        wb, wb_traits, new_bot_name, mode,
        chat_history=chat_hist,
        members=members,
        allow_action=allow_action,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"welcome:{wb_name}"
    )
    if not response:
        logger.warning(
            f"Welcome LLM returned no response "
            f"for {wb_name}"
        )
        return

    parsed = parse_single_response(response)
    msg = strip_speaker_prefix(
        parsed['message'], wb_name
    )
    msg = cleanup_message(
        msg, action=parsed.get('action')
    )
    if not msg:
        logger.warning(
            "Empty welcome message after cleanup"
        )
        return
    if len(msg) > 255:
        msg = msg[:252] + "..."

    logger.info(
        f"Welcome from {wb_name} to "
        f"{new_bot_name}: {msg}"
    )

    # Insert with 5s delay (greeting is at 2s)
    emote = (
        parsed.get('emote')
        or pick_emote_for_statement(msg)
    )
    insert_chat_message(
        db, wb_guid, wb_name, msg,
        channel='party', delay_seconds=5,
        event_id=event_id, sequence=1,
        emote=emote,
    )

    _store_chat(
        db, group_id, wb_guid,
        wb_name, True, msg
    )


def _get_group_role_summary(db, group_id):
    """Query all bots in the group, look up their
    classes from the characters table, and return a
    role summary string like:
    "1 tank (Warrior), 1 healer (Priest),
     2 DPS (Mage, Rogue)"

    Returns (summary_str, role_counts_dict) or
    (None, None) if no data.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.bot_guid, t.bot_name,
               c.class AS class_id
        FROM llm_group_bot_traits t
        JOIN characters c ON c.guid = t.bot_guid
        WHERE t.group_id = %s
    """, (group_id,))
    rows = cursor.fetchall()
    if not rows:
        return None, None

    # Map to roles
    role_labels = {
        'tank': 'tank',
        'healer': 'healer',
        'melee_dps': 'DPS',
        'ranged_dps': 'DPS',
        'hybrid_tank': 'hybrid',
        'hybrid_healer': 'hybrid',
    }
    role_members = {}
    for row in rows:
        cls = get_class_name(row['class_id'])
        role_key = CLASS_ROLE_MAP.get(cls, 'DPS')
        label = role_labels.get(role_key, 'DPS')
        if label not in role_members:
            role_members[label] = []
        role_members[label].append(cls)

    # Build readable summary
    parts = []
    for label in ['tank', 'healer', 'DPS', 'hybrid']:
        members = role_members.get(label, [])
        if members:
            n = len(members)
            classes = ', '.join(members)
            parts.append(
                f"{n} {label} ({classes})"
            )

    has_tank = bool(role_members.get('tank'))
    has_healer = bool(role_members.get('healer'))

    summary = ', '.join(parts)
    return summary, {
        'has_tank': has_tank,
        'has_healer': has_healer,
        'total': len(rows),
    }


def _build_composition_comment_prompt(
    bot, traits, mode, role_summary,
    role_info, player_name="",
    player_class="",
    allow_action=True,
):
    """Build a short prompt for a bot to comment
    on the group's composition after joining.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot.get('race', ''),
            bot.get('class', '')
        )
        if ctx:
            rp_context = f"\n{ctx}"

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']}.\n"
        f"Your personality: {trait_str}"
        f"{rp_context}\n\n"
        f"You just joined a group"
    )
    if player_name:
        prompt += f" with {player_name}"
    player_desc = (
        f" (plus {player_name} the {player_class})"
        if player_name and player_class
        else " (plus the player)"
    )
    prompt += (
        f".\nGroup composition: {role_summary}"
        f"{player_desc}.\n"
    )

    # Add pointed observations
    if not role_info.get('has_tank'):
        prompt += "There is no dedicated tank.\n"
    if not role_info.get('has_healer'):
        prompt += "There is no dedicated healer.\n"

    if is_rp:
        style = (
            "Stay in-character. Make a brief, "
            "natural observation about the group "
            "composition from your class perspective."
        )
    else:
        style = (
            "Make a brief, casual comment about "
            "the group composition."
        )

    prompt += (
        f"\n{style}\n"
        f"One short sentence only (under 120 "
        f"characters). No greetings — you already "
        f"said hello."
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
    return append_json_instruction(
        prompt, allow_action
    )


def _maybe_comment_on_composition(
    db, client, config, group_id,
    bot, traits, mode, event_id,
    player_name=""
):
    """Optionally generate a composition comment
    after the bot joins a group. Chance controlled
    by CompositionCommentChance config (default 10%).
    Only fires if group has 2+ bots.
    """
    chance = int(config.get(
        'LLMChatter.GroupChatter'
        '.CompositionCommentChance', 10
    ))
    if random.randint(1, 100) > chance:
        return

    role_summary, role_info = (
        _get_group_role_summary(db, group_id)
    )

    # Look up the player's class for composition
    player_class = ""
    if player_name:
        try:
            cur = db.cursor(dictionary=True)
            cur.execute(
                "SELECT class FROM characters "
                "WHERE name = %s LIMIT 1",
                (player_name,)
            )
            row = cur.fetchone()
            if row:
                player_class = get_class_name(
                    row['class']
                )
        except Exception:
            pass
    if not role_summary or not role_info:
        return
    if role_info.get('total', 0) < 2:
        return

    allow_action = (
        random.random() < get_action_chance()
    )
    prompt = _build_composition_comment_prompt(
        bot, traits, mode, role_summary,
        role_info, player_name,
        player_class=player_class,
        allow_action=allow_action,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=min(max_tokens, 100),
        context=f"comp-comment:{bot['name']}"
    )
    if not response:
        logger.warning(
            f"Comp comment ({bot['name']}): "
            f"LLM returned no response"
        )
        return

    parsed = parse_single_response(response)
    msg = strip_speaker_prefix(
        parsed['message'], bot['name']
    )
    msg = cleanup_message(
        msg, action=parsed.get('action')
    )
    if not msg:
        return
    if len(msg) > 255:
        msg = msg[:252] + "..."

    logger.info(
        f"Comp comment from {bot['name']}: {msg}"
    )

    emote = (
        parsed.get('emote')
        or pick_emote_for_statement(msg)
    )
    insert_chat_message(
        db, bot['guid'], bot['name'], msg,
        channel='party', delay_seconds=8,
        event_id=event_id, sequence=2,
        emote=emote,
    )

    _store_chat(
        db, group_id, bot['guid'],
        bot['name'], True, msg
    )


def build_resurrect_reaction_prompt(
    bot, traits, mode, chat_history="",
    allow_action=True,
):
    """Build prompt for a bot reacting to being
    resurrected. The bot itself was just rezzed
    and reacts with gratitude, relief, or drama.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group resurrect creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    if is_rp:
        style = (
            "React in-character to being "
            "resurrected. A grateful warrior, "
            "a relieved healer, a dramatic mage "
            "— whatever fits your personality."
        )
    else:
        style = (
            "React naturally to being brought "
            "back to life. Could be grateful, "
            "relieved, dramatic, or casual."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"You just died and someone in your "
        f"party resurrected you. You are back "
        f"on your feet.\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Express gratitude, relief, or drama\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_zone_transition_prompt(
    bot, traits, zone_name, zone_id, mode,
    chat_history="", allow_action=True,
):
    """Build prompt for a bot commenting on arriving
    in a new zone.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group zone transition creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Try to get atmospheric zone flavor
    zone_flavor = get_zone_flavor(zone_id)
    zone_desc = ""
    if zone_flavor:
        zone_desc = (
            f"\nZone atmosphere: {zone_flavor}\n"
        )

    if is_rp:
        style = (
            "Comment in-character on arriving "
            "in this new area. Explorers get "
            "excited, cautious types express "
            "concern, warriors comment on "
            "potential threats."
        )
    else:
        style = (
            "Make a casual comment about "
            "arriving in a new zone. Natural "
            "and brief."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"Your party just arrived in "
        f"{zone_name}."
        f"{zone_desc}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {zone_name} by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
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
    return append_json_instruction(
        prompt, allow_action
    )


def build_quest_accept_reaction_prompt(
    bot, traits, acceptor_name, quest_name,
    quest_level, zone_name,
    mode, chat_history="", allow_action=True,
    quest_details="", quest_objectives="",
):
    """Build prompt for a bot reacting to the group
    accepting a new quest. Tone varies: excited,
    curious, cautious, matter-of-fact depending
    on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group quest accept creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    quest_context = (
        f"{acceptor_name} just "
        f"picked up the quest \"{quest_name}\" "
        f"(level {quest_level}) for the group in "
        f"{zone_name}. Current Status: "
        f"PREPARATION. You have the instructions "
        f"but haven't begun yet. Focus on the "
        f"task ahead, the travel required, or "
        f"the plan of attack. Use 'we' language."
    )

    level_diff = int(bot['level']) - int(quest_level)
    if level_diff < -3:
        difficulty_note = (
            " This quest is above your level — "
            "it could be challenging."
        )
    elif level_diff > 5:
        difficulty_note = (
            " This quest is well below your level "
            "— should be easy."
        )
    else:
        difficulty_note = ""

    quest_context += difficulty_note
    if quest_details:
        quest_context += (
            f" Quest description: {quest_details}"
        )
    if quest_objectives:
        quest_context += (
            f" Objectives: {quest_objectives}"
        )

    if is_rp:
        style = (
            "Show anticipation, caution, or "
            "eagerness about heading out. Speak "
            "about getting started or what lies "
            "ahead. Treat this as the beginning "
            "of a to-do list."
        )
    else:
        style = (
            "Casual comment about heading out "
            "to start the quest. Focus on the "
            "journey ahead, not the outcome."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{quest_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the quest by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
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
    return append_json_instruction(
        prompt, allow_action
    )


def build_discovery_reaction_prompt(
    bot, traits, area_name, player_name,
    player_class, xp_amount, mode,
    chat_history="", allow_action=True,
):
    """Build prompt for a bot reacting to the group
    discovering a new area. Should feel like arriving
    somewhere new — wonder, excitement, caution, or
    recognition depending on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group discovery creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    discovery_context = (
        f"Your group just discovered a new area: "
        f"{area_name}! This is a first-time "
        f"discovery — the group has never been "
        f"here before."
    )

    if is_rp:
        style = (
            "React in-character to discovering "
            "this new place. Comment on the "
            "scenery, what you've heard about it, "
            "whether it looks dangerous, or the "
            "thrill of exploring together."
        )
    else:
        style = (
            "Make a casual comment about "
            "discovering a new area. Natural "
            "and brief — like an explorer "
            "reacting to a new place."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{discovery_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {area_name} by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
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
    return append_json_instruction(
        prompt, allow_action
    )


def build_dungeon_entry_prompt(
    db, bot, traits, map_name, is_raid, map_id,
    mode, chat_history="", allow_action=True,
):
    """Build prompt for a bot reacting to entering
    a dungeon or raid instance.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group dungeon entry creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Try to get dungeon-specific flavor
    dungeon_flavor = get_dungeon_flavor(map_id)
    dungeon_desc = ""
    if dungeon_flavor:
        dungeon_desc = (
            f"\nDungeon atmosphere: "
            f"{dungeon_flavor}\n"
        )

    # Try to get boss names for context
    dungeon_bosses = get_dungeon_bosses(db, map_id)
    boss_context = ""
    if dungeon_bosses:
        boss_list = ', '.join(
            dungeon_bosses[:3]
        )
        boss_context = (
            f"\nKnown bosses here: {boss_list}\n"
        )

    instance_type = "raid" if is_raid else "dungeon"

    if is_rp:
        if is_raid:
            style = (
                "React in-character to entering "
                "a raid. This is a major challenge. "
                "Eager warriors steel themselves, "
                "cautious healers check supplies, "
                "scholarly mages study the "
                "surroundings."
            )
        else:
            style = (
                "React in-character to entering "
                "a dungeon. Personality-appropriate "
                "— eager, cautious, scholarly, or "
                "casual depending on your traits."
            )
    else:
        if is_raid:
            style = (
                "React casually to entering a "
                "raid. Could be excited, nervous, "
                "or just ready to go."
            )
        else:
            style = (
                "React casually to entering a "
                "dungeon. Brief and natural."
            )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"Your party just entered {map_name}, "
        f"a {instance_type}."
        f"{dungeon_desc}"
        f"{boss_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {map_name} by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_wipe_reaction_prompt(
    bot, traits, killer_name, mode,
    chat_history="", extra_data=None,
    allow_action=True,
):
    """Build prompt for a bot reacting to a total
    party wipe. Dramatic, frustrated, humorous,
    or resigned depending on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
        )
        actual_role = (
            extra_data.get('bot_state', {})
            .get('role')
        )

    logger.info(
        f"Group wipe creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=actual_role
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    wipe_context = (
        "Everyone in your party just died"
    )
    if killer_name:
        wipe_context += (
            f" — wiped by {killer_name}"
        )
    wipe_context += ". Total party wipe."

    if is_rp:
        style = (
            "React in-character to the wipe. "
            "Could be in-character despair, "
            "gallows humor, stoic acceptance, "
            "or dramatic frustration — whatever "
            "fits your personality."
        )
    else:
        style = (
            "React naturally to the wipe. "
            "Could be frustrated, humorous, "
            "resigned, or self-deprecating."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{wipe_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
    )
    if killer_name:
        prompt += (
            f"- Can reference {killer_name}\n"
        )
    prompt += (
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_corpse_run_reaction_prompt(
    bot, traits, zone_name, mode,
    chat_history="", dead_name="",
    is_player_death=False,
    allow_action=True,
):
    """Build prompt for a bot commenting on a
    corpse run. Either the bot died (self), or
    the real player died and the bot reacts.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=0.5, mode=mode
    )

    logger.info(
        f"Corpse run creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    zone_ctx = ""
    if zone_name:
        zone_ctx = (
            f" through {zone_name}"
        )

    if is_player_death:
        # Bot reacts to the player dying
        situation = (
            f"Your party leader {dead_name} "
            f"just died and released their "
            f"spirit. They're now running "
            f"back{zone_ctx} as a ghost to "
            f"reach their corpse."
        )
        if is_rp:
            style = (
                "React in-character to your "
                "leader's death. Could be "
                "concerned, offering words of "
                "encouragement, commenting on "
                "the danger, or darkly amused "
                "depending on your personality."
            )
        else:
            style = (
                "React to your party leader "
                "dying. Could be sympathetic, "
                "joking about it, offering to "
                "wait, or commenting on what "
                "killed them."
            )
    else:
        # Bot died themselves
        situation = (
            f"You just died and released your "
            f"spirit. Now you're running "
            f"back{zone_ctx} as a ghost to "
            f"reach your corpse."
        )
        if is_rp:
            style = (
                "Comment in-character on "
                "running back to your corpse "
                "as a ghost. Could be "
                "philosophical about death, "
                "grumbling about the walk, "
                "marveling at seeing the world "
                "as a spirit, or eager to get "
                "back into the fight."
            )
        else:
            style = (
                "Comment on the corpse run. "
                "Could be annoyed about the "
                "distance, making a joke about "
                "being a ghost, commenting on "
                "the scenery, or just resigned "
                "to the walk back."
            )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"{style}\n\n"
        f"Say something in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    if is_player_death:
        prompt += (
            f"\n- Refer to {dead_name} by name"
        )
    return append_json_instruction(
        prompt, allow_action
    )


# ============================================================
# STATE-TRIGGERED CALLOUT PROMPTS (Phase 2C)
# ============================================================
def build_low_health_callout_prompt(
    bot, traits, target_name, mode,
    chat_history="", extra_data=None,
    allow_action=True,
):
    """Bot is critically wounded (combat or OOC)."""
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
        )
        actual_role = (
            extra_data.get('bot_state', {})
            .get('role')
        )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=actual_role
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    hp = 0
    if extra_data:
        hp = int(
            extra_data.get('bot_state', {})
            .get('health_pct', 0)
        )

    situation = (
        f"You are critically wounded "
        f"({hp}% health)."
    )
    if target_name:
        situation += (
            f" You are fighting {target_name}."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"React with urgency — call for help, "
        f"express pain, or show desperation.\n"
        f"Say ONE short sentence in party chat.\n"
        f"Rules:\n"
        f"- Extremely brief, 3-10 words\n"
        f"- No quotes, no emojis\n"
        f"- Reflect your personality traits"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_oom_callout_prompt(
    bot, traits, target_name, mode,
    chat_history="", extra_data=None,
    allow_action=True,
):
    """Bot is running out of mana (combat or OOC).

    NOTE: Non-mana classes (Warrior, Rogue, DK) are
    filtered in C++ via GetMaxPower(POWER_MANA) > 0
    before the event is queued, so this function
    should only be called for mana-using classes.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
        )
        actual_role = (
            extra_data.get('bot_state', {})
            .get('role')
        )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=actual_role
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    mp = 0
    if extra_data:
        mp = int(
            extra_data.get('bot_state', {})
            .get('mana_pct', 0)
        )

    situation = (
        f"You are almost out of mana ({mp}%)."
    )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"Alert your group — ask for a moment "
        f"to drink, warn about low mana, or "
        f"express frustration.\n"
        f"Say ONE short sentence in party chat.\n"
        f"Rules:\n"
        f"- Extremely brief, 3-10 words\n"
        f"- No quotes, no emojis\n"
        f"- Reflect your personality traits"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_aggro_loss_callout_prompt(
    bot, traits, target_name, aggro_target,
    mode, chat_history="", extra_data=None,
    allow_action=True,
):
    """Tank lost aggro — mob attacking someone
    else in group."""
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
        )
        actual_role = (
            extra_data.get('bot_state', {})
            .get('role')
        )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=actual_role
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    situation = (
        f"You are the tank but {target_name} "
        f"is now attacking {aggro_target}."
    )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"React with urgency — warn the group, "
        f"try to get the mob's attention back, "
        f"or call out the danger.\n"
        f"Say ONE short sentence in party chat.\n"
        f"Rules:\n"
        f"- Extremely brief, 3-10 words\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {target_name} or "
        f"{aggro_target} by name\n"
        f"- Reflect your personality traits"
    )
    return append_json_instruction(
        prompt, allow_action
    )


# ============================================================
# HELPERS
# ============================================================


# ============================================================
# CHAT HISTORY
# ============================================================








def get_group_player_name(db, group_id):
    """Get the real player's name from chat history
    or player_msg events. Returns name or None.
    """
    cursor = db.cursor(dictionary=True)
    # Check chat history first (most reliable)
    cursor.execute("""
        SELECT speaker_name
        FROM llm_group_chat_history
        WHERE group_id = %s AND is_bot = 0
        ORDER BY id DESC
        LIMIT 1
    """, (group_id,))
    row = cursor.fetchone()
    if row:
        return row['speaker_name']

    # Fallback: check player_msg events
    cursor.execute("""
        SELECT JSON_EXTRACT(
            extra_data, '$.player_name'
        ) as pname
        FROM llm_chatter_events
        WHERE event_type = 'bot_group_player_msg'
          AND CAST(
              JSON_EXTRACT(
                  extra_data, '$.group_id'
              ) AS UNSIGNED
          ) = %s
        ORDER BY id DESC
        LIMIT 1
    """, (group_id,))
    row = cursor.fetchone()
    if row and row['pname']:
        # JSON_EXTRACT returns quoted string
        name = row['pname'].strip('"')
        if name:
            return name

    return None


def get_recent_weather(db, zone_id):
    """Get the most recent weather for a zone.
    Uses the ambient chatter queue (C++ writes real-time
    weather from its in-memory map) as the primary source.
    Returns weather type string or None.
    """
    cursor = db.cursor(dictionary=True)
    # Primary: get weather from ambient chatter queue
    # (C++ writes accurate real-time weather here)
    cursor.execute("""
        SELECT weather
        FROM llm_chatter_queue
        WHERE zone_id = %s
          AND weather != 'clear'
          AND TIMESTAMPDIFF(
              MINUTE, created_at, NOW()
          ) < 30
        ORDER BY id DESC
        LIMIT 1
    """, (zone_id,))
    row = cursor.fetchone()
    if row and row['weather']:
        return row['weather']
    return None


# ============================================================
# IDLE GROUP CHATTER
# ============================================================

# Idle chatter topics — richer categories focused
# on environment, lore, and party banter.
# Explicitly excluded: items, quests, quest rewards,
# spells, trade.
GROUP_IDLE_TOPICS = [
    # Environment / Zone
    'commenting on the scenery or surroundings',
    'noticing something interesting in the zone',
    'remarking on the local wildlife or creatures',
    'observing the landscape or terrain',
    # Weather / Time
    'commenting on the weather',
    'noticing the time of day',
    'mentioning how the light looks',
    # Class / Race
    'mentioning something about their class abilities',
    'making a comment related to their racial background',
    'comparing fighting styles or approaches',
    'sharing class-specific knowledge or tips',
    # Lore / World
    'mentioning a rumor or piece of lore',
    'wondering about the history of this place',
    'recalling something from their travels',
    'making an observation about the faction war',
    # Food / Drink
    'asking if anyone has food or water',
    'complaining about being hungry or thirsty',
    'mentioning a favorite food or drink',
    # Travel / Mounts
    'talking about their mount or travel stories',
    'commenting on how far they have walked',
    'wishing they had a faster mount',
    # Professions
    'mentioning their profession skill progress',
    'talking about gathering or crafting',
    'asking if anyone needs something crafted',
    # Capital Cities / Inns
    'reminiscing about a capital city or inn',
    'talking about what they do in town',
    'mentioning a favorite hangout spot',
    # Gear / Equipment
    'commenting on their own gear or armor',
    'noticing a party member looks well-equipped',
    'wishing they had better equipment',
    # Level Progress
    'mentioning how close they are to leveling',
    'talking about what abilities they want next',
    'reflecting on how far they have come',
    # AFK / Bio / Humor
    'joking about needing a bio break',
    'wondering how long until the next rest stop',
    'making a joke about falling asleep at the keys',
    # General party banter
    'making small talk with a party member',
    'cracking a joke or making a witty observation',
    'complaining about something minor',
    'sharing a random thought',
]

# Track last idle chatter per group
_last_idle_chatter = {}
_idle_inflight = set()
_last_idle_chatter_lock = threading.Lock()


def build_idle_chatter_prompt(
    bot, traits, mode,
    chat_history="", members=None,
    zone_id=0, map_id=0,
    current_weather=None,
    player_name=None,
    address_target=None,
    dungeon_bosses=None,
    recent_messages=None,
    allow_action=True,
):
    """Build prompt for idle party chat.

    Bot says something casual during a quiet moment
    — no specific event triggered this, just
    natural party banter.

    Args:
        address_target: None (general), 'player',
            or a bot name to address specifically
        player_name: real player name if known
        current_weather: weather string (overworld)
        zone_id: for zone flavor
        map_id: for dungeon flavor
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    topic = random.choice(GROUP_IDLE_TOPICS)

    logger.info(
        f"Idle chatter creativity: tone={tone}, "
        f"mood={mood}, twist={twist}, topic={topic}"
        f", target={address_target}"
    )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=bot.get('role')
        )
        if ctx:
            rp_context = f"\n{ctx}"

        profile = RACE_SPEECH_PROFILES.get(
            bot['race']
        )
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

    # Location context
    dungeon_flav = get_dungeon_flavor(map_id)
    zone_flav = get_zone_flavor(zone_id)
    in_dungeon = dungeon_flav is not None
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )
        if dungeon_bosses:
            boss_list = ', '.join(
                dungeon_bosses[:6]
            )
            rp_context += (
                f"\nBosses here: {boss_list}"
            )
    elif zone_flav:
        rp_context += (
            f"\nZone context: {zone_flav}"
        )

    # Environmental context (time sometimes,
    # weather only overworld)
    weather_arg = (
        None if in_dungeon else current_weather
    )
    env = get_environmental_context(weather_arg)
    if env['time']:
        rp_context += (
            f"\nTime of day: {env['time']}"
        )
    if env['weather']:
        rp_context += (
            f"\nCurrent weather: {env['weather']}"
        )

    if members:
        others = [
            m for m in members
            if m != bot['name']
        ]
        if player_name and player_name not in others:
            others.append(f"{player_name} (player)")
        if others:
            rp_context += (
                f"\nParty members: "
                f"{', '.join(others)}"
            )
    if chat_history:
        rp_context += f"{chat_history}"

    if is_rp:
        style = (
            "Say something casual in party chat "
            "while adventuring. Stay in-character."
        )
    else:
        style = (
            "Say something casual in party chat "
            "during downtime or while traveling. "
            "Natural and relaxed."
        )

    # Address direction
    address_hint = ""
    if address_target == 'player' and player_name:
        address_hint = (
            f"\nDirect your comment to "
            f"{player_name} (the player in "
            f"your group). You can use their "
            f"name."
        )
    elif address_target and address_target != 'player':
        address_hint = (
            f"\nDirect your comment to "
            f"{address_target} (a party member). "
            f"You can use their name."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"You're in a party, currently {topic}.\n"
        f"{address_hint}\n"
        f"{style}\n\n"
        f"Say something casual in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Reflect your personality traits\n"
        f"- Just a natural idle comment\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat\n"
        f"- NEVER claim to have killed a creature, "
        f"looted an item, completed a quest, "
        f"or made a trade\n"
        f"- Stick to observation, opinion, banter, "
        f"and small talk"
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
    return append_json_instruction(
        prompt, allow_action
    )


def build_idle_conversation_prompt(
    bots, traits_map, mode, topic,
    chat_history="", members=None,
    zone_id=0, map_id=0,
    current_weather=None,
    player_name=None,
    dungeon_bosses=None,
    recent_messages=None,
    allow_action=True,
):
    """Build prompt for a multi-bot idle conversation.

    Generates a short message exchange between 2-4
    bots about environment, lore, class/race, etc.
    Message count scales with number of bots.

    Args:
        bots: list of 2-4 bot dicts
            (name, class, etc)
        traits_map: dict mapping bot name to traits
        mode: 'normal' or 'roleplay'
        topic: conversation topic string
        chat_history: formatted recent chat string
        members: list of all group member names
        zone_id: zone ID for flavor text
        map_id: map ID for dungeon flavor text
        current_weather: weather string (overworld)
        player_name: real player name if known
        dungeon_bosses: list of boss names
    """
    is_rp = (mode == 'roleplay')
    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]

    parts = []

    if num_bots == 2:
        speaker_desc = "two"
    elif num_bots == 3:
        speaker_desc = "three"
    else:
        speaker_desc = "four"

    if is_rp:
        parts.append(
            f"Generate a short in-character party "
            f"chat exchange between {speaker_desc} "
            f"adventurers."
        )
    else:
        parts.append(
            f"Generate a short casual party chat "
            f"exchange between {speaker_desc} "
            f"WoW players."
        )

    # Dungeon flavor takes priority over zone flavor
    dungeon_flav = get_dungeon_flavor(map_id)
    zone_flav = get_zone_flavor(zone_id)
    in_dungeon = dungeon_flav is not None
    if dungeon_flav:
        parts.append(
            f"Dungeon context: {dungeon_flav}"
        )
        if dungeon_bosses:
            boss_list = ', '.join(
                dungeon_bosses[:6]
            )
            parts.append(
                f"Bosses here: {boss_list}"
            )
    elif zone_flav:
        parts.append(f"Zone context: {zone_flav}")

    # Environmental context: time sometimes,
    # weather only overworld
    weather_arg = (
        None if in_dungeon else current_weather
    )
    env = get_environmental_context(weather_arg)
    if env['time']:
        parts.append(f"Time of day: {env['time']}")
    if env['weather']:
        parts.append(
            f"Current weather: {env['weather']}"
        )

    # Speakers with traits and class/race
    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    for bot in bots:
        t = traits_map.get(bot['name'], [])
        trait_str = (
            ', '.join(t) if t else 'average'
        )
        parts.append(
            f"{bot['name']} is a level "
            f"{bot['level']} {bot['race']} "
            f"{bot['class']} "
            f"(personality: {trait_str})"
        )
        if is_rp:
            rp_ctx = build_race_class_context(
                bot.get('race', ''),
                bot.get('class', ''),
                actual_role=bot.get('role'),
            )
            if rp_ctx:
                parts.append(f"  {rp_ctx}")

    parts.append(
        "Names: Sometimes address each other by "
        "name (1-2 times), but not every message."
    )
    if player_name:
        parts.append(
            f"Also in party: {player_name} "
            f"(a real player). You may mention "
            f"or address them occasionally."
        )

    # Topic
    parts.append(f"Topic: {topic}")

    # Tone and twist
    tone = pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    parts.append(f"Overall tone: {tone}")
    if twist:
        parts.append(f"Creative twist: {twist}")

    # Message count scales with num_bots, cap at 8
    msg_count = min(2 * num_bots, 8)
    mood_sequence = (
        generate_conversation_mood_sequence(
            msg_count, mode
        )
    )
    length_sequence = (
        generate_conversation_length_sequence(
            msg_count
        )
    )

    twist_log = (
        f", twist={twist}" if twist else ""
    )
    logger.info(
        f"Idle conversation: tone={tone}, "
        f"moods={mood_sequence}{twist_log}, "
        f"topic={topic}, bots={num_bots}, "
        f"msgs={msg_count}"
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow for each message):"
    )
    for i, mood in enumerate(mood_sequence):
        speaker = bot_names[i % num_bots]
        parts.append(
            f"  Message {i+1} ({speaker}): "
            f"mood={mood}, "
            f"length={length_sequence[i]}"
        )

    # Natural flow instruction for 3+ bots
    if num_bots > 2:
        parts.append(
            "IMPORTANT: EVERY speaker MUST have "
            "at least one message — do NOT skip "
            "any participant. Don't use rigid "
            "round-robin order — let the "
            "conversation flow organically. "
            "Some speakers may reply back-to-back "
            "if it feels natural."
        )

    # Party context
    if members:
        others = [
            m for m in members
            if m not in bot_names
        ]
        if others:
            parts.append(
                f"Other party members: "
                f"{', '.join(others)}"
            )

    if chat_history:
        parts.append(chat_history)

    # Style and rules
    length_hint = _pick_length_hint(mode)
    if is_rp:
        parts.append(
            "Guidelines: Stay in-character for "
            "race and class; no game terms or "
            f"OOC; {length_hint}; "
            "vary message lengths naturally"
        )
    else:
        parts.append(
            "Guidelines: Sound like normal people "
            "chatting in a game; casual and "
            f"relaxed; {length_hint}; "
            "vary lengths naturally"
        )

    parts.append(
        "Do NOT mention quests, quest rewards, "
        "items, spells, or trade. "
        "NEVER claim to have just killed a creature (past explots is fine), "
        "just looted an item (you can mention items looted in the past), just completed a quest (you can mention quests completed in the past), "
        "or made a trade. "
        "Stick to observation, opinion, banter, "
        "ocasional philosophical consideration. "
        "Don't repeat jokes or themes already "
        "said in chat."
    )

    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        parts.append(
            "Background feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )

    anti_rep = build_anti_repetition_context(
        recent_messages
    )
    if anti_rep:
        parts.append(anti_rep)

    parts.append(
        f"Emotes: Each message may include an "
        f"optional \"emote\" field (one of: "
        f"{EMOTE_LIST_STR}). Pick an emote that "
        f"fits the message mood, or omit it."
    )

    if allow_action:
        parts.append(
            "Actions: Each message may include an "
            "optional \"action\" field — a short "
            "physical action the character performs "
            "(e.g. \"scratches chin\", \"leans on "
            "staff\", \"adjusts pack\"). 2-5 words, "
            "no asterisks. Omit if not needed."
        )
    else:
        parts.append(
            "Actions: Do not include an action "
            "field in this response."
        )

    parts.append(
        "JSON rules: Use double quotes, escape "
        "quotes/newlines, no trailing commas, "
        "no code fences."
    )
    example_msgs = ',\n  '.join(
        [
            f'{{"speaker": "{name}", '
            f'"message": "...", "emote": "talk"'
            f', "action": "..."}}'
            for name in bot_names
        ]
    )
    parts.append(
        f"\nRespond with EXACTLY {msg_count} "
        f"messages in JSON:\n[\n  "
        f"{example_msgs}\n]\n"
        f"ONLY the JSON array, nothing else."
    )

    return '\n'.join(parts)


def check_idle_group_chatter(
    db, client, config
):
    """Check active groups for idle chatter.

    Called periodically from the bridge main loop.
    Finds groups that have been quiet and maybe
    triggers casual party chat from a random bot.

    50% chance: single idle statement (original)
    50% chance: 2-bot conversation (new)

    Returns True if a message was generated.
    """
    # Read config values (with defaults)
    idle_chance = int(config.get(
        'LLMChatter.GroupChatter.IdleChance', 15
    ))
    idle_cooldown = int(config.get(
        'LLMChatter.GroupChatter.IdleCooldown', 30
    ))

    # Get all active groups from bot traits
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT group_id
        FROM llm_group_bot_traits
    """)
    groups = cursor.fetchall()

    if not groups:
        return False

    # Pick one group at random to check
    group = random.choice(groups)
    group_id = group['group_id']

    # Atomic cooldown check + inflight reservation
    with _last_idle_chatter_lock:
        # Prune stale entries (older than 30 min)
        cutoff = time.time() - 1800
        for k in list(_last_idle_chatter):
            if _last_idle_chatter[k] <= cutoff:
                del _last_idle_chatter[k]

        now = time.time()
        last_idle = _last_idle_chatter.get(
            group_id, 0
        )
        if now - last_idle < idle_cooldown:
            return False
        if group_id in _idle_inflight:
            return False
        _idle_inflight.add(group_id)

    try:
        # Get all bots in this group (needed for
        # dynamic chance scaling before RNG roll)
        cursor.execute("""
            SELECT bot_guid, bot_name,
                   trait1, trait2, trait3, role
            FROM llm_group_bot_traits
            WHERE group_id = %s
            ORDER BY RAND()
        """, (group_id,))
        all_bots = cursor.fetchall()

        if not all_bots:
            return False

        # Scale chance by bot count so total group
        # idle output stays constant regardless of
        # group size
        num_bots = len(all_bots)
        effective_chance = max(
            1, idle_chance // max(num_bots, 1)
        )
        if random.randint(1, 100) > effective_chance:
            return False

        idle_history_limit = int(config.get(
            'LLMChatter.GroupChatter.'
            'IdleHistoryLimit', 5
        ))

        mode = get_chatter_mode(config)
        history = _get_recent_chat(
            db, group_id,
            limit=idle_history_limit
        )
        chat_hist = format_chat_history(history)
        members = get_group_members(
            db, group_id
        )

        # Get context: player name, zone, weather
        player_name = get_group_player_name(
            db, group_id
        )

        # Get zone/map from first bot's character
        cursor.execute("""
            SELECT zone, map
            FROM characters WHERE guid = %s
        """, (all_bots[0]['bot_guid'],))
        loc_row = cursor.fetchone()
        zone_id = (
            int(loc_row['zone'])
            if loc_row else 0
        )
        map_id = (
            int(loc_row['map'])
            if loc_row else 0
        )

        current_weather = (
            get_recent_weather(db, zone_id)
            if zone_id else None
        )

        # Get dungeon bosses if in a dungeon
        in_dungeon = (
            get_dungeon_flavor(map_id) is not None
        )
        dungeon_bosses = (
            get_dungeon_bosses(db, map_id)
            if in_dungeon else []
        )

        # Log gathered context
        bot_names_str = ', '.join(
            b['bot_name'] for b in all_bots
        )
        logger.info(
            f"Idle chatter context: "
            f"group={group_id}, "
            f"bots=[{bot_names_str}], "
            f"player={player_name}, "
            f"zone={zone_id}, map={map_id}, "
            f"in_dungeon={in_dungeon}, "
            f"weather={current_weather}, "
            f"bosses={len(dungeon_bosses)}, "
            f"history={len(history)} msgs"
        )

        conv_bias = int(config.get(
            'LLMChatter.GroupChatter.'
            'ConversationBias', 70
        ))
        use_conversation = (
            random.randint(1, 100) <= conv_bias
            and len(all_bots) >= 2
        )

        logger.info(
            f"Idle chatter mode: "
            f"{'conversation' if use_conversation else 'statement'}"
            f" ({len(all_bots)} bots in group)"
        )

        if use_conversation:
            result = _idle_conversation(
                db, client, config, group_id,
                all_bots, mode,
                chat_hist, members, now,
                current_weather=current_weather,
                player_name=player_name,
                dungeon_bosses=dungeon_bosses,
            )
        else:
            result = _idle_single_statement(
                db, client, config, group_id,
                all_bots, mode,
                chat_hist, members, now,
                zone_id=zone_id, map_id=map_id,
                current_weather=current_weather,
                player_name=player_name,
                dungeon_bosses=dungeon_bosses,
            )
        return result
    finally:
        with _last_idle_chatter_lock:
            _idle_inflight.discard(group_id)


def _idle_single_statement(
    db, client, config, group_id,
    all_bots, mode, chat_hist, members, now,
    zone_id=0, map_id=0,
    current_weather=None, player_name=None,
    dungeon_bosses=None,
):
    """Generate a single idle statement from one bot.

    Address targets:
    - 1 bot: always talk to the real player
    - 2+ bots: randomly pick between player,
      another bot, or general group comment
    """

    bot_row = all_bots[0]
    bot_guid = bot_row['bot_guid']
    bot_name = bot_row['bot_name']
    traits = [
        bot_row['trait1'],
        bot_row['trait2'],
        bot_row['trait3'],
    ]

    # Get class/race from characters table
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (bot_guid,))
    char_row = cursor.fetchone()

    if not char_row:
        return False

    bot = {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
        'role': bot_row.get('role'),
    }

    # Determine address target
    if len(all_bots) == 1:
        # Solo bot — always talk to player
        address_target = 'player'
    else:
        # Multiple bots — pick a target
        roll = random.random()
        if roll < 0.35 and player_name:
            address_target = 'player'
        elif roll < 0.65:
            # Pick another bot to address
            other = random.choice(
                [b for b in all_bots
                 if b['bot_guid'] != bot_guid]
            )
            address_target = other['bot_name']
        else:
            address_target = None

    boss_str = (
        f", bosses={len(dungeon_bosses or [])}"
        if dungeon_bosses else ""
    )
    logger.info(
        f"Triggering idle statement for "
        f"{bot_name} in group {group_id}: "
        f"target={address_target}, "
        f"zone={zone_id}, map={map_id}, "
        f"weather={current_weather}, "
        f"player={player_name}{boss_str}"
    )

    recent_msgs = get_recent_bot_messages(
        db, bot_guid
    )

    try:
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_idle_chatter_prompt(
            bot, traits, mode,
            chat_history=chat_hist,
            members=members,
            zone_id=zone_id,
            map_id=map_id,
            current_weather=current_weather,
            player_name=player_name,
            address_target=address_target,
            dungeon_bosses=dungeon_bosses,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        response = call_llm(
            client, prompt, config,
            max_tokens_override=max_tokens,
            context=f"idle:{bot_name}"
        )

        if not response:
            logger.warning(
                f"Idle statement ({bot_name}): "
                f"LLM returned no response"
            )
            return False

        parsed = parse_single_response(response)
        message = strip_speaker_prefix(
            parsed['message'], bot_name
        )
        message = cleanup_message(
            message, action=parsed.get('action')
        )
        if not message:
            logger.warning(
                "Idle chatter: empty after cleanup"
            )
            return False
        if len(message) > 255:
            message = message[:252] + "..."

        logger.info(
            f"Idle chatter from {bot_name}: "
            f"{message}"
        )

        # Insert directly into messages table
        emote = (
            parsed.get('emote')
            or pick_emote_for_statement(message)
        )
        insert_chat_message(
            db, bot_guid, bot_name, message,
            channel='party', delay_seconds=2,
            event_id=None, emote=emote,
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        with _last_idle_chatter_lock:
            _last_idle_chatter[group_id] = now
        return True

    except Exception as e:
        logger.error(
            f"Error generating idle statement: {e}"
        )
        return False


def _idle_conversation(
    db, client, config, group_id,
    bot_rows, mode, chat_hist, members, now,
    current_weather=None, player_name=None,
    dungeon_bosses=None,
):
    """Generate a multi-bot idle conversation.

    Picks 2 to N bots (capped at 4), builds a
    conversation prompt, parses JSON response,
    inserts staggered messages, and stores in
    chat history.
    """

    # Pick how many bots participate (2 to 4)
    num_bots = random.randint(
        2, min(len(bot_rows), 4)
    )
    selected_rows = random.sample(
        bot_rows, num_bots
    )

    # Build bot dicts and traits map
    bots = []
    traits_map = {}
    zone_id = 0
    map_id = 0
    for br in selected_rows:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT class, race, level, zone, map
            FROM characters
            WHERE guid = %s
        """, (br['bot_guid'],))
        char = cursor.fetchone()
        if not char:
            return False
        bot = {
            'guid': br['bot_guid'],
            'name': br['bot_name'],
            'class': get_class_name(
                char['class']
            ),
            'race': get_race_name(char['race']),
            'level': char['level'],
            'role': br.get('role'),
        }
        bots.append(bot)
        traits_map[br['bot_name']] = [
            br['trait1'], br['trait2'],
            br['trait3'],
        ]
        zone_id = int(char.get('zone', 0))
        map_id = int(char.get('map', 0))

    bot_names = [b['name'] for b in bots]
    topic = random.choice(GROUP_IDLE_TOPICS)

    boss_str = (
        f", bosses={len(dungeon_bosses or [])}"
        if dungeon_bosses else ""
    )
    names_str = ' & '.join(bot_names)
    logger.info(
        f"Triggering idle conversation in "
        f"group {group_id}: {names_str} "
        f"({num_bots} bots), topic={topic}, "
        f"map={map_id}, zone={zone_id}, "
        f"weather={current_weather}, "
        f"player={player_name}{boss_str}"
    )

    # Pool recent messages from all participating bots
    recent_msgs = []
    for br in selected_rows:
        msgs = get_recent_bot_messages(
            db, br['bot_guid']
        )
        recent_msgs.extend(msgs)

    try:
        allow_action = (
            random.random() < get_action_chance()
        )
        prompt = build_idle_conversation_prompt(
            bots, traits_map, mode, topic,
            chat_history=chat_hist,
            members=members,
            zone_id=zone_id,
            map_id=map_id,
            current_weather=current_weather,
            player_name=player_name,
            dungeon_bosses=dungeon_bosses,
            recent_messages=recent_msgs,
            allow_action=allow_action,
        )

        # Scale tokens with number of bots
        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        conv_tokens = min(
            max_tokens * (1 + num_bots), 1000
        )
        names_ctx = ','.join(bot_names)
        response = call_llm(
            client, prompt, config,
            max_tokens_override=conv_tokens,
            context=f"idle-conv:{names_ctx}"
        )

        if not response:
            logger.warning(
                f"Idle conversation "
                f"({names_ctx}): "
                f"LLM returned no response"
            )
            return False

        logger.info(
            f"LLM raw response "
            f"(len={len(response)}):\n{response}"
        )

        # Parse JSON conversation
        messages = parse_conversation_response(
            response, bot_names
        )

        if not messages:
            logger.warning(
                "Idle conversation: failed to "
                "parse"
            )
            return False

        logger.info(
            f"Idle conversation "
            f"({len(messages)} msgs, "
            f"{num_bots} bots) in group "
            f"{group_id}: "
            + ', '.join(
                f"{m['name']}: {m['message']}"
                for m in messages
            )
        )

        # Insert messages with staggered delivery
        cumulative_delay = 2.0
        prev_len = 0

        for seq, msg in enumerate(messages):
            msg_text = msg['message']
            text = strip_speaker_prefix(
                msg_text, msg['name']
            )
            text = cleanup_message(
                text,
                action=msg.get('action')
            )
            if not text:
                continue
            if len(text) > 255:
                text = text[:252] + "..."

            # Find the bot_guid for speaker
            speaker_guid = None
            for br in selected_rows:
                if br['bot_name'] == msg['name']:
                    speaker_guid = (
                        br['bot_guid']
                    )
                    break
            if not speaker_guid:
                continue

            # Calculate staggered delay
            if seq > 0:
                delay = calculate_dynamic_delay(
                    len(text), config,
                    prev_message_length=prev_len,
                )
                cumulative_delay += delay

            insert_chat_message(
                db, speaker_guid, msg['name'],
                text, channel='party',
                delay_seconds=int(cumulative_delay),
                event_id=None, sequence=seq,
                emote=msg.get('emote'),
            )

            _store_chat(
                db, group_id, speaker_guid,
                msg['name'], True, text
            )

            prev_len = len(text)

        with _last_idle_chatter_lock:
            _last_idle_chatter[group_id] = now
        return True

    except Exception as e:
        logger.error(
            f"Error generating idle "
            f"conversation: {e}"
        )
        return False


# ============================================================
# PRE-CACHE PROMPT BUILDERS
# ============================================================

def build_precache_combat_pull_prompt(
    bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=True,
):
    """Build prompt for a cached combat pull cry.

    The response must contain {target} where the
    enemy name goes. C++ resolves it at delivery.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
        f"\nCurrent mood: {mood}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"
    prompt += (
        "\n\nYou just engaged an enemy in combat "
        "with your party. Write a very short "
        "pull cry or battle shout (1 sentence, "
        "3-10 words).\n"
        "Use {target} where the enemy name goes "
        "(e.g. \"I'll handle {target}!\" or "
        "\"Watch out, {target} incoming!\").\n"
        "Rules:\n"
        "- Must include {target} exactly once\n"
        "- Reflect your personality and mood\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )


def build_precache_state_prompt(
    state_type, bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=True,
):
    """Build prompt for a cached state callout.

    state_type: 'low_health', 'oom', 'aggro_loss'
    low_health and oom have NO placeholders.
    aggro_loss uses {target} only.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
        f"\nCurrent mood: {mood}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"

    if state_type == 'low_health':
        prompt += (
            "\n\nYou are critically wounded. "
            "Write a very short callout "
            "(1 sentence, 3-10 words) asking for "
            "help or expressing pain.\n"
            "Rules:\n"
            "- First person only (\"I need "
            "healing!\", \"I'm going down!\")\n"
            "- Do NOT use any placeholders or "
            "names\n"
        )
    elif state_type == 'oom':
        # NOTE: Non-mana classes (Warrior, Rogue, DK)
        # are filtered upstream — C++ checks
        # GetMaxPower(POWER_MANA) > 0 for live events,
        # and refill_precache_pool() skips state_oom
        # for class_ids {1, 4, 6}.
        prompt += (
            "\n\nYou are almost out of mana. "
            "Write a very short callout "
            "(1 sentence, 3-10 words) alerting "
            "your group.\n"
            "Rules:\n"
            "- First person only (\"I need to "
            "drink\", \"No mana left!\")\n"
            "- Do NOT use any placeholders or "
            "names\n"
        )
    elif state_type == 'aggro_loss':
        prompt += (
            "\n\nYou are in combat and losing "
            "threat on your target. Write a very "
            "short callout (1 sentence, 3-10 "
            "words) warning your group.\n"
            "Use {target} where the enemy name "
            "goes (e.g. \"I'm losing {target}!\" "
            "or \"{target} is breaking free!\").\n"
            "Rules:\n"
            "- Must include {target} exactly once\n"
        )
    else:
        prompt += (
            "\n\nYou are in a stressful combat "
            "situation. Write a very short callout "
            "(1 sentence, 3-10 words).\n"
            "Rules:\n"
        )

    prompt += (
        "- Reflect your personality and mood\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )


def build_precache_spell_support_prompt(
    bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=True,
):
    """Build prompt for a cached spell support
    reaction. Uses {target} and {spell} placeholders.

    Caster perspective — the bot IS the caster.
    C++ skips cache only for self-cast (bot casting
    on itself). When bot casts on someone else, the
    cached message delivers instantly.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
        f"\nCurrent mood: {mood}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"

    prompt += (
        "\n\nYou just cast a support spell on a "
        "groupmate. Write a very short comment "
        "(1 sentence, 3-10 words) about YOUR "
        "spell from the CASTER perspective."
        "\nUse these placeholders:\n"
        "- {spell} = the spell you cast\n"
        "- {target} = who you cast it on\n"
        "Example: \"There you go {target}, "
        "{spell} should help.\" or \"{target}, "
        "you're covered.\"\n"
    )

    prompt += (
        "Rules:\n"
        "- Use the placeholders exactly as shown "
        "(with curly braces)\n"
        "- Reflect your personality and mood\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )


def build_precache_spell_offensive_prompt(
    bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=True,
):
    """Build prompt for a cached offensive spell
    reaction. Uses {target} and {spell} placeholders.

    Caster perspective — the bot IS the caster.
    C++ only uses this cache when casterIsBot.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
        f"\nCurrent mood: {mood}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"

    prompt += (
        "\n\nYou just cast an offensive spell on "
        "an enemy in combat. Write a very short "
        "battle cry or taunt (1 sentence, 3-10 "
        "words) from the CASTER perspective."
        "\nUse these placeholders:\n"
        "- {spell} = the spell you cast\n"
        "- {target} = the enemy you hit (may be "
        "absent — write lines that work without it)\n"
        "Example: \"{spell} incoming!\" or "
        "\"Eat {spell}, {target}!\" or "
        "\"They won't last long.\"\n"
    )

    prompt += (
        "Rules:\n"
        "- Use the placeholders exactly as shown "
        "(with curly braces)\n"
        "- Reflect your personality and mood\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )
