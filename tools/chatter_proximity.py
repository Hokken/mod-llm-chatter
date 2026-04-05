"""Proximity chatter event handlers."""

import logging
import random
from typing import Dict, List, Optional

from chatter_constants import PROXIMITY_CHAT_TOPICS
from chatter_db import insert_chat_message
from chatter_llm import call_llm
from chatter_shared import (
    PromptParts,
    append_json_instruction,
    append_conversation_json_instruction,
    parse_conversation_response,
    parse_extra_data,
    get_class_name,
    get_race_name,
    strip_conversation_actions,
)
from chatter_text import (
    cleanup_message,
    parse_single_response,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)


def _get_proximity_int(
    config: Dict, name: str, default: int
) -> int:
    return int(config.get(
        f'LLMChatter.ProximityChatter.{name}',
        default,
    ))


def _mark_event(db, event_id: int, status: str) -> None:
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events SET status = %s "
        "WHERE id = %s",
        (status, event_id),
    )
    db.commit()


def _query_bot_identity(
    db, bot_guid: int
) -> Dict[str, str]:
    if not bot_guid:
        return {}

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT class, race FROM characters "
            "WHERE guid = %s",
            (bot_guid,),
        )
        row = cursor.fetchone()
        if not row:
            return {}
        return {
            'class': get_class_name(
                int(row.get('class', 0) or 0)
            ),
            'race': get_race_name(
                int(row.get('race', 0) or 0)
            ),
        }
    except Exception:
        logger.error(
            "query bot identity failed",
            exc_info=True,
        )
        return {}


def _describe_speaker(
    db, speaker: Dict
) -> str:
    if speaker.get('is_npc'):
        role = speaker.get('role') or 'NPC'
        sub_name = speaker.get('sub_name') or ''
        parts = [speaker.get('name', 'NPC'), role]
        if sub_name:
            parts.append(sub_name)
        return " | ".join(part for part in parts if part)

    bot_guid = int(speaker.get('bot_guid', 0) or 0)
    info = _query_bot_identity(db, bot_guid)
    class_name = speaker.get('class') or info.get(
        'class', 'Adventurer'
    )
    race_name = speaker.get('race') or info.get(
        'race', 'Unknown'
    )
    return (
        f"{speaker.get('name', 'Bot')} | "
        f"{race_name} {class_name}"
    )


def _speaker_channel(speaker: Dict) -> str:
    return 'msay' if speaker.get('is_npc') else 'say'


def _insert_proximity_line(
    db,
    event_id: int,
    speaker: Dict,
    player_guid: int,
    sequence: int,
    delay_seconds: int,
    parsed: Dict,
) -> bool:
    raw_message = parsed.get('message', '')
    message = strip_speaker_prefix(
        raw_message, speaker.get('name', '')
    )
    message = cleanup_message(
        message, action=parsed.get('action')
    )
    if not message:
        return False
    if len(message) > 255:
        message = message[:252] + "..."

    bot_guid = int(speaker.get('bot_guid', 0) or 0)
    npc_spawn_id = int(
        speaker.get('npc_spawn_id', 0) or 0
    )

    insert_chat_message(
        db,
        bot_guid=bot_guid,
        bot_name=speaker.get('name', 'Unknown'),
        message=message,
        channel=_speaker_channel(speaker),
        delay_seconds=delay_seconds,
        event_id=event_id,
        sequence=sequence,
        emote=parsed.get('emote'),
        npc_spawn_id=npc_spawn_id or None,
        player_guid=player_guid or None,
    )
    return True


