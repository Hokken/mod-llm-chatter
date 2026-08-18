#!/usr/bin/env python3
"""
mod-llm-chatter HEALTH CHECK (preflight diagnostic).

When bots will not chat, run this to get a clear
PASS/FAIL report pointing at the exact misconfiguration.
Most real-world failures are: wrong DB credentials, a
missing/placeholder API key for a cloud LLM provider, or
a wrong/unreachable local LLM (Ollama) URL.

Primary use: the bridge runs this automatically at startup
(gated by LLMChatter.HealthCheck.Enable). It imports
run_all_checks(), logs the PASS/FAIL report, also writes it to
<RequestLog dir>/healthcheck.log, and loud-exits on a critical
failure. Most users never run anything themselves.

It can also be run standalone (e.g. by a server admin re-checking
after editing the conf, without restarting the bridge):

  Docker (run inside the bridge container):
    docker exec ac-llm-chatter-bridge python \
        /app/chatter_healthcheck.py \
        --config /config/mod_llm_chatter.conf

  Non-Docker (run on the host, point at the real MySQL):
    python chatter_healthcheck.py \
        --config <path/to/mod_llm_chatter.conf> \
        --db-host 127.0.0.1

Zero extra dependencies — uses only the stdlib plus the
packages the bridge already needs (mysql.connector,
anthropic, openai), imported lazily so a missing optional
provider SDK never breaks the rest of the report.
"""

import argparse
import json
import os
import sys

from chatter_constants import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_GOOGLE_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OPENROUTER_MODEL,
    GOOGLE_OPENAI_BASE_URL,
    OPENROUTER_BASE_URL,
)
from chatter_llm import (
    _extract_anthropic_content,
    _extract_responses_content,
)
from chatter_provider import (
    apply_anthropic_options,
    apply_openai_compatible_options,
    create_anthropic_client,
    get_openai_compatible_request_mode,
)

# Path to the base SQL that creates the required tables
# (used in the "tables" check hint).
_TABLES_SQL_PATH = (
    'modules/mod-llm-chatter/data/sql/characters/'
    'base/00000000_llm_chatter_tables.sql'
)

# Required tables the bridge / C++ side depend on.
_REQUIRED_TABLES = [
    'llm_chatter_queue',
    'llm_chatter_events',
    'llm_chatter_messages',
    'llm_group_bot_traits',
    'llm_bot_memories',
    'llm_guild_chat_sessions',
    'llm_guild_session_history',
]

_VALID_PROVIDERS = (
    'anthropic', 'openai', 'google', 'openrouter', 'ollama'
)

# provider -> (api_key_config_key, example_placeholder)
_PROVIDER_KEYS = {
    'anthropic': ('LLMChatter.Anthropic.ApiKey', 'sk-ant-xxxxx'),
    'openai': ('LLMChatter.OpenAI.ApiKey', 'sk-xxxxx'),
    'google': ('LLMChatter.Google.ApiKey', 'AIza-xxxxx'),
    'openrouter': (
        'LLMChatter.OpenRouter.ApiKey', 'sk-or-v1-xxxxx'
    ),
}


def _result(check_id, title, status, message, hint=''):
    """Build a single check-result dict."""
    return {
        'id': check_id,
        'title': title,
        'status': status,
        'message': message,
        'hint': hint,
    }


# =====================================================================
# Target description helpers (never print the password)
# =====================================================================
def format_db_target(config):
    """Human string of the MySQL target being probed."""
    host = config.get(
        '__healthcheck_db_host__'
    ) or config.get('LLMChatter.Database.Host', 'localhost')
    port = config.get(
        '__healthcheck_db_port__'
    ) or config.get('LLMChatter.Database.Port', 3306)
    user = config.get('LLMChatter.Database.User', 'acore')
    name = config.get(
        'LLMChatter.Database.Name', 'acore_characters'
    )
    return f"{user}@{host}:{port}/{name}"


