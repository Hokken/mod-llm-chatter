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
- bot_group_dungeon_entry: reaction to dungeon/raid
- bot_group_wipe: reaction to total party wipe
- idle chatter: periodic casual party chat during lulls
  (2 to N bot conversations)

Imports from chatter_constants, chatter_shared,
and chatter_prompts.
"""

import logging
import random
import threading
import time

# Module-level config defaults (set by init_group_config)
_chat_history_limit = 10
_spice_count = 2

from chatter_shared import (
    call_llm, cleanup_message, strip_speaker_prefix,
    get_chatter_mode, get_class_name, get_race_name,
    get_db_connection, build_race_class_context,
    build_race_class_context_parts,
    parse_extra_data, get_zone_flavor,
    get_subzone_lore,
    format_location_label,
    pick_random_max_tokens,
    get_dungeon_flavor, get_dungeon_bosses,
    parse_conversation_response,
    calculate_dynamic_delay,
    find_addressed_bot,
    insert_chat_message,
    pick_emote_for_statement,
    detect_item_links,
    query_item_details,
    format_item_context,
    build_anti_repetition_context,
    get_recent_bot_messages,
    append_json_instruction,
    parse_single_response,
    build_talent_context,
    get_zone_name,
    get_subzone_name,
    stagger_if_needed,
    build_zone_metadata,
    get_player_zone,
    strip_conversation_actions,
    append_conversation_json_instruction,
)
from chatter_db import (
    get_character_info_by_name,
    get_group_location,
    is_player_online,
)
from chatter_prompts import (
    pick_random_tone,
    maybe_get_creative_twist,
    get_environmental_context,
    generate_conversation_mood_sequence,
    generate_conversation_length_sequence,
    pick_personality_spices,
)
from chatter_group_state import (
    set_group_chat_history_limit,
    assign_bot_traits,
    get_other_group_bot,
    _generate_farewell,
    _has_recent_event,
    _mark_event,
    _store_chat,
    _get_recent_chat,
    format_chat_history,
    get_group_members,
    get_group_player_name,
)
from chatter_group_handlers import (
    _maybe_talent_context,
    process_group_kill_event,
    process_group_loot_event,
    process_group_combat_event,
    process_group_death_event,
    process_group_levelup_event,
    process_group_quest_complete_event,
    process_group_quest_objectives_event,
    process_group_achievement_event,
    process_group_spell_cast_event,
    process_group_resurrect_event,
    process_group_zone_transition_event,
    process_group_quest_accept_event,
    process_group_quest_accept_batch_event,
    process_group_dungeon_entry_event,
    process_group_wipe_event,
    process_group_corpse_run_event,
    process_group_low_health_event,
    process_group_oom_event,
    process_group_aggro_loss_event,
    process_group_nearby_object_event,
    execute_player_msg_conversation,
)
from chatter_links import resolve_and_format_links
from chatter_memory import (
    start_session,
    queue_memory,
    get_bot_memories,
    flush_session_memories,
    sanitize_memory_for_prompt,
    _get_group_lock,
    _active_sessions,
)
from chatter_group_prompts import (
    set_prompt_spice_count,
    _pick_length_hint,
    build_bot_greeting_prompt,
    build_bot_welcome_prompt,
    build_batch_welcome_prompt,
    build_player_response_prompt,
    build_precache_combat_pull_prompt,
    build_precache_state_prompt,
    build_precache_spell_support_prompt,
    build_precache_spell_offensive_prompt,
    build_nearby_object_conversation_prompt,
    build_bot_question_prompt,
)
from chatter_constants import (
    RACE_SPEECH_PROFILES,
    CLASS_ROLE_MAP,
    AMBIENT_CHAT_TOPICS,
    AMBIENT_CHAT_TOPICS_RP,
    BG_MAP_NAMES,
    RAID_MAP_IDS,
)

logger = logging.getLogger(__name__)

# N3 compatibility note:
# keep this module as the stable import surface while
# split skeleton modules are introduced incrementally.
__all__ = [
    'init_group_config',
    'process_group_event',
    'process_group_join_batch_event',
    'process_group_player_msg_event',
    'process_group_kill_event',
    'process_group_loot_event',
    'process_group_combat_event',
    'process_group_death_event',
    'process_group_levelup_event',
    'process_group_quest_complete_event',
    'process_group_quest_objectives_event',
    'process_group_achievement_event',
    'process_group_spell_cast_event',
    'process_group_resurrect_event',
    'process_group_zone_transition_event',
    'process_group_quest_accept_event',
    'process_group_quest_accept_batch_event',
    'process_group_dungeon_entry_event',
    'process_group_wipe_event',
    'process_group_corpse_run_event',
    'process_group_low_health_event',
    'process_group_oom_event',
    'process_group_aggro_loss_event',
    'process_group_nearby_object_event',
    'check_idle_group_chatter',
    'build_precache_combat_pull_prompt',
    'build_precache_state_prompt',
    'build_precache_spell_support_prompt',
    'build_precache_spell_offensive_prompt',
    'build_nearby_object_conversation_prompt',
    'process_group_farewell_event',
]


def init_group_config(config):
    """Initialize module-level config values."""
    global _chat_history_limit, _spice_count
    try:
        val = int(
            config.get('LLMChatter.ChatHistoryLimit', 10)
        )
    except (ValueError, TypeError):
        val = 10
    _chat_history_limit = max(1, min(val, 50))
    try:
        _spice_count = int(config.get(
            'LLMChatter.PersonalitySpiceCount', 2
        ))
        _spice_count = max(0, min(_spice_count, 5))
    except Exception:
        logger.error(
            "Failed to parse PersonalitySpiceCount",
            exc_info=True,
        )
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
    'cast', 'castnc', 'spell',
    'buff', 'glyphs', 'glyph equip',
    'remove glyph', 'pet', 'tame',
    'trainer', 'talent', 'talents', 'spells',
    # Trading / interaction
    'trade', 'nontrade', 'craft', 'flag',
    'mail', 'sendmail', 'bank', 'gbank',
    'talk', 'emote', 'enter vehicle',
    'leave vehicle',
    # Status / information
    'stats', 'reputation', 'rep',
    'pvp stats', 'dps', 'who', 'position',
    'aura', 'attackers', 'target', 'help',
    'log', 'los',
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


def _has_recent_join_greeting(
    db, group_id, bot_guid, seconds=60,
    exclude_id=None
):
    """Check if a bot was already greeted in this
    specific group via either a single bot_group_join
    (subject_guid + group_id match) or a
    bot_group_join_batch (bot_guid + group_id inside
    the extra_data JSON).

    Both event types store "group_id":NNN in
    extra_data, so we scope to the current group to
    avoid cross-group false positives.
    """
    cursor = db.cursor(dictionary=True)

    # Both queries share these conditions
    group_pattern = f'%"group_id":{group_id},%'

    # 1. Single join: subject_guid is the bot,
    #    extra_data contains the group_id
    query1 = """
        SELECT 1 FROM llm_chatter_events
        WHERE event_type = 'bot_group_join'
          AND subject_guid = %s
          AND status IN (
              'pending', 'processing', 'completed'
          )
          AND created_at > DATE_SUB(
              NOW(), INTERVAL %s SECOND
          )
          AND extra_data LIKE %s
    """
    params1 = [bot_guid, seconds, group_pattern]
    if exclude_id:
        query1 += "  AND id != %s"
        params1.append(exclude_id)
    query1 += " LIMIT 1"
    cursor.execute(query1, params1)
    if cursor.fetchone() is not None:
        return True

    # 2. Batch join: bot_guid appears inside the
    #    extra_data bots array, same group_id.
    #    Pattern "bot_guid":NNNN, is safe because
    #    bot_guid is a uint32 always followed by a
    #    comma in the JSON object.
    bot_pattern = f'%"bot_guid":{bot_guid},%'
    query2 = """
        SELECT 1 FROM llm_chatter_events
        WHERE event_type = 'bot_group_join_batch'
          AND status IN (
              'pending', 'processing', 'completed'
          )
          AND created_at > DATE_SUB(
              NOW(), INTERVAL %s SECOND
          )
          AND extra_data LIKE %s
          AND extra_data LIKE %s
    """
    params2 = [seconds, bot_pattern, group_pattern]
    if exclude_id:
        query2 += "  AND id != %s"
        params2.append(exclude_id)
    query2 += " LIMIT 1"
    cursor.execute(query2, params2)
    return cursor.fetchone() is not None


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
        _mark_event(db, event_id, 'skipped')
        return False

    # Dedup check: skip if this bot was already
    # greeted recently in this group (checks both
    # single and batch join events, scoped by
    # group_id to avoid cross-group suppression).
    if _has_recent_join_greeting(
        db, group_id, bot_guid, 60,
        exclude_id=event_id
    ):
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
        bot_zone = int(
            extra_data.get('zone', 0) or 0
        )
        bot_area = int(
            extra_data.get('area', 0) or 0
        )
        bot_map = int(
            extra_data.get('map', 0) or 0
        )
        trait_result = assign_bot_traits(
            db, group_id, bot_guid, bot_name,
            role=bot_role,
            zone=bot_zone,
            area_id=bot_area,
            map_id=bot_map,
            config=config,
            bot_class=bot_class,
            bot_race=bot_race,
        )
        traits = trait_result['traits']
        stored_tone = trait_result.get('tone')

        # 1b. Memory: start session + fetch memories
        player_guid = 0
        memories = None
        player_name_known = False
        recall_memory = None
        if int(config.get(
            'LLMChatter.Memory.Enable', 1
        )):
            p_info = get_character_info_by_name(
                db, player_name,
            )
            if p_info:
                player_guid = int(p_info['guid'])
            else:
                logger.warning(
                    "Memory disabled: player"
                    " '%s' not found"
                    " in characters table",
                    player_name,
                )
            member_data = {
                bot_guid: {
                    'name': bot_name,
                    'class': bot_class,
                    'race': bot_race,
                },
            }
            start_session(
                group_id, bot_guid,
                player_guid, time.time(),
                member_data,
            )
            if player_guid:
                memories = get_bot_memories(
                    db, bot_guid, player_guid,
                    count=3,
                )
                player_name_known = bool(memories)
                recall_chance = int(config.get(
                    'LLMChatter.Memory.RecallChance',
                    30,
                )) / 100.0
                if (
                    player_name_known
                    and random.random()
                        < recall_chance
                ):
                    recall_memory = memories[0]

                # First meeting: write a factual
                # memory so the bot always remembers
                if not player_name_known:
                    pz_mem, _ = get_player_zone(
                        db, player_name
                    )
                    zone_name = (
                        get_zone_name(pz_mem)
                        if pz_mem else None
                    )
                    if zone_name:
                        mem_text = (
                            f"Met {player_name} and"
                            f" began adventuring"
                            f" together in"
                            f" {zone_name}."
                        )
                    else:
                        mem_text = (
                            f"Met {player_name} and"
                            f" began adventuring"
                            f" together."
                        )
                    mc = db.cursor()
                    mc.execute(
                        "INSERT INTO llm_bot_memories"
                        " (bot_guid, player_guid,"
                        "  group_id, memory_type,"
                        "  memory, mood, emote,"
                        "  active, session_start)"
                        " SELECT"
                        "  %s,%s,%s,"
                        "  'first_meeting',"
                        "  %s,'warm',NULL,1,%s"
                        " WHERE NOT EXISTS ("
                        "  SELECT 1 FROM"
                        "  llm_bot_memories"
                        "  WHERE bot_guid=%s"
                        "    AND player_guid=%s"
                        "    AND memory_type="
                        "    'first_meeting')",
                        (
                            bot_guid, player_guid,
                            group_id,
                            mem_text, time.time(),
                            bot_guid, player_guid,
                        ),
                    )
                    db.commit()
                    mc.close()
                    player_name_known = True

        # 1c. Normalize this bot's trait row to the
        # player's live location so get_group_location()
        # is immediately consistent. C++ OnPlayerUpdate-
        # Zone keeps it current after this initial sync.
        pz, pm = get_player_zone(db, player_name)
        if pz or pm:
            # Only normalize zone + map (from the
            # player's characters row). Area has no
            # reliable player-side source at join
            # time — C++ OnPlayerUpdateZone sets the
            # authoritative area on the next update.
            norm_c = db.cursor()
            norm_c.execute(
                "UPDATE llm_group_bot_traits"
                " SET zone = %s, map = %s"
                " WHERE group_id = %s"
                " AND bot_guid = %s",
                (pz or 0, pm or 0,
                 group_id, bot_guid),
            )
            db.commit()

        # 1d. Dungeon entry memory: if the player
        # is in a dungeon, queue a memory for this
        # bot (player-centric via get_player_zone).
        if (
            int(config.get(
                'LLMChatter.Memory.Enable', 1
            ))
            and pm and player_guid
        ):
            dn = get_dungeon_flavor(pm)
            dng_chance = int(config.get(
                'LLMChatter.Memory'
                '.DungeonGenerationChance', 50
            ))
            if (dn and random.random() * 100
                    < dng_chance):
                try:
                    queue_memory(
                        config, group_id,
                        bot_guid, player_guid,
                        memory_type='dungeon',
                        event_context=(
                            f"Entered "
                            f"{dn.split(':')[0]}"
                        ),
                        bot_name=bot_name,
                        bot_class=bot_class,
                        bot_race=bot_race,
                    )
                except Exception:
                    logger.error(
                        "queue_memory (join) failed",
                        exc_info=True,
                    )

        # 2. Build prompt with chat history
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        members = get_group_members(db, group_id)
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        greet_zone_id, _, greet_map_id = (
            get_group_location(db, group_id)
        )
        prompt = build_bot_greeting_prompt(
            bot, traits, mode,
            chat_history=chat_hist,
            members=members,
            player_name=player_name,
            group_size=group_size,
            speaker_talent_context=speaker_talent,
            memories=memories or None,
            player_name_known=player_name_known,
            recall_memory=recall_memory,
            stored_tone=stored_tone,
            map_id=greet_map_id,
            zone_id=greet_zone_id,
        )

        # 3. Call LLM
        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        _greet_label = (
            'group_greeting_memory'
            if (memories and player_name_known)
            else 'group_greeting'
        )
        response = call_llm(
            client, prompt, config,
            max_tokens_override=max_tokens,
            context=f"grp-join:#{event_id}:{bot_name}",
            label=_greet_label,
        )

        if not response:
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
            _mark_event(db, event_id, 'skipped')
            return False
        if len(message) > 255:
            message = message[:252] + "..."


        # 5. Insert message for delivery via party
        emote = parsed.get('emote')
        insert_chat_message(
            db, bot_guid, bot_name, message,
            channel='party', delay_seconds=0,
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
            logger.error(
                "Composition comment failed",
                exc_info=True,
            )

        # 8. Pre-generate farewell message
        try:
            _generate_farewell(
                db, client, config,
                bot_name, bot_race, bot_class,
                traits, mode, group_id, bot_guid,
            )
        except Exception as e:
            logger.error(
                "Farewell generation failed "
                "bot=%s", bot_name, exc_info=True,
            )

        # 9. Mark event completed
        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            "process_group_join_event failed "
            "event=%d", event_id, exc_info=True,
        )
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_join_batch_event(
    db, client, config, event
):
    """Handle a bot_group_join_batch event.

    Multiple bots joined within the debounce window.
    Process all greetings with staggered delays, then
    ONE welcome from an existing bot (addressed to
    the whole batch), and ONE composition comment
    with full group knowledge.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_join_batch'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    group_id = int(extra_data.get('group_id', 0))
    player_name = extra_data.get('player_name', '')
    bots_raw = extra_data.get('bots', [])

    if not group_id or not isinstance(
        bots_raw, list
    ) or len(bots_raw) < 1:
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

    mode = get_chatter_mode(config)
    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))

    # Look up player_guid once for memory system
    batch_player_guid = 0
    memory_enabled = int(config.get(
        'LLMChatter.Memory.Enable', 1
    ))
    if memory_enabled and player_name:
        p_info = get_character_info_by_name(
            db, player_name,
        )
        if p_info:
            batch_player_guid = int(p_info['guid'])
        else:
            logger.warning(
                "Memory disabled: player"
                " '%s' not found"
                " in characters table",
                player_name,
            )

    greeted_bots = []
    last_bot = None
    last_delay = 0

    # Resolve player zone/map BEFORE the per-bot loop
    # so pz/pm are available for greeting prompts.
    pz, pm = get_player_zone(db, player_name)

    try:
        # --- Per-bot greetings (staggered) ---
        for idx, bot_raw in enumerate(bots_raw):
            bot_guid = int(
                bot_raw.get('bot_guid', 0)
            )
            bot_name = bot_raw.get(
                'bot_name', 'Unknown'
            )
            bot_class_id = int(
                bot_raw.get('bot_class', 0)
            )
            bot_race_id = int(
                bot_raw.get('bot_race', 0)
            )
            bot_level = int(
                bot_raw.get('bot_level', 1)
            )
            bot_role = bot_raw.get('role')

            if not bot_guid:
                continue

            # Dedup: skip if this bot was already
            # greeted recently in this group (checks
            # both single and batch join events)
            if _has_recent_join_greeting(
                db, group_id, bot_guid, 60,
                exclude_id=event_id
            ):
                continue

            bot_class = get_class_name(bot_class_id)
            bot_race = get_race_name(bot_race_id)

            bot = {
                'guid': bot_guid,
                'name': bot_name,
                'class': bot_class,
                'race': bot_race,
                'level': bot_level,
            }

            # 1. Assign traits
            # zone/map from per-bot data or
            # top-level extra_data fallback.
            # area always from top-level (real
            # player's area, set by C++).
            bot_zone = int(
                bot_raw.get(
                    'zone',
                    extra_data.get('zone', 0)
                ) or 0
            )
            bot_area = int(
                extra_data.get('area', 0) or 0
            )
            bot_map = int(
                bot_raw.get(
                    'map',
                    extra_data.get('map', 0)
                ) or 0
            )
            trait_result = assign_bot_traits(
                db, group_id, bot_guid,
                bot_name, role=bot_role,
                zone=bot_zone,
                area_id=bot_area,
                map_id=bot_map,
                config=config,
                bot_class=bot_class,
                bot_race=bot_race,
            )
            traits = trait_result['traits']
            stored_tone = trait_result.get('tone')

            # 1b. Memory: start session + fetch
            bot_memories = None
            bot_player_known = False
            bot_recall = None
            if memory_enabled:
                member_data = {
                    bot_guid: {
                        'name': bot_name,
                        'class': bot_class,
                        'race': bot_race,
                    },
                }
                start_session(
                    group_id, bot_guid,
                    batch_player_guid,
                    time.time(), member_data,
                )
                if batch_player_guid:
                    bot_memories = get_bot_memories(
                        db, bot_guid,
                        batch_player_guid,
                        count=3,
                    )
                    bot_player_known = bool(
                        bot_memories
                    )
                    recall_chance = int(config.get(
                        'LLMChatter.Memory'
                        '.RecallChance', 30,
                    )) / 100.0
                    if (
                        bot_player_known
                        and random.random()
                            < recall_chance
                    ):
                        bot_recall = bot_memories[0]

                    # First meeting: write a factual
                    # memory so the bot remembers
                    if not bot_player_known:
                        pz_mem, _ = get_player_zone(
                            db, player_name
                        )
                        zone_name = (
                            get_zone_name(pz_mem)
                            if pz_mem else None
                        )
                        if zone_name:
                            mem_text = (
                                f"Met {player_name}"
                                f" and began"
                                f" adventuring"
                                f" together in"
                                f" {zone_name}."
                            )
                        else:
                            mem_text = (
                                f"Met {player_name}"
                                f" and began"
                                f" adventuring"
                                f" together."
                            )
                        mc = db.cursor()
                        mc.execute(
                            "INSERT INTO"
                            " llm_bot_memories"
                            " (bot_guid,"
                            "  player_guid,"
                            "  group_id,"
                            "  memory_type,"
                            "  memory, mood,"
                            "  emote, active,"
                            "  session_start)"
                            " SELECT"
                            "  %s,%s,%s,"
                            "  'first_meeting',"
                            "  %s,'warm',"
                            "  NULL,1,%s"
                            " WHERE NOT EXISTS ("
                            "  SELECT 1 FROM"
                            "  llm_bot_memories"
                            "  WHERE bot_guid=%s"
                            "    AND player_guid=%s"
                            "    AND memory_type="
                            "    'first_meeting')",
                            (
                                bot_guid,
                                batch_player_guid,
                                group_id,
                                mem_text,
                                time.time(),
                                bot_guid,
                                batch_player_guid,
                            ),
                        )
                        db.commit()
                        mc.close()
                        bot_player_known = True

            # 2. Build greeting prompt
            history = _get_recent_chat(
                db, group_id
            )
            chat_hist = format_chat_history(history)
            members = get_group_members(
                db, group_id
            )
            speaker_talent = _maybe_talent_context(
                config, db, bot_guid,
                bot['class'], bot_name,
            )
            # BG context: if extra_data contains
            # bg_type, build a bg_context dict for
            # the prompt builder instead of zone/
            # dungeon flavor.
            _bg_ctx = None
            if extra_data.get('bg_type'):
                _bg_ctx = {
                    'bg_type_id': int(
                        extra_data.get(
                            'bg_type_id', 0)),
                    'bg_type': extra_data.get(
                        'bg_type', ''),
                    'team': extra_data.get(
                        'team', ''),
                }
                sa = extra_data.get(
                    'score_alliance')
                sh = extra_data.get(
                    'score_horde')
                if sa is not None:
                    _bg_ctx['score_alliance'] = (
                        int(sa))
                if sh is not None:
                    _bg_ctx['score_horde'] = (
                        int(sh))

            prompt = build_bot_greeting_prompt(
                bot, traits, mode,
                chat_history=chat_hist,
                members=members,
                player_name=player_name,
                group_size=len(bots_raw) + 1,
                speaker_talent_context=speaker_talent,
                memories=bot_memories or None,
                player_name_known=bot_player_known,
                recall_memory=bot_recall,
                stored_tone=stored_tone,
                map_id=pm or 0,
                zone_id=pz or 0,
                bg_context=_bg_ctx,
            )

            # 3. Call LLM
            _greet_label = (
                'group_greeting_memory'
                if (bot_memories and bot_player_known)
                else 'group_greeting'
            )
            response = call_llm(
                client, prompt, config,
                max_tokens_override=max_tokens,
                context=(
                    f"batch-join:#{event_id}"
                    f":{bot_name}"
                ),
                label=_greet_label,
            )
            if not response:
                continue

            # 4. Clean up + insert
            parsed = parse_single_response(response)
            message = strip_speaker_prefix(
                parsed['message'], bot_name
            )
            message = cleanup_message(
                message,
                action=parsed.get('action')
            )
            if not message:
                continue
            if len(message) > 255:
                message = message[:252] + "..."

            # Stagger: 0s, 2s, 4s, 6s ...
            delay = idx * 2
            last_delay = delay

            emote = parsed.get('emote')
            insert_chat_message(
                db, bot_guid, bot_name, message,
                channel='party',
                delay_seconds=delay,
                event_id=event_id,
                emote=emote,
            )

            _store_chat(
                db, group_id, bot_guid,
                bot_name, True, message
            )


            greeted_bots.append(bot)
            last_bot = {
                'bot': bot,
                'traits': traits,
                'bot_class': bot_class,
                'bot_race': bot_race,
            }

            # 5. Pre-generate farewell
            try:
                _generate_farewell(
                    db, client, config,
                    bot_name, bot_race, bot_class,
                    traits, mode,
                    group_id, bot_guid,
                )
            except Exception as e:
                logger.error(
                    "Farewell generation failed "
                    "bot=%s", bot_name,
                    exc_info=True,
                )

        if not greeted_bots:
            _mark_event(db, event_id, 'skipped')
            return False

        # Normalize all trait rows to the player's
        # live location so get_group_location() is
        # immediately consistent. C++ OnPlayerUpdate-
        # Zone keeps it current after this initial
        # sync.
        pz, pm = get_player_zone(db, player_name)
        if pz or pm:
            # Only normalize zone + map. Area has
            # no reliable player-side source at
            # join time — C++ OnPlayerUpdateZone
            # sets authoritative area on next update.
            norm_c = db.cursor()
            norm_c.execute(
                "UPDATE llm_group_bot_traits"
                " SET zone = %s, map = %s"
                " WHERE group_id = %s",
                (pz or 0, pm or 0, group_id),
            )
            db.commit()

        # Dungeon entry memory: if the player is
        # in a dungeon/raid, queue a memory for
        # each bot. Player-centric: pm comes from
        # get_player_zone() (source of truth).
        if memory_enabled and pm:
            dungeon_name = get_dungeon_flavor(pm)
            dng_chance = int(config.get(
                'LLMChatter.Memory'
                '.DungeonGenerationChance', 50
            ))
            if dungeon_name:
                dungeon_name = (
                    dungeon_name.split(':')[0]
                )
                for b in greeted_bots:
                    if (random.random() * 100
                            >= dng_chance):
                        continue
                    try:
                        queue_memory(
                            config, group_id,
                            b['guid'],
                            batch_player_guid,
                            memory_type='dungeon',
                            event_context=(
                                f"Entered "
                                f"{dungeon_name}"
                            ),
                            bot_name=b['name'],
                            bot_class=b.get(
                                'class', ''
                            ),
                            bot_race=b.get(
                                'race', ''
                            ),
                        )
                    except Exception:
                        logger.error(
                            "queue_memory (batch) "
                            "failed",
                            exc_info=True,
                        )

        # --- ONE welcome from existing bot ---
        new_names = [
            b['name'] for b in greeted_bots
        ]
        new_guids = {
            b['guid'] for b in greeted_bots
        }

        # Find an existing bot NOT in the batch
        wb = _find_existing_welcomer(
            db, group_id, new_guids
        )
        if wb:
            welcome_delay = last_delay + 3
            _batch_welcome(
                db, client, config, wb,
                new_names, group_id, mode,
                event_id, welcome_delay
            )

        # --- ONE composition comment ---
        # Delay after welcome (or last greeting if
        # no welcomer was found)
        comp_delay = last_delay + 5
        if wb:
            comp_delay = last_delay + 6

        if last_bot:
            try:
                _maybe_comment_on_composition(
                    db, client, config, group_id,
                    last_bot['bot'],
                    last_bot['traits'],
                    mode, event_id,
                    player_name=player_name,
                    delay_seconds=comp_delay,
                )
            except Exception as e:
                logger.error(
                    "Batch composition comment "
                    "failed", exc_info=True,
                )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            "process_group_join_batch_event failed "
            "event=%d", event_id, exc_info=True,
        )
        _mark_event(db, event_id, 'skipped')
        return False


