"""Chatter Persona - who is speaking and how they feel.

This module owns bot persona resolution and rendering for every
chatter channel (party, guild, General):

- identity: traits, tone and (roleplay only) backstory, resolved from
  the bot's active group row, then the persistent identity row, then
  a deterministic fallback seeded from the bot's name (else GUID)
- mood: the bot's real event mood from ``chatter_group_state``, the
  same in every channel, and never invented
- rendering: the shared persona block and conversation cast, which
  state that mood, topic, twists and spices colour a bot's voice but
  never replace it

Prompt builders must not roll their own tone, traits or mood. They
take a ``Persona`` (or a bot dict carrying one), or fall back to
``fallback_tone`` for a missing stored tone.
"""

import dataclasses
import hashlib
import logging
import random
from typing import Iterable, List, Optional, Sequence

from chatter_constants import PERSONALITY_TRAITS
from chatter_group_state import get_bot_mood_label_by_guid
from chatter_mode import is_roleplay, resolve_player_personality

logger = logging.getLogger(__name__)


# Trait categories that describe *how* someone talks. The fallback
# persona builds its tone from these, and takes its traits from the
# remaining categories so the tone adds information instead of
# repeating a trait.
_TONE_CATEGORIES = ('demeanor', 'humor')

PERSONA_PRIORITY_RULE = (
    "Personality and tone are fixed: they define how {who} speak. "
    "Mood, topic, optional angles and background feelings only "
    "colour that voice; never let them change who {who} are. "
    "Traits shape how {who} see and say things; they are not "
    "subjects to name or repeat in every line."
)

CONVERSATION_EMOTION_RULE = (
    "Emotions shift only in reaction to what is said, and always "
    "through each speaker's own personality."
)


@dataclasses.dataclass(frozen=True)
class Persona:
    """A bot's identity plus its current real mood.

    ``mood`` is empty when the bot has no live event mood (or is
    neutral); renderers then emit no mood line at all.
    """

    name: str
    traits: tuple
    tone: str
    backstory: str = ''
    mood: str = ''
    source: str = 'fallback'


# ------------------------------------------------------------------
# Deterministic fallback identity
# ------------------------------------------------------------------
def _seed_for(bot_guid, bot_name) -> int:
    """Stable cross-process seed from the bot's name, else GUID.

    The name is preferred because every prompt path has it, while
    some (pre-cache, nearby objects) have no GUID. Character names
    are unique, so the seed still identifies one bot.
    """
    name = str(bot_name or '').strip().casefold()
    if name:
        key = f"name:{name}"
    else:
        try:
            key = f"guid:{int(bot_guid or 0)}"
        except (TypeError, ValueError):
            key = "guid:0"
    digest = hashlib.sha256(
        f"persona:{key}".encode('utf-8')
    ).digest()
    return int.from_bytes(digest[:8], 'big')


def fallback_identity(bot_guid, bot_name, mode) -> tuple:
    """Return ``(traits, tone)`` for a bot with no stored identity.

    The same bot always gets the same result (no ``random`` state is
    consumed). Normal mode uses the player-style profile that
    ``resolve_player_personality`` derives from the name.
    """
    if not is_roleplay(mode):
        traits, tone = resolve_player_personality(
            bot_name, mode=mode
        )
        return tuple(traits), tone

    rng = random.Random(_seed_for(bot_guid, bot_name))
    tone_parts = [
        rng.choice(PERSONALITY_TRAITS[cat])
        for cat in _TONE_CATEGORIES
        if PERSONALITY_TRAITS.get(cat)
    ]
    trait_categories = sorted(
        cat for cat in PERSONALITY_TRAITS
        if cat not in _TONE_CATEGORIES
    )
    chosen = rng.sample(trait_categories, 3)
    traits = tuple(
        rng.choice(PERSONALITY_TRAITS[cat]) for cat in chosen
    )
    tone = ' and '.join(tone_parts) if tone_parts else 'plain-spoken'
    return traits, tone


def fallback_tone(bot_guid, bot_name, mode) -> str:
    """Deterministic tone for a bot whose stored tone is missing."""
    return fallback_identity(bot_guid, bot_name, mode)[1]


# ------------------------------------------------------------------
# Mood
# ------------------------------------------------------------------
def resolve_mood(bot_guid) -> str:
    """Return the bot's live event mood, or '' for none/neutral.

    The same lookup serves party, guild and General, so a bot that
    just wiped in a party sounds gloomy everywhere. No mood is ever
    invented here.
    """
    try:
        guid = int(bot_guid or 0)
    except (TypeError, ValueError):
        return ''
    if not guid:
        return ''
    label = get_bot_mood_label_by_guid(guid)
    return '' if label == 'neutral' else label


