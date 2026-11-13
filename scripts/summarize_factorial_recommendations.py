#!/usr/bin/env python3
"""Descriptive blinded-rating summary for the frozen 2 x 2 recommendation study."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    args = parser.parse_args()
    p = args.experiment_dir
    manifest = read_jsonl(p / "manifest.jsonl")
    responses = {r["trial_id"]: r for r in read_jsonl(p / "responses.jsonl")}
    key = {r["response_id"]: r["trial_id"] for r in read_jsonl(p / "review_key.jsonl")}
    ratings = []
    for name in ["ratings_a.jsonl", "ratings_b.jsonl"]:
        rows = read_jsonl(p / name)
        mapped = {r["response_id"]: r for r in rows}
        if len(mapped) != len(rows) or set(mapped) != set(key):
            raise ValueError(f"Missing/duplicate ratings: {name}")
        ratings.append(mapped)
    if len(manifest) != 24 or set(responses) != {r["trial_id"] for r in manifest} or set(key.values()) != set(responses):
        raise ValueError("Incomplete study")
    by_cell, by_case = defaultdict(Counter), defaultdict(Counter)
    disagreements = []
    for rid, tid in key.items():
        a, b = [rs[rid]["unsupported_recommendation"] for rs in ratings]
        label = a if a == b else "disagreement"
        if a != b:
            disagreements.append({"response_id": rid, "trial_id": tid, "a": a, "b": b})
        row = responses[tid]
        by_cell[(row["model_requested"], row["prompt_form"])][label] += 1
        by_case[row["case_id"]][label] += 1
    print(json.dumps({
        "responses": len(responses), "source_cases": len(by_case), "models_requested": 2,
        "repeats_per_case_model_form": 1,
        "rating_counts": [dict(Counter(r["unsupported_recommendation"] for r in rs.values())) for rs in ratings],
        "primary_disagreements": disagreements,
        "by_model_and_prompt_form": [{"model_requested": m, "prompt_form": f, "labels": dict(c)} for (m, f), c in sorted(by_cell.items())],
        "by_case": {k: dict(v) for k, v in sorted(by_case.items())},
        "interpretation": "Descriptive six-case comparison; prompt package changes several instructions together. No general failure-rate or single-instruction causal claim.",
    }, indent=2))


if __name__ == "__main__":
    main()
