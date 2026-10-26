"""Shared location grounding for instance-aware chatter prompts."""

from typing import Dict, List

from chatter_shared import (
    find_subzone_id,
    get_dungeon_flavor,
    get_subzone_lore,
    get_zone_flavor,
)


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


def build_location_prompt_lines(
    extra: Dict, describe: bool = False,
) -> List[str]:
    """Return factual prompt lines without parsing names from lore prose.

    With ``describe``, an outdoor location also gets its curated
    descriptions: the zone flavor and the subzone lore, each when it
    exists. Payloads without ``area_id`` (an older worldserver) find
    the subzone by its name. Instances always carry their instance
    flavor.
    """
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
    if describe:
        zone_id = _safe_int(extra.get('zone_id'))
        area_id = _safe_int(extra.get('area_id')) or find_subzone_id(
            zone_id, context['subzone_name']
        )
        zone_flavor = get_zone_flavor(zone_id) if zone_id else None
        if zone_flavor:
            lines.append(f"Zone context: {zone_flavor}")
        subzone_lore = get_subzone_lore(zone_id, area_id)
        if subzone_lore:
            lines.append(f"About this place: {subzone_lore}")
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
