"""
chatter_raid_base.py — Shared foundation for raid and BG chatter.

Provides dual-worker dispatch: sub-group (squad) worker for close
party reactions, and raid (crowd) worker for raid-wide callouts.
Both use run_single_reaction() from chatter_shared.py.

Created in Phase 1 (shared raid base). Called by BG handlers
(Phase 2) and future PvE raid handlers.
"""

import logging
import random
from typing import Any, Callable, Dict, List, Optional

from chatter_shared import (
    get_class_name,
    get_race_name,
    run_single_reaction,
    build_talent_context,
)
from chatter_group_state import get_bot_traits

LOG = logging.getLogger("chatter_raid_base")


def _maybe_talent_context(
    config, db, bot_guid, bot_class, bot_name,
    perspective='speaker',
):
    """Compute talent context if RNG passes.

    Returns str or None.  Rolls once against
    LLMChatter.TalentInjectionChance config key.
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
    if result:
        LOG.info(
            "Talent injected for %s: %s",
            bot_name, result,
        )
    return result


# ── Event classification ──────────────────────────

# "Big events" only matter for callers that still
# use the default DISPATCH_BOTH_IF_BIG mode.
# BG handlers now pass explicit dispatch modes, so
# this set mainly describes the remaining default
# behavior used by raid-style paths.
BIG_EVENTS = {
    # BG
    'bg_match_start', 'bg_match_end',
    'bg_flag_picked_up', 'bg_flag_captured',
    'bg_flag_dropped', 'bg_flag_returned',
    # PvE Raid
    'raid_boss_pull', 'raid_boss_kill',
    'raid_boss_wipe', 'raid_idle_morale',
}

DISPATCH_SUBGROUP_ONLY = "subgroup_only"
DISPATCH_RAID_ONLY = "raid_only"
DISPATCH_BOTH_IF_BIG = "both_if_big"

# Everything else fires sub-group worker only.

# Events suppressed at the Python level as a safety
# net (C++ guards are the primary filter).
SUPPRESSED_ALWAYS = {
    'bot_group_join',
    'bot_group_discovery',
    'bot_group_zone_transition',
    'player_general_msg',
    'holiday_start', 'holiday_end',
    'transport_arrives',
    'weather_change', 'weather_ambient',
    'bot_group_levelup', 'bot_level_up',
    'day_night_transition',
}

SUPPRESSED_IN_BG = {
    'bot_group_quest_complete',
    'bot_group_quest_objectives',
    'bot_group_quest_accept',
    'bot_group_loot',
    'bot_group_corpse_run',
}

SUPPRESSED_IN_RAID = {
    'bot_group_corpse_run',
}


# ── Helpers ───────────────────────────────────────

def is_event_suppressed(
    event_type: str, extra_data: dict
) -> bool:
    """Check if event should be suppressed in
    raid/BG context."""
    in_raid = extra_data.get('in_raid', False)
    in_bg = extra_data.get('is_battleground', False)

    if not in_raid and not in_bg:
        return False

    if event_type in SUPPRESSED_ALWAYS:
        return True
    if in_bg and event_type in SUPPRESSED_IN_BG:
        return True
    if in_raid and not in_bg:
        if event_type in SUPPRESSED_IN_RAID:
            return True

    return False


def get_subgroup_bots(extra_data: dict) -> List[int]:
    """Return bot GUIDs in player's sub-group."""
    return extra_data.get('party_bot_guids', [])


def get_crowd_bots(extra_data: dict) -> List[int]:
    """Return bot GUIDs outside player's sub-group."""
    return extra_data.get('raid_bot_guids', [])


def get_lightweight_bot_data(
    db, bot_guid: int
) -> Optional[Dict[str, Any]]:
    """Query characters table for minimal bot info.

    Returns dict with bot_name, race, class (strings),
    or None if not found.
    """
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT name, race, class "
            "FROM characters WHERE guid = %s",
            (bot_guid,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'bot_name': row['name'],
            'bot_guid': bot_guid,
            'race': get_race_name(int(row['race'])),
            'class': get_class_name(
                int(row['class'])),
        }
    finally:
        cursor.close()


