#!/usr/bin/env python3
"""Check native Adaption capture against the frozen five-family manifest."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import random


def read_jsonl(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def jsonl(path, rows):
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--freeze-time", required=True)
    args = parser.parse_args()
    p = args.directory
    jobs = read_jsonl(p / "manifest.jsonl")
    captures = read_jsonl(p / "responses.jsonl")
    protocol = json.loads((p / "protocol.json").read_text())
    if digest((p / "manifest.jsonl").read_bytes()) != protocol["manifest_sha256"]:
        raise ValueError("Frozen manifest changed")
    if len(jobs) != 20 or len(captures) != 20:
        raise ValueError("Require all 20 attempts, including incomplete/error captures")
    if len({(j["case_id"], j["requested_model"]) for j in jobs}) != 20:
        raise ValueError("Duplicate case/configuration cell")
    if set(Counter(j["case_id"] for j in jobs).values()) != {4}:
        raise ValueError("Require four model attempts per case")
    if len({j["case_id"] for j in jobs}) != 5:
        raise ValueError("Require five source-case families")
    recorded = {r["trial_id"]: r for r in captures}
    if len(recorded) != 20 or set(recorded) != {j["trial_id"] for j in jobs}:
        raise ValueError("Missing or duplicate trial captures")
    freeze = dt.datetime.fromisoformat(args.freeze_time.replace("Z", "+00:00"))
    rows = []
    for job in jobs:
        row = recorded[job["trial_id"]]
        if row.get("request_payload") != job["request_payload"] or row.get("attempt_count") != 1:
            raise ValueError("Changed payload or attempt count")
        body = json.dumps(job["request_payload"], sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode()
        if digest(body) != row["request_sha256"]:
            raise ValueError("Wire payload hash mismatch")
        if digest(row["output_text"].encode()) != row["output_text_sha256"]:
            raise ValueError("Final answer hash mismatch")
        if json.loads((p / "api_artifacts" / (job["trial_id"] + ".json")).read_text()) != row:
            raise ValueError("Individual artifact differs from ordered aggregate")
        if dt.datetime.fromisoformat(row["started_utc"]) <= freeze:
            raise ValueError("Request precedes protocol freeze")
        rows.append({**row, "case_id": job["case_id"], "response": row["output_text"]})
    jsonl(p / "responses_enriched.jsonl", rows)
    shuffled = rows.copy()
    random.Random(2026111307).shuffle(shuffled)
    packet, key = [], []
    for i, row in enumerate(shuffled, 1):
        rid = f"X{i:02d}"
        packet.append({"response_id": rid, "case_id": row["case_id"],
                       "response": row["response"], "capture_complete": row["completed_nonempty"],
                       "incomplete_details": row.get("incomplete_details")})
        key.append({"response_id": rid, "trial_id": row["trial_id"]})
    jsonl(p / "review_packet.jsonl", packet)
    jsonl(p / "review_key.jsonl", key)
    case_counts = {cid: {"attempted": sum(r["case_id"] == cid for r in rows),
                         "complete": sum(r["case_id"] == cid and r["completed_nonempty"] for r in rows)}
                   for cid in sorted({r["case_id"] for r in rows})}
    integrity = {"freeze_commit": args.freeze_commit, "freeze_utc": args.freeze_time,
                 "requested": 20, "recorded": len(rows),
                 "completed_nonempty": sum(r["completed_nonempty"] for r in rows),
                 "http_status_counts": dict(Counter(str(r.get("http_status")) for r in rows)),
                 "response_status_counts": dict(Counter(str(r.get("response_status")) for r in rows)),
                 "case_counts": case_counts, "new_families_with_final_answers": sum(c["complete"] > 0 for c in case_counts.values()),
                 "all_payload_text_and_artifact_hashes_match": True,
                 "all_request_starts_after_freeze": True, "client_retries": 0,
                 "word_cap_deviations": sum(r["output_words_whitespace"] > 300 for r in rows),
                 "earliest_request_utc": min(r["started_utc"] for r in rows),
                 "latest_capture_utc": max(r["ended_utc"] for r in rows),
                 "reported_usage_cost_sum": sum((r.get("usage") or {}).get("cost", 0) for r in rows),
                 "cost_note": "Provider-reported cost; missing responses may omit cost; no USD/balance inference",
                 "manifest_sha256": digest((p / "manifest.jsonl").read_bytes()),
                 "packet_sha256": digest((p / "review_packet.jsonl").read_bytes()),
                 "source_cases": 5, "human_review": "pending"}
    (p / "integrity.json").write_text(json.dumps(integrity, indent=2) + "\n")
    print(json.dumps(integrity))


if __name__ == "__main__":
    main()
