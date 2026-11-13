#!/usr/bin/env python3
"""One-shot format-only gate; arithmetic correctness is deliberately not evaluated."""
import argparse
import datetime as dt
import importlib.util
import json
from pathlib import Path

from capture_math import RUNNER_SHA, load, sha, verify_one
from scoring import numeric, parse_answers


def run(args):
    root = args.directory.resolve()
    protocol = load(root / "protocol.json")
    if sha(root / "protocol.json") != args.freeze_protocol_sha256 or sha(args.runner) != RUNNER_SHA:
        raise ValueError("Frozen protocol or runner changed")
    for path, expected in protocol["source_sha256"].items():
        if sha(root / path) != expected:
            raise ValueError("Frozen source changed: " + path)
    for path, expected in protocol.get("implementation_sha256", {}).items():
        if sha(root / path) != expected:
            raise ValueError("Frozen implementation changed: " + path)
    if len(args.freeze_commit) != 40 or any(c not in "0123456789abcdef" for c in args.freeze_commit):
        raise ValueError("Real externally published execution commit required")
    instant = dt.datetime.fromisoformat(args.freeze_time.replace("Z", "+00:00"))
    if instant.tzinfo is None or instant > dt.datetime.now(dt.timezone.utc):
        raise ValueError("Freeze timestamp must precede requests")
    path = root / "admission"
    gate = path / "GATE.json"
    if gate.exists():
        raise FileExistsError("Admission gate already exists; no replacement")
    spec = importlib.util.spec_from_file_location("frozen_admission_runner", args.runner)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    manifest, manifest_sha = runner.load_manifest(path)
    if len(manifest) != 2 or {r["requested_model"] for r in manifest} != set(protocol["models"]):
        raise ValueError("Exactly one format control per fixed candidate required")
    reports = []
    for row in manifest:
        _, text, report = verify_one(row, path, runner, instant)
        valid = False
        error = None
        if report["capture_complete"]:
            try:
                answers = parse_answers(text, row["item_ids"])
                for answer in answers.values():
                    if not (isinstance(answer, str) and answer.strip().upper() == "ABSTAIN"):
                        numeric(answer)
                valid = True
            except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
                error = type(exc).__name__ + ": " + str(exc)
        reports.append({**report, "format_valid": valid, "format_error": error,
                        "arithmetic_correctness_checked": False})
    passed = all(r["capture_complete"] and r["format_valid"] for r in reports)
    result = {"status": "pass" if passed else "fail", "gate_passed": passed,
              "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "freeze_commit": args.freeze_commit, "freeze_time": args.freeze_time,
              "protocol_sha256": sha(root / "protocol.json"), "manifest_sha256": manifest_sha,
              "planned_requests": 2, "arithmetic_correctness_checked": False,
              "scope": "Fixed format-only admission; no candidate or prompt replacement and no study-performance scoring",
              "rows": reports}
    with gate.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"admission_gate": result["status"], "model_calls_here": 0,
                      "arithmetic_correctness_checked": False}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--freeze-time", required=True)
    parser.add_argument("--freeze-protocol-sha256", required=True)
    run(parser.parse_args())
