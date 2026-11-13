#!/usr/bin/env python3
"""Summarize preserved blind first ratings without silently adjudicating them."""
from collections import Counter
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wmt-dir", type=Path, default=Path("experiments/wmt-targeted-replication-20261112"))
    parser.add_argument("--holdout-dir", type=Path, default=Path("experiments/independent-holdouts-20261112"))
    parser.add_argument("--ratings-dir", type=Path, default=Path("experiments/followup-review-20261112"))
    parser.add_argument("--freeze-record", type=Path)
    parser.add_argument("--freeze-first-ratings", action="store_true", help="Create first-rating record before initial unblinding only")
    args = parser.parse_args()
    root = args.ratings_dir
    ratings = {}
    for name in ["a", "b"]:
        rows = read_jsonl(root / f"ratings_{name}.jsonl")
        assert len(rows) == len({r["response_id"] for r in rows}) == 24
        ratings[name] = {r["response_id"]: r for r in rows}
    assert ratings["a"].keys() == ratings["b"].keys()
    frozen = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "note": "First ratings preserved before coordinator unblinding; no silent adjudication",
              "rating_sha256": {k: sha(root / f"ratings_{k}.jsonl") for k in ratings}}
    freeze_record = args.freeze_record or root / "review-freeze.json"
    if freeze_record.exists():
        preserved = json.loads(freeze_record.read_text())
        if preserved["rating_sha256"] != frozen["rating_sha256"]:
            raise ValueError("First ratings changed after their original freeze")
        frozen = preserved
    elif args.freeze_first_ratings:
        with freeze_record.open("x") as f:
            f.write(json.dumps(frozen, indent=2) + "\n")
    else:
        raise ValueError("Original review-freeze record required; do not silently create a retrospective freeze")
    for p in [args.wmt_dir, args.holdout_dir]:
        key = {x["response_id"]: x["trial_id"] for x in read_jsonl(p / "review_key.jsonl")}
        rows = {x["trial_id"]: x for x in read_jsonl(p / "responses.jsonl")}
        trials, cells = [], {}
        for rid, tid in key.items():
            row = rows[tid]
            labels = {k: r[rid]["unsupported_recommendation"] for k, r in ratings.items()}
            assert set(labels.values()) <= {"yes", "no", "uncertain", "unscorable"}
            cid = (row["model_config"], row.get("condition", row["case_id"]))
            cell = cells.setdefault(cid, {"model_config": cid[0], "condition_or_case": cid[1],
                                          "completed": 0, "ratings_a": Counter(), "ratings_b": Counter()})
            cell["completed"] += 1
            for k in ratings:
                cell["ratings_" + k][labels[k]] += 1
            trials.append({"response_id": rid, "trial_id": tid, "model_config": row["model_config"],
                           "condition": row.get("condition"), "case_id": row["case_id"],
                           "ratings": labels, "primary_agreement": len(set(labels.values())) == 1,
                           "source_hash": row["response_sha256"]})
        summary = {"cohort": p.name, "attempted": len(rows), "completed": len(rows),
                   "cells": sorted(cells.values(), key=lambda x: (x["model_config"], x["condition_or_case"])),
                   "overall_first_ratings": {k: dict(Counter(ratings[k][rid]["unsupported_recommendation"] for rid in key)) for k in ratings},
                   "primary_disagreements": [t for t in trials if not t["primary_agreement"]],
                   "trials": trials, "rating_sha256": frozen["rating_sha256"],
                   "human_review": "pending", "adjudication": "none; both original ratings retained",
                   "scope": "Descriptive counts within frozen selected cases; not population prevalence"}
        (p / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({k: summary[k] for k in ["cohort", "completed", "cells", "overall_first_ratings", "primary_disagreements"]}))


if __name__ == "__main__":
    main()
