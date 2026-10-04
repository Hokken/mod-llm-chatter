"""LLM call-layer helpers extracted from chatter_shared (N14)."""

import logging
import importlib.util
import re
from collections import OrderedDict
import threading
import time
from typing import Any, Optional

from chatter_constants import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_GOOGLE_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OPENROUTER_MODEL,
    GOOGLE_OPENAI_BASE_URL,
    OPENROUTER_BASE_URL,
)
from llm_compat import (
    build_chat_options,
    create_chat_completion,
    needs_reasoning_token_multiplier,
    structured_rejection_category,
    with_response_schema,
)
from chatter_structured import (
    StructuredDependencyError, StructuredOutputError, schema_for,
    structured_output_enabled,
    validate_and_normalize,
)

logger = logging.getLogger(__name__)

_structured_failures = OrderedDict()
_structured_targets = OrderedDict()
_structured_failure_lock = threading.Lock()


def reset_structured_diagnostics():
    """Reset logging-only state on process/config initialization."""
    with _structured_failure_lock:
        _structured_failures.clear()
        _structured_targets.clear()


def log_structured_target(role, provider, model, enabled, active_logger=None):
    """Report resolved targets once; this is not a capability probe/cache."""
    key = (role, provider, model, enabled)
    with _structured_failure_lock:
        if key in _structured_targets:
            return
        _structured_targets[key] = True
        if len(_structured_targets) > 256:
            _structured_targets.popitem(last=False)
    (active_logger or logger).info(
        'Structured output requested=%s role=%s provider=%s model=%s; '
        'endpoint support is not verified by startup',
        'on' if enabled else 'off', role, provider, model,
    )


def check_structured_dependencies(enabled, active_logger=None):
    """Fail startup clearly before generation when the validator is missing."""
    if enabled and importlib.util.find_spec('jsonschema') is None:
        (active_logger or logger).error(
            'Structured output requires jsonschema; install '
            'tools/requirements.txt in this Python environment before startup',
        )
        return False
    return True


def _provider_error_message(error):
    """Keep normal diagnostics short; never serialize the SDK request/body."""
    body = getattr(error, 'body', None)
    if isinstance(body, dict):
        body = body.get('error', body)
    message = body.get('message', '') if isinstance(body, dict) else ''
    message = re.sub(r'(?i)\b(?:sk-|bearer\s+)\S+', '[redacted]', str(message))
    message = re.sub(
        r'(?i)((?:api[_-]?key|authorization)\s*[:=]\s*)\S+',
        r'\1[redacted]', message,
    )
    return ' '.join(message.split())[:240] or 'No provider message available'


def log_structured_failure(provider, model, schema_id, category,
                           active_logger=None, *, diagnostics=None,
                           label='', error=None):
    active_logger = active_logger or logger
    diagnostics = diagnostics or {}
    key = (provider, model, schema_id, category,
           label if category == 'contract_error' else '')
    now = time.monotonic()
    with _structured_failure_lock:
        previous = _structured_failures.get(key)
        count = previous[1] + 1 if previous else 0
        warn = previous is None or now - previous[0] >= 300
        _structured_failures[key] = (now, 0) if warn else (previous[0], count)
        _structured_failures.move_to_end(key)
        if len(_structured_failures) > 256:
            _structured_failures.popitem(last=False)
    if category == 'format_unsupported':
        detail = ('Endpoint does not support this format; disable '
                  'LLMChatter.StructuredOutput.Enable for unsupported targets')
    elif category == 'incomplete_or_refused':
        detail = ('finish_reason=%s token_budget=%s; check output budget or '
                  'provider refusal' % (diagnostics.get('finish_reason'),
                                       diagnostics.get('token_budget')))
    elif category == 'contract_error':
        detail = 'label=%s; missing or conflicting caller contract' % label
    elif category == 'invalid_response':
        detail = 'Response failed local JSON/schema validation; output discarded'
    elif category == 'schema_rejected':
        detail = 'Endpoint rejected the schema; check schema compatibility'
    elif category == 'dependency_missing':
        detail = ('Local schema validator unavailable; install '
                  'tools/requirements.txt in this Python environment')
    else:
        detail = ('Provider rejected request: ' + _provider_error_message(error)
                  if warn else 'Provider rejected request')
    active_logger.log(
        logging.WARNING if warn else logging.DEBUG,
        'Structured output rejected: provider=%s model=%s schema=%s reason=%s; '
        '%s (%s repeats since last warning)',
        provider, model, schema_id, category, detail, count,
    )


