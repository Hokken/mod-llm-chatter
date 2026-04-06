"""
chatter_raid_prompts.py — PvE raid-specific prompt
builders for mod-llm-chatter.

Each builder follows the signature:
    (extra_data, bot_data, is_raid_worker=False) -> str

Called by chatter_raids.py handlers via
dual_worker_dispatch.
"""

import logging
import random

from chatter_shared import (
    build_race_class_context,
    build_bot_identity,
    build_anti_repetition_context,
    get_recent_zone_messages,
    append_json_instruction,
)
from chatter_prompts import (
    pick_personality_spices,
    get_time_of_day_context,
)

LOG = logging.getLogger("chatter_raid_prompts")

# -- Raid lore constants ---------------------------------

RAID_LORE = {
    # ── WotLK ──────────────────────────────────────
    'Icecrown Citadel': {
        'lore': (
            'The Lich King\'s throne atop '
            'Icecrown. The Ashen Verdict leads '
            'the final assault against Arthas '
            'and his undead armies.'),
        'tone': 'Dark, desperate, epic.',
        'landmarks': (
            'Lower Spire, Plagueworks, '
            'Crimson Hall, Frostwing Halls, '
            'the Frozen Throne. Saronite and '
            'ice architecture, oppressive cold.'),
    },
    'Ulduar': {
        'lore': (
            'Ancient titan city-prison in the '
            'Storm Peaks. The corrupted keepers '
            'guard Yogg-Saron\'s prison vault. '
            'The grandest raid in Northrend.'),
        'tone': 'Awe-inspiring, mysterious, grand.',
        'landmarks': (
            'Siege area, Antechamber, Keepers '
            'of Ulduar, the Descent into '
            'Madness, the Celestial Planetarium. '
            'Gleaming titan metal and stone.'),
    },
    'Naxxramas': {
        'lore': (
            'Floating necropolis of Kel\'Thuzad '
            'over Dragonblight. Four themed '
            'wings of undead horrors and the '
            'lich\'s inner sanctum.'),
        'tone': 'Creepy, tense, grim.',
        'landmarks': (
            'Arachnid Quarter (giant spiders), '
            'Plague Quarter (disease and '
            'abominations), Military Quarter '
            '(death knight commanders), '
            'Construct Quarter (flesh golems), '
            'Frostwyrm Lair. Green slime and '
            'dark stone.'),
    },
    'Vault of Archavon': {
        'lore': (
            'Titan vault beneath Wintergrasp '
            'Fortress, accessible only to the '
            'faction controlling Wintergrasp.'),
        'tone': 'Quick, practical, loot-focused.',
        'landmarks': (
            'Utilitarian titan chambers. Stone '
            'giants and elemental constructs. '
            'Massive but unadorned.'),
    },
    'The Obsidian Sanctum': {
        'lore': (
            'Volcanic chamber beneath Wyrmrest '
            'Temple where Sartharion guards '
            'black dragon eggs alongside '
            'three drake lieutenants.'),
        'tone': 'Intense, fiery, dragon-themed.',
        'landmarks': (
            'Lava rivers, obsidian platforms, '
            'three drake islands. Orange and '
            'red glow, heat shimmer.'),
    },
    'The Eye of Eternity': {
        'lore': (
            'Malygos\'s sanctum atop the Nexus '
            'above Coldarra. A platform in raw '
            'ley energy where the Spell-Weaver '
            'wages war on all magic users.'),
        'tone': 'Arcane, otherworldly, desperate.',
        'landmarks': (
            'No ground or walls. A disc of '
            'magical force over swirling blue '
            'and violet arcana. The heart of '
            'Azeroth\'s arcane storm.'),
    },
    'The Ruby Sanctum': {
        'lore': (
            'Red dragon sanctum beneath Wyrmrest '
            'Temple, invaded by the twilight '
            'dragonflight. Halion phases between '
            'physical and shadow realms.'),
        'tone': 'Urgent, fiery, apocalyptic.',
        'landmarks': (
            'Chamber shifts between warm ruby '
            'light and cold purple shadow. '
            'The last raid before the Cataclysm.'),
    },
    'Trial of the Crusader': {
        'lore': (
            'Argent Coliseum in Icecrown. '
            'A tournament arena that collapses '
            'into nerubian caverns below. '
            'Festive competition above, '
            'ancient terror below.'),
        'tone': 'Competitive, tense, dramatic.',
        'landmarks': (
            'Tournament arena with banners and '
            'crowds, underground nerubian '
            'cavern. Anub\'arak lurks below.'),
    },
    # ── TBC ────────────────────────────────────────
    'Karazhan': {
        'lore': (
            'Medivh\'s haunted tower in '
            'Deadwind Pass. Echoes of the Last '
            'Guardian play out eternally in '
            'rooms that shift and bend time.'),
        'tone': 'Eerie, magical, surreal.',
        'landmarks': (
            'Ballroom, Opera stage, Chess '
            'event, Netherspace. '
            'Spectral dinner party. The tower '
            'exists partially outside reality.'),
    },
    'Gruul\'s Lair': {
        'lore': (
            'Rough cavern complex in Blade\'s '
            'Edge Mountains. Home to Gruul the '
            'Dragonkiller and his gronn sons. '
            'Dragon bones litter the floor.'),
        'tone': 'Brutal, primal, savage.',
        'landmarks': (
            'Raw stone caves, ogre servants, '
            'dragon bone trophies. No '
            'architecture, just giant fists '
            'and brute force.'),
    },
    'Magtheridon\'s Lair': {
        'lore': (
            'A single brutal chamber beneath '
            'Hellfire Citadel where the pit '
            'lord Magtheridon is chained. '
            'Channelers maintain his prison.'),
        'tone': 'Oppressive, demonic, punishing.',
        'landmarks': (
            'One deadly room. Hellfire energy, '
            'demon blood and brimstone. '
            'No room for error.'),
    },
    'Serpentshrine Cavern': {
        'lore': (
            'Lady Vashj\'s underwater palace '
            'in Coilfang Reservoir. Naga '
            'architecture meets the raw power '
            'of a subterranean ocean.'),
        'tone': (
            'Elegant, aquatic, treacherous.'),
        'landmarks': (
            'Waterfalls, luminous pools, '
            'bridges over underground lakes. '
            'Naga, tidewalkers, colossal '
            'hydras. Corrupted Zangarmarsh '
            'waters.'),
    },
    'Tempest Keep': {
        'lore': (
            'Kael\'thas Sunstrider\'s captured '
            'naaru fortress floating above '
            'Netherstorm. Crystalline draenei '
            'technology repurposed by desperate '
            'blood elves.'),
        'tone': 'Arcane, alien, beautiful.',
        'landmarks': (
            'Shimmering crystal chambers. '
            'Blood elf advisors, void '
            'creatures. Stunning views of '
            'shattered Netherstorm.'),
    },
    'Battle for Mount Hyjal': {
        'lore': (
            'Caverns of Time raid during the '
            'Battle of Mount Hyjal. Waves of '
            'undead and demons assault three '
            'bases in succession with legendary '
            'heroes at your side.'),
        'tone': 'Epic, heroic, desperate.',
        'landmarks': (
            'Alliance base (Jaina), Horde base '
            '(Thrall), night elf camp at '
            'Nordrassil. The forest burns. '
            'Archimonde approaches.'),
    },
    'Black Temple': {
        'lore': (
            'Illidan\'s fortress in Shadowmoon '
            'Valley. A draenei temple corrupted '
            'by demonic occupation. Fel orcs, '
            'demons, naga, and blood elves '
            'serve the Betrayer.'),
        'tone': 'Dark, grand, corrupted.',
        'landmarks': (
            'Sprawling courtyards, sewer '
            'systems, grand halls. Cracked '
            'holy symbols, defiled altars, '
            'green fel fire. Illidan\'s throne '
            'awaits at the summit.'),
    },
    'Sunwell Plateau': {
        'lore': (
            'The heart of the Sunwell on the '
            'Isle of Quel\'Danas. The Burning '
            'Legion attempts to summon '
            'Kil\'jaeden through the Sunwell '
            'itself.'),
        'tone': 'Holy, desperate, climactic.',
        'landmarks': (
            'Pristine elven architecture. '
            'The Sunwell\'s holy light clashes '
            'with demonic darkness. The final '
            'stand of the Burning Crusade.'),
    },
    # ── Classic ────────────────────────────────────
    'Molten Core': {
        'lore': (
            'The burning heart of Blackrock '
            'Mountain. Ragnaros the Firelord '
            'rules this realm of pure fire. '
            'The ultimate trial by fire.'),
        'tone': 'Fiery, apocalyptic, primal.',
        'landmarks': (
            'Lava rivers between obsidian '
            'platforms. Core hounds, molten '
            'giants, flamewakers. The heat '
            'is overwhelming.'),
    },
    'Blackwing Lair': {
        'lore': (
            'Nefarian\'s dark laboratory atop '
            'Blackrock Spire where the black '
            'dragon experiments on other '
            'dragonflights. Clinical and '
            'sinister.'),
        'tone': 'Sinister, experimental, draconic.',
        'landmarks': (
            'Dark iron and dragon bone halls. '
            'Drakonid soldiers, chromatic '
            'drakes, failed experiments. '
            'A mad scientist\'s lair at '
            'dragon scale.'),
    },
    'Onyxia\'s Lair': {
        'lore': (
            'A vast cavern in Dustwallow '
            'Marsh, home to the broodmother '
            'Onyxia. Whelps swarm, lava '
            'bubbles, dragonfire fills the '
            'chamber.'),
        'tone': 'Intense, claustrophobic, fiery.',
        'landmarks': (
            'Narrow scorched tunnel opening '
            'into enormous cavern. Bones, '
            'egg clutches, lava edges.'),
    },
    'Ruins of Ahn\'Qiraj': {
        'lore': (
            'Open-air battlefield in Silithus '
            'where qiraji insectoid forces '
            'mass for war. Sand-swept '
            'courtyards and crumbling temple '
            'ruins.'),
        'tone': 'Alien, harsh, warlike.',
        'landmarks': (
            'Insectoid warriors, obsidian '
            'destroyers. Architecture is '
            'half Egyptian tomb, half insect '
            'hive. Desert wind and clicking '
            'of countless legs.'),
    },
    'Temple of Ahn\'Qiraj': {
        'lore': (
            'Sealed inner sanctum of the '
            'qiraji empire. The old god '
            'C\'Thun lurks within. Walls '
            'pulse with organic growth, '
            'eyes watch from every surface.'),
        'tone': (
            'Alien, disturbing, oppressive.'),
        'landmarks': (
            'Twin emperors\' chamber, '
            'organic corridors, C\'Thun\'s '
            'stomach. Reality bends near '
            'the old god\'s prison. The most '
            'alien place in Azeroth.'),
    },
    'Zul\'Gurub': {
        'lore': (
            'Massive troll temple in '
            'Stranglethorn jungle. The '
            'Gurubashi have unleashed the '
            'blood god Hakkar. Overgrown '
            'courtyards and sacrificial '
            'altars.'),
        'tone': 'Primal, voodoo, tropical.',
        'landmarks': (
            'Snake priests, bat riders, '
            'tiger cultists. Sacrificial '
            'altars dripping with blood '
            'magic. The jungle pulses with '
            'primal voodoo energy.'),
    },
}

