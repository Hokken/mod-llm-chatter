"""Group reaction handlers extracted from chatter_group (N6 batch 1)."""

import logging
import random
import re
from chatter_shared import (
    parse_extra_data,
    get_class_name,
    get_race_name,
    get_gender_label,
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
    strip_conversation_actions,
)
from chatter_db import (
    fail_event,
    get_group_location,
    insert_chat_message,
    get_character_info_by_name,
)
from chatter_constants import BG_MAP_NAMES, RAID_MAP_IDS
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
from chatter_raid_prompts import (
    build_raid_battle_cry_prompt,
)
from chatter_handler_pipeline import (
    run_group_handler,
    _maybe_talent_context,
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


def _kill_post_success(db, ctx, message):
    """Memory: bots remember boss/rare kills."""
    is_boss = ctx['is_boss']
    is_rare = ctx['is_rare']
    if not (is_boss or is_rare):
        return
    mem_type = (
        'boss_kill' if is_boss else 'rare_kill'
    )
    config = ctx['config']
    group_id = ctx['group_id']
    creature_name = ctx['creature_name']
    boss_mem_chance = int(config.get(
        'LLMChatter.Memory'
        '.BossKillGenerationChance', 60
    ))
    mc = db.cursor(dictionary=True)
    mc.execute(
        "SELECT t.bot_guid, t.bot_name,"
        " c.class, c.race, c.gender"
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
                    f"Killed {creature_name}"
                ),
                bot_name=ab['bot_name'],
                bot_class=get_class_name(
                    ab['class']
                ),
                bot_race=get_race_name(
                    ab['race']
                ),
                bot_gender=get_gender_label(
                    ab.get('gender', 0)
                ),
            )
        except Exception:
            logger.error(
                "kill memory queue failed",
                exc_info=True,
            )


def process_group_kill_event(
    db, client, config, event
):
    """Handle a bot_group_kill event.

    The killing bot reacts to a boss/rare kill
    in party chat.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_kill',
        extract_fields=lambda ed: {
            'creature_name': ed.get(
                'creature_name', 'something'),
            'is_boss': bool(int(
                ed.get('is_boss', 0))),
            'is_rare': bool(int(
                ed.get('is_rare', 0))),
        },
        build_prompt=lambda ctx: (
            build_kill_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['creature_name'],
                ctx['is_boss'], ctx['is_rare'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                extra_data=ctx['extra_data'],
                allow_action=not ctx[
                    'extra_data'].get(
                    'is_battleground', False),
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
                map_id=ctx['map_id'],
            )
        ),
        needs_map_id=True,
        mood_key=lambda ctx: (
            'boss_kill' if ctx['is_boss']
            else 'kill'
        ),
        label='reaction_kill',
        post_success=_kill_post_success,
    )

def process_group_loot_event(
    db, client, config, event
):
    """Handle a bot_group_loot event.

    The looting bot reacts to picking up an item
    in party chat. Excitement scales with quality.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_loot',
        extract_fields=lambda ed: {
            'looter_name': ed.get(
                'looter_name',
                ed.get('bot_name', 'Unknown')),
            'item_name': ed.get(
                'item_name', 'something'),
            'item_quality': int(
                ed.get('item_quality', 2)),
            'item_entry': int(
                ed.get('item_entry', 0)),
        },
        build_prompt=lambda ctx: (
            build_loot_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['item_name'],
                ctx['item_quality'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                looter_name=(
                    None
                    if ctx['bot_name']
                        == ctx['looter_name']
                    else ctx['looter_name']
                ),
                extra_data=ctx['extra_data'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
                map_id=ctx['map_id'],
            )
        ),
        needs_map_id=True,
        mood_key=lambda ctx: (
            'epic_loot'
            if 4 <= ctx['item_quality'] < 200
            else 'loot'
        ),
        message_transform=lambda msg: (
            _loot_msg_xform(msg, event)
        ),
        label='reaction_loot',
    )


def _loot_msg_xform(raw_message, event):
    """Inject clickable item link into loot msg."""
    import json
    try:
        ed = json.loads(
            event.get('extra_data', '{}')
        )
    except Exception:
        return raw_message
    item_entry = int(ed.get('item_entry', 0))
    item_name = ed.get('item_name', '')
    item_quality = int(ed.get('item_quality', 2))
    if item_entry and item_name:
        link = format_item_link(
            item_entry, item_quality, item_name,
        )
        return re.sub(
            re.escape(item_name), link,
            raw_message, count=1,
            flags=re.IGNORECASE,
        )
    return raw_message

