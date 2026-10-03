"""Bounded, length-aware pacing for nearby conversation lines."""

import math
import random

from chatter_text import (
    cleanup_message,
    shorten_chat_message,
    strip_speaker_prefix,
)

_PREFIX = 'LLMChatter.ProximityChatter.DynamicPacing.'


def _number(config, key, default):
    try:
        value = float(config.get(_PREFIX + key, default))
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def proximity_line_delays(messages, config, fixed_delay):
    """Keep the first line immediate; vary bounded gaps between later lines.

    Reading and composing can overlap, so the longer of the previous
    visible line and the next line sets the length contribution.
    Sample inside the bounds rather than clipping jitter afterwards,
    preserving variation even for very short or very long messages.
    """
    config = config or {}
    if not _number(config, 'Enable', 1):
        return [index * fixed_delay for index in range(len(messages))]

    minimum = max(1.0, _number(config, 'MinSeconds', 3))
    maximum = max(minimum, _number(config, 'MaxSeconds', 8))
    rate = _number(config, 'CharsPerSecond', 20)
    if rate <= 0:
        rate = 20
    jitter = max(0.0, min(100.0, _number(
        config, 'JitterPercent', 20,
    ))) / 100.0
    delays = []
    elapsed = 0.0
    previous_length = 0
    for index, line in enumerate(messages):
        text = strip_speaker_prefix(
            line.get('message', ''), line.get('name', ''),
        )
        text = shorten_chat_message(cleanup_message(
            text, action=line.get('action'),
        ))
        length = len(text)
        if index:
            base = min(maximum, minimum + max(
                previous_length, length,
            ) / rate)
            elapsed += random.uniform(
                max(minimum, base * (1.0 - jitter)),
                min(maximum, base * (1.0 + jitter)),
            )
        delays.append(round(elapsed))
        previous_length = length
    return delays
