"""Shared pipeline for group event handlers.

Extracts the ~70-line boilerplate that every
process_group_*_event() function repeats into a
single reusable function. Each handler becomes a
thin wrapper providing only its unique logic:
extract_fields, build_prompt, and optional
post_success callback.
"""

import logging
import random

from chatter_shared import (
    parse_extra_data,
    get_class_name,
    get_race_name,
    get_gender_label,
    get_chatter_mode,
    get_dungeon_flavor,
    run_single_reaction,
    build_zone_metadata,
)
from chatter_db import (
    fail_event,
    get_group_location,
    mark_event,
)
from chatter_group_state import (
    _mark_event,
    _store_chat,
    _get_recent_chat,
    format_chat_history,
    get_bot_traits,
    get_bot_mood_label,
    update_bot_mood,
)
from chatter_raid_base import dual_worker_dispatch

logger = logging.getLogger(__name__)


def _build_bot_from_extra(extra_data):
    """Build bot dict from extra_data fields."""
    return {
        'guid': int(extra_data.get('bot_guid', 0)),
        'name': extra_data.get('bot_name', 'Unknown'),
        'class': get_class_name(
            int(extra_data.get('bot_class', 0))
        ),
        'race': get_race_name(
            int(extra_data.get('bot_race', 0))
        ),
        'level': int(
            extra_data.get('bot_level', 1)
        ),
        'gender': get_gender_label(
            int(extra_data.get('bot_gender', 0))
        ),
    }


