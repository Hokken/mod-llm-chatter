# -*- coding: utf-8 -*-
"""Per-language data for mod-llm-chatter, one module per locale.

These tables are bulk translation data rather than module logic, so they
live here instead of in chatter_constants.py. Each module names its
dictionaries without a locale suffix -- the module is the locale -- and
this registry maps WoW locale codes onto them.

A locale carries only the datasets it actually has. Callers ask for one
dataset at a time with dataset(), and any locale missing it simply does
not appear in the result, which is what lets the accessors in
chatter_shared.py fall back to English per lookup.
"""

from typing import Any, Dict

from . import deDE, esES, frFR, koKR, ruRU

LOCALE_MODULES = {
    "ruRU": ruRU,
    "frFR": frFR,
    "deDE": deDE,
    "esES": esES,
    "koKR": koKR,
}


def dataset(name: str) -> Dict[str, Any]:
    """Map every locale that has `name` onto its table.

    Locales without that dataset are omitted rather than mapped to an
    empty dict, so a caller can tell "no translation exists" from "the
    translation is empty".
    """
    found = {}
    for code, module in LOCALE_MODULES.items():
        table = getattr(module, name, None)
        if table:
            found[code] = table
    return found


def available(name: str) -> tuple:
    """Locale codes carrying `name`, for tests and diagnostics."""
    return tuple(sorted(dataset(name)))
