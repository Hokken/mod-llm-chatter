#!/usr/bin/env python3
"""Focused model capability and adaptive request regression checks."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from llm_compat import (  # noqa: E402
    build_chat_options,
    create_anthropic_message,
    create_chat_completion,
    needs_reasoning_token_multiplier,
    reset_compatibility_cache,
)


class ProviderError(ValueError):
    def __init__(self, message, status_code=400, body=None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body or {}


def routing_404(step="Filter by Parameters", metadata=True):
    body = {"error": {
        "message": "No endpoints found that can handle the requested "
                   "parameters.",
        "code": 404,
    }}
    if metadata:
        body["error"]["metadata"] = {"failed_routing_step": step}
    return ProviderError(body["error"]["message"], 404, body)


def required_request(effort="none"):
    return {
        "max_tokens": 80,
        "temperature": 0.4,
        "response_format": {"type": "json_schema"},
        "extra_body": {
            "reasoning": {"effort": effort},
            "provider": {"require_parameters": True},
        },
    }


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

    def test_gpt6_luna_disables_reasoning_without_inflating_budget(self):
        self.assertEqual(build_chat_options(
            "openai", "gpt-6-luna", 350,
            temperature=0.8, reasoning_effort="none",
        ), {
            "max_completion_tokens": 350,
            "temperature": 0.8,
            "reasoning_effort": "none",
        })
        self.assertFalse(needs_reasoning_token_multiplier(
            "openai", "gpt-6-luna", "none"
        ))
        self.assertTrue(needs_reasoning_token_multiplier(
            "openai", "gpt-6-luna", "medium"
        ))
        self.assertNotIn("temperature", build_chat_options(
            "openai", "gpt-6-luna", 350,
            temperature=0.8, reasoning_effort="medium",
        ))
        for model in ("gpt-6-astra", "gpt-6.1-sol"):
            self.assertNotIn("reasoning_effort", build_chat_options(
                "openai", model, 350, reasoning_effort="none",
            ))

    def test_fine_tuned_model_uses_base_model_profile(self):
        self.assertEqual(build_chat_options(
            "openai", "ft:gpt-4o-mini:org:custom", 100,
            temperature=0.7,
        ), {
            "max_completion_tokens": 100,
            "temperature": 0.7,
        })

    def test_capability_rules_preserve_provider_routing(self):
        for model in ("gpt-6-luna", "gpt-6-sol", "gpt-5.6-terra"):
            with self.subTest(model=model):
                direct = build_chat_options(
                    "openai", model, 100,
                    temperature=0.8, reasoning_effort="none",
                )
                self.assertEqual(direct, {
                    "max_completion_tokens": 100,
                    "temperature": 0.8,
                    "reasoning_effort": "none",
                })
                self.assertEqual(build_chat_options(
                    " OPENAI ", " FT:" + model.upper() + ":org:custom ",
                    100, temperature=0.8, reasoning_effort="NONE",
                ), direct)
                self.assertEqual(build_chat_options(
                    "openrouter", "openai/" + model, 100,
                    temperature=0.8, reasoning_effort="none",
                ), {"max_tokens": 100, "temperature": 0.8})

        for model in ("gpt-6-astra", "gpt-6.1-sol", "gpt-6-unknown"):
            with self.subTest(model=model):
                self.assertEqual(build_chat_options(
                    "openai", model, 100,
                    temperature=0.8, reasoning_effort="none",
                ), {"max_completion_tokens": 100})
                self.assertTrue(needs_reasoning_token_multiplier(
                    "openai", model, "none"
                ))

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

    def test_anthropic_rejected_fields_are_removed_and_cached(self):
        calls = []
        rejections = [
            "`temperature` is deprecated for this model.",
            "thinking: type 'disabled' is not supported for this model",
        ]

        def operation(**kwargs):
            calls.append(kwargs)
            if rejections:
                raise ProviderError(rejections.pop(0))
            return "ok"

        request = {
            "max_tokens": 80,
            "extra_body": {
                "temperature": 0.4,
                "thinking": {"type": "disabled"},
            },
        }
        self.assertEqual(create_anthropic_message(
            operation, request, "claude-new"
        ), "ok")
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[2]["extra_body"], {})
        self.assertEqual(request["extra_body"]["temperature"], 0.4)

        calls.clear()
        self.assertEqual(create_anthropic_message(
            operation, request, "claude-new"
        ), "ok")
        self.assertEqual(calls[0]["extra_body"], {})

    def test_anthropic_other_errors_propagate(self):
        def operation(**kwargs):
            raise ProviderError("overloaded", status_code=529)

        with self.assertRaises(ProviderError):
            create_anthropic_message(
                operation,
                {"extra_body": {"temperature": 0.4}},
                "claude-new",
            )

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


class OpenRouterRoutingTests(unittest.TestCase):
    def setUp(self):
        reset_compatibility_cache()

    def run_with(self, failures, request, model="vendor/model"):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            if len(calls) <= failures:
                raise routing_404()
            return "ok"

        result = create_chat_completion(
            operation, request, "openrouter", model,
        )
        return result, calls

    def test_none_reasoning_is_dropped_and_learned_on_success(self):
        request = required_request()
        result, calls = self.run_with(1, request)
        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 2)
        self.assertNotIn("reasoning", calls[1]["extra_body"])
        self.assertTrue(
            calls[1]["extra_body"]["provider"]["require_parameters"]
        )
        self.assertEqual(calls[1]["response_format"],
                         request["response_format"])
        # Caller's request is never mutated.
        self.assertEqual(request, required_request())

        # Next required request for this model skips the failed attempt.
        _, calls = self.run_with(0, required_request())
        self.assertEqual(len(calls), 1)
        self.assertNotIn("reasoning", calls[0]["extra_body"])

    def test_learned_override_keeps_none_on_unrestricted_requests(self):
        self.run_with(1, required_request())
        plain = {"max_tokens": 80,
                 "extra_body": {"reasoning": {"effort": "none"}}}
        _, calls = self.run_with(0, plain)
        self.assertEqual(calls[0]["extra_body"]["reasoning"],
                         {"effort": "none"})
        # Other models are unaffected.
        _, calls = self.run_with(0, required_request(), "other/model")
        self.assertIn("reasoning", calls[0]["extra_body"])

    def test_nothing_learned_when_the_retry_still_fails(self):
        with self.assertRaises(ProviderError):
            self.run_with(2, required_request())
        _, calls = self.run_with(0, required_request())
        self.assertIn("reasoning", calls[0]["extra_body"])

    def test_message_fallback_without_metadata(self):
        calls = []

        def operation(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise routing_404(metadata=False)
            return "ok"

        self.assertEqual(create_chat_completion(
            operation, required_request(), "openrouter", "vendor/model",
        ), "ok")
        self.assertNotIn("reasoning", calls[1]["extra_body"])

    def test_real_effort_is_never_dropped_and_warns_once(self):
        logger = Mock()
        for _ in range(2):
            with self.assertRaises(ProviderError):
                create_chat_completion(
                    Mock(side_effect=routing_404()),
                    required_request("high"), "openrouter", "vendor/model",
                    logger,
                )
        self.assertEqual(logger.warning.call_count, 1)
        self.assertIn("ReasoningEffort", logger.warning.call_args.args[0])

    def test_unrelated_routing_and_providers_are_not_retried(self):
        cases = (
            (routing_404("Filter by Regional Surcharge"),
             required_request(), "openrouter"),
            (routing_404(), required_request(), "openai_compatible"),
            (routing_404(), {"max_tokens": 80, "extra_body": {
                "reasoning": {"effort": "none"}}}, "openrouter"),
            (ProviderError("No endpoints found that can handle the "
                           "requested parameters", 400),
             required_request(), "openrouter"),
        )
        for error, request, provider in cases:
            with self.subTest(error=str(error), provider=provider):
                operation = Mock(side_effect=error)
                with self.assertRaises(ProviderError):
                    create_chat_completion(
                        operation, request, provider, "vendor/model",
                    )
                self.assertEqual(operation.call_count, 1)


if __name__ == "__main__":
    unittest.main()
