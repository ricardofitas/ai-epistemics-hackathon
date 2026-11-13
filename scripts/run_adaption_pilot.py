#!/usr/bin/env python3
"""Run a frozen, bounded Adaption Responses pilot without retries or credential logs.

Manifest: JSONL rows containing trial_id and the exact request_payload object.
The canonical UTF-8 JSON body is stored with its SHA256 in every trial artifact.
ADAPTION_API_KEY is read from the environment, otherwise from a hidden prompt.
No API request is made by --dry-run. The output directory cannot be reused.
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
        if type(tokens) is not int or not 1 <= tokens <= 4096:
            raise ValueError(f"Require explicit 1..4096 output-token bound: {tid}")
        if (payload.get("tools") != [] or payload.get("agentic_memory") is not False
                or payload.get("store") is not False or payload.get("tool_choice") != "none"):
            raise ValueError(f"Explicit tools=[], memory=false, store=false, tool_choice=none required: {tid}")
        if "previous_response_id" in payload or payload.get("stream") is True:
            raise ValueError(f"No history or streaming in this one-shot pilot: {tid}")
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


def request_once(url, credential, timeout, body=None):
    if url not in (BASE + "/api/v1/responses", BASE + "/api/v1/models?type=hosted"):
        raise ValueError("Only the two fixed official Adaption endpoints are permitted")
    headers = {"Authorization": "Bearer " + credential, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers,
                                     method="POST" if body is not None else "GET")
    opener = urllib.request.build_opener(NoRedirect())
    status, retained_headers, raw, error = None, {}, b"", None
    try:
        with opener.open(request, timeout=timeout) as result:
            status = result.status
            retained_headers = {h: result.headers[h] for h in HEADERS_TO_RETAIN if result.headers.get(h)}
            raw = result.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        retained_headers = {h: exc.headers[h] for h in HEADERS_TO_RETAIN if exc.headers.get(h)}
        raw = exc.read()
        error = {"type": "HTTPError", "message": f"HTTP {status}; no retry attempted"}
    except (TimeoutError, socket.timeout) as exc:
        error = {"type": type(exc).__name__, "message": "Socket/request timeout; no retry attempted"}
    except Exception as exc:
        # Avoid exception reprs, which may contain request/header/credential material.
        error = {"type": type(exc).__name__, "message": "Request failed; no retry attempted"}
    try:
        decoded = json.loads(raw.decode("utf-8")) if raw else None
        non_json_text = None
    except (UnicodeDecodeError, json.JSONDecodeError):
        decoded, non_json_text = None, raw.decode("utf-8", errors="replace")
    return sanitize({"http_status": status, "response_headers": retained_headers,
                     "raw_response": decoded, "non_json_response_text": non_json_text,
                     "transport_error": error}, credential)


def run_trial(row, credential, timeout, artifacts):
    tid, payload = row["trial_id"], row["request_payload"]
    started, tick = now(), time.monotonic()
    body = canonical(payload)
    result = request_once(BASE + "/api/v1/responses", credential, timeout, body)
    raw = result["raw_response"]
    data = raw if isinstance(raw, dict) else {}
    answer = output_text(data)
    record = {"trial_id": tid, "started_utc": started, "ended_utc": now(),
              "elapsed_seconds": round(time.monotonic() - tick, 6), "attempt_count": 1,
              "requested_model": payload["model"], "returned_model": data.get("model"),
              "response_id": data.get("id"), "request_payload": payload,
              "request_sha256": hashlib.sha256(body).hexdigest(),
              "response_status": data.get("status"), "incomplete_details": data.get("incomplete_details"),
              "api_error": data.get("error"), "usage": data.get("usage"),
              "output_text": answer, "output_text_sha256": hashlib.sha256(answer.encode()).hexdigest(),
              "output_words_whitespace": len(answer.split()), "empty_output": not answer.strip(),
              "capture_note": "Final message/output_text only; raw sanitized response retained separately",
              **result}
    record["completed_nonempty"] = (result["http_status"] == 200 and
                                       data.get("status") == "completed" and bool(answer.strip()))
    record = sanitize(record, credential)
    atomic_json(artifacts / f"{tid}.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 0 < args.timeout <= 120 or not 1 <= args.concurrency <= 4:
        parser.error("Require timeout in (0,120] and concurrency in [1,4]")
    directory = args.experiment_dir
    rows, manifest_hash = ([], None) if args.catalog_only else load_manifest(directory)
    if args.dry_run:
        print(json.dumps({"dry_run": True, "requests": len(rows),
                          "maximum_generated_tokens": sum(r["request_payload"]["max_output_tokens"] for r in rows),
                          "manifest_sha256": manifest_hash, "catalog_only": args.catalog_only}))
        return
    # Fail before prompting for a secret or making a call if output exists.
    if args.catalog_only:
        directory.mkdir(parents=True, exist_ok=True)
        if (directory / "catalog.json").exists():
            raise FileExistsError("catalog.json already exists; refusing to overwrite")
    else:
        if (directory / "responses.jsonl").exists():
            raise FileExistsError("responses.jsonl already exists; refusing to overwrite")
        artifacts = directory / "api_artifacts"
        artifacts.mkdir(exist_ok=False)
    credential = os.environ.get("ADAPTION_API_KEY") or getpass.getpass("Adaption key (hidden): ")
    if not credential or "\n" in credential or "\r" in credential:
        raise ValueError("Missing/invalid Adaption credential")
    if args.catalog_only:
        record = {"retrieved_utc": now(), "endpoint": BASE + "/api/v1/models?type=hosted",
                  **request_once(BASE + "/api/v1/models?type=hosted", credential, args.timeout)}
        atomic_json(directory / "catalog.json", record)
        print(json.dumps({"catalog_path": str(directory / "catalog.json"),
                          "http_status": record["http_status"]}))
        return
    records = {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(run_trial, row, credential, args.timeout, artifacts): row["trial_id"] for row in rows}
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
        "exact_provider_snapshot": "Not established merely by returned model alias",
        "completed_nonempty": sum(bool(r.get("completed_nonempty")) for r in records.values())})
    print(json.dumps({"responses_path": str(directory / "responses.jsonl"),
                      "requested": len(rows), "recorded": len(records),
                      "completed_nonempty": sum(bool(r.get("completed_nonempty")) for r in records.values())}))


if __name__ == "__main__":
    main()
