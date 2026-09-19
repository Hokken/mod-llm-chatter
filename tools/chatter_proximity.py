"""Proximity chatter event handlers."""

import json
import logging
import random
from typing import Dict, List, Optional

from chatter_constants import (
    EMOTE_CATEGORIES,
    EMOTE_NAME_TO_ID,
    PROXIMITY_CHAT_TOPICS,
    PROXIMITY_PLAYER_CHAT_TOPICS,
    REACTION_TONES,
)
from chatter_db import insert_chat_message
from chatter_llm import call_llm
from chatter_instance_context import (
    build_instance_context,
    build_location_metadata,
    build_location_prompt_lines,
)
from chatter_shared import (
    PromptParts,
    append_json_instruction,
    append_conversation_json_instruction,
    build_conversational_scale_guidance,
    find_addressed_bot,
    should_reply_to_optional_casual,
    brief_casual_response_fits,
    build_brief_casual_repair_prompt,
    parse_conversation_response,
    parse_extra_data,
    get_class_name,
    get_chatter_mode,
    get_gender_label,
    get_race_name,
    strip_conversation_actions,
)
from chatter_mode import (
    build_npc_chat_guidance,
    build_player_chat_guidance,
    build_player_prompt_header,
    is_roleplay,
    resolve_player_personality,
)
from chatter_text import (
    cleanup_message,
    parse_single_response,
    shorten_chat_message,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)

_DEFAULT_EMOTE_TONES = [
    "briefly",
    "with curiosity",
    "with dry wit",
    "with restraint",
]


def _prepare_emote_context(
    extra: Dict, player_emote: str
) -> None:
    emote_id = int(
        extra.get('player_emote_id', 0)
        or EMOTE_NAME_TO_ID.get(player_emote, 0)
    )
    category = EMOTE_CATEGORIES.get(
        emote_id, 'social'
    )
    extra['emote_category'] = category
    extra['reaction_tone'] = random.choice(
        REACTION_TONES.get(
            category, _DEFAULT_EMOTE_TONES
        )
    )


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
            "SELECT class, race, gender, level FROM characters "
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
            'gender': get_gender_label(
                int(row.get('gender', 0) or 0)
            ),
            'level': int(row.get('level', 0) or 0),
        }
    except Exception:
        logger.error(
            "query bot identity failed",
            exc_info=True,
        )
        return {}


def _query_bot_traits(
    db, bot_guid: int
) -> Dict[str, object]:
    if not bot_guid:
        return {}

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT trait1, trait2, trait3,"
            "       tone, backstory "
            "FROM llm_group_bot_traits "
            "WHERE bot_guid = %s LIMIT 1",
            (bot_guid,),
        )
        row = cursor.fetchone()
        if not row:
            return {}
        return {
            'traits': [
                trait for trait in (
                    row.get('trait1'),
                    row.get('trait2'),
                    row.get('trait3'),
                )
                if trait
            ],
            'tone': row.get('tone') or '',
            'backstory': row.get('backstory') or '',
        }
    except Exception:
        logger.error(
            "query bot traits failed",
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
        gender = speaker.get('gender') or ''
        if gender:
            parts.append(f"gender: {gender}")
        disposition = speaker.get('disposition') or ''
        rank = speaker.get('rank') or ''
        creature_type = speaker.get('creature_type') or ''
        qualification = speaker.get('qualification') or ''
        if disposition:
            parts.append(f"disposition: {disposition}")
        if rank and rank != 'normal':
            parts.append(f"rank: {rank}")
        if creature_type:
            parts.append(f"creature type: {creature_type}")
        if qualification:
            parts.append(f"qualified by: {qualification}")
        return " | ".join(part for part in parts if part)

    bot_guid = int(speaker.get('bot_guid', 0) or 0)
    info = _query_bot_identity(db, bot_guid)
    class_name = speaker.get('class') or info.get(
        'class', 'Adventurer'
    )
    race_name = speaker.get('race') or info.get(
        'race', 'Unknown'
    )
    gender = speaker.get('gender') or info.get(
        'gender', ''
    )
    gender_prefix = f"{gender} " if gender else ""
    return (
        f"{speaker.get('name', 'Bot')} | "
        f"{gender_prefix}{race_name} {class_name}"
    )


def _speaker_channel(speaker: Dict) -> str:
    return 'msay' if speaker.get('is_npc') else 'say'


def _speaker_is_roleplay(speaker: Dict, mode: str) -> bool:
    """NPCs are always in-world; only playerbots follow the mode."""
    return bool(speaker.get('is_npc')) or is_roleplay(mode)


def _apply_speaker_action_policy(
    parsed: List[Dict],
    speaker_by_name: Dict[str, Dict],
    mode: str,
    *,
    label: str,
) -> None:
    """Apply shared action chance, then enforce each speaker's mode."""
    strip_conversation_actions(parsed, label=label)
    for line in parsed:
        speaker = speaker_by_name.get(line.get('name', ''))
        if speaker and not _speaker_is_roleplay(speaker, mode):
            line['action'] = None


def _playerbot_topic(config: Optional[Dict]) -> str:
    mode = get_chatter_mode(config or {})
    pool = (
        PROXIMITY_CHAT_TOPICS
        if is_roleplay(mode)
        else PROXIMITY_PLAYER_CHAT_TOPICS
    )
    return random.choice(pool)


def _mixed_voice_guidance(mode: str) -> List[str]:
    lines = [
        "For each roster entry tagged [NPC], follow this rule: "
        + build_npc_chat_guidance(),
    ]
    lines.append(
        "For each roster entry tagged [PLAYERBOT]: "
        + build_player_chat_guidance(mode, 'say')
    )
    lines.append(
        "Apply the appropriate rule independently to every speaker."
    )
    lines.append(
        "Respect each NPC disposition tag. Hostile can mean wary, mocking, "
        "dismissive, or threatening, but does not mean combat has started."
    )
    lines.append(
        "Respect NPC creature-type and qualification tags. A listed "
        "non-humanoid is intentionally capable of speech; do not imply "
        "that every creature of its type can talk."
    )
    return lines


def _npc_disposition_guidance(speaker: Dict) -> str:
    disposition = str(
        speaker.get('disposition') or ''
    ).lower()
    if disposition == 'hostile':
        return (
            "This NPC is hostile to the player but not yet in combat. "
            "Sound wary, mocking, dismissive, or threatening as fits the "
            "NPC; do not force a combat taunt."
        )
    if disposition == 'unfriendly':
        return (
            "This NPC is unfriendly rather than openly hostile. A cool or "
            "guarded tone is appropriate, but violence is not inevitable."
        )
    return ''


def _npc_speech_capability_guidance(speaker: Dict) -> str:
    if not speaker.get('is_npc'):
        return ''
    creature_type = str(
        speaker.get('creature_type') or ''
    ).lower()
    if not creature_type or creature_type == 'humanoid':
        return ''
    qualification = str(
        speaker.get('qualification') or ''
    ).lower()
    if qualification == 'configured entry':
        reason = 'this exact creature entry was deliberately approved'
    elif qualification == 'functional npc':
        reason = 'its established interactive NPC role permits speech'
    else:
        reason = 'the supplied eligibility metadata permits speech'
    return (
        f"This {creature_type} can genuinely speak because {reason}. "
        "Ground its voice in the supplied name, title, role, and location; "
        "do not invent a persistent backstory or species-wide speech rule."
    )


def _location_lines(
    extra: Dict,
    mode: str,
    speakers: List[Dict],
) -> List[str]:
    lines = build_location_prompt_lines(extra)
    context = build_instance_context(extra)
    has_normal_playerbot = (
        not is_roleplay(mode)
        and any(
            not speaker.get('is_npc')
            for speaker in speakers
        )
    )
    if context['is_instance'] and has_normal_playerbot:
        lines.append(
            "Normal-mode playerbots treat the instance context as game "
            "knowledge. They must not claim to physically sense its lore."
        )
    return lines


def _insert_proximity_line(
    db,
    event_id: int,
    speaker: Dict,
    player_guid: int,
    sequence: int,
    delay_seconds: int,
    parsed: Dict,
    *,
    allow_emote_only: bool = False,
) -> bool:
    raw_message = parsed.get('message', '')
    message = strip_speaker_prefix(
        raw_message, speaker.get('name', '')
    )
    message = cleanup_message(
        message, action=parsed.get('action')
    )
    emote = parsed.get('emote')
    if not message and (
        not emote or not allow_emote_only
    ):
        return False
    if message:
        message = shorten_chat_message(message)

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
        emote=emote,
        npc_spawn_id=npc_spawn_id or None,
        player_guid=player_guid or None,
        addressee_player_guid=(
            int(parsed.get('_addressee_player_guid', 0) or 0)
            or None
        ),
        addressee_bot_guid=(
            int(parsed.get('_addressee_bot_guid', 0) or 0)
            or None
        ),
        addressee_npc_spawn_id=(
            int(parsed.get('_addressee_npc_spawn_id', 0) or 0)
            or None
        ),
    )
    return True


