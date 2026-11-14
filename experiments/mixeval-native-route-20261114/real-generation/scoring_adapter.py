"""Task-aware adapter for the pinned official MixEval RULE parser.

This is an integration wrapper, not the default model-judge scoring mode.
The original helper function ASTs execute unchanged after SHA256 validation.
Callers own the RNG and must preserve its seed and call order for reproducibility.
This module performs no generation, network request, model loading or benchmark
aggregation. Pass chat/API response text; base-model response extraction is out
of scope. Invalid/unsupported source records return INCOMPLETE without a score.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import hashlib
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, Mapping

import numpy as np

MODE = "official_mixeval_rule"
OFFICIAL_REVISION = "7c52b41929d461df7733573528bdfb08774b0c53"
METRIC_UTILS_SHA256 = "85077e61ca01f4c240158ff3b18a0451130fa879a2a46a11f3b382dbbf1fd73a"
SOURCE = Path(__file__).resolve().parent / "official/mix_eval/utils/metric_utils.py"
HELPERS = (
    "find_all_sub",
    "parse_multi_choice_response_rule",
    "check_is_number",
    "normalize_str",
    "extract_numbers",
    "parse_freeform_response_rule",
    "eval_multi_choice",
    "eval_freeform_rule",
)


class _RNGTrace:
    """Delegate unchanged choice draws while recording official fallback use."""

    def __init__(self, rng: Any) -> None:
        self.rng = rng
        self.draws: list[str] = []

    def choice(self, choices: list[str]) -> str:
        result = self.rng.choice(choices)
        self.draws.append(result)
        return result


@lru_cache(maxsize=1)
def _verified_code():
    payload = SOURCE.read_bytes()
    if hashlib.sha256(payload).hexdigest() != METRIC_UTILS_SHA256:
        raise ValueError("official_source_hash_mismatch")
    tree = ast.parse(payload, filename=str(SOURCE))
    functions = {
        item.name: item for item in tree.body if isinstance(item, ast.FunctionDef)
    }
    if any(name not in functions for name in HELPERS):
        raise ValueError("official_helper_missing")
    module = ast.Module(body=[functions[name] for name in HELPERS], type_ignores=[])
    return compile(ast.fix_missing_locations(module), str(SOURCE), "exec")


def _incomplete(error: str, kind: Any = None) -> dict[str, Any]:
    return {
        "status": "INCOMPLETE",
        "mode": MODE,
        "official_revision": OFFICIAL_REVISION,
        "problem_type": kind if isinstance(kind, str) else None,
        "score": None,
        "parsed": None,
        "random_fallback": False,
        "random_draws": [],
        "error": error,
    }


def score_case(record: Mapping[str, Any], response: str, rng: Any) -> dict[str, Any]:
    """Score one typed source case using the exact official rule-mode helpers.

    Free-form targets are OR aliases. Choice targets are one zero-based integer
    index. MC empty/unparseable responses retain official random-choice fallback;
    no score override converts that fallback into a forced incorrect outcome.
    Unknown response text (None/non-string) remains INCOMPLETE.
    """
    if not isinstance(record, Mapping):
        return _incomplete("source_not_mapping")
    kind = record.get("problem_type")
    if not isinstance(kind, str) or kind not in {"free-form", "single-choice", "multiple-choice"}:
        return _incomplete("unsupported_problem_type", kind)
    if not isinstance(record.get("prompt"), str) or not record["prompt"].strip():
        return _incomplete("invalid_source_prompt", kind)
    if not isinstance(record.get("benchmark_name"), str) or not record["benchmark_name"].strip():
        return _incomplete("invalid_source_benchmark_name", kind)
    if kind == "free-form" and record["benchmark_name"] == "QuAc":
        return _incomplete("official_freeform_prompt_not_implemented_for_QuAc", kind)
    if record.get("context") is not None and not isinstance(record["context"], str):
        return _incomplete("invalid_source_context", kind)
    if not isinstance(response, str):
        return _incomplete("response_missing_or_not_text", kind)

    target = record.get("target")
    if not isinstance(target, list) or not target:
        return _incomplete("missing_or_invalid_target_list", kind)
    options = record.get("options")
    if kind == "free-form":
        if not all(isinstance(alias, str) and bool(alias.strip()) for alias in target):
            return _incomplete("invalid_freeform_alias_list", kind)
        if options is not None and (
            not isinstance(options, list)
            or not all(isinstance(option, str) for option in options)
        ):
            return _incomplete("invalid_optional_freeform_options", kind)
    else:
        if not isinstance(options, list) or len(options) < 2:
            return _incomplete("invalid_choice_options", kind)
        if not all(isinstance(option, str) and bool(option.strip()) for option in options):
            return _incomplete("invalid_choice_option_text", kind)
        if len(options) > 26:
            return _incomplete("choice_alphabet_exceeds_A_to_Z", kind)
        if len(target) != 1 or type(target[0]) is not int:
            return _incomplete("choice_target_requires_one_zero_based_integer", kind)
        if not 0 <= target[0] < len(options):
            return _incomplete("choice_target_index_out_of_range", kind)
        if not callable(getattr(rng, "choice", None)):
            return _incomplete("choice_rng_not_provided", kind)

    trace = _RNGTrace(rng)
    environment: dict[str, Any] = {"re": re, "np": np, "random": trace}
    try:
        exec(_verified_code(), environment)
        args = SimpleNamespace(model_type="APIModelBase")
        if kind == "free-form":
            parsed = environment["parse_freeform_response_rule"](args, response)
            score = float(environment["eval_freeform_rule"](target, parsed))
            reference = list(target)
        else:
            labels = [chr(ord("A") + i) for i in range(len(options))]
            reference = labels[target[0]]
            parsed = environment["parse_multi_choice_response_rule"](
                args, response, labels, dict(zip(labels, options))
            )
            score = float(environment["eval_multi_choice"](reference, parsed))
    except Exception as exc:
        result = _incomplete("official_rule_execution_error:" + type(exc).__name__, kind)
        result["detail"] = str(exc)
        result["random_fallback"] = bool(trace.draws)
        result["random_draws"] = trace.draws
        return result
    return {
        "status": "PASS",
        "mode": MODE,
        "official_revision": OFFICIAL_REVISION,
        "source_sha256": METRIC_UTILS_SHA256,
        "problem_type": kind,
        "score": score,
        "parsed": parsed,
        "reference": reference,
        "random_fallback": bool(trace.draws),
        "random_draws": trace.draws,
        "error": None,
        "scope": "Exact official rule-mode scoring, not default model judging or model accuracy.",
    }
