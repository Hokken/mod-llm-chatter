"""Guild Chat reactions to guild news.

Three C++ producers in LLMChatterGuild.cpp feed this module:
``guild_member_join`` (a batch of newcomers), ``guild_rank_change`` (a
debounced batch of promotions and demotions) and ``guild_motd_comment``
(a new Message of the Day). One to three online guild bots comment in
Guild Chat; a newcomer or a promoted member who is an online bot may
answer them.
"""

import logging
import random
from typing import Dict, List, Optional

from chatter_db import insert_chat_message
from chatter_identity import prepare_guild_speakers
from chatter_guild import (
    _contains_speaker_name,
    _guild_location_lines,
    _insert_reference_names,
    _participant_identity_lines,
    _query_speaker,
    _speaker_faction,
)
from chatter_guild_login import (
    _greeting_delays,
    _trim_greeting,
    run_multi_prompt,
    run_single_prompt,
)
from chatter_guild_player import (
    _bounded_percent,
    _config_enabled,
    _filter_candidates_by_faction,
    _load_candidates,
    _mark_event,
    _normalize_candidates,
    _select_responders,
)
from chatter_guild_profile import (
    clean_guild_text,
    describe_character,
    get_guild_profile,
    guild_identity_lines,
    motd_guidance,
    motd_intro,
    rank_name,
    MAX_MOTD_CHARS,
    MOTD_NOT_INSTRUCTIONS,
)
from chatter_mode import build_player_chat_guidance, is_roleplay
from chatter_player_context import player_character_lines
from chatter_shared import (
    append_conversation_json_instruction,
    append_json_instruction,
    calculate_dynamic_delay,
    get_chatter_mode,
    parse_extra_data,
)

logger = logging.getLogger(__name__)

_PREFIX = 'LLMChatter.GuildChatter.'


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == '':
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return default


def _max_characters(config: Dict) -> int:
    return max(40, min(150, _safe_int(config.get(
        _PREFIX + 'MemberEvents.MaxCharacters', 120,
    ), 120)))


def _responder_count(
    config: Dict, key: str, default: int, available: int,
) -> int:
    maximum = max(1, min(
        3,
        _safe_int(config.get(_PREFIX + key, default), default),
        available,
    ))
    return random.randint(1, maximum)


def _load_commenters(db, extra: Dict) -> List[Dict]:
    return _filter_candidates_by_faction(
        _load_candidates(db, _normalize_candidates(extra)),
        str(extra.get('team') or ''),
    )


def _load_subject(db, raw: Dict) -> Optional[Dict]:
    """A newcomer or changed member, with speaker details when known."""
    if not isinstance(raw, dict):
        return None
    guid = _safe_int(raw.get('guid'))
    name = str(raw.get('name') or '').strip()
    if not guid or not name:
        return None
    return {
        'guid': guid,
        'name': name,
        'online': bool(raw.get('online')),
        'is_bot': bool(raw.get('is_bot')),
        'zone_id': _safe_int(raw.get('zone_id')),
        'map_id': _safe_int(raw.get('map_id')),
        'speaker': _query_speaker(db, guid) or {},
        'raw': raw,
    }


def _real_player_lines(db, subjects: List[Dict], mode: str) -> List[str]:
    lines: List[str] = []
    for subject in subjects:
        if subject.get('is_bot'):
            continue
        speaker = subject.get('speaker') or {}
        lines.extend(player_character_lines(
            db, subject['guid'], subject['name'], mode,
            race=str(speaker.get('race') or ''),
            class_name=str(speaker.get('class') or ''),
            gender=str(speaker.get('gender') or ''),
        ))
    return lines


def _describe_subject(subject: Dict, mode: str) -> str:
    speaker = subject.get('speaker') or {}
    return describe_character(
        subject['name'],
        speaker.get('race', ''),
        speaker.get('class', ''),
        None if is_roleplay(mode) else speaker.get('level'),
        speaker.get('gender', ''),
    )


