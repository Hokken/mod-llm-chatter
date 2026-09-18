#!/usr/bin/env python3
"""
mod-llm-chatter LATENCY PROBE.

When chatter feels slow, run this to find out where the time
goes.  It sends chatter-sized prompts through the exact request
builder the bridge uses, then reports wall-clock latency and the
token accounting behind it -- including reasoning tokens, which
are the usual cause of a slow cloud provider.

DeepSeek enables thinking by default and the bridge disables it
explicitly.  Nothing in the normal request path checks whether
the provider honoured that, so a model that keeps thinking looks
identical to a model that is simply slow.  This probe tells the
two apart: a non-zero reasoning-token count with the production
variant means the disable flag is being ignored.

  Docker (run inside the bridge container):
    docker exec ac-llm-chatter-bridge python \
        /app/chatter_latency_probe.py \
        --config /config/mod_llm_chatter.conf

  Non-Docker:
    python chatter_latency_probe.py \
        --config <path/to/mod_llm_chatter.conf> --compare

Zero extra dependencies -- stdlib plus the openai package the
bridge already needs.
"""

import argparse
import json
import os
import statistics
import sys
import time

from chatter_constants import (
    DEFAULT_DEEPSEEK_MODEL,
    DEFAULT_PROVIDER,
)

# A prompt pair sized like real ambient chatter: a persona system
# prompt plus a short situational user turn.  Latency scales with
# both input and output length, so a toy "say OK" probe would
# understate what the bridge actually waits for.
_SYSTEM_PROMPT = (
    "You are Grimtusk, a gruff dwarven hunter in World of "
    "Warcraft. You are level 34, currently in the Wetlands with "
    "your party. Speak in first person, in character, in one or "
    "two short sentences. No narration, no asterisks, no quotes."
)

_USER_PROMPT = (
    "Your party just wiped on a patrol of murlocs near the "
    "Menethil docks and is running back from the graveyard. "
    "Your party member Sylvara (a night elf druid) said: "
    "\"That was my fault, I pulled too early.\" "
    "Say something back to her."
)

# Request variants.  'production' is whatever the bridge would
# send for this config; the others isolate the thinking controls.
_VARIANTS = ('production', 'no-thinking-param', 'thinking-enabled')


def _require_openai():
    """Exit with a usable hint when the SDK is missing.

    The bridge installs its dependencies inside its container, so
    the usual cause of this is running the probe from the host
    shell instead of from the bridge.
    """
    try:
        import openai  # noqa: F401
    except ModuleNotFoundError:
        print(
            "ERROR: the 'openai' package is not installed for this "
            "Python.\n\n"
            "The bridge installs it inside its container, so run "
            "the probe there -- the tools directory is already "
            "mounted at /app and the conf at /config:\n\n"
            "  docker exec ac-llm-chatter-bridge python \\\n"
            "      /app/chatter_latency_probe.py \\\n"
            "      --config /config/mod_llm_chatter.conf "
            "--compare\n\n"
            "To run it on the host instead, install the bridge's "
            "dependencies first:\n\n"
            "  pip install -r tools/requirements.txt",
            file=sys.stderr,
        )
        sys.exit(2)


