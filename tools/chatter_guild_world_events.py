"""Open-world guild moments produced by LLMChatterGuildWorld.cpp.

``guild_meet_greeting``      a guild bot waves (/hello) and greets a
                             guildmate it meets outside their group, and
                             may tell the guild about it afterwards.
``guild_join_zone_announce`` a bot that just joined a guild tells its
                             zone's General channel; zone bots react.
``guild_npc_encounter``      a guild bot tells the guild about a friendly
                             NPC it is standing near.

The prompts describe what happened and let each bot's personality and
tone decide how it reacts.
"""

import logging
import random
from typing import Dict, List, Optional

from chatter_db import insert_chat_message
from chatter_guild import (
    _participant_identity_lines,
    _query_speaker,
)
from chatter_guild_event_common import (
    PREFIX,
    build_prompt,
    deliver,
    generate,
    line_delays,
    max_characters,
    personality_rule,
    run_multi_prompt,
    run_single_prompt,
    safe_int,
)
from chatter_guild_player import _config_enabled, _mark_event
from chatter_guild_profile import (
    describe_character,
    get_character_guild_name,
    get_guild_profile,
    guild_identity_lines,
)
from chatter_identity import prepare_guild_speakers
from chatter_mode import build_player_chat_guidance, is_roleplay
from chatter_player_context import player_character_lines
from chatter_shared import (
    _reserve_zone_delivery_window,
    append_conversation_json_instruction,
    append_json_instruction,
    get_chatter_mode,
    get_subzone_name,
    get_zone_name,
    parse_extra_data,
)

logger = logging.getLogger(__name__)

FOLLOW_UP_DELAY = (8.0, 15.0)
FOLLOW_UP_DROP_REASON = 'meet_greeting_not_delivered'


def _participant(db, extra: Dict, prefix: str = 'bot') -> Dict:
    guid = safe_int(extra.get(f'{prefix}_guid'))
    speaker = _query_speaker(db, guid) if guid else {}
    return {
        'guid': guid,
        'name': str(extra.get(f'{prefix}_name') or ''),
        'zone_id': safe_int(extra.get('zone_id')),
        'map_id': 0,
        'speaker': speaker,
    }


def _prepared(db, client, config, participant: Dict,
              channel: str = 'guild') -> Dict:
    return prepare_guild_speakers(
        db, client, config, [participant], channel=channel,
    )[0]


def _describe(extra: Dict, prefix: str, mode: str) -> str:
    return describe_character(
        str(extra.get(f'{prefix}_name') or 'someone'),
        str(extra.get(f'{prefix}_race') or ''),
        str(extra.get(f'{prefix}_class') or ''),
        None if is_roleplay(mode) else extra.get(f'{prefix}_level'),
        str(extra.get(f'{prefix}_gender') or ''),
    )


def _place(extra: Dict) -> str:
    zone_id = safe_int(extra.get('zone_id'))
    zone = get_zone_name(zone_id) or ''
    subzone = get_subzone_name(zone_id, safe_int(extra.get('area_id'))) or ''
    if subzone and zone and subzone != zone:
        return f"{subzone} in {zone}"
    return subzone or zone


# --------------------------------------------------------------------------
# Guild NPC encounter
# --------------------------------------------------------------------------

def _npc_scenario(extra: Dict, mode: str) -> List[str]:
    bot_name = str(extra.get('bot_name') or 'The speaker')
    zone = get_zone_name(safe_int(extra.get('zone_id'))) or ''
    npc = str(extra.get('npc_name') or 'someone')
    subname = str(extra.get('npc_subname') or '').strip()
    role = str(extra.get('npc_role') or '').strip()
    what = subname or role or 'local'
    return [
        f"{bot_name} is standing near {npc} <{what}>"
        f"{' in ' + zone if zone else ''}.",
        f"{bot_name} mentions this {what.lower()} to the guild with a "
        "short opinion of them. Helpful, odd, overpriced, kind, gruff, "
        "worth a visit or not worth the trip are all possible.",
        f"Name {npc}{' and ' + zone if zone else ''} so guildmates know "
        "who and where. Do not invent quests or rewards.",
    ]


