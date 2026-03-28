"""Text/parsing helpers extracted from chatter_shared (N13)."""

import json
import logging
import random
import re
from typing import Optional, Tuple

from chatter_constants import EMOTE_LIST

logger = logging.getLogger(__name__)


def strip_speaker_prefix(message: str, bot_name: str) -> str:
    """Strip 'BotName:' prefix that LLMs sometimes add."""
    if message.startswith(f"{bot_name}:"):
        return message[len(bot_name) + 1:].strip()
    return message


def _validate_emote(emote_str: Optional[str]) -> Optional[str]:
    """Local emote validator used by parse_single_response.

    Mirrors chatter_shared.validate_emote() behavior
    to avoid cross-module import coupling.
    """
    if not emote_str or not isinstance(emote_str, str):
        return None
    cleaned = emote_str.strip().lower()
    cleaned = cleaned.strip('"').strip("'")
    if cleaned in EMOTE_LIST and cleaned != 'none':
        return cleaned
    return None


def parse_single_response(response: str) -> dict:
    """Parse a single LLM response that may be JSON
    with message/emote/action fields.

    Returns dict with 'message', 'emote', 'action'.
    Falls back to plain text if JSON parsing fails.
    """
    if not response:
        return {
            'message': '',
            'emote': None,
            'action': None,
        }

    cleaned = response.strip()
    # Strip ```json wrapper
    cleaned = re.sub(
        r'```(?:json)?', '', cleaned,
        flags=re.IGNORECASE
    ).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            msg = data.get('message', '')
            if isinstance(msg, str):
                msg = msg.strip().strip('"')
            else:
                msg = str(msg).strip()

            # Validate emote
            raw_emote = data.get('emote')
            emote = _validate_emote(raw_emote)

            # Sanitize action
            raw_action = data.get('action')
            action = _sanitize_action(raw_action)

            return {
                'message': msg,
                'emote': emote,
                'action': action,
            }
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: treat as plain text
    msg = cleaned.strip().strip('"')
    return {
        'message': msg,
        'emote': None,
        'action': None,
    }


def _sanitize_action(raw_action) -> Optional[str]:
    """Clean and validate an action string from
    LLM JSON output.

    Returns sanitized action (2-80 chars) or None.
    Filters out LLM null-like strings ("none", "null",
    "n/a", "no action", etc.).
    """
    if not raw_action or not isinstance(
        raw_action, str
    ):
        return None
    action = raw_action.strip().strip('*"\'')
    # LLM sometimes returns "none"/"null" as string
    # instead of JSON null - strip trailing punct
    # first to catch "none." / "null," variants
    check = action.rstrip('.,!;:').lower()
    if check in (
        'none', 'null', 'n/a', 'no action',
        'no', 'na', '',
    ):
        return None
    if len(action) < 2 or len(action) > 80:
        return None
    return action


def cleanup_message(
    message: str, action: str = None
) -> str:
    """Clean up any formatting issues from LLM output.

    If action is provided (from structured JSON),
    prepend *action* and skip Phase 1/2 regex
    narration detection (JSON supersedes heuristic).
    """
    result = message

    # Collapse newlines into single space (WoW chat
    # is single-line; multi-line LLM output causes
    # ugly line breaks). Catches real newlines,
    # \r\n, and literal backslash-n sequences that
    # survive JSON decoding.
    result = re.sub(r'\s*(?:\r\n|\r|\n)\s*', ' ', result)
    result = result.replace('\\n', ' ')

    # Em-dashes
    result = re.sub(r'\s*—\s*', ', ', result)

    # Backslash escapes leaking from SQL/JSON encoding
    result = result.replace("\\'", "'")
    result = result.replace('\\"', '"')
    result = result.replace('\\\\', '\\')

    # Strip *action text* sneaked into the message
    # field by the LLM. Must run BEFORE the structured
    # action is prepended, otherwise the valid action
    # gets stripped too.
    # Min 4 chars protects *ok*/*no* from removal;
    # max 60 covers realistic multi-word actions.
    result = re.sub(
        r'^\*[^*]{4,60}\*\s*', '', result
    )

    # Structured action from JSON - prepend *action*.
    # This is the only source of narrator comments;
    # frequency is controlled by LLMChatter.ActionChance.
    if action:
        result = f"*{action}* {result}"

    result = result.strip()

    # Clean up spacing
    result = re.sub(r'\s{2,}', ' ', result)

    # Multi-speaker truncation: LLM sometimes embeds
    # a second speaker in the response, e.g.
    # "Well fought! Cylaea: Hold, do you smell that?"
    # Truncate at "Name: " pattern appearing after
    # the first 20 characters (to avoid false-matching
    # legitimate uses at the start of a message).
    if len(result) > 20:
        second_speaker = re.search(
            r'\b[A-Z][a-z]{2,}:\s', result[20:]
        )
        if second_speaker:
            cut_pos = 20 + second_speaker.start()
            truncated = result[:cut_pos].rstrip(
                ' ,.-'
            )
            if len(truncated) > 10:
                result = truncated

    # Emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE
    )
    result = emoji_pattern.sub('', result)

    # NPC markers to plain text
    result = re.sub(
        r'\[\[npc:\d+:([^\]]+)\]\]', r'\1', result
    )
    result = re.sub(
        r'\[npc:\d+:([^\]]+)\]', r'\1', result
    )
    # [npc:Name] without numeric ID (LLM variant)
    result = re.sub(
        r'\[npc:([^\]]+)\]', r'\1', result
    )
    result = re.sub(
        r'npc:\d+:([A-Za-z][A-Za-z\' ]+)', r'\1', result
    )

    # Strip *none* leaked from LLM action field
    result = re.sub(
        r'\*none\*\s*', '', result,
        flags=re.IGNORECASE
    )

    # Fix {[Name]} -> [Name]
    result = re.sub(r'\{\[([^\]]+)\]\}', r'[\1]', result)

    # Fix [[Name]] -> [Name]
    result = re.sub(r'\[\[([^\]]+)\]\]', r'[\1]', result)

    # Fix {Name} when not a known placeholder
    # Preserve pre-cache placeholders: {target},
    # {caster}, {spell} and WoW link prefixes
    result = re.sub(
        r'\{(?!quest:|item:|spell:|'
        r'target\}|caster\}|spell\})'
        r'([^}]+)\}',
        r'\1', result
    )

    return result