def _maybe_raid_battle_cry(
    db, client, config, extra_data,
    party_bot_guid,
):
    """Fire a raid battle cry if in a raid and
    fighting a boss/elite. Picks a DIFFERENT bot
    from the one that spoke in party chat.

    Gated by config chance and per-group cooldown.
    """
    group_id = int(
        extra_data.get('group_id', 0))
    if not group_id:
        return

    # Check if in a raid instance
    _, _, map_id = get_group_location(
        db, group_id)
    if map_id not in RAID_MAP_IDS:
        return

    # Must be boss or elite
    is_boss = bool(int(
        extra_data.get('is_boss', 0)))
    is_elite = bool(int(
        extra_data.get('is_elite', 0)))
    if not (is_boss or is_elite):
        return

    # Config chance gate
    chance = int(config.get(
        'LLMChatter.RaidChatter'
        '.BattleCryChance', 70))
    if chance <= 0:
        return
    if random.randint(1, 100) > chance:
        return

    # Pick a different bot
    cry_bot = get_other_group_bot(
        db, group_id, party_bot_guid)
    if not cry_bot:
        return

    # Build bot_data dict for the prompt
    cry_guid = cry_bot['guid']
    cry_name = cry_bot['name']

    # Skip dead/ghost bots — no battle cry
    # from a corpse
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT class, race, health "
        "FROM characters WHERE guid = %s",
        (cry_guid,),
    )
    row = cursor.fetchone()
    cursor.close()
    if not row or int(row.get('health', 0)) == 0:
        return

    bot_data = {
        'bot_name': cry_name,
        'race': '',
        'class': '',
        'traits': cry_bot.get('traits'),
    }
    if row:
        bot_data['race'] = get_race_name(
            row['race'])
        bot_data['class'] = get_class_name(
            row['class'])

    # Inject config and db for prompt builder
    extra_data['_config'] = config
    extra_data['_db'] = db

    prompt = build_raid_battle_cry_prompt(
        extra_data, bot_data,
        is_raid_worker=True,
    )

    result = run_single_reaction(
        db, client, config,
        prompt=prompt,
        speaker_name=cry_name,
        bot_guid=cry_guid,
        channel='raid',
        delay_seconds=2,
        allow_emote_fallback=False,
        max_tokens_override=100,
        context=(
            f"raid-battle-cry:{cry_name}"),
        label='raid_battle_cry',
    )

    return


