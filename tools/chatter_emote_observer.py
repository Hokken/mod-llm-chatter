"""Emote observer handler -- bot sees player emote
at a creature, external player, or nobody."""

import random

from chatter_constants import (
    EMOTE_CATEGORIES,
    EMOTE_NAME_TO_ID,
    NPC_TYPE_NAMES,
    NPC_RANK_NAMES,
    REACTION_TONES,
    CLASS_NAMES,
    RACE_NAMES,
)
from chatter_shared import (
    parse_extra_data,
    run_single_reaction,
    build_bot_identity,
    append_json_instruction,
    get_gender_label,
)
from chatter_group_state import (
    _mark_event,
    _store_chat,
    get_bot_traits,
)


def handle_emote_observer(db, client, config, event):
    """Bot observes player emoting at a creature,
    external player, or nobody."""
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id,
        'bot_group_emote_observer',
    )
    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    tgt = extra.get('target_type', 'none')
    emote = extra.get('emote_name', 'wave')
    t_name = extra.get('target_name', '')
    p_name = extra.get('player_name', 'the player')
    bot_name = extra.get('bot_name', 'Bot')
    npc_rank = int(extra.get('npc_rank') or 0)
    npc_type = int(extra.get('npc_type') or 0)
    npc_subname = extra.get('npc_subname', '')
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

    if tgt == 'creature':
        prompt = _build_creature_prompt(
            bot_name, bot_race, bot_class,
            bot_gender,
            p_name, emote, t_name,
            category, npc_rank, npc_type,
            npc_subname,
            traits=traits,
            stored_tone=stored_tone,
        )
    elif tgt == 'player_external':
        prompt = _build_player_prompt(
            bot_name, bot_race, bot_class,
            bot_gender,
            p_name, emote, t_name, category,
            traits=traits,
            stored_tone=stored_tone,
        )
    else:
        prompt = _build_undirected_prompt(
            bot_name, bot_race, bot_class,
            bot_gender,
            p_name, emote,
            traits=traits,
            stored_tone=stored_tone,
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
            f"emote-obs:#{event_id}:{bot_name}"
        ),
        bypass_speaker_cooldown=True,
        label='reaction_emote_obs',
    )
    if not result['ok']:
        _mark_event(db, event_id, 'skipped')
        return False

    _store_chat(
        db, group_id, bot_guid,
        bot_name, True, result['message'],
    )
    return True


_DEFAULT_TONES = [
    "dry wit", "humor",
    "curiosity", "brief observation",
]


def _pick_tone(category: str) -> str:
    pool = REACTION_TONES.get(
        category, _DEFAULT_TONES
    )
    return random.choice(pool)


def _build_creature_prompt(
    bot_name, bot_race, bot_class, bot_gender,
    p_name, emote, t_name,
    category, npc_rank, npc_type,
    npc_subname='',
    traits=None,
    stored_tone=None,
):
    rank_str = NPC_RANK_NAMES.get(npc_rank, "")
    type_str = NPC_TYPE_NAMES.get(
        npc_type, "creature"
    )
    rank_label = (
        f"{rank_str} "
        if rank_str and rank_str != "Normal"
        else ""
    )
    creature_label = t_name or "a creature"
    # Build role description: prefer subname
    # ("Druid Trainer", "Food Vendor", "Guard"),
    # fall back to type ("Humanoid", "Beast").
    if npc_subname:
        role_label = npc_subname
    else:
        role_label = f"{rank_label}{type_str}"
    tone = stored_tone or _pick_tone(category)
    identity = build_bot_identity(
        bot_name, bot_race, bot_class, bot_gender
    )
    prompt = identity
    if traits:
        prompt += (
            " Your personality: "
            f"{', '.join(traits)}."
        )
    prompt += (
        f" Your tone: {tone}. "
        f"You witness {p_name} "
        f"/{emote} at {creature_label} "
        f"({role_label}). "
        f"Make a brief offhand remark about it "
        f"— {tone}. 1-2 sentences. "
        "NEVER put /slash commands in your "
        "response."
    )
    return append_json_instruction(prompt)


def _build_player_prompt(
    bot_name, bot_race, bot_class, bot_gender,
    p_name, emote, t_name, category,
    traits=None,
    stored_tone=None,
):
    tone = stored_tone or _pick_tone(category)
    identity = build_bot_identity(
        bot_name, bot_race, bot_class, bot_gender
    )
    prompt = identity
    if traits:
        prompt += (
            " Your personality: "
            f"{', '.join(traits)}."
        )
    prompt += (
        f" Your tone: {tone}. "
        f"You notice {p_name} "
        f"/{emote} at {t_name}, "
        "a stranger outside the group. "
        f"Make a brief comment about it "
        f"— {tone}. 1-2 sentences. "
        "NEVER put /slash commands in your "
        "response."
    )
    return append_json_instruction(prompt)


def _build_undirected_prompt(
    bot_name, bot_race, bot_class, bot_gender,
    p_name, emote,
    traits=None,
    stored_tone=None,
):
    category = EMOTE_CATEGORIES.get(
        EMOTE_NAME_TO_ID.get(emote, 0), "ambient"
    )
    tone = stored_tone or _pick_tone(category)
    identity = build_bot_identity(
        bot_name, bot_race, bot_class, bot_gender
    )
    prompt = identity
    if traits:
        prompt += (
            " Your personality: "
            f"{', '.join(traits)}."
        )
    prompt += (
        f" Your tone: {tone}. "
        f"You notice {p_name} "
        f"just /{emote}. "
        f"Make a brief offhand remark — {tone}. "
        "1-2 sentences. "
        "NEVER put /slash commands in your "
        "response."
    )
    return append_json_instruction(prompt)
