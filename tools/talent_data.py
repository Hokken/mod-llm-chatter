"""Talent data loader for mod-llm-chatter.

Loads `talent_data.json` (generated from the client DBC files by
`generate_talent_data.py`) and exposes:
  - TALENT_TABS: tab id -> {'name', 'class_mask', 'order'}
  - TALENT_SPELLS: rank spell id -> {'talent_id', 'tab_id', 'rank',
    'tier', 'column', 'name'}
"""

import json
import logging
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).with_name("talent_data.json")


def _load_talent_data() -> Tuple[Dict[int, dict], Dict[int, dict]]:
    """Return empty maps on failure so imports remain safe."""
    try:
        with _DATA_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        logger.warning(
            "talent_data.json missing or unreadable; talent-aware "
            "prompts will have no talent details"
        )
        return {}, {}

    tabs: Dict[int, dict] = {}
    for key, value in (payload.get("tabs") or {}).items():
        try:
            tabs[int(key)] = {
                'name': str(value['name']),
                'class_mask': int(value['class_mask']),
                'order': int(value['order']),
            }
        except (KeyError, TypeError, ValueError):
            continue

    spells: Dict[int, dict] = {}
    for key, value in (payload.get("spells") or {}).items():
        try:
            talent_id, tab_id, rank, tier, column, name = value
            spells[int(key)] = {
                'talent_id': int(talent_id),
                'tab_id': int(tab_id),
                'rank': int(rank),
                'tier': int(tier),
                'column': int(column),
                'name': str(name),
            }
        except (TypeError, ValueError):
            continue
    return tabs, spells


TALENT_TABS, TALENT_SPELLS = _load_talent_data()