def _load_config(config_path):
    """Load the WoW-style conf, tolerating odd lines."""
    if not os.path.exists(config_path):
        print(
            f"ERROR: config file not found: {config_path}",
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


def _build_variant_kwargs(variant, provider, model, config,
                          max_tokens):
    """Build request kwargs for one variant."""
    from chatter_llm import build_compatible_chat_request

    messages = [
        {'role': 'system', 'content': _SYSTEM_PROMPT},
        {'role': 'user', 'content': _USER_PROMPT},
    ]
    try:
        temperature = float(config.get(
            'LLMChatter.Temperature', 0.85
        ))
    except (TypeError, ValueError):
        temperature = 0.85

    variant_config = dict(config)
    if variant == 'thinking-enabled':
        variant_config['LLMChatter.DeepSeek.ReasoningEffort'] = (
            'medium'
        )
        variant_config['LLMChatter.Ollama.DisableThinking'] = '0'

    kwargs = build_compatible_chat_request(
        provider,
        model,
        messages,
        variant_config,
        max_tokens,
        temperature,
    )

    if variant == 'no-thinking-param':
        # Send nothing about thinking at all, so the provider
        # default applies.  Comparing this against 'production'
        # shows whether the explicit disable buys anything.
        kwargs.pop('reasoning_effort', None)
        kwargs.pop('extra_body', None)

    return kwargs


def _usage_counts(response):
    """Pull completion / reasoning token counts from usage."""
    usage = getattr(response, 'usage', None)
    if usage is None:
        return {}
    counts = {
        'prompt_tokens': getattr(usage, 'prompt_tokens', None),
        'completion_tokens': getattr(
            usage, 'completion_tokens', None
        ),
    }
    details = getattr(
        usage, 'completion_tokens_details', None
    )
    reasoning = None
    if details is not None:
        reasoning = getattr(details, 'reasoning_tokens', None)
        if reasoning is None and isinstance(details, dict):
            reasoning = details.get('reasoning_tokens')
    if reasoning is None:
        # Some compatible endpoints report it at the top level.
        reasoning = getattr(usage, 'reasoning_tokens', None)
    counts['reasoning_tokens'] = reasoning
    return counts


def _response_text(response):
    """Extract assistant text, tolerating list content."""
    message = response.choices[0].message
    content = getattr(message, 'content', None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            text = (
                part.get('text') if isinstance(part, dict)
                else getattr(part, 'text', None)
            )
            if text:
                parts.append(text)
        return ''.join(parts).strip()
    return ''


def _has_reasoning_text(response):
    """True when the provider returned a thinking trace."""
    message = response.choices[0].message
    return bool(getattr(message, 'reasoning_content', None))


def _run_variant(client, variant, provider, model, config,
                 max_tokens, runs):
    """Run one variant `runs` times, return a result dict."""
    from llm_compat import create_chat_completion

    kwargs = _build_variant_kwargs(
        variant, provider, model, config, max_tokens
    )
    sent = {
        key: value for key, value in kwargs.items()
        if key != 'messages'
    }

    calls = []
    for _ in range(runs):
        t0 = time.monotonic()
        try:
            response = create_chat_completion(
                client.chat.completions.create,
                kwargs,
                provider,
                model,
            )
        except Exception as exc:
            calls.append({
                'ms': int((time.monotonic() - t0) * 1000),
                'error': f"{type(exc).__name__}: {exc}",
            })
            continue
        duration_ms = int((time.monotonic() - t0) * 1000)
        text = _response_text(response)
        call = {'ms': duration_ms, 'chars': len(text)}
        call.update(_usage_counts(response))
        call['reasoning_text'] = _has_reasoning_text(response)
        call['sample'] = text[:70]
        calls.append(call)

    return {
        'variant': variant,
        'request': sent,
        'calls': calls,
    }


def _summarize(result):
    """Add min/median/max latency over the successful calls."""
    times = [
        call['ms'] for call in result['calls']
        if 'error' not in call
    ]
    if not times:
        result['summary'] = None
        return result
    result['summary'] = {
        'runs': len(times),
        'min_ms': min(times),
        'median_ms': int(statistics.median(times)),
        'max_ms': max(times),
    }
    return result


def _reasoning_verdict(result):
    """Describe whether thinking actually ran, or None."""
    observed = []
    for call in result['calls']:
        if 'error' in call:
            continue
        tokens = call.get('reasoning_tokens')
        if tokens:
            observed.append(tokens)
        elif call.get('reasoning_text'):
            observed.append(0)
    if not observed:
        return None
    return max(observed)


def render_text_report(results, config_path, target):
    """Render the human-readable report."""
    lines = []
    lines.append("=" * 62)
    lines.append("mod-llm-chatter LATENCY PROBE")
    lines.append("=" * 62)
    lines.append(f"Config: {config_path}")
    lines.append(f"Target: {target}")
    lines.append("")

    for result in results:
        lines.append(f"[{result['variant']}]")
        lines.append(
            "  request: "
            + json.dumps(result['request'], sort_keys=True)
        )
        for index, call in enumerate(result['calls'], 1):
            if 'error' in call:
                lines.append(
                    f"  run {index}: FAILED after "
                    f"{call['ms']} ms -- {call['error']}"
                )
                continue
            reasoning = call.get('reasoning_tokens')
            reasoning_note = (
                f", reasoning={reasoning}"
                if reasoning is not None else ""
            )
            if call.get('reasoning_text') and not reasoning:
                reasoning_note += ", reasoning_content present"
            lines.append(
                f"  run {index}: {call['ms']} ms "
                f"(completion="
                f"{call.get('completion_tokens')}"
                f"{reasoning_note})"
            )
            if call['sample']:
                lines.append(f"    -> {call['sample']}")
            elif not reasoning:
                lines.append("    -> (empty response)")

        summary = result['summary']
        if summary:
            lines.append(
                f"  latency: min {summary['min_ms']} ms / "
                f"median {summary['median_ms']} ms / "
                f"max {summary['max_ms']} ms"
            )
        thinking = _reasoning_verdict(result)
        if thinking:
            lines.append(
                f"  THINKING IS ON: the provider spent up to "
                f"{thinking} reasoning tokens."
            )
        elif thinking == 0:
            lines.append(
                "  THINKING IS ON: the provider returned a "
                "reasoning trace."
            )
        lines.append("")

    production = next(
        (r for r in results if r['variant'] == 'production'),
        None,
    )
    if production and production['summary']:
        median = production['summary']['median_ms']
        lines.append("-" * 62)
        lines.append(
            f"Production request median: {median} ms per call."
        )
        if _reasoning_verdict(production):
            lines.append(
                "The bridge asked for thinking to be off and the "
                "provider thought anyway -- that is the slowness. "
                "Try a non-thinking model for "
                "LLMChatter.Model."
            )
        else:
            lines.append(
                "Thinking is off, so this is the provider's raw "
                "speed for this model and prompt size. Compare it "
                "against LLMChatter.MaxTokens and the chatter "
                "cooldowns before blaming the model."
            )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='mod-llm-chatter LLM latency probe',
    )
    parser.add_argument(
        '--config', required=True,
        help='Path to mod_llm_chatter.conf',
    )
    parser.add_argument(
        '--runs', type=int, default=3,
        help='Calls per variant (default 3)',
    )
    parser.add_argument(
        '--max-tokens', type=int, default=None,
        help='Output budget (default LLMChatter.MaxTokens)',
    )
    parser.add_argument(
        '--compare', action='store_true',
        help='Also time the provider default and thinking-on '
             'variants, to show what the thinking flags buy',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Print results as JSON instead of text',
    )
    args = parser.parse_args()

    _require_openai()
    config = _load_config(args.config)

    from chatter_healthcheck import format_llm_target
    from chatter_llm import build_llm_client, resolve_model

    provider = str(config.get(
        'LLMChatter.Provider', DEFAULT_PROVIDER
    )).strip().lower()
    model = resolve_model(config.get(
        'LLMChatter.Model', DEFAULT_DEEPSEEK_MODEL
    ))

    if args.max_tokens is not None:
        max_tokens = args.max_tokens
    else:
        try:
            max_tokens = int(config.get(
                'LLMChatter.MaxTokens', 350
            ))
        except (TypeError, ValueError):
            max_tokens = 350

    client = build_llm_client(config, provider)
    if client is None:
        print(
            f"ERROR: could not build a client for "
            f"provider '{provider}' -- check the provider name "
            f"and its API key.",
            file=sys.stderr,
        )
        return 2

    variants = (
        _VARIANTS if args.compare else ('production',)
    )
    results = []
    for variant in variants:
        results.append(_summarize(_run_variant(
            client, variant, provider, model, config,
            max_tokens, max(1, args.runs),
        )))

    target = format_llm_target(config)
    if args.json:
        print(json.dumps({
            'target': target,
            'max_tokens': max_tokens,
            'results': results,
        }, ensure_ascii=False, indent=2))
    else:
        print(render_text_report(results, args.config, target))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