def _field(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(
        value, name, default,
    )


def read_structured_response(response, provider, contract, diagnostics):
    """Reject incomplete/refused outputs before the tolerant legacy parsers."""
    usage = _field(response, 'usage')
    diagnostics['usage'] = {
        key: _field(usage, key) for key in (
            'input_tokens', 'output_tokens', 'prompt_tokens',
            'completion_tokens', 'total_tokens',
        ) if _field(usage, key) is not None
    }
    refused = False
    malformed = False
    if provider == 'anthropic':
        finish = _field(response, 'stop_reason')
        blocks = _field(response, 'content', []) or []
        parts = []
        for block in blocks:
            kind = _field(block, 'type')
            if kind == 'text' and isinstance(_field(block, 'text'), str):
                parts.append(_field(block, 'text'))
            elif kind not in ('thinking', 'redacted_thinking'):
                refused = True
        raw = ''.join(parts)
        complete = str(finish).lower() == 'end_turn'
    else:
        choices = _field(response, 'choices', []) or []
        choice = choices[0] if choices else None
        message = _field(choice, 'message')
        finish = _field(choice, 'finish_reason')
        refused = bool(_field(message, 'refusal') or
                       _field(message, 'tool_calls') or
                       _field(message, 'function_call'))
        content = _field(message, 'content')
        if isinstance(content, list):
            parts = []
            for block in content:
                text = _field(block, 'text')
                if _field(block, 'type') == 'text' and isinstance(text, str):
                    parts.append(text)
                else:
                    malformed = True
            raw = ''.join(parts)
        else:
            raw = content if isinstance(content, str) else ''
        complete = bool(choices) and str(finish).lower() == 'stop'
    diagnostics.update(finish_reason=finish, _raw_response=raw)
    if not complete or refused or malformed or not raw.strip():
        diagnostics['validation'] = 'incomplete_or_refused'
        raise StructuredOutputError('Incomplete or refused response')
    try:
        normalized = validate_and_normalize(raw, contract)
    except StructuredOutputError:
        diagnostics['validation'] = 'invalid_response'
        raise
    diagnostics.update(validation='passed', normalization='passed')
    return normalized


def structured_completion(operation, kwargs, provider, model, contract,
                          diagnostics, active_logger=None,
                          reasoning_token_multiplier=1):
    """Shared text/vision transport, preserving existing bounded retries."""
    schema_id, schema = schema_for(contract)
    diagnostics['schema_id'] = schema_id
    request = with_response_schema(kwargs, provider, schema_id, schema)

    def observed_operation(**attempt):
        for field in ('max_tokens', 'max_completion_tokens'):
            if field in attempt:
                diagnostics['token_field'] = field
                diagnostics['token_budget'] = attempt[field]
        return operation(**attempt)

    if provider == 'anthropic':
        response = observed_operation(**request)
    else:
        response = create_chat_completion(
            observed_operation, request, provider, model,
            active_logger or logger,
            reasoning_token_multiplier=reasoning_token_multiplier,
        )
    return read_structured_response(response, provider, contract, diagnostics)


def _split_prompt(prompt):
    """Extract system/user parts from a prompt.

    Returns (system_msg, user_msg). system_msg is
    None for plain str prompts.
    """
    from chatter_shared import PromptParts
    if isinstance(prompt, PromptParts) and prompt.system_prompt:
        return prompt.system_prompt, prompt.user_prompt
    return None, str(prompt)


def _build_chat_messages(sys_msg, user_content):
    """Build OpenAI-style messages list with optional
    system message."""
    messages = []
    if sys_msg:
        messages.append({
            "role": "system",
            "content": sys_msg,
        })
    messages.append({
        "role": "user",
        "content": user_content,
    })
    return messages


def _build_anthropic_request_kwargs(
    model, max_tokens, temperature, sys_msg, user_msg
):
    """Build Anthropic SDK v1-compatible request arguments."""
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{
            "role": "user",
            "content": user_msg,
        }],
        "extra_body": {
            "temperature": temperature,
        },
    }
    if sys_msg:
        kwargs["system"] = sys_msg
    return kwargs


