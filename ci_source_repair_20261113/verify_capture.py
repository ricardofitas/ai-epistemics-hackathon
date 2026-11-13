#!/usr/bin/env python3
"""Validate frozen SR-01..SR-36 captures and create an anonymous review packet.

This helper makes no network calls and reads no credentials. Missing, interrupted,
malformed or contradictory captures remain present as unscorable packet rows.
An integrity mismatch is reported and prevents a capture being called complete.
Packet order uses a fixed seed independent of the experimental execution seed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import random

PINS = {
    "protocol.json": "b2946561e395a6ac751d9d282229a16ab3b1892ca247ba8ad63a56a2135cf97f",
    "manifest.jsonl": "a02a82eb6cb83a1063531c3b0d6ecc8441e8a23acb641f81feddf1830b929e85",
}
RUNNER_SHA = "c280811c5f685cdc5b254d5097946835428cd87de6ea58218de1e2cad537fe5e"
PACKET_SEED = 2026111381
FREEZE_TIME = dt.datetime(2026, 11, 13, 6, 44, 30, tzinfo=dt.timezone.utc)
TERMINAL = {"response.completed", "response.incomplete", "response.failed", "response.cancelled"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def final_text(response):
    parts = []
    for item in response.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message" or item.get("role", "assistant") != "assistant":
            continue
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and content.get("type") == "output_text" and isinstance(content.get("text"), str):
                parts.append(content["text"])
    text = "\n".join(parts)
    if not text and isinstance(response.get("output_text"), str):
        text = response["output_text"]
    return text


def read_journal(path, runner):
    """Check saved raw SSE lines and independently derive the last terminal."""
    frames = jsonl(path)
    ends = [frame for frame in frames if frame.get("event") == "capture_end"]
    problems = []
    if len(ends) != 1 or not frames or frames[-1].get("event") != "capture_end":
        problems.append("journal_capture_end_not_unique_final")
    terminal = None
    kind = None
    count = 0
    errors = 0
    partials = 0
    terminals = []
    for frame in frames:
        if frame.get("event") == "capture_end":
            continue
        count += 1
        errors += bool(frame.get("json_error"))
        partials += bool(frame.get("partial_frame"))
        # HTTP-error and non-SSE records deliberately have no raw SSE lines.
        if "raw_lines" in frame:
            decoder = runner.SSEFrameDecoder()
            reconstructed = None
            if not isinstance(frame["raw_lines"], list) or not all(isinstance(v, str) for v in frame["raw_lines"]):
                problems.append("invalid_journal_raw_lines")
            else:
                for line in frame["raw_lines"]:
                    emitted = decoder.feed(line)
                    if emitted is not None:
                        problems.append("embedded_frame_boundary_in_raw_lines")
                reconstructed = decoder.finish(partial=bool(frame.get("partial_frame")))
                keys = ("event", "data_text", "sse_id", "partial_frame", "raw_lines", "data", "json_error")
                if reconstructed is None or any(reconstructed.get(k) != frame.get(k) for k in keys):
                    problems.append("journal_SSE_reconstruction_mismatch")
        payload = frame.get("data")
        if not isinstance(payload, dict):
            continue
        event = payload.get("type") or frame.get("event")
        response = payload.get("response")
        if event in TERMINAL and isinstance(response, dict) and not frame.get("partial_frame"):
            terminal, kind = response, event
            terminals.append(event)
    if len(terminals) > 1:
        problems.append("multiple_terminal_response_events")
    return {"terminal": terminal, "terminal_event": kind, "frames": count,
            "json_errors": errors, "partial_frames": partials,
            "capture_end": ends[-1] if ends else {}, "problems": problems}


def verify_one(row, directory, runner):
    tid = row["trial_id"]
    artifact = directory / "api_artifacts" / (tid + ".json")
    journal = directory / "stream_journals" / (tid + ".jsonl")
    problems = []
    record = {}
    text = ""
    if artifact.is_file():
        try:
            record = load(artifact)
            if not isinstance(record, dict):
                raise ValueError("artifact must be an object")
        except (ValueError, OSError) as exc:
            problems.append("unreadable_artifact:" + type(exc).__name__)
    else:
        problems.append("missing_artifact")
    if record:
        if record.get("trial_id") != tid:
            problems.append("trial_id_mismatch")
        if record.get("attempt_count") != 1:
            problems.append("attempt_count_not_one")
        if record.get("local_capture_error"):
            problems.append("local_capture_error")
        try:
            started = dt.datetime.fromisoformat(record["started_utc"].replace("Z", "+00:00"))
            ended = dt.datetime.fromisoformat(record["ended_utc"].replace("Z", "+00:00"))
            if started.tzinfo is None or started < FREEZE_TIME or ended < started:
                problems.append("invalid_or_prefreeze_capture_time")
        except (ValueError, KeyError, TypeError):
            problems.append("missing_or_invalid_capture_time")
        payload = row["request_payload"]
        if record.get("request_payload") != payload:
            problems.append("request_payload_mismatch")
        if record.get("request_sha256") != hashlib.sha256(canonical(payload)).hexdigest():
            problems.append("request_sha256_mismatch")
        if record.get("requested_model") != payload["model"]:
            problems.append("requested_model_mismatch")
        text = record.get("output_text", "")
        if not isinstance(text, str):
            problems.append("output_text_not_string")
            text = ""
        if record.get("output_text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            problems.append("output_text_sha256_mismatch")
    replay = None
    if journal.is_file():
        try:
            replay = read_journal(journal, runner)
            problems.extend(replay["problems"])
            if record.get("stream_journal_sha256") != sha(journal):
                problems.append("journal_sha256_mismatch")
            if record.get("stream_frame_count") != replay["frames"]:
                problems.append("journal_frame_count_mismatch")
            if record.get("stream_json_error_count") != replay["json_errors"]:
                problems.append("journal_json_error_count_mismatch")
            if record.get("terminal_event") != replay["terminal_event"]:
                problems.append("terminal_event_mismatch")
            if record.get("raw_response") != replay["terminal"]:
                # Nonterminal/error captures need not equal a terminal object.
                if replay["terminal"] is not None:
                    problems.append("terminal_object_mismatch")
            if replay["capture_end"].get("http_status") != record.get("http_status"):
                problems.append("capture_end_http_mismatch")
            if replay["capture_end"].get("transport_error") != record.get("transport_error"):
                problems.append("capture_end_transport_mismatch")
            if replay["terminal"] is not None and final_text(replay["terminal"]) != text:
                problems.append("terminal_text_mismatch")
        except (ValueError, OSError, TypeError, KeyError) as exc:
            problems.append("unreadable_journal:" + type(exc).__name__)
    else:
        problems.append("missing_journal")
    conditions = {
        "http_200": record.get("http_status") == 200,
        "provider_completed": record.get("response_status") == "completed",
        "terminal_completed": record.get("terminal_event") == "response.completed",
        "terminal_seen": record.get("terminal_event_seen") is True,
        "event_stream": record.get("response_content_type") == "text/event-stream",
        "native_sse": record.get("parse_mode") == "sse",
        "no_format_deviation": record.get("stream_format_deviation") is False,
        "no_delta_fallback": record.get("used_delta_fallback") is False,
        "not_stream_incomplete": record.get("stream_incomplete") is False,
        "no_transport_error": record.get("transport_error") is None,
        "no_api_error": record.get("api_error") is None,
        "no_stream_json_errors": record.get("stream_json_error_count") == 0,
        "nonempty_final_text": bool(text.strip()),
        "no_partial_frames": replay is not None and replay["partial_frames"] == 0,
        "replayed_provider_completed": replay is not None and isinstance(replay["terminal"], dict) and replay["terminal"].get("status") == "completed",
    }
    complete = not problems and all(conditions.values())
    report = {"trial_id": tid, "capture_complete": complete,
              "integrity_problems": sorted(set(problems)),
              "capture_conditions": conditions,
              "artifact_sha256": sha(artifact) if artifact.is_file() else None,
              "journal_sha256": sha(journal) if journal.is_file() else None,
              "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
              "artifact_completed_nonempty": record.get("completed_nonempty"),
              "local_capture_error": record.get("local_capture_error")}
    return record, text, report


def write_new(path, text):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def run(args):
    directory = args.experiment_dir.resolve()
    for name, expected in PINS.items():
        if sha(directory / name) != expected:
            raise ValueError("Frozen source hash mismatch: " + name)
    if sha(args.runner) != RUNNER_SHA:
        raise ValueError("Frozen runner hash mismatch")
    spec = importlib.util.spec_from_file_location("frozen_adaption_runner", args.runner)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    manifest, manifest_hash = runner.load_manifest(directory)
    if len(manifest) != 36 or {r["trial_id"] for r in manifest} != {f"SR-{i:02d}" for i in range(1, 37)}:
        raise ValueError("Unexpected frozen trial set")
    if len({r["original_question"] for r in manifest}) != 1:
        raise ValueError("Expected one shared original question")
    expected_ids = {r["trial_id"] for r in manifest}
    for name, suffix in (("api_artifacts", ".json"), ("stream_journals", ".jsonl")):
        if (directory / name).is_dir():
            unexpected = {p.stem for p in (directory / name).glob("*" + suffix)} - expected_ids
            if unexpected:
                raise ValueError("Unexpected capture files: " + repr(sorted(unexpected)))
    aggregate = {}
    global_problems = []
    if (directory / "responses.jsonl").is_file():
        try:
            entries = jsonl(directory / "responses.jsonl")
            aggregate = {r["trial_id"]: r for r in entries}
            if len(aggregate) != len(entries) or set(aggregate) != expected_ids:
                global_problems.append("aggregate_trial_set_mismatch")
        except (ValueError, OSError, KeyError, TypeError):
            global_problems.append("unreadable_aggregate")
    else:
        global_problems.append("missing_aggregate_partial_capture")
    metadata_path = directory / "run_metadata.json"
    if metadata_path.is_file():
        try:
            metadata = load(metadata_path)
            checks = {"manifest_sha256": manifest_hash, "requested": 36,
                      "recorded": 36, "attempts_per_trial": 1,
                      "concurrency": 2, "socket_timeout_seconds": 120,
                      "retries": 0, "transport": "native_sse",
                      "base_url": "https://api.prod.adaptionlabs.ai"}
            if any(metadata.get(k) != v for k, v in checks.items()):
                global_problems.append("run_metadata_protocol_mismatch")
        except (ValueError, OSError, TypeError):
            global_problems.append("unreadable_run_metadata")
    else:
        global_problems.append("missing_run_metadata_partial_capture")
    records = []
    for row in manifest:
        record, text, report = verify_one(row, directory, runner)
        if aggregate and aggregate.get(row["trial_id"]) != record:
            report["integrity_problems"].append("aggregate_artifact_mismatch")
            report["capture_complete"] = False
        records.append((row, text, report, record.get("returned_model")))
    random.Random(PACKET_SEED).shuffle(records)
    packet = []
    key = []
    reports = []
    enriched = []
    for i, (row, text, report, returned_model) in enumerate(records, 1):
        rid = f"I{i:03d}"
        packet.append({"response_id": rid, "case_id": row["case_id"],
                       "original_question": row["original_question"],
                       "response": text, "capture_complete": report["capture_complete"]})
        key.append({"response_id": rid, "trial_id": row["trial_id"],
                    "case_id": row["case_id"], "arm": row["arm"],
                    "requested_model": row["requested_model"], "repetition": row["repetition"]})
        reports.append({"response_id": rid, **report})
        # Companion file is private to the coordinator, like review_key.jsonl.
        enriched.append({"trial_id": row["trial_id"], "case_id": row["case_id"],
                         "requested_model": row["requested_model"],
                         "returned_model": returned_model,
                         "arm": row["arm"], "repetition": row["repetition"],
                         "response": text, "capture_complete": report["capture_complete"]})
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name, rows in (("review_packet.jsonl", packet), ("review_key.jsonl", key),
                       ("responses_enriched.jsonl", sorted(enriched, key=lambda r: r["trial_id"]))):
        write_new(out / name, "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows))
    report = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "status": "capture_verified" if not global_problems and all(not r["integrity_problems"] for r in reports) else "capture_integrity_issues_or_partial",
              "frozen_source_sha256": PINS, "runner_sha256": RUNNER_SHA,
              "manifest_sha256": manifest_hash, "planned": 36,
              "strict_complete": sum(r["capture_complete"] for r in reports),
              "unscorable": sum(not r["capture_complete"] for r in reports),
              "global_issues": global_problems, "packet_shuffle_seed": PACKET_SEED,
              "review_packet_sha256": sha(out / "review_packet.jsonl"),
              "review_key_sha256": sha(out / "review_key.jsonl"),
              "responses_enriched_sha256": sha(out / "responses_enriched.jsonl"),
              "helper_sha256": sha(Path(__file__)),
              "rows": sorted(reports, key=lambda r: r["trial_id"]),
              "scope": "Operational capture validity only; no scientific labels assigned. Every frozen attempt remains in the packet. Reviewers must label incomplete captures unscorable."}
    write_new(out / "capture_integrity.json", json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output_dir": str(out), "planned": 36,
                      "strict_complete": report["strict_complete"], "unscorable": report["unscorable"],
                      "status": report["status"], "packet_sha256": report["review_packet_sha256"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--runner", type=Path, default=Path("scripts/run_adaption_stream_pilot.py"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
