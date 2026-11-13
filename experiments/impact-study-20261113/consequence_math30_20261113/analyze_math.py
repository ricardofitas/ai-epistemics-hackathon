#!/usr/bin/env python3
"""Analyze a frozen, source-validated math benchmark-choice consequence pilot.

Unknown capture/format outcomes remain [0,1]. Both selectors use the same
family-mean correctness metric over two variants. Resampling is descriptive,
paired and conditional on the fixed observed choices, never a missing-value
imputation or a general population confidence guarantee.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random

VARIANTS = ("numeric", "paraphrase", "p1", "p2")
ROLES = ("selection", "confirmation")
POLICIES = {"bad": ("p1", "p2"), "corrected": ("numeric", "paraphrase")}
EXPECTED_MODELS = ("gemma-4-31b-it", "deepseek-v4-flash")
COHORT = {"families": 30, "selection": 15, "confirmation": 15,
          "variants_per_family": 4, "models": 2, "batch_size": 3,
          "requests": 80, "classifications": 240, "unique_items": 120,
          "blocks_per_split": 5}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as out:
        json.dump(value, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write("\n")


def bounds(values):
    require(values, "Empty metric")
    low = sum(v[0] for v in values) / len(values)
    high = sum(v[1] for v in values) / len(values)
    return {"lower": low, "upper": high,
            "point": low if low == high else None,
            "known": sum(a == b for a, b in values), "n": len(values)}


def joint_bounds(values):
    require(values, "Empty joint endpoint")
    return [math.prod(v[0] for v in values), math.prod(v[1] for v in values)]


def winner(scores, names):
    """Keep exact raw ties and permit a missing-data choice only if identified."""
    fully_known = all(scores[m]["lower"] == scores[m]["upper"] for m in names)
    point_winners = None
    if fully_known:
        top = max(scores[m]["lower"] for m in names)
        point_winners = [m for m in names if scores[m]["lower"] == top]
    separated = [m for m in names
                 if all(scores[m]["lower"] > scores[n]["upper"]
                        for n in names if n != m)]
    require(len(separated) <= 1, "Inconsistent score bounds")
    selected = separated[0] if separated else None
    return {"fully_known_scores": fully_known, "point_winners": point_winners,
            "unique_point_winner": point_winners[0] if point_winners and
                len(point_winners) == 1 else None,
            "robust_unique_winner": selected, "selected_winner": selected,
            "choice_basis": ("complete_unique_raw_maximum" if fully_known else
                              "strictly_separated_conservative_bounds") if selected else
                             ("tie" if fully_known else "unidentified_with_unknowns")}


def contrast_bounds(a, b, same=False):
    if same:
        return [0.0, 0.0]
    return [a[0] - b[1], a[1] - b[0]]


def percentile(values, p):
    require(values, "Empty bootstrap distribution")
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] * (hi - index) + ordered[hi] * (index - lo) if lo != hi else ordered[lo]


def bootstrap(rows, names, metric, repeats, seed, unit, difference=None):
    """Joint draws preserve candidate pairing; missing values yield an envelope."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["family_id"] if unit == "family" else row["batch_block"]].append(row)
    keys = sorted(groups, key=str)
    require(keys and repeats > 0, "No bootstrap units")
    rng = random.Random(seed)
    low = {m: [] for m in names}
    high = {m: [] for m in names}
    dl, dh = [], []
    for _ in range(repeats):
        sample = list(itertools.chain.from_iterable(
            groups[keys[rng.randrange(len(keys))]] for _ in keys))
        means = {m: [sum(r[metric][m][k] for r in sample) / len(sample)
                     for k in (0, 1)] for m in names}
        for m in names:
            low[m].append(means[m][0]); high[m].append(means[m][1])
        if difference:
            a, b = difference
            d = contrast_bounds(means[a], means[b], same=a == b)
            dl.append(d[0]); dh.append(d[1])
    all_known = {m: all(r[metric][m][0] == r[metric][m][1] for r in rows)
                 for m in names}
    envelope = {m: [percentile(low[m], .025), percentile(high[m], .975)] for m in names}
    result = {"unit": unit, "unit_count": len(keys), "repeats": repeats, "seed": seed,
              "model_bound_envelopes95": envelope,
              "model_point_intervals95": {m: envelope[m] if all_known[m] else None
                                           for m in names},
              "fixed_winner_difference_bound_envelope95":
                  [percentile(dl, .025), percentile(dh, .975)] if difference else None,
              "fixed_winner_difference_point_interval95": None,
              "scope": "Conditional descriptive resampling of this fixed source sample; "
                       "fixed observed winners, no missing-value imputation. Bound envelopes "
                       "cover the retained unknown outcomes, not calibrated population inference."}
    if difference and (difference[0] == difference[1] or
                       all(all_known[m] for m in difference)):
        result["fixed_winner_difference_point_interval95"] = result[
            "fixed_winner_difference_bound_envelope95"]
    if unit == "batch_block":
        result["small_cluster_warning"] = (
            "Only five co-batched family blocks per split; "
            "this sensitivity is fragile and does not establish generalization.")
    return result