def _openrouter_headers(config):
    """Build optional OpenRouter app-attribution headers."""
    headers = {}
    referer = str(config.get(
        'LLMChatter.OpenRouter.HttpReferer', ''
    )).strip()
    title = str(config.get(
        'LLMChatter.OpenRouter.Title', ''
    )).strip()
    if referer:
        headers['HTTP-Referer'] = referer
    if title:
        headers['X-OpenRouter-Title'] = title
    return headers or None


def _openrouter_reasoning_effort(config):
    """Return the configured OpenRouter reasoning effort."""
    effort = str(config.get(
        'LLMChatter.OpenRouter.ReasoningEffort', ''
    )).strip()
    return effort or None


def _openrouter_reasoning_enabled(config):
    """Return whether OpenRouter reasoning needs extra output budget."""
    effort = _openrouter_reasoning_effort(config)
    return bool(effort) and effort.lower() != 'none'


def compatible_reasoning_effort(provider, config):
    """Return the effort that can affect parameter compatibility."""
    if provider == 'openai':
        return config.get(
            'LLMChatter.OpenAI.ReasoningEffort', ''
        )
    if provider == 'openrouter':
        return _openrouter_reasoning_effort(config)
    return None


def compatible_reasoning_token_multiplier(provider, config):
    """Return the retry budget multiplier for direct OpenAI."""
    if provider != 'openai':
        return 1.0
    try:
        multiplier = float(config.get(
            'LLMChatter.OpenAI.MaxTokensMultiplier', 4
        ))
    except (TypeError, ValueError):
        multiplier = 4.0
    return max(1.0, min(multiplier, 8.0))


def _apply_openrouter_options(kwargs, config):
    """Attach opt-in OpenRouter reasoning request options."""
    effort = _openrouter_reasoning_effort(config)
    if not effort:
        return

    # Unlike Google, "none" is sent explicitly so hybrid models are
    # forced into their non-reasoning mode instead of using defaults.
    # Normalize only the "none" sentinel; other values keep their
    # configured case since supported effort spellings vary by model.
    if effort.lower() == 'none':
        effort = 'none'
    reasoning = {'effort': effort}
    if str(config.get(
        'LLMChatter.OpenRouter.ReasoningExclude', '0'
    )).strip() == '1':
        reasoning['exclude'] = True
    kwargs['extra_body'] = {'reasoning': reasoning}


def _ollama_user_msg(user_msg, config):
    """Apply Ollama-specific transforms to user msg
    (e.g. /no_think prefix)."""
    disable_thinking = (
        config.get(
            'LLMChatter.Ollama.DisableThinking',
            '1',
        ) == '1'
    )
    if disable_thinking:
        return "/no_think " + user_msg
    return user_msg


def _google_reasoning_effort(config):
    """Return Gemini OpenAI-compatible reasoning effort."""
    if _google_thinking_config(config):
        return None
    effort = str(config.get(
        'LLMChatter.Google.ReasoningEffort', 'minimal'
    )).strip().lower()
    if not effort or effort in ('0', 'none', 'off', 'disabled'):
        return None
    return effort


def _google_thinking_config(config):
    """Return Gemini thinking_config for OpenAI compatibility."""
    raw_budget = str(config.get(
        'LLMChatter.Google.ThinkingBudget', ''
    )).strip()
    if not raw_budget:
        return None
    try:
        return {'thinking_budget': int(raw_budget)}
    except (TypeError, ValueError):
        logger.warning(
            "Invalid LLMChatter.Google.ThinkingBudget=%r",
            raw_budget,
        )
        return None