def _build_bot_from_db(db, bot_guid, bot_name):
    """Build bot dict by querying the characters
    table. Returns dict or None.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT class, race, level, gender "
        "FROM characters WHERE guid = %s",
        (bot_guid,),
    )
    row = cursor.fetchone()
    cursor.close()
    if not row:
        return None
    return {
        'guid': bot_guid,
        'name': bot_name,
        'class': get_class_name(row['class']),
        'race': get_race_name(row['race']),
        'level': row['level'],
        'gender': get_gender_label(row['gender']),
    }


def _maybe_talent_context(
    config, db, bot_guid, bot_class, bot_name,
    perspective='speaker',
):
    """Compute talent context if RNG passes."""
    from chatter_shared import build_talent_context
    chance = int(config.get(
        'LLMChatter.TalentInjectionChance', '40',
    ))
    if chance <= 0:
        return None
    if random.randint(1, 100) > chance:
        return None
    return build_talent_context(
        db, int(bot_guid), bot_class,
        bot_name, perspective=perspective,
    )


def run_group_handler(
    db, client, config, event,
    *,
    event_type_label,
    extract_fields,
    build_prompt,
    delay_seconds=3,
    mood_key=None,
    label='single_reaction',
    channel='party',
    allow_emote=True,
    max_tokens_override=None,
    message_transform=None,
    needs_map_id=False,
    needs_reactor_from_db=False,
    post_success=None,
    inject_mood=True,
    bg_fallback_prompt=None,
    pre_parsed_extra=None,
):
    """Shared pipeline for group event handlers.

    Steps:
    1. Parse extra_data
    2. Extract shared + handler-specific fields
    3. Guard checks
    4. Optional dedup
    5. Traits lookup (+ optional BG fallback)
    6. Build bot dict
    7. Build context (mode, history, talent, map)
    8. Call build_prompt(ctx)
    9. Optional mood injection
    10. run_single_reaction()
    11. Store chat + update mood
    12. Optional post_success callback
    13. Mark completed
    """
    event_id = event['id']

    # 1. Parse extra_data (skip if pre-parsed
    #    by conversation-branch handlers)
    if pre_parsed_extra is not None:
        extra_data = pre_parsed_extra
    else:
        extra_data = parse_extra_data(
            event.get('extra_data'),
            event_id, event_type_label,
        )
    if not extra_data:
        _mark_event(db, event_id, 'skipped')
        return False

    # 2. Extract shared fields
    bot_guid = int(extra_data.get('bot_guid', 0))
    bot_name = extra_data.get(
        'bot_name', 'Unknown',
    )
    group_id = int(extra_data.get('group_id', 0))

    # 3. Extract handler-specific fields
    try:
        fields = extract_fields(extra_data)
    except Exception:
        fail_event(
            db, event_id, event_type_label,
            'extract_fields error',
        )
        return False

    # 4. Guard
    if not bot_guid or not group_id:
        _mark_event(db, event_id, 'skipped')
        return False

    # 5. Traits lookup
    trait_data = get_bot_traits(
        db, group_id, bot_guid,
    )

    # 7. BG fallback if no traits
    if not trait_data and bg_fallback_prompt:
        try:
            ok = dual_worker_dispatch(
                db, client, config, event,
                extra_data,
                subgroup_prompt_fn=(
                    bg_fallback_prompt
                ),
                label=label,
            )
            _mark_event(
                db, event_id,
                'completed' if ok else 'skipped',
            )
            return ok
        except Exception:
            fail_event(
                db, event_id, event_type_label,
                'bg_fallback error',
            )
            return False

    if not trait_data:
        _mark_event(db, event_id, 'skipped')
        return False

    traits = trait_data['traits']
    stored_tone = trait_data.get('tone')

    # 8. Build bot dict
    if needs_reactor_from_db:
        bot = _build_bot_from_db(
            db, bot_guid, bot_name,
        )
        if not bot:
            _mark_event(db, event_id, 'skipped')
            return False
    else:
        bot = _build_bot_from_extra(extra_data)

    try:
        # 9. Build context
        mode = get_chatter_mode(config)
        history = _get_recent_chat(db, group_id)
        chat_hist = format_chat_history(history)
        speaker_talent = _maybe_talent_context(
            config, db, bot_guid,
            bot['class'], bot_name,
        )

        zone_id = 0
        area_id = 0
        map_id = None
        dungeon_flavor = None
        if needs_map_id:
            zone_id, area_id, map_id = (
                get_group_location(db, group_id)
            )
            dungeon_flavor = get_dungeon_flavor(
                map_id,
            )

        zone_meta = build_zone_metadata(
            extra_data.get('zone_id', 0),
            extra_data.get('area_id', 0),
        )

        ctx = {
            'bot': bot,
            'traits': traits,
            'stored_tone': stored_tone,
            'mode': mode,
            'chat_hist': chat_hist,
            'speaker_talent': speaker_talent,
            'zone_id': zone_id,
            'area_id': area_id,
            'map_id': map_id,
            'dungeon_flavor': dungeon_flavor,
            'zone_meta': zone_meta,
            'group_id': group_id,
            'event_id': event_id,
            'extra_data': extra_data,
            'config': config,
            'db': db,
            'client': client,
            'bot_guid': bot_guid,
            'bot_name': bot_name,
        }
        # Merge handler fields — guard against
        # accidental overwrites of pipeline keys
        _RESERVED = frozenset(ctx.keys())
        conflicts = _RESERVED & fields.keys()
        if conflicts:
            logger.warning(
                "extract_fields returned reserved "
                "keys %s for %s — skipping them",
                conflicts, event_type_label,
            )
            fields = {
                k: v for k, v in fields.items()
                if k not in _RESERVED
            }
        ctx.update(fields)

        # 10. Build prompt
        prompt = build_prompt(ctx)

        # 11. Mood injection
        if inject_mood:
            mood_label = get_bot_mood_label(
                group_id, bot_guid,
            )
            if mood_label != 'neutral':
                prompt += (
                    f"\nCurrent mood: {mood_label}"
                )

        # 12. Compute delay
        actual_delay = (
            delay_seconds(ctx)
            if callable(delay_seconds)
            else delay_seconds
        )

        # 13. run_single_reaction
        result = run_single_reaction(
            db, client, config,
            prompt=prompt,
            speaker_name=bot_name,
            bot_guid=bot_guid,
            channel=channel,
            delay_seconds=actual_delay,
            event_id=event_id,
            allow_emote_fallback=allow_emote,
            max_tokens_override=max_tokens_override,
            message_transform=message_transform,
            context=(
                f"grp-{label}:#{event_id}"
                f":{bot_name}"
            ),
            label=label,
            metadata=zone_meta,
        )

        if not result['ok']:
            _mark_event(db, event_id, 'skipped')
            return False

        message = result['message']

        # 14. Store chat
        _store_chat(
            db, group_id, bot_guid,
            bot_name, True, message,
        )

        # 15. Update mood
        if mood_key:
            actual_mood = (
                mood_key(ctx)
                if callable(mood_key)
                else mood_key
            )
            update_bot_mood(
                group_id, bot_guid, actual_mood,
            )

        # 16. Post-success callback
        if post_success:
            try:
                post_success(db, ctx, message)
            except Exception:
                logger.error(
                    "post_success failed for %s",
                    event_type_label,
                    exc_info=True,
                )

        # 17. Mark completed
        _mark_event(db, event_id, 'completed')
        return True

    except Exception:
        fail_event(
            db, event_id, event_type_label,
            'handler error',
        )
        return False
