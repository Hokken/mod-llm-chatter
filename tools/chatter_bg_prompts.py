"""
chatter_bg_prompts.py — BG-specific prompt builders for
mod-llm-chatter.

Uses get_class_name() from chatter_shared to resolve
class IDs from C++ extra_data.

Each builder follows the signature:
    (extra_data, bot_data, is_raid_worker=False) -> str

Called by chatter_battlegrounds.py handlers via
dual_worker_dispatch.
"""

import logging
import random

from chatter_shared import (
    get_class_name,
    build_race_class_context,
    build_anti_repetition_context,
    get_recent_zone_messages,
    append_json_instruction,
)
from chatter_prompts import (
    pick_personality_spices,
    get_time_of_day_context,
)

LOG = logging.getLogger("chatter_bg_prompts")

# ── BG Lore constants ────────────────────────────────

BG_LORE = {
    1: {  # AV (BATTLEGROUND_AV = 1)
        'name': 'Alterac Valley',
        'alliance_faction': 'Stormpike Expedition',
        'horde_faction': 'Frostwolf Clan',
        'lore': (
            'The frozen mountain conflict \u2014 '
            'Stormpike dwarves vs Frostwolf '
            'orcs in the Alterac Mountains.'),
        'tone': (
            'Epic, large-scale, war-like. '
            '40v40 feels like an actual battle.'),
        'objectives': (
            'Kill the enemy general. '
            'Capture towers and graveyards.'),
        'landmarks': (
            'Key locations: Stormpike Base, '
            'Dun Baldar, Icewing Bunker, '
            'Stonehearth Graveyard, Snowfall '
            'Graveyard, Iceblood Tower, '
            'Tower Point, Frostwolf Graveyard, '
            'Frostwolf Keep. Do NOT mention '
            'locations from other battlegrounds.'),
    },
    2: {  # WSG (BATTLEGROUND_WS = 2)
        'name': 'Warsong Gulch',
        'alliance_faction': 'Silverwing Sentinels',
        'horde_faction': 'Warsong Outriders',
        'lore': (
            'The lumber war in Ashenvale \u2014 '
            'Silverwing defend the forest, '
            'Warsong seek its resources.'),
        'tone': (
            'Intense, fast, personal. '
            'Small team, every player matters.'),
        'objectives': (
            'Capture the enemy flag 3 times.'),
        'landmarks': (
            'Key locations: Silverwing Hold '
            '(Alliance base), Warsong Fort '
            '(Horde base), the tunnel, midfield, '
            'the ramp. Do NOT mention locations '
            'from other battlegrounds like '
            'mills, farms, or towers.'),
    },
    3: {  # AB (BATTLEGROUND_AB = 3)
        'name': 'Arathi Basin',
        'alliance_faction': 'League of Arathor',
        'horde_faction': 'The Defilers',
        'lore': (
            'The fight for Arathi Highlands '
            'resources between Stromgarde '
            'and Forsaken.'),
        'tone': (
            'Strategic, territorial, spread out. '
            'Reactions about node control.'),
        'objectives': (
            'Control nodes to reach '
            '1600 resources first.'),
        'landmarks': (
            'Key locations: Stables (north, open '
            'pastures with horse pens), Blacksmith '
            '(center crossroads, smoke and anvils), '
            'Lumber Mill (hilltop overlook, wooden '
            'platforms and sawblades), Gold Mine '
            '(southeast cave entrance, mine carts '
            'and torches), Farm (south, fields and '
            'haystacks near a farmhouse). '
            'Do NOT mention locations from '
            'other battlegrounds.'),
    },
    7: {  # EY (BATTLEGROUND_EY = 7)
        'name': 'Eye of the Storm',
        'alliance_faction': 'Alliance',
        'horde_faction': 'Horde',
        'lore': (
            'A Netherstorm battlefield over '
            'a fragment of Draenor.'),
        'tone': (
            'Hybrid tension. Holding bases '
            'while fighting over a central flag.'),
        'objectives': (
            'Control bases and capture the '
            'central flag to reach 1600 points.'),
        'landmarks': (
            'Key locations: Fel Reaver Ruins, '
            'Blood Elf Tower, Draenei Ruins, '
            'Mage Tower, the center flag. '
            'Do NOT mention locations from '
            'other battlegrounds.'),
    },
}

