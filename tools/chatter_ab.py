"""Bounded Arathi Basin snapshot validation and prompt rendering.

Only value data crosses this boundary. Internal contest estimates are never
rendered as numerical timers before delivery-time validation is available.
"""

NODE_NAMES = ('Stables', 'Blacksmith', 'Farm', 'Lumber Mill', 'Gold Mine')
_TEAM = {1: 'Alliance', 2: 'Horde', 3: 'Alliance', 4: 'Horde'}
_RATES = ((0, 0), (10, 12000), (10, 9000), (10, 6000),
          (10, 3000), (30, 1000))


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def normalize_ab_state(raw):
    """Reject incomplete/inconsistent snapshots; copy only bounded fields."""
    if not isinstance(raw, dict):
        return None
    source = raw.get('nodes')
    if not isinstance(source, list) or len(source) != len(NODE_NAMES):
        return None
    nodes = {}
    counts = {'Alliance': 0, 'Horde': 0}
    for entry in source:
        if not isinstance(entry, dict):
            return None
        node_id, state = entry.get('id'), entry.get('state')
        if (not _integer(node_id, 0, 4) or node_id in nodes
                or not _integer(state, 0, 4)
                or type(entry.get('captured')) is not bool
                or not _integer(entry.get('revision'), 1, 2**64 - 1)):
            return None
        owner = _TEAM[state] if state in (1, 2) else None
        claimant = _TEAM[state] if state in (3, 4) else None
        if (entry.get('owner') != owner
                or entry.get('claimant') != claimant
                or (owner and not entry['captured'])
                or (state == 0 and entry['captured'])):
            return None
        if owner:
            counts[owner] += 1
        nodes[node_id] = {
            'id': node_id, 'name': NODE_NAMES[node_id], 'state': state,
            'owner': owner, 'claimant': claimant,
            'captured': entry['captured'], 'revision': entry['revision'],
        }
        estimate = entry.get('contest_estimate')
        if isinstance(estimate, dict) and claimant:
            low, high = (estimate.get('remaining_min_ms'),
                         estimate.get('remaining_max_ms'))
            if (estimate.get('basis') == 'bg_update_time'
                    and _integer(low, 1, 60000)
                    and _integer(high, low, 60000)):
                nodes[node_id]['contest_estimate'] = {
                    'basis': 'bg_update_time', 'remaining_min_ms': low,
                    'remaining_max_ms': high,
                }
    result = {'nodes': [nodes[i] for i in range(5)]}
    for team, suffix in (('Alliance', 'alliance'), ('Horde', 'horde')):
        count = counts[team]
        supplied = raw.get(f'occupied_{suffix}')
        rate = raw.get(f'income_{suffix}')
        if (not _integer(supplied, 0, 5) or supplied != count
                or not isinstance(rate, dict)):
            return None
        points, interval = rate.get('points'), rate.get('interval_ms')
        if (type(points) is not int or type(interval) is not int
                or (points, interval) != _RATES[count]):
            return None
        result[f'occupied_{suffix}'] = count
        result[f'income_{suffix}'] = {'points': points, 'interval_ms': interval}
    # A malformed/unverified target must not destroy otherwise valid nodes.
    maximum = raw.get('max_score')
    verified = (raw.get('max_score_verified') is True
                and _integer(maximum, 1, 2**31 - 1))
    result['max_score_verified'] = verified
    if verified:
        result['max_score'] = maximum
    warning = raw.get('warning_score')
    if _integer(warning, 1, 2**31 - 1):
        result['warning_score'] = warning
    return result


def _side(team, own_team):
    """Team-relative label, falling back to the faction name."""
    if own_team not in ('Alliance', 'Horde'):
        return f'the {team}'
    return f'your team ({team})' if team == own_team else f'the enemy ({team})'


def _race_verdict(snapshot, scores, own_team):
    """One short leading line so the key comparison is not buried."""
    counts = {'Alliance': snapshot['occupied_alliance'],
              'Horde': snapshot['occupied_horde']}
    alliance = snapshot['income_alliance']
    horde = snapshot['income_horde']
    # Cross products compare the actual nonlinear tick rates without an ETA.
    rate_difference = (alliance['points'] * (horde['interval_ms'] or 1)
                       - horde['points'] * (alliance['interval_ms'] or 1))
    faster = (None if not rate_difference else
              'Alliance' if rate_difference > 0 else 'Horde')
    parts = []
    if scores is not None:
        difference = scores[0] - scores[1]
        if difference:
            leader = 'Alliance' if difference > 0 else 'Horde'
            parts.append(f'{_side(leader, own_team)} leads by '
                         f'{abs(difference)} resources')
        else:
            parts.append('the score is tied')
    if faster:
        slower = 'Horde' if faster == 'Alliance' else 'Alliance'
        parts.append(f'{_side(faster, own_team)} earns faster '
                     f'({counts[faster]} bases held vs {counts[slower]})')
    else:
        parts.append(f'both teams earn at the same rate '
                     f'({counts["Alliance"]} bases held each)')
    verdict = '; '.join(parts)
    return 'Race verdict: ' + verdict[0].upper() + verdict[1:] + '.'


