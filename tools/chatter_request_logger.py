"""
Thread-safe JSONL logger for LLM requests.

Logs every LLM API call (prompt, response, timing)
to a rotating JSONL file for offline analysis.

Config keys (all [BRIDGE]):
  LLMChatter.RequestLog.Enable     (default 0)
  LLMChatter.RequestLog.Path       (default see below)
  LLMChatter.RequestLog.MaxSizeMB  (default 50)

Only imports stdlib — no circular dependency risk.
"""

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_enabled = False
_log_path = None
_max_size_bytes = 50 * 1024 * 1024
_lock = threading.Lock()
_seq = 0

_DEFAULT_PATH = '/logs/llm_requests.jsonl'


def init_request_logger(config: dict) -> None:
    """Read config and prepare the log file path.

    Call once at bridge startup after parse_config().
    """
    global _enabled, _log_path, _max_size_bytes, _seq

    enable = config.get(
        'LLMChatter.RequestLog.Enable', '0'
    )
    _enabled = (str(enable).strip() == '1')
    if not _enabled:
        return

    raw_path = config.get(
        'LLMChatter.RequestLog.Path',
        _DEFAULT_PATH
    ).strip()
    _log_path = Path(raw_path)

    max_mb = int(config.get(
        'LLMChatter.RequestLog.MaxSizeMB', 50
    ))
    _max_size_bytes = max(1, max_mb) * 1024 * 1024

    # Create directory if needed
    try:
        _log_path.parent.mkdir(
            parents=True, exist_ok=True
        )
    except OSError as exc:
        logger.error(
            "RequestLog: cannot create dir %s: %s",
            _log_path.parent, exc
        )
        _enabled = False
        return

    _seq = 0
    logger.info(
        "RequestLog enabled -> %s (max %d MB)",
        _log_path, max_mb
    )


def _rotate_if_needed() -> None:
    """Rename current log to .1.jsonl and start
    fresh if the file exceeds the configured size.

    Caller must hold _lock.
    """
    if _log_path is None:
        return
    try:
        size = _log_path.stat().st_size
    except FileNotFoundError:
        return
    if size < _max_size_bytes:
        return

    rotated = _log_path.with_suffix('.1.jsonl')
    try:
        # Overwrite previous rotation
        if rotated.exists():
            rotated.unlink()
        _log_path.rename(rotated)
    except OSError as exc:
        logger.error(
            "RequestLog: rotation failed: %s", exc
        )


def log_request(
    label: str,
    prompt: str,
    response,
    model: str,
    provider: str,
    duration_ms: int,
    metadata: dict = None,
    system_prompt: str = None,
) -> None:
    """Write one JSONL entry. No-op when disabled.

    metadata: optional dict of extra fields merged
    between duration_ms and prompt. Only non-empty
    string values are written (no null keys).
    system_prompt: if set, logged as a separate field
    so the user/system split is visible in logs.
    """
    if not _enabled:
        return

    global _seq

    ts = datetime.now(timezone.utc).isoformat()

    with _lock:
        _seq += 1
        seq = _seq

        _rotate_if_needed()

        entry = {
            'timestamp': ts,
            'seq': seq,
            'label': label,
            'model': model,
            'provider': provider,
            'duration_ms': duration_ms,
        }
        if metadata:
            for k, v in metadata.items():
                if v is not None and v != "":
                    entry[k] = v
        if system_prompt is not None:
            entry['system_prompt'] = system_prompt
        entry['prompt'] = prompt
        entry['response'] = response

        try:
            with open(
                _log_path, 'a', encoding='utf-8'
            ) as fh:
                fh.write(
                    json.dumps(
                        entry, ensure_ascii=False
                    ) + '\n'
                )
        except OSError as exc:
            logger.error(
                "RequestLog: write failed: %s", exc
            )


def log_delivered_messages(
    label: str,
    original_messages: list,
    delivered_messages: list,
) -> None:
    """Log before/after action stripping for
    conversation messages. No-op when disabled.

    original_messages: snapshot before stripping
    delivered_messages: same list after stripping
    """
    if not _enabled:
        return

    global _seq

    ts = datetime.now(timezone.utc).isoformat()

    with _lock:
        _seq += 1
        seq = _seq

        _rotate_if_needed()

        # Format as readable text for log viewer
        orig_lines = []
        deliv_lines = []
        for o, d in zip(
            original_messages, delivered_messages
        ):
            name = o.get('name', '?')
            o_act = o.get('action') or '(none)'
            d_act = d.get('action') or '(none)'
            orig_lines.append(
                f"{name}: {o_act}"
            )
            kept = d.get('action') is not None
            tag = 'KEPT' if kept else 'STRIPPED'
            deliv_lines.append(
                f"{name}: {d_act}  [{tag}]"
            )

        entry = {
            'timestamp': ts,
            'seq': seq,
            'label': f'{label}__delivered',
            'model': '',
            'provider': '',
            'duration_ms': 0,
            'prompt': (
                "ORIGINAL actions (from LLM):\n"
                + "\n".join(orig_lines)
            ),
            'response': (
                "DELIVERED actions (after "
                "ActionChance strip):\n"
                + "\n".join(deliv_lines)
            ),
        }

        try:
            with open(
                _log_path, 'a', encoding='utf-8'
            ) as fh:
                fh.write(
                    json.dumps(
                        entry, ensure_ascii=False
                    ) + '\n'
                )
        except OSError as exc:
            logger.error(
                "RequestLog: write failed: %s", exc
            )
