#!/usr/bin/env python3
"""AB prompt regressions and producer source contracts (no C++ execution)."""

from pathlib import Path
from unittest.mock import patch

import test_battleground_flag_context  # noqa: F401 - dependency stubs
from chatter_bg_prompts import _ab_node_observation, build_bg_node_prompt


ROOT = Path(__file__).resolve().parents[2]
NODES = ('Stables', 'Blacksmith', 'Farm', 'Lumber Mill', 'Gold Mine')


def event(**overrides):
    data = {
        'bg_type_id': 3, 'team': 'Alliance', 'node_name': 'Stables',
        'new_owner': 'Horde', 'event_type': 'bg_node_captured',
        'prev_state': 4, 'state': 1, 'transition': 'state_update',
        'evidence': 'ambiguous', 'observation_gap_ms': 10,
    }
    data.update(overrides)
    return data


def who(faction, team='Alliance'):
    return 'Your team' if faction == team else f'The enemy ({faction})'


def test_ambiguous_pairs_are_state_only():
    # Includes claim, assault, counter-claim, defence, capture, reversal,
    # unchanged and impossible pairs. Neither labels nor a short gap prove
    # an exhaustive history. Invalid baselines also cannot upgrade wording.
    for node in NODES:
        for previous in (None, -1, 0, 1, 2, 3, 4, 99):
            for current, fact in (
                (0, f'{node} is neutral.'),
                (1, f'Your team holds {node}.'),
                (2, f'The enemy (Horde) holds {node}.'),
                (3, f'Your team is contesting {node}; it is not held yet.'),
                (4, f'The enemy (Horde) is contesting {node}; it is not held yet.'),
            ):
                for gap in (0, 1, 3000, 60000):
                    data = event(node_name=node, prev_state=previous,
                                 state=current, observation_gap_ms=gap)
                    baseline = _ab_node_observation(data)
                    assert baseline.startswith('\nAB objective observation: ' + fact)
                    for evidence in ('unknown_baseline', 'ambiguous',
                                     None, {}, 123):
                        for transition in ('claim', 'assault', 'counter_claim',
                                           'defence', 'capture', None, []):
                            assert _ab_node_observation(dict(
                                data, transition=transition, evidence=evidence,
                            )) == baseline


def test_sampled_transition_matrix():
    for node in NODES:
        for team in ('Alliance', 'Horde'):
            for owner, occupied, contested, enemy_occ, enemy_cont in (
                ('Alliance', 1, 3, 2, 4), ('Horde', 2, 4, 1, 3),
            ):
                subject = who(owner, team)
                assaulted = (f'the enemy-held {node}. The enemy stops earning'
                             if owner == team else
                             f'your {node}. Your team stops earning')
                for previous, current, transition, expected in (
                    (0, contested, 'claim',
                     f'{subject} is claiming the neutral {node}. Nobody held '
                     'it before and nobody holds it yet.'),
                    (enemy_occ, contested, 'assault',
                     f'{subject} is assaulting {assaulted}'),
                    (enemy_cont, contested, 'counter_claim',
                     f'{subject} has taken over the contested claim at {node}. '
                     'Neither team holds it yet.'),
                    (enemy_cont, occupied, 'defence',
                     f'{subject} defended {node} and holds it again'),
                    (contested, occupied, 'capture',
                     f'{subject} now holds {node}; the claim completed.'),
                ):
                    data = event(node_name=node, team=team, prev_state=previous,
                                 state=current, transition=transition,
                                 evidence='sampled', observation_gap_ms=1000)
                    assert expected in _ab_node_observation(data)
                    for bad_gap in (-1, None, '1000', []):
                        fallback = _ab_node_observation(dict(data, observation_gap_ms=bad_gap))
                        assert expected not in fallback
                    for evidence in ('ambiguous', 'unknown_baseline', None):
                        assert expected not in _ab_node_observation(dict(data, evidence=evidence))
    # Invalid pair/label combinations cannot invent a defence or capture.
    assert 'defended' not in _ab_node_observation(event(
        evidence='sampled', prev_state=0, state=1, transition='defence'))
    assert 'claim completed' not in _ab_node_observation(event(
        evidence='sampled', prev_state=4, state=1, transition='capture'))


def test_claims_and_assaults_are_never_framed_as_held_or_lost():
    # Live regressions: "Mill's ours now" for our assault and "Farm fell to
    # the Horde" for a Horde claim on a NEUTRAL base.
    for team in ('Alliance', 'Horde'):
        enemy = 'Horde' if team == 'Alliance' else 'Alliance'
        own_cont = 3 if team == 'Alliance' else 4
        enemy_cont = 4 if team == 'Alliance' else 3
        enemy_occ = 2 if team == 'Alliance' else 1
        own_occ = 1 if team == 'Alliance' else 2
        enemy_neutral_claim = _ab_node_observation(event(
            team=team, prev_state=0, state=enemy_cont, transition='claim',
            evidence='sampled', observation_gap_ms=1000))
        assert f'The enemy ({enemy}) is claiming the neutral Stables' in enemy_neutral_claim
        assert 'Nobody held it before' in enemy_neutral_claim
        assert 'lost' not in enemy_neutral_claim
        our_assault = _ab_node_observation(event(
            team=team, prev_state=enemy_occ, state=own_cont,
            transition='assault', evidence='sampled', observation_gap_ms=1000))
        assert 'it is not ours yet' in our_assault
        their_assault = _ab_node_observation(event(
            team=team, prev_state=own_occ, state=enemy_cont,
            transition='assault', evidence='sampled', observation_gap_ms=1000))
        assert 'lost only if their assault completes' in their_assault
        for text in (enemy_neutral_claim, our_assault, their_assault):
            assert 'A claimed or assaulted base is not held by anyone yet' in text


