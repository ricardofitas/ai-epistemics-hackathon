#!/usr/bin/env python3
"""Post-outcome ranking sensitivity on the fixed 20-source factorial panel.

This script consumes the independently verified official RULE scores. It makes
no provider or judge calls and assigns each incomplete score both possible
binary values. All 256 joint assignments are retained for the ranking claim.
"""

import argparse
import collections
import csv
import hashlib
import itertools
import json
import pathlib


GEMMA = "gemma-4-31b-it"
QWEN = "qwen3.8-27b"
CONDITIONS = (
    "free_form__absent",
    "free_form__A.None",
    "choice__absent",
    "choice__A.None",
)
PROBLEMATIC = "choice__A.None"
REPAIRED = "free_form__absent"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def endpoints(values):
    return [min(values), max(values)]


def ranking_name(difference):
    if difference > 0:
        return "qwen_ahead"
    if difference < 0:
        return "gemma_ahead"
    return "tie"


def analyze(scores_path, verification_path):
    verification = json.loads(verification_path.read_text())
    assert verification["status"] == "PASS"
    assert verification["expected_run_id"] == 43615821403
    rows = json.loads(scores_path.read_text())
    assert len(rows) == 160
    assert {row["model"] for row in rows} == {GEMMA, QWEN}
    assert {row["condition"] for row in rows} == set(CONDITIONS)
    sources = sorted({row["source_index"] for row in rows})
    assert len(sources) == 20
    cells = {
        (row["model"], row["source_index"], row["condition"]): row["score"]
        for row in rows
    }
    assert len(cells) == 160
    assert set(cells) == set(itertools.product((GEMMA, QWEN), sources, CONDITIONS))
    assert set(cells.values()) <= {0, 1, None}
    unknowns = [key for key, score in cells.items() if score is None]
    assert len(unknowns) == 8
    totals_by_condition = {condition: [] for condition in CONDITIONS}
    rank_assignments = collections.Counter()
    relative_shifts = []
    model_gains = {model: [] for model in (GEMMA, QWEN)}
    caveat_exclusions = {
        "exclude_source860_historical_office": {860},
        "exclude_source571_multipart_reference": {571},
        "exclude_source281_intrinsic_yes_no_options": {281},
        "exclude_sources860_and571": {860, 571},
        "exclude_sources860_and281": {860, 281},
        "exclude_sources571_and281": {571, 281},
        "exclude_all_three_predeclared_caveats": {860, 571, 281},
    }
    caveat_samples = {
        name: {"from_differences": [], "to_differences": [], "relative_shifts": [],
               "rank_assignments": collections.Counter()}
        for name in caveat_exclusions
    }
    observed_totals = collections.defaultdict(int)
    unknown_totals = collections.Counter()
    for (model, source, condition), score in cells.items():
        if score is None:
            unknown_totals[(model, condition)] += 1
        else:
            observed_totals[(model, condition)] += int(score)

    for assignment in itertools.product((0, 1), repeat=len(unknowns)):
        complete = {**cells, **dict(zip(unknowns, assignment))}
        totals = {
            (model, condition): sum(complete[(model, source, condition)] for source in sources)
            for model, condition in itertools.product((GEMMA, QWEN), CONDITIONS)
        }
        differences = {
            condition: int(totals[(QWEN, condition)] - totals[(GEMMA, condition)])
            for condition in CONDITIONS
        }
        for condition in CONDITIONS:
            totals_by_condition[condition].append(differences[condition])
        rank_assignments[(ranking_name(differences[PROBLEMATIC]),
                          ranking_name(differences[REPAIRED]))] += 1
        relative_shifts.append(differences[REPAIRED] - differences[PROBLEMATIC])
        for model in (GEMMA, QWEN):
            model_gains[model].append(int(totals[(model, REPAIRED)] - totals[(model, PROBLEMATIC)]))
        for name, excluded in caveat_exclusions.items():
            retained_sources = [source for source in sources if source not in excluded]
            panel_differences = {
                condition: int(sum(complete[(QWEN, source, condition)]
                                   - complete[(GEMMA, source, condition)]
                                   for source in retained_sources))
                for condition in (PROBLEMATIC, REPAIRED)
            }
            samples = caveat_samples[name]
            samples["from_differences"].append(panel_differences[PROBLEMATIC])
            samples["to_differences"].append(panel_differences[REPAIRED])
            samples["relative_shifts"].append(panel_differences[REPAIRED] - panel_differences[PROBLEMATIC])
            samples["rank_assignments"][(ranking_name(panel_differences[PROBLEMATIC]),
                                          ranking_name(panel_differences[REPAIRED]))] += 1

    condition_summary = {}
    per_source = []
    for condition in CONDITIONS:
        model_counts = {}
        for model in (GEMMA, QWEN):
            correct = observed_totals[(model, condition)]
            unknown = unknown_totals[(model, condition)]
            model_counts[model] = {
                "planned": 20,
                "known_correct": correct,
                "known_incorrect": 20 - correct - unknown,
                "unknown": unknown,
                "correct_count_bounds": [correct, correct + unknown],
            }
        q = model_counts[QWEN]
        g = model_counts[GEMMA]
        direct_bounds = [q["known_correct"] - g["known_correct"] - g["unknown"],
                         q["known_correct"] + q["unknown"] - g["known_correct"]]
        assert endpoints(totals_by_condition[condition]) == direct_bounds
        paired = collections.Counter()
        possible_directions = collections.Counter()
        for source in sources:
            gemma = cells[(GEMMA, source, condition)]
            qwen = cells[(QWEN, source, condition)]
            if gemma is None or qwen is None:
                paired["at_least_one_unknown"] += 1
            elif qwen == gemma == 1:
                paired["both_correct"] += 1
            elif qwen == gemma == 0:
                paired["both_incorrect"] += 1
            elif qwen == 1:
                paired["qwen_only_correct"] += 1
            else:
                paired["gemma_only_correct"] += 1
            possibilities = sorted({
                ranking_name(q - g)
                for q, g in itertools.product((0, 1) if qwen is None else (qwen,),
                                              (0, 1) if gemma is None else (gemma,))
            })
            possible_directions["|".join(possibilities)] += 1
            per_source.append({
                "source_index": source,
                "condition": condition,
                "gemma_score": gemma,
                "qwen_score": qwen,
                "possible_ranking_directions": "|".join(possibilities),
            })
        assert sum(paired.values()) == 20
        condition_summary[condition] = {
            "models": model_counts,
            "qwen_minus_gemma_correct_count_bounds": direct_bounds,
            "qwen_minus_gemma_percentage_point_bounds": [5 * bound for bound in direct_bounds],
            "source_paired_observed_outcomes": dict(paired),
            "source_possible_ranking_directions": dict(possible_directions),
        }

    shift_bounds = endpoints(relative_shifts)
    independent_shift_bounds = [
        condition_summary[REPAIRED]["qwen_minus_gemma_correct_count_bounds"][0]
        - condition_summary[PROBLEMATIC]["qwen_minus_gemma_correct_count_bounds"][1],
        condition_summary[REPAIRED]["qwen_minus_gemma_correct_count_bounds"][1]
        - condition_summary[PROBLEMATIC]["qwen_minus_gemma_correct_count_bounds"][0],
    ]
    assert shift_bounds == independent_shift_bounds
    caveat_sensitivity = {}
    for name, samples in caveat_samples.items():
        excluded = caveat_exclusions[name]
        assert excluded <= set(sources)
        denominator = len(sources) - len(excluded)
        keys = ("from_differences", "to_differences", "relative_shifts")
        bounds = {key: endpoints(samples[key]) for key in keys}
        caveat_sensitivity[name] = {
            "excluded_source_indices": sorted(excluded),
            "retained_source_denominator": denominator,
            "correct_count_difference_bounds": bounds,
            "percentage_point_difference_bounds": {
                key: [100 * value / denominator for value in values]
                for key, values in bounds.items()
            },
            "strict_reversal_for_all_256_original_unknown_assignments": samples["rank_assignments"] == {
                ("gemma_ahead", "qwen_ahead"): 256
            },
            "note": "Secondary post-outcome exclusion sensitivity. Original20-source primary panel remains unchanged."
        }
    source_contributions = []
    for source in sources:
        keys = [(model, source, condition)
                for condition in (PROBLEMATIC, REPAIRED)
                for model in (QWEN, GEMMA)]
        possibilities = [(0, 1) if cells[key] is None else (cells[key],) for key in keys]
        possible_shifts = [int(q_to - g_to - q_from + g_from)
                           for q_from, g_from, q_to, g_to in itertools.product(*possibilities)]
        source_contributions.append({
            "source_index": source,
            "problematic_qwen": cells[(QWEN, source, PROBLEMATIC)],
            "problematic_gemma": cells[(GEMMA, source, PROBLEMATIC)],
            "repaired_qwen": cells[(QWEN, source, REPAIRED)],
            "repaired_gemma": cells[(GEMMA, source, REPAIRED)],
            "relative_shift_minimum_correct_count": min(possible_shifts),
            "relative_shift_maximum_correct_count": max(possible_shifts),
        })
    assert sum(row["relative_shift_minimum_correct_count"] for row in source_contributions) == shift_bounds[0]
    assert sum(row["relative_shift_maximum_correct_count"] for row in source_contributions) == shift_bounds[1]
    report = {
        "status": "PASS",
        "stage": "Exploratory post-outcome model-ranking sensitivity analysis",
        "run_id": 43615821403,
        "planned_requests": 160,
        "source_questions": 20,
        "eligible_scores": 152,
        "unknown_scores": 8,
        "joint_assignments_enumerated": 2 ** len(unknowns),
        "primary_endpoint": "Unmodified pinned official optional RULE acceptance",
        "input_sha256": {
            "independent_scores": digest(scores_path),
            "independent_verification": digest(verification_path),
        },
        "conditions": condition_summary,
        "exploratory_reversal": {
            "from_condition": PROBLEMATIC,
            "to_condition": REPAIRED,
            "joint_assignment_ranking_counts": [
                {"from_rank": key[0], "to_rank": key[1], "assignments": count}
                for key, count in sorted(rank_assignments.items())
            ],
            "strict_reversal_for_every_assignment": rank_assignments == {
                ("gemma_ahead", "qwen_ahead"): 256
            },
            "relative_qwen_gain_correct_count_bounds": shift_bounds,
            "relative_qwen_gain_percentage_point_bounds": [5 * value for value in shift_bounds],
            "each_model_gain_percentage_point_bounds": {
                model: [5 * value for value in endpoints(gains)]
                for model, gains in model_gains.items()
            },
        },
        "checks": {
            "exhaustive_condition_bounds_equal_independent_count_formula": "PASS",
            "exhaustive_relative_shift_equals_endpoint_formula": "PASS",
            "all_twenty_source_pairs_accounted_per_condition": "PASS",
            "sum_of_source_paired_contributions_matches_joint_assignment_bounds": "PASS",
        },
        "secondary_caveat_exclusion_sensitivity": caveat_sensitivity,
        "source_paired_relative_ranking_contributions": source_contributions,
        "interpretation": [
            "Every possible binary score assignment to the eight incomplete outputs preserves the selected full-panel ranking reversal.",
            "The ranking comparison was selected after aggregate results were seen. It is an exploratory derivative, not a prospectively registered ranking endpoint.",
            "The same twenty source cases are repeated across two models and four conditions. Score differences are paired fixed-panel differences.",
            "Bounds express incomplete-output sensitivity and are not population confidence intervals or model capability estimates.",
            "RULE acceptance can reflect factual material in a rationale even when the final answer is a symbolic tag. These rankings retain that endpoint and do not substitute semantic judgments.",
            "The four conditions are a custom diagnostic template. They do not establish results from a full installed native provider or default model judge path.",
            "No incomplete response is upgraded from its partial text. All eight remain unknown in the retained primary score file.",
        ],
        "new_model_or_judge_calls": 0,
    }
    return report, per_source


def main():
    parser = argparse.ArgumentParser()
    directory = pathlib.Path(__file__).resolve().parent
    parser.add_argument("--scores", type=pathlib.Path, default=directory / "INDEPENDENT_SCORES.json")
    parser.add_argument("--verification", type=pathlib.Path, default=directory / "PRIMARY_VERIFICATION.json")
    parser.add_argument("--output", type=pathlib.Path, default=directory / "RANKING_SENSITIVITY.json")
    args = parser.parse_args()
    report, per_source = analyze(args.scores, args.verification)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with args.output.with_name("SOURCE_PAIRED_OUTCOMES.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_source[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(per_source)
    print(json.dumps(report["exploratory_reversal"], ensure_ascii=False))


if __name__ == "__main__":
    main()
