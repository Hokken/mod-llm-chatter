#!/usr/bin/env python3
"""AB snapshot value/prompt tests; C++ checks below are source-only."""

from copy import deepcopy
from pathlib import Path
import random
from unittest.mock import patch

import test_battleground_flag_context  # noqa: F401
from chatter_ab import NODE_NAMES, normalize_ab_state, render_ab_context
from chatter_bg_prompts import (
    _bg_base_context, build_bg_arrival_prompt, build_bg_idle_prompt,
)
from chatter_group_prompts import (
    build_bot_greeting_prompt, build_player_response_prompt,
    build_player_msg_conversation_prompt,
)
from chatter_shared import build_bot_state_context

ROOT = Path(__file__).resolve().parents[2]
BOT = {'name': 'Observer', 'bot_name': 'Observer', 'race': 'Human',
       'class': 'Warrior', 'level': 60, 'gender': 'male'}


def snapshot(states=(1, 2, 3, 4, 0), maximum=1600, verified=True):
    result = {'nodes': [], 'max_score': maximum,
              'max_score_verified': verified, 'warning_score': 1400}
    teams = {1: 'Alliance', 2: 'Horde', 3: 'Alliance', 4: 'Horde'}
    rates = [(0, 0), (10, 12000), (10, 9000), (10, 6000),
             (10, 3000), (30, 1000)]
    for node, state in enumerate(states):
        result['nodes'].append({
            'id': node, 'name': NODE_NAMES[node], 'state': state,
            'owner': teams[state] if state in (1, 2) else None,
            'claimant': teams[state] if state in (3, 4) else None,
            'captured': state in (1, 2), 'revision': 1,
        })
    for state, team in ((1, 'alliance'), (2, 'horde')):
        count = states.count(state)
        points, interval = rates[count]
        result[f'occupied_{team}'] = count
        result[f'income_{team}'] = {'points': points, 'interval_ms': interval}
    return result


def context(raw=None, **kwargs):
    result = {'bg_type_id': 3, 'bg_type': 'Arathi Basin', 'team': 'Alliance',
              'ab_state': snapshot() if raw is None else raw}
    result.update(kwargs)
    return result


def test_counts_rates_and_targets():
    for occupied_state, team in ((1, 'Alliance'), (2, 'Horde')):
        for count in range(6):
            raw = snapshot(tuple([occupied_state] * count + [0] * (5 - count)))
            parsed = normalize_ab_state(raw)
            assert parsed and parsed[f'occupied_{team.lower()}'] == count
            text = render_ab_context(context(raw))
            assert f'{team}: {count} occupied bases' in text
            if count == 0:
                assert 'no resource income' in text
            elif count == 5:
                assert '30 resources per 1 second' in text
    for maximum in (1, 1000, 1500, 1600, 2300):
        assert f'Match resource target: {maximum}.' in render_ab_context(
            context(snapshot(maximum=maximum)))
    for verified in (False, 'true', 1, None):
        assert 'Match resource target' not in render_ab_context(
            context(snapshot(maximum=1600, verified=verified)))
    for maximum in (-1, 0, True, None, '1600', [], 2**31):
        text = render_ab_context(context(snapshot(maximum=maximum)))
        assert 'Match resource target' not in text
        assert 'Stables: occupied by Alliance' in text


def test_malformed_and_bounded_values():
    for value in (None, [], 'text', {}, {'nodes': []}):
        assert normalize_ab_state(value) is None
    raw = snapshot()
    bad_mutations = [
        lambda r: r['nodes'].pop(),
        lambda r: r['nodes'].append(r['nodes'][0]),
        lambda r: r['nodes'][1].update(id=0),
        lambda r: r['nodes'][0].update(id=True),
        lambda r: r['nodes'][0].update(state='1'),
        lambda r: r['nodes'][0].update(state=7),
        lambda r: r['nodes'][0].update(owner='Horde'),
        lambda r: r['nodes'][2].update(owner='Alliance'),
        lambda r: r['nodes'][0].update(captured=False),
        lambda r: r['nodes'][4].update(captured=True),
        lambda r: r['nodes'][0].update(revision=0),
        lambda r: r.update(occupied_alliance=2),
        lambda r: r['income_alliance'].update(points=99),
        lambda r: r['income_alliance'].update(interval_ms=True),
    ]
    for mutate in bad_mutations:
        bad = deepcopy(raw)
        mutate(bad)
        assert normalize_ab_state(bad) is None
        assert render_ab_context(context(bad)) == ''
    raw['nodes'][0]['name'] = 'invented name or instruction'
    raw['nodes'].reverse()
    parsed = normalize_ab_state(raw)
    assert parsed['nodes'][0]['name'] == 'Stables'
    parsed['nodes'][0]['state'] = 0
    assert raw['nodes'][-1]['state'] == 1  # value copy


