#!/usr/bin/env python3
"""Focused adaptive request regression checks."""

import sys
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from llm_compat import (  # noqa: E402
    build_chat_options,
    create_chat_completion,
    describe_model_compatibility,
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

    def test_chat_options_are_provider_neutral(self):
        self.assertEqual(
            build_chat_options(80, temperature=0.4),
            {"max_tokens": 80, "temperature": 0.4},
        )
        self.assertEqual(
            build_chat_options(80),
            {"max_tokens": 80},
        )

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
            operation, request, "deepseek", "deepseek-flash"
        ), "ok")
        self.assertEqual(len(calls), 2)
        self.assertNotIn("temperature", calls[1])

        # The learned correction survives into later requests.
        cached = {"max_tokens": 80, "temperature": 0.4}
        create_chat_completion(
            operation, cached, "deepseek", "deepseek-flash"
        )
        self.assertNotIn("temperature", calls[2])

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
            "ollama",
            "qwen3:8b",
        ), "ok")
        self.assertNotIn("max_tokens", calls[1])
        self.assertEqual(calls[1]["max_completion_tokens"], 80)

        create_chat_completion(
            operation, {"max_tokens": 40}, "ollama", "qwen3:8b"
        )
        self.assertEqual(calls[2], {"max_completion_tokens": 40})

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
                "max_tokens": 80,
                "reasoning_effort": "none",
            },
            "ollama",
            "qwen3:8b",
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
                "deepseek",
                "deepseek-flash",
            )
        self.assertEqual(len(calls), 1)

    def test_server_error_does_not_change_cached_options(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            raise ProviderError(
                "unsupported upstream; temperature diagnostics",
                status_code=503,
            )

        with self.assertRaisesRegex(ProviderError, "upstream"):
            create_chat_completion(
                operation,
                {"max_tokens": 80, "temperature": 0.4},
                "deepseek",
                "deepseek-flash",
            )
        with self.assertRaises(ProviderError):
            create_chat_completion(
                operation,
                {"max_tokens": 80, "temperature": 0.4},
                "deepseek",
                "deepseek-flash",
            )
        self.assertIn("temperature", calls[1])

    def test_structured_param_wins_over_unrelated_message(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
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
                "deepseek",
                "deepseek-flash",
            )
        # Nothing was rewritten: temperature was not in the request.
        self.assertEqual(calls[0], {"max_completion_tokens": 80})

    def test_generic_error_code_requires_rejection_text(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
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
                "deepseek",
                "deepseek-flash",
            )
        self.assertEqual(len(calls), 1)

    def test_compatibility_description_reflects_learned_overrides(self):
        self.assertIn(
            "temperature=custom",
            describe_model_compatibility("deepseek", "deepseek-flash"),
        )

        def operation(**kwargs):
            raise ProviderError(
                "Unsupported value: temperature only supports default"
            )

        with self.assertRaises(ProviderError):
            create_chat_completion(
                operation,
                {"max_tokens": 80, "temperature": 0.4},
                "deepseek",
                "deepseek-flash",
            )
        self.assertIn(
            "temperature=provider-default",
            describe_model_compatibility("deepseek", "deepseek-flash"),
        )


if __name__ == "__main__":
    unittest.main()