def render_ab_context(extra_data):
    """AB objective facts; incidental prompts do not call this renderer."""
    if (not isinstance(extra_data, dict)
            or extra_data.get('bg_type_id') not in (3, '3')):
        return ''
    snapshot = normalize_ab_state(extra_data.get('ab_state'))
    if snapshot is None:
        return ''
    raw_scores = [extra_data.get('score_alliance'), extra_data.get('score_horde')]
    verdict_scores = (raw_scores if all(
        _integer(score, 0, snapshot.get('max_score', 2**31 - 1))
        for score in raw_scores) else None)
    bases = []
    for node in snapshot['nodes']:
        state = ('occupied by ' + node['owner'] if node['owner'] else
                 'contested by ' + node['claimant'] if node['claimant'] else
                 'neutral')
        bases.append(f"{node['name']}: {state}")
    lines = [
        _race_verdict(snapshot, verdict_scores, extra_data.get('team')),
        'Arathi Basin observed base control: ' + '; '.join(bases) + '.',
    ]
    rates = []
    for team, suffix in (('Alliance', 'alliance'), ('Horde', 'horde')):
        count = snapshot[f'occupied_{suffix}']
        rate = snapshot[f'income_{suffix}']
        seconds = rate['interval_ms'] // 1000
        unit = 'second' if seconds == 1 else 'seconds'
        income = (f"{rate['points']} resources per {seconds} {unit}" if count else
                  'no resource income')
        rates.append(f'{team}: {count} occupied bases, {income}')
    lines.append('Observed income: ' + '; '.join(rates) + '.')
    if snapshot['max_score_verified']:
        lines.append(f"Match resource target: {snapshot['max_score']}.")
    scores = [extra_data.get('score_alliance'), extra_data.get('score_horde')]
    maximum = snapshot.get('max_score', 2**31 - 1)
    if all(_integer(score, 0, maximum) for score in scores):
        difference = scores[0] - scores[1]
        if difference:
            leader = 'Alliance' if difference > 0 else 'Horde'
            lines.append(f'Observed score lead: {leader} by {abs(difference)} resources.')
        else:
            lines.append('Observed scores are tied.')
        if snapshot['max_score_verified']:
            lines.append(
                f'Resources remaining at this observation: Alliance '
                f'{maximum - scores[0]}; Horde {maximum - scores[1]}.')
    alliance = snapshot['income_alliance']
    horde = snapshot['income_horde']
    # Cross products compare the actual nonlinear tick rates without an ETA.
    rate_difference = (alliance['points'] * (horde['interval_ms'] or 1)
                       - horde['points'] * (alliance['interval_ms'] or 1))
    if rate_difference:
        faster = 'Alliance' if rate_difference > 0 else 'Horde'
        lines.append(f'At this observation {faster} earns resources faster.')
    else:
        lines.append('Observed resource income rates are equal.')
    lines.append(
        'These are sampled observations. Contested bases earn no resources. '
        'Do not infer a winner, domination, guaranteed victory, exact finish '
        'time, countdown or individual objective credit. A score lead alone '
        'does not establish which team will win.'
    )
    return '\n' + '\n'.join(lines) + '\n'


def normalize_ab_node_changes(raw):
    """Validate an entire bounded batch; never salvage partial bad facts."""
    if not isinstance(raw, list) or not 1 <= len(raw) <= len(NODE_NAMES):
        return None
    result, seen = [], set()
    for item in raw:
        if not isinstance(item, dict):
            return None
        node = item.get('node_id')
        if (not _integer(node, 0, 4) or node in seen
                or not _integer(item.get('node_revision'), 1, 2**64 - 1)
                or not _integer(item.get('state'), 0, 4)):
            return None
        seen.add(node)
        change = dict(item, node_name=NODE_NAMES[node])
        # A malformed actor drops only the attribution, never the change.
        if not _valid_actor(change):
            for key in ('actor_name', 'actor_is_real_player', 'actor_role'):
                change.pop(key, None)
        result.append(change)
    return result


_ACTOR_ROLES = frozenset(
    ('claim', 'assault', 'counter_claim', 'defence', 'flag_held'))


def _valid_actor(change):
    """Verified actor fields from C++: WoW name, bool, known role."""
    name = change.get('actor_name')
    role = change.get('actor_role')
    return (isinstance(name, str) and 2 <= len(name) <= 12
            and name.isalpha()
            and type(change.get('actor_is_real_player')) is bool
            and isinstance(role, str) and role in _ACTOR_ROLES)


def render_ab_milestone(extra_data):
    """Describe a validated observed threshold, without forecasting victory."""
    snapshot = normalize_ab_state(extra_data.get('ab_state'))
    team = extra_data.get('milestone_team')
    value = extra_data.get('milestone_value')
    kind = extra_data.get('milestone_kind')
    if (snapshot is None or not snapshot['max_score_verified']
            or team not in ('Alliance', 'Horde')
            or not _integer(value, 1, snapshot['max_score'] - 1)):
        return '\nReact briefly to the observed resource race; no verified threshold is available.'
    score = extra_data.get('score_' + team.lower())
    if not _integer(score, value, snapshot['max_score']):
        return '\nReact briefly to the observed resource race without asserting a threshold crossing.'
    if kind == 'core_warning' and value == snapshot.get('warning_score'):
        label = 'core warning threshold'
    elif kind == 'percentage':
        label = 'configured resource milestone'
    else:
        return '\nReact briefly to the observed resource race without guessing a milestone type.'
    who = _side(team, extra_data.get('team'))
    return (f'\n{who[0].upper() + who[1:]} crossed the {label}: {value} of '
            f'{snapshot["max_score"]} resources. '
            'Give one brief reaction using the observed score and base facts; '
            'do not promise a win or estimate a finishing time.')
