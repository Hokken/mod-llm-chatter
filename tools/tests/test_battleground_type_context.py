#!/usr/bin/env python3
"""BG map/queue identity regression checks (no C++ execution).

Run from the module root:
  python tools/tests/test_battleground_type_context.py
"""

import re
import random
from pathlib import Path
from unittest.mock import patch

# Reuse the existing standalone BG test's optional dependency setup.
import test_battleground_flag_context  # noqa: F401
from chatter_bg_prompts import _bg_base_context, build_bg_arrival_prompt


ROOT = Path(__file__).resolve().parents[2]


def test_producers_use_map_type_and_preserve_queue():
    """Contract checks for C++ producers; compilation is a separate check."""
    source = (ROOT / 'src/LLMChatterBG.cpp').read_text(encoding='utf-8')
    for start, end in (
        ('void AppendBGContext(', 'void QueueBGEvent('),
        ('void OnBattlegroundUpdate(', 'void OnBattlegroundDestroy('),
    ):
        body = source.split(start, 1)[1].split(end, 1)[0]
        for key, argument in (('bg_type_id', 'true'), ('queue_type_id', '')):
            # Check the expression attached to each field, not a loose
            # occurrence elsewhere in the function.
            marker = '\\"' + key + '\\":'
            field = body.split(marker, 1)[1]
            call = re.search(r'GetBgTypeID\((.*?)\)', field)
            assert call and call.group(1) == argument, (start, key)
    score = source.split('static void DetectScoreEvents(', 1)[1]
    score = score.split('static void PollWSGState(', 1)[0]
    assert 'uint32 bgType = bg->GetBgTypeID(true);' in score
    assert 'switch (bg->GetBgTypeID(true))' in source
    assert 'switch (bg->GetBgTypeID())' not in source


def test_queue_identity_does_not_override_map_prompts():
    bot = {'bot_name': 'Observer'}
    for mode in ('normal', 'roleplay'):
        for bg_id, name in (
            (2, 'Warsong Gulch'), (3, 'Arathi Basin'),
            (7, 'Eye of the Storm'),
        ):
            for team in ('Alliance', 'Horde'):
                common = {
                    'bg_type_id': bg_id, 'team': team,
                    'score_alliance': 100, 'score_horde': 80,
                    'match_in_progress': True,
                    'player_name': 'Listener',
                    '_config': {'LLMChatter.ChatterMode': mode},
                }
                with patch('chatter_bg_prompts.pick_personality_spices',
                           return_value=[]), patch(
                        'chatter_bg_prompts.build_environmental_context_lines',
                        return_value=[]):
                    for builder in (_bg_base_context, build_bg_arrival_prompt):
                        random.seed(1234)
                        direct = builder(dict(common, queue_type_id=bg_id), bot)
                        random.seed(1234)
                        random_bg = builder(dict(common, queue_type_id=32), bot)
                        random.seed(1234)
                        legacy = builder(common, bot)
                        assert name in direct, (mode, bg_id, builder.__name__)
                        assert direct == random_bg == legacy


if __name__ == '__main__':
    test_producers_use_map_type_and_preserve_queue()
    test_queue_identity_does_not_override_map_prompts()
    print('Battleground map/queue identity checks passed.')