def process_guild_npc_encounter_event(db, client, config, event):
    """A guild bot tells the guild about a friendly NPC near it."""
    event_id = safe_int(event.get('id'))
    if not _config_enabled(config, PREFIX + 'NpcEncounter.Enable'):
        _mark_event(db, event_id, 'skipped')
        return False
    extra = parse_extra_data(
        event.get('extra_data'), event_id, 'guild_npc_encounter',
    )
    if not extra or not safe_int(extra.get('guild_id')):
        _mark_event(db, event_id, 'skipped')
        return False

    speaker = _participant(db, extra)
    if not speaker['guid'] or not speaker['name'] or not speaker['speaker']:
        _mark_event(db, event_id, 'skipped')
        return False
    speaker = _prepared(db, client, config, speaker)

    mode = get_chatter_mode(config)
    profile = get_guild_profile(db, extra.get('guild_id'))
    guild_context = guild_identity_lines(profile)
    maximum = max_characters(config)
    prompt, names = build_prompt(
        [speaker],
        str(extra.get('guild_name') or 'the guild'),
        str(extra.get('team') or ''),
        mode,
        guild_context,
        _npc_scenario(extra, mode),
        maximum,
    )
    metadata = {
        'guild_id': safe_int(extra.get('guild_id')),
        'guild_event': 'guild_npc_encounter',
        'guild_responders': speaker['name'],
        'guild_responder_count': 1,
        'guild_info_included': bool(guild_context),
        'guild_repair': False,
    }
    messages = generate(
        client, config, event_id, 'guild_npc_encounter', prompt, names,
        maximum, metadata,
    )
    if not messages or not deliver(
        db, config, event_id, messages, [],
        {speaker['name']: speaker['guid']},
        delivery_policy='filler',
    ):
        _mark_event(db, event_id, 'skipped')
        return False
    _mark_event(db, event_id, 'completed')
    logger.info(
        "guild_npc_encounter guild=%s speaker=%s npc=%s",
        extra.get('guild_id'), speaker['name'], extra.get('npc_name'),
    )
    return True


# --------------------------------------------------------------------------
# Meet greeting (/hello + /say) and the held Guild follow-up
# --------------------------------------------------------------------------

def build_meet_greeting_prompt(db, bot: Dict, extra: Dict, mode: str):
    player_guid = safe_int(extra.get('player_guid'))
    player_name = str(extra.get('player_name') or '')
    guild_name = str(extra.get('guild_name') or 'the guild')
    zone = get_zone_name(safe_int(extra.get('zone_id'))) or ''
    lines = (
        ["Write one natural in-character World of Warcraft /say line."]
        if is_roleplay(mode)
        else [build_player_chat_guidance(mode, 'say')]
    )
    lines.extend(_participant_identity_lines(bot, mode))
    lines.extend(player_character_lines(
        db, player_guid, player_name, mode,
        race=str(extra.get('player_race') or ''),
        class_name=str(extra.get('player_class') or ''),
        gender=str(extra.get('player_gender') or ''),
    ))
    lines.extend([
        f"{bot['name']} and {player_name} are both members of the "
        f"guild \"{guild_name}\" but are not travelling together.",
        f"{bot['name']} has just run into "
        f"{_describe(extra, 'player', mode)}"
        f"{' in ' + zone if zone else ''} by chance and waves.",
        f"React to meeting {player_name} the way {bot['name']} naturally "
        "would, given their personality and tone. A greeting, a nod, a "
        "dry remark, a question or a wish of luck all fit.",
        f"Address {player_name} by name once.",
        "Spoken text only: no narrator text, emotes or name prefix.",
        "Aim for 4 to 14 words.",
    ])
    return append_json_instruction(
        "\n".join(lines), allow_action=False, message_only=True,
    )


def _meet_guild_scenario(extra: Dict, greeting: str) -> List[str]:
    bot_name = str(extra.get('bot_name') or 'The speaker')
    player = str(extra.get('player_name') or 'a guildmate')
    place = _place(extra)
    where = f" in {place}" if place else ""
    return [
        f"{bot_name} has just run into their guildmate {player}{where} by "
        f"chance and greeted them in person: \"{greeting}\".",
        f"Now {bot_name} mentions the meeting to the guild. A remark about "
        "the place or what they might be up to there may fit.",
        f"Name {player}" + (f" and {place}" if place else "")
        + " so the guild knows who and where. Do not repeat the greeting "
        "and do not invent a long story.",
    ]


