"""Shared prompt, generation and delivery helpers for Guild event
reactions: guild news, guild world events and guild PvP reactions.

Every event describes what happened and lets each bot's own
personality and tone decide how it reacts; the prompts never prescribe
a mood.
"""

import logging
from typing import Dict, List, Optional

from chatter_db import insert_chat_message
from chatter_guild import (
    _clean_guild_conversation,
    _guild_location_lines,
    _participant_identity_lines,
)
from chatter_guild_player import _clean_single
from chatter_llm import call_llm
from chatter_mode import build_player_chat_guidance, is_roleplay
from chatter_shared import (
    append_conversation_json_instruction,
    append_json_instruction,
    build_conversation_json_repair_prompt,
    calculate_dynamic_delay,
    parse_conversation_response,
    structured_output_enabled,
)
from chatter_text import parse_single_response

logger = logging.getLogger(__name__)

PREFIX = 'LLMChatter.GuildChatter.'

PERSONALITY_RULE_ONE = (
    "React the way {name} naturally would, given their personality "
    "and tone. Any reaction that fits them is fine, from warm to dry, "
    "curt or indifferent."
)
PERSONALITY_RULE_MANY = (
    "Each speaker reacts the way they naturally would, given their own "
    "personality and tone. Any reaction that fits them is fine, from "
    "warm to dry, curt or indifferent."
)


def safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == '':
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return default


def max_characters(
    config: Dict, key: str = 'MemberEvents.MaxCharacters',
    default: int = 120,
) -> int:
    return max(40, min(150, safe_int(
        config.get(PREFIX + key, default), default,
    )))


def trim_line(text: str, maximum: int) -> str:
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


def base_lines(
    participants: List[Dict],
    guild_name: str,
    faction: str,
    mode: str,
    guild_context: List[str],
) -> List[str]:
    if is_roleplay(mode):
        lines = ["Write natural in-character World of Warcraft Guild Chat."]
    else:
        lines = [build_player_chat_guidance(mode, 'guild')]
    lines.append(f"The guild is \"{guild_name}\".")
    lines.extend(guild_context)
    for participant in participants:
        lines.extend(_participant_identity_lines(participant, mode))
    if faction and is_roleplay(mode):
        lines.append(
            f"They fight for the {faction}. Never insult or mock "
            f"the {faction}, their own faction."
        )
    lines.extend(_guild_location_lines(participants, False, mode))
    return lines


def rule_lines(maximum: int, mode: str) -> List[str]:
    lines = [
        "Guild Chat reaches across the game world. Never imply "
        "the speakers can see, touch, or stand beside anyone.",
        "Each line is spoken text only: no narrator text, roleplay "
        "asterisks, slash commands, emotes, or name prefixes.",
        f"Hard limit: {maximum} characters per message.",
    ]
    if is_roleplay(mode):
        lines.append(
            "Stay fully in Azeroth and avoid game-mechanic terms."
        )
    return lines


def personality_rule(names: List[str]) -> str:
    if len(names) == 1:
        return PERSONALITY_RULE_ONE.format(name=names[0])
    return PERSONALITY_RULE_MANY


def build_prompt(
    participants: List[Dict],
    guild_name: str,
    faction: str,
    mode: str,
    guild_context: List[str],
    scenario: List[str],
    maximum: int,
    first_names: Optional[List[str]] = None,
):
    """Return (prompt, names) for one or several independent lines."""
    names = [participant['name'] for participant in participants]
    lines = base_lines(
        participants, guild_name, faction, mode, guild_context,
    )
    lines.append("")
    lines.extend(scenario)
    lines.append(personality_rule(names))
    lines.extend(rule_lines(maximum, mode))
    address = " and ".join(first_names or [])

    if len(participants) == 1:
        lines.extend([
            "",
            f"{names[0]} writes exactly one short Guild Chat line.",
            "Aim for roughly 3 to 14 words.",
        ])
        if address:
            lines.append(
                f"Naturally address {address} by name once."
            )
        lines.append("Output the spoken line only.")
        return (
            append_json_instruction(
                "\n".join(lines),
                allow_action=False,
                message_only=True,
            ),
            names,
        )

    lines.extend([
        "",
        "Generate one independent short line from each selected "
        "guildmate.",
        "Each speaker reacts from their own perspective. Do not "
        "create a bot-to-bot conversation.",
        "Make the lines clearly different from one another.",
        "Every selected bot speaks exactly once.",
        "Aim for roughly 3 to 14 words per message.",
        "MESSAGE SEQUENCE:",
    ])
    for index, name in enumerate(names):
        instruction = f"  Message {index + 1} ({name}): one distinct line"
        if index == 0 and address:
            instruction += f"; naturally address {address} by name once"
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


def checked_order(
    messages: List[Dict], names: List[str], expected_first: str = '',
) -> Optional[List[Dict]]:
    """Messages in delivery order, or None when the speakers are wrong.

    Every expected speaker must have exactly one line and nobody else
    may speak. When ``expected_first`` speaks later, its single line is
    moved to the front.
    """
    speakers = [str(message.get('name') or '') for message in messages]
    if (
        len(speakers) != len(names)
        or len(set(speakers)) != len(speakers)
        or set(speakers) != set(names)
    ):
        return None
    if expected_first and speakers[0] != expected_first:
        if expected_first not in speakers:
            return None
        index = speakers.index(expected_first)
        messages = (
            [messages[index]] + messages[:index] + messages[index + 1:]
        )
    return messages


