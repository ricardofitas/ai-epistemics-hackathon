"""Replay the frozen MadinahQA context-restoration crossover comparison."""
import argparse
import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from fetch_context import RELEASES, run_catalogue
from score_helm import archived_metric, direction, order

REPS = 100_000


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load_run(path):
    scores = archived_metric(path / "per_instance_stats.json")
    stats = json.loads((path / "stats.json").read_text())
    published, = [r["mean"] for r in stats if r["name"] == {"name": "exact_match", "split": "test"}]
    assert math.isclose(sum(scores.values()) / len(scores), published, abs_tol=1e-12)
    requests = {}
    state = json.loads((path / "scenario_state.json").read_text())
    for row in state["request_states"]:
        key = row["instance"]["id"]
        assert row["train_trial_index"] == 0 and row["instance"]["split"] == "test" and key not in requests
        requests[key] = row
    return requests, scores, published


def request_class(old, new):
    before, after = (r["instance"]["input"]["text"] for r in (old, new))
    if old["output_mapping"] != new["output_mapping"] or old["instance"]["references"] != new["instance"]["references"]:
        return "changed_references", None
    if before == after and old["request"] == new["request"]:
        return "identical_request", None
    suffix = "\n\n" + before
    if not after.endswith(suffix):
        return "changed_question_or_other", None
    passage = after[:-len(suffix)]
    old_request, new_request = old["request"], new["request"]
    prompt = new_request["prompt"]
    if not passage.strip() or after not in prompt or old_request != dict(new_request, prompt=prompt.replace(after, before, 1)):
        return "change_beyond_context", None
    return "context_inserted", digest(passage)


def compare_model(root, model):
    paths = [root / release / model for release in RELEASES]
    if any(not (path / name).is_file() for path in paths
           for name in ("scenario_state.json", "per_instance_stats.json", "stats.json")):
        return None, {"unavailable_archive": 1}
    (before, old_scores, old_em), (after, new_scores, new_em) = map(load_run, paths)
    coverage = Counter(before=len(before), after=len(after))
    coverage["missing_in_before"] = len(after.keys() - before.keys())
    coverage["missing_in_after"] = len(before.keys() - after.keys())
    records, controls = {}, []
    for key in sorted(before.keys() & after.keys()):
        change, passage = request_class(before[key], after[key])
        coverage[change] += 1
        if key not in old_scores or key not in new_scores:
            coverage["missing_score"] += 1
            continue
        if not all((row.get("result") or {}).get("success") for row in (before[key], after[key])):
            coverage["unavailable_completion"] += 1
            continue
        coverage[change + "_cached_before"] += int(bool(before[key]["result"].get("cached")))
        coverage[change + "_cached_after"] += int(bool(after[key]["result"].get("cached")))
        if passage is not None:
            records[key] = (passage, old_scores[key], new_scores[key])
        elif change == "identical_request":
            controls.append((old_scores[key], new_scores[key]))
    summary = {"coverage": coverage, "release_em": [old_em, new_em], "identical_prompt_controls": len(controls),
               "identical_prompt_score_changes": sum(x != y for x, y in controls),
               "identical_prompt_net_correct": sum(y - x for x, y in controls)}
    return records, summary


def group_sums(groups, records, models):
    return np.array([
        [[sum(records[model][item][i] for item in group) for model in models] for i in (1, 2)]
        for group in groups], dtype=np.int64)


def audit(root):
    prior, repaired = [run_catalogue(root, release) for release in RELEASES]
    models, coverage, outcomes = [], {}, {}
    for model in sorted(prior.keys() | repaired.keys()):
        if model not in prior or model not in repaired or prior[model][1] != repaired[model][1]:
            coverage[model] = {"ineligible_release_configuration": 1}
            continue
        matched, coverage[model] = compare_model(root, model)
        if matched is not None:
            models.append(model)
            outcomes[model] = matched
    assert len(models) >= 2
    common = sorted(set.intersection(*(set(outcomes[m]) for m in models)))
    grouped = {}
    for key in common:
        passage = {outcomes[model][key][0] for model in models}
        assert len(passage) == 1
        grouped.setdefault(passage.pop(), []).append(key)
    ordered = [grouped[key] for key in sorted(grouped)]
    panels = {"first_pass": ordered[::2], "assessment": ordered[1::2], "whole": ordered}
    assert min(map(len, panels.values())) >= 2
    totals = {name: group_sums(groups, outcomes, models) for name, groups in panels.items()}
    n_questions = {name: sum(map(len, groups)) for name, groups in panels.items()}
    rates = {name: array.sum(axis=0) * 100 / n_questions[name] for name, array in totals.items()}

    pairs = []
    for first, second in itertools.combinations(range(len(models)), 2):
        comparisons = {}
        for panel, scores in rates.items():
            old, new = (scores[:, first] - scores[:, second]).tolist()
            comparisons[panel] = {"old_margin_pp": old, "new_margin_pp": new, "direction": direction(old, new)}
        pairs.append({"first": models[first], "second": models[second], **comparisons})
    selected = [r for r in pairs if r["first_pass"]["direction"].startswith("reversed")]
    adjusted_alpha = 0.05 / (2 * len(selected)) if selected else None
    if selected:
        rng = np.random.default_rng(41122)
        sizes = np.array(list(map(len, panels["assessment"])))
        count = len(sizes)
        draws = rng.multinomial(count, np.repeat(1 / count, count), size=REPS).astype(np.float64)
        denominators = draws @ sizes
        for pair in selected:
            left, right = [models.index(pair[key]) for key in ("first", "second")]
            sums = totals["assessment"]
            margins = 100 * (draws @ (sums[:, :, left] - sums[:, :, right])) / denominators[:, None]
            lows, highs = np.quantile(margins, [adjusted_alpha / 2, 1 - adjusted_alpha / 2], axis=0)
            result = pair["assessment"]
            ci_old, ci_new = np.column_stack((lows, highs)).tolist()
            old, new = result["old_margin_pp"], result["new_margin_pp"]
            result.update(
                old_adjusted_95_pp=ci_old, new_adjusted_95_pp=ci_new,
                confirmed=(result["direction"] == pair["first_pass"]["direction"]
                           and abs(old) > 2 and abs(new) > 2
                           and order(ci_old[0]) == order(ci_old[1]) == order(old)
                           and order(ci_new[0]) == order(ci_new[1]) == order(new)),
            )
    return {
        "model_count": len(models), "pair_count": len(pairs), "item_counts": n_questions,
        "passage_groups": {name: len(groups) for name, groups in panels.items()},
        "model_coverage": coverage, "model_order": models,
        "paired_panel_accuracies_pp": {name: values.tolist() for name, values in rates.items()},
        "direction_counts": {name: Counter(row[name]["direction"] for row in pairs) for name in panels},
        "selected_reversals": len(selected), "adjusted_alpha": adjusted_alpha,
        "confirmed_reversals": [[r["first"], r["second"]] for r in selected if r["assessment"].get("confirmed")],
        "comparisons": pairs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(args.archive), indent=2) + "\n")


if __name__ == "__main__":
    main()
