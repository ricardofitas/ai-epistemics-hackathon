"""Audit retained installed-native artifacts without importing the probe.

The verifier validates capture association and reports the original native scores.
Incomplete provider results retain an unknown interpreted score. The fixture ID
type erratum is evaluated on preserved rows with an exact string roundtrip.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


MODEL = "qwen3.8-27b"
CONDITIONS = ("native_gallery", "source_typed")
SOURCE_HASHES = {
    40: "0636d90afc424880c765e9732fba7405f91edcf667bb17d2b22c6134dbeff5c7",
    200: "05ffdf0514950787a180a2568505a9b4867b87c392a9fc0da1a1ea8e4e6d304b",
}
ORIGIN_HASHES = {
    "one_eval.toolkits.dataflow_eval_tool": "640884f634a3009784a8698d4f4fd05a0485f991dad395b3c31fd630c6cf427b",
    "one_eval.metrics.runner": "d599a3665c2594fc1bce9b9c3cf664d704fd0cfcff57146961abeb4ac359b706",
    "one_eval.metrics.common.general": "dd7104eee19c829f3ddb5dd1faec0b97a230b253ab41b615d20b6799699d06a7",
    "dataflow.operators.core_text.generate.bench_answer_generator": "9b3b29c44c60d71510f88b0f19e964339806fc29bd0fd91ff16c97072219e09a",
    "dataflow.operators.core_text.eval.unified_bench_dataset_evaluator": "a06f70fac52f9e5287b70aa908852468aa0b945be79f4445cf91566a04878c7f",
    "dataflow.serving.api_llm_serving_request": "92e0188aaef8d622435e09c9b0ce5946c50cb5c5b311ab24bbb5bb43e400653f",
    "dataflow.utils.storage": "9497e91a1b9b63f354ecfc36adf5b600e0ac5b173eb9ca1bd3da52368bc3b58d",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def normalize(value):
    """Pinned native exact_match normalization, One-Eval 8aba20ad utils/extractor.py."""
    if value is None:
        return ""
    text = str(value)
    if "####" in text:
        text = text.split("####")[-1]
    elif "\\boxed{" in text:
        boxed = re.findall(r"\\boxed\{([^}]+)\}", text)
        if boxed:
            text = boxed[-1]
    elif len(text) > 50:
        answer = re.search(r"(?:answer|result)\s+is\s+:?\s*([^!.?\n]+)",
                           text, re.IGNORECASE)
        if answer:
            text = answer.group(1).strip()
    punctuation = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
    text = "".join(char for char in text.lower() if char not in punctuation)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def native_client_text(message):
    content = message.get("content", "")
    if re.search(r"<think>.*?</think>.*?<answer>.*?</answer>", content, re.DOTALL):
        return content
    reasoning = message.get("reasoning_content")
    if reasoning:
        return f"<think>{reasoning}</think>\n<answer>{content}</answer>"
    return content


def verify(root, mode, archive=None, expected_archive_sha=None,
           expected_protocol_sha=None, expected_protocol_commit=None):
    root = Path(root).resolve()
    errors = []
    warnings = []

    def check(condition, label):
        if not condition:
            errors.append(label)

    protocol_path = root / "PROTOCOL.json"
    protocol = read(protocol_path)
    launch = read(root / "LAUNCH.json")
    check(launch.get("protocol_sha256") == digest(protocol_path.read_bytes()),
          "launch_protocol_hash")
    if expected_protocol_sha:
        check(digest(protocol_path.read_bytes()) == expected_protocol_sha,
              "expected_protocol_hash")
    if expected_protocol_commit:
        check(launch.get("protocol_commit") == expected_protocol_commit,
              "expected_protocol_commit")
    check(launch.get("mode") == mode, "launch_mode")
    check(protocol.get("one_eval_revision") == "8aba20ad17ee2c7d2391162ac03ffaebcbb17506",
          "native_source_revision")
    check(protocol.get("dataflow_wheel_sha256") == "75dd8e03fd96875472c11bd9fdf8af30e66d76a6b2d59b6b426d998db25e8790",
          "native_distribution_pin")
    for name, expected in protocol.get("frozen_files", {}).items():
        path = root / name
        if path.is_file():
            check(digest(path.read_bytes()) == expected, "frozen_file:" + name)
        else:
            warnings.append("frozen_file_not_retained:" + name)

    archive_report = None
    if archive:
        archive = Path(archive)
        actual_hash = digest(archive.read_bytes())
        if expected_archive_sha:
            check(actual_hash == expected_archive_sha, "archive_hash")
        count = 0
        with zipfile.ZipFile(archive) as zipped:
            for name in zipped.namelist():
                if name.endswith("/"):
                    continue
                target = (root / name).resolve()
                check(target.is_relative_to(root), "archive_path_escape:" + name)
                check(target.is_file() and target.read_bytes() == zipped.read(name),
                      "retained_archive_member:" + name)
                count += 1
        archive_report = {"sha256": actual_hash, "retained_members": count}

    sources = read(root / "selected2.json")
    check(len(sources) == 2, "source_count")
    by_source = {item["source_index"]: item for item in sources}
    check(set(by_source) == set(SOURCE_HASHES), "source_ids")
    for index, item in by_source.items():
        check(digest(canonical(item["record"])) == item["source_sha256"] == SOURCE_HASHES[index],
              "source_hash:" + str(index))
    summary = read(root / (mode.upper() + "_SUMMARY.json"))
    expected_cells = [(index, condition) for index in sorted(SOURCE_HASHES)
                      for condition in CONDITIONS]
    entries = summary.get("results", [])
    check([(row.get("source_index"), row.get("condition")) for row in entries] == expected_cells,
          "fixed_four_slot_order")
    attempts = []
    response_ids = []
    slots = []
    output_tokens = 0
    for index, condition in expected_cells:
        slot_name = f"{index}_{condition}"
        directory = root / "results" / mode / slot_name
        record = by_source[index]["record"]
        result_path = directory / "RESULT.json"
        result = read(result_path) if result_path.exists() else {}
        trace_path = directory / "HTTP_TRACE.json"
        traces = read(trace_path) if trace_path.exists() else []
        check(len(traces) <= 1, "one_attempt:" + slot_name)
        slot = {"source_index": index, "condition": condition,
                "original_probe_status": result.get("status", "UNATTEMPTED"),
                "capture_eligible": False, "eligible_native_score": None}
        if not traces:
            slot["outcome"] = "UNKNOWN_CAPTURE"
            slots.append(slot)
            continue
        trace = traces[0]
        attempts.append({"source_index": index, "condition": condition, **trace})
        payload = trace["request_payload"]
        check(digest(json.dumps(payload).encode()) == trace["request_sha256"],
              "request_hash:" + slot_name)
        check(payload.get("model") == MODEL and payload.get("max_tokens") == 4096
              and payload.get("temperature") == 0 and not payload.get("stream", False),
              "request_caps:" + slot_name)
        user_messages = [message.get("content") for message in payload.get("messages", [])
                         if message.get("role") == "user"]
        check(len(user_messages) == 1 and isinstance(user_messages[0], str),
              "user_message_count:" + slot_name)
        if condition == "source_typed" and len(user_messages) == 1:
            user = user_messages[0]
            check(record["prompt"] in user and str(record["context"]) in user
                  and "A. None" not in user and "{question}" not in user,
                  "typed_source_request_binding:" + slot_name)
        raw = {}
        body = trace.get("response_body")
        if isinstance(body, str):
            if not trace.get("credential_redacted"):
                check(digest(body.encode()) == trace.get("body_sha256"),
                      "response_body_hash:" + slot_name)
            else:
                warnings.append("response_redacted_before_upload:" + slot_name)
            try:
                parsed = json.loads(body)
                raw = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                pass
        choices = raw.get("choices") or []
        first = choices[0] if choices and isinstance(choices[0], dict) else {}
        message = first.get("message") or {}
        content = message.get("content") if isinstance(message, dict) else None
        eligible = (trace.get("http_status") == 200
                    and isinstance(raw.get("id"), str) and bool(raw["id"].strip())
                    and not raw.get("error") and raw.get("model") == MODEL
                    and first.get("finish_reason") == "stop"
                    and isinstance(content, str) and bool(content.strip()))
        usage = raw.get("usage")
        valid_usage = (isinstance(usage, dict)
                       and type(usage.get("completion_tokens")) is int
                       and 0 <= usage["completion_tokens"] <= 4096
                       and type(usage.get("prompt_tokens")) is int
                       and usage["prompt_tokens"] >= 0)
        if mode == "real":
            eligible = eligible and valid_usage
            if isinstance(raw.get("id"), str):
                response_ids.append(raw["id"])
            if valid_usage:
                output_tokens += usage["completion_tokens"]
        slot["capture_eligible"] = bool(eligible)
        slot["finish_reason"] = first.get("finish_reason")
        slot["usage"] = usage
        origins_path = directory / "IMPORT_ORIGINS.json"
        if origins_path.exists():
            origins = read(origins_path)
            check(set(origins) == set(ORIGIN_HASHES), "native_origin_set:" + slot_name)
            for name, expected in ORIGIN_HASHES.items():
                origin = origins.get(name, {})
                check(origin.get("sha256") == expected and "/site-packages/" in origin.get("path", ""),
                      "native_origin:" + slot_name + ":" + name)
        else:
            check(False, "missing_native_origins:" + slot_name)
        row = result.get("delivered_row")
        metric = result.get("native_metric_runner", {})
        if isinstance(row, dict):
            for key, value in record.items():
                same = str(row.get(key)) == str(value) if key == "id" else row.get(key) == value
                check(same, "source_column:" + slot_name + ":" + key)
            slot["source_id_annotation"] = {
                "source": record["id"], "source_type": type(record["id"]).__name__,
                "delivered": row.get("id"), "delivered_type": type(row.get("id")).__name__,
            }
            if isinstance(content, str):
                check(row.get("generated_ans") == native_client_text(message),
                      "response_to_delivered_text:" + slot_name)
            primary = metric.get("primary_metric_result", {})
            details = metric.get("primary_metric_details")
            check(metric.get("num_samples") == 1 and primary.get("total_samples") == 1,
                  "native_metric_one_source:" + slot_name)
            slot["native_primary"] = primary
            slot["native_details"] = details
            if condition == "native_gallery":
                check(primary.get("metric") == "choice_accuracy"
                      and primary.get("scored_samples") == 0
                      and primary.get("invalid_references") == 1
                      and details == [None], "native_unscorable_reference:" + slot_name)
                slot["outcome"] = "UNSCORABLE_REFERENCE" if eligible else "UNKNOWN_CAPTURE"
            else:
                expected_score = float(any(normalize(row.get("generated_ans")) == normalize(alias)
                                           for alias in record["target"]))
                check(primary.get("metric") == "exact_match" and details == [expected_score]
                      and primary.get("score") == expected_score,
                      "native_exact_match_recalculation:" + slot_name)
                slot["outcome"] = "KNOWN" if eligible else "UNKNOWN_CAPTURE"
                slot["eligible_native_score"] = expected_score if eligible else None
                if mode == "fixture":
                    check(expected_score == 1, "known_fixture_exact_match:" + slot_name)
        else:
            slot["outcome"] = "UNKNOWN_CAPTURE"
        if "outcome_status" in result:
            check(result["outcome_status"] == slot["outcome"], "reported_outcome_status:" + slot_name)
            check(result.get("eligible_native_score") == slot["eligible_native_score"],
                  "reported_eligible_score:" + slot_name)
        if result.get("error") == "source_column_changed:id":
            slot["derived_erratum"] = "Original audit rejected an ID representation change. Source/delivered values remain preserved and exact string-roundtrip matched."
        slots.append(slot)
    check(len(attempts) <= 4, "maximum_four_http_attempts")
    check(len(response_ids) == len(set(response_ids)), "unique_real_response_ids")
    starts = [event["started_utc_epoch"] for event in attempts]
    intervals = [later - earlier for earlier, later in zip(starts, starts[1:])]
    check(not intervals or min(intervals) >= 4.99, "actual_http_cadence")
    check(output_tokens <= 16384, "total_output_tokens")
    ledger_path = root / ("REAL_CALL_LEDGER.jsonl" if mode == "real" else "FIXTURE_CALL_LEDGER.jsonl")
    if ledger_path.exists():
        ledger = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()]
        check(len(ledger) == len(attempts), "ledger_attempt_count")
        for ledger_event, event in zip(ledger, attempts):
            check(all(ledger_event.get(key) == event.get(key)
                      for key in ("source_index", "condition", "request_sha256", "started_utc_epoch")),
                  "ledger_event_binding")
    else:
        warnings.append("initial_fixture_has_no_separate_global_ledger")
        check(mode == "fixture", "real_attempt_ledger_missing")
    check(summary.get("new_provider_calls") == (len(attempts) if mode == "real" else 0),
          "reported_provider_call_count")
    return {
        "status": "PASS" if not errors else "FAIL", "mode": mode,
        "archive": archive_report, "protocol_sha256": digest(protocol_path.read_bytes()),
        "protocol_commit": launch.get("protocol_commit"),
        "executable_sha256": digest((root / "native_probe.py").read_bytes()),
        "planned_slots": 4, "observed_http_attempts": len(attempts),
        "new_provider_calls": len(attempts) if mode == "real" else 0,
        "known_interpreted_scores": sum(slot["eligible_native_score"] is not None for slot in slots),
        "minimum_actual_http_interval_seconds": min(intervals) if intervals else None,
        "verified_output_tokens": output_tokens, "slots": slots,
        "errors": errors, "warnings": warnings,
        "scope": "Independent retained-artifact audit, with pinned source normalization copied for native EM reproduction. No probe imports, provider calls, semantic judging, or independent provider attestation. Original native raw scores and original audit failures remain preserved.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--mode", choices=("fixture", "real"), required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--expected-archive-sha")
    parser.add_argument("--expected-protocol-sha")
    parser.add_argument("--expected-protocol-commit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.root, args.mode, args.archive, args.expected_archive_sha,
                    args.expected_protocol_sha, args.expected_protocol_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("status", "mode", "observed_http_attempts", "new_provider_calls", "errors")}))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