def process_group_combat_event(
    db, client, config, event
):
    """Handle a bot_group_combat event.

    A bot shouts a short battle cry when engaging
    an elite or boss creature. If in a raid and
    fighting a boss/elite, also fires a raid-wide
    battle cry from a different bot.
    """
    # Pre-pipeline dedup: DB-based recent event check
    event_id = event['id']
    ed = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bot_group_combat',
    )
    if ed:
        bg = int(ed.get('bot_guid', 0))
        if bg and _has_recent_event(
            db, 'bot_group_combat', bg,
            seconds=60, exclude_id=event_id,
        ):
            _mark_event(db, event_id, 'skipped')
            return False

    result = run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_combat',
        extract_fields=lambda ed: {
            'creature_name': ed.get(
                'creature_name', 'something'),
            'is_boss': bool(int(
                ed.get('is_boss', 0))),
            'is_elite': bool(int(
                ed.get('is_elite', 0))),
        },
        build_prompt=lambda ctx: (
            build_combat_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['creature_name'],
                ctx['is_boss'], ctx['mode'],
                chat_history=ctx['chat_hist'],
                is_elite=ctx['is_elite'],
                extra_data=ctx['extra_data'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        delay_seconds=1,
        max_tokens_override=60,
        inject_mood=False,
        label='reaction_combat',
        bg_fallback_prompt=build_bg_combat_prompt,
    )

    # Attempt raid battle cry regardless of whether
    # the party reaction succeeded — the reactor bot
    # may lack traits but another bot can still shout.
    if ed:
        try:
            _maybe_raid_battle_cry(
                db, client, config, ed,
                int(ed.get('bot_guid', 0)),
            )
        except Exception:
            logger.error(
                "Raid battle cry failed",
                exc_info=True,
            )

    return result

def process_group_death_event(
    db, client, config, event
):
    """Handle a bot_group_death event.

    A DIFFERENT bot from the dead one reacts in
    party chat. If no other bot has traits, skip.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_death',
        extract_fields=lambda ed: {
            'dead_name': ed.get(
                'dead_name',
                ed.get('bot_name', 'someone')),
            'dead_guid': int(
                ed.get('dead_guid', 0)),
            'killer_name': ed.get(
                'killer_name', ''),
            'is_player_death': ed.get(
                'is_player_death', False),
        },
        build_prompt=lambda ctx: (
            build_death_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['dead_name'],
                ctx['killer_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                is_player_death=(
                    ctx['is_player_death']),
                extra_data=ctx['extra_data'],
                allow_action=not ctx[
                    'extra_data'].get(
                    'is_battleground', False),
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
                map_id=ctx['map_id'],
            )
        ),
        needs_map_id=True,
        delay_seconds=2,
        mood_key='death',
        label='reaction_death',
        bg_fallback_prompt=build_bg_death_prompt,
    )

def _levelup_post_success(db, ctx, message):
    """Memory: reactor + leveler remember level-up."""
    config = ctx['config']
    group_id = ctx['group_id']
    reactor_guid = ctx['bot_guid']
    reactor_name = ctx['bot_name']
    leveler_name = ctx['leveler_name']
    new_level = ctx['new_level']
    is_bot = ctx['is_bot']
    leveler_guid = ctx['leveler_guid']

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
            bot_class=ctx['bot']['class'],
            bot_race=ctx['bot']['race'],
            bot_gender=ctx['bot'].get(
                'gender', ''
            ),
        )

    # Leveler remembers own milestone (bot only)
    if is_bot and leveler_guid != reactor_guid:
        lv_c = db.cursor(dictionary=True)
        lv_c.execute(
            "SELECT class, race, gender FROM"
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
                bot_gender=get_gender_label(
                    lv_row.get('gender', 0)
                ),
            )


def process_group_levelup_event(
    db, client, config, event
):
    """Handle a bot_group_levelup event.

    A DIFFERENT bot congratulates the one who
    leveled up. If no other bot exists in the
    group, the leveling bot itself reacts.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_levelup',
        extract_fields=lambda ed: {
            'leveler_name': ed.get(
                'leveler_name',
                ed.get('bot_name', 'someone')),
            'leveler_guid': int(
                ed.get('leveler_guid', 0)),
            'new_level': int(
                ed.get('bot_level', 1)),
            'is_bot': bool(int(
                ed.get('is_bot', 1))),
        },
        build_prompt=lambda ctx: (
            build_levelup_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['leveler_name'],
                ctx['new_level'],
                ctx['is_bot'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_reactor_from_db=True,
        delay_seconds=2,
        mood_key='levelup',
        label='reaction_levelup',
        post_success=_levelup_post_success,
    )

def _quest_complete_memory(db, ctx, message):
    """Post-success: queue memory for quest
    completion."""
    mem_chance = int(ctx['config'].get(
        'LLMChatter.Memory'
        '.QuestGenerationChance', 40,
    ))
    if random.random() * 100 < mem_chance:
        queue_memory(
            ctx['config'], ctx['group_id'],
            ctx['bot_guid'], 0,
            memory_type='quest_complete',
            event_context=(
                f"Completed quest:"
                f" {ctx['quest_name']}"
            ),
            bot_name=ctx['bot_name'],
            bot_class=ctx['bot']['class'],
            bot_race=ctx['bot']['race'],
            bot_gender=ctx['bot'].get(
                'gender', ''
            ),
        )


def process_group_quest_complete_event(
    db, client, config, event
):
    """Handle a bot_group_quest_complete event.

    A DIFFERENT bot reacts to the quest completion.
    If no other bot exists, the completing bot
    itself reacts.
    """
    # -- Try conversation path first --
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_quest_complete',
    )
    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    conv_chance = int(config.get(
        'LLMChatter.GroupChatter'
        '.QuestConversationChance', 30,
    ))
    group_id = int(
        extra_data.get('group_id', 0)
    )
    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    completer_name = extra_data.get(
        'completer_name',
        extra_data.get('bot_name', 'someone'),
    )
    quest_name = extra_data.get(
        'quest_name', 'a quest'
    )
    members = (
        get_group_members(db, group_id)
        if group_id else []
    )

    if (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    ):
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
                # Memory: quest completion (conv)
                bot_class = get_class_name(int(
                    extra_data.get('bot_class', 0)
                ))
                bot_race = get_race_name(int(
                    extra_data.get('bot_race', 0)
                ))
                bot_gender = get_gender_label(int(
                    extra_data.get('bot_gender', 0)
                ))
                try:
                    mem_ch = int(config.get(
                        'LLMChatter.Memory'
                        '.QuestGenerationChance',
                        40,
                    ))
                    if (
                        random.random() * 100
                        < mem_ch
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
                            bot_class=bot_class,
                            bot_race=bot_race,
                            bot_gender=bot_gender,
                        )
                except Exception:
                    logger.error(
                        "quest_complete memory"
                        " failed (conv path)",
                        exc_info=True,
                    )
                return True
        except Exception:
            logger.error(
                "quest_complete conversation"
                " failed, falling through",
                exc_info=True,
            )

    # -- Fall through to statement via pipeline --
    def _extract(ed):
        quest_id = int(ed.get('quest_id', 0))
        turnin_npc = None
        if quest_id:
            turnin_npc = query_quest_turnin_npc(
                config, quest_id,
            )
        return {
            'completer_name': ed.get(
                'completer_name',
                ed.get('bot_name', 'someone'),
            ),
            'quest_name': ed.get(
                'quest_name', 'a quest',
            ),
            'quest_id': quest_id,
            'turnin_npc': turnin_npc,
            'quest_details': ed.get(
                'quest_details', '',
            ),
            'quest_objectives': ed.get(
                'quest_objectives', '',
            ),
        }

    def _build(ctx):
        return (
            build_quest_complete_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['completer_name'],
                ctx['quest_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                turnin_npc=ctx['turnin_npc'],
                quest_details=(
                    ctx['quest_details']
                ),
                quest_objectives=(
                    ctx['quest_objectives']
                ),
                speaker_talent_context=(
                    ctx['speaker_talent']
                ),
                stored_tone=ctx['stored_tone'],
                zone_id=ctx.get('zone_id', 0),
            )
        )

    return run_group_handler(
        db, client, config, event,
        event_type_label=(
            'bot_group_quest_complete'
        ),
        extract_fields=_extract,
        build_prompt=_build,
        delay_seconds=2,
        mood_key='quest',
        label='reaction_quest_complete',
        post_success=_quest_complete_memory,
        pre_parsed_extra=extra_data,
        needs_map_id=True,
    )

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
        'bot_group_quest_objectives',
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
    completer_name = extra_data.get(
        'completer_name',
        extra_data.get('bot_name', 'someone'),
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

    # DB-level dedup: skip if recent objectives
    # event for this bot within 60 seconds
    if _has_recent_event(
        db, 'bot_group_quest_objectives',
        reactor_guid, 60,
        exclude_id=event_id,
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    # -- Try conversation path first --
    conv_chance = int(config.get(
        'LLMChatter.GroupChatter'
        '.QuestConversationChance', 30,
    ))
    members = get_group_members(db, group_id)

    if (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    ):
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
            logger.error(
                "quest_objectives conversation"
                " failed, falling through",
                exc_info=True,
            )

    def _extract(ed):
        return {
            'completer_name': ed.get(
                'completer_name',
                ed.get('bot_name', 'someone'),
            ),
            'quest_name': ed.get(
                'quest_name', 'a quest',
            ),
            'quest_details': ed.get(
                'quest_details', '',
            ),
            'quest_objectives': ed.get(
                'quest_objectives', '',
            ),
        }

    def _build(ctx):
        return (
            build_quest_objectives_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['quest_name'],
                ctx['completer_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                quest_details=(
                    ctx['quest_details']
                ),
                quest_objectives=(
                    ctx['quest_objectives']
                ),
                speaker_talent_context=(
                    ctx['speaker_talent']
                ),
                stored_tone=ctx['stored_tone'],
                zone_id=ctx.get('zone_id', 0),
            )
        )

    return run_group_handler(
        db, client, config, event,
        event_type_label=(
            'bot_group_quest_objectives'
        ),
        extract_fields=_extract,
        build_prompt=_build,
        delay_seconds=2,
        label='reaction_quest_complete',
        inject_mood=False,
        needs_reactor_from_db=True,
        pre_parsed_extra=extra_data,
        needs_map_id=True,
    )

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


def _achievement_post_success(db, ctx, message):
    """Memory: ALL bots remember the achievement.
    Skip in BG (achievements fire constantly).
    """
    if ctx['extra_data'].get('is_battleground'):
        return
    config = ctx['config']
    group_id = ctx['group_id']
    achievement_name = ctx['achievement_name']
    achv_chance = int(config.get(
        'LLMChatter.Memory'
        '.AchievementGenerationChance', 35
    ))
    mc = db.cursor(dictionary=True)
    mc.execute(
        "SELECT t.bot_guid, t.bot_name,"
        " c.class, c.race, c.gender"
        " FROM llm_group_bot_traits t"
        " JOIN characters c"
        "   ON c.guid = t.bot_guid"
        " WHERE t.group_id = %s",
        (group_id,),
    )
    all_bots = mc.fetchall()
    for ab in all_bots:
        if random.random() * 100 >= achv_chance:
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
                bot_gender=get_gender_label(
                    ab.get('gender', 0)
                ),
            )
        except Exception:
            logger.error(
                "achievement memory queue failed",
                exc_info=True,
            )


def process_group_achievement_event(
    db, client, config, event
):
    """Handle a bot_group_achievement event.

    A DIFFERENT bot reacts to the achievement.
    Achievements are special -- more excited than
    regular events. If no other bot exists, the
    achieving bot itself reacts.
    """
    # --- Pre-pipeline: batch dedup + reactor ---
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bot_group_achievement',
    )
    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    achiever_guid = int(
        extra_data.get('bot_guid', 0)
    )
    achiever_name = extra_data.get(
        'achiever_name',
        extra_data.get('bot_name', 'someone'),
    )
    achievement_name = extra_data.get(
        'achievement_name', 'an achievement',
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

    # Achievement batch dedup
    batch_result = _check_achievement_batch(
        db, event_id, group_id, achievement_name,
    )
    if batch_result == 'already_batched':
        _mark_event(db, event_id, 'completed')
        return True
    batched_names = batch_result

    # Pick a different bot to react
    reactor_data = get_other_group_bot(
        db, group_id, achiever_guid,
    )
    if reactor_data:
        reactor_guid = reactor_data['guid']
        reactor_name = reactor_data['name']
    else:
        # No other bot -- achiever reacts
        trait_data = get_bot_traits(
            db, group_id, achiever_guid,
        )
        if not trait_data:
            if extra_data.get('is_battleground'):
                extra_data['event_type'] = (
                    'bot_group_achievement')
                result = dual_worker_dispatch(
                    db, client, config,
                    event, extra_data,
                    subgroup_prompt_fn=(
                        build_bg_achievement_prompt),
                    raid_prompt_fn=None,
                )
                _mark_event(
                    db, event_id,
                    'completed' if result
                    else 'skipped',
                )
                return result
            _mark_event(db, event_id, 'skipped')
            return False
        reactor_guid = achiever_guid
        reactor_name = achiever_name

    # Re-check status (batch owner may have
    # already completed this event)
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT status FROM llm_chatter_events "
        "WHERE id = %s",
        (event_id,),
    )
    status_row = cursor.fetchone()
    if (
        status_row
        and status_row['status'] == 'completed'
    ):
        return True

    # Inject resolved reactor into extra_data
    # so the pipeline uses the correct speaker
    import json as _json
    ed_raw = event.get('extra_data', '{}')
    try:
        ed_mut = _json.loads(ed_raw)
    except Exception:
        ed_mut = {}
    ed_mut['bot_guid'] = reactor_guid
    ed_mut['bot_name'] = reactor_name
    event = dict(event)
    event['extra_data'] = _json.dumps(ed_mut)

    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_achievement',
        extract_fields=lambda ed: {
            'achiever_name': achiever_name,
            'achievement_name': achievement_name,
            'is_bot': is_bot,
            'batched_names': batched_names,
        },
        build_prompt=lambda ctx: (
            build_group_achievement_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['batched_names'],
                ctx['achievement_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
                map_id=ctx['map_id'],
            )
            if ctx['batched_names']
            else build_achievement_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['achiever_name'],
                ctx['achievement_name'],
                ctx['is_bot'], ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                map_id=ctx['map_id'],
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_map_id=True,
        needs_reactor_from_db=True,
        delay_seconds=2,
        mood_key='achievement',
        label='reaction_achievement',
        post_success=_achievement_post_success,
    )

