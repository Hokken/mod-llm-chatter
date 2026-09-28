"""Duel reactions for group bots.

Handles bot_group_duel_start and bot_group_duel_end,
queued by src/LLMChatterDuel.cpp. The reactor is
either one of the duellists (a group bot) or a group
bot watching the duel.
"""

import logging

from chatter_shared import (
    build_race_class_context,
    build_bot_state_context,
    append_json_instruction,
    get_class_name,
    get_race_name,
)
from chatter_prompts import (
    pick_random_tone,
    maybe_get_creative_twist,
)
from chatter_mode import build_player_prompt_header_from_dict
from chatter_group_prompts import _pick_length_hint
from chatter_handler_pipeline import run_group_handler

logger = logging.getLogger(__name__)

_OUTCOME_TEXT = {
    'won': 'won the duel',
    'fled': 'won the duel after the other fled '
            'the duel area',
}


def _payload_flag(value):
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true')
    return bool(value)


def _describe_duellist(extra_data, prefix, bot_guid):
    """Describe one duellist from the reactor's point
    of view. Never labels anyone as a bot.

    C++ omits the identity of a duellist the reactor
    cannot perceive (`<prefix>_identity_known` false).
    """
    try:
        guid = int(extra_data.get(f'{prefix}_guid', 0))
    except (TypeError, ValueError):
        guid = 0
    if guid and guid == bot_guid:
        return 'you'
    if not _payload_flag(
            extra_data.get(f'{prefix}_identity_known', True)):
        return 'an opponent you cannot see clearly'

    name = str(
        extra_data.get(f'{prefix}_name') or ''
    ).strip() or 'someone'
    try:
        level = int(extra_data.get(f'{prefix}_level', 0))
        race = get_race_name(
            int(extra_data.get(f'{prefix}_race', 0)))
        cls = get_class_name(
            int(extra_data.get(f'{prefix}_class', 0)))
    except (TypeError, ValueError):
        level, race, cls = 0, '', ''

    desc = ' '.join(p for p in (
        f"level {level}" if level else '', race, cls,
    ) if p)
    who = f"{name} ({desc})" if desc else name
    if _payload_flag(
            extra_data.get(f'{prefix}_is_real_player')):
        who += ", the real player in your party"
    elif _payload_flag(
            extra_data.get(f'{prefix}_in_group')):
        who += ", from your party"
    else:
        who += ", from outside your party"
    return who


def _build_duel_prompt(
    bot, traits, situation, guidance, mode,
    chat_history="", extra_data=None,
    speaker_talent_context=None, stored_tone=None,
):
    """Shared prompt shape for duel reactions."""
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data, mode
        )
        actual_role = (
            extra_data.get('bot_state', {})
            .get('role')
        )

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=actual_role
        )
        if ctx:
            rp_context = f"\n{ctx}"
    if chat_history:
        rp_context += f"{chat_history}\n"

    prompt = (
        f"{build_player_prompt_header_from_dict(bot, mode)}\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += f"Your tone: {tone}\n"
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"{guidance}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- A duel is a friendly contest; nobody "
        f"dies\n"
        f"- Friendly teasing is fine, but no slurs, "
        f"abuse, or hateful language\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(prompt, True)


def build_duel_start_prompt(
    bot, traits, extra_data, mode,
    chat_history="", speaker_talent_context=None,
    stored_tone=None,
):
    """Prompt for a bot reacting as a duel begins."""
    bot_guid = int(extra_data.get('bot_guid', 0))
    a = _describe_duellist(
        extra_data, 'duellist_a', bot_guid)
    b = _describe_duellist(
        extra_data, 'duellist_b', bot_guid)
    role = extra_data.get('reactor_role', 'spectator')

    if role == 'duellist':
        opponent = b if a == 'you' else a
        situation = (
            f"You just started a duel against "
            f"{opponent}."
        )
        guidance = (
            "Say something as the duel begins: "
            "confidence, a friendly taunt, or nerves, "
            "as your personality suggests."
        )
    else:
        situation = (
            f"A duel just started between {a} and "
            f"{b}. You are watching."
        )
        guidance = (
            "Comment as a spectator: cheer someone "
            "on, predict the winner, or offer a "
            "friendly bet."
        )

    initiator = str(
        extra_data.get('initiator_name') or ''
    ).strip()
    if initiator:
        situation += f" {initiator} issued the challenge."

    return _build_duel_prompt(
        bot, traits, situation, guidance, mode,
        chat_history=chat_history,
        extra_data=extra_data,
        speaker_talent_context=speaker_talent_context,
        stored_tone=stored_tone,
    )


def build_duel_end_prompt(
    bot, traits, extra_data, mode,
    chat_history="", speaker_talent_context=None,
    stored_tone=None,
):
    """Prompt for a bot reacting to a duel result."""
    bot_guid = int(extra_data.get('bot_guid', 0))
    winner = _describe_duellist(
        extra_data, 'winner', bot_guid)
    loser = _describe_duellist(
        extra_data, 'loser', bot_guid)
    role = extra_data.get('reactor_role', 'spectator')
    outcome = extra_data.get('outcome', 'won')

    if outcome == 'interrupted':
        situation = (
            f"The duel between {winner} and {loser} "
            f"was interrupted before it was settled."
        )
        guidance = (
            "React to the anticlimax: disappointment, "
            "relief, or a call for a rematch."
        )
    elif role == 'winner':
        how = (
            " after they fled the duel area"
            if outcome == 'fled' else ""
        )
        situation = f"You just won a duel against {loser}{how}."
        guidance = (
            "React to your win: gracious, smug, or "
            "playful, as your personality suggests."
        )
    elif role == 'loser':
        if outcome == 'fled':
            situation = (
                f"You left the duel area, so {winner} "
                f"won the duel against you."
            )
        else:
            situation = f"You just lost a duel to {winner}."
        guidance = (
            "React to losing: a good sport, a grumble, "
            "an excuse, or a demand for a rematch."
        )
    else:
        result = _OUTCOME_TEXT.get(outcome, 'won the duel')
        situation = (
            f"You watched a duel: {winner} {result} "
            f"against {loser}."
        )
        guidance = (
            "Comment as a spectator: congratulate, "
            "tease the loser kindly, or settle a bet."
        )

    return _build_duel_prompt(
        bot, traits, situation, guidance, mode,
        chat_history=chat_history,
        extra_data=extra_data,
        speaker_talent_context=speaker_talent_context,
        stored_tone=stored_tone,
    )


def process_duel_start_event(db, client, config, event):
    """Handle a bot_group_duel_start event."""
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_duel_start',
        extract_fields=lambda ed: {},
        build_prompt=lambda ctx: (
            build_duel_start_prompt(
                ctx['bot'], ctx['traits'],
                ctx['extra_data'], ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        delay_seconds=2,
        label='reaction_duel_start',
    )


def process_duel_end_event(db, client, config, event):
    """Handle a bot_group_duel_end event."""
    return run_group_handler(
        db, client, config, event,
        event_type_label='bot_group_duel_end',
        extract_fields=lambda ed: {},
        build_prompt=lambda ctx: (
            build_duel_end_prompt(
                ctx['bot'], ctx['traits'],
                ctx['extra_data'], ctx['mode'],
                chat_history=ctx['chat_hist'],
                speaker_talent_context=(
                    ctx['speaker_talent']),
                stored_tone=ctx['stored_tone'],
            )
        ),
        delay_seconds=2,
        label='reaction_duel_end',
    )
