"""Canonical prompt rules for playerbot chatter modes.

Playerbots follow ``LLMChatter.ChatterMode``. Actual NPCs always remain
in-world, including when they share a proximity scene with playerbots.
"""

import hashlib


_NORMAL_PLAYER_STYLE_PROFILES = [
    (('friendly', 'patient'), 'warm and conversational'),
    (('quiet', 'polite'), 'brief and understated'),
    (('helpful', 'practical'), 'clear and matter-of-fact'),
    (('relaxed', 'easygoing'), 'casual and unhurried'),
    (('dry-humored', 'observant'), 'wry and concise'),
    (('chatty', 'curious'), 'friendly and engaged'),
    (('focused', 'cooperative'), 'direct but respectful'),
    (('experienced', 'patient'), 'calm and measured'),
    (('playful', 'good-natured'), 'lightly teasing but kind'),
    (('reserved', 'considerate'), 'soft-spoken and thoughtful'),
    (('competitive', 'fair-minded'), 'energetic without hostility'),
    (('methodical', 'reliable'), 'precise and composed'),
    (('newer', 'open-minded'), 'curious and unpretentious'),
    (('social', 'encouraging'), 'upbeat without overdoing it'),
    (('independent', 'courteous'), 'plain-spoken and self-contained'),
    (('blunt', 'well-meaning'), 'direct with occasional mild salt'),
    (('mature', 'supportive'), 'steady and reassuring'),
    (('casual', 'adaptable'), 'natural and low-key'),
    (('analytical', 'calm'), 'specific without lecturing'),
    (('self-deprecating', 'friendly'), 'dry and approachable'),
]

_NORMAL_PLAYER_EXTRA_TRAITS = [
    'attentive',
    'team-minded',
    'low-key',
    'curious',
    'straightforward',
    'good-humored',
    'steady',
    'flexible',
    'thoughtful',
    'game-focused',
]


def normalize_chatter_mode(mode: str) -> str:
    """Return a supported playerbot chatter mode."""
    value = str(mode or '').strip().lower()
    return value if value in ('normal', 'roleplay') else 'normal'


def is_roleplay(mode: str) -> bool:
    """Return whether playerbots should speak in character."""
    return normalize_chatter_mode(mode) == 'roleplay'


def resolve_player_personality(
    name: str,
    traits=None,
    tone: str = '',
    mode: str = 'normal',
):
    """Return RP identity metadata or a stable normal-player profile.

    Persistent identities predate the mode boundary and may contain mystical
    or in-world traits. Normal mode must never send that legacy metadata to
    the model, so it derives a deterministic player-side style from the bot
    name instead. Roleplay mode receives the stored values unchanged.
    """
    if is_roleplay(mode):
        return [value for value in (traits or []) if value], tone or ''

    seed = str(name or 'playerbot').strip().casefold().encode('utf-8')
    digest = hashlib.sha256(seed).digest()
    index = int.from_bytes(digest[:4], 'big') % len(
        _NORMAL_PLAYER_STYLE_PROFILES
    )
    player_traits, player_tone = _NORMAL_PLAYER_STYLE_PROFILES[index]
    extra_index = int.from_bytes(digest[4:8], 'big') % len(
        _NORMAL_PLAYER_EXTRA_TRAITS
    )
    return (
        list(player_traits)
        + [_NORMAL_PLAYER_EXTRA_TRAITS[extra_index]],
        player_tone,
    )


def build_player_identity(
    name: str,
    race: str = '',
    class_name: str = '',
    level=None,
    gender: str = '',
    mode: str = 'normal',
) -> str:
    """Build an identity with an explicit player/character boundary."""
    details = []
    if level not in (None, '', 0, '0'):
        details.append(f"level {level}")
    if gender:
        details.append(str(gender))
    if race:
        details.append(str(race))
    if class_name:
        details.append(str(class_name))
    avatar = ' '.join(details) or 'WoW character'

    if is_roleplay(mode):
        return f"You are {name}, a {avatar} in World of Warcraft."
    return (
        f"You are {name}, a person playing a {avatar} "
        "character in World of Warcraft."
    )


def build_player_identity_from_dict(
    bot: dict,
    mode: str,
    include_level: bool = True,
) -> str:
    """Build the mode-aware identity for a standard bot dictionary."""
    return build_player_identity(
        bot.get('name', 'Unknown'),
        bot.get('race', ''),
        bot.get('class', ''),
        bot.get('level') if include_level else None,
        bot.get('gender', ''),
        mode,
    )


def build_player_prompt_header(
    name: str,
    race: str = '',
    class_name: str = '',
    level=None,
    gender: str = '',
    mode: str = 'normal',
    channel: str = 'party',
) -> str:
    """Build a playerbot identity followed by its channel voice contract."""
    return (
        build_player_identity(
            name, race, class_name, level, gender, mode
        )
        + "\n"
        + build_player_chat_guidance(mode, channel)
    )


def build_player_prompt_header_from_dict(
    bot: dict,
    mode: str,
    channel: str = 'party',
) -> str:
    """Build a standard playerbot prompt header from a bot dictionary."""
    return build_player_prompt_header(
        bot.get('name', 'Unknown'),
        bot.get('race', ''),
        bot.get('class', ''),
        bot.get('level'),
        bot.get('gender', ''),
        mode,
        channel,
    )


def build_player_chat_guidance(
    mode: str,
    channel: str = 'party',
) -> str:
    """Return the shared voice contract for playerbot chat prompts."""
    if is_roleplay(mode):
        return (
            "CHAT MODE: ROLEPLAY. Speak as the character living in Azeroth. "
            "Stay in character and avoid game-system or real-world talk."
        )

    channel_note = {
        'general': (
            "Use ordinary zone chat: questions, help, progress, opinions, "
            "complaints, or loose banter."
        ),
        'guild': (
            "Use familiar guild chat between players who may be in "
            "different zones."
        ),
        'battleground': (
            "Use concise battleground team chat: tactical, reactive, and "
            "competitive without becoming hostile."
        ),
        'raid': (
            "Use concise raid chat: practical, reactive, and focused on the "
            "run when appropriate."
        ),
        'say': (
            "Use casual player /say near other characters and NPCs."
        ),
    }.get(
        channel,
        "Use casual party chat between people playing together.",
    )
    return (
        "CHAT MODE: NORMAL. Speak as a person playing WoW, not as an "
        "inhabitant of Azeroth. Race, class, level, gear, deaths, travel, "
        "weather, and locations describe the character or game; never claim "
        "to physically feel the game world's wounds, armor, weather, hunger, "
        "smells, or fatigue. "
        "If any other prompt data contains mystical, devotional, heroic, "
        "racial, or in-world personality and tone labels, treat it as legacy "
        "character metadata and do not express it. "
        f"{channel_note} Friendly and respectful is the default. Different "
        "personalities may be quiet, polite, helpful, dry, playful, blunt, "
        "or occasionally mildly salty or immature, but never force rudeness. "
        "Use familiar WoW shorthand only when natural. Avoid slurs, personal "
        "abuse, l33tspeak, meme spam, current social-media slang, and "
        "customer-service or motivational-assistant phrasing. Natural "
        "kindness, patience, and complete sentences are welcome."
    )


def build_npc_chat_guidance() -> str:
    """Return the mode-invariant voice contract for actual NPCs."""
    return (
        "SPEAKER TYPE: NPC. Speak as an inhabitant of Azeroth. Stay grounded "
        "and lore-friendly; never mention players, screens, UI, game systems, "
        "or the real world."
    )
