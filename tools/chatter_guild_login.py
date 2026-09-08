"""Guild Chat greetings for a real player's login."""

import logging
import random
from typing import Dict, List, Tuple

from chatter_db import insert_chat_message
from chatter_guild import (
    _clean_guild_conversation,
    _contains_speaker_name,
    _guild_location_lines,
    _insert_reference_names,
    _participant_identity_lines,
    _valid_guild_conversation,
)
from chatter_guild_player import (
    _bounded_percent,
    _clean_single,
    _config_enabled,
    _load_candidates,
    _mark_event,
    _normalize_candidates,
    _select_responders,
    _session_is_current,
)
from chatter_llm import call_llm
from chatter_mode import build_player_chat_guidance, is_roleplay
from chatter_shared import (
    append_conversation_json_instruction,
    append_json_instruction,
    build_conversation_json_repair_prompt,
    calculate_dynamic_delay,
    get_chatter_mode,
    parse_conversation_response,
    parse_extra_data,
)
from chatter_text import parse_single_response

logger = logging.getLogger(__name__)


def _complete_event_if_current(
    db,
    event_id: int,
) -> bool:
    """Complete only a greeting that was not cancelled.

    Output is inserted before completion, so a failed
    compare-and-set must also consume those rows.
    """
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = 'completed' "
        "WHERE id = %s AND status = 'processing'",
        (event_id,),
    )
    completed = cursor.rowcount == 1
    if not completed:
        cursor.execute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1, delivered_at = NOW() "
            "WHERE event_id = %s AND delivered = 0",
            (event_id,),
        )
    db.commit()
    return completed


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == '':
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return default


def _max_characters(config: Dict) -> int:
    return max(40, min(150, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'LoginGreeting.MaxCharacters',
        100,
    ), 100)))


def _trim_greeting(text: str, maximum: int) -> str:
    text = " ".join(str(text or '').split())
    if len(text) <= maximum:
        return text

    shortened = text[:maximum - 1].rsplit(' ', 1)[0]
    shortened = shortened.rstrip(' ,;:-')
    if not shortened:
        return ""
    if shortened[-1] not in '.!?':
        shortened += '.'
    return shortened


def _clean_greeting(
    text: str,
    speaker_name: str,
    maximum: int,
) -> str:
    return _trim_greeting(
        _clean_single(text, speaker_name),
        maximum,
    )


def _choose_responder_count(
    config: Dict,
    candidate_count: int,
) -> int:
    maximum = max(
        1,
        min(
            3,
            _safe_int(config.get(
                'LLMChatter.GuildChatter.'
                'LoginGreeting.MaxResponders',
                3,
            ), 3),
            candidate_count,
        ),
    )
    if maximum < 2:
        return 1

    chance = _bounded_percent(
        config,
        'LLMChatter.GuildChatter.'
        'LoginGreeting.MultiReplyChance',
        20,
    )
    if random.randint(1, 100) > chance:
        return 1
    return random.randint(2, maximum)


def _greeting_delays(
    messages: List[Dict],
    config: Dict,
) -> List[float]:
    cumulative = 0.0
    delays = []
    previous_length = 0
    for index, message in enumerate(messages):
        text = str(message.get('message') or '')
        if index:
            cumulative += calculate_dynamic_delay(
                len(text),
                config,
                prev_message_length=previous_length,
                responsive=False,
            )
        delays.append(cumulative)
        previous_length = len(text)
    return delays


def _shared_prompt_lines(
    participants: List[Dict],
    guild_name: str,
    faction: str,
    player_name: str,
    maximum: int,
    mode: str = 'roleplay',
) -> List[str]:
    lines = [f"The guild is \"{guild_name}\"."]
    if is_roleplay(mode):
        lines.insert(
            0, "Write natural in-character World of Warcraft Guild Chat."
        )
    else:
        lines.insert(0, build_player_chat_guidance(mode, 'guild'))
    for participant in participants:
        lines.extend(
            _participant_identity_lines(participant, mode)
        )

    if faction and is_roleplay(mode):
        lines.append(
            f"They fight for the {faction}. Never "
            f"insult or mock the {faction}, their own "
            "faction."
        )
    lines.extend(
        _guild_location_lines(participants, False, mode)
    )
    lines.extend([
        "",
        f"{player_name}, a real guild member, has just "
        "logged in.",
        "Greet them as a familiar guildmate, not as a "
        "stranger or a newly recruited member.",
        "Keep every greeting warm, casual, and brief. "
        "It may acknowledge their return, ask what they "
        "are doing, or offer a small friendly wish.",
        "Do not invent where they have been, how long "
        "they were absent, or what they intend to do.",
        "Guild Chat reaches across the game world. Never imply "
        "the speakers can see, touch, or stand beside "
        "the player or one another.",
        "Each line is spoken text only: no narrator "
        "text, roleplay asterisks, slash commands, "
        "emotes, or name prefixes.",
        f"Hard limit: {maximum} characters per message.",
    ])
    if is_roleplay(mode):
        lines.append(
            "Stay fully in Azeroth and avoid game-mechanic terms."
        )
    return lines


