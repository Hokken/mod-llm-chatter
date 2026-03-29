"""Group prompt builders extracted from chatter_group (N5)."""

import logging
import random

from chatter_shared import (
    get_zone_flavor,
    get_subzone_lore,
    get_dungeon_flavor,
    get_dungeon_bosses,
    build_race_class_context,
    build_race_class_context_parts,
    build_bot_state_context,
    append_json_instruction,
    append_conversation_json_instruction,
    build_anti_repetition_context,
    format_distance,
)
from chatter_prompts import (
    pick_random_tone,
    maybe_get_creative_twist,
    pick_personality_spices,
    generate_conversation_mood_sequence,
    generate_conversation_length_sequence,
)
from chatter_constants import (
    RACE_SPEECH_PROFILES,
    EMOTE_LIST_STR,
    LENGTH_HINTS,
    RP_LENGTH_HINTS,
    BG_MAP_NAMES,
    CLASS_ROLE_MAP,
)
from chatter_bg_prompts import BG_LORE

logger = logging.getLogger(__name__)

# Keep in sync from chatter_group.init_group_config
_spice_count = 2


def set_prompt_spice_count(value: int):
    """Set spice count used by moved prompt builders."""
    global _spice_count
    _spice_count = max(0, min(int(value), 5))


def _pick_length_hint(mode):
    """Pick a random length hint plus optional humor.

    The hint alone drives length — no competing
    'short/medium only' override that flattens variety.
    """
    is_rp = (mode == 'roleplay')
    pool = RP_LENGTH_HINTS if is_rp else LENGTH_HINTS
    hint = random.choice(pool)
    result = f"Length: {hint} — follow this closely."
    humor = _maybe_humor_hint(mode)
    if humor:
        result += f"\n{humor}"
    return result


def _maybe_humor_hint(mode):
    """RNG-gated humor encouragement for group
    prompts. 40% normal, 35% roleplay."""
    is_rp = (mode == 'roleplay')
    chance = 0.35 if is_rp else 0.40
    if random.random() < chance:
        if is_rp:
            return (
                "A touch of wry or dry humor "
                "fits here"
            )
        return "A touch of humor fits here"
    return None


def _append_bots_with_rp(parts, bots, traits_map, is_rp):
    """Append bot header lines + race/class RP context
    for a multi-bot list.

    Shared race content (worldview, lore) is emitted
    once per unique race. Shared class content (role
    perspective) is emitted once per unique class.
    Per-bot content (traits, class modifier, vocab)
    is emitted for every bot. Header and RP context
    are kept together per bot to preserve association.
    """
    shared_race_cache = {}
    if is_rp:
        race_counts = {}
        for bot in bots:
            r = bot.get('race', '')
            if r:
                race_counts[r] = (
                    race_counts.get(r, 0) + 1
                )
        for race, count in race_counts.items():
            _, sr, _ = build_race_class_context_parts(
                race, '', race_count=count
            )
            shared_race_cache[race] = sr
    seen_races = set()
    seen_classes = set()
    for bot in bots:
        t = traits_map.get(bot['name'], [])
        trait_str = ', '.join(t) if t else 'average'
        parts.append(
            f"{bot['name']} is a level "
            f"{bot['level']} {bot['race']} "
            f"{bot['class']} "
            f"(personality: {trait_str})"
        )
        if is_rp:
            race = bot.get('race', '')
            cls = bot.get('class', '')
            per_bot, _, shared_class = (
                build_race_class_context_parts(
                    race, cls
                )
            )
            if per_bot:
                parts.append(f"  {per_bot}")
            if race not in seen_races:
                sr = shared_race_cache.get(race, '')
                if sr:
                    parts.append(f"  {sr}")
                seen_races.add(race)
            resolved_role = (
                CLASS_ROLE_MAP.get(cls) or ''
            )
            cls_role_key = (cls, resolved_role)
            if cls_role_key not in seen_classes:
                if shared_class:
                    parts.append(f"  {shared_class}")
                seen_classes.add(cls_role_key)


def build_bot_greeting_prompt(
    bot, traits, mode,
    chat_history="", members=None,
    player_name="", group_size=0,
    allow_action=True,
    speaker_talent_context=None,
    memories=None,
    player_name_known=False,
    recall_memory=None,
    stored_tone=None,
    map_id=0,
    zone_id=0,
    bg_context=None,
):
    """Build the LLM prompt for a group greeting.

    Uses tone/twist system from ambient chatter
    for variety. RP mode includes race speech flavor.

    When memories are provided, switches to reunion
    mode: familiar tone, player name, optional
    specific memory reference.

    Args:
        bot: dict with name, class, race, level
        traits: list of 3 trait strings
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        members: list of group member names
        player_name: real player's name (from C++)
        group_size: total group members including
            this bot
        memories: list of sanitized memory strings
        player_name_known: True if bot has memories
            with this player
        recall_memory: specific memory to reference
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

        # Add race flavor examples if available
        profile = RACE_SPEECH_PROFILES.get(
            bot['race']
        )
        if profile:
            fw = profile.get('flavor_words', [])
            flavor = ', '.join(
                random.sample(fw, min(3, len(fw)))
            )
            if flavor:
                rp_context += (
                    f"\nRace flavor words you might "
                    f"use: {flavor}"
                )

    if is_rp:
        style_guide = (
            "Speak as your character would on "
            "an RP server. Stay in-character but "
            "keep it casual and grounded. No game "
            "terms or OOC references."
        )
    else:
        style_guide = (
            "Sound like a normal person chatting "
            "in a game. Casual but natural, "
            "no excessive slang or abbreviations."
        )

    # Location context: BG > dungeon > zone flavor
    location_context = ""
    if bg_context:
        bg_type_id = int(
            bg_context.get('bg_type_id', 0))
        lore = BG_LORE.get(bg_type_id, {})
        bg_name = lore.get(
            'name',
            bg_context.get('bg_type', 'a battleground'))
        bg_team = bg_context.get('team', '')
        faction = lore.get(
            f'{bg_team.lower()}_faction',
            bg_team,
        ) if bg_team else ''
        location_context = (
            f"\nYou are entering {bg_name}"
        )
        if faction:
            location_context += (
                f" as part of the {faction}"
                f" ({bg_team})"
            )
        location_context += "."
        bg_tone = lore.get('tone')
        if bg_tone:
            location_context += (
                f"\nBattleground feel: {bg_tone}"
            )
    else:
        dungeon_flav = get_dungeon_flavor(map_id)
        if dungeon_flav:
            location_context = (
                f"\nLocation: {dungeon_flav}"
            )
        else:
            zone_flav = get_zone_flavor(zone_id)
            if zone_flav:
                location_context = (
                    f"\nLocation: {zone_flav}"
                )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}"
        f"{rp_context}"
        f"{location_context}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"

    if members:
        others = [
            m for m in members
            if m != bot['name']
        ]
        if others:
            prompt += (
                f"\nParty members: "
                f"{', '.join(others)}\n"
            )
    if chat_history:
        prompt += f"{chat_history}\n"

    # Reunion mode: inject memories if available
    is_reunion = bool(
        memories and player_name_known
    )
    if is_reunion:
        from chatter_memory import (
            sanitize_memory_for_prompt,
        )
        sanitized = [
            sanitize_memory_for_prompt(m)
            for m in memories
        ]
        sanitized = [s for s in sanitized if s]
        if sanitized:
            mem_lines = '\n'.join(
                f"  - {m}" for m in sanitized
            )
            prompt += (
                f"\n<past_memories>\n"
                f"These are your past memories of "
                f"adventuring with {player_name}. "
                f"Use them as passive context only "
                f"— do not recite them.\n"
                f"{mem_lines}\n"
                f"</past_memories>\n"
            )
        if recall_memory:
            safe_recall = sanitize_memory_for_prompt(
                recall_memory
            )
            if safe_recall:
                prompt += (
                    f"\nYou vividly recall: "
                    f"\"{safe_recall}\" — "
                    f"reference this naturally.\n"
                )

    # If just player + this bot (group_size=2),
    # 80% chance to use the player's name
    use_player_name = (
        player_name
        and group_size == 2
        and random.random() < 0.8
    )
    # Reunion always uses the player's name
    if is_reunion and player_name:
        use_player_name = True

    # Greetings should be short — when inviting
    # multiple bots quickly, long messages flood chat
    # 70% short, 30% medium
    roll = random.random()
    if roll < 0.70:
        length_hint = "short (5-10 words)"
    else:
        length_hint = (
            "a short sentence (10-16 words)"
        )

    if is_reunion:
        prompt += (
            f"\nYou are rejoining a party with "
            f"{player_name}, someone you have "
            f"adventured with before. Greet them "
            f"as a familiar companion.\n"
            f"Length: {length_hint}\n"
            f"Length mode: short only "
            f"(keep it brief)\n\n"
            f"Your greeting should feel warm and "
            f"familiar — like seeing an old friend. "
            f"You may use their name, but vary "
            f"where it appears: mid-sentence, at the "
            f"end, or omit it entirely. Never start "
            f"your message with the player's name.\n\n"
            f"{style_guide}\n\n"
            f"Rules:\n"
            f"- One short sentence only\n"
            f"- No quotes around your message\n"
            f"- No emojis\n"
            f"- Don't mention your class or race\n"
            f"- Don't recite memories verbatim\n"
            f"- Do NOT begin with the player's name\n"
        )
    else:
        prompt += (
            f"\nYou just joined a party with a "
            f"real player. Say a greeting in "
            f"party chat.\n"
            f"Length: {length_hint}\n"
            f"Length mode: short only "
            f"(keep it brief)\n\n"
            f"Your greeting should reflect your "
            f"personality traits. For example:\n"
            f"- A 'friendly, eager' bot might say: "
            f"\"Hey! Ready to go whenever "
            f"you are\"\n"
            f"- A 'cynical, reserved' bot might "
            f"say: \"Sure, let's get this over "
            f"with\"\n"
            f"- A 'sarcastic, laid-back' bot "
            f"might say: \"Oh good, I was getting "
            f"bored\"\n\n"
            f"{style_guide}\n\n"
            f"Rules:\n"
            f"- One short sentence only\n"
            f"- No quotes around your message\n"
            f"- No emojis\n"
            f"- Don't mention your class or race\n"
        )

    if use_player_name:
        prompt += (
            f"- Address the player by name: "
            f"{player_name}"
        )
    else:
        prompt += (
            f"- Don't use the player's name"
        )

    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    return append_json_instruction(
        prompt, allow_action
    )


def build_bot_welcome_prompt(
    bot, traits, new_bot_name, mode,
    chat_history="", members=None,
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
):
    """Build prompt for an existing bot welcoming
    a new member to the group.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

        profile = RACE_SPEECH_PROFILES.get(
            bot['race']
        )
        if profile:
            fw = profile.get('flavor_words', [])
            flavor = ', '.join(
                random.sample(fw, min(3, len(fw)))
            )
            if flavor:
                rp_context += (
                    f"\nRace flavor words you might "
                    f"use: {flavor}"
                )

    if is_rp:
        style_guide = (
            "Speak as your character would on "
            "an RP server. Stay in-character but "
            "keep it casual and grounded. No game "
            "terms or OOC references."
        )
    else:
        style_guide = (
            "Sound like a normal person chatting "
            "in a game. Casual but natural, "
            "no excessive slang or abbreviations."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}"
        f"{rp_context}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"

    if members:
        others = [
            m for m in members
            if m != bot['name']
        ]
        if others:
            prompt += (
                f"\nParty members: "
                f"{', '.join(others)}\n"
            )
    if chat_history:
        prompt += f"{chat_history}\n"

    # Welcomes should be short — multiple bots may
    # welcome at once during rapid invites
    # 70% short, 30% medium
    roll = random.random()
    if roll < 0.70:
        wl_hint = "short (5-10 words)"
    else:
        wl_hint = "a short sentence (10-16 words)"

    prompt += (
        f"\nA new player named {new_bot_name} "
        f"just joined your party. Welcome them "
        f"briefly.\n"
        f"Length: {wl_hint}\n"
        f"Length mode: short only (keep it brief)\n\n"
        f"Don't repeat jokes or themes already "
        f"said in chat.\n\n"
        f"Your welcome should reflect your "
        f"personality traits. For example:\n"
        f"- A 'friendly, eager' bot might say: "
        f"\"Welcome aboard, glad to have you\"\n"
        f"- A 'cynical, reserved' bot might say: "
        f"\"Another one, huh? Fine by me\"\n"
        f"- A 'sarcastic, laid-back' bot might "
        f"say: \"Oh good, more company\"\n\n"
        f"{style_guide}\n\n"
        f"Rules:\n"
        f"- One short sentence only\n"
        f"- No quotes around your message\n"
        f"- No emojis\n"
        f"- Don't mention your class or race\n"
        f"- You can use {new_bot_name}'s name "
        f"or just say a general welcome"
    )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    return append_json_instruction(
        prompt, allow_action
    )