def validate_sources(directory):
    protocol = load(directory / "protocol.json")
    if "allocation" in protocol:
        fields = ("families", "selection", "confirmation", "variants_per_family",
                  "models", "batch_size", "requests", "classifications")
        require(all(protocol["allocation"].get(k) == COHORT[k] for k in fields),
                "Allocation differs from the fixed 30-family cohort")
    pins = protocol["source_sha256"]
    require({"selected_data.json", "task_key.json", "manifest.jsonl"} <= set(pins),
            "Required source pins absent")
    for relative, expected in pins.items():
        path = (directory / relative).resolve()
        require(path.is_file() and sha(path) == expected, "Source hash mismatch: " + relative)
    for relative, expected in protocol.get("implementation_sha256", {}).items():
        path = (directory / relative).resolve()
        require(path.is_file() and sha(path) == expected,
                "Implementation hash mismatch: " + relative)
    names = protocol["models"]
    require(isinstance(names, list) and len(names) == 2 and
            set(names) == set(EXPECTED_MODELS), "Changed candidate set")
    if "admission" in protocol:
        admission = directory / "admission"
        require("admission/manifest.jsonl" in pins,
                "Admission manifest must be source-pinned")
        gate = load(admission / "GATE.json")
        controls = jsonl(admission / "manifest.jsonl")
        require(len(controls) == 2 and len({r["trial_id"] for r in controls}) == 2 and
                {r["requested_model"] for r in controls} == set(names),
                "Expected one fixed format-only control per candidate")
        require(all(len(r.get("item_ids", [])) == 3 and
                    set(r["item_ids"]) == {"A001", "A002", "A003"} for r in controls),
                "Expected three fixed nonstudy admission items per request")
        reports = gate.get("rows", [])
        require(gate.get("status") == "pass" and gate.get("gate_passed") is True and
                gate.get("protocol_sha256") == sha(directory / "protocol.json") and
                gate.get("manifest_sha256") == sha(admission / "manifest.jsonl") and
                gate.get("planned_requests") == 2 and
                gate.get("arithmetic_correctness_checked") is False,
                "Format-only admission did not pass or provenance differs")
        require(isinstance(reports, list) and len(reports) == 2 and
                {r.get("trial_id") for r in reports} == {r["trial_id"] for r in controls},
                "Admission report IDs differ from fixed controls")
        for row in reports:
            require(row.get("capture_complete") is True and row.get("format_valid") is True and
                    row.get("arithmetic_correctness_checked") is False,
                    "Admission requires complete formatted controls without correctness selection")
            tid = row["trial_id"]
            for folder, suffix, field in (("api_artifacts", ".json", "artifact_sha256"),
                                          ("stream_journals", ".jsonl", "journal_sha256")):
                evidence = admission / folder / (tid + suffix)
                require(evidence.is_file() and row.get(field) == sha(evidence),
                        "Admission capture hash mismatch: " + tid)
    selected = load(directory / "selected_data.json")["families"]
    require(len(selected) == COHORT["families"] and
            len({f["source_family_id"] for f in selected}) == COHORT["families"],
            "Expected 30 unique source families")
    require(Counter(f["analysis_role"] for f in selected) ==
            {role: COHORT[role] for role in ROLES}, "Changed source split")
    family = {f["source_family_id"]: f for f in selected}
    for f in selected:
        require(len(f["variants"]) == 4 and {v["variant"] for v in f["variants"]} == set(VARIANTS),
                "Changed variant set")
    keys = load(directory / "task_key.json")["rows"]
    require(len(keys) == COHORT["unique_items"] and
            len({r["task_id"] for r in keys}) == COHORT["unique_items"],
            "Expected 120 unique tasks")
    tasks = {r["task_id"]: r for r in keys}
    require(len({(r["family_id"], r["variant"]) for r in keys}) == COHORT["unique_items"],
            "Duplicated family/variant task")
    for r in keys:
        require(r["family_id"] in family and r["variant"] in VARIANTS,
                "Unknown source task linkage")
        f = family[r["family_id"]]
        variant = next(v for v in f["variants"] if v["variant"] == r["variant"])
        require(r["analysis_role"] == f["analysis_role"] and
                r["batch_block"] == f["batch_block"] and
                str(r["gold_answer"]) == str(variant["gold_answer"]),
                "Source task fields differ")
    for role in ROLES:
        block_sizes = Counter(str(f["batch_block"]) for f in selected if f["analysis_role"] == role)
        require(len(block_sizes) == COHORT["blocks_per_split"] and
                set(block_sizes.values()) == {COHORT["batch_size"]},
                "Expected five co-batch blocks of three families per split")
    manifest = jsonl(directory / "manifest.jsonl")
    require(len(manifest) == COHORT["requests"] and
            len({r["trial_id"] for r in manifest}) == COHORT["requests"],
            "Expected exactly 80 frozen requests")
    seen = Counter()
    for row in manifest:
        require(row["requested_model"] in names and
                row["request_payload"]["model"] == row["requested_model"],
                "Unexpected request model")
        ids = row["item_ids"]
        require(len(ids) == len(set(ids)) == COHORT["batch_size"] and set(ids) <= set(tasks),
                "Invalid three-item batch")
        linked = [tasks[i] for i in ids]
        require(len({r["family_id"] for r in linked}) == COHORT["batch_size"],
                "Related variants share a request")
        for field in ("analysis_role", "variant", "batch_block"):
            require(all(r[field] == row[field] for r in linked),
                    "Mixed split/variant/block request")
        seen.update((row["requested_model"], tid) for tid in ids)
    require(set(seen.values()) == {1} and set(seen) ==
            set(itertools.product(names, tasks)), "Missing or repeated candidate task")
    return protocol, names, selected, tasks


