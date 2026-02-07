"""
Chatter Events - Event context building and cleanup
for the LLM Chatter Bridge.

Imports from chatter_constants and chatter_shared.
"""

import json
import logging
import re

from chatter_constants import EVENT_DESCRIPTIONS
from chatter_shared import parse_extra_data, get_zone_name

logger = logging.getLogger(__name__)


# =============================================================================
# EVENT CONTEXT BUILDING
# =============================================================================
def build_event_context(event: dict) -> str:
    """Build context string for an event."""
    event_type = event['event_type']
    extra_data = parse_extra_data(
        event.get('extra_data'),
        event.get('id'),
        event_type
    )

    context_parts = []

    if event_type == 'holiday_start':
        name = extra_data.get('event_name', 'a holiday')
        context_parts.append(
            f"The {name} festival has just begun!"
        )

    elif event_type == 'holiday_end':
        name = extra_data.get('event_name', 'a holiday')
        context_parts.append(
            f"The {name} festival is coming to an end."
        )

    elif event_type == 'world_boss_spawn':
        target = event.get('target_name', 'A world boss')
        context_parts.append(
            f"{target} has been spotted in the world!"
        )

    elif event_type == 'rare_spawn':
        target = event.get(
            'target_name', 'A rare creature'
        )
        context_parts.append(
            f"A rare creature ({target}) has appeared "
            f"nearby."
        )

    elif event_type == 'creature_death_boss':
        target = event.get('target_name', 'A boss')
        killer = extra_data.get('killer_name', 'someone')
        context_parts.append(
            f"{target} has been defeated by {killer}!"
        )

    elif event_type == 'creature_death_rare':
        target = event.get('target_name', 'A rare')
        context_parts.append(
            f"A rare creature ({target}) was just killed."
        )

    elif event_type == 'bot_level_up':
        subject = event.get('subject_name', 'Someone')
        new_level = extra_data.get('new_level', '?')
        is_milestone = extra_data.get(
            'is_milestone', False
        )
        if is_milestone:
            context_parts.append(
                f"{subject} has reached level "
                f"{new_level}!"
            )
        else:
            context_parts.append(
                f"{subject} leveled up to {new_level}."
            )

    elif event_type == 'bot_quest_complete':
        subject = event.get('subject_name', 'Someone')
        quest_name = extra_data.get(
            'quest_name', 'a quest'
        )
        context_parts.append(
            f"{subject} just completed the quest "
            f"'{quest_name}'."
        )

    elif event_type == 'bot_achievement':
        subject = event.get('subject_name', 'Someone')
        achi_name = extra_data.get(
            'achievement_name', 'an achievement'
        )
        context_parts.append(
            f"{subject} earned the achievement "
            f"'{achi_name}'!"
        )

    elif event_type == 'bot_pvp_kill':
        subject = event.get('subject_name', 'Someone')
        target = event.get('target_name', 'an enemy')
        context_parts.append(
            f"{subject} defeated {target} in PvP combat!"
        )

    elif event_type == 'bot_loot_item':
        subject = event.get('subject_name', 'Someone')
        item_name = extra_data.get(
            'item_name', 'something valuable'
        )
        quality = extra_data.get('quality', 0)
        quality_name = [
            'poor', 'common', 'uncommon',
            'rare', 'epic', 'legendary'
        ][min(quality, 5)]
        context_parts.append(
            f"{subject} found a {quality_name} item: "
            f"{item_name}!"
        )

    elif event_type == 'day_night_transition':
        time_period = extra_data.get(
            'time_period', 'day'
        )
        previous_period = extra_data.get(
            'previous_period', ''
        )
        hour = extra_data.get('hour', 12)
        description = extra_data.get('description', '')

        # Time period descriptions for context
        period_contexts = {
            'dawn': (
                "The first light of dawn breaks over "
                "the horizon. The sky turns pink and "
                "gold."
            ),
            'early_morning': (
                "It's early morning. The world is "
                "waking up, dew still on the grass."
            ),
            'morning': (
                "The morning sun climbs higher. It's "
                "a good time for adventures."
            ),
            'midday': (
                "The sun reaches its peak. Shadows "
                "are short and the day is warm."
            ),
            'afternoon': (
                "The afternoon sun casts long shadows."
                " The day is well underway."
            ),
            'evening': (
                "Evening approaches. The light turns "
                "golden as the sun descends."
            ),
            'dusk': (
                "Dusk settles over the land. The sky "
                "blazes with sunset colors."
            ),
            'night': (
                "Night has fallen. Stars begin to "
                "appear in the darkening sky."
            ),
            'midnight': (
                "It's the middle of the night. The "
                "world is quiet under the stars."
            ),
            'late_night': (
                "The deep hours of night. Few are "
                "awake at this hour."
            ),
        }

        desc = period_contexts.get(
            time_period,
            description or "The time of day is changing."
        )
        context_parts.append(desc)

        # Add time info for additional context
        if hour is not None:
            context_parts.append(
                f"(In-game time: {hour:02d}:00)"
            )

    elif event_type == 'weather_change':
        weather_type = extra_data.get(
            'weather_type', 'unusual weather'
        )
        previous_weather = extra_data.get(
            'previous_weather', 'clear'
        )
        transition = extra_data.get(
            'transition', 'changing'
        )
        intensity = extra_data.get(
            'intensity', 'moderate'
        )
        category = extra_data.get('category', 'weather')

        # Weather starting descriptions
        starting_descriptions = {
            'light rain': (
                "A light drizzle has begun to fall."
            ),
            'rain': (
                "Rain clouds have rolled in and it's "
                "starting to rain."
            ),
            'heavy rain': (
                "Dark clouds have gathered and heavy "
                "rain is pouring down!"
            ),
            'light snow': (
                "A few snowflakes are beginning to "
                "drift down from the sky."
            ),
            'snow': (
                "It's starting to snow, white flakes "
                "covering the ground."
            ),
            'heavy snow': (
                "A blizzard is setting in with heavy "
                "snowfall!"
            ),
            'foggy': (
                "A thick fog is rolling in, reducing "
                "visibility."
            ),
            'light sandstorm': (
                "The wind is picking up, kicking sand "
                "into the air."
            ),
            'sandstorm': (
                "A sandstorm is sweeping through the "
                "area!"
            ),
            'heavy sandstorm': (
                "A massive sandstorm has engulfed "
                "everything!"
            ),
            'thunderstorm': (
                "Storm clouds are gathering, thunder "
                "rumbles in the distance!"
            ),
            'black rain': (
                "Strange dark clouds have formed... "
                "black rain is falling!"
            ),
            'black snow': (
                "Something ominous... black snow is "
                "drifting down from above."
            ),
        }

        # Weather clearing descriptions
        clearing_descriptions = {
            'rain': (
                "The rain is stopping. Clouds are "
                "parting."
            ),
            'snow': (
                "The snowfall is easing. The sky is "
                "clearing."
            ),
            'sandstorm': (
                "The sandstorm is dying down. "
                "Visibility is returning."
            ),
            'fog': (
                "The fog is lifting, revealing the "
                "landscape."
            ),
            'storm': (
                "The storm is passing. The thunder "
                "fades away."
            ),
            'weather': "The weather is clearing up.",
        }

        # Weather intensifying descriptions
        intensifying_descriptions = {
            'rain': (
                f"The rain is getting heavier - now "
                f"{weather_type}."
            ),
            'snow': (
                f"The snow is intensifying - now "
                f"{weather_type}."
            ),
            'sandstorm': (
                f"The sandstorm grows stronger - now "
                f"{weather_type}."
            ),
            'storm': "The storm is intensifying!",
            'weather': (
                f"The {category} is getting worse."
            ),
        }

        if transition == 'starting':
            desc = starting_descriptions.get(
                weather_type,
                f"The weather is changing to "
                f"{weather_type}."
            )
        elif transition == 'clearing':
            desc = clearing_descriptions.get(
                category,
                "The weather is clearing up. The sky "
                "brightens."
            )
        elif transition == 'intensifying':
            desc = intensifying_descriptions.get(
                category,
                f"The {weather_type} is getting more "
                f"intense."
            )
        else:  # changing (different weather type)
            desc = (
                f"The weather is shifting from "
                f"{previous_weather} to {weather_type}."
            )

        context_parts.append(desc)

    elif event_type == 'transport_arrives':
        transport_type = extra_data.get(
            'transport_type', ''
        )
        destination = extra_data.get('destination', '')
        transport_name = extra_data.get(
            'transport_name', ''
        )

        # Extract the ship's actual name
        # (e.g., "The Moonspray") from transport_name
        # Format: 'Auberdine, Darkshore and
        #   Rut'theran Village, Teldrassil
        #   (Boat, Alliance ("The Moonspray"))'
        ship_name = ''
        if transport_name:
            # Look for quoted name like
            # ("The Moonspray") or ("Orgrim's Hammer")
            name_match = re.search(
                r'\("([^"]+)"\)', transport_name
            )
            if name_match:
                ship_name = name_match.group(1)

        # Fallback: parse target_name if extra_data
        # failed. Format: "Auberdine, Darkshore and
        #   Rut'theran Village, Teldrassil
        #   (Boat, Alliance)"
        target_name = event.get('target_name', '')
        if not destination and target_name:
            # Try to extract destination from
            # "X and Y (Type)" format
            if ' and ' in target_name:
                parts = target_name.split(' and ')
                if len(parts) >= 2:
                    # Second part before parenthesis
                    # is destination
                    dest_part = (
                        parts[1].split('(')[0].strip()
                    )
                    destination = dest_part
            # Try to extract transport type
            if not transport_type and '(' in target_name:
                type_part = (
                    target_name.split('(')[-1]
                    .rstrip(')')
                )
                if 'Boat' in type_part:
                    transport_type = 'Boat'
                elif 'Zeppelin' in type_part:
                    transport_type = 'Zeppelin'
                elif 'Turtle' in type_part:
                    transport_type = 'Turtle'

        # Extract origin from transport_name
        # (first part before ' and ')
        origin = ''
        if transport_name and ' and ' in transport_name:
            origin = (
                transport_name.split(' and ')[0].strip()
            )

        # Final defaults
        if not transport_type:
            transport_type = 'transport'
        if not destination:
            destination = 'its next stop'

        # Build description based on transport type
        # with ship name
        # IMPORTANT: The boat ARRIVED at destination
        # (where bots are), coming FROM origin
        # If bots board it, it will take them BACK
        # to origin
        ship_info = (
            f' "{ship_name}"' if ship_name else ''
        )

        # Clarify: arrived HERE from origin,
        # will depart TO origin
        if origin and destination:
            arrival_info = (
                f"This {transport_type.lower()}"
                f"{ship_info} just arrived here at "
                f"{destination} from {origin}."
            )
            departure_info = (
                f"If bots want to board, it will take "
                f"them to {origin}."
            )
        elif destination:
            arrival_info = (
                f"This {transport_type.lower()}"
                f"{ship_info} just arrived here at "
                f"{destination}."
            )
            departure_info = ""
        else:
            arrival_info = (
                f"A {transport_type.lower()}"
                f"{ship_info} has just arrived."
            )
            departure_info = ""

        if transport_type.lower() == 'zeppelin':
            desc = (
                f"A zeppelin{ship_info} has just "
                f"arrived! {arrival_info} "
                f"{departure_info}"
            )
        elif transport_type.lower() == 'boat':
            desc = (
                f"A boat{ship_info} has just docked "
                f"at the pier! {arrival_info} "
                f"{departure_info}"
            )
        elif transport_type.lower() == 'turtle':
            desc = (
                f"A giant sea turtle transport"
                f"{ship_info} has arrived! "
                f"{arrival_info} {departure_info}"
            )
        else:
            desc = (
                f"A {transport_type}{ship_info} has "
                f"arrived. {arrival_info} "
                f"{departure_info}"
            )

        context_parts.append(desc)
        # Clarify that bots are AT the destination,
        # not going TO it
        context_parts.append(
            f"IMPORTANT: The bots are currently AT "
            f"{destination}. The transport just "
            f"arrived FROM {origin}. If mentioning "
            f"boarding, they would be heading TO "
            f"{origin}, not to {destination}."
        )

    elif event_type == 'player_enters_zone':
        subject = event.get(
            'subject_name', 'A player'
        )
        level = extra_data.get('level', '?')
        context_parts.append(
            f"A level {level} player ({subject}) "
            f"entered the area."
        )

    else:
        desc = EVENT_DESCRIPTIONS.get(
            event_type, 'something happened'
        )
        context_parts.append(
            f"Something notable happened: {desc}."
        )

    return ' '.join(context_parts)