def process_group_spell_cast_event(
    db, client, config, event
):
    """Handle a bot_group_spell_cast event.

    A bot reacts to a notable spell cast (heal, cc,
    resurrect, shield) in party chat.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_spell_cast',
        extract_fields=lambda ed: {
            'caster_name': ed.get(
                'caster_name', 'someone'),
            'spell_name': ed.get(
                'spell_name', 'a spell'),
            'spell_category': ed.get(
                'spell_category', 'heal'),
            'target_name': ed.get(
                'target_name', 'someone'),
        },
        build_prompt=lambda ctx: (
            build_spell_cast_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['caster_name'],
                ctx['spell_name'],
                ctx['spell_category'],
                ctx['target_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                members=get_group_members(
                    ctx['db'], ctx['group_id']),
                dungeon_bosses=(
                    get_dungeon_bosses(
                        ctx['db'], ctx['map_id'])
                    if ctx['dungeon_flavor']
                    else None
                ),
                extra_data=ctx['extra_data'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_map_id=True,
        delay_seconds=lambda ctx: random.randint(
            2, 3),
        inject_mood=False,
        label='reaction_spell',
        bg_fallback_prompt=(
            build_bg_spell_cast_prompt),
    )

def process_group_resurrect_event(
    db, client, config, event
):
    """Handle a bot_group_resurrect event.

    The resurrected bot itself reacts with gratitude
    or relief in party chat.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_resurrect',
        extract_fields=lambda ed: {},
        build_prompt=lambda ctx: (
            build_resurrect_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_reactor_from_db=True,
        delay_seconds=2,
        mood_key='resurrect',
        label='reaction_rez',
    )

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

    # The queued GUID is the real player (zone
    # transitions are player-centric). Try bot
    # traits first; if that fails (player GUID),
    # pick a random bot from the group to react.
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    )
    if not trait_data:
        reactor = get_other_group_bot(
            db, group_id, bot_guid)
        if not reactor:
            _mark_event(db, event_id, 'skipped')
            return False
        bot_guid = reactor['guid']
        bot_name = reactor['name']
        trait_data = get_bot_traits(
            db, group_id, bot_guid)
        if not trait_data:
            _mark_event(db, event_id, 'skipped')
            return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

    # Get class/race from characters table
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT class, race, level, gender
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
        'gender': get_gender_label(char_row['gender']),
    }


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
        members = get_group_members(db, group_id)
        solo_bot = len(members) <= 1
        player_name = get_group_player_name(
            db, group_id
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
            player_name=player_name,
            solo_bot=solo_bot,
        )

        # Use raid chat in raid instances so all
        # sub-groups see the message
        zt_channel = (
            'raid' if map_id in RAID_MAP_IDS
            else 'party'
        )

        result = run_single_reaction(
            db,
            client,
            config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot_guid,
            channel=zt_channel,
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
                    bot_gender=bot.get(
                        'gender', ''
                    ),
                )
        except Exception:
            logger.error(
                "ambient memory failed",
                exc_info=True,
            )

        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
        fail_event(
            db, event_id,
            'bot_group_zone_transition',
            'handler error',
        )
        return False