def _apply_google_options(kwargs, config):
    """Attach Gemini-specific OpenAI compatibility options."""
    thinking_config = _google_thinking_config(config)
    if thinking_config:
        kwargs['extra_body'] = {
            'extra_body': {
                'google': {
                    'thinking_config': thinking_config,
                },
            },
        }
        return

    effort = _google_reasoning_effort(config)
    if effort:
        kwargs['reasoning_effort'] = effort


def _effective_max_tokens(
    provider, model, config, max_tokens
):
    """Adjust provider-specific output budget."""
    if provider == 'google':
        config_key = 'LLMChatter.Google.MaxTokensMultiplier'
        default_multiplier = 2
    elif (
        provider == 'openai'
        and needs_reasoning_token_multiplier(
            provider,
            model,
            compatible_reasoning_effort(provider, config),
        )
    ):
        return int(
            max_tokens
            * compatible_reasoning_token_multiplier(provider, config)
        )
    elif (
        provider == 'openrouter'
        and _openrouter_reasoning_enabled(config)
    ):
        config_key = (
            'LLMChatter.OpenRouter.MaxTokensMultiplier'
        )
        default_multiplier = 1
    else:
        return max_tokens

    try:
        multiplier = float(config.get(
            config_key, default_multiplier
        ))
    except (TypeError, ValueError):
        multiplier = float(default_multiplier)
    multiplier = max(1.0, min(multiplier, 8.0))
    return int(max_tokens * multiplier)


def build_compatible_chat_request(
    provider,
    model,
    messages,
    config,
    max_tokens,
    temperature=None,
):
    """Build the production request shape for a compatible provider."""
    kwargs = {
        'model': model,
        'messages': messages,
    }
    kwargs.update(build_chat_options(
        provider,
        model,
        _effective_max_tokens(
            provider, model, config, max_tokens
        ),
        temperature=temperature,
        reasoning_effort=compatible_reasoning_effort(
            provider, config
        ),
    ))
    if provider == 'google':
        _apply_google_options(kwargs, config)
    elif provider == 'openrouter':
        _apply_openrouter_options(kwargs, config)
    elif (
        provider == 'ollama'
        and str(config.get(
            'LLMChatter.Ollama.DisableThinking', '1'
        )).strip() == '1'
    ):
        kwargs['reasoning_effort'] = 'none'
    return kwargs