# ── Shared constraints ────────────────────────────────

OBSERVATION_CONSTRAINT = (
    "CRITICAL RULE: You are an observer. React to "
    "what happened. NEVER claim you are doing or "
    "will do something \u2014 your actual behavior may "
    "contradict the message. No action declarations, "
    "no promises, no movement plans. Only reactive "
    "observations and generic encouragement."
)

BREVITY_INSTRUCTION = (
    "Keep it VERY SHORT. One sentence only. "
    "Aim for roughly 6 to 14 words. BG chat is "
    "fast and urgent. No paragraphs, no poetry, "
    "no contemplation, no long explanations."
)

BG_EMOTE_GUIDANCE = (
    "NEVER put /slash commands or emote commands "
    "in your message text. No /roar, /cheer, "
    "/say, /yell, /battleshout, /angry, or any "
    "/command. Just write plain speech. Emotes "
    "are handled separately — do NOT include them "
    "in your text at all."
)



# ── Shared context builder ────────────────────────────

def _bg_base_context(
    extra_data, bot_data,
    db=None, config=None,
    skip_observation_constraint=False
):
    """Build shared BG context block for all prompts.

    Args:
        extra_data: Parsed extra_data from event.
            May contain '_db' and '_config' keys
            injected by the dispatch layer.
        bot_data: Bot traits or lightweight data.
        db: Optional DB connection for anti-rep.
            Falls back to extra_data['_db'].
        config: Optional config dict for spices.
            Falls back to extra_data['_config'].
    """
    # Allow injected refs from dispatch layer
    if db is None:
        db = extra_data.get('_db')
    if config is None:
        config = extra_data.get('_config')
    bg_type_id = int(extra_data.get('bg_type_id', 0))
    lore = BG_LORE.get(bg_type_id, {})
    team = extra_data.get('team', 'Unknown')

    faction_name = lore.get(
        f'{team.lower()}_faction', team)

    score_a = int(
        extra_data.get('score_alliance', 0))
    score_h = int(
        extra_data.get('score_horde', 0))

    # Bot identity (full traits or lightweight)
    bot_name = bot_data.get('bot_name', 'Unknown')
    traits = bot_data.get('traits')
    race = bot_data.get('race', '')
    cls = bot_data.get('class', '')

    # Time of day
    _, time_desc = get_time_of_day_context()

    ctx = (
        f"You are {bot_name}"
    )
    if race and cls:
        ctx += f", a {race} {cls}"
    ctx += (
        f", fighting in "
        f"{lore.get('name', 'a battleground')}. "
        f"You fight for the {faction_name} "
        f"({team}).\n"
        f"Score: Alliance {score_a} \u2014 "
        f"Horde {score_h}.\n"
        f"Alive on your team: "
        f"{extra_data.get('players_alive_team', '?')}. "
        f"Alive on enemy team: "
        f"{extra_data.get('players_alive_enemy', '?')}.\n"
        f"Time of day: {time_desc}.\n"
    )

    # Flag carrier status (WSG)
    friendly_fc = extra_data.get(
        'friendly_flag_carrier')
    enemy_fc = extra_data.get(
        'enemy_flag_carrier')
    if friendly_fc:
        ctx += (
            f"Your teammate {friendly_fc} is "
            f"carrying the enemy flag!\n"
        )
    if enemy_fc:
        ctx += (
            f"Enemy {enemy_fc} is carrying "
            f"YOUR flag!\n"
        )

    # Real players on the team (name + race)
    real_players = extra_data.get('real_players')
    if real_players and isinstance(
            real_players, list):
        parts = []
        for rp in real_players:
            n = rp.get('name', '?')
            r = rp.get('race', '')
            parts.append(
                f"{n} ({r})" if r else n)
        if parts:
            ctx += (
                "Real players on your team: "
                + ", ".join(parts) + ".\n"
            )

    if lore.get('lore'):
        ctx += f"Lore: {lore['lore']}\n"

    if lore.get('landmarks'):
        ctx += f"{lore['landmarks']}\n"

    if traits:
        trait_str = ', '.join(
            str(t) for t in traits[:3])
        ctx += f"Your personality: {trait_str}\n"

    # Race/class personality context
    if race and cls:
        rp_ctx = build_race_class_context(race, cls)
        if rp_ctx:
            ctx += f"{rp_ctx}\n"

    # Personality spices
    if config:
        spices = pick_personality_spices(
            config, spice_count_override=1)
        if spices:
            ctx += (
                f"Background flavor: "
                f"{', '.join(spices)}\n"
            )

    # Talent context (injected by dispatch layer)
    talent_ctx = extra_data.get(
        '_talent_context')
    if talent_ctx:
        ctx += f"{talent_ctx}\n"

    # Anti-repetition
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

    if not skip_observation_constraint:
        ctx += f"\n{OBSERVATION_CONSTRAINT}\n"
    ctx += f"{BREVITY_INSTRUCTION}\n"
    ctx += f"{BG_EMOTE_GUIDANCE}\n"

    return ctx


