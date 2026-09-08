"""Player-driven Guild Chat replies and session memory."""

import logging
import random
from typing import Dict, List, Optional, Tuple

from chatter_db import insert_chat_message
from chatter_general import _pick_length_hint
from chatter_guild import (
    _apply_participant_references,
    _clean_guild_conversation,
    _contains_speaker_name,
    _guild_location_lines,
    _insert_reference_names,
    _participant_identity_lines,
    _query_speaker,
    _select_participant_references,
    _strip_rp_artifacts,
    _valid_guild_conversation,
)
from chatter_llm import call_llm
from chatter_mode import build_player_chat_guidance, is_roleplay
from chatter_prompts import (
    generate_conversation_length_sequence,
    generate_conversation_mood_sequence,
)
from chatter_shared import (
    append_conversation_json_instruction,
    append_json_instruction,
    build_conversation_json_repair_prompt,
    calculate_dynamic_delay,
    find_addressed_bot,
    get_chatter_mode,
    parse_conversation_response,
    parse_extra_data,
    select_conversation_message_count,
)
from chatter_text import (
    cleanup_message,
    parse_single_response,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == '':
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return default


def _bounded_percent(config: Dict, key: str, default: int) -> int:
    return max(0, min(100, _safe_int(
        config.get(key, default),
        default,
    )))


def _config_enabled(
    config: Dict,
    key: str,
    default: str = '1',
) -> bool:
    return str(config.get(key, default)).strip() == '1'


def _mark_event(db, event_id: int, status: str) -> None:
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events "
        "SET status = %s WHERE id = %s",
        (status, event_id),
    )
    db.commit()


def _session_is_current(
    db,
    session_id: int,
    player_guid: int,
    turn_id: int,
) -> bool:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT 1 FROM llm_guild_chat_sessions "
        "WHERE id = %s AND player_guid = %s "
        "AND turn_id = %s LIMIT 1",
        (session_id, player_guid, turn_id),
    )
    return cursor.fetchone() is not None


def _fetch_session_context(
    db,
    session_id: int,
    keep_recent: int,
) -> Tuple[str, List[Dict]]:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT summary "
        "FROM llm_guild_chat_sessions "
        "WHERE id = %s LIMIT 1",
        (session_id,),
    )
    session = cursor.fetchone() or {}
    summary = str(session.get('summary') or '').strip()

    cursor.execute(
        "SELECT id, speaker_name, is_bot, "
        "source_kind, message "
        "FROM llm_guild_session_history "
        "WHERE session_id = %s "
        "ORDER BY id DESC LIMIT %s",
        (session_id, max(1, keep_recent)),
    )
    recent = list(reversed(cursor.fetchall()))
    return summary, recent


def _format_session_context(
    summary: str,
    recent: List[Dict],
    mode: str = 'roleplay',
) -> str:
    blocks = []
    if summary:
        blocks.extend([
            "Compact memory from earlier in this "
            "login session:",
            summary,
        ])

    if recent:
        lines = []
        for row in recent:
            name = str(row.get('speaker_name') or 'Unknown')
            marker = (
                " (player)"
                if not row.get('is_bot')
                else ""
            )
            kind = row.get('source_kind')
            ambient = (
                " [ambient]"
                if kind == 'ambient'
                else ""
            )
            lines.append(
                f"  {name}{marker}{ambient}: "
                f"{row.get('message') or ''}"
            )
        blocks.extend([
            "Recent Guild chat actually visible "
            "during this session:",
            "\n".join(lines),
        ])
    if blocks and not is_roleplay(mode):
        blocks.append(
            "Older bot lines may use roleplay voice. Treat their events as "
            "gameplay context and reply only in normal player voice."
        )
    return "\n".join(blocks)


def _normalize_candidates(extra: Dict) -> List[Dict]:
    candidates = []
    seen = set()
    for raw in extra.get('candidates') or []:
        if not isinstance(raw, dict):
            continue
        guid = _safe_int(raw.get('guid'))
        name = str(raw.get('name') or '').strip()
        if not guid or not name or guid in seen:
            continue
        speaker = raw.get('speaker') or {}
        if not speaker:
            speaker = None
        candidates.append({
            'guid': guid,
            'name': name,
            'zone_id': _safe_int(raw.get('zone_id')),
            'map_id': _safe_int(raw.get('map_id')),
            'speaker': speaker,
        })
        seen.add(guid)
    return candidates