def _parse_brief_single_with_retry(
    client,
    config: Dict,
    prompt: PromptParts,
    response: str,
    *,
    brief_casual: bool,
    max_tokens: int,
    label: str,
    metadata: Dict,
) -> Dict:
    """Parse a single response and repair one oversized brief turn."""
    parsed = parse_single_response(response or '')
    if not brief_casual:
        return parsed

    rendered = cleanup_message(
        str(parsed.get('message') or ''),
        action=parsed.get('action'),
    )
    if brief_casual_response_fits(
        rendered, parsed.get('emote')
    ):
        return parsed

    repair_metadata = dict(metadata)
    repair_metadata['brief_casual_repair'] = True
    repaired = call_llm(
        client,
        build_brief_casual_repair_prompt(prompt),
        config,
        max_tokens_override=max_tokens,
        label=label,
        metadata=repair_metadata,
    )
    parsed = parse_single_response(repaired or '')
    rendered = cleanup_message(
        str(parsed.get('message') or ''),
        action=parsed.get('action'),
    )
    if not brief_casual_response_fits(
        rendered, parsed.get('emote')
    ):
        return {}
    return parsed


def _brief_conversation_fits(messages: List[Dict]) -> bool:
    return bool(messages) and all(
        brief_casual_response_fits(
            cleanup_message(
                str(message.get('message') or ''),
                action=message.get('action'),
            ),
            message.get('emote'),
        )
        for message in messages
    )


def _set_line_addressee(
    line: Dict,
    extra: Dict,
    participants: List[Dict],
    fallback_name: str,
) -> None:
    addressee = str(
        line.get('addressee') or fallback_name
    )
    speaker_name = str(line.get('name', ''))
    if addressee == speaker_name:
        addressee = fallback_name
    player_name = str(extra.get('player_name', ''))
    if addressee == speaker_name:
        if (
            extra.get('interaction_mode') != 'npc_aside'
            and player_name
            and player_name != speaker_name
        ):
            addressee = player_name
        else:
            addressee = next(
                (
                    str(participant.get('name', ''))
                    for participant in participants
                    if str(participant.get('name', ''))
                    and str(participant.get('name', ''))
                    != speaker_name
                ),
                '',
            )
    if addressee == player_name:
        line['_addressee_player_guid'] = int(
            extra.get('player_guid', 0) or 0
        )
        return

    known_addressees = list(participants)
    addressed_participant = extra.get('addressed_participant')
    if isinstance(addressed_participant, dict):
        addressed_name = str(
            addressed_participant.get('name', '')
        )
        if addressed_name and all(
            addressed_name
            != str(participant.get('name', ''))
            for participant in known_addressees
        ):
            known_addressees.append(addressed_participant)

    for participant in known_addressees:
        if addressee != str(participant.get('name', '')):
            continue
        if participant.get('is_npc'):
            line['_addressee_npc_spawn_id'] = int(
                participant.get('npc_spawn_id', 0) or 0
            )
        else:
            line['_addressee_bot_guid'] = int(
                participant.get('bot_guid', 0) or 0
            )
        return


def _emote_addressed_participant(
    extra: Dict,
    participants: List[Dict],
) -> Dict:
    addressed = extra.get('addressed_participant')
    if isinstance(addressed, dict) and addressed.get('name'):
        return addressed
    addressed_name = str(extra.get('addressed_name', ''))
    return next(
        (
            participant
            for participant in participants
            if str(participant.get('name', '')) == addressed_name
        ),
        {},
    )


