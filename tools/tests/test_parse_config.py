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


def test_config_log_lines_mask_secrets():
    config = {
        "LLMChatter.Enable": "1",
        "LLMChatter.Anthropic.ApiKey": "sk-ant-real-secret",
        "LLMChatter.OpenAI.ApiKey": "",
        "LLMChatter.Database.Password": "acore",
        "LLMChatter.MaxTokens": "350",
        "__healthcheck_config_path__": "/etc/chatter.conf",
    }
    lines = chatter_shared.format_config_for_log(config)
    text = "\n".join(lines)
    rows = {
        line.split()[0]: line.split(None, 1)[1]
        for line in lines if line.startswith("  ")
    }
    assert "sk-ant-real-secret" not in text, text
    assert "acore" not in text, text
    assert rows["Anthropic.ApiKey"] == "<set, hidden>", rows
    assert rows["OpenAI.ApiKey"] == "<empty>", rows
    assert rows["Database.Password"] == "<set, hidden>", rows
    # Non-secret values, including *Tokens keys, print as-is.
    assert rows["MaxTokens"] == "350", rows
    assert rows["Enable"] == "1", rows
    # Internal runtime keys are not part of the user's config.
    assert "__healthcheck" not in text, text
    # Without section data everything lands in one OTHER group.
    assert lines[1].startswith("-- OTHER (5) "), lines
    assert lines[2].strip().startswith("Enable"), lines


def test_config_log_groups_by_file_section():
    data = (
        "# header comment, no section yet\n"
        "###############################################################\n"
        "# ESSENTIAL SETTINGS [BOTH]\n"
        "#\n"
        "#   intro text\n"
        "###############################################################\n"
        "LLMChatter.Enable = 1\n"
        "LLMChatter.HealthCheck.LogPath =\n"
        "###############################################################\n"
        "# ANTHROPIC SETTINGS [BRIDGE] (only needed if Provider = x)\n"
        "###############################################################\n"
        "LLMChatter.Anthropic.Model = claude-haiku\n"
        "###############################################################\n"
        "# Emote Reaction System [SERVER]\n"
        "###############################################################\n"
        "LLMChatter.EmoteReactions.Enable = 1\n"
    ).encode("utf-8")
    path = _write_config(data)
    try:
        config = chatter_shared.parse_config(path)
        sections = chatter_shared.parse_config_sections(path)
    finally:
        os.unlink(path)
    config["LLMChatter.NotInFile"] = "7"
    lines = chatter_shared.format_config_for_log(config, sections)
    headers = [line for line in lines if line.startswith("-- ")]
    assert [h.split(" (")[0] for h in headers] == [
        "-- ESSENTIAL SETTINGS",
        "-- ANTHROPIC SETTINGS",
        "-- EMOTE REACTION SYSTEM",
        "-- OTHER",
    ], headers
    assert headers[0].startswith("-- ESSENTIAL SETTINGS (2) --"), headers
    # A blank line separates every group.
    for i, line in enumerate(lines):
        if line.startswith("-- "):
            assert lines[i - 1] == "", lines
    # Values line up within a group; empty values are visible.
    essential = lines[2:4]
    assert essential[0].index("1") == essential[1].index("<empty>"), (
        essential
    )


def main() -> int:
    test_utf8_with_bom_and_non_ascii_parses()
    test_legacy_cp1252_config_remains_readable()
    test_missing_file_logs_and_exits()
    test_config_log_lines_mask_secrets()
    test_config_log_groups_by_file_section()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