def process_group_quest_accept_event(
    db, client, config, event
):
    """Handle a bot_group_quest_accept event.

    A bot reacts to the group accepting a new quest.
    The C++ hook pre-selects the reactor bot.
    """
    # -- Try conversation path first --
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_quest_accept',
    )
    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    conv_chance = int(config.get(
        'LLMChatter.GroupChatter'
        '.QuestConversationChance', 30,
    ))
    group_id = int(
        extra_data.get('group_id', 0)
    )
    reactor_guid = int(
        extra_data.get('bot_guid', 0)
    )
    reactor_name = extra_data.get(
        'bot_name', 'Unknown'
    )
    acceptor_name = extra_data.get(
        'acceptor_name',
        extra_data.get('bot_name', 'someone'),
    )
    quest_name = extra_data.get(
        'quest_name', 'a quest'
    )
    quest_level = int(
        extra_data.get('quest_level', 0)
    )
    zone_name = _resolve_zone_name(
        db, group_id,
        extra_data.get('zone_name', 'somewhere'),
    )
    members = (
        get_group_members(db, group_id)
        if group_id else []
    )

    if (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    ):
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
            logger.error(
                "quest_accept conversation"
                " failed, falling through",
                exc_info=True,
            )

    # -- Fall through to statement via pipeline --
    def _extract(ed):
        return {
            'acceptor_name': ed.get(
                'acceptor_name',
                ed.get('bot_name', 'someone'),
            ),
            'quest_name': ed.get(
                'quest_name', 'a quest',
            ),
            'quest_level': int(
                ed.get('quest_level', 0)
            ),
            'zone_name': zone_name,
            'quest_details': ed.get(
                'quest_details', '',
            ),
            'quest_objectives': ed.get(
                'quest_objectives', '',
            ),
        }

    def _build(ctx):
        return (
            build_quest_accept_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['acceptor_name'],
                ctx['quest_name'],
                ctx['quest_level'],
                ctx['zone_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                quest_details=(
                    ctx['quest_details']
                ),
                quest_objectives=(
                    ctx['quest_objectives']
                ),
                speaker_talent_context=(
                    ctx['speaker_talent']
                ),
                stored_tone=ctx['stored_tone'],
                zone_id=ctx.get('zone_id', 0),
            )
        )

    return run_group_handler(
        db, client, config, event,
        event_type_label=(
            'bot_group_quest_accept'
        ),
        extract_fields=_extract,
        build_prompt=_build,
        delay_seconds=2,
        mood_key='quest',
        label='reaction_quest_accept',
        pre_parsed_extra=extra_data,
        needs_map_id=True,
    )