def _single_prompt(
    db,
    extra: Dict,
    speaker: Dict,
    topic: str,
    player_message: Optional[str] = None,
    last_message: Optional[str] = None,
    config: Optional[Dict] = None,
) -> PromptParts:
    mode = get_chatter_mode(config or {})
    speaker_roleplay = _speaker_is_roleplay(speaker, mode)
    player_name = extra.get('player_name', 'the player')
    player_addressed = bool(
        extra.get('player_addressed', False)
    )
    speaker_desc = _describe_speaker(db, speaker)
    nearby_names = extra.get('nearby_names') or []
    speaker_traits = []
    speaker_tone = ''
    speaker_backstory = ''
    if not speaker.get('is_npc'):
        profile = _query_bot_traits(
            db,
            int(speaker.get('bot_guid', 0) or 0),
        )
        speaker_traits = profile.get('traits', [])
        speaker_tone = profile.get('tone', '')
        speaker_backstory = profile.get(
            'backstory', ''
        )
        speaker_traits, speaker_tone = resolve_player_personality(
            speaker.get('name', 'Bot'),
            speaker_traits,
            speaker_tone,
            mode,
        )

    if speaker.get('is_npc'):
        lines = [
            build_npc_chat_guidance(),
            "Write an extremely short, immersive in-world /say line.",
        ]
    elif speaker_roleplay:
        lines = [
            "Write an extremely short, immersive in-world /say line.",
            build_player_prompt_header(
                speaker.get('name', 'Bot'),
                speaker.get('race') or '',
                speaker.get('class') or '',
                speaker.get('level'),
                speaker.get('gender') or '',
                mode,
                channel='say',
            ),
        ]
    else:
        info = _query_bot_identity(
            db, int(speaker.get('bot_guid', 0) or 0)
        )
        lines = [build_player_prompt_header(
            speaker.get('name', 'Bot'),
            speaker.get('race') or info.get('race', ''),
            speaker.get('class') or info.get('class', ''),
            speaker.get('level') or info.get('level'),
            speaker.get('gender') or info.get('gender', ''),
            mode,
            channel='say',
        )]
    brief_casual = bool(extra.get('brief_casual'))
    lines.extend([
        (
            "Message must use 2-8 words and no more than 50 "
            "characters."
            if brief_casual
            else "Message must be 8-15 words, natural, local, "
            "and low-stakes."
        ),
        "No AI talk, markdown, or forced slang.",
        "",
        f"Speaker: {speaker_desc}",
    ])
    lines.extend(_location_lines(
        extra, mode, [speaker]
    ))
    disposition_guidance = _npc_disposition_guidance(
        speaker
    )
    if disposition_guidance:
        lines.append(disposition_guidance)
    speech_guidance = _npc_speech_capability_guidance(
        speaker
    )
    if speech_guidance:
        lines.append(speech_guidance)
    if speaker_traits:
        lines.append(
            "Speaker personality: "
            + ", ".join(speaker_traits)
        )
    if speaker_tone:
        lines.append(f"Speaker tone: {speaker_tone}")
    # RNG-gate backstory injection
    if speaker_roleplay and speaker_backstory and config:
        bs_enabled = int(config.get(
            'LLMChatter.Backstory.Enable', 1
        ))
        prox_chance = int(config.get(
            'LLMChatter.Backstory.ProximityChance',
            15,
        )) / 100.0
        if bs_enabled and random.random() < prox_chance:
            lines.append(
                f"Speaker background: "
                f"{speaker_backstory}"
            )
    lines.append(f"Topic seed: {topic}")

    if player_message:
        lines.append(
            f"Player message to answer: {player_message}"
        )
        lines.append(
            build_conversational_scale_guidance(
                force_brief=bool(extra.get('brief_casual')),
            )
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
        allow_action=speaker_roleplay,
        skip_emote=False,
        allow_emote_only=(
            bool(player_message) and brief_casual
        ),
    )