def _load_candidates(db, candidates: List[Dict]) -> List[Dict]:
    loaded = []
    for candidate in candidates:
        speaker = (
            candidate.get('speaker')
            or _query_speaker(db, candidate['guid'])
        )
        if not speaker:
            continue
        item = dict(candidate)
        item['speaker'] = speaker
        loaded.append(item)
    return loaded


def _recent_bot_names(recent: List[Dict]) -> List[str]:
    return [
        str(row.get('speaker_name') or '')
        for row in recent
        if row.get('is_bot')
        and row.get('speaker_name')
    ]


def _weighted_pick(
    candidates: List[Dict],
    recent_names: List[str],
    penalty: int,
) -> Optional[Dict]:
    if not candidates:
        return None

    latest_positions = {}
    for offset, name in enumerate(reversed(recent_names)):
        latest_positions.setdefault(name.casefold(), offset)

    weights = []
    for candidate in candidates:
        offset = latest_positions.get(
            candidate['name'].casefold()
        )
        if offset is None:
            weights.append(100)
            continue
        decay = max(0.25, 1.0 - (offset * 0.2))
        reduction = int(penalty * decay)
        weights.append(max(1, 100 - reduction))

    return random.choices(
        candidates,
        weights=weights,
        k=1,
    )[0]


def _select_responders(
    candidates: List[Dict],
    addressed_name: str,
    count: int,
    recent_names: List[str],
    penalty: int,
) -> List[Dict]:
    selected = []
    remaining = list(candidates)

    if addressed_name:
        addressed_key = addressed_name.casefold()
        addressed = next(
            (
                candidate
                for candidate in remaining
                if candidate['name'].casefold()
                == addressed_key
            ),
            None,
        )
        if addressed:
            selected.append(addressed)
            remaining.remove(addressed)

    while remaining and len(selected) < count:
        picked = _weighted_pick(
            remaining, recent_names, penalty
        )
        if not picked:
            break
        selected.append(picked)
        remaining.remove(picked)
    return selected


def _choose_topology(
    config: Dict,
    candidate_count: int,
    multi_addressed: bool,
) -> Tuple[str, int]:
    max_responders = max(
        1,
        min(
            3,
            _safe_int(config.get(
                'LLMChatter.GuildChatter.'
                'PlayerReplies.MaxResponders',
                3,
            ), 3),
            candidate_count,
        ),
    )
    conversation_chance = _bounded_percent(
        config,
        'LLMChatter.GuildChatter.'
        'PlayerReplies.ConversationChance',
        20,
    )
    multi_base = _bounded_percent(
        config,
        'LLMChatter.GuildChatter.'
        'PlayerReplies.MultiReplyChance',
        15,
    )
    configured_bonus = _bounded_percent(
        config,
        'LLMChatter.GuildChatter.'
        'PlayerReplies.MultiAddressedBonus',
        15,
    )
    applied_bonus = (
        configured_bonus if multi_addressed else 0
    )
    multi_chance = min(
        100,
        multi_base + applied_bonus,
    )
    if max_responders < 2:
        return 'single', 1

    conversation_roll = random.randint(1, 100)
    if conversation_roll <= conversation_chance:
        responder_count = random.randint(
            2, max_responders
        )
        return 'conversation', responder_count

    multi_roll = random.randint(1, 100)
    if multi_roll <= multi_chance:
        responder_count = random.randint(
            2, max_responders
        )
        result = 'multi_reply'
    else:
        responder_count = 1
        result = 'single'
    if result == 'multi_reply':
        return result, responder_count
    return 'single', 1


