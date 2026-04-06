"""
chatter_battlegrounds.py — BG-specific event handlers for
mod-llm-chatter.

Each handler follows the bridge contract:
    handler(db, client, config, event) -> bool

Handlers parse extra_data, check suppression, dispatch
via dual_worker_dispatch, and mark event status.
"""

import logging
import random

logger = logging.getLogger(__name__)

from chatter_shared import (
    parse_extra_data,
    run_single_reaction,
)
from chatter_group_state import (
    _mark_event,
    get_bot_traits,
)
from chatter_raid_base import (
    dual_worker_dispatch,
    is_event_suppressed,
    get_subgroup_bots,
    get_lightweight_bot_data,
    _maybe_talent_context,
    DISPATCH_RAID_ONLY,
    DISPATCH_SUBGROUP_ONLY,
)
from chatter_memory import queue_memory
from chatter_bg_prompts import (
    build_bg_match_start_prompt,
    build_bg_match_end_prompt,
    build_bg_flag_prompt,
    build_bg_flag_return_prompt,
    build_bg_flag_carrier_prompt,
    build_bg_node_prompt,
    build_bg_pvp_kill_prompt,
    build_bg_score_milestone_prompt,
    build_bg_idle_prompt,
)
from chatter_constants import BG_LORE

LOG = logging.getLogger("chatter_battlegrounds")


def process_bg_match_start_event(
    db, client, config, event
):
    """Handle bg_match_start — gates open."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bg_match_start')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    if is_event_suppressed(
            'bg_match_start', extra_data):
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_bg_match_start_prompt),
        raid_prompt_fn=(
            build_bg_match_start_prompt),
        dispatch_mode=DISPATCH_RAID_ONLY,
        label='reaction_bg_match_start')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_bg_match_end_event(
    db, client, config, event
):
    """Handle bg_match_end — victory or defeat."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bg_match_end')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_bg_match_end_prompt),
        raid_prompt_fn=(
            build_bg_match_end_prompt),
        dispatch_mode=DISPATCH_RAID_ONLY,
        label='reaction_bg_match_end')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)

    # Memory: BG match result
    if result:
        try:
            mem_chance = int(config.get(
                'LLMChatter.Memory'
                '.BGMatchGenerationChance', 25
            ))
            if random.random() * 100 < mem_chance:
                won = extra_data.get('won', False)
                bg_type_id = int(
                    extra_data.get('bg_type_id', 0)
                )
                lore = BG_LORE.get(bg_type_id, {})
                bg_name = lore.get(
                    'name', 'a battleground'
                )
                group_id = int(
                    extra_data.get('group_id', 0)
                )
                party_guids = get_subgroup_bots(
                    extra_data
                )
                if party_guids and group_id:
                    bot_guid = random.choice(
                        party_guids
                    )
                    bot_data = (
                        get_lightweight_bot_data(
                            db, bot_guid
                        )
                    )
                    if bot_data:
                        queue_memory(
                            config, group_id,
                            bot_guid, 0,
                            memory_type=(
                                'bg_win' if won
                                else 'bg_loss'
                            ),
                            event_context=(
                                f"{'Won' if won else 'Lost'}"
                                f" {bg_name}"
                            ),
                            bot_name=bot_data[
                                'bot_name'],
                            bot_class=bot_data.get(
                                'class', ''),
                            bot_race=bot_data.get(
                                'race', ''),
                            bot_gender=bot_data.get(
                                'gender', ''),
                        )
        except Exception:
            logger.error(
                "bg_match memory failed",
                exc_info=True,
            )

    return result


def _try_carrier_self_message(
    db, client, config, event_id,
    event_type, extra_data
):
    """Fire a first-person message from the bot
    that picked up or dropped the flag.

    Only fires when the carrier/dropper is a bot
    (not a real player).
    """
    if event_type == 'bg_flag_picked_up':
        name = extra_data.get('carrier_name')
        guid = int(
            extra_data.get('carrier_guid', 0))
        is_real = extra_data.get(
            'carrier_is_real_player', False)
        action = 'pickup'
    elif event_type == 'bg_flag_dropped':
        name = extra_data.get('dropper_name')
        guid = int(
            extra_data.get('dropper_guid', 0))
        is_real = extra_data.get(
            'dropper_is_real_player', False)
        action = 'drop'
    else:
        return

    if not name or not guid:
        return
    # Real players speak for themselves
    if is_real:
        return

    bot_data = get_lightweight_bot_data(db, guid)
    if not bot_data:
        return

    # Skip if bot is on a different faction
    # than the event perspective
    # (race is a string name from
    #  get_lightweight_bot_data)
    event_team = extra_data.get('team', '')
    if event_team:
        race = bot_data.get('race', '')
        ALLIANCE_RACES = {
            'Human', 'Dwarf', 'Night Elf',
            'Gnome', 'Draenei',
        }
        HORDE_RACES = {
            'Orc', 'Undead', 'Tauren',
            'Troll', 'Blood Elf',
        }
        if (event_team == 'Alliance'
                and race not in ALLIANCE_RACES):
            return
        if (event_team == 'Horde'
                and race not in HORDE_RACES):
            return

    extra_data['_db'] = db
    extra_data['_config'] = config

    bot_class = bot_data.get('class', '')
    talent_ctx = _maybe_talent_context(
        config, db, guid,
        bot_class, name,
    )
    if talent_ctx:
        extra_data['_talent_context'] = (
            talent_ctx)
    else:
        extra_data.pop(
            '_talent_context', None)

    prompt = build_bg_flag_carrier_prompt(
        extra_data, bot_data, action)
    bg_max_tokens = int(config.get(
        'LLMChatter.BGChatter.MaxTokens',
        32,
    ))

    fc_meta = {}
    if talent_ctx:
        fc_meta['speaker_talent'] = talent_ctx
    run_single_reaction(
        db, client, config,
        prompt=prompt,
        speaker_name=name,
        bot_guid=guid,
        channel='party',
        delay_seconds=2,
        event_id=event_id,
        allow_emote_fallback=True,
        max_tokens_override=bg_max_tokens,
        context=(
            f"bg-flag-carrier:{action}"
            f":#{event_id}:{name}"),
        metadata=fc_meta or None,
        label='reaction_bg_carrier',
    )