# ── Prompt builders ───────────────────────────────────

def build_bg_match_start_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Match start \u2014 battle cries, faction pride."""
    ctx = _bg_base_context(extra_data, bot_data)
    ctx += (
        "\nThe gates just opened! The match is "
        "starting. React with a battle cry, "
        "faction pride, or encouragement for "
        "your team. Be fierce and energetic."
    )
    return append_json_instruction(
        ctx, False, skip_emote=True)


def build_bg_match_end_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Match end \u2014 victory or defeat."""
    ctx = _bg_base_context(extra_data, bot_data)
    won = extra_data.get('won', False)

    # Override score with final_score if available
    # (AppendBGContext snapshot may miss the
    # winning capture)
    fs_a = extra_data.get('final_score_alliance')
    fs_h = extra_data.get('final_score_horde')
    if fs_a is not None and fs_h is not None:
        ctx += (
            f"Final score: Alliance {fs_a} "
            f"- Horde {fs_h}.\n"
        )

    # Performance stats (may be absent for bots)
    kb = extra_data.get('player_killing_blows')
    dmg = extra_data.get('player_damage_done')
    heal = extra_data.get('player_healing_done')
    if kb is not None:
        ctx += (
            f"Team performance glimpse: "
            f"{kb} killing blows, "
            f"{dmg} damage, {heal} healing.\n"
        )

    if won:
        ctx += (
            "\nYour team WON! React with "
            "celebration, faction pride, or a "
            "victory cheer. Reference the final "
            "score if meaningful."
        )
    else:
        ctx += (
            "\nYour team LOST. React with "
            "frustration, defiance, or honorable "
            "defeat. No whining \u2014 keep dignity."
        )
    return append_json_instruction(
        ctx, False, skip_emote=True)


