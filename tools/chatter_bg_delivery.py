"""Normalize BG transport metadata without refreshing original facts.

Legacy prompt inputs remain readable. The C++ final-send guard rejects
queued legacy rows without a complete match envelope.
"""

AB_SNAPSHOT_EVENTS = frozenset((
    'bg_node_captured', 'bg_node_contested', 'bg_idle_chatter',
    'bg_score_milestone',
))


def normalize_bg_transport(data, event_type=None):
    if not isinstance(data, dict):
        return data
    is_bg = (str(event_type or '').startswith('bg_')
             or data.get('is_battleground') is True
             or any(key in data for key in (
                 'bg_type_id', 'bg_instance_id', 'bg_match_token', 'ab_state')))
    if not is_bg:
        return data

    def uint(value, maximum=0xffffffff):
        return type(value) is int and 0 <= value <= maximum

    group = data.get('group_id', 0)
    raid = data.get('raid_group_id', 0)
    if (not uint(group) or not uint(raid)
            or (group and raid and group != raid)):
        return {}
    result = dict(data)
    if event_type not in AB_SNAPSHOT_EVENTS:
        result.pop('ab_state', None)
    if group or raid:
        result['group_id'] = group or raid
    if 'bg_match_token' not in result:
        return result
    if (not isinstance(result['bg_match_token'], str)
            or not result['bg_match_token']
            or result.get('team') not in ('Alliance', 'Horde')
            or not uint(result.get('bg_observed_ms'), 0xffffffffffffffff)
            or not uint(result.get('player_subgroup'), 7)):
        return {}
    for key in ('bg_instance_id', 'bg_type_id', 'bg_map_id',
                'bg_recipient_guid', 'group_id'):
        if not uint(result.get(key)) or not result[key]:
            return {}
    return result