# -- Shared constraints ----------------------------------

RAID_EMOTE_GUIDANCE = (
    "NEVER put /slash commands or emote commands "
    "in your message text. No /roar, /cheer, "
    "/say, /yell, /battleshout, /angry, or any "
    "/command. Just write plain speech. Emotes "
    "are handled separately — do NOT include them "
    "in your text at all."
)

BREVITY_INSTRUCTION = (
    "Keep it VERY SHORT. One sentence only. "
    "Aim for roughly 6 to 14 words. Raid chat "
    "is fast and urgent. No paragraphs, no "
    "poetry, no contemplation."
)


# -- Shared context builder ------------------------------

def _raid_base_context(extra_data, bot_data):
    """Build shared PvE raid context block."""
    # Bot identity
    bot_name = bot_data.get('bot_name', 'Unknown')
    race = bot_data.get('race', '')
    cls = bot_data.get('class', '')
    gender = bot_data.get('gender', '')
    traits = bot_data.get('traits')

    # Race/class context
    rc_ctx = ''
    if race and cls:
        rc_ctx = build_race_class_context(race, cls)

    # Personality spices
    config = extra_data.get('_config')
    spice_str = ''
    if config:
        spices = pick_personality_spices(
            config, spice_count_override=1)
        if spices:
            spice_str = ', '.join(spices)

    # Raid info
    raid_name = extra_data.get(
        'raid_name', 'an unknown raid')
    wing = extra_data.get('wing', '')
    difficulty = extra_data.get(
        'difficulty', 'Normal')
    lore_entry = RAID_LORE.get(raid_name, {})

    # Time of day
    _, time_desc = get_time_of_day_context()

    # Talent context
    talent_ctx = extra_data.get(
        '_talent_context', '')

    # Build the context string
    ctx = f"You are {bot_name}"
    if race and cls:
        ctx = build_bot_identity(
            bot_name, race, cls, gender
        )[:-1]
    ctx += (
        f", raiding {raid_name}"
    )
    if wing:
        ctx += f" ({wing})"
    ctx += f". Difficulty: {difficulty}.\n"
    ctx += f"Time of day: {time_desc}.\n"

    if lore_entry.get('lore'):
        ctx += f"Lore: {lore_entry['lore']}\n"
    if lore_entry.get('landmarks'):
        ctx += (
            f"Setting: {lore_entry['landmarks']}\n")
    if lore_entry.get('tone'):
        ctx += f"Tone: {lore_entry['tone']}\n"

    if traits:
        trait_str = ', '.join(
            str(t) for t in traits[:3])
        ctx += f"Your personality: {trait_str}\n"

    if rc_ctx:
        ctx += f"{rc_ctx}\n"

    if spice_str:
        ctx += (
            f"Background flavor: {spice_str}\n")

    if talent_ctx:
        ctx += f"{talent_ctx}\n"

    # Anti-repetition
    db = extra_data.get('_db')
    if db:
        zone_id = int(
            extra_data.get('zone_id', 0))
        if zone_id:
            recent = get_recent_zone_messages(
                db, zone_id, limit=8, minutes=10)
            anti_rep = build_anti_repetition_context(
                recent, max_items=6)
            if anti_rep:
                ctx += f"{anti_rep}\n"

    ctx += f"\n{BREVITY_INSTRUCTION}\n"
    ctx += f"{RAID_EMOTE_GUIDANCE}\n"

    return ctx


