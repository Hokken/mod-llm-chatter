"""Guild chatter event handlers.

Ambient guild-channel banter: online guild members occasionally
exchange short, in-character lines in guild chat. Driven by
``CheckGuildIdleChatter`` in LLMChatterWorld.cpp, gated by
``LLMChatter.GuildChatter.*`` config. Mirrors the structure of the
raid idle-morale and proximity handlers.
"""

import logging
import random
import re
from typing import Dict, Optional

from chatter_db import insert_chat_message
from chatter_llm import call_llm
from chatter_shared import (
    append_json_instruction,
    get_class_name,
    get_gender_label,
    get_race_name,
    get_zone_name,
    get_zone_flavor,
    parse_extra_data,
)
from chatter_text import (
    cleanup_message,
    parse_single_response,
    strip_speaker_prefix,
)

logger = logging.getLogger(__name__)


def _mark_event(db, event_id: int, status: str) -> None:
    cursor = db.cursor()
    cursor.execute(
        "UPDATE llm_chatter_events SET status = %s "
        "WHERE id = %s",
        (status, event_id),
    )
    db.commit()


def _query_speaker(db, bot_guid: int) -> Dict[str, object]:
    """Load a speaker's class/race/level/gender plus their
    stored personality (traits/tone/backstory) from the
    bot-identity table. Returns {} if the bot is unknown."""
    if not bot_guid:
        return {}

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT class, race, gender, level "
            "FROM characters WHERE guid = %s",
            (bot_guid,),
        )
        base = cursor.fetchone()
        if not base:
            return {}

        cursor.execute(
            "SELECT trait1, trait2, trait3, tone, "
            "       backstory "
            "FROM llm_bot_identities "
            "WHERE bot_guid = %s LIMIT 1",
            (bot_guid,),
        )
        ident = cursor.fetchone() or {}

        traits = [
            trait for trait in (
                ident.get('trait1'),
                ident.get('trait2'),
                ident.get('trait3'),
            )
            if trait
        ]
        return {
            'class': get_class_name(
                int(base.get('class', 0) or 0)
            ),
            'race': get_race_name(
                int(base.get('race', 0) or 0)
            ),
            'gender': get_gender_label(
                int(base.get('gender', 0) or 0)
            ),
            'level': int(base.get('level', 0) or 0),
            'traits': traits,
            'tone': ident.get('tone') or '',
            'backstory': ident.get('backstory') or '',
        }
    except Exception:
        logger.error(
            "query guild speaker failed",
            exc_info=True,
        )
        return {}


import random
from chatter_constants import GUILD_CHAT_TOPICS, GUILD_CHAT_TOPICS_RP


# Roadmap #5 / review #1: deterministic length buckets. The model is unreliable
# at obeying character limits (observed compliance was poor), so we pick a bucket,
# hint it in the prompt, AND hard-cap the parsed output to the bucket's max after
# the fact. Hint + enforcement are kept in lockstep here.
GUILD_LENGTH_BUCKETS = [
    # (key, prompt hint, hard max chars, weight)
    ("very_short", "very short — just a few words", 48, 20),
    ("short", "short — one brief line", 90, 40),
    ("medium", "medium — a single sentence", 145, 30),
    ("long", "a full sentence", 190, 10),
]


def _pick_guild_length():
    """Return (key, hint, max_chars) for one weighted length bucket."""
    bucket = random.choices(
        GUILD_LENGTH_BUCKETS,
        weights=[b[3] for b in GUILD_LENGTH_BUCKETS],
    )[0]
    return bucket[0], bucket[1], bucket[2]


def _truncate_to(message: str, max_chars: int) -> str:
    """Hard-cap a message to max_chars, avoiding a mid-word split WHEN POSSIBLE:
    prefers a sentence boundary, then a word boundary, and only falls back to a
    hard cut for unbroken text (e.g. a single very long token). Never emits an
    ellipsis so the result stays strictly within the bucket's char budget."""
    message = message.strip()
    if len(message) <= max_chars:
        return message
    window = message[:max_chars]
    # 1) end on sentence punctuation if one sits in the back half of the window
    best = -1
    for p in ('. ', '! ', '? ', '; '):
        idx = window.rfind(p)
        if idx > best:
            best = idx
    if best >= max_chars * 0.5:
        return window[:best + 1].strip()
    # 2) otherwise cut on the last word boundary
    idx = window.rfind(' ')
    if idx >= max_chars * 0.4:
        return window[:idx].rstrip(' ,;:-').strip()
    # 3) last resort: hard cut
    return window.rstrip()


# Review #4: never insult your own faction. Derive Alliance/Horde from race so
# the prompt can pass the speaker's side and forbid self-faction jabs.
_ALLIANCE_RACES = {"Human", "Dwarf", "Night Elf", "Gnome", "Draenei"}
_HORDE_RACES = {"Orc", "Undead", "Scourge", "Tauren", "Troll", "Blood Elf"}