def test_legacy_and_malformed_states():
    for node in NODES:
        for team in ('Alliance', 'Horde'):
            for category, expected in (
                ('bg_node_contested',
                 f'{who(team)} is contesting {node}; it is not held yet.'),
                ('bg_node_captured', f'{who(team)} holds {node}.'),
            ):
                data = event(node_name=node, new_owner=team, event_type=category)
                del data['state']
                assert expected in _ab_node_observation(data)
                for bad in (None, True, False, '1', 1.0, -1, 5, [], {}):
                    text = _ab_node_observation(dict(data, state=bad))
                    assert f'The current control of {node} is unknown.' in text
                    assert expected not in text
    for owner in ('Neutral', '', None, [], {}):
        data = event(new_owner=owner)
        del data['state']
        assert 'control of Stables is unknown.' in _ab_node_observation(data)
    for name in (None, [], {}, 'Unverified base'):
        assert 'Your team holds a base.' in _ab_node_observation(
            event(node_name=name))


def test_full_prompts_never_credit_objective_actor():
    for mode in ('normal', 'roleplay'):
        for team in ('Alliance', 'Horde'):
            for traits in ([], ['patient', 'competitive']):
                for bg_id in (3, '3', 32, None):
                    for is_human in (False, True):
                        data = event(
                            bg_type_id=bg_id, team=team,
                            claimer_name='GuessedBystander',
                            claimer_is_real_player=is_human,
                            _config={'LLMChatter.ChatterMode': mode},
                        )
                        for legacy in (False, True, 'sampled'):
                            payload = dict(data)
                            if legacy is True:
                                for key in ('prev_state', 'state', 'transition',
                                            'evidence', 'observation_gap_ms'):
                                    del payload[key]
                            elif legacy == 'sampled':
                                payload.update(evidence='sampled', transition='defence')
                            text = build_bg_node_prompt(payload, {
                                'bot_name': 'Observer', 'traits': traits,
                            })
                            assert 'Arathi Basin' in text
                            assert 'AB objective observation:' in text
                            assert 'GuessedBystander' not in text
                            assert 'Credit only a player named in these observations' in text
                            assert 'invented history, timers or promises.' in text
                            assert 'CRITICAL RULE: You are an observer.' in text


def test_ey_prompt_policy_unchanged():
    for team in ('Alliance', 'Horde'):
        text = build_bg_node_prompt(event(
            bg_type_id=7, node_name='Mage Tower', team=team, new_owner=team,
            claimer_name='ExistingEYActor', claimer_is_real_player=True,
        ), {'bot_name': 'Observer'})
        assert 'ExistingEYActor captured Mage Tower for your team!' in text
        assert 'AB objective observation:' not in text


def test_observer_source_contract():
    """Tripwires only: these do not execute the C++ observer or scheduler."""
    source = (ROOT / 'src/LLMChatterBG.cpp').read_text(encoding='utf-8')
    ab_source = (ROOT / 'src/LLMChatterAB.cpp').read_text(encoding='utf-8')
    observer = ab_source.split('static void ObserveNodes(', 1)[1].split(
        'static std::string NodeJson(', 1)[0]
    consume = ab_source.split('static std::string NodeJson(', 1)[1].split(
        'static void ReadMatchTarget(', 1)[0]
    poll = ab_source.split('void QueueABNodeBatch(', 1)[1].split(
        'static void ReadMatchTarget(', 1)[0]
    update = source.split('void OnBattlegroundUpdate(', 1)[1].split(
        'void OnBattlegroundDestroy(', 1)[0]
    assert 'getMSTimeDiff(tracker.abLastObservationMs, now)' in observer
    assert 'i < BG_AB_DYNAMIC_NODES_COUNT' in observer
    assert 'if (!node.initialized)' in observer
    assert 'if (state == node.state)' in observer
    assert 'node.prevState = node.state;' in observer
    assert 'node.observationGapMs = gap;' in observer
    assert 'std::max(node.observationGapMs, gap)' in observer
    assert 'tracker.pending.Record(' in observer
    assert 'urand' not in observer and 'Queue' not in observer
    assert update.index('ObserveABContext(bg, diff)') < update.index(
        'if (tracker.diffAccum < pollInterval)')
    assert 'ResetABContext(bg->GetInstanceID())' in update
    assert 'tracker.inProgress != inProgress' in ab_source
    assert 'claimer' not in poll
    assert '"ambiguous"' in consume and '"sampled"' in consume
    assert 'ClassifyABTransition(' in observer
    assert 'gap > maxGap' in observer
    assert 'node.pendingChanges = 2;' in observer
    assert 'if (!pending.active)' in observer
    assert 'tracker.pending.Select(' in poll
    assert poll.index('tracker.pending.Select(') < poll.index('urand')
    assert 'TryQueueBGBigEvent' not in poll
    assert 'AsyncCommitTransaction(trans)' in poll
    assert 'tracker.pending.Acknowledge(audience, items, success)' in poll
    destroy = source.split('void OnBattlegroundDestroy(', 1)[1]
    assert '_bgTrackers.erase(' in destroy


if __name__ == '__main__':
    with patch('chatter_bg_prompts.pick_personality_spices', return_value=[]), \
            patch('chatter_bg_prompts.build_environmental_context_lines',
                  return_value=[]):
        test_ambiguous_pairs_are_state_only()
        test_sampled_transition_matrix()
        test_legacy_and_malformed_states()
        test_full_prompts_never_credit_objective_actor()
        test_ey_prompt_policy_unchanged()
        test_observer_source_contract()
    print('AB prompt regressions and producer source contracts passed.')
