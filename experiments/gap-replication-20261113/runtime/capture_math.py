#!/usr/bin/env python3
"""Strict, independent replay of fixed math captures; no network calls or repairs."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

from scoring import parse_answers, score_answer

RUNNER_SHA = "c280811c5f685cdc5b254d5097946835428cd87de6ea58218de1e2cad537fe5e"
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


def verify_one(row, directory, runner, freeze_time):
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
            if started.tzinfo is None or started < freeze_time or ended < started:
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


def run(args):
    directory = args.directory.resolve()
    protocol_path = directory / "protocol.json"
    if sha(protocol_path) != args.freeze_protocol_sha256:
        raise ValueError("Protocol differs from externally published freeze")
    if len(args.freeze_commit) != 40 or any(c not in "0123456789abcdef" for c in args.freeze_commit):
        raise ValueError("Real published Git freeze commit required")
    instant = dt.datetime.fromisoformat(args.freeze_time.replace("Z", "+00:00"))
    if instant.tzinfo is None or instant > dt.datetime.now(dt.timezone.utc):
        raise ValueError("Freeze instant must be real and earlier than capture")
    protocol = load(protocol_path)
    for name, expected in protocol["source_sha256"].items():
        if sha(directory / name) != expected:
            raise ValueError("Frozen source changed: " + name)
    for name, expected in protocol.get("implementation_sha256", {}).items():
        if sha(directory / name) != expected:
            raise ValueError("Frozen implementation changed: " + name)
    if sha(args.runner) != RUNNER_SHA or protocol["runner_sha256"] != RUNNER_SHA:
        raise ValueError("Original SSE runner mismatch")
    spec = importlib.util.spec_from_file_location("frozen_math_runner", args.runner)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    manifest, manifest_hash = runner.load_manifest(directory)
    if len(manifest) != 80 or {r["trial_id"] for r in manifest} != {f"GR-{i:03d}" for i in range(1, 81)}:
        raise ValueError("Expected exact frozen 80-request cohort")
    models = protocol["models"]
    tasks = {r["task_id"]: r for r in load(directory / "task_key.json")["rows"]}
    if len(tasks) != 120 or len(models) != 2:
        raise ValueError("Expected two candidates and 120 source tasks")
    memberships = Counter((r["requested_model"], item) for r in manifest for item in r["item_ids"])
    if memberships != Counter({(m, item): 1 for m in models for item in tasks}):
        raise ValueError("Candidate task allocation changed")
    expected_trials = {r["trial_id"] for r in manifest}
    for subdir, suffix in (("api_artifacts", ".json"), ("stream_journals", ".jsonl")):
        extras = {p.stem for p in (directory / subdir).glob("*" + suffix)} - expected_trials
        if extras:
            raise ValueError("Unexpected capture file IDs")
    for output in ("prediction_rows.jsonl", "capture_integrity.json"):
        if (directory / output).exists():
            raise FileExistsError("Capture analysis output already exists: " + output)
    reports, predictions = [], []
    aggregate = {}
    global_issues = []
    if (directory / "responses.jsonl").is_file():
        try:
            entries = jsonl(directory / "responses.jsonl")
            aggregate = {r["trial_id"]: r for r in entries}
            if len(aggregate) != len(entries) or set(aggregate) != expected_trials:
                global_issues.append("aggregate_trial_set_mismatch")
        except (ValueError, KeyError, TypeError, OSError):
            global_issues.append("unreadable_aggregate")
    else:
        global_issues.append("missing_aggregate_partial_run")
    metadata = directory / "run_metadata.json"
    if metadata.is_file():
        try:
            meta = load(metadata)
            if meta.get("manifest_sha256") != manifest_hash or meta.get("requested") != 80 or meta.get("attempts_per_trial") != 1 or meta.get("retries") != 0:
                global_issues.append("run_metadata_deviation")
        except (ValueError, OSError):
            global_issues.append("unreadable_run_metadata")
    else:
        global_issues.append("missing_run_metadata_partial_run")
    for row in manifest:
        record, text, report = verify_one(row, directory, runner, instant)
        if row["trial_id"] in aggregate and aggregate[row["trial_id"]] != record:
            report["integrity_problems"].append("aggregate_artifact_mismatch")
            report["capture_complete"] = False
        parsed, format_error = None, None
        if report["capture_complete"]:
            try:
                parsed = parse_answers(text, row["item_ids"])
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                format_error = type(exc).__name__ + ": " + str(exc)
        report.update(requested_model=row["requested_model"], item_ids=row["item_ids"],
                      batch_json_valid=parsed is not None, format_error=format_error)
        reports.append(report)
        for item_id in row["item_ids"]:
            if parsed is None:
                scored = {"label": "unknown", "parsed_answer": None,
                          "score_lower": 0, "score_upper": 1, "format_valid": False}
            else:
                scored = score_answer(parsed[item_id], tasks[item_id]["gold_answer"])
            predictions.append({"model": row["requested_model"], "task_id": item_id,
                                "trial_id": row["trial_id"], "capture_complete": report["capture_complete"],
                                "raw_answer": parsed[item_id] if parsed is not None else None, **scored})
    with (directory / "prediction_rows.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for row in predictions:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    receipt = {"status": "capture_verified", "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "freeze_commit": args.freeze_commit, "freeze_time": args.freeze_time,
               "protocol_sha256": sha(protocol_path), "manifest_sha256": manifest_hash,
               "prediction_rows_sha256": sha(directory / "prediction_rows.jsonl"),
               "helper_sha256": sha(Path(__file__)), "runner_sha256": RUNNER_SHA,
               "planned_requests": 80, "predictions": len(predictions),
               "strict_complete_requests": sum(r["capture_complete"] for r in reports),
               "valid_json_requests": sum(r["batch_json_valid"] for r in reports),
               "known_item_scores": sum(r["score_lower"] == r["score_upper"] for r in predictions),
               "global_issues": global_issues, "requests": reports,
               "scope": "Operational and answer-format replay only. Unknown outcomes are retained as [0,1]; no model calls or repairs."}
    with (directory / "capture_integrity.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: receipt[k] for k in ("status", "planned_requests", "predictions", "strict_complete_requests", "valid_json_requests", "known_item_scores")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--freeze-time", required=True)
    parser.add_argument("--freeze-protocol-sha256", required=True)
    run(parser.parse_args())


