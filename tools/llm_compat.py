"""Model-aware OpenAI-compatible request construction and recovery.

Provider APIs expose a common Chat Completions shape, but individual
models do not accept every optional parameter.  This module keeps those
differences out of the feature call sites and learns narrowly-scoped
fallbacks when a provider explicitly rejects a parameter.
"""

import logging
from copy import deepcopy
import re
import threading


logger = logging.getLogger(__name__)

_MODEL_OVERRIDES = {}
_MODEL_OVERRIDES_LOCK = threading.Lock()

# First match wins: verified model capabilities precede family fallbacks.
# Columns: model pattern, request profile, explicit "none" effort support.
# GPT-6 Astra and GPT-6.1 Sol deliberately use the reasoning fallback.
_OPENAI_MODEL_PROFILES = (
    (r"^gpt-6-(?:luna|sol)$", "reasoning", True),
    (r"^gpt-5\.\d", "reasoning", True),
    (r"^(?:gpt-5|gpt-6|o1|o3|o4)", "reasoning", False),
    (r"^(?:gpt-3\.5|gpt-4|chatgpt-4)", "sampling", False),
)

_REJECTION_MARKERS = (
    "unsupported",
    "not supported",
    "does not support",
    "unknown parameter",
    "unrecognized parameter",
    "unexpected keyword",
    "only the default",
    "deprecated",
)

_REJECTION_CODES = {
    "invalid_parameter",
    "unsupported_parameter",
    "unsupported_value",
}

_GENERIC_REJECTION_CODES = {
    "invalid_request_error",
}

# Optional Anthropic request fields that may be dropped after an
# explicit rejection, in the order they are checked.
_ANTHROPIC_OPTIONAL_FIELDS = ("temperature", "thinking")


def _normalized_target(provider, model):
    return (
        str(provider or "").strip().lower(),
        str(model or "").strip().lower(),
    )


def _openai_model_name(provider, model):
    """Return an OpenAI model ID, including OpenRouter-routed IDs."""
    provider, model = _normalized_target(provider, model)
    if provider == "openrouter" and model.startswith("openai/"):
        model = model.split("/", 1)[1]
    elif provider != "openai":
        return ""
    if model.startswith("ft:"):
        model = model.split(":", 2)[1]
    return model


def _openai_model_profile(provider, model):
    """Resolve model capabilities independently of provider transport."""
    model_name = _openai_model_name(provider, model)
    for pattern, profile, supports_none in _OPENAI_MODEL_PROFILES:
        if re.match(pattern, model_name):
            return profile, supports_none
    return "safe-default", False


def needs_reasoning_token_multiplier(
    provider, model, reasoning_effort=None
):
    """Return whether hidden reasoning can consume the output budget."""
    provider, _ = _normalized_target(provider, model)
    capabilities = model_capabilities(provider, model)
    if provider != "openai" or not capabilities["reasoning_effort"]:
        return False
    effort = str(reasoning_effort or "").strip().lower()
    if effort == "none":
        return (
            not capabilities["reasoning_effort_none"]
            or _cached_overrides(provider, model).get(
                "omit_reasoning_effort", False
            )
        )
    return True


def model_capabilities(provider, model):
    """Resolve a conservative request profile for a model target."""
    provider, _ = _normalized_target(provider, model)
    profile, supports_none = _openai_model_profile(provider, model)
    reasoning = profile == "reasoning"

    if provider == "openai":
        return {
            "profile": profile,
            "token_field": "max_completion_tokens",
            "temperature": profile == "sampling",
            "reasoning_effort": reasoning,
            "reasoning_effort_none": supports_none,
        }

    return {
        "profile": "openai-compatible",
        "token_field": "max_tokens",
        "temperature": not reasoning,
        "reasoning_effort": False,
        "reasoning_effort_none": supports_none,
    }


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


def build_chat_options(
    provider,
    model,
    max_tokens,
    temperature=None,
    reasoning_effort=None,
):
    """Build model-compatible optional Chat Completions parameters."""
    capabilities = model_capabilities(provider, model)
    kwargs = {
        capabilities["token_field"]: max_tokens,
    }
    effort = str(reasoning_effort or "").strip().lower()
    supports_temperature = (
        capabilities["temperature"]
        or (
            effort == "none"
            and capabilities["reasoning_effort_none"]
        )
    )
    if temperature is not None and supports_temperature:
        kwargs["temperature"] = temperature

    if (
        capabilities["reasoning_effort"]
        and effort
        and effort not in ("off", "disabled")
        and (
            effort != "none"
            or capabilities["reasoning_effort_none"]
        )
    ):
        kwargs["reasoning_effort"] = effort

    _apply_cached_overrides(kwargs, provider, model)
    return kwargs