def _conversation_prompt(
    db, extra: Dict, participants: List[Dict],
    config: Optional[Dict] = None,
) -> PromptParts:
    mode = get_chatter_mode(config or {})
    has_playerbot = any(
        not speaker.get('is_npc')
        for speaker in participants
    )
    has_npc = any(
        speaker.get('is_npc')
        for speaker in participants
    )
    if is_roleplay(mode) or not has_playerbot:
        topic = random.choice(PROXIMITY_CHAT_TOPICS)
    else:
        topic = (
            "NPC angle: " + random.choice(PROXIMITY_CHAT_TOPICS)
            + "; playerbot angle: "
            + random.choice(PROXIMITY_PLAYER_CHAT_TOPICS)
        )
    max_lines = max(
        2, min(
            int(extra.get('max_lines', 3) or 3),
            len(participants) + 1,
        ),
    )
    # Check backstory config once
    _bs_enabled = False
    _bs_chance = 0.0
    if config:
        _bs_enabled = int(config.get(
            'LLMChatter.Backstory.Enable', 1
        )) == 1
        _bs_chance = int(config.get(
            'LLMChatter.Backstory.ProximityChance',
            15,
        )) / 100.0

    roster_lines = []
    for speaker in participants:
        speaker_type = (
            'NPC' if speaker.get('is_npc') else 'PLAYERBOT'
        )
        line = (
            f"- [{speaker_type}] "
            f"{_describe_speaker(db, speaker)}"
        )
        if not speaker.get('is_npc'):
            profile = _query_bot_traits(
                db,
                int(speaker.get('bot_guid', 0) or 0),
            )
            traits = profile.get('traits', [])
            tone = profile.get('tone', '')
            backstory = profile.get('backstory', '')
            traits, tone = resolve_player_personality(
                speaker.get('name', 'Bot'),
                traits,
                tone,
                mode,
            )
            if traits:
                line += (
                    "; personality: "
                    + ", ".join(traits)
                )
            if tone:
                line += f"; tone: {tone}"
            if (is_roleplay(mode) and backstory and _bs_enabled
                    and random.random() < _bs_chance):
                line += (
                    f"; background: {backstory}"
                )
        roster_lines.append(line)
    roster = "\n".join(roster_lines)

    nearby_names = extra.get('nearby_names') or []
    player_name = extra.get('player_name', '')
    player_addressed = bool(
        extra.get('player_addressed', False)
    )

    lines = [
        "You write short World of Warcraft ambient "
        "overheard /say conversations.",
        "Use only the provided speaker names.",
        "Each message must be 6-14 words, natural, and relevant to the "
        "nearby exchange.",
        "Every listed speaker must speak at least once.",
        "Keep the exchange brief.",
        "",
        f"Topic seed: {topic}",
        f"Write EXACTLY {max_lines} messages.",
        "Speakers may address each other by name.",
    ]
    lines.extend(_location_lines(
        extra, mode, participants
    ))
    lines.extend(_mixed_voice_guidance(mode))

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
        allow_action=is_roleplay(mode) or has_npc,
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
        topic or (
            random.choice(PROXIMITY_CHAT_TOPICS)
            if speaker.get('is_npc')
            else _playerbot_topic(config)
        ),
        player_message=player_message,
        last_message=last_message,
        config=config,
    )
    max_tokens = _get_proximity_int(
        config, 'MaxTokensPerLine', 120
    )
    metadata = {
        **build_location_metadata(extra),
        'speaker_name': speaker.get('name', ''),
        'brief_casual': bool(extra.get('brief_casual')),
    }
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label=label,
        metadata=metadata,
    )
    if not response:
        return False

    parsed = _parse_brief_single_with_retry(
        client,
        config,
        prompt,
        response,
        brief_casual=bool(extra.get('brief_casual')),
        max_tokens=max_tokens,
        label=label,
        metadata=metadata,
    )
    return _insert_proximity_line(
        db,
        message_event_id or event_id,
        speaker,
        int(extra.get('player_guid', 0) or 0),
        sequence,
        delay_seconds,
        parsed,
        allow_emote_only=bool(
            extra.get('brief_casual')
        ),
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
        db, extra, participants, config=config,
    )
    max_lines = int(extra.get('max_lines', 3) or 3)
    # Each line needs ~60-80 tokens for JSON structure
    # (speaker, message, emote, action keys + values).
    # The per-line config controls message brevity in the
    # prompt, but the token budget must cover full JSON.
    max_tokens = 80 * max_lines
    metadata = {
        **build_location_metadata(extra),
        'speaker_count': len(participants),
        'brief_casual': bool(extra.get('brief_casual')),
    }
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label='proximity_conversation',
        metadata=metadata,
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
    for index, line in enumerate(parsed[:max_lines]):
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
        'npc_entry': int(
            extra.get('responder_npc_entry', 0) or 0
        ),
        'role': extra.get('responder_role', ''),
        'sub_name': extra.get(
            'responder_sub_name', ''
        ),
        'disposition': extra.get(
            'responder_disposition', ''
        ),
        'rank': extra.get('responder_rank', ''),
        'creature_type': extra.get(
            'responder_creature_type', ''
        ),
        'qualification': extra.get(
            'responder_qualification', ''
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

    player_message = str(extra.get('player_message', ''))
    scale = find_addressed_bot(
        player_message,
        [str(responder.get('name', ''))],
        client=client,
        config=config,
        chat_history=str(extra.get('last_message', '')),
    )
    extra['brief_casual'] = bool(scale.get('brief_casual'))
    if not should_reply_to_optional_casual(config, scale):
        logger.info(
            "proximity_reply event=%s left unanswered "
            "after optional-casual RNG",
            event_id,
        )
        _mark_event(db, event_id, 'skipped')
        return False

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
        player_message=player_message,
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
    map_id: int, instance_id: int,
    addressed_name: str = '',
    addressed_npc_spawn_id: int = 0,
    limit: int = 10,
) -> List[Dict]:
    """Fetch recent lines involving the addressed NPC."""
    if not player_guid or not zone_id or not addressed_name:
        return []
    try:
        if addressed_npc_spawn_id:
            identity_sql = (
                "    AND JSON_VALID(e.extra_data)"
                "    AND JSON_CONTAINS("
                "JSON_EXTRACT(e.extra_data, '$.participants'), "
                "JSON_OBJECT('npc_spawn_id', %s))"
            )
            identity_params = [addressed_npc_spawn_id]
        else:
            identity_sql = (
                "    AND JSON_VALID(e.extra_data)"
                "    AND (JSON_UNQUOTE(JSON_EXTRACT("
                "e.extra_data, '$.addressed_name')) = %s"
                "      OR JSON_SEARCH(JSON_EXTRACT("
                "e.extra_data, '$.participants[*].name'), "
                "'one', %s) IS NOT NULL)"
            )
            identity_params = [addressed_name, addressed_name]

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT m.bot_name, m.message, m.delivered_at,"
            "       e.id AS event_id, e.extra_data"
            "  FROM llm_chatter_messages m"
            "  JOIN llm_chatter_events e"
            "    ON m.event_id = e.id"
            "  WHERE m.delivered = 1"
            "    AND m.drop_reason IS NULL"
            "    AND m.channel IN ('say', 'msay')"
            "    AND e.zone_id = %s"
            "    AND e.map_id = %s"
            "    AND m.player_guid = %s"
            "    AND m.delivered_at"
            "        > DATE_SUB(NOW(),"
            "          INTERVAL 5 MINUTE)"
            + identity_sql
            + "  ORDER BY m.delivered_at DESC"
            "  LIMIT %s",
            (
                zone_id, map_id, player_guid,
                *identity_params, limit * 2,
            ),
        )
        rows = cursor.fetchall()
        history = []
        seen_events = set()
        for row in reversed(rows):
            try:
                event_extra = json.loads(
                    row.get('extra_data') or '{}'
                )
            except (TypeError, ValueError):
                continue
            if instance_id and int(
                event_extra.get('instance_id', 0) or 0
            ) != instance_id:
                continue
            participant_names = [
                str(item.get('name', ''))
                for item in event_extra.get('participants', [])
                if isinstance(item, dict)
            ]
            previous_addressed = str(
                event_extra.get('addressed_name', '')
            )
            participant_spawn_ids = {
                int(item.get('npc_spawn_id', 0) or 0)
                for item in event_extra.get('participants', [])
                if isinstance(item, dict) and item.get('is_npc')
            }
            same_addressed_npc = (
                addressed_npc_spawn_id > 0
                and addressed_npc_spawn_id in participant_spawn_ids
            )
            same_legacy_name = (
                not addressed_npc_spawn_id
                and (
                    addressed_name == previous_addressed
                    or addressed_name in participant_names
                )
            )
            if not same_addressed_npc and not same_legacy_name:
                continue

            event_id = int(row.get('event_id', 0) or 0)
            if event_id not in seen_events:
                player_message = str(
                    event_extra.get('player_message', '')
                ).strip()
                player_name = str(
                    event_extra.get('player_name', 'Player')
                )
                if player_message:
                    history.append({
                        'name': player_name,
                        'message': player_message,
                    })
                else:
                    player_emote = str(
                        event_extra.get('player_emote', '')
                    ).strip()
                    if player_emote:
                        target_name = (
                            previous_addressed
                            or addressed_name
                        )
                        history.append({
                            'name': player_name,
                            'message': (
                                f"[performed /{player_emote}"
                                f" at {target_name}]"
                            ),
                        })
                seen_events.add(event_id)
            history.append({
                'name': row['bot_name'],
                'message': row['message'],
            })
        return history[-limit:]
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
    config: Optional[Dict] = None,
) -> PromptParts:
    mode = get_chatter_mode(config or {})
    speaker_roleplay = _speaker_is_roleplay(speaker, mode)
    player_name = extra.get(
        'player_name', 'the player'
    )
    speaker_desc = _describe_speaker(db, speaker)
    nearby_names = extra.get('nearby_names') or []

    if speaker.get('is_npc'):
        lines = [build_npc_chat_guidance()]
    elif speaker_roleplay:
        lines = [build_player_prompt_header(
            speaker.get('name', 'Bot'),
            speaker.get('race', ''),
            speaker.get('class', ''),
            speaker.get('level'),
            speaker.get('gender', ''),
            mode,
            channel='say',
        )]
    else:
        info = _query_bot_identity(
            db, int(speaker.get('bot_guid', 0) or 0)
        )
        lines = [build_player_prompt_header(
            speaker.get('name', 'Bot'),
            speaker.get('race') or info.get('race', ''),
            speaker.get('class') or info.get('class', ''),
            speaker.get('level') or info.get('level'),
            speaker.get('gender') or info.get('gender', ''),
            mode,
            channel='say',
        )]
    brief_casual = bool(extra.get('brief_casual'))
    lines.extend([
        (
            "Write an extremely short /say reply using 2-8 words "
            "and no more than 50 characters."
            if brief_casual
            else "Write an extremely short /say reply of 8-15 words."
        ),
        "Keep it natural and low-stakes. No AI talk or markdown.",
        "",
        f"Speaker: {speaker_desc}",
    ])
    lines.extend(_location_lines(
        extra, mode, [speaker]
    ))
    disposition_guidance = _npc_disposition_guidance(
        speaker
    )
    if disposition_guidance:
        lines.append(disposition_guidance)
    speech_guidance = _npc_speech_capability_guidance(
        speaker
    )
    if speech_guidance:
        lines.append(speech_guidance)

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
    lines.append(build_conversational_scale_guidance(
        force_brief=bool(extra.get('brief_casual')),
    ))

    history_block = _format_history_block(history)
    if history_block:
        lines.append("")
        lines.append(history_block)

    if nearby_names:
        lines.append(
            "Reply to the player. Other nearby people may be mentioned "
            "but not addressed: "
            + ", ".join(nearby_names[:5]) + "."
        )

    return append_json_instruction(
        "\n".join(lines) + "\n",
        allow_action=speaker_roleplay,
        skip_emote=False,
        allow_emote_only=brief_casual,
    )