def _single_prompt(
    db,
    extra: Dict,
    speaker: Dict,
    topic: str,
    player_message: Optional[str] = None,
    last_message: Optional[str] = None,
) -> PromptParts:
    zone_name = extra.get('zone_name', 'the area')
    subzone_name = extra.get('subzone_name', '')
    player_name = extra.get('player_name', 'the player')
    player_addressed = bool(
        extra.get('player_addressed', False)
    )
    speaker_desc = _describe_speaker(db, speaker)
    nearby_names = extra.get('nearby_names') or []

    lines = [
        "You write extremely short, immersive World of "
        "Warcraft in-world /say lines.",
        "message must be 8-15 words, grounded, local, "
        "and low-stakes.",
        "Keep it lore-friendly. No modern memes, no AI "
        "talk, no markdown.",
        "",
        f"Speaker: {speaker_desc}",
        f"Zone: {zone_name}",
    ]
    if subzone_name:
        lines.append(f"Subzone: {subzone_name}")
    lines.append(f"Topic seed: {topic}")

    if player_message:
        lines.append(
            f"Player message to answer: {player_message}"
        )
    if last_message:
        lines.append(
            f"Most recent nearby line: {last_message}"
        )

    addressable = list(nearby_names)
    if player_addressed:
        addressable.insert(0, player_name)
    if addressable:
        lines.append(
            "Nearby people you may address by name: "
            + ", ".join(addressable[:5]) + "."
        )

    # Use global EmoteChance / ActionChance gates
    return append_json_instruction(
        "\n".join(lines) + "\n",
        allow_action=True,
        skip_emote=False,
    )


def _conversation_prompt(
    db, extra: Dict, participants: List[Dict]
) -> PromptParts:
    topic = random.choice(PROXIMITY_CHAT_TOPICS)
    zone_name = extra.get('zone_name', 'the area')
    subzone_name = extra.get('subzone_name', '')
    max_lines = max(
        2, min(
            int(extra.get('max_lines', 3) or 3),
            len(participants) + 1,
        ),
    )
    roster = "\n".join(
        f"- {_describe_speaker(db, speaker)}"
        for speaker in participants
    )

    nearby_names = extra.get('nearby_names') or []
    player_name = extra.get('player_name', '')
    player_addressed = bool(
        extra.get('player_addressed', False)
    )

    lines = [
        "You write short World of Warcraft ambient "
        "overheard /say conversations.",
        "Use only the provided speaker names.",
        "Each message must be 6-14 words, natural, and "
        "grounded in the immediate place.",
        "Keep the exchange brief and immersive.",
        "",
        f"Zone: {zone_name}",
        f"Topic seed: {topic}",
        f"Write EXACTLY {max_lines} messages.",
        "Speakers may address each other by name.",
    ]
    if subzone_name:
        lines.append(f"Subzone: {subzone_name}")

    addressable = list(nearby_names)
    if player_addressed and player_name:
        addressable.insert(0, player_name)
    if addressable:
        lines.append(
            "Also nearby: "
            + ", ".join(addressable[:5])
            + ". A speaker may address one of them."
        )

    lines.append("Speakers:")
    lines.append(roster)

    speaker_names = [
        s.get('name', '') for s in participants
    ]
    # Use global EmoteChance / ActionChance gates
    return append_conversation_json_instruction(
        "\n".join(lines) + "\n",
        speaker_names,
        max_lines,
        allow_action=True,
    )


def _generate_single_line(
    db,
    client,
    config,
    event_id: int,
    extra: Dict,
    speaker: Dict,
    *,
    message_event_id: Optional[int] = None,
    topic: Optional[str] = None,
    player_message: Optional[str] = None,
    last_message: Optional[str] = None,
    sequence: int = 0,
    delay_seconds: int = 0,
    label: str = 'proximity_say',
) -> bool:
    prompt = _single_prompt(
        db,
        extra,
        speaker,
        topic or random.choice(
            PROXIMITY_CHAT_TOPICS
        ),
        player_message=player_message,
        last_message=last_message,
    )
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=_get_proximity_int(
            config, 'MaxTokensPerLine', 40
        ),
        label=label,
        metadata={
            'zone_name': extra.get('zone_name', ''),
            'speaker_name': speaker.get('name', ''),
        },
    )
    if not response:
        return False

    parsed = parse_single_response(response)
    return _insert_proximity_line(
        db,
        message_event_id or event_id,
        speaker,
        int(extra.get('player_guid', 0) or 0),
        sequence,
        delay_seconds,
        parsed,
    )


def handle_proximity_say(db, client, config, event):
    event_id = int(event['id'])
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'proximity_say',
    )
    participants = extra.get('participants') or []
    if not participants:
        _mark_event(db, event_id, 'skipped')
        return False

    ok = _generate_single_line(
        db,
        client,
        config,
        event_id,
        extra,
        participants[0],
        label='proximity_say',
    )
    _mark_event(
        db, event_id,
        'completed' if ok else 'skipped',
    )
    return ok