def build_bg_flag_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Flag events \u2014 pickup, drop, capture."""
    ctx = _bg_base_context(extra_data, bot_data)
    event_type = extra_data.get('event_type', '')
    flag_team = extra_data.get('flag_team', '')
    team = extra_data.get('team', '')
    score_a = int(
        extra_data.get('score_alliance', 0))
    score_h = int(
        extra_data.get('score_horde', 0))
    exact_score = int(
        extra_data.get('new_score', 0))

    # flag_team = which team's flag was affected.
    # In WSG: you carry the ENEMY flag to score.
    # So flag_team == your team means YOUR flag
    # was taken/dropped by the enemy.
    # For capture events only, flag_team is the
    # scoring team, so flag_team == your team means
    # your team just scored.

    # Player-centric names from C++ extra_data
    carrier = extra_data.get('carrier_name', '')
    scorer = extra_data.get('scorer_name', '')
    dropper = extra_data.get('dropper_name', '')
    carrier_real = extra_data.get(
        'carrier_is_real_player', False)
    scorer_real = extra_data.get(
        'scorer_is_real_player', False)
    dropper_real = extra_data.get(
        'dropper_is_real_player', False)

    if 'picked_up' in event_type:
        if flag_team == team:
            ctx += (
                "\nThe enemy picked up YOUR flag!")
        else:
            if carrier and carrier_real:
                ctx += (
                    f"\n{carrier} grabbed the "
                    "enemy flag! Cheer them on "
                    f"by name ({carrier}).")
            elif carrier:
                ctx += (
                    f"\n{carrier} picked up the "
                    "enemy flag!")
            else:
                ctx += (
                    "\nYour team picked up the "
                    "enemy flag!")
    elif 'dropped' in event_type:
        if flag_team == team:
            # Enemy dropped YOUR flag — good news!
            if dropper:
                ctx += (
                    f"\nThe enemy {dropper} dropped "
                    "your flag! Celebrate, the "
                    "threat is neutralized.")
            else:
                ctx += (
                    "\nThe enemy dropped your flag! "
                    "Celebrate, someone needs to "
                    "return it to base.")
        else:
            # Your team dropped the enemy flag —
            # bad news
            if dropper and dropper_real:
                ctx += (
                    f"\n{dropper} dropped the "
                    "enemy flag! Express concern "
                    f"for {dropper}.")
            else:
                ctx += (
                    "\nThe enemy flag was dropped! "
                    "Someone needs to pick it back "
                    "up before they recover it.")
    elif 'captured' in event_type:
        if flag_team == team:
            enemy_score = (
                score_h if team == 'Alliance'
                else score_a
            )
            ctx += (
                f"\nCURRENT SCORE: Alliance {score_a}, "
                f"Horde {score_h}. "
                "Use these exact numbers if you "
                "mention the score."
            )
            if scorer and scorer_real:
                ctx += (
                    f"\n{scorer} SCORED for your "
                    "team! Celebrate and praise "
                    f"{scorer} by name. "
                    f"They raised your team to "
                    f"{exact_score} captures while "
                    f"the enemy remains on "
                    f"{enemy_score}.")
            elif scorer:
                ctx += (
                    f"\n{scorer} CAPTURED the "
                    f"flag for your team. Your "
                    f"team is now on exactly "
                    f"{exact_score} captures.")
            else:
                ctx += (
                    "\nYour team CAPTURED the "
                    f"flag! Your exact capture "
                    f"count is now {exact_score}.")
        else:
            ctx += (
                "\nThe enemy captured YOUR flag! "
                "EXACT SCORE AFTER THIS CAPTURE: "
                f"Alliance {score_a}, Horde {score_h}. "
                f"The enemy now has exactly "
                f"{exact_score} captures. "
                "Do NOT guess a different number.")

    ctx += " React appropriately."
    return append_json_instruction(
        ctx, False, skip_emote=True)


def build_bg_flag_carrier_prompt(
    extra_data, bot_data, action
):
    """First-person message from the bot carrying
    or dropping the flag.

    action: 'pickup' or 'drop'
    """
    ctx = _bg_base_context(
        extra_data, bot_data,
        skip_observation_constraint=True)
    if action == 'pickup':
        ctx += (
            "\nYOU just picked up the enemy flag! "
            "Say something in first person: call "
            "for protection, express urgency, "
            "rally your team to cover you. "
            "One sentence, spoken as the flag "
            "carrier. Examples of tone: "
            "\"I've got it, keep them off me!\" "
            "or \"Their banner is mine, don't let "
            "them touch me!\""
        )
    else:
        ctx += (
            "\nYOU just dropped the enemy flag "
            "after being overwhelmed. Say "
            "something in first person: brief "
            "apology, frustration, or a call for "
            "someone else to grab it. One sentence. "
            "Examples of tone: "
            "\"They got me, someone grab that "
            "flag!\" or \"Couldn't hold them off, "
            "sorry lads.\""
        )
    return append_json_instruction(ctx, False)


def build_bg_flag_return_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Flag return — friendly player returns
    their team's flag to base."""
    ctx = _bg_base_context(extra_data, bot_data)
    flag_team = extra_data.get('flag_team', '')
    team = extra_data.get('team', '')
    returner = extra_data.get(
        'returner_name', '')
    returner_real = extra_data.get(
        'returner_is_real_player', False)

    if flag_team == team:
        # Our flag was returned to base
        if returner and returner_real:
            ctx += (
                f"\n{returner} returned your "
                "team's flag to base! Praise "
                f"{returner} by name for the "
                "clutch return.")
        elif returner:
            ctx += (
                f"\n{returner} returned the "
                "flag to base!")
        else:
            ctx += (
                "\nYour flag was returned to "
                "base!")
    else:
        # Enemy returned their flag
        ctx += (
            "\nThe enemy returned their flag "
            "to base. Express frustration.")

    ctx += " React appropriately."
    return append_json_instruction(
        ctx, False, skip_emote=True)