# -- Prompt builders -------------------------------------

def build_raid_boss_pull_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Boss pull — adrenaline, battle cries."""
    boss_name = extra_data.get(
        'boss_name', 'the boss')
    raid_name = extra_data.get(
        'raid_name', 'the raid')
    wing = extra_data.get('wing', '')
    difficulty = extra_data.get(
        'difficulty', 'Normal')

    ctx = _raid_base_context(extra_data, bot_data)

    if is_raid_worker:
        ctx += (
            "You are addressing the ENTIRE RAID "
            "over raid chat. Speak with authority "
            "— rally, command, declare. Short bold "
            "statement. Never casual.\n"
        )
    else:
        ctx += (
            "You are talking to your SQUAD in "
            "party chat. Raw emotion — nervousness, "
            "excitement, adrenaline. Intimate talk "
            "between comrades about to fight.\n"
        )

    if wing:
        ctx += (
            f"Your raid is about to engage "
            f"{boss_name} in {wing} of "
            f"{raid_name} ({difficulty}).\n"
        )
    else:
        ctx += (
            f"Your raid is about to engage "
            f"{boss_name} in "
            f"{raid_name} ({difficulty}).\n"
        )

    ctx += (
        "ONE short sentence. Stay in character. "
        "No asterisks."
    )
    return append_json_instruction(
        ctx,
        allow_action=(not is_raid_worker),
        skip_emote=is_raid_worker,
    )


def build_raid_boss_kill_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Boss kill — celebration, triumph."""
    boss_name = extra_data.get(
        'boss_name', 'the boss')

    ctx = _raid_base_context(extra_data, bot_data)

    if is_raid_worker:
        ctx += (
            "Victory announcement to the ENTIRE "
            "RAID. Bold, triumphant, brief.\n"
        )
    else:
        ctx += (
            "Celebration with your SQUAD. Relief, "
            "joy, exhaustion, humor.\n"
        )

    ctx += (
        f"Your raid has defeated {boss_name}!\n"
        "ONE short sentence. Stay in character. "
        "No asterisks."
    )
    return append_json_instruction(
        ctx,
        allow_action=(not is_raid_worker),
        skip_emote=is_raid_worker,
    )


