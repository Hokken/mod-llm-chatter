"""Group reaction handlers extracted from chatter_group (N6 batch 1)."""

import logging
import random
import re

from chatter_shared import (
    parse_extra_data,
    get_class_name,
    get_race_name,
    get_chatter_mode,
    get_zone_name,
    get_zone_flavor,
    get_subzone_lore,
    get_subzone_name,
    query_quest_turnin_npc,
    get_dungeon_flavor,
    get_dungeon_bosses,
    format_item_link,
    format_item_context,
    run_single_reaction,
    parse_conversation_response,
    calculate_dynamic_delay,
    build_talent_context,
    build_zone_metadata,
    should_include_action,
)
from chatter_db import (
    get_group_location,
    insert_chat_message,
    get_character_info_by_name,
)
from chatter_constants import BG_MAP_NAMES
from chatter_text import (
    strip_speaker_prefix,
    cleanup_message,
)
from chatter_llm import call_llm
from chatter_group_state import (
    _has_recent_event,
    _mark_event,
    _store_chat,
    _get_recent_chat,
    format_chat_history,
    get_group_members,
    get_group_player_name,
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
    build_group_achievement_reaction_prompt,
    build_spell_cast_reaction_prompt,
    build_resurrect_reaction_prompt,
    build_zone_transition_prompt,
    build_quest_accept_reaction_prompt,
    build_quest_accept_batch_prompt,
    build_dungeon_entry_prompt,
    build_wipe_reaction_prompt,
    build_corpse_run_reaction_prompt,
    build_low_health_callout_prompt,
    build_oom_callout_prompt,
    build_aggro_loss_callout_prompt,
    build_nearby_object_reaction_prompt,
    build_nearby_object_conversation_prompt,
    build_player_msg_conversation_prompt,
    build_quest_complete_conversation_prompt,
    build_quest_objectives_conversation_prompt,
    build_quest_accept_conversation_prompt,
)
from chatter_raid_base import (
    dual_worker_dispatch,
)
from chatter_memory import queue_memory
from chatter_bg_prompts import (
    build_bg_achievement_prompt,
    build_bg_spell_cast_prompt,
    build_bg_low_health_prompt,
    build_bg_oom_prompt,
    build_bg_death_prompt,
    build_bg_combat_prompt,
)

logger = logging.getLogger(__name__)


def _maybe_talent_context(
    config, db, bot_guid, bot_class, bot_name,
    perspective='speaker',
):
    """Compute talent context if RNG passes.

    Returns str or None. Rolls once against the
    TalentInjectionChance config key.
    """
    chance = int(config.get(
        'LLMChatter.TalentInjectionChance', '40'
    ))
    if chance <= 0:
        return None
    if random.randint(1, 100) > chance:
        return None
    result = build_talent_context(
        db, int(bot_guid), bot_class,
        bot_name, perspective=perspective,
    )
    return result