def build_bg_node_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Node events \u2014 contest, capture."""
    ctx = _bg_base_context(extra_data, bot_data)
    node_name = extra_data.get(
        'node_name', 'a node')
    new_owner = extra_data.get('new_owner', '')
    team = extra_data.get('team', '')
    event_type = extra_data.get('event_type', '')

    # Player-centric claimer from C++
    claimer = extra_data.get('claimer_name', '')
    claimer_real = extra_data.get(
        'claimer_is_real_player', False)

    # Score context for tactical awareness
    score_a = int(
        extra_data.get('score_alliance', 0))
    score_h = int(
        extra_data.get('score_horde', 0))
    my_score = (score_a if team == 'Alliance'
                else score_h)
    enemy_score = (score_h if team == 'Alliance'
                   else score_a)

    if 'contested' in event_type:
        if new_owner == team:
            # WE are assaulting an enemy node
            if claimer and claimer_real:
                ctx += (
                    f"\n{claimer} is assaulting "
                    f"{node_name}! Cheer them on "
                    f"by name ({claimer}). "
                    f"Aggressive, attacking energy.")
            else:
                ctx += (
                    f"\nYour team is assaulting "
                    f"{node_name}! Show attacking "
                    f"energy \u2014 push forward!")
        else:
            # ENEMY is assaulting OUR node
            if claimer and claimer_real:
                ctx += (
                    f"\n{node_name} is under "
                    f"attack! {claimer} is "
                    f"assaulting it \u2014 rally "
                    f"to stop them! URGENT: "
                    f"call for defenders!")
            else:
                ctx += (
                    f"\n{node_name} is under "
                    f"enemy attack! URGENT: call "
                    f"for defenders, sound the "
                    f"alarm! We need help there!")
    elif 'captured' in event_type:
        if new_owner == team:
            if claimer and claimer_real:
                ctx += (
                    f"\n{claimer} captured "
                    f"{node_name} for your team! "
                    f"Praise {claimer} by name.")
            else:
                ctx += (
                    f"\nYour team captured "
                    f"{node_name}! Celebrate!")
        else:
            ctx += (
                f"\nThe enemy captured "
                f"{node_name}! Express "
                f"frustration or call to "
                f"take it back.")

    # Add score-based urgency
    if my_score > 0 or enemy_score > 0:
        diff = my_score - enemy_score
        if diff > 300:
            ctx += " We're dominating!"
        elif diff < -300:
            ctx += " We're falling behind badly!"
        elif abs(diff) <= 100 and (my_score + enemy_score) > 500:
            ctx += " It's neck and neck!"

    ctx += " React appropriately."
    return append_json_instruction(ctx, False)


def build_bg_pvp_kill_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """PvP kill \u2014 quick reaction."""
    ctx = _bg_base_context(extra_data, bot_data)
    victim = extra_data.get(
        'victim_name', 'an enemy')
    # victim_class arrives as int from C++
    victim_class_id = extra_data.get(
        'victim_class')
    victim_class = ''
    if victim_class_id is not None:
        victim_class = get_class_name(
            int(victim_class_id))

    killer = extra_data.get('killer_name', '')
    killer_real = extra_data.get(
        'killer_is_real_player', False)

    kill_variety = (
        " Vary your style: try trash talk, "
        "tactical praise, dark humor, or "
        "class-specific taunts. Avoid "
        "'one less X' and 'won't be Y "
        "anymore' patterns."
    )
    if killer and killer_real:
        ctx += (
            f"\n{killer} killed {victim}"
            f"{' (' + victim_class + ')' if victim_class else ''}! "
            f"Praise {killer} by name for the "
            f"kill. Quick, sharp comment."
            f"{kill_variety}"
        )
    elif killer:
        ctx += (
            f"\n{killer} took down {victim}"
            f"{' (' + victim_class + ')' if victim_class else ''}. "
            f"React with a quick, sharp comment."
            f"{kill_variety}"
        )
    else:
        ctx += (
            f"\nA teammate killed {victim}"
            f"{' (' + victim_class + ')' if victim_class else ''}. "
            f"React with a quick, sharp comment."
            f"{kill_variety}"
        )
    return append_json_instruction(ctx, False)


def build_bg_score_milestone_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Score milestone \u2014 tension, momentum."""
    ctx = _bg_base_context(extra_data, bot_data)
    milestone_team = extra_data.get(
        'milestone_team', '')
    milestone_value = int(
        extra_data.get('milestone_value', 0))
    team = extra_data.get('team', '')

    score_a = int(
        extra_data.get('score_alliance', 0))
    score_h = int(
        extra_data.get('score_horde', 0))
    my_score = (score_a if team == 'Alliance'
                else score_h)
    enemy_score = (score_h if team == 'Alliance'
                   else score_a)

    if milestone_team == team:
        # OUR team hit a milestone
        if milestone_value >= 1500:
            ctx += (
                f"\nYour team just hit "
                f"{milestone_value} resources \u2014 "
                f"VICTORY IS CLOSE! Finish them!")
        elif my_score > enemy_score + 200:
            ctx += (
                f"\nYour team reached "
                f"{milestone_value} resources "
                f"and we're ahead! Keep the "
                f"pressure on!")
        else:
            ctx += (
                f"\nYour team reached "
                f"{milestone_value} resources. "
                f"React to the momentum.")
    else:
        # ENEMY hit a milestone
        if milestone_value >= 1500:
            ctx += (
                f"\nThe enemy just hit "
                f"{milestone_value} resources \u2014 "
                f"they're about to win! "
                f"DESPERATE urgency!")
        elif enemy_score > my_score + 200:
            ctx += (
                f"\nThe enemy reached "
                f"{milestone_value} resources "
                f"and they're pulling ahead! "
                f"Express frustration or rally "
                f"the team!")
        else:
            ctx += (
                f"\nThe enemy reached "
                f"{milestone_value} resources. "
                f"React to the pressure.")

    return append_json_instruction(ctx, False)


