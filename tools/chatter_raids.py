"""
chatter_raids.py — PvE raid event handlers for
mod-llm-chatter.

Each handler follows the bridge contract:
    handler(db, client, config, event) -> bool

Handlers parse extra_data, check suppression, dispatch
via dual_worker_dispatch, and mark event status.
"""

import logging

from chatter_shared import parse_extra_data
from chatter_group_state import _mark_event
from chatter_raid_base import (
    dual_worker_dispatch,
    is_event_suppressed,
    DISPATCH_SUBGROUP_ONLY,
    DISPATCH_BOTH_IF_BIG,
    DISPATCH_RAID_ONLY,
)
from chatter_raid_prompts import (
    build_raid_boss_pull_prompt,
    build_raid_boss_kill_prompt,
    build_raid_boss_wipe_prompt,
    build_raid_morale_prompt,
)

LOG = logging.getLogger("chatter_raids")


def process_raid_boss_pull_event(
    db, client, config, event
):
    """Handle raid_boss_pull — boss engaged."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'raid_boss_pull')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    if is_event_suppressed(
            'raid_boss_pull', extra_data):
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_raid_boss_pull_prompt),
        raid_prompt_fn=(
            build_raid_boss_pull_prompt),
        dispatch_mode=DISPATCH_BOTH_IF_BIG,
        config_prefix='RaidChatter')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_raid_boss_kill_event(
    db, client, config, event
):
    """Handle raid_boss_kill — boss defeated."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'raid_boss_kill')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    if is_event_suppressed(
            'raid_boss_kill', extra_data):
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_raid_boss_kill_prompt),
        raid_prompt_fn=(
            build_raid_boss_kill_prompt),
        dispatch_mode=DISPATCH_BOTH_IF_BIG,
        config_prefix='RaidChatter')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_raid_boss_wipe_event(
    db, client, config, event
):
    """Handle raid_boss_wipe — raid wiped."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'raid_boss_wipe')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    if is_event_suppressed(
            'raid_boss_wipe', extra_data):
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=(
            build_raid_boss_wipe_prompt),
        raid_prompt_fn=(
            build_raid_boss_wipe_prompt),
        dispatch_mode=DISPATCH_BOTH_IF_BIG,
        config_prefix='RaidChatter')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result


def process_raid_idle_morale_event(
    db, client, config, event
):
    """Handle raid_idle_morale — idle banter and
    morale between pulls."""
    event_id = event['id']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event_id, 'raid_idle_morale')

    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    if is_event_suppressed(
            'raid_idle_morale', extra_data):
        _mark_event(db, event_id, 'skipped')
        return False

    result = dual_worker_dispatch(
        db, client, config, event, extra_data,
        subgroup_prompt_fn=None,
        raid_prompt_fn=build_raid_morale_prompt,
        dispatch_mode=DISPATCH_RAID_ONLY,
        config_prefix='RaidChatter')

    status = (
        'completed' if result else 'skipped')
    _mark_event(db, event_id, status)
    return result
