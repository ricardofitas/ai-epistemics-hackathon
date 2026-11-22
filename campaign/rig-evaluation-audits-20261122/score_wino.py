"""Estimate paired WinoGrande contrasts, bootstrap intervals and missing-answer bounds."""
import argparse
import itertools
import json
import random
import sqlite3
from collections import Counter
from pathlib import Path
from statistics import mean

from freeze import ROOT

CELLS = ("full_official", "omitted_official", "full_constant_B", "omitted_constant_B")


def pair_scores(answers, gold):
    full = answers[:2]
    omitted = answers[2:]
    return (int(full == gold), int(omitted == gold),
            int(full == ("B", "B")), int(omitted == ("B", "B")))


def contrasts(scores):
    full, omitted, constant_full, constant_omitted = scores
    official_gain = full - omitted
    return official_gain, official_gain - (constant_full - constant_omitted)


def read_answers(database, models, panel):
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        rows = db.execute("SELECT model, revision, pair_id, item_id, variant, official, prediction "
                          "FROM answers").fetchall()
    expected = {(model, model_revision, pair, item, variant)
                for model, model_revision in models.items() for pair, items in panel.items()
                for item in items for variant in ("full", "omitted")}
    assert {r[:5] for r in rows} == expected and len(rows) == len(expected), "Incomplete or unexpected run"
    return {(model, pair, item, variant): (gold, answer)
            for model, _revision, pair, item, variant, gold, answer in rows}


def evaluate(rows, models, panel):
    by_model = {model: Counter() for model in models}
    effects = []
    lower, upper = [0, 0], [0, 0]
    for pair, items in panel.items():
        pair_effects = []
        for model in models:
            cells = [rows[model, pair, item, variant] for variant in ("full", "omitted")
                     for item in items]
            gold = tuple(cell[0] for cell in cells[:2])
            assert gold in {("A", "B"), ("B", "A")} and gold == tuple(cell[0] for cell in cells[2:])
            answers = tuple(cell[1] for cell in cells)
            scores = pair_scores(answers, gold)
            by_model[model].update(dict(zip(CELLS, scores)))
            pair_effects.append(contrasts(scores))
            possible = [
                contrasts(pair_scores(candidate, gold))
                for candidate in itertools.product(*[(None, "A", "B") if answer is None else (answer,)
                                                        for answer in answers])
            ]
            for i in range(2):
                lower[i] += min(values[i] for values in possible)
                upper[i] += max(values[i] for values in possible)
            for variant, start in (("full", 0), ("omitted", 2)):
                predictions = answers[start:start + 2]
                summary = by_model[model]
                summary[variant + "_invalid_items"] += predictions.count(None)
                summary[variant + "_individual_official_correct"] += sum(a == g for a, g in zip(predictions, gold))
                summary[variant + "_individual_constant_B_correct"] += predictions.count("B")
                summary[variant + "_identical_predictions"] += int(predictions[0] == predictions[1])
        effects.append(tuple(mean(column) for column in zip(*pair_effects)))

    rng = random.Random(41122)
    bootstrap = [[], []]
    for _ in range(10_000):
        sample = rng.choices(effects, k=len(effects))
        for i, column in enumerate(zip(*sample)):
            bootstrap[i].append(mean(column))
    for values in bootstrap:
        values.sort()

    names = ("official_gain", "key_by_sentence_interaction")
    denominator = len(panel) * len(models)
    endpoints = {}
    for i, name in enumerate(names):
        endpoints[name] = {
            "percentage_points": 100 * mean(effect[i] for effect in effects),
            "pair_bootstrap_95_pp": [100 * bootstrap[i][j] for j in (249, 9749)],
            "missing_identification_interval_pp": [100 * bound[i] / denominator for bound in (lower, upper)],
        }
    key_orders = {}
    for cell in CELLS:
        left, right = models
        margin = by_model[left][cell] - by_model[right][cell]
        key_orders[cell] = {"winner": left if margin > 0 else right if margin < 0 else "tie",
                            "first_minus_second_pp": 100 * margin / len(panel)}
    return {
        "pairs": len(panel),
        "models_in_margin_order": list(models),
        "observed_pairs": by_model,
        "pair_ranking": key_orders,
        "contrasts": endpoints,
        "eligible_for_heldout": all(e["percentage_points"] >= 10 for e in endpoints.values()),
        "meets_heldout_success_threshold": all(e["percentage_points"] >= 10
                                              and e["pair_bootstrap_95_pp"][0] > 0 for e in endpoints.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--split", choices=("pilot", "heldout"), required=True)
    args = parser.parse_args()
    models = json.loads((ROOT / "pilot.json").read_text())["models"]
    panel = json.loads((ROOT / "frozen-items.json").read_text())[args.split]
    rows = read_answers(args.database, models, panel)
    result = dict(split=args.split, **evaluate(rows, tuple(models), panel))
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