# -- Group-event BG prompt builders ------------------

def build_bg_achievement_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Achievement earned mid-battle."""
    ctx = _bg_base_context(extra_data, bot_data)
    achiever = extra_data.get(
        'achiever_name', 'someone')
    achievement = extra_data.get(
        'achievement_name', 'an achievement')
    ctx += (
        f"\n{achiever} just earned "
        f"[{achievement}] mid-battle! "
        "Quick, impressed reaction -- keep "
        "it short and battlefield-appropriate."
    )
    return append_json_instruction(ctx, False)


def build_bg_spell_cast_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Spell cast reaction in BG context."""
    ctx = _bg_base_context(extra_data, bot_data)
    caster = extra_data.get(
        'caster_name', 'someone')
    spell = extra_data.get(
        'spell_name', 'a spell')
    target = extra_data.get(
        'target_name', 'someone')
    category = extra_data.get(
        'spell_category', 'spell')
    ctx += (
        f"\n{caster} cast {spell} on {target} "
        f"({category}). Brief tactical comment -- "
        "acknowledge the play, keep it snappy."
    )
    return append_json_instruction(ctx, False)


def build_bg_low_health_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Low health callout in BG context."""
    ctx = _bg_base_context(extra_data, bot_data)
    target = extra_data.get(
        'target_name', '')
    if target:
        ctx += (
            f"\n{target} is badly wounded in "
            "combat! Brief urgent callout -- "
            "panic, plea for healing, or "
            "defiant last stand."
        )
    else:
        ctx += (
            "\nYou're badly wounded in combat! "
            "Brief urgent callout -- panic, plea "
            "for healing, or defiant last stand."
        )
    return append_json_instruction(ctx, False)


def build_bg_oom_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Out of mana callout in BG context."""
    ctx = _bg_base_context(extra_data, bot_data)
    ctx += (
        "\nYou're out of mana mid-fight! "
        "Brief frustrated or urgent callout -- "
        "announce it to your team, express "
        "frustration, or ask for support."
    )
    return append_json_instruction(ctx, False)


