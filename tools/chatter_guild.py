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
    get_chatter_mode,
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


from chatter_constants import GUILD_CHAT_TOPICS_RP
from chatter_general import _pick_length_hint


# Length control mirrors the General channel, which works well: we do NOT
# hard-cap or chop the model's output after the fact (the old per-bucket
# _truncate_to butchered lines mid-sentence). Instead we reuse General's
# _pick_length_hint(mode) — a char-range target plus a single generous
# "HARD LIMIT: Never exceed 150 characters total" stated in the prompt —
# and deliver the model's full, coherent sentence intact.


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
    length_hint: str = "",
    topic: str = "",
    faction: str = "",
    name_zone: bool = False,
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
    # PR #30 follow-up #1: prefer the authoritative C++ GetTeamId() value
    # (extra_data "team"); fall back to the Python race-derived faction.
    if not faction:
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
            # Guild chat reaches guildmates scattered across other zones who
            # cannot see where the speaker stands, so deictic references ("this
            # swamp", "here") read as nonsense to them. Whether to name the
            # location is decided by an RNG roll in the handler (name_zone) —
            # the model cannot be trusted to self-pace it. We deliberately give
            # NO phrasing examples here: examples make the model echo them into
            # repetitive patterns.
            flavor = get_zone_flavor(zone_id)
            if name_zone:
                # Review #5: curated lore flavor as POSITIVE context so the
                # model draws on real local color rather than inventing it.
                if flavor:
                    lines.append(
                        f"You are currently in {zone}. Local color you may "
                        f"draw on: {flavor} Use only this for specifics; do "
                        "NOT invent other local NPCs, towns, factions, or "
                        "events."
                    )
                else:
                    lines.append(
                        f"You are currently in {zone}. You may react to the "
                        "land itself (its weather, danger, mood) but do NOT "
                        "invent specific local NPCs, towns, or events you "
                        "cannot be sure exist."
                    )
                lines.append(
                    f"Most of your guildmates are far away in other lands and "
                    f"cannot see where you are, so name {zone} somewhere in "
                    "your line, woven in naturally, so they know where you "
                    "speak from."
                )
            else:
                # RNG said no: forbid referencing the location at all this
                # round so we never get a deictic line with no place name.
                lines.append(
                    "Most of your guildmates are far away and cannot see "
                    "where you are. Do NOT name or describe your current "
                    "location or immediate surroundings this time — speak of "
                    "other matters instead."
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
        "way this person would actually speak. No quotation marks, "
        "no name prefix, no roleplay asterisks, no emotes or "
        "actions — just the spoken line."
    )
    # Length control mirrors the General channel: a char-range target plus a
    # single generous HARD LIMIT, stated in the prompt. No post-parse cut.
    if length_hint:
        lines.append(length_hint)

    # Review #2: message-only JSON. Do not request emote/action
    # fields so they cannot leak into the displayed line.
    return append_json_instruction(
        "\n".join(lines) + "\n",
        allow_action=False,
        skip_emote=True,
        message_only=True,
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
    # Length control mirrors the General channel (which works well): reuse
    # its _pick_length_hint(mode) and let the prompt enforce length. No
    # post-parse truncation — the model's full sentence is delivered intact.
    length_hint = _pick_length_hint(get_chatter_mode(config))
    topic = random.choice(GUILD_CHAT_TOPICS_RP)
    # PR #30 follow-up #1: prefer the C++ GetTeamId() faction (extra_data
    # "team"); fall back to the Python race-derived faction.
    faction = extra.get('team') or _speaker_faction(speaker)
    # Zone-naming is decided here by RNG, not left to the model (it cannot
    # self-pace "occasionally"). On a hit the prompt asks the bot to name its
    # zone so scattered guildmates have context; on a miss it forbids any
    # location reference. Tunable via LLMChatter.GuildChatter.ZoneNameChance.
    zone_name_chance = int(config.get(
        'LLMChatter.GuildChatter.ZoneNameChance', 10))
    name_zone = random.randint(1, 100) <= zone_name_chance
    prompt = _build_guild_prompt(
        speaker_name, speaker, guild_name,
        guildmates, config, zone_id=zone_id,
        length_hint=length_hint, topic=topic, faction=faction,
        name_zone=name_zone,
    )

    max_tokens = int(config.get(
        'LLMChatter.GuildChatter.MaxTokens', 200
    ))
    # PR #30 follow-up #2: pass the generation controls as structured
    # metadata so they land as top-level fields in llm_requests.jsonl
    # (the monitoring pass can read them without parsing prompt text).
    metadata = {
        "guild_length_hint": length_hint.split("\n", 1)[0]
        .replace("Length: ", "").strip(),
        "guild_topic": topic,
        "guild_named_zone": name_zone,
        "guild_faction": faction,
        "guild_zone_id": zone_id,
        "guild_zone_name": get_zone_name(zone_id) or "",
        "guild_zone_flavor": get_zone_flavor(zone_id) or "",
    }
    response = call_llm(
        client, prompt, config,
        max_tokens_override=max_tokens,
        context=f"guild:{speaker_name}",
        label='guild_idle_chatter',
        metadata=metadata,
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
    # No post-parse truncation (mirrors the General channel): the prompt's
    # length hint + HARD LIMIT control length, and the full coherent line is
    # delivered as-is so messages are never cut mid-sentence.
    logger.info(
        "guild_idle_chatter speaker=%s "
        "faction=%s zone_id=%d topic=%r out_len=%d",
        speaker_name,
        faction or "-", zone_id, topic, len(message),
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
