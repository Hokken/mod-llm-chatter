"""Open-world guild moments produced by LLMChatterGuildWorld.cpp.

``guild_meet_greeting``      a guild bot waves (/hello) and greets a
                             guildmate it meets outside their group.
``guild_join_zone_announce`` a bot that just joined a guild boasts in
                             General; zone bots congratulate or scoff.
``guild_pvp_kill``           a lone guild bot tells the guild about an
                             enemy it killed ("I killed").
``bot_group_pvp_kill``       a bot in the player's group reacts in party
                             chat to an enemy the group killed ("we
                             killed"); never gated by guild membership.
``guild_npc_encounter``      a guild bot tells the guild about a friendly
                             NPC it just met.
``guild_pvp_death``          a guild bot killed by an enemy bot complains
                             in Guild chat.
``zone_pvp_death``           a bot killed by an enemy bot complains in its
                             zone's General chat.
"""

import logging
import random
from typing import Dict, List

from chatter_db import insert_chat_message
from chatter_group_prompts import _pick_length_hint
from chatter_guild import (
    _participant_identity_lines,
    _query_speaker,
)
from chatter_guild_events import (
    _build_prompt,
    _deliver,
    _generate,
    _max_characters,
    _safe_int,
)
from chatter_guild_login import (
    _greeting_delays,
    run_multi_prompt,
    run_single_prompt,
)
from chatter_guild_player import _config_enabled, _mark_event
from chatter_guild_profile import (
    describe_character,
    get_character_guild_name,
    get_guild_profile,
    guild_identity_lines,
)
from chatter_handler_pipeline import run_group_handler
from chatter_mode import (
    build_player_chat_guidance,
    build_player_prompt_header_from_dict,
    is_roleplay,
)
from chatter_prompts import pick_random_tone
from chatter_shared import (
    append_conversation_json_instruction,
    append_json_instruction,
    build_race_class_context,
    get_chatter_mode,
    get_zone_name,
    parse_extra_data,
)

logger = logging.getLogger(__name__)

_PREFIX = 'LLMChatter.GuildChatter.'


def _participant(db, extra: Dict, prefix: str = 'bot') -> Dict:
    guid = _safe_int(extra.get(f'{prefix}_guid'))
    speaker = _query_speaker(db, guid) if guid else {}
    return {
        'guid': guid,
        'name': str(extra.get(f'{prefix}_name') or ''),
        'zone_id': _safe_int(extra.get('zone_id')),
        'map_id': 0,
        'speaker': speaker,
    }


def _describe(extra: Dict, prefix: str, mode: str) -> str:
    return describe_character(
        str(extra.get(f'{prefix}_name') or 'someone'),
        str(extra.get(f'{prefix}_race') or ''),
        str(extra.get(f'{prefix}_class') or ''),
        None if is_roleplay(mode) else extra.get(f'{prefix}_level'),
        str(extra.get(f'{prefix}_gender') or ''),
    )


def _strength_note(own_level, victim_level) -> str:
    diff = _safe_int(own_level) - _safe_int(victim_level)
    if diff >= 5:
        return "The enemy was far less seasoned than the killer."
    if diff <= -5:
        return "The enemy was far more seasoned than the killer."
    return "It was a fairly even fight."


