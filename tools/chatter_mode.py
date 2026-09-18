"""Canonical prompt rules for playerbot chatter modes.

Playerbots follow ``LLMChatter.ChatterMode``. Actual NPCs always remain
in-world, including when they share a proximity scene with playerbots.

The configured mode is a *default*, not a verdict. A server that wants
in-character zone chat still wants plain, focused party chat once the
group zones into a dungeon, so :func:`resolve_chatter_mode` layers a
per-channel override and an instanced-content gate on top of the global
value. Call it instead of reading ``LLMChatter.ChatterMode`` directly
wherever the channel is known.
"""

import hashlib
import random

from chatter_constants import INSTANCE_MAP_IDS, RAID_MAP_IDS


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


# A resolved mode carries both halves of the voice contract: who is
# speaking, and how focused they are.
#
#   'normal'     player voice, social register
#   'instanced'  player voice, working register -- a dungeon, raid,
#                battleground, or arena, where chat is part of the run
#   'roleplay'   in-character voice
#
# Everything downstream branches on is_roleplay(), so 'instanced'
# behaves exactly like 'normal' except where the register matters.
# Never compare a mode against 'normal' directly; use is_roleplay().
CHATTER_MODES = ('normal', 'instanced', 'roleplay')


def normalize_chatter_mode(mode: str) -> str:
    """Return a supported playerbot chatter mode."""
    value = str(mode or '').strip().lower()
    return value if value in CHATTER_MODES else 'normal'


def is_roleplay(mode: str) -> bool:
    """Return whether playerbots should speak in character."""
    return normalize_chatter_mode(mode) == 'roleplay'


def is_instanced_register(mode: str) -> bool:
    """Return whether chat should use the tighter instanced register."""
    return normalize_chatter_mode(mode) == 'instanced'


# Channels whose chat is a shared task while the group is in instanced
# content. Roleplay in zone or guild chat costs nobody anything; roleplay
# in the middle of a dungeon pull buries the call that mattered.
GROUP_TASK_CHANNELS = ('party', 'raid', 'battleground')

# Per-channel overrides for the global LLMChatter.ChatterMode. An empty
# value (or 'inherit') falls back to the global setting, so existing
# configs keep behaving exactly as they did.
CHANNEL_MODE_KEYS = {
    'party': 'LLMChatter.ChatterMode.Party',
    'raid': 'LLMChatter.ChatterMode.Raid',
    'battleground': 'LLMChatter.ChatterMode.Battleground',
    'guild': 'LLMChatter.ChatterMode.Guild',
    'general': 'LLMChatter.ChatterMode.General',
    'say': 'LLMChatter.ChatterMode.Say',
    # /yell is player speech in the world, same register as /say
    'yell': 'LLMChatter.ChatterMode.Say',
}

_INHERIT_VALUES = ('', 'inherit', 'default', 'global')


def is_instance_map(map_id) -> bool:
    """Return whether a map ID is a dungeon, raid, battleground, or arena."""
    try:
        return int(map_id or 0) in INSTANCE_MAP_IDS
    except (TypeError, ValueError):
        return False


def is_raid_map(map_id) -> bool:
    """Return whether a map ID is a raid instance."""
    try:
        return int(map_id or 0) in RAID_MAP_IDS
    except (TypeError, ValueError):
        return False


def in_instanced_content(
    map_id=0,
    is_raid: bool = False,
    is_dungeon: bool = False,
    is_battleground: bool = False,
) -> bool:
    """Return whether the speaker is inside instanced group content.

    Server-side flags win when an event carries them; otherwise the map ID
    is enough, because every instanced map in the supported expansions is
    a known ID.
    """
    if is_raid or is_dungeon or is_battleground:
        return True
    return is_instance_map(map_id)


def _configured_mode(config: dict, channel: str):
    """Return (mode, explicit) for a channel, before any gating.

    ``explicit`` is True when this channel names its own mode. An admin
    who writes ``LLMChatter.ChatterMode.Raid = roleplay`` means it, so
    the instance gate leaves that channel alone.
    """
    key = CHANNEL_MODE_KEYS.get(str(channel or '').strip().lower())
    value = ''
    if key:
        value = str(config.get(key, '') or '').strip().lower()
    if value not in _INHERIT_VALUES:
        return value, True
    return str(
        config.get('LLMChatter.ChatterMode', 'normal') or 'normal'
    ).strip().lower(), False


