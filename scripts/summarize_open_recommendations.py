#!/usr/bin/env python3
"""Summarize the complete exploratory agent pilot without treating repeats as cases."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_dir", type=Path)
    args = parser.parse_args()
    p = args.results_dir
    responses = {r["trial_id"]: r for r in read_jsonl(p / "responses.jsonl")}
    key = {r["response_id"]: r["trial_id"] for r in read_jsonl(p / "review_key.jsonl")}
    ratings = []
    for filename in ("ratings_a.jsonl", "ratings_b.jsonl"):
        rows = read_jsonl(p / filename)
        mapped = {r["response_id"]: r for r in rows}
        if len(rows) != len(mapped) or set(mapped) != set(key):
            raise ValueError(f"Missing or duplicate rating in {filename}")
        ratings.append(mapped)
    manifest = read_jsonl(p / "manifest.jsonl")
    if len(responses) != len(manifest) or set(key.values()) != set(responses):
        raise ValueError("Incomplete pilot or review key")

    by_condition = defaultdict(Counter)
    by_case = defaultdict(Counter)
    disagreements = []
    for rid, tid in key.items():
        left, right = (r[rid]["unsupported_recommendation"] for r in ratings)
        if left != right:
            disagreements.append({"response_id": rid, "left": left, "right": right})
            label = "disagreement"
        else:
            label = left
        row = responses[tid]
        by_condition[row["condition"]][label] += 1
        by_case[row["case_id"]][label] += 1
    summary = {
        "source_cases": len({row["case_id"] for row in manifest}),
        "model_configurations": 1,
        "responses": len(responses),
        "rating_counts": [dict(Counter(r["unsupported_recommendation"] for r in rs.values())) for rs in ratings],
        "primary_disagreements": disagreements,
        "by_condition": {k: dict(v) for k, v in sorted(by_condition.items())},
        "by_variant": {k: dict(v) for k, v in sorted(by_case.items())},
        "interpretation": "Exploratory source-backed open prompts, one inherited configuration; repeated answers are not independent source cases. No general prevalence or checklist-efficacy claim.",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
