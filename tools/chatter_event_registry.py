"""Central event type registry for mod-llm-chatter.

Single source of truth for all event types: handler
routing, producer location, priority band, and
extra_data payload schema. Replaces the manually
maintained EVENT_HANDLERS dict in the bridge.
"""

import importlib
import logging
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


@dataclass
class EventSpec:
    """Metadata for one event type."""
    handler_module: str
    handler_func: str
    producer: str
    priority: str = 'normal'
    description: str = ''
    payload_fields: Dict[str, Tuple[type, bool]] = (
        field(default_factory=dict)
    )


# --------------------------------------------------
# Live event registry — 52 entries
# --------------------------------------------------

EVENT_REGISTRY: Dict[str, EventSpec] = {

    # -- Group events (chatter_group_handlers) ----

    'bot_group_kill': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func='process_group_kill_event',
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to creature kill',
        payload_fields={
            'creature_name': (str, True),
            'creature_entry': (int, True),
            'is_boss': (int, False),
            'is_rare': (int, False),
            'is_normal': (int, False),
        },
    ),

    'bot_group_loot': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func='process_group_loot_event',
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to item loot',
        payload_fields={
            'looter_name': (str, True),
            'item_name': (str, True),
            'item_entry': (int, True),
            'item_quality': (int, True),
            'is_bot': (int, True),
        },
    ),

    'bot_group_combat': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func='process_group_combat_event',
        producer='LLMChatterGroup.cpp',
        priority='critical',
        description='Bot reacts to combat start',
        payload_fields={
            'creature_name': (str, True),
            'creature_entry': (int, True),
            'is_boss': (str, False),
            'is_elite': (str, False),
        },
    ),

    'bot_group_death': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func='process_group_death_event',
        producer='LLMChatterGroup.cpp',
        priority='high',
        description=(
            'Bot reacts to party member death'
        ),
        payload_fields={
            'dead_name': (str, True),
            'dead_guid': (int, True),
            'killer_name': (str, False),
            'killer_entry': (int, False),
            'is_player_death': (int, True),
        },
    ),

    'bot_group_levelup': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func='process_group_levelup_event',
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to level up',
        payload_fields={
            'leveler_name': (str, True),
            'old_level': (int, True),
            'is_bot': (str, False),
        },
    ),

    'bot_group_quest_complete': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_quest_complete_event'
        ),
        producer='LLMChatterGroup.cpp',
        description=(
            'Bot reacts to quest completion'
        ),
        payload_fields={
            'completer_name': (str, True),
            'quest_name': (str, True),
            'quest_id': (int, True),
            'quest_details': (str, False),
            'quest_objectives': (str, False),
        },
    ),

    'bot_group_quest_objectives': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_quest_objectives_event'
        ),
        producer='LLMChatterGroup.cpp',
        description=(
            'Bot reacts to quest objective progress'
        ),
        payload_fields={
            'completer_name': (str, True),
            'quest_name': (str, True),
            'quest_id': (int, True),
            'quest_details': (str, False),
            'quest_objectives': (str, False),
        },
    ),

    'bot_group_achievement': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_achievement_event'
        ),
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to achievement',
        payload_fields={
            'achiever_name': (str, True),
            'achievement_name': (str, True),
            'achievement_id': (int, True),
            'is_bot': (str, False),
        },
    ),

    'bot_group_spell_cast': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_spell_cast_event'
        ),
        producer='LLMChatterGroup.cpp',
        priority='critical',
        description='Bot reacts to spell cast',
        payload_fields={
            'caster_name': (str, True),
            'spell_name': (str, True),
            'spell_category': (str, True),
            'target_name': (str, True),
        },
    ),

    'bot_group_resurrect': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_resurrect_event'
        ),
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to resurrection',
        payload_fields={},
    ),

    'bot_group_zone_transition': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_zone_transition_event'
        ),
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to zone change',
        payload_fields={
            'zone_id': (int, True),
            'zone_name': (str, True),
            'area_id': (int, False),
            'area_name': (str, False),
        },
    ),

    'bot_group_subzone_change': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_zone_transition_event'
        ),
        producer='LLMChatterPlayer.cpp',
        description='Bot reacts to subzone change',
        payload_fields={
            'zone_id': (int, True),
            'zone_name': (str, True),
            'area_id': (int, True),
            'area_name': (str, True),
        },
    ),

    'bot_group_quest_accept': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_quest_accept_event'
        ),
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to quest accept',
        payload_fields={
            'acceptor_name': (str, True),
            'quest_name': (str, True),
            'quest_id': (int, True),
            'quest_level': (int, False),
            'zone_name': (str, False),
            'quest_details': (str, False),
            'quest_objectives': (str, False),
        },
    ),

    'bot_group_quest_accept_batch': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_quest_accept_batch_event'
        ),
        producer='LLMChatterGroup.cpp',
        description=(
            'Bot reacts to multiple quest accepts'
        ),
        payload_fields={
            'acceptor_name': (str, True),
            'quest_names': (list, True),
            'quest_count': (int, True),
            'zone_name': (str, False),
        },
    ),

    'bot_group_dungeon_entry': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_dungeon_entry_event'
        ),
        producer='LLMChatterGroup.cpp',
        description='Bot reacts to dungeon entry',
        payload_fields={
            'map_id': (int, True),
            'map_name': (str, True),
            'is_raid': (int, False),
            'zone_id': (int, False),
        },
    ),

    'bot_group_wipe': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func='process_group_wipe_event',
        producer='LLMChatterGroup.cpp',
        priority='high',
        description='Bot reacts to party wipe',
        payload_fields={
            'killer_name': (str, False),
            'killer_entry': (int, False),
        },
    ),

    'bot_group_corpse_run': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_corpse_run_event'
        ),
        producer='LLMChatterGroup.cpp',
        description=(
            'Bot reacts during corpse run'
        ),
        payload_fields={
            'zone_name': (str, True),
            'dead_name': (str, True),
            'is_player_death': (int, True),
        },
    ),

    'bot_group_low_health': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_low_health_event'
        ),
        producer='LLMChatterGroup.cpp',
        priority='critical',
        description=(
            'Bot calls out low health target'
        ),
        payload_fields={
            'target_name': (str, True),
        },
    ),

    'bot_group_oom': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func='process_group_oom_event',
        producer='LLMChatterGroup.cpp',
        priority='critical',
        description='Bot calls out OOM',
        payload_fields={
            'target_name': (str, True),
        },
    ),

    'bot_group_aggro_loss': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_aggro_loss_event'
        ),
        producer='LLMChatterGroup.cpp',
        priority='critical',
        description='Bot calls out aggro loss',
        payload_fields={
            'target_name': (str, True),
            'aggro_target': (str, False),
        },
    ),

    'bot_group_nearby_object': EventSpec(
        handler_module='chatter_group_handlers',
        handler_func=(
            'process_group_nearby_object_event'
        ),
        producer='LLMChatterWorld.cpp',
        priority='critical',
        description=(
            'Bot comments on nearby object/creature'
        ),
        payload_fields={
            'objects': (list, True),
            'zone_name': (str, True),
            'subzone_name': (str, False),
            'in_city': (int, False),
            'in_dungeon': (int, False),
        },
    ),

    'bot_group_farewell': EventSpec(
        handler_module='chatter_group',
        handler_func=(
            'process_group_farewell_event'
        ),
        producer='LLMChatterGroup.cpp',
        description=(
            'Bot says farewell on group leave'
        ),
        payload_fields={
            'bot_guid': (int, True),
            'player_guid': (int, True),
        },
    ),

    # -- Group events (specialized modules) ------─

    'bot_group_emote_reaction': EventSpec(
        handler_module='chatter_emote_reaction',
        handler_func='handle_emote_reaction',
        producer='LLMChatterGroup.cpp',
        description=(
            'Bot reacts to directed emote'
        ),
        payload_fields={
            'emote_name': (str, True),
            'player_name': (str, True),
            'directed': (int, True),
        },
    ),

    'bot_group_emote_observer': EventSpec(
        handler_module='chatter_emote_observer',
        handler_func='handle_emote_observer',
        producer='LLMChatterGroup.cpp',
        description=(
            'Bot observes emote at external target'
        ),
        payload_fields={
            'emote_name': (str, True),
            'player_name': (str, True),
            'target_type': (str, True),
            'target_name': (str, False),
            'npc_rank': (int, False),
            'npc_type': (int, False),
            'npc_subname': (str, False),
        },
    ),

    'bot_group_screenshot_observation': EventSpec(
        handler_module='chatter_screenshot_handler',
        handler_func='handle_screenshot_observation',
        producer='screenshot_agent.py',
        description=(
            'Bot comments on screenshot vision'
        ),
        payload_fields={
            'landmark_type': (str, True),
            'weather': (str, True),
            'time_of_day': (str, True),
            'atmosphere': (str, True),
            'environment': (str, True),
            'creatures': (str, False),
        },
    ),

    # -- Group events (chatter_group) ----------

    'bot_group_join': EventSpec(
        handler_module='chatter_group',
        handler_func='process_group_event',
        producer='LLMChatterGroup.cpp',
        priority='high',
        description='Bot joins group',
        payload_fields={
            'role': (str, True),
            'player_name': (str, True),
            'group_size': (int, False),
            'zone': (int, True),
            'area': (int, False),
            'map': (int, False),
        },
    ),

    'bot_group_join_batch': EventSpec(
        handler_module='chatter_group',
        handler_func=(
            'process_group_join_batch_event'
        ),
        producer='LLMChatterGroup.cpp',
        priority='high',
        description=(
            'Multiple bots join group at once'
        ),
        payload_fields={
            'player_name': (str, True),
            'zone': (int, True),
            'area': (int, False),
            'map': (int, False),
            'bots': (list, True),
        },
    ),

    'bot_group_player_msg': EventSpec(
        handler_module='chatter_group',
        handler_func=(
            'process_group_player_msg_event'
        ),
        producer='LLMChatterGroup.cpp',
        priority='high',
        description=(
            'Bot responds to player party message'
        ),
        payload_fields={
            'player_name': (str, True),
            'player_message': (str, True),
        },
    ),

    # -- Player events ------------------------

    'player_general_msg': EventSpec(
        handler_module='llm_chatter_bridge',
        handler_func=(
            '_dispatch_player_general_msg'
        ),
        producer='LLMChatterPlayer.cpp',
        priority='high',
        description=(
            'Bot responds to General chat message'
        ),
        payload_fields={
            'player_name': (str, True),
            'player_message': (str, True),
            'zone_id': (int, True),
            'zone_name': (str, True),
            'bot_guids': (list, True),
            'bot_names': (list, True),
        },
    ),

    'player_enters_zone': EventSpec(
        handler_module='chatter_events',
        handler_func=(
            'process_zone_intrusion_event'
        ),
        producer='LLMChatterPlayer.cpp',
        priority='high',
        description=(
            'Bot yells at enemy faction intruder'
        ),
        payload_fields={
            'intruder_name': (str, True),
            'intruder_class': (int, True),
            'intruder_race': (int, True),
            'intruder_level': (int, True),
            'intruder_is_bot': (int, True),
            'is_capital': (int, True),
            'zone_name': (str, True),
            'defender_guid': (int, True),
            'defender_name': (str, True),
            'defender_class': (int, True),
            'defender_race': (int, True),
            'defender_level': (int, True),
        },
    ),

    'proximity_say': EventSpec(
        handler_module='chatter_proximity',
        handler_func='handle_proximity_say',
        producer='LLMChatterProximity.cpp',
        priority='filler',
        description='Ambient nearby /say line',
        payload_fields={
            'player_guid': (int, True),
            'zone_name': (str, True),
            'participants': (list, True),
        },
    ),

    'proximity_conversation': EventSpec(
        handler_module='chatter_proximity',
        handler_func='handle_proximity_conversation',
        producer='LLMChatterProximity.cpp',
        priority='filler',
        description='Ambient nearby multi-speaker scene',
        payload_fields={
            'player_guid': (int, True),
            'zone_name': (str, True),
            'participants': (list, True),
            'max_lines': (int, True),
        },
    ),

    'proximity_reply': EventSpec(
        handler_module='chatter_proximity',
        handler_func='handle_proximity_reply',
        producer='LLMChatterProximity.cpp',
        priority='normal',
        description='Reply to player /say near active scene',
        payload_fields={
            'player_guid': (int, True),
            'player_message': (str, True),
            'responder_name': (str, True),
        },
    ),

    # -- BG events (chatter_battlegrounds) --------

    'bg_match_start': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func=(
            'process_bg_match_start_event'
        ),
        producer='LLMChatterBG.cpp',
        priority='high',
        description='BG match begins',
        payload_fields={
            'event_detail': (str, True),
        },
    ),

    'bg_match_end': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func=(
            'process_bg_match_end_event'
        ),
        producer='LLMChatterBG.cpp',
        description='BG match ends',
        payload_fields={
            'winner_team': (str, True),
            'won': (int, True),
            'final_score_alliance': (int, True),
            'final_score_horde': (int, True),
        },
    ),

    'bg_flag_picked_up': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func='process_bg_flag_event',
        producer='LLMChatterBG.cpp',
        priority='critical',
        description='Flag picked up in WSG/EY',
        payload_fields={
            'flag_team': (str, True),
            'carrier_guid': (int, False),
            'carrier_name': (str, False),
        },
    ),

    'bg_flag_dropped': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func='process_bg_flag_event',
        producer='LLMChatterBG.cpp',
        priority='critical',
        description='Flag dropped in WSG/EY',
        payload_fields={
            'flag_team': (str, True),
            'dropper_guid': (int, False),
            'dropper_name': (str, False),
        },
    ),

    'bg_flag_captured': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func='process_bg_flag_event',
        producer='LLMChatterBG.cpp',
        priority='critical',
        description='Flag captured in WSG',
        payload_fields={
            'flag_team': (str, True),
            'new_score': (int, True),
            'scorer_name': (str, False),
        },
    ),

    'bg_flag_returned': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func=(
            'process_bg_flag_return_event'
        ),
        producer='LLMChatterBG.cpp',
        priority='critical',
        description='Flag returned in WSG',
        payload_fields={
            'flag_team': (str, True),
            'returner_name': (str, True),
            'returner_is_real_player': (int, True),
        },
    ),

    'bg_node_contested': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func='process_bg_node_event',
        producer='LLMChatterBG.cpp',
        priority='critical',
        description='AB/EY node contested',
        payload_fields={
            'node_name': (str, True),
            'new_owner': (str, True),
            'claimer_name': (str, False),
        },
    ),

    'bg_node_captured': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func='process_bg_node_event',
        producer='LLMChatterBG.cpp',
        priority='critical',
        description='AB/EY node captured',
        payload_fields={
            'node_name': (str, True),
            'new_owner': (str, True),
            'claimer_name': (str, False),
        },
    ),

    'bg_pvp_kill': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func=(
            'process_bg_pvp_kill_event'
        ),
        producer='LLMChatterPlayer.cpp',
        priority='high',
        description='PvP kill in BG',
        payload_fields={
            'victim_name': (str, True),
            'victim_class': (int, True),
            'killer_name': (str, True),
            'killer_is_real_player': (int, True),
        },
    ),

    'bg_score_milestone': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func=(
            'process_bg_score_milestone_event'
        ),
        producer='LLMChatterBG.cpp',
        description='AB/EY score milestone reached',
        payload_fields={
            'milestone_team': (str, True),
            'milestone_value': (int, True),
            'milestone_description': (str, True),
        },
    ),

    'bg_idle_chatter': EventSpec(
        handler_module='chatter_battlegrounds',
        handler_func=(
            'process_bg_idle_chatter_event'
        ),
        producer='LLMChatterBG.cpp',
        priority='filler',
        description='Ambient BG chatter',
        payload_fields={
            'player_name': (str, True),
        },
    ),

    # -- Raid events (chatter_raids) ---------------

    'raid_boss_pull': EventSpec(
        handler_module='chatter_raids',
        handler_func=(
            'process_raid_boss_pull_event'
        ),
        producer='LLMChatterRaid.cpp',
        priority='critical',
        description='Raid boss pulled',
        payload_fields={
            'boss_name': (str, True),
            'boss_entry': (int, True),
            'raid_name': (str, True),
            'difficulty': (str, True),
            'event_subtype': (str, True),
            'player_name': (str, True),
            'zone_id': (int, True),
        },
    ),

    'raid_boss_kill': EventSpec(
        handler_module='chatter_raids',
        handler_func=(
            'process_raid_boss_kill_event'
        ),
        producer='LLMChatterRaid.cpp',
        priority='critical',
        description='Raid boss killed',
        payload_fields={
            'boss_name': (str, True),
            'boss_entry': (int, True),
            'raid_name': (str, True),
            'difficulty': (str, True),
            'event_subtype': (str, True),
            'player_name': (str, True),
            'zone_id': (int, True),
        },
    ),

    'raid_boss_wipe': EventSpec(
        handler_module='chatter_raids',
        handler_func=(
            'process_raid_boss_wipe_event'
        ),
        producer='LLMChatterRaid.cpp',
        priority='critical',
        description='Raid boss wipe',
        payload_fields={
            'boss_name': (str, True),
            'boss_entry': (int, True),
            'raid_name': (str, True),
            'difficulty': (str, True),
            'event_subtype': (str, True),
            'player_name': (str, True),
            'zone_id': (int, True),
        },
    ),

    'raid_idle_morale': EventSpec(
        handler_module='chatter_raids',
        handler_func=(
            'process_raid_idle_morale_event'
        ),
        producer='LLMChatterWorld.cpp',
        priority='filler',
        description='Ambient raid morale chatter',
        payload_fields={
            'player_name': (str, True),
            'raid_name': (str, True),
            'zone_id': (int, True),
            'difficulty': (str, True),
        },
    ),

    # -- World events (chatter_world_events) ------

    'transport_arrives': EventSpec(
        handler_module='chatter_world_events',
        handler_func=(
            'process_transport_arrives_event'
        ),
        producer='LLMChatterWorld.cpp',
        priority='critical',
        description='Transport arrives at stop',
        payload_fields={
            'transport_name': (str, True),
            'transport_entry': (int, True),
            'destination': (str, True),
            'transport_type': (str, True),
            'verified_bots': (list, True),
        },
    ),

    'weather_change': EventSpec(
        handler_module='chatter_world_events',
        handler_func=(
            'process_weather_change_event'
        ),
        producer='LLMChatterWorld.cpp',
        priority='critical',
        description='Weather transitions',
        payload_fields={
            'weather_type': (str, True),
            'previous_weather': (str, True),
            'transition': (str, True),
            'category': (str, True),
            'intensity': (str, True),
        },
    ),

    'weather_ambient': EventSpec(
        handler_module='chatter_world_events',
        handler_func=(
            'process_weather_ambient_event'
        ),
        producer='LLMChatterWorld.cpp',
        priority='filler',
        description='Ongoing weather comment',
        payload_fields={
            'weather_type': (str, True),
            'category': (str, True),
            'intensity': (str, True),
            'is_ambient': (int, True),
        },
    ),

    'holiday_start': EventSpec(
        handler_module='chatter_world_events',
        handler_func=(
            'process_holiday_start_event'
        ),
        producer='LLMChatterWorld.cpp',
        description='Holiday event begins',
        payload_fields={
            'event_name': (str, True),
            'zone_id': (int, True),
        },
    ),

    'holiday_end': EventSpec(
        handler_module='chatter_world_events',
        handler_func=(
            'process_holiday_end_event'
        ),
        producer='LLMChatterWorld.cpp',
        description='Holiday event ends',
        payload_fields={
            'event_name': (str, True),
            'zone_id': (int, True),
        },
    ),

    'minor_event': EventSpec(
        handler_module='chatter_world_events',
        handler_func='process_minor_event',
        producer='LLMChatterWorld.cpp',
        priority='filler',
        description=(
            'Minor game event (Call to Arms etc.)'
        ),
        payload_fields={
            'event_name': (str, True),
            'zone_id': (int, True),
        },
    ),

    'day_night_transition': EventSpec(
        handler_module='chatter_world_events',
        handler_func=(
            'process_day_night_transition_event'
        ),
        producer='LLMChatterWorld.cpp',
        priority='filler',
        description=(
            'Dawn/dusk/day/night transition'
        ),
        payload_fields={
            'is_day': (int, True),
            'hour': (int, True),
            'minute': (int, True),
            'time_period': (str, True),
            'previous_period': (str, True),
            'description': (str, True),
        },
    ),
}


