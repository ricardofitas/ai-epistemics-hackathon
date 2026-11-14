"""Execute original method bodies and isolate three input-construction repairs.

All source units and fault families were previously observed. The output is a
post-discovery mechanism experiment with a local recording sink. No model runs.
"""

import ast
from collections import Counter, defaultdict
import copy
import gzip
import hashlib
import inspect
import json
import logging
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
LAB = "lab-bench-language-agent-biology-benchmark"


def load_class(path, name, namespace, remove_bases=False):
    tree = ast.parse(path.read_text())
    node = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == name)
    node.decorator_list = []
    if remove_bases:
        node.bases = []
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, node], type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)
    return namespace[name]


def load_native_classes():
    namespace = {
        "Any": Any, "Dict": Dict, "List": List, "Literal": Literal,
        "Optional": Optional, "Union": Union, "pd": pd, "np": np,
        "json": json, "re": re, "Path": Path, "inspect": inspect,
        "hashlib": hashlib, "log": logging.getLogger("native_preprocessing"),
        "get_logger": lambda: logging.getLogger("native_generator"),
    }
    sources = ROOT / "upstream"
    load_class(sources / "core_prompt.py", "PromptABC", namespace)
    load_class(sources / "core_text.py", "FormatStrPrompt", namespace)
    generator = load_class(sources / "bench_answer_generator.py", "BenchAnswerGenerator", namespace, remove_bases=True)
    preprocessor = load_class(sources / "dataflow_eval_tool.py", "DataFlowEvalTool", namespace)
    return preprocessor, generator


class RecordedServing:
    def __init__(self):
        self.prompts = []
        self.calls = 0

    def generate_from_input(self, user_inputs, system_prompt=None):
        self.calls += 1
        self.prompts = list(user_inputs)
        return ["<answer>A</answer>"] * len(user_inputs)


class FrameStorage:
    def __init__(self, frame):
        self.frame = frame.copy()

    def read(self, *args, **kwargs):
        return self.frame.copy()

    def write(self, frame):
        self.frame = frame.copy()
        return "in_memory_recording_fixture"


def bind_source_symbols(entry, mapping):
    prompt = entry["meta"]["prompt"]["user_template"]
    for mapping_key, canonical_name in (("input_question_key", "question"), ("input_context_key", "context")):
        source_name = mapping.get(mapping_key)
        if isinstance(source_name, str):
            prompt = prompt.replace("{" + source_name + "}", "{" + canonical_name + "}")
    entry["meta"]["prompt"]["user_template"] = prompt


def install_parallel_choice_decoder(preprocessor):
    original = preprocessor._normalize_choices_value

    def decode(value):
        if isinstance(value, dict) and set(value) == {"label", "text"}:
            labels, texts = value["label"], value["text"]
            if isinstance(labels, list) and isinstance(texts, list) and len(labels) == len(texts) and len(set(labels)) == len(labels):
                return original(texts)
        return original(value)

    preprocessor._normalize_choices_value = decode