def _guild_post_wanted(config: Dict, extra: Dict) -> bool:
    if extra.get('guild_post_allowed') is False:
        return False
    chance = max(0, min(100, safe_int(config.get(
        PREFIX + 'MeetGreeting.GuildPostChance', 50,
    ), 50)))
    return bool(chance) and random.randint(1, 100) <= chance


def _meet_follow_up_text(
    db, client, config, event_id: int, extra: Dict, bot: Dict, mode: str,
    greeting: str,
) -> str:
    profile = get_guild_profile(db, extra.get('guild_id'))
    guild_context = guild_identity_lines(profile)
    maximum = max_characters(config)
    prompt, names = build_prompt(
        [bot],
        str(extra.get('guild_name') or 'the guild'),
        str(extra.get('team') or ''),
        mode,
        guild_context,
        _meet_guild_scenario(extra, greeting),
        maximum,
    )
    metadata = {
        'guild_id': safe_int(extra.get('guild_id')),
        'guild_event': 'guild_meet_post',
        'guild_responders': bot['name'],
        'guild_responder_count': 1,
        'guild_info_included': bool(guild_context),
        'guild_repair': False,
        'guild_meet_place': _place(extra),
    }
    messages = run_single_prompt(
        client, config, prompt, names[0], maximum, metadata,
        'guild_meet_post',
        f"guild_meet_post:{event_id}:{names[0]}",
        f"guild_meet_post-repair:{event_id}",
    )
    return messages[0]['message'] if messages else ''


