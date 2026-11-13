#!/usr/bin/env python3
"""Audit a frozen 60-request SSE wave and create a model-blind review packet."""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import re

TERMINALS = {"response.completed", "response.incomplete", "response.failed", "response.cancelled"}


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def instant(value):
    value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("An explicit UTC offset is required")
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def write(path, value, jsonl=False):
    text = ("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in value)
            if jsonl else json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    if path.name in {"review_packet.jsonl", "review_key.jsonl"} and path.exists():
        if path.read_text() != text:
            raise ValueError("Refusing to change an existing review packet/key")
        return
    path.write_text(text)


def final_text(response):
    parts = [part["text"] for item in response.get("output", []) or []
             if isinstance(item, dict) and item.get("type") == "message"
             and item.get("role", "assistant") == "assistant"
             for part in item.get("content", []) or []
             if isinstance(part, dict) and part.get("type") == "output_text"
             and isinstance(part.get("text"), str)]
    return "\n".join(parts) or response.get("output_text", "") or ""


def audit_capture(directory, job, record, freeze):
    tid = job["trial_id"]
    artifact = directory / "api_artifacts" / f"{tid}.json"
    if load(artifact) != record:
        raise ValueError(f"Aggregate differs from individual artifact: {tid}")
    if record.get("attempt_count") != 1:
        raise ValueError(f"Missing or multiple declared attempts: {tid}")
    if record.get("local_capture_error"):
        # Retain an operational failure without pretending missing evidence was checked.
        return {"capture_integrity": "unverifiable_local_capture_error",
                "journal_verified": False, "completion_verified": False,
                "terminal_status_consistent": None, "event_status_mismatch": False}
    for flag in ["terminal_event_seen", "used_delta_fallback", "stream_incomplete",
                 "stream_format_deviation", "completed_nonempty"]:
        if not isinstance(record.get(flag), bool):
            raise ValueError(f"Missing/nonboolean capture flag {flag}: {tid}")
    if record.get("request_payload") != job["request_payload"]:
        raise ValueError(f"Changed frozen payload: {tid}")
    if record.get("request_sha256") != sha(canonical(job["request_payload"])):
        raise ValueError(f"Wire hash mismatch: {tid}")
    if record.get("output_text_sha256") != sha(record["output_text"].encode()):
        raise ValueError(f"Text hash mismatch: {tid}")
    if instant(record["started_utc"]) <= freeze or instant(record["ended_utc"]) < instant(record["started_utc"]):
        raise ValueError(f"Invalid start/end relative to freeze: {tid}")
    # The historical absolute path is metadata. Resolve local files portably by trial ID.
    journal = directory / "stream_journals" / f"{tid}.jsonl"
    if not journal.exists() or sha(journal.read_bytes()) != record.get("stream_journal_sha256"):
        raise ValueError(f"Missing/changed durable journal: {tid}")
    events = rows(journal)
    endings = [e for e in events if e.get("event") == "capture_end"]
    if len(endings) != 1 or events[-1] != endings[0]:
        raise ValueError(f"Journal lacks its single terminal capture receipt: {tid}")
    for field in ["http_status", "terminal_event", "transport_error"]:
        if endings[0].get(field) != record.get(field):
            raise ValueError(f"Capture receipt differs in {field}: {tid}")
    frames = events[:-1]
    if len(frames) != record.get("stream_frame_count"):
        raise ValueError(f"Journal frame count mismatch: {tid}")
    if sum(bool(e.get("json_error")) for e in frames) != record.get("stream_json_error_count"):
        raise ValueError(f"Journal JSON-error count mismatch: {tid}")
    terminal = []
    for frame in frames:
        payload = frame.get("data")
        if not isinstance(payload, dict):
            continue
        kind = payload.get("type") or frame.get("event")
        if kind in TERMINALS and isinstance(payload.get("response"), dict) and not frame.get("partial_frame"):
            terminal.append((kind, payload["response"]))
    if bool(terminal) != bool(record.get("terminal_event_seen")):
        raise ValueError(f"Terminal-event flag contradicts journal: {tid}")
    terminal_status_consistent = None
    if terminal:
        kind, provider = terminal[-1]
        if kind != record.get("terminal_event") or provider != record.get("raw_response"):
            raise ValueError(f"Captured provider terminal differs from journal: {tid}")
        if provider.get("status") != record.get("response_status"):
            raise ValueError(f"Status differs from terminal provider object: {tid}")
        expected_statuses = {"response.completed": {"completed"},
                             "response.incomplete": {"incomplete"},
                             "response.failed": {"failed"},
                             "response.cancelled": {"cancelled", "canceled"}}
        # A contradictory provider terminal is an auditable operational outcome.
        # Preserve both original flags/statuses; it is never a completed capture.
        terminal_status_consistent = provider.get("status") in expected_statuses[kind]
        if not record.get("used_delta_fallback") and final_text(provider) != record["output_text"]:
            raise ValueError(f"Final text differs from terminal final text: {tid}")
    complete = bool(record.get("http_status") == 200 and terminal
                    and terminal[-1][0] == "response.completed"
                    and record.get("response_status") == "completed"
                    and record["output_text"].strip()
                    and not record.get("stream_incomplete")
                    and not record.get("used_delta_fallback")
                    and not record.get("stream_format_deviation")
                    and record.get("transport_error") is None)
    if complete != bool(record.get("completed_nonempty")):
        raise ValueError(f"Completion promoted/demoted inconsistently: {tid}")
    return {"capture_integrity": "verified", "journal_verified": True,
            "completion_verified": complete,
            "terminal_status_consistent": terminal_status_consistent,
            "event_status_mismatch": terminal_status_consistent is False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--freeze-time", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.freeze_commit):
        raise ValueError("Require the independently checked Git freeze commit")
    p = args.directory
    protocol = load(p / "protocol.json")
    for name in ["manifest", "casepack", "review_casepack"]:
        path = p / ("manifest.jsonl" if name == "manifest" else name + ".json")
        if sha(path.read_bytes()) != protocol["hashes"][name]:
            raise ValueError(f"Changed frozen {name}")
    jobs, captures = rows(p / "manifest.jsonl"), rows(p / "responses.jsonl")
    if len(jobs) != 60 or len(captures) != 60:
        raise ValueError("Require every one of the 60 planned captures")
    if Counter(j["stage"] for j in jobs) != {"new_screen": 24, "selected_recurrence": 36}:
        raise ValueError("Allocation is not the frozen 24+36 design")
    if len({j["case_id"] for j in jobs}) != 9 or len({j["trial_id"] for j in jobs}) != 60:
        raise ValueError("Wrong case/trial coverage")
    cells = defaultdict(list)
    for j in jobs:
        cells[(j["case_id"], j["requested_model"], j["stage"])].append(j)
    if len(cells) != 36:
        raise ValueError("Expected 9×4 distinct case/configuration cells")
    for case in {j["case_id"] for j in jobs}:
        case_jobs = [j for j in jobs if j["case_id"] == case]
        if {j["requested_model"] for j in case_jobs} != set(protocol["models"]) or len({j["stage"] for j in case_jobs}) != 1:
            raise ValueError(f"Incomplete model/stage coverage: {case}")
    if Counter(next(j["stage"] for j in jobs if j["case_id"] == c)
               for c in {j["case_id"] for j in jobs}) != {"new_screen": 6, "selected_recurrence": 3}:
        raise ValueError("Require six new and three recurrence source cases")
    for (_, _, stage), cell in cells.items():
        expected = [1] if stage == "new_screen" else [1, 2, 3]
        if sorted(j["repetition"] for j in cell) != expected:
            raise ValueError("Missing/duplicate repetition")
    recorded = {r["trial_id"]: r for r in captures}
    if len(recorded) != 60 or set(recorded) != {j["trial_id"] for j in jobs}:
        raise ValueError("Missing/duplicate capture IDs")
    freeze = instant(args.freeze_time)
    enriched = []
    for job in jobs:
        raw = recorded[job["trial_id"]]
        audit = audit_capture(p, job, raw, freeze)
        enriched.append({**raw, **audit, "case_id": job["case_id"], "stage": job["stage"],
                         "repetition": job["repetition"], "requested_model": job["requested_model"],
                         "response": raw.get("output_text", ""),
                         "capture_complete": audit["completion_verified"]})
    write(p / "responses_enriched.jsonl", enriched, jsonl=True)
    shuffled = enriched.copy()
    random.Random(2026111313).shuffle(shuffled)
    packet, key = [], []
    for i, r in enumerate(shuffled, 1):
        rid = f"Q{i:02d}"
        packet.append({"response_id": rid, "case_id": r["case_id"], "response": r["response"],
                       "capture_complete": r["capture_complete"], "incomplete_details": r.get("incomplete_details")})
        key.append({"response_id": rid, "trial_id": r["trial_id"]})
    write(p / "review_packet.jsonl", packet, jsonl=True)
    write(p / "review_key.jsonl", key, jsonl=True)
    def group(field):
        return {k: {"attempted": len(v), "complete": sum(r["capture_complete"] for r in v)}
                for k, v in sorted(((k, [r for r in enriched if r[field] == k])
                                    for k in {r[field] for r in enriched}))}
    metadata = load(p / "run_metadata.json")
    if metadata.get("requested") != 60 or metadata.get("recorded") != 60 or metadata.get("retries") != 0:
        raise ValueError("Run receipt conflicts with frozen allocation")
    checked = [r for r in enriched if r["capture_integrity"] == "verified"]
    integrity = {"requested": 60, "recorded": 60, "completed_nonempty": sum(r["capture_complete"] for r in enriched),
                 "freeze_commit": args.freeze_commit, "freeze_utc": args.freeze_time,
                 "independent_freeze_lookup": "Caller supplies externally checked Git commit/time; script performs no network lookup",
                 "verified_capture_records": len(checked), "unverifiable_local_capture_errors": 60 - len(checked),
                 "all_wire_text_artifact_journal_checks_pass": len(checked) == 60,
                 "all_observed_starts_after_freeze": True, "source_cases": 9,
                 "by_case": group("case_id"), "by_stage": group("stage"),
                 "new_families_with_final_answers": len({r["case_id"] for r in enriched if r["stage"] == "new_screen" and r["capture_complete"]}),
                 "http_status_counts": dict(Counter(str(r.get("http_status")) for r in enriched)),
                 "response_status_counts": dict(Counter(str(r.get("response_status")) for r in enriched)),
                 "terminal_events_seen": sum(bool(r.get("terminal_event_seen")) for r in enriched),
                 "delta_fallbacks": sum(bool(r.get("used_delta_fallback")) for r in enriched),
                 "stream_format_deviations": sum(bool(r.get("stream_format_deviation")) for r in enriched),
                 "terminal_status_mismatches": sum(bool(r.get("event_status_mismatch")) for r in enriched),
                 "operator_provider_deviation_counts": {
                     "terminal_event_status_mismatch": sum(bool(r.get("event_status_mismatch")) for r in enriched),
                     "delta_fallback": sum(bool(r.get("used_delta_fallback")) for r in enriched),
                     "stream_format_deviation": sum(bool(r.get("stream_format_deviation")) for r in enriched)},
                 "word_cap_deviations": sum(len(r["response"].split()) > 300 for r in enriched),
                 "reported_usage_cost_sum": sum((r.get("usage") or {}).get("cost") or 0 for r in enriched),
                 "cost_note": "Provider usage.cost is not a verified complete bill, wallet balance or USD conversion",
                 "manifest_sha256": sha((p / "manifest.jsonl").read_bytes()),
                 "packet_sha256": sha((p / "review_packet.jsonl").read_bytes()),
                 "run_receipt": metadata, "human_review": "pending"}
    write(p / "integrity.json", integrity)
    print(json.dumps(integrity))


if __name__ == "__main__":
    main()