def _find_existing_welcomer(
    db, group_id, exclude_guids
):
    """Find an existing bot in the group who is NOT
    in the batch, to deliver the welcome message.
    Returns dict with guid, name, traits or None.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT bot_guid, bot_name,
               trait1, trait2, trait3
        FROM llm_group_bot_traits
        WHERE group_id = %s
    """, (group_id,))
    rows = cursor.fetchall()

    candidates = []
    for row in rows:
        guid = row['bot_guid']
        if guid not in exclude_guids:
            candidates.append({
                'guid': guid,
                'name': row['bot_name'],
                'traits': [
                    row['trait1'],
                    row['trait2'],
                    row['trait3'],
                ],
            })

    if not candidates:
        return None
    return random.choice(candidates)


def _batch_welcome(
    db, client, config, wb_info,
    new_names, group_id, mode,
    event_id, delay
):
    """Generate a welcome message from an existing
    bot addressed to the whole batch of newcomers.
    """
    wb_guid = wb_info['guid']
    wb_name = wb_info['name']
    wb_traits = wb_info['traits']
    wb_tone = wb_info.get('tone')

    # Get class/race/level for the welcoming bot
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (wb_guid,))
    char_row = cursor.fetchone()
    if not char_row:
        return

    wb = {
        'guid': wb_guid,
        'name': wb_name,
        'class': get_class_name(char_row['class']),
        'race': get_race_name(char_row['race']),
        'level': char_row['level'],
    }

    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)
    members = get_group_members(db, group_id)

    speaker_talent = _maybe_talent_context(
        config, db, wb_guid,
        wb['class'], wb_name,
    )
    prompt = build_batch_welcome_prompt(
        wb, wb_traits, new_names, mode,
        chat_history=chat_hist,
        members=members,
        speaker_talent_context=speaker_talent,
        stored_tone=wb_tone,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"batch-welcome:{wb_name}",
        label='group_welcome',
    )
    if not response:
        return

    parsed = parse_single_response(response)
    msg = strip_speaker_prefix(
        parsed['message'], wb_name
    )
    msg = cleanup_message(
        msg, action=parsed.get('action')
    )
    if not msg:
        return
    if len(msg) > 255:
        msg = msg[:252] + "..."


    emote = parsed.get('emote')
    insert_chat_message(
        db, wb_guid, wb_name, msg,
        channel='party',
        delay_seconds=delay,
        event_id=event_id,
        sequence=1,
        emote=emote,
    )

    _store_chat(
        db, group_id, wb_guid,
        wb_name, True, msg
    )








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

    # Parse and resolve WoW links in message
    # Keep raw message for detect_item_links
    raw_player_message = player_message
    link_context = ""
    player_message, link_context = (
        resolve_and_format_links(
            config, player_message
        )
    )

    # Skip playerbot commands (follow, stay, etc.)
    if _is_playerbot_command(player_message):
        _mark_event(db, event_id, 'skipped')
        return False

    # Get all bots in group for name matching
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT bot_guid, bot_name,
               trait1, trait2, trait3, tone
        FROM llm_group_bot_traits
        WHERE group_id = %s
    """, (group_id,))
    all_bots = cursor.fetchall()

    if not all_bots:
        _mark_event(db, event_id, 'skipped')
        return False

    # Fetch chat history early for LLM bot matching
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)

    # Prefer addressed bot, else random
    bot_row = None
    all_names = [b['bot_name'] for b in all_bots]
    addr_result = find_addressed_bot(
        player_message, all_names,
        client=client, config=config,
        chat_history=chat_hist
    )
    addressed = addr_result.get('bot')
    multi_addressed = addr_result.get(
        'multi_addressed', False
    )
    if addressed:
        for b in all_bots:
            if b['bot_name'] == addressed:
                bot_row = b
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
    stored_tone = bot_row.get('tone')

    # Get bot class/race from characters table
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


    # Get zone/area/map from bot traits (single
    # source of truth, updated by C++ in real-time)
    zone_id, area_id, map_id = get_group_location(
        db, group_id)

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
        items_info = []
        linked_items = detect_item_links(
            raw_player_message
        )
        if linked_items:
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
                logger.error(
                    "Item link query failed",
                    exc_info=True,
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

        # -- Conversation vs single reply --
        # Roll for multi-bot conversation when
        # >=2 bots are available. Mutual exclusion:
        # if conversation fires, skip second bot.
        used_conversation = False
        num_bots = len(all_bots)
        conv_chance = int(config.get(
            'LLMChatter.GroupChatter'
            '.PlayerMsgConversationChance',
            '30',
        ))
        # Dynamic scaling: divide by bot count,
        # floor at 1% when configured > 0
        eff_conv_chance = (
            max(conv_chance // max(num_bots, 1), 1)
            if conv_chance > 0 else 0
        )

        force_conv = (
            multi_addressed and num_bots >= 2
        )
        rng_conv = (
            not force_conv
            and num_bots >= 2
            and eff_conv_chance > 0
            and random.randint(1, 100)
                <= eff_conv_chance
        )

        if force_conv or rng_conv:
            trigger = (
                "multi_addressed"
                if force_conv else
                f"RNG({eff_conv_chance}%)"
            )
            # Pass addressed bot with traits
            # for reuse as first speaker
            addr_bot = {
                'guid': bot_guid,
                'name': bot_name,
                'class': bot['class'],
                'race': bot['race'],
                'level': bot['level'],
                'trait1': bot_row['trait1'],
                'trait2': bot_row['trait2'],
                'trait3': bot_row['trait3'],
            }
            try:
                conv_ok = (
                    execute_player_msg_conversation(
                        db, client, config,
                        event_id, group_id,
                        addr_bot, all_bots,
                        player_name,
                        player_message, mode,
                        chat_hist, members,
                        item_context=item_context,
                        link_context=link_context,
                        items_info=items_info,
                        zone_id=zone_id,
                        area_id=area_id,
                        map_id=map_id,
                    )
                )
                if conv_ok:
                    used_conversation = True
                    _mark_event(
                        db, event_id,
                        'completed',
                    )
                    return True
                # Conversation failed, fall
                # through to single-bot path
            except Exception as ec:
                logger.error(
                    "Player msg conversation "
                    "failed, falling through",
                    exc_info=True,
                )

        # -- Single-bot reply path --
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        target_talent = None
        player_info = get_character_info_by_name(
            db, player_name,
        )
        if player_info:
            target_talent = _maybe_talent_context(
                config, db,
                player_info['guid'],
                get_class_name(
                    player_info['class']
                ),
                player_name,
                perspective='target',
            )

        # Fetch memories for player message
        # response — RNG-gated like idle recall
        msg_memories = None
        memory_enabled = int(config.get(
            'LLMChatter.Memory.Enable', 1
        ))
        if memory_enabled and player_info:
            recall_chance = int(config.get(
                'LLMChatter.Memory'
                '.IdleRecallChance', 30,
            )) / 100.0
            player_guid = int(
                player_info['guid']
            )
            if (
                player_guid
                and random.random()
                    < recall_chance
            ):
                msg_memories = get_bot_memories(
                    db, bot_guid,
                    player_guid, count=3,
                    exclude_first_meeting=True,
                )
                if not msg_memories:
                    msg_memories = None

        prompt = build_player_response_prompt(
            bot, traits, player_name,
            player_message, mode,
            chat_history=chat_hist,
            members=members,
            item_context=item_context,
            link_context=link_context,
            speaker_talent_context=speaker_talent,
            target_talent_context=target_talent,
            zone_id=zone_id,
            area_id=area_id,
            map_id=map_id,
            stored_tone=stored_tone,
            memories=msg_memories,
        )

        max_tokens = pick_random_max_tokens(config)
        if msg_memories:
            max_tokens = max(max_tokens, 250)
        _pmsg_label = (
            'group_player_msg_memory'
            if msg_memories
            else 'group_player_msg'
        )
        _dflav_pmsg = get_dungeon_flavor(map_id)
        pmsg_meta = build_zone_metadata(
            zone_name=(
                get_zone_name(zone_id) or ''
            ),
            zone_flavor=(
                get_zone_flavor(zone_id) or ''
            ),
            subzone_name=(
                get_subzone_name(
                    zone_id, area_id
                ) or ''
            ),
            subzone_lore=(
                get_subzone_lore(
                    zone_id, area_id
                ) or ''
            ),
            dungeon_name=(
                _dflav_pmsg.split(':')[0].strip()
                if _dflav_pmsg else ''
            ),
            dungeon_flavor=_dflav_pmsg or '',
        )
        response = call_llm(
            client, prompt, config,
            max_tokens_override=max_tokens,
            context=(
                f"grp-msg:#{event_id}"
                f":{bot_name}"
            ),
            label=_pmsg_label,
            metadata=pmsg_meta or None,
        )

        if not response:
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
            _mark_event(db, event_id, 'skipped')
            return False
        if len(message) > 255:
            message = message[:252] + "..."


        emote = parsed.get('emote')
        reply_delay = calculate_dynamic_delay(
            len(message), config,
            prev_message_length=len(
                player_message
            ),
            responsive=True,
        )
        insert_chat_message(
            db, bot_guid, bot_name, message,
            channel='party',
            delay_seconds=reply_delay,
            event_id=event_id, emote=emote,
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        # Second bot chance — MUTUAL EXCLUSION:
        # skip if conversation path was used
        if not used_conversation:
            second_chance = int(config.get(
                'LLMChatter.GroupChatter'
                '.PlayerMsgSecondBotChance',
                '25',
            ))
            if random.randint(1, 100) <= (
                second_chance
            ):
                try:
                    _try_second_bot_response(
                        db, client, config,
                        group_id,
                        bot_guid, player_name,
                        player_message, mode,
                        event_id,
                        link_context=link_context,
                        items_info=items_info,
                    )
                except Exception as e2:
                    logger.error(
                        "Second bot response failed",
                        exc_info=True,
                    )

        # Memory: queue player_message memories
        try:
            if int(config.get(
                'LLMChatter.Memory.Enable', 1
            )):
                _maybe_queue_player_msg_memory(
                    config, group_id,
                    player_message, all_bots,
                )
        except Exception:
            logger.error(
                "player_message memory failed",
                exc_info=True,
            )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception as e:
        logger.error(
            "process_group_player_msg_event failed "
            "event=%d", event_id, exc_info=True,
        )
        _mark_event(db, event_id, 'skipped')
        return False


def _maybe_queue_player_msg_memory(
    config, group_id, player_message, all_bots,
):
    """Queue player_message memory generation for
    random bots in the group.

    Eligibility filters:
    - Not a playerbot command
    - Not over max length
    - Session msg_count < max per session
    - Not whitespace-only or URL-only
    """
    max_len = int(config.get(
        'LLMChatter.Memory.PlayerMsgMaxLength', 200
    ))
    max_per_session = int(config.get(
        'LLMChatter.Memory.PlayerMsgMaxPerSession', 3
    ))

    msg = player_message.strip()
    if not msg:
        return
    if len(msg) > max_len:
        return
    if _is_playerbot_command(msg):
        return
    # Skip URL-only messages
    import re as _re
    if _re.match(
        r'^https?://\S+$', msg, _re.IGNORECASE
    ):
        return

    lock = _get_group_lock(group_id, create=False)
    if lock is None:
        return
    with lock:
        session = _active_sessions.get(group_id)
        if not session:
            return
        if session["msg_count"] >= max_per_session:
            return
        player_guid = session["player_guid"]
        bots_in_session = list(session["bots"])
        # Guard before incrementing: rehydrated
        # sessions have player_guid=0 and cannot
        # generate memories — don't burn quota
        if not bots_in_session or not player_guid:
            return
        # Increment atomically inside the lock so
        # concurrent player messages can't both
        # slip past the max_per_session check
        session["msg_count"] += 1

    # Select 1-min(4, bot_count) random bots
    num_to_pick = min(
        random.randint(1, 4),
        len(bots_in_session),
    )
    picked = random.sample(
        bots_in_session, num_to_pick
    )

    # Find bot data for context
    bot_map = {}
    for b in all_bots:
        bg = int(b.get('bot_guid', 0))
        if bg:
            bot_map[bg] = b

    for bg in picked:
        bd = bot_map.get(bg, {})
        try:
            queue_memory(
                config, group_id, bg, player_guid,
                memory_type='player_message',
                event_context=(
                    f"Player said: {msg[:100]}"
                ),
                bot_name=bd.get('bot_name', ''),
                bot_class=bd.get('class', ''),
                bot_race=bd.get('race', ''),
            )
        except Exception:
            logger.error(
                "player_message memory failed",
                exc_info=True,
            )
























# ============================================================
# STATE-TRIGGERED CALLOUT PROCESSORS (Phase 2C)
# ============================================================






def _try_second_bot_response(
    db, client, config, group_id,
    first_bot_guid, player_name,
    player_message, mode, event_id,
    link_context="", items_info=None,
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
    bot2_tone = second.get('tone')

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

    bot2_item_context = ""
    if items_info:
        bot2_item_context = format_item_context(
            items_info, bot2['class']
        )
    speaker_talent = _maybe_talent_context(
        config, db, bot2_guid,
        bot2['class'], bot2_name,
    )
    target_talent = None
    player_info = get_character_info_by_name(
        db, player_name,
    )
    if player_info:
        target_talent = _maybe_talent_context(
            config, db,
            player_info['guid'],
            get_class_name(
                player_info['class']
            ),
            player_name,
            perspective='target',
        )
    prompt = build_player_response_prompt(
        bot2, bot2_traits, player_name,
        player_message, mode,
        chat_history=chat_hist,
        members=members,
        link_context=link_context,
        item_context=bot2_item_context,
        speaker_talent_context=speaker_talent,
        target_talent_context=target_talent,
        zone_id=zone_id,
        area_id=area_id,
        stored_tone=bot2_tone,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"2nd-reply:{bot2_name}",
        label='group_player_msg',
    )
    if not response:
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


    emote = parsed.get('emote')
    bot2_delay = calculate_dynamic_delay(
        len(msg2), config,
        prev_message_length=len(
            player_message
        ),
        responsive=True,
    ) + 2  # offset after first bot
    insert_chat_message(
        db, bot2_guid, bot2_name, msg2,
        channel='party',
        delay_seconds=bot2_delay,
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
        return

    wb_guid = other['guid']
    wb_name = other['name']
    wb_traits = other['traits']
    wb_tone = other.get('tone')

    # Get class/race/level for the welcoming bot
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
    """, (wb_guid,))
    char_row = cursor.fetchone()
    if not char_row:
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

    speaker_talent = _maybe_talent_context(
        config, db, wb_guid,
        wb['class'], wb_name,
    )
    prompt = build_bot_welcome_prompt(
        wb, wb_traits, new_bot_name, mode,
        chat_history=chat_hist,
        members=members,
        speaker_talent_context=speaker_talent,
        stored_tone=wb_tone,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"welcome:{wb_name}",
        label='group_welcome',
    )
    if not response:
        return

    parsed = parse_single_response(response)
    msg = strip_speaker_prefix(
        parsed['message'], wb_name
    )
    msg = cleanup_message(
        msg, action=parsed.get('action')
    )
    if not msg:
        return
    if len(msg) > 255:
        msg = msg[:252] + "..."


    # Insert with 5s delay (greeting is at 2s)
    emote = parsed.get('emote')
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
    speaker_talent_context=None,
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
        f"{rp_context}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"\nYou just joined a group"
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
    player_name="",
    delay_seconds=8
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
            logger.error(
                "Player class lookup failed",
                exc_info=True,
            )
    if not role_summary or not role_info:
        return
    if role_info.get('total', 0) < 2:
        return

    speaker_talent = _maybe_talent_context(
        config, db, bot['guid'],
        bot['class'], bot['name'],
    )
    prompt = _build_composition_comment_prompt(
        bot, traits, mode, role_summary,
        role_info, player_name,
        player_class=player_class,
        speaker_talent_context=speaker_talent,
    )

    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=min(max_tokens, 100),
        context=f"comp-comment:{bot['name']}",
        label='group_composition',
    )
    if not response:
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


    emote = parsed.get('emote')
    insert_chat_message(
        db, bot['guid'], bot['name'], msg,
        channel='party',
        delay_seconds=delay_seconds,
        event_id=event_id, sequence=2,
        emote=emote,
    )

    _store_chat(
        db, group_id, bot['guid'],
        bot['name'], True, msg
    )
