def _greeting_state(db, greeting_id: int) -> str:
    """'pending' until delivery has finished with the greeting row, then
    'spoken' or 'dropped'."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT delivered, delivered_at, drop_reason "
        "FROM llm_chatter_messages WHERE id = %s",
        (greeting_id,),
    )
    row = cursor.fetchone()
    if not row:
        return 'dropped'
    if isinstance(row, dict):
        delivered = row.get('delivered')
        delivered_at = row.get('delivered_at')
        drop_reason = row.get('drop_reason')
    else:
        delivered, delivered_at, drop_reason = row[0], row[1], row[2]
    if not delivered or delivered_at is None:
        return 'pending'
    return 'dropped' if drop_reason else 'spoken'


def hold_follow_up(db, follow_up_id: int, greeting_id: int) -> str:
    """Hold the Guild follow-up until the greeting has been spoken.

    A held row has no deliver_at, so delivery never picks it up. C++
    releases or cancels it once the greeting row is final; when that
    already happened, it is settled here instead. Returns the greeting
    state seen.
    """
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_messages SET deliver_at = NULL "
        "WHERE id = %s AND delivered = 0",
        (follow_up_id,),
    )
    db.commit()
    state = _greeting_state(db, greeting_id)
    if state == 'spoken':
        cursor.execute(
            "UPDATE llm_chatter_messages "
            "SET deliver_at = DATE_ADD(NOW(), INTERVAL %s SECOND) "
            "WHERE id = %s AND delivered = 0 AND deliver_at IS NULL",
            (int(random.uniform(*FOLLOW_UP_DELAY)), follow_up_id),
        )
    elif state == 'dropped':
        cursor.execute(
            "UPDATE llm_chatter_messages "
            "SET delivered = 1, delivered_at = NOW(), drop_reason = %s "
            "WHERE id = %s AND delivered = 0 AND deliver_at IS NULL",
            (FOLLOW_UP_DROP_REASON, follow_up_id),
        )
    db.commit()
    return state


def _post_meet_follow_up(
    db, client, config, event_id: int, extra: Dict, bot: Dict, mode: str,
    greeting: str, greeting_id: Optional[int],
) -> bool:
    if not greeting_id or not _guild_post_wanted(config, extra):
        return False
    try:
        text = _meet_follow_up_text(
            db, client, config, event_id, extra, bot, mode, greeting,
        )
        if not text:
            return False
        follow_up_id = insert_chat_message(
            db,
            bot_guid=bot['guid'],
            bot_name=bot['name'],
            message=text,
            channel='guild',
            delay_seconds=FOLLOW_UP_DELAY[1],
            event_id=event_id,
            sequence=1,
            owner_subsystem='guild',
            delivery_policy='filler',
        )
        if not follow_up_id:
            return False
        return hold_follow_up(db, follow_up_id, greeting_id) != 'dropped'
    except Exception:
        logger.exception("guild_meet_post failed event=%s", event_id)
        return False


def process_guild_meet_greeting_event(db, client, config, event):
    """A guild bot greets a guildmate it meets in the open world."""
    event_id = safe_int(event.get('id'))
    if not _config_enabled(config, PREFIX + 'MeetGreeting.Enable'):
        _mark_event(db, event_id, 'skipped')
        return False
    extra = parse_extra_data(
        event.get('extra_data'), event_id, 'guild_meet_greeting',
    )
    player_guid = safe_int((extra or {}).get('player_guid'))
    if not extra or not player_guid:
        _mark_event(db, event_id, 'skipped')
        return False
    bot = _participant(db, extra)
    if not bot['guid'] or not bot['speaker']:
        _mark_event(db, event_id, 'skipped')
        return False
    bot = _prepared(db, client, config, bot)

    mode = get_chatter_mode(config)
    prompt = build_meet_greeting_prompt(db, bot, extra, mode)
    maximum = min(max_characters(config), 100)
    metadata = {
        'guild_id': safe_int(extra.get('guild_id')),
        'guild_event': 'guild_meet_greeting',
        'guild_responders': bot['name'],
        'guild_repair': False,
    }
    messages = run_single_prompt(
        client, config, prompt, bot['name'], maximum, metadata,
        'guild_meet_greeting',
        f"guild_meet_greeting:{event_id}:{bot['name']}",
        f"guild_meet_greeting-repair:{event_id}",
    )
    text = messages[0]['message'] if messages else ''
    if not text:
        _mark_event(db, event_id, 'skipped')
        return False
    greeting_id = insert_chat_message(
        db,
        bot_guid=bot['guid'],
        bot_name=bot['name'],
        message=text,
        channel='say',
        delay_seconds=1.0,
        event_id=event_id,
        emote='hello',
        player_guid=player_guid,
        addressee_player_guid=player_guid,
        owner_subsystem='guild',
    )
    posted = _post_meet_follow_up(
        db, client, config, event_id, extra, bot, mode, text, greeting_id,
    )
    _mark_event(db, event_id, 'completed')
    logger.info(
        "guild_meet_greeting bot=%s player=%s guild_post=%s", bot['name'],
        extra.get('player_name'), posted,
    )
    return True


# --------------------------------------------------------------------------
# Join announcement in General
# --------------------------------------------------------------------------

def _responder_count(config: Dict, available: int) -> int:
    maximum = max(0, min(3, available, safe_int(config.get(
        PREFIX + 'JoinZoneAnnounce.MaxResponders', 2,
    ), 2)))
    return random.randint(0, maximum) if maximum else 0


def _announce_lines(
    participants: List[Dict], responders: List[Dict], announcer: Dict,
    guild_name: str, zone: str, mode: str,
) -> List[str]:
    lines = (
        ["Write natural in-character World of Warcraft General chat "
         f"in {zone}."]
        if is_roleplay(mode)
        else [build_player_chat_guidance(mode, 'general')]
    )
    for participant in participants:
        lines.extend(_participant_identity_lines(participant, mode))
    lines.append(
        f"{announcer['name']} has just joined the guild \"{guild_name}\"."
    )
    for responder in responders:
        if responder['guild_name'] == guild_name:
            lines.append(f"{responder['name']} already belongs to "
                         f"\"{guild_name}\".")
        elif responder['guild_name']:
            lines.append(f"{responder['name']} belongs to another guild, "
                         f"\"{responder['guild_name']}\".")
        else:
            lines.append(f"{responder['name']} has no guild.")
    lines.extend([
        f"Message 1: {announcer['name']} tells General chat about joining "
        f"\"{guild_name}\", naming the guild.",
        personality_rule([p['name'] for p in participants]),
        "Spoken text only: no narrator text, emotes or name prefixes.",
        "Aim for 4 to 16 words per message.",
    ])
    return lines


def _single_announcement(
    client, config, lines: List[str], announcer: Dict, maximum: int,
    metadata: Dict, event_id: int,
) -> List[Dict]:
    prompt = append_json_instruction(
        "\n".join(lines), allow_action=False, message_only=True,
    )
    return run_single_prompt(
        client, config, prompt, announcer['name'], maximum, metadata,
        'guild_join_zone_announce',
        f"guild_join_zone_announce:{event_id}",
        f"guild_join_zone_announce-repair:{event_id}",
    )


def _insert_general_lines(
    db, config, event_id: int, zone_id: int, messages: List[Dict],
    guid_by_name: Dict[str, int],
) -> int:
    delays = line_delays(messages, config)
    base_delay = _reserve_zone_delivery_window(
        zone_id, config, duration_seconds=delays[-1] if delays else 0.0,
    )
    inserted = 0
    for sequence, (message, delay) in enumerate(zip(messages, delays)):
        guid = guid_by_name.get(str(message.get('name') or ''))
        text = str(message.get('message') or '')
        if not guid or not text:
            continue
        insert_chat_message(
            db,
            bot_guid=guid,
            bot_name=message['name'],
            message=text,
            channel='general',
            delay_seconds=base_delay + delay + 1.0,
            event_id=event_id,
            sequence=sequence,
        )
        inserted += 1
    return inserted


def process_guild_join_zone_announce_event(db, client, config, event):
    """A new guild member tells General about it; zone bots react."""
    event_id = safe_int(event.get('id'))
    if not _config_enabled(config, PREFIX + 'JoinZoneAnnounce.Enable'):
        _mark_event(db, event_id, 'skipped')
        return False
    extra = parse_extra_data(
        event.get('extra_data'), event_id, 'guild_join_zone_announce',
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False
    announcer = _participant(db, extra)
    if not announcer['guid'] or not announcer['speaker']:
        _mark_event(db, event_id, 'skipped')
        return False

    candidates = []
    for raw in extra.get('candidates') or []:
        guid = safe_int((raw or {}).get('guid'))
        speaker = _query_speaker(db, guid) if guid else {}
        if speaker:
            candidates.append({
                'guid': guid,
                'name': str(raw.get('name') or ''),
                'zone_id': announcer['zone_id'],
                'map_id': 0,
                'speaker': speaker,
                'guild_name': get_character_guild_name(db, guid) or '',
            })
    random.shuffle(candidates)
    responders = candidates[:_responder_count(config, len(candidates))]
    participants = prepare_guild_speakers(
        db, client, config, [announcer] + responders, channel='general',
    )
    announcer = participants[0]

    mode = get_chatter_mode(config)
    guild_name = str(extra.get('guild_name') or 'a guild')
    zone = get_zone_name(announcer['zone_id']) or 'this zone'
    lines = _announce_lines(
        participants, responders, announcer, guild_name, zone, mode,
    )
    maximum = max_characters(config)
    metadata = {
        'guild_id': safe_int(extra.get('guild_id')),
        'guild_event': 'guild_join_zone_announce',
        'guild_responders': ','.join(p['name'] for p in participants),
        'guild_responder_count': len(responders),
        'guild_repair': False,
    }
    names = [p['name'] for p in participants]
    messages: List[Dict] = []
    if responders:
        reaction_lines = list(lines)
        for index, responder in enumerate(responders, start=2):
            reaction_lines.append(
                f"Message {index}: {responder['name']} reacts from their "
                "own point of view. Congratulations, teasing, indifference "
                "or disdain for that guild are all possible."
            )
        prompt = append_conversation_json_instruction(
            "\n".join(reaction_lines), names, len(names),
            allow_action=False, message_only=True,
        )
        messages = run_multi_prompt(
            client, config, prompt, names, maximum, metadata,
            'guild_join_zone_announce',
            f"guild_join_zone_announce-multi:{event_id}",
            f"guild_join_zone_announce-json-repair:{event_id}",
            expected_first=announcer['name'],
        )
        if not messages:
            metadata['guild_announce_fallback'] = True
    if not messages:
        messages = _single_announcement(
            client, config,
            _announce_lines(
                [announcer], [], announcer, guild_name, zone, mode,
            ),
            announcer, maximum, metadata, event_id,
        )
    if not messages:
        _mark_event(db, event_id, 'skipped')
        return False

    inserted = _insert_general_lines(
        db, config, event_id, announcer['zone_id'], messages,
        {p['name']: p['guid'] for p in participants},
    )
    _mark_event(db, event_id, 'completed' if inserted else 'skipped')
    logger.info(
        "guild_join_zone_announce announcer=%s lines=%d", announcer['name'],
        inserted,
    )
    return bool(inserted)