def extract_conversation_msg_count(prompt: str) -> int:
    """Extract expected message count from a prompt."""
    match = re.search(r'EXACTLY (\d+) messages', prompt)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return 0
    return 0


def repair_json_string(raw_json: str) -> str:
    """Attempt to repair common JSON escaping issues."""
    if not raw_json:
        return raw_json

    try:
        json.loads(raw_json)
        return raw_json
    except Exception:
        pass

    def escape_inner_quotes(match):
        inner = match.group(1)
        return '(\\"' + inner + '\\")'

    repaired = re.sub(
        r'\("([^"\\]+)"\)', escape_inner_quotes, raw_json
    )

    try:
        json.loads(repaired)
        return repaired
    except Exception:
        pass

    try:
        result = {}

        entry_match = re.search(
            r'"transport_entry":(\d+)', raw_json
        )
        if entry_match:
            result['transport_entry'] = int(
                entry_match.group(1)
            )

        type_match = re.search(
            r'"transport_type":"([^"]+)"', raw_json
        )
        if type_match:
            result['transport_type'] = type_match.group(1)

        dest_match = re.search(
            r'"destination":"([^"]+)"', raw_json
        )
        if dest_match:
            result['destination'] = dest_match.group(1)

        name_match = re.search(
            r'"transport_name":"(.+?)","'
            r'(?:destination|transport_type)"',
            raw_json
        )
        if name_match:
            result['transport_name'] = name_match.group(1)

        if result:
            return json.dumps(result)
    except Exception:
        pass

    return raw_json


def _extract_ngrams(text: str, n: int = 4) -> set:
    """Extract word n-grams from text for similarity
    comparison. Lowercased, punctuation stripped."""
    words = re.sub(
        r'[^\w\s]', '', text.lower()
    ).split()
    if len(words) < n:
        return set()
    return {
        ' '.join(words[i:i+n])
        for i in range(len(words) - n + 1)
    }


def is_too_similar(
    new_message: str,
    recent_messages: list,
    threshold: int = 3
) -> bool:
    """Check if new_message shares too many n-grams
    with recent messages.

    Args:
        new_message: The message to check
        recent_messages: List of recent message strings
        threshold: Min shared 4-grams to trigger
            rejection. Default 3 avoids false positives
            from common phrases like "in the heart of"
            while catching real repetitions.

    Returns True if message should be rejected.
    """
    if not recent_messages or not new_message:
        return False

    new_ngrams = _extract_ngrams(new_message, 4)
    if not new_ngrams:
        return False

    # Pool all recent n-grams together
    recent_ngrams = set()
    for msg in recent_messages:
        recent_ngrams.update(_extract_ngrams(msg, 4))

    overlap = new_ngrams & recent_ngrams
    if len(overlap) >= threshold:
        return True

    return False


# ============================================================
# STATEMENT LENGTH ENFORCEMENT
# ============================================================

# Weighted ranges: short messages are more common
# than long ones, matching natural chat patterns.
STATEMENT_LENGTH_RANGES = [
    (20, 40, 20),    # very short
    (40, 70, 35),    # short
    (70, 120, 35),   # medium
    (120, 150, 10),  # longer
]


def pick_statement_length() -> Tuple[int, int, str]:
    """Pick a random target length range for an
    ambient statement via weighted RNG.

    Returns (min_chars, max_chars, label) where
    label is a human-readable hint for the prompt.
    """
    weights = [w for _, _, w in STATEMENT_LENGTH_RANGES]
    chosen = random.choices(
        STATEMENT_LENGTH_RANGES, weights=weights,
        k=1,
    )[0]
    lo, hi, _ = chosen
    if hi <= 40:
        label = f"very short (under {hi} chars)"
    elif hi <= 70:
        label = f"short ({lo}-{hi} chars)"
    elif hi <= 120:
        label = f"medium ({lo}-{hi} chars)"
    else:
        label = f"longer ({lo}-{hi} chars)"
    return lo, hi, label


