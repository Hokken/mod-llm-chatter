#!/usr/bin/env python3
"""Language tables live in the locales package, served by one registry.

They used to sit in chatter_constants.py, which grew past nine thousand
lines and made the module hard to review -- the tables are bulk
translation data, not module logic, and they change for entirely
different reasons.

These tests pin the arrangement: every dataset each locale claims is
actually reachable through the registry, the shapes are what the
accessors in chatter_shared expect, and the bulk data has not crept back
into the constants module.

Run directly from the module root:
  python tools/tests/test_locale_registry.py
"""

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import chatter_constants  # noqa: E402
import locales  # noqa: E402

# What each dataset is expected to cover. koKR is zone names only.
EXPECTED = {
    "ZONE_NAMES": ("deDE", "esES", "frFR", "koKR", "ruRU"),
    "RACE_SPEECH_PROFILES": ("deDE", "esES", "frFR", "ruRU"),
    "ZONE_FLAVOR": ("deDE", "esES", "frFR", "ruRU"),
    "BG_LORE": ("deDE", "esES", "frFR", "ruRU"),
    "DUNGEON_FLAVOR": ("deDE", "esES", "frFR", "ruRU"),
}


def test_every_dataset_reaches_its_locales():
    for name, codes in EXPECTED.items():
        assert locales.available(name) == codes, (
            "%s serves %r, expected %r"
            % (name, locales.available(name), codes))


def test_tables_are_populated():
    """A silently empty table would fall back to English everywhere."""
    for name in EXPECTED:
        for code, table in locales.dataset(name).items():
            assert isinstance(table, dict), (
                "%s/%s is %s, not a dict" % (name, code, type(table)))
            assert table, "%s/%s is empty" % (name, code)


def test_keys_match_what_the_accessors_look_up():
    """Zone-keyed tables use ids; race-keyed tables use names."""
    for name in ("ZONE_NAMES", "ZONE_FLAVOR", "BG_LORE", "DUNGEON_FLAVOR"):
        for code, table in locales.dataset(name).items():
            bad = [k for k in table if not isinstance(k, int)]
            assert not bad, (
                "%s/%s has non-integer keys: %r" % (name, code, bad[:5]))

    for code, table in locales.dataset("RACE_SPEECH_PROFILES").items():
        bad = [k for k in table if not isinstance(k, str)]
        assert not bad, (
            "RACE_SPEECH_PROFILES/%s has non-string keys: %r"
            % (code, bad[:5]))


def test_bulk_language_data_stays_out_of_the_constants_module():
    """The regression this split exists to prevent."""
    strays = [
        name for name in dir(chatter_constants)
        if name.endswith(("_RU", "_FR", "_DE", "_ES", "_KO"))
        and isinstance(getattr(chatter_constants, name), dict)
    ]
    assert not strays, (
        "per-language tables are back in chatter_constants: %r" % strays)


def test_english_defaults_stay_where_the_accessors_expect_them():
    """Only the translations moved; the English base did not."""
    for name in EXPECTED:
        assert hasattr(chatter_constants, name), (
            "%s (the English default) must remain in chatter_constants"
            % name)


def main() -> int:
    test_every_dataset_reaches_its_locales()
    test_tables_are_populated()
    test_keys_match_what_the_accessors_look_up()
    test_bulk_language_data_stays_out_of_the_constants_module()
    test_english_defaults_stay_where_the_accessors_expect_them()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
