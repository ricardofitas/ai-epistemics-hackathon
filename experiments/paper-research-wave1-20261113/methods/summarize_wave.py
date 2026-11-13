#!/usr/bin/env python3
"""Summarize two frozen independent reviews, with explicit mechanism adjudication."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

LABELS = {"yes", "no", "uncertain", "unscorable"}
FLAGS = {"yes", "no", "uncertain"}
TARGETS = {
    "open_mt_news_ende_late2019": "wrong_source_news_period",
    "NEW-HANS-ROLES": "paraphrase_score_sufficient_for_directional_entailment",
    "NEW-BEIR-COVID-RETRIEVAL-POSITIVE": "nonsignificance_implies_equivalence",
}
MECHANISMS = set(TARGETS.values()) | {"other_material"}


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index(data, expected, kind):
    result = {r["response_id"]: r for r in data}
    if len(data) != 60 or len(result) != 60 or set(result) != expected:
        raise ValueError(f"{kind} must contain exactly Q01 through Q60, once each")
    return result


def mechanism_flags(row, required=False):
    """An explicit list is exhaustive. Omitted flag-map entries remain uncertain."""
    if "mechanisms" in row and "mechanism_flags" in row:
        raise ValueError("Use mechanisms OR mechanism_flags, not both")
    if "mechanisms" in row:
        values = row["mechanisms"]
        if not isinstance(values, list) or len(values) != len(set(values)) or not set(values) <= MECHANISMS:
            raise ValueError("Invalid mechanisms: use documented exact IDs")
        return {m: "yes" if m in values else "no" for m in sorted(MECHANISMS)}
    if "mechanism_flags" in row:
        values = row["mechanism_flags"]
        if not isinstance(values, dict) or not set(values) <= MECHANISMS or not set(values.values()) <= FLAGS:
            raise ValueError("Invalid mechanism_flags")
        return {m: values.get(m, "uncertain") for m in sorted(MECHANISMS)}
    if required:
        raise ValueError("A positive recommendation-error label requires explicit mechanism coding")
    return {m: "uncertain" for m in sorted(MECHANISMS)}


def validate_review(review, packet):
    for rid, row in review.items():
        label = row.get("unsupported_recommendation")
        if label not in LABELS:
            raise ValueError(f"Invalid primary label: {rid}")
        if not packet[rid]["capture_complete"] and label != "unscorable":
            raise ValueError(f"Incomplete capture must remain unscorable: {rid}")
        excerpts = row.get("exact_supporting_passages", [])
        if not isinstance(excerpts, list) or any(not isinstance(v, str) or not v.strip() or v not in packet[rid]["response"] for v in excerpts):
            raise ValueError(f"Evidence passages must be exact nonempty response substrings: {rid}")
        if label == "yes" and not excerpts:
            raise ValueError(f"Positive label needs supporting response passage: {rid}")
        mechanism_flags(row, required=label == "yes")


def recurrence_cells(data):
    """Descriptive fixed-context heuristic; never a significance/prevalence estimate."""
    grouped = defaultdict(list)
    for row in data:
        if row["stage"] == "selected_recurrence":
            grouped[(row["case_id"], row["requested_model"])].append(row)
    result = []
    for (case, model), cell in sorted(grouped.items()):
        if case not in TARGETS or sorted(r["repetition"] for r in cell) != [1, 2, 3]:
            raise ValueError("Recurrence requires the three planned distinct contexts per case/configuration")
        target = TARGETS[case]
        complete = sum(bool(r["capture_complete"]) for r in cell)
        scorable = sum(bool(r["capture_complete"]) and r["coordinator_label"] != "unscorable" for r in cell)
        verified = sum(bool(r["capture_complete"]) and r["coordinator_label"] == "yes"
                       and r["coordinator_mechanism_flags"].get(target) == "yes" for r in cell)
        result.append({"case_id": case, "requested_model": model, "target_mechanism": target,
                       "planned": 3, "complete": complete, "scorable": scorable,
                       "material_error_yes": sum(r["coordinator_label"] == "yes" for r in cell),
                       "verified_same_mechanism": verified,
                       "two_of_three_same_mechanism": complete == 3 and scorable == 3 and verified >= 2,
                       "response_ids": [r["response_id"] for r in sorted(cell, key=lambda v: v["repetition"])]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--ratings-a", type=Path, required=True)
    parser.add_argument("--ratings-b", type=Path, required=True)
    parser.add_argument("--first-review-freeze", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    p = args.directory
    expected = {f"Q{i:02d}" for i in range(1, 61)}
    # Freeze proof is checked BEFORE loading the model/repetition key.
    freeze = load(args.first_review_freeze)
    hashes = freeze.get("first_rating_sha256", freeze.get("rating_sha256"))
    if not isinstance(hashes, dict) or hashes.get("a") != sha(args.ratings_a) or hashes.get("b") != sha(args.ratings_b):
        raise ValueError("Both original review SHA256 values must match their separate first-review freeze proof")
    if not freeze.get("frozen_utc"):
        raise ValueError("First-review freeze must record frozen_utc")
    packet = index(rows(p / "review_packet.jsonl"), expected, "Review packet")
    if freeze.get("packet_sha256") != sha(p / "review_packet.jsonl"):
        raise ValueError("First-review freeze must bind the exact review packet")
    a = index(rows(args.ratings_a), expected, "Reviewer A")
    b = index(rows(args.ratings_b), expected, "Reviewer B")
    validate_review(a, packet)
    validate_review(b, packet)
    adjudication = load(args.adjudication) if args.adjudication else {}
    dispositions = adjudication.get("coordinator_dispositions", {})
    mechanisms = adjudication.get("coordinator_mechanisms", {})
    if not isinstance(dispositions, dict) or not isinstance(mechanisms, dict) or not set(dispositions) <= expected or not set(mechanisms) <= expected:
        raise ValueError("Adjudication contains invalid response IDs")
    decisions, primary_disagreements, mechanism_disagreements = {}, [], []
    unresolved = []
    for rid in sorted(expected):
        la, lb = a[rid]["unsupported_recommendation"], b[rid]["unsupported_recommendation"]
        fa, fb = mechanism_flags(a[rid], la == "yes"), mechanism_flags(b[rid], lb == "yes")
        if la != lb:
            primary_disagreements.append(rid)
            if rid not in dispositions:
                unresolved.append(f"{rid}: primary label")
        label = dispositions.get(rid, la if la == lb else None)
        if label is not None and label not in LABELS:
            raise ValueError(f"Invalid adjudicated primary label: {rid}")
        if not packet[rid]["capture_complete"] and label != "unscorable":
            raise ValueError(f"Adjudication cannot promote an incomplete capture: {rid}")
        if fa != fb:
            mechanism_disagreements.append(rid)
        resolved_flags = fa if fa == fb else {m: fa[m] if fa[m] == fb[m] else "uncertain" for m in sorted(MECHANISMS)}
        if rid in mechanisms:
            value = mechanisms[rid]
            if isinstance(value, list):
                resolved_flags = mechanism_flags({"mechanisms": value}, True)
            elif isinstance(value, dict):
                resolved_flags = mechanism_flags({"mechanism_flags": value}, True)
            else:
                raise ValueError(f"Invalid adjudicated mechanisms: {rid}")
        elif label == "yes" and (fa != fb or la != lb):
            # A primary positive disposition alone cannot silently resolve a mechanism.
            unresolved.append(f"{rid}: mechanism disposition for positive primary label")
        decisions[rid] = {"response_id": rid, "first_labels": {"a": la, "b": lb},
                          "coordinator_label": label, "first_mechanism_flags": {"a": fa, "b": fb},
                          "coordinator_mechanism_flags": resolved_flags}
    if unresolved:
        raise ValueError("Explicit adjudication required before claims/gate: " + "; ".join(unresolved))
    # Only after the immutable first reviews and dispositions are checked is the key read.
    key = index(rows(p / "review_key.jsonl"), expected, "Review key")
    enriched_rows = rows(p / "responses_enriched.jsonl")
    enriched = {r["trial_id"]: r for r in enriched_rows}
    if len(enriched_rows) != 60 or len(enriched) != 60 or {v["trial_id"] for v in key.values()} != set(enriched):
        raise ValueError("Incomplete/duplicate enriched capture join")
    joined = []
    for rid in sorted(expected):
        raw = enriched[key[rid]["trial_id"]]
        if raw["case_id"] != packet[rid]["case_id"] or raw["response"] != packet[rid]["response"] or raw["capture_complete"] != packet[rid]["capture_complete"]:
            raise ValueError(f"Review key/capture join mismatch: {rid}")
        joined.append({**decisions[rid], "trial_id": raw["trial_id"], "case_id": raw["case_id"],
                       "stage": raw["stage"], "requested_model": raw["requested_model"],
                       "returned_model": raw.get("returned_model"), "repetition": raw["repetition"],
                       "capture_complete": raw["capture_complete"]})
    if Counter(r["stage"] for r in joined) != {"new_screen": 24, "selected_recurrence": 36}:
        raise ValueError("Invalid wave allocation")
    recurrence = recurrence_cells(joined)
    if len(recurrence) != 12:
        raise ValueError("Expected 3 recurrence cases × 4 requested configurations")
    def grouped(field):
        return {name: dict(Counter(r["coordinator_label"] for r in joined if r[field] == name))
                for name in sorted({r[field] for r in joined})}
    eligible = [c["requested_model"] for c in recurrence if c["case_id"] == "NEW-HANS-ROLES" and c["two_of_three_same_mechanism"]]
    summary = {"scope": "Only this frozen 60-attempt wave; no historical counts pooled",
               "primary_unit": "Attempted response; complete/scorable denominators reported separately",
               "attempted": 60, "capture_complete": sum(r["capture_complete"] for r in joined),
               "first_review_counts": {"a": dict(Counter(v["unsupported_recommendation"] for v in a.values())),
                                       "b": dict(Counter(v["unsupported_recommendation"] for v in b.values()))},
               "primary_disagreements": primary_disagreements,
               "mechanism_disagreements": mechanism_disagreements,
               "coordinator_counts": dict(Counter(r["coordinator_label"] for r in joined)),
               "by_case": grouped("case_id"), "by_stage": grouped("stage"),
               "by_requested_configuration": grouped("requested_model"),
               "recurrence_cells": recurrence,
               "consequence_gate": {"case_id": "NEW-HANS-ROLES", "eligible": bool(eligible),
                                    "eligible_requested_configurations": eligible,
                                    "rule": "At least one configuration with all 3 planned contexts complete/scorable and >=2 verified exact target mechanisms"},
               "interpretation": "Descriptive recurrence in three fixed sampled contexts, not a prevalence estimate or significance test. Requested and returned aliases do not establish immutable weights.",
               "human_review": "Independent first labels plus explicit coordinator dispositions; no claim of external expert validation",
               "first_review_freeze": freeze,
               "sha256": {"ratings_a": sha(args.ratings_a), "ratings_b": sha(args.ratings_b),
                          "first_review_freeze": sha(args.first_review_freeze),
                          "packet": sha(p / "review_packet.jsonl"), "key": sha(p / "review_key.jsonl"),
                          "enriched": sha(p / "responses_enriched.jsonl"),
                          "adjudication": sha(args.adjudication) if args.adjudication else None},
               "rows": joined}
    output = args.output or p / "analysis_summary.json"
    protected = {args.ratings_a.resolve(), args.ratings_b.resolve(), args.first_review_freeze.resolve(),
                 (p / "review_packet.jsonl").resolve(), (p / "review_key.jsonl").resolve(),
                 (p / "responses_enriched.jsonl").resolve()}
    if args.adjudication:
        protected.add(args.adjudication.resolve())
    if output.resolve() in protected:
        raise ValueError("Refusing to overwrite immutable/input evidence")
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}))


if __name__ == "__main__":
    main()