def run_condition(preprocessor_class, generator_class, entry, cases, condition):
    entry = copy.deepcopy(entry)
    mapping = copy.deepcopy(entry["meta"]["key_mapping"])
    records = [copy.deepcopy(case["record"]) for case in cases]
    preprocessor = preprocessor_class.__new__(preprocessor_class)
    if condition in ("bind_source_symbols", "both_shared_repairs", "all_input_repairs"):
        bind_source_symbols(entry, mapping)
    if condition in ("decode_parallel_choices", "both_shared_repairs", "all_input_repairs"):
        install_parallel_choice_decoder(preprocessor)
    if entry["bench_name"] == LAB and condition in ("lab_complete_options", "all_input_repairs"):
        for record in records:
            record["_source_complete_choices"] = [record["ideal"], *record["distractors"]]
        mapping["input_choices_key"] = "_source_complete_choices"
    frame, mapping = preprocessor._preprocess_dataframe(pd.DataFrame(records), entry["bench_name"], mapping, eval_type=entry["bench_dataflow_eval_type"])
    bench = SimpleNamespace(meta=entry["meta"], bench_prompt_template=entry.get("bench_prompt_template"))
    template, _ = preprocessor._resolve_prompt_template(bench, entry["bench_dataflow_eval_type"])
    serving = RecordedServing()
    operator = generator_class(eval_type=entry["bench_dataflow_eval_type"], llm_serving=serving, prompt_template=template, force_generate=True)
    storage = FrameStorage(frame)
    operator.run(storage=storage, input_question_key=mapping["input_question_key"], input_choices_key=mapping["input_choices_key"], input_context_key=mapping.get("input_context_key"), output_key="generated_ans")
    if len(serving.prompts) != len(cases):
        raise RuntimeError("Native generator did not record every selected source row")
    rows = []
    for case, record, prompt in zip(cases, frame.to_dict("records"), serving.prompts):
        question = str(record[mapping["input_question_key"]])
        context = operator._normalize_context(record.get(mapping.get("input_context_key")))
        choices = operator._ensure_list(record[mapping["input_choices_key"]])
        changed_question = operator._build_prompt(eval_type=entry["bench_dataflow_eval_type"], question="QUESTION_NONCE_20261114", context=context, choices=choices)
        changed_context = operator._build_prompt(eval_type=entry["bench_dataflow_eval_type"], question=question, context="CONTEXT_NONCE_20261114", choices=choices)
        expected = [str(value).strip() for value in case["expected_choices"]]
        displayed = [str(value).strip() for value in choices]
        rows.append({
            "bench": case["bench"], "source_index": case["source_index"], "condition": condition,
            "question_bound": prompt != changed_question,
            "declared_nonempty_context": bool(context),
            "declared_context_bound": bool(context) and prompt != changed_context,
            "choices_preserved": displayed == expected,
            "gold_present": expected[case["gold_index"]] in displayed,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt": prompt,
            "displayed_choices": choices,
        })
    counts = Counter()
    for row in rows:
        for field in ("question_bound", "declared_nonempty_context", "declared_context_bound", "choices_preserved", "gold_present"):
            counts[field] += row[field]
    return {"rows": len(rows), "recording_sink_batch_calls": serving.calls, **counts}, rows


def main():
    hashes = json.loads((ROOT / "UPSTREAM_HASHES.json").read_text())
    for name, expected_hash in hashes.items():
        assert hashlib.sha256((ROOT / "upstream" / name).read_bytes()).hexdigest() == expected_hash
    protocol = json.loads((ROOT / "PROTOCOL.json").read_text())
    gallery = json.loads((ROOT / "GALLERY_SELECTED.json").read_text())
    cases = defaultdict(list)
    for line in gzip.decompress((ROOT / "INPUTS.jsonl.gz").read_bytes()).splitlines():
        case = json.loads(line)
        cases[case["bench"]].append(case)
    preprocessor, generator = load_native_classes()
    summary = {}
    captures = []
    errors = []
    for bench, selected in cases.items():
        summary[bench] = {}
        for condition in protocol["conditions"]:
            try:
                result, rows = run_condition(preprocessor, generator, gallery[bench], selected, condition)
                summary[bench][condition] = result
                captures.extend(rows)
            except Exception as error:
                errors.append({"bench": bench, "condition": condition, "error": repr(error)})
    report = {
        "status": "complete" if not errors else "partial",
        "scope": protocol["scope"],
        "source_rows_reused": sum(map(len, cases.values())),
        "condition_records": len(captures),
        "provider_model_requests": 0,
        "errors": errors,
        "panels": summary,
        "limits": ["Previously observed source units and mechanisms; no new natural failure discovery or prevalence estimate.", "Data-only AST method replay with a local recording sink; model/tokenizer/network transport excluded.", "Input repairs do not test or repair reference parsing, metric computation, option randomization or task-population validity.", "Mapped context preservation measures the declared configuration, rather than proving that context is required for every source task."],
    }
    (ROOT / "SUMMARY.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in captures).encode()
    (ROOT / "CAPTURES.jsonl.gz").write_bytes(gzip.compress(payload, mtime=0))
    (ROOT / "ERRORS.json").write_text(json.dumps(errors, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "source_rows_reused": report["source_rows_reused"], "condition_records": len(captures), "errors": errors}, indent=2))


if __name__ == "__main__":
    main()
