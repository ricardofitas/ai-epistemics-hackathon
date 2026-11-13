#!/usr/bin/env python3
"""Independent deterministic audit and explicitly post-hoc scope sensitivity."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

TARGETS = {
    "open_mt_news_ende_late2019": "wrong_source_news_period",
    "NEW-HANS-ROLES": "paraphrase_score_sufficient_for_directional_entailment",
    "NEW-BEIR-COVID-RETRIEVAL-POSITIVE": "nonsignificance_implies_equivalence",
}
MECHANISMS = sorted(set(TARGETS.values()) | {"other_material"})
FINAL_SHA = "46f12c436a49518c160927e7cd7558d7ecd40ac6a8630e204f58d5a5a75c8f21"
FIRST_COMMIT = "d592e6df7d8aef413ece3b3986b75f75f1b7b49e"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lookup(data, field, expected=None):
    result = {r[field]: r for r in data}
    require(len(data) == len(result), f"Duplicate {field}")
    if expected is not None:
        require(set(result) == expected, f"Wrong {field} coverage")
    return result


def flags(row):
    if "mechanisms" in row:
        return {m: "yes" if m in row["mechanisms"] else "no" for m in MECHANISMS}
    return {m: row.get("mechanism_flags", {}).get(m, "uncertain") for m in MECHANISMS}


def cells(data, excluded_positives=frozenset()):
    grouped = defaultdict(list)
    for r in data:
        if r["stage"] == "selected_recurrence":
            grouped[r["case_id"], r["requested_model"]].append(r)
    result = []
    for (case, model), values in sorted(grouped.items()):
        require(sorted(r["repetition"] for r in values) == [1, 2, 3], "Missing planned repetition")
        complete = sum(r["capture_complete"] for r in values)
        scorable = sum(r["capture_complete"] and r["coordinator_label"] != "unscorable" for r in values)
        positive = [r for r in values if r["response_id"] not in excluded_positives
                    and r["capture_complete"] and r["coordinator_label"] == "yes"]
        verified = sum(r["coordinator_mechanism_flags"][TARGETS[case]] == "yes" for r in positive)
        result.append({"case_id": case, "requested_model": model, "target_mechanism": TARGETS[case],
                       "planned": 3, "complete": complete, "scorable": scorable,
                       "material_error_yes": len(positive), "verified_same_mechanism": verified,
                       "two_of_three_same_mechanism": complete == 3 and scorable == 3 and verified >= 2,
                       "response_ids": [r["response_id"] for r in sorted(values, key=lambda r: r["repetition"])]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    script_parent = Path(__file__).resolve().parent
    default_root = script_parent.parent if script_parent.name == "methods" else script_parent
    parser.add_argument("wave_root", type=Path, nargs="?", default=default_root)
    parser.add_argument("--expected-summary-sha256", default=FINAL_SHA)
    parser.add_argument("--first-review-commit", default=FIRST_COMMIT)
    args = parser.parse_args()
    root = args.wave_root
    # Local work keeps captures in study/; the published experiment places them
    # directly at its root and stores this script under methods/.
    study = root / "study" if (root / "study").is_dir() else root
    reviews = root / "reviews"
    summary_path = study / "analysis_summary.json"
    require(digest(summary_path) == args.expected_summary_sha256, "Final summary differs from independently supplied SHA")
    summary, adjudication = read(summary_path), read(reviews / "adjudication.json")
    freeze = read(reviews / "first_review_freeze.json")
    expected = {f"Q{i:02d}" for i in range(1, 61)}
    packet = lookup(jsonl(study / "review_packet.jsonl"), "response_id", expected)
    key = lookup(jsonl(study / "review_key.jsonl"), "response_id", expected)
    a = lookup(jsonl(reviews / "first_a.jsonl"), "response_id", expected)
    b = lookup(jsonl(reviews / "first_b.jsonl"), "response_id", expected)
    paths = {"ratings_a": reviews / "first_a.jsonl", "ratings_b": reviews / "first_b.jsonl",
             "first_review_freeze": reviews / "first_review_freeze.json", "packet": study / "review_packet.jsonl",
             "key": study / "review_key.jsonl", "enriched": study / "responses_enriched.jsonl",
             "adjudication": reviews / "adjudication.json"}
    actual_hashes = {name: digest(path) for name, path in paths.items()}
    require(summary["sha256"] == actual_hashes, "Summary inputs are stale")
    require(freeze["packet_sha256"] == actual_hashes["packet"], "Frozen packet changed")
    require(freeze["first_rating_sha256"] == {"a": actual_hashes["ratings_a"], "b": actual_hashes["ratings_b"]}, "Original first review changed")
    require(summary["first_review_freeze"] == freeze, "Summary embeds stale first-review freeze")
    commit = read(reviews / "FIRST_REVIEW_COMMIT.json")
    tree = read(root / "publication/review_freeze_tree_readback.json")
    require(commit["review_freeze_commit"] == args.first_review_commit == adjudication["first_reviews_commit"], "Wrong first-review commit")
    require(commit["tree"] == tree["sha"], "Saved Git tree readback differs from commit record")
    tree_entries = {v["path"]: v for v in tree["tree"]}
    git_blob_checks = {}
    for relative in ["reviews/first_a.jsonl", "reviews/first_b.jsonl", "reviews/first_review_freeze.json"]:
        raw = (root / relative).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        stored = tree_entries["experiments/paper-research-wave1-20261113/" + relative]["sha"]
        require(blob == stored, f"First-review file differs from committed Git blob: {relative}")
        git_blob_checks[relative] = blob
    attachments = {}
    for relative, expected_hash in adjudication["source_evidence"].items():
        attachments[relative] = digest(reviews / relative)
        require(attachments[relative] == expected_hash, f"Stale adjudication attachment: {relative}")
    require({"fact_audit.json", "WSC_LABEL_CONVERSION_WITNESS.json"} <= set(attachments), "Missing fact/witness attachment")
    manifest = lookup(jsonl(study / "manifest.jsonl"), "trial_id")
    enriched = lookup(jsonl(study / "responses_enriched.jsonl"), "trial_id")
    captures = lookup(jsonl(study / "responses.jsonl"), "trial_id")
    require(len(manifest) == 60 and set(manifest) == set(enriched) == set(captures) == {v["trial_id"] for v in key.values()}, "Not all 60 planned attempts join")
    protocol = read(study / "protocol.json")
    require(protocol["target_mechanisms"] == TARGETS, "Target mechanism map changed")
    for relative, name in [("manifest.jsonl", "manifest"), ("casepack.json", "casepack"), ("review_casepack.json", "review_casepack")]:
        require(digest(study / relative) == protocol["hashes"][name], f"Frozen {name} changed")
    for tid, capture in captures.items():
        require(capture == read(study / f"api_artifacts/{tid}.json"), f"Raw aggregate/artifact mismatch: {tid}")
        require(capture["request_payload"] == manifest[tid]["request_payload"], f"Frozen payload mismatch: {tid}")
        wire = json.dumps(manifest[tid]["request_payload"], sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
        require(hashlib.sha256(wire).hexdigest() == capture["request_sha256"], f"Wire hash mismatch: {tid}")
        require(hashlib.sha256(capture["output_text"].encode()).hexdigest() == capture["output_text_sha256"], f"Final text hash mismatch: {tid}")
        require(digest(study / f"stream_journals/{tid}.jsonl") == capture["stream_journal_sha256"], f"Journal hash mismatch: {tid}")
    summary_rows = lookup(summary["rows"], "response_id", expected)
    independent, disagreements, mechanism_disagreements = [], [], []
    for rid in sorted(expected):
        la, lb = a[rid]["unsupported_recommendation"], b[rid]["unsupported_recommendation"]
        fa, fb = flags(a[rid]), flags(b[rid])
        if la != lb:
            disagreements.append(rid)
            require(rid in adjudication["coordinator_dispositions"], f"Unresolved label: {rid}")
        label = adjudication["coordinator_dispositions"].get(rid, la)
        if fa != fb:
            mechanism_disagreements.append(rid)
        mechanism = {m: fa[m] if fa[m] == fb[m] else "uncertain" for m in MECHANISMS}
        if rid in adjudication["coordinator_mechanisms"]:
            value = adjudication["coordinator_mechanisms"][rid]
            mechanism = flags({"mechanisms": value} if isinstance(value, list) else {"mechanism_flags": value})
        elif label == "yes":
            require(fa == fb and la == lb, f"Unresolved positive mechanism: {rid}")
        tid = key[rid]["trial_id"]
        raw, job, evidence = enriched[tid], manifest[tid], packet[rid]
        require(evidence["case_id"] == raw["case_id"] == job["case_id"], f"Case join mismatch: {rid}")
        require(evidence["response"] == raw["response"] == captures[tid]["output_text"], f"Text join mismatch: {rid}")
        require(evidence["capture_complete"] == raw["capture_complete"] == captures[tid]["completed_nonempty"], f"Completion join mismatch: {rid}")
        require(raw["capture_complete"] or label == "unscorable", f"Incomplete response promoted: {rid}")
        row = {"response_id": rid, "first_labels": {"a": la, "b": lb}, "coordinator_label": label,
               "first_mechanism_flags": {"a": fa, "b": fb}, "coordinator_mechanism_flags": mechanism,
               "trial_id": tid, "case_id": job["case_id"], "stage": job["stage"],
               "requested_model": job["requested_model"], "returned_model": captures[tid].get("returned_model"),
               "repetition": job["repetition"], "capture_complete": raw["capture_complete"]}
        require(row == summary_rows[rid], f"Summary row differs from independent decision/join: {rid}")
        independent.append(row)
    counts = dict(Counter(r["coordinator_label"] for r in independent))
    require(counts == summary["coordinator_counts"] == {"no": 36, "yes": 12, "uncertain": 5, "unscorable": 7}, "Primary counts differ")
    require(disagreements == summary["primary_disagreements"] and mechanism_disagreements == summary["mechanism_disagreements"], "Disagreement bookkeeping differs")
    for reviewer, data in [("a", a), ("b", b)]:
        require(dict(Counter(r["unsupported_recommendation"] for r in data.values())) == summary["first_review_counts"][reviewer], "First counts differ")
    for field, summary_field in [("case_id", "by_case"), ("stage", "by_stage"), ("requested_model", "by_requested_configuration")]:
        grouped = {v: dict(Counter(r["coordinator_label"] for r in independent if r[field] == v)) for v in {r[field] for r in independent}}
        require(grouped == summary[summary_field], f"Grouped counts differ: {field}")
    original_cells = cells(independent)
    require(original_cells == summary["recurrence_cells"] and len(original_cells) == 12, "Recurrence cells differ")
    role = [r for r in independent if r["case_id"] == "NEW-HANS-ROLES"]
    exact_role = sum(r["capture_complete"] and r["coordinator_label"] == "yes" and r["coordinator_mechanism_flags"][TARGETS["NEW-HANS-ROLES"]] == "yes" for r in role)
    gate = any(c["case_id"] == "NEW-HANS-ROLES" and c["two_of_three_same_mechanism"] for c in original_cells)
    require(exact_role == 0 and gate is False and summary["consequence_gate"]["eligible"] is False and summary["consequence_gate"]["eligible_requested_configurations"] == [], "Gate differs")
    not_run = read(root / "consequence/NOT_RUN_STATUS.json")
    require(not_run["actual_consequence_model_calls"] == 0 and not_run["status"] == "NOT_RUN_GATE_FAILED" and not_run["official_analysis_summary_sha256"] == args.expected_summary_sha256, "Consequence status not bound to current failed gate")
    require(not (root / "consequence/api_artifacts").exists() and not (root / "consequence/responses.jsonl").exists(), "Unexpected consequence execution artifacts")
    positive_ids = {r["response_id"] for r in independent if r["coordinator_label"] == "yes"}
    wmt = {r["response_id"] for r in independent if r["coordinator_label"] == "yes" and r["case_id"] == "open_mt_news_ende_late2019"}
    partition = {"resource_fit_mismatch": sorted(wmt | {"Q40"}), "invalid_wsc_to_nli_label_conversion": ["Q48"],
                 "explicit_nonsignificance_as_equivalence": ["Q55", "Q57"], "internal_reasoning_overclaim": ["Q50"]}
    flattened = [rid for values in partition.values() for rid in values]
    require(len(wmt) == 7 and len(flattened) == len(set(flattened)) == 12 and set(flattened) == positive_ids, "Post-hoc partition does not cover exactly the primary positives")
    sensitivity_cells = cells(independent, {"Q46"})
    before, after = {(c["case_id"], c["requested_model"]): c for c in original_cells}, {(c["case_id"], c["requested_model"]): c for c in sensitivity_cells}
    for cell in before:
        require(all(before[cell][k] == after[cell][k] for k in ["planned", "complete", "scorable", "response_ids"]), "Sensitivity altered a denominator or scorable status")
    wmt_cells = [{"requested_model": model, "planned": before[case, model]["planned"], "complete": before[case, model]["complete"],
                  "scorable": before[case, model]["scorable"], "original_verified_target": before[case, model]["verified_same_mechanism"],
                  "sensitivity_verified_target": after[case, model]["verified_same_mechanism"],
                  "original_flag": before[case, model]["two_of_three_same_mechanism"],
                  "sensitivity_flag": after[case, model]["two_of_three_same_mechanism"]}
                 for case, model in sorted(before) if case == "open_mt_news_ende_late2019"]
    output = {"audit_status": "PASS", "analysis_status": "Independent deterministic audit; no inference or Git writes",
              "scope": "Only this wave; post-hoc case-specific type partition and one-row positive-count sensitivity, not a new frozen primary outcome",
              "primary_counts_unchanged": counts, "attempted": 60, "capture_complete": sum(r["capture_complete"] for r in independent),
              "first_review_commit": args.first_review_commit, "saved_git_blob_readback_matches": git_blob_checks,
              "git_proof_scope": "Verified local file bytes against saved Git tree readback and commit record; no fresh network/Git query",
              "input_sha256": actual_hashes, "analysis_summary_sha256": digest(summary_path),
              "adjudication_attachment_sha256": attachments,
              "attachment_binding": "Fresh fact-audit/witness bytes match adjudication source_evidence; current summary binds the exact current adjudication hash",
              "all_60_capture_payload_text_artifact_journal_hash_checks": True,
              "all_60_independent_label_mechanism_join_checks": True, "all_12_recurrence_cells_match": True,
              "posthoc_type_partition": {name: {"count": len(ids), "response_ids": ids} for name, ids in partition.items()},
              "resource_fit_boundary": {"narrow_subset_count": 8, "wmt_source_period_count": 7, "svamp_construct_mismatch_count": 1,
                                        "note": "The broader generic primary outcome has 12 positives; only eight belong to this resource-fit subset."},
              "q46_exclusion_sensitivity": {"excluded_from_positive_numerators_only": ["Q46"],
                  "reason": "Mixed endorsement includes both the incorrect WMT19 and correct WMT20 alternative",
                  "remaining_positive_count": 11, "remaining_wmt_positive_count": 6,
                  "remaining_narrow_resource_fit_count": 7, "original_labels_modified": False,
                  "denominators_and_scorable_status_unchanged": True, "wmt_cells": wmt_cells,
                  "all_recurrence_cells": sensitivity_cells},
              "consequence_gate": {"eligible": gate, "exact_paws_mechanism_positive": exact_role,
                  "role_attempted": len(role), "role_complete": sum(r["capture_complete"] for r in role),
                  "actual_model_calls_recorded": not_run["actual_consequence_model_calls"], "execution_artifacts_absent": True},
              "limitations": "Fixed curated cases and requested model aliases; no population percentages, prevalence, immutable-weight claims, or external human validation. Original files are unchanged."}
    (root / "scope_sensitivity_audit.json").write_text(json.dumps(output, indent=2) + "\n")
    lines = ["# Scope and sensitivity audit", "", "PASS. Independently reconstructed all 60 primary decisions and joins, all 12 recurrence cells, the gate, and first-review/input hashes. Primary labels remain 12 yes, 36 no, 5 uncertain, 7 unscorable; 53 captures are complete.", "", "The following case-specific classification is post hoc and does not replace the frozen generic primary outcome.", "", "| Type | Count | Response IDs |", "| --- | ---: | --- |"]
    lines += [f"| {name.replace('_', ' ')} | {len(ids)} | {', '.join(ids)} |" for name, ids in partition.items()]
    lines += ["", "The narrow resource-fit subset is eight: seven WMT source-period cases plus the Q40 SVAMP construct mismatch. The four remaining positives concern other error types.", "", "Excluding mixed WMT endorsement Q46 from positive numerators leaves 11 positives, including six WMT and seven narrow resource-fit positives. This is a sensitivity result only: original labels, all planned cells, completion and scorable statuses remain unchanged.", "", "| WMT configuration | Planned / complete / scorable | Original target count | Without Q46 | Original flag | Sensitivity flag |", "| --- | --- | ---: | ---: | --- | --- |"]
    lines += [f"| {c['requested_model']} | {c['planned']} / {c['complete']} / {c['scorable']} | {c['original_verified_target']} | {c['sensitivity_verified_target']} | {c['original_flag']} | {c['sensitivity_flag']} |" for c in wmt_cells]
    lines += ["", "Gemma and DeepSeek retain their WMT two-of-three flags. Exact PAWS-to-directional-NLI positives remain zero among ten complete role responses (12 attempted). The consequence gate fails and the recorded consequence model-call count is zero; prepared methods were not executed.", "", "Fresh fact-audit and WSC witness hashes match adjudication attachments. The final summary binds that current adjudication hash. Original first-review SHA256 values match the freeze and their saved committed Git blobs. This audit checks saved Git readbacks rather than making a new network query.", "", f"Summary SHA256: `{digest(summary_path)}`. First-review commit: `{args.first_review_commit}`.", "", "Reproduce with `python path/to/audit_scope_sensitivity.py WAVE_ROOT`; in the published experiment, run `python methods/audit_scope_sensitivity.py .`. Both study/ and flat experiment layouts are supported. Historical path strings in consequence status remain metadata; the summary binding is checked by hash. No inference calls or Git writes are performed. Counts describe these curated cases; no prevalence or immutable-weight claim follows."]
    (root / "scope_sensitivity_audit.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"audit_status": "PASS", "primary_yes": 12, "narrow_resource_fit": 8, "q46_excluded_positive_count": 11, "q46_excluded_wmt_count": 6, "exact_paws_positives": exact_role, "consequence_calls": 0}))


if __name__ == "__main__":
    main()
