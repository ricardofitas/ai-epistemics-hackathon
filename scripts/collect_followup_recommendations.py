#!/usr/bin/env python3
"""Collect exact subject artifacts and check frozen follow-up assignments."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import random


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--kind", choices=["wmt", "holdout"], required=True)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--freeze-time", required=True)
    args = parser.parse_args()
    p = args.directory
    jobs = [json.loads(x) for x in (p / "manifest.jsonl").read_text().splitlines()]
    expected = 20 if args.kind == "wmt" else 4
    assert len(jobs) == len({x["trial_id"] for x in jobs}) == expected
    cells = Counter((x["model_config"], x.get("condition", x["case_id"])) for x in jobs)
    assert len(cells) == 4 and set(cells.values()) == ({5} if args.kind == "wmt" else {1})
    acknowledgments = json.loads((p / "acknowledged-hashes.json").read_text())
    assert set(acknowledgments) == {x["trial_id"] for x in jobs}
    freeze_time = dt.datetime.fromisoformat(args.freeze_time.replace("Z", "+00:00"))
    prior_rows = {}
    if (p / "responses.jsonl").exists():
        prior_rows = {r["trial_id"]: r for r in map(json.loads, (p / "responses.jsonl").read_text().splitlines())}
    rows = []
    for j in jobs:
        tid = j["trial_id"]
        for folder, field in [("prompts", "prompt"), ("launchers", "launcher")]:
            path = p / folder / f"{tid}.txt"
            assert sha(path.read_bytes()) == j[field + "_sha256"] == sha(j[field].encode())
        path = p / "responses" / f"{tid}.md"
        raw = path.read_bytes()
        assert raw.strip() and sha(raw) == acknowledgments[tid]["response_sha256"], tid
        timestamp = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)
        if tid in prior_rows and prior_rows[tid]["response_sha256"] == sha(raw):
            timestamp = dt.datetime.fromisoformat(prior_rows[tid]["artifact_mtime_utc"])
        assert timestamp > freeze_time, f"Response precedes freeze: {tid}"
        row = {**j, "status": "completed", "response": raw.decode(),
               "response_sha256": sha(raw), "artifact_mtime_utc": timestamp.isoformat(),
               "agent_path": "/root/" + tid.lower().replace("-", "_"),
               "response_words_whitespace": len(raw.decode().split())}
        row["word_limit_deviation"] = row["response_words_whitespace"] > 300
        if args.kind == "wmt":
            source_raw = (p / "source_access" / f"{tid}.json").read_bytes()
            assert sha(source_raw) == acknowledgments[tid]["source_access_sha256"], tid
            row["source_access_sha256"] = sha(source_raw)
            row["source_access_record"] = json.loads(source_raw)
        rows.append(row)
    write_jsonl(p / "responses.jsonl", rows)
    shuffled = rows.copy()
    random.Random(2026111270 if args.kind == "wmt" else 2026111271).shuffle(shuffled)
    prefix = "R" if args.kind == "wmt" else "H"
    packet, key = [], []
    for i, row in enumerate(shuffled, 1):
        rid = f"{prefix}{i:02d}"
        packet.append({"response_id": rid, "case_id": row["case_id"], "response": row["response"]})
        key.append({"response_id": rid, "trial_id": row["trial_id"]})
    write_jsonl(p / "review_packet.jsonl", packet)
    write_jsonl(p / "review_key.jsonl", key)
    metadata = dict(collected_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                    freeze_commit=args.freeze_commit, freeze_commit_utc=args.freeze_time,
                    attempted=expected, completed=len(rows), source_cases=1 if args.kind == "wmt" else 2,
                    model_configs=["gpt-6.1-sol inherited", "gpt-6-luna requested override"],
                    exact_backend_snapshot=None, sampling_settings="Inherited defaults, not surfaced",
                    interface="Fresh collaboration agents, fork_turns=none; exact launchers retained",
                    capture="Verbatim subject-written UTF-8 files; final subject hash acknowledgment checked",
                    isolation="Instruction-based file restrictions in a shared filesystem, not a security sandbox",
                    word_limit_deviations=sum(x["word_limit_deviation"] for x in rows),
                    source_access_evidence="Subject-generated logs with tool/result references where available; no independently captured provider traces" if args.kind == "wmt" else "Memory-only instructions",
                    rubric="Unchanged generic rule; frozen case-specific requirements and prereview clarifications",
                    review="Two fresh agent ratings, incomplete blinding where citations reveal package; human pending",
                    scope="Selected-case replication" if args.kind == "wmt" else "Two independent curated source-family holdouts, one answer/configuration/case")
    write_json(p / "metadata.json", metadata)
    integrity = dict(requested=expected, completed=len(rows),
                     all_prompt_and_launcher_hashes_match=True,
                     all_final_answer_hashes_match=True,
                     all_source_record_hashes_match=True if args.kind == "wmt" else None,
                     all_artifacts_after_freeze=True,
                     earliest_response_utc=min(x["artifact_mtime_utc"] for x in rows),
                     latest_response_utc=max(x["artifact_mtime_utc"] for x in rows),
                     distinct_response_hashes=len({x["response_sha256"] for x in rows}),
                     manifest_sha256=sha((p / "manifest.jsonl").read_bytes()),
                     packet_sha256=sha((p / "review_packet.jsonl").read_bytes()))
    write_json(p / "integrity.json", integrity)
    print(json.dumps(integrity))


if __name__ == "__main__":
    main()