# ------------------------------------------------------------------
# Resolution
# ------------------------------------------------------------------
def _clean_traits(traits: Optional[Iterable]) -> List[str]:
    return [
        str(t).strip() for t in (traits or [])
        if t and str(t).strip()
    ]


def persona_from_fields(
    bot_name: str,
    mode: str,
    bot_guid=0,
    traits: Optional[Sequence] = None,
    tone: Optional[str] = None,
    backstory: Optional[str] = None,
    source: str = 'group',
    with_mood: bool = True,
) -> Persona:
    """Build a persona from identity fields the caller already has.

    Enforces the mode boundary: normal mode always uses the
    player-style profile derived from the name, whatever traits,
    tone or backstory were stored. Roleplay fills any missing field
    from the deterministic fallback, never from a random roll.
    """
    mood = resolve_mood(bot_guid) if with_mood else ''
    if not is_roleplay(mode):
        player_traits, player_tone = resolve_player_personality(
            bot_name, mode=mode
        )
        return Persona(
            name=bot_name or '',
            traits=tuple(player_traits),
            tone=player_tone,
            mood=mood,
            source=source,
        )
    fb_traits, fb_tone = fallback_identity(bot_guid, bot_name, mode)
    clean = _clean_traits(traits)
    if not clean:
        source = 'fallback'
    return Persona(
        name=bot_name or '',
        traits=tuple(clean) if clean else fb_traits,
        tone=(tone or '').strip() or fb_tone,
        backstory=(backstory or '').strip(),
        mood=mood,
        source=source,
    )


_IDENTITY_COLUMNS = "trait1, trait2, trait3, tone, backstory"


def _query_identity(db, bot_guid, group_id) -> tuple:
    """Return ``(row, source)``: group row, then identity row.

    Without ``group_id`` the bot's most recently assigned active
    group row is used, so Guild and General see the same session
    identity as Party (a grouped bot may have no persistent
    identity row when memory is disabled).
    """
    cursor = db.cursor(dictionary=True)
    if group_id:
        cursor.execute(
            f"SELECT {_IDENTITY_COLUMNS} "
            "FROM llm_group_bot_traits "
            "WHERE group_id = %s AND bot_guid = %s",
            (group_id, bot_guid),
        )
    else:
        cursor.execute(
            f"SELECT {_IDENTITY_COLUMNS} "
            "FROM llm_group_bot_traits "
            "WHERE bot_guid = %s "
            "ORDER BY assigned_at DESC LIMIT 1",
            (bot_guid,),
        )
    row = cursor.fetchone()
    if row:
        return row, 'group'
    cursor.execute(
        f"SELECT {_IDENTITY_COLUMNS} "
        "FROM llm_bot_identities WHERE bot_guid = %s LIMIT 1",
        (bot_guid,),
    )
    row = cursor.fetchone()
    if row:
        return row, 'identity'
    return None, 'fallback'


def resolve_persona(
    db, bot_guid, bot_name, mode, group_id=None,
) -> Persona:
    """Resolve a bot's persona: group row > identity row > fallback.

    Resolved on every call (two indexed lookups at most), so a bot
    that joins or leaves a group is reflected immediately and the
    mood is always current.
    """
    try:
        guid = int(bot_guid or 0)
    except (TypeError, ValueError):
        guid = 0
    row, source = None, 'fallback'
    if db is not None and guid:
        try:
            row, source = _query_identity(db, guid, group_id)
        except Exception:
            logger.error(
                "persona lookup failed for %s", bot_name,
                exc_info=True,
            )
    row = row or {}
    return persona_from_fields(
        bot_name, mode, guid,
        traits=(
            row.get('trait1'), row.get('trait2'),
            row.get('trait3'),
        ),
        tone=row.get('tone'),
        backstory=row.get('backstory'),
        source=source,
    )


def persona_for_bot(bot: dict, mode: str) -> Persona:
    """Return the persona carried by a bot dict, or derive one.

    Callers with DB access attach ``bot['persona']``. Builders use
    this so a bot dict without one still gets a stable persona
    instead of a random tone.
    """
    persona = (bot or {}).get('persona')
    if isinstance(persona, Persona):
        return persona
    bot = bot or {}
    return persona_from_fields(
        bot.get('name', ''), mode, bot.get('guid', 0),
        traits=bot.get('traits'),
        tone=bot.get('tone'),
        backstory=bot.get('backstory'),
        source='group' if bot.get('traits') else 'fallback',
    )


