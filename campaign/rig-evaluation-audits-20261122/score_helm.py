"""Audit HELM v1.0.0 completions against the official MMLU test keys."""
import argparse
import csv
import hashlib
import io
import itertools
import json
import math
import tarfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from fetch_helm import SUBJECTS, catalogue

LETTERS = "ABCD"
REPS = 100_000


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def questions(archive):
    official = {}
    with tarfile.open(archive) as tar:
        members = {Path(name).name: name for name in tar.getnames()}
        for subject in SUBJECTS:
            key = members[f"{subject}_test.csv"]
            table = io.TextIOWrapper(tar.extractfile(key), encoding="utf-8", newline="")
            rows = defaultdict(list)
            for index, row in enumerate(csv.reader(table)):
                assert len(row) == 6 and row[-1] in LETTERS
                rows[tuple(map(normalize, row[:5]))].append((index, row[-1]))
            official[subject] = rows
    return official


def published_scores(root, runs):
    tables = json.loads((root / "published.json").read_text())
    by_run = {name: pair for pair, name in runs.items()}
    full, means, labels = {}, defaultdict(dict), {}
    overall = next(table for table in tables if table["name"] == "mmlu")
    assert overall["header"][1]["value"] == "EM"
    for display, value, *_ in overall["rows"]:
        entries = [by_run[name] for name in value["run_spec_names"]]
        models = {model for model, _ in entries}
        assert len(entries) == 57 and len(models) == 1
        model = models.pop()
        assert display["value"] not in labels and model not in full
        labels[display["value"]] = model
        full[model] = value["value"]
    for table in tables:
        if table is overall:
            continue
        assert table["header"][1]["value"] == "EM"
        subject = table["name"].removeprefix("mmlu_subject:")
        for display, value, *_ in table["rows"]:
            model = labels[display["value"]]
            assert (model, subject) in runs and subject not in means[model]
            means[model][subject] = value["value"]
    assert len(full) == 22 and all(len(m) == 57 for m in means.values())
    for model, value in full.items():
        assert math.isclose(sum(means[model].values()) / 57, value, rel_tol=1e-12)
    return full, means


def archived_metric(path):
    rows = json.loads(path.read_text())
    result = {}
    for row in rows:
        stats = [s for s in row["stats"] if s["name"]["name"] == "exact_match"]
        if len(stats) != 1 or stats[0]["count"] != 1:
            raise ValueError(f"Unexpected exact_match record in {path}")
        key = row["instance_id"]
        assert row["train_trial_index"] == 0 and key not in result
        value = stats[0]["sum"]
        assert value in (0, 1)
        result[key] = value
    return result


def bind(root, model, subject, official, published):
    coverage = Counter()
    path = root / model / subject
    if not all((path / file).is_file() for file in ("scenario_state.json", "per_instance_stats.json")):
        coverage["unavailable_archive"] = 1
        return {}, coverage
    metric = archived_metric(path / "per_instance_stats.json")
    coverage["archived_scores"] = len(metric)
    coverage["archived_correct"] = sum(metric.values())
    coverage["subject_em_reproduced"] = int(math.isclose(sum(metric.values()) / len(metric), published, abs_tol=1e-12))
    state = json.loads((path / "scenario_state.json").read_text())
    assert state["adapter_spec"]["model"] == model
    by_id = defaultdict(list)
    instances = Counter()
    for row in state["request_states"]:
        instance = row["instance"]
        key = instance["id"]
        instances[key] += 1
        assert instance["split"] == "test" and row["train_trial_index"] == 0
        refs = instance["references"]
        mapping = row["output_mapping"]
        choices = tuple(normalize(mapping[letter]) for letter in LETTERS)
        assert choices == tuple(normalize(ref["output"]["text"]) for ref in refs)
        binding = official.get((normalize(instance["input"]["text"]), *choices), [])
        if len(binding) != 1:
            coverage["unbound_or_ambiguous_request"] += 1
            continue
        index, official_key = binding[0]
        old_key = [letter for letter, ref in zip(LETTERS, refs) if "correct" in ref["tags"]]
        assert len(old_key) == 1
        old_key = old_key[0]
        coverage["key_mismatch"] += int(old_key != official_key)
        result = row.get("result") or {}
        options = result.get("completions") or []
        if not result.get("success") or len(options) != 1 or key not in metric:
            coverage["unavailable_completion_or_score"] += 1
            continue
        prediction = options[0]["text"].strip().upper()
        coverage["unparseable_completion"] += int(len(prediction) != 1 or prediction not in LETTERS)
        score_old = int(prediction == old_key)
        score_new = int(prediction == official_key)
        coverage["parser_vs_published_changes"] += int(score_old != metric[key])
        coverage["key_only_score_changes"] += int(score_old != score_new)
        by_id[index].append((metric[key], score_old, score_new))

    assert all(count == 1 for count in instances.values())
    coverage["archived_requests"] = len(instances)
    coverage["published_ids_without_requests"] = len(set(metric) - instances.keys())
    usable = {i: rows[0] for i, rows in by_id.items() if len(rows) == 1}
    coverage["duplicated_bindings"] = sum(len(rows) > 1 for rows in by_id.values())
    coverage["eligible_official_questions"] = sum(map(len, official.values()))
    coverage["usable"] = len(usable)
    coverage["official_questions_without_usable_response"] = coverage["eligible_official_questions"] - len(usable)
    return usable, coverage