def build_batch_welcome_prompt(
    bot, traits, new_bot_names, mode,
    chat_history="", members=None,
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
):
    """Build prompt for an existing bot welcoming
    multiple new members who joined in a batch.

    Args:
        bot: dict with name, class, race, level
        traits: list of trait strings
        new_bot_names: list of new member names
        mode: 'normal' or 'roleplay'
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

        profile = RACE_SPEECH_PROFILES.get(
            bot['race']
        )
        if profile:
            fw = profile.get('flavor_words', [])
            flavor = ', '.join(
                random.sample(fw, min(3, len(fw)))
            )
            if flavor:
                rp_context += (
                    f"\nRace flavor words you might "
                    f"use: {flavor}"
                )

    if is_rp:
        style_guide = (
            "Speak as your character would on "
            "an RP server. Stay in-character but "
            "keep it casual and grounded. No game "
            "terms or OOC references."
        )
    else:
        style_guide = (
            "Sound like a normal person chatting "
            "in a game. Casual but natural, "
            "no excessive slang or abbreviations."
        )

    names_str = ', '.join(new_bot_names)
    count = len(new_bot_names)

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}"
        f"{rp_context}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"

    if members:
        others = [
            m for m in members
            if m != bot['name']
        ]
        if others:
            prompt += (
                f"\nParty members: "
                f"{', '.join(others)}\n"
            )
    if chat_history:
        prompt += f"{chat_history}\n"

    # Short welcome hint
    roll = random.random()
    if roll < 0.70:
        wl_hint = "short (5-12 words)"
    else:
        wl_hint = "a short sentence (12-20 words)"

    if count == 2:
        join_desc = (
            f"{names_str} just joined your party"
        )
    else:
        join_desc = (
            f"{count} new members just joined "
            f"your party: {names_str}"
        )

    prompt += (
        f"\n{join_desc}. Welcome them briefly.\n"
        f"Length: {wl_hint}\n"
        f"Length mode: short only "
        f"(keep it brief)\n\n"
        f"Don't repeat jokes or themes already "
        f"said in chat.\n\n"
        f"Your welcome should reflect your "
        f"personality traits. For example:\n"
        f"- A 'friendly, eager' bot might say: "
        f"\"Welcome aboard everyone!\"\n"
        f"- A 'cynical, reserved' bot might say: "
        f"\"Well, the gang's all here\"\n"
        f"- A 'sarcastic, laid-back' bot might "
        f"say: \"Oh good, a full house\"\n\n"
        f"{style_guide}\n\n"
        f"Rules:\n"
        f"- One short sentence only\n"
        f"- No quotes around your message\n"
        f"- No emojis\n"
        f"- Don't mention your class or race\n"
        f"- You can name them or just say a "
        f"general welcome"
    )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    return append_json_instruction(
        prompt, allow_action
    )


def build_kill_reaction_prompt(
    bot, traits, creature_name, is_boss, is_rare,
    mode, chat_history="", extra_data=None,
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    map_id=0,
):
    """Build prompt for a bot reacting to a kill.

    Boss kills get more excited prompts.
    Rare kills get 'nice find' style prompts.
    Personality traits influence the reaction.
    """
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
            extra_data
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

    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )

    # Raid context for kill prompts
    in_raid = (
        extra_data.get('in_raid', False)
        if extra_data else False
    )
    raid_name = (
        extra_data.get('raid_name', '')
        if extra_data else ''
    )

    if is_boss:
        kill_context = (
            f"Your party just killed the boss "
            f"{creature_name}! This was a big fight."
        )
    elif is_rare:
        kill_context = (
            f"Your party just killed a rare mob: "
            f"{creature_name}. Nice find!"
        )
    elif in_raid:
        kill_context = (
            f"Your raid just cleared {creature_name}"
            f" (trash mob) while pushing through"
        )
        if raid_name:
            kill_context += f" {raid_name}"
        kill_context += (
            ". Brief offhand remark — casual, "
            "not excited. Trash mobs are routine."
        )
    else:
        kill_context = (
            f"Your party just killed {creature_name}. "
            f"Just a regular mob, nothing special. "
            f"Make a brief, casual offhand remark "
            f"about it - don't be too excited."
        )

    if is_rp:
        style = (
            "React in-character. Keep it natural "
            "and grounded."
        )
    else:
        style = (
            "React naturally in party chat. "
            "Casual and brief."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{kill_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the creature by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_loot_reaction_prompt(
    bot, traits, item_name, item_quality, mode,
    chat_history="", looter_name=None,
    extra_data=None, allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    map_id=0,
):
    """Build prompt for a bot reacting to looting
    an item. Quality affects excitement level:
    2=green(casual), 3=blue(excited),
    4+=epic/legendary(very excited).
    If looter_name is set, a groupmate looted it
    and this bot is reacting to someone else's loot.
    """
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
            extra_data
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

    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )

    # Quality names for context
    quality_names = {
        2: 'uncommon (green)',
        3: 'rare (blue)',
        4: 'epic (purple)',
        5: 'legendary (orange)',
    }
    quality_label = quality_names.get(
        item_quality, 'special'
    )

    # Who looted: self or a groupmate?
    if looter_name:
        who = f"Your groupmate {looter_name}"
    else:
        who = "You"

    if item_quality >= 200:
        # Unknown quality (bot loot, Item* skipped
        # for crash safety). Generic reaction.
        loot_context = (
            f"{who} just picked up some loot. "
            f"Make a brief, casual remark about "
            f"it."
        )
    elif item_quality >= 4:
        loot_context = (
            f"{who} just looted {item_name}, an "
            f"{quality_label} item! This is a huge "
            f"find!"
        )
    elif item_quality == 3:
        loot_context = (
            f"{who} just looted {item_name}, a "
            f"{quality_label} item. That's a nice "
            f"drop worth mentioning."
        )
    else:
        loot_context = (
            f"{who} just looted {item_name}, an "
            f"{quality_label} item. Not bad, make "
            f"a brief casual remark about it."
        )

    if is_rp:
        style = (
            "React in-character about the loot. "
            "Keep it natural and grounded."
        )
    else:
        style = (
            "React naturally in party chat "
            "about getting loot. "
            "Casual and brief."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{loot_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the item by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat\n"
        f"- NEVER say the item will serve YOU "
        f"if someone else looted it"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_combat_reaction_prompt(
    bot, traits, creature_name, is_boss, mode,
    chat_history="", is_elite=False,
    extra_data=None, allow_action=False,
    speaker_talent_context=None,
    stored_tone=None,
):
    """Build prompt for a bot's battle cry when
    engaging a creature. Very short — must feel
    like real-time combat chat.
    """
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
            extra_data
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

    if is_boss:
        combat_context = (
            f"Your group just engaged "
            f"{creature_name}, a powerful boss! "
            f"This is a serious fight."
        )
    elif is_elite:
        combat_context = (
            f"Your group just engaged "
            f"{creature_name}, an elite enemy. "
            f"Time to fight."
        )
    else:
        combat_context = (
            f"Your group just pulled "
            f"{creature_name}. Just a regular mob, "
            f"make a quick casual combat remark."
        )

    if is_rp:
        style = (
            "Shout a brief battle cry or combat "
            "remark in-character."
        )
    else:
        style = (
            "Say something quick in party chat "
            "as you pull or engage the mob. "
            "Casual and natural."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{combat_context}\n\n"
        f"{style}\n\n"
        f"Say ONE very short battle cry or combat "
        f"remark (under 50 characters).\n"
        f"Rules:\n"
        f"- Extremely brief, 3-8 words max\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the enemy by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_death_reaction_prompt(
    reactor, reactor_traits, dead_name,
    killer_name, mode, chat_history="",
    is_player_death=False, extra_data=None,
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    map_id=0,
):
    """Build prompt for a bot reacting to a
    groupmate dying. The reactor is a DIFFERENT
    bot. Works for both bot and player deaths.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(reactor_traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
        )
        actual_role = (
            extra_data.get('bot_state', {})
            .get('role')
        )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            reactor['race'], reactor['class'],
            actual_role=actual_role
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )

    if is_player_death:
        who = f"Your party leader {dead_name}"
        if is_rp:
            style = (
                "React in-character to your "
                "leader falling. This is "
                "serious — show concern, "
                "urgency, protectiveness, "
                "or grim determination "
                "depending on personality."
            )
        else:
            style = (
                "React to the party leader "
                "dying. Could be alarmed, "
                "concerned, joking about it, "
                "or offering reassurance."
            )
    else:
        who = f"Your party member {dead_name}"
        if is_rp:
            style = (
                "React in-character. Could be "
                "sympathy, concern, or dark "
                "humor depending on your "
                "personality."
            )
        else:
            style = (
                "React naturally. Could be "
                "sympathy, humor, frustration, "
                "or just acknowledgment."
            )

    prompt = (
        f"You are {reactor['name']}, a level "
        f"{reactor['level']} {reactor['race']} "
        f"{reactor['class']} in World of "
        f"Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{who} just died"
    )
    if killer_name:
        prompt += f" (killed by {killer_name})"
    prompt += (
        f"!\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Mention {dead_name} by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_levelup_reaction_prompt(
    bot, traits, leveler_name, new_level, is_bot,
    mode, chat_history="", allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
):
    """Build prompt for a bot reacting to someone
    leveling up. Always congratulatory/excited.
    If is_bot=True, reacting to another bot.
    If is_bot=False, reacting to the real player.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    who = leveler_name
    if not is_bot:
        who = f"{leveler_name} (the real player)"

    levelup_context = (
        f"{who} just reached level {new_level}! "
        f"Leveling up is always exciting. "
        f"Congratulate or react to this milestone."
    )

    if is_rp:
        style = (
            "React in-character with genuine "
            "excitement or congratulations. "
            "Keep it natural and grounded."
        )
    else:
        style = (
            "React naturally in party chat. "
            "Congratulate or comment on "
            "the level-up."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{levelup_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention level {new_level}\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_quest_complete_reaction_prompt(
    bot, traits, completer_name, quest_name,
    mode, chat_history="",
    turnin_npc=None, allow_action=True,
    quest_details="", quest_objectives="",
    speaker_talent_context=None,
    stored_tone=None,
    zone_id=0,
):
    """Build prompt for a bot reacting to a quest
    completion. Tone varies: relief, satisfaction,
    excitement depending on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    # Zone context
    zone_flav = get_zone_flavor(zone_id)
    if is_rp and zone_flav:
        rp_context += (
            f"\nZone context: {zone_flav}"
        )

    if chat_history:
        rp_context += f"{chat_history}\n"

    npc_note = ""
    if turnin_npc:
        npc_note = (
            f" You turned it in to "
            f"{turnin_npc} (the quest giver NPC). "
            f"Do NOT address or congratulate the "
            f"NPC — talk to your PARTY instead. "
            f"Celebrate with your teammates."
        )
    quest_context = (
        f"TRANSACTION COMPLETE: Your group "
        f"handed in \"{quest_name}\" and got "
        f"paid.{npc_note} "
        f"Celebrate the XP, gold, reward item, "
        f"or simply ticking the quest off the "
        f"log. This is a TEAM win — use 'we' "
        f"language."
    )
    if quest_details:
        quest_context += (
            f" Quest description: {quest_details}"
        )
    if quest_objectives:
        quest_context += (
            f" Objectives: {quest_objectives}"
        )

    if is_rp:
        style = (
            "Express satisfaction at the payoff. "
            "You earned the reward together. "
            "Treat the NPC as a business partner "
            "or ally, not an enemy."
        )
    else:
        style = (
            "Casual celebration — quest done, "
            "reward collected, moving on. "
            "Brief and team-oriented."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{quest_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the quest by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_quest_objectives_reaction_prompt(
    bot, traits, quest_name, completer_name,
    mode, chat_history="", allow_action=True,
    quest_details="", quest_objectives="",
    speaker_talent_context=None,
    stored_tone=None,
    zone_id=0,
):
    """Build prompt for a bot reacting to quest
    objectives being completed (before turn-in).

    This is a GROUP effort — don't attribute to
    a specific player. Tone should be casual
    satisfaction, not over-excitement (that is
    reserved for the actual turn-in).
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    # Zone context
    zone_flav = get_zone_flavor(zone_id)
    if is_rp and zone_flav:
        rp_context += (
            f"\nZone context: {zone_flav}"
        )

    if chat_history:
        rp_context += f"{chat_history}\n"

    quest_context = (
        f"The objectives for \"{quest_name}\" "
        f"are done, but the quest is PENDING "
        f"TURN-IN. You are still in the field. "
        f"Your immediate goal is to travel back "
        f"to the quest giver and get paid. "
        f"Focus on the relief that the hard work "
        f"is done and that it's time to head back "
        f"— not on the story outcome."
    )
    if quest_details:
        quest_context += (
            f" Quest description: {quest_details}"
        )
    if quest_objectives:
        quest_context += (
            f" Objectives: {quest_objectives}"
        )

    if is_rp:
        style = (
            "Sound relieved or out of breath "
            "that the fighting is over, and "
            "focused on heading back. Use phrases "
            "like 'let's head back' or 'time to "
            "turn this in.' The quest is not "
            "resolved yet — you haven't been paid."
        )
    else:
        style = (
            "Casual confirmation that the work "
            "is done. Focus on returning to turn "
            "it in. Keep it transactional: "
            "'Done here, let's go back.'"
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{quest_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the quest by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't attribute the completion to "
        f"any specific player — it was a group "
        f"effort\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_achievement_reaction_prompt(
    bot, traits, achiever_name, achievement_name,
    is_bot, mode, chat_history="",
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    map_id=0,
):
    """Build prompt for a bot reacting to an
    achievement being earned. Achievements are
    special — more excited than regular events.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )

    # When the bot itself earned it, it speaks about
    # its own achievement. When someone else earned
    # it, the bot congratulates them.
    bot_is_achiever = (
        achiever_name == bot['name']
    )

    if bot_is_achiever:
        achieve_context = (
            f"You just earned the achievement "
            f"\"{achievement_name}\"! Achievements "
            f"are a big deal — celebrate your own "
            f"accomplishment with excitement!"
        )
    else:
        achieve_context = (
            f"Your groupmate {achiever_name} just "
            f"earned the achievement "
            f"\"{achievement_name}\"! Congratulate "
            f"them — achievements are a big deal "
            f"and worth celebrating!"
        )

    if bot_is_achiever:
        if is_rp:
            style = (
                "Celebrate your own achievement "
                "in-character. Be proud and excited."
            )
        else:
            style = (
                "Celebrate your own achievement "
                "in party chat. Be proud!"
            )
    else:
        if is_rp:
            style = (
                "Congratulate your groupmate "
                "in-character with genuine "
                "excitement. Keep it natural "
                "but enthusiastic."
            )
        else:
            style = (
                "Congratulate your groupmate "
                "naturally in party chat. "
                "Achievements are special, "
                "be excited for them!"
            )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{achieve_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the achievement by name\n"
    )
    if not bot_is_achiever:
        prompt += (
            f"- Address {achiever_name} by name\n"
            f"- This is THEIR achievement, not "
            f"yours — congratulate them\n"
        )
    prompt += (
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_group_achievement_reaction_prompt(
    bot, traits, achiever_names, achievement_name,
    mode, chat_history="",
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    map_id=0,
):
    """Build prompt for a bot reacting to multiple
    groupmates earning the same achievement at once.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )

    names_str = ', '.join(achiever_names)
    count = len(achiever_names)
    achieve_context = (
        f"Your whole group just earned the "
        f"achievement \"{achievement_name}\"! "
        f"{count} groupmates got it at once: "
        f"{names_str}. Congratulate them all — "
        f"this is a shared accomplishment worth "
        f"celebrating together!"
    )

    if is_rp:
        style = (
            "Congratulate the group in-character "
            "with genuine excitement. Address the "
            "group as a whole, not each person "
            "individually."
        )
    else:
        style = (
            "Congratulate the group naturally in "
            "party chat. Address them as a group, "
            "not one by one. Be excited!"
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{achieve_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the achievement by name\n"
        f"- You may mention a few names but don't "
        f"list everyone\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_spell_cast_reaction_prompt(
    bot, traits, caster_name, spell_name,
    spell_category, target_name, mode,
    chat_history="", members=None,
    dungeon_bosses=None, extra_data=None,
    allow_action=False,
    speaker_talent_context=None,
    stored_tone=None,
):
    """Build prompt for a bot reacting to a notable
    spell cast (heal, cc, resurrect, shield, buff,
    dispel, offensive, support).

    Args:
        bot: dict with name, class, race, level
        traits: list of 3 trait strings
        caster_name: who cast the spell
        spell_name: name of the spell cast
        spell_category: heal, cc, resurrect, shield,
            buff, dispel, offensive, support
        target_name: who was targeted
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        members: list of group member names
        dungeon_bosses: list of boss names if in
            a dungeon
        extra_data: parsed extra_data dict from event
    """
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
            extra_data
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

    # Determine if the speaking bot is the caster
    is_caster = (bot['name'] == caster_name)

    # Situation varies by category + perspective
    if is_caster:
        # Bot is the caster — speak about YOUR spell
        if spell_category == 'heal':
            situation = (
                f"You just healed {target_name} "
                f"with {spell_name}. Say something "
                f"brief and supportive to them."
            )
        elif spell_category == 'resurrect':
            situation = (
                f"You just resurrected {target_name}"
                f" with {spell_name}. Welcome them "
                f"back."
            )
        elif spell_category == 'shield':
            situation = (
                f"You just cast {spell_name} on "
                f"{target_name} to protect them. "
                f"Say something brief about it."
            )
        elif spell_category == 'buff':
            situation = (
                f"You just cast {spell_name} on "
                f"{target_name} to strengthen them. "
                f"Say something brief and supportive."
            )
        elif spell_category == 'cc':
            situation = (
                f"You just crowd-controlled an "
                f"enemy with {spell_name}. Say "
                f"something quick about it."
            )
        elif spell_category == 'dispel':
            situation = (
                f"You just cleansed {target_name} "
                f"with {spell_name}, removing a "
                f"harmful effect. Say something "
                f"brief about it."
            )
        elif spell_category == 'offensive':
            situation = (
                f"You just cast {spell_name} on an "
                f"enemy"
                + (f" ({target_name})"
                   if target_name else "")
                + ". Say something brief and "
                f"aggressive."
            )
        elif spell_category == 'support':
            situation = (
                f"You just cast {spell_name}"
                + (f" on {target_name}"
                   if target_name else "")
                + ". Say something brief and "
                f"supportive."
            )
        else:
            situation = (
                f"You just cast {spell_name}"
                + (f" on {target_name}"
                   if target_name else "")
            )
    else:
        # Bot is observing someone else's cast
        if spell_category == 'heal':
            situation = (
                f"{caster_name} just healed "
                f"{target_name} with {spell_name}"
            )
        elif spell_category == 'cc':
            situation = (
                f"{caster_name} just crowd-controlled"
                f" an enemy with {spell_name}"
            )
        elif spell_category == 'resurrect':
            situation = (
                f"{caster_name} just resurrected "
                f"{target_name} with {spell_name}"
            )
        elif spell_category == 'shield':
            situation = (
                f"{caster_name} just cast a "
                f"protective spell ({spell_name}) "
                f"on {target_name}"
            )
        elif spell_category == 'buff':
            situation = (
                f"{caster_name} just buffed "
                f"{target_name} with {spell_name}"
            )
        elif spell_category == 'dispel':
            situation = (
                f"{caster_name} just cleansed "
                f"{target_name} with {spell_name}, "
                f"removing a harmful effect"
            )
        elif spell_category == 'offensive':
            situation = (
                f"{caster_name} just cast "
                f"{spell_name}"
                + (f" on {target_name}"
                   if target_name else "")
            )
        elif spell_category == 'support':
            situation = (
                f"{caster_name} just cast "
                f"{spell_name}"
                + (f" on {target_name}"
                   if target_name else "")
            )
        else:
            situation = (
                f"{caster_name} just cast "
                f"{spell_name}"
                + (f" on {target_name}"
                   if target_name else "")
            )

    if members:
        others = [
            m for m in members
            if m != bot['name']
        ]
        if others:
            rp_context += (
                f"\nParty members: "
                f"{', '.join(others)}"
            )

    if dungeon_bosses:
        boss_list = ', '.join(
            dungeon_bosses[:6]
        )
        rp_context += (
            f"\nBosses in this dungeon: "
            f"{boss_list}"
        )

    if is_caster:
        if is_rp:
            style = (
                "Speak in-character about the "
                "spell you just cast. Keep it "
                "natural and grounded."
            )
        else:
            style = (
                "Say something casual in party "
                "chat about your spell. Brief "
                "and natural."
            )
    else:
        if is_rp:
            style = (
                "React in-character to the spell. "
                "Keep it natural and grounded."
            )
        else:
            style = (
                "React naturally in party chat. "
                "Casual and brief."
            )

    # Instruction differs based on caster vs observer
    if is_caster:
        instruction = (
            f"Say something in party chat to "
            f"{target_name} about your spell. "
            f"Mention {target_name} by name."
        )
    else:
        instruction = (
            f"Say a short reaction in party chat."
        )

    actor_guard = (
        "\nActor lock:\n"
        f"- Caster is exactly {caster_name}.\n"
    )
    if target_name:
        actor_guard += (
            f"- Target is exactly {target_name}.\n"
        )
    else:
        actor_guard += (
            "- No exact target name is known.\n"
        )
    actor_guard += (
        "- Do NOT invent a different caster, "
        "target, or credited player.\n"
        "- Do NOT praise or blame anyone whose "
        "name is not listed above unless they "
        "already appear in the recent chat "
        "history.\n"
    )

    # Extract previous spell reactions from this bot
    # in chat history for strong anti-repetition
    anti_rep_block = ""
    if chat_history:
        bot_name = bot['name']
        prev_lines = []
        for line in chat_history.strip().split('\n'):
            stripped = line.strip()
            if stripped.startswith(
                f"{bot_name}:"
            ) or stripped.startswith(
                f"  {bot_name}:"
            ):
                msg = stripped.split(':', 1)[-1]
                msg = msg.strip()
                if msg and len(msg) > 5:
                    prev_lines.append(msg)
        if prev_lines:
            anti_rep_block = (
                "\nYou have ALREADY said these in "
                "chat. Say something COMPLETELY "
                "different:\n"
            )
            for pl in prev_lines[-5:]:
                anti_rep_block += f'- "{pl}"\n'

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"{style}\n\n"
        f"{actor_guard}\n"
        f"{instruction}\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- Short reaction, one sentence only\n"
        f"- No quotes around your message\n"
        f"- No emojis\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
        f"{anti_rep_block}"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_player_response_prompt(
    bot, traits, player_name, player_message, mode,
    chat_history="", members=None, item_context="",
    allow_action=True, link_context="",
    speaker_talent_context=None,
    target_talent_context=None,
    zone_id=0, area_id=0, map_id=0,
    stored_tone=None,
    memories=None,
):
    """Build prompt for a bot responding to a real
    player's party chat message. The bot should
    reply naturally and contextually.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

        profile = RACE_SPEECH_PROFILES.get(
            bot['race']
        )
        if profile:
            fw = profile.get('flavor_words', [])
            flavor = ', '.join(
                random.sample(fw, min(3, len(fw)))
            )
            if flavor:
                rp_context += (
                    f"\nRace flavor words you might "
                    f"use: {flavor}"
                )

    # Location context — dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )
    else:
        zone_flav = get_zone_flavor(zone_id)
        if zone_flav:
            rp_context += (
                f"\nZone context: {zone_flav}"
            )
        subzone = get_subzone_lore(
            zone_id, area_id
        )
        if subzone:
            rp_context += (
                f"\nCurrent subzone: {subzone}"
            )

    if is_rp:
        style = (
            "Reply in-character. Stay natural and "
            "grounded. Don't break character."
        )
    else:
        style = (
            "Reply naturally in party chat. "
            "Casual and conversational."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if target_talent_context:
        prompt += f"{target_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if members:
        others = [
            m for m in members
            if m != bot['name']
        ]
        if others:
            rp_context += (
                f"\nParty members: "
                f"{', '.join(others)}, "
                f"{player_name} (player)"
            )
    if chat_history:
        rp_context += f"{chat_history}"

    # 40% chance to suggest addressing someone
    address_hint = ""
    if random.random() < 0.4:
        # Build list of addressable names
        candidates = []
        if player_name:
            candidates.append(player_name)
        if members:
            for m in members:
                if m != bot['name']:
                    candidates.append(m)
        if candidates:
            target = random.choice(candidates)
            address_hint = (
                f"- You may address {target} by "
                f"name in your reply\n"
            )

    # Inject memories if available
    if memories:
        from chatter_memory import (
            sanitize_memory_for_prompt,
        )
        sanitized = [
            sanitize_memory_for_prompt(m)
            for m in memories
        ]
        sanitized = [s for s in sanitized if s]
        if sanitized:
            mem_lines = '\n'.join(
                f"  - {m}" for m in sanitized
            )
            rp_context += (
                f"\n<past_memories>\n"
                f"Your memories from past "
                f"adventures with "
                f"{player_name}:\n"
                f"{mem_lines}\n"
                f"Reference one of these "
                f"memories clearly enough "
                f"that {player_name} would "
                f"recognise the callback — "
                f"mention the place, the "
                f"creature, or the moment "
                f"by name. Keep it natural "
                f"(not a full retelling).\n"
                f"</past_memories>"
            )

    prompt += f"{rp_context}\n\n"
    if link_context:
        prompt += f"{link_context}\n\n"
    prompt += (
        f"You are in a party. {player_name} just "
        f"said in party chat:\n"
        f"\"{player_message}\"\n\n"
        f"{style}\n\n"
        f"Reply in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Respond to what {player_name} said\n"
        f"{address_hint}"
        f"- Reflect your personality traits\n"
        f"- Don't repeat what they said\n"
        f"- If there's chat history, stay "
        f"consistent with the conversation\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat\n"
    )
    if item_context:
        prompt += (
            f"\n{item_context}\n"
            f"Comment on the item(s) from your "
            f"class/role perspective. Is it useful "
            f"for you? Good stats? Would you want it?"
        )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    return append_json_instruction(
        prompt, allow_action
    )

def build_resurrect_reaction_prompt(
    bot, traits, mode, chat_history="",
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
):
    """Build prompt for a bot reacting to being
    resurrected. The bot itself was just rezzed
    and reacts with gratitude, relief, or drama.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    if is_rp:
        style = (
            "React in-character to being "
            "resurrected. A grateful warrior, "
            "a relieved healer, a dramatic mage "
            "— whatever fits your personality."
        )
    else:
        style = (
            "React naturally to being brought "
            "back to life. Could be grateful, "
            "relieved, dramatic, or casual."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"You just died and someone in your "
        f"party resurrected you. You are back "
        f"on your feet.\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Express gratitude, relief, or drama\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )

def build_zone_transition_prompt(
    bot, traits, zone_name, zone_id, mode,
    chat_history="", allow_action=True,
    speaker_talent_context=None,
    area_id=0,
    stored_tone=None,
    is_subzone=False,
    area_name="",
):
    """Build prompt for a bot commenting on arriving
    in a new zone or subzone.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Try to get atmospheric zone/subzone context
    zone_flavor = get_zone_flavor(zone_id)
    zone_desc = ""
    if zone_flavor:
        zone_desc = (
            f"\nZone atmosphere: {zone_flavor}\n"
        )
    subzone = get_subzone_lore(zone_id, area_id)
    if subzone:
        zone_desc += (
            f"Current subzone: {subzone}\n"
        )

    # Resolve subzone name for subzone events
    # Prefer lore name, fall back to DBC area_name
    area_label = ""
    if is_subzone and area_id:
        from chatter_shared import get_subzone_name
        sn = get_subzone_name(zone_id, area_id)
        area_label = sn or area_name or ""

    if is_rp:
        if is_subzone and area_label:
            style = (
                f"Comment in-character on entering "
                f"the {area_label} area. Notice the "
                f"surroundings, atmosphere, or "
                f"what this part of the city/zone "
                f"is known for."
            )
        else:
            style = (
                "Comment in-character on arriving "
                "in this new area. Explorers get "
                "excited, cautious types express "
                "concern, warriors comment on "
                "potential threats."
            )
    else:
        if is_subzone and area_label:
            style = (
                f"Make a casual comment about "
                f"entering the {area_label} area. "
                f"Natural and brief."
            )
        else:
            style = (
                "Make a casual comment about "
                "arriving in a new zone. Natural "
                "and brief."
            )

    arrival_text = (
        f"Your party just entered the "
        f"{area_label} area of {zone_name}."
        if is_subzone and area_label
        else f"Your party just arrived in "
        f"{zone_name}."
    )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    location_name = (
        area_label if is_subzone and area_label
        else zone_name
    )
    prompt += (
        f"{rp_context}\n\n"
        f"{arrival_text}"
        f"{zone_desc}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {location_name} by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    return append_json_instruction(
        prompt, allow_action
    )

def build_quest_accept_reaction_prompt(
    bot, traits, acceptor_name, quest_name,
    quest_level, zone_name,
    mode, chat_history="", allow_action=True,
    quest_details="", quest_objectives="",
    speaker_talent_context=None,
    stored_tone=None,
    zone_id=0,
):
    """Build prompt for a bot reacting to the group
    accepting a new quest. Tone varies: excited,
    curious, cautious, matter-of-fact depending
    on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    # Zone context
    zone_flav = get_zone_flavor(zone_id)
    if is_rp and zone_flav:
        rp_context += (
            f"\nZone context: {zone_flav}"
        )

    if chat_history:
        rp_context += f"{chat_history}\n"

    quest_context = (
        f"{acceptor_name} just "
        f"picked up the quest \"{quest_name}\" "
        f"(level {quest_level}) for the group in "
        f"{zone_name}. Current Status: "
        f"PREPARATION. You have the instructions "
        f"but haven't begun yet. Focus on the "
        f"task ahead, the travel required, or "
        f"the plan of attack. Use 'we' language."
    )

    level_diff = int(bot['level']) - int(quest_level)
    if level_diff < -3:
        difficulty_note = (
            " This quest is above your level — "
            "it could be challenging."
        )
    elif level_diff > 5:
        difficulty_note = (
            " This quest is well below your level "
            "— should be easy."
        )
    else:
        difficulty_note = ""

    quest_context += difficulty_note
    if quest_details:
        quest_context += (
            f" Quest description: {quest_details}"
        )
    if quest_objectives:
        quest_context += (
            f" Objectives: {quest_objectives}"
        )

    if is_rp:
        style = (
            "Show anticipation, caution, or "
            "eagerness about heading out. Speak "
            "about getting started or what lies "
            "ahead. Treat this as the beginning "
            "of a to-do list."
        )
    else:
        style = (
            "Casual comment about heading out "
            "to start the quest. Focus on the "
            "journey ahead, not the outcome."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{quest_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention the quest by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    return append_json_instruction(
        prompt, allow_action
    )


def build_quest_accept_batch_prompt(
    bot, traits, acceptor_name, quest_names,
    zone_name, mode, chat_history="",
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    zone_id=0,
):
    """Build prompt for a bot reacting to the group
    picking up multiple quests at once. Produces a
    single generic 'lots of work ahead' message
    instead of per-quest spam.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    # Zone context
    zone_flav = get_zone_flavor(zone_id)
    if is_rp and zone_flav:
        rp_context += (
            f"\nZone context: {zone_flav}"
        )

    if chat_history:
        rp_context += f"{chat_history}\n"

    quest_list = ", ".join(
        f'"{q}"' for q in quest_names
    )
    quest_context = (
        f"{acceptor_name} just picked up "
        f"{len(quest_names)} quests for the "
        f"group in {zone_name}: {quest_list}. "
        f"The party has a lot of work ahead. "
        f"Use 'we' language."
    )

    if is_rp:
        style = (
            "React to the pile of new quests. "
            "Show excitement, determination, "
            "overwhelm, or humor about the "
            "workload. Do NOT list every quest "
            "by name — mention at most one, or "
            "speak generally about the tasks."
        )
    else:
        style = (
            "Casual comment about picking up a "
            "bunch of quests. Can joke about "
            "the to-do list or express readiness."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{quest_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention one quest name at most\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    spices = pick_personality_spices(
        mode=mode, spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )
    return append_json_instruction(
        prompt, allow_action
    )


def build_dungeon_entry_prompt(
    db, bot, traits, map_name, is_raid, map_id,
    mode, chat_history="", allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
):
    """Build prompt for a bot reacting to entering
    a dungeon or raid instance.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Try to get dungeon-specific flavor
    dungeon_flavor = get_dungeon_flavor(map_id)
    dungeon_desc = ""
    if dungeon_flavor:
        dungeon_desc = (
            f"\nDungeon atmosphere: "
            f"{dungeon_flavor}\n"
        )

    # Try to get boss names for context
    dungeon_bosses = get_dungeon_bosses(db, map_id)
    boss_context = ""
    if dungeon_bosses:
        boss_list = ', '.join(
            dungeon_bosses[:3]
        )
        boss_context = (
            f"\nKnown bosses here: {boss_list}\n"
        )

    instance_type = "raid" if is_raid else "dungeon"

    if is_rp:
        if is_raid:
            style = (
                "React in-character to entering "
                "a raid. This is a major challenge. "
                "Eager warriors steel themselves, "
                "cautious healers check supplies, "
                "scholarly mages study the "
                "surroundings."
            )
        else:
            style = (
                "React in-character to entering "
                "a dungeon. Personality-appropriate "
                "— eager, cautious, scholarly, or "
                "casual depending on your traits."
            )
    else:
        if is_raid:
            style = (
                "React casually to entering a "
                "raid. Could be excited, nervous, "
                "or just ready to go."
            )
        else:
            style = (
                "React casually to entering a "
                "dungeon. Brief and natural."
            )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"Your party just entered {map_name}, "
        f"a {instance_type}."
        f"{dungeon_desc}"
        f"{boss_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {map_name} by name\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )

def build_wipe_reaction_prompt(
    bot, traits, killer_name, mode,
    chat_history="", extra_data=None,
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    map_id=0,
):
    """Build prompt for a bot reacting to a total
    party wipe. Dramatic, frustrated, humorous,
    or resigned depending on personality.
    """
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
            extra_data
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

    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )

    wipe_context = (
        "Everyone in your party just died"
    )
    if killer_name:
        wipe_context += (
            f" — wiped by {killer_name}"
        )
    wipe_context += ". Total party wipe."

    if is_rp:
        style = (
            "React in-character to the wipe. "
            "Could be in-character despair, "
            "gallows humor, stoic acceptance, "
            "or dramatic frustration — whatever "
            "fits your personality."
        )
    else:
        style = (
            "React naturally to the wipe. "
            "Could be frustrated, humorous, "
            "resigned, or self-deprecating."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{wipe_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
    )
    if killer_name:
        prompt += (
            f"- Can reference {killer_name}\n"
        )
    prompt += (
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    return append_json_instruction(
        prompt, allow_action
    )

def build_corpse_run_reaction_prompt(
    bot, traits, zone_name, mode,
    chat_history="", dead_name="",
    is_player_death=False,
    allow_action=True,
    speaker_talent_context=None,
    stored_tone=None,
    map_id=0,
):
    """Build prompt for a bot commenting on a
    corpse run. Either the bot died (self), or
    the real player died and the bot reacts.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=0.5, mode=mode
    )


    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class']
        )
        if ctx:
            rp_context = f"\n{ctx}"

    if chat_history:
        rp_context += f"{chat_history}\n"

    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )

    zone_ctx = ""
    if zone_name:
        zone_ctx = (
            f" through {zone_name}"
        )

    if is_player_death:
        # Bot reacts to the player dying
        situation = (
            f"Your party leader {dead_name} "
            f"just died and released their "
            f"spirit. They're now running "
            f"back{zone_ctx} as a ghost to "
            f"reach their corpse."
        )
        if is_rp:
            style = (
                "React in-character to your "
                "leader's death. Could be "
                "concerned, offering words of "
                "encouragement, commenting on "
                "the danger, or darkly amused "
                "depending on your personality."
            )
        else:
            style = (
                "React to your party leader "
                "dying. Could be sympathetic, "
                "joking about it, offering to "
                "wait, or commenting on what "
                "killed them."
            )
    else:
        # Bot died themselves
        situation = (
            f"You just died and released your "
            f"spirit. Now you're running "
            f"back{zone_ctx} as a ghost to "
            f"reach your corpse."
        )
        if is_rp:
            style = (
                "Comment in-character on "
                "running back to your corpse "
                "as a ghost. Could be "
                "philosophical about death, "
                "grumbling about the walk, "
                "marveling at seeing the world "
                "as a spirit, or eager to get "
                "back into the fight."
            )
        else:
            style = (
                "Comment on the corpse run. "
                "Could be annoyed about the "
                "distance, making a joke about "
                "being a ghost, commenting on "
                "the scenery, or just resigned "
                "to the walk back."
            )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"{style}\n\n"
        f"Say something in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Reflect your personality traits\n"
        f"- Don't repeat jokes or themes "
        f"already said in chat"
    )
    if is_player_death:
        prompt += (
            f"\n- Refer to {dead_name} by name"
        )
    return append_json_instruction(
        prompt, allow_action
    )

def build_low_health_callout_prompt(
    bot, traits, target_name, mode,
    chat_history="", extra_data=None,
    allow_action=False,
    speaker_talent_context=None,
):
    """Bot is critically wounded (combat or OOC)."""
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
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

    hp = 0
    if extra_data:
        hp = int(
            extra_data.get('bot_state', {})
            .get('health_pct', 0)
        )

    situation = (
        f"You are critically wounded "
        f"({hp}% health)."
    )
    if target_name:
        situation += (
            f" You are fighting {target_name}."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"React with urgency — call for help, "
        f"express pain, or show desperation.\n"
        f"Say ONE short sentence in party chat.\n"
        f"Rules:\n"
        f"- Extremely brief, 3-10 words\n"
        f"- No quotes, no emojis\n"
        f"- Reflect your personality traits"
    )
    return append_json_instruction(
        prompt, allow_action
    )

def build_oom_callout_prompt(
    bot, traits, target_name, mode,
    chat_history="", extra_data=None,
    allow_action=False,
    speaker_talent_context=None,
):
    """Bot is running out of mana (combat or OOC).

    NOTE: Non-mana classes (Warrior, Rogue, DK) are
    filtered in C++ via GetMaxPower(POWER_MANA) > 0
    before the event is queued, so this function
    should only be called for mana-using classes.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
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

    mp = 0
    if extra_data:
        mp = int(
            extra_data.get('bot_state', {})
            .get('mana_pct', 0)
        )

    situation = (
        f"You are almost out of mana ({mp}%)."
    )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"Alert your group — ask for a moment "
        f"to drink, warn about low mana, or "
        f"express frustration.\n"
        f"Say ONE short sentence in party chat.\n"
        f"Rules:\n"
        f"- Extremely brief, 3-10 words\n"
        f"- No quotes, no emojis\n"
        f"- Reflect your personality traits"
    )
    return append_json_instruction(
        prompt, allow_action
    )

def build_aggro_loss_callout_prompt(
    bot, traits, target_name, aggro_target,
    mode, chat_history="", extra_data=None,
    allow_action=False,
    speaker_talent_context=None,
):
    """Tank lost aggro — mob attacking someone
    else in group."""
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    state_ctx = ""
    actual_role = None
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
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

    situation = (
        f"You are the tank but {target_name} "
        f"is now attacking {aggro_target}."
    )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"React with urgency — warn the group, "
        f"try to get the mob's attention back, "
        f"or call out the danger.\n"
        f"Say ONE short sentence in party chat.\n"
        f"Rules:\n"
        f"- Extremely brief, 3-10 words\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {target_name} or "
        f"{aggro_target} by name\n"
        f"- Reflect your personality traits"
    )
    return append_json_instruction(
        prompt, allow_action
    )


def build_precache_combat_pull_prompt(
    bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=False,
):
    """Build prompt for a cached combat pull cry.

    The response must contain {target} where the
    enemy name goes. C++ resolves it at delivery.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"
    prompt += (
        "\n\nYou just engaged an enemy in combat "
        "with your party. Write a very short "
        "pull cry or battle shout (1 sentence, "
        "3-10 words).\n"
        "Use {target} where the enemy name goes "
        "(e.g. \"I'll handle {target}!\" or "
        "\"Watch out, {target} incoming!\").\n"
        "Rules:\n"
        "- Must include {target} exactly once\n"
        "- Reflect your personality\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )


def build_precache_state_prompt(
    state_type, bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=False,
):
    """Build prompt for a cached state callout.

    state_type: 'low_health', 'oom', 'aggro_loss'
    low_health and oom have NO placeholders.
    aggro_loss uses {target} only.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"

    if state_type == 'low_health':
        prompt += (
            "\n\nYou are critically wounded. "
            "Write a very short callout "
            "(1 sentence, 3-10 words) asking for "
            "help or expressing pain.\n"
            "Rules:\n"
            "- First person only (\"I need "
            "healing!\", \"I'm going down!\")\n"
            "- Do NOT use any placeholders or "
            "names\n"
        )
    elif state_type == 'oom':
        # NOTE: Non-mana classes (Warrior, Rogue, DK)
        # are filtered upstream - C++ checks
        # GetMaxPower(POWER_MANA) > 0 for live events,
        # and refill_precache_pool() skips state_oom
        # for class_ids {1, 4, 6}.
        prompt += (
            "\n\nYou are almost out of mana. "
            "Write a very short callout "
            "(1 sentence, 3-10 words) alerting "
            "your group.\n"
            "Rules:\n"
            "- First person only (\"I need to "
            "drink\", \"No mana left!\")\n"
            "- Do NOT use any placeholders or "
            "names\n"
        )
    elif state_type == 'aggro_loss':
        prompt += (
            "\n\nYou are in combat and losing "
            "threat on your target. Write a very "
            "short callout (1 sentence, 3-10 "
            "words) warning your group.\n"
            "Use {target} where the enemy name "
            "goes (e.g. \"I'm losing {target}!\" "
            "or \"{target} is breaking free!\").\n"
            "Rules:\n"
            "- Must include {target} exactly once\n"
        )
    else:
        prompt += (
            "\n\nYou are in a stressful combat "
            "situation. Write a very short callout "
            "(1 sentence, 3-10 words).\n"
            "Rules:\n"
        )

    prompt += (
        "- Reflect your personality\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )


def build_precache_spell_support_prompt(
    bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=False,
):
    """Build prompt for a cached spell support
    reaction. Uses {target} and {spell} placeholders.

    Caster perspective - the bot IS the caster.
    C++ skips cache only for self-cast (bot casting
    on itself). When bot casts on someone else, the
    cached message delivers instantly.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"

    prompt += (
        "\n\nYou just cast a support spell on a "
        "groupmate. Write a very short comment "
        "(1 sentence, 3-10 words) about YOUR "
        "spell from the CASTER perspective."
        "\nUse these placeholders:\n"
        "- {spell} = the spell you cast\n"
        "- {target} = who you cast it on\n"
        "Example: \"There you go {target}, "
        "{spell} should help.\" or \"{target}, "
        "you're covered.\"\n"
    )

    prompt += (
        "Rules:\n"
        "- Use the placeholders exactly as shown "
        "(with curly braces)\n"
        "- Reflect your personality\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )


def build_precache_spell_offensive_prompt(
    bot_name, race, class_name, level,
    traits, mood, role=None, recent_cached=None,
    allow_action=False,
):
    """Build prompt for a cached offensive spell
    reaction. Uses {target} and {spell} placeholders.

    Caster perspective - the bot IS the caster.
    C++ only uses this cache when casterIsBot.
    """
    trait_str = ', '.join(traits) if traits else ''
    rp_ctx = build_race_class_context(
        race, class_name, actual_role=role
    )

    anti_rep = ''
    if recent_cached:
        anti_rep = build_anti_repetition_context(
            recent_cached, max_items=3
        )

    prompt = (
        f"You are {bot_name}, a level {level} "
        f"{race} {class_name} in World of Warcraft."
        f"\nPersonality: {trait_str}"
    )
    if rp_ctx:
        prompt += f"\n{rp_ctx}"

    prompt += (
        "\n\nYou just cast an offensive spell on "
        "an enemy in combat. Write a very short "
        "battle cry or taunt (1 sentence, 3-10 "
        "words) from the CASTER perspective."
        "\nUse these placeholders:\n"
        "- {spell} = the spell you cast\n"
        "- {target} = the enemy you hit (may be "
        "absent - write lines that work without it)\n"
        "Example: \"{spell} incoming!\" or "
        "\"Eat {spell}, {target}!\" or "
        "\"They won't last long.\"\n"
    )

    prompt += (
        "Rules:\n"
        "- Use the placeholders exactly as shown "
        "(with curly braces)\n"
        "- Reflect your personality\n"
        "- No quotes, no emojis\n"
        "- Respond with ONLY the message text"
    )
    if anti_rep:
        prompt += f"\n\n{anti_rep}"
    return append_json_instruction(
        prompt, allow_action
    )


def _format_object_lines(objects, config):
    """Format nearby objects into human-readable lines.

    Shared helper for both statement and conversation
    prompt builders.
    """
    _focus_map = {
        1: 'Anvil', 2: 'Loom', 3: 'Forge',
        4: 'Campfire/Cooking Fire',
        6: 'Moonwell', 7: 'Altar',
        8: 'Cauldron', 15: 'Runeforge',
    }
    lines = []
    for obj in objects:
        obj_type = obj.get('type', 'Object')
        is_creature = obj.get(
            'is_creature', False
        )
        sub_name = obj.get('sub_name', '')

        if is_creature:
            if sub_name:
                line = (
                    f"- {obj['name']}"
                    f" ({sub_name})"
                )
            else:
                line = (
                    f"- {obj['name']}"
                    f" ({obj_type})"
                )
            level = obj.get('level', 0)
            if level:
                line += f", level {level}"
        elif obj_type == 'SpellFocus':
            label = _focus_map.get(
                obj.get('spell_focus_id', 0),
                'SpellFocus',
            )
            line = f"- {obj['name']} ({label})"
        else:
            line = (
                f"- {obj['name']} ({obj_type})"
            )

        dist = obj.get('distance_yards', 0)
        if dist:
            line += (
                f" — "
                f"{format_distance(dist, config or {})}"
                f" away"
            )
        lines.append(line)
    return "\n".join(lines)


def build_nearby_object_reaction_prompt(
    bot_name, class_name, race_name, traits,
    objects, zone_name, subzone_name,
    in_city, in_dungeon, mode,
    chat_history="", allow_action=True,
    config=None,
    speaker_talent_context=None,
    subzone_lore=None,
    map_id=0,
):
    """Build prompt for a bot commenting on nearby
    GameObjects.

    class_name and race_name are pre-resolved strings
    (handler calls get_class_name / get_race_name from
    chatter_shared before passing them here -- matches
    the pattern used by all other prompt builders).
    """

    obj_desc = _format_object_lines(objects, config)

    # Location context
    location = (subzone_name or zone_name
                or "the area")
    setting = ("a dungeon" if in_dungeon
               else ("a city" if in_city
                     else "the wilderness"))

    # Personality
    trait_str = (", ".join(traits)
                 if traits else "")

    is_rp = (mode == 'roleplay')

    prompt = (
        f"You are {bot_name}, a "
        f"{race_name} {class_name}."
    )
    if trait_str:
        prompt += f" Personality: {trait_str}."
    prompt += (
        f"\n\nYou are walking through {location} "
        f"({setting}) with your group."
    )
    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        prompt += (
            f"\nDungeon context: {dungeon_flav}"
        )
    elif is_rp and subzone_lore:
        prompt += (
            f"\nAbout this place: {subzone_lore}"
        )
    elif not is_rp and subzone_name:
        prompt += f"\nSubzone: {subzone_name}"
    if is_rp:
        style = (
            "Make a brief, in-character observation "
            "or comment about what you see. Stay true "
            "to your race, class, and personality."
        )
    else:
        style = (
            "Make a brief comment about what you see "
            "as a regular WoW player — could be any "
            "age, mature and grounded. Natural "
            "reaction, as a player not a character."
        )
    prompt += (
        f"\nYou notice the following nearby:\n"
        f"{obj_desc}"
        f"\n\n{style} "
        f"One to two sentences. "
        f"Don't narrate actions — just speak."
    )

    if chat_history:
        prompt += (
            f"\n\nRecent party chat for context "
            f"(don't repeat these):\n{chat_history}"
        )

    return append_json_instruction(
        prompt, allow_action=allow_action)


def build_nearby_object_conversation_prompt(
    bots, traits_map, objects,
    zone_name, subzone_name,
    in_city, in_dungeon, mode,
    chat_history="", allow_action=True,
    config=None,
    speaker_talent_context=None,
    target_talent_context=None,
    subzone_lore=None,
    map_id=0,
):
    """Build prompt for a multi-bot conversation
    about nearby GameObjects.

    Args:
        bots: list of dicts with name, class, race,
            level keys
        traits_map: dict mapping bot_name to
            [trait1, trait2, trait3]
        objects: list of object dicts from extra_data
        zone_name: current zone name
        subzone_name: current subzone name
        in_city: bool, party is in a city
        in_dungeon: bool, party is in a dungeon
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        allow_action: whether to allow action field
        config: config dict for format_distance
    """
    is_rp = (mode == 'roleplay')
    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]

    obj_desc = _format_object_lines(objects, config)

    # -- Location context --
    location = (
        subzone_name or zone_name or "the area"
    )
    setting = (
        "a dungeon" if in_dungeon
        else ("a city" if in_city
              else "the wilderness")
    )

    # -- Speaker count word --
    count_word = {
        2: "two", 3: "three", 4: "four"
    }.get(num_bots, str(num_bots))

    # -- Build prompt parts --
    parts = []
    if is_rp:
        parts.append(
            f"Generate a short in-character party "
            f"chat exchange between {count_word} "
            f"adventurers reacting to something "
            f"they notice nearby."
        )
    else:
        parts.append(
            f"Generate a short casual party chat "
            f"exchange between {count_word} WoW "
            f"players commenting on something "
            f"they see nearby."
        )

    parts.append(
        f"Location: {location} ({setting})."
    )
    # Location context -- dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        parts.append(
            f"Dungeon context: {dungeon_flav}"
        )
    elif is_rp and subzone_lore:
        parts.append(
            f"About this place: {subzone_lore}"
        )
    elif not is_rp and subzone_name:
        parts.append(f"Subzone: {subzone_name}")
    parts.append(
        f"Nearby points of interest:\n{obj_desc}"
    )

    # Speakers with traits and class/race
    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    _append_bots_with_rp(
        parts, bots, traits_map, is_rp
    )

    if speaker_talent_context:
        parts.append(speaker_talent_context)
    if target_talent_context:
        parts.append(target_talent_context)

    # Tone and twist
    tone = pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    parts.append(f"Overall tone: {tone}")
    if twist:
        parts.append(f"Creative twist: {twist}")

    # Message count: 2 per bot, cap at 8
    msg_count = min(2 * num_bots, 8)

    # Natural flow for 3+ bots
    if num_bots > 2:
        parts.append(
            "IMPORTANT: EVERY speaker MUST have "
            "at least one message — do NOT skip "
            "any participant. Let the conversation "
            "flow organically, not rigid "
            "round-robin."
        )

    # Style guidance
    length_hint = _pick_length_hint(mode)
    if is_rp:
        parts.append(
            "Guidelines: Stay in-character for "
            "race and class; no game terms or "
            f"OOC; {length_hint}; "
        )
    else:
        parts.append(
            "Guidelines: Sound like normal "
            "people chatting in a game; casual "
            f"and relaxed; {length_hint}; "
        )

    parts.append(
        "React to the nearby objects — "
        "observations, opinions, memories, "
        "jokes, or lore. Don't just list what "
        "you see. Don't repeat themes from "
        "recent chat."
    )

    spices = pick_personality_spices(
        mode=mode,
        spice_count_override=_spice_count,
    )
    if spices:
        parts.append(
            "Background feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )

    if chat_history:
        parts.append(
            "Recent party chat for context "
            "(don't repeat these):\n"
            + chat_history
        )

    prompt = '\n'.join(parts)

    return append_conversation_json_instruction(
        prompt, bot_names, msg_count,
        allow_action=allow_action,
    )


def build_player_msg_conversation_prompt(
    bots, traits_map, player_name,
    player_message, mode,
    chat_history="", members=None,
    item_context="", link_context="",
    allow_action=True,
    speaker_talent_context=None,
    target_talent_context=None,
    zone_id=0, area_id=0, map_id=0,
):
    """Build prompt for a multi-bot conversation
    responding to a player's party chat message.

    Args:
        bots: list of bot dicts (name, class, race,
            level). First bot is the addressed one.
        traits_map: dict mapping bot_name to
            [trait1, trait2, trait3]
        player_name: real player who spoke
        player_message: what the player said
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        members: list of all group member names
        item_context: formatted item link context
        link_context: WoW link context string
        allow_action: whether to allow action field
    """
    is_rp = (mode == 'roleplay')
    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]
    addressed_name = bot_names[0]

    # Each bot speaks exactly once
    msg_count = num_bots

    count_word = {
        2: "two", 3: "three",
    }.get(num_bots, str(num_bots))

    parts = []

    if is_rp:
        parts.append(
            f"Generate a short in-character party "
            f"chat exchange between {count_word} "
            f"adventurers reacting to what a "
            f"real player just said."
        )
    else:
        parts.append(
            f"Generate a short casual party chat "
            f"exchange between {count_word} WoW "
            f"players reacting to what a real "
            f"player just said."
        )

    parts.append(
        f"\n{player_name} just said in party "
        f"chat:\n\"{player_message}\""
    )

    if link_context:
        parts.append(link_context)
    if item_context:
        parts.append(item_context)

    # Location context — dungeon takes priority
    dungeon_flav = get_dungeon_flavor(map_id)
    if dungeon_flav:
        parts.append(
            f"Dungeon context: {dungeon_flav}"
        )
    else:
        zone_flav = get_zone_flavor(zone_id)
        if zone_flav:
            parts.append(
                f"Zone context: {zone_flav}"
            )
        subzone = get_subzone_lore(
            zone_id, area_id
        )
        if subzone:
            parts.append(
                f"Current subzone: {subzone}"
            )

    # Speakers with traits and class/race
    parts.append(
        f"\nSpeakers: {', '.join(bot_names)}"
    )
    _append_bots_with_rp(
        parts, bots, traits_map, is_rp
    )

    if speaker_talent_context:
        parts.append(speaker_talent_context)
    if target_talent_context:
        parts.append(target_talent_context)

    # Party context
    if members:
        others = [
            m for m in members
            if m not in bot_names
            and m != player_name
        ]
        if others:
            parts.append(
                f"Other party members: "
                f"{', '.join(others)}"
            )

    # Tone and twist
    tone = pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    parts.append(f"\nOverall tone: {tone}")
    if twist:
        parts.append(f"Creative twist: {twist}")

    # Mood and length sequence
    mood_seq = generate_conversation_mood_sequence(
        msg_count, mode
    )
    length_seq = (
        generate_conversation_length_sequence(
            msg_count
        )
    )
    # First speaker responds directly; override
    # mood to 'engaged'
    mood_seq[0] = 'engaged'

    twist_log = (
        f", twist={twist}" if twist else ""
    )

    parts.append(
        "\nMOOD AND LENGTH SEQUENCE "
        "(follow for each message):"
    )
    for i, mood in enumerate(mood_seq):
        speaker = bot_names[i]
        if i == 0:
            parts.append(
                f"  Message {i+1} ({speaker}): "
                f"mood={mood}, "
                f"length={length_seq[i]} "
                f"— respond directly to "
                f"{player_name}"
            )
        else:
            parts.append(
                f"  Message {i+1} ({speaker}): "
                f"mood={mood}, "
                f"length={length_seq[i]} "
                f"— build on the conversation"
            )

    # Style guidance
    length_hint = _pick_length_hint(mode)
    if is_rp:
        parts.append(
            "\nGuidelines: Stay in-character for "
            "race and class; no game terms or "
            f"OOC; {length_hint}; "
        )
    else:
        parts.append(
            "\nGuidelines: Sound like normal "
            "people chatting in a game; casual "
            f"and relaxed; {length_hint}; "
        )

    parts.append(
        "Rules:\n"
        f"- {addressed_name} responds directly "
        f"to what {player_name} said\n"
        "- Other speakers react to the "
        "conversation, building on each other\n"
        "- Each bot speaks EXACTLY once\n"
        "- Stay in character\n"
        "- Don't repeat what the player said\n"
        "- Don't repeat jokes or themes "
        "already said in chat"
    )

    spices = pick_personality_spices(
        mode=mode,
        spice_count_override=_spice_count,
    )
    if spices:
        parts.append(
            "Background feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )

    if chat_history:
        parts.append(
            "Recent party chat for context "
            "(don't repeat these):\n"
            + chat_history
        )

    recent = (
        chat_history.splitlines()[-10:]
        if chat_history else []
    )
    anti_rep = build_anti_repetition_context(recent)
    if anti_rep:
        parts.append(anti_rep)

    prompt = '\n'.join(parts)

    # JSON instruction built inline (party-chat
    # variant with emotes). Must stay in sync with
    # append_conversation_json_instruction() in
    # chatter_shared.py if format changes.
    if allow_action:
        action_text = (
            "Actions: Each message may include "
            "an optional \"action\" field — a "
            "short physical action (2-5 words, "
            "e.g. \"scratches chin\"). Omit if "
            "not needed. "
            "NEVER put {item:}, {quest:}, or "
            "{spell:} placeholders in the action "
            "field — those belong in message only."
        )
    else:
        action_text = (
            "Actions: Do not include an action "
            "field in this response."
        )

    example_msgs = ',\n  '.join(
        [
            f'{{"speaker": "{name}", '
            f'"message": "...", '
            f'"emote": "talk", '
            f'"action": "..."}}'
            for name in bot_names
        ]
    )

    prompt += (
        f"\n\nEmotes: Each message may include "
        f"an optional \"emote\" field (one of: "
        f"{EMOTE_LIST_STR}). Pick an emote that "
        f"fits the message mood, or omit it.\n"
        f"{action_text}\n"
        f"JSON rules: Use double quotes, escape "
        f"quotes/newlines, no trailing commas, "
        f"no code fences.\n"
        f"\nRespond with EXACTLY {msg_count} "
        f"messages in JSON:\n[\n  "
        f"{example_msgs}\n]\n"
        f"ONLY the JSON array, nothing else."
    )

    return prompt


# ============================================================
# BOT-INITIATED QUESTION TO PLAYER
# ============================================================

# Question topic suggestions — creative and specific
BOT_QUESTION_TOPICS = [
    # Class / role curiosity
    'their class abilities or fighting style',
    'what drew them to their class',
    'their favorite spell or ability',
    'how they handle tough fights as their class',
    # Race / identity
    'their homeland or racial background',
    'what life is like for their race',
    'traditions or customs of their people',
    # Zone / location
    'the current area and its history',
    'something they noticed about this place',
    'whether they have been here before',
    'rumors about this region',
    # Adventure / party
    'their most memorable battle or adventure',
    'what they hope to find or accomplish today',
    'their opinion on the group composition',
    'a past experience with a similar group',
    # Philosophy / personality
    'their thoughts on the faction conflict',
    'what motivates them to keep adventuring',
    'something they miss about home',
    'what they would do if they were not an adventurer',
]

# Questions focused on the dungeon/raid context
DUNGEON_QUESTION_TOPICS = [
    'whether they have run this dungeon before',
    'their strategy for the next boss',
    'the most dangerous enemy they expect here',
    'what loot or reward they are hoping for',
    'a close call or wipe they remember in this place',
    'what they know about the lore behind this dungeon',
    'their role in the group for the tougher fights ahead',
    'how they feel about the difficulty so far',
    'the part of this dungeon they find most challenging',
    'whether they prefer this dungeon over others',
]

# Questions focused on the battleground context
BG_QUESTION_TOPICS = [
    'their strategy for this battleground',
    'their favourite role in PvP fights',
    'the best play they ever made in a battleground',
    'which objective they think matters most here',
    'how they read the flow of a battle like this',
    'what frustrates them most about losing a battleground',
    'their opinion on the current team composition',
    'whether they prefer this battleground over others',
]


def build_bot_question_prompt(
    bot, traits, mode,
    player_name, player_class, player_race,
    player_level,
    chat_history="", members=None,
    zone_id=0, map_id=0,
    current_weather=None,
    recent_messages=None,
    allow_action=True,
    speaker_talent_context=None,
    target_talent_context=None,
    area_id=0,
    stored_tone=None,
    memories=None,
):
    """Build prompt for a bot asking the player a
    creative, contextual question in party chat.

    Args:
        bot: dict with name, class, race, level, role
        traits: list of 3 trait strings
        mode: 'normal' or 'roleplay'
        player_name: real player's character name
        player_class: player's class name string
        player_race: player's race name string
        player_level: player's level (int)
        chat_history: formatted recent chat string
        members: list of group member names
        zone_id: for zone flavor
        map_id: for dungeon flavor
        current_weather: weather string or None
        recent_messages: for anti-repetition
        allow_action: whether to allow action field
        memories: list of memory strings or None
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    # --------------------------------------------------
    # LEAN MEMORY PATH — when memories are present,
    # the question should be ABOUT the memory rather
    # than a generic topic.
    # --------------------------------------------------
    if memories:
        from chatter_memory import (
            sanitize_memory_for_prompt,
        )
        sanitized = [
            sanitize_memory_for_prompt(m)
            for m in memories
        ]
        sanitized = [s for s in sanitized if s]
        if sanitized:
            mem_lines = '\n'.join(
                f"  - {m}" for m in sanitized
            )
            prompt = (
                f"You are {bot['name']}, a level "
                f"{bot['level']} {bot['race']} "
                f"{bot['class']}.\n"
                f"Your personality: {trait_str}\n"
            )
            if speaker_talent_context:
                prompt += (
                    f"{speaker_talent_context}\n"
                )
            prompt += (
                f"\n<past_memories>\n"
                f"Your memories from past "
                f"adventures with "
                f"{player_name}:\n"
                f"{mem_lines}\n"
                f"Ask {player_name} a question "
                f"about one of these memories — "
                f"\"remember when we...?\" style. "
                f"Mention the place, creature, or "
                f"moment by name so {player_name} "
                f"would recognise it.\n"
                f"</past_memories>\n\n"
                f"You are grouped with "
                f"{player_name}, a level "
                f"{player_level} {player_race} "
                f"{player_class} (real player).\n\n"
                f"Ask {player_name} ONE short "
                f"question about a shared memory "
                f"above.\n"
            )
            if chat_history:
                prompt += (
                    f"\nRecent party chat "
                    f"(for context only):"
                    f"{chat_history}\n"
                )
            prompt += (
                f"\n{_pick_length_hint(mode)}\n"
                f"Rules:\n"
                f"- Ask exactly ONE question\n"
                f"- Your message MUST end with "
                f"a question mark (?)\n"
                f"- Keep it to 1-2 sentences\n"
                f"- Do NOT answer your own "
                f"question\n"
                f"- The memory must be the focus "
                f"of the question\n"
                f"- No quotes, no emojis\n"
                f"- You can use "
                f"{player_name}'s name"
            )
            anti_rep = build_anti_repetition_context(
                recent_messages
            )
            if anti_rep:
                prompt += f"\n{anti_rep}"
            return append_json_instruction(
                prompt, allow_action
            )
    # memories were empty or all sanitized away —
    # fall through to the normal full prompt below.

    # --------------------------------------------------
    # NORMAL PATH — no memories, full context prompt
    # --------------------------------------------------
    tone = stored_tone or pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    # Pick topic pool based on location context
    if get_dungeon_flavor(map_id) is not None:
        topic = random.choice(DUNGEON_QUESTION_TOPICS)
    elif map_id in BG_MAP_NAMES:
        topic = random.choice(BG_QUESTION_TOPICS)
    else:
        topic = random.choice(BOT_QUESTION_TOPICS)

    rp_context = ""
    if is_rp:
        ctx = build_race_class_context(
            bot['race'], bot['class'],
            actual_role=bot.get('role')
        )
        if ctx:
            rp_context = f"\n{ctx}"

        profile = RACE_SPEECH_PROFILES.get(
            bot['race']
        )
        if profile:
            fw = profile.get('flavor_words', [])
            flavor = ', '.join(
                random.sample(fw, min(3, len(fw)))
            )
            if flavor:
                rp_context += (
                    f"\nRace flavor words you might "
                    f"use: {flavor}"
                )

    # Location context
    dungeon_flav = get_dungeon_flavor(map_id)
    zone_flav = get_zone_flavor(zone_id)
    in_dungeon = dungeon_flav is not None
    if dungeon_flav:
        rp_context += (
            f"\nDungeon context: {dungeon_flav}"
        )
    elif zone_flav:
        rp_context += (
            f"\nZone context: {zone_flav}"
        )
    if not in_dungeon:
        subzone = get_subzone_lore(
            zone_id, area_id
        )
        if subzone:
            rp_context += (
                f"\nCurrent subzone: {subzone}"
            )

    # Environmental context
    from chatter_prompts import get_environmental_context
    weather_arg = (
        None if in_dungeon else current_weather
    )
    env = get_environmental_context(weather_arg)
    if env['time']:
        rp_context += (
            f"\nTime of day: {env['time']}"
        )
    if env['weather']:
        rp_context += (
            f"\nCurrent weather: {env['weather']}"
        )

    # Party context
    if members:
        others = [
            m for m in members
            if m != bot['name']
        ]
        if (
            player_name
            and player_name not in others
        ):
            others.append(
                f"{player_name} (player)"
            )
        if others:
            rp_context += (
                f"\nParty members: "
                f"{', '.join(others)}"
            )
    if chat_history:
        rp_context += f"{chat_history}"

    if is_rp:
        style = (
            "Ask your question in-character. "
            "Stay true to your race and class "
            "identity."
        )
    else:
        style = (
            "Ask casually, like a normal person "
            "chatting in a game. Natural and "
            "relaxed."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
    )
    if speaker_talent_context:
        prompt += f"{speaker_talent_context}\n"
    if target_talent_context:
        prompt += f"{target_talent_context}\n"
    prompt += (
        f"Your tone: {tone}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"

    prompt += (
        f"{rp_context}\n\n"
        f"You are grouped with {player_name}, "
        f"a level {player_level} {player_race} "
        f"{player_class} (real player).\n"
        f"You want to ask {player_name} about "
        f"{topic}.\n\n"
        f"Ask {player_name} ONE short, creative "
        f"question in party chat.\n"
        f"{style}\n\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- Ask exactly ONE question\n"
        f"- Your message MUST end with a "
        f"question mark (?)\n"
        f"- Keep it to 1-2 sentences\n"
        f"- Do NOT answer your own question\n"
        f"- Do NOT ask generic questions like "
        f"'how are you' or 'what's up'\n"
        f"- Be specific and creative based on "
        f"their class, race, the zone, or "
        f"your personality\n"
        f"- No quotes around your message\n"
        f"- No emojis\n"
        f"- You can use {player_name}'s name"
    )

    spices = pick_personality_spices(
        mode=mode,
        spice_count_override=_spice_count
    )
    if spices:
        prompt += (
            "\nBackground feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )

    anti_rep = build_anti_repetition_context(
        recent_messages
    )
    if anti_rep:
        prompt += f"\n{anti_rep}"

    return append_json_instruction(
        prompt, allow_action
    )


# ================================================================
# QUEST CONVERSATION PROMPT BUILDERS
# ================================================================

def build_quest_complete_conversation_prompt(
    bots, traits_map, completer_name,
    quest_name, mode, chat_history="",
    turnin_npc=None, allow_action=True,
    quest_details="", quest_objectives="",
    msg_count=3,
    speaker_talent_context=None,
    zone_id=0,
):
    """Build prompt for a multi-bot conversation
    about a quest completion.

    Args:
        bots: list of dicts with name, class, race,
            level keys
        traits_map: dict mapping bot_name to
            [trait1, trait2, trait3]
        completer_name: who completed the quest
        quest_name: name of the completed quest
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        turnin_npc: NPC the quest was turned in to
        allow_action: whether to allow action field
        quest_details: quest description text
        quest_objectives: quest objectives text
        msg_count: number of messages to generate
    """
    is_rp = (mode == 'roleplay')
    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]

    count_word = {
        2: "two", 3: "three", 4: "four"
    }.get(num_bots, str(num_bots))

    npc_note = ""
    if turnin_npc:
        npc_note = (
            f" You turned it in to "
            f"{turnin_npc} (the quest giver NPC)."
            f" Do NOT address or congratulate the"
            f" NPC — talk to your PARTY instead."
        )

    quest_context = (
        f"TRANSACTION COMPLETE: Your group "
        f"handed in \"{quest_name}\" and got "
        f"paid.{npc_note} "
        f"Celebrate the XP, gold, reward item, "
        f"or simply ticking the quest off the "
        f"log. This is a TEAM win — use 'we' "
        f"language."
    )
    if quest_details:
        quest_context += (
            f" Quest description: {quest_details}"
        )
    if quest_objectives:
        quest_context += (
            f" Objectives: {quest_objectives}"
        )

    parts = []
    if is_rp:
        parts.append(
            f"Generate a short in-character party "
            f"chat exchange between {count_word} "
            f"adventurers celebrating a completed "
            f"quest."
        )
    else:
        parts.append(
            f"Generate a short casual party chat "
            f"exchange between {count_word} WoW "
            f"players celebrating a completed "
            f"quest."
        )

    parts.append(quest_context)

    # Zone context
    zone_flav = get_zone_flavor(zone_id)
    if zone_flav:
        parts.append(
            f"Zone context: {zone_flav}"
        )

    # Speakers with traits and class/race
    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    _append_bots_with_rp(
        parts, bots, traits_map, is_rp
    )

    if speaker_talent_context:
        parts.append(speaker_talent_context)

    # Tone and twist
    tone = pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    parts.append(f"Overall tone: {tone}")
    if twist:
        parts.append(f"Creative twist: {twist}")

    if num_bots > 2:
        parts.append(
            "IMPORTANT: EVERY speaker MUST have "
            "at least one message — do NOT skip "
            "any participant."
        )

    length_hint = _pick_length_hint(mode)
    if is_rp:
        parts.append(
            "Guidelines: Stay in-character for "
            "race and class; no game terms or "
            f"OOC; {length_hint}; "
        )
    else:
        parts.append(
            "Guidelines: Sound like normal "
            "people chatting in a game; casual "
            f"and relaxed; {length_hint}; "
        )

    parts.append(
        "Celebrate the quest completion — "
        "relief, satisfaction, humor, or "
        "excitement about the reward. "
        "Don't repeat themes from recent chat."
    )

    spices = pick_personality_spices(
        mode=mode,
        spice_count_override=_spice_count,
    )
    if spices:
        parts.append(
            "Background feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )

    if chat_history:
        parts.append(
            "Recent party chat for context "
            "(don't repeat these):\n"
            + chat_history
        )

    prompt = '\n'.join(parts)

    return append_conversation_json_instruction(
        prompt, bot_names, msg_count,
        allow_action=allow_action,
    )


def build_quest_objectives_conversation_prompt(
    bots, traits_map, quest_name,
    completer_name, mode, chat_history="",
    allow_action=True,
    quest_details="", quest_objectives="",
    msg_count=3,
    speaker_talent_context=None,
    zone_id=0,
):
    """Build prompt for a multi-bot conversation
    about quest objectives being completed.

    Args:
        bots: list of dicts with name, class, race,
            level keys
        traits_map: dict mapping bot_name to
            [trait1, trait2, trait3]
        quest_name: name of the quest
        completer_name: who finished objectives
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        allow_action: whether to allow action field
        quest_details: quest description text
        quest_objectives: quest objectives text
        msg_count: number of messages to generate
    """
    is_rp = (mode == 'roleplay')
    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]

    count_word = {
        2: "two", 3: "three", 4: "four"
    }.get(num_bots, str(num_bots))

    quest_context = (
        f"The objectives for \"{quest_name}\" "
        f"are done, but the quest is PENDING "
        f"TURN-IN. You are still in the field. "
        f"Your immediate goal is to travel back "
        f"to the quest giver and get paid. "
        f"Focus on the relief that the hard "
        f"work is done and that it's time to "
        f"head back — not on the story outcome."
    )
    if quest_details:
        quest_context += (
            f" Quest description: {quest_details}"
        )
    if quest_objectives:
        quest_context += (
            f" Objectives: {quest_objectives}"
        )

    parts = []
    if is_rp:
        parts.append(
            f"Generate a short in-character party "
            f"chat exchange between {count_word} "
            f"adventurers reacting to finishing "
            f"quest objectives."
        )
    else:
        parts.append(
            f"Generate a short casual party chat "
            f"exchange between {count_word} WoW "
            f"players reacting to finishing "
            f"quest objectives."
        )

    parts.append(quest_context)

    # Zone context
    zone_flav = get_zone_flavor(zone_id)
    if zone_flav:
        parts.append(
            f"Zone context: {zone_flav}"
        )

    # Speakers with traits and class/race
    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    _append_bots_with_rp(
        parts, bots, traits_map, is_rp
    )

    if speaker_talent_context:
        parts.append(speaker_talent_context)

    # Tone and twist
    tone = pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    parts.append(f"Overall tone: {tone}")
    if twist:
        parts.append(f"Creative twist: {twist}")

    if num_bots > 2:
        parts.append(
            "IMPORTANT: EVERY speaker MUST have "
            "at least one message — do NOT skip "
            "any participant."
        )

    length_hint = _pick_length_hint(mode)
    if is_rp:
        parts.append(
            "Guidelines: Stay in-character for "
            "race and class; no game terms or "
            f"OOC; {length_hint}; "
        )
    else:
        parts.append(
            "Guidelines: Sound like normal "
            "people chatting in a game; casual "
            f"and relaxed; {length_hint}; "
        )

    parts.append(
        "React to objectives being done — "
        "relief, readiness to head back, or "
        "casual satisfaction. Don't attribute "
        "the completion to any specific player."
        " Don't repeat themes from recent chat."
    )

    spices = pick_personality_spices(
        mode=mode,
        spice_count_override=_spice_count,
    )
    if spices:
        parts.append(
            "Background feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )

    if chat_history:
        parts.append(
            "Recent party chat for context "
            "(don't repeat these):\n"
            + chat_history
        )

    prompt = '\n'.join(parts)

    return append_conversation_json_instruction(
        prompt, bot_names, msg_count,
        allow_action=allow_action,
    )


def build_quest_accept_conversation_prompt(
    bots, traits_map, acceptor_name,
    quest_name, quest_level, zone_name,
    mode, chat_history="",
    allow_action=True,
    quest_details="", quest_objectives="",
    msg_count=3,
    speaker_talent_context=None,
    zone_id=0,
):
    """Build prompt for a multi-bot conversation
    about the group accepting a new quest.

    Args:
        bots: list of dicts with name, class, race,
            level keys
        traits_map: dict mapping bot_name to
            [trait1, trait2, trait3]
        acceptor_name: who accepted the quest
        quest_name: name of the quest
        quest_level: level of the quest
        zone_name: current zone name
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        allow_action: whether to allow action field
        quest_details: quest description text
        quest_objectives: quest objectives text
        msg_count: number of messages to generate
    """
    is_rp = (mode == 'roleplay')
    num_bots = len(bots)
    bot_names = [b['name'] for b in bots]

    count_word = {
        2: "two", 3: "three", 4: "four"
    }.get(num_bots, str(num_bots))

    quest_context = (
        f"{acceptor_name} just picked up the "
        f"quest \"{quest_name}\" "
        f"(level {quest_level}) for the group "
        f"in {zone_name}. Current Status: "
        f"PREPARATION. You have the instructions"
        f" but haven't begun yet. Focus on the "
        f"task ahead, the travel required, or "
        f"the plan of attack. Use 'we' language."
    )
    if quest_details:
        quest_context += (
            f" Quest description: {quest_details}"
        )
    if quest_objectives:
        quest_context += (
            f" Objectives: {quest_objectives}"
        )

    parts = []
    if is_rp:
        parts.append(
            f"Generate a short in-character party "
            f"chat exchange between {count_word} "
            f"adventurers discussing a newly "
            f"accepted quest."
        )
    else:
        parts.append(
            f"Generate a short casual party chat "
            f"exchange between {count_word} WoW "
            f"players discussing a newly "
            f"accepted quest."
        )

    parts.append(quest_context)

    zone_flav = get_zone_flavor(zone_id)
    if zone_flav:
        parts.append(
            f"Zone context: {zone_flav}"
        )

    # Speakers with traits and class/race
    parts.append(
        f"Speakers: {', '.join(bot_names)}"
    )
    _append_bots_with_rp(
        parts, bots, traits_map, is_rp
    )

    if speaker_talent_context:
        parts.append(speaker_talent_context)

    # Tone and twist
    tone = pick_random_tone(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )
    parts.append(f"Overall tone: {tone}")
    if twist:
        parts.append(f"Creative twist: {twist}")

    if num_bots > 2:
        parts.append(
            "IMPORTANT: EVERY speaker MUST have "
            "at least one message — do NOT skip "
            "any participant."
        )

    length_hint = _pick_length_hint(mode)
    if is_rp:
        parts.append(
            "Guidelines: Stay in-character for "
            "race and class; no game terms or "
            f"OOC; {length_hint}; "
        )
    else:
        parts.append(
            "Guidelines: Sound like normal "
            "people chatting in a game; casual "
            f"and relaxed; {length_hint}; "
        )

    parts.append(
        "Discuss the new quest — anticipation, "
        "caution, eagerness, or planning. Focus "
        "on the journey ahead, not the outcome. "
        "Don't repeat themes from recent chat."
    )

    spices = pick_personality_spices(
        mode=mode,
        spice_count_override=_spice_count,
    )
    if spices:
        parts.append(
            "Background feelings (texture, "
            "not the topic): "
            + "; ".join(spices)
        )

    if chat_history:
        parts.append(
            "Recent party chat for context "
            "(don't repeat these):\n"
            + chat_history
        )

    prompt = '\n'.join(parts)

    return append_conversation_json_instruction(
        prompt, bot_names, msg_count,
        allow_action=allow_action,
    )
