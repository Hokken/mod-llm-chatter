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
    append_json_instruction,
    get_chatter_mode,
    get_gender_label,
    build_gear_context,
)
from chatter_mode import build_player_prompt_header
from chatter_group_state import (
    _mark_event,
    _store_chat,
    build_party_context,
    get_bot_traits,
)

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
    bot_gender = get_gender_label(
        int(extra.get('bot_gender') or 0)
    )

    is_custom = bool(int(extra.get('custom_emote') or 0))
    if is_custom:
        # Free text has no id, so no emote category and no
        # category tone pool. 'custom' is not a REACTION_TONES
        # key, which lands _pick_tone on the generic pool.
        category = 'custom'
    else:
        emote_id = EMOTE_NAME_TO_ID.get(emote, 0)
        category = EMOTE_CATEGORIES.get(
            emote_id, 'greeting'
        )
    trait_data = get_bot_traits(
        db, group_id, bot_guid
    ) if group_id and bot_guid else None
    traits = (
        trait_data.get('traits', [])
        if trait_data else []
    )
    stored_tone = (
        trait_data.get('tone')
        if trait_data else None
    )

    prompt = _build_reaction_prompt(
        bot_name, bot_race, bot_class,
        bot_gender,
        p_name, emote, category,
        traits=traits,
        stored_tone=stored_tone,
        mode=get_chatter_mode(config),
        is_custom=is_custom,
        gear=build_gear_context(
            db, bot_guid, bot_class, config,
        ),
        party_context=build_party_context(
            db, group_id, bot_name,
        ),
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
        label='reaction_emote',
        group_id=group_id,
        delivery_policy='responsive',
        delivery_reason='bot_group_emote_reaction',
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
    bot_name, bot_race, bot_class, bot_gender,
    p_name, emote, category,
    traits=None,
    stored_tone=None,
    mode='roleplay',
    is_custom=False,
    gear='',
    party_context='',
):
    tone = stored_tone or _pick_tone(category)
    identity = build_player_prompt_header(
        bot_name, bot_race, bot_class,
        gender=bot_gender, mode=mode, channel='party',
        gear=gear,
    )
    prompt = identity
    if traits:
        prompt += (
            " Your personality: "
            f"{', '.join(traits)}."
        )
    if party_context:
        prompt += f"\n{party_context}"
    if is_custom:
        # Free text is already phrased as an action
        # ("grabs your hand"), so quote it rather than
        # rendering it as a /slash command.
        did = (
            f"just did this to you: \"{emote}\""
        )
    else:
        did = f"just /{emote} at you"
    prompt += (
        f"\nYour tone: {tone}. "
        f"Your party member {p_name} "
        f"{did}. React {tone}. "
        "1-2 sentences. "
        "NEVER put /slash commands in your "
        "response."
    )
    return append_json_instruction(prompt)