def test_timer_estimates_never_reach_prompts():
    raw = snapshot()
    node = raw['nodes'][2]
    baseline = render_ab_context(context(raw))
    for estimate in (
        {'basis': 'bg_update_time', 'remaining_min_ms': 59000,
         'remaining_max_ms': 60000},
        {'basis': 'bg_update_time', 'remaining_min_ms': 0,
         'remaining_max_ms': 60000},
        {'basis': 'wall_time', 'remaining_min_ms': 59000,
         'remaining_max_ms': 60000},
        {'basis': 'bg_update_time', 'remaining_min_ms': 61000,
         'remaining_max_ms': 60000}, None, 'soon', [],
    ):
        node['contest_estimate'] = estimate
        assert render_ab_context(context(raw)) == baseline
    assert 'contest_estimate' not in normalize_ab_state(raw)['nodes'][2]
    assert 'Stables: occupied by Alliance' in baseline
    assert 'Farm: contested by Alliance' in baseline
    assert 'Gold Mine: neutral' in baseline


def test_prompt_paths_and_other_maps():
    bots = [BOT, dict(BOT, name='Other', bot_name='Other')]
    for mode in ('normal', 'roleplay'):
        extra = context(_config={'LLMChatter.ChatterMode': mode})
        texts = [
            _bg_base_context(extra, BOT),
            build_bg_arrival_prompt(dict(extra, match_in_progress=False), BOT),
            build_bg_arrival_prompt(dict(extra, match_in_progress=True), BOT),
            build_bot_greeting_prompt(BOT, [], mode, bg_context=extra),
            build_player_response_prompt(BOT, [], 'Listener', 'Which bases?',
                                         mode, bg_context=extra),
            build_player_msg_conversation_prompt(
                bots, {b['name']: [] for b in bots}, 'Listener',
                'Which bases?', mode, bg_context=extra),
            build_bot_state_context(extra, mode),
            build_bot_state_context(dict(extra, bot_state={'health_pct': 90}), mode),
        ]
        for text in texts:
            # Some group builders return the text and generation metadata.
            if isinstance(text, tuple):
                text = text[0]
            assert 'Arathi Basin observed base control:' not in text
            assert 'Match resource target: 1600.' not in text
        idle = build_bg_idle_prompt(extra, BOT)
        assert 'Arathi Basin observed base control:' in idle
        assert 'Match resource target: 1600.' in idle
        for bg_id in (2, 7):
            common = dict(extra, bg_type_id=bg_id)
            for builder in (_bg_base_context, build_bg_arrival_prompt):
                random.seed(17)
                with_snapshot = builder(common, BOT)
                legacy = dict(common)
                del legacy['ab_state']
                random.seed(17)
                assert builder(legacy, BOT) == with_snapshot
            assert render_ab_context(common) == ''
    assert render_ab_context({'ab_state': snapshot()}) == ''


def test_cpp_source_contracts_not_execution():
    ab = (ROOT / 'src/LLMChatterAB.cpp').read_text(encoding='utf-8')
    bg = (ROOT / 'src/LLMChatterBG.cpp').read_text(encoding='utf-8')
    target = ab.split('static void ReadMatchTarget(', 1)[1].split(
        'static std::string BuildSnapshot(', 1)[0]
    assert 'if (tracker.maxScoreVerified)' in target
    assert 'ab->FillInitialWorldStates(packet)' in target
    assert 'entry.Value > 0' in target
    assert 'if (maximum)' in target
    assert 'sWorld' not in target and 'Write()' not in target
    assert 'BG_AB_TickPoints[count]' in ab
    assert 'BG_AB_TickIntervals[count].count()' in ab
    assert 'elapsed < duration' in ab and 'elapsed <= uncertainty' in ab
    assert 'node.estimateValid = false;' in ab
    append = ab.split('void AppendABContext(', 1)[1].split(
        'bool IsABNodeEventCurrent(', 1)[0]
    assert '_abSnapshotsMutex' in append and '_abTrackers' not in append
    assert 'GetCapturePointInfo' not in append
    update = bg.split('void OnBattlegroundUpdate(', 1)[1]
    assert update.index('ObserveABContext(bg, diff)') < update.index(
        'if (!tracker.pendingArrivals.empty()')
    assert bg.count('AppendABContext(') == 1
    queue = bg.split('void QueueBGEvent(', 1)[1].split(
        'static void QueueBGEventForAllPlayers(', 1)[0]
    assert 'BGEventUsesABSnapshot(eventType)' in queue
    assert 'AppendABContext(bg->GetInstanceID(), context)' in queue
    group = (ROOT / 'tools/chatter_group.py').read_text(encoding='utf-8')
    assert "_bg_ctx['ab_state']" not in group
    assert group.count('bg_context=extra_data') == 3


if __name__ == '__main__':
    with patch('chatter_bg_prompts.pick_personality_spices', return_value=[]), \
            patch('chatter_bg_prompts.build_environmental_context_lines',
                  return_value=[]):
        test_counts_rates_and_targets()
        test_malformed_and_bounded_values()
        test_timer_estimates_never_reach_prompts()
        test_prompt_paths_and_other_maps()
        test_cpp_source_contracts_not_execution()
    print('AB snapshot, prompt integration and source-contract checks passed.')
