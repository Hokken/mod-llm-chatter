"""LLM call-layer helpers extracted from chatter_shared (N14)."""

import logging
import threading
import time
from typing import Any, Optional

from chatter_constants import (
    DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_PROVIDER,
)
from llm_compat import (
    build_chat_options,
    create_chat_completion,
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


def _deepseek_reasoning_effort(config):
    """Return the configured DeepSeek reasoning effort.

    DeepSeek enables thinking by default, which is slow and
    expensive for short chatter, so an empty setting is read
    as the explicit "none" rather than the provider default.
    """
    effort = str(config.get(
        'LLMChatter.DeepSeek.ReasoningEffort', 'none'
    )).strip().lower()
    return effort or 'none'


def _deepseek_reasoning_enabled(config):
    """Return whether DeepSeek thinking mode is requested."""
    return _deepseek_reasoning_effort(config) != 'none'


def _apply_deepseek_options(kwargs, config):
    """Attach DeepSeek thinking-mode request options.

    ``thinking`` is stated explicitly in both directions
    because the API enables it by default.
    """
    if _deepseek_reasoning_enabled(config):
        kwargs['reasoning_effort'] = _deepseek_reasoning_effort(
            config
        )
        kwargs['extra_body'] = {'thinking': {'type': 'enabled'}}
        # DeepSeek ignores temperature in thinking mode.
        kwargs.pop('temperature', None)
        return
    kwargs['reasoning_effort'] = 'none'
    kwargs['extra_body'] = {'thinking': {'type': 'disabled'}}


def compatible_reasoning_effort(provider, config):
    """Return the effort that can affect parameter compatibility."""
    if provider == 'deepseek':
        return _deepseek_reasoning_effort(config)
    return None


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


def _effective_max_tokens(
    provider, model, config, max_tokens
):
    """Adjust provider-specific output budget.

    DeepSeek thinking tokens share the output budget, so the
    configured multiplier applies only while thinking is on.
    """
    if not (
        provider == 'deepseek'
        and _deepseek_reasoning_enabled(config)
    ):
        return max_tokens

    try:
        multiplier = float(config.get(
            'LLMChatter.DeepSeek.MaxTokensMultiplier', 1
        ))
    except (TypeError, ValueError):
        multiplier = 1.0
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
        _effective_max_tokens(
            provider, model, config, max_tokens
        ),
        temperature=temperature,
    ))
    if provider == 'deepseek':
        _apply_deepseek_options(kwargs, config)
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
    """Resolve friendly model aliases to provider model IDs.

    Ollama tags are returned untouched; only the DeepSeek
    aliases are rewritten.
    """
    normalized = (model_name or '').strip()
    aliases = {
        'deepseek': DEFAULT_DEEPSEEK_MODEL,
        'deepseek-flash': DEFAULT_DEEPSEEK_MODEL,
        'deepseek-v4-flash': DEFAULT_DEEPSEEK_MODEL,
        'deepseek-pro': 'deepseek-v4-pro',
        'deepseek-v4-pro': 'deepseek-v4-pro',
    }
    return aliases.get(normalized.lower(), normalized)


_main_client = None
_main_client_provider = None
_main_client_lock = threading.Lock()


def resolve_provider(config):
    """Return the configured provider name, normalised."""
    provider = str(config.get(
        'LLMChatter.Provider', DEFAULT_PROVIDER
    )).strip().lower()
    return provider or DEFAULT_PROVIDER


def build_llm_client(config, provider=None):
    """Build an OpenAI-compatible client for a provider.

    Both supported providers speak the Chat Completions
    API, so this is the single client factory for the
    bridge, the feature modules, and the health check.
    Returns None when a cloud provider has no API key.
    """
    import openai

    if provider is None:
        provider = resolve_provider(config)

    if provider == 'ollama':
        # Ollama needs no key; its compatible API is at /v1.
        base_url = config.get(
            'LLMChatter.Ollama.BaseUrl',
            DEFAULT_OLLAMA_BASE_URL,
        )
        return openai.OpenAI(
            base_url=f"{str(base_url).rstrip('/')}/v1",
            api_key='ollama',
        )

    if provider == 'deepseek':
        api_key = config.get(
            'LLMChatter.DeepSeek.ApiKey', ''
        )
        if not api_key:
            return None
        return openai.OpenAI(
            api_key=api_key,
            base_url=config.get(
                'LLMChatter.DeepSeek.BaseUrl',
                DEEPSEEK_BASE_URL,
            ),
        )

    logger.error(
        "Unknown LLMChatter.Provider %r; expected "
        "deepseek or ollama.",
        provider,
    )
    return None


def get_llm_client(config):
    """Get or create the main LLM client.

    Thread-safe, lazily initialised, cached by
    provider. Returns the client object suitable
    for passing to call_llm().
    """
    global _main_client, _main_client_provider

    provider = resolve_provider(config)

    with _main_client_lock:
        if (
            _main_client is not None
            and _main_client_provider == provider
        ):
            return _main_client

        client = build_llm_client(config, provider)
        if client is None:
            return None

        _main_client = client
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

    Supports DeepSeek and Ollama, both through the
    OpenAI-compatible Chat Completions API.
    """
    provider = resolve_provider(config)
    model = resolve_model(config.get(
        'LLMChatter.Model', DEFAULT_DEEPSEEK_MODEL
    ))
    if max_tokens_override is not None:
        max_tokens = max_tokens_override
    else:
        max_tokens = int(
            config.get('LLMChatter.MaxTokens', 350)
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
        kwargs = build_compatible_chat_request(
            provider,
            model,
            _build_chat_messages(
                sys_msg, sent_user_msg
            ),
            config,
            max_tokens,
            temperature,
        )
        response = create_chat_completion(
            client.chat.completions.create,
            kwargs,
            provider,
            model,
            logger,
        )
        result = _extract_chat_content(
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

    qa_provider = str(config.get(
        'LLMChatter.QuickAnalyze.Provider', ''
    )).strip().lower()
    main_provider = resolve_provider(config)

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
        # provider; fall back when it is unusable.
        client = build_llm_client(config, qa_provider)
        if client is None:
            return None, main_provider

        _quick_analyze_client = client
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
    or defaults to DeepSeek Flash for DeepSeek and the
    configured main model for Ollama.

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
    qa_model = str(config.get(
        'LLMChatter.QuickAnalyze.Model', ''
    )).strip()

    if qa_model:
        model = qa_model
    elif provider == 'deepseek' and using_quick_provider:
        model = DEFAULT_DEEPSEEK_MODEL
    else:
        # Main provider, or Ollama: use the configured model.
        model = config.get(
            'LLMChatter.Model', DEFAULT_DEEPSEEK_MODEL
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
        kwargs = build_compatible_chat_request(
            provider,
            model,
            _build_chat_messages(
                sys_msg, sent_user_msg
            ),
            config,
            max_tokens,
            0.1,
        )
        response = create_chat_completion(
            active_client.chat.completions.create,
            kwargs,
            provider,
            model,
            logger,
        )
        result = _extract_chat_content(
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
