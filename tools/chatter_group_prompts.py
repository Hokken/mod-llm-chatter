"""Group prompt builders extracted from chatter_group (N5)."""

import logging
import random

from chatter_shared import (
    get_chatter_mode,
    get_zone_flavor,
    get_dungeon_flavor,
    get_dungeon_bosses,
    build_race_class_context,
    build_bot_state_context,
    format_item_link,
    find_addressed_bot,
    query_quest_turnin_npc,
    append_json_instruction,
)
from chatter_prompts import (
    pick_random_tone,
    pick_random_mood,
    maybe_get_creative_twist,
    get_environmental_context,
    pick_personality_spices,
)
from chatter_constants import (
    RACE_SPEECH_PROFILES,
    LENGTH_HINTS,
    RP_LENGTH_HINTS,
    CLASS_ROLE_MAP,
)

logger = logging.getLogger(__name__)

# Keep in sync from chatter_group.init_group_config
_spice_count = 2


def set_prompt_spice_count(value: int):
    """Set spice count used by moved prompt builders."""
    global _spice_count
    _spice_count = max(0, min(int(value), 5))


def _pick_length_hint(mode):
    """Pick a random length hint with chance of
    allowing longer messages. Matches general
    chatter's variable length system.
    """
    is_rp = (mode == 'roleplay')
    pool = RP_LENGTH_HINTS if is_rp else LENGTH_HINTS
    hint = random.choice(pool)
    long_chance = 15 if is_rp else 12
    if random.randint(1, 100) <= long_chance:
        return (
            f"Length: {hint}\n"
            f"Length mode: long allowed (up to "
            f"~200 chars) if it feels natural"
        )
    return (
        f"Length: {hint}\n"
        f"Length mode: short/medium only "
        f"(avoid long messages)"
    )
def build_bot_greeting_prompt(
    bot, traits, mode,
    chat_history="", members=None,
    player_name="", group_size=0,
    allow_action=True,
):
    """Build the LLM prompt for a group greeting.

    Uses tone/mood/twist system from ambient chatter
    for variety. RP mode includes race speech flavor.

    Args:
        bot: dict with name, class, race, level
        traits: list of 3 trait strings
        mode: 'normal' or 'roleplay'
        chat_history: formatted recent chat string
        members: list of group member names
        player_name: real player's name (from C++)
        group_size: total group members including
            this bot
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group greeting creativity: tone={tone}, "
        f"mood={mood}, twist={twist}"
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

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}"
        f"{rp_context}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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

    # If just player + this bot (group_size=2),
    # 80% chance to use the player's name
    use_player_name = (
        player_name
        and group_size == 2
        and random.random() < 0.8
    )

    # Greetings should be short — when inviting
    # multiple bots quickly, long messages flood chat
    # 70% short, 30% medium
    roll = random.random()
    if roll < 0.70:
        length_hint = "short (5-10 words)"
    else:
        length_hint = "a short sentence (10-16 words)"

    prompt += (
        f"\nYou just joined a party with a real "
        f"player. Say a greeting in party chat.\n"
        f"Length: {length_hint}\n"
        f"Length mode: short only (keep it brief)\n\n"
        f"Your greeting should reflect your "
        f"personality traits. For example:\n"
        f"- A 'friendly, eager' bot might say: "
        f"\"Hey! Ready to go whenever you are\"\n"
        f"- A 'cynical, reserved' bot might say: "
        f"\"Sure, let's get this over with\"\n"
        f"- A 'sarcastic, laid-back' bot might "
        f"say: \"Oh good, I was getting bored\"\n\n"
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
):
    """Build prompt for an existing bot welcoming
    a new member to the group.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)

    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group welcome creativity: tone={tone}, "
        f"mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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


def build_kill_reaction_prompt(
    bot, traits, creature_name, is_boss, is_rare,
    mode, chat_history="", extra_data=None,
    allow_action=True,
):
    """Build prompt for a bot reacting to a kill.

    Boss kills get more excited prompts.
    Rare kills get 'nice find' style prompts.
    Personality traits influence the reaction.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
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

    logger.info(
        f"Group kill creativity: tone={tone}, "
        f"mood={mood}, twist={twist}"
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
        kill_context = (
            f"Your party just killed the boss "
            f"{creature_name}! This was a big fight."
        )
    elif is_rare:
        kill_context = (
            f"Your party just killed a rare mob: "
            f"{creature_name}. Nice find!"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
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

    logger.info(
        f"Group loot creativity: tone={tone}, "
        f"mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
    extra_data=None, allow_action=True,
):
    """Build prompt for a bot's battle cry when
    engaging a creature. Very short — must feel
    like real-time combat chat.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
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

    logger.info(
        f"Group combat creativity: tone={tone}, "
        f"mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
):
    """Build prompt for a bot reacting to a
    groupmate dying. The reactor is a DIFFERENT
    bot. Works for both bot and player deaths.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(reactor_traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
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

    logger.info(
        f"Group death creativity: tone={tone}, "
        f"mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
):
    """Build prompt for a bot reacting to someone
    leveling up. Always congratulatory/excited.
    If is_bot=True, reacting to another bot.
    If is_bot=False, reacting to the real player.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group levelup creativity: tone={tone}, "
        f"mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
):
    """Build prompt for a bot reacting to a quest
    completion. Tone varies: relief, satisfaction,
    excitement depending on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group quest complete creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group quest objectives creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
):
    """Build prompt for a bot reacting to an
    achievement being earned. Achievements are
    special — more excited than regular events.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group achievement creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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