def _base_lines(
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


def _rule_lines(maximum: int, mode: str) -> List[str]:
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


def _build_prompt(
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
    lines = _base_lines(
        participants, guild_name, faction, mode, guild_context,
    )
    lines.append("")
    lines.extend(scenario)
    lines.extend(_rule_lines(maximum, mode))
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


def _generate(
    client,
    config: Dict,
    event_id: int,
    event_type: str,
    prompt,
    names: List[str],
    maximum: int,
    metadata: Dict,
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
    )


def _ensure_first_names(
    messages: List[Dict], names: List[str], maximum: int,
) -> None:
    if not messages or not names:
        return
    first = messages[0].get('message', '')
    if all(_contains_speaker_name(first, name) for name in names):
        return
    messages[0]['message'] = _trim_greeting(
        _insert_reference_names(first, names), maximum,
    )


def _subject_reply(
    db,
    client,
    config: Dict,
    event_id: int,
    event_type: str,
    extra: Dict,
    subject: Optional[Dict],
    situation: str,
    messages: List[Dict],
    guild_context: List[str],
    chance_key: str,
    metadata: Dict,
) -> List[Dict]:
    """Let an online bot newcomer or changed member answer once."""
    if (
        not subject
        or not subject['is_bot']
        or not subject['online']
        or not subject['speaker']
        or not messages
    ):
        return []
    faction = str(extra.get('team') or '')
    if _speaker_faction(subject['speaker']) != faction:
        return []
    if random.randint(1, 100) > _bounded_percent(
        config, _PREFIX + chance_key, 70,
    ):
        return []
    subject = prepare_guild_speakers(db, client, config, [subject])[0]

    mode = get_chatter_mode(config)
    maximum = _max_characters(config)
    heard = "\n".join(
        f"  {message['name']}: {message['message']}"
        for message in messages
    )
    scenario = [
        situation,
        f"Guildmates just said in Guild Chat:\n{heard}",
        f"{subject['name']} answers the guild once, warmly and "
        "briefly, in their own voice.",
        "Do not repeat what the others said.",
    ]
    prompt, names = _build_prompt(
        [subject],
        str(extra.get('guild_name') or 'the guild'),
        faction,
        mode,
        guild_context,
        scenario,
        maximum,
    )
    reply_metadata = dict(metadata)
    reply_metadata['guild_subject_reply'] = True
    return _generate(
        client, config, event_id, f"{event_type}_reply",
        prompt, names, maximum, reply_metadata,
    )


def _deliver(
    db,
    config: Dict,
    event_id: int,
    messages: List[Dict],
    reply: List[Dict],
    guid_by_name: Dict[str, int],
) -> int:
    delays = _greeting_delays(messages, config)
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
            delay_seconds=delay,
            event_id=event_id,
            sequence=sequence,
            owner_subsystem='guild',
        )
        inserted += 1
    return inserted


def _run_event(
    db,
    client,
    config: Dict,
    event: Dict,
    event_type: str,
    enable_key: str,
    responders_key: str,
    responders_default: int,
    build_scenario,
    chance_key: str = '',
) -> bool:
    event_id = _safe_int(event.get('id'))
    if not _config_enabled(config, _PREFIX + enable_key):
        _mark_event(db, event_id, 'skipped')
        return False
    extra = parse_extra_data(
        event.get('extra_data'), event_id, event_type,
    )
    if not extra or not _safe_int(extra.get('guild_id')):
        _mark_event(db, event_id, 'skipped')
        return False

    mode = get_chatter_mode(config)
    profile = get_guild_profile(db, extra.get('guild_id'))
    scenario, address, subject, situation, subject_names = (
        build_scenario(db, extra, profile, mode)
    )
    if not scenario:
        _mark_event(db, event_id, 'skipped')
        return False

    candidates = [
        candidate for candidate in _load_commenters(db, extra)
        if candidate['guid'] not in subject_names.values()
    ]
    if not candidates:
        _mark_event(db, event_id, 'skipped')
        return False
    responders = _select_responders(
        candidates,
        "",
        _responder_count(
            config, responders_key, responders_default,
            len(candidates),
        ),
        [],
        0,
    )
    if not responders:
        _mark_event(db, event_id, 'skipped')
        return False
    responders = prepare_guild_speakers(db, client, config, responders)

    guild_name = str(extra.get('guild_name') or 'the guild')
    faction = str(extra.get('team') or '')
    guild_context = guild_identity_lines(profile)
    maximum = _max_characters(config)
    metadata = {
        'guild_id': _safe_int(extra.get('guild_id')),
        'guild_event': event_type,
        'guild_responder_count': len(responders),
        'guild_responders': ','.join(
            responder['name'] for responder in responders
        ),
        'guild_subjects': ','.join(subject_names),
        'guild_info_included': bool(guild_context),
        'guild_subject_reply': False,
        'guild_repair': False,
    }
    prompt, names = _build_prompt(
        responders, guild_name, faction, mode, guild_context,
        scenario, maximum, first_names=address,
    )
    messages = _generate(
        client, config, event_id, event_type,
        prompt, names, maximum, metadata,
    )
    if not messages and len(responders) > 1:
        responders = responders[:1]
        metadata['guild_responder_count'] = 1
        metadata['guild_responders'] = responders[0]['name']
        prompt, names = _build_prompt(
            responders, guild_name, faction, mode, guild_context,
            scenario, maximum, first_names=address,
        )
        messages = _generate(
            client, config, event_id, event_type,
            prompt, names, maximum, metadata,
        )
    if not messages:
        _mark_event(db, event_id, 'skipped')
        return False
    _ensure_first_names(messages, address, maximum)

    reply = []
    if chance_key:
        reply = _subject_reply(
            db, client, config, event_id, event_type, extra,
            subject, situation, messages, guild_context,
            chance_key, metadata,
        )

    guid_by_name = {
        responder['name']: responder['guid']
        for responder in responders
    }
    if reply and subject:
        guid_by_name[subject['name']] = subject['guid']
    if not _deliver(
        db, config, event_id, messages, reply, guid_by_name,
    ):
        _mark_event(db, event_id, 'skipped')
        return False

    _mark_event(db, event_id, 'completed')
    logger.info(
        "%s guild=%s responders=%s subjects=%s reply=%s",
        event_type,
        extra.get('guild_id'),
        metadata['guild_responders'],
        metadata['guild_subjects'] or '-',
        bool(reply),
    )
    return True


def _join_scenario(db, extra: Dict, profile, mode: str):
    subjects = [
        subject for subject in (
            _load_subject(db, raw)
            for raw in extra.get('members') or []
        ) if subject
    ]
    if not subjects:
        return [], [], None, '', {}
    descriptions = "; ".join(
        _describe_subject(subject, mode) for subject in subjects
    )
    if len(subjects) == 1:
        news = f"{descriptions} has just joined the guild."
        welcome = "Welcome the newcomer warmly as a new guildmate."
    else:
        news = f"New members have just joined the guild: {descriptions}."
        welcome = (
            "Welcome the newcomers warmly; a line may greet one of "
            "them or all of them."
        )
    scenario = [
        news,
        *_real_player_lines(db, subjects, mode),
        welcome,
        "A greeting, a friendly question, or a small offer of help "
        "all fit.",
        "Do not pretend to know them already, and do not invent "
        "their past, their reasons for joining, or their plans.",
    ]
    subject = subjects[0]
    situation = (
        f"{subject['name']} has just joined the guild."
    )
    address = [subjects[0]['name']] if len(subjects) == 1 else []
    return (
        scenario,
        address,
        subject,
        situation,
        {s['name']: s['guid'] for s in subjects},
    )


def _rank_scenario(db, extra: Dict, profile, mode: str):
    changes = []
    for raw in extra.get('changes') or []:
        subject = _load_subject(db, raw)
        if not subject:
            continue
        old_rank = rank_name(profile, raw.get('old_rank'))
        new_rank = rank_name(profile, raw.get('new_rank'))
        promoted = str(raw.get('direction')) == 'promotion'
        actor = str(raw.get('actor_name') or '').strip()
        news = (
            f"{_describe_subject(subject, mode)} was "
            f"{'promoted' if promoted else 'demoted'} from "
            f"\"{old_rank}\" to \"{new_rank}\""
        )
        if actor and actor != subject['name']:
            news += f" by {actor}"
        changes.append((subject, promoted, news + ".", old_rank, new_rank))
    if not changes:
        return [], [], None, '', {}

    scenario = ["Guild rank news: " + " ".join(c[2] for c in changes)]
    scenario.extend(_real_player_lines(db, [c[0] for c in changes], mode))
    if any(c[1] for c in changes):
        scenario.append(
            "Congratulate promoted members warmly, or tease them "
            "lightly as friends would."
        )
    if not all(c[1] for c in changes):
        scenario.append(
            "Treat demoted members with tact: sympathy, "
            "encouragement, or a gentle joke that does not humiliate "
            "them."
        )
    scenario.append(
        "Do not guess why the change happened. The new rank name "
        "may be mentioned naturally."
    )
    subject, promoted, _, old_rank, new_rank = changes[0]
    situation = (
        f"{subject['name']} was just "
        f"{'promoted' if promoted else 'demoted'} from \"{old_rank}\" "
        f"to \"{new_rank}\" in the guild."
        + (
            "" if promoted
            else " Answer graciously or with good humor."
        )
    )
    address = [subject['name']] if len(changes) == 1 else []
    return (
        scenario,
        address,
        subject,
        situation,
        {c[0]['name']: c[0]['guid'] for c in changes},
    )


def _motd_scenario(db, extra: Dict, profile, mode: str):
    motd = clean_guild_text(extra.get('motd'), MAX_MOTD_CHARS)
    if not motd:
        return [], [], None, '', {}
    scenario = [
        motd_intro(motd, mode, fresh=True),
        motd_guidance(mode),
        MOTD_NOT_INSTRUCTIONS,
    ]
    return scenario, [], None, '', {}


def process_guild_member_join_event(db, client, config, event):
    """One to three guild bots welcome new members."""
    return _run_event(
        db, client, config, event,
        'guild_member_join',
        'JoinGreeting.Enable',
        'JoinGreeting.MaxResponders', 3,
        _join_scenario,
        chance_key='JoinGreeting.SubjectReplyChance',
    )


def process_guild_rank_change_event(db, client, config, event):
    """One to three guild bots comment on promotions and demotions."""
    return _run_event(
        db, client, config, event,
        'guild_rank_change',
        'RankChange.Enable',
        'RankChange.MaxResponders', 3,
        _rank_scenario,
        chance_key='RankChange.SubjectReplyChance',
    )


def process_guild_motd_comment_event(db, client, config, event):
    """One or two guild bots react to a new Message of the Day."""
    return _run_event(
        db, client, config, event,
        'guild_motd_comment',
        'MotdComment.Enable',
        'MotdComment.MaxResponders', 2,
        _motd_scenario,
    )