def _resolve_zone_name(
    db, group_id, extra_data_zone_name
):
    """Resolve the authoritative zone name for a
    group using llm_group_bot_traits (single source
    of truth, updated by C++ OnPlayerUpdateZone).

    Falls back to C++ extra_data zone_name if
    the traits lookup fails.

    Returns zone_name string.
    """
    zone_id, _, _ = get_group_location(
        db, group_id
    )
    if zone_id:
        resolved = get_zone_name(zone_id)
        if resolved and not resolved.startswith(
            'zone '
        ):
            return resolved
    # Fallback to C++ extra_data zone_name
    return extra_data_zone_name or 'somewhere'


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
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot_class, bot_name,
        )
        _, _, map_id = get_group_location(
            db, group_id
        )
        prompt = build_kill_reaction_prompt(
            bot, traits, creature_name,
            is_boss, is_rare, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            allow_action=not extra_data.get(
                'is_battleground', False),
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
            map_id=map_id,
        )
        mood_label = get_bot_mood_label(
            group_id, bot_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-kill:#{event_id}:{bot_name}"
            ),
            label='reaction_kill',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        update_bot_mood(
            group_id, bot_guid,
            'boss_kill' if is_boss else 'kill'
        )

        # Memory: bots remember boss/rare kills
        if is_boss or is_rare:
            try:
                mem_type = (
                    'boss_kill' if is_boss
                    else 'rare_kill'
                )
                boss_mem_chance = int(config.get(
                    'LLMChatter.Memory'
                    '.BossKillGenerationChance',
                    60
                ))
                mc = db.cursor(dictionary=True)
                mc.execute(
                    "SELECT t.bot_guid, t.bot_name,"
                    " c.class, c.race"
                    " FROM llm_group_bot_traits t"
                    " JOIN characters c"
                    "   ON c.guid = t.bot_guid"
                    " WHERE t.group_id = %s",
                    (group_id,),
                )
                all_bots = mc.fetchall()
                for ab in all_bots:
                    if (random.random() * 100
                            >= boss_mem_chance):
                        continue
                    try:
                        queue_memory(
                            config, group_id,
                            ab['bot_guid'], 0,
                            memory_type=mem_type,
                            event_context=(
                                f"Killed"
                                f" {creature_name}"
                            ),
                            bot_name=ab['bot_name'],
                            bot_class=get_class_name(
                                ab['class']
                            ),
                            bot_race=get_race_name(
                                ab['race']
                            ),
                        )
                    except Exception:
                        pass
            except Exception:
                logger.error(
                    "boss/rare_kill memory failed",
                    exc_info=True,
                )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')
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
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            bot['class'], reactor_name,
        )
        _, _, map_id = get_group_location(
            db, group_id
        )
        prompt = build_loot_reaction_prompt(
            bot, traits, item_name,
            item_quality, mode,
            chat_history=chat_hist,
            looter_name=prompt_looter_name,
            extra_data=extra_data,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
            map_id=map_id,
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
            context=(
                f"grp-loot:#{event_id}"
                f":{bot['name']}"
            ),
            message_transform=_loot_message_transform,
            label='reaction_loot',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


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

    except Exception:
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
        # BG fallback: no traits, use
        # lightweight data + BG dispatch
        if extra_data.get('is_battleground'):
            extra_data['event_type'] = (
                'bot_group_combat')
            extra_data['party_bot_guids'] = [
                bot_guid]
            result = dual_worker_dispatch(
                db, client, config,
                event, extra_data,
                subgroup_prompt_fn=(
                    build_bg_combat_prompt),
                raid_prompt_fn=None)
            _mark_event(
                db, event_id,
                'completed' if result
                else 'skipped')
            return result
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        prompt = build_combat_reaction_prompt(
            bot, traits, creature_name,
            is_boss, mode,
            chat_history=chat_hist,
            is_elite=is_elite,
            extra_data=extra_data,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
        )

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
            max_tokens_override=60,
            context=(
                f"grp-combat:#{event_id}"
                f":{bot_name}"
            ),
            label='reaction_combat',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot['guid'],
            bot['name'], True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
            # BG fallback: no traits, use
            # lightweight data + BG dispatch
            if extra_data.get('is_battleground'):
                extra_data['event_type'] = (
                    'bot_group_death')
                extra_data['party_bot_guids'] = [
                    reactor_guid]
                result = dual_worker_dispatch(
                    db, client, config,
                    event, extra_data,
                    subgroup_prompt_fn=(
                        build_bg_death_prompt),
                    raid_prompt_fn=None)
                _mark_event(
                    db, event_id,
                    'completed' if result
                    else 'skipped')
                return result
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
        stored_tone = reactor_data.get('tone')
    else:
        reactor_traits = trait_data['traits']
        stored_tone = trait_data.get('tone')
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
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            reactor['class'], reactor_name,
        )
        _, _, map_id = get_group_location(
            db, group_id
        )
        prompt = build_death_reaction_prompt(
            reactor, reactor_traits, dead_name,
            killer_name, mode,
            chat_history=chat_hist,
            is_player_death=is_player_death,
            extra_data=extra_data,
            allow_action=not extra_data.get(
                'is_battleground', False),
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
            map_id=map_id,
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-death:#{event_id}"
                f":{reactor_name}"
            ),
            label='reaction_death',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'death'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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

    # C++ already picked the reactor bot
    # (bot_guid/bot_name) and the leveler
    # (leveler_name). Use them directly.
    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'someone'
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

    if not reactor_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # Get reactor traits from DB
    trait_data = get_bot_traits(
        db, group_id, reactor_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False
    reactor_traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

    # Get reactor's class/race from characters
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
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
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            reactor['class'], reactor_name,
        )
        prompt = build_levelup_reaction_prompt(
            reactor, reactor_traits,
            leveler_name, new_level, is_bot,
            mode, chat_history=chat_hist,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-levelup:#{event_id}"
                f":{reactor_name}"
            ),
            label='reaction_levelup',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'levelup'
        )
        _mark_event(db, event_id, 'completed')

        # Memory: reactor remembers the level-up
        try:
            mem_chance = int(config.get(
                'LLMChatter.Memory'
                '.LevelUpGenerationChance', 50
            ))
            if random.random() * 100 < mem_chance:
                queue_memory(
                    config, group_id,
                    reactor_guid, 0,
                    memory_type='level_up',
                    event_context=(
                        f"{leveler_name} reached"
                        f" level {new_level}"
                    ),
                    bot_name=reactor_name,
                    bot_class=reactor['class'],
                    bot_race=reactor['race'],
                )
        except Exception:
            logger.error(
                "level_up memory failed",
                exc_info=True,
            )

        # Memory: leveler remembers their own
        # milestone (only if bot, not player)
        if is_bot and leveler_guid != reactor_guid:
            try:
                # Get leveler's class/race
                lv_c = db.cursor(dictionary=True)
                lv_c.execute(
                    "SELECT class, race FROM"
                    " characters WHERE guid = %s",
                    (leveler_guid,),
                )
                lv_row = lv_c.fetchone()
                if lv_row:
                    queue_memory(
                        config, group_id,
                        leveler_guid, 0,
                        memory_type='level_up',
                        event_context=(
                            f"I reached level"
                            f" {new_level}"
                        ),
                        bot_name=leveler_name,
                        bot_class=get_class_name(
                            lv_row['class']
                        ),
                        bot_race=get_race_name(
                            lv_row['race']
                        ),
                    )
            except Exception:
                pass

        return True

    except Exception:
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
        _mark_event(db, event_id, 'skipped')
        return False
    reactor_traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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


    # Mark as processing
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = 'processing' WHERE id = %s",
        (event_id,)
    )
    db.commit()

    # -- Decide: conversation or statement? --
    conv_chance = int(config.get(
        'LLMChatter.GroupChatter'
        '.QuestConversationChance', 30
    ))
    members = get_group_members(db, group_id)
    do_conversation = (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    )

    if do_conversation:
        try:
            ok = _quest_complete_conversation(
                db, client, config, event_id,
                group_id, reactor_name,
                reactor_guid, members,
                completer_name, quest_name,
                extra_data,
            )
            if ok:
                update_bot_mood(
                    group_id, reactor_guid,
                    'quest',
                )
                # Memory: quest completion (conv path)
                try:
                    mem_chance = int(config.get(
                        'LLMChatter.Memory'
                        '.QuestGenerationChance', 40
                    ))
                    if (
                        random.random() * 100
                        < mem_chance
                    ):
                        queue_memory(
                            config, group_id,
                            reactor_guid, 0,
                            memory_type=(
                                'quest_complete'
                            ),
                            event_context=(
                                f"Completed quest:"
                                f" {quest_name}"
                            ),
                            bot_name=reactor_name,
                            bot_class=(
                                reactor['class']
                            ),
                            bot_race=(
                                reactor['race']
                            ),
                        )
                except Exception:
                    logger.error(
                        "quest_complete memory"
                        " failed (conv path)",
                        exc_info=True,
                    )
                return True
        except Exception:
            pass
        # Fall through to statement path

    try:
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        zone_id, _, _ = get_group_location(
            db, group_id
        )
        # Look up turn-in NPC name
        quest_id = int(
            extra_data.get('quest_id', 0)
        )
        turnin_npc = None
        if quest_id:
            turnin_npc = query_quest_turnin_npc(
                config, quest_id
            )
        quest_details = extra_data.get(
            'quest_details', ''
        )
        quest_objectives = extra_data.get(
            'quest_objectives', ''
        )
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            reactor['class'], reactor_name,
        )
        prompt = (
            build_quest_complete_reaction_prompt(
                reactor, reactor_traits,
                completer_name, quest_name,
                mode,
                chat_history=chat_hist,
                turnin_npc=turnin_npc,
                quest_details=quest_details,
                quest_objectives=quest_objectives,
                speaker_talent_context=speaker_talent,
                stored_tone=stored_tone,
                zone_id=zone_id,
            )
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-quest:#{event_id}"
                f":{reactor_name}"
            ),
            label='reaction_quest_complete',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'quest'
        )

        # Memory: quest completion
        try:
            mem_chance = int(config.get(
                'LLMChatter.Memory'
                '.QuestGenerationChance', 40
            ))
            if random.random() * 100 < mem_chance:
                queue_memory(
                    config, group_id,
                    reactor_guid, 0,
                    memory_type='quest_complete',
                    event_context=(
                        f"Completed quest:"
                        f" {quest_name}"
                    ),
                    bot_name=reactor_name,
                    bot_class=reactor['class'],
                    bot_race=reactor['race'],
                )
        except Exception:
            logger.error(
                "quest_complete memory failed",
                exc_info=True,
            )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
        _mark_event(db, event_id, 'skipped')
        return False

    # Pick a different bot to react
    reactor_data = get_other_group_bot(
        db, group_id, completer_guid
    )
    stored_tone = None
    if reactor_data:
        reactor_guid = reactor_data['guid']
        reactor_name = reactor_data['name']
        reactor_traits = reactor_data['traits']
        stored_tone = reactor_data.get('tone')
    else:
        # No other bot — use the completing bot
        trait_data = get_bot_traits(
            db, group_id, completer_guid
        )
        if not trait_data:
            _mark_event(db, event_id, 'skipped')
            return False
        reactor_guid = completer_guid
        reactor_name = completer_name
        reactor_traits = trait_data['traits']
        stored_tone = trait_data.get('tone')

    # Get reactor's class/race from characters
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
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


    # Mark as processing
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = 'processing' WHERE id = %s",
        (event_id,)
    )
    db.commit()

    # -- Decide: conversation or statement? --
    conv_chance = int(config.get(
        'LLMChatter.GroupChatter'
        '.QuestConversationChance', 30
    ))
    members = get_group_members(db, group_id)
    do_conversation = (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    )

    if do_conversation:
        try:
            ok = _quest_objectives_conversation(
                db, client, config, event_id,
                group_id, reactor_name,
                reactor_guid, members,
                completer_name, quest_name,
                extra_data,
            )
            if ok:
                return True
        except Exception:
            pass
        # Fall through to statement path

    try:
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        zone_id, _, _ = get_group_location(
            db, group_id
        )
        quest_details = extra_data.get(
            'quest_details', ''
        )
        quest_objectives = extra_data.get(
            'quest_objectives', ''
        )
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            reactor['class'], reactor_name,
        )
        prompt = (
            build_quest_objectives_reaction_prompt(
                reactor, reactor_traits,
                quest_name, completer_name,
                mode,
                chat_history=chat_hist,
                quest_details=quest_details,
                quest_objectives=quest_objectives,
                speaker_talent_context=speaker_talent,
                stored_tone=stored_tone,
                zone_id=zone_id,
            )
        )

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
            context=(
                f"grp-objectives:#{event_id}"
                f":{reactor_name}"
            ),
            label='reaction_quest_complete',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
        _mark_event(db, event_id, 'skipped')
        return False

