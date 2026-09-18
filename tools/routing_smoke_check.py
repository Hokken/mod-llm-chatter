#!/usr/bin/env python3
"""Per-feature provider routing check for mod-llm-chatter.

Verifies that each feature resolves to the provider and model its
config asks for, and that the feature modules are bound to the
feature they belong to. Stubs the optional third-party modules the
same way import_smoke_check.py does, so it runs anywhere.

  python routing_smoke_check.py
"""

import sys
import types
from pathlib import Path


def _install_stubs():
    """Stub the optional deps so routing can be imported."""
    for name in ("openai",):
        if name not in sys.modules:
            mod = types.ModuleType(name)
            mod.OpenAI = type("OpenAI", (), {})
            sys.modules[name] = mod
    if "mysql.connector" not in sys.modules:
        mysql = types.ModuleType("mysql")
        connector = types.ModuleType("mysql.connector")
        mysql.connector = connector
        sys.modules["mysql"] = mysql
        sys.modules["mysql.connector"] = connector


# (label, config, feature, expected provider/model)
CASES = [
    (
        "default config keeps every feature on the main provider",
        {'LLMChatter.Provider': 'deepseek',
         'LLMChatter.Model': 'deepseek-flash'},
        'guild', ('deepseek', 'deepseek-flash'),
    ),
    (
        "feature override moves one feature to the cloud",
        {'LLMChatter.Provider': 'ollama',
         'LLMChatter.Model': 'qwen3:8b',
         'LLMChatter.GuildChatter.Provider': 'deepseek',
         'LLMChatter.GuildChatter.Model': 'deepseek-v4-pro'},
        'guild', ('deepseek', 'deepseek-v4-pro'),
    ),
    (
        "override without a model takes the provider's fast model",
        {'LLMChatter.Provider': 'ollama',
         'LLMChatter.Model': 'qwen3:8b',
         'LLMChatter.GuildChatter.Provider': 'deepseek'},
        'guild', ('deepseek', 'deepseek-flash'),
    ),
    (
        "an unrouted feature is untouched by another's override",
        {'LLMChatter.Provider': 'ollama',
         'LLMChatter.Model': 'qwen3:8b',
         'LLMChatter.GuildChatter.Provider': 'deepseek'},
        'memory', ('ollama', 'qwen3:8b'),
    ),
    (
        "Ollama override with a model is honoured",
        {'LLMChatter.Provider': 'deepseek',
         'LLMChatter.Model': 'deepseek-flash',
         'LLMChatter.Memory.Provider': 'ollama',
         'LLMChatter.Memory.Model': 'qwen3:8b'},
        'memory', ('ollama', 'qwen3:8b'),
    ),
    (
        "Ollama override with NO model falls back, never guesses",
        {'LLMChatter.Provider': 'deepseek',
         'LLMChatter.Model': 'deepseek-flash',
         'LLMChatter.Memory.Provider': 'ollama'},
        'memory', ('deepseek', 'deepseek-flash'),
    ),
    (
        "quick analyze prefers the fast model over a Pro main model",
        {'LLMChatter.Provider': 'deepseek',
         'LLMChatter.Model': 'deepseek-v4-pro'},
        'quick_analyze', ('deepseek', 'deepseek-flash'),
    ),
    (
        "quick analyze still honours an explicit model",
        {'LLMChatter.Provider': 'deepseek',
         'LLMChatter.Model': 'deepseek-v4-pro',
         'LLMChatter.QuickAnalyze.Model': 'deepseek-v4-pro'},
        'quick_analyze', ('deepseek', 'deepseek-v4-pro'),
    ),
    (
        "model aliases resolve in feature overrides",
        {'LLMChatter.Provider': 'ollama',
         'LLMChatter.Model': 'qwen3:8b',
         'LLMChatter.RaidChatter.Provider': 'deepseek',
         'LLMChatter.RaidChatter.Model': 'deepseek-pro'},
        'raid', ('deepseek', 'deepseek-v4-pro'),
    ),
]

# module -> the feature its call_llm must be bound to
BINDINGS = {
    'chatter_proximity': 'proximity',
    'chatter_guild': 'guild',
    'chatter_guild_login': 'guild',
    'chatter_guild_player': 'guild',
    'chatter_group': 'group',
    'chatter_group_handlers': 'group',
    'chatter_group_general_reaction': 'group',
    'chatter_group_state': 'group',
    'chatter_cache': 'group',
    'chatter_general': 'general',
    'chatter_memory': 'memory',
    'chatter_boss_dialogue': 'raid',
}


def check_resolution(chatter_llm):
    """Run the config matrix. Returns the failure count."""
    failures = 0
    for label, config, feature, expected in CASES:
        chatter_llm.reset_client_cache()
        actual = chatter_llm.resolve_feature_target(config, feature)
        ok = actual == expected
        failures += not ok
        print(
            f"  {'PASS' if ok else 'FAIL'}  {label}\n"
            f"        {feature}: {actual[0]}/{actual[1]}"
            + ("" if ok else f"  (expected {expected[0]}/{expected[1]})")
        )
    return failures


def check_bindings():
    """Every feature module routes to its own feature."""
    import importlib
    failures = 0
    for module_name, feature in sorted(BINDINGS.items()):
        module = importlib.import_module(module_name)
        bound = getattr(module.call_llm, 'keywords', {}).get('feature')
        ok = bound == feature
        failures += not ok
        print(
            f"  {'PASS' if ok else 'FAIL'}  {module_name} -> "
            f"{bound}" + ("" if ok else f"  (expected {feature})")
        )
    return failures


def main():
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    _install_stubs()

    import chatter_llm

    print("Feature resolution:")
    failures = check_resolution(chatter_llm)
    print("\nModule bindings:")
    failures += check_bindings()

    print()
    if failures:
        print(f"ROUTING_CHECK_FAIL ({failures})")
        return 1
    print("OK")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
