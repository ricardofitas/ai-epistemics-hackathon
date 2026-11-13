#!/usr/bin/env python3
"""Analyze a separately frozen local NLI WSC→HANS cohort.

The source-derived labels are never sent to classifiers by this script. This
is a selected exploratory recast, not official three-way WSC gold.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import statistics

LABELS = {"entailment", "contradiction", "neutral"}
ROLES = ("selection", "confirmation")
EXPECTED = {"selection": 35, "confirmation": 37}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def percentile(sorted_values, p):
    require(sorted_values, "Empty bootstrap distribution")
    position = p * (len(sorted_values) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def interval(values):
    ordered = sorted(values)
    return [percentile(ordered, .025), percentile(ordered, .975)]


def cluster_bootstrap(rows, group_field, model_names, metric, repeats, seed,
                      difference=None):
    """Jointly resample clusters, preserving paired candidate comparisons."""
    groups = defaultdict(list)
    for row in rows:
        groups[row[group_field]].append(row)
    keys = sorted(groups)
    require(keys and repeats > 0, "No bootstrap clusters or repeats")
    rng = random.Random(seed)
    draws = {m: [] for m in model_names}
    contrast = [] if difference else None
    for _ in range(repeats):
        selected = [groups[keys[rng.randrange(len(keys))]]
                    for _ in keys]
        sample = list(itertools.chain.from_iterable(selected))
        means = {m: sum(row[metric][m] for row in sample) / len(sample)
                 for m in model_names}
        for m in model_names:
            draws[m].append(means[m])
        if difference:
            contrast.append(means[difference[0]] - means[difference[1]])
    return {
        "cluster_count": len(keys),
        "repeats": repeats,
        "model_intervals95": {m: interval(draws[m]) for m in model_names},
        "fixed_winner_difference_interval95": interval(contrast) if difference else None,
    }


def label_from_logits(logits, label_map):
    """Mirror runner's float32 argmax rule, including lowest-index ties."""
    return label_map[str(max(range(3), key=lambda index: logits[index]))]


def load_predictions(directory, protocol, task_ids):
    out = {}
    pred_dir = directory / "predictions"
    protocol_hash = sha(directory / "protocol.json")
    source_receipt_hash = sha(directory / "source_receipt.json")
    for model in protocol["models"]:
        slug = model["slug"]
        path = pred_dir / (slug + ".jsonl")
        receipt_path = pred_dir / (slug + ".receipt.json")
        require(path.exists() and receipt_path.exists(),
                "Missing predictions or receipt for " + slug)
        receipt = read(receipt_path)
        require(receipt.get("status") == "complete", "Run not complete: " + slug)
        require(receipt.get("predictions_sha256") == sha(path),
                "Prediction hash mismatch: " + slug)
        require(receipt.get("model_id") == model["id"] and
                receipt.get("revision") == model["revision"] and
                receipt.get("slug") == slug,
                "Model provenance mismatch: " + slug)
        require(receipt.get("protocol_sha256") == protocol_hash and
                receipt.get("source_receipt_sha256") == source_receipt_hash,
                "Protocol or source receipt hash mismatch: " + slug)
        require(type(receipt.get("rows")) is int and receipt["rows"] == 224,
                "Prediction receipt row count mismatch: " + slug)
        label_map = receipt.get("label_map")
        require(isinstance(label_map, dict) and
                set(label_map) == {"0", "1", "2"} and
                set(label_map.values()) == LABELS,
                "Invalid index-to-label receipt map: " + slug)
        rows = [json.loads(line) for line in path.read_text().splitlines()
                if line.strip()]
        found = {}
        for row in rows:
            task = row.get("task_id")
            require(isinstance(task, str) and task not in found,
                    "Invalid/repeated task ID for " + slug)
            require(row.get("label") in LABELS,
                    "Invalid class label: " + slug + "/" + str(task))
            logits = row.get("logits")
            require(isinstance(logits, list) and len(logits) == 3 and
                    all(type(x) in (int, float) and math.isfinite(x) for x in logits),
                    "Invalid raw logits: " + slug + "/" + str(task))
            require(row["label"] == label_from_logits(logits, label_map),
                    "Label/logit argmax mismatch: " + slug + "/" + str(task))
            found[task] = row
        require(set(found) == task_ids and len(rows) == 224,
                "Incomplete or unexpected task set for " + slug)
        out[slug] = found
    return out


def pairwise_orderings(names, scores):
    rows = []
    for a, b in itertools.combinations(names, 2):
        imposed = scores[a]["imposed"] - scores[b]["imposed"]
        repaired = scores[a]["repaired"] - scores[b]["repaired"]
        rows.append({
            "model_a": a, "model_b": b,
            "imposed_count_difference": imposed,
            "repaired_count_difference": repaired,
            "strict_reversal": imposed * repaired < 0,
            "imposed_tie": imposed == 0,
            "repaired_tie": repaired == 0,
        })
    return rows


def winners(names, scores, metric):
    top = max(scores[name][metric] for name in names)
    return [name for name in names if scores[name][metric] == top]