def format_llm_target(config):
    """Human string of the LLM endpoint/provider/model."""
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).strip().lower()
    default_model = DEFAULT_ANTHROPIC_MODEL
    if provider == 'openai':
        default_model = DEFAULT_OPENAI_MODEL
    elif provider == 'google':
        default_model = DEFAULT_GOOGLE_MODEL
    elif provider == 'openrouter':
        default_model = DEFAULT_OPENROUTER_MODEL
    model = config.get('LLMChatter.Model', default_model)

    if provider == 'ollama':
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://host.docker.internal:11434',
        )
        return f"ollama {model} @ {base_url}"
    if provider == 'google':
        base_url = config.get(
            'LLMChatter.Google.BaseUrl', GOOGLE_OPENAI_BASE_URL
        )
        return f"google {model} @ {base_url}"
    if provider == 'openrouter':
        base_url = config.get(
            'LLMChatter.OpenRouter.BaseUrl', OPENROUTER_BASE_URL
        )
        return f"openrouter {model} @ {base_url}"
    return f"{provider} {model}"


def _resolved_model(config, provider):
    """Resolve the model id for a provider as main() does."""
    default_model = DEFAULT_ANTHROPIC_MODEL
    if provider == 'openai':
        default_model = DEFAULT_OPENAI_MODEL
    elif provider == 'google':
        default_model = DEFAULT_GOOGLE_MODEL
    elif provider == 'openrouter':
        default_model = DEFAULT_OPENROUTER_MODEL
    model = config.get('LLMChatter.Model', default_model)
    try:
        from chatter_llm import resolve_model
        return resolve_model(model)
    except Exception:
        return model


# =====================================================================
# Individual checks (each NEVER raises, NEVER exits)
# =====================================================================
def _check_config_file(config, config_path):
    """Validate config path readability + parsed dict."""
    try:
        if config_path and not os.path.exists(config_path):
            return _result(
                'config_file', 'Config file', 'fail',
                f"Config file not found: {config_path}",
                "Pass the correct path with --config.",
            )
        if config_path and not os.access(config_path, os.R_OK):
            return _result(
                'config_file', 'Config file', 'fail',
                f"Config file not readable: {config_path}",
                "Check file permissions.",
            )
        if not config:
            return _result(
                'config_file', 'Config file', 'fail',
                "Config parsed to zero keys.",
                "Confirm the conf is a WoW-style Key = Value "
                "file and not empty.",
            )
        return _result(
            'config_file', 'Config file', 'pass',
            f"Loaded {len(config)} keys from "
            f"{config_path or '(in-memory)'}.",
        )
    except Exception as exc:
        return _result(
            'config_file', 'Config file', 'fail',
            f"Error reading config: {exc}",
            "Check the path and file contents.",
        )


def _check_module_enabled(config):
    """LLMChatter.Enable must be 1."""
    if config.get('LLMChatter.Enable', '0') == '1':
        return _result(
            'module_enabled', 'Module enabled', 'pass',
            "LLMChatter.Enable = 1.",
        )
    return _result(
        'module_enabled', 'Module enabled', 'warn',
        "LLMChatter.Enable is not 1; the bridge will idle "
        "and bots will never chat.",
        "Set LLMChatter.Enable = 1 in the conf and restart.",
    )


def _check_provider_config(config):
    """Validate provider name + API key (or Ollama URL)."""
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).strip().lower()

    if provider not in _VALID_PROVIDERS:
        return _result(
            'provider_config', 'LLM provider config', 'fail',
            f"Unknown provider '{provider}'.",
            "Set LLMChatter.Provider to one of: "
            + ", ".join(_VALID_PROVIDERS) + ".",
        )

    if provider == 'ollama':
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://host.docker.internal:11434',
        )
        msg = f"Provider 'ollama' (no API key needed). URL: {base_url}"
        if 'host.docker.internal' in base_url:
            msg += (
                ". Note: host-run (non-Docker) setups usually "
                "need http://localhost:11434 instead."
            )
        return _result(
            'provider_config', 'LLM provider config', 'pass', msg,
        )

    key_name, placeholder = _PROVIDER_KEYS[provider]
    api_key = (config.get(key_name, '') or '').strip()

    if not api_key:
        return _result(
            'provider_config', 'LLM provider config', 'fail',
            f"Provider '{provider}' has no API key set.",
            f"Set {key_name} to your real API key.",
        )

    if api_key == placeholder or 'xxxxx' in api_key.lower():
        return _result(
            'provider_config', 'LLM provider config', 'fail',
            f"The {provider} API key is still the example "
            "placeholder.",
            f"Replace the placeholder in {key_name} with your "
            "real key.",
        )

    return _result(
        'provider_config', 'LLM provider config', 'pass',
        f"Provider '{provider}', API key set in {key_name}.",
    )