def _check_achievement_batch(
    db, event_id, group_id, achievement_name
):
    """Check for duplicate achievement events that
    should be batched together.

    Returns:
        None: no duplicates found, process normally
        'already_batched': this event is owned by
            an earlier event, skip it
        list[str]: list of all achiever names
            (this event is the batch owner)
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id,
            JSON_UNQUOTE(
                JSON_EXTRACT(extra_data,
                    '$.achiever_name')
            ) AS achiever_name,
            JSON_UNQUOTE(
                JSON_EXTRACT(extra_data,
                    '$.bot_name')
            ) AS bot_name
        FROM llm_chatter_events
        WHERE event_type = 'bot_group_achievement'
            AND status IN ('pending', 'processing')
            AND id != %s
            AND CAST(JSON_EXTRACT(extra_data,
                '$.group_id'
            ) AS UNSIGNED) = %s
            AND JSON_UNQUOTE(
                JSON_EXTRACT(extra_data,
                    '$.achievement_name')
            ) = %s
            AND ABS(TIMESTAMPDIFF(
                SECOND, created_at,
                (SELECT created_at
                 FROM llm_chatter_events
                 WHERE id = %s)
            )) <= 2
    """, (event_id, group_id,
          achievement_name, event_id))
    dupes = cursor.fetchall()

    if not dupes:
        return None

    # Find lowest ID among this event + dupes
    all_ids = [event_id] + [d['id'] for d in dupes]
    min_id = min(all_ids)

    if event_id != min_id:
        return 'already_batched'

    # This event is the batch owner — collect names
    # and mark duplicates as completed
    # Get this event's achiever name
    cursor.execute("""
        SELECT
            JSON_UNQUOTE(
                JSON_EXTRACT(extra_data,
                    '$.achiever_name')
            ) AS achiever_name,
            JSON_UNQUOTE(
                JSON_EXTRACT(extra_data,
                    '$.bot_name')
            ) AS bot_name
        FROM llm_chatter_events
        WHERE id = %s
    """, (event_id,))
    own_row = cursor.fetchone()
    own_name = (
        own_row['achiever_name']
        or own_row['bot_name']
        or 'someone'
    ) if own_row else 'someone'

    names = [own_name]
    dupe_ids = []
    for d in dupes:
        name = (
            d['achiever_name']
            or d['bot_name']
            or 'someone'
        )
        names.append(name)
        dupe_ids.append(d['id'])

    # Mark all duplicates as completed
    if dupe_ids:
        placeholders = ', '.join(
            ['%s'] * len(dupe_ids)
        )
        cursor.execute(
            f"UPDATE llm_chatter_events "
            f"SET status = 'completed' "
            f"WHERE id IN ({placeholders})",
            tuple(dupe_ids)
        )
        db.commit()


    return names


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

    # --- Achievement dedup: batch simultaneous ---
    batch_result = _check_achievement_batch(
        db, event_id, group_id, achievement_name
    )
    if batch_result == 'already_batched':
        # Another event with lower ID owns this
        _mark_event(db, event_id, 'completed')
        return True
    # batch_result is None (no dupes) or a list
    # of achiever names (this event is the owner)
    batched_names = batch_result

    # Pick a different bot to react
    reactor_data = get_other_group_bot(
        db, group_id, achiever_guid
    )
    trait_data = None
    if reactor_data:
        reactor_guid = reactor_data['guid']
        reactor_name = reactor_data['name']
        reactor_traits = reactor_data['traits']
        trait_data = reactor_data
    else:
        # No other bot — use the achieving bot
        trait_data = get_bot_traits(
            db, group_id, achiever_guid
        )
        if not trait_data:
            # BG fallback: no traits, use
            # lightweight data + BG dispatch
            if extra_data.get('is_battleground'):
                extra_data['event_type'] = (
                    'bot_group_achievement')
                result = dual_worker_dispatch(
                    db, client, config,
                    event, extra_data,
                    subgroup_prompt_fn=(
                        build_bg_achievement_prompt),
                    raid_prompt_fn=None)
                _mark_event(
                    db, event_id,
                    'completed' if result
                    else 'skipped')
                return result
            _mark_event(db, event_id, 'skipped')
            return False
        reactor_guid = achiever_guid
        reactor_name = achiever_name
        reactor_traits = trait_data['traits']
    stored_tone = (
        trait_data.get('tone') if trait_data
        else None
    )

    # Get reactor's class/race from characters
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level
        FROM characters
        WHERE guid = %s
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

    # Re-check status — another thread (batch owner)
    # may have already completed this event
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT status FROM llm_chatter_events "
        "WHERE id = %s",
        (event_id,)
    )
    status_row = cursor.fetchone()
    if (
        status_row
        and status_row['status'] == 'completed'
    ):
        return True

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
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            reactor['class'], reactor_name,
        )
        _, _, map_id = get_group_location(
            db, group_id
        )
        if batched_names:
            prompt = (
                build_group_achievement_reaction_prompt(
                    reactor, reactor_traits,
                    batched_names, achievement_name,
                    mode,
                    chat_history=chat_hist,
                    speaker_talent_context=(
                        speaker_talent),
                    stored_tone=stored_tone,
                    map_id=map_id,
                )
            )
        else:
            prompt = (
                build_achievement_reaction_prompt(
                    reactor, reactor_traits,
                    achiever_name,
                    achievement_name,
                    is_bot, mode,
                    chat_history=chat_hist,
                    speaker_talent_context=(
                        speaker_talent),
                    map_id=map_id,
                    stored_tone=stored_tone,
                )
            )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-achieve:#{event_id}"
                f":{reactor_name}"
            ),
            label='reaction_achievement',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'achievement'
        )

        # Memory: ALL bots remember the achievement.
        # Skip in BG — achievements fire constantly
        # (Honorable Kill, etc.) and would flood
        # memory with low-value entries.
        if extra_data.get('is_battleground'):
            _mark_event(db, event_id, 'completed')
            return True
        try:
            mc = db.cursor(dictionary=True)
            mc.execute(
                "SELECT t.bot_guid, t.bot_name,"
                " c.class, c.race"
                " FROM llm_group_bot_traits t"
                " JOIN characters c"
                "   ON c.guid = t.bot_guid"
                " WHERE t.group_id = %s",
                (group_id,),
            )
            all_bots = mc.fetchall()
            achv_chance = int(config.get(
                'LLMChatter.Memory'
                '.AchievementGenerationChance',
                35
            ))
            for ab in all_bots:
                if (random.random() * 100
                        >= achv_chance):
                    continue
                try:
                    queue_memory(
                        config, group_id,
                        ab['bot_guid'], 0,
                        memory_type='achievement',
                        event_context=(
                            f"Earned achievement:"
                            f" {achievement_name}"
                        ),
                        bot_name=ab['bot_name'],
                        bot_class=get_class_name(
                            ab['class']
                        ),
                        bot_race=get_race_name(
                            ab['race']
                        ),
                    )
                except Exception:
                    pass
        except Exception:
            logger.error(
                "achievement memory failed",
                exc_info=True,
            )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
        # BG fallback: no traits, use BG dispatch
        if extra_data.get('is_battleground'):
            extra_data['event_type'] = (
                'bot_group_spell_cast')
            # Pin to event's bot so dispatch
            # speaks from the correct character
            extra_data['party_bot_guids'] = (
                [bot_guid])
            result = dual_worker_dispatch(
                db, client, config,
                event, extra_data,
                subgroup_prompt_fn=(
                    build_bg_spell_cast_prompt),
                raid_prompt_fn=None)
            _mark_event(
                db, event_id,
                'completed' if result
                else 'skipped')
            return result
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        members = get_group_members(db, group_id)

        # Get map from group location (single source
        # of truth, updated by C++ in real-time)
        _, _, map_id = get_group_location(
            db, group_id
        )

        # Get dungeon bosses if in a dungeon
        in_dungeon = (
            get_dungeon_flavor(map_id) is not None
        )
        dungeon_bosses = (
            get_dungeon_bosses(db, map_id)
            if in_dungeon else None
        )

        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot_class, bot_name,
        )
        prompt = build_spell_cast_reaction_prompt(
            bot, traits, caster_name,
            spell_name, spell_category,
            target_name, mode,
            chat_history=chat_hist,
            members=members,
            dungeon_bosses=dungeon_bosses,
            extra_data=extra_data,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
        )

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
            context=(
                f"grp-spell:#{event_id}"
                f":{bot['name']}"
            ),
            label='reaction_spell',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        prompt = build_resurrect_reaction_prompt(
            bot, traits, mode,
            chat_history=chat_hist,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
        )
        mood_label = get_bot_mood_label(
            group_id, bot_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-resurrect:#{event_id}"
                f":{bot_name}"
            ),
            label='reaction_rez',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        update_bot_mood(
            group_id, bot_guid, 'resurrect'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
        _mark_event(db, event_id, 'skipped')
        return False

def process_group_zone_transition_event(
    db, client, config, event
):
    """Handle a bot_group_zone_transition or
    bot_group_subzone_change event.

    The bot comments on entering a new zone or
    subzone in party chat.
    """
    event_id = event['id']
    event_type = event.get(
        'event_type', 'bot_group_zone_transition'
    )
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        event_type,
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

    # Use live traits (single source of truth) for
    # all location data — avoids mixing event-time
    # extra_data with live-time traits lookups.
    zone_id, area_id, map_id = get_group_location(
        db, group_id
    )

    # BG subzone moves are constant noise — bots
    # sprint between flag rooms, lumber mill, etc.
    # bg_idle_chatter already covers ambient BG
    # narrative, so suppress zone transitions in BG.
    if map_id in BG_MAP_NAMES:
        _mark_event(db, event_id, 'skipped')
        return False
    zone_name = (
        get_zone_name(zone_id)
        if zone_id else None
    )
    if not zone_name or zone_name.startswith(
        'zone '
    ):
        # Fallback to C++ extra_data zone_name
        zone_name = extra_data.get(
            'zone_name', 'somewhere'
        )
        zone_id = int(
            extra_data.get('zone_id', 0)
        )
        area_id = int(
            extra_data.get('area_id', 0)
        )

    # The bot that entered the zone reacts
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        is_subzone = (
            event_type == 'bot_group_subzone_change'
        )
        prompt = build_zone_transition_prompt(
            bot, traits, zone_name, zone_id,
            mode,
            chat_history=chat_hist,
            speaker_talent_context=speaker_talent,
            area_id=area_id,
            stored_tone=stored_tone,
            is_subzone=is_subzone,
            area_name=extra_data.get(
                'area_name', ''
            ),
        )

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
            label='reaction_zone_transition',
            context=(
                f"grp-zone:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        # Memory: ambient on zone transition
        try:
            ambient_chance = int(config.get(
                'LLMChatter.Memory.AmbientChance',
                15,
            ))
            if (
                ambient_chance > 0
                and random.randint(1, 100)
                    <= ambient_chance
            ):
                queue_memory(
                    config, group_id, bot_guid, 0,
                    memory_type='ambient',
                    event_context=(
                        f"Traveling through "
                        f"{zone_name}"
                    ),
                    bot_name=bot_name,
                    bot_class=bot['class'],
                    bot_race=bot['race'],
                )
        except Exception:
            logger.error(
                "ambient memory failed",
                exc_info=True,
            )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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

    # Player zone as source of truth
    zone_name = _resolve_zone_name(
        db, group_id, zone_name
    )

    trait_data = get_bot_traits(
        db, group_id, reactor_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False
    reactor_traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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


    # Mark as processing
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = 'processing' WHERE id = %s",
        (event_id,)
    )
    db.commit()

    # -- Decide: conversation or statement? --
    conv_chance = int(config.get(
        'LLMChatter.GroupChatter'
        '.QuestConversationChance', 30
    ))
    members = get_group_members(db, group_id)
    do_conversation = (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    )

    if do_conversation:
        try:
            ok = _quest_accept_conversation(
                db, client, config, event_id,
                group_id, reactor_name,
                reactor_guid, members,
                acceptor_name, quest_name,
                quest_level, zone_name,
                extra_data,
            )
            if ok:
                update_bot_mood(
                    group_id, reactor_guid,
                    'quest',
                )
                return True
        except Exception:
            pass
        # Fall through to statement path

    try:
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        zone_id, _, _ = get_group_location(
            db, group_id
        )
        quest_details = extra_data.get(
            'quest_details', ''
        )
        quest_objectives = extra_data.get(
            'quest_objectives', ''
        )
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            reactor['class'], reactor_name,
        )
        prompt = (
            build_quest_accept_reaction_prompt(
                reactor, reactor_traits,
                acceptor_name, quest_name,
                quest_level,
                zone_name, mode,
                chat_history=chat_hist,
                quest_details=quest_details,
                quest_objectives=quest_objectives,
                speaker_talent_context=speaker_talent,
                stored_tone=stored_tone,
                zone_id=zone_id,
            )
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-qacc:#{event_id}"
                f":{reactor_name}"
            ),
            label='reaction_quest_accept',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'quest'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_quest_accept_batch_event(
    db, client, config, event
):
    """Handle a bot_group_quest_accept_batch event.

    Multiple quests accepted within the debounce
    window → one generic 'lots of work' reaction.
    """
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_quest_accept_batch'
    )

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    acceptor_name = extra_data.get(
        'acceptor_name', 'someone'
    )
    quest_names = extra_data.get(
        'quest_names', []
    )
    if not isinstance(quest_names, list):
        quest_names = []
    zone_name = extra_data.get(
        'zone_name', 'somewhere'
    )
    group_id = int(
        extra_data.get('group_id', 0)
    )

    if not reactor_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    if not quest_names:
        _mark_event(db, event_id, 'skipped')
        return False

    # Player zone as source of truth
    zone_name = _resolve_zone_name(
        db, group_id, zone_name
    )

    trait_data = get_bot_traits(
        db, group_id, reactor_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False
    reactor_traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        zone_id, _, _ = get_group_location(
            db, group_id
        )
        speaker_talent = _maybe_talent_context(
            config, db, reactor_guid,
            reactor['class'], reactor_name,
        )
        prompt = build_quest_accept_batch_prompt(
            reactor, reactor_traits,
            acceptor_name, quest_names,
            zone_name, mode,
            chat_history=chat_hist,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
            zone_id=zone_id,
        )
        mood_label = get_bot_mood_label(
            group_id, reactor_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-qbatch:#{event_id}"
                f":{reactor_name}"
            ),
            label='reaction_quest_accept',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        _store_chat(
            db, group_id, reactor_guid,
            reactor_name, True, message
        )

        update_bot_mood(
            group_id, reactor_guid, 'quest'
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        prompt = build_dungeon_entry_prompt(
            db, bot, traits, map_name, is_raid,
            map_id, mode,
            chat_history=chat_hist,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
        )

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
            label='reaction_dungeon_entry',
            context=(
                f"grp-dungeon:#{event_id}"
                f":{bot_name}"
            ),
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        # Dungeon memory is now handled at join time
        # (process_group_event / process_group_join_batch)
        # where traits are guaranteed to exist.
        # Removed from here to avoid double-firing.

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        _, _, map_id = get_group_location(
            db, group_id
        )
        prompt = build_wipe_reaction_prompt(
            bot, traits, killer_name, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
            map_id=map_id,
        )
        mood_label = get_bot_mood_label(
            group_id, bot_guid
        )
        if mood_label != 'neutral':
            prompt += (
                f"\nCurrent mood: {mood_label}"
            )

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
            context=(
                f"grp-wipe:#{event_id}"
                f":{bot_name}"
            ),
            label='reaction_wipe',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        update_bot_mood(
            group_id, bot_guid, 'wipe'
        )

        # Memory: wipe
        try:
            wipe_chance = int(config.get(
                'LLMChatter.Memory'
                '.WipeGenerationChance', 80
            ))
            if random.random() * 100 < wipe_chance:
                context = "Total party wipe"
                if killer_name:
                    context = (
                        f"Wiped to {killer_name}"
                    )
                queue_memory(
                    config, group_id,
                    bot_guid, 0,
                    memory_type='wipe',
                    event_context=context,
                    bot_name=bot_name,
                    bot_class=bot['class'],
                    bot_race=bot['race'],
                )
        except Exception:
            logger.error(
                "wipe memory failed",
                exc_info=True,
            )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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

    # Player zone as source of truth
    zone_name = _resolve_zone_name(
        db, group_id, zone_name
    )

    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        map_id = int(event.get('map_id') or 0)
        prompt = build_corpse_run_reaction_prompt(
            bot, traits, zone_name, mode,
            chat_history=chat_hist,
            dead_name=dead_name,
            is_player_death=is_player_death,
            speaker_talent_context=speaker_talent,
            stored_tone=stored_tone,
            map_id=map_id,
        )

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
            context=(
                f"grp-corpse:#{event_id}"
                f":{bot_name}"
            ),
            label='reaction_corpse_run',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
        _mark_event(db, event_id, 'skipped')
        return False

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
        # BG fallback: no traits, use BG dispatch
        if extra_data.get('is_battleground'):
            extra_data['event_type'] = (
                'bot_group_low_health')
            # Pin to event's bot so dispatch
            # speaks from the affected character
            extra_data['party_bot_guids'] = (
                [bot_guid])
            result = dual_worker_dispatch(
                db, client, config,
                event, extra_data,
                subgroup_prompt_fn=(
                    build_bg_low_health_prompt),
                raid_prompt_fn=None)
            _mark_event(
                db, event_id,
                'completed' if result
                else 'skipped')
            return result
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        prompt = build_low_health_callout_prompt(
            bot, traits, target_name, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            speaker_talent_context=speaker_talent,
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
            label='reaction_low_health',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
        # BG fallback: no traits, use BG dispatch
        if extra_data.get('is_battleground'):
            extra_data['event_type'] = (
                'bot_group_oom')
            # Pin to event's bot so dispatch
            # speaks from the affected character
            extra_data['party_bot_guids'] = (
                [bot_guid])
            result = dual_worker_dispatch(
                db, client, config,
                event, extra_data,
                subgroup_prompt_fn=(
                    build_bg_oom_prompt),
                raid_prompt_fn=None)
            _mark_event(
                db, event_id,
                'completed' if result
                else 'skipped')
            return result
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        prompt = build_oom_callout_prompt(
            bot, traits, target_name, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            speaker_talent_context=speaker_talent,
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
            label='reaction_oom',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
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
    stored_tone = trait_data.get('tone')

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
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )
        prompt = build_aggro_loss_callout_prompt(
            bot, traits, target_name,
            aggro_target, mode,
            chat_history=chat_hist,
            extra_data=extra_data,
            speaker_talent_context=speaker_talent,
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
            label='reaction_aggro_loss',
        )
        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']


        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message
        )
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
        _mark_event(db, event_id, 'skipped')
        return False


def process_group_nearby_object_event(
    db, client, config, event
):
    """Handle bot_group_nearby_object event.

    Branches between a single-bot statement and a
    multi-bot conversation based on
    NearbyObject.ConversationChance.
    """
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'), event_id,
        'bot_group_nearby_object')
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    bot_guid = int(extra.get('bot_guid', 0))
    bot_name = extra.get('bot_name', 'Unknown')
    group_id = int(extra.get('group_id', 0))
    objects = extra.get('objects', [])

    if not objects or not bot_guid:
        _mark_event(db, event_id, 'skipped')
        return False

    # Get triggering bot's traits
    trait_data = get_bot_traits(
        db, group_id, bot_guid)
    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

    # Mark as processing BEFORE LLM call
    _mark_event(db, event_id, 'processing')

    mode = get_chatter_mode(config)
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)
    bot_class_name = get_class_name(
        int(extra.get('bot_class', 0)))
    bot_race_name = get_race_name(
        int(extra.get('bot_race', 0)))

    zone_name = extra.get('zone_name', '')
    subzone_name = extra.get('subzone_name', '')

    # Player zone as source of truth for zone_name.
    # subzone_name stays from C++ extra_data (no
    # subzone in the characters table).
    zone_name = _resolve_zone_name(
        db, group_id, zone_name
    )

    in_city = extra.get('in_city', False)
    in_dungeon = extra.get('in_dungeon', False)

    # Look up subzone lore for richer context
    zone_id, area_id, map_id = get_group_location(
        db, group_id)
    subzone_lore = get_subzone_lore(
        zone_id, area_id
    )

    # Zone metadata for request logging
    zf = get_zone_flavor(zone_id)
    resolved_subzone = (
        subzone_name
        or get_subzone_name(zone_id, area_id)
    )
    zone_meta = build_zone_metadata(
        zone_name, zf,
        resolved_subzone, subzone_lore,
    )

    # -- Decide: conversation or statement? --
    members = get_group_members(db, group_id)
    conv_chance = int(config.get(
        'LLMChatter.NearbyObject.ConversationChance',
        40,
    ))
    do_conversation = (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    )

    if do_conversation:
        try:
            return _nearby_object_conversation(
                db, client, config, event_id,
                group_id, bot_guid, bot_name,
                members, objects,
                zone_name, subzone_name,
                in_city, in_dungeon,
                mode, chat_hist,
                subzone_lore=subzone_lore,
                zone_meta=zone_meta,
                map_id=map_id,
            )
        except Exception:
            _mark_event(
                db, event_id, 'skipped')
            return False

    # -- Single-bot statement (original path) --
    speaker_talent = _maybe_talent_context(
        config, db, bot_guid,
        bot_class_name, bot_name,
    )
    prompt = build_nearby_object_reaction_prompt(
        bot_name=bot_name,
        class_name=bot_class_name,
        race_name=bot_race_name,
        traits=traits,
        objects=objects,
        zone_name=zone_name,
        subzone_name=subzone_name,
        in_city=in_city,
        in_dungeon=in_dungeon,
        mode=mode,
        chat_history=chat_hist,
        config=config,
        speaker_talent_context=speaker_talent,
        subzone_lore=subzone_lore,
        map_id=map_id,
    )

    if speaker_talent:
        zone_meta['speaker_talent'] = (
            speaker_talent
        )
    result = run_single_reaction(
        db, client, config,
        prompt=prompt,
        speaker_name=bot_name,
        bot_guid=bot_guid,
        channel='party',
        delay_seconds=3,
        event_id=event_id,
        allow_emote_fallback=True,
        metadata=zone_meta,
        label='reaction_nearby_obj',
    )

    if not result['ok']:
        _mark_event(db, event_id, 'skipped')
        return False

    _store_chat(
        db, group_id, bot_guid,
        bot_name, True, result['message'])
    _mark_event(db, event_id, 'completed')
    return True


