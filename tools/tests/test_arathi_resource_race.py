#!/usr/bin/env python3
"""AB resource facts, safe milestone/status prompts and source wiring."""
from pathlib import Path
import unittest
from unittest.mock import patch

import test_battleground_carrier_messages  # dependency stubs/tools path
from test_arathi_snapshot import snapshot, BOT
from chatter_ab import render_ab_context, render_ab_milestone
from chatter_bg_prompts import build_bg_score_milestone_prompt, build_bg_idle_prompt
from chatter_bg_delivery import normalize_bg_transport

ROOT = Path(__file__).resolve().parents[2]


def context(states=(1, 1, 1, 2, 2), target=1600, alliance=800, horde=1000):
    return dict(bg_type_id=3, team='Alliance', ab_state=snapshot(states, target),
                score_alliance=alliance, score_horde=horde,
                milestone_team='Horde', milestone_value=960,
                milestone_kind='percentage')


class ResourceTests(unittest.TestCase):
    def test_lead_and_income_are_independent(self):
        text = render_ab_context(context())
        self.assertIn('Horde by 200 resources', text)
        self.assertIn('Alliance earns resources faster', text)
        self.assertIn('Alliance 800; Horde 600', text)
        text = render_ab_context(context((0, 0, 0, 2, 2), alliance=1100, horde=900))
        self.assertIn('Alliance by 200 resources', text)
        self.assertIn('Alliance: 0 occupied bases, no resource income', text)
        self.assertIn('Horde earns resources faster', text)

    def test_race_verdict_leads_the_snapshot_and_is_team_relative(self):
        # Live regression: Horde led and earned faster, yet the reply said
        # "we've got the income advantage". The verdict is the first line.
        cases = (
            # states, alliance score, horde score, viewer, expected verdict
            ((2, 2, 2, 1, 1), 330, 480, 'Alliance',
             'Race verdict: The enemy (Horde) leads by 150 resources; '
             'the enemy (Horde) earns faster (3 bases held vs 2).'),
            ((2, 2, 2, 1, 1), 330, 480, 'Horde',
             'Race verdict: Your team (Horde) leads by 150 resources; '
             'your team (Horde) earns faster (3 bases held vs 2).'),
            ((1, 1, 1, 2, 2), 800, 1000, 'Alliance',
             'Race verdict: The enemy (Horde) leads by 200 resources; '
             'your team (Alliance) earns faster (3 bases held vs 2).'),
            ((1, 1, 2, 2, 0), 500, 500, 'Alliance',
             'Race verdict: The score is tied; both teams earn at the same '
             'rate (2 bases held each).'),
        )
        for states, alliance, horde, viewer, expected in cases:
            data = context(states, alliance=alliance, horde=horde)
            data['team'] = viewer
            text = render_ab_context(data)
            self.assertEqual(text.strip().splitlines()[0], expected)
            self.assertNotIn('halfway', text.lower())
        # Without a known viewer team the verdict uses faction names.
        data = context((2, 2, 2, 1, 1), alliance=330, horde=480)
        data.pop('team')
        self.assertIn('Race verdict: The Horde leads by 150', render_ab_context(data))

    def test_milestone_is_team_relative_with_absolute_progress(self):
        data = context(alliance=330, horde=480)
        data.update(milestone_value=480)
        text = render_ab_milestone(data)
        self.assertIn('The enemy (Horde) crossed the configured resource '
                      'milestone: 480 of 1600 resources.', text)
        data['team'] = 'Horde'
        self.assertIn('Your team (Horde) crossed', render_ab_milestone(data))

    def test_zero_to_five_bases_use_nonlinear_rates(self):
        expected = ['no resource income', '10 resources per 12 seconds',
                    '10 resources per 9 seconds', '10 resources per 6 seconds',
                    '10 resources per 3 seconds', '30 resources per 1 second']
        for count, rate in enumerate(expected):
            data = context(tuple([1] * count + [0] * (5 - count)))
            self.assertIn(f'Alliance: {count} occupied bases, {rate}',
                          render_ab_context(data))

    def test_custom_targets_and_warning_labels(self):
        for target, value in [(1600, 1440), (1500, 1350), (1000, 900), (2, 1)]:
            data = context(target=target, alliance=0, horde=value)
            data['milestone_value'] = value
            text = render_ab_milestone(data)
            self.assertIn(f'{value} of {target} resources', text)
            self.assertIn('configured resource milestone', text)
        data = context(alliance=0, horde=1400)
        data.update(milestone_kind='core_warning', milestone_value=1400)
        self.assertIn('core warning threshold: 1400 of 1600', render_ab_milestone(data))
        data = context(target=1000, alliance=0, horde=900)
        data['ab_state']['warning_score'] = 900
        data.update(milestone_kind='core_warning', milestone_value=900)
        self.assertIn('core warning threshold', render_ab_milestone(data))
        data['milestone_value'] = 1400
        self.assertNotIn('crossed the', render_ab_milestone(data))
        self.assertNotIn('crossed the', render_ab_milestone(
            context(target=1, alliance=0, horde=0)))

    def test_both_modes_no_AB_1500_prediction_and_EY_unchanged(self):
        for mode in ('normal', 'roleplay'):
            data = context(alliance=1500, horde=1450)
            data.update(milestone_team='Alliance', milestone_value=1440,
                        _config={'LLMChatter.ChatterMode': mode})
            text = build_bg_score_milestone_prompt(data, BOT)
            for unsafe in ("We're dominating!", 'VICTORY IS CLOSE!', "they're about to win!"):
                self.assertNotIn(unsafe, text)
            self.assertIn('Alliance 100; Horde 150', text)
            data.update(ab_objective_status=True)
            text = build_bg_idle_prompt(data, BOT)
            self.assertIn('one brief tactical observation', text)
            self.assertNotIn("There's a lull", text)
        ey = context()
        ey.update(bg_type_id=7, milestone_value=1500)
        self.assertIn("they're about to win!", build_bg_score_milestone_prompt(ey, BOT))

    def test_bad_snapshot_fallback_and_transport_boundaries(self):
        for raw in (None, {}, {'nodes': []}, 'bad'):
            data = context()
            data.update(ab_state=raw, ab_objective_status=True)
            text = build_bg_idle_prompt(data, BOT)
            self.assertNotIn('observed base control:', text)
            self.assertNotIn('Match resource target:', text)
            self.assertIn('if unavailable, offer general encouragement', text)
            self.assertNotIn('crossed the', render_ab_milestone(data))
        data = context()
        self.assertIn('ab_state', normalize_bg_transport(data, 'bg_score_milestone'))
        self.assertNotIn('ab_state', normalize_bg_transport(data, 'bot_group_player_msg'))

    def test_cpp_source_contracts_not_execution(self):
        ab = (ROOT / 'src/LLMChatterAB.cpp').read_text()
        bg = (ROOT / 'src/LLMChatterBG.cpp').read_text()
        score = ab.split('void QueueABScoreMilestone(', 1)[1].split(
            'bool TryABObjectiveStatus(', 1)[0]
        self.assertIn('tracker.score.TakeAttempt(', score)
        self.assertIn('tracker.scoreInsertion', score)
        self.assertNotIn('tracker.insertions', score)
        self.assertNotIn('TryQueueBGBigEvent', score)
        self.assertIn('AsyncCommitTransaction(trans)', score)
        update = ab.split('void ObserveABContext(', 1)[1].split(
            'void ResetABContext(', 1)[0]
        self.assertIn('tracker.score.Observe(', update)
        self.assertIn('tracker.scoreInsertion.reset()', update)
        detect = bg.split('static void DetectScoreEvents(', 1)[1].split(
            'static void PollWSGState(', 1)[0]
        self.assertNotIn('bgType == BATTLEGROUND_AB', detect)
        self.assertIn('bgType == BATTLEGROUND_EY', detect)
        idle = bg.split('uint32 idleCooldownMs =', 1)[1].split(
            'void OnBattlegroundDestroy(', 1)[0]
        self.assertIn('objectiveStatus || urand', idle)
        self.assertEqual(idle.count('QueueBGEvent('), 1)
        self.assertIn('TryABObjectiveStatus(bg)', idle)


if __name__ == '__main__':
    with patch('chatter_bg_prompts.pick_personality_spices', return_value=[]), \
            patch('chatter_bg_prompts.build_environmental_context_lines', return_value=[]):
        unittest.main()
