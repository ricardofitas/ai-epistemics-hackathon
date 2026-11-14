"""Regression and deliberate fault controls, entirely local and read-only on originals."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys
import analyze_paired_hardened as hardened

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "prior" / "real-generation"


def main():
    manifest, cases, receipts = hardened.load_inputs(PRIOR)
    scorer = hardened.load_scorer(PRIOR / "scoring_adapter.py")
    before = {str(path.relative_to(PRIOR)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in PRIOR.rglob("*") if path.is_file()}
    old_summary = json.loads((PRIOR / "ANALYSIS_SUMMARY.json").read_text())
    old_captures = json.loads((PRIOR / "ANALYSIS_CAPTURES.json").read_text())
    report, outcomes = hardened.analyze_objects(manifest, cases, receipts, scorer)
    invariant_fields = ["status", "planned_requests", "recorded_artifacts", "completed_scored", "effects",
                        "usage_records", "input_tokens", "output_tokens", "cost_units", "cost_currency",
                        "scoring_mode", "new_judge_calls"]
    assert all(report[field] == old_summary[field] for field in invariant_fields)
    def normalized_judgment(item):
        judged = deepcopy(item["judged"])
        if judged and isinstance(judged.get("parsed"), list):
            # The pinned official helper returns list(set(...)); candidate order
            # can differ across Python hash seeds while score/content agree.
            judged["parsed"] = sorted(judged["parsed"], key=lambda value: json.dumps(value, sort_keys=True))
        return item["trial_id"], item["score"], judged
    assert [normalized_judgment(item) for item in outcomes] == [normalized_judgment(item) for item in old_captures]
    assert report["integrity_status"] == "PASS" and report["unknown"] == 11
    rows = []
    tid, tid2 = manifest[0]["trial_id"], manifest[1]["trial_id"]

    def check(name, mutation, expected_integrity, expected_scored, target_reason=None):
        modified = deepcopy(receipts)
        mutation(modified)
        result, captures = hardened.analyze_objects(manifest, cases, modified, scorer)
        assert result["planned_requests"] == 80 and len(captures) == 80
        assert all(item["pairs"] == 20 for item in result["effects"])
        assert result["completed_scored"] == expected_scored, (name, result["completed_scored"])
        assert result["integrity_status"] == expected_integrity, (name, result["integrity_status"])
        if target_reason:
            assert target_reason in next(item for item in captures if item["trial_id"] == tid)["reasons"]
        if expected_integrity == "FAIL":
            assert result["status"] == "integrity_failure"
        rows.append({"control": name, "status": "PASS", "integrity_status": result["integrity_status"],
                     "completed_scored": result["completed_scored"], "unknown": result["unknown"],
                     "effects": [{"model": item["model"], "pairs": item["pairs"], "gain_bounds": item["gain_bounds"]}
                                 for item in result["effects"]]})

    check("minimal_local_capture_error", lambda r: r.__setitem__(tid, {
        "trial_id": tid, "attempt_count": 1, "local_capture_error": "TimeoutError", "completed_nonempty": False}),
        "PASS", 68, "local_capture_error")
    check("missing_artifact", lambda r: r.pop(tid), "PASS", 68, "missing_artifact")
    check("unreadable_artifact", lambda r: r.__setitem__(tid, {"_unreadable_receipt": "JSONDecodeError"}),
          "PASS", 68, "unreadable_artifact")
    check("missing_trial_id", lambda r: r[tid].pop("trial_id"), "PASS", 68, "missing_trial_id")
    check("missing_request_hash", lambda r: r[tid].pop("request_sha256"), "PASS", 68, "missing_request_sha256")
    check("missing_output_hash", lambda r: r[tid].pop("output_text_sha256"), "PASS", 68, "missing_output_text_sha256")
    check("missing_request_payload", lambda r: r[tid].pop("request_payload"), "PASS", 68, "missing_request_payload")
    check("wrong_request_hash", lambda r: r[tid].__setitem__("request_sha256", "0" * 64),
          "FAIL", 68, "request_sha256_mismatch")
    check("changed_payload", lambda r: r[tid]["request_payload"].__setitem__("input", "different question"),
          "FAIL", 68, "request_payload_hash_mismatch")
    check("changed_output_bytes", lambda r: r[tid].__setitem__("output_text", "changed"),
          "FAIL", 68, "output_text_hash_mismatch")
    check("wrong_returned_model", lambda r: r[tid].__setitem__("returned_model", "other-model"),
          "FAIL", 68, "returned_model_mismatch")
    check("wrong_trial_identity", lambda r: r[tid].__setitem__("trial_id", "unplanned-id"),
          "FAIL", 68, "trial_id_mismatch")
    check("duplicate_trial_identity", lambda r: r[tid2].__setitem__("trial_id", tid),
          "FAIL", 67, "duplicate_identity")
    check("duplicate_provider_response_id", lambda r: r[tid2].__setitem__("response_id", r[tid]["response_id"]),
          "FAIL", 67, "duplicate_identity")
    check("unexpected_extra_receipt", lambda r: r.__setitem__("unplanned", {"trial_id": "unplanned"}), "FAIL", 69)
    check("incomplete_even_if_completion_flag_true", lambda r: r[tid].__setitem__("response_status", "incomplete"),
          "PASS", 68, "capture_incomplete_or_empty")
    check("cap_violation", lambda r: r[tid]["usage"].__setitem__("output_tokens", 4097),
          "FAIL", 68, "output_token_cap_violation")
    for name, mutation in [
        ("duplicate_manifest_id", lambda m, c: m[1].__setitem__("trial_id", m[0]["trial_id"])),
        ("missing_manifest_slot", lambda m, c: m.pop()),
        ("changed_source_record", lambda m, c: c[0]["record"].__setitem__("prompt", "changed")),
    ]:
        new_manifest, new_cases = deepcopy(manifest), deepcopy(cases)
        mutation(new_manifest, new_cases)
        try:
            hardened.analyze_objects(new_manifest, new_cases, receipts, scorer)
        except hardened.InputIntegrityError as error:
            rows.append({"control": name, "status": "PASS", "fatal_design_error": str(error)})
        else:
            raise AssertionError(name)
    after = {str(path.relative_to(PRIOR)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in PRIOR.rglob("*") if path.is_file()}
    assert before == after
    result = {"status": "PASS", "baseline": {"exact_invariant_fields": invariant_fields,
              "all_80_per_slot_scores_identical": True,
              "judged_results_identical_after_ordering_official_unordered_parsed_candidates": True,
              "parsed_candidate_order_note": "Official list(set(...)) candidate order is process-hash dependent; sorted only for verification comparison, not scorer execution.",
              "completed_scored": 69, "unknown": 11,
              "effects": report["effects"]}, "fault_controls": rows, "control_count": len(rows),
              "original_files_unchanged": True, "original_file_count": len(before),
              "original_tree_hash": hardened.digest(before), "new_model_calls": 0,
              "limits": ["Local derivative and deliberate fault controls only; not full installed-provider integration.",
                         "Scientific scores remain the pinned optional official RULE mode, not semantic adjudication.",
                         "Unknown integrity means evidence missing; FAIL means contradictory or duplicate identity/hash evidence."]}
    (ROOT / "VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    (ROOT / "baseline").mkdir(exist_ok=True)
    (ROOT / "baseline" / "ANALYSIS_SUMMARY.json").write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "baseline" / "ANALYSIS_CAPTURES.json").write_text(json.dumps(outcomes, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "PASS", "controls": len(rows), "baseline_scored": 69, "unknown": 11,
                      "original_files_unchanged": True}))


if __name__ == "__main__":
    main()
