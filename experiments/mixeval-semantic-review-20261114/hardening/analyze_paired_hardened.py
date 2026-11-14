"""Read-only paired analysis that retains unknown outcomes and fails closed on identity drift.

This derivative preserves the frozen trial and its official optional RULE scorer.
No network/model calls; no original files are written. Integrity errors prevent a
successful report and cannot be converted into scores. Every planned slot remains
in the sensitivity denominator, including missing/unattempted/error captures.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

SCORER_SHA256 = "c0e2bc7183c5716de0b55aefa7b0507dfddb7cbe4ebaffc3f84fd8c041033000"
CONDITIONS = ("binding_only", "official_typed")
sys.dont_write_bytecode = True


class InputIntegrityError(ValueError):
    """The intended experiment itself cannot be uniquely reconstructed."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load_inputs(root):
    root = Path(root)
    manifest = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines() if line.strip()]
    cases = json.loads((root / "selected20.json").read_text())
    receipts = {}
    for path in sorted((root / "api_artifacts").glob("*.json")):
        try:
            receipts[path.stem] = json.loads(path.read_text())
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            receipts[path.stem] = {"_unreadable_receipt": type(error).__name__}
    return manifest, cases, receipts


def load_scorer(path):
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != SCORER_SHA256:
        raise InputIntegrityError("scorer_source_hash_mismatch")
    spec = importlib.util.spec_from_file_location("pinned_scoring_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.score_case


def validate_design(manifest, cases):
    if not isinstance(cases, list) or len(cases) != 20 or len(manifest) != 80:
        raise InputIntegrityError("expected_20_sources_and_80_planned_slots")
    case_map = {case["source_index"]: case for case in cases}
    if len(case_map) != 20:
        raise InputIntegrityError("duplicate_source_index")
    ids, keys = set(), set()
    for row in manifest:
        tid = row["trial_id"]
        if not isinstance(tid, str) or not tid or tid in ids:
            raise InputIntegrityError("duplicate_or_invalid_manifest_trial_id")
        ids.add(tid)
        payload = row["request_payload"]
        model = payload["model"]
        key = (model, row["source_index"], row["condition"])
        if key in keys:
            raise InputIntegrityError("duplicate_manifest_model_source_condition")
        keys.add(key)
        if row["source_index"] not in case_map or row["condition"] not in CONDITIONS:
            raise InputIntegrityError("unknown_source_or_condition")
        if row.get("request_sha256") != digest(payload):
            raise InputIntegrityError("manifest_request_hash_mismatch")
        if row.get("source_sha256") != digest(case_map[row["source_index"]]["record"]):
            raise InputIntegrityError("manifest_source_hash_mismatch")
        if row.get("prompt_sha256") != hashlib.sha256(payload["input"].encode()).hexdigest():
            raise InputIntegrityError("manifest_prompt_hash_mismatch")
        if payload.get("max_output_tokens") != 4096:
            raise InputIntegrityError("unrecognized_output_cap")
    models = sorted({row["request_payload"]["model"] for row in manifest})
    expected = {(model, i, condition) for model in models for i in case_map for condition in CONDITIONS}
    if len(models) != 2 or keys != expected:
        raise InputIntegrityError("incomplete_or_extra_manifest_factorial_cells")
    return case_map, models, ids


def analyze_objects(manifest, cases, receipts, score_case):
    case_map, models, ids = validate_design(manifest, cases)
    issues = []
    duplicate_slots = set()
    for field in ("trial_id", "response_id"):
        groups = defaultdict(list)
        for slot, receipt in receipts.items():
            if isinstance(receipt, dict) and isinstance(receipt.get(field), str) and receipt[field]:
                groups[receipt[field]].append(slot)
        for slots in groups.values():
            if len(slots) > 1:
                duplicate_slots.update(slots)
                issues.append({"kind": "duplicate_" + field, "slots": sorted(slots)})
    extra = sorted(set(receipts) - ids)
    if extra:
        issues.append({"kind": "unexpected_receipt_slots", "slots": extra})
    outcomes, lookup = [], {}
    inp = out = usage_records = 0
    cost = Decimal(0)
    for row in manifest:
        tid, model = row["trial_id"], row["request_payload"]["model"]
        receipt = receipts.get(tid)
        problems, errors = [], []
        score, judged = None, None
        if tid in duplicate_slots:
            errors.append("duplicate_identity")
        if receipt is None:
            problems.append("missing_artifact")
        elif not isinstance(receipt, dict):
            errors.append("receipt_not_object")
        elif "_unreadable_receipt" in receipt:
            problems.append("unreadable_artifact")
        else:
            for key, expected in (("trial_id", tid), ("request_sha256", row["request_sha256"]),
                                  ("requested_model", model), ("returned_model", model)):
                value = receipt.get(key)
                if value is None:
                    problems.append("missing_" + key)
                elif value != expected:
                    errors.append(key + "_mismatch")
            payload = receipt.get("request_payload")
            if payload is None:
                problems.append("missing_request_payload")
            elif digest(payload) != row["request_sha256"]:
                errors.append("request_payload_hash_mismatch")
            text = receipt.get("output_text")
            if isinstance(text, str):
                output_hash = receipt.get("output_text_sha256")
                if output_hash is None:
                    problems.append("missing_output_text_sha256")
                elif hashlib.sha256(text.encode()).hexdigest() != output_hash:
                    errors.append("output_text_hash_mismatch")
            else:
                problems.append("missing_or_nontext_output")
            if receipt.get("local_capture_error"):
                problems.append("local_capture_error")
            complete = (receipt.get("completed_nonempty") is True and receipt.get("http_status") == 200
                        and receipt.get("response_status") == "completed" and not receipt.get("stream_incomplete")
                        and not receipt.get("transport_error") and not receipt.get("api_error")
                        and not receipt.get("local_capture_error") and isinstance(text, str) and bool(text.strip()))
            if not complete:
                problems.append("capture_incomplete_or_empty")
            usage = receipt.get("usage") or {}
            if not isinstance(usage, dict):
                usage = {}
            valid_usage = all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens"))
            if valid_usage and usage["output_tokens"] > row["request_payload"]["max_output_tokens"]:
                errors.append("output_token_cap_violation")
            if valid_usage and not errors:
                usage_records += 1
                inp += usage["input_tokens"]
                out += usage["output_tokens"]
                if usage.get("cost") is not None:
                    try:
                        value = Decimal(str(usage["cost"]))
                        if not value.is_finite() or value < 0:
                            raise InvalidOperation()
                        cost += value
                    except (InvalidOperation, ValueError):
                        problems.append("invalid_usage_cost")
            if complete and not errors and not problems:
                judged = score_case(case_map[row["source_index"]]["record"], text, random.Random(42))
                if judged.get("status") == "PASS" and type(judged.get("score")) in (int, float) and judged["score"] in (0, 1):
                    score = judged["score"]
                else:
                    problems.append("scorer_incomplete")
        if errors:
            issues.append({"kind": "receipt_integrity_error", "slot": tid, "errors": errors})
        integrity = "FAIL" if errors else ("INCOMPLETE" if problems else "PASS")
        status = "completed_scored" if score is not None else ("integrity_failure_unknown" if errors else "unknown")
        item = {"trial_id": tid, "source_index": row["source_index"], "model": model,
                "condition": row["condition"], "score": score, "status": status,
                "integrity": integrity, "reasons": errors + problems, "judged": judged}
        outcomes.append(item)
        lookup[(model, row["source_index"], row["condition"])] = item
    effects = []
    for model in models:
        low = high = complete = typed_win = binding_win = ties = 0
        pairs = []
        for i in case_map:
            b, t = (lookup[(model, i, condition)]["score"] for condition in CONDITIONS)
            low += (0 if t is None else t) - (1 if b is None else b)
            high += (1 if t is None else t) - (0 if b is None else b)
            if b is not None and t is not None:
                complete += 1
                typed_win += t > b
                binding_win += b > t
                ties += t == b
            pairs.append({"source_index": i, "binding_only": b, "official_typed": t})
        effects.append({"model": model, "pairs": 20, "complete_pairs": complete, "typed_wins": typed_win,
                        "binding_wins": binding_win, "ties": ties, "gain_bounds": [low / 20, high / 20], "pairs_detail": pairs})
    completed = sum(x["score"] is not None for x in outcomes)
    incomplete_association = [item["trial_id"] for item in outcomes if any(
        reason.startswith("missing_") or reason in ("unreadable_artifact", "missing_artifact")
        for reason in item["reasons"])]
    report = {"status": "integrity_failure" if issues else ("complete" if completed == 80 else "partial"),
              "integrity_status": "FAIL" if issues else "PASS", "integrity_issues": issues,
              "integrity_status_definition": "PASS means no contradictory/duplicate evidence, not complete capture or association coverage.",
              "association_evidence_complete": not incomplete_association,
              "incomplete_association_slots": incomplete_association,
              "planned_requests": 80, "recorded_artifacts": sum(tid in receipts for tid in ids),
              "completed_scored": completed, "unknown": 80 - completed, "effects": effects,
              "usage_records": usage_records, "input_tokens": inp, "output_tokens": out,
              "cost_units": str(cost), "cost_currency": None,
              "unknown_reason_counts": dict(Counter(reason for item in outcomes for reason in item["reasons"])),
              "scoring_mode": "official_optional_rule_not_default_judge", "new_judge_calls": 0,
              "usage_scope": "Validated association, nonnegative integer token counts and output cap; rejected identities excluded."}
    return report, outcomes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.input.resolve() in args.output.resolve().parents:
        raise InputIntegrityError("output_must_not_be_within_frozen_input")
    scorer = load_scorer(args.input / "scoring_adapter.py")
    report, outcomes = analyze_objects(*load_inputs(args.input), scorer)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "ANALYSIS_SUMMARY.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "ANALYSIS_CAPTURES.json").write_text(json.dumps(outcomes, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "integrity_status", "planned_requests", "completed_scored", "unknown")}))
    return 2 if report["integrity_status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