def run_single_prompt(
    client,
    config: Dict,
    prompt,
    speaker_name: str,
    maximum: int,
    metadata: Dict,
    label: str,
    context: str,
    repair_context: str,
) -> List[Dict]:
    """Generate one short Guild line, with one repair attempt."""
    token_budget = max(80, safe_int(config.get(
        PREFIX + 'MaxTokens', 200,
    ), 200))

    def _parse(response) -> str:
        return trim_line(
            _clean_single(
                parse_single_response(response or '').get('message', ''),
                speaker_name,
            ),
            maximum,
        )

    text = _parse(call_llm(
        client, prompt, config,
        max_tokens_override=token_budget,
        context=context, label=label, metadata=metadata,
    ))
    if not text:
        repair_metadata = dict(metadata)
        repair_metadata['guild_repair'] = True
        text = _parse(call_llm(
            client,
            prompt
            + "\n\nYour previous output did not contain a usable "
            "message. Return exactly one short, non-empty message in "
            "the requested JSON shape.",
            config,
            max_tokens_override=token_budget,
            context=repair_context, label=label,
            metadata=repair_metadata,
        ))
    if not text:
        return []
    return [{'name': speaker_name, 'message': text}]


def run_multi_prompt(
    client,
    config: Dict,
    prompt,
    names: List[str],
    maximum: int,
    metadata: Dict,
    label: str,
    context: str,
    repair_context: str,
    expected_first: str = '',
) -> List[Dict]:
    """Generate one short Guild line per speaker, with one repair.

    The reply is accepted only when every speaker in ``names`` has
    exactly one line and nobody else speaks; ``expected_first`` (when
    set) is delivered first. Otherwise the result is empty.
    """
    base_tokens = max(100, safe_int(config.get(
        PREFIX + 'MaxTokens', 200,
    ), 200))
    token_budget = min(600, base_tokens * len(names))

    def _parse(response) -> Optional[List[Dict]]:
        messages = _clean_guild_conversation(
            parse_conversation_response(response or '', names)
        )
        ordered = checked_order(messages, names, expected_first)
        if ordered is not None and ordered is not messages:
            metadata['guild_order_repaired'] = True
        return ordered

    messages = _parse(call_llm(
        client, prompt, config,
        max_tokens_override=token_budget,
        context=context, label=label, metadata=metadata,
    ))
    if messages is None:
        repair_metadata = dict(metadata)
        repair_metadata['guild_repair'] = True
        messages = _parse(call_llm(
            client,
            build_conversation_json_repair_prompt(
                prompt, names, message_only=True,
                structured_output=structured_output_enabled(config),
            ),
            config,
            max_tokens_override=token_budget,
            context=repair_context, label=label,
            metadata=repair_metadata,
        ))
    if messages is None:
        logger.info(
            "%s rejected: speakers did not match %s (first=%s)",
            label, ",".join(names), expected_first or '-',
        )
        return []

    for message in messages:
        message['message'] = trim_line(
            message.get('message', ''), maximum,
        )
    if not all(message.get('message') for message in messages):
        return []
    return messages


def generate(
    client,
    config: Dict,
    event_id: int,
    event_type: str,
    prompt,
    names: List[str],
    maximum: int,
    metadata: Dict,
    expected_first: str = '',
) -> List[Dict]:
    if len(names) == 1:
        return run_single_prompt(
            client, config, prompt, names[0], maximum, metadata,
            event_type,
            f"{event_type}:{event_id}:{names[0]}",
            f"{event_type}-repair:{event_id}",
        )
    return run_multi_prompt(
        client, config, prompt, names, maximum, metadata,
        event_type,
        f"{event_type}-multi:{event_id}",
        f"{event_type}-json-repair:{event_id}",
        expected_first=expected_first,
    )


def line_delays(messages: List[Dict], config: Dict) -> List[float]:
    """Cumulative reading delays: the first line goes out at once."""
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


def deliver(
    db,
    config: Dict,
    event_id: int,
    messages: List[Dict],
    reply: List[Dict],
    guid_by_name: Dict[str, int],
    delivery_policy: Optional[str] = None,
    start_delay: float = 0.0,
) -> int:
    """Insert the Guild lines (and an optional answer) in order.

    ``delivery_policy='filler'`` marks lines that C++ drops while the
    guild is in a conversation with a real player.
    """
    delays = line_delays(messages, config)
    lines = list(zip(messages, delays))
    if reply:
        previous = messages[-1]['message'] if messages else ''
        lines.append((
            reply[0],
            (delays[-1] if delays else 0.0)
            + calculate_dynamic_delay(
                len(reply[0]['message']),
                config,
                prev_message_length=len(previous),
                responsive=False,
            ),
        ))

    inserted = 0
    for sequence, (message, delay) in enumerate(lines):
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
            delay_seconds=start_delay + delay,
            event_id=event_id,
            sequence=sequence,
            owner_subsystem='guild',
            delivery_policy=delivery_policy,
        )
        inserted += 1
    return inserted