def build_bg_death_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Teammate death reaction in BG context."""
    ctx = _bg_base_context(extra_data, bot_data)
    dead = extra_data.get(
        'dead_name', 'a teammate')
    killer = extra_data.get('killer_name', '')
    if killer:
        ctx += (
            f"\n{dead} was just killed by {killer}! "
            "Brief urgent reaction -- mourn, vow "
            "revenge, or rally the team."
        )
    else:
        ctx += (
            f"\n{dead} just went down! Brief urgent "
            "reaction -- mourn, vow revenge, or "
            "rally the team."
        )
    return append_json_instruction(ctx, False)


def build_bg_combat_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Combat pull reaction in BG context."""
    ctx = _bg_base_context(extra_data, bot_data)
    creature = extra_data.get(
        'creature_name', 'enemies')
    is_boss = bool(int(
        extra_data.get('is_boss', 0)))
    if is_boss:
        ctx += (
            f"\nEngaging {creature}! Brief battle "
            "cry or taunt at a worthy foe."
        )
    else:
        ctx += (
            f"\nEngaging {creature}! Quick battle "
            "cry -- one sentence only."
        )
    return append_json_instruction(ctx, False)


# -- Idle chatter ------------------------------------

BG_IDLE_CATEGORIES = [
    "battle humor or sarcasm about the match",
    "faction pride or a brief war cry",
    "tactical observation (score, team strength)",
    "combat fatigue or resource complaint",
    "class fantasy -- something your class "
    "would say in battle",
    "taunting the enemy faction",
    "morale boost or rallying cry",
    "lore reference about this battleground",
    "comment about a teammate's performance",
    "enemy team observation or grudging respect",
    "weather or environment comment with "
    "battle urgency",
    "dark humor about dying or respawning",
    "racial grudge against the enemy faction",
    "nostalgia for a past battle or victory",
    "complaint about the chaos of the fight",
    "admiring or cursing a specific enemy class",
    "spiritual or religious invocation "
    "(Light, Elune, ancestors, elements)",
    "impatience or eagerness for the next clash",
    "gallows humor when losing badly",
    "swagger or overconfidence when winning",
]


def build_bg_idle_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Ambient idle chatter during a BG match."""
    ctx = _bg_base_context(extra_data, bot_data)
    category = random.choice(BG_IDLE_CATEGORIES)
    ctx += (
        f"\nThere's a lull in the action. Say "
        f"something to your team about: "
        f"{category}. "
        "Keep it natural and in-character. "
        "One sentence only."
    )
    return append_json_instruction(ctx, False)


# -- BG arrival greeting ----------------------------

def build_bg_arrival_prompt(
    extra_data, bot_data, is_raid_worker=False
):
    """Greeting when player first enters a BG."""
    ctx = _bg_base_context(extra_data, bot_data)
    player_name = extra_data.get(
        'player_name', 'an ally')
    ctx += (
        "\nYou just joined a battleground and "
        "the team is gathering before the fight. "
        "Say something team-oriented: a battle "
        "cry, faction pride, rallying your side, "
        "trash-talking the enemy, or hyping up "
        "the group. Focus on the TEAM, not any "
        "one player. One sentence only."
    )
    return append_json_instruction(ctx, False)
