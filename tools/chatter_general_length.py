"""Length selection for player-driven General replies only."""

import random

_TIERS = ('short', 'medium', 'developed')
_DEFAULT_WEIGHTS = (35, 45, 20)
_DEFAULT_MAXIMA = (75, 150, 240)


def _triplet(config, key, default, maxima=False):
    raw = (config or {}).get(key)
    if raw is None:
        return default
    try:
        values = tuple(int(part.strip()) for part in str(raw).split(','))
        valid = len(values) == 3
        if maxima:
            valid = valid and 1 <= values[0] < values[1] < values[2] <= 255
        else:
            valid = valid and min(values) >= 0 and sum(values) > 0
        return values if valid else default
    except (ValueError, TypeError):
        return default


def pick_general_reply_tier(config, avoid=None):
    """Avoid the prior speaker's band when another weighted band exists."""
    weights = _triplet(
        config, 'LLMChatter.GeneralChat.PlayerReplyLengthWeights',
        _DEFAULT_WEIGHTS,
    )
    pairs = [(tier, weight) for tier, weight in zip(_TIERS, weights)
             if weight > 0]
    if avoid and any(tier != avoid for tier, _ in pairs):
        pairs = [(tier, weight) for tier, weight in pairs if tier != avoid]
    tiers, weights = zip(*pairs)
    return random.choices(tiers, weights=weights, k=1)[0]


def general_reply_length_line(config=None, tier='medium'):
    """An approximate ceiling/nudge, subordinate to player intent and conversation."""
    maxima = _triplet(
        config, 'LLMChatter.GeneralChat.PlayerReplyLengthMaxima',
        _DEFAULT_MAXIMA, maxima=True,
    )
    index = _TIERS.index(tier) if tier in _TIERS else 1
    lower = 1 if index == 0 else maxima[index - 1] + 1
    upper = maxima[index]
    return (
        f'Length suggestion: {tier}, around {lower}-{upper} characters. '
        'This is an approximate ceiling and nudge, not a quota. '
        "The player's intent and the conversation take priority. "
        'Use less space for a simple point; use an extra sentence or a '
        'specific detail when the answer benefits from it. Never pad to '
        'reach a minimum or sacrifice a meaningful answer to fit the '
        'suggestion. HARD LIMIT: 255 characters total.'
    )