def _build_single_prompt(
    participant: Dict,
    guild_name: str,
    faction: str,
    player_name: str,
    name_requested: bool,
    maximum: int,
    mode: str = 'roleplay',
):
    lines = _shared_prompt_lines(
        [participant],
        guild_name,
        faction,
        player_name,
        maximum,
        mode,
    )
    lines.extend([
        "",
        f"{participant['name']} gives exactly one "
        "short greeting.",
        "Aim for roughly 3 to 12 words.",
    ])
    if name_requested:
        lines.append(
            f"Naturally address {player_name} by name "
            "once, not necessarily at the beginning."
        )
    lines.append("Output the spoken greeting only.")
    return append_json_instruction(
        "\n".join(lines),
        allow_action=False,
        message_only=True,
    )


def _build_multi_prompt(
    participants: List[Dict],
    guild_name: str,
    faction: str,
    player_name: str,
    name_requested: bool,
    maximum: int,
    mode: str = 'roleplay',
) -> Tuple[object, List[str]]:
    names = [
        participant['name']
        for participant in participants
    ]
    lines = _shared_prompt_lines(
        participants,
        guild_name,
        faction,
        player_name,
        maximum,
        mode,
    )
    lines.extend([
        "",
        "Generate one independent short greeting from "
        "each selected guildmate.",
        "Each bot greets the player from its own "
        "perspective. Do not create a bot-to-bot "
        "conversation.",
        "Make the greetings clearly different from one "
        "another. Do not repeat the same welcome-back "
        "phrase or question.",
        "Every selected bot speaks exactly once.",
        "Aim for roughly 3 to 12 words per message.",
        "MESSAGE SEQUENCE:",
    ])
    for index, name in enumerate(names):
        instruction = (
            f"  Message {index + 1} ({name}): "
            "one distinct greeting"
        )
        if index == 0 and name_requested:
            instruction += (
                f"; naturally address {player_name} "
                "by name once"
            )
        elif index:
            instruction += (
                "; do not repeat the player's name"
            )
        lines.append(instruction)

    return (
        append_conversation_json_instruction(
            "\n".join(lines),
            names,
            len(names),
            allow_action=False,
            message_only=True,
        ),
        names,
    )


def _generate_single(
    client,
    config: Dict,
    event_id: int,
    participant: Dict,
    guild_name: str,
    faction: str,
    player_name: str,
    name_requested: bool,
    maximum: int,
    metadata: Dict,
) -> List[Dict]:
    prompt = _build_single_prompt(
        participant,
        guild_name,
        faction,
        player_name,
        name_requested,
        maximum,
        get_chatter_mode(config),
    )
    token_budget = max(80, _safe_int(config.get(
        'LLMChatter.GuildChatter.MaxTokens',
        200,
    ), 200))
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=token_budget,
        context=(
            f"guild-login:{event_id}:"
            f"{participant['name']}"
        ),
        label='guild_login_greeting',
        metadata=metadata,
    )
    text = _clean_greeting(
        parse_single_response(
            response or ''
        ).get('message', ''),
        participant['name'],
        maximum,
    )
    if not text:
        repair_metadata = dict(metadata)
        repair_metadata['guild_repair'] = True
        repair_prompt = (
            prompt
            + "\n\nYour previous output did not contain "
            "a usable greeting. Return exactly one "
            "short, non-empty greeting in the requested "
            "JSON shape."
        )
        response = call_llm(
            client,
            repair_prompt,
            config,
            max_tokens_override=token_budget,
            context=(
                f"guild-login-single-repair:{event_id}"
            ),
            label='guild_login_greeting',
            metadata=repair_metadata,
        )
        text = _clean_greeting(
            parse_single_response(
                response or ''
            ).get('message', ''),
            participant['name'],
            maximum,
        )
    if not text:
        return []
    return [{
        'name': participant['name'],
        'message': text,
    }]


def _generate_multi(
    client,
    config: Dict,
    event_id: int,
    participants: List[Dict],
    guild_name: str,
    faction: str,
    player_name: str,
    name_requested: bool,
    maximum: int,
    metadata: Dict,
) -> List[Dict]:
    prompt, names = _build_multi_prompt(
        participants,
        guild_name,
        faction,
        player_name,
        name_requested,
        maximum,
        get_chatter_mode(config),
    )
    base_tokens = max(100, _safe_int(config.get(
        'LLMChatter.GuildChatter.MaxTokens',
        200,
    ), 200))
    token_budget = min(
        600,
        base_tokens * len(participants),
    )
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=token_budget,
        context=f"guild-login-multi:{event_id}",
        label='guild_login_greeting',
        metadata=metadata,
    )
    messages = _clean_guild_conversation(
        parse_conversation_response(
            response or '',
            names,
        )
    )[:len(names)]

    if not _valid_guild_conversation(
        messages, names
    ):
        repair_metadata = dict(metadata)
        repair_metadata['guild_repair'] = True
        response = call_llm(
            client,
            build_conversation_json_repair_prompt(
                prompt,
                names,
                message_only=True,
            ),
            config,
            max_tokens_override=token_budget,
            context=f"guild-login-json-repair:{event_id}",
            label='guild_login_greeting',
            metadata=repair_metadata,
        )
        messages = _clean_guild_conversation(
            parse_conversation_response(
                response or '',
                names,
            )
        )[:len(names)]

    if not _valid_guild_conversation(
        messages, names
    ):
        return []

    for message in messages:
        message['message'] = _trim_greeting(
            message.get('message', ''),
            maximum,
        )
    return [
        message for message in messages
        if message.get('message')
    ]