def _single_guild_line(
    db, client, config, event, event_type: str, enable_key: str,
    scenario_fn,
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

    speaker = _participant(db, extra)
    if not speaker['guid'] or not speaker['name'] or not speaker['speaker']:
        _mark_event(db, event_id, 'skipped')
        return False

    mode = get_chatter_mode(config)
    profile = get_guild_profile(db, extra.get('guild_id'))
    guild_context = guild_identity_lines(profile)
    maximum = _max_characters(config)
    prompt, names = _build_prompt(
        [speaker],
        str(extra.get('guild_name') or 'the guild'),
        str(extra.get('team') or ''),
        mode,
        guild_context,
        scenario_fn(extra, mode),
        maximum,
    )
    metadata = {
        'guild_id': _safe_int(extra.get('guild_id')),
        'guild_event': event_type,
        'guild_responders': speaker['name'],
        'guild_responder_count': 1,
        'guild_info_included': bool(guild_context),
        'guild_repair': False,
    }
    messages = _generate(
        client, config, event_id, event_type, prompt, names, maximum,
        metadata,
    )
    if not messages or not _deliver(
        db, config, event_id, messages, [],
        {speaker['name']: speaker['guid']},
    ):
        _mark_event(db, event_id, 'skipped')
        return False
    _mark_event(db, event_id, 'completed')
    logger.info(
        "%s guild=%s speaker=%s", event_type,
        extra.get('guild_id'), speaker['name'],
    )
    return True


# --------------------------------------------------------------------------
# Guild PvP kill ("I killed")
# --------------------------------------------------------------------------

def _pvp_kill_scenario(extra: Dict, mode: str) -> List[str]:
    zone = get_zone_name(_safe_int(extra.get('zone_id'))) or ''
    victim = _describe(extra, 'victim', mode)
    return [
        f"{extra.get('bot_name')} has just killed an enemy of the "
        f"opposing faction{' in ' + zone if zone else ''}: {victim}.",
        _strength_note(extra.get('bot_level'), extra.get('victim_level')),
        f"{extra.get('bot_name')} tells the guild about it in the first "
        "person (\"I\"): a taunt at the fallen foe, contempt for the "
        "enemy, grim satisfaction or a brag all fit.",
        "Use the victim's race, class or name if it sharpens the line. "
        "Do not invent a long story.",
    ]


def process_guild_pvp_kill_event(db, client, config, event):
    """A lone guild bot tells the guild about an enemy it killed."""
    return _single_guild_line(
        db, client, config, event, 'guild_pvp_kill',
        'PvpKill.Enable', _pvp_kill_scenario,
    )


# --------------------------------------------------------------------------
# PvP death complaint (Guild chat or zone General chat)
# --------------------------------------------------------------------------

def _death_strength_note(name, own_level, killer_level) -> str:
    diff = _safe_int(own_level) - _safe_int(killer_level)
    if diff >= 5:
        return (f"The killer was far less seasoned than {name}, which "
                "makes the defeat all the more humiliating.")
    if diff <= -5:
        return f"The killer was far more seasoned than {name}."
    return "It was a fairly even fight."


def _pvp_death_scenario(extra: Dict, mode: str, audience: str) -> List[str]:
    name = str(extra.get('bot_name') or 'The speaker')
    killer_name = str(extra.get('killer_name') or 'the killer')
    zone = get_zone_name(_safe_int(extra.get('zone_id'))) or ''
    lines = [
        f"{name} has just been killed{' in ' + zone if zone else ''} by "
        f"an enemy of the opposing faction: "
        f"{_describe(extra, 'killer', mode)}.",
        _death_strength_note(name, extra.get('bot_level'),
                             extra.get('killer_level')),
        f"{name} tells {audience} about it in the first person, full of "
        f"contempt, resentment or anger toward {killer_name}: a curse, a "
        "vow of revenge, or bitter scorn for the killer or their people "
        "all fit.",
        f"Name {killer_name} or use their race or class so it is clear "
        "who did it. Do not invent a long story.",
    ]
    if is_roleplay(mode):
        lines.append(
            "Speak as someone who lives in Azeroth and was just struck "
            "down, not as a player: never mention respawning, corpse runs, "
            "spirit healers, ganking, levels or other game terms."
        )
    else:
        lines.append(
            "It may sound like a player grumbling about being killed by "
            "another player."
        )
    return lines


def process_guild_pvp_death_event(db, client, config, event):
    """A guild bot killed by an enemy bot complains in Guild chat."""
    return _single_guild_line(
        db, client, config, event, 'guild_pvp_death',
        'PvpDeath.Enable',
        lambda extra, mode: _pvp_death_scenario(extra, mode, 'the guild'),
    )


def build_zone_pvp_death_prompt(bot: Dict, extra: Dict, mode: str) -> str:
    zone = get_zone_name(bot['zone_id']) or 'this zone'
    lines = (
        ["Write one natural in-character World of Warcraft General chat "
         f"line in {zone}."]
        if is_roleplay(mode)
        else [build_player_chat_guidance(mode, 'general')]
    )
    lines.extend(_participant_identity_lines(bot, mode))
    team = str(extra.get('team') or '')
    if team and is_roleplay(mode):
        lines.append(f"They fight for the {team}. Never insult or mock "
                     f"the {team}, their own faction.")
    lines.extend(_pvp_death_scenario(
        extra, mode, f"everyone in {zone} on General chat"))
    lines.extend([
        f"{bot['name']} may also warn others that "
        f"{extra.get('killer_name') or 'the killer'} could still be "
        "around.",
        "Spoken text only: no narrator text, emotes or name prefix.",
        "Aim for 4 to 16 words.",
    ])
    return append_json_instruction(
        "\n".join(lines), allow_action=False, message_only=True,
    )


def process_zone_pvp_death_event(db, client, config, event):
    """A bot killed by an enemy bot complains in its zone's General chat."""
    event_id = _safe_int(event.get('id'))
    if not _config_enabled(config, 'LLMChatter.GeneralChat.PvpDeath.Enable'):
        _mark_event(db, event_id, 'skipped')
        return False
    extra = parse_extra_data(
        event.get('extra_data'), event_id, 'zone_pvp_death',
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False
    bot = _participant(db, extra)
    if not bot['guid'] or not bot['name'] or not bot['speaker']:
        _mark_event(db, event_id, 'skipped')
        return False

    mode = get_chatter_mode(config)
    prompt = build_zone_pvp_death_prompt(bot, extra, mode)
    metadata = {
        'pvp_death_channel': 'general',
        'killer_name': str(extra.get('killer_name') or ''),
        'zone_id': bot['zone_id'],
    }
    messages = run_single_prompt(
        client, config, prompt, bot['name'], _max_characters(config),
        metadata, 'zone_pvp_death',
        f"zone_pvp_death:{event_id}:{bot['name']}",
        f"zone_pvp_death-repair:{event_id}",
    )
    text = messages[0]['message'] if messages else ''
    if not text:
        _mark_event(db, event_id, 'skipped')
        return False
    insert_chat_message(
        db,
        bot_guid=bot['guid'],
        bot_name=bot['name'],
        message=text,
        channel='general',
        delay_seconds=2.0,
        event_id=event_id,
    )
    _mark_event(db, event_id, 'completed')
    logger.info(
        "zone_pvp_death bot=%s killer=%s zone=%s", bot['name'],
        extra.get('killer_name'), bot['zone_id'],
    )
    return True


# --------------------------------------------------------------------------
# Guild NPC encounter
# --------------------------------------------------------------------------

def _npc_scenario(extra: Dict, mode: str) -> List[str]:
    zone = get_zone_name(_safe_int(extra.get('zone_id'))) or ''
    npc = str(extra.get('npc_name') or 'someone')
    subname = str(extra.get('npc_subname') or '').strip()
    role = str(extra.get('npc_role') or '').strip()
    what = subname or role or 'local'
    return [
        f"{extra.get('bot_name')} has just met {npc} <{what}>"
        f"{' in ' + zone if zone else ''}, a friendly face they had "
        "not met before.",
        f"{extra.get('bot_name')} tells the guild about this "
        f"{what.lower()} and shares a short opinion of them: helpful, "
        "odd, overpriced, kind, gruff, worth a visit, or anything that "
        "fits.",
        f"Name {npc}{' and ' + zone if zone else ''} so guildmates know "
        "who and where. Do not invent quests or rewards.",
    ]


def process_guild_npc_encounter_event(db, client, config, event):
    """A guild bot tells the guild about a friendly NPC near it."""
    return _single_guild_line(
        db, client, config, event, 'guild_npc_encounter',
        'NpcEncounter.Enable', _npc_scenario,
    )


# --------------------------------------------------------------------------
# Meet greeting (/hello + /say)
# --------------------------------------------------------------------------

def process_guild_meet_greeting_event(db, client, config, event):
    """A guild bot greets a guildmate it meets in the open world."""
    event_id = _safe_int(event.get('id'))
    if not _config_enabled(config, _PREFIX + 'MeetGreeting.Enable'):
        _mark_event(db, event_id, 'skipped')
        return False
    extra = parse_extra_data(
        event.get('extra_data'), event_id, 'guild_meet_greeting',
    )
    player_guid = _safe_int((extra or {}).get('player_guid'))
    if not extra or not player_guid:
        _mark_event(db, event_id, 'skipped')
        return False
    bot = _participant(db, extra)
    if not bot['guid'] or not bot['speaker']:
        _mark_event(db, event_id, 'skipped')
        return False

    mode = get_chatter_mode(config)
    player_name = str(extra.get('player_name') or '')
    guild_name = str(extra.get('guild_name') or 'the guild')
    zone = get_zone_name(_safe_int(extra.get('zone_id'))) or ''
    lines = (
        ["Write one natural in-character World of Warcraft /say line."]
        if is_roleplay(mode)
        else [build_player_chat_guidance(mode, 'say')]
    )
    lines.extend(_participant_identity_lines(bot, mode))
    lines.extend([
        f"{bot['name']} and {player_name} are both members of the "
        f"guild \"{guild_name}\" but are not travelling together.",
        f"{bot['name']} has just run into "
        f"{_describe(extra, 'player', mode)}"
        f"{' in ' + zone if zone else ''} and waves hello.",
        f"{bot['name']} greets {player_name} warmly as a guildmate met "
        "by chance on the road, addressing them by name once. A short "
        "wish of luck, a friendly question or a light joke may follow.",
        "Spoken text only: no narrator text, emotes or name prefix.",
        "Aim for 4 to 14 words.",
    ])
    prompt = append_json_instruction(
        "\n".join(lines), allow_action=False, message_only=True,
    )
    maximum = min(_max_characters(config), 100)
    metadata = {
        'guild_id': _safe_int(extra.get('guild_id')),
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
    insert_chat_message(
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
    _mark_event(db, event_id, 'completed')
    logger.info(
        "guild_meet_greeting bot=%s player=%s", bot['name'], player_name,
    )
    return True


# --------------------------------------------------------------------------
# Join announcement in General
# --------------------------------------------------------------------------

def _responder_count(config: Dict, available: int) -> int:
    maximum = max(0, min(3, available, _safe_int(config.get(
        _PREFIX + 'JoinZoneAnnounce.MaxResponders', 2,
    ), 2)))
    return random.randint(0, maximum) if maximum else 0


def process_guild_join_zone_announce_event(db, client, config, event):
    """A new guild member boasts in General; zone bots react."""
    event_id = _safe_int(event.get('id'))
    if not _config_enabled(config, _PREFIX + 'JoinZoneAnnounce.Enable'):
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
        guid = _safe_int((raw or {}).get('guid'))
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
    participants = [announcer] + responders

    mode = get_chatter_mode(config)
    guild_name = str(extra.get('guild_name') or 'a guild')
    zone = get_zone_name(announcer['zone_id']) or 'this zone'
    lines = (
        ["Write natural in-character World of Warcraft General chat "
         f"in {zone}."]
        if is_roleplay(mode)
        else [build_player_chat_guidance(mode, 'general')]
    )
    for participant in participants:
        lines.extend(_participant_identity_lines(participant, mode))
    lines.append(
        f"{announcer['name']} has just joined the guild \"{guild_name}\" "
        "and is proud of it."
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
        f"Message 1: {announcer['name']} enthusiastically tells General "
        f"chat about joining \"{guild_name}\", naming the guild.",
        "Spoken text only: no narrator text, emotes or name prefixes.",
        "Aim for 4 to 16 words per message.",
    ])
    maximum = _max_characters(config)
    metadata = {
        'guild_id': _safe_int(extra.get('guild_id')),
        'guild_event': 'guild_join_zone_announce',
        'guild_responders': ','.join(p['name'] for p in participants),
        'guild_responder_count': len(responders),
        'guild_repair': False,
    }
    names = [p['name'] for p in participants]
    if responders:
        for index, responder in enumerate(responders, start=2):
            lines.append(
                f"Message {index}: {responder['name']} reacts from their "
                "own point of view: congratulations, friendly teasing, "
                "or open disdain for that guild."
            )
        prompt = append_conversation_json_instruction(
            "\n".join(lines), names, len(names),
            allow_action=False, message_only=True,
        )
        messages = run_multi_prompt(
            client, config, prompt, names, maximum, metadata,
            'guild_join_zone_announce',
            f"guild_join_zone_announce-multi:{event_id}",
            f"guild_join_zone_announce-json-repair:{event_id}",
        )
    else:
        prompt = append_json_instruction(
            "\n".join(lines), allow_action=False, message_only=True,
        )
        messages = run_single_prompt(
            client, config, prompt, announcer['name'], maximum, metadata,
            'guild_join_zone_announce',
            f"guild_join_zone_announce:{event_id}",
            f"guild_join_zone_announce-repair:{event_id}",
        )
    if not messages:
        _mark_event(db, event_id, 'skipped')
        return False

    guid_by_name = {p['name']: p['guid'] for p in participants}
    delays = _greeting_delays(messages, config)
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
            delay_seconds=delay + 1.0,
            event_id=event_id,
            sequence=sequence,
            owner_subsystem='guild',
        )
        inserted += 1
    _mark_event(db, event_id, 'completed' if inserted else 'skipped')
    logger.info(
        "guild_join_zone_announce announcer=%s responders=%d",
        announcer['name'], len(responders),
    )
    return bool(inserted)


# --------------------------------------------------------------------------
# Group PvP kill ("we killed") — no guild checks
# --------------------------------------------------------------------------

def build_group_pvp_kill_prompt(ctx: Dict) -> str:
    bot = ctx['bot']
    extra = ctx['extra_data']
    mode = ctx['mode']
    is_rp = mode == 'roleplay'
    victim = _describe(extra, 'victim', mode)
    killer = str(extra.get('killer_name') or '')
    killer_is_reactor = bool(extra.get('killer_is_reactor'))
    zone = get_zone_name(_safe_int(extra.get('zone_id'))) or ''

    parts = [build_player_prompt_header_from_dict(bot, mode)]
    parts.append(f"Your personality: {', '.join(ctx['traits'])}")
    parts.append(f"Your tone: {ctx['stored_tone'] or pick_random_tone(mode)}")
    if is_rp:
        rp = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=(extra.get('bot_state') or {}).get('role'),
        )
        if rp:
            parts.append(rp)
    if ctx['chat_hist']:
        parts.append(ctx['chat_hist'])
    if killer_is_reactor:
        who = "You struck the killing blow"
    elif killer:
        who = f"{killer} struck the killing blow"
    else:
        who = "Your party brought them down"
    parts.extend([
        f"Your party has just killed an enemy of the opposing faction"
        f"{' in ' + zone if zone else ''}: {victim}. {who}.",
        _strength_note(bot.get('level'), extra.get('victim_level')),
        "React in party chat from the group's point of view (\"we\", "
        "\"us\"): taunt the fallen foe, scorn the enemy faction, or "
        "share grim satisfaction. The victim's race or class may "
        "sharpen the line.",
        _pick_length_hint(mode),
        "Rules:\n- No quotes, no emojis\n- Reflect your personality\n"
        "- Don't repeat what was already said in chat",
    ])
    return append_json_instruction("\n".join(parts), False)


def process_group_pvp_kill_event(db, client, config, event):
    """A bot in the player's group reacts to an enemy kill."""
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_pvp_kill',
        extract_fields=lambda extra: {},
        build_prompt=build_group_pvp_kill_prompt,
        allow_emote=False,
    )
