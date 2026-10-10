"""Open-world PvP reactions produced by LLMChatterGuildPvP.cpp.

``guild_pvp_kill``   a lone guild bot tells the guild about an enemy of
                     the other faction it killed.
``guild_pvp_death``  a guild bot killed by an enemy bot tells the guild.
``zone_pvp_death``   a bot killed by an enemy bot speaks in its zone's
                     General channel.

The prompts describe what happened and let each bot's personality and
tone decide how it reacts.
"""

import logging
from typing import Dict, List

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
    max_characters,
    personality_rule,
    run_single_prompt,
    safe_int,
)
from chatter_guild_player import _config_enabled, _mark_event
from chatter_guild_profile import (
    describe_character,
    get_guild_profile,
    guild_identity_lines,
)
from chatter_identity import prepare_guild_speakers
from chatter_mode import build_player_chat_guidance, is_roleplay
from chatter_shared import (
    _zone_delivery_delay,
    append_json_instruction,
    faction_war_line,
    get_chatter_mode,
    get_zone_name,
    parse_extra_data,
)

logger = logging.getLogger(__name__)


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


def _single_guild_line(
    db, client, config, event, event_type: str, enable_key: str,
    scenario_fn,
) -> bool:
    event_id = safe_int(event.get('id'))
    if not _config_enabled(config, PREFIX + enable_key):
        _mark_event(db, event_id, 'skipped')
        return False
    extra = parse_extra_data(
        event.get('extra_data'), event_id, event_type,
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
        scenario_fn(extra, mode),
        maximum,
    )
    metadata = {
        'guild_id': safe_int(extra.get('guild_id')),
        'guild_event': event_type,
        'guild_responders': speaker['name'],
        'guild_responder_count': 1,
        'guild_info_included': bool(guild_context),
        'guild_repair': False,
    }
    messages = generate(
        client, config, event_id, event_type, prompt, names, maximum,
        metadata,
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
        "%s guild=%s speaker=%s", event_type,
        extra.get('guild_id'), speaker['name'],
    )
    return True


# --------------------------------------------------------------------------
# Guild PvP kill
# --------------------------------------------------------------------------

def _strength_note(own_level, victim_level) -> str:
    diff = safe_int(own_level) - safe_int(victim_level)
    if diff >= 5:
        return "The enemy was far less seasoned than the killer."
    if diff <= -5:
        return "The enemy was far more seasoned than the killer."
    # Only the levels are known, not how the fight went.
    return "They were of similar experience."


def _pvp_kill_scenario(extra: Dict, mode: str) -> List[str]:
    name = str(extra.get('bot_name') or 'The speaker')
    zone = get_zone_name(safe_int(extra.get('zone_id'))) or ''
    victim = _describe(extra, 'victim', mode)
    lines = [
        f"{name} has just killed an enemy of the opposing faction"
        f"{' in ' + zone if zone else ''}: {victim}.",
    ]
    war = faction_war_line(
        name, extra.get('bot_team'),
        extra.get('victim_name') or 'the victim', extra.get('victim_team'),
    )
    if war:
        lines.append(war)
    return lines + [
        _strength_note(extra.get('bot_level'), extra.get('victim_level')),
        f"{name} tells the guild about it in the first person (\"I\"). "
        "A taunt, grim satisfaction, a brag, a shrug or a dry remark "
        "are all possible.",
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
# PvP death (Guild chat or zone General chat)
# --------------------------------------------------------------------------

def _death_strength_note(name, own_level, killer_level) -> str:
    diff = safe_int(own_level) - safe_int(killer_level)
    if diff >= 5:
        return f"The killer was far less seasoned than {name}."
    if diff <= -5:
        return f"The killer was far more seasoned than {name}."
    # Only the levels are known, not how the fight went.
    return "They were of similar experience."


def _pvp_death_scenario(extra: Dict, mode: str, audience: str) -> List[str]:
    name = str(extra.get('bot_name') or 'The speaker')
    killer_name = str(extra.get('killer_name') or 'the killer')
    zone = get_zone_name(safe_int(extra.get('zone_id'))) or ''
    lines = [
        f"{name} has just been killed{' in ' + zone if zone else ''} by "
        f"an enemy of the opposing faction: "
        f"{_describe(extra, 'killer', mode)}.",
    ]
    war = faction_war_line(
        name, extra.get('bot_team'), killer_name, extra.get('killer_team'),
    )
    if war:
        lines.append(war)
    lines += [
        _death_strength_note(name, extra.get('bot_level'),
                             extra.get('killer_level')),
        f"{name} tells {audience} about it in the first person. Anger, "
        "grief, a shrug, a dry joke, a vow of revenge or a warning are "
        "all possible.",
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
            "It may sound like a player commenting on being killed by "
            "another player."
        )
    return lines


def process_guild_pvp_death_event(db, client, config, event):
    """A guild bot killed by an enemy bot tells the guild."""
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
        personality_rule([bot['name']]),
        "Spoken text only: no narrator text, emotes or name prefix.",
        "Aim for 4 to 16 words.",
    ])
    return append_json_instruction(
        "\n".join(lines), allow_action=False, message_only=True,
    )


def process_zone_pvp_death_event(db, client, config, event):
    """A bot killed by an enemy bot speaks in its zone's General chat."""
    event_id = safe_int(event.get('id'))
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
    bot = _prepared(db, client, config, bot, channel='general')

    mode = get_chatter_mode(config)
    prompt = build_zone_pvp_death_prompt(bot, extra, mode)
    metadata = {
        'pvp_death_channel': 'general',
        'killer_name': str(extra.get('killer_name') or ''),
        'zone_id': bot['zone_id'],
    }
    messages = run_single_prompt(
        client, config, prompt, bot['name'], max_characters(config),
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
        delay_seconds=_zone_delivery_delay(bot['zone_id'], config),
        event_id=event_id,
    )
    _mark_event(db, event_id, 'completed')
    logger.info(
        "zone_pvp_death bot=%s killer=%s zone=%s", bot['name'],
        extra.get('killer_name'), bot['zone_id'],
    )
    return True