# ── Dispatch ──────────────────────────────────────

def dual_worker_dispatch(
    db,
    client,
    config: dict,
    event: dict,
    extra_data: dict,
    subgroup_prompt_fn: Optional[Callable] = None,
    raid_prompt_fn: Optional[Callable] = None,
    dispatch_mode: str = DISPATCH_BOTH_IF_BIG,
    config_prefix: str = 'BGChatter',
) -> bool:
    """Route event to sub-group worker, raid worker,
    or both.

    Args:
        db: MySQL connection.
        client: LLM client.
        config: Parsed config dict.
        event: Event dict from llm_chatter_events.
        extra_data: Parsed extra_data JSON with
            party_bot_guids, raid_bot_guids, etc.
        subgroup_prompt_fn: Builds the prompt for
            the sub-group worker. Signature:
            (extra_data, bot_data,
             is_raid_worker=False) -> str
        raid_prompt_fn: Builds the prompt for the
            raid worker. None skips raid worker.
            Signature:
            (extra_data, bot_data,
             is_raid_worker=True) -> str

    Returns:
        True if at least one message was generated.
    """
    event_type = event.get('event_type', '')
    is_big = event_type in BIG_EVENTS
    any_sent = False

    sg_result: Optional[Dict[str, Any]] = {}

    if dispatch_mode != DISPATCH_RAID_ONLY:
        sg_result = fire_subgroup_worker(
            db, client, config,
            event, extra_data,
            prompt_fn=subgroup_prompt_fn,
            config_prefix=config_prefix)
        if sg_result:
            any_sent = True

    should_fire_raid = (
        dispatch_mode == DISPATCH_RAID_ONLY
        or (
            dispatch_mode == DISPATCH_BOTH_IF_BIG
            and is_big
        )
    )

    if should_fire_raid and raid_prompt_fn is not None:
        allow_raid = True
        if dispatch_mode != DISPATCH_RAID_ONLY:
            chance = int(config.get(
                f'LLMChatter.{config_prefix}'
                '.RaidWorkerChance',
                50))
            allow_raid = (
                random.randint(1, 100) <= chance
            )
        if allow_raid:
            used = (
                sg_result.get('used_guids', [])
                if isinstance(sg_result, dict)
                else []
            )
            rw_result = fire_raid_worker(
                db, client, config,
                event, extra_data,
                prompt_fn=raid_prompt_fn,
                exclude_guids=used,
                config_prefix=config_prefix)
            if rw_result:
                any_sent = True

    return any_sent


def fire_subgroup_worker(
    db, client, config: dict,
    event: dict, extra_data: dict,
    prompt_fn: Optional[Callable] = None,
    config_prefix: str = 'BGChatter',
) -> Optional[Dict[str, Any]]:
    """Select bot from player's sub-group, build
    prompt, call LLM, insert message.

    Returns dict with 'used_guids' on success,
    or {} on skip.
    """
    if prompt_fn is None:
        return {}

    # Inject db/config refs so prompt builders
    # can access anti-rep and spices
    extra_data['_db'] = db
    extra_data['_config'] = config

    party_guids = get_subgroup_bots(extra_data)
    if not party_guids:
        LOG.info(
            "Skipped: subgroup worker "
            "(no party bots)")
        return {}

    bot_guid = random.choice(party_guids)
    group_id = int(extra_data.get('group_id', 0))

    trait_data = get_bot_traits(
        db, group_id, bot_guid)
    if not trait_data:
        # BG bots may not have traits — fall
        # back to lightweight character data
        trait_data = get_lightweight_bot_data(
            db, bot_guid)
        if not trait_data:
            LOG.warning(
                "No data for bot %s group %s",
                bot_guid, group_id)
            return {}

    bot_name = trait_data['bot_name']

    # get_bot_traits() doesn't return race/class
    # — enrich from characters table so prompt
    # builders can include identity context
    bot_class = trait_data.get('class', '')
    bot_race = trait_data.get('race', '')
    if not bot_class or not bot_race:
        lw = get_lightweight_bot_data(db, bot_guid)
        if lw:
            if not bot_class:
                bot_class = lw.get('class', '')
                trait_data['class'] = bot_class
            if not bot_race:
                bot_race = lw.get('race', '')
                trait_data['race'] = bot_race
    talent_ctx = _maybe_talent_context(
        config, db, bot_guid,
        bot_class, bot_name,
    )
    if talent_ctx:
        extra_data['_talent_context'] = (
            talent_ctx)
    else:
        extra_data.pop(
            '_talent_context', None)

    prompt = prompt_fn(
        extra_data, trait_data,
        is_raid_worker=False)
    max_tokens = int(config.get(
        f'LLMChatter.{config_prefix}.MaxTokens',
        32,
    ))

    result = run_single_reaction(
        db, client, config,
        prompt=prompt,
        speaker_name=bot_name,
        bot_guid=bot_guid,
        channel='party',
        delay_seconds=2,
        event_id=event.get('id'),
        allow_emote_fallback=True,
        max_tokens_override=max_tokens,
        context=(
            f"squad:#{event.get('id')}"
            f":{bot_name}"),
    )

    if not result.get('ok'):
        return {}

    return {'used_guids': [bot_guid]}


