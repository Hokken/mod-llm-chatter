"""Shared provider-client construction and request options."""

import logging


logger = logging.getLogger(__name__)


def _config_enabled(config, key, default='0'):
    """Return a permissive boolean config value."""
    return str(config.get(key, default)).strip().lower() in (
        '1', 'true', 'yes', 'on',
    )


def create_anthropic_client(anthropic_module, config, api_key=None):
    """Create an Anthropic client, optionally against a compatible endpoint."""
    key = api_key or config.get('LLMChatter.Anthropic.ApiKey', '')
    kwargs = {'api_key': key}
    base_url = config.get('LLMChatter.Anthropic.BaseUrl', '').strip()
    if base_url:
        kwargs['base_url'] = base_url.rstrip('/') + '/'
    return anthropic_module.Anthropic(**kwargs)


def get_openai_compatible_request_mode(config):
    """Return ``chat`` or ``responses`` for compatible endpoints."""
    raw = str(config.get(
        'LLMChatter.OpenAICompatible.RequestMode', 'chat'
    )).strip().lower().replace('-', '_')
    aliases = {
        'chat': 'chat',
        'chat_completion': 'chat',
        'chat_completions': 'chat',
        'responses': 'responses',
        'response': 'responses',
    }
    mode = aliases.get(raw)
    if mode:
        return mode
    logger.warning(
        "Invalid OpenAICompatible.RequestMode=%r; using chat",
        raw,
    )
    return 'chat'


def get_openai_compatible_thinking_style(config):
    """Return the configured non-reasoning request style."""
    raw = str(config.get(
        'LLMChatter.OpenAICompatible.DisableThinkingStyle',
        'thinking',
    )).strip().lower().replace('-', '_')
    aliases = {
        'thinking': 'thinking',
        'thinking_disabled': 'thinking',
        'reasoning': 'reasoning',
        'reasoning_none': 'reasoning',
        'reasoning_effort': 'reasoning_effort',
        'reasoning_effort_none': 'reasoning_effort',
    }
    style = aliases.get(raw)
    if style:
        return style
    logger.warning(
        "Invalid OpenAICompatible.DisableThinkingStyle=%r; "
        "using thinking",
        raw,
    )
    return 'thinking'


def apply_openai_compatible_options(kwargs, config, request_mode='chat'):
    """Attach an explicitly configured non-reasoning control.

    Compatible gateways expose several mutually incompatible wire formats.
    ``thinking`` is used by DeepSeek and OpenCode Zen; ``reasoning`` is used
    by OpenCode Go.  The Responses API accepts ``reasoning`` natively, while
    Chat Completions needs it in ``extra_body``.
    """
    if not _config_enabled(
        config, 'LLMChatter.OpenAICompatible.DisableThinking'
    ):
        return

    style = get_openai_compatible_thinking_style(config)
    if style == 'reasoning' and request_mode == 'responses':
        kwargs['reasoning'] = {'effort': 'none'}
        return
    if style == 'reasoning_effort':
        if request_mode == 'responses':
            kwargs['reasoning'] = {'effort': 'none'}
        else:
            kwargs['reasoning_effort'] = 'none'
        return

    extra_body = kwargs.setdefault('extra_body', {})
    if style == 'reasoning':
        extra_body['reasoning'] = {'effort': 'none'}
    else:
        extra_body['thinking'] = {'type': 'disabled'}


def apply_anthropic_options(kwargs, config):
    """Attach optional native Anthropic request controls."""
    if _config_enabled(
        config, 'LLMChatter.Anthropic.DisableThinking'
    ):
        kwargs['thinking'] = {'type': 'disabled'}
