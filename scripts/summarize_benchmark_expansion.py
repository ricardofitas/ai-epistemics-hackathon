#!/usr/bin/env python3
"""Join immutable blind reviews and explicit scope adjudication, retaining both."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    p = args.directory
    packet = {r["response_id"]: r for r in rows(p / "review_packet.jsonl")}
    key = {r["response_id"]: r["trial_id"] for r in rows(p / "review_key.jsonl")}
    captures = {r["trial_id"]: r for r in rows(p / "responses_enriched.jsonl")}
    frozen = json.loads((p / "review-freeze.json").read_text())["first_rating_sha256"]
    judgments = json.loads((p / "adjudication.json").read_text())["coordinator_dispositions"]
    ratings = {}
    for who in ["a", "b"]:
        path = p / f"ratings_{who}.jsonl"
        if hashlib.sha256(path.read_bytes()).hexdigest() != frozen[who]:
            raise ValueError("First rating file changed")
        ratings[who] = {r["response_id"]: r for r in rows(path)}
        if set(ratings[who]) != set(packet):
            raise ValueError("Incomplete rating coverage")
        for rid, rating in ratings[who].items():
            if not all(s in packet[rid]["response"] for s in rating["exact_supporting_passages"]):
                raise ValueError("Non-verbatim rating evidence")
    if len(packet) != 20 or set(key) != set(packet) or len(captures) != 20:
        raise ValueError("Missing captures or key rows")
    result, disagreements = [], []
    for rid, sample in packet.items():
        row = captures[key[rid]]
        labels = {who: ratings[who][rid]["unsupported_recommendation"] for who in ratings}
        if labels["a"] != labels["b"]:
            disagreements.append(rid)
            if rid not in judgments:
                raise ValueError("Disagreement lacks explicit separate disposition")
        final = judgments.get(rid, labels["a"])
        if final not in {"yes", "no", "uncertain", "unscorable"}:
            raise ValueError("Unknown primary label")
        result.append({"response_id": rid, "trial_id": row["trial_id"],
                       "case_id": sample["case_id"], "requested_model": row["requested_model"],
                       "returned_model": row["returned_model"], "http_status": row["http_status"],
                       "capture_complete": row["completed_nonempty"], "first_labels": labels,
                       "coordinator_label": final, "explicit_scope_adjudication": rid in judgments,
                       "output_text_sha256": row["output_text_sha256"]})
    case_groups, model_groups = defaultdict(list), defaultdict(list)
    for r in result:
        case_groups[r["case_id"]].append(r)
        model_groups[r["requested_model"]].append(r)
    def table(groups):
        return {k: {"attempted": len(v), "complete": sum(r["capture_complete"] for r in v),
                    "coordinator_counts": dict(Counter(r["coordinator_label"] for r in v))}
                for k, v in sorted(groups.items())}
    out = {"requested": 20, "completed_nonempty": sum(r["capture_complete"] for r in result),
           "source_case_families": 5,
           "first_ratings_counts": {who: dict(Counter(r["first_labels"][who] for r in result)) for who in ratings},
           "first_disagreement_ids": sorted(disagreements),
           "coordinator_counts": dict(Counter(r["coordinator_label"] for r in result)),
           "by_case": table(case_groups), "by_requested_model": table(model_groups),
           "trials": sorted(result, key=lambda r: r["trial_id"]),
           "first_rating_sha256": frozen, "human_review": "pending",
           "scope": "One answer per curated source case/configuration. Descriptive counts only; no population prevalence, general model ranking or automatic proof of harm."}
    (p / "summary.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ["requested", "completed_nonempty", "first_ratings_counts",
                                          "first_disagreement_ids", "coordinator_counts", "by_case", "by_requested_model"]}))


if __name__ == "__main__":
    main()