def _player_say_conversation_prompt(
    db,
    extra: Dict,
    participants: List[Dict],
    player_message: str,
    history: List[Dict],
    config: Optional[Dict] = None,
) -> PromptParts:
    mode = get_chatter_mode(config or {})
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
        f"- [{'NPC' if speaker.get('is_npc') else 'PLAYERBOT'}] "
        f"{_describe_speaker(db, speaker)}"
        for speaker in participants
    )
    nearby_names = extra.get('nearby_names') or []

    brief_casual = bool(extra.get('brief_casual'))
    lines = [
        "You write short World of Warcraft "
        "overheard /say conversations.",
        "Use only the provided speaker names.",
        (
            "Each message must use 2-8 words and no more than 50 "
            "characters."
            if brief_casual
            else "Each message must be 6-14 words, natural, and "
            "relevant to the nearby exchange."
        ),
        "Keep the exchange brief.",
        "",
    ]
    lines.extend(_location_lines(
        extra, mode, participants
    ))
    lines.extend(_mixed_voice_guidance(mode))

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
    lines.append(build_conversational_scale_guidance(
        force_brief=bool(extra.get('brief_casual')),
    ))
    interaction_mode = extra.get(
        'interaction_mode', 'player_inclusive'
    )
    if interaction_mode == 'npc_aside':
        lines.extend([
            "The NPCs discuss the player's actual words with each other.",
            "Do not address the player or invent additional player speech.",
        ])
    else:
        lines.append(
            "Speakers should react to or acknowledge "
            "the player's words."
        )
    lines.append(
        f"Write EXACTLY {max_lines} messages."
    )
    if interaction_mode == 'npc_aside':
        lines.append(
            "Speakers address only each other, never the player."
        )
    else:
        lines.append(
            "Speakers may address each other or the "
            "player by name."
        )

    history_block = _format_history_block(history)
    if history_block:
        lines.append("")
        lines.append(history_block)

    if nearby_names:
        lines.append(
            "Also nearby: "
            + ", ".join(nearby_names[:5])
            + ". They may be mentioned but are not participants."
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
        allow_action=(
            is_roleplay(mode)
            or any(s.get('is_npc') for s in participants)
        ),
        addressee_names=(
            speaker_names
            if interaction_mode == 'npc_aside'
            else [player_name] + speaker_names
        ),
        allow_emote_only=brief_casual,
    )


