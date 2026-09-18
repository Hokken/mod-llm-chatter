"""OpenAI-compatible request construction and recovery.

DeepSeek and Ollama both expose the common Chat Completions shape, but
individual models do not accept every optional parameter.  This module
keeps those differences out of the feature call sites and learns
narrowly-scoped fallbacks when a provider explicitly rejects a
parameter.
"""

import logging
import re
import threading


logger = logging.getLogger(__name__)

_MODEL_OVERRIDES = {}
_MODEL_OVERRIDES_LOCK = threading.Lock()

_REJECTION_MARKERS = (
    "unsupported",
    "not supported",
    "does not support",
    "unknown parameter",
    "unrecognized parameter",
    "unexpected keyword",
    "only the default",
)

_REJECTION_CODES = {
    "invalid_parameter",
    "unsupported_parameter",
    "unsupported_value",
}

_GENERIC_REJECTION_CODES = {
    "invalid_request_error",
}


def _normalized_target(provider, model):
    return (
        str(provider or "").strip().lower(),
        str(model or "").strip().lower(),
    )


def _cached_overrides(provider, model):
    key = _normalized_target(provider, model)
    with _MODEL_OVERRIDES_LOCK:
        return dict(_MODEL_OVERRIDES.get(key, {}))


def _remember_override(provider, model, name, value):
    key = _normalized_target(provider, model)
    with _MODEL_OVERRIDES_LOCK:
        _MODEL_OVERRIDES.setdefault(key, {})[name] = value


def _apply_cached_overrides(kwargs, provider, model):
    overrides = _cached_overrides(provider, model)
    if overrides.get("omit_temperature"):
        kwargs.pop("temperature", None)
    if overrides.get("omit_reasoning_effort"):
        kwargs.pop("reasoning_effort", None)

    token_field = overrides.get("token_field")
    if token_field == "max_completion_tokens" and "max_tokens" in kwargs:
        kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
    elif token_field == "max_tokens" and "max_completion_tokens" in kwargs:
        kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")


def build_chat_options(max_tokens, temperature=None):
    """Build the optional Chat Completions parameters.

    Both supported providers accept ``max_tokens`` and sampling
    temperature; reasoning is applied per provider in
    ``chatter_llm.py``.  Learned overrides still apply, so a model
    that once rejected a parameter keeps the corrected shape.
    """
    kwargs = {"max_tokens": max_tokens}
    if temperature is not None:
        kwargs["temperature"] = temperature
    return kwargs


def describe_model_compatibility(provider, model):
    """Return a concise description suitable for startup logs."""
    options = dict(build_chat_options(1, temperature=0.5))
    _apply_cached_overrides(options, provider, model)
    temperature = (
        "custom" if "temperature" in options else "provider-default"
    )
    token_field = (
        "max_completion_tokens"
        if "max_completion_tokens" in options
        else "max_tokens"
    )
    return (
        f"profile=openai-compatible, token_limit={token_field}, "
        f"temperature={temperature}, "
        f"reasoning_effort=provider-specific"
    )


def _error_status(error):
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    try:
        return int(status)
    except (TypeError, ValueError):
        return None


def _error_body(error):
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return {}
    nested = body.get("error")
    return nested if isinstance(nested, dict) else body


def _normalize_parameter(value):
    return str(value or "").lower().replace("-", "_").replace(".", "_")


def _is_parameter_rejection(error, parameter):
    """Match only a client error that rejects the named parameter."""
    if _error_status(error) not in (400, 422):
        return False

    body = _error_body(error)
    structured_param = _normalize_parameter(body.get("param"))
    structured_code = _normalize_parameter(body.get("code"))
    if structured_param:
        if structured_param != parameter:
            return False
        if structured_code in _REJECTION_CODES:
            return True
        if (
            structured_code
            and structured_code not in _GENERIC_REJECTION_CODES
        ):
            return False

    message = _normalize_parameter(str(error))
    markers = "|".join(re.escape(marker) for marker in _REJECTION_MARKERS)
    parameter_pattern = re.escape(parameter)
    return bool(re.search(
        rf"(?:{parameter_pattern}.{{0,100}}(?:{markers})|"
        rf"(?:{markers}).{{0,100}}{parameter_pattern})",
        message,
    ))


def _adjust_rejected_parameters(
    kwargs,
    provider,
    model,
    error,
    changed_fields,
):
    """Apply one safe correction for an explicit parameter rejection."""
    if (
        "temperature" in kwargs
        and "temperature" not in changed_fields
        and _is_parameter_rejection(error, "temperature")
    ):
        kwargs.pop("temperature", None)
        changed_fields.add("temperature")
        _remember_override(
            provider, model, "omit_temperature", True
        )
        return "omitted unsupported temperature"

    if (
        "reasoning_effort" in kwargs
        and "reasoning_effort" not in changed_fields
        and _is_parameter_rejection(error, "reasoning_effort")
    ):
        kwargs.pop("reasoning_effort", None)
        changed_fields.add("reasoning_effort")
        _remember_override(
            provider, model, "omit_reasoning_effort", True
        )
        return "omitted unsupported reasoning_effort"

    if (
        "max_tokens" in kwargs
        and "token_field" not in changed_fields
        and _is_parameter_rejection(error, "max_tokens")
    ):
        kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
        changed_fields.add("token_field")
        _remember_override(
            provider, model, "token_field",
            "max_completion_tokens",
        )
        return "changed max_tokens to max_completion_tokens"

    if (
        "max_completion_tokens" in kwargs
        and "token_field" not in changed_fields
        and _is_parameter_rejection(
            error, "max_completion_tokens"
        )
    ):
        kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")
        changed_fields.add("token_field")
        _remember_override(
            provider, model, "token_field", "max_tokens"
        )
        return "changed max_completion_tokens to max_tokens"

    return None


def create_chat_completion(
    operation,
    request_kwargs,
    provider,
    model,
    request_logger=None,
):
    """Call Chat Completions and learn explicit compatibility fixes.

    Only invalid-parameter failures are retried. Authentication,
    availability, rate-limit, timeout, and content errors propagate
    unchanged to the normal provider error handling.
    """
    active_logger = request_logger or logger
    kwargs = dict(request_kwargs)
    _apply_cached_overrides(kwargs, provider, model)
    changed_fields = set()
    last_error = None

    for _ in range(4):
        try:
            return operation(**kwargs)
        except Exception as error:
            last_error = error
            adjustment = _adjust_rejected_parameters(
                kwargs,
                provider,
                model,
                error,
                changed_fields,
            )
            if not adjustment:
                raise
            active_logger.warning(
                "Adjusted request parameters for %s/%s after provider "
                "rejection: %s",
                provider,
                model,
                adjustment,
            )
    raise last_error


def reset_compatibility_cache():
    """Clear learned model overrides (used by focused tests)."""
    with _MODEL_OVERRIDES_LOCK:
        _MODEL_OVERRIDES.clear()
