"""World event handlers -- General-channel events
formerly served by the fallthrough path in
llm_chatter_bridge.py.

Covers: transport_arrives, weather_change,
weather_ambient, holiday_start, holiday_end,
minor_event, day_night_transition.

Extracting them into dedicated handlers lets
process_single_event() terminate at the
EVENT_HANDLERS dispatch map with no fallthrough.
"""

import logging
import random

from chatter_db import (
    get_zone_bot_candidates,
    get_bots_by_guid,
    get_zone_event_count,
    get_recent_speaker_guids,
    get_recent_zone_messages,
    insert_chat_message,
    mark_event,
)
from chatter_events import build_event_context
from chatter_prompts import (
    build_event_conversation_prompt,
    build_event_statement_prompt,
)
from chatter_shared import (
    get_zone_name,
    get_class_name,
    get_race_name,
    run_single_reaction,
    get_effective_speaker_cooldown,
    call_llm,
    parse_extra_data,
    parse_conversation_response,
    strip_conversation_actions,
    strip_speaker_prefix,
    cleanup_message,
    calculate_dynamic_delay,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Shared helpers (module-private)
# ------------------------------------------------------------------
def _normalize_bot(bot):
    """Ensure class/race are string names not ints."""
    bot = dict(bot)
    if isinstance(bot.get('bot1_class'), int):
        bot['bot1_class'] = get_class_name(
            bot['bot1_class']
        )
    if isinstance(bot.get('bot1_race'), int):
        bot['bot1_race'] = get_race_name(
            bot['bot1_race']
        )
    return bot


def _resolve_bots(db, event, extra_data, zone_id):
    """Find eligible bots for a world event.

    For transport_arrives with verified_bots, uses the
    verified GUID list. Otherwise falls back to zone
    or global bot candidate query.

    Returns (bot_list, used_verified) or (None, False)
    if no bots are available.
    """
    event_type = event.get('event_type', '')
    verified = extra_data.get('verified_bots')
    cursor = db.cursor(dictionary=True)

    # Transport events with verified bot list
    if (
        event_type == 'transport_arrives'
        and isinstance(verified, list)
    ):
        if not verified:
            cursor.close()
            return None, False
        guid_list = [int(g) for g in verified]
        bots = [
            _normalize_bot(b)
            for b in get_bots_by_guid(
                cursor, guid_list
            )
        ]
        cursor.close()
        return (bots or None), True

    # Zone-specific or global candidate query
    bots = [
        _normalize_bot(b)
        for b in get_zone_bot_candidates(
            cursor, zone_id=zone_id
        )
    ]
    cursor.close()

    if not bots:
        return None, False

    # If C++ provided verified bot GUIDs but we
    # didn't use the GUID lookup path, filter to
    # only verified bots.
    if isinstance(verified, list):
        if not verified:
            return None, False
        verified_set = set(
            int(g) for g in verified
        )
        bots = [
            b for b in bots
            if int(b['bot1_guid']) in verified_set
        ]
        if not bots:
            return None, False

    return bots, False


def _check_zone_fatigue(
    db, zone_id, config
):
    """Return True if zone fatigue threshold is
    exceeded (too many recent events in this zone).
    """
    if not zone_id:
        return False
    fatigue_threshold = int(config.get(
        'LLMChatter.ZoneFatigueThreshold', 3
    ))
    fatigue_cooldown = int(config.get(
        'LLMChatter.ZoneFatigueCooldownSeconds',
        900
    ))
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(*) as cnt
        FROM llm_chatter_events
        WHERE zone_id = %s
          AND status = 'completed'
          AND processed_at > DATE_SUB(
              NOW(), INTERVAL %s SECOND
          )
    """, (zone_id, fatigue_cooldown))
    result = cursor.fetchone()
    cursor.close()
    return (
        result is not None
        and result['cnt'] >= fatigue_threshold
    )


def _deliver_conversation(
    db, client, config, event, bots, extra_data,
    zone_id,
):
    """Build conversation prompt, call LLM, insert
    messages. Returns True on success, False on
    failure (caller should fall through to statement
    mode).
    """
    event_id = event['id']

    formatted = []
    for b in bots:
        formatted.append({
            'guid': b['bot1_guid'],
            'name': b['bot1_name'],
            'class': b['bot1_class'],
            'race': b['bot1_race'],
            'level': b['bot1_level'],
            'zone': get_zone_name(
                b.get('zone_id', zone_id)
            ),
        })

    bot_names = [b['name'] for b in formatted]
    bot_guids = {
        b['name']: b['guid'] for b in formatted
    }

    current_weather = extra_data.get(
        'current_weather', 'clear'
    )
    recent_msgs = get_recent_zone_messages(
        db, zone_id
    )
    event_context = build_event_context(event)

    prompt = build_event_conversation_prompt(
        formatted,
        event_context,
        zone_id,
        config,
        current_weather,
        recent_messages=recent_msgs,
        area_id=int(
            formatted[0].get('area_id', 0) or 0
        ),
    )

    evt_names = ','.join(bot_names)
    response = call_llm(
        client, prompt, config,
        context=(
            f"event-conv:#{event_id}"
            f":{evt_names}"
        ),
        label='event_conv',
    )

    if not response:
        return False

    messages = parse_conversation_response(
        response, bot_names
    )
    if not messages:
        return False

    strip_conversation_actions(
        messages, label='event_conv',
    )

    cumulative_delay = 0.0
    for i, msg in enumerate(messages):
        bot_guid = bot_guids.get(
            msg['name'],
            formatted[0]['guid'],
        )
        final_message = strip_speaker_prefix(
            msg['message'], msg['name'],
        )
        final_message = cleanup_message(
            final_message,
            action=msg.get('action'),
        )

        if i > 0:
            delay = calculate_dynamic_delay(
                len(final_message), config,
            )
            cumulative_delay += delay

        insert_chat_message(
            db,
            bot_guid,
            msg['name'],
            final_message,
            channel='general',
            delay_seconds=cumulative_delay,
            event_id=event_id,
            sequence=i,
        )

    mark_event(db, event_id, 'completed')
    return True


def _deliver_statement(
    db, client, config, event, bots, extra_data,
    zone_id,
):
    """Build statement prompt, call LLM via
    run_single_reaction, insert message.
    Returns True on success, False on failure.
    """
    event_id = event['id']
    bot = dict(random.choice(list(bots)))

    # Prefer event zone_id (player-centric) over
    # bot's characters.zone (stale).
    evt_zone_id = int(zone_id or 0)
    use_zone_id = (
        evt_zone_id
        or int(bot.get('zone_id', 0) or 0)
    )
    zone_name = (
        get_zone_name(use_zone_id) or "the world"
    )

    event_context = build_event_context(event)
    event_prompt = build_event_statement_prompt(
        bot,
        event_context,
        event_type=event.get('event_type', ''),
        zone_name=zone_name,
        config=config,
        extra_data=extra_data,
        zone_id=use_zone_id,
        # area_id not available from candidate query
        area_id=0,
    )

    delay_min = int(config.get(
        'LLMChatter.MessageDelayMin', 1000
    ))
    delay_max = int(config.get(
        'LLMChatter.MessageDelayMax', 30000
    ))
    delay_ms = random.randint(delay_min, delay_max)

    result = run_single_reaction(
        db,
        client,
        config,
        prompt=event_prompt,
        speaker_name=bot['bot1_name'],
        bot_guid=int(bot['bot1_guid']),
        channel='general',
        delay_seconds=delay_ms // 1000,
        event_id=event_id,
        bypass_speaker_cooldown=True,
        context=(
            f"event_statement:"
            f"{event.get('event_type', '')}:"
            f"{bot['bot1_name']}"
        ),
        label='reaction_world_event',
    )

    if result and result.get('ok'):
        mark_event(db, event_id, 'completed')
        return True

    mark_event(db, event_id, 'skipped')
    return False


# ------------------------------------------------------------------
# Core dispatch: statement vs conversation
# ------------------------------------------------------------------
def _process_world_event(
    db, client, config, event,
    fatigue_exempt=False,
):
    """Shared pipeline for transport_arrives and
    weather_change.

    1. Resolve eligible bots
    2. Check zone fatigue (unless exempt)
    3. Pre-filter by speaker cooldown
    4. Decide conversation vs statement
    5. Deliver via LLM
    """
    event_id = event['id']
    zone_id = event.get('zone_id')

    extra_data = parse_extra_data(
        event.get('extra_data'),
        event['id'],
        event.get('event_type', ''),
    ) or {}

    # Step 1: resolve bots
    bots, _ = _resolve_bots(
        db, event, extra_data, zone_id
    )
    if not bots:
        mark_event(db, event_id, 'skipped')
        return False

    # Step 2: zone fatigue (transport and weather
    # bypass this, but keep the parameter for
    # potential future world events)
    if not fatigue_exempt:
        if _check_zone_fatigue(
            db, zone_id, config
        ):
            mark_event(db, event_id, 'skipped')
            return False

    # Step 3: pre-filter by speaker cooldown
    num_bots = len(bots)
    cooldown = get_effective_speaker_cooldown(
        config, num_bots
    )
    cursor = db.cursor(dictionary=True)
    all_guids = [
        int(b['bot1_guid']) for b in bots
    ]
    recent = get_recent_speaker_guids(
        cursor, all_guids, cooldown
    )
    cursor.close()
    eligible = [
        b for b in bots
        if int(b['bot1_guid']) not in recent
    ]
    if not eligible:
        mark_event(db, event_id, 'skipped')
        return False

    # Step 4: decide conversation vs statement
    event_conv_chance = int(config.get(
        'LLMChatter.EventConversationChance', 60
    ))
    use_conversation = (
        len(eligible) >= 2
        and random.randint(1, 100)
        <= event_conv_chance
    )

    # Step 5: deliver
    if use_conversation:
        num_conv = min(
            random.randint(2, 4),
            len(eligible),
        )
        selected = random.sample(
            list(eligible), num_conv
        )
        ok = _deliver_conversation(
            db, client, config, event,
            selected, extra_data, zone_id,
        )
        if ok:
            return True
        # Fall through to statement on failure

    return _deliver_statement(
        db, client, config, event,
        eligible, extra_data, zone_id,
    )


# ------------------------------------------------------------------
# Public handler entry points
# ------------------------------------------------------------------
def process_transport_arrives_event(
    db, client, config, event,
):
    """Bots comment on a transport arriving at a stop.
    Uses verified_bots list from C++ when available.
    """
    return _process_world_event(
        db, client, config, event,
        fatigue_exempt=True,
    )


def process_weather_change_event(
    db, client, config, event,
):
    """Bots react to weather transitions."""
    return _process_world_event(
        db, client, config, event,
        fatigue_exempt=True,
    )


def process_weather_ambient_event(
    db, client, config, event,
):
    """Bots comment on ongoing weather."""
    return _process_world_event(
        db, client, config, event,
        fatigue_exempt=True,
    )


def process_holiday_start_event(
    db, client, config, event,
):
    """A seasonal holiday has just begun."""
    return _process_world_event(
        db, client, config, event,
        fatigue_exempt=True,
    )


def process_holiday_end_event(
    db, client, config, event,
):
    """A seasonal holiday is ending."""
    return _process_world_event(
        db, client, config, event,
        fatigue_exempt=True,
    )


def process_minor_event(
    db, client, config, event,
):
    """Call to Arms, Fishing Extravaganza, etc."""
    return _process_world_event(
        db, client, config, event,
        fatigue_exempt=False,
    )


def process_day_night_transition_event(
    db, client, config, event,
):
    """Time of day changes (dawn, dusk, etc.)."""
    return _process_world_event(
        db, client, config, event,
        fatigue_exempt=False,
    )