def _db_connect(config):
    """Open a mysql connection mirroring get_db_connection,
    honoring optional __healthcheck_db_*__ overrides."""
    import mysql.connector
    host = config.get(
        '__healthcheck_db_host__'
    ) or config.get('LLMChatter.Database.Host', 'localhost')
    port = config.get(
        '__healthcheck_db_port__'
    ) or config.get('LLMChatter.Database.Port', 3306)
    return mysql.connector.connect(
        host=host,
        port=int(port),
        user=config.get('LLMChatter.Database.User', 'acore'),
        password=config.get(
            'LLMChatter.Database.Password', 'acore'
        ),
        database=config.get(
            'LLMChatter.Database.Name', 'acore_characters'
        ),
        # See issue #31: buffered cursors avoid cext
        # "Unread result found" errors.
        buffered=True,
    )


def _check_database(config):
    """Connect to MySQL and classify failures."""
    target = format_db_target(config)
    try:
        import mysql.connector
        from mysql.connector import errorcode
    except Exception as exc:
        return _result(
            'database', 'Database connection', 'fail',
            f"mysql.connector unavailable: {exc}",
            "Install mysql-connector-python in this "
            "environment.",
        )

    user = config.get('LLMChatter.Database.User', 'acore')
    name = config.get(
        'LLMChatter.Database.Name', 'acore_characters'
    )
    host = config.get(
        '__healthcheck_db_host__'
    ) or config.get('LLMChatter.Database.Host', 'localhost')
    port = config.get(
        '__healthcheck_db_port__'
    ) or config.get('LLMChatter.Database.Port', 3306)

    conn = None
    try:
        conn = _db_connect(config)
        return _result(
            'database', 'Database connection', 'pass',
            f"Connected to {target}.",
        )
    except mysql.connector.Error as exc:
        code = getattr(exc, 'errno', None)
        if code == errorcode.ER_ACCESS_DENIED_ERROR:
            return _result(
                'database', 'Database connection', 'fail',
                f"Access denied for user '{user}' — wrong "
                "username or password.",
                "Check LLMChatter.Database.User / "
                "LLMChatter.Database.Password. The bridge "
                "typically needs root/password, not "
                "acore/acore.",
            )
        if code == errorcode.ER_BAD_DB_ERROR:
            return _result(
                'database', 'Database connection', 'fail',
                f"Database '{name}' does not exist.",
                "Check LLMChatter.Database.Name (usually "
                "acore_characters).",
            )
        # Connection / interface errors (e.g. CR_CONN_HOST_ERROR
        # 2003) — cannot reach the server at all.
        return _result(
            'database', 'Database connection', 'fail',
            f"Cannot reach MySQL at {host}:{port}.",
            "Is MySQL running and reachable from here? Docker "
            "users running this on the host usually need "
            "--db-host 127.0.0.1 (the config host may be a "
            "container name).",
        )
    except Exception as exc:
        return _result(
            'database', 'Database connection', 'fail',
            f"Cannot reach MySQL at {host}:{port}: {exc}",
            "Is MySQL running and reachable from here? Docker "
            "users running this on the host usually need "
            "--db-host 127.0.0.1.",
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _check_tables(config, db_ok):
    """Verify required tables exist (skip if DB down)."""
    if not db_ok:
        return _result(
            'tables', 'Required tables', 'skip',
            "skipped — database not reachable",
        )

    name = config.get(
        'LLMChatter.Database.Name', 'acore_characters'
    )
    conn = None
    try:
        conn = _db_connect(config)
        cur = conn.cursor()
        cur.execute(
            "SELECT table_name FROM "
            "information_schema.tables "
            "WHERE table_schema = %s",
            (name,),
        )
        present = {
            (row[0] or '').lower() for row in cur.fetchall()
        }
        cur.close()
        missing = [
            t for t in _REQUIRED_TABLES
            if t.lower() not in present
        ]
        if missing:
            return _result(
                'tables', 'Required tables', 'fail',
                "Missing tables: " + ", ".join(missing) + ".",
                f"Load {_TABLES_SQL_PATH} into the characters "
                "DB (the module SQL did not run).",
            )
        return _result(
            'tables', 'Required tables', 'pass',
            f"All {len(_REQUIRED_TABLES)} required tables "
            f"present in {name}.",
        )
    except Exception as exc:
        return _result(
            'tables', 'Required tables', 'fail',
            f"Could not list tables in {name}: {exc}",
            "Check DB permissions for the configured user.",
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _is_auth_error(exc):
    """Best-effort detect of an LLM authentication error."""
    name = type(exc).__name__.lower()
    if 'authentication' in name or 'permissiondenied' in name:
        return True
    status = getattr(exc, 'status_code', None)
    if status in (401, 403):
        return True
    text = str(exc).lower()
    return (
        '401' in text or '403' in text
        or 'unauthorized' in text
        or 'invalid api key' in text
        or 'incorrect api key' in text
        or 'authentication' in text
    )


def _is_connection_error(exc):
    """Best-effort detect of an unreachable-endpoint error."""
    name = type(exc).__name__.lower()
    if 'connection' in name or 'timeout' in name:
        return True
    text = str(exc).lower()
    return (
        'connection refused' in text
        or 'failed to establish a new connection' in text
        or 'cannot connect' in text
        or 'connection error' in text
        or 'max retries' in text
        or 'name or service not known' in text
        or 'timed out' in text
    )


def _is_model_error(exc):
    """Best-effort detect of a model not-found / rejected error."""
    name = type(exc).__name__.lower()
    if 'notfound' in name:
        return True
    status = getattr(exc, 'status_code', None)
    if status == 404:
        return True
    text = str(exc).lower()
    return (
        'model' in text and (
            'not found' in text
            or 'does not exist' in text
            or 'invalid model' in text
            or 'unknown model' in text
        )
    )


def _probe_anthropic(config, model):
    """Make a minimal Anthropic call; returns text or raises."""
    import anthropic
    client = create_anthropic_client(anthropic, config)
    kwargs = {
        'model': model,
        'max_tokens': 5,
        'messages': [{
            'role': 'user',
            'content': 'Reply with the single word: OK',
        }],
    }
    apply_anthropic_options(kwargs, config)
    resp = client.messages.create(**kwargs)
    return _extract_anthropic_content(resp, 'healthcheck') or ''


def _probe_openai_compatible(
    client, model, config=None, provider=''
):
    """Make a minimal OpenAI-compatible call; text or raises."""
    request_mode = 'chat'
    if provider == 'openrouter' and config:
        request_mode = get_openai_compatible_request_mode(config)

    if request_mode == 'responses':
        kwargs = {
            'model': model,
            'max_output_tokens': 150,
            'input': 'Reply with the single word: OK',
        }
        apply_openai_compatible_options(
            kwargs, config, request_mode='responses'
        )
        resp = client.responses.create(**kwargs)
        return _extract_responses_content(
            resp, 'healthcheck'
        ) or ''

    kwargs = {
        'model': model,
        'max_tokens': 150,
        'messages': [{
            'role': 'user',
            'content': 'Reply with the single word: OK',
        }],
    }
    if provider == 'openrouter' and config:
        apply_openai_compatible_options(
            kwargs, config, request_mode='chat'
        )
    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content
    if isinstance(content, str):
        return content.strip()
    return str(content or '').strip()


def _build_openai_compatible_client(config, provider):
    """Construct the OpenAI-style client exactly like main()."""
    import openai
    if provider == 'ollama':
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://host.docker.internal:11434',
        )
        return openai.OpenAI(
            base_url=f"{base_url.rstrip('/')}/v1",
            api_key='ollama',
        )
    if provider == 'openai':
        return openai.OpenAI(
            api_key=config.get('LLMChatter.OpenAI.ApiKey', ''),
        )
    if provider == 'google':
        return openai.OpenAI(
            api_key=config.get('LLMChatter.Google.ApiKey', ''),
            base_url=config.get(
                'LLMChatter.Google.BaseUrl', GOOGLE_OPENAI_BASE_URL
            ),
        )
    # openrouter
    kwargs = {
        'api_key': config.get('LLMChatter.OpenRouter.ApiKey', ''),
        'base_url': config.get(
            'LLMChatter.OpenRouter.BaseUrl', OPENROUTER_BASE_URL
        ),
    }
    return openai.OpenAI(**kwargs)


def _check_llm_probe(config):
    """Make a minimal real LLM call and classify failures."""
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).strip().lower()
    target = format_llm_target(config)
    model = _resolved_model(config, provider)

    # Endpoint URL for connection-error hints.
    if provider == 'ollama':
        endpoint = config.get(
            'LLMChatter.Ollama.BaseUrl',
            'http://host.docker.internal:11434',
        )
    elif provider == 'google':
        endpoint = config.get(
            'LLMChatter.Google.BaseUrl', GOOGLE_OPENAI_BASE_URL
        )
    elif provider == 'openrouter':
        endpoint = config.get(
            'LLMChatter.OpenRouter.BaseUrl', OPENROUTER_BASE_URL
        )
    else:
        endpoint = "the provider API"

    try:
        if provider == 'anthropic':
            text = _probe_anthropic(config, model)
        else:
            client = _build_openai_compatible_client(
                config, provider
            )
            text = _probe_openai_compatible(
                client, model, config, provider
            )

        if text:
            return _result(
                'llm_probe',
                'LLM connectivity (live test)', 'pass',
                f"Live call succeeded ({target}).",
            )
        return _result(
            'llm_probe', 'LLM connectivity (live test)', 'fail',
            f"The LLM returned an empty response ({target}).",
            "The endpoint is reachable but produced no text — "
            "check the model / max_tokens for this provider.",
        )
    except Exception as exc:
        if _is_auth_error(exc):
            return _result(
                'llm_probe',
                'LLM connectivity (live test)', 'fail',
                "API key was rejected (authentication failed) "
                "— the key is present but invalid.",
                "Double-check the key value for typos / that "
                "it's active and has credit.",
            )
        if _is_connection_error(exc):
            return _result(
                'llm_probe',
                'LLM connectivity (live test)', 'fail',
                f"Cannot reach the LLM endpoint at {endpoint}.",
                "Is the LLM server running and is the URL "
                "correct? Docker users pointing at a local "
                "Ollama usually need host.docker.internal; "
                "host users need localhost.",
            )
        if _is_model_error(exc):
            return _result(
                'llm_probe',
                'LLM connectivity (live test)', 'fail',
                f"Model '{model}' was rejected or not found.",
                "Check LLMChatter.Model is a valid model for "
                "this provider.",
            )
        return _result(
            'llm_probe', 'LLM connectivity (live test)', 'fail',
            f"LLM probe failed: {exc}",
            "Check the provider, API key, and endpoint URL.",
        )