# ============================================================
# STATE-TRIGGERED CALLOUT PROMPTS (Phase 2C)
# ============================================================






# ============================================================
# HELPERS
# ============================================================


# ============================================================
# CHAT HISTORY
# ============================================================








# get_group_player_name moved to chatter_group_state
# (imported above) to avoid circular imports with
# chatter_group_handlers.


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
    speaker_talent_context=None,
    area_id=0,
    stored_tone=None,
    memories=None,
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

    # --------------------------------------------------
    # LEAN MEMORY PATH — when memories are present,
    # strip away distracting content and make the
    # memory the central purpose of the message.
    # --------------------------------------------------
    if memories:
        sanitized = [
            sanitize_memory_for_prompt(m)
            for m in memories
        ]
        sanitized = [s for s in sanitized if s]
        if sanitized:
            p_label = (
                player_name
                or 'your party leader'
            )
            mem_lines = '\n'.join(
                f"  - {m}" for m in sanitized
            )
            prompt = (
                f"You are {bot['name']}, a level "
                f"{bot['level']} {bot['race']} "
                f"{bot['class']}.\n"
                f"Your personality: {trait_str}\n"
            )
            if speaker_talent_context:
                prompt += (
                    f"{speaker_talent_context}\n"
                )
            prompt += (
                f"\n<past_memories>\n"
                f"Your memories from past "
                f"adventures with {p_label}:\n"
                f"{mem_lines}\n"
                f"Reference one of these memories "
                f"clearly — mention the place, "
                f"creature, or moment by name so "
                f"{p_label} would recognise the "
                f"callback. Keep it natural "
                f"(not a full retelling).\n"
                f"</past_memories>\n\n"
                f"Say something in party chat that "
                f"references one of your memories "
                f"above. The memory should be the "
                f"main point of your message, not "
                f"a side note.\n"
            )
            if chat_history:
                prompt += (
                    f"\nRecent party chat "
                    f"(for context only):"
                    f"{chat_history}\n"
                )
            prompt += (
                f"\n{_pick_length_hint(mode)}\n"
                f"Rules:\n"
                f"- No quotes, no emojis\n"
                f"- The memory reference must be "
                f"recognisable\n"
                f"- Don't repeat themes from "
                f"recent chat\n"
                f"- NEVER claim to have killed a "
                f"creature, looted an item, "
                f"completed a quest, or made "
                f"a trade"
            )
            anti_rep = build_anti_repetition_context(
                recent_messages
            )
            if anti_rep:
                prompt += f"\n{anti_rep}"
            return append_json_instruction(
                prompt, allow_action
            )
    # memories were empty or all sanitized away —
    # fall through to the normal full prompt below.

    # --------------------------------------------------
    # NORMAL PATH — no memories, full context prompt
    # --------------------------------------------------
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    # Detect dungeon/BG before topic selection so we
    # can skip AMBIENT topics when inside an instance
    # or battleground.
    dungeon_flav_early = get_dungeon_flavor(map_id)
    in_dungeon_early = dungeon_flav_early is not None
    in_bg_early = map_id in BG_MAP_NAMES
    if in_dungeon_early or in_bg_early:
        topic = None  # instance/BG context drives tone
    else:
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        topic = random.choice(topic_pool)

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
    bg_name = BG_MAP_NAMES.get(map_id)
    if in_dungeon:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )
        if dungeon_bosses:
            boss_list = ', '.join(dungeon_bosses[:6])
            rp_context += f"\nBosses here: {boss_list}"
    elif bg_name:
        rp_context += f"\nBattleground: {bg_name}"
    else:
        zone_name = get_zone_name(zone_id)
        if is_rp and zone_flav:
            rp_context += (
                f"\nZone context: {zone_flav}"
            )
        elif zone_name:
            rp_context += f"\nZone: {zone_name}"
        subzone_lore = get_subzone_lore(
            zone_id, area_id
        )
        if is_rp and subzone_lore:
            rp_context += (
                f"\nCurrent subzone: {subzone_lore}"
            )
        else:
            subzone_name = get_subzone_name(
                zone_id, area_id
            )
            if subzone_name:
                rp_context += (
                    f"\nSubzone: {subzone_name}"
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

    # Dead bot awareness — let the LLM know so it
    # can produce fitting dialogue (gallows humor,
    # pleas for a rez, floor commentary, etc.)
    if bot.get('is_dead'):
        rp_context += (
            "\nYou are DEAD — lying on the ground "
            "as a ghost. Speak accordingly: dark "
            "humor, complain about the cold floor, "
            "ask for a resurrection, or comment on "
            "the view from down here. Do NOT pretend "
            "you are alive or give tactical advice."
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
            "Say something in party chat as a "
            "regular WoW player — could be any age, "
            "mature and grounded. Talk about the "
            "game naturally, as a player not a "
            "character. Reference zones, classes, "
            "abilities, and creatures by name."
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
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"

    party_ctx = (
        f"You're in a party, currently {topic}."
        if topic else
        "You're in a party."
    )
    prompt += (
        f"{rp_context}\n\n"
        f"{party_ctx}\n"
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
    speaker_talent_context=None,
    area_id=0,
    memories_map=None,
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
    msg_count = 4

    # --------------------------------------------------
    # LEAN MEMORY PATH — when any bot has memories,
    # strip away distracting content and make the
    # memories the central purpose of the exchange.
    # --------------------------------------------------
    if memories_map:
        p_label = player_name or 'the player'
        # Sanitize all bot memories up front
        has_any_memories = False
        bot_mem_blocks = {}
        for b in bots:
            raw = memories_map.get(b['guid'])
            if not raw:
                continue
            sanitized = [
                sanitize_memory_for_prompt(m)
                for m in raw
            ]
            sanitized = [
                m for m in sanitized if m
            ]
            if sanitized:
                bot_mem_blocks[b['name']] = (
                    sanitized
                )
                has_any_memories = True

        if has_any_memories:
            parts = []
            if num_bots == 2:
                speaker_desc = "two"
            elif num_bots == 3:
                speaker_desc = "three"
            else:
                speaker_desc = "four"

            parts.append(
                f"Generate a short party chat "
                f"exchange between {speaker_desc} "
                f"adventurers sharing memories "
                f"from past adventures with "
                f"{p_label}."
            )

            # Compact bot identities — no worldview
            parts.append(
                f"Speakers: "
                f"{', '.join(bot_names)}"
            )
            for bot in bots:
                t = traits_map.get(
                    bot['name'], []
                )
                trait_str = (
                    ', '.join(t)
                    if t else 'average'
                )
                dead_tag = (
                    " [DEAD]"
                    if bot.get('is_dead') else ""
                )
                parts.append(
                    f"{bot['name']} is a level "
                    f"{bot['level']} "
                    f"{bot['race']} "
                    f"{bot['class']} "
                    f"(personality: {trait_str})"
                    f"{dead_tag}"
                )

            # Per-bot memory blocks
            for b in bots:
                mems = bot_mem_blocks.get(
                    b['name']
                )
                if mems:
                    mem_lines = '\n'.join(
                        f"  - {m}" for m in mems
                    )
                    parts.append(
                        f"<past_memories "
                        f"bot=\"{b['name']}\">\n"
                        f"{b['name']}'s memories "
                        f"with {p_label}:\n"
                        f"{mem_lines}\n"
                        f"Have {b['name']} "
                        f"reference one of these "
                        f"memories clearly — "
                        f"mention the place, "
                        f"creature, or moment by "
                        f"name so {p_label} "
                        f"recognises the callback."
                        f"\n</past_memories>"
                    )
                else:
                    parts.append(
                        f"{b['name']} has no "
                        f"memories — react to what "
                        f"others share."
                    )

            parts.append(
                "The memories should be the main "
                "point of the conversation, not "
                "side notes. Bots with memories "
                "share them; bots without react "
                "naturally."
            )

            if chat_history:
                parts.append(
                    f"Recent party chat "
                    f"(for context only):"
                    f"{chat_history}"
                )

            length_hint = _pick_length_hint(mode)
            parts.append(
                f"Rules: No quotes, no emojis; "
                f"{length_hint}; "
                f"don't repeat themes from "
                f"recent chat"
            )

            anti_rep = (
                build_anti_repetition_context(
                    recent_messages
                )
            )
            if anti_rep:
                parts.append(anti_rep)

            return append_conversation_json_instruction(
                '\n'.join(parts),
                bot_names,
                msg_count,
                allow_action=allow_action,
            )
    # memories_map was empty or all sanitized away
    # — fall through to the normal full prompt.

    # --------------------------------------------------
    # NORMAL PATH — no memories, full context prompt
    # --------------------------------------------------
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

    # Dungeon/BG flavor takes priority over zone flavor
    dungeon_flav = get_dungeon_flavor(map_id)
    zone_flav = get_zone_flavor(zone_id)
    in_dungeon = dungeon_flav is not None
    bg_name = BG_MAP_NAMES.get(map_id)
    if in_dungeon:
        parts.append(
            f"Dungeon context: {dungeon_flav}"
        )
        if dungeon_bosses:
            boss_list = ', '.join(dungeon_bosses[:6])
            parts.append(f"Bosses here: {boss_list}")
    elif bg_name:
        parts.append(f"Battleground: {bg_name}")
    else:
        zone_name = get_zone_name(zone_id)
        if is_rp and zone_flav:
            parts.append(f"Zone context: {zone_flav}")
        elif zone_name:
            parts.append(f"Zone: {zone_name}")
        subzone_lore = get_subzone_lore(
            zone_id, area_id
        )
        if is_rp and subzone_lore:
            parts.append(
                f"Current subzone: {subzone_lore}"
            )
        else:
            subzone_name = get_subzone_name(
                zone_id, area_id
            )
            if subzone_name:
                parts.append(
                    f"Subzone: {subzone_name}"
                )

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

    # Precompute shared race context once per unique
    # race to avoid duplicating worldview/lore for
    # same-race bots.
    shared_race_cache = {}
    if is_rp:
        race_counts = {}
        for bot in bots:
            r = bot.get('race', '')
            if r:
                race_counts[r] = (
                    race_counts.get(r, 0) + 1
                )
        for race, count in race_counts.items():
            _, sr, _ = build_race_class_context_parts(
                race, '', race_count=count
            )
            shared_race_cache[race] = sr

    # Speakers with traits and class/race
    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    seen_races = set()
    seen_classes = set()
    for bot in bots:
        t = traits_map.get(bot['name'], [])
        trait_str = (
            ', '.join(t) if t else 'average'
        )
        dead_tag = (
            " [DEAD - lying on the ground]"
            if bot.get('is_dead') else ""
        )
        parts.append(
            f"{bot['name']} is a level "
            f"{bot['level']} {bot['race']} "
            f"{bot['class']} "
            f"(personality: {trait_str})"
            f"{dead_tag}"
        )
        if is_rp:
            race = bot.get('race', '')
            cls = bot.get('class', '')
            role = bot.get('role', '') or ''
            per_bot, _, shared_class = (
                build_race_class_context_parts(
                    race, cls,
                    actual_role=role or None,
                )
            )
            if per_bot:
                parts.append(f"  {per_bot}")
            if race not in seen_races:
                sr = shared_race_cache.get(race, '')
                if sr:
                    parts.append(f"  {sr}")
                seen_races.add(race)
            # Resolve role the same way
            # build_race_class_context_parts does
            # (actual_role or CLASS_ROLE_MAP fallback)
            # so the dedup key matches the actual
            # shared_class string that was emitted.
            resolved_role = (
                role or CLASS_ROLE_MAP.get(cls) or ''
            )
            cls_role_key = (cls, resolved_role)
            if cls_role_key not in seen_classes:
                if shared_class:
                    parts.append(f"  {shared_class}")
                seen_classes.add(cls_role_key)

    if speaker_talent_context:
        parts.append(speaker_talent_context)

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

    # Topic (skipped in dungeons — dungeon context
    # already grounds the conversation)
    if topic:
        parts.append(f"Topic: {topic}")

    # Tone and twist
    tone = pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    parts.append(f"Overall tone: {tone}")
    if twist:
        parts.append(f"Creative twist: {twist}")

    # Fixed message count keeps idle conversation
    # volume constant regardless of group size.
    # Bots still all participate via round-robin
    # speaker assignment (bot_names[i % num_bots]).
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
            f"OOC; {length_hint}."
        )
    else:
        parts.append(
            "Guidelines: Sound like regular WoW "
            "players chatting — could be any age, "
            "mature and grounded; talk about the "
            "game as players, not as characters; "
            f"{length_hint}."
        )

    parts.append(
        "Do NOT mention quests, quest rewards, "
        "items, spells, or trade. "
        "NEVER claim to have just killed a "
        "creature (past exploits is fine), "
        "just looted an item (you can mention "
        "items looted in the past), just "
        "completed a quest (you can mention "
        "quests completed in the past), "
        "or made a trade. "
        "Stick to observation, opinion, banter, "
        "occasional philosophical consideration. "
        "Don't repeat jokes or themes already "
        "said in chat."
    )
    parts.append(
        "STRICT: Each message MUST be under "
        "120 characters. Short is better."
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

    return append_conversation_json_instruction(
        '\n'.join(parts),
        bot_names,
        msg_count,
        allow_action=allow_action,
    )


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

    _dbg = config.get(
        'LLMChatter.DebugLog', '0') == '1'
    if _dbg:
        logger.info(
            f"[DEBUG] idle check: "
            f"{len(groups)} group(s), "
            f"picked group {group_id}")

    # Quick map lookup from traits for raid boost
    # (before cooldown check so we can halve it)
    _pre_map = None
    try:
        cursor.execute(
            "SELECT map FROM llm_group_bot_traits "
            "WHERE group_id = %s LIMIT 1",
            (group_id,),
        )
        _pre_row = cursor.fetchone()
        if _pre_row:
            _pre_map = int(
                _pre_row.get('map') or 0)
    except Exception:
        pass

    # Raid instance: use dedicated idle chance/cooldown
    _in_raid = (
        _pre_map is not None
        and _pre_map in RAID_MAP_IDS
    )
    if _in_raid:
        idle_chance = int(config.get(
            'LLMChatter.RaidChatter.IdleChance',
            30))
        idle_cooldown = int(config.get(
            'LLMChatter.RaidChatter.IdleCooldown',
            20))
        if _dbg:
            logger.info(
                "[DEBUG] idle: raid config "
                "active (chance=%d%%, cd=%ds)",
                idle_chance, idle_cooldown,
            )

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
            if _dbg:
                logger.info(
                    f"[DEBUG] idle: cooldown "
                    f"({now - last_idle:.0f}s / "
                    f"{idle_cooldown}s)")
            return False
        if group_id in _idle_inflight:
            if _dbg:
                logger.info(
                    "[DEBUG] idle: inflight, "
                    "skipping")
            return False
        _idle_inflight.add(group_id)

    try:
        # Get all bots in this group, with health
        # from characters table to detect dead bots
        cursor.execute("""
            SELECT t.bot_guid, t.bot_name,
                   t.trait1, t.trait2, t.trait3,
                   t.role, t.tone, t.zone, t.map,
                   COALESCE(c.health, 1) AS health
            FROM llm_group_bot_traits t
            LEFT JOIN characters c
                ON c.guid = t.bot_guid
            WHERE t.group_id = %s
            ORDER BY RAND()
        """, (group_id,))
        all_bots = cursor.fetchall()

        if not all_bots:
            if _dbg:
                logger.info(
                    "[DEBUG] idle: no bots in "
                    "traits table")
            return False

        # RNG gate
        if random.randint(1, 100) > idle_chance:
            if _dbg:
                logger.info(
                    "[DEBUG] idle: RNG failed "
                    f"({idle_chance}%)")
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

        # Skip idle chatter if player is offline
        if player_name and not is_player_online(
            db, player_name
        ):
            if _dbg:
                logger.info(
                    "[DEBUG] idle: player %s "
                    "offline, skipping",
                    player_name)
            return False

        # In raids, filter bots to the player's
        # sub-group so party chat is visible to them.
        # group_member.guid matches our group_id.
        # Falls back to all bots if not in a raid
        # or if the query fails.
        try:
            sg_cursor = db.cursor(dictionary=True)
            sg_cursor.execute("""
                SELECT gm.subgroup
                FROM group_member gm
                JOIN characters c
                    ON c.guid = gm.memberGuid
                WHERE gm.guid = %s
                AND c.name = %s
                LIMIT 1
            """, (group_id, player_name))
            sg_row = sg_cursor.fetchone()
            if sg_row is not None:
                player_sg = sg_row['subgroup']
                bot_guids = [
                    b['bot_guid'] for b in all_bots
                ]
                fmt = ','.join(
                    ['%s'] * len(bot_guids)
                )
                sg_cursor.execute(f"""
                    SELECT memberGuid, subgroup
                    FROM group_member
                    WHERE guid = %s
                    AND memberGuid IN ({fmt})
                """, [group_id] + bot_guids)
                sg_map = {
                    r['memberGuid']: r['subgroup']
                    for r in sg_cursor.fetchall()
                }
                filtered = [
                    b for b in all_bots
                    if sg_map.get(
                        b['bot_guid']
                    ) == player_sg
                ]
                if filtered:
                    all_bots = filtered
                    logger.info(
                        "[IDLE] sub-group filter: "
                        "%d/%d bots in player's "
                        "sub-group %d",
                        len(filtered),
                        len(bot_guids),
                        player_sg,
                    )
        except Exception:
            logger.error(
                "Raid sub-group filter failed, "
                "using all bots",
                exc_info=True,
            )

        # Single source of truth for location —
        # bot traits updated by C++ OnPlayerUpdateZone
        # in real-time.
        zone_id, area_id, map_id = get_group_location(
            db, group_id)

        # BG already has bg_idle_chatter — skip
        # generic group idle to avoid double party
        # chat in battlegrounds.
        if map_id in BG_MAP_NAMES:
            return False

        # Debug: log location context
        if _dbg:
            loc = format_location_label(
                zone_id, area_id
            )
            logger.info(
                f"[DEBUG] Idle chatter group "
                f"{group_id}: {loc} "
                f"(map={map_id}, "
                f"player={player_name})")

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

        conv_bias = int(config.get(
            'LLMChatter.GroupChatter.'
            'ConversationBias', 70
        ))
        use_conversation = (
            random.randint(1, 100) <= conv_bias
            and len(all_bots) >= 2
        )

        # Stagger if another system already submitted
        # an LLM call this poll cycle (avoids two
        # systems delivering in the same bucket).
        poll_iv = int(config.get(
            'LLMChatter.Bridge.PollIntervalSeconds',
            3
        ))
        stagger_min = float(config.get(
            'LLMChatter.Bridge.InterSystemStaggerMin',
            3
        ))
        stagger_max = float(config.get(
            'LLMChatter.Bridge.InterSystemStaggerMax',
            6
        ))
        stagger_if_needed(
            poll_iv, stagger_min, stagger_max
        )

        if use_conversation:
            result = _idle_conversation(
                db, client, config, group_id,
                all_bots, mode,
                chat_hist, members, now,
                zone_id=zone_id, map_id=map_id,
                current_weather=current_weather,
                player_name=player_name,
                dungeon_bosses=dungeon_bosses,
                area_id=area_id,
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
                area_id=area_id,
            )
        return result
    except Exception as e:
        logger.error(
            f"[IDLE-DIAG] idle EXCEPTION: {e}",
            exc_info=True)
        return False
    finally:
        with _last_idle_chatter_lock:
            _idle_inflight.discard(group_id)


def _idle_single_statement(
    db, client, config, group_id,
    all_bots, mode, chat_hist, members, now,
    zone_id=0, map_id=0,
    current_weather=None, player_name=None,
    dungeon_bosses=None, area_id=0,
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
    stored_tone = bot_row.get('tone')

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
        'is_dead': int(bot_row.get('health', 1)) == 0,
    }

    # Determine address target
    if len(all_bots) == 1:
        # Solo bot — sometimes address player,
        # sometimes just speak generally
        if random.random() < 0.4 and player_name:
            address_target = 'player'
        else:
            address_target = None
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

    recent_msgs = get_recent_bot_messages(
        db, bot_guid
    )

    # Zone metadata for request logging
    _dflav_meta = get_dungeon_flavor(map_id)
    zone_meta = build_zone_metadata(
        zone_name=get_zone_name(zone_id) or '',
        zone_flavor=get_zone_flavor(zone_id) or '',
        subzone_name=(
            get_subzone_name(zone_id, area_id) or ''
        ),
        subzone_lore=(
            get_subzone_lore(zone_id, area_id) or ''
        ),
        dungeon_name=(
            _dflav_meta.split(':')[0].strip()
            if _dflav_meta else ''
        ),
        dungeon_flavor=_dflav_meta or '',
    )

    # Fetch memories for idle recall
    idle_memories = None
    memory_enabled = int(config.get(
        'LLMChatter.Memory.Enable', 1
    ))
    if memory_enabled and player_name:
        recall_chance = int(config.get(
            'LLMChatter.Memory.IdleRecallChance',
            30,
        )) / 100.0
        if random.random() < recall_chance:
            p_info = get_character_info_by_name(
                db, player_name,
            )
            if p_info:
                player_guid = int(p_info['guid'])
                if player_guid:
                    idle_memories = get_bot_memories(
                        db, bot_guid,
                        player_guid, count=2,
                        exclude_first_meeting=True,
                    )
                    if not idle_memories:
                        idle_memories = None

    try:
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
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
            speaker_talent_context=speaker_talent,
            area_id=area_id,
            stored_tone=stored_tone,
            memories=idle_memories,
        )

        _dflav = get_dungeon_flavor(map_id)
        _bg = BG_MAP_NAMES.get(map_id)
        if _dflav:
            _ctx_key = "dungeon"
            _ctx_label = _dflav.split(':')[0].strip()
        elif _bg:
            _ctx_key = "bg"
            _ctx_label = _bg
        else:
            _ctx_key = "zone"
            _ctx_label = (
                get_zone_name(zone_id)
                or f"zone={zone_id}"
            )
        logger.info(
            "[IDLE] stmt | bot=%s %s=%s map=%s",
            bot_name,
            _ctx_key,
            _ctx_label,
            map_id,
        )
        logger.info(
            "[IDLE] prompt snippet: %r",
            prompt[:600],
        )

        if speaker_talent:
            zone_meta['speaker_talent'] = (
                speaker_talent
            )
        zone_meta['channel'] = 'party'
        zone_meta['bot_name'] = bot_name
        if idle_memories:
            zone_meta['has_memory'] = True
            zone_meta['memory_count'] = len(
                idle_memories
            )
        max_tokens = pick_random_max_tokens(config)
        # Memory allusions need room — lift floor
        if idle_memories:
            max_tokens = max(max_tokens, 250)
        _idle_label = (
            'group_idle_memory'
            if idle_memories else 'group_idle'
        )
        response = call_llm(
            client, prompt, config,
            max_tokens_override=max_tokens,
            context=f"idle:{bot_name}",
            label=_idle_label,
            metadata=zone_meta,
        )

        if not response:
            return False

        parsed = parse_single_response(response)
        message = strip_speaker_prefix(
            parsed['message'], bot_name
        )
        message = cleanup_message(
            message, action=parsed.get('action')
        )
        if not message:
            return False
        if len(message) > 255:
            message = message[:252] + "..."


        # Insert directly into messages table
        emote = parsed.get('emote')
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
            "_idle_single_reaction failed "
            "group=%d", group_id, exc_info=True,
        )
        return False


def _idle_conversation(
    db, client, config, group_id,
    bot_rows, mode, chat_hist, members, now,
    zone_id=0, map_id=0,
    current_weather=None, player_name=None,
    dungeon_bosses=None, area_id=0,
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
    # zone_id and map_id are passed from the caller
    # (sourced from the real player's characters
    # table — the authoritative source of truth).
    bots = []
    traits_map = {}
    for br in selected_rows:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT class, race, level
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
            'is_dead': int(
                br.get('health', 1)) == 0,
        }
        bots.append(bot)
        traits_map[br['bot_name']] = [
            br['trait1'], br['trait2'],
            br['trait3'],
        ]

    bot_names = [b['name'] for b in bots]
    # Skip AMBIENT topics inside dungeons and BGs —
    # the instance/BG context injected by the prompt
    # builder already grounds the conversation.
    if (
        get_dungeon_flavor(map_id) is not None
        or map_id in BG_MAP_NAMES
    ):
        topic = None
    else:
        topic_pool = (
            AMBIENT_CHAT_TOPICS_RP
            if mode == 'roleplay'
            else AMBIENT_CHAT_TOPICS
        )
        topic = random.choice(topic_pool)

    boss_str = (
        f", bosses={len(dungeon_bosses or [])}"
        if dungeon_bosses else ""
    )
    names_str = ' & '.join(bot_names)

    # Pool recent messages from all participating bots
    recent_msgs = []
    for br in selected_rows:
        msgs = get_recent_bot_messages(
            db, br['bot_guid']
        )
        recent_msgs.extend(msgs)

    # Zone metadata for request logging
    _dflav_meta2 = get_dungeon_flavor(map_id)
    zone_meta = build_zone_metadata(
        zone_name=get_zone_name(zone_id) or '',
        zone_flavor=get_zone_flavor(zone_id) or '',
        subzone_name=(
            get_subzone_name(zone_id, area_id) or ''
        ),
        subzone_lore=(
            get_subzone_lore(zone_id, area_id) or ''
        ),
        dungeon_name=(
            _dflav_meta2.split(':')[0].strip()
            if _dflav_meta2 else ''
        ),
        dungeon_flavor=_dflav_meta2 or '',
    )

    # Fetch per-bot memories for idle recall
    memories_map = {}
    memory_enabled = int(config.get(
        'LLMChatter.Memory.Enable', 1
    ))
    if memory_enabled and player_name:
        recall_chance = int(config.get(
            'LLMChatter.Memory.IdleRecallChance',
            30,
        )) / 100.0
        if random.random() < recall_chance:
            p_info = get_character_info_by_name(
                db, player_name,
            )
            if p_info:
                player_guid = int(p_info['guid'])
                if player_guid:
                    for b in bots:
                        mems = get_bot_memories(
                            db, b['guid'],
                            player_guid,
                            count=2,
                            exclude_first_meeting=(
                                True
                            ),
                        )
                        if mems:
                            memories_map[
                                b['guid']
                            ] = mems

    try:
        # Talent context for first bot only
        first_bot = bots[0] if bots else None
        speaker_talent = None
        if first_bot:
            speaker_talent = _maybe_talent_context(
                config, db,
                first_bot['guid'],
                first_bot['class'],
                first_bot['name'],
            )
        _dflav = get_dungeon_flavor(map_id)
        _bg = BG_MAP_NAMES.get(map_id)
        if _dflav:
            _ctx_key = "dungeon"
            _ctx_label = _dflav.split(':')[0].strip()
        elif _bg:
            _ctx_key = "bg"
            _ctx_label = _bg
        else:
            _ctx_key = "zone"
            _ctx_label = (
                get_zone_name(zone_id)
                or f"zone={zone_id}"
            )
        logger.info(
            "[IDLE] conv | bots=%s %s=%s map=%s "
            "topic=%s",
            names_str,
            _ctx_key,
            _ctx_label,
            map_id,
            topic or f"({_ctx_key} context)",
        )

        allow_action = (mode == 'roleplay')
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
            speaker_talent_context=speaker_talent,
            area_id=area_id,
            memories_map=memories_map or None,
            allow_action=allow_action,
        )
        logger.info(
            "[IDLE] prompt snippet: %r",
            prompt[:300],
        )

        # Scale tokens with number of bots
        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        conv_tokens = min(
            max_tokens * (1 + num_bots), 1000
        )
        if speaker_talent:
            zone_meta['speaker_talent'] = (
                speaker_talent
            )
        zone_meta['channel'] = 'party'
        zone_meta['bot_name'] = ','.join(bot_names)
        zone_meta['bot_count'] = num_bots
        if memories_map:
            zone_meta['has_memory'] = True
            zone_meta['memory_bots'] = ','.join(
                b['name'] for b in bots
                if b['guid'] in memories_map
            )
        names_ctx = ','.join(bot_names)
        _conv_label = (
            'group_idle_conv_memory'
            if memories_map else 'group_idle_conv'
        )
        response = call_llm(
            client, prompt, config,
            max_tokens_override=conv_tokens,
            context=f"idle-conv:{names_ctx}",
            label=_conv_label,
            metadata=zone_meta,
        )

        if not response:
            return False

        # Parse JSON conversation
        messages = parse_conversation_response(
            response, bot_names
        )

        if not messages:
            return False

        # Strip actions per-message based on
        # ActionChance — LLM can't apply true RNG
        # so Python enforces it post-parse.
        strip_conversation_actions(
            messages, label='group_idle_conv'
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
            "[IDLE-DIAG] conv EXCEPTION: %s", e,
            exc_info=True,
        )
        return False


