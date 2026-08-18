"""LLM call-layer helpers extracted from chatter_shared (N14)."""

import logging
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
from chatter_provider import (
    apply_anthropic_options,
    apply_openai_compatible_options,
    create_anthropic_client,
    get_openai_compatible_request_mode,
)

logger = logging.getLogger(__name__)


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


def _effective_max_tokens(provider, config, max_tokens):
    """Adjust provider-specific output budget."""
    if provider != 'google':
        return max_tokens
    try:
        multiplier = float(config.get(
            'LLMChatter.Google.MaxTokensMultiplier', 2
        ))
    except (TypeError, ValueError):
        multiplier = 2.0
    multiplier = max(1.0, min(multiplier, 8.0))
    return int(max_tokens * multiplier)


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


def _extract_anthropic_content(response, label=''):
    """Extract all text blocks from an Anthropic response."""
    parts = []
    content = (
        response.get('content')
        if isinstance(response, dict)
        else getattr(response, 'content', None)
    ) or []
    for block in content:
        if isinstance(block, dict):
            block_type = block.get('type')
            text = block.get('text')
        else:
            block_type = getattr(block, 'type', None)
            text = getattr(block, 'text', None)
        if block_type in (None, 'text') and text:
            parts.append(text)
    if parts:
        return ''.join(parts).strip()
    logger.warning(
        "LLM returned no Anthropic text content (%s): "
        "stop_reason=%s",
        label, getattr(response, 'stop_reason', None),
    )
    return None


