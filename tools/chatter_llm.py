"""LLM call-layer helpers extracted from chatter_shared (N14)."""

import logging
import threading
import time
from typing import Any, Optional

from chatter_constants import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


def resolve_model(model_name: str) -> str:
    """Pass through model name (no aliasing)."""
    return model_name


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
    """Call LLM API (Anthropic, OpenAI, or Ollama)."""
    provider = config.get(
        'LLMChatter.Provider', 'anthropic'
    ).lower()
    model = config.get(
        'LLMChatter.Model', DEFAULT_ANTHROPIC_MODEL
    )
    if max_tokens_override is not None:
        max_tokens = max_tokens_override
    else:
        max_tokens = int(
            config.get('LLMChatter.MaxTokens', 200)
        )
    temperature = float(
        config.get('LLMChatter.Temperature', 0.85)
    )

    t0 = time.monotonic()
    result = None
    try:
        if provider == 'ollama':
            actual_prompt = prompt
            disable_thinking = (
                config.get(
                    'LLMChatter.Ollama.DisableThinking', '1'
                ) == '1'
            )
            if disable_thinking:
                actual_prompt = "/no_think " + prompt

            context_size = int(
                config.get(
                    'LLMChatter.Ollama.ContextSize', 2048
                )
            )

            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": actual_prompt}
                ],
                extra_body={
                    "options": {"num_ctx": context_size}
                }
            )
            result = (
                response.choices[0]
                .message.content.strip()
            )
        elif provider == 'openai':
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            result = (
                response.choices[0]
                .message.content.strip()
            )
        else:
            # Anthropic (default)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            result = response.content[0].text.strip()
    except Exception:
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
                label, prompt, result,
                model, provider, duration_ms,
                metadata=metadata,
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

    import anthropic
    import openai

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
            api_key = config.get(
                'LLMChatter.OpenAI.ApiKey', ''
            )
            if not api_key:
                return None, main_provider
            _quick_analyze_client = openai.OpenAI(
                api_key=api_key
            )
        elif qa_provider == 'anthropic':
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
) -> Optional[str]:
    """Fast LLM call for pre-processing analysis.

    Uses the configured QuickAnalyze provider/model,
    or defaults to the fastest model on the main
    provider (Haiku for Anthropic, gpt-4o-mini for
    OpenAI, main model for Ollama).

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
    else:
        active_client = client

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
    else:
        # Ollama: use configured model
        model = config.get(
            'LLMChatter.Model',
            DEFAULT_ANTHROPIC_MODEL
        )

    t0 = time.monotonic()
    result = None
    try:
        if provider == 'ollama':
            actual_prompt = prompt
            disable_thinking = (
                config.get(
                    'LLMChatter.Ollama.'
                    'DisableThinking', '1'
                ) == '1'
            )
            if disable_thinking:
                actual_prompt = (
                    "/no_think " + prompt
                )
            context_size = int(config.get(
                'LLMChatter.Ollama.ContextSize',
                2048
            ))
            response = (
                active_client
                .chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": actual_prompt
                    }],
                    extra_body={
                        "options": {
                            "num_ctx": context_size
                        }
                    }
                )
            )
            result = (
                response.choices[0]
                .message.content.strip()
            )
        elif provider == 'openai':
            response = (
                active_client
                .chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )
            result = (
                response.choices[0]
                .message.content.strip()
            )
        else:
            response = (
                active_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
            )
            result = response.content[0].text.strip()
    except Exception:
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
                label, prompt, result,
                model, provider, duration_ms,
                metadata=metadata,
            )
        except Exception:
            pass
    return result