def _player_emote_single_prompt(
    db,
    extra: Dict,
    speaker: Dict,
    player_emote: str,
    config: Optional[Dict] = None,
    history: Optional[List[Dict]] = None,
) -> PromptParts:
    mode = get_chatter_mode(config or {})
    player_name = extra.get('player_name', 'the player')
    addressed = str(
        extra.get('addressed_name')
        or speaker.get('name', 'the speaker')
    )
    addressed_speaks = bool(
        extra.get('addressed_speaks', True)
    )
    speaker_is_npc = bool(speaker.get('is_npc'))
    if speaker_is_npc:
        lines = [
            build_npc_chat_guidance(),
            "Write an extremely short /say reaction of 2-8 words.",
            "Keep it natural and low-stakes. No AI talk or markdown.",
            "",
            f"Speaker: {_describe_speaker(db, speaker)}",
        ]
    else:
        identity = {}
        if any(
            not speaker.get(field)
            for field in ('race', 'class', 'gender', 'level')
        ):
            identity = _query_bot_identity(
                db, int(speaker.get('bot_guid', 0) or 0)
            )
        lines = [
            build_player_prompt_header(
                speaker.get('name', 'Bot'),
                speaker.get('race') or identity.get('race', ''),
                speaker.get('class') or identity.get('class', ''),
                speaker.get('level') or identity.get('level'),
                speaker.get('gender') or identity.get('gender', ''),
                mode,
                channel='say',
            ),
            "Write an extremely short /say reaction of 2-8 words.",
            "Keep it natural and low-stakes. No AI talk or markdown.",
        ]
    lines.extend(_location_lines(extra, mode, [speaker]))
    if speaker_is_npc:
        disposition = _npc_disposition_guidance(speaker)
        if disposition:
            lines.append(disposition)
        speech_guidance = _npc_speech_capability_guidance(speaker)
        if speech_guidance:
            lines.append(speech_guidance)
    lines.extend([
        f"The player ({player_name}) performed /{player_emote} "
        f"directly at {addressed}.",
        f"Social meaning: {extra.get('emote_category', 'social')}.",
        f"React {extra.get('reaction_tone', 'briefly')}.",
        "React to that real action. "
        "Do not invent or quote player speech.",
        build_conversational_scale_guidance(
            subject="emote",
            force_brief=True,
        ),
    ])
    if not addressed_speaks:
        lines.extend([
            f"{speaker.get('name', 'The speaker')} witnessed the gesture "
            "nearby and may comment on it.",
            f"{addressed} remains silent and is not the speaker. "
            "Do not invent dialogue or actions for them.",
        ])
    mirror_emote = str(extra.get('mirror_emote', '')).strip()
    if mirror_emote:
        mirror_subject = (
            "The speaker" if addressed_speaks else addressed
        )
        lines.append(
            f"{mirror_subject} is also scheduled to perform "
            f"/{mirror_emote}; the spoken reaction must not "
            "contradict that animation."
        )
    history_block = _format_history_block(history or [])
    if history_block:
        lines.extend(["", history_block])
    return append_json_instruction(
        "\n".join(lines) + "\n",
        allow_action=_speaker_is_roleplay(speaker, mode),
        skip_emote=False,
        allow_emote_only=True,
    )


def _player_emote_conversation_prompt(
    db,
    extra: Dict,
    participants: List[Dict],
    player_emote: str,
    config: Optional[Dict] = None,
    history: Optional[List[Dict]] = None,
) -> PromptParts:
    mode = get_chatter_mode(config or {})
    player_name = extra.get('player_name', 'the player')
    addressed = extra.get('addressed_name', '')
    addressed_speaks = bool(
        extra.get('addressed_speaks', True)
    )
    first_speaker = (
        addressed
        if addressed_speaks
        else participants[0].get('name', '')
    )
    max_lines = max(
        2,
        min(
            int(extra.get('max_lines', 3) or 3),
            len(participants) + 1,
        ),
    )
    roster = "\n".join(
        f"- [{'NPC' if speaker.get('is_npc') else 'PLAYERBOT'}] "
        f"{_describe_speaker(db, speaker)}"
        for speaker in participants
    )
    lines = [
        "You write short World of Warcraft overheard /say conversations.",
        "Use only the provided speaker names.",
        "Each message must be 2-8 words, natural, and relevant.",
        "Every listed speaker must speak at least once.",
        "Never invent dialogue, thoughts, or actions for the real player.",
        "",
    ]
    lines.extend(_location_lines(extra, mode, participants))
    lines.extend(_mixed_voice_guidance(mode))
    lines.extend([
        f"The player ({player_name}) performed /{player_emote} "
        f"directly at {addressed}.",
        f"Social meaning: {extra.get('emote_category', 'social')}.",
        f"Overall reaction tone: "
        f"{extra.get('reaction_tone', 'briefly')}.",
        f"The FIRST message MUST be spoken by {first_speaker}.",
        build_conversational_scale_guidance(
            subject="emote",
            force_brief=True,
        ),
    ])
    if not addressed_speaks:
        lines.extend([
            f"{addressed} remains silent and is not in the speaker roster.",
            f"Do not invent dialogue or actions for {addressed}.",
            "The listed speakers witnessed the gesture and may comment "
            "on that same action.",
        ])
    mirror_emote = str(extra.get('mirror_emote', '')).strip()
    if mirror_emote:
        lines.append(
            f"{addressed} is also scheduled to perform /{mirror_emote}; "
            "the conversation must not contradict that animation."
        )
    interaction_mode = extra.get(
        'interaction_mode', 'player_inclusive'
    )
    if interaction_mode == 'npc_aside':
        lines.extend([
            "The speakers discuss the player's real action with each other.",
            "Do not address the player or invent speech for them.",
            "Speakers address only each other, never the player.",
        ])
    else:
        lines.append(
            "Speakers may react to the player and to each other."
        )
    history_block = _format_history_block(history or [])
    if history_block:
        lines.extend(["", history_block])
    lines.extend([
        f"Write EXACTLY {max_lines} messages.",
        "Speakers:",
        roster,
    ])
    return append_conversation_json_instruction(
        "\n".join(lines) + "\n",
        [speaker.get('name', '') for speaker in participants],
        max_lines,
        allow_action=(
            is_roleplay(mode)
            or any(s.get('is_npc') for s in participants)
        ),
        addressee_names=(
            [
                speaker.get('name', '')
                for speaker in participants
            ]
            if interaction_mode == 'npc_aside'
            else [player_name] + [
                speaker.get('name', '')
                for speaker in participants
            ] + (
                [addressed] if not addressed_speaks else []
            )
        ),
        allow_emote_only=True,
    )


