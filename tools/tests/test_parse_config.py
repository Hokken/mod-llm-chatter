#!/usr/bin/env python3
"""Regression checks for parse_config() config-file encoding handling.

Run directly from the module root:
  python tools/tests/test_parse_config.py
"""

import importlib
import logging
import os
import sys
import tempfile
import types
from pathlib import Path


def _ensure_module(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


def _install_non_strict_stubs() -> None:
    """Install minimal stubs for optional provider/database deps."""
    for mod_name in ("anthropic", "openai"):
        try:
            importlib.import_module(mod_name)
        except ModuleNotFoundError:
            mod = _ensure_module(mod_name)
            if mod_name == "anthropic":
                setattr(mod, "Anthropic", type("Anthropic", (), {}))
            else:
                setattr(mod, "OpenAI", type("OpenAI", (), {}))

    try:
        importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        mysql_mod = _ensure_module("mysql")
        connector_mod = _ensure_module("mysql.connector")
        setattr(mysql_mod, "connector", connector_mod)


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_shared  # noqa: E402


def _write_config(data: bytes) -> str:
    fd, path = tempfile.mkstemp(prefix="chatter_cfg_", suffix=".conf")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def test_utf8_with_bom_and_non_ascii_parses():
    # UTF-8 BOM + a right double quotation mark (U+201D). Its UTF-8 bytes
    # end in 0x9D, which cp1252 rejects, so this only decodes as UTF-8.
    data = "﻿LLMChatter.Greeting = Hail”\n".encode("utf-8")
    path = _write_config(data)
    try:
        config = chatter_shared.parse_config(path)
    finally:
        os.unlink(path)
    # BOM must be stripped from the first key, value must round-trip.
    assert config["LLMChatter.Greeting"] == "Hail”", config


def test_legacy_cp1252_config_remains_readable():
    # 'cafe' + 0xE9 ('e' acute) is a valid cp1252 byte but invalid UTF-8,
    # so it exercises the locale fallback. Force cp1252 so the test is
    # deterministic on non-Windows hosts too.
    data = b"LLMChatter.Name = caf\xe9\n"
    path = _write_config(data)
    original = chatter_shared.locale.getpreferredencoding
    chatter_shared.locale.getpreferredencoding = (
        lambda do_setlocale=True: "cp1252"
    )
    try:
        config = chatter_shared.parse_config(path)
    finally:
        chatter_shared.locale.getpreferredencoding = original
        os.unlink(path)
    assert config["LLMChatter.Name"] == "café", config


def test_missing_file_logs_and_exits():
    handler = _ListHandler()
    chatter_shared.logger.addHandler(handler)
    missing = os.path.join(
        tempfile.gettempdir(), "chatter_cfg_does_not_exist_9d201d.conf"
    )
    if os.path.exists(missing):
        os.unlink(missing)
    try:
        exit_code = None
        try:
            chatter_shared.parse_config(missing)
        except SystemExit as exc:
            exit_code = exc.code
        assert exit_code == 1, "parse_config should sys.exit(1) on read failure"
        assert handler.records, "expected a fatal log record"
        message = handler.records[-1].getMessage()
        assert "FATAL" in message, message
        assert missing in message, message
        # The underlying error type should be surfaced, not swallowed.
        assert "FileNotFoundError" in message, message
    finally:
        chatter_shared.logger.removeHandler(handler)


def main() -> int:
    test_utf8_with_bom_and_non_ascii_parses()
    test_legacy_cp1252_config_remains_readable()
    test_missing_file_logs_and_exits()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