def id_partitions(subject, source):
    ids = [index for entries in source.values() for index, _ in entries]
    by_hash = sorted(ids, key=lambda i: hashlib.sha256(f"{subject}:{i}".encode()).digest())
    return {"first_pass": set(by_hash[::2]), "assessment": set(by_hash[1::2]), "whole": set(ids)}


def order(value):
    return int(value > 1e-12) - int(value < -1e-12)


def direction(original, matched):
    first, second = order(original), order(matched)
    if first == second:
        return "unchanged" if first else "persistent_tie"
    if not first:
        return "resolved_tie"
    if not second:
        return "new_tie"
    return "reversed_first_to_second" if first > 0 else "reversed_second_to_first"


def summary_for_pair(a, b, usable, partitions, panel):
    data = []
    for subject in SUBJECTS:
        left, right = usable[a, subject], usable[b, subject]
        ids = sorted(partitions[subject][panel] & left.keys() & right.keys())
        if not ids:
            return None
        data.append(np.array([np.subtract(left[i], right[i]) for i in ids], dtype=np.int8))
    scores = np.mean([d.mean(axis=0) for d in data], axis=0) * 100
    return scores.tolist(), [len(d) for d in data], [np.bincount(d[:, 2] + 1, minlength=3) for d in data]


def bootstrap_distributions(counts, seed):
    rng = np.random.default_rng(seed)
    estimates = np.zeros(REPS)
    for count in counts:
        n = count.sum()
        draws = rng.multinomial(n, count / n, size=REPS)
        estimates += (draws[:, 2] - draws[:, 0]) / n
    return np.sort(estimates * (100 / len(SUBJECTS)))


def audit(official, root):
    runs = catalogue(root)
    published_full, published_subjects = published_scores(root, runs)
    usable, coverage = {}, {}
    models = sorted(published_full)
    for model, subject in itertools.product(models, SUBJECTS):
        usable[model, subject], coverage[model + ":" + subject] = bind(
            root, model, subject, official[subject], published_subjects[model][subject])
    partitions = {s: id_partitions(s, official[s]) for s in SUBJECTS}
    rows = []
    for index, (left, right) in enumerate(itertools.combinations(models, 2)):
        baseline = 100 * (published_full[left] - published_full[right])
        published_five = 100 * sum(published_subjects[left][s] - published_subjects[right][s]
                                   for s in SUBJECTS) / len(SUBJECTS)
        compared = {}
        for panel in ("first_pass", "assessment", "whole"):
            info = summary_for_pair(left, right, usable, partitions, panel)
            if info is not None:
                margins, n, counts = info
                distribution = bootstrap_distributions(counts, 41122 + 3 * index + len(compared))
                low, high = np.quantile(distribution, [0.025, 0.975]).tolist()
                compared[panel] = {
                    "n": n, "published_metric_margin_pp": margins[0],
                    "archived_key_strict_margin_pp": margins[1], "official_key_margin_pp": margins[2],
                    "official_bootstrap_95_pp": [low, high], "official_direction": direction(baseline, margins[2]),
                    "key_only_direction": direction(margins[1], margins[2]),
                    "parser_only_direction": direction(margins[0], margins[1]),
                    "distribution": distribution if panel == "assessment" else None,
                }
        if "whole" in compared:
            matched_margin = compared["whole"]["published_metric_margin_pp"]
            compared["whole"]["binding_only_direction"] = direction(published_five, matched_margin)
        rows.append({"first": left, "second": right, "published_full_margin_pp": baseline,
                     "published_five_margin_pp": published_five, **compared})

    selected = [r for r in rows if r.get("first_pass", {}).get("official_direction", "").startswith("reversed")]
    adjusted_alpha = 0.05 / len(selected) if selected else 0.05
    confirmed = []
    for row in rows:
        for panel in ("first_pass", "assessment", "whole"):
            if panel not in row:
                continue
            result = row[panel]
            distribution = result.pop("distribution")
            if panel == "assessment" and row in selected:
                ci = np.quantile(distribution, [adjusted_alpha / 2, 1 - adjusted_alpha / 2]).tolist()
                result["adjusted_ci_pp"] = ci
                result["confirmed_reversal"] = (
                    result["official_direction"] == row["first_pass"]["official_direction"]
                    and abs(result["official_key_margin_pp"]) > 2
                    and (order(ci[0]) == order(ci[1]) == order(result["official_key_margin_pp"])))
                if result["confirmed_reversal"]:
                    confirmed.append([row["first"], row["second"]])

    panel_names = ("first_pass", "assessment", "whole")
    return {
        "subjects": list(SUBJECTS), "eligible_models": len(models), "eligible_pairs": len(rows),
        "official_subject_sizes": {s: sum(map(len, official[s].values())) for s in SUBJECTS},
        "direction_counts": {p: Counter(row.get(p, {}).get("official_direction", "unavailable") for row in rows)
                             for p in panel_names},
        "whole_binding_only_direction": Counter(r.get("whole", {}).get("binding_only_direction", "unavailable")
                                               for r in rows),
        "whole_key_only_direction": Counter(r.get("whole", {}).get("key_only_direction", "unavailable") for r in rows),
        "whole_parser_only_direction": Counter(r.get("whole", {}).get("parser_only_direction", "unavailable") for r in rows),
        "first_pass_reversals": len(selected), "heldout_confirmed_reversals": confirmed,
        "adjusted_alpha": adjusted_alpha, "bootstrap_replicates": REPS,
        "coverage_by_model_subject": coverage, "published_full_scores": published_full,
        "comparisons": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("official_tar", type=Path)
    parser.add_argument("archive_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit(questions(args.official_tar), args.archive_directory)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
