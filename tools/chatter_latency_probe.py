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

With per-feature provider routing, --feature measures one feature's
route and --all-routes measures the main provider plus every feature
routed away from it, each against the endpoint the bridge would
really use:

    python chatter_latency_probe.py \
        --config <path/to/mod_llm_chatter.conf> --all-routes

Zero extra dependencies -- stdlib plus the openai package the
bridge already needs.
"""

import argparse
import json
import os
import statistics
import sys
import time

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


def _resolve_routes(config, args):
    """Return the routes to measure, as a list of dicts.

    A route is one (feature, provider, model, client) the bridge
    would actually use. With no selection this is just the main
    provider, which is what the probe measured before feature
    routing existed.
    """
    from chatter_llm import (
        FEATURES,
        get_client_for_provider,
        resolve_feature_target,
        resolve_main_model,
        resolve_provider,
    )

    main_provider = resolve_provider(config)
    main_model = resolve_main_model(config)

    if args.feature:
        feature = args.feature.strip().lower()
        if feature not in FEATURES:
            print(
                f"ERROR: unknown feature {args.feature!r}.\n"
                "Known features: " + ", ".join(sorted(FEATURES)),
                file=sys.stderr,
            )
            sys.exit(2)
        wanted = [(feature, *resolve_feature_target(config, feature))]
    elif args.all_routes:
        # The main provider, plus every feature that leaves it.
        # Features sharing a target collapse into one measurement:
        # the endpoint does not care which feature asked.
        wanted = [('main', main_provider, main_model)]
        seen = {(main_provider, main_model)}
        for feature in sorted(FEATURES):
            target = resolve_feature_target(config, feature)
            if target in seen:
                continue
            seen.add(target)
            wanted.append((feature, *target))
    else:
        wanted = [('main', main_provider, main_model)]

    routes = []
    for label, provider, model in wanted:
        client = get_client_for_provider(config, provider)
        if client is None:
            print(
                f"ERROR: could not build a client for provider "
                f"'{provider}' (route: {label}) -- check the "
                f"provider name and its API key.",
                file=sys.stderr,
            )
            sys.exit(2)
        routes.append({
            'route': label,
            'provider': provider,
            'model': model,
            'client': client,
            'is_default': (provider, model) == (
                main_provider, main_model
            ),
        })
    return routes


def render_text_report(routes, config_path):
    """Render the human-readable report."""
    lines = []
    lines.append("=" * 62)
    lines.append("mod-llm-chatter LATENCY PROBE")
    lines.append("=" * 62)
    lines.append(f"Config: {config_path}")
    lines.append("")

    for route in routes:
        suffix = "" if route['is_default'] else "  (routed)"
        lines.append(
            f"### route: {route['route']} -> "
            f"{route['provider']}/{route['model']}{suffix}"
        )
        lines.append("")
        for result in route['results']:
            lines.extend(_render_variant(result))
        production = next(
            (r for r in route['results']
             if r['variant'] == 'production'),
            None,
        )
        if production and production['summary']:
            lines.append(
                f"  production median: "
                f"{production['summary']['median_ms']} ms"
            )
            lines.append("")

    lines.append("-" * 62)
    lines.extend(_render_conclusion(routes))
    return "\n".join(lines)


def _render_variant(result):
    """Render one variant's runs and summary."""
    lines = [f"[{result['variant']}]"]
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
            f"(completion={call.get('completion_tokens')}"
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
    return lines


def _render_conclusion(routes):
    """Name what the numbers mean."""
    lines = []
    for route in routes:
        production = next(
            (r for r in route['results']
             if r['variant'] == 'production'),
            None,
        )
        if not production or not production['summary']:
            continue
        median = production['summary']['median_ms']
        label = (
            f"{route['route']} ({route['provider']}/"
            f"{route['model']})"
        )
        if _reasoning_verdict(production):
            lines.append(
                f"{label}: {median} ms median, and the provider "
                f"thought despite being told not to -- that is "
                f"the slowness. Try a non-thinking model."
            )
        else:
            lines.append(
                f"{label}: {median} ms median with thinking off, "
                f"so this is the provider's raw speed for this "
                f"model and prompt size."
            )
    if len(routes) > 1:
        lines.append("")
        lines.append(
            "Each route above was measured against the endpoint "
            "the bridge would actually use for it."
        )
    return lines


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
        '--feature', default=None,
        help='Measure one feature\'s route (e.g. guild) instead '
             'of the main provider',
    )
    parser.add_argument(
        '--all-routes', action='store_true',
        help='Measure the main provider plus every feature '
             'routed away from it',
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

    if args.feature and args.all_routes:
        print(
            "ERROR: pass --feature or --all-routes, not both.",
            file=sys.stderr,
        )
        return 2

    _require_openai()
    config = _load_config(args.config)

    if args.max_tokens is not None:
        max_tokens = args.max_tokens
    else:
        try:
            max_tokens = int(config.get(
                'LLMChatter.MaxTokens', 350
            ))
        except (TypeError, ValueError):
            max_tokens = 350

    routes = _resolve_routes(config, args)
    variants = (
        _VARIANTS if args.compare else ('production',)
    )

    for route in routes:
        route['results'] = [
            _summarize(_run_variant(
                route['client'], variant, route['provider'],
                route['model'], config, max_tokens,
                max(1, args.runs),
            ))
            for variant in variants
        ]

    if args.json:
        print(json.dumps({
            'max_tokens': max_tokens,
            'routes': [
                {k: v for k, v in route.items() if k != 'client'}
                for route in routes
            ],
        }, ensure_ascii=False, indent=2))
    else:
        print(render_text_report(routes, args.config))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
