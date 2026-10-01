"""Emote observer handler -- bot sees player emote
at a creature, external player, a fellow party bot,
or nobody."""

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
    append_json_instruction,
    append_conversation_json_instruction,
    call_llm,
    parse_conversation_response,
    calculate_dynamic_delay,
    insert_chat_message,
    get_chatter_mode,
    get_gender_label,
    build_gear_context,
)
from chatter_mode import build_player_prompt_header
from chatter_guild_profile import (
    get_character_guild_name,
    same_guild_note,
)
from chatter_group_state import (
    _mark_event,
    _store_chat,
    build_party_context,
    get_bot_traits,
)
from chatter_persona import (
    build_cast_lines,
    build_persona_block,
    persona_from_fields,
)
from chatter_text import (
    cleanup_message,
    shorten_chat_message,
    strip_speaker_prefix,
)
from chatter_threads import capture_session, note_event
from chatter_party_gate import (
    defer_event_for_party_gate,
    should_defer_party_generation,
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

    if should_defer_party_generation(
        db, config, group_id,
        policy='filler',
        reason='bot_group_emote_observer',
    ):
        defer_event_for_party_gate(
            db, config, event_id,
            'bot_group_emote_observer',
        )
        return False

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

    gear = build_gear_context(
        db, bot_guid, bot_class, config,
    )
    party_context = build_party_context(
        db, group_id, bot_name,
    )
    guild_name = get_character_guild_name(db, bot_guid)
    guild_note = same_guild_note(
        db, bot_guid, extra.get('player_guid'), p_name,
    )

    mode = get_chatter_mode(config)
    thread_session = capture_session(group_id)
    if tgt == 'party_bot':
        target_guid = int(extra.get('target_guid') or 0)
        if (
            target_guid
            and t_name
            and _party_exchange_roll(config)
        ):
            ok = _party_bot_exchange(
                db, client, config, event_id, extra,
                group_id, bot_guid, bot_name, traits,
                stored_tone, target_guid, t_name,
                p_name, emote, is_custom, mode,
                thread_session,
            )
            if ok:
                return True
        prompt = _build_party_bot_prompt(
            bot_name, bot_race, bot_class,
            bot_gender,
            p_name, emote, t_name, category,
            traits=traits,
            stored_tone=stored_tone,
            mode=mode,
            is_custom=is_custom,
            gear=gear,
            party_context=party_context,
            bot_guid=bot_guid,
        )
    elif tgt == 'creature':
        prompt = _build_creature_prompt(
            bot_name, bot_race, bot_class,
            bot_gender,
            p_name, emote, t_name,
            category, npc_rank, npc_type,
            npc_subname,
            traits=traits,
            stored_tone=stored_tone,
            mode=get_chatter_mode(config),
            is_custom=is_custom,
            gear=gear,
            party_context=party_context,
            guild_name=guild_name,
            guild_note=guild_note,
        )
    elif tgt == 'player_external':
        prompt = _build_player_prompt(
            bot_name, bot_race, bot_class,
            bot_gender,
            p_name, emote, t_name, category,
            traits=traits,
            stored_tone=stored_tone,
            mode=get_chatter_mode(config),
            is_custom=is_custom,
            gear=gear,
            party_context=party_context,
            guild_name=guild_name,
            guild_note=guild_note,
            target_desc=_describe_target_player(extra, db),
        )
    else:
        prompt = _build_undirected_prompt(
            bot_name, bot_race, bot_class,
            bot_gender,
            p_name, emote,
            traits=traits,
            stored_tone=stored_tone,
            mode=get_chatter_mode(config),
            is_custom=is_custom,
            gear=gear,
            party_context=party_context,
            guild_name=guild_name,
            guild_note=guild_note,
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
        group_id=group_id,
        delivery_policy='filler',
        delivery_reason='bot_group_emote_observer',
    )
    if not result['ok']:
        _mark_event(db, event_id, 'skipped')
        return False

    _store_chat(
        db, group_id, bot_guid,
        bot_name, True, result['message'],
    )
    note_event(
        group_id, 'bot_group_emote_observer', bot_name,
        result['message'],
        message_id=result.get('message_id'),
        session=thread_session,
    )
    return True


def _party_exchange_roll(config) -> bool:
    """Roll EmoteReactions.PartyObserverExchangeChance."""
    try:
        chance = int((config or {}).get(
            'LLMChatter.EmoteReactions.'
            'PartyObserverExchangeChance', 35
        ))
    except (TypeError, ValueError):
        return False
    chance = max(0, min(chance, 100))
    return chance > 0 and random.randint(1, 100) <= chance


def _party_bot_exchange(
    db, client, config, event_id, extra,
    group_id, bot_guid, bot_name, traits, stored_tone,
    target_guid, t_name, p_name, emote, is_custom, mode,
    thread_session,
):
    """Two-line exchange: the observer remarks on the
    player's emote at their party member, who answers the
    observer. Returns False (caller falls back to a single
    statement) when nothing could be delivered."""
    target_data = get_bot_traits(db, group_id, target_guid)
    if not target_data:
        return False
    cast = [
        persona_from_fields(
            bot_name, mode, bot_guid,
            traits=traits, tone=stored_tone,
        ),
        persona_from_fields(
            t_name, mode, target_guid,
            traits=target_data.get('traits'),
            tone=target_data.get('tone'),
        ),
    ]
    seen = (
        f"{p_name} did this to {t_name}: \"{emote}\""
        if is_custom
        else f"{p_name} just did /{emote} at {t_name}"
    )
    lines = [
        f"Two party members react to a moment in their "
        f"group: {seen}.",
    ]
    lines.extend(build_cast_lines(cast, mode))
    lines.append(
        f"Message 1 ({bot_name}): a brief remark about what "
        f"{p_name} did to {t_name}, in {bot_name}'s own way."
    )
    lines.append(
        f"Message 2 ({t_name}): {t_name} answers {bot_name}'s "
        f"remark, not {p_name}."
    )
    lines.append(
        "Each line is short party chat (under 100 "
        "characters). NEVER put /slash commands in a message."
    )
    prompt = append_conversation_json_instruction(
        '\n'.join(lines), [bot_name, t_name], 2,
        allow_action=False,
    )
    response = call_llm(
        client, prompt, config,
        context=f"emote-obs-conv:#{event_id}:{bot_name}",
        label='reaction_emote_obs_conv',
    )
    messages = parse_conversation_response(
        response or '', [bot_name, t_name],
    )
    guids = {bot_name: bot_guid, t_name: target_guid}
    # Accept only the complete exchange: exactly the observer
    # then the targeted bot, both usable after cleanup.
    # Anything else falls back to the single observer comment.
    lines = []
    for msg in messages:
        text = cleanup_message(
            strip_speaker_prefix(msg['message'], msg['name'])
        )
        lines.append((
            msg['name'],
            shorten_chat_message(text) if text else '',
            msg.get('emote'),
        ))
    if (
        [name for name, _, _ in lines] != [bot_name, t_name]
        or not all(text for _, text, _ in lines)
    ):
        return False

    delivered = 0
    delay = 2.0
    prev_len = 0
    for seq, (name, text, emote_name) in enumerate(lines):
        if seq:
            delay += calculate_dynamic_delay(
                len(text), config, prev_message_length=prev_len,
            )
        message_id = insert_chat_message(
            db, guids[name], name, text,
            channel='party', delay_seconds=int(delay),
            event_id=event_id, sequence=seq,
            emote=emote_name, config=config,
            group_id=group_id,
            delivery_policy='filler',
            delivery_reason='bot_group_emote_observer',
        )
        _store_chat(
            db, group_id, guids[name],
            name, True, text,
        )
        note_event(
            group_id, 'bot_group_emote_observer',
            name, text,
            message_id=message_id, session=thread_session,
        )
        prev_len = len(text)
        delivered += 1
    return delivered > 0


_DEFAULT_TONES = [
    "dry wit", "humor",
    "curiosity", "brief observation",
]


def _pick_tone(category: str) -> str:
    pool = REACTION_TONES.get(
        category, _DEFAULT_TONES
    )
    return random.choice(pool)


def _describe_target_player(extra, db=None) -> str:
    """Describe an emote's player target, e.g.
    "a level 24 female Orc Hunter". Empty when C++
    sent no details for the target."""
    level = int(extra.get('target_level') or 0)
    race = RACE_NAMES.get(
        int(extra.get('target_race') or 0), ''
    )
    class_name = CLASS_NAMES.get(
        int(extra.get('target_class') or 0), ''
    )
    # Gender is only meaningful alongside a race/class —
    # on its own "female" describes nothing useful, and an
    # absent field must not silently read as male.
    gender = (
        get_gender_label(int(extra.get('target_gender') or 0))
        if 'target_gender' in extra and (race or class_name)
        else ''
    )
    parts = []
    if level:
        parts.append(f"level {level}")
    if gender:
        parts.append(gender)
    if race:
        parts.append(race)
    if class_name:
        parts.append(class_name)
    target_guid = int(extra.get('target_guid') or 0)
    if parts and db is not None and target_guid:
        guild_name = get_character_guild_name(db, target_guid)
        if guild_name:
            parts.append(f'of the guild "{guild_name}"')
    return ' '.join(parts)


def _build_creature_prompt(
    bot_name, bot_race, bot_class, bot_gender,
    p_name, emote, t_name,
    category, npc_rank, npc_type,
    npc_subname='',
    traits=None,
    stored_tone=None,
    mode='roleplay',
    is_custom=False,
    gear='',
    party_context='',
    guild_name='',
    guild_note='',
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
    identity = build_player_prompt_header(
        bot_name, bot_race, bot_class,
        gender=bot_gender, mode=mode, channel='party',
        gear=gear, guild_name=guild_name,
    )
    prompt = identity
    if traits:
        prompt += (
            " Your personality: "
            f"{', '.join(traits)}."
        )
    if party_context:
        prompt += f"\n{party_context}"
    if guild_note:
        prompt += f"\n{guild_note}"
    if is_custom:
        seen = (
            f"You witness {p_name} do this at "
            f"{creature_label} ({role_label}): "
            f"\"{emote}\""
        )
    else:
        seen = (
            f"You witness {p_name} "
            f"/{emote} at {creature_label} "
            f"({role_label})"
        )
    prompt += (
        f"\nYour tone: {tone}. "
        f"{seen}. "
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
    mode='roleplay',
    is_custom=False,
    gear='',
    party_context='',
    guild_name='',
    guild_note='',
    target_desc='',
):
    tone = stored_tone or _pick_tone(category)
    identity = build_player_prompt_header(
        bot_name, bot_race, bot_class,
        gender=bot_gender, mode=mode, channel='party',
        gear=gear, guild_name=guild_name,
    )
    prompt = identity
    if traits:
        prompt += (
            " Your personality: "
            f"{', '.join(traits)}."
        )
    if party_context:
        prompt += f"\n{party_context}"
    if guild_note:
        prompt += f"\n{guild_note}"
    stranger = (
        f"{t_name}, a {target_desc} from outside the group"
        if target_desc
        else f"{t_name}, a stranger outside the group"
    )
    if is_custom:
        seen = (
            f"You notice {p_name} do this at "
            f"{stranger}: \"{emote}\""
        )
    else:
        seen = (
            f"You notice {p_name} "
            f"/{emote} at {stranger}"
        )
    prompt += (
        f"\nYour tone: {tone}. "
        f"{seen}. "
        f"Make a brief comment about it "
        f"— {tone}. 1-2 sentences. "
        "NEVER put /slash commands in your "
        "response."
    )
    return append_json_instruction(prompt)


def _build_party_bot_prompt(
    bot_name, bot_race, bot_class, bot_gender,
    p_name, emote, t_name, category,
    traits=None,
    stored_tone=None,
    mode='roleplay',
    is_custom=False,
    gear='',
    party_context='',
    bot_guid=0,
):
    """The player emoted at a fellow party member; this bot
    saw it and may chime in. Identity goes through the shared
    persona resolution: normal mode uses the player-style
    profile, and a missing tone falls back deterministically."""
    persona = persona_from_fields(
        bot_name, mode, bot_guid,
        traits=traits, tone=stored_tone,
    )
    identity = build_player_prompt_header(
        bot_name, bot_race, bot_class,
        gender=bot_gender, mode=mode, channel='party',
        gear=gear,
    )
    prompt = f"{identity}\n{build_persona_block(persona, mode)}"
    if party_context:
        prompt += f"\n{party_context}"
    if is_custom:
        seen = (
            f"You notice {p_name} do this to your party "
            f"member {t_name}: \"{emote}\""
        )
    else:
        seen = (
            f"You notice {p_name} /{emote} at your party "
            f"member {t_name}"
        )
    prompt += (
        f"\n{seen}. "
        "Chime in with a brief comment, in your own way "
        "— you can tease, cheer, or react to either of "
        "them. 1-2 sentences. "
        "NEVER put /slash commands in your response."
    )
    return append_json_instruction(prompt)


def _build_undirected_prompt(
    bot_name, bot_race, bot_class, bot_gender,
    p_name, emote,
    traits=None,
    stored_tone=None,
    mode='roleplay',
    is_custom=False,
    gear='',
    party_context='',
    guild_name='',
    guild_note='',
):
    if is_custom:
        category = 'custom'
    else:
        category = EMOTE_CATEGORIES.get(
            EMOTE_NAME_TO_ID.get(emote, 0), "ambient"
        )
    tone = stored_tone or _pick_tone(category)
    identity = build_player_prompt_header(
        bot_name, bot_race, bot_class,
        gender=bot_gender, mode=mode, channel='party',
        gear=gear, guild_name=guild_name,
    )
    prompt = identity
    if traits:
        prompt += (
            " Your personality: "
            f"{', '.join(traits)}."
        )
    if party_context:
        prompt += f"\n{party_context}"
    if guild_note:
        prompt += f"\n{guild_note}"
    if is_custom:
        seen = f"You notice {p_name} do this: \"{emote}\""
    else:
        seen = f"You notice {p_name} just /{emote}"
    prompt += (
        f"\nYour tone: {tone}. "
        f"{seen}. "
        f"Make a brief offhand remark — {tone}. "
        "1-2 sentences. "
        "NEVER put /slash commands in your "
        "response."
    )
    return append_json_instruction(prompt)