# =============================================================================
# EVENT LIFECYCLE
# =============================================================================
def cleanup_expired_events(db) -> int:
    """Mark expired events and clean up old completed
    events."""
    cursor = db.cursor()

    # Mark pending events that have expired
    cursor.execute("""
        UPDATE llm_chatter_events
        SET status = 'expired'
        WHERE status = 'pending'
          AND expires_at IS NOT NULL
          AND expires_at < NOW()
    """)
    expired_count = cursor.rowcount

    # Delete old completed/expired/skipped events
    # (older than 24 hours)
    cursor.execute("""
        DELETE FROM llm_chatter_events
        WHERE status IN ('completed', 'expired',
                         'skipped')
          AND created_at < DATE_SUB(
              NOW(), INTERVAL 24 HOUR
          )
    """)
    deleted_count = cursor.rowcount

    db.commit()

    if expired_count > 0 or deleted_count > 0:
        logger.debug(
            f"Event cleanup: {expired_count} expired, "
            f"{deleted_count} deleted"
        )

    return expired_count + deleted_count


def reset_stuck_processing_events(db) -> int:
    """Reset events stuck in 'processing' status back
    to 'pending'.

    Called on bridge startup - if any events are stuck
    in 'processing', it means the bridge crashed before
    completing them. Reset them so they can be retried.
    """
    cursor = db.cursor()

    cursor.execute("""
        UPDATE llm_chatter_events
        SET status = 'pending'
        WHERE status = 'processing'
    """)
    reset_count = cursor.rowcount
    db.commit()

    if reset_count > 0:
        logger.info(
            f"Reset {reset_count} stuck 'processing' "
            f"events to 'pending'"
        )

    return reset_count