def fire_raid_worker(
    db, client, config: dict,
    event: dict, extra_data: dict,
    prompt_fn: Optional[Callable] = None,
    exclude_guids: Optional[List[int]] = None,
    config_prefix: str = 'BGChatter',
) -> Optional[Dict[str, Any]]:
    """Select bot from OTHER sub-groups, build
    lightweight prompt, call LLM, insert message.

    Raid worker messages have no emotes (orange
    emote text in raid chat looks bizarre).

    Returns dict with 'used_guids' on success,
    or {} on skip.
    """
    if prompt_fn is None:
        return {}

    # Inject db/config refs so prompt builders
    # can access anti-rep and spices
    # (needed for DISPATCH_RAID_ONLY where
    # fire_subgroup_worker is skipped)
    extra_data['_db'] = db
    extra_data['_config'] = config

    raid_guids = get_crowd_bots(extra_data)
    if not raid_guids:
        # Fall back to subgroup bots when the
        # player's party is the only bot subgroup
        # (common in BGs and small PvE raids).
        raid_guids = get_subgroup_bots(extra_data)
    if not raid_guids:
        LOG.info(
            "Skipped: raid worker "
            "(no crowd bots)")
        return {}

    available = [
        g for g in raid_guids
        if g not in (exclude_guids or [])
    ]
    if not available:
        return {}

    bot_guid = random.choice(available)

    bot_data = get_lightweight_bot_data(
        db, bot_guid)
    if not bot_data:
        LOG.warning(
            "No character data for bot %s",
            bot_guid)
        return {}

    bot_name = bot_data['bot_name']

    # Talent injection for BG raid worker
    bot_class = bot_data.get('class', '')
    talent_ctx = _maybe_talent_context(
        config, db, bot_guid,
        bot_class, bot_name,
    )
    if talent_ctx:
        extra_data['_talent_context'] = (
            talent_ctx)
    else:
        extra_data.pop(
            '_talent_context', None)

    prompt = prompt_fn(
        extra_data, bot_data,
        is_raid_worker=True)
    max_tokens = int(config.get(
        f'LLMChatter.{config_prefix}.MaxTokens',
        32,
    ))

    # Channel: 'battleground' for BGs, 'raid' for
    # PvE raids
    in_bg = extra_data.get(
        'is_battleground', False)
    channel = 'battleground' if in_bg else 'raid'

    result = run_single_reaction(
        db, client, config,
        prompt=prompt,
        speaker_name=bot_name,
        bot_guid=bot_guid,
        channel=channel,
        delay_seconds=2,
        event_id=event.get('id'),
        allow_emote_fallback=False,
        max_tokens_override=max_tokens,
        context=(
            f"crowd:#{event.get('id')}"
            f":{bot_name}"),
    )

    if not result.get('ok'):
        return {}

    return {'used_guids': [bot_guid]}