# =====================================================================
# Orchestration
# =====================================================================
def run_all_checks(config, *, do_llm_probe=True):
    """Run all checks in order, return list of result dicts."""
    config_path = config.get('__healthcheck_config_path__', '')
    results = []
    results.append(_check_config_file(config, config_path))
    results.append(_check_module_enabled(config))
    results.append(_check_provider_config(config))

    db_result = _check_database(config)
    results.append(db_result)
    db_ok = db_result['status'] == 'pass'

    results.append(_check_tables(config, db_ok))

    if do_llm_probe:
        results.append(_check_llm_probe(config))
    else:
        results.append(_result(
            'llm_probe', 'LLM connectivity (live test)', 'skip',
            "skipped — live LLM probe disabled",
        ))
    return results


def has_critical_failure(results):
    """True if any result has status 'fail'."""
    return any(r.get('status') == 'fail' for r in results)


_STATUS_LABEL = {
    'pass': 'PASS',
    'fail': 'FAIL',
    'warn': 'WARN',
    'skip': 'SKIP',
}

# ANSI colors keyed by status (only used on a TTY).
_STATUS_ANSI = {
    'pass': '\033[32m',
    'fail': '\033[31m',
    'warn': '\033[33m',
    'skip': '\033[90m',
}
_ANSI_RESET = '\033[0m'


