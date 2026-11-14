"""Bounded full-module One-Eval run_eval integration with captured outputs.

The run_eval/generator.run/evaluator.run/FileStorage entry points are imported
unchanged from pinned source modules. Explicit interventions are prompt binding,
provider-boundary local replay, per-task official-rule scoring, and suppression
of the incompatible native choice post-rescore. No model execution is implied.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import types

from native_import import HERE, load_native

sys.path.insert(0, str(HERE / "support"))
from scoring_adapter import score_case

_spec = importlib.util.spec_from_file_location(
    "pinned_official_mixeval_prompts",
    HERE / "support/official/mix_eval/prompts/evaluation_prompts.py",
)
_prompts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prompts)


class CoverageError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def response_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def case_id(record):
    value = record.get("id")
    if type(value) not in (str, int) or str(value) == "":
        raise CoverageError("missing_or_invalid_source_id")
    kind = record.get("problem_type")
    if kind == "free-form":
        family = "free_form"
    elif kind in ("single-choice", "multiple-choice"):
        family = "multiple_choice"
    else:
        raise CoverageError("unsupported_problem_type")
    return family + ":" + str(value)


def source_prompt(record):
    if not isinstance(record, dict):
        raise CoverageError("source_not_object")
    if not isinstance(record.get("prompt"), str) or not record["prompt"].strip():
        raise CoverageError("invalid_source_prompt")
    if not isinstance(record.get("benchmark_name"), str):
        raise CoverageError("invalid_benchmark_name")
    if record.get("context") is not None and not isinstance(record["context"], str):
        raise CoverageError("invalid_context")
    target = record.get("target")
    if not isinstance(target, list) or not target:
        raise CoverageError("invalid_target_list")
    key = case_id(record)
    if key.startswith("free_form:"):
        if not all(isinstance(x, str) and bool(x.strip()) for x in target):
            raise CoverageError("invalid_alias_list")
        if record["benchmark_name"] == "QuAc":
            raise CoverageError("official_QuAc_prompt_unsupported")
        return _prompts.construct_prompt_freeform(record)
    options = record.get("options")
    if (not isinstance(options, list) or not 2 <= len(options) <= 26
            or not all(isinstance(x, str) and bool(x.strip()) for x in options)):
        raise CoverageError("invalid_choice_options")
    if len(target) != 1 or type(target[0]) is not int:
        raise CoverageError("invalid_zero_based_target")
    if not 0 <= target[0] < len(options):
        raise CoverageError("zero_based_target_out_of_range")
    return _prompts.construct_prompt_multichoice(record)


def validate_coverage(records, outputs, expected_sources, expected_responses):
    if not isinstance(records, list) or not records:
        raise CoverageError("empty_or_invalid_source_list")
    if not isinstance(outputs, list):
        raise CoverageError("outputs_not_list")
    ids = [case_id(record) for record in records]
    if len(set(ids)) != len(ids):
        raise CoverageError("duplicate_source_id")
    if len({key.split(":")[0] for key in ids}) != 1:
        raise CoverageError("mixed_task_family_group")
    if any("generated_ans" in record for record in records):
        raise CoverageError("preexisting_generated_ans_would_skip_generation")
    if not isinstance(expected_sources, dict) or set(expected_sources) != set(ids):
        raise CoverageError("expected_source_id_coverage")
    if not isinstance(expected_responses, dict) or set(expected_responses) != set(ids):
        raise CoverageError("expected_response_id_coverage")
    prompts = {}
    for record, key in zip(records, ids):
        if digest(record) != expected_sources[key]:
            raise CoverageError("source_hash_or_reference_drift:" + key)
        prompts[key] = source_prompt(record)
    if any(not isinstance(output, dict) for output in outputs):
        raise CoverageError("output_not_object")
    output_ids = [output.get("case_id") for output in outputs]
    if len(set(output_ids)) != len(output_ids):
        raise CoverageError("duplicate_output_id")
    if set(output_ids) != set(ids):
        raise CoverageError("missing_or_extra_output_id")
    by_id = {output["case_id"]: output for output in outputs}
    for key in ids:
        output = by_id[key]
        if output.get("source_sha256") != expected_sources[key]:
            raise CoverageError("output_source_association_drift:" + key)
        if not isinstance(output.get("response"), str):
            raise CoverageError("missing_or_nontext_response:" + key)
        if response_digest(output["response"]) != expected_responses[key]:
            raise CoverageError("response_bytes_or_association_drift:" + key)
    return ids, prompts, by_id


def run_group(records, outputs, expected_sources, expected_responses, output_dir, seed=42):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "scope": "Pinned full-module ordinary run_eval integration; local captured-output serving",
        "installed_distribution": False,
        "new_model_calls": 0,
        "native_primary_metric_stage_executed": False,
        "native_return_role": "diagnostic",
        "generation_calls": 0,
        "typed_rule_mean": None,
        "scoring_mode": "official_mixeval_rule_not_default_model_judge",
        "seed": seed,
    }
    try:
        ids, expected_prompts, by_id = validate_coverage(
            records, outputs, expected_sources, expected_responses
        )
        n = load_native(output_dir / "one_eval.log")
        report["module_origins"] = n.origins
        native_tool = n.tool.DataFlowEvalTool
        generator_class = n.generator.BenchAnswerGenerator
        evaluator_class = n.evaluator.UnifiedBenchDatasetEvaluator
        original_entry_points = {
            "run_eval": native_tool.run_eval.__code__.co_filename,
            "generator_run": generator_class.run.__code__.co_filename,
            "evaluator_run": evaluator_class.run.__code__.co_filename,
        }
        report["entry_points"] = original_entry_points
        records_by_id = dict(zip(ids, records))
        rng = random.Random(seed)
        score_captures = []

        class SourceBoundPrompt(n.core.prompt.DIYPromptABC):
            def __init__(self):
                self.cursor = 0

            def build_prompt(self, need_fields=None, **kwargs):
                if self.cursor >= len(ids):
                    raise CoverageError("too_many_prompt_constructions")
                key = ids[self.cursor]
                record = records_by_id[key]
                if kwargs.get("question") != record["prompt"]:
                    raise CoverageError("generator_question_drift:" + key)
                expected_context = str(record.get("context") or "").strip()
                if str(kwargs.get("context") or "").strip() != expected_context:
                    raise CoverageError("generator_context_drift:" + key)
                if key.startswith("multiple_choice:"):
                    # Native preprocessing strips entire option edges. This
                    # normalization is checked; original option bytes are
                    # restored in the official prompt returned below.
                    got = kwargs.get("choices") or []
                    if got != [option.strip() for option in record["options"]]:
                        raise CoverageError("generator_choices_drift:" + key)
                self.cursor += 1
                return expected_prompts[key]

        bound_prompt = SourceBoundPrompt()

        class CapturedServing(n.core.LLMServingABC):
            def __init__(self):
                self.calls = []
                self.completed = False
                self.failure = None

            def start_serving(self):
                return None

            def cleanup(self):
                return None

            def generate_from_input(self, user_inputs, system_prompt=""):
                self.calls.append({"prompts": list(user_inputs), "system_prompt": system_prompt})
                wanted = [expected_prompts[key] for key in ids]
                if self.completed or list(user_inputs) != wanted:
                    self.failure = "provider_boundary_request_or_coverage_drift"
                    raise CoverageError(self.failure)
                self.completed = True
                return [by_id[key]["response"] for key in ids]

        serving = CapturedServing()

        def official_score(self, df, pred_col, **kwargs):
            if not serving.completed or serving.failure or bound_prompt.cursor != len(ids):
                raise CoverageError("provider_coverage_not_complete")
            seen = []
            for idx, row in df.iterrows():
                record = json.loads(row["_source_json"])
                key = row["_case_id"]
                if key not in records_by_id or digest(record) != expected_sources[key]:
                    raise CoverageError("source_carrier_drift:" + str(key))
                # Original source columns survive native preprocessing; added
                # normalized fields may coexist, but cannot change task/gold.
                for field in ("problem_type", "prompt", "target", "benchmark_name", "options", "context"):
                    if field in record:
                        actual = row[field]
                        if field == "context" and actual is None and record[field] is None:
                            continue
                        if canonical(actual) != canonical(record[field]):
                            raise CoverageError("native_source_column_drift:" + key + ":" + field)
                response = row[pred_col]
                if not isinstance(response, str) or response_digest(response) != expected_responses[key]:
                    raise CoverageError("native_response_association_drift:" + key)
                result = score_case(record, response, rng)
                if result["status"] != "PASS":
                    raise CoverageError("typed_rule_incomplete:" + key + ":" + result["error"])
                df.at[idx, self.output_eval_valid_key] = True
                df.at[idx, self.output_eval_score_key] = result["score"]
                df.at[idx, self.output_eval_pred_key] = response
                df.at[idx, self.output_eval_error_key] = ""
                score_detail = dict(result)
                scorer_source_sha256 = score_detail.pop("source_sha256")
                score_captures.append({"case_id": key,
                                       "source_record_sha256": expected_sources[key],
                                       "scorer_source_sha256": scorer_source_sha256,
                                       "response_sha256": expected_responses[key], **score_detail})
                seen.append(key)
            if seen != ids:
                raise CoverageError("evaluator_row_order_or_coverage_drift")

        old_qa = evaluator_class._eval_qa_multi
        old_mc = evaluator_class._eval_mc_single
        evaluator_class._eval_qa_multi = official_score
        evaluator_class._eval_mc_single = official_score
        tool = native_tool(output_root=str(output_dir / "native"))
        tool._init_llm_serving = types.MethodType(lambda self, config: setattr(self, "llm_serving", serving), tool)
        tool._resolve_prompt_template = types.MethodType(
            lambda self, bench, eval_type: (bound_prompt, {"source": "source_bound_official_constructor"}), tool
        )
        tool._rescore_choice_single = types.MethodType(
            lambda self, step_file, eval_result_path, stats, *args: stats, tool
        )
        group_type = "key2_q_ma" if ids[0].startswith("free_form:") else "key3_q_choices_a"
        mapping = {"input_question_key": "prompt", "input_context_key": "context"}
        if group_type == "key2_q_ma":
            mapping["input_targets_key"] = "target"
        else:
            mapping.update(input_choices_key="options", input_label_key="target")
        source_path = output_dir / "input.jsonl"
        with source_path.open("w") as stream:
            for record, key in zip(records, ids):
                stream.write(json.dumps({**record, "_case_id": key, "_source_json": canonical(record)},
                                        ensure_ascii=False) + "\n")
        bench = n.state.BenchInfo(
            bench_name="mixeval_" + ids[0].split(":")[0], bench_dataflow_eval_type=group_type,
            dataset_cache=str(source_path), meta={"key_mapping": mapping},
        )
        config = n.state.ModelConfig(model_name_or_path="captured_public_response_boundary", is_api=True)
        try:
            native = tool.run_eval(bench, config)
        finally:
            evaluator_class._eval_qa_multi = old_qa
            evaluator_class._eval_mc_single = old_mc
        report["generation_calls"] = len(serving.calls)
        report["serving_requests"] = serving.calls
        report["shim_events"] = n.shim_events
        if serving.failure or not serving.completed or len(score_captures) != len(ids) or n.shim_events:
            raise CoverageError("post_run_boundary_or_scoring_coverage_incomplete")
        if native["stats"].get("total_samples") != len(ids) or native["stats"].get("valid_samples") != len(ids):
            raise CoverageError("native_stats_denominator_drift")
        report.update(
            status="PASS", source_rows=len(ids), scored_rows=len(ids),
            typed_rule_mean=sum(item["score"] for item in score_captures) / len(ids),
            score_captures=score_captures, native_return=native,
            coverage={"source_ids": ids, "complete": True},
            replacements=[
                "Package export/bootstrap facades and inert optional-dependency import shims",
                "Provider initialization replaced by captured-response local serving",
                "Prompt resolver replaced by source-bound official full-module constructors",
                "Evaluator _eval_qa_multi/_eval_mc_single replaced by verified official-rule adapter",
                "Native choice post-rescore bypassed to preserve explicit official rule mode",
            ],
        )
    except Exception as exc:
        report.update(status="INCOMPLETE", error=type(exc).__name__ + ":" + str(exc),
                      typed_rule_mean=None)
        if "serving" in locals():
            report["generation_calls"] = len(serving.calls)
            report["serving_requests"] = serving.calls
            report["provider_boundary_failure"] = serving.failure
        if "n" in locals():
            report["shim_events"] = n.shim_events
        if "score_captures" in locals():
            report["partial_score_captures"] = score_captures
    (output_dir / "RESULT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_bundle")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    bundle = json.loads(Path(args.input_bundle).read_text())
    result = run_group(bundle["records"], bundle["outputs"],
                       bundle["expected_sources"], bundle["expected_responses"],
                       args.output_dir, bundle.get("seed", 42))
    print(json.dumps({key: result.get(key) for key in (
        "status", "error", "source_rows", "scored_rows", "typed_rule_mean", "generation_calls"
    )}))