def _resolve_mixed(config: dict, roll_seed: str = '') -> str:
    """Roll a 'mixed' configuration into a concrete mode.

    With a seed the roll is stable, so one bot keeps one voice for the
    length of a conversation instead of flipping between messages.
    """
    try:
        chance = float(config.get('LLMChatter.MixedRoleplayChance', 0.5))
    except (TypeError, ValueError):
        chance = 0.5
    chance = min(1.0, max(0.0, chance))

    seed = str(roll_seed or '').strip()
    if seed:
        digest = hashlib.sha256(seed.casefold().encode('utf-8')).digest()
        roll = int.from_bytes(digest[:8], 'big') / float(1 << 64)
    else:
        roll = random.random()
    return 'roleplay' if roll < chance else 'normal'


def _is_enabled(config: dict, key: str, default: str = '1') -> bool:
    value = str((config or {}).get(key, default)).strip().lower()
    return value not in ('0', 'false', 'no', 'off')


def suppress_roleplay_in_instances(config: dict) -> bool:
    """Return whether instanced group content forces normal voice."""
    return _is_enabled(
        config, 'LLMChatter.Roleplay.SuppressInInstances'
    )


def tactical_chat_in_instances(config: dict) -> bool:
    """Return whether instanced group content tightens the register."""
    return _is_enabled(config, 'LLMChatter.Instance.TacticalChat')


def resolve_chatter_mode(
    config: dict,
    channel: str = 'party',
    map_id=0,
    is_raid: bool = False,
    is_dungeon: bool = False,
    is_battleground: bool = False,
    roll_seed: str = '',
) -> str:
    """Return the chatter mode for one message, given where it is spoken.

    Three layers, applied in order:

    1. ``LLMChatter.ChatterMode.<Channel>`` if set, else the global
       ``LLMChatter.ChatterMode``. A channel that names its own mode is
       taken at its word and skips step 3's roleplay gate.
    2. ``mixed`` is rolled into normal or roleplay, stably when a
       ``roll_seed`` (bot name, conversation key) is supplied.
    3. Inside a dungeon, raid, battleground, or arena, on a group task
       channel: roleplay drops to the player voice unless
       ``LLMChatter.Roleplay.SuppressInInstances`` is 0, and the player
       voice tightens to the 'instanced' register unless
       ``LLMChatter.Instance.TacticalChat`` is 0.
    """
    if not config:
        return 'normal'

    mode, explicit = _configured_mode(config, channel)
    if mode == 'mixed':
        mode = _resolve_mixed(config, roll_seed)
    mode = normalize_chatter_mode(mode)

    channel_key = str(channel or '').strip().lower()
    if channel_key not in GROUP_TASK_CHANNELS:
        return mode
    if not in_instanced_content(
        map_id, is_raid, is_dungeon, is_battleground
    ):
        return mode

    if mode == 'roleplay':
        if explicit or not suppress_roleplay_in_instances(config):
            return mode
        mode = 'normal'
    if mode == 'normal' and tactical_chat_in_instances(config):
        return 'instanced'
    return mode


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
    gear: str = '',
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
        identity = (
            f"You are {name}, a {avatar} in World of Warcraft."
        )
    else:
        identity = (
            f"You are {name}, a person playing a {avatar} "
            "character in World of Warcraft."
        )

    gear = (gear or '').strip()
    return f"{identity} {gear}" if gear else identity


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
        bot.get('gear', ''),
    )


def build_player_prompt_header(
    name: str,
    race: str = '',
    class_name: str = '',
    level=None,
    gender: str = '',
    mode: str = 'normal',
    channel: str = 'party',
    gear: str = '',
    instanced: bool = False,
) -> str:
    """Build a playerbot identity followed by its channel voice contract."""
    return (
        build_player_identity(
            name, race, class_name, level, gender, mode,
            gear,
        )
        + "\n"
        + build_player_chat_guidance(mode, channel, instanced)
    )


def build_player_prompt_header_from_dict(
    bot: dict,
    mode: str,
    channel: str = 'party',
    instanced: bool = False,
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
        bot.get('gear', ''),
        instanced,
    )


def build_player_chat_guidance(
    mode: str,
    channel: str = 'party',
    instanced: bool = False,
) -> str:
    """Return the shared voice contract for playerbot chat prompts.

    ``instanced`` marks group content — a dungeon, raid, battleground, or
    arena — where party chat is a working channel rather than a social
    one, and the voice should tighten accordingly.
    """
    if is_roleplay(mode):
        return (
            "CHAT MODE: ROLEPLAY. Speak as the character living in Azeroth. "
            "Stay in character and avoid game-system or real-world talk."
        )

    if (instanced or is_instanced_register(mode)) and channel == 'party':
        channel_note = (
            "Use concise dungeon party chat: practical, reactive, and "
            "focused on the run. Keep idle chatter short and infrequent "
            "while the group is working through the instance."
        )
        return _build_normal_guidance(channel_note)

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
    return _build_normal_guidance(channel_note)


def _build_normal_guidance(channel_note: str) -> str:
    """Return the normal-mode voice contract around a channel note."""
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