def process_guild_login_greeting_event(
    db,
    client,
    config: Dict,
    event: Dict,
) -> bool:
    """Generate one or more short login greetings."""
    event_id = _safe_int(event.get('id'))
    if not _config_enabled(
        config,
        'LLMChatter.GuildChatter.'
        'LoginGreeting.Enable',
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'guild_login_greeting',
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    session_id = _safe_int(extra.get('session_id'))
    turn_id = _safe_int(extra.get('turn_id'))
    player_guid = _safe_int(extra.get('player_guid'))
    player_name = str(
        extra.get('player_name') or ''
    ).strip()
    guild_id = _safe_int(extra.get('guild_id'))
    if (
        not session_id
        or turn_id != 0
        or not player_guid
        or not player_name
        or not guild_id
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    if not _session_is_current(
        db,
        session_id,
        player_guid,
        turn_id,
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    candidates = _load_candidates(
        db,
        _normalize_candidates(extra),
    )
    if not candidates:
        _mark_event(db, event_id, 'skipped')
        return False

    responder_count = _choose_responder_count(
        config,
        len(candidates),
    )
    responders = _select_responders(
        candidates,
        "",
        responder_count,
        [],
        0,
    )
    if not responders:
        _mark_event(db, event_id, 'skipped')
        return False

    name_requested = (
        random.randint(1, 100)
        <= _bounded_percent(
            config,
            'LLMChatter.GuildChatter.'
            'LoginGreeting.PlayerNameChance',
            60,
        )
    )
    maximum = _max_characters(config)
    metadata = {
        'guild_id': guild_id,
        'guild_session_id': session_id,
        'guild_turn_id': turn_id,
        'guild_player_name': player_name,
        'guild_login_greeting': True,
        'guild_responder_count': len(responders),
        'guild_responders': ','.join(
            responder['name']
            for responder in responders
        ),
        'guild_player_name_requested': name_requested,
        'guild_initial_delay_seconds': _safe_int(
            extra.get('initial_delay_seconds')
        ),
        'guild_initial_delay_band': str(
            extra.get('initial_delay_band') or ''
        ),
        'guild_repair': False,
    }
    guild_name = str(
        extra.get('guild_name') or 'the guild'
    )
    faction = str(extra.get('team') or '')

    if len(responders) == 1:
        messages = _generate_single(
            client,
            config,
            event_id,
            responders[0],
            guild_name,
            faction,
            player_name,
            name_requested,
            maximum,
            metadata,
        )
        topology = 'single'
    else:
        messages = _generate_multi(
            client,
            config,
            event_id,
            responders,
            guild_name,
            faction,
            player_name,
            name_requested,
            maximum,
            metadata,
        )
        topology = 'multi_reply'

    if not messages and responders:
        topology = 'single_fallback'
        metadata['guild_responder_count'] = 1
        metadata['guild_responders'] = (
            responders[0]['name']
        )
        messages = _generate_single(
            client,
            config,
            event_id,
            responders[0],
            guild_name,
            faction,
            player_name,
            name_requested,
            maximum,
            metadata,
        )
        responders = responders[:1]

    if (
        messages
        and name_requested
        and not _contains_speaker_name(
            messages[0].get('message', ''),
            player_name,
        )
    ):
        messages[0]['message'] = _trim_greeting(
            _insert_reference_names(
                messages[0].get('message', ''),
                [player_name],
            ),
            maximum,
        )

    if not messages:
        _mark_event(db, event_id, 'skipped')
        return False

    if not _session_is_current(
        db,
        session_id,
        player_guid,
        turn_id,
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    guid_by_name = {
        responder['name']: responder['guid']
        for responder in responders
    }
    delays = _greeting_delays(messages, config)
    inserted = 0
    for sequence, message in enumerate(messages):
        name = str(message.get('name') or '')
        text = str(message.get('message') or '')
        guid = guid_by_name.get(name)
        if not guid or not text:
            continue
        insert_chat_message(
            db,
            bot_guid=guid,
            bot_name=name,
            message=text,
            channel='guild',
            delay_seconds=delays[sequence],
            event_id=event_id,
            sequence=sequence,
            player_guid=player_guid,
            owner_subsystem='guild',
        )
        inserted += 1

    if not inserted:
        _mark_event(db, event_id, 'skipped')
        return False

    if not _complete_event_if_current(
        db, event_id
    ):
        return False

    logger.info(
        "guild_login_greeting player=%s topology=%s "
        "responders=%s messages=%s session=%s",
        player_name,
        topology,
        ",".join(guid_by_name),
        inserted,
        session_id,
    )
    return True
