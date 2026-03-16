"""Spell data loader for mod-llm-chatter.

Loads spell names/descriptions from `spell_names.json`
and exposes the same public constants used by existing
call sites:
  - SPELL_NAMES
  - SPELL_DESCRIPTIONS
"""

import json
import logging
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).with_name("spell_names.json")


def _coerce_spell_map(raw: dict) -> Dict[int, str]:
    """Convert JSON object keys back to int IDs."""
    result: Dict[int, str] = {}
    for key, value in raw.items():
        try:
            spell_id = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(value, str):
            result[spell_id] = value
    return result


def _load_spell_data() -> Tuple[Dict[int, str], Dict[int, str]]:
    """Load spell maps from JSON.

    Returns empty dicts on failure so imports remain safe.
    """
    try:
        with _DATA_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return {}, {}

    names_raw = payload.get("spell_names", {})
    desc_raw = payload.get("spell_descriptions", {})

    if not isinstance(names_raw, dict) or not isinstance(
        desc_raw, dict
    ):
        return {}, {}

    names = _coerce_spell_map(names_raw)
    descriptions = _coerce_spell_map(desc_raw)
    return names, descriptions


SPELL_NAMES, SPELL_DESCRIPTIONS = _load_spell_data()