def validate_predictions(directory, protocol, names, tasks):
    path = directory / "prediction_rows.jsonl"
    integrity = load(directory / "capture_integrity.json")
    require(integrity.get("status") == "capture_verified" and
            integrity.get("protocol_sha256") == sha(directory / "protocol.json") and
            integrity.get("manifest_sha256") == sha(directory / "manifest.jsonl") and
            integrity.get("prediction_rows_sha256") == sha(path),
            "Prediction capture provenance mismatch")
    require(integrity.get("planned_requests") == COHORT["requests"] and
            integrity.get("predictions") == COHORT["classifications"],
            "Capture allocation differs")
    rows = jsonl(path)
    require(len(rows) == COHORT["classifications"], "Expected 240 candidate-task predictions")
    scoring = None
    if "scoring.py" in protocol.get("implementation_sha256", {}):
        spec = importlib.util.spec_from_file_location("frozen_math_score_check", directory / "scoring.py")
        scoring = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scoring)
    found = {}
    for row in rows:
        key = row.get("model"), row.get("task_id")
        require(key[0] in names and key[1] in tasks and key not in found,
                "Unexpected or repeated candidate-task prediction")
        a, b = row.get("score_lower"), row.get("score_upper")
        require(type(a) in (int, float) and type(b) in (int, float) and
                a in (0, 1) and b in (0, 1) and a <= b,
                "Invalid item correctness bounds")
        require(type(row.get("capture_complete")) is bool and
                type(row.get("format_valid")) is bool, "Missing capture/format validity")
        label = row.get("label")
        require(label in {"valid", "wrong", "unknown", "abstain"}, "Unknown scoring label")
        if label in {"valid", "wrong", "abstain"}:
            require(row["capture_complete"] and row["format_valid"],
                    "A known score requires complete valid capture/format")
            require((a, b) == ((1, 1) if label == "valid" else (0, 0)),
                    "Correctness label and score disagree")
        require(isinstance(row.get("parsed_answer"), str) if label in {"valid", "wrong"}
                else row.get("parsed_answer") is None, "Parsed answer and label disagree")
        if not row["capture_complete"] or not row["format_valid"] or row.get("label") == "unknown":
            require((a, b) == (0, 1), "Unknown item was imputed")
        if label == "unknown":
            require(row["format_valid"] is False, "Unknown answer cannot have valid numeric format")
        if row.get("label") == "abstain":
            require((a, b) == (0, 0), "Explicit abstention must score zero")
        if scoring is not None:
            require("raw_answer" in row, "Actual pinned codec requires retained raw answer")
            expected = scoring.score_answer(row["raw_answer"], tasks[key[1]]["gold_answer"])
            if not row["capture_complete"]:
                expected = {"label": "unknown", "parsed_answer": None,
                            "score_lower": 0, "score_upper": 1, "format_valid": False}
            require(all(row.get(k) == v for k, v in expected.items()),
                    "Prediction differs from frozen answer-codec replay")
        found[key] = row
    require(set(found) == set(itertools.product(names, tasks)), "Missing predictions")
    return found, integrity