def handle_proximity_conversation(
    db, client, config, event
):
    event_id = int(event['id'])
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'proximity_conversation',
    )
    participants = extra.get('participants') or []
    if len(participants) < 2:
        _mark_event(db, event_id, 'skipped')
        return False

    prompt = _conversation_prompt(
        db, extra, participants
    )
    max_lines = int(extra.get('max_lines', 3) or 3)
    # Each line needs ~60-80 tokens for JSON structure
    # (speaker, message, emote, action keys + values).
    # The per-line config controls message brevity in the
    # prompt, but the token budget must cover full JSON.
    max_tokens = 80 * max_lines
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label='proximity_conversation',
        metadata={
            'zone_name': extra.get('zone_name', ''),
            'speaker_count': len(participants),
        },
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    names = [
        speaker.get('name', '')
        for speaker in participants
    ]
    parsed = parse_conversation_response(
        response, names
    )
    line_delay = max(0, int(
        extra.get('line_delay_seconds', 4) or 4
    ))
    player_guid = int(
        extra.get('player_guid', 0) or 0
    )
    speaker_by_name = {
        speaker.get('name', ''): speaker
        for speaker in participants
    }

    # Strip actions per-message based on
    # ActionChance — LLM always provides them,
    # Python enforces randomness post-parse.
    strip_conversation_actions(
        parsed, label='proximity_conversation'
    )

    inserted = 0
    cumulative_delay = 0
    for index, line in enumerate(parsed):
        speaker = speaker_by_name.get(
            line.get('name', '')
        )
        if not speaker:
            continue
        if index > 0:
            cumulative_delay += line_delay
        ok = _insert_proximity_line(
            db,
            event_id,
            speaker,
            player_guid,
            index,
            cumulative_delay,
            line,
        )
        if ok:
            inserted += 1

    if inserted == 0:
        logger.warning(
            "proximity_conversation event %s fell back "
            "to single-line output after parse failure",
            event_id,
        )
        fallback = _generate_single_line(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            label='proximity_conversation_fallback',
        )
        _mark_event(
            db, event_id,
            'completed' if fallback else 'skipped',
        )
        return fallback

    _mark_event(db, event_id, 'completed')
    return True


