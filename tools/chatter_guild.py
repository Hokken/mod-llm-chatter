"""Guild chatter event handlers.

Ambient guild-channel banter: online guild members occasionally
exchange short, in-character lines in guild chat. Driven by
``CheckGuildIdleChatter`` in LLMChatterWorld.cpp, gated by
``LLMChatter.GuildChatter.*`` config. Mirrors the structure of the
raid idle-morale and proximity handlers.
"""

import logging
import random
from typing import Dict, Optional

from chatter_db import insert_chat_message
from chatter_llm import call_llm
from chatter_shared import (
    append_json_instruction,
    build_bot_identity_with_level,
    get_class_name,
    get_gender_label,
    get_race_name,
    get_zone_name,
    parse_extra_data,
)
from chatter_text import (
    cleanup_message,
    parse_single_response,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)


def _mark_event(db, event_id: int, status: str) -> None:
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events SET status = %s "
        "WHERE id = %s",
        (status, event_id),
    )
    db.commit()


def _query_speaker(db, bot_guid: int) -> Dict[str, object]:
    """Load a speaker's class/race/level/gender plus their
    stored personality (traits/tone/backstory) from the
    bot-identity table. Returns {} if the bot is unknown."""
    if not bot_guid:
        return {}

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT class, race, gender, level "
            "FROM characters WHERE guid = %s",
            (bot_guid,),
        )
        base = cursor.fetchone()
        if not base:
            return {}

        cursor.execute(
            "SELECT trait1, trait2, trait3, tone, "
            "       backstory "
            "FROM llm_bot_identities "
            "WHERE bot_guid = %s LIMIT 1",
            (bot_guid,),
        )
        ident = cursor.fetchone() or {}

        traits = [
            trait for trait in (
                ident.get('trait1'),
                ident.get('trait2'),
                ident.get('trait3'),
            )
            if trait
        ]
        return {
            'class': get_class_name(
                int(base.get('class', 0) or 0)
            ),
            'race': get_race_name(
                int(base.get('race', 0) or 0)
            ),
            'gender': get_gender_label(
                int(base.get('gender', 0) or 0)
            ),
            'level': int(base.get('level', 0) or 0),
            'traits': traits,
            'tone': ident.get('tone') or '',
            'backstory': ident.get('backstory') or '',
        }
    except Exception:
        logger.error(
            "query guild speaker failed",
            exc_info=True,
        )
        return {}


import random
from chatter_constants import GUILD_CHAT_TOPICS, GUILD_CHAT_TOPICS_RP


def _guild_length_hint():
    """Roadmap #5: vary message length so guild lines do not all read the
    same length. Favors short/medium, occasionally a full sentence."""
    return random.choices(
        ["very short (under 50 characters)",
         "short (50-90 characters)",
         "short (50-90 characters)",
         "medium (90-150 characters)",
         "a full sentence (150-200 characters)"],
        weights=[20, 30, 30, 15, 5],
    )[0]


def _build_guild_prompt(
    speaker_name: str,
    speaker: Dict,
    guild_name: str,
    guildmates: str,
    config: Optional[Dict] = None,
    zone_id: int = 0,
) -> str:
    identity = build_bot_identity_with_level(
        speaker_name,
        speaker.get('race', 'Unknown'),
        speaker.get('class', 'Adventurer'),
        speaker.get('level', 1),
        gender=speaker.get('gender', ''),
    )

    lines = [identity]
    lines.append(
        f"You are a member of the guild "
        f"\"{guild_name}\"."
    )

    traits = speaker.get('traits') or []
    if traits:
        lines.append(
            "Personality: " + ", ".join(traits) + "."
        )
    if speaker.get('tone'):
        lines.append(f"Tone: {speaker['tone']}.")
    if speaker.get('backstory'):
        lines.append(
            f"Background: {speaker['backstory']}"
        )
    if guildmates:
        lines.append(
            f"Guildmates currently online: "
            f"{guildmates}."
        )

    if zone_id:
        zone = get_zone_name(zone_id)
        if zone:
            lines.append(
                f"You are currently in {zone}. You may "
                "naturally mention what you are doing there "
                "(questing, leveling, traveling) or react to "
                "it — this is guild chat, so guildmates "
                "elsewhere will read it."
            )
    topic = random.choice(GUILD_CHAT_TOPICS_RP)
    lines.append(
        "Topic idea (optional - only use it if it fits "
        f"naturally, do not force it): {topic}."
    )
    lines.append(
        "Stay fully in character — you ARE this person "
        "in Azeroth. No fourth-wall breaks and no "
        "out-of-character or game-mechanic talk (no DPS "
        "meters, rotations, addons, or references to the "
        "player behind the screen). Draw on your race, "
        "class and surroundings."
    )
    lines.append(
        "Write ONE short, casual line for guild "
        "chat, in character, the way a real person "
        "playing WoW would chat with their guild. "
        f"Length: {_guild_length_hint()}. HARD LIMIT: never exceed 200 characters. No "
        "quotation marks, no name prefix, no "
        "roleplay asterisks."
    )

    return append_json_instruction(
        "\n".join(lines) + "\n"
    )


def process_guild_idle_chatter_event(
    db, client, config, event
):
    """Handle guild_idle_chatter — one online guild member
    posts a short in-character line to guild chat."""
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id, 'guild_idle_chatter')

    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    speaker_guid = int(
        event.get('subject_guid', 0) or 0
    )
    speaker_name = (
        event.get('subject_name')
        or extra.get('speaker_name')
        or ''
    )
    guild_name = extra.get('guild_name') or 'the guild'
    guildmates = extra.get('guildmates') or ''

    speaker = _query_speaker(db, speaker_guid)
    if not speaker or not speaker_name:
        _mark_event(db, event_id, 'skipped')
        return False

    zone_id = int(extra.get('zone_id', 0) or 0)
    prompt = _build_guild_prompt(
        speaker_name, speaker, guild_name,
        guildmates, config, zone_id=zone_id,
    )

    max_tokens = int(config.get(
        'LLMChatter.GuildChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"guild:{speaker_name}",
        label='guild_idle_chatter',
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    parsed = parse_single_response(response)
    message = strip_speaker_prefix(
        parsed.get('message', ''), speaker_name
    )
    message = cleanup_message(
        message, action=parsed.get('action')
    )
    if not message:
        _mark_event(db, event_id, 'skipped')
        return False
    if len(message) > 255:
        message = message[:252] + "..."

    insert_chat_message(
        db,
        bot_guid=speaker_guid,
        bot_name=speaker_name,
        message=message,
        channel='guild',
        owner_subsystem='guild',
        event_id=event_id,
    )

    _mark_event(db, event_id, 'completed')
    return True