def _generate_player_say_single(
    db,
    client,
    config,
    event_id: int,
    extra: Dict,
    speaker: Dict,
    player_message: str,
    history: List[Dict],
    *,
    label: str = 'proximity_player_say',
) -> bool:
    prompt = _player_say_single_prompt(
        db, extra, speaker, player_message, history,
        config,
    )
    max_tokens = _get_proximity_int(
        config, 'MaxTokensPerLine', 120
    )
    metadata = {
        **build_location_metadata(extra),
        'speaker_name': speaker.get('name', ''),
        'brief_casual': bool(extra.get('brief_casual')),
    }
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label=label,
        metadata=metadata,
    )
    if not response:
        return False
    parsed = _parse_brief_single_with_retry(
        client,
        config,
        prompt,
        response,
        brief_casual=bool(extra.get('brief_casual')),
        max_tokens=max_tokens,
        label=label,
        metadata=metadata,
    )
    _set_line_addressee(
        parsed,
        extra,
        [speaker],
        str(extra.get('player_name', '')),
    )
    return _insert_proximity_line(
        db,
        event_id,
        speaker,
        int(extra.get('player_guid', 0) or 0),
        0,
        0,
        parsed,
        allow_emote_only=bool(
            extra.get('brief_casual')
        ),
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
    map_id = int(extra.get('map_id', 0) or 0)
    instance_id = int(
        extra.get('instance_id', 0) or 0
    )
    history_addressed_name = str(
        extra.get('addressed_name')
        or participants[0].get('name', '')
    )
    history = _fetch_proximity_history(
        db, player_guid, zone_id,
        map_id, instance_id,
        history_addressed_name,
        int(participants[0].get('npc_spawn_id', 0) or 0),
    )
    scale = find_addressed_bot(
        player_message,
        [str(participant.get('name', '')) for participant in participants],
        client=client,
        config=config,
        chat_history=_format_history_block(history),
    )
    extra['brief_casual'] = bool(scale.get('brief_casual'))
    if not should_reply_to_optional_casual(config, scale):
        logger.info(
            "proximity_player_say event=%s left unanswered "
            "after optional-casual RNG",
            event_id,
        )
        _mark_event(db, event_id, 'skipped')
        return False

    ok = _generate_player_say_single(
        db,
        client,
        config,
        event_id,
        extra,
        participants[0],
        player_message,
        history,
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
    map_id = int(extra.get('map_id', 0) or 0)
    instance_id = int(
        extra.get('instance_id', 0) or 0
    )
    history_addressed_name = str(
        extra.get('addressed_name')
        or participants[0].get('name', '')
    )
    history = _fetch_proximity_history(
        db, player_guid, zone_id,
        map_id, instance_id,
        history_addressed_name,
        int(participants[0].get('npc_spawn_id', 0) or 0),
    )
    scale = find_addressed_bot(
        player_message,
        [str(participant.get('name', '')) for participant in participants],
        client=client,
        config=config,
        chat_history=_format_history_block(history),
    )
    extra['brief_casual'] = bool(scale.get('brief_casual'))
    if not should_reply_to_optional_casual(config, scale):
        logger.info(
            "proximity_player_conversation event=%s left "
            "unanswered after optional-casual RNG",
            event_id,
        )
        _mark_event(db, event_id, 'skipped')
        return False
    if (
        bool(scale.get('reply_optional'))
        or (
            extra['brief_casual']
            and not bool(scale.get('multi_addressed'))
        )
    ):
        ok = _generate_player_say_single(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            player_message,
            history,
            label='proximity_player_conversation_brief',
        )
        _mark_event(
            db, event_id,
            'completed' if ok else 'skipped',
        )
        return ok

    prompt = _player_say_conversation_prompt(
        db, extra, participants,
        player_message, history, config
    )
    max_lines = int(
        extra.get('max_lines', 3) or 3
    )
    max_tokens = 80 * max_lines
    metadata = {
        **build_location_metadata(extra),
        'speaker_count': len(participants),
        'brief_casual': bool(extra.get('brief_casual')),
    }
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label='proximity_player_conversation',
        metadata=metadata,
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    names = [
        speaker.get('name', '')
        for speaker in participants
    ]
    addressee_names = (
        names
        if extra.get('interaction_mode') == 'npc_aside'
        else [str(extra.get('player_name', '')), *names]
    )
    parsed = parse_conversation_response(
        response, names,
        unique_tokens_only=True,
        addressee_names=addressee_names,
        allow_emote_only=bool(
            extra.get('brief_casual')
        ),
    )
    if (
        extra.get('brief_casual')
        and not _brief_conversation_fits(parsed)
    ):
        repair_metadata = dict(metadata)
        repair_metadata['brief_casual_repair'] = True
        response = call_llm(
            client,
            build_brief_casual_repair_prompt(prompt),
            config,
            max_tokens_override=max_tokens,
            label='proximity_player_conversation',
            metadata=repair_metadata,
        )
        parsed = parse_conversation_response(
            response or '',
            names,
            unique_tokens_only=True,
            addressee_names=addressee_names,
            allow_emote_only=True,
        )
        if not _brief_conversation_fits(parsed):
            parsed = []
    line_delay = max(0, int(
        extra.get('line_delay_seconds', 4) or 4
    ))
    speaker_by_name = {
        speaker.get('name', ''): speaker
        for speaker in participants
    }
    addressed = extra.get('addressed_name', '')
    parsed = parsed[:max_lines]
    parsed_speakers = {
        line.get('name', '') for line in parsed
    }
    if not parsed or (
        addressed and parsed[0].get('name') != addressed
    ) or not set(names).issubset(parsed_speakers):
        logger.warning(
            "proximity_player_conversation event %s "
            "fell back to its addressed speaker",
            event_id,
        )
        fallback = _generate_player_say_single(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            player_message,
            history,
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

    _apply_speaker_action_policy(
        parsed,
        speaker_by_name,
        get_chatter_mode(config or {}),
        label='proximity_player_conversation',
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
        first_fallback = (
            names[1]
            if extra.get('interaction_mode') == 'npc_aside'
            else str(extra.get('player_name', ''))
        )
        fallback_addressee = (
            first_fallback
            if index == 0
            else parsed[index - 1].get('name', '')
        )
        _set_line_addressee(
            line,
            extra,
            participants,
            fallback_addressee,
        )
        ok = _insert_proximity_line(
            db,
            event_id,
            speaker,
            player_guid,
            index,
            cumulative_delay,
            line,
            allow_emote_only=bool(
                extra.get('brief_casual')
            ),
        )
        if ok:
            inserted += 1

    if inserted == 0:
        logger.warning(
            "proximity_player_conversation "
            "event %s fell back to single-line",
            event_id,
        )
        fallback = _generate_player_say_single(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            player_message,
            history,
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
    return inserted > 0


def _generate_player_emote_single(
    db,
    client,
    config,
    event_id: int,
    extra: Dict,
    speaker: Dict,
    player_emote: str,
    history: Optional[List[Dict]] = None,
    *,
    label: str = 'proximity_player_emote',
) -> bool:
    prompt = _player_emote_single_prompt(
        db, extra, speaker, player_emote,
        config, history,
    )
    max_tokens = _get_proximity_int(
        config, 'MaxTokensPerLine', 120
    )
    metadata = {
        **build_location_metadata(extra),
        'speaker_name': speaker.get('name', ''),
        'player_emote': player_emote,
        'brief_emote': True,
    }
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label=label,
        metadata=metadata,
    )
    if not response:
        return False
    parsed = parse_single_response(response)
    _set_line_addressee(
        parsed,
        extra,
        [speaker],
        str(extra.get('player_name', '')),
    )
    return _insert_proximity_line(
        db,
        event_id,
        speaker,
        int(extra.get('player_guid', 0) or 0),
        0,
        0,
        parsed,
        allow_emote_only=True,
    )


def handle_proximity_player_emote(
    db, client, config, event
):
    event_id = int(event['id'])
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'proximity_player_emote',
    )
    participants = extra.get('participants') or []
    player_emote = extra.get('player_emote', '')
    addressed = extra.get('addressed_name', '')
    if not participants or not player_emote or not addressed:
        _mark_event(db, event_id, 'skipped')
        return False

    _prepare_emote_context(extra, player_emote)
    player_guid = int(
        extra.get('player_guid', 0) or 0
    )
    zone_id = int(extra.get('zone_id', 0) or 0)
    map_id = int(extra.get('map_id', 0) or 0)
    instance_id = int(
        extra.get('instance_id', 0) or 0
    )
    addressed_participant = _emote_addressed_participant(
        extra, participants
    )
    history = _fetch_proximity_history(
        db, player_guid, zone_id,
        map_id, instance_id,
        str(addressed),
        int(
            addressed_participant.get('npc_spawn_id', 0)
            or 0
        ),
    )

    if len(participants) == 1:
        ok = _generate_player_emote_single(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            player_emote,
            history,
        )
        _mark_event(
            db, event_id,
            'completed' if ok else 'skipped',
        )
        return ok

    prompt = _player_emote_conversation_prompt(
        db, extra, participants, player_emote,
        config, history,
    )
    max_lines = max(
        2, int(extra.get('max_lines', 3) or 3)
    )
    max_tokens = 80 * max_lines
    metadata = {
        **build_location_metadata(extra),
        'speaker_count': len(participants),
        'player_emote': player_emote,
        'interaction_mode': extra.get(
            'interaction_mode', 'player_inclusive'
        ),
        'addressed_speaks': bool(
            extra.get('addressed_speaks', True)
        ),
        'brief_emote': True,
    }
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max_tokens,
        label='proximity_player_emote',
        metadata=metadata,
    )
    names = [
        speaker.get('name', '')
        for speaker in participants
    ]
    addressed_speaks = bool(
        extra.get('addressed_speaks', True)
    )
    addressee_names = (
        names
        if extra.get('interaction_mode') == 'npc_aside'
        else [str(extra.get('player_name', '')), *names]
    )
    if not addressed_speaks and str(addressed):
        addressee_names.append(str(addressed))
    parsed = (
        parse_conversation_response(
            response,
            names,
            unique_tokens_only=True,
            addressee_names=addressee_names,
            allow_emote_only=True,
        )
        if response else []
    )
    parsed = parsed[:max_lines]
    parsed_speakers = {
        line.get('name', '') for line in parsed
    }
    if (
        not parsed
        or parsed[0].get('name')
        != (addressed if addressed_speaks else names[0])
        or not set(names).issubset(parsed_speakers)
    ):
        logger.warning(
            "proximity_player_emote event %s fell back "
            "to its first selected speaker",
            event_id,
        )
        fallback = _generate_player_emote_single(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            player_emote,
            history,
            label='proximity_player_emote_fallback',
        )
        _mark_event(
            db, event_id,
            'completed' if fallback else 'skipped',
        )
        return fallback

    speaker_by_name = {
        speaker.get('name', ''): speaker
        for speaker in participants
    }
    _apply_speaker_action_policy(
        parsed,
        speaker_by_name,
        get_chatter_mode(config or {}),
        label='proximity_player_emote',
    )
    line_delay = max(
        0,
        int(extra.get('line_delay_seconds', 4) or 4),
    )
    inserted = 0
    cumulative_delay = 0
    for index, line in enumerate(parsed):
        speaker = speaker_by_name.get(line.get('name', ''))
        if not speaker:
            continue
        if index > 0:
            cumulative_delay += line_delay
        first_fallback = (
            names[1]
            if extra.get('interaction_mode') == 'npc_aside'
            else str(extra.get('player_name', ''))
        )
        fallback_addressee = (
            first_fallback
            if index == 0
            else parsed[index - 1].get('name', '')
        )
        _set_line_addressee(
            line,
            extra,
            participants,
            fallback_addressee,
        )
        if _insert_proximity_line(
            db,
            event_id,
            speaker,
            player_guid,
            index,
            cumulative_delay,
            line,
            allow_emote_only=True,
        ):
            inserted += 1

    if inserted == 0:
        logger.warning(
            "proximity_player_emote event %s fell back "
            "to single-line output after zero inserts",
            event_id,
        )
        fallback = _generate_player_emote_single(
            db,
            client,
            config,
            event_id,
            extra,
            participants[0],
            player_emote,
            history,
            label='proximity_player_emote_fallback',
        )
        _mark_event(
            db, event_id,
            'completed' if fallback else 'skipped',
        )
        return fallback

    _mark_event(db, event_id, 'completed')
    return True
