#!/usr/bin/env python3
"""Capture a frozen Adaption Responses SSE pilot without retries or credential logs.

Manifest: JSONL rows containing trial_id and the exact request_payload object.
The canonical UTF-8 JSON body is stored with its SHA256 in every trial artifact.
ADAPTION_API_KEY is read from the environment, otherwise from a hidden prompt.
No API request is made by --dry-run. Output and streaming journals cannot be reused.
Socket timeout is per blocking operation, not a total wall-clock deadline.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import tempfile
import time
import urllib.error
import urllib.request

BASE = "https://api.prod.adaptionlabs.ai"
HEADERS_TO_RETAIN = ("x-request-id", "request-id", "x-correlation-id", "traceparent")
TERMINAL_EVENTS = {"response.completed", "response.incomplete", "response.failed", "response.cancelled"}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sanitize(value, credential):
    if isinstance(value, str):
        return value.replace(credential, "[REDACTED_CREDENTIAL]") if credential else value
    if isinstance(value, list):
        return [sanitize(x, credential) for x in value]
    if isinstance(value, dict):
        return {sanitize(k, credential): sanitize(v, credential) for k, v in value.items()}
    return value


def atomic_json(path, value):
    """Publish a complete JSON artifact; fail rather than overwrite an old artifact."""
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.link(temporary, path)  # Atomic exclusive publication on the same filesystem.
    finally:
        os.unlink(temporary)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward bearer credentials or silently alter a POST.


def load_manifest(directory):
    path = directory / "manifest.jsonl"
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Empty manifest")
    seen = set()
    for row in rows:
        tid, payload = row.get("trial_id"), row.get("request_payload")
        if not isinstance(tid, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", tid) or tid in seen:
            raise ValueError("Missing, unsafe, or repeated trial_id")
        seen.add(tid)
        if not isinstance(payload, dict) or not isinstance(payload.get("model"), str):
            raise ValueError(f"Invalid request_payload/model: {tid}")
        if not payload["model"] or payload["model"].startswith("stack:"):
            raise ValueError(f"Pilot requires an explicit hosted model: {tid}")
        if not isinstance(payload.get("input"), str) or not payload["input"].strip():
            raise ValueError(f"Pilot requires a standalone string input: {tid}")
        tokens = payload.get("max_output_tokens")
        if type(tokens) is not int or not 1 <= tokens <= 16384:
            raise ValueError(f"Require explicit 1..16384 output-token bound: {tid}")
        if (payload.get("tools") != [] or payload.get("agentic_memory") is not False
                or payload.get("store") is not False or payload.get("tool_choice") != "none"):
            raise ValueError(f"Explicit tools=[], memory=false, store=false, tool_choice=none required: {tid}")
        if "previous_response_id" in payload or payload.get("stream") is not True:
            raise ValueError(f"No history and explicit stream=true required: {tid}")
        body = canonical(payload)
        if row.get("request_sha256") not in (None, hashlib.sha256(body).hexdigest()):
            raise ValueError(f"Frozen request hash mismatch: {tid}")
    return rows, hashlib.sha256(raw).hexdigest()


def output_text(response):
    """Extract final assistant text only; do not fold reasoning/tool output into it."""
    if not isinstance(response, dict):
        return ""
    parts = []
    for item in response.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        if item.get("role", "assistant") != "assistant":
            continue
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
    return "\n".join(parts)


class SSEFrameDecoder:
    """SSE field parser: multiline data, comments, CRLF and EOF partial frames."""
    def __init__(self):
        self.event = ""
        self.data = []
        self.event_id = None
        self.raw_lines = []

    def pending(self):
        return bool(self.raw_lines)

    def finish(self, partial=False):
        if not self.pending():
            return None
        frame = {"event": self.event or "message", "data_text": "\n".join(self.data),
                 "sse_id": self.event_id, "partial_frame": partial,
                 "raw_lines": self.raw_lines.copy()}
        try:
            frame["data"] = json.loads(frame["data_text"]) if self.data else None
            frame["json_error"] = False
        except json.JSONDecodeError:
            frame["data"] = None
            frame["json_error"] = frame["data_text"] != "[DONE]"
        self.__init__()
        return frame

    def feed(self, raw_line):
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", errors="replace")
        else:
            line = raw_line
        line = line.rstrip("\r\n")
        if not line:
            return self.finish()
        self.raw_lines.append(line)
        if line.startswith(":"):
            return None
        field, separator, value = line.partition(":")
        if separator and value.startswith(" "):
            value = value[1:]
        if field == "data":
            self.data.append(value)
        elif field == "event":
            self.event = value
        elif field == "id" and "\x00" not in value:
            self.event_id = value
        return None


def request_stream_once(credential, timeout, body, journal_path, opener=None):
    """One exact-host POST. Append each sanitized SSE frame durably as it arrives.

    The optional opener is for offline fixtures, not exposed through the CLI.
    A crash can leave a journal without its final artifact; never regenerate it.
    """
    url = BASE + "/api/v1/responses"
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": "Bearer " + credential, "Accept": "text/event-stream",
        "Content-Type": "application/json"})
    opener = opener or urllib.request.build_opener(NoRedirect())
    status, retained_headers, error = None, {}, None
    terminal, terminal_event, latest = None, None, None
    deltas, event_count, json_errors = {}, 0, 0
    content_type, raw_non_sse, parse_mode = None, None, "sse"
    decoder = SSEFrameDecoder()
    # Exclusive journal exists before the POST; fsync after every captured frame.
    with journal_path.open("x", encoding="utf-8") as journal:
        def capture(frame):
            nonlocal terminal, terminal_event, latest, event_count, json_errors
            if frame is None:
                return
            safe = sanitize(frame, credential)
            safe["captured_utc"] = now()
            journal.write(json.dumps(safe, ensure_ascii=False) + "\n")
            journal.flush()
            os.fsync(journal.fileno())
            event_count += 1
            json_errors += bool(frame.get("json_error"))
            payload = safe.get("data")
            if not isinstance(payload, dict):
                return
            kind = payload.get("type") or safe["event"]
            response = payload.get("response")
            if isinstance(response, dict):
                latest = response
                if kind in TERMINAL_EVENTS and not safe.get("partial_frame"):
                    terminal, terminal_event = response, kind
            if kind == "response.output_text.delta" and isinstance(payload.get("delta"), str):
                part = tuple(payload.get(k) if type(payload.get(k)) is int else 0
                             for k in ["output_index", "content_index"])
                deltas.setdefault(part, []).append(payload["delta"])

        try:
            with opener.open(request, timeout=timeout) as result:
                status = result.status
                retained_headers = {h: result.headers[h] for h in HEADERS_TO_RETAIN if result.headers.get(h)}
                content_type = result.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if content_type == "application/json":
                    # Explicitly report a provider ignoring stream=true; do not retry.
                    parse_mode = "json_response_to_stream_request"
                    raw = result.read().decode("utf-8", errors="replace")
                    try:
                        latest = json.loads(raw)
                        if not isinstance(latest, dict):
                            latest = None
                        capture({"event": "non_sse_json_response", "data": latest,
                                 "data_text": raw, "partial_frame": False, "json_error": False})
                    except json.JSONDecodeError:
                        raw_non_sse = sanitize(raw, credential)
                else:
                    while True:
                        line = result.readline()
                        if not line:
                            capture(decoder.finish(partial=True))
                            break
                        frame = decoder.feed(line)
                        capture(frame)
                        if terminal is not None:
                            # Terminal object carries final output/status/usage; avoid
                            # waiting on a kept-open connection after completion.
                            break
        except urllib.error.HTTPError as exc:
            status = exc.code
            retained_headers = {h: exc.headers[h] for h in HEADERS_TO_RETAIN if exc.headers.get(h)}
            try:
                raw = exc.read().decode("utf-8", errors="replace")
                try:
                    raw_non_sse = json.loads(raw)
                    if isinstance(raw_non_sse, dict):
                        latest, raw_non_sse = raw_non_sse, None
                except json.JSONDecodeError:
                    raw_non_sse = raw
            except Exception:
                raw_non_sse = None
            error = {"type": "HTTPError", "message": f"HTTP {status}; no retry attempted"}
            capture({"event": "http_error", "data": latest,
                     "data_text": raw_non_sse or "", "partial_frame": False,
                     "json_error": False})
        except (TimeoutError, socket.timeout) as exc:
            error = {"type": type(exc).__name__, "message": "Socket operation timed out; no retry attempted"}
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": "Stream request/capture failed; no retry attempted"}
        finally:
            # An interrupted multiline frame is retained, not silently discarded.
            capture(decoder.finish(partial=True))
            outcome = sanitize({"event": "capture_end", "captured_utc": now(),
                                "http_status": status, "terminal_event": terminal_event,
                                "transport_error": error}, credential)
            journal.write(json.dumps(outcome, ensure_ascii=False) + "\n")
            journal.flush()
            os.fsync(journal.fileno())
    data = terminal or (latest if isinstance(latest, dict) else {})
    answer = output_text(data)
    text_source = "terminal_message_output_text" if terminal is not None else "nonterminal_message_output_text"
    if parse_mode != "sse":
        text_source = "non_sse_json_message_output_text"
    if not answer and isinstance(data.get("output_text"), str):
        answer = data["output_text"]
        text_source = "terminal_top_level_output_text" if terminal is not None else "nonterminal_top_level_output_text"
    used_fallback = False
    if not answer and deltas:
        answer = "\n".join("".join(deltas[k]) for k in sorted(deltas))
        used_fallback = True
        text_source = "accumulated_output_text_deltas_fallback"
    missing_terminal = parse_mode == "sse" and terminal is None
    if missing_terminal and error is None:
        error = {"type": "MissingTerminalEvent", "message": "Stream ended without a terminal response event; no retry attempted"}
    return sanitize({"http_status": status, "response_headers": retained_headers,
                     "response_content_type": content_type, "parse_mode": parse_mode,
                     "stream_format_deviation": parse_mode != "sse",
                     "raw_response": data or None, "non_json_response_text": raw_non_sse,
                     "transport_error": error, "terminal_event": terminal_event,
                     "terminal_event_seen": terminal is not None,
                     "stream_frame_count": event_count, "stream_json_error_count": json_errors,
                     "stream_journal_path": str(journal_path),
                     "stream_journal_sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest(),
                     "text_source": text_source, "used_delta_fallback": used_fallback,
                     "stream_incomplete": missing_terminal or used_fallback or parse_mode != "sse",
                     "captured_output_text": answer}, credential)


def run_trial(row, credential, timeout, artifacts, journals, opener=None):
    tid, payload = row["trial_id"], row["request_payload"]
    started, tick = now(), time.monotonic()
    body = canonical(payload)
    result = request_stream_once(credential, timeout, body, journals / f"{tid}.jsonl", opener=opener)
    raw = result["raw_response"]
    data = raw if isinstance(raw, dict) else {}
    answer = result.pop("captured_output_text")
    record = {"trial_id": tid, "started_utc": started, "ended_utc": now(),
              "elapsed_seconds": round(time.monotonic() - tick, 6), "attempt_count": 1,
              "requested_model": payload["model"], "returned_model": data.get("model"),
              "response_id": data.get("id"), "request_payload": payload,
              "request_sha256": hashlib.sha256(body).hexdigest(),
              "response_status": data.get("status"), "incomplete_details": data.get("incomplete_details"),
              "api_error": data.get("error"), "usage": data.get("usage"),
              "output_text": answer, "output_text_sha256": hashlib.sha256(answer.encode()).hexdigest(),
              "output_words_whitespace": len(answer.split()), "empty_output": not answer.strip(),
              "capture_note": "Final message/output_text preferred; delta fallback explicitly flagged and never silently completed; durable sanitized SSE journal retained",
              **result}
    record["completed_nonempty"] = (result["http_status"] == 200 and
                                       data.get("status") == "completed" and bool(answer.strip())
                                       and not result["stream_incomplete"] and result["transport_error"] is None)
    record = sanitize(record, credential)
    atomic_json(artifacts / f"{tid}.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 0 < args.timeout <= 120 or not 1 <= args.concurrency <= 4:
        parser.error("Require timeout in (0,120] and concurrency in [1,4]")
    directory = args.experiment_dir
    rows, manifest_hash = load_manifest(directory)
    if args.dry_run:
        print(json.dumps({"dry_run": True, "requests": len(rows),
                          "maximum_generated_tokens": sum(r["request_payload"]["max_output_tokens"] for r in rows),
                          "manifest_sha256": manifest_hash, "transport": "native_sse"}))
        return
    # Fail before prompting for a secret or making a call if output exists.
    if any((directory / name).exists() for name in ["responses.jsonl", "api_artifacts", "stream_journals", "run_metadata.json"]):
        raise FileExistsError("Prior artifacts/journals exist; refusing to overwrite or regenerate")
    artifacts = directory / "api_artifacts"
    journals = directory / "stream_journals"
    artifacts.mkdir(exist_ok=False)
    journals.mkdir(exist_ok=False)
    credential = os.environ.get("ADAPTION_API_KEY") or getpass.getpass("Adaption key (hidden): ")
    if not credential or "\n" in credential or "\r" in credential:
        raise ValueError("Missing/invalid Adaption credential")
    records = {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(run_trial, row, credential, args.timeout, artifacts, journals): row["trial_id"] for row in rows}
        for future in as_completed(futures):
            tid = futures[future]
            try:
                record = future.result()
            except Exception as exc:
                # Preserve a local capture failure; never retry its inference call.
                record = {"trial_id": tid, "attempt_count": 1,
                          "local_capture_error": type(exc).__name__,
                          "note": "Call may have occurred; not retried. Inspect existing artifact before interpretation."}
                if not (artifacts / f"{tid}.json").exists():
                    atomic_json(artifacts / f"{tid}.json", record)
            records[tid] = record
            print(json.dumps({"trial_id": tid, "http_status": record.get("http_status"),
                              "response_status": record.get("response_status"),
                              "empty_output": record.get("empty_output"),
                              "local_capture_error": record.get("local_capture_error")}), flush=True)
    # Individual complete artifacts survive interruption; this ordered aggregate is final only.
    aggregate = "".join(json.dumps(records[r["trial_id"]], ensure_ascii=False) + "\n" for r in rows)
    fd, temporary = tempfile.mkstemp(prefix=".responses-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(aggregate)
            f.flush()
            os.fsync(f.fileno())
        os.link(temporary, directory / "responses.jsonl")
    finally:
        os.unlink(temporary)
    atomic_json(directory / "run_metadata.json", {
        "completed_capture_utc": now(), "manifest_sha256": manifest_hash,
        "requested": len(rows), "recorded": len(records), "attempts_per_trial": 1,
        "concurrency": args.concurrency, "socket_timeout_seconds": args.timeout,
        "retries": 0, "base_url": BASE, "history": "none; standalone requests",
        "transport": "native_sse", "socket_timeout_scope": "Per blocking socket operation, not hard wall-clock",
        "exact_provider_snapshot": "Not established merely by returned model alias",
        "completed_nonempty": sum(bool(r.get("completed_nonempty")) for r in records.values())})
    print(json.dumps({"responses_path": str(directory / "responses.jsonl"),
                      "requested": len(rows), "recorded": len(records),
                      "completed_nonempty": sum(bool(r.get("completed_nonempty")) for r in records.values())}))


if __name__ == "__main__":
    main()