def build_raid_boss_wipe_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Boss wipe — grief, determination."""
    boss_name = extra_data.get(
        'boss_name', 'the boss')

    ctx = _raid_base_context(extra_data, bot_data)

    if is_raid_worker:
        ctx += (
            "Address the ENTIRE RAID after a wipe. "
            "Brief, rallying, never blame "
            "individuals.\n"
        )
    else:
        ctx += (
            "Talk to your SQUAD after dying. "
            "Frustration, dark humor, "
            "determination.\n"
        )

    ctx += (
        f"Your raid wiped on {boss_name}.\n"
        "ONE short sentence. Stay in character. "
        "No asterisks."
    )
    return append_json_instruction(
        ctx,
        allow_action=(not is_raid_worker),
        skip_emote=is_raid_worker,
    )


def build_raid_battle_cry_prompt(
    extra_data, bot_data, is_raid_worker=True
):
    """Short battle cry for raid chat during
    boss/elite combat.

    Kept very short (5-15 words) and punchy.
    Race/class/personality flavored.
    """
    creature_name = extra_data.get(
        'creature_name', 'the enemy')
    is_boss = bool(int(
        extra_data.get('is_boss', 0)))

    ctx = _raid_base_context(extra_data, bot_data)

    ctx += (
        "You are shouting a BATTLE CRY to your "
        "entire raid as you charge into combat.\n"
    )
    if is_boss:
        ctx += (
            f"Your raid is engaging the boss "
            f"{creature_name}!\n"
        )
    else:
        ctx += (
            f"Your raid is fighting the elite "
            f"{creature_name}!\n"
        )
    ctx += (
        "Write ONE short, punchy battle cry. "
        "5 to 15 words maximum. Think war shouts, "
        "rallying calls, or fierce declarations. "
        "Draw from your race and class identity.\n"
        "Examples of the style (do NOT copy these): "
        "\"For the Light!\", \"Into the fire!\", "
        "\"Elune guide my arrows!\", "
        "\"Blood and thunder!\"\n"
        "No asterisks. No narration. Just the cry."
    )
    return append_json_instruction(
        ctx, allow_action=False, skip_emote=True
    )


def build_raid_banter_prompt(
    extra_data, bot_data, is_raid_worker=True
):
    """Casual banter between pulls — humorous,
    lore-aware, environment-focused."""
    ctx = _raid_base_context(extra_data, bot_data)

    banter_topics = random.choice([
        "a funny observation about the raid "
        "environment or architecture",
        "a playful jab at a fellow raider or "
        "a class stereotype",
        "a lore tidbit or rumor about this place",
        "a humorous complaint about the trash "
        "mobs or the walk back",
        "an irreverent comment about the bosses",
        "wondering aloud about something weird "
        "you noticed in this raid",
        "a joke about repair bills, wipe recovery, "
        "or consumable costs",
        "casual banter about food, drink, or "
        "downtime activities",
        "a sarcastic remark about raid readiness "
        "or someone going AFK",
        "a lighthearted comment about loot drama "
        "or RNG luck",
    ])

    ctx += (
        "You are making casual BANTER in raid "
        "chat between pulls. The mood is relaxed. "
        "Be humorous, observational, or playful. "
        "NOT motivational or tactical — save that "
        "for morale. This is just friends chatting "
        "in a dungeon.\n"
    )
    ctx += f"Topic hint: {banter_topics}\n"
    ctx += (
        "ONE short sentence (10-25 words). Stay "
        "in character. No asterisks."
    )
    return append_json_instruction(
        ctx, allow_action=False, skip_emote=True
    )


def build_raid_morale_prompt(
    extra_data, bot_data, is_raid_worker=True
):
    """Idle morale — banter between pulls."""
    ctx = _raid_base_context(extra_data, bot_data)

    topics = random.choice([
        "morale boost or encouragement",
        "tactical banter about the next pull",
        "readiness check or gear question",
        "raid encouragement or hype",
        "idle commentary between pulls",
        "joke or light trash talk",
        "compliment a recent play or save",
        "reminisce about a past wipe or close call",
        "comment on the raid's architecture or "
        "atmosphere",
        "complain about repair bills or consumables",
        "speculation about what loot will drop",
        "lore or history of this raid instance",
        "banter about who is pulling their weight",
        "comment on how the raid is progressing",
        "nervous anticipation about a tough boss "
        "ahead",
        "ask if everyone has food and flask buffs",
        "joke about AFK raiders or slow pullers",
        "share a rumor or gossip about this place",
        "comment on the trash mobs they just "
        "fought through",
    ])

    ctx += (
        "You are chatting in RAID chat between "
        "pulls. The mood is relaxed but focused "
        "— a seasoned raider making conversation "
        "or checking readiness. Not urgent "
        "commander voice. Casual and "
        "authoritative.\n"
    )
    ctx += f"Topic hint: {topics}\n"
    ctx += (
        "ONE short sentence. Stay in character. "
        "No asterisks."
    )
    return append_json_instruction(
        ctx, allow_action=False, skip_emote=True
    )