def handle_proximity_reply(db, client, config, event):
    event_id = int(event['id'])
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'proximity_reply',
    )
    responder = {
        'name': extra.get('responder_name', 'Nearby'),
        'is_npc': bool(
            extra.get('responder_is_npc', False)
        ),
        'bot_guid': int(
            extra.get('responder_bot_guid', 0) or 0
        ),
        'npc_spawn_id': int(
            extra.get(
                'responder_npc_spawn_id', 0
            ) or 0
        ),
    }
    if (
        not responder['bot_guid']
        and not responder['npc_spawn_id']
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    topic = "brief local reply"
    if int(extra.get('turn_count', 0) or 0) >= (
        _get_proximity_int(config, 'ReplyMaxTurns', 5)
        - 1
    ):
        topic = "brief reply with a graceful exit"

    ok = _generate_single_line(
        db,
        client,
        config,
        event_id,
        extra,
        responder,
        message_event_id=int(extra.get('scene_id', 0) or 0)
        or event_id,
        topic=topic,
        player_message=extra.get(
            'player_message', ''
        ),
        last_message=extra.get(
            'last_message', ''
        ),
        label='proximity_reply',
    )
    _mark_event(
        db, event_id,
        'completed' if ok else 'skipped',
    )
    return ok


def _fetch_proximity_history(
    db, player_guid: int, zone_id: int,
    limit: int = 10,
) -> List[Dict]:
    """Fetch recent proximity messages for context."""
    if not player_guid or not zone_id:
        return []
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT t.bot_name, t.message FROM ("
            "  SELECT m.bot_name, m.message,"
            "         m.delivered_at"
            "  FROM llm_chatter_messages m"
            "  JOIN llm_chatter_events e"
            "    ON m.event_id = e.id"
            "  WHERE m.delivered = 1"
            "    AND m.channel IN ('say', 'msay')"
            "    AND e.zone_id = %s"
            "    AND m.player_guid = %s"
            "    AND m.delivered_at"
            "        > DATE_SUB(NOW(),"
            "          INTERVAL 5 MINUTE)"
            "  ORDER BY m.delivered_at DESC"
            "  LIMIT %s"
            ") t ORDER BY t.delivered_at ASC",
            (zone_id, player_guid, limit),
        )
        rows = cursor.fetchall()
        return [
            {
                'name': r['bot_name'],
                'message': r['message'],
            }
            for r in rows
        ]
    except Exception:
        logger.error(
            "fetch proximity history failed",
            exc_info=True,
        )
        return []


def _format_history_block(
    history: List[Dict],
) -> str:
    if not history:
        return ""
    lines = [
        f"{h['name']}: {h['message']}"
        for h in history
    ]
    return (
        "Recent nearby conversation:\n"
        + "\n".join(lines)
    )


def _player_say_single_prompt(
    db,
    extra: Dict,
    speaker: Dict,
    player_message: str,
    history: List[Dict],
) -> PromptParts:
    zone_name = extra.get('zone_name', 'the area')
    subzone_name = extra.get('subzone_name', '')
    player_name = extra.get(
        'player_name', 'the player'
    )
    speaker_desc = _describe_speaker(db, speaker)
    nearby_names = extra.get('nearby_names') or []

    lines = [
        "You write extremely short, immersive World "
        "of Warcraft in-world /say lines.",
        "message must be 8-15 words, grounded, "
        "local, and low-stakes.",
        "Keep it lore-friendly. No modern memes, no "
        "AI talk, no markdown.",
        "",
        f"Speaker: {speaker_desc}",
        f"Zone: {zone_name}",
    ]
    if subzone_name:
        lines.append(f"Subzone: {subzone_name}")

    addressed = extra.get('addressed_name', '')
    if addressed:
        lines.append(
            f"The player ({player_name}) is "
            f"addressing {addressed} directly."
        )
    lines.append(
        f"A nearby player ({player_name}) said: "
        f"{player_message}"
    )
    lines.append(
        "Respond naturally to the player's words."
    )

    history_block = _format_history_block(history)
    if history_block:
        lines.append("")
        lines.append(history_block)

    addressable = list(nearby_names)
    addressable.insert(0, player_name)
    if addressable:
        lines.append(
            "Nearby people you may address by "
            "name: "
            + ", ".join(addressable[:5]) + "."
        )

    return append_json_instruction(
        "\n".join(lines) + "\n",
        allow_action=True,
        skip_emote=False,
    )


def _player_say_conversation_prompt(
    db,
    extra: Dict,
    participants: List[Dict],
    player_message: str,
    history: List[Dict],
) -> PromptParts:
    zone_name = extra.get('zone_name', 'the area')
    subzone_name = extra.get('subzone_name', '')
    player_name = extra.get(
        'player_name', 'the player'
    )
    max_lines = max(
        2, min(
            int(extra.get('max_lines', 3) or 3),
            len(participants) + 1,
        ),
    )
    roster = "\n".join(
        f"- {_describe_speaker(db, speaker)}"
        for speaker in participants
    )
    nearby_names = extra.get('nearby_names') or []

    lines = [
        "You write short World of Warcraft "
        "overheard /say conversations.",
        "Use only the provided speaker names.",
        "Each message must be 6-14 words, natural, "
        "and grounded in the immediate place.",
        "Keep the exchange brief and immersive.",
        "",
        f"Zone: {zone_name}",
    ]
    if subzone_name:
        lines.append(f"Subzone: {subzone_name}")

    addressed = extra.get('addressed_name', '')
    if addressed:
        lines.append(
            f"The player ({player_name}) is "
            f"addressing {addressed} directly."
        )
        lines.append(
            f"IMPORTANT: The FIRST message in the "
            f"array MUST be spoken by {addressed}, "
            f"since the player is talking to them."
        )
    lines.append(
        f"A nearby player ({player_name}) said: "
        f"{player_message}"
    )
    lines.append(
        "Speakers should react to or acknowledge "
        "the player's words."
    )
    lines.append(
        f"Write EXACTLY {max_lines} messages."
    )
    lines.append(
        "Speakers may address each other or the "
        "player by name."
    )

    history_block = _format_history_block(history)
    if history_block:
        lines.append("")
        lines.append(history_block)

    addressable = list(nearby_names)
    addressable.insert(0, player_name)
    if addressable:
        lines.append(
            "Also nearby: "
            + ", ".join(addressable[:5])
            + ". A speaker may address one of them."
        )

    lines.append("Speakers:")
    lines.append(roster)

    speaker_names = [
        s.get('name', '') for s in participants
    ]
    return append_conversation_json_instruction(
        "\n".join(lines) + "\n",
        speaker_names,
        max_lines,
        allow_action=True,
    )


def handle_proximity_player_say(
    db, client, config, event
):
    event_id = int(event['id'])
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'proximity_player_say',
    )
    participants = extra.get('participants') or []
    if not participants:
        _mark_event(db, event_id, 'skipped')
        return False

    player_message = extra.get(
        'player_message', ''
    )
    if not player_message:
        _mark_event(db, event_id, 'skipped')
        return False

    player_guid = int(
        extra.get('player_guid', 0) or 0
    )
    zone_id = int(
        extra.get('zone_id', 0) or 0
    )
    history = _fetch_proximity_history(
        db, player_guid, zone_id
    )

    speaker = participants[0]
    prompt = _player_say_single_prompt(
        db, extra, speaker, player_message, history
    )
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=_get_proximity_int(
            config, 'MaxTokensPerLine', 40
        ),
        label='proximity_player_say',
        metadata={
            'zone_name': extra.get(
                'zone_name', ''
            ),
            'speaker_name': speaker.get(
                'name', ''
            ),
        },
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    parsed = parse_single_response(response)
    ok = _insert_proximity_line(
        db,
        event_id,
        speaker,
        player_guid,
        0,
        0,
        parsed,
    )
    _mark_event(
        db, event_id,
        'completed' if ok else 'skipped',
    )
    return ok