def _reply_delays(
    messages: List[Dict],
    player_message: str,
    config: Dict,
) -> List[float]:
    delay_min = max(0, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'PlayerReplies.FirstDelayMin',
        8,
    ), 8))
    delay_max = max(delay_min, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'PlayerReplies.FirstDelayMax',
        20,
    ), 20))
    cumulative = float(
        random.randint(delay_min, delay_max)
    )
    delays = []
    previous_length = len(player_message)
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
    player_message: str,
    session_context: str,
    callback_requested: bool,
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
    if session_context:
        lines.extend(["", session_context])
    lines.extend([
        "",
        f"{player_name} just said in Guild Chat:",
        f"\"{player_message}\"",
        "",
        "The latest player message is authoritative. "
        "Answer it rather than an obsolete earlier turn.",
        "Stay consistent with the session memory and "
        "with each bot's earlier opinions. A bot may "
        "change its mind only if it acknowledges why.",
        "Preserve unresolved questions and promises "
        "naturally; do not recite the memory.",
        "Do not invent facts that were not said.",
        "Guild Chat reaches across the game world. Never imply "
        "the speakers can see, touch, or stand beside "
        "one another.",
        "Each line is spoken text only: no narrator "
        "text, roleplay asterisks, slash commands, "
        "emotes, or name prefixes.",
        "Never exceed 150 characters in one message.",
    ])
    if is_roleplay(mode):
        lines.append(
            "Stay fully in Azeroth and avoid game-mechanic terms."
        )
    if callback_requested:
        lines.append(
            "If genuinely relevant, make one subtle "
            "callback to an earlier session detail. "
            "Do not force or announce the callback."
        )
    return lines


def _clean_single(text: str, speaker_name: str) -> str:
    text = strip_speaker_prefix(text, speaker_name)
    text = cleanup_message(text)
    return _strip_rp_artifacts(text)


def _build_single_prompt(
    participant: Dict,
    guild_name: str,
    faction: str,
    player_name: str,
    player_message: str,
    session_context: str,
    callback_requested: bool,
    name_requested: bool,
    question_requested: bool,
    mode: str = 'roleplay',
) -> str:
    lines = _shared_prompt_lines(
        [participant],
        guild_name,
        faction,
        player_name,
        player_message,
        session_context,
        callback_requested,
        mode,
    )
    lines.extend([
        "",
        f"{participant['name']} gives one direct, "
        "meaningful reply.",
        _pick_length_hint(mode),
    ])
    if name_requested:
        lines.append(
            f"Naturally address {player_name} by name "
            "once, not necessarily at the beginning."
        )
    if question_requested:
        lines.append(
            "End with one natural follow-up question "
            "only if the player's message supports it."
        )
    lines.extend([
        "Do not merely repeat or paraphrase what the "
        "player said.",
        "Output the spoken reply only.",
    ])
    return append_json_instruction(
        "\n".join(lines),
        allow_action=False,
        message_only=True,
    )


