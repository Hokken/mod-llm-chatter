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
    instance_has_sky,
    build_race_class_context,
    build_bot_identity,
    build_anti_repetition_context,
    get_recent_zone_messages,
    append_json_instruction,
    localize_creature_name,
    get_chatter_mode,
)
from chatter_mode import (
    build_player_prompt_header,
    is_roleplay,
)
from chatter_prompts import (
    pick_personality_spices,
    build_environmental_context_lines,
)

from chatter_location_topics import roll_location_topic

LOG = logging.getLogger("chatter_raid_prompts")

# -- Raid lore constants ---------------------------------

RAID_LORE = {
    # ── WotLK ──────────────────────────────────────
    'Icecrown Citadel': {
        'lore': (
            'The Lich King\'s fortress, a '
            'cathedral of saronite raised '
            'around the Frozen Throne in the '
            'black ice of Icecrown. The Ashen '
            'Verdict, the union of the Argent '
            'Crusade and the Knights of the '
            'Ebon Blade, leads the assault '
            'through its halls against Arthas '
            'and his most loyal servants.'),
        'tone': 'Dark, grim, desperate, momentous.',
        'landmarks': (
            'The Lower Spire, the Plagueworks, '
            'the Crimson Hall and the Frostwing '
            'Halls rising toward the Frozen '
            'Throne. Saronite spires, bone and '
            'black ice, and a cold that seeps '
            'into the soul.'),
    },
    'Ulduar': {
        'lore': (
            'The greatest titan city on '
            'Azeroth, hidden in the Storm '
            'Peaks, once home to the keepers '
            'and their engines of creation. Its '
            'guardians have turned against all '
            'intruders, and whispers speak of a '
            'great evil imprisoned in its '
            'depths that has corrupted the '
            'city.'),
        'tone': (
            'Awe-inspiring, ancient, '
            'mysterious, foreboding.'),
        'landmarks': (
            'Colossal gates and siege grounds, '
            'the halls of the keepers, a '
            'starlit observatory, and passages '
            'descending into darkness. Gleaming '
            'titan metal, carved stone and '
            'humming machinery.'),
    },
    'Naxxramas': {
        'lore': (
            'Kel\'Thuzad\'s necropolis, a '
            'nerubian ziggurat torn from the '
            'earth and raised into the sky by '
            'the Lich King, now hovering over '
            'the Dragonblight to besiege '
            'Wintergarde. It holds the '
            'Scourge\'s foulest laboratories and '
            'its most dreaded commanders.'),
        'tone': 'Creepy, grim, oppressive.',
        'landmarks': (
            'Four quarters: webbed crypts of '
            'the nerubians, plague-filled '
            'laboratories, the halls of the '
            'death knights and the stitched '
            'constructs, and the frozen lair of '
            'a great frost wyrm. Green slime, '
            'rotting flesh and dark stone.'),
    },
    'Vault of Archavon': {
        'lore': (
            'A titan vault beneath Wintergrasp '
            'Fortress, holding relics of untold '
            'power. Ancient stone watchers '
            'guard it and resent every '
            'intruder, and only those who hold '
            'the fortress above may enter.'),
        'tone': 'Ancient, solemn, watchful.',
        'landmarks': (
            'Vast, bare titan chambers of '
            'carved stone, guarded by giant '
            'stone and elemental watchers. '
            'Silence, dust and the faint hum of '
            'old machinery.'),
    },
    'The Obsidian Sanctum': {
        'lore': (
            'The black dragonflight\'s chamber '
            'in the Chamber of the Aspects '
            'beneath Wyrmrest Temple, where '
            'Sartharion the Onyx Guardian '
            'watches over a clutch of twilight '
            'dragon eggs with three twilight '
            'drakes at his side.'),
        'tone': 'Fiery, intense, menacing.',
        'landmarks': (
            'Obsidian islands between rivers of '
            'lava, each drake on its own '
            'island. An orange and red glow, '
            'shimmering heat and the stench of '
            'sulfur.'),
    },
    'The Eye of Eternity': {
        'lore': (
            'The personal domain of Malygos, '
            'the blue Aspect of Magic, above '
            'the Nexus on Coldarra. From here '
            'the Spell-Weaver wages his war to '
            'reclaim dominion over all the '
            'arcane energies of Azeroth, and he '
            'will tolerate no mortal '
            'spellcaster.'),
        'tone': (
            'Arcane, otherworldly, '
            'overwhelming.'),
        'landmarks': (
            'A disc of magical force floating '
            'in an endless void of swirling '
            'blue and violet arcane energy and '
            'stars, where the ley lines of the '
            'world converge.'),
    },
    'The Ruby Sanctum': {
        'lore': (
            'The red dragonflight\'s sanctum in '
            'the Chamber of the Aspects beneath '
            'Wyrmrest Temple, a refuge of the '
            'red flight\'s eggs. Its guardians '
            'have fallen silent, and a dark '
            'power has broken in to strike at '
            'the red dragonflight.'),
        'tone': 'Urgent, fiery, ominous.',
        'landmarks': (
            'Warm ruby light, green growth and '
            'red dragon eggs, now scarred by '
            'fire and shadow. Slain guardians '
            'and shattered stones lie at the '
            'portal.'),
    },
    'Trial of the Crusader': {
        'lore': (
            'The Argent Coliseum in Icecrown, '
            'built by the Argent Crusade under '
            'Highlord Tirion Fordring to test '
            'the champions worthy of the final '
            'assault on the Lich King. The '
            'Alliance and the Horde compete '
            'before the crowds, their old '
            'rivalry flaring in the stands.'),
        'tone': 'Competitive, proud, tense.',
        'landmarks': (
            'A grand tournament arena with '
            'banners, cheering stands and the '
            'crusade\'s leaders watching from '
            'above, at the very doorstep of the '
            'Lich King\'s fortress.'),
    },
    # ── TBC ────────────────────────────────────────
    'Karazhan': {
        'lore': (
            'The ivory tower of Medivh, the '
            'last Guardian of Tirisfal, in '
            'Deadwind Pass, on a nexus of ley '
            'lines where reality is weak. A '
            'curse has lain over it since his '
            'death, and now an evil presence '
            'has claimed it, its halls full of '
            'spirits, demons and echoes of the '
            'past.'),
        'tone': 'Eerie, magical, surreal.',
        'landmarks': (
            'A ghostly ballroom feast, an opera '
            'house where phantom actors '
            'perform, a vast library and a '
            'menagerie, all in dusty grandeur. '
            'Rooms seem to shift, and the past '
            'replays itself.'),
    },
    'Gruul\'s Lair': {
        'lore': (
            'A cavern in the northern Blade\'s '
            'Edge Mountains, home of Gruul the '
            'Dragonkiller, overlord of the '
            'gronn, and his son, the ogre High '
            'King Maulgar, who rule the ogres '
            'of the mountains through fear and '
            'brute strength.'),
        'tone': 'Brutal, primal, savage.',
        'landmarks': (
            'Raw stone caves, crude ogre '
            'banners and the bones of slain '
            'dragons as trophies. The ground '
            'shakes under the steps of giants.'),
    },
    'Magtheridon\'s Lair': {
        'lore': (
            'A chamber deep beneath Hellfire '
            'Citadel where the pit lord '
            'Magtheridon, once master of '
            'Outland, lies chained since '
            'Illidan defeated him. Fel orc '
            'channelers keep his bonds in place '
            'while his blood is harvested to '
            'breed the Fel Horde.'),
        'tone': 'Oppressive, demonic, furious.',
        'landmarks': (
            'A single great chamber of fel fire '
            'and brimstone, the ceiling cracked '
            'by the demon\'s rage, and the '
            'chains and channelers around him.'),
    },
    'Serpentshrine Cavern': {
        'lore': (
            'The lair of Lady Vashj, the naga '
            'sorceress who serves Illidan, deep '
            'within Coilfang Reservoir, where '
            'the waters drained from '
            'Zangarmarsh collect. Her '
            'lieutenants guard the shrine, and '
            'her naga swarm its waters.'),
        'tone': 'Elegant, aquatic, treacherous.',
        'landmarks': (
            'Waterfalls, luminous pools and '
            'bridges over underground lakes, '
            'coral pillars and naga '
            'architecture, all bathed in an '
            'eerie blue light.'),
    },
    'Tempest Keep': {
        'lore': (
            'The naaru fortress floating above '
            'Netherstorm, seized by the blood '
            'elves of Kael\'thas Sunstrider, the '
            'Sun King, who rule it with stolen '
            'naaru technology and drain the '
            'power of a captive naaru.'),
        'tone': 'Arcane, alien, majestic.',
        'landmarks': (
            'Shimmering crystal halls, floating '
            'platforms, phoenixes and arcane '
            'machinery, with views over the '
            'shattered, storm-wracked lands of '
            'Netherstorm.'),
    },
    'Battle for Mount Hyjal': {
        'lore': (
            'A journey through the Caverns of '
            'Time to the Battle of Mount Hyjal '
            'at the end of the Third War, when '
            'humans, orcs and night elves stood '
            'together against the Burning '
            'Legion and the Scourge as '
            'Archimonde marched on the World '
            'Tree.'),
        'tone': 'Epic, heroic, desperate.',
        'landmarks': (
            'The human base under Jaina '
            'Proudmoore, the Horde base under '
            'Thrall, and the night elf camp '
            'beneath Nordrassil. Burning '
            'forests and endless waves of '
            'demons and undead.'),
    },
    'Black Temple': {
        'lore': (
            'Once the draenei Temple of '
            'Karabor, conquered by Gul\'dan\'s '
            'Shadow Council and later held by '
            'the Burning Legion, now the '
            'fortress of Illidan Stormrage, the '
            'self-proclaimed Lord of Outland, '
            'guarded by his naga, blood elves, '
            'Broken, demons and fel orcs.'),
        'tone': 'Dark, grand, corrupted.',
        'landmarks': (
            'Sprawling courtyards, sewers and '
            'grand halls of the old temple, '
            'defiled altars, cracked holy '
            'symbols, green fel fire, and '
            'Illidan\'s throne at the summit.'),
    },
    'Sunwell Plateau': {
        'lore': (
            'The holiest place of the elves on '
            'the Isle of Quel\'Danas, where the '
            'Sunwell sustained Quel\'Thalas for '
            'millennia. In recent times the '
            'Burning Legion has sought to use '
            'it as a gateway for the eredar '
            'lord Kil\'jaeden.'),
        'tone': 'Holy, desperate, climactic.',
        'landmarks': (
            'Pristine elven courtyards and '
            'golden spires, captured naaru, and '
            'the Sunwell itself, its holy light '
            'clashing with demonic darkness.'),
    },
    # ── Classic ────────────────────────────────────
    'Molten Core': {
        'lore': (
            'The burning heart of Blackrock '
            'Mountain, where Thaurissan '
            'summoned Ragnaros the Firelord. A '
            'lake of fire here is a rift to the '
            'Elemental Plane, and the '
            'Firelord\'s flamewakers command his '
            'elementals and the enslaved Dark '
            'Iron dwarves.'),
        'tone': 'Fiery, primal, overwhelming.',
        'landmarks': (
            'Rivers of lava between obsidian '
            'platforms, core hounds, molten '
            'giants and fire elementals. The '
            'heat is crushing.'),
    },
    'Blackwing Lair': {
        'lore': (
            'The lair of the black dragon '
            'Nefarian atop Blackrock Spire, '
            'where, like his father Deathwing, '
            'he breeds a new army, '
            'experimenting with the blood of '
            'every dragonflight to create '
            'unstoppable warriors.'),
        'tone': 'Sinister, cruel, draconic.',
        'landmarks': (
            'Halls of dark iron and dragon '
            'bone, laboratories and hatcheries, '
            'drakonid soldiers and the twisted '
            'results of his experiments.'),
    },
    'Onyxia\'s Lair': {
        'lore': (
            'A volcanic cave in the Wyrmbog of '
            'Dustwallow Marsh, home of Onyxia, '
            'the black dragon broodmother and '
            'daughter of Deathwing, who guards '
            'a vast clutch of eggs.'),
        'tone': 'Intense, claustrophobic, fiery.',
        'landmarks': (
            'A narrow scorched tunnel opening '
            'into an enormous cavern of bones '
            'and egg clutches, its floor a thin '
            'crust over molten rock.'),
    },
    'Ruins of Ahn\'Qiraj': {
        'lore': (
            'The outer ruins of Ahn\'Qiraj '
            'behind the Scarab Wall in '
            'Silithus, where the Qiraji were '
            'sealed a thousand years ago. The '
            'gates have been opened, and their '
            'generals and swarms defend the '
            'ruins against the armies of the '
            'Alliance and the Horde.'),
        'tone': 'Alien, harsh, warlike.',
        'landmarks': (
            'Sand-swept courtyards and colossal '
            'crumbling structures among '
            'silithid hives. Desert wind and '
            'the clicking of countless legs.'),
    },
    'Temple of Ahn\'Qiraj': {
        'lore': (
            'The great temple at the heart of '
            'Ahn\'Qiraj, stronghold of the '
            'Qiraji emperors. Dark whispers say '
            'an Old God stirs in its depths, '
            'regaining his strength after '
            'thousands of years.'),
        'tone': 'Alien, disturbing, oppressive.',
        'landmarks': (
            'Insectile halls, pulsing hives and '
            'twisted chambers leading ever '
            'deeper, where the walls seem alive '
            'and something unseen seems to '
            'watch.'),
    },
    'Zul\'Gurub': {
        'lore': (
            'The ancient capital of the '
            'Gurubashi trolls in the jungles of '
            'Stranglethorn, where the blood god '
            'Hakkar the Soulflayer has '
            'returned. The high priests of the '
            'Bat, Panther, Tiger, Spider and '
            'Snake have fallen under his sway.'),
        'tone': 'Primal, savage, blood-soaked.',
        'landmarks': (
            'Overgrown temples and ziggurats, '
            'sacrificial altars dripping with '
            'blood magic, and the drums and '
            'beasts of the jungle all around.'),
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

    config = extra_data.get('_config') or {}
    mode = get_chatter_mode(config)
    roleplay = is_roleplay(mode)

    # Race/class context
    rc_ctx = ''
    if roleplay and race and cls:
        rc_ctx = build_race_class_context(race, cls)

    # Personality spices
    spice_str = ''
    if config:
        spices = pick_personality_spices(
            config, mode=mode, spice_count_override=1)
        if spices:
            spice_str = ', '.join(spices)

    # Raid info
    raid_name = extra_data.get(
        'raid_name', 'an unknown raid')
    wing = extra_data.get('wing', '')
    difficulty = extra_data.get(
        'difficulty', 'Normal')
    lore_entry = RAID_LORE.get(raid_name, {})

    env_lines = (
        build_environmental_context_lines()
        if roleplay and instance_has_sky(map_name=raid_name)
        else []
    )

    # Talent context
    talent_ctx = extra_data.get(
        '_talent_context', '')

    # Build the context string
    if roleplay:
        ctx = f"You are {bot_name}"
        if race and cls:
            ctx = build_bot_identity(
                bot_name, race, cls, gender
            )[:-1]
        ctx += f", raiding {raid_name}"
    else:
        ctx = build_player_prompt_header(
            bot_name, race, cls,
            bot_data.get('level'), gender,
            mode, channel='raid',
        )
        ctx += f"\nYour character is raiding {raid_name}"
    if wing:
        ctx += f" ({wing})"
    ctx += f". Difficulty: {difficulty}.\n"
    ctx += "\n".join(env_lines) + "\n"

    if roleplay and lore_entry.get('lore'):
        ctx += f"Lore: {lore_entry['lore']}\n"
    if roleplay and lore_entry.get('landmarks'):
        ctx += (
            f"Setting: {lore_entry['landmarks']}\n")
    if roleplay and lore_entry.get('tone'):
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
    boss_name = localize_creature_name(
        extra_data.get('_db'),
        extra_data.get('boss_name', 'the boss'),
        extra_data.get('boss_entry'))
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
        "ONE short sentence in the configured chat mode. "
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
    boss_name = localize_creature_name(
        extra_data.get('_db'),
        extra_data.get('boss_name', 'the boss'),
        extra_data.get('boss_entry'))

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
        "ONE short sentence in the configured chat mode. "
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
    boss_name = localize_creature_name(
        extra_data.get('_db'),
        extra_data.get('boss_name', 'the boss'),
        extra_data.get('boss_entry'))

    ctx = _raid_base_context(extra_data, bot_data)

    if is_raid_worker:
        ctx += (
            "Address the ENTIRE RAID after a wipe. "
            "Brief, rallying, never blame "
            "individuals.\n"
        )
    else:
        if is_roleplay(get_chatter_mode(
            extra_data.get('_config') or {}
        )):
            ctx += (
                "Talk to your SQUAD after dying. Frustration, dark humor, "
                "or determination.\n"
            )
        else:
            ctx += (
                "Talk to your SQUAD after your character died. React with "
                "mild frustration, analysis, humor, or determination.\n"
            )

    ctx += (
        f"Your raid wiped on {boss_name}.\n"
        "ONE short sentence in the configured chat mode. "
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
    creature_name = localize_creature_name(
        extra_data.get('_db'),
        extra_data.get(
            'creature_name', 'the enemy'),
        extra_data.get('creature_entry'))
    is_boss = bool(int(
        extra_data.get('is_boss', 0)))

    ctx = _raid_base_context(extra_data, bot_data)

    roleplay = is_roleplay(get_chatter_mode(
        extra_data.get('_config') or {}
    ))
    if roleplay:
        ctx += (
            "You are shouting a BATTLE CRY to your entire raid as you "
            "charge into combat.\n"
        )
    else:
        ctx += (
            "Give your raid one quick combat-start callout or hype line.\n"
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
    if roleplay:
        ctx += (
            "Write ONE short, punchy battle cry, 5 to 15 words maximum. "
            "Draw from your race and class identity. No asterisks or "
            "narration; just the cry."
        )
    else:
        ctx += (
            "Write ONE natural raid-chat line, 5 to 15 words maximum. It "
            "may be practical, excited, calm, or lightly playful."
        )
    return append_json_instruction(
        ctx, allow_action=False, skip_emote=True
    )


def _raid_location_lines(extra_data):
    """A topic tied to this raid, roleplay only, at
    LocationTopics.Chance; it replaces the topic hint. The Lore
    line already describes raids that have one; the others get
    the raid's description."""
    if not is_roleplay(get_chatter_mode(
        extra_data.get('_config') or {}
    )):
        return []
    location = roll_location_topic(
        extra_data.get('zone_id'), extra_data.get('map_id'),
    )
    if location is None:
        return []
    has_lore = bool(
        RAID_LORE.get(extra_data.get('raid_name'), {}).get('lore')
    )
    return location.lines(with_description=not has_lore)


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
    location_lines = _raid_location_lines(extra_data)
    if location_lines:
        ctx += "\n".join(location_lines) + "\n"
    else:
        ctx += f"Topic hint: {banter_topics}\n"
    ctx += (
        "ONE short sentence (10-25 words) in the configured chat mode. "
        "No asterisks."
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
    location_lines = _raid_location_lines(extra_data)
    if location_lines:
        ctx += "\n".join(location_lines) + "\n"
    else:
        ctx += f"Topic hint: {topics}\n"
    ctx += (
        "ONE short sentence in the configured chat mode. "
        "No asterisks."
    )
    return append_json_instruction(
        ctx, allow_action=False, skip_emote=True
    )