def _nearby_object_conversation(
    db, client, config, event_id,
    group_id, bot_guid, bot_name,
    members, objects,
    zone_name, subzone_name,
    in_city, in_dungeon,
    mode, chat_hist,
    subzone_lore=None,
    zone_meta=None,
    map_id=0,
):
    """Run a multi-bot conversation about nearby
    objects. Returns True on success."""

    # Pick 2 to min(4, num_members) random bots.
    # Ensure the triggering bot is included.
    num_pick = random.randint(
        2, min(len(members), 4)
    )
    other_names = [
        m for m in members if m != bot_name
    ]
    random.shuffle(other_names)
    picked = [bot_name] + other_names[
        :num_pick - 1
    ]
    random.shuffle(picked)

    # Gather traits and build bot dicts
    bots = []
    traits_map = {}
    bot_guids = {}
    for name in picked:
        # Look up guid + traits from the traits table
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT bot_guid, trait1, trait2, trait3
            FROM llm_group_bot_traits
            WHERE group_id = %s
                AND bot_name = %s
        """, (group_id, name))
        row = cursor.fetchone()
        if not row:
            continue
        guid = int(row['bot_guid'])
        bot_guids[name] = guid
        traits_map[name] = [
            row['trait1'], row['trait2'],
            row['trait3'],
        ]
        # Look up class/race/level from characters
        cursor.execute("""
            SELECT class, race, level
            FROM characters
            WHERE guid = %s
        """, (guid,))
        char = cursor.fetchone()
        if not char:
            continue
        bots.append({
            'name': name,
            'class': get_class_name(
                char['class']
            ),
            'race': get_race_name(char['race']),
            'level': char['level'],
        })

    if len(bots) < 2:
        # Not enough bots — fall back to skipped
        _mark_event(db, event_id, 'skipped')
        return False

    bot_names = [b['name'] for b in bots]
    num_bots = len(bots)

    # Talent context for first/triggering bot
    speaker_talent = _maybe_talent_context(
        config, db, bot_guid,
        bots[0]['class'] if bots else '',
        bot_name,
    )
    prompt = build_nearby_object_conversation_prompt(
        bots=bots,
        traits_map=traits_map,
        objects=objects,
        zone_name=zone_name,
        subzone_name=subzone_name,
        in_city=in_city,
        in_dungeon=in_dungeon,
        mode=mode,
        chat_history=chat_hist,
        config=config,
        speaker_talent_context=speaker_talent,
        subzone_lore=subzone_lore,
        map_id=map_id,
    )

    # Scale tokens with number of bots
    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    conv_tokens = min(
        max_tokens * (1 + num_bots), 1000
    )
    if speaker_talent:
        if zone_meta is None:
            zone_meta = {}
        zone_meta['speaker_talent'] = (
            speaker_talent
        )
    names_ctx = ','.join(bot_names)

    response = call_llm(
        client, prompt, config,
        max_tokens_override=conv_tokens,
        context=(
            f"nearby-obj-conv:{names_ctx}"
        ),
        label='group_nearby_obj',
        metadata=zone_meta,
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    messages = parse_conversation_response(
        response, bot_names
    )
    if not messages:
        _mark_event(db, event_id, 'skipped')
        return False


    # Insert messages with staggered delivery.
    # Only the first message gets an action.
    cumulative_delay = 2.0
    prev_len = 0
    for seq, msg in enumerate(messages):
        msg_text = msg['message']
        text = strip_speaker_prefix(
            msg_text, msg['name']
        )
        action = (
            msg.get('action')
            if should_include_action()
            else None
        )
        text = cleanup_message(
            text, action=action
        )
        if not text:
            continue
        if len(text) > 255:
            text = text[:252] + "..."

        speaker_guid = bot_guids.get(
            msg['name']
        )
        if not speaker_guid:
            continue

        if seq > 0:
            # Ambient idle path — full delay
            # simulation (responsive=False)
            delay = calculate_dynamic_delay(
                len(text), config,
                prev_message_length=prev_len,
            )
            cumulative_delay += delay

        insert_chat_message(
            db, speaker_guid, msg['name'],
            text, channel='party',
            delay_seconds=cumulative_delay,
            event_id=event_id, sequence=seq,
            emote=msg.get('emote'),
        )
        _store_chat(
            db, group_id, speaker_guid,
            msg['name'], True, text,
        )
        prev_len = len(text)

    _mark_event(db, event_id, 'completed')
    return True


def execute_player_msg_conversation(
    db, client, config, event_id,
    group_id, addressed_bot, all_bots,
    player_name, player_message, mode,
    chat_hist, members,
    item_context="", link_context="",
    items_info=None,
    zone_id=0, area_id=0, map_id=0,
):
    """Run a multi-bot conversation responding to
    a player's party chat message.

    Args:
        addressed_bot: dict with guid, name, class,
            race, level — the bot identified as
            primary responder
        all_bots: list of all bot rows from
            llm_group_bot_traits
        player_name: real player who spoke
        player_message: what the player said
        items_info: list of item detail dicts

    Returns True on success.
    """
    # Pick 2-3 bots total. Addressed bot is first.
    max_conv_bots = min(
        random.randint(2, 3), len(all_bots)
    )
    # Get other bots (not addressed)
    other_bots = [
        b for b in all_bots
        if b['bot_guid'] != addressed_bot['guid']
    ]
    random.shuffle(other_bots)
    extra_count = max_conv_bots - 1
    extra_rows = other_bots[:extra_count]

    # Build bot dicts and traits_map
    bots = [addressed_bot]
    traits_map = {
        addressed_bot['name']: [
            addressed_bot.get('trait1', ''),
            addressed_bot.get('trait2', ''),
            addressed_bot.get('trait3', ''),
        ]
    }
    bot_guids = {
        addressed_bot['name']:
            addressed_bot['guid']
    }

    for row in extra_rows:
        guid = int(row['bot_guid'])
        name = row['bot_name']
        traits_map[name] = [
            row.get('trait1', ''),
            row.get('trait2', ''),
            row.get('trait3', ''),
        ]
        bot_guids[name] = guid
        # Look up class/race/level
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT class, race, level
            FROM characters
            WHERE guid = %s
        """, (guid,))
        char = cursor.fetchone()
        if not char:
            bot_guids.pop(name, None)
            traits_map.pop(name, None)
            continue
        bots.append({
            'name': name,
            'guid': guid,
            'class': get_class_name(
                char['class']
            ),
            'race': get_race_name(char['race']),
            'level': char['level'],
        })

    if len(bots) < 2:
        return False

    bot_names = [b['name'] for b in bots]
    num_bots = len(bots)

    # Build shared item context for all bots
    conv_item_context = ""
    if items_info:
        conv_item_context = format_item_context(
            items_info, bots[0]['class']
        )

    # Talent context for first bot only
    speaker_talent = _maybe_talent_context(
        config, db, addressed_bot['guid'],
        addressed_bot['class'],
        addressed_bot['name'],
    )
    # Talent context for the player (target)
    target_talent = None
    player_info = get_character_info_by_name(
        db, player_name,
    )
    if player_info:
        target_talent = _maybe_talent_context(
            config, db, player_info['guid'],
            get_class_name(player_info['class']),
            player_name, perspective='target',
        )
    prompt = build_player_msg_conversation_prompt(
        bots=bots,
        traits_map=traits_map,
        player_name=player_name,
        player_message=player_message,
        mode=mode,
        chat_history=chat_hist,
        members=members,
        item_context=conv_item_context,
        link_context=link_context,
        speaker_talent_context=speaker_talent,
        target_talent_context=target_talent,
        zone_id=zone_id,
        area_id=area_id,
        map_id=map_id,
    )

    # Token budget: max_tokens * (1 + num_bots),
    # capped at 1000
    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    conv_tokens = min(
        max_tokens * (1 + num_bots), 1000
    )

    _dflav_conv = get_dungeon_flavor(map_id)
    pmsg_meta = build_zone_metadata(
        zone_name=get_zone_name(zone_id) or '',
        zone_flavor=get_zone_flavor(zone_id) or '',
        subzone_name=(
            get_subzone_name(zone_id, area_id)
            or ''
        ),
        subzone_lore=(
            get_subzone_lore(zone_id, area_id)
            or ''
        ),
        dungeon_name=(
            _dflav_conv.split(':')[0].strip()
            if _dflav_conv else ''
        ),
        dungeon_flavor=_dflav_conv or '',
    )
    if speaker_talent:
        pmsg_meta['speaker_talent'] = (
            speaker_talent
        )
    if target_talent:
        pmsg_meta['target_talent'] = (
            target_talent
        )
    names_ctx = ','.join(bot_names)

    response = call_llm(
        client, prompt, config,
        max_tokens_override=conv_tokens,
        context=(
            f"pmsg-conv:{names_ctx}"
        ),
        label='group_player_msg_conv',
        metadata=pmsg_meta or None,
    )
    if not response:
        return False

    messages = parse_conversation_response(
        response, bot_names
    )
    if not messages:
        return False


    # Insert messages with staggered delivery.
    # Only the first message gets an action.
    # Player msg conversations use responsive
    # timing — player is actively waiting.
    cumulative_delay = 2.0
    prev_len = 0
    for seq, msg in enumerate(messages):
        msg_text = msg['message']
        text = strip_speaker_prefix(
            msg_text, msg['name']
        )
        action = (
            msg.get('action')
            if should_include_action()
            else None
        )
        text = cleanup_message(
            text, action=action
        )
        if not text:
            continue
        if len(text) > 255:
            text = text[:252] + "..."

        speaker_guid = bot_guids.get(
            msg['name']
        )
        if not speaker_guid:
            continue

        if seq > 0:
            # Skip prev_message_length — all msgs
            # were generated in one LLM call, no
            # "reading" time needed between speakers
            delay = calculate_dynamic_delay(
                len(text), config,
                responsive=True,
            )
            cumulative_delay += delay

        emote = msg.get('emote')
        insert_chat_message(
            db, speaker_guid, msg['name'],
            text, channel='party',
            delay_seconds=cumulative_delay,
            event_id=event_id, sequence=seq,
            emote=emote,
        )
        _store_chat(
            db, group_id, speaker_guid,
            msg['name'], True, text,
        )
        prev_len = len(text)

    return True