def _extract_chat_content(response, label=''):
    """Extract text from an OpenAI-compatible chat response."""
    choice = response.choices[0]
    message = choice.message
    content = getattr(message, 'content', None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                text = part.get('text')
            else:
                text = getattr(part, 'text', None)
            if text:
                parts.append(text)
        if parts:
            return ''.join(parts).strip()

    finish_reason = getattr(choice, 'finish_reason', None)
    tool_calls = getattr(message, 'tool_calls', None)
    logger.warning(
        "LLM returned no text content (%s): "
        "finish_reason=%s tool_calls=%s",
        label, finish_reason, bool(tool_calls),
    )
    return None


def resolve_model(model_name: str) -> str:
    """Resolve friendly model aliases to provider model IDs."""
    normalized = (model_name or '').strip()
    aliases = {
        'haiku': DEFAULT_ANTHROPIC_MODEL,
        'gpt4o-mini': DEFAULT_OPENAI_MODEL,
        'gpt-4o-mini': DEFAULT_OPENAI_MODEL,
        'openrouter-auto': 'openrouter/auto',
        'google-2.5-flash': 'gemini-2.5-flash',
        'google2.5-flash': 'gemini-2.5-flash',
        'gemini-2.5-flash': 'gemini-2.5-flash',
        'google-3.1-flash-lite': 'gemini-3.1-flash-lite',
        'google3.1-flash-lite': 'gemini-3.1-flash-lite',
        'gemini-3.1-flash-lite': 'gemini-3.1-flash-lite',
        'google-3-flash': 'gemini-3-flash-preview',
        'google3-flash': 'gemini-3-flash-preview',
        'gemini-3-flash': 'gemini-3-flash-preview',
        'gemini-3-flash-preview': 'gemini-3-flash-preview',
    }
    return aliases.get(normalized.lower(), normalized)


_main_client = None
_main_client_provider = None
_main_client_lock = threading.Lock()


def get_llm_client(config):
    """Get or create the main LLM client.

    Thread-safe, lazily initialised, cached by
    provider. Returns the client object suitable
    for passing to call_llm().
    """
    global _main_client, _main_client_provider

    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()

    with _main_client_lock:
        if (
            _main_client is not None
            and _main_client_provider == provider
        ):
            return _main_client

        if provider == 'ollama':
            import openai
            base_url = config.get(
                'LLMChatter.Ollama.BaseUrl',
                'http://localhost:11434',
            )
            _main_client = openai.OpenAI(
                base_url=(
                    f"{base_url.rstrip('/')}/v1"
                ),
                api_key="ollama",
            )
        elif provider == 'openai':
            import openai
            _main_client = openai.OpenAI(
                api_key=config.get(
                    'LLMChatter.OpenAI.ApiKey', ''
                ),
            )
        elif provider == 'google':
            import openai
            _main_client = openai.OpenAI(
                api_key=config.get(
                    'LLMChatter.Google.ApiKey', ''
                ),
                base_url=config.get(
                    'LLMChatter.Google.BaseUrl',
                    GOOGLE_OPENAI_BASE_URL,
                ),
            )
        elif provider == 'openrouter':
            import openai
            kwargs = {
                'api_key': config.get(
                    'LLMChatter.OpenRouter.ApiKey', ''
                ),
                'base_url': config.get(
                    'LLMChatter.OpenRouter.BaseUrl',
                    OPENROUTER_BASE_URL,
                ),
            }
            headers = _openrouter_headers(config)
            if headers:
                kwargs['default_headers'] = headers
            _main_client = openai.OpenAI(**kwargs)
        else:
            import anthropic
            _main_client = anthropic.Anthropic(
                api_key=config.get(
                    'LLMChatter.Anthropic.ApiKey',
                    '',
                ),
            )

        _main_client_provider = provider
        return _main_client


def _call_target(client, prompt, config, provider, model, max_tokens,
                 temperature, label, metadata, response_contract, free_text):
    """One request boundary after main/auxiliary target resolution."""
    t0 = time.monotonic()
    result = None
    enabled = structured_output_enabled(config)
    contract = response_contract or getattr(prompt, 'response_contract', None)
    role = contract.kind if contract and contract.kind in (
        'analysis', 'memory',
    ) else 'main'
    log_structured_target(role, provider, model, enabled)
    diagnostics = dict(requested=enabled,
                       applied='schema' if enabled and contract else
                       'text' if enabled else 'off')
    log_metadata = dict(metadata or {})
    sys_msg, user_msg = _split_prompt(prompt)
    sent_user_msg = user_msg
    try:
        if enabled:
            annotated = getattr(prompt, 'response_contract', None)
            if (getattr(prompt, 'contract_conflict', False)
                    or (not contract and not free_text)
                    or (contract and free_text)
                    or (response_contract is not None and annotated is not None
                        and response_contract != annotated)):
                diagnostics.update(applied='error', validation='contract_error')
                raise StructuredOutputError('Conflicting prompt contract')
            if contract and getattr(prompt, 'structured_system_prompt', None):
                sys_msg = prompt.structured_system_prompt
        if provider == 'ollama':
            sent_user_msg = _ollama_user_msg(user_msg, config)
        compatible = provider in ('openai', 'google', 'openrouter', 'ollama')
        if compatible:
            kwargs = build_compatible_chat_request(
                provider, model, _build_chat_messages(sys_msg, sent_user_msg),
                config, max_tokens, temperature,
            )
            operation = client.chat.completions.create
        else:
            kwargs = _build_anthropic_request_kwargs(
                model, max_tokens, temperature, sys_msg, user_msg,
            )
            operation = client.messages.create
        multiplier = compatible_reasoning_token_multiplier(provider, config)
        if enabled and contract:
            result = structured_completion(
                operation, kwargs, provider, model, contract, diagnostics,
                reasoning_token_multiplier=multiplier,
            )
        elif compatible:
            response = create_chat_completion(
                operation, kwargs, provider, model, logger,
                reasoning_token_multiplier=multiplier,
            )
            result = _extract_chat_content(response, label)
        else:
            response = operation(**kwargs)
            result = response.content[0].text.strip()
    except Exception as exc:
        category = None
        if enabled:
            category = ('dependency_missing'
                        if isinstance(exc, StructuredDependencyError) else
                        diagnostics.get('validation', 'invalid_response')
                        if isinstance(exc, StructuredOutputError) else
                        structured_rejection_category(exc, provider))
        if category:
            diagnostics['error_category'] = category
            log_structured_failure(
                provider, model, diagnostics.get('schema_id'), category,
                diagnostics=diagnostics, label=label, error=exc,
            )
        else:
            logger.error('LLM call failed (%s): %s', label, exc)
        result = None
    finally:
        raw_response = diagnostics.pop('_raw_response', result)
        log_metadata['structured_output'] = diagnostics
        try:
            from chatter_request_logger import log_request
            log_request(
                label, sent_user_msg, raw_response, model, provider,
                int((time.monotonic() - t0) * 1000),
                metadata=log_metadata, system_prompt=sys_msg,
            )
        except Exception:
            pass
    return result


def call_llm(
    client: Any,
    prompt: str,
    config: dict,
    max_tokens_override: int = None,
    context: str = '',
    *,
    label: str = '',
    metadata: dict = None,
    response_contract=None,
    free_text: bool = False,
) -> str:
    """Call LLM API.

    Supports Anthropic, OpenAI, Google, OpenRouter, and Ollama.
    """
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()
    default_model = DEFAULT_ANTHROPIC_MODEL
    if provider == 'openai':
        default_model = DEFAULT_OPENAI_MODEL
    elif provider == 'google':
        default_model = DEFAULT_GOOGLE_MODEL
    elif provider == 'openrouter':
        default_model = DEFAULT_OPENROUTER_MODEL
    model = config.get(
        'LLMChatter.Model', default_model
    )
    model = resolve_model(model)
    if max_tokens_override is not None:
        max_tokens = max_tokens_override
    else:
        max_tokens = int(
            config.get('LLMChatter.MaxTokens', 350)
        )
    temperature = float(
        config.get('LLMChatter.Temperature', 0.85)
    )

    return _call_target(
        client, prompt, config, provider, model, max_tokens,
        temperature, label, metadata, response_contract, free_text,
    )


# Cached client for quick analyze when provider
# differs from main provider
_quick_analyze_client = None
_quick_analyze_provider = None
_quick_analyze_lock = threading.Lock()


def _get_quick_analyze_client(config):
    """Get or create the LLM client for quick
    analyze calls. Returns (client, provider).

    If QuickAnalyze.Provider matches the main
    provider (or is empty), returns None so the
    caller uses the main client.

    Thread-safe: lazy init protected by lock.
    """
    global _quick_analyze_client
    global _quick_analyze_provider

    qa_provider = config.get(
        'LLMChatter.QuickAnalyze.Provider', ''
    ).strip().lower()
    main_provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()

    # Empty = use main provider
    if not qa_provider or qa_provider == main_provider:
        return None, main_provider

    with _quick_analyze_lock:
        # Return cached client if already created
        if (
            _quick_analyze_client is not None
            and _quick_analyze_provider == qa_provider
        ):
            return _quick_analyze_client, qa_provider

        # Create new client for the quick analyze
        # provider
        if qa_provider == 'ollama':
            import openai
            base_url = config.get(
                'LLMChatter.Ollama.BaseUrl',
                'http://localhost:11434'
            )
            ollama_api_url = (
                f"{base_url.rstrip('/')}/v1"
            )
            _quick_analyze_client = openai.OpenAI(
                base_url=ollama_api_url,
                api_key="ollama"
            )
        elif qa_provider == 'openai':
            import openai
            api_key = config.get(
                'LLMChatter.OpenAI.ApiKey', ''
            )
            if not api_key:
                return None, main_provider
            _quick_analyze_client = openai.OpenAI(
                api_key=api_key
            )
        elif qa_provider == 'google':
            import openai
            api_key = config.get(
                'LLMChatter.Google.ApiKey', ''
            )
            if not api_key:
                return None, main_provider
            _quick_analyze_client = openai.OpenAI(
                api_key=api_key,
                base_url=config.get(
                    'LLMChatter.Google.BaseUrl',
                    GOOGLE_OPENAI_BASE_URL,
                ),
            )
        elif qa_provider == 'openrouter':
            import openai
            api_key = config.get(
                'LLMChatter.OpenRouter.ApiKey', ''
            )
            if not api_key:
                return None, main_provider
            kwargs = {
                'api_key': api_key,
                'base_url': config.get(
                    'LLMChatter.OpenRouter.BaseUrl',
                    OPENROUTER_BASE_URL,
                ),
            }
            headers = _openrouter_headers(config)
            if headers:
                kwargs['default_headers'] = headers
            _quick_analyze_client = openai.OpenAI(**kwargs)
        elif qa_provider == 'anthropic':
            import anthropic
            api_key = config.get(
                'LLMChatter.Anthropic.ApiKey', ''
            )
            if not api_key:
                return None, main_provider
            _quick_analyze_client = anthropic.Anthropic(
                api_key=api_key
            )
        else:
            return None, main_provider

        _quick_analyze_provider = qa_provider
        return _quick_analyze_client, qa_provider


def quick_llm_analyze(
    client: Any,
    config: dict,
    prompt: str,
    max_tokens: int = 50,
    *,
    label: str = '',
    metadata: dict = None,
    response_contract=None,
    free_text: bool = False,
) -> Optional[str]:
    """Fast LLM call for pre-processing analysis.

    Uses the configured QuickAnalyze provider/model,
    or defaults to the fastest model on the main
    provider (Haiku for Anthropic, gpt-4o-mini for
    OpenAI, Gemini Flash for Google, OpenRouter's
    configured model, main model for Ollama).

    Useful for tasks like:
    - Determining which bot a player is addressing
    - Classifying message intent or sentiment
    - Summarizing context before a full prompt

    Returns raw text response, or None on error.
    """
    # Check for separate quick analyze provider
    qa_client, provider = (
        _get_quick_analyze_client(config)
    )
    if qa_client is not None:
        active_client = qa_client
        using_quick_provider = True
    else:
        active_client = client
        using_quick_provider = False

    # Resolve model
    qa_model = config.get(
        'LLMChatter.QuickAnalyze.Model', ''
    ).strip()

    if qa_model:
        model = qa_model
    elif provider == 'anthropic':
        model = DEFAULT_ANTHROPIC_MODEL
    elif provider == 'openai':
        model = DEFAULT_OPENAI_MODEL
    elif provider == 'google':
        if using_quick_provider:
            model = DEFAULT_GOOGLE_MODEL
        else:
            model = config.get(
                'LLMChatter.Model',
                DEFAULT_GOOGLE_MODEL
            )
    elif provider == 'openrouter':
        if using_quick_provider:
            model = DEFAULT_OPENROUTER_MODEL
        else:
            model = config.get(
                'LLMChatter.Model',
                DEFAULT_OPENROUTER_MODEL
            )
    else:
        # Ollama: use configured model
        model = config.get(
            'LLMChatter.Model',
            DEFAULT_ANTHROPIC_MODEL
        )
    model = resolve_model(model)

    return _call_target(
        active_client, prompt, config, provider, model, max_tokens,
        0.1, label, metadata, response_contract, free_text,
    )