def _build_multi_prompt(
    participants: List[Dict],
    topology: str,
    guild_name: str,
    faction: str,
    player_name: str,
    player_message: str,
    session_context: str,
    callback_requested: bool,
    name_requested: bool,
    question_requested: bool,
    config: Dict,
) -> Tuple[str, List[Dict], int]:
    mode = get_chatter_mode(config)
    names = [
        participant['name']
        for participant in participants
    ]
    if topology == 'multi_reply':
        message_count = len(participants)
    else:
        max_lines = min(
            8,
            max(
                len(participants),
                _safe_int(config.get(
                    'LLMChatter.GuildChatter.'
                    'MaxConversationLines',
                    4,
                ), 4),
            ),
        )
        message_count = (
            select_conversation_message_count(
                len(participants),
                len(participants),
                max_lines,
            )
        )

    reference_plans = []
    if topology == 'conversation':
        reference_plans = (
            _select_participant_references(
                names,
                message_count,
                _bounded_percent(
                    config,
                    'LLMChatter.GuildChatter.'
                    'ParticipantReferenceChance',
                    25,
                ),
                _bounded_percent(
                    config,
                    'LLMChatter.GuildChatter.'
                    'MultiReferenceChance',
                    15,
                ),
                _safe_int(config.get(
                    'LLMChatter.GuildChatter.'
                    'MaxReferenceLines',
                    2,
                ), 2),
            )
        )

    lines = _shared_prompt_lines(
        participants,
        guild_name,
        faction,
        player_name,
        player_message,
        session_context,
        callback_requested,
        mode,
    )
    lines.append("")
    if topology == 'multi_reply':
        lines.extend([
            "Generate independent reactions from each "
            "selected guildmate.",
            "Each bot answers the player from its own "
            "perspective. Do not turn these lines into "
            "a bot-to-bot conversation.",
            "Every selected bot speaks exactly once.",
        ])
    else:
        lines.extend([
            "The player's message starts a coherent "
            "conversation among the selected guildmates.",
            "The first bot answers the player. Later "
            "bots may answer the player or respond to "
            "an earlier guildmate.",
            "Every selected bot must speak at least once.",
        ])

    moods = generate_conversation_mood_sequence(
        message_count, mode
    )
    lengths = generate_conversation_length_sequence(
        message_count
    )
    sequence_names = [
        names[index % len(names)]
        for index in range(message_count)
    ]
    reference_by_index = {
        plan['message_index']: plan
        for plan in reference_plans
    }
    lines.append("MESSAGE SEQUENCE:")
    for index, speaker in enumerate(sequence_names):
        instruction = (
            f"  Message {index + 1} ({speaker}): "
            f"mood={moods[index]}, "
            f"length={lengths[index]}"
        )
        plan = reference_by_index.get(index)
        if plan:
            candidates = ", ".join(plan['candidates'])
            instruction += (
                "; naturally address an earlier "
                "speaker by name while replying "
                f"(choose contextually from {candidates})"
            )
        if index == 0 and name_requested:
            instruction += (
                f"; naturally address {player_name} "
                "by name once"
            )
        if (
            index == message_count - 1
            and question_requested
        ):
            instruction += (
                "; ask one natural follow-up question "
                "if the context supports it"
            )
        lines.append(instruction)

    prompt = append_conversation_json_instruction(
        "\n".join(lines),
        sequence_names,
        message_count,
        allow_action=False,
        message_only=True,
    )
    return prompt, reference_plans, message_count


def _generate_single_reply(
    db,
    client,
    config: Dict,
    event_id: int,
    participant: Dict,
    guild_name: str,
    faction: str,
    player_name: str,
    player_message: str,
    session_context: str,
    callback_requested: bool,
    name_requested: bool,
    question_requested: bool,
    metadata: Dict,
) -> List[Dict]:
    prompt = _build_single_prompt(
        participant,
        guild_name,
        faction,
        player_name,
        player_message,
        session_context,
        callback_requested,
        name_requested,
        question_requested,
        get_chatter_mode(config),
    )
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=_safe_int(config.get(
            'LLMChatter.GuildChatter.MaxTokens',
            200,
        ), 200),
        context=(
            f"guild-player:{event_id}:"
            f"{participant['name']}"
        ),
        label='guild_player_message',
        metadata=metadata,
    )
    parsed = parse_single_response(response or '')
    text = _clean_single(
        parsed.get('message', ''),
        participant['name'],
    )
    if not text:
        repair_prompt = (
            prompt
            + "\n\nYour previous output did not contain "
            "a usable spoken message. Return exactly one "
            "non-empty message in the requested JSON shape."
        )
        repair_metadata = dict(metadata)
        repair_metadata['guild_repair'] = True
        response = call_llm(
            client,
            repair_prompt,
            config,
            max_tokens_override=_safe_int(config.get(
                'LLMChatter.GuildChatter.MaxTokens',
                200,
            ), 200),
            context=(
                f"guild-player-single-repair:"
                f"{event_id}"
            ),
            label='guild_player_message',
            metadata=repair_metadata,
        )
        parsed = parse_single_response(response or '')
        text = _clean_single(
            parsed.get('message', ''),
            participant['name'],
        )
    if not text:
        return []
    return [{
        'name': participant['name'],
        'message': text,
    }]