def describe_model_compatibility(
    provider, model, reasoning_effort=None
):
    """Return a concise description suitable for startup logs."""
    capabilities = model_capabilities(provider, model)
    options = build_chat_options(
        provider,
        model,
        1,
        temperature=0.5,
        reasoning_effort=reasoning_effort,
    )
    temperature = (
        "custom" if "temperature" in options else "provider-default"
    )
    if str(provider).strip().lower() == "openai":
        effort = options.get("reasoning_effort", "omitted")
    else:
        effort = "provider-specific"
    token_field = (
        "max_completion_tokens"
        if "max_completion_tokens" in options
        else "max_tokens"
    )
    return (
        f"profile={capabilities['profile']}, "
        f"token_limit={token_field}, temperature={temperature}, "
        f"reasoning_effort={effort}"
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
    reasoning_token_multiplier,
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
        rejected_effort = str(
            kwargs.pop("reasoning_effort", "")
        ).strip().lower()
        changed_fields.add("reasoning_effort")
        _remember_override(
            provider, model, "omit_reasoning_effort", True
        )
        if rejected_effort == "none":
            if "temperature" in kwargs:
                kwargs.pop("temperature", None)
                changed_fields.add("temperature")
            _remember_override(
                provider, model, "omit_temperature", True
            )
            token_field = (
                "max_completion_tokens"
                if "max_completion_tokens" in kwargs
                else "max_tokens" if "max_tokens" in kwargs
                else None
            )
            if token_field:
                kwargs[token_field] = int(
                    kwargs[token_field]
                    * reasoning_token_multiplier
                )
            return (
                "omitted unsupported reasoning_effort and expanded "
                "the default-reasoning budget"
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
    reasoning_token_multiplier=1,
):
    """Call Chat Completions and learn explicit compatibility fixes.

    Only invalid-parameter failures are retried. Authentication,
    availability, rate-limit, timeout, and content errors propagate
    unchanged to the normal provider error handling.
    """
    active_logger = request_logger or logger
    kwargs = dict(request_kwargs)
    _apply_cached_overrides(kwargs, provider, model)
    try:
        reasoning_token_multiplier = float(
            reasoning_token_multiplier
        )
    except (TypeError, ValueError):
        reasoning_token_multiplier = 1.0
    reasoning_token_multiplier = max(
        1.0, min(reasoning_token_multiplier, 8.0)
    )
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
                reasoning_token_multiplier,
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


def create_anthropic_message(
    operation,
    request_kwargs,
    model,
    request_logger=None,
):
    """Call Anthropic Messages and learn rejected optional parameters.

    The Anthropic path sends temperature and thinking through
    ``extra_body``. Some models reject one of them outright, so drop
    the rejected field, remember the override for this model, and
    retry. Every other error propagates unchanged.
    """
    active_logger = request_logger or logger
    kwargs = dict(request_kwargs)
    extra = dict(kwargs.get("extra_body") or {})
    overrides = _cached_overrides("anthropic", model)
    for field in _ANTHROPIC_OPTIONAL_FIELDS:
        if overrides.get(f"omit_{field}"):
            extra.pop(field, None)
    kwargs["extra_body"] = extra

    changed_fields = set()
    while True:
        try:
            return operation(**kwargs)
        except Exception as error:
            field = next((
                name for name in _ANTHROPIC_OPTIONAL_FIELDS
                if name in extra and name not in changed_fields
                and _is_parameter_rejection(error, name)
            ), None)
            if field is None:
                raise
        extra.pop(field, None)
        changed_fields.add(field)
        _remember_override("anthropic", model, f"omit_{field}", True)
        active_logger.warning(
            "Adjusted request parameters for anthropic/%s after provider "
            "rejection: omitted unsupported %s",
            model,
            field,
        )


def reset_compatibility_cache():
    """Clear learned model overrides (used by focused tests)."""
    with _MODEL_OVERRIDES_LOCK:
        _MODEL_OVERRIDES.clear()


def with_response_schema(request_kwargs, provider, name, schema):
    """Attach native schema parameters without changing existing options."""
    kwargs = dict(request_kwargs)
    if provider == 'anthropic':
        output = deepcopy(kwargs.get('output_config', {}))
        output['format'] = {'type': 'json_schema', 'schema': deepcopy(schema)}
        kwargs['output_config'] = output
    elif provider in ('openai', 'google', 'openrouter', 'ollama'):
        kwargs['response_format'] = {
            'type': 'json_schema',
            'json_schema': {'name': name, 'strict': True,
                            'schema': deepcopy(schema)},
        }
        if provider == 'openrouter':
            extra = deepcopy(kwargs.get('extra_body', {}))
            routing = extra.setdefault('provider', {})
            routing['require_parameters'] = True
            kwargs['extra_body'] = extra
    else:
        raise ValueError('Unknown structured-output provider')
    return kwargs


def structured_rejection_category(error, provider):
    """Classify diagnostics only; never learn a schema-removal retry."""
    if _error_status(error) not in (400, 422):
        return None
    body = _error_body(error)
    parameter = _normalize_parameter(body.get('param'))
    code = _normalize_parameter(body.get('code'))
    message = str(body.get('message', '')).lower()
    # An invalid nested schema is not evidence that a model lacks support.
    if ('schema' in parameter or 'schema' in code or 'schema' in message):
        if 'invalid' in code or 'invalid schema' in message:
            return 'schema_rejected'
    field = 'output_config' if provider == 'anthropic' else 'response_format'
    rejected = _is_parameter_rejection(error, field)
    if provider == 'anthropic' and field in message:
        rejected = True
    unsupported = code in ('unsupported_parameter', 'unknown_parameter') or any(
        marker in message for marker in ('not supported', 'unsupported',
                                         'not support', 'unknown parameter')
    )
    if rejected and unsupported:
        return 'format_unsupported'
    return 'request_rejected'
