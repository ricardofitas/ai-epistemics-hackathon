#!/usr/bin/env python3
"""Create a new fixed math cohort from source-reviewed families; no API calls."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import shutil

from scoring import numeric

ROOT = Path(__file__).resolve().parent
MODELS = ["gemma-4-31b-it", "deepseek-v4-flash"]
VARIANTS = ["numeric", "paraphrase", "p1", "p2"]
ROLES = ["selection", "confirmation"]
N_FAMILIES, N_PER_ROLE, BATCH_SIZE, N_BLOCKS = 30, 15, 3, 5
N_TASKS = N_FAMILIES * len(VARIANTS)
N_REQUESTS = len(MODELS) * len(ROLES) * len(VARIANTS) * N_BLOCKS
RUNNER_SHA = "c280811c5f685cdc5b254d5097946835428cd87de6ea58218de1e2cad537fe5e"
INSTRUCTION = """Solve each arithmetic word problem independently. Return only one JSON object mapping every provided ID to its final numerical answer as a string. Use exact integers, finite decimals, or an exact fraction a/b. Do not include units or explanations. If you cannot solve an item, use the string ABSTAIN. Include every ID exactly once and no extra keys. Do not browse or use tools."""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def prepare(args):
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for field in ("selected_data", "source_manifest", "source_disposition", "selection_plan", "runner"):
        path = getattr(args, field, None)
        if path is not None and not path.is_file():
            raise FileNotFoundError("Missing preparation input before writing any outputs: " + str(path))
    for name in ("manifest.jsonl", "task_key.json", "protocol.json"):
        if (output / name).exists():
            raise FileExistsError("Prepared cohort exists: " + name)
    if sha(args.runner) != RUNNER_SHA:
        raise ValueError("Exact original native-SSE runner required")
    source = json.loads(args.selected_data.read_text())
    if source.get("source_validation_status", source.get("status")) != "accepted_source_reviewed":
        raise ValueError("Final source-review disposition required before manifest preparation")
    families = sorted(source["families"], key=lambda f: f["selection_slot"])
    if len(families) != N_FAMILIES or len({f["source_family_id"] for f in families}) != N_FAMILIES:
        raise ValueError("Need exactly 30 reviewed source families")
    if [f["selection_slot"] for f in families] != list(range(1, N_FAMILIES + 1)):
        raise ValueError("Expected selection slots 1..30")
    if Counter(f["analysis_role"] for f in families) != {r: N_PER_ROLE for r in ROLES}:
        raise ValueError("Expected 15/15 allocation")
    for family in families:
        if family.get("source_validation_status") != "accepted":
            raise ValueError("Every family must have an accepted source-only disposition")
        slot = family["selection_slot"]
        role = "selection" if slot <= N_PER_ROLE else "confirmation"
        block = ((slot - 1) % N_PER_ROLE) // BATCH_SIZE + 1
        if family["analysis_role"] != role or family["batch_block"] != block:
            raise ValueError("Role/common block partition changed")
        variants = {x["variant"]: x for x in family["variants"]}
        if set(variants) != set(VARIANTS) or len(family["variants"]) != 4:
            raise ValueError("Expected four source variants")
        for item in variants.values():
            if not isinstance(item["question"], str) or not item["question"].strip():
                raise ValueError("Empty source question")
            numeric(item["gold_answer"])
    destination = output / "selected_data.json"
    if destination.resolve() != args.selected_data.resolve():
        if destination.exists():
            raise FileExistsError(destination)
        shutil.copyfile(args.selected_data, destination)
    auxiliaries = {"source_manifest.json": args.source_manifest,
                   "source_disposition.json": getattr(args, "source_disposition", None),
                   "selection_plan.json": getattr(args, "selection_plan", None)}
    for name, expected_field in (("source_disposition.json", "source_disposition_sha256"),
                                 ("selection_plan.json", "selection_plan_sha256")):
        expected = source.get(expected_field)
        if expected and (not auxiliaries[name] or sha(auxiliaries[name]) != expected):
            raise ValueError("Source-review proof required and must match: " + name)
    for name, source_path in auxiliaries.items():
        if source_path:
            target = output / name
            if target.resolve() != source_path.resolve():
                if target.exists():
                    if sha(target) != sha(source_path):
                        raise FileExistsError("Conflicting auxiliary input: " + str(target))
                else:
                    shutil.copyfile(source_path, target)
    # Opaque IDs have no monotone relationship with split, category or family.
    ids = [f"T{i:04d}" for i in range(1, N_TASKS + 1)]
    random.Random(2026111394).shuffle(ids)
    tasks, lookup = [], {}
    for family in families:
        by_variant = {x["variant"]: x for x in family["variants"]}
        for variant in VARIANTS:
            item = by_variant[variant]
            row = {"task_id": ids[len(tasks)], "family_id": family["source_family_id"],
                   "selection_slot": family["selection_slot"],
                   "analysis_role": family["analysis_role"], "batch_block": family["batch_block"],
                   "variant": variant, "gold_answer": item["gold_answer"],
                   "question_sha256": hashlib.sha256(item["question"].encode()).hexdigest()}
            tasks.append(row)
            lookup[family["source_family_id"], variant] = row
    write_new(output / "task_key.json", {"rows": tasks})
    requests = []
    for model in MODELS:
        for role in ROLES:
            for variant in VARIANTS:
                for block in range(1, N_BLOCKS + 1):
                    batch = [f for f in families if f["analysis_role"] == role and f["batch_block"] == block]
                    if len(batch) != BATCH_SIZE:
                        raise ValueError("Expected three unrelated source families per block")
                    model_items = []
                    for family in batch:
                        item = next(x for x in family["variants"] if x["variant"] == variant)
                        model_items.append({"id": lookup[family["source_family_id"], variant]["task_id"],
                                            "question": item["question"]})
                    payload = {"model": model, "input": INSTRUCTION + "\n\n" + json.dumps(model_items, ensure_ascii=False),
                               "stream": True, "temperature": 0, "max_output_tokens": 8192,
                               "tools": [], "tool_choice": "none", "agentic_memory": False, "store": False}
                    requests.append({"requested_model": model, "analysis_role": role, "variant": variant,
                                     "batch_block": block, "item_ids": [x["id"] for x in model_items],
                                     "family_ids": [f["source_family_id"] for f in batch],
                                     "request_payload": payload,
                                     "request_sha256": hashlib.sha256(canonical(payload)).hexdigest()})
    random.Random(2026111392).shuffle(requests)
    for index, row in enumerate(requests, 1):
        row.update(trial_id=f"MC-{index:03d}", execution_order=index)
    with (output / "manifest.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for row in requests:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    admission = output / "admission"
    admission.mkdir(exist_ok=False)
    neutral = [{"id": "A001", "question": "A box contains 2 red balls and 3 blue balls. How many balls are in the box?"},
               {"id": "A002", "question": "A pencil costs 4 dollars. What is the cost of 3 pencils?"},
               {"id": "A003", "question": "Mira has 9 cards and gives away 2 cards. How many cards remain?"}]
    with (admission / "manifest.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for index, model in enumerate(MODELS, 1):
            payload = {"model": model, "input": INSTRUCTION + "\n\n" + json.dumps(neutral, ensure_ascii=False),
                       "stream": True, "temperature": 0, "max_output_tokens": 8192,
                       "tools": [], "tool_choice": "none", "agentic_memory": False, "store": False}
            row = {"trial_id": f"AD-{index:02d}", "requested_model": model,
                   "item_ids": [x["id"] for x in neutral], "admission_only": True,
                   "request_payload": payload, "request_sha256": hashlib.sha256(canonical(payload)).hexdigest()}
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    names = ["selected_data.json", "task_key.json", "manifest.jsonl", "admission/manifest.jsonl"]
    names.extend(name for name, value in auxiliaries.items() if value)
    protocol = {
        "id": "source-reviewed-math-advice-consequence30-20261113",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "prepared_before_math_model_performance",
        "models": MODELS,
        "candidate_selection": "Two configurations chosen for 9/9 complete prior advice captures each; no math performance inspected. Aliases do not pin provider weights.",
        "source_sha256": {name: sha(output / name) for name in names},
        "implementation_sha256": {name: sha(ROOT / name) for name in [
            "prepare_manifest.py", "scoring.py", "capture_math.py", "gate_admission.py",
            "analyze_math.py", "test_runtime.py", "test_analyze_math.py", "README.md",
            "prospective_design.md"]},
        "runner_sha256": RUNNER_SHA,
        "allocation": {"families": N_FAMILIES, "selection": N_PER_ROLE, "confirmation": N_PER_ROLE,
                       "variants_per_family": len(VARIANTS), "models": len(MODELS), "batch_size": BATCH_SIZE,
                       "requests": N_REQUESTS, "classifications": N_TASKS * len(MODELS)},
        "admission": {"requests": 2, "items_per_request": BATCH_SIZE, "directory": "admission",
                      "gate": "Strict capture plus exact JSON IDs and numeric/ABSTAIN answer representation only; correctness is never checked",
                      "failure": "If either fixed candidate fails, stop before all 80 study requests; no retries, repairs or candidate replacement",
                      "scope": "Trivial nonstudy format controls excluded from performance and all study denominators",
                      "maximum_total_requests": N_REQUESTS + 2, "maximum_total_requested_output_tokens": (N_REQUESTS + 2) * 8192},
        "randomization": {"source_order_seed": 2026111391, "request_order_seed": 2026111392,
                          "task_id_seed": 2026111394,
                          "common_batch_blocks": "Slots grouped by three within each role, identical for every variant and candidate"},
        "inference": {"temperature": 0, "max_output_tokens": 8192, "concurrency": 2,
                      "socket_timeout_seconds": 120, "attempts_per_request": 1,
                      "maximum_requested_output_tokens": N_REQUESTS * 8192,
                      "tools": [], "agentic_memory": False, "store": False, "history": "none"},
        "parse": {"final": "Entire JSON object; optional single outer code fence; every exact requested ID once, no extras or duplicates",
                  "answers": "JSON strings with exact integer/finite decimal/exponent/fraction, optional valid thousands commas and leading dollar symbol; ABSTAIN is valid incorrect",
                  "unknown": "Incomplete capture, invalid batch JSON or invalid numeric item remains [0,1], never imputed wrong",
                  "numeric": "Exact Fraction equality; representation at most 128 characters and exponent magnitude at most 100; no rounding tolerance, expression execution, unit inference or repair call"},
        "scoring": {"primary": "Family mean accuracy over two variants for both selectors",
                    "imposed_variants": ["p1", "p2"], "corrected_variants": ["numeric", "paraphrase"],
                    "choice": "Unique complete raw maximum, or unique robust winner whose lower score exceeds every other upper score; overlap/ties indeterminate",
                    "confirmation": "Fixed corrected-selected minus imposed-selected mean target accuracy on independent confirmation families; retain signed zero/negative; same winner gives exact zero by identity",
                    "joint_secondary": "Both target variants correct within a family",
                    "limits": "Targets are separate numerical substitution and wording changes, not their composition; source-fit/score policy abstraction, not actual user adoption"},
        "bootstrap": {"repeats": 10000, "seed": 2026111393,
                      "units": ["source_family", "common_three_family_batch_block"],
                      "scope": "Paired descriptive percentile uncertainty with fixed observed winners; only five request-sharing blocks per role",
                      "missing": "Resample coupled lower/upper score rows; report percentile bound envelope without complete-case deletion"},
        "stopping": "All 80 frozen study requests once after two format admissions; no retry, replacement, model/item additions, silent resumption or early success stop. Preserve every failed/incomplete/unparseable result and all nulls.",
        "evidence_scope": "One source-reviewed selected-case follow-up. Human validation and pretraining absence unproved. No population or general assistant error rate; no reversal assumed.",
    }
    write_new(output / "protocol.json", protocol)
    print(json.dumps({"prepared": str(output), "study_requests": len(requests), "admission_requests": 2, "tasks": len(tasks),
                      "classifications": len(tasks) * len(MODELS), "inference_calls": 0,
                      "protocol_sha256": sha(output / "protocol.json")}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected-data", type=Path, required=True)
    p.add_argument("--source-manifest", type=Path)
    p.add_argument("--source-disposition", type=Path)
    p.add_argument("--selection-plan", type=Path)
    p.add_argument("--runner", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=ROOT)
    prepare(p.parse_args())