def process_group_quest_accept_batch_event(
    db, client, config, event
):
    """Handle a bot_group_quest_accept_batch event.

    Multiple quests accepted within the debounce
    window -- one generic 'lots of work' reaction.
    """
    # Pre-pipeline: validate quest_names
    event_id = event['id']
    ed = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bot_group_quest_accept_batch',
    )
    if ed:
        qn = ed.get('quest_names', [])
        if not isinstance(qn, list) or not qn:
            _mark_event(db, event_id, 'skipped')
            return False

    return run_group_handler(
        db, client, config, event,
        event_type_label=(
            'bot_group_quest_accept_batch'),
        extract_fields=lambda ed: {
            'acceptor_name': ed.get(
                'acceptor_name', 'someone'),
            'quest_names': (
                ed.get('quest_names', [])
                if isinstance(
                    ed.get('quest_names', []),
                    list)
                else []
            ),
            'zone_name': _resolve_zone_name(
                db,
                int(ed.get('group_id', 0)),
                ed.get('zone_name', 'somewhere'),
            ),
        },
        build_prompt=lambda ctx: (
            build_quest_accept_batch_prompt(
                ctx['bot'], ctx['traits'],
                ctx['acceptor_name'],
                ctx['quest_names'],
                ctx['zone_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
                zone_id=ctx['extra_data'].get(
                    'zone_id', 0),
            )
        ),
        delay_seconds=2,
        mood_key='quest',
        label='reaction_quest_accept',
    )


def process_group_dungeon_entry_event(
    db, client, config, event
):
    """Handle a bot_group_dungeon_entry event.

    The bot that entered a dungeon or raid instance
    reacts in party chat.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_dungeon_entry',
        extract_fields=lambda ed: {
            'dungeon_map_id': int(
                ed.get('map_id', 0)),
            'map_name': ed.get(
                'map_name', 'a dungeon'),
            'is_raid': bool(int(
                ed.get('is_raid', 0))),
        },
        build_prompt=lambda ctx: (
            build_dungeon_entry_prompt(
                ctx['db'], ctx['bot'],
                ctx['traits'],
                ctx['map_name'],
                ctx['is_raid'],
                ctx['dungeon_map_id'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_reactor_from_db=True,
        delay_seconds=lambda ctx: random.randint(
            2, 4),
        inject_mood=False,
        label='reaction_dungeon_entry',
    )

def _wipe_post_success(db, ctx, message):
    """Memory: bot remembers the wipe."""
    config = ctx['config']
    group_id = ctx['group_id']
    bot_guid = ctx['bot_guid']
    bot_name = ctx['bot_name']
    killer_name = ctx['killer_name']
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
            bot_class=ctx['bot']['class'],
            bot_race=ctx['bot']['race'],
            bot_gender=ctx['bot'].get(
                'gender', ''
            ),
        )


def process_group_wipe_event(
    db, client, config, event
):
    """Handle a bot_group_wipe event.

    The designated bot reacts to a total party wipe
    in party chat.
    """
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_wipe',
        extract_fields=lambda ed: {
            'killer_name': ed.get(
                'killer_name', ''),
        },
        build_prompt=lambda ctx: (
            build_wipe_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['killer_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                extra_data=ctx['extra_data'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
                map_id=ctx['map_id'],
            )
        ),
        needs_map_id=True,
        needs_reactor_from_db=True,
        delay_seconds=2,
        mood_key='wipe',
        label='reaction_wipe',
        post_success=_wipe_post_success,
    )

def process_group_corpse_run_event(
    db, client, config, event
):
    """Handle a bot_group_corpse_run event.

    A bot comments on a corpse run -- either
    their own or the real player's. Humorous,
    philosophical, or resigned depending on
    personality.
    """
    # Capture event-level map_id before pipeline
    evt_map_id = int(event.get('map_id') or 0)

    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_corpse_run',
        extract_fields=lambda ed: {
            'zone_name': _resolve_zone_name(
                db, int(ed.get('group_id', 0)),
                ed.get('zone_name', '')),
            'dead_name': ed.get(
                'dead_name',
                ed.get('bot_name', 'someone')),
            'is_player_death': ed.get(
                'is_player_death', False),
            'evt_map_id': evt_map_id,
        },
        build_prompt=lambda ctx: (
            build_corpse_run_reaction_prompt(
                ctx['bot'], ctx['traits'],
                ctx['zone_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                dead_name=ctx['dead_name'],
                is_player_death=(
                    ctx['is_player_death']),
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
                map_id=ctx['evt_map_id'],
            )
        ),
        needs_reactor_from_db=True,
        delay_seconds=2,
        inject_mood=False,
        label='reaction_corpse_run',
    )

def process_group_low_health_event(
    db, client, config, event
):
    """Handle bot_group_low_health callout."""
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_low_health',
        extract_fields=lambda ed: {
            'target_name': ed.get(
                'target_name', ''),
        },
        build_prompt=lambda ctx: (
            build_low_health_callout_prompt(
                ctx['bot'], ctx['traits'],
                ctx['target_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                extra_data=ctx['extra_data'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_reactor_from_db=True,
        delay_seconds=1,
        max_tokens_override=60,
        inject_mood=False,
        label='reaction_low_health',
        bg_fallback_prompt=(
            build_bg_low_health_prompt),
    )

def process_group_oom_event(
    db, client, config, event
):
    """Handle bot_group_oom callout."""
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_oom',
        extract_fields=lambda ed: {
            'target_name': ed.get(
                'target_name', ''),
        },
        build_prompt=lambda ctx: (
            build_oom_callout_prompt(
                ctx['bot'], ctx['traits'],
                ctx['target_name'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                extra_data=ctx['extra_data'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_reactor_from_db=True,
        delay_seconds=1,
        max_tokens_override=60,
        inject_mood=False,
        label='reaction_oom',
        bg_fallback_prompt=build_bg_oom_prompt,
    )

def process_group_aggro_loss_event(
    db, client, config, event
):
    """Handle bot_group_aggro_loss callout."""
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_aggro_loss',
        extract_fields=lambda ed: {
            'target_name': ed.get(
                'target_name', ''),
            'aggro_target': ed.get(
                'aggro_target', 'someone'),
        },
        build_prompt=lambda ctx: (
            build_aggro_loss_callout_prompt(
                ctx['bot'], ctx['traits'],
                ctx['target_name'],
                ctx['aggro_target'],
                ctx['mode'],
                chat_history=ctx['chat_hist'],
                extra_data=ctx['extra_data'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        needs_reactor_from_db=True,
        delay_seconds=1,
        max_tokens_override=60,
        inject_mood=False,
        label='reaction_aggro_loss',
    )


def process_group_nearby_object_event(
    db, client, config, event
):
    """Handle bot_group_nearby_object event.

    Branches between a single-bot statement and a
    multi-bot conversation based on
    NearbyObject.ConversationChance.
    """
    # -- Try conversation path first --
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'), event_id,
        'bot_group_nearby_object',
    )
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

    # Pre-resolve zone data for both paths
    zone_name = _resolve_zone_name(
        db, group_id,
        extra.get('zone_name', ''),
    )
    subzone_name = extra.get('subzone_name', '')
    in_city = extra.get('in_city', False)
    in_dungeon = extra.get('in_dungeon', False)

    zone_id, area_id, map_id = (
        get_group_location(db, group_id)
    )
    subzone_lore = get_subzone_lore(
        zone_id, area_id,
    )
    zf = get_zone_flavor(zone_id)
    resolved_subzone = (
        subzone_name
        or get_subzone_name(zone_id, area_id)
    )
    zone_meta = build_zone_metadata(
        zone_name, zf,
        resolved_subzone, subzone_lore,
    )

    conv_chance = int(config.get(
        'LLMChatter.NearbyObject'
        '.ConversationChance', 40,
    ))
    members = (
        get_group_members(db, group_id)
        if group_id else []
    )

    if (
        len(members) >= 2
        and random.randint(1, 100) <= conv_chance
    ):
        try:
            mode = get_chatter_mode(config)
            history = _get_recent_chat(
                db, group_id,
            )
            chat_hist = format_chat_history(
                history,
            )
            ok = _nearby_object_conversation(
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
            if ok:
                return True
            # Conversation failed — fall through
            # to statement path below
        except Exception:
            logger.error(
                "nearby_object conversation "
                "failed, falling through",
                exc_info=True,
            )

    # -- Fall through to statement via pipeline --
    def _extract(ed):
        return {
            'objects': ed.get('objects', []),
            'zone_name': zone_name,
            'subzone_name': subzone_name,
            'in_city': in_city,
            'in_dungeon': in_dungeon,
            'subzone_lore': subzone_lore,
            'rich_zone_meta': zone_meta,
            'obj_map_id': map_id,
        }

    def _build(ctx):
        # Rebuild zone_meta in-place so the
        # pipeline passes it as metadata
        meta = ctx['zone_meta']
        rich = ctx['rich_zone_meta']
        meta.clear()
        meta.update(rich)

        prompt = (
            build_nearby_object_reaction_prompt(
                bot_name=ctx['bot_name'],
                class_name=ctx['bot']['class'],
                race_name=ctx['bot']['race'],
                traits=ctx['traits'],
                objects=ctx['objects'],
                zone_name=ctx['zone_name'],
                subzone_name=(
                    ctx['subzone_name']
                ),
                in_city=ctx['in_city'],
                in_dungeon=ctx['in_dungeon'],
                mode=ctx['mode'],
                chat_history=ctx['chat_hist'],
                config=ctx['config'],
                speaker_talent_context=(
                    ctx['speaker_talent']
                ),
                subzone_lore=(
                    ctx['subzone_lore']
                ),
                map_id=ctx['obj_map_id'],
                stored_tone=ctx['stored_tone'],
            )
        )
        if ctx['speaker_talent']:
            meta['speaker_talent'] = (
                ctx['speaker_talent']
            )
        return prompt

    return run_group_handler(
        db, client, config, event,
        event_type_label=(
            'bot_group_nearby_object'
        ),
        extract_fields=_extract,
        build_prompt=_build,
        delay_seconds=3,
        label='reaction_nearby_obj',
        inject_mood=False,
        pre_parsed_extra=extra,
    )


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
            SELECT class, race, level, gender
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
            'gender': get_gender_label(char['gender']),
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
    strip_conversation_actions(
        messages, label='nearby_obj_conv'
    )
    cumulative_delay = 2.0
    prev_len = 0
    for seq, msg in enumerate(messages):
        msg_text = msg['message']
        text = strip_speaker_prefix(
            msg_text, msg['name']
        )
        text = cleanup_message(
            text, action=msg.get('action')
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
            SELECT class, race, level, gender
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
            'gender': get_gender_label(char['gender']),
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
    # Player msg conversations use responsive
    # timing — player is actively waiting.
    strip_conversation_actions(
        messages, label='player_msg_conv'
    )
    cumulative_delay = 2.0
    prev_len = 0
    for seq, msg in enumerate(messages):
        msg_text = msg['message']
        text = strip_speaker_prefix(
            msg_text, msg['name']
        )
        text = cleanup_message(
            text, action=msg.get('action')
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
            SELECT class, race, level, gender
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
            'gender': get_gender_label(char['gender']),
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
    strip_conversation_actions(
        messages, label='quest_conv'
    )
    cumulative_delay = 2.0
    prev_len = 0
    for seq, msg in enumerate(messages):
        msg_text = msg['message']
        text = strip_speaker_prefix(
            msg_text, msg['name']
        )
        text = cleanup_message(
            text, action=msg.get('action')
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