# ============================================================
# QUEST CONVERSATION HELPERS
# ============================================================

def _quest_conversation_pick_bots(
    db, group_id, reactor_name, members,
):
    """Pick 2-3 bots for a quest conversation.
    Reactor is always included. Returns
    (bots, traits_map, bot_guids) or None
    if fewer than 2 bots are available.
    """
    num_pick = random.randint(
        2, min(len(members), 3)
    )
    other_names = [
        m for m in members if m != reactor_name
    ]
    random.shuffle(other_names)
    picked = [reactor_name] + other_names[
        :num_pick - 1
    ]
    random.shuffle(picked)

    bots = []
    traits_map = {}
    bot_guids = {}
    for name in picked:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT bot_guid, trait1, trait2, trait3
            FROM llm_group_bot_traits
            WHERE group_id = %s
                AND bot_name = %s
        """, (group_id, name))
        row = cursor.fetchone()
        if not row:
            continue
        guid = int(row['bot_guid'])
        bot_guids[name] = guid
        traits_map[name] = [
            row['trait1'], row['trait2'],
            row['trait3'],
        ]
        cursor.execute("""
            SELECT class, race, level
            FROM characters
            WHERE guid = %s
        """, (guid,))
        char = cursor.fetchone()
        if not char:
            continue
        bots.append({
            'name': name,
            'class': get_class_name(
                char['class']
            ),
            'race': get_race_name(char['race']),
            'level': char['level'],
        })

    if len(bots) < 2:
        return None

    return bots, traits_map, bot_guids


def _quest_conversation_deliver(
    db, config, event_id, group_id,
    messages, bot_guids, reactor_guid,
):
    """Insert parsed conversation messages with
    staggered delays. Updates mood for first
    speaker only. Returns True on success.
    """
    cumulative_delay = 2.0
    prev_len = 0
    for seq, msg in enumerate(messages):
        msg_text = msg['message']
        text = strip_speaker_prefix(
            msg_text, msg['name']
        )
        action = (
            msg.get('action')
            if should_include_action()
            else None
        )
        text = cleanup_message(
            text, action=action
        )
        if not text:
            continue
        if len(text) > 255:
            text = text[:252] + "..."

        speaker_guid = bot_guids.get(
            msg['name']
        )
        if not speaker_guid:
            continue

        if seq > 0:
            delay = calculate_dynamic_delay(
                len(text), config,
                prev_message_length=prev_len,
            )
            cumulative_delay += delay

        insert_chat_message(
            db, speaker_guid, msg['name'],
            text, channel='party',
            delay_seconds=cumulative_delay,
            event_id=event_id, sequence=seq,
            emote=msg.get('emote'),
        )
        _store_chat(
            db, group_id, speaker_guid,
            msg['name'], True, text,
        )
        prev_len = len(text)

    _mark_event(db, event_id, 'completed')
    return True


def _quest_complete_conversation(
    db, client, config, event_id,
    group_id, reactor_name, reactor_guid,
    members, completer_name, quest_name,
    extra_data,
):
    """Run a multi-bot conversation about a quest
    completion. Returns True on success, False
    to fall back to statement path.
    """
    result = _quest_conversation_pick_bots(
        db, group_id, reactor_name, members,
    )
    if not result:
        return False
    bots, traits_map, bot_guids = result

    mode = get_chatter_mode(config)
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)
    zone_id, _, _ = get_group_location(
        db, group_id
    )

    quest_id = int(
        extra_data.get('quest_id', 0)
    )
    turnin_npc = None
    if quest_id:
        turnin_npc = query_quest_turnin_npc(
            config, quest_id
        )

    quest_details = extra_data.get(
        'quest_details', ''
    )
    quest_objectives = extra_data.get(
        'quest_objectives', ''
    )

    msg_count = max(
        len(bots), random.randint(2, 3)
    )

    speaker_talent = _maybe_talent_context(
        config, db, reactor_guid,
        bots[0]['class'] if bots else '',
        reactor_name,
    )
    prompt = build_quest_complete_conversation_prompt(
        bots=bots,
        traits_map=traits_map,
        completer_name=completer_name,
        quest_name=quest_name,
        mode=mode,
        chat_history=chat_hist,
        turnin_npc=turnin_npc,
        quest_details=quest_details,
        quest_objectives=quest_objectives,
        msg_count=msg_count,
        speaker_talent_context=speaker_talent,
        zone_id=zone_id,
    )

    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]
    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    conv_tokens = min(
        max_tokens * (1 + num_bots), 1000
    )

    qc_meta = {}
    if speaker_talent:
        qc_meta['speaker_talent'] = (
            speaker_talent
        )
    names_ctx = ','.join(bot_names)

    response = call_llm(
        client, prompt, config,
        max_tokens_override=conv_tokens,
        context=(
            f"quest-complete-conv:{names_ctx}"
        ),
        label='group_quest_conv',
        metadata=qc_meta or None,
    )
    if not response:
        return False

    messages = parse_conversation_response(
        response, bot_names
    )
    if not messages:
        return False

    return _quest_conversation_deliver(
        db, config, event_id, group_id,
        messages, bot_guids, reactor_guid,
    )


def _quest_objectives_conversation(
    db, client, config, event_id,
    group_id, reactor_name, reactor_guid,
    members, completer_name, quest_name,
    extra_data,
):
    """Run a multi-bot conversation about quest
    objectives being completed. Returns True on
    success, False to fall back to statement path.
    """
    result = _quest_conversation_pick_bots(
        db, group_id, reactor_name, members,
    )
    if not result:
        return False
    bots, traits_map, bot_guids = result

    mode = get_chatter_mode(config)
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)
    zone_id, _, _ = get_group_location(
        db, group_id
    )

    quest_details = extra_data.get(
        'quest_details', ''
    )
    quest_objectives = extra_data.get(
        'quest_objectives', ''
    )

    msg_count = max(
        len(bots), random.randint(2, 3)
    )

    speaker_talent = _maybe_talent_context(
        config, db, reactor_guid,
        bots[0]['class'] if bots else '',
        reactor_name,
    )
    prompt = (
        build_quest_objectives_conversation_prompt(
            bots=bots,
            traits_map=traits_map,
            quest_name=quest_name,
            completer_name=completer_name,
            mode=mode,
            chat_history=chat_hist,
            quest_details=quest_details,
            quest_objectives=quest_objectives,
            msg_count=msg_count,
            speaker_talent_context=speaker_talent,
            zone_id=zone_id,
        )
    )

    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]
    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    conv_tokens = min(
        max_tokens * (1 + num_bots), 1000
    )

    qo_meta = {}
    if speaker_talent:
        qo_meta['speaker_talent'] = (
            speaker_talent
        )
    names_ctx = ','.join(bot_names)

    response = call_llm(
        client, prompt, config,
        max_tokens_override=conv_tokens,
        context=(
            f"quest-obj-conv:{names_ctx}"
        ),
        label='group_quest_conv',
        metadata=qo_meta or None,
    )
    if not response:
        return False

    messages = parse_conversation_response(
        response, bot_names
    )
    if not messages:
        return False

    return _quest_conversation_deliver(
        db, config, event_id, group_id,
        messages, bot_guids, reactor_guid,
    )


def _quest_accept_conversation(
    db, client, config, event_id,
    group_id, reactor_name, reactor_guid,
    members, acceptor_name, quest_name,
    quest_level, zone_name, extra_data,
):
    """Run a multi-bot conversation about
    accepting a new quest. Returns True on
    success, False to fall back to statement path.
    """
    result = _quest_conversation_pick_bots(
        db, group_id, reactor_name, members,
    )
    if not result:
        return False
    bots, traits_map, bot_guids = result

    mode = get_chatter_mode(config)
    history = _get_recent_chat(db, group_id)
    chat_hist = format_chat_history(history)

    quest_details = extra_data.get(
        'quest_details', ''
    )
    quest_objectives = extra_data.get(
        'quest_objectives', ''
    )

    msg_count = max(
        len(bots), random.randint(2, 3)
    )

    speaker_talent = _maybe_talent_context(
        config, db, reactor_guid,
        bots[0]['class'] if bots else '',
        reactor_name,
    )
    zone_id, _, _ = get_group_location(
        db, group_id
    )
    prompt = build_quest_accept_conversation_prompt(
        bots=bots,
        traits_map=traits_map,
        acceptor_name=acceptor_name,
        quest_name=quest_name,
        quest_level=quest_level,
        zone_name=zone_name,
        mode=mode,
        chat_history=chat_hist,
        quest_details=quest_details,
        quest_objectives=quest_objectives,
        msg_count=msg_count,
        speaker_talent_context=speaker_talent,
        zone_id=zone_id,
    )

    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]
    max_tokens = int(config.get(
        'LLMChatter.MaxTokens', 200
    ))
    conv_tokens = min(
        max_tokens * (1 + num_bots), 1000
    )

    qa_meta = {}
    if speaker_talent:
        qa_meta['speaker_talent'] = (
            speaker_talent
        )
    names_ctx = ','.join(bot_names)

    response = call_llm(
        client, prompt, config,
        max_tokens_override=conv_tokens,
        context=(
            f"quest-acc-conv:{names_ctx}"
        ),
        label='group_quest_conv',
        metadata=qa_meta or None,
    )
    if not response:
        return False

    messages = parse_conversation_response(
        response, bot_names
    )
    if not messages:
        return False

    return _quest_conversation_deliver(
        db, config, event_id, group_id,
        messages, bot_guids, reactor_guid,
    )