def _faction_of(race_name: str) -> str:
    if race_name in _ALLIANCE_RACES:
        return "Alliance"
    if race_name in _HORDE_RACES:
        return "Horde"
    return ""


def _speaker_faction(speaker: Dict) -> str:
    """Resolve the speaker's faction from its race (name or id), defensively."""
    race = speaker.get('race')
    candidates = []
    if isinstance(race, str):
        candidates.append(race)
    try:
        candidates.append(get_race_name(race))
    except Exception:
        pass
    for c in candidates:
        fac = _faction_of((c or '').strip())
        if fac:
            return fac
    return ""


# Review #2 (strict): guild lines are SPOKEN text only. The message-only schema +
# cleanup_message() handle the common cases, but the model can still embed marked
# RP artifacts INSIDE the message field. Deterministically strip them so we never
# rely on prompt pressure alone: /me|/e|/emote prefixes, *narrator* fragments
# (leading/trailing/inline), <emote>..</emote>-style tags, and stray backticks.
def _strip_rp_artifacts(message: str) -> str:
    if not message:
        return ""
    s = message
    # slash-emote command prefixes (/me, /e, /emote)
    s = re.sub(r'^\s*/(?:me|e|emote)\b[:,]?\s*', '', s, flags=re.IGNORECASE)
    # angle-bracket emote/action tags and any stray short html-ish tag
    s = re.sub(r'</?\s*(?:emote|action|i|em|rp|me)\s*>', ' ',
               s, flags=re.IGNORECASE)
    s = re.sub(r'<[^<>]{0,40}>', ' ', s)
    # *...* narrator fragments anywhere, then any leftover lone asterisks
    s = re.sub(r'\*[^*]{1,80}\*', ' ', s)
    s = s.replace('*', '')
    # explicit "emote:"/"action:" leads
    s = re.sub(r'^\s*(?:emote|action)\s*:\s*', '', s, flags=re.IGNORECASE)
    # stray fences/backticks
    s = s.replace('```', '').replace('`', '')
    # collapse whitespace opened up by removals
    s = re.sub(r'\s{2,}', ' ', s).strip(' ,;:-\t')
    return s.strip()


# Review #6: never put "level N" in the guild prompt — handing the model the exact
# forbidden mechanic ("levels") undermines the jargon ban. Translate level into
# non-mechanical flavor instead.
def _level_flavor(level) -> str:
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        return ""
    if lvl <= 0:
        return ""
    if lvl < 20:
        return "a young adventurer"
    if lvl < 60:
        return "a seasoned traveler"
    if lvl < 80:
        return "a hardened campaigner"
    return "a battle-hardened veteran"


def _resolve_name(name_fn, val, default: str) -> str:
    """Resolve a race/class to a display name whether it's already a name or an id."""
    if isinstance(val, str) and val and not val.isdigit():
        return val
    try:
        r = name_fn(val)
        if r:
            return r
    except Exception:
        pass
    return default


def _guild_identity(speaker_name: str, speaker: Dict) -> str:
    """Non-mechanical identity line for guild chat (no 'level N')."""
    race = _resolve_name(get_race_name, speaker.get('race'), 'wanderer')
    klass = _resolve_name(get_class_name, speaker.get('class'), 'adventurer')
    flavor = _level_flavor(speaker.get('level'))
    base = f"You are {speaker_name}, a {race} {klass} of Azeroth"
    if flavor:
        base += f" — {flavor}"
    return base + "."


