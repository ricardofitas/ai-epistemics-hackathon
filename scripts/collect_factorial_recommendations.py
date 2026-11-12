#!/usr/bin/env python3
"""Check frozen prompts and collect verbatim agent-written response artifacts."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import random


def digest(data):
    return hashlib.sha256(data).hexdigest()


def jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--casepack", type=Path, required=True, help="Previously frozen shared casepack")
    args = parser.parse_args()
    p = args.experiment_dir
    jobs = [json.loads(x) for x in (p / "manifest.jsonl").read_text().splitlines()]
    if len(jobs) != 24 or len({r["trial_id"] for r in jobs}) != 24:
        raise ValueError("Expected the complete 24-trial frozen manifest")
    if set(Counter(r["case_id"] for r in jobs).values()) != {4}:
        raise ValueError("Expected four trials for every case")
    acknowledgments = json.loads((p / "acknowledged-hashes.json").read_text())
    if set(acknowledgments) != {r["trial_id"] for r in jobs}:
        raise ValueError("Missing final subject hash acknowledgment")
    rows = []
    for job in jobs:
        tid = job["trial_id"]
        if digest((p / "prompts" / f"{tid}.txt").read_bytes()) != job["prompt_sha256"]:
            raise ValueError(f"Changed prompt: {tid}")
        path = p / "responses" / f"{tid}.md"
        if not path.exists():
            raise ValueError(f"Missing response: {tid}; preserve/log any failed call before analysis")
        data = path.read_bytes()
        if digest(data) != acknowledgments[tid]:
            raise ValueError(f"Response differs from subject's final acknowledged hash: {tid}")
        text = data.decode("utf-8")
        if not text.strip():
            raise ValueError(f"Empty response: {tid}")
        words = len(text.split())
        rows.append({
            **job,
            "agent_path": "/root/factor_" + tid[-2:],
            "status": "completed",
            "response": text,
            "response_sha256": digest(data),
            "response_words_whitespace": words,
            "word_limit_deviation": words > 300,
            "artifact_mtime_utc": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat(),
        })
    jsonl(p / "responses.jsonl", rows)
    shuffled = rows.copy()
    random.Random(2026111231).shuffle(shuffled)
    packet, key = [], []
    for i, row in enumerate(shuffled, 1):
        rid = f"F{i:02d}"
        packet.append({"response_id": rid, "case_id": row["case_id"], "response": row["response"]})
        key.append({"response_id": rid, "trial_id": row["trial_id"]})
    jsonl(p / "review_packet.jsonl", packet)
    jsonl(p / "review_key.jsonl", key)
    metadata = {
        "date": "2026-11-12",
        "collected_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "freeze_commit": args.freeze_commit,
        "requested": len(jobs), "completed": len(rows), "source_cases": 6, "domain_clusters": 5,
        "prompt_forms": 2, "repeats_per_model_form_case_cell": 1,
        "model_configurations_requested": ["gpt-6.1-sol (inherited)", "gpt-6-luna (explicit collaboration model override)"],
        "exact_returned_snapshot": None,
        "generation_settings": "Inherited defaults, not surfaced per call",
        "interface": "collaboration.spawn_agent, fork_turns none; exact launcher and file prompt retained",
        "tools": "Subjects instructed to read only opaque prompt and write/hash only their own answer, without browsing/search/delegation",
        "knowledge_policy": "Existing-knowledge only; source case notes/criteria and parent history withheld",
        "capture": "Verbatim subject-written UTF-8 answer artifact, exact bytes hashed; no coordinator text transcription",
        "timestamps": "Artifact filesystem write time is retained; not a provider request/response timestamp",
        "system_context": "Platform system/developer instructions inherited, not a stateless API",
        "response_word_limit_deviations": sum(r["word_limit_deviation"] for r in rows),
        "manifest_sha256": digest((p / "manifest.jsonl").read_bytes()),
        "casepack_sha256": digest(args.casepack.read_bytes()),
        "packet_sha256": digest((p / "review_packet.jsonl").read_bytes()),
        "review": "Two fresh same-family agent reviewers blinded to condition/model; human review pending",
        "scope": "Prospectively frozen descriptive 2-model x 2-prompt-package contrast on six selected cases. One response per cell does not estimate stochastic variance or population prevalence.",
    }
    (p / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({k: metadata[k] for k in ["requested", "completed", "source_cases", "response_word_limit_deviations"]}))


if __name__ == "__main__":
    main()