def handle_proximity_player_conversation(
    db, client, config, event
):
    event_id = int(event['id'])
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'proximity_player_conversation',
    )
    participants = extra.get('participants') or []
    if len(participants) < 2:
        _mark_event(db, event_id, 'skipped')
        return False

    player_message = extra.get(
        'player_message', ''
    )
    if not player_message:
        _mark_event(db, event_id, 'skipped')
        return False

    player_guid = int(
        extra.get('player_guid', 0) or 0
    )
    zone_id = int(
        extra.get('zone_id', 0) or 0
    )
    history = _fetch_proximity_history(
        db, player_guid, zone_id
    )

    prompt = _player_say_conversation_prompt(
        db, extra, participants,
        player_message, history
    )
    max_lines = int(
        extra.get('max_lines', 3) or 3
    )
    max_tokens = 80 * max_lines
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label='proximity_player_conversation',
        metadata={
            'zone_name': extra.get(
                'zone_name', ''
            ),
            'speaker_count': len(participants),
        },
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    names = [
        speaker.get('name', '')
        for speaker in participants
    ]
    parsed = parse_conversation_response(
        response, names
    )
    line_delay = max(0, int(
        extra.get('line_delay_seconds', 4) or 4
    ))
    speaker_by_name = {
        speaker.get('name', ''): speaker
        for speaker in participants
    }

    strip_conversation_actions(
        parsed,
        label='proximity_player_conversation',
    )

    # If the player targeted a specific entity, the
    # first line MUST come from that speaker.  Discard
    # the whole conversation and fall back to a single
    # line from the target rather than reorder (which
    # would break conversational coherence).
    addressed = extra.get('addressed_name', '')
    if addressed and parsed:
        first_name = parsed[0].get('name', '')
        if first_name != addressed:
            logger.warning(
                "proximity_player_conversation "
                "event %s: LLM assigned first line "
                "to %s instead of addressed %s — "
                "falling back to single line",
                event_id, first_name, addressed,
            )
            parsed = []

    inserted = 0
    cumulative_delay = 0
    for index, line in enumerate(parsed):
        speaker = speaker_by_name.get(
            line.get('name', '')
        )
        if not speaker:
            continue
        if index > 0:
            cumulative_delay += line_delay
        ok = _insert_proximity_line(
            db,
            event_id,
            speaker,
            player_guid,
            index,
            cumulative_delay,
            line,
        )
        if ok:
            inserted += 1

    if inserted == 0:
        logger.warning(
            "proximity_player_conversation "
            "event %s fell back to single-line",
            event_id,
        )
        fallback = _generate_single_line(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            player_message=player_message,
            label=(
                'proximity_player_conversation'
                '_fallback'
            ),
        )
        _mark_event(
            db, event_id,
            'completed' if fallback else 'skipped',
        )
        return fallback

    _mark_event(db, event_id, 'completed')
    return True