def _build_guild_prompt(
    speaker_name: str,
    speaker: Dict,
    guild_name: str,
    guildmates: str,
    config: Optional[Dict] = None,
    zone_id: int = 0,
    length_hint: str = "short — one brief line",
    topic: str = "",
) -> str:
    lines = [_guild_identity(speaker_name, speaker)]
    lines.append(
        f"You are a member of the guild "
        f"\"{guild_name}\"."
    )

    traits = speaker.get('traits') or []
    if traits:
        lines.append(
            "Personality: " + ", ".join(traits) + "."
        )
    if speaker.get('tone'):
        lines.append(f"Tone: {speaker['tone']}.")
    if speaker.get('backstory'):
        lines.append(
            f"Background: {speaker['backstory']}"
        )
    if guildmates:
        lines.append(
            f"Guildmates currently online: "
            f"{guildmates}."
        )

    # Review #4: faction awareness — never insult your own side.
    faction = _speaker_faction(speaker)
    if faction:
        lines.append(
            f"You fight for the {faction}. Never insult or mock "
            f"the {faction} — they are your own people. If you "
            "speak of rivalry, it is only toward the opposing "
            "faction."
        )

    if zone_id:
        zone = get_zone_name(zone_id)
        if zone:
            # Review #5: prefer the curated, lore-accurate zone flavor as
            # POSITIVE context so the model draws on real local color rather
            # than inventing NPCs/towns/factions that may not exist there.
            flavor = get_zone_flavor(zone_id)
            if flavor:
                lines.append(
                    f"You are currently in {zone}. Local color you may "
                    f"draw on: {flavor} Use only this for specifics; do "
                    "NOT invent other local NPCs, towns, factions, or events."
                )
            else:
                lines.append(
                    f"You are currently in {zone}. You may react to "
                    "the land itself (its weather, danger, mood) but "
                    "do NOT invent specific local NPCs, towns, or "
                    "events you cannot be sure exist."
                )
    if not topic:
        topic = random.choice(GUILD_CHAT_TOPICS_RP)
    lines.append(
        "Topic idea (optional - only use it if it fits "
        f"naturally, do not force it): {topic}."
    )
    # Review #3: keep content within the speaker's OWN class/race idiom — the
    # model otherwise borrows another class's fantasy (a warlock invoking
    # ancestors, a death knight using fel, etc.).
    lines.append(
        "Speak only in the idiom that fits your own race and class. Do NOT "
        "borrow another class's powers or imagery — do not invoke spirits, "
        "ancestors, the Light, the elements, nature, or fel unless that "
        "genuinely belongs to who you are."
    )
    lines.append(
        "Stay fully in character — you ARE this person in Azeroth, "
        "speaking to your guild. No fourth-wall breaks and no "
        "out-of-character or game-mechanic talk. NEVER use words "
        "like grinding, pulls, DPS, specs, talents, loot, mobs, "
        "XP, levels, rotations, addons, or any reference to the "
        "player behind the screen. Speak of foes, the road, your "
        "craft and your calling — not game systems."
    )
    lines.append(
        "Write ONE casual, in-character line for guild chat, the "
        "way this person would actually speak. "
        f"Length: {length_hint}. No quotation marks, no name "
        "prefix, no roleplay asterisks, no emotes or actions — "
        "just the spoken line."
    )

    # Review #2: message-only JSON. Do not request emote/action
    # fields so they cannot leak into the displayed line.
    return append_json_instruction(
        "\n".join(lines) + "\n",
        allow_action=False,
        skip_emote=True,
    )


def process_guild_idle_chatter_event(
    db, client, config, event
):
    """Handle guild_idle_chatter — one online guild member
    posts a short in-character line to guild chat."""
    event_id = event['id']
    extra = parse_extra_data(
        event.get('extra_data'),
        event_id, 'guild_idle_chatter')

    if not extra:
        _mark_event(db, event_id, 'skipped')
        return False

    speaker_guid = int(
        event.get('subject_guid', 0) or 0
    )
    speaker_name = (
        event.get('subject_name')
        or extra.get('speaker_name')
        or ''
    )
    guild_name = extra.get('guild_name') or 'the guild'
    guildmates = extra.get('guildmates') or ''

    speaker = _query_speaker(db, speaker_guid)
    if not speaker or not speaker_name:
        _mark_event(db, event_id, 'skipped')
        return False

    zone_id = int(extra.get('zone_id', 0) or 0)
    length_key, length_hint, length_max = _pick_guild_length()
    topic = random.choice(GUILD_CHAT_TOPICS_RP)
    prompt = _build_guild_prompt(
        speaker_name, speaker, guild_name,
        guildmates, config, zone_id=zone_id,
        length_hint=length_hint, topic=topic,
    )

    max_tokens = int(config.get(
        'LLMChatter.GuildChatter.MaxTokens', 200
    ))
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"guild:{speaker_name}",
        label='guild_idle_chatter',
    )
    if not response:
        _mark_event(db, event_id, 'skipped')
        return False

    parsed = parse_single_response(response)
    message = strip_speaker_prefix(
        parsed.get('message', ''), speaker_name
    )
    # Review #2: message-only — drop any emote/action the model may have
    # leaked; never prepend a narrator action to guild lines.
    message = cleanup_message(message)
    # Review #2 (strict): deterministically strip marked RP artifacts that can
    # still ride inside the message field (/me, *action*, <emote>, fences).
    message = _strip_rp_artifacts(message)
    if not message:
        _mark_event(db, event_id, 'skipped')
        return False
    # Review #1: deterministic hard cap to the chosen length bucket
    # (the model is unreliable at obeying the in-prompt limit).
    message = _truncate_to(message, length_max)
    # Review #7: surface the generation controls for later verification.
    logger.info(
        "guild_idle_chatter speaker=%s bucket=%s max_chars=%d "
        "faction=%s zone_id=%d topic=%r out_len=%d",
        speaker_name, length_key, length_max,
        _speaker_faction(speaker) or "-", zone_id, topic, len(message),
    )

    insert_chat_message(
        db,
        bot_guid=speaker_guid,
        bot_name=speaker_name,
        message=message,
        channel='guild',
        owner_subsystem='guild',
        event_id=event_id,
    )

    _mark_event(db, event_id, 'completed')
    return True
