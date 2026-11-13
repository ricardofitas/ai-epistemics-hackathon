#!/usr/bin/env python3
"""Analyze the frozen, source-balanced HANS600 external holdout.

This program never selects a candidate on HANS. It imports the two WSC35
winners from the separately frozen local NLI cohort, recomputes those winners
from its selection counts, and scores all four fixed candidates on HANS600.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent / "local_nli_20261113"
LABELS = {"contradiction", "entailment", "neutral"}
HEURISTICS = {"lexical_overlap", "subsequence", "constituent"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def quantile(values, fraction):
    ordered = sorted(values)
    require(bool(ordered), "Empty interval")
    position = fraction * (len(ordered) - 1)
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] * (hi - position) + ordered[hi] * (position - lo) if lo != hi else ordered[lo]


def interval(values):
    return [quantile(values, .025), quantile(values, .975)]


def read_plan(directory):
    plan = read(directory / "inference_plan.json")
    broad_protocol = read(directory / "protocol.json")
    local_protocol = read(LOCAL / "protocol.json")
    source = broad_protocol["selection"]
    require(sha(directory / "selected_data.json") == source["selected_data_sha256"],
            "Broad selected-data SHA mismatch")
    require(sha(directory / "task_key.json") == source["task_key_sha256"],
            "Broad task-key SHA mismatch")
    require(sha(directory / "protocol.json") == plan["broad_protocol_sha256"],
            "Broad source protocol differs from inference plan")
    require(sha(directory / "selected_data.json") == plan["selected_data_sha256"] and
            sha(directory / "task_key.json") == plan["task_key_sha256"],
            "Broad cases differ from inference plan")
    require(sha(LOCAL / "protocol.json") == plan["local_protocol_sha256"] and
            sha(LOCAL / "source_receipt.json") == plan["source_receipt_sha256"],
            "Local model pins differ from inference plan")
    require(plan["models"] == [m["slug"] for m in local_protocol["models"]],
            "Candidate list changed")
    require(plan["analysis"]["bootstrap"]["repeats"] == 10000 and
            plan["analysis"]["bootstrap"]["seed"] == 2026111360,
            "Unexpected bootstrap plan")
    return plan, broad_protocol, local_protocol


def source_rows(directory):
    data = read(directory / "selected_data.json")["items"]
    key = read(directory / "task_key.json")["rows"]
    require(len(data) == len(key) == 600, "Unexpected HANS600 source count")
    require([x["task_id"] for x in data] == [x["task_id"] for x in key],
            "HANS600 key order differs")
    require(all(x["source_pair_id"] == k["source_pair_id"] for x, k in zip(data, key)),
            "HANS600 pair IDs differ")
    require(len({x["task_id"] for x in data}) == 600 and
            len({x["source_pair_id"] for x in data}) == 600 and
            len({(x["premise"], x["hypothesis"]) for x in data}) == 600,
            "Repeated HANS600 source row")
    require({x["heuristic"] for x in data} == HEURISTICS and
            {x["gold_binary"] for x in data} == {"entailment", "non-entailment"},
            "Unexpected HANS600 strata")
    subcases = Counter((x["heuristic"], x["gold_binary"], x["subcase"]) for x in data)
    cells = Counter((h, g) for h, g, _ in subcases)
    require(len(subcases) == 30 and set(subcases.values()) == {20} and
            len(cells) == 6 and set(cells.values()) == {5},
            "HANS600 is not balanced across 30 subcases and 6 cells")
    return data, subcases


def load_predictions(directory, plan, source, models):
    out = {}
    pred_dir = directory / "broad_predictions"
    seen_commits = set()
    plan_hash = sha(directory / "inference_plan.json")
    broad_hash = sha(directory / "protocol.json")
    model_receipt_hash = sha(LOCAL / "source_receipt.json")
    task_ids = {x["task_id"] for x in source}
    for model in models:
        slug = model["slug"]
        file = pred_dir / f"{slug}.jsonl"
        receipt_file = pred_dir / f"{slug}.receipt.json"
        require(file.exists() and receipt_file.exists(), "Incomplete HANS600 model " + slug)
        receipt = read(receipt_file)
        require(receipt.get("status") == "complete" and receipt.get("rows") == 600 and
                receipt.get("model_id") == model["id"] and
                receipt.get("revision") == model["revision"] and
                receipt.get("slug") == slug, "Bad HANS600 model provenance: " + slug)
        require(receipt.get("predictions_sha256") == sha(file) and
                receipt.get("plan_sha256") == plan_hash and
                receipt.get("broad_protocol_sha256") == broad_hash and
                receipt.get("source_receipt_sha256") == model_receipt_hash,
                "Bad HANS600 prediction/source receipt hash: " + slug)
        require(receipt.get("model_weight_sha256") ==
                read(LOCAL / "protocol.json")["model_weight_sha256"][slug],
                "Bad HANS600 weight pin: " + slug)
        freeze_commit = receipt.get("freeze_commit")
        require(isinstance(freeze_commit, str) and len(freeze_commit) == 40 and
                all(c in "0123456789abcdef" for c in freeze_commit),
                "Invalid Git freeze commit: " + slug)
        seen_commits.add(freeze_commit)
        label_map = receipt.get("label_map")
        require(isinstance(label_map, dict) and set(label_map) == {"0", "1", "2"} and
                set(label_map.values()) == LABELS, "Invalid class map: " + slug)
        predictions = {}
        raw = [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines()
               if line.strip()]
        for row in raw:
            task_id, label, logits = row.get("task_id"), row.get("label"), row.get("logits")
            require(isinstance(task_id, str) and task_id not in predictions,
                    "Duplicate or invalid prediction ID: " + slug)
            require(label in LABELS and isinstance(logits, list) and len(logits) == 3 and
                    all(type(v) in (int, float) and math.isfinite(v) for v in logits),
                    "Invalid prediction/logits: " + slug + "/" + task_id)
            require(label == label_map[str(max(range(3), key=lambda i: logits[i]))],
                    "Prediction disagrees with argmax logits: " + slug + "/" + task_id)
            predictions[task_id] = label
        require(len(raw) == 600 and set(predictions) == task_ids,
                "Incomplete or unexpected HANS600 predictions: " + slug)
        out[slug] = predictions
    require(len(seen_commits) == 1, "Models have different Git freeze commits")
    return out, next(iter(seen_commits))


def wsc_winners(local_protocol, names, expected_summary_sha256):
    path = LOCAL / "analysis" / "summary.json"
    require(sha(path) == expected_summary_sha256,
            "Original WSC analysis hash differs from inference plan")
    summary = read(path)
    require(summary.get("status") == "complete_exploratory_local_model_cohort" and
            summary.get("protocol_sha256") == sha(LOCAL / "protocol.json") and
            summary.get("models") == names and
            summary.get("source", {}).get("selection_passages") == 35 and
            summary.get("source", {}).get("confirmation_passages") == 37,
            "Original WSC cohort incomplete or inconsistent")
    scores = summary["scores"]["selection"]
    require(set(scores) == set(names), "Unexpected WSC candidates")
    winners = {}
    for rule in ("imposed", "repaired"):
        vals = {m: scores[m][rule] for m in names}
        require(all(type(v) is int and 0 <= v <= 35 for v in vals.values()),
                "Invalid original WSC35 selection counts")
        best = max(vals.values())
        winners[rule] = [m for m in names if vals[m] == best]
        require(summary[f"selection_{rule}_winners"] == winners[rule],
                "WSC summary winner differs from recomputed maximum")
    require(summary["unique_winners_both_rules"] ==
            (len(winners["imposed"]) == len(winners["repaired"]) == 1),
            "WSC uniqueness flag mismatch")
    return winners, sha(path)


def bootstrap_subcases(subcase_rows, names, winner_pair, repeats, seed):
    """Paired stratified cluster resampling: five subcases per label/heuristic cell."""
    cells = defaultdict(list)
    for row in subcase_rows:
        cells[(row["heuristic"], row["gold_binary"])].append(row)
    require(len(cells) == 6 and all(len(v) == 5 for v in cells.values()),
            "Not five subcases in every cell")
    rng = random.Random(seed)
    samples = {m: [] for m in names}
    contrasts = [] if winner_pair else None
    for _ in range(repeats):
        draw = [v[rng.randrange(5)] for _, v in sorted(cells.items()) for _ in range(5)]
        means = {m: sum(r["accuracy"][m] for r in draw) / 30 for m in names}
        for m in names:
            samples[m].append(means[m])
        if winner_pair:
            contrasts.append(means[winner_pair[0]] - means[winner_pair[1]])
    return {"method": "paired stratified subcase-cluster percentile bootstrap",
            "subcases_per_cell": 5, "cell_count": 6, "repeats": repeats, "seed": seed,
            "model_accuracy_interval95": {m: interval(samples[m]) for m in names},
            "repaired_minus_imposed_winner_interval95":
                interval(contrasts) if winner_pair else None,
            "scope": "Descriptive conditional sensitivity to subcase resampling on fixed HANS source; not a population or pretraining-absence guarantee."}


def analyze(directory):
    plan, broad, local_protocol = read_plan(directory)
    source, strata = source_rows(directory)
    models = local_protocol["models"]
    names = [m["slug"] for m in models]
    predictions, freeze_commit = load_predictions(directory, plan, source, models)
    winners, wsc_analysis_hash = wsc_winners(local_protocol, names,
                                            plan["wsc_analysis_sha256"])
    unique = len(winners["imposed"]) == len(winners["repaired"]) == 1
    winner_pair = (winners["repaired"][0], winners["imposed"][0]) if unique else None
    rows = []
    for item in source:
        row = {k: item[k] for k in ("task_id", "source_pair_id", "heuristic", "gold_binary", "subcase", "template")}
        row["predicted"] = predictions_for_row = {m: predictions[m][item["task_id"]] for m in names}
        row["binary_correct"] = {
            m: int(("entailment" if predictions_for_row[m] == "entailment" else "non-entailment")
                   == item["gold_binary"]) for m in names}
        rows.append(row)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["heuristic"], row["gold_binary"], row["subcase"])].append(row)
    subcases = [{"heuristic": h, "gold_binary": g, "subcase": s,
                 "n": len(items),
                 "accuracy": {m: sum(x["binary_correct"][m] for x in items) / len(items)
                              for m in names}}
                for (h, g, s), items in sorted(grouped.items())]
    require(len(subcases) == 30 and all(x["n"] == 20 for x in subcases),
            "Incorrect HANS600 subcase sizes")
    accuracy = {m: statistics.mean(x["accuracy"][m] for x in subcases) for m in names}
    require(all(math.isclose(accuracy[m], sum(x["binary_correct"][m] for x in rows) / 600,
                             rel_tol=0, abs_tol=1e-12)
                for m in names), "Macro/micro equivalence failed")
    by_cell = {}
    by_heuristic = {}
    for h in sorted(HEURISTICS):
        subset = [x for x in rows if x["heuristic"] == h]
        require(len(subset) == 200, "Unexpected heuristic size")
        by_heuristic[h] = {m: sum(x["binary_correct"][m] for x in subset) / 200
                           for m in names}
        for gold in ("entailment", "non-entailment"):
            cell = [x for x in subset if x["gold_binary"] == gold]
            require(len(cell) == 100, "Unexpected heuristic-by-label size")
            by_cell[f"{h}|{gold}"] = {m: sum(x["binary_correct"][m] for x in cell) / 100
                                      for m in names}
    delta = accuracy[winner_pair[0]] - accuracy[winner_pair[1]] if unique else None
    boot = bootstrap_subcases(subcases, names, winner_pair,
                              plan["analysis"]["bootstrap"]["repeats"],
                              plan["analysis"]["bootstrap"]["seed"])
    output = directory / "broad_analysis"
    require(not output.exists(), "Broad analysis already exists; refusing overwrite")
    output.mkdir()
    cases_path = output / "case_scores.jsonl"
    cases_path.write_text("".join(json.dumps(x, ensure_ascii=False, allow_nan=False) + "\n"
                                  for x in rows), encoding="utf-8")
    (output / "subcase_scores.json").write_text(
        json.dumps(subcases, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    result = {
        "status": "complete_broad_external_holdout", "created_utc": datetime.now(timezone.utc).isoformat(),
        "inference_freeze_commit": freeze_commit,
        "inference_plan_sha256": sha(directory / "inference_plan.json"),
        "broad_source_protocol_sha256": sha(directory / "protocol.json"),
        "selected_data_sha256": sha(directory / "selected_data.json"),
        "source_receipt_sha256": sha(LOCAL / "source_receipt.json"),
        "wsc_analysis_sha256": wsc_analysis_hash,
        "models": names, "source": {"examples": 600, "subcases": 30, "templates": len({x["template"] for x in rows}),
                                      "heuristics": sorted(HEURISTICS), "label_heuristic_cells": 6,
                                      "items_per_subcase": 20},
        "wsc_selection_imposed_winners": winners["imposed"],
        "wsc_selection_repaired_winners": winners["repaired"],
        "unique_winners_both_rules": unique,
        "different_selection_winners": unique and winner_pair[0] != winner_pair[1],
        "macro30_accuracy": accuracy,
        "micro600_accuracy": accuracy,
        "heuristic_accuracy": by_heuristic,
        "heuristic_by_gold_accuracy": by_cell,
        "repaired_selected_minus_imposed_selected_accuracy": delta,
        "bootstrap": boot,
        "case_scores_sha256": sha(cases_path),
        "subcase_scores_sha256": sha(output / "subcase_scores.json"),
        "scope": "External to the WSC selection cases but drawn from the same public HANS source as HANS80; broader 30-subcase/58-template coverage. Pretraining exposure unknown and template dependence remains. The raw-count WSC choice is an abstraction of the original recommendation. No actual user decision, human-certified WSC NLI gold or general benchmark-wide claim.",
    }
    (output / "summary.json").write_text(json.dumps(result, ensure_ascii=False,
                                                     indent=2, allow_nan=False) + "\n",
                                         encoding="utf-8")
    print(json.dumps({"status": result["status"], "macro30_accuracy": accuracy,
                      "imposed": winners["imposed"], "repaired": winners["repaired"],
                      "difference": delta}))


def self_test():
    require(quantile([0, 1, 2, 3], .5) == 1.5, "Quantile test")
    require(interval([0, 0, 0]) == [0, 0], "Degenerate interval test")
    rows = []
    for h in HEURISTICS:
        for g in ("entailment", "non-entailment"):
            for i in range(5):
                rows.append({"heuristic": h, "gold_binary": g,
                             "accuracy": {"a": 1., "b": 0.}})
    b1 = bootstrap_subcases(rows, ["a", "b"], ("a", "b"), 100, 9)
    b2 = bootstrap_subcases(rows, ["a", "b"], ("a", "b"), 100, 9)
    require(b1 == b2 and b1["repaired_minus_imposed_winner_interval95"] == [1., 1.],
            "Stratified paired bootstrap test")
    return {"status": "pass", "checks": 3}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, default=HERE)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test()))
    else:
        analyze(args.directory.resolve())


if __name__ == "__main__":
    main()
