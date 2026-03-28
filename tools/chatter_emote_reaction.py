"""Emote reaction handler -- THIS bot was targeted
directly by a player emote. Personal verbal response
after the C++ mirror emote."""

import random

from chatter_constants import (
    EMOTE_CATEGORIES,
    EMOTE_NAME_TO_ID,
    REACTION_TONES,
    CLASS_NAMES,
    RACE_NAMES,
)
from chatter_shared import (
    parse_extra_data,
    run_single_reaction,
    build_bot_identity,
    append_json_instruction,
)
from chatter_group_state import _mark_event, _store_chat

_DEFAULT_TONES = [
    "with dry wit", "with humor",
    "with curiosity", "briefly",
]


def _pick_tone(category: str) -> str:
    pool = REACTION_TONES.get(
        category, _DEFAULT_TONES
    )
    return random.choice(pool)


def handle_emote_reaction(db, client, config, event):
    """THIS bot was targeted directly -- personal
    verbal response after the C++ mirror emote."""
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_emote_reaction',
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    emote = extra.get('emote_name', 'wave')
    p_name = extra.get('player_name', 'someone')
    bot_name = extra.get('bot_name', 'Bot')
    group_id = int(extra.get('group_id') or 0)
    bot_guid = int(extra.get('bot_guid') or 0)
    bot_class = CLASS_NAMES.get(
        int(extra.get('bot_class') or 0), ''
    )
    bot_race = RACE_NAMES.get(
        int(extra.get('bot_race') or 0), ''
    )

    emote_id = EMOTE_NAME_TO_ID.get(emote, 0)
    category = EMOTE_CATEGORIES.get(
        emote_id, 'greeting'
    )

    prompt = _build_reaction_prompt(
        bot_name, bot_race, bot_class,
        p_name, emote, category,
    )

    result = run_single_reaction(
        db, client, config,
        prompt=prompt,
        speaker_name=bot_name,
        bot_guid=bot_guid,
        channel='party',
        delay_seconds=2,
        event_id=event_id,
        allow_emote_fallback=True,
        context=(
            f"emote-react:#{event_id}:{bot_name}"
        ),
        bypass_speaker_cooldown=True,
    )
    if not result['ok']:
        _mark_event(db, event_id, 'skipped')
        return False

    _store_chat(
        db, group_id, bot_guid,
        bot_name, True, result['message'],
    )
    return True


def _build_reaction_prompt(
    bot_name, bot_race, bot_class,
    p_name, emote, category,
):
    tone = _pick_tone(category)
    identity = build_bot_identity(
        bot_name, bot_race, bot_class
    )
    prompt = (
        f"{identity} Your party member {p_name} "
        f"just /{emote} at you. React {tone}. "
        "1-2 sentences. "
        "NEVER put /slash commands in your "
        "response."
    )
    return append_json_instruction(prompt)
