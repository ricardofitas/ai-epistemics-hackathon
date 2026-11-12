#!/usr/bin/env python3
"""Reproduce the MNLI/HANS comparison from McCoy, Min & Linzen's run-level CSV."""

import argparse
import csv
import json
import re
import statistics
from pathlib import Path


def analyze(path: Path) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        source = csv.DictReader(handle)
        columns = {"Run", "MNLI dev acc.", "Overall accuracy", "ln_subject/object_swap"}
        if not columns.issubset(source.fieldnames or []):
            raise ValueError(f"Missing columns: {columns - set(source.fieldnames or [])}")
        rows = [
            {
                "run": row["Run"],
                "mnli": float(row["MNLI dev acc."]),
                "hans_overall": float(row["Overall accuracy"]),
                "subject_object_swap": float(row["ln_subject/object_swap"]),
            }
            for row in source
            if re.fullmatch(r"Run \d+", row["Run"])
        ]
    if len(rows) != 100:
        raise ValueError(f"Expected 100 model runs, got {len(rows)}")

    tied_pairs = [
        (left, right, abs(left["subject_object_swap"] - right["subject_object_swap"]))
        for i, left in enumerate(rows)
        for right in rows[i + 1 :]
        if left["mnli"] == right["mnli"]
    ]
    if not tied_pairs:
        raise ValueError("No pairs with identical MNLI development accuracy")
    left, right, gap = max(tied_pairs, key=lambda pair: pair[2])
    gaps = [pair[2] for pair in tied_pairs]
    return {
        "model_runs": len(rows),
        "mnli_range": [min(r["mnli"] for r in rows), max(r["mnli"] for r in rows)],
        "subject_object_swap_range": [
            min(r["subject_object_swap"] for r in rows),
            max(r["subject_object_swap"] for r in rows),
        ],
        "exact_mnli_tie_pairs": len(tied_pairs),
        "median_swap_gap_among_ties": statistics.median(gaps),
        "tied_pairs_with_swap_gap_at_least_20_points": sum(g >= 0.20 for g in gaps),
        "largest_tied_pair_gap": gap,
        "largest_tied_pair": [left, right],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="Upstream berts_of_a_feather_accuracies_by_run.csv")
    args = parser.parse_args()
    print(json.dumps(analyze(args.csv_file), indent=2))


if __name__ == "__main__":
    main()