def analyze(directory):
    protocol, names, selected, tasks = validate_sources(directory)
    prediction, integrity = validate_predictions(directory, protocol, names, tasks)
    repeats, seed = protocol["bootstrap"]["repeats"], protocol["bootstrap"]["seed"]
    require(type(repeats) is int and repeats == 10000 and type(seed) is int,
            "Unexpected bootstrap pins")
    task_by_family = {(r["family_id"], r["variant"]): tid for tid, r in tasks.items()}
    rows = []
    for family in selected:
        fid = family["source_family_id"]
        row = {"family_id": fid, "analysis_role": family["analysis_role"],
               "batch_block": family["batch_block"], "variants": {}}
        for variant in VARIANTS:
            row["variants"][variant] = {
                m: [prediction[m, task_by_family[fid, variant]]["score_lower"],
                    prediction[m, task_by_family[fid, variant]]["score_upper"]]
                for m in names}
        for policy, variants in POLICIES.items():
            row[policy] = {m: [sum(row["variants"][v][m][k] for v in variants) / 2
                               for k in (0, 1)] for m in names}
        row["joint_target"] = {m: joint_bounds([row["variants"][v][m]
                                               for v in POLICIES["corrected"]]) for m in names}
        rows.append(row)
    scores, resampling = {}, {}
    for offset, role in enumerate(ROLES):
        subset = [r for r in rows if r["analysis_role"] == role]
        scores[role] = {metric: {m: bounds([r[metric][m] for r in subset]) for m in names}
                        for metric in ("bad", "corrected", "joint_target")}
        scores[role]["per_variant"] = {
            v: {m: bounds([r["variants"][v][m] for r in subset]) for m in names}
            for v in VARIANTS}
    choices = {policy: winner(scores["selection"][policy], names) for policy in POLICIES}
    pair_order = {"model_a": names[0], "model_b": names[1]}
    for policy in POLICIES:
        a, b = scores["selection"][policy][names[0]], scores["selection"][policy][names[1]]
        d = contrast_bounds([a["lower"], a["upper"]], [b["lower"], b["upper"]])
        pair_order[policy + "_difference_bounds"] = d
        pair_order[policy + "_point_difference"] = d[0] if d[0] == d[1] else None
        pair_order[policy + "_point_tie"] = d == [0, 0]
    bd, cd = pair_order["bad_point_difference"], pair_order["corrected_point_difference"]
    pair_order["strict_point_ordering_reversal"] = (
        bd * cd < 0 if bd is not None and cd is not None else None)
    bl, bh = pair_order["bad_difference_bounds"]
    cl, ch = pair_order["corrected_difference_bounds"]
    pair_order["ordering_reversal_identified_by_bounds"] = (
        (bl > 0 and ch < 0) or (bh < 0 and cl > 0))
    bad, corrected = choices["bad"]["selected_winner"], choices["corrected"]["selected_winner"]
    pair = (corrected, bad) if corrected and bad else None
    confirmation = {"identified_choices_both_policies": pair is not None,
                    "different_selected_candidates": corrected != bad if pair else None,
                    "repaired_selected_minus_bad_selected_mean_accuracy_bounds": None,
                    "repaired_selected_minus_bad_selected_mean_accuracy_point": None,
                    "joint_target_difference_bounds": None,
                    "joint_target_difference_point": None}
    if pair:
        for metric, field in (("corrected", "mean_accuracy"),
                              ("joint_target", "joint_target_difference")):
            a, b = scores["confirmation"][metric][corrected], scores["confirmation"][metric][bad]
            d = contrast_bounds([a["lower"], a["upper"]], [b["lower"], b["upper"]],
                                same=corrected == bad)
            prefix = "repaired_selected_minus_bad_selected_" if metric == "corrected" else ""
            confirmation[prefix + field + "_bounds"] = d
            confirmation[prefix + field + "_point"] = d[0] if d[0] == d[1] else None
    primary_bounds = confirmation["repaired_selected_minus_bad_selected_mean_accuracy_bounds"]
    confirmation["positive_target_consequence_under_all_unknown_dispositions"] = (
        primary_bounds[0] > 0 if primary_bounds is not None else None)
    for offset, role in enumerate(ROLES):
        subset = [r for r in rows if r["analysis_role"] == role]
        resampling[role] = {}
        for k, metric in enumerate(("bad", "corrected", "joint_target")):
            difference = pair if role == "confirmation" and metric != "bad" else None
            resampling[role][metric] = {
                unit: bootstrap(subset, names, metric, repeats,
                                seed + offset * 100 + k * 10 + u, unit, difference)
                for u, unit in enumerate(("family", "batch_block"))}
    summary = {
        "status": "complete_analysis_with_conservative_unknown_bounds",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "protocol_sha256": sha(directory / "protocol.json"),
        "source_sha256": protocol["source_sha256"],
        "prediction_rows_sha256": sha(directory / "prediction_rows.jsonl"),
        "capture_integrity_sha256": sha(directory / "capture_integrity.json"),
        "models": names,
        "source": {"families": COHORT["families"],
                   "selection_families": COHORT["selection"],
                   "confirmation_families": COHORT["confirmation"],
                   "variants_per_family": COHORT["variants_per_family"],
                   "unique_items": COHORT["unique_items"],
                   "requests": COHORT["requests"],
                   "candidate_item_predictions": COHORT["classifications"],
                   "co_batch_blocks_per_split": COHORT["blocks_per_split"]},
        "capture": {"strict_complete_items": sum(r["capture_complete"] for r in prediction.values()),
                    "format_valid_items": sum(r["format_valid"] for r in prediction.values()),
                    "unknown_correctness_items": sum(r["score_lower"] != r["score_upper"]
                                                     for r in prediction.values()),
                    "label_counts": dict(Counter(r.get("label") for r in prediction.values()))},
        "score_unit": "Fraction correct in [0,1]",
        "scores": scores, "selection_choices": choices,
        "selection_pair_ordering": pair_order,
        "confirmation": confirmation, "bootstrap": resampling,
        "scope": "A prospective fixed-candidate benchmark/score-policy abstraction on one "
                 "source-validated linked-family sample. Both selectors use the same mean "
                 "correctness metric. The target has separate numeric and paraphrase items, "
                 "not their composed transformation. Missing capture/format outcomes remain "
                 "[0,1]; ties and unidentified choices are retained. Fixed observed winners "
                 "are not reselected during resampling. Five co-batch blocks per split make "
                 "block envelopes fragile. No actual user choice, full literal advice-policy "
                 "causality, pretraining absence, population prevalence or model ranking "
                 "beyond this fixed sample is established. Human source validation is pending.",
    }
    output = directory / "analysis"
    require(not output.exists(), "Analysis directory already exists; no overwrite")
    output.mkdir()
    with (output / "per_source_family.jsonl").open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    summary["per_source_family_sha256"] = sha(output / "per_source_family.jsonl")
    write(output / "summary.json", summary)
    print(json.dumps({"analysis_dir": str(output), "selection_choices": choices,
                      "confirmation": confirmation, "unknown_items":
                          summary["capture"]["unknown_correctness_items"]}))