def analyze(directory):
    protocol_path = directory / "protocol.json"
    protocol = read(protocol_path)
    source_receipt_path = directory / "source_receipt.json"
    source_receipt = read(source_receipt_path)
    require(source_receipt.get("status") == "source_only_no_inference" and
            source_receipt.get("protocol_sha256") == sha(protocol_path) and
            source_receipt.get("source_sha256") == protocol["source_sha256"],
            "Source receipt and pinned protocol mismatch")
    root = directory.parent
    for relative, expected_hash in protocol["source_sha256"].items():
        path = (directory / relative).resolve()
        require(path.is_file() and sha(path) == expected_hash,
                "Source pin failed: " + relative)
    wsc = read(root / "wsc/selected_data.json")["items"]
    wsc_key = read(root / "wsc/task_key.json")["rows"]
    hans = read(root / "hans_target/selected_data.json")["items"]
    hans_key = read(root / "hans_target/task_key.json")["rows"]
    require(len(wsc) == 72 and len(wsc_key) == 144 and
            len(hans) == len(hans_key) == 80, "Unexpected source allocation")
    role_counts = Counter(item["analysis_role"] for item in wsc)
    require(role_counts == EXPECTED, "Unexpected WSC split")
    task_ids = {row["task_id"] for row in wsc_key + hans_key}
    require(len(task_ids) == 224, "Duplicate task IDs in source")
    by_passage = defaultdict(dict)
    for row in wsc_key:
        require(row["variant"] in ("gold", "non_gold"), "Unexpected WSC variant")
        by_passage[row["passage_id"]][row["variant"]] = row["task_id"]
    require(len(by_passage) == 72 and all(set(v) == {"gold", "non_gold"}
                                         for v in by_passage.values()),
            "WSC pair linkage failed")
    by_hans = {row["task_id"]: row for row in hans}
    require(len(by_hans) == 80 and set(by_hans) == {
        row["task_id"] for row in hans_key}, "HANS key mismatch")
    hans_template_gold_counts = Counter(
        (item["template"], item["gold_binary"], item["heuristic"])
        for item in hans)
    require(hans_template_gold_counts == {
        ("temp1", "non-entailment", "lexical_overlap"): 40,
        ("temp35", "entailment", "lexical_overlap"): 20,
        ("temp36", "entailment", "lexical_overlap"): 20,
    }, "Unexpected HANS template/label allocation")

    predictions = load_predictions(directory, protocol, task_ids)
    names = [m["slug"] for m in protocol["models"]]
    require(len(names) == len(set(names)) == 4, "Expected four fixed candidates")
    passage_rows = []
    for item in wsc:
        pair = by_passage[item["passage_id"]]
        row = {k: item[k] for k in ("passage_id", "family_id", "analysis_role")}
        row["imposed"] = {}
        row["repaired"] = {}
        row["distortion"] = {}
        for m in names:
            positive = predictions[m][pair["gold"]]["label"]
            negative = predictions[m][pair["non_gold"]]["label"]
            imposed = int(positive == "entailment" and negative == "contradiction")
            repaired = int(positive == "entailment" and negative != "entailment")
            row["imposed"][m] = imposed
            row["repaired"][m] = repaired
            row["distortion"][m] = repaired - imposed
            require(row["distortion"][m] in (0, 1), "Non-monotone scoring")
        passage_rows.append(row)

    scores = {}
    for role in ROLES:
        subset = [r for r in passage_rows if r["analysis_role"] == role]
        scores[role] = {
            m: {metric: sum(r[metric][m] for r in subset)
                for metric in ("imposed", "repaired", "distortion")}
            for m in names
        }
    selected_i = winners(names, scores["selection"], "imposed")
    selected_r = winners(names, scores["selection"], "repaired")
    unique = len(selected_i) == len(selected_r) == 1
    different_selection_winners = unique and selected_i[0] != selected_r[0]
    winner_diff = (selected_r[0], selected_i[0]) if unique else None
    confirmation_delta = None
    if unique:
        confirmation_delta = (
            scores["confirmation"][selected_r[0]]["repaired"] -
            scores["confirmation"][selected_i[0]]["repaired"]
        ) / EXPECTED["confirmation"]

    # HANS supplies official binary labels, not a three-way neutral/contradiction gold.
    hans_rows = []
    for item in hans:
        row = {"task_id": item["task_id"], "template": item["template"],
               "subcase": item["subcase"], "heuristic": item["heuristic"],
               "binary_correct": {}}
        gold = item["gold_binary"].replace("-", "_")
        require(gold in ("entailment", "non_entailment"), "Unknown HANS gold")
        for m in names:
            predicted = ("entailment" if predictions[m][item["task_id"]]["label"]
                         == "entailment" else "non_entailment")
            row["binary_correct"][m] = int(predicted == gold)
        hans_rows.append(row)
    hans_accuracy = {m: sum(row["binary_correct"][m] for row in hans_rows) / 80
                     for m in names}
    hans_delta = (hans_accuracy[selected_r[0]] - hans_accuracy[selected_i[0]]
                  if unique else None)

    bootstrap_config = protocol["bootstrap"]
    require(isinstance(bootstrap_config, dict) and
            type(bootstrap_config.get("repeats")) is int and
            bootstrap_config["repeats"] == 10000 and
            type(bootstrap_config.get("seed")) is int and
            bootstrap_config["seed"] >= 0 and
            bootstrap_config["seed"] == protocol["scoring"]["bootstrap_seed"],
            "Invalid or inconsistent pinned bootstrap repeats/seed")
    repeats = bootstrap_config["repeats"]
    seed = bootstrap_config["seed"]
    bootstrap = {}
    for offset, role in enumerate(ROLES):
        subset = [r for r in passage_rows if r["analysis_role"] == role]
        bootstrap[role] = {
            metric: cluster_bootstrap(subset, "family_id", names, metric,
                                      repeats, seed + offset * 100 + k,
                                      difference=winner_diff if role == "confirmation"
                                      and metric == "repaired" else None)
            for k, metric in enumerate(("imposed", "repaired", "distortion"))
        }
    bootstrap["hans"] = cluster_bootstrap(
        hans_rows, "template", names, "binary_correct", repeats, seed + 300,
        difference=winner_diff)
    summary = {
        "status": "complete_exploratory_local_model_cohort",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "protocol_sha256": sha(protocol_path),
        "models": names,
        "source": {"wsc_passages": len(wsc), "wsc_source_families": len({
            r["family_id"] for r in wsc}), "selection_passages": 35,
            "confirmation_passages": 37, "hans_examples": 80,
            "predictions_per_model": 224},
        "scores": scores,
        "selection_pairwise_orderings": pairwise_orderings(names, scores["selection"]),
        "selection_imposed_winners": selected_i,
        "selection_repaired_winners": selected_r,
        "unique_winners_both_rules": unique,
        "different_selection_winners": different_selection_winners,
        "strict_selection_pairwise_reversals": sum(
            r["strict_reversal"] for r in pairwise_orderings(names, scores["selection"])),
        "confirmation_repaired_selected_minus_imposed_selected_accuracy": confirmation_delta,
        "hans_binary_accuracy": hans_accuracy,
        "hans_repaired_selected_minus_imposed_selected_accuracy": hans_delta,
        "hans_template_gold_counts": {
            f"{template}|{gold}": count
            for (template, gold, _), count in sorted(hans_template_gold_counts.items())
        },
        "hans_design_limitation": "HANS80 includes only lexical_overlap and three "
                                  "template clusters: temp1 has 40 non-entailment "
                                  "items, while temp35 and temp36 have 20 entailment "
                                  "items each. Gold is confounded with template; "
                                  "the three-cluster bootstrap interval is descriptive "
                                  "and fragile, not robust evidence of generalization.",
        "bootstrap": bootstrap,
        "scope": "Separate local public-classifier cohort; not Adaption replication. "
                 "Curated WSC binary recast conditional on intended coreference, "
                 "human NLI gold pending. HANS is independent examples, but "
                 "pretraining absence is unproved. Winner comparison is a raw-score "
                 "abstraction, not the complete original statistical/macro-F1 advice.",
    }
    output = directory / "analysis"
    require(not output.exists(), "Analysis output already exists; refuse overwrite")
    output.mkdir()
    (output / "passage_scores.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in passage_rows))
    (output / "hans_scores.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in hans_rows))
    summary["passage_scores_sha256"] = sha(output / "passage_scores.jsonl")
    summary["hans_scores_sha256"] = sha(output / "hans_scores.jsonl")
    write(output / "summary.json", summary)
    print(json.dumps({"analysis_dir": str(output),
                      "selection_imposed_winners": selected_i,
                      "selection_repaired_winners": selected_r,
                      "confirmation_delta": confirmation_delta,
                      "hans_delta": hans_delta}))


def self_test():
    sample = [0.0, 1.0, 2.0, 3.0]
    require(percentile(sample, .5) == 1.5, "Quantile interpolation")
    names = ["a", "b"]
    x = {"a": {"imposed": 2, "repaired": 3},
         "b": {"imposed": 3, "repaired": 2}}
    require(pairwise_orderings(names, x)[0]["strict_reversal"], "Reversal fixture")
    x["a"]["repaired"] = 2
    require(pairwise_orderings(names, x)[0]["repaired_tie"], "Tie fixture")
    rows = [{"family_id": "f1", "score": {"a": 1, "b": 0}},
            {"family_id": "f2", "score": {"a": 0, "b": 1}}]
    a = cluster_bootstrap(rows, "family_id", names, "score", 100, 9,
                          difference=("a", "b"))
    b = cluster_bootstrap(rows, "family_id", names, "score", 100, 9,
                          difference=("a", "b"))
    require(a == b and a["cluster_count"] == 2, "Shared seeded bootstrap fixture")
    mapping = {"0": "contradiction", "1": "entailment", "2": "neutral"}
    require(label_from_logits([1.0, 1.0, -1.0], mapping) == "contradiction",
            "Lowest-index argmax tie fixture")
    return {"status": "pass", "checks": 5}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test()))
    else:
        analyze(args.directory.resolve())


if __name__ == "__main__":
    main()
