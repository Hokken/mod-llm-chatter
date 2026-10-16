#!/usr/bin/env python3
"""LLMChatter.Language decides the language, not the worldserver locale.

C++ resolves names with sWorld->GetDefaultDbcLocale(), which is the
worldserver's client locale and has nothing to do with the bridge-only
LLMChatter.Language setting. Wherever the bridge can resolve a name from
a stable id it must do so and treat the C++ text as a fallback, otherwise
the two disagree on any server whose client locale differs from the
configured chatter language.

Raised in review of PR #49, in both directions:

  * a Russian-configured bridge on an English worldserver was handed the
    English subzone name and preferred it over its own Russian one;
  * an English-configured bridge on a Russian worldserver kept the
    Russian creature name, because the English text lives in
    creature_template rather than creature_template_locale and nothing
    looked there.

Run directly from the module root:
  python tools/tests/test_locale_authority.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chatter_shared  # noqa: E402
import chatter_group_prompts  # noqa: E402


class _Cursor:
    """Answers the one query the code under test issues."""

    def __init__(self, rows):
        self._rows = rows
        self._result = None

    def execute(self, sql, params=()):
        self._result = self._rows.get(_table_of(sql))

    def fetchone(self):
        return self._result

    def close(self):
        pass


def _table_of(sql):
    """Which table a SELECT names, so the stub can answer per-table."""
    if 'creature_template_locale' in sql:
        return 'creature_template_locale'
    if 'creature_template' in sql:
        return 'creature_template'
    return 'other'


class _DB:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, *args, **kwargs):
        return _Cursor(self._rows)


def _clear_name_cache():
    """Entries are cached for the process lifetime; tests need a reset."""
    chatter_shared._creature_name_locale_cache.clear()


def test_english_resolves_english_name_over_a_localized_input():
    """An English bridge must not keep a name C++ localized for it."""
    _clear_name_cache()
    chatter_shared.set_language('US')
    db = _DB({
        'creature_template': {'name': 'Hogger'},
        'creature_template_locale': {'Name': 'Дробитель'},
    })
    # What C++ handed over, resolved against a ruRU worldserver locale.
    result = chatter_shared.localize_creature_name(
        db, 'Дробитель', entry=448)
    assert result == 'Hogger', (
        'English chatter kept the worldserver-localized name: %r'
        % result)


def test_non_english_resolves_through_the_locale_table():
    """The original direction still works."""
    _clear_name_cache()
    chatter_shared.set_language('RU')
    db = _DB({
        'creature_template': {'name': 'Hogger'},
        'creature_template_locale': {'Name': 'Дробитель'},
    })
    result = chatter_shared.localize_creature_name(
        db, 'Hogger', entry=448)
    assert result == 'Дробитель', (
        'Russian chatter did not reach the locale table: %r' % result)


def test_name_survives_when_no_entry_id_is_available():
    """Without an id there is nothing to resolve; keep what we were given."""
    _clear_name_cache()
    chatter_shared.set_language('RU')
    db = _DB({})
    assert chatter_shared.localize_creature_name(
        db, 'Hogger') == 'Hogger'


def test_subzone_prefers_the_bridge_name_over_the_cpp_name():
    """The bridge lookup follows LLMChatter.Language; area_name does not."""
    chatter_shared.set_language('RU')
    english_name = 'Amberstill Ranch'

    zone_id, area_id = 1, 803              # Dun Morogh / Amberstill Ranch
    bridge_name = chatter_shared.get_subzone_name(zone_id, area_id)
    assert bridge_name and bridge_name != english_name, (
        'test fixture is wrong: %r must be a localized name distinct '
        'from the English one' % bridge_name)

    prompt = chatter_group_prompts.build_zone_transition_prompt(
        bot={'name': 'Thrallmar', 'race': 'Orc', 'class': 'Warrior',
             'level': 70, 'gender': 'male'},
        traits=['gruff'],
        zone_name='Dun Morogh',
        zone_id=zone_id,
        mode='roleplay',
        is_subzone=True,
        area_id=area_id,
        area_name=english_name,        # what C++ sends, in its own locale
    )
    # The lore blurb in this prompt is English-only by design, so look
    # at the sentence that names the area rather than the whole text.
    assert ('entered the %s area' % bridge_name) in prompt, (
        'the transition line did not use the bridge-localized name')
    assert ('entered the %s area' % english_name) not in prompt, (
        'the English C++ subzone name won over the localized one')


def main() -> int:
    test_english_resolves_english_name_over_a_localized_input()
    test_non_english_resolves_through_the_locale_table()
    test_name_survives_when_no_entry_id_is_available()
    test_subzone_prefers_the_bridge_name_over_the_cpp_name()
    chatter_shared.set_language('US')
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