def self_test():
    names = ["a", "b"]
    known = {"a": {"lower": .75, "upper": .75}, "b": {"lower": .5, "upper": .5}}
    require(winner(known, names)["selected_winner"] == "a", "Exact unique winner")
    tied = {"a": {"lower": .5, "upper": .5}, "b": {"lower": .5, "upper": .5}}
    require(winner(tied, names)["selected_winner"] is None and
            winner(tied, names)["point_winners"] == names, "No arbitrary tie break")
    unknown = {"a": {"lower": .5, "upper": 1}, "b": {"lower": .25, "upper": .75}}
    require(winner(unknown, names)["selected_winner"] is None, "Overlapping unknown bounds")
    separated = {"a": {"lower": .75, "upper": 1}, "b": {"lower": .25, "upper": .5}}
    require(winner(separated, names)["selected_winner"] == "a" and
            winner(separated, names)["unique_point_winner"] is None, "Identified bounded winner")
    require(joint_bounds([[0, 0], [0, 1]]) == [0, 0] and
            joint_bounds([[1, 1], [0, 1]]) == [0, 1], "Coupled joint success bounds")
    require(contrast_bounds([0, 1], [0, 1], same=True) == [0, 0], "Identical choice coupling")
    rows = [{"family_id": "f1", "batch_block": 1, "corrected": {"a": [0, 1], "b": [0, 0]}},
            {"family_id": "f2", "batch_block": 2, "corrected": {"a": [1, 1], "b": [0, 0]}}]
    a = bootstrap(rows, names, "corrected", 100, 9, "family", ("a", "b"))
    b = bootstrap(rows, names, "corrected", 100, 9, "family", ("a", "b"))
    require(a == b and a["fixed_winner_difference_point_interval95"] is None and
            a["fixed_winner_difference_bound_envelope95"][0] <= .5 and
            a["fixed_winner_difference_bound_envelope95"][1] >= 1,
            "Seeded missing-data envelope instead of complete-case inference")
    identity = bootstrap(rows, names, "corrected", 100, 9, "batch_block", ("a", "a"))
    require(identity["fixed_winner_difference_bound_envelope95"] == [0, 0] and
            identity["fixed_winner_difference_point_interval95"] == [0, 0],
            "Unknown identical-candidate contrast remains exactly zero")
    return {"status": "pass", "checks": 8}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test()))
    else:
        analyze(args.directory.resolve())


if __name__ == "__main__":
    main()