def _generate_multi_reply(
    db,
    client,
    config: Dict,
    event_id: int,
    participants: List[Dict],
    topology: str,
    guild_name: str,
    faction: str,
    player_name: str,
    player_message: str,
    session_context: str,
    callback_requested: bool,
    name_requested: bool,
    question_requested: bool,
    metadata: Dict,
) -> List[Dict]:
    prompt, reference_plans, message_count = (
        _build_multi_prompt(
            participants,
            topology,
            guild_name,
            faction,
            player_name,
            player_message,
            session_context,
            callback_requested,
            name_requested,
            question_requested,
            config,
        )
    )
    names = [
        participant['name']
        for participant in participants
    ]
    base_tokens = _safe_int(config.get(
        'LLMChatter.GuildChatter.MaxTokens',
        200,
    ), 200)
    token_budget = min(
        base_tokens * (1 + len(participants)),
        1000,
    )
    metadata = dict(metadata)
    metadata['guild_requested_message_count'] = (
        message_count
    )
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=token_budget,
        context=(
            f"guild-player-{topology}:{event_id}"
        ),
        label='guild_player_message',
        metadata=metadata,
    )
    messages = _clean_guild_conversation(
        parse_conversation_response(
            response or '',
            names,
        )
    )[:message_count]

    if not _valid_guild_conversation(
        messages, names
    ):
        repair_prompt = (
            build_conversation_json_repair_prompt(
                prompt,
                names,
                message_only=True,
            )
        )
        repair_metadata = dict(metadata)
        repair_metadata['guild_repair'] = True
        response = call_llm(
            client,
            repair_prompt,
            config,
            max_tokens_override=token_budget,
            context="guild-player-json-repair",
            label='guild_player_message',
            metadata=repair_metadata,
        )
        messages = _clean_guild_conversation(
            parse_conversation_response(
                response or '',
                names,
            )
        )[:message_count]

    if not _valid_guild_conversation(
        messages, names
    ):
        return []
    if reference_plans:
        _apply_participant_references(
            messages,
            reference_plans,
        )
    return messages


def _trim_summary(text: str, maximum: int) -> str:
    text = " ".join(str(text or '').split())
    if len(text) <= maximum:
        return text
    shortened = text[:maximum].rsplit(' ', 1)[0]
    return shortened.rstrip(' ,;:-') + "."