def without_backstory(persona: Persona) -> Persona:
    """Copy of ``persona`` with the backstory dropped."""
    return dataclasses.replace(persona, backstory='')


def sample_channel_backstory(config, persona, channel):
    """Sample prompt context without modifying the saved profile."""
    from chatter_identity import config_int
    from chatter_shared import get_chatter_mode
    mode = get_chatter_mode(config)
    chance = config_int(
        config, f'LLMChatter.Backstory.{channel.title()}Chance',
        25, 0, 100,
    )
    enabled = config_int(config, 'LLMChatter.Backstory.Enable', 1)
    if (not is_roleplay(mode) or not enabled or not persona.backstory
            or chance == 0):
        return without_backstory(persona)
    if chance < 100 and random.randint(1, 100) > chance:
        return without_backstory(persona)
    return persona


# ------------------------------------------------------------------
# Rendering
# ------------------------------------------------------------------
def format_mood_line(mood: str, subject: str = 'you') -> str:
    """Render a mood as colour on the personality, never a swap."""
    if not mood:
        return ''
    if subject == 'you':
        return (
            f"Current mood: {mood} (from recent events), expressed "
            f"the way your personality naturally would"
        )
    return (
        f"current mood {mood} (from recent events), "
        f"shown through their personality"
    )


def format_backstory_block(backstory: str, mode: str) -> str:
    """Render a speaker's backstory (roleplay mode only).

    The single wording shared by the persona block, party event
    reactions and replies to the player.
    """
    text = (backstory or '').strip()
    if not text or not is_roleplay(mode):
        return ''
    return (
        "<backstory>\n"
        f"Your history: {text}\n"
        "Draw from this background naturally if it fits "
        "the moment -- don't force it.\n"
        "</backstory>"
    )


def party_reaction_backstory(config, backstory, mode) -> str:
    """Backstory for a party reaction or reply, or '' when gated.

    Roleplay only, and only when LLMChatter.Backstory.Enable is on
    and the LLMChatter.Backstory.PartyReactionChance roll passes.
    """
    text = (backstory or '').strip()
    if not text or not is_roleplay(mode):
        return ''
    config = config or {}
    try:
        enabled = int(config.get('LLMChatter.Backstory.Enable', 1))
        chance = int(config.get(
            'LLMChatter.Backstory.PartyReactionChance', 50
        ))
    except (TypeError, ValueError):
        logger.error("Invalid Backstory party reaction settings")
        return ''
    chance = max(0, min(chance, 100))
    if not enabled or chance <= 0:
        return ''
    if chance < 100 and random.randint(1, 100) > chance:
        return ''
    return text


def build_persona_block(
    persona: Persona, mode: str, include_rule: bool = True,
) -> str:
    """Render a single speaker's persona as prompt lines."""
    lines = []
    if persona.traits:
        lines.append(
            f"Your personality: {', '.join(persona.traits)}"
        )
    if persona.tone:
        lines.append(f"Your tone: {persona.tone}")
    backstory_block = format_backstory_block(persona.backstory, mode)
    if backstory_block:
        lines.append(backstory_block)
    mood_line = format_mood_line(persona.mood)
    if mood_line:
        lines.append(mood_line)
    if include_rule:
        lines.append(PERSONA_PRIORITY_RULE.format(who='you'))
    return '\n'.join(lines)


def build_cast_lines(
    personas: Sequence[Persona], mode: str,
    include_rule: bool = True,
) -> List[str]:
    """Render every speaker's persona for a multi-bot prompt."""
    lines = []
    for p in personas:
        bits = []
        if p.traits:
            bits.append(f"personality: {', '.join(p.traits)}")
        if p.tone:
            bits.append(f"tone: {p.tone}")
        mood_line = format_mood_line(p.mood, subject='them')
        if mood_line:
            bits.append(mood_line)
        if bits:
            lines.append(f"  {p.name} — {'; '.join(bits)}")
    if is_roleplay(mode):
        bs_lines = [
            f"  {p.name}: {p.backstory}"
            for p in personas if p.backstory
        ]
        if bs_lines:
            lines.append(
                "<backstories>\n"
                + "\n".join(bs_lines)
                + "\nDraw from these backgrounds naturally if they "
                "fit the moment -- don't force them.\n"
                "</backstories>"
            )
    if lines:
        lines.insert(0, "Speaker personalities:")
    if include_rule:
        lines.append(PERSONA_PRIORITY_RULE.format(who='the speakers'))
        lines.append(CONVERSATION_EMOTION_RULE)
    return lines