# ============================================================
# BOT-INITIATED QUESTIONS TO PLAYER
# ============================================================

_last_bot_question = {}
_bot_question_lock = threading.Lock()
_bot_question_inflight = set()


def check_bot_questions(db, client, config):
    """Check active groups for bot-initiated questions.

    Called periodically from the bridge main loop.
    A bot may ask the real player a creative question
    based on contextual information. The player's reply
    is handled by the existing bot_group_player_msg
    event system since the question is stored in
    chat history.

    Returns True if a question was generated.
    """
    enable = config.get(
        'LLMChatter.GroupChatter.BotQuestionEnable',
        '1'
    )
    if str(enable) != '1':
        return False

    question_chance = int(config.get(
        'LLMChatter.GroupChatter.BotQuestionChance',
        1
    ))
    question_cooldown = int(config.get(
        'LLMChatter.GroupChatter.BotQuestionCooldown',
        600
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
    with _bot_question_lock:
        # Prune stale entries (older than 30 min)
        cutoff = time.time() - 1800
        for k in list(_last_bot_question):
            if _last_bot_question[k] <= cutoff:
                del _last_bot_question[k]

        now = time.time()
        last_q = _last_bot_question.get(
            group_id, 0
        )
        if now - last_q < question_cooldown:
            return False
        if group_id in _bot_question_inflight:
            return False
        _bot_question_inflight.add(group_id)

    try:
        # Roll chance
        if random.randint(1, 100) > question_chance:
            return False

        # Combat suppression: skip if any recent
        # combat-related events (broader than just
        # bot_group_combat which only fires for
        # elite/boss pulls)
        cursor.execute("""
            SELECT 1 FROM llm_chatter_events
            WHERE event_type IN (
                'bot_group_combat',
                'bot_group_kill',
                'bot_group_spell_cast',
                'bot_group_death'
            )
              AND CAST(JSON_EXTRACT(
                  extra_data, '$.group_id'
              ) AS UNSIGNED) = %s
              AND created_at > DATE_SUB(
                  NOW(), INTERVAL 90 SECOND
              )
            LIMIT 1
        """, (group_id,))
        if cursor.fetchone():
            return False

        # Get player name — try chat history first,
        # fall back to player_guid in bot_traits
        player_name = get_group_player_name(
            db, group_id
        )

        # Skip bot questions if player is offline
        if player_name and not is_player_online(
            db, player_name
        ):
            return False

        player_row = None
        if player_name:
            cursor.execute("""
                SELECT class, race, level
                FROM characters
                WHERE name = %s LIMIT 1
            """, (player_name,))
            player_row = cursor.fetchone()

        if not player_row:
            # Fallback: derive player name from
            # join event extra_data (available even
            # if player has never spoken)
            cursor.execute("""
                SELECT JSON_EXTRACT(
                    extra_data, '$.player_name'
                ) AS pname
                FROM llm_chatter_events
                WHERE CAST(JSON_EXTRACT(
                    extra_data, '$.group_id'
                ) AS UNSIGNED) = %s
                  AND event_type IN (
                      'bot_group_join',
                      'bot_group_join_batch'
                  )
                  AND extra_data IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1
            """, (group_id,))
            ev = cursor.fetchone()
            if ev and ev.get('pname'):
                # JSON_EXTRACT returns quoted string
                pn = str(ev['pname']).strip('"')
                if pn:
                    cursor.execute("""
                        SELECT name, class, race,
                               level
                        FROM characters
                        WHERE name = %s LIMIT 1
                    """, (pn,))
                    player_row = cursor.fetchone()
                    if player_row:
                        player_name = (
                            player_row['name']
                        )

        if not player_name or not player_row:
            return False

        player_class = get_class_name(
            player_row['class']
        )
        player_race = get_race_name(
            player_row['race']
        )
        player_level = int(player_row['level'])

        # Get all bots in this group
        cursor.execute("""
            SELECT bot_guid, bot_name,
                   trait1, trait2, trait3, role,
                   tone, zone, map
            FROM llm_group_bot_traits
            WHERE group_id = %s
            ORDER BY RAND()
        """, (group_id,))
        all_bots = cursor.fetchall()

        if not all_bots:
            return False

        # Pick one random bot to ask the question
        bot_row = all_bots[0]
        bot_guid = bot_row['bot_guid']
        bot_name = bot_row['bot_name']
        traits = [
            bot_row['trait1'],
            bot_row['trait2'],
            bot_row['trait3'],
        ]
        stored_tone = bot_row.get('tone')

        # Get bot class/race/level
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
            'class': get_class_name(
                char_row['class']
            ),
            'race': get_race_name(
                char_row['race']
            ),
            'level': char_row['level'],
            'role': bot_row.get('role'),
        }

        # Gather context
        mode = get_chatter_mode(config)
        idle_history_limit = int(config.get(
            'LLMChatter.GroupChatter.'
            'IdleHistoryLimit', 5
        ))
        history = _get_recent_chat(
            db, group_id,
            limit=idle_history_limit
        )
        chat_hist = format_chat_history(history)
        members = get_group_members(db, group_id)

        # Single source of truth for location —
        # bot traits updated by C++ OnPlayerUpdateZone
        # in real-time.
        zone_id, area_id, map_id = get_group_location(
            db, group_id)
        current_weather = (
            get_recent_weather(db, zone_id)
            if zone_id else None
        )

        recent_msgs = get_recent_bot_messages(
            db, bot_guid
        )

        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        # Target talent for the player
        target_talent = None
        player_info = get_character_info_by_name(
            db, player_name,
        )
        if player_info:
            target_talent = _maybe_talent_context(
                config, db,
                player_info['guid'],
                get_class_name(
                    player_info['class']
                ),
                player_name,
                perspective='target',
            )

        # RNG-gated memory injection
        question_memories = None
        memory_enabled = int(config.get(
            'LLMChatter.Memory.Enable', 1
        ))
        if memory_enabled and player_info:
            recall_chance = int(config.get(
                'LLMChatter.Memory'
                '.IdleRecallChance', 30,
            )) / 100.0
            p_guid = int(
                player_info['guid']
            )
            if (
                p_guid
                and random.random()
                    < recall_chance
            ):
                question_memories = (
                    get_bot_memories(
                        db, bot_guid,
                        p_guid, count=3,
                        exclude_first_meeting=True,
                    )
                )
                if not question_memories:
                    question_memories = None

        prompt = build_bot_question_prompt(
            bot, traits, mode,
            player_name=player_name,
            player_class=player_class,
            player_race=player_race,
            player_level=player_level,
            chat_history=chat_hist,
            members=members,
            zone_id=zone_id,
            map_id=map_id,
            current_weather=current_weather,
            recent_messages=recent_msgs,
            speaker_talent_context=speaker_talent,
            target_talent_context=target_talent,
            area_id=area_id,
            stored_tone=stored_tone,
            memories=question_memories or None,
        )

        max_tokens = int(config.get(
            'LLMChatter.MaxTokens', 200
        ))
        bq_meta = {
            'channel': 'party',
            'bot_name': bot_name,
        }
        if speaker_talent:
            bq_meta['speaker_talent'] = (
                speaker_talent
            )
        if target_talent:
            bq_meta['target_talent'] = (
                target_talent
            )
        if question_memories:
            bq_meta['has_memory'] = True
            bq_meta['memory_count'] = len(
                question_memories
            )
        _bq_label = (
            'group_bot_question_memory'
            if question_memories
            else 'group_bot_question'
        )
        bq_cap = 250 if question_memories else 200
        response = call_llm(
            client, prompt, config,
            max_tokens_override=min(
                max_tokens, bq_cap
            ),
            context=f"bot-question:{bot_name}",
            label=_bq_label,
            metadata=bq_meta or None,
        )

        if not response:
            return False

        parsed = parse_single_response(response)
        message = strip_speaker_prefix(
            parsed['message'], bot_name
        )
        message = cleanup_message(
            message,
            action=parsed.get('action')
        )
        if not message:
            return False

        # Validate: must end with a question mark
        if not message.rstrip().endswith('?'):
            # Retry once with stricter instruction
            retry_prompt = (
                prompt
                + "\n\nCRITICAL: You MUST ask a "
                "question ending with '?'. Your "
                "previous response was not a "
                "question. Try again."
            )
            response = call_llm(
                client, retry_prompt, config,
                max_tokens_override=min(
                    max_tokens, 200
                ),
                context=(
                    f"bot-question-retry:{bot_name}"
                ),
                label='group_bot_question',
                metadata=bq_meta or None,
            )
            if not response:
                return False
            parsed = parse_single_response(
                response
            )
            message = strip_speaker_prefix(
                parsed['message'], bot_name
            )
            message = cleanup_message(
                message,
                action=parsed.get('action')
            )
            if (
                not message
                or not message.rstrip().endswith('?')
            ):
                return False

        if len(message) > 255:
            # Preserve trailing '?' after truncation
            message = message[:254] + "?"

        # Deliver the question
        emote = parsed.get('emote')
        insert_chat_message(
            db, bot_guid, bot_name, message,
            channel='party', delay_seconds=2,
            event_id=None, emote=emote,
        )

        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        with _bot_question_lock:
            _last_bot_question[group_id] = now

        return True

    except Exception as e:
        logger.error(
            "_maybe_bot_question failed group=%d",
            group_id, exc_info=True,
        )
        return False
    finally:
        with _bot_question_lock:
            _bot_question_inflight.discard(
                group_id
            )


def process_group_farewell_event(
    db, client, config, event
):
    """Handle bot_group_farewell — triggers memory
    flush when a bot leaves the group.

    Called by the bridge dispatch table. The event
    extra_data contains bot_guid, group_id, and
    player_guid.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_farewell',
    )
    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(
        extra_data.get('bot_guid', 0)
    )
    group_id = int(
        extra_data.get('group_id', 0)
    )
    player_guid = int(
        extra_data.get('player_guid', 0)
    )

    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    try:
        flush_session_memories(
            db, group_id, player_guid,
            bot_guid, config,
        )
        _mark_event(db, event_id, 'completed')
        return True
    except Exception:
        logger.error(
            f"Farewell flush failed for "
            f"bot={bot_guid} group={group_id}",
            exc_info=True,
        )
        _mark_event(db, event_id, 'skipped')
        return False