def _maybe_summarize_session(
    db,
    client,
    config: Dict,
    session_id: int,
) -> bool:
    if not _config_enabled(
        config,
        'LLMChatter.GuildChatter.'
        'SessionMemory.Enable',
    ):
        return False

    keep_recent = max(4, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'SessionMemory.KeepRecentMessages',
        15,
    ), 15))
    threshold = max(500, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryThresholdChars',
        3500,
    ), 3500))

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT summary, summarized_through_id "
        "FROM llm_guild_chat_sessions "
        "WHERE id = %s LIMIT 1",
        (session_id,),
    )
    session = cursor.fetchone()
    if not session:
        return False

    cursor.execute(
        "SELECT id "
        "FROM llm_guild_session_history "
        "WHERE session_id = %s "
        "AND delivered_at IS NOT NULL "
        "ORDER BY id DESC LIMIT %s",
        (session_id, keep_recent),
    )
    recent_ids = [
        _safe_int(row.get('id'))
        for row in cursor.fetchall()
        if _safe_int(row.get('id'))
    ]
    recent_floor = min(recent_ids) if recent_ids else 0

    cursor.execute(
        "SELECT id, speaker_name, is_bot, message "
        "FROM llm_guild_session_history "
        "WHERE session_id = %s "
        "AND source_kind IN ('player', 'reply') "
        "AND delivered_at IS NOT NULL "
        "AND id > %s "
        "ORDER BY id ASC",
        (
            session_id,
            _safe_int(
                session.get('summarized_through_id')
            ),
        ),
    )
    rows = cursor.fetchall()
    pending = [
        row for row in rows
        if _safe_int(row.get('id')) < recent_floor
    ]
    if not pending:
        return False

    pending_chars = sum(
        len(str(row.get('speaker_name') or ''))
        + len(str(row.get('message') or ''))
        + 3
        for row in pending
    )
    if pending_chars < threshold:
        return False

    max_input = max(threshold, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryMaxInputChars',
        8000,
    ), 8000))
    candidates = []
    char_count = 0
    for row in pending:
        row_chars = (
            len(str(row.get('speaker_name') or ''))
            + len(str(row.get('message') or ''))
            + 3
        )
        if (
            candidates
            and char_count + row_chars > max_input
        ):
            break
        candidates.append(row)
        char_count += row_chars

    transcript = "\n".join(
        (
            f"{row.get('speaker_name')}"
            f"{' (player)' if not row.get('is_bot') else ''}: "
            f"{row.get('message')}"
        )
        for row in candidates
    )
    previous = str(session.get('summary') or '').strip()
    max_chars = max(400, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'SessionMemory.SummaryMaxChars',
        1200,
    ), 1200))
    prompt = (
        "Update a compact factual memory of a World "
        "of Warcraft Guild Chat session.\n"
        "Preserve exact speaker names, facts explicitly "
        "stated by the player, important callbacks, "
        "unresolved questions or promises, and each "
        "speaker's established opinion or disagreement.\n"
        "Discard greetings, repetition, and filler. "
        "Never invent, infer, or embellish facts.\n"
        f"Hard limit: {max_chars} characters.\n\n"
        f"Previous compact memory:\n"
        f"{previous or '(none)'}\n\n"
        f"New older transcript to fold in:\n"
        f"{transcript}\n\n"
        "Return the rewritten compact memory."
    )
    prompt = append_json_instruction(
        prompt,
        allow_action=False,
        message_only=True,
    )
    response = call_llm(
        client,
        prompt,
        config,
        max_tokens_override=max(
            100,
            _safe_int(config.get(
                'LLMChatter.GuildChatter.'
                'SessionMemory.SummaryMaxTokens',
                300,
            ), 300),
        ),
        context=f"guild-summary:{session_id}",
        label='guild_session_summary',
        metadata={
            'guild_session_id': session_id,
            'summary_input_lines': len(candidates),
            'summary_input_chars': char_count,
            'summary_pending_chars': pending_chars,
        },
    )
    parsed = parse_single_response(response or '')
    summary = _trim_summary(
        parsed.get('message', ''),
        max_chars,
    )
    if not summary:
        return False

    cursor.execute(
        "UPDATE llm_guild_chat_sessions "
        "SET summary = %s, "
        "summarized_through_id = %s "
        "WHERE id = %s",
        (
            summary,
            candidates[-1]['id'],
            session_id,
        ),
    )
    db.commit()
    logger.info(
        "Guild session summary updated "
        "session=%s lines=%s chars=%s out=%s",
        session_id,
        len(candidates),
        char_count,
        len(summary),
    )
    return True


