"""Shared location grounding for instance-aware chatter prompts."""

from typing import Dict, List

from chatter_shared import get_dungeon_flavor


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_instance_context(extra: Dict) -> Dict[str, object]:
    """Normalize outdoor and instance location data from event JSON."""
    map_id = _safe_int(extra.get('map_id'))
    map_name = str(extra.get('map_name') or '').strip()
    zone_name = str(extra.get('zone_name') or '').strip()
    subzone_name = str(
        extra.get('subzone_name') or ''
    ).strip()
    flavor = get_dungeon_flavor(map_id)
    is_raid = bool(extra.get('is_raid', False))
    is_dungeon = bool(
        extra.get('is_dungeon', False)
    )
    is_instance = is_raid or is_dungeon or bool(flavor)

    instance_name = ''
    current_area = ''
    if is_instance:
        instance_name = map_name or zone_name or 'the instance'
        if subzone_name and subzone_name != instance_name:
            current_area = subzone_name

    return {
        'map_id': map_id,
        'instance_id': _safe_int(extra.get('instance_id')),
        'map_name': map_name,
        'zone_name': zone_name,
        'subzone_name': subzone_name,
        'is_instance': is_instance,
        'is_raid': is_raid,
        'is_dungeon': is_dungeon,
        'instance_name': instance_name,
        'current_area': current_area,
        'instance_flavor': flavor or '',
    }


def build_location_prompt_lines(extra: Dict) -> List[str]:
    """Return factual prompt lines without parsing names from lore prose."""
    context = build_instance_context(extra)
    if context['is_instance']:
        lines = [f"Instance: {context['instance_name']}"]
        if context['current_area']:
            lines.append(
                f"Current area: {context['current_area']}"
            )
        if context['instance_flavor']:
            lines.append(
                "Instance context (grounding only; do not recite): "
                f"{context['instance_flavor']}"
            )
        lines.append(
            "Do not claim a boss is present, alive, engaged, or defeated "
            "unless the event explicitly says so."
        )
        return lines

    zone_name = context['zone_name'] or 'the area'
    lines = [f"Zone: {zone_name}"]
    if context['subzone_name']:
        lines.append(
            f"Subzone: {context['subzone_name']}"
        )
    return lines


def build_location_metadata(extra: Dict) -> Dict[str, object]:
    """Return compact request-log metadata for a normalized location."""
    context = build_instance_context(extra)
    return {
        'map_id': context['map_id'],
        'instance_id': context['instance_id'],
        'map_name': context['map_name'],
        'zone_name': context['zone_name'],
        'is_instance': context['is_instance'],
        'is_raid': context['is_raid'],
    }
