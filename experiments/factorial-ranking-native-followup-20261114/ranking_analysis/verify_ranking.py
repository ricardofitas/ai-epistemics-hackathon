#!/usr/bin/env python3
"""Check the derived ranking report using coefficient-sign endpoint arithmetic.

This independent check does not import the enumeration analysis. It uses exact
fractions internally and verifies every caveat subset and paired contribution.
"""

import fractions
import itertools
import json
import pathlib


def interval(rows, weights, retained_sources):
    lower = upper = 0
    for row in rows:
        if row["source_index"] not in retained_sources:
            continue
        weight = weights.get((row["model"], row["condition"]), 0)
        if row["score"] is None:
            lower += min(0, weight)
            upper += max(0, weight)
        else:
            lower += int(row["score"]) * weight
            upper += int(row["score"]) * weight
    return [lower, upper]


def main():
    root = pathlib.Path(__file__).resolve().parent
    rows = json.loads((root / "INDEPENDENT_SCORES.json").read_text())
    result = json.loads((root / "RANKING_SENSITIVITY.json").read_text())
    sources = {row["source_index"] for row in rows}
    qwen = "qwen3.8-27b"
    gemma = "gemma-4-31b-it"
    before = "choice__A.None"
    after = "free_form__absent"
    weights_before = {(qwen, before): 1, (gemma, before): -1}
    weights_after = {(qwen, after): 1, (gemma, after): -1}
    weights_shift = {**weights_after, (qwen, before): -1, (gemma, before): 1}
    count = 0
    for condition, summary in result["conditions"].items():
        weights = {(qwen, condition): 1, (gemma, condition): -1}
        bounds = interval(rows, weights, sources)
        assert bounds == summary["qwen_minus_gemma_correct_count_bounds"]
        assert [float(fractions.Fraction(100 * value, 20)) for value in bounds] == summary["qwen_minus_gemma_percentage_point_bounds"]
        count += 1
    assert interval(rows, weights_before, sources)[1] < 0
    assert interval(rows, weights_after, sources)[0] > 0
    assert result["exploratory_reversal"]["strict_reversal_for_every_assignment"] is True
    assert interval(rows, weights_shift, sources) == result["exploratory_reversal"]["relative_qwen_gain_correct_count_bounds"]
    count += 3
    observed_exclusions = set()
    for summary in result["secondary_caveat_exclusion_sensitivity"].values():
        excluded = set(summary["excluded_source_indices"])
        observed_exclusions.add(frozenset(excluded))
        retained = sources - excluded
        assert len(retained) == summary["retained_source_denominator"]
        for key, weights in (("from_differences", weights_before),
                             ("to_differences", weights_after),
                             ("relative_shifts", weights_shift)):
            bounds = interval(rows, weights, retained)
            assert bounds == summary["correct_count_difference_bounds"][key]
            percentages = [float(fractions.Fraction(100 * value, len(retained))) for value in bounds]
            assert percentages == summary["percentage_point_difference_bounds"][key]
            count += 1
        assert interval(rows, weights_before, retained)[1] < 0
        assert interval(rows, weights_after, retained)[0] > 0
        assert summary["strict_reversal_for_all_256_original_unknown_assignments"] is True
        count += 1
    assert observed_exclusions == {
        frozenset(combination)
        for length in (1, 2, 3)
        for combination in itertools.combinations((281, 571, 860), length)
    }
    for contribution in result["source_paired_relative_ranking_contributions"]:
        bounds = interval(rows, weights_shift, {contribution["source_index"]})
        assert bounds == [contribution["relative_shift_minimum_correct_count"],
                          contribution["relative_shift_maximum_correct_count"]]
        count += 1
    verification = {
        "status": "PASS",
        "method": "Independent signed-coefficient endpoint arithmetic with exact rational percentage conversion; analysis implementation not imported",
        "checked_condition_reversal_exclusion_source_contribution_values": count,
        "all_nonempty_subsets_of_three_predeclared_caveats_checked": 7,
        "new_model_or_judge_calls": 0,
    }
    (root / "RANKING_VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification))


if __name__ == "__main__":
    main()