def _extract_responses_content(response, label=''):
    """Extract text from an OpenAI Responses-compatible response."""
    if isinstance(response, dict):
        output_text = response.get('output_text')
        output = response.get('output') or []
        status = response.get('status')
        details = response.get('incomplete_details')
    else:
        output_text = getattr(response, 'output_text', None)
        output = getattr(response, 'output', None) or []
        status = getattr(response, 'status', None)
        details = getattr(response, 'incomplete_details', None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts = []
    for item in output:
        if isinstance(item, dict):
            item_type = item.get('type')
            content = item.get('content') or []
        else:
            item_type = getattr(item, 'type', None)
            content = getattr(item, 'content', None) or []
        if item_type != 'message':
            continue
        for block in content:
            if isinstance(block, dict):
                block_type = block.get('type')
                text = block.get('text')
            else:
                block_type = getattr(block, 'type', None)
                text = getattr(block, 'text', None)
            if block_type in ('output_text', 'text') and text:
                parts.append(text)
    if parts:
        return ''.join(parts).strip()

    reason = (
        details.get('reason')
        if isinstance(details, dict)
        else getattr(details, 'reason', None)
    )
    logger.warning(
        "LLM returned no Responses API text content (%s): "
        "status=%s incomplete_reason=%s",
        label, status, reason,
    )
    return None


def _call_openai_compatible(
    client, provider, model, config, max_tokens,
    temperature, sys_msg, user_msg, label='',
):
    """Dispatch one OpenAI-compatible request using its configured API."""
    request_mode = 'chat'
    if provider == 'openrouter':
        request_mode = get_openai_compatible_request_mode(config)

    if request_mode == 'responses':
        kwargs = {
            'model': model,
            'max_output_tokens': max_tokens,
            'input': user_msg,
        }
        if sys_msg:
            kwargs['instructions'] = sys_msg
        apply_openai_compatible_options(
            kwargs, config, request_mode='responses'
        )
        response = client.responses.create(**kwargs)
        return _extract_responses_content(response, label)

    kwargs = {
        'model': model,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'messages': _build_chat_messages(sys_msg, user_msg),
    }
    if provider == 'google':
        _apply_google_options(kwargs, config)
    elif provider == 'openrouter':
        apply_openai_compatible_options(
            kwargs, config, request_mode='chat'
        )
    response = client.chat.completions.create(**kwargs)
    return _extract_chat_content(response, label)


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
            _main_client = create_anthropic_client(anthropic, config)

        _main_client_provider = provider
        return _main_client


def call_llm(
    client: Any,
    prompt: str,
    config: dict,
    max_tokens_override: int = None,
    context: str = '',
    *,
    label: str = '',
    metadata: dict = None,
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
            config.get('LLMChatter.MaxTokens', 200)
        )
    request_max_tokens = _effective_max_tokens(
        provider, config, max_tokens
    )
    temperature = float(
        config.get('LLMChatter.Temperature', 0.85)
    )

    t0 = time.monotonic()
    result = None
    sys_msg, user_msg = _split_prompt(prompt)
    sent_user_msg = user_msg  # tracks actual payload
    try:
        if provider == 'ollama':
            sent_user_msg = _ollama_user_msg(
                user_msg, config
            )
            context_size = int(
                config.get(
                    'LLMChatter.Ollama'
                    '.ContextSize', 2048
                )
            )
            response = client.chat.completions.create(
                model=model,
                max_tokens=request_max_tokens,
                temperature=temperature,
                messages=_build_chat_messages(
                    sys_msg, sent_user_msg
                ),
                extra_body={
                    "options": {
                        "num_ctx": context_size
                    }
                }
            )
            result = _extract_chat_content(
                response, label
            )
        elif provider in ('openai', 'google', 'openrouter'):
            result = _call_openai_compatible(
                client, provider, model, config,
                request_max_tokens, temperature,
                sys_msg, user_msg, label,
            )
        else:
            # Anthropic (default)
            kwargs = {
                "model": model,
                "max_tokens": request_max_tokens,
                "temperature": temperature,
                "messages": [{
                    "role": "user",
                    "content": user_msg,
                }],
            }
            if sys_msg:
                kwargs["system"] = sys_msg
            apply_anthropic_options(kwargs, config)
            response = client.messages.create(
                **kwargs
            )
            result = _extract_anthropic_content(
                response, label
            )
    except Exception as exc:
        logger.error(
            "LLM call failed (%s): %s", label, exc
        )
        result = None
    finally:
        duration_ms = int(
            (time.monotonic() - t0) * 1000
        )
        try:
            from chatter_request_logger import (
                log_request,
            )
            log_request(
                label, sent_user_msg, result,
                model, provider, duration_ms,
                metadata=metadata,
                system_prompt=sys_msg,
            )
        except Exception:
            pass
    return result


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
            _quick_analyze_client = create_anthropic_client(
                anthropic, config, api_key
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

    t0 = time.monotonic()
    result = None
    sys_msg, user_msg = _split_prompt(prompt)
    sent_user_msg = user_msg
    try:
        if provider == 'ollama':
            sent_user_msg = _ollama_user_msg(
                user_msg, config
            )
            context_size = int(config.get(
                'LLMChatter.Ollama.ContextSize',
                2048
            ))
            response = (
                active_client
                .chat.completions.create(
                model=model,
                max_tokens=_effective_max_tokens(
                    provider, config, max_tokens
                ),
                temperature=0.1,
                    messages=_build_chat_messages(
                        sys_msg, sent_user_msg
                    ),
                    extra_body={
                        "options": {
                            "num_ctx": context_size
                        }
                    }
                )
            )
            result = _extract_chat_content(
                response, label
            )
        elif provider in ('openai', 'google', 'openrouter'):
            result = _call_openai_compatible(
                active_client, provider, model, config,
                _effective_max_tokens(
                    provider, config, max_tokens
                ),
                0.1, sys_msg, user_msg, label,
            )
        else:
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": 0.1,
                "messages": [{
                    "role": "user",
                    "content": user_msg,
                }],
            }
            if sys_msg:
                kwargs["system"] = sys_msg
            apply_anthropic_options(kwargs, config)
            response = (
                active_client.messages.create(
                    **kwargs
                )
            )
            result = _extract_anthropic_content(
                response, label
            )
    except Exception as exc:
        logger.error(
            "LLM call failed (%s): %s", label, exc
        )
        result = None
    finally:
        duration_ms = int(
            (time.monotonic() - t0) * 1000
        )
        try:
            from chatter_request_logger import (
                log_request,
            )
            log_request(
                label, sent_user_msg, result,
                model, provider, duration_ms,
                metadata=metadata,
                system_prompt=sys_msg,
            )
        except Exception:
            pass
    return result