def render_text_report(results, config_path, use_color=None):
    """Produce a plain-terminal report.

    use_color: None -> auto (color only on a TTY); pass False to
    force plain text (e.g. when writing to a file).
    """
    if use_color is None:
        use_color = sys.stdout.isatty()
    lines = []
    lines.append('=' * 60)
    lines.append('mod-llm-chatter HEALTH CHECK')
    lines.append('=' * 60)
    lines.append(f"Config: {config_path or '(in-memory)'}")
    for r in results:
        status = r.get('status', 'fail')
        label = _STATUS_LABEL.get(status, '????')
        if use_color:
            tag = (
                f"{_STATUS_ANSI.get(status, '')}"
                f"[{label}]{_ANSI_RESET}"
            )
        else:
            tag = f"[{label}]"
        lines.append('-' * 60)
        lines.append(f"{tag} {r.get('title', r.get('id', ''))}")
        msg = r.get('message', '')
        if msg:
            lines.append(f"      {msg}")
        hint = r.get('hint', '')
        if hint and status in ('fail', 'warn'):
            lines.append(f"      -> {hint}")
    lines.append('=' * 60)
    return '\n'.join(lines)


def save_report_file(path, results, config_path):
    """Write a plain-text (no-color) report to a file.

    Truncates/overwrites on each call and prepends a timestamp.
    Returns True on success; never raises (returns False on any
    error, e.g. an unwritable directory).
    """
    try:
        from datetime import datetime
        text = render_text_report(
            results, config_path, use_color=False
        )
        header = (
            "Generated: "
            + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            + "\n"
        )
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(header + text + "\n")
        return True
    except Exception:
        return False