# --------------------------------------------------
# Dead (removed) event types — 13 entries
# --------------------------------------------------

DEAD_EVENTS: frozenset = frozenset({
    'creature_death_boss',
    'creature_death_rare',
    'creature_death_guard',
    'bot_pvp_kill',
    'bot_level_up',
    'bot_achievement',
    'bot_quest_complete',
    'world_boss_spawn',
    'rare_spawn',
    'enemy_player_near',
    'bot_loot_item',
    'bot_group_discovery',
    'bg_player_arrival',
})


# --------------------------------------------------
# Handler resolution
# --------------------------------------------------

def build_handler_map():
    """Build EVENT_HANDLERS dict from registry.

    Dynamically imports each handler module and
    resolves the handler function by name.
    """
    handlers = {}
    for event_type, spec in EVENT_REGISTRY.items():
        try:
            mod = importlib.import_module(
                spec.handler_module
            )
            fn = getattr(mod, spec.handler_func)
            handlers[event_type] = fn
        except (ImportError, AttributeError) as e:
            logger.error(
                "Registry: cannot resolve %s.%s "
                "for event '%s': %s",
                spec.handler_module,
                spec.handler_func,
                event_type, e,
            )
    return handlers


def validate_registry():
    """Run startup validation and log results."""
    errors = 0
    for event_type, spec in EVENT_REGISTRY.items():
        try:
            mod = importlib.import_module(
                spec.handler_module
            )
            if not hasattr(mod, spec.handler_func):
                logger.warning(
                    "Registry: %s.%s not found "
                    "for '%s'",
                    spec.handler_module,
                    spec.handler_func,
                    event_type,
                )
                errors += 1
        except ImportError:
            logger.warning(
                "Registry: module %s not found "
                "for '%s'",
                spec.handler_module,
                event_type,
            )
            errors += 1
    logger.info(
        "Registry: %d live events, "
        "%d validation errors",
        len(EVENT_REGISTRY),
        errors,
    )
    return errors


def validate_extra_data(event_type, extra_data):
    """Check required payload fields are present.

    Warning-level logging only -- non-blocking.
    Returns True if valid, False if missing fields.
    """
    spec = EVENT_REGISTRY.get(event_type)
    if not spec or not spec.payload_fields:
        return True
    missing = []
    for field_name, (ftype, required) in (
        spec.payload_fields.items()
    ):
        if required and field_name not in extra_data:
            missing.append(field_name)
    if missing:
        logger.warning(
            "Event '%s' missing required fields: %s",
            event_type, missing,
        )
        return False
    return True