def build_spell_cast_reaction_prompt(
    bot, traits, caster_name, spell_name,
    spell_category, target_name, mode,
    chat_history="", members=None,
    dungeon_bosses=None, extra_data=None,
    allow_action=True,
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
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
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

    logger.info(
        f"Group spell cast creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    if state_ctx:
        prompt += f"{state_ctx}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{situation}\n\n"
        f"{style}\n\n"
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
    allow_action=True,
):
    """Build prompt for a bot responding to a real
    player's party chat message. The bot should
    reply naturally and contextually.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Player response creativity: tone={tone},"
        f" mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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

    prompt += (
        f"{rp_context}\n\n"
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
        f"- Keep your response proportional to "
        f"what was said. Simple statements or "
        f"questions only need brief replies"
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
):
    """Build prompt for a bot reacting to being
    resurrected. The bot itself was just rezzed
    and reacts with gratitude, relief, or drama.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group resurrect creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
):
    """Build prompt for a bot commenting on arriving
    in a new zone.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group zone transition creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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

    # Try to get atmospheric zone flavor
    zone_flavor = get_zone_flavor(zone_id)
    zone_desc = ""
    if zone_flavor:
        zone_desc = (
            f"\nZone atmosphere: {zone_flavor}\n"
        )

    if is_rp:
        style = (
            "Comment in-character on arriving "
            "in this new area. Explorers get "
            "excited, cautious types express "
            "concern, warriors comment on "
            "potential threats."
        )
    else:
        style = (
            "Make a casual comment about "
            "arriving in a new zone. Natural "
            "and brief."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"Your party just arrived in "
        f"{zone_name}."
        f"{zone_desc}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {zone_name} by name\n"
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
):
    """Build prompt for a bot reacting to the group
    accepting a new quest. Tone varies: excited,
    curious, cautious, matter-of-fact depending
    on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group quest accept creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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

def build_discovery_reaction_prompt(
    bot, traits, area_name, player_name,
    player_class, xp_amount, mode,
    chat_history="", allow_action=True,
):
    """Build prompt for a bot reacting to the group
    discovering a new area. Should feel like arriving
    somewhere new — wonder, excitement, caution, or
    recognition depending on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group discovery creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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

    discovery_context = (
        f"Your group just discovered a new area: "
        f"{area_name}! This is a first-time "
        f"discovery — the group has never been "
        f"here before."
    )

    if is_rp:
        style = (
            "React in-character to discovering "
            "this new place. Comment on the "
            "scenery, what you've heard about it, "
            "whether it looks dangerous, or the "
            "thrill of exploring together."
        )
    else:
        style = (
            "Make a casual comment about "
            "discovering a new area. Natural "
            "and brief — like an explorer "
            "reacting to a new place."
        )

    prompt = (
        f"You are {bot['name']}, a level "
        f"{bot['level']} {bot['race']} "
        f"{bot['class']} in World of Warcraft.\n"
        f"Your personality: {trait_str}\n"
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
    )
    if twist:
        prompt += f"Creative twist: {twist}\n"
    prompt += (
        f"{rp_context}\n\n"
        f"{discovery_context}\n\n"
        f"{style}\n\n"
        f"Say a reaction in party chat.\n"
        f"{_pick_length_hint(mode)}\n"
        f"Rules:\n"
        f"- No quotes, no emojis\n"
        f"- Can mention {area_name} by name\n"
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
):
    """Build prompt for a bot reacting to entering
    a dungeon or raid instance.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=1.0, mode=mode
    )

    logger.info(
        f"Group dungeon entry creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
):
    """Build prompt for a bot reacting to a total
    party wipe. Dramatic, frustrated, humorous,
    or resigned depending on personality.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
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

    logger.info(
        f"Group wipe creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
):
    """Build prompt for a bot commenting on a
    corpse run. Either the bot died (self), or
    the real player died and the bot reacts.
    """
    is_rp = (mode == 'roleplay')
    trait_str = ', '.join(traits)
    tone = pick_random_tone(mode)
    mood = pick_random_mood(mode)
    twist = maybe_get_creative_twist(
        chance=0.5, mode=mode
    )

    logger.info(
        f"Corpse run creativity: "
        f"tone={tone}, mood={mood}, twist={twist}"
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
        f"Your tone: {tone}\n"
        f"Your mood: {mood}\n"
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
    allow_action=True,
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
    allow_action=True,
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
    allow_action=True,
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
