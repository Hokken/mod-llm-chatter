#!/usr/bin/env python3
"""Focused model capability and adaptive request regression checks."""

import sys
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from llm_compat import (  # noqa: E402
    build_chat_options,
    create_chat_completion,
    needs_reasoning_token_multiplier,
    reset_compatibility_cache,
)


class ProviderError(ValueError):
    def __init__(self, message, status_code=400, body=None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body or {}


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        reset_compatibility_cache()

    def test_known_openai_profiles(self):
        sampling = build_chat_options(
            "openai", "gpt-4o-mini", 100,
            temperature=0.7, reasoning_effort="none",
        )
        self.assertEqual(sampling, {
            "max_completion_tokens": 100,
            "temperature": 0.7,
        })

        reasoning = build_chat_options(
            "openai", "gpt-5.6-luna", 100,
            temperature=0.7, reasoning_effort="none",
        )
        self.assertEqual(reasoning, {
            "max_completion_tokens": 100,
            "temperature": 0.7,
            "reasoning_effort": "none",
        })
        deliberate = build_chat_options(
            "openai", "gpt-5.6-luna", 100,
            temperature=0.7, reasoning_effort="medium",
        )
        self.assertEqual(deliberate, {
            "max_completion_tokens": 100,
            "reasoning_effort": "medium",
        })

        unsupported_none = build_chat_options(
            "openai", "gpt-5-mini", 100,
            temperature=0.7, reasoning_effort="none",
        )
        self.assertEqual(unsupported_none, {
            "max_completion_tokens": 100,
        })

        for model in (
            "gpt-5.3-codex", "gpt-5.5", "gpt-5.7"
        ):
            with self.subTest(model=model):
                self.assertEqual(build_chat_options(
                    "openai", model, 100,
                    temperature=0.8,
                    reasoning_effort="none",
                ), {
                    "max_completion_tokens": 100,
                    "temperature": 0.8,
                    "reasoning_effort": "none",
                })

    def test_reasoning_budget_detection(self):
        self.assertFalse(needs_reasoning_token_multiplier(
            "openai", "gpt-5.6-luna", "none"
        ))
        self.assertTrue(needs_reasoning_token_multiplier(
            "openai", "gpt-5.6-luna", "medium"
        ))
        self.assertTrue(needs_reasoning_token_multiplier(
            "openai", "gpt-5-mini", "none"
        ))
        self.assertTrue(needs_reasoning_token_multiplier(
            "openai", "o4-mini", ""
        ))

    def test_fine_tuned_model_uses_base_model_profile(self):
        self.assertEqual(build_chat_options(
            "openai", "ft:gpt-4o-mini:org:custom", 100,
            temperature=0.7,
        ), {
            "max_completion_tokens": 100,
            "temperature": 0.7,
        })

    def test_unknown_openai_model_uses_safe_defaults(self):
        self.assertEqual(build_chat_options(
            "openai", "future-model", 100,
            temperature=0.7, reasoning_effort="high",
        ), {"max_completion_tokens": 100})

    def test_openrouter_keeps_compatible_parameters(self):
        self.assertEqual(build_chat_options(
            "openrouter", "vendor/model", 80,
            temperature=0.4,
        ), {"max_tokens": 80, "temperature": 0.4})

    def test_rejected_temperature_is_removed_and_cached(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise ProviderError(
                    "Unsupported value: temperature only supports default"
                )
            return "ok"

        request = {
            "max_tokens": 80,
            "temperature": 0.4,
        }
        self.assertEqual(create_chat_completion(
            operation, request, "openrouter", "vendor/model"
        ), "ok")
        self.assertEqual(len(calls), 2)
        self.assertNotIn("temperature", calls[1])
        self.assertNotIn("temperature", build_chat_options(
            "openrouter", "vendor/model", 80, temperature=0.4
        ))

    def test_rejected_token_field_is_changed_and_cached(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise ProviderError(
                    "Unsupported parameter: max_tokens; use "
                    "max_completion_tokens"
                )
            return "ok"

        self.assertEqual(create_chat_completion(
            operation,
            {"max_tokens": 80},
            "openrouter",
            "vendor/new-model",
        ), "ok")
        self.assertNotIn("max_tokens", calls[1])
        self.assertEqual(calls[1]["max_completion_tokens"], 80)
        cached = build_chat_options(
            "openrouter", "vendor/new-model", 40
        )
        self.assertEqual(cached, {"max_completion_tokens": 40})

    def test_rejected_reasoning_effort_is_removed(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise ProviderError(
                    "Unsupported value for reasoning.effort"
                )
            return "ok"

        self.assertEqual(create_chat_completion(
            operation,
            {
                "max_completion_tokens": 80,
                "reasoning_effort": "none",
            },
            "openai",
            "gpt-6-astra",
        ), "ok")
        self.assertNotIn("reasoning_effort", calls[1])

    def test_unrelated_failures_are_not_hidden(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            raise RuntimeError("authentication failed")

        with self.assertRaisesRegex(RuntimeError, "authentication"):
            create_chat_completion(
                operation,
                {"max_tokens": 80},
                "openrouter",
                "vendor/model",
            )
        self.assertEqual(len(calls), 1)

    def test_server_error_does_not_change_cached_options(self):
        def operation(**kwargs):
            raise ProviderError(
                "unsupported upstream; temperature diagnostics",
                status_code=503,
            )

        with self.assertRaisesRegex(ProviderError, "upstream"):
            create_chat_completion(
                operation,
                {"max_tokens": 80, "temperature": 0.4},
                "openrouter",
                "vendor/model",
            )
        self.assertIn("temperature", build_chat_options(
            "openrouter", "vendor/model", 80, temperature=0.4
        ))

    def test_structured_param_wins_over_unrelated_message(self):
        def operation(**kwargs):
            raise ProviderError(
                "max_completion_tokens appeared in diagnostics",
                body={
                    "param": "temperature",
                    "code": "unsupported_parameter",
                },
            )

        with self.assertRaises(ProviderError):
            create_chat_completion(
                operation,
                {"max_completion_tokens": 80},
                "openai",
                "o1-mini",
            )
        self.assertIn("max_completion_tokens", build_chat_options(
            "openai", "o1-mini", 80
        ))

    def test_generic_error_code_requires_rejection_text(self):
        def operation(**kwargs):
            raise ProviderError(
                "max_tokens must be <= 8192",
                body={
                    "param": "max_tokens",
                    "code": "invalid_request_error",
                },
            )

        with self.assertRaisesRegex(ProviderError, "must be"):
            create_chat_completion(
                operation,
                {"max_tokens": 9000},
                "openrouter",
                "vendor/model",
            )
        self.assertIn("max_tokens", build_chat_options(
            "openrouter", "vendor/model", 80
        ))

    def test_none_rejection_expands_budget_and_drops_temperature(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise ProviderError(
                    "Unsupported value for reasoning_effort",
                    body={
                        "param": "reasoning_effort",
                        "code": "unsupported_value",
                    },
                )
            return "ok"

        request = build_chat_options(
            "openai", "gpt-5.7", 60,
            temperature=0.8,
            reasoning_effort="none",
        )
        self.assertEqual(create_chat_completion(
            operation,
            request,
            "openai",
            "gpt-5.7",
            reasoning_token_multiplier=4,
        ), "ok")
        self.assertEqual(calls[1], {
            "max_completion_tokens": 240,
        })
        self.assertTrue(needs_reasoning_token_multiplier(
            "openai", "gpt-5.7", "none"
        ))
        cached = build_chat_options(
            "openai", "gpt-5.7", 240,
            temperature=0.8,
            reasoning_effort="none",
        )
        self.assertEqual(cached, {
            "max_completion_tokens": 240,
        })

    def test_token_field_is_not_reversed_and_last_error_surfaces(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise ProviderError(
                    "Unsupported parameter: max_tokens"
                )
            raise ProviderError(
                "Unsupported parameter: max_completion_tokens"
            )

        with self.assertRaisesRegex(
            ProviderError, "max_completion_tokens"
        ):
            create_chat_completion(
                operation,
                {"max_tokens": 80},
                "openrouter",
                "vendor/model",
            )
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
