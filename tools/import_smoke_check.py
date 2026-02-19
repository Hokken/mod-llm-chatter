#!/usr/bin/env python3
"""Import smoke/cycle guard for mod-llm-chatter tools.

Default mode focuses on internal import/cycle safety by stubbing
optional third-party provider modules if missing locally.

Use --strict to require real third-party dependencies.
"""

import argparse
import importlib
import sys
import traceback
import types
from pathlib import Path


def _ensure_module(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


def _install_non_strict_stubs() -> list[str]:
    """Install minimal stubs for optional deps.

    Returns names of modules that were stubbed.
    """
    stubbed: list[str] = []

    for mod_name in ("anthropic", "openai"):
        try:
            importlib.import_module(mod_name)
        except ModuleNotFoundError:
            mod = _ensure_module(mod_name)
            if mod_name == "anthropic":
                setattr(mod, "Anthropic", type("Anthropic", (), {}))
            elif mod_name == "openai":
                setattr(mod, "OpenAI", type("OpenAI", (), {}))
            stubbed.append(mod_name)

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_mod = _ensure_module("mysql")
        connector_mod = _ensure_module("mysql.connector")
        setattr(mysql_mod, "connector", connector_mod)
        stubbed.append("mysql.connector")

    return stubbed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="require real third-party dependencies",
    )
    args = parser.parse_args()

    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

    stubbed = []
    if not args.strict:
        stubbed = _install_non_strict_stubs()

    try:
        __import__("llm_chatter_bridge")
    except Exception:
        traceback.print_exc()
        print("IMPORT_SMOKE_FAIL")
        return 1

    if stubbed:
        print("OK (stubbed: " + ", ".join(stubbed) + ")")
    else:
        print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