# =====================================================================
# CLI
# =====================================================================
def _load_config_tolerantly(config_path):
    """Load config, but tolerate failure (parse_config exits)."""
    if not os.path.exists(config_path):
        print(
            f"ERROR: config file not found: {config_path}",
            file=sys.stderr,
        )
        sys.exit(2)
    if not os.access(config_path, os.R_OK):
        print(
            f"ERROR: config file not readable: {config_path}",
            file=sys.stderr,
        )
        sys.exit(2)
    config = {}
    try:
        with open(config_path, 'r') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except Exception as exc:
        print(
            f"ERROR: failed to read config: {exc}",
            file=sys.stderr,
        )
        sys.exit(2)
    return config


def main():
    parser = argparse.ArgumentParser(
        description='mod-llm-chatter health check / preflight'
    )
    parser.add_argument(
        '--config', required=True,
        help='Path to mod_llm_chatter.conf',
    )
    parser.add_argument(
        '--no-llm', action='store_true',
        help='Skip the live LLM probe',
    )
    parser.add_argument(
        '--db-host', default=None,
        help='Override DB host (e.g. 127.0.0.1 on the host)',
    )
    parser.add_argument(
        '--db-port', default=None,
        help='Override DB port',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Print results as JSON instead of text',
    )
    args = parser.parse_args()

    config = _load_config_tolerantly(args.config)
    config['__healthcheck_config_path__'] = args.config
    if args.db_host:
        config['__healthcheck_db_host__'] = args.db_host
    if args.db_port:
        config['__healthcheck_db_port__'] = args.db_port

    do_llm = not args.no_llm

    results = run_all_checks(config, do_llm_probe=do_llm)

    if args.json:
        print(json.dumps({
            'results': results,
            'ok': not has_critical_failure(results),
        }, ensure_ascii=False, indent=2))
    else:
        print(render_text_report(results, args.config))
        if has_critical_failure(results):
            print(
                "RESULT: FAILED — fix the items marked "
                "[FAIL] above."
            )
        else:
            print("RESULT: OK — no critical failures.")

    return 1 if has_critical_failure(results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