def process_guild_player_message_event(
    db,
    client,
    config: Dict,
    event: Dict,
) -> bool:
    """Always produce at least one reply when a live
    session, eligible bot, and functioning LLM exist.
    """
    event_id = _safe_int(event.get('id'))
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'guild_player_message',
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    session_id = _safe_int(extra.get('session_id'))
    turn_id = _safe_int(extra.get('turn_id'))
    player_guid = _safe_int(extra.get('player_guid'))
    player_name = str(
        extra.get('player_name') or 'the player'
    )
    player_message = str(
        extra.get('player_message') or ''
    ).strip()
    if (
        not session_id
        or not turn_id
        or not player_guid
        or not player_message
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

    keep_recent = max(4, _safe_int(config.get(
        'LLMChatter.GuildChatter.'
        'SessionMemory.KeepRecentMessages',
        15,
    ), 15))
    summary, recent = _fetch_session_context(
        db, session_id, keep_recent
    )
    memory_enabled = _config_enabled(
        config,
        'LLMChatter.GuildChatter.'
        'SessionMemory.Enable',
    )
    session_context = (
        _format_session_context(
            summary, recent, get_chatter_mode(config)
        )
        if memory_enabled
        else ""
    )
    names = [
        candidate['name']
        for candidate in candidates
    ]
    addressed = find_addressed_bot(
        player_message,
        names,
        client=client,
        config=config,
        chat_history=(
            session_context if memory_enabled else ""
        ),
    )
    topology, responder_count = _choose_topology(
        config,
        len(candidates),
        bool(addressed.get('multi_addressed')),
    )
    responders = _select_responders(
        candidates,
        str(addressed.get('bot') or ''),
        responder_count,
        _recent_bot_names(recent),
        _bounded_percent(
            config,
            'LLMChatter.GuildChatter.'
            'PlayerReplies.RecentSpeakerPenalty',
            60,
        ),
    )
    if not responders:
        _mark_event(db, event_id, 'skipped')
        return False

    callback_requested = (
        memory_enabled
        and bool(summary or len(recent) > 2)
        and random.randint(1, 100)
        <= _bounded_percent(
            config,
            'LLMChatter.GuildChatter.'
            'PlayerReplies.CallbackChance',
            25,
        )
    )
    name_requested = (
        random.randint(1, 100)
        <= _bounded_percent(
            config,
            'LLMChatter.GuildChatter.'
            'PlayerReplies.PlayerNameChance',
            35,
        )
    )
    question_requested = (
        random.randint(1, 100)
        <= _bounded_percent(
            config,
            'LLMChatter.GuildChatter.'
            'PlayerReplies.FollowupQuestionChance',
            20,
        )
    )

    metadata = {
        'guild_id': _safe_int(extra.get('guild_id')),
        'guild_session_id': session_id,
        'guild_turn_id': turn_id,
        'guild_player_name': player_name,
        'guild_reply_topology': topology,
        'guild_responder_count': len(responders),
        'guild_responders': ','.join(
            responder['name']
            for responder in responders
        ),
        'guild_addressed_bot': (
            addressed.get('bot') or ''
        ),
        'guild_callback_requested': callback_requested,
        'guild_player_name_requested': name_requested,
        'guild_question_requested': question_requested,
        'guild_summary_chars': len(summary),
        'guild_recent_context_lines': len(recent),
        'guild_repair': False,
    }
    guild_name = str(
        extra.get('guild_name') or 'the guild'
    )
    faction = str(extra.get('team') or '')

    if topology == 'single':
        messages = _generate_single_reply(
            db,
            client,
            config,
            event_id,
            responders[0],
            guild_name,
            faction,
            player_name,
            player_message,
            session_context,
            callback_requested,
            name_requested,
            question_requested,
            metadata,
        )
    else:
        messages = _generate_multi_reply(
            db,
            client,
            config,
            event_id,
            responders,
            topology,
            guild_name,
            faction,
            player_name,
            player_message,
            session_context,
            callback_requested,
            name_requested,
            question_requested,
            metadata,
        )

    if not messages and len(responders) > 0:
        topology = 'single_fallback'
        metadata['guild_reply_topology'] = topology
        messages = _generate_single_reply(
            db,
            client,
            config,
            event_id,
            responders[0],
            guild_name,
            faction,
            player_name,
            player_message,
            session_context,
            callback_requested,
            name_requested,
            question_requested,
            metadata,
        )

    if (
        messages
        and name_requested
        and not _contains_speaker_name(
            messages[0].get('message', ''),
            player_name,
        )
    ):
        messages[0]['message'] = (
            _insert_reference_names(
                messages[0].get('message', ''),
                [player_name],
            )
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
    reply_delays = _reply_delays(
        messages,
        player_message,
        config,
    )
    inserted = 0
    for sequence, message in enumerate(messages):
        name = message.get('name') or ''
        text = message.get('message') or ''
        guid = guid_by_name.get(name)
        if not guid or not text:
            continue
        cumulative_delay = reply_delays[sequence]
        insert_chat_message(
            db,
            bot_guid=guid,
            bot_name=name,
            message=text,
            channel='guild',
            delay_seconds=cumulative_delay,
            event_id=event_id,
            sequence=sequence,
            player_guid=player_guid,
            owner_subsystem='guild',
        )
        inserted += 1

    if not inserted:
        _mark_event(db, event_id, 'skipped')
        return False

    _mark_event(db, event_id, 'completed')
    try:
        _maybe_summarize_session(
            db, client, config, session_id
        )
    except Exception:
        logger.error(
            "Guild session summarization failed "
            "session=%s",
            session_id,
            exc_info=True,
        )

    logger.info(
        "guild_player_message player=%s topology=%s "
        "responders=%s messages=%s session=%s turn=%s "
        "callback=%s addressed=%s",
        player_name,
        topology,
        ",".join(guid_by_name),
        inserted,
        session_id,
        turn_id,
        callback_requested,
        addressed.get('bot') or 'none',
    )
    return True