def process_bg_flag_event(
    db, client, config, event
):
    """Handle bg_flag_picked_up, bg_flag_dropped,
    bg_flag_captured."""
    event_id = event['id']
    event_type = event.get('event_type', '')
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, event_type)

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    # Inject event_type into extra_data so prompt
    # builder can distinguish pickup/drop/capture
    extra_data['event_type'] = event_type

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=build_bg_flag_prompt,
        raid_prompt_fn=build_bg_flag_prompt,
        dispatch_mode=DISPATCH_RAID_ONLY,
        label='reaction_bg_flag')

    # Carrier bot first-person message (pickup/drop)
    _try_carrier_self_message(
        db, client, config, event_id,
        event_type, dict(extra_data))

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_bg_flag_return_event(
    db, client, config, event
):
    """Handle bg_flag_returned — flag returned
    to base by friendly player."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bg_flag_returned')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    extra_data['event_type'] = 'bg_flag_returned'

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_bg_flag_return_prompt),
        raid_prompt_fn=(
            build_bg_flag_return_prompt),
        dispatch_mode=DISPATCH_RAID_ONLY,
        label='reaction_bg_flag')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_bg_node_event(
    db, client, config, event
):
    """Handle bg_node_contested, bg_node_captured."""
    event_id = event['id']
    event_type = event.get('event_type', '')
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, event_type)

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    # Inject event_type for prompt builder
    extra_data['event_type'] = event_type

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=build_bg_node_prompt,
        raid_prompt_fn=None,
        dispatch_mode=DISPATCH_SUBGROUP_ONLY,
        label='reaction_bg_node')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_bg_pvp_kill_event(
    db, client, config, event
):
    """Handle bg_pvp_kill — PvP kill in BG context."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bg_pvp_kill')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_bg_pvp_kill_prompt),
        raid_prompt_fn=None,
        dispatch_mode=DISPATCH_SUBGROUP_ONLY,
        label='reaction_bg_pvp_kill')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)

    # Memory: PvP kill
    if result:
        try:
            mem_chance = int(config.get(
                'LLMChatter.Memory'
                '.PvPKillGenerationChance', 10
            ))
            if random.random() * 100 < mem_chance:
                victim_name = extra_data.get(
                    'victim_name', 'an enemy'
                )
                bg_type_id = int(
                    extra_data.get('bg_type_id', 0)
                )
                lore = BG_LORE.get(bg_type_id, {})
                bg_name = lore.get(
                    'name', 'a battleground'
                )
                group_id = int(
                    extra_data.get('group_id', 0)
                )
                party_guids = get_subgroup_bots(
                    extra_data
                )
                if party_guids and group_id:
                    bot_guid = random.choice(
                        party_guids
                    )
                    bot_data = (
                        get_lightweight_bot_data(
                            db, bot_guid
                        )
                    )
                    if bot_data:
                        queue_memory(
                            config, group_id,
                            bot_guid, 0,
                            memory_type='pvp_kill',
                            event_context=(
                                f"Killed"
                                f" {victim_name}"
                                f" in {bg_name}"
                            ),
                            bot_name=bot_data[
                                'bot_name'],
                            bot_class=bot_data.get(
                                'class', ''),
                            bot_race=bot_data.get(
                                'race', ''),
                            bot_gender=bot_data.get(
                                'gender', ''),
                        )
        except Exception:
            logger.error(
                "pvp_kill memory failed",
                exc_info=True,
            )

    return result


def process_bg_score_milestone_event(
    db, client, config, event
):
    """Handle bg_score_milestone — major score
    thresholds."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bg_score_milestone')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_bg_score_milestone_prompt),
        raid_prompt_fn=None,
        dispatch_mode=DISPATCH_SUBGROUP_ONLY,
        label='reaction_bg_score')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_bg_idle_chatter_event(
    db, client, config, event
):
    """Handle bg_idle_chatter -- ambient battle talk."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'bg_idle_chatter')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    if is_event_suppressed(
            'bg_idle_chatter', extra_data):
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=build_bg_idle_prompt,
        raid_prompt_fn=None,
        dispatch_mode=DISPATCH_SUBGROUP_ONLY,
        label='reaction_bg_idle')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


