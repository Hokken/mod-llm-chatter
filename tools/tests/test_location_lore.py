#!/usr/bin/env python3
"""Location lore checks: subzone_lore.json, ZONE_FLAVOR, DUNGEON_FLAVOR,
RAID_LORE and BG_LORE contracts, their translations, and where zone and
subzone descriptions reach the prompts.

Run directly from the module root:
  python tools/tests/test_location_lore.py
"""

import importlib
import json
import re
import sys
import types
from pathlib import Path
from unittest.mock import patch


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_non_strict_stubs() -> None:
    for module_name in ("anthropic", "openai"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            module = _ensure_module(module_name)
            class_name = (
                "Anthropic"
                if module_name == "anthropic"
                else "OpenAI"
            )
            setattr(module, class_name, type(class_name, (), {}))

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_module = _ensure_module("mysql")
        connector_module = _ensure_module("mysql.connector")
        setattr(mysql_module, "connector", connector_module)


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_constants as constants  # noqa: E402
import chatter_prompts  # noqa: E402
import chatter_shared  # noqa: E402
import locales  # noqa: E402
from chatter_instance_context import build_location_prompt_lines  # noqa: E402
from chatter_raid_prompts import RAID_LORE  # noqa: E402

LORE = json.loads(
    (TOOLS_DIR / 'subzone_lore.json').read_text(encoding='utf-8')
)['zones']
FIRST_PERSON = re.compile(r"\b(I|me|my|we|our)\b")
ARENA_MAPS = (559, 562, 572, 617, 618)


# -- Data contracts ----------------------------------------------------

def test_lore_texts_are_third_person_and_bounded():
    for zone_id, zone in LORE.items():
        texts = [zone.get('description') or '']
        texts += [s.get('description') or ''
                  for s in zone.get('subzones', {}).values()]
        for text in texts:
            if not text:
                continue
            assert not FIRST_PERSON.search(text), (zone_id, text[:60])
            assert 60 <= len(text) <= 1700, (zone_id, len(text))


def test_every_described_zone_has_short_flavor():
    described = {int(k) for k, v in LORE.items() if v.get('description')}
    assert described == set(constants.ZONE_FLAVOR), (
        described ^ set(constants.ZONE_FLAVOR))
    for zone_id, text in constants.ZONE_FLAVOR.items():
        assert text.split(':')[0] == LORE[str(zone_id)]['name'], zone_id
        assert 250 <= len(text) <= 700, (zone_id, len(text))
        assert not FIRST_PERSON.search(text), zone_id


def test_instance_flavor_is_in_world_and_named():
    assert set(ARENA_MAPS) <= set(constants.DUNGEON_FLAVOR)
    # Game jargon, not in-world words: "raid" as an attack or "wing"
    # of a building are fine.
    meta = re.compile(
        r"Wrath of the Lich King|Burning Crusade|Cataclysm|"
        r"\braid (instance|dungeon)\b|\bdungeon instance\b|"
        r"\bboss(es)?\b|\bloot\b|\bplayers?\b|\bheroic\b", re.I)
    for map_id, text in constants.DUNGEON_FLAVOR.items():
        name, _, body = text.partition(':')
        assert name and body.strip(), map_id
        assert not meta.search(body), (map_id, meta.search(body).group(0))
        assert 200 <= len(text) <= 700, (map_id, len(text))
    for map_id in (559, 562, 572, 618):
        assert map_id in constants.OPEN_AIR_INSTANCES


def test_raid_and_battleground_lore_is_complete():
    for name, entry in RAID_LORE.items():
        assert set(entry) == {'lore', 'tone', 'landmarks'}, name
        assert all(entry.values()), name
    assert set(constants.BG_LORE) == {1, 2, 3, 7, 9, 30}
    for bg_id, entry in constants.BG_LORE.items():
        assert {'name', 'alliance_faction', 'horde_faction', 'lore',
                'tone', 'objectives', 'landmarks'} <= set(entry), bg_id
        assert 'Do NOT mention locations' in entry['landmarks'], bg_id
    assert constants.BG_MAP_NAMES[607] == 'Strand of the Ancients'
    assert constants.BG_MAP_NAMES[628] == 'Isle of Conquest'


def test_translations_cover_the_english_keys():
    for name in ('ZONE_FLAVOR', 'DUNGEON_FLAVOR', 'BG_LORE'):
        english = getattr(constants, name)
        for code, table in locales.dataset(name).items():
            assert set(table) == set(english), (
                name, code, set(table) ^ set(english))
    for code, table in locales.dataset('DUNGEON_FLAVOR').items():
        for map_id, text in table.items():
            assert ':' in text[:80], (code, map_id)


# -- Lookups -----------------------------------------------------------

def test_zone_lore_steps_aside_for_a_translation():
    assert chatter_shared.get_zone_lore(12).startswith('Elwynn Forest')
    assert chatter_shared.get_zone_lore(0) is None
    with patch.object(chatter_shared, 'get_language_locale_code',
                      return_value='ruRU'), \
            patch.dict(chatter_shared._ZONE_FLAVOR_LOCALE_MAPS,
                       {'ruRU': {12: 'translated'}}):
        assert chatter_shared.get_zone_lore(12) is None


def test_location_lore_lines():
    lines = chatter_shared.location_lore_lines(12, 87)
    assert lines[0].startswith('Zone context: Elwynn Forest:')
    assert lines[1].startswith('Current subzone: Goldshire')
    assert chatter_shared.location_lore_lines(
        12, 87, include_zone=False)[0].startswith('Current subzone:')
    assert chatter_shared.location_lore_lines(12, 12) == [
        lines[0]]


# -- Prompt placement --------------------------------------------------

def test_event_location_lines_are_gated():
    with patch.object(chatter_prompts, '_event_location_chance', 100):
        rp = chatter_prompts.maybe_event_location_lines(
            12, 87, 0, 'roleplay')
        assert rp and rp[-1].startswith('Current subzone: Goldshire')
        assert chatter_prompts.maybe_event_location_lines(
            12, 87, 0, 'normal') == []
        # Instances and battlegrounds keep their own flavor.
        assert chatter_prompts.maybe_event_location_lines(
            12, 87, 33, 'roleplay') == []
        assert chatter_prompts.maybe_event_location_lines(
            12, 87, 489, 'roleplay') == []
    with patch.object(chatter_prompts, '_event_location_chance', 0):
        assert chatter_prompts.maybe_event_location_lines(
            12, 87, 0, 'roleplay') == []
    chatter_prompts.configure_prompt_flavor(
        {'LLMChatter.LocationContext.EventChance': '250'})
    assert chatter_prompts._event_location_chance == 100
    chatter_prompts.configure_prompt_flavor({})
    assert chatter_prompts._event_location_chance == 50


def test_proximity_location_lines_describe_on_request():
    extra = {'zone_id': 12, 'area_id': 87, 'map_id': 0,
             'zone_name': 'Elwynn Forest', 'subzone_name': 'Goldshire'}
    plain = build_location_prompt_lines(extra)
    assert plain == ['Zone: Elwynn Forest', 'Subzone: Goldshire']
    described = build_location_prompt_lines(extra, describe=True)
    assert described[-1].startswith('About this place: Goldshire')
    # Older payloads without an area fall back to the zone flavor.
    no_area = dict(extra, area_id=0)
    assert build_location_prompt_lines(
        no_area, describe=True)[-1].startswith('Zone context: Elwynn')


def test_proximity_describes_for_in_world_speakers():
    import chatter_proximity as prox

    extra = {'zone_id': 12, 'area_id': 87, 'map_id': 0,
             'zone_name': 'Elwynn Forest', 'subzone_name': 'Goldshire'}
    bot = {'name': 'Aliss', 'is_npc': False}
    npc = {'name': 'Guard', 'is_npc': True}

    def has_lore(lines):
        return any(line.startswith('About this place') for line in lines)

    with patch.object(prox, '_environment_lines', return_value=[]), \
            patch.object(prox, '_player_context_line', return_value=''):
        assert not has_lore(prox._location_lines(extra, 'normal', [bot]))
        assert has_lore(prox._location_lines(extra, 'normal', [bot, npc]))
        assert has_lore(prox._location_lines(extra, 'roleplay', [bot]))


def test_world_events_describe_only_transport_harbours():
    import chatter_world_events as world

    extra = {'dock_area_id': 150}
    assert world._event_area_id(
        {'event_type': 'transport_arrives'}, extra) == 150
    assert world._event_area_id(
        {'event_type': 'weather_change'}, extra) == 0
    assert world._event_area_id(
        {'event_type': 'transport_arrives'}, {}) == 0


def test_party_reply_keeps_subzone_lore_in_roleplay():
    from chatter_group_prompts import build_player_response_prompt

    bot = {'name': 'Aliss', 'class': 'Mage', 'race': 'Human',
           'level': 10, 'gender': 'female'}
    common = dict(zone_id=12, area_id=87, map_id=0)
    normal = str(build_player_response_prompt(
        bot, ['curious'], 'Lyn', 'hello', 'normal', **common))
    rp = str(build_player_response_prompt(
        bot, ['curious'], 'Lyn', 'hello', 'roleplay', **common))
    assert 'Current subzone:' not in normal
    assert 'Subzone: Goldshire' in normal
    assert 'Current subzone: Goldshire' in rp


if __name__ == '__main__':
    tests = [
        value
        for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} location lore tests passed")
