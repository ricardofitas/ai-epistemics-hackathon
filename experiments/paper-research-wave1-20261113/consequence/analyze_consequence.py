#!/usr/bin/env python3
"""Offline, frozen-input PAWS-to-NLI consequence analysis. No network or API calls.

Run --self-test for synthetic fixtures only. Actual analysis requires externally
supplied gate evidence and separate frozen commit/time/hash arguments. Outputs
are exclusively created in a new analysis directory; captures are never edited.
The Git commit argument is an external provenance assertion, not a remote Git
verification. Frozen local bytes and capture ordering are checked independently.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import random
import re
import tempfile
from collections import Counter, defaultdict


LABELS = {"entailment", "contradiction", "neutral"}
TERMINALS = {"response.completed", "response.incomplete", "response.failed", "response.cancelled"}
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 2026111313


class IntegrityError(ValueError):
    """Evidence contradicts a frozen input or an independently retained capture."""


class PredictionError(ValueError):
    """Completed assistant text does not satisfy the registered answer format."""


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def strict_json(text):
    def pairs(values):
        answer = {}
        for key, value in values:
            if key in answer:
                raise ValueError("Duplicate JSON object key: " + key)
            answer[key] = value
        return answer

    def constant(value):
        raise ValueError("Non-finite JSON constant: " + value)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def read_json(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    return [strict_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def timestamp(value):
    require(isinstance(value, str), "Missing timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IntegrityError("Invalid ISO timestamp") from exc
    require(parsed.tzinfo is not None, "Timestamps must contain a UTC offset")
    return parsed.astimezone(dt.timezone.utc)


def valid_sha(value, length=64):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def unfence(text):
    stripped = text.strip()
    fence = re.fullmatch(r"```(?:json)?[ \t]*\r?\n(.*)\r?\n```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        stripped = fence.group(1).strip()
    return stripped


def parse_predictions(text, expected_ids):
    """Whole-object parse only; never infer a missing answer from prose/deltas."""
    if not isinstance(text, str):
        raise PredictionError("Final text is not a string")
    try:
        parsed = strict_json(unfence(text))
    except (ValueError, TypeError) as exc:
        raise PredictionError("Not one valid JSON object: " + str(exc)) from exc
    if not isinstance(parsed, dict) or set(parsed) != {"predictions"}:
        raise PredictionError("Root must contain only predictions")
    values = parsed["predictions"]
    if not isinstance(values, list) or len(values) != len(expected_ids):
        raise PredictionError("Prediction count differs from the supplied batch")
    result = {}
    for value in values:
        if not isinstance(value, dict) or set(value) != {"id", "label"}:
            raise PredictionError("Each prediction must contain only id and label")
        qid, raw_label = value["id"], value["label"]
        if not isinstance(qid, str) or qid not in expected_ids or qid in result:
            raise PredictionError("Unknown or duplicate task id")
        if not isinstance(raw_label, str) or raw_label.casefold() not in LABELS:
            raise PredictionError("Label is not an allowed three-way NLI label")
        result[qid] = {"raw_label": raw_label, "label": raw_label.casefold()}
    if set(result) != set(expected_ids):
        raise PredictionError("Missing task ids")
    return result


def final_text(raw):
    parts = []
    for item in raw.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message" or item.get("role", "assistant") != "assistant":
            continue
        for part in item.get("content", []) or []:
            if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                parts.append(part["text"])
    answer = "\n".join(parts)
    if answer:
        return answer, "terminal_message_output_text"
    if isinstance(raw.get("output_text"), str):
        return raw["output_text"], "terminal_top_level_output_text"
    return "", "terminal_message_output_text"


def validate_gate(gate, frozen_time):
    """Validate an externally adjudicated recurrence receipt, not its judgment."""
    require(gate.get("activated") is True, "Consequence gate is not activated")
    require(gate.get("mechanism") == "PAWS_TO_DIRECTIONAL_NLI", "Wrong gate mechanism")
    config = gate.get("qualifying_configuration")
    require(isinstance(config, (str, dict)) and bool(config), "Missing qualifying configuration")
    require(type(gate.get("completed_replicates")) is int and gate["completed_replicates"] == 3,
            "Gate requires exactly three completed replicates of one configuration")
    require(type(gate.get("same_mechanism_count")) is int and gate["same_mechanism_count"] in (2, 3),
            "Gate requires same-mechanism recurrence in two or three replicates")
    ids = gate.get("source_trial_ids")
    require(isinstance(ids, list) and len(ids) == 3 and all(isinstance(x, str) and x for x in ids) and len(set(ids)) == 3,
            "Gate must identify exactly three distinct source trials")
    replicates = gate.get("replicates")
    require(isinstance(replicates, list) and len(replicates) == 3, "Gate needs three per-replicate attestations")
    require(all(isinstance(r, dict) for r in replicates), "Invalid gate replicate entry")
    require({r.get("trial_id") for r in replicates} == set(ids), "Gate source ids disagree with replicate attestations")
    for row in replicates:
        require(row.get("configuration") == config, "Gate pools different configurations")
        require(all(row.get(k) is True for k in ("completed", "fresh", "original_question")),
                "Each qualifying replicate must be completed, fresh and original-question")
        require(type(row.get("same_mechanism")) is bool, "Missing per-replicate mechanism adjudication")
    require(sum(r["same_mechanism"] for r in replicates) == gate["same_mechanism_count"], "Gate recurrence count mismatch")
    require(valid_sha(gate.get("source_freeze_commit"), 40), "Missing source-study freeze commit")
    require(valid_sha(gate.get("source_summary_sha256")), "Missing source-summary SHA256")
    require(timestamp(gate.get("generated_utc")) <= frozen_time, "Gate evidence was created after consequence freeze")
    return {"status": "external_receipt_validated", "qualifying_configuration": config,
            "source_trial_ids": ids, "same_mechanism_count": gate["same_mechanism_count"],
            "source_summary_sha256": gate["source_summary_sha256"],
            "limitation": "Recurrence labels and completion/freshness are externally adjudicated assertions. This analyzer does not reread recommendation answers or independently relabel them."}


def frozen_inputs(directory, protocol_sha, gate_sha, frozen_time):
    require(valid_sha(protocol_sha) and valid_sha(gate_sha), "Frozen protocol and gate SHA256 are required")
    require(sha_file(directory / "protocol.json") == protocol_sha, "Protocol differs from frozen protocol hash")
    protocol = read_json(directory / "protocol.json")
    hashes = protocol.get("artifacts_sha256", {})
    for required in ("selected_data.json", "selection_manifest.json", "task_key.json", "manifest.jsonl", "analyze_consequence.py"):
        require(required in hashes, "Protocol must freeze " + required)
    require(sha_file(Path(__file__)) == hashes["analyze_consequence.py"], "Executing analyzer differs from frozen analyzer hash")
    for relative, digest in hashes.items():
        path = (directory / relative).resolve()
        require(path.is_relative_to(directory.resolve()), "Frozen artifact path escapes experiment directory")
        require(valid_sha(digest) and path.is_file() and sha_file(path) == digest, "Frozen artifact hash mismatch: " + relative)
    runner = protocol.get("native_sse_runner", {})
    require(runner.get("stream_true_required") is True and valid_sha(runner.get("sha256")), "Missing frozen native SSE runner")
    runner_path = (directory / runner["path"]).resolve()
    require(runner_path.is_file() and sha_file(runner_path) == runner["sha256"], "Native SSE runner hash mismatch")
    gate_path = directory / "gate_activation.json"
    require(gate_path.is_file() and sha_file(gate_path) == gate_sha, "Gate receipt differs from frozen hash")
    gate = validate_gate(read_json(gate_path), frozen_time)
    require(protocol.get("uncertainty", {}).get("bootstrap_repeats") == BOOTSTRAP_DRAWS and
            protocol["uncertainty"].get("bootstrap_seed") == BOOTSTRAP_SEED and
            protocol["uncertainty"].get("confidence_level") == 0.95, "Bootstrap constants differ from protocol")
    data = read_json(directory / "selected_data.json")
    selection = read_json(directory / "selection_manifest.json")
    require(selection.get("selected_data_sha256") == sha_file(directory / "selected_data.json"), "Selection receipt hash mismatch")
    items = data["items"]
    require(len(items) == 40 and len({i["item_id"] for i in items}) == 40, "Expected forty unique source items")
    item_map = {i["item_id"]: i for i in items}
    strata = Counter((i["suite"], i["analysis_role"], str(i["gold_label"])) for i in items)
    require(strata == Counter({("paws", "proxy_selection", "0"): 10, ("paws", "proxy_selection", "1"): 10,
                              ("hans", "target_selection", "non-entailment"): 5, ("hans", "target_selection", "entailment"): 5,
                              ("hans", "target_confirmation", "non-entailment"): 5, ("hans", "target_confirmation", "entailment"): 5}),
            "Frozen sample strata differ from registered counts")
    selection_rows = selection["item_selection"]
    require(len(selection_rows) == 40, "Selection receipt item count mismatch")
    for row in selection_rows:
        require(row.get("item_id") in item_map, "Selection receipt contains an unknown item")
        require(all(item_map[row["item_id"]].get(k) == v for k, v in row.items()), "Selection receipt item metadata mismatch")
    keys = read_json(directory / "task_key.json")
    require(len(keys) == 60 and len({k["id"] for k in keys}) == 60, "Expected sixty unique ordered questions")
    key_map = {k["id"]: k for k in keys}
    by_item = defaultdict(list)
    expected_questions = {}
    for key in keys:
        require(set(key) == {"id", "item_id", "direction"} and key["item_id"] in item_map, "Invalid ordered task key")
        item = item_map[key["item_id"]]
        direction = key["direction"]
        require(direction in ("forward", "reverse"), "Invalid pair direction")
        by_item[item["item_id"]].append(direction)
        first, second = ("sentence1", "sentence2") if direction == "forward" else ("sentence2", "sentence1")
        expected_questions[key["id"]] = {"id": key["id"], "premise": item[first], "hypothesis": item[second]}
    for item in items:
        require(sorted(by_item[item["item_id"]]) == (["forward", "reverse"] if item["suite"] == "paws" else ["forward"]),
                "Missing, duplicate or unintended direction")
    manifest = read_jsonl(directory / "manifest.jsonl")
    require(len(manifest) == 24 and len({r["trial_id"] for r in manifest}) == 24, "Expected twenty-four unique client calls")
    models = protocol["models"]
    require(len(models) == 2 and len(set(models)) == 2, "Expected two fixed classifier configurations")
    model_rows = defaultdict(list)
    for row in manifest:
        model, payload, qids = row["requested_model"], row["request_payload"], row["task_ids"]
        require(model in models and payload.get("model") == model, "Unregistered classifier configuration")
        require(len(qids) == 5 and len(set(qids)) == 5 and set(qids) <= set(key_map), "Invalid batch ids")
        questions = strict_json(payload["input"])
        require(questions == [expected_questions[q] for q in qids], "Model input differs from ordered task key or leaks metadata")
        roles = {item_map[key_map[q]["item_id"]]["analysis_role"] for q in qids}
        require(roles == {row["batch_role"]}, "Batch mixes selection and confirmation roles")
        require(payload.get("stream") is True and payload.get("temperature") == 0.0 and payload.get("max_output_tokens") == 8192,
                "Request capture settings differ from frozen protocol")
        require(payload.get("tools") == [] and payload.get("tool_choice") == "none" and
                payload.get("agentic_memory") is False and payload.get("store") is False, "Unexpected tools, memory or storage")
        model_rows[model].append(row)
    normalized_batches = []
    for model in models:
        rows = model_rows[model]
        require(len(rows) == 12 and Counter(r["batch_role"] for r in rows) ==
                Counter({"proxy_selection": 8, "target_selection": 2, "target_confirmation": 2}), "Batch role counts differ")
        require(Counter(q for r in rows for q in r["task_ids"]) == Counter(key_map.keys()), "Missing or repeated ordered question")
        normalized_batches.append(sorted((r["batch_index"], r["batch_role"], tuple(r["task_ids"])) for r in rows))
    require(normalized_batches[0] == normalized_batches[1], "Models receive different batch membership/order")
    return protocol, gate, items, keys, manifest


def audit_trial(row, record, artifact, journal, frozen_time):
    """Audit one native-SSE trial. Return scorable predictions or explicit failure."""
    tid = row["trial_id"]
    result = {"trial_id": tid, "requested_model": row["requested_model"], "task_ids": row["task_ids"],
              "batch_role": row["batch_role"], "status": "unscorable", "reasons": []}
    if record is None:
        result["reasons"].append("missing_aggregate_record")
        return result, {}
    require(record.get("trial_id") == tid, "Trial id differs from manifest: " + tid)
    require(record.get("attempt_count") == 1, "Attempt count differs from one: " + tid)
    for field in ("http_status", "response_status", "api_error", "transport_error", "usage", "incomplete_details",
                  "parse_mode", "response_content_type", "stream_format_deviation", "terminal_event", "terminal_event_seen",
                  "stream_incomplete", "used_delta_fallback", "completed_nonempty", "local_capture_error"):
        result[field] = record.get(field)
    result["returned_model"] = record.get("returned_model")
    result["provider_alias_matches_requested"] = record.get("returned_model") == row["requested_model"]
    result["model_identity_limit"] = "Requested/returned aliases are retained; immutable weights are not established. Alias equality is descriptive, not an added completeness exclusion."
    if artifact is None or not artifact.is_file():
        result["reasons"].append("missing_individual_artifact")
        return result, {}
    require(read_json(artifact) == record, "Aggregate differs from individual artifact: " + tid)
    result["artifact_sha256"] = sha_file(artifact)
    if record.get("local_capture_error"):
        result["reasons"].append("local_capture_error:" + str(record["local_capture_error"]))
        return result, {}
    require(record.get("request_payload") == row["request_payload"], "Request payload differs from frozen manifest: " + tid)
    require(record.get("requested_model") == row["requested_model"], "Requested model differs from manifest: " + tid)
    require(record.get("request_sha256") == sha_bytes(canonical(row["request_payload"])), "Wire request hash mismatch: " + tid)
    start, end = timestamp(record.get("started_utc")), timestamp(record.get("ended_utc"))
    require(frozen_time < start <= end, "Trial began before freeze or has invalid time ordering: " + tid)
    text = record.get("output_text")
    require(isinstance(text, str) and record.get("output_text_sha256") == sha_bytes(text.encode()), "Final text hash mismatch: " + tid)
    result.update({"response_id": record.get("response_id"), "returned_model": record.get("returned_model"),
                   "started_utc": record["started_utc"], "ended_utc": record["ended_utc"],
                   "output_text_sha256": record["output_text_sha256"]})
    if journal is None or not journal.is_file():
        result["reasons"].append("missing_stream_journal")
        return result, {}
    journal_sha = sha_file(journal)
    require(record.get("stream_journal_sha256") == journal_sha, "Journal hash mismatch: " + tid)
    result["stream_journal_sha256"] = journal_sha
    frames = read_jsonl(journal)
    captures = [f for f in frames if f.get("event") == "capture_end"]
    require(len(captures) == 1 and frames[-1] == captures[0], "Journal lacks a unique final capture_end: " + tid)
    events = frames[:-1]
    require(len(events) == record.get("stream_frame_count"), "Journal frame count mismatch: " + tid)
    require(sum(bool(f.get("json_error")) for f in events) == record.get("stream_json_error_count"), "Journal JSON-error count mismatch: " + tid)
    times = [timestamp(f.get("captured_utc")) for f in frames]
    require(all(start <= t <= end for t in times) and times == sorted(times), "Journal timestamps outside capture or out of order: " + tid)
    cap = captures[0]
    for field in ("http_status", "terminal_event", "transport_error"):
        require(cap.get(field) == record.get(field), "Capture-end metadata mismatch: " + tid + ":" + field)
    terminals = []
    for frame in events:
        data = frame.get("data")
        if isinstance(data, dict):
            # Sanitized decoded data must agree with its retained wire data text.
            if isinstance(frame.get("data_text"), str) and not frame.get("json_error"):
                try:
                    decoded = strict_json(frame["data_text"])
                except ValueError:
                    decoded = None
                require(decoded == data, "Decoded event differs from retained data_text: " + tid)
            kind = data.get("type") or frame.get("event")
            if kind in TERMINALS and isinstance(data.get("response"), dict) and not frame.get("partial_frame"):
                terminals.append((kind, data["response"]))
    if not terminals:
        result["reasons"].append("missing_nonpartial_terminal_event")
        return result, {}
    require(len(terminals) == 1, "More than one terminal event in capture: " + tid)
    event, raw = terminals[0]
    require(record.get("raw_response") == raw, "Terminal journal object differs from artifact: " + tid)
    require(record.get("terminal_event") == event and record.get("terminal_event_seen") is True, "Terminal metadata mismatch: " + tid)
    require(record.get("response_id") == raw.get("id") and record.get("returned_model") == raw.get("model") and
            record.get("response_status") == raw.get("status"), "Provider response metadata mismatch: " + tid)
    require(record.get("usage") == raw.get("usage") and record.get("api_error") == raw.get("error") and
            record.get("incomplete_details") == raw.get("incomplete_details"), "Provider completion metadata mismatch: " + tid)
    extracted, source = final_text(raw)
    if record.get("used_delta_fallback"):
        result["reasons"].append("delta_fallback")
    else:
        require(extracted == text and source == record.get("text_source"), "Final assistant text differs from terminal object: " + tid)
    checks = {"non_200_http": record.get("http_status") == 200,
              "not_completed_terminal": event == "response.completed" and raw.get("status") == "completed",
              "non_sse_capture": record.get("parse_mode") == "sse" and record.get("response_content_type") == "text/event-stream" and record.get("stream_format_deviation") is False,
              "incomplete_stream": record.get("stream_incomplete") is False,
              "transport_error": record.get("transport_error") is None,
              "provider_error": raw.get("error") is None and raw.get("incomplete_details") is None,
              "empty_final_text": bool(text.strip()),
              "runner_not_completed_nonempty": record.get("completed_nonempty") is True,
              "malformed_stream_json": record.get("stream_json_error_count") == 0}
    result["reasons"].extend(name for name, ok in checks.items() if not ok)
    if result["reasons"]:
        return result, {}
    try:
        candidate = strict_json(unfence(text))
        if isinstance(candidate, dict) and isinstance(candidate.get("predictions"), list):
            # Preserve exact entries, including duplicates/invalid labels, as
            # unscored evidence. Only parse_predictions can promote a batch.
            result["raw_prediction_entries"] = candidate["predictions"]
    except ValueError:
        pass
    try:
        predictions = parse_predictions(text, row["task_ids"])
    except PredictionError as exc:
        result["reasons"].append("invalid_prediction_format:" + str(exc))
        return result, {}
    result["status"] = "valid_completed_batch"
    return result, predictions


def item_scores(items, keys, models, predictions):
    lookup = {(k["item_id"], k["direction"]): k["id"] for k in keys}
    scored = {}
    for model in models:
        rows = []
        for item in items:
            directions = ["forward", "reverse"] if item["suite"] == "paws" else ["forward"]
            qids = [lookup[(item["item_id"], d)] for d in directions]
            values = [predictions.get((model, q)) for q in qids]
            valid = all(v is not None for v in values)
            predicted = None
            if valid:
                labels = [v["label"] for v in values]
                predicted = int(all(x == "entailment" for x in labels)) if item["suite"] == "paws" else ("entailment" if labels[0] == "entailment" else "non-entailment")
            rows.append({"item_id": item["item_id"], "suite": item["suite"], "source_id": item["source_id"],
                         "analysis_role": item["analysis_role"], "gold_label": item["gold_label"],
                         "task_ids": qids, "valid": valid, "predicted_label": predicted,
                         "correct": predicted == item["gold_label"] if valid else None})
        scored[model] = rows
    return scored


def summarize_rows(rows):
    available = [r for r in rows if r["valid"]]
    correct = sum(r["correct"] for r in available)
    confusion = Counter((str(r["gold_label"]), str(r["predicted_label"])) for r in available)
    return {"planned_items": len(rows), "valid_items": len(available), "unscorable_items": len(rows) - len(available),
            "correct": correct, "incorrect": len(available) - correct,
            "accuracy_on_valid_items": correct / len(available) if available else None,
            "complete": len(available) == len(rows),
            "confusion_counts": [{"gold": g, "predicted": p, "count": n} for (g, p), n in sorted(confusion.items())]}


def summaries(scored):
    out = {}
    for model, rows in scored.items():
        roles = {role: summarize_rows([r for r in rows if r["analysis_role"] == role])
                 for role in ("proxy_selection", "target_selection", "target_confirmation")}
        roles["hans_all_secondary"] = summarize_rows([r for r in rows if r["suite"] == "hans"])
        strata = defaultdict(list)
        for row in rows:
            strata[(row["suite"], row["analysis_role"], str(row["gold_label"]))].append(row)
        out[model] = {"roles": roles, "strata": [{"suite": s, "analysis_role": r, "gold_label": g, **summarize_rows(v)}
                                                    for (s, r, g), v in sorted(strata.items())]}
    return out


def selection_outcome(scored, models):
    by_model = {m: {r["item_id"]: r for r in rows} for m, rows in scored.items()}
    require(all(r["valid"] for rows in scored.values() for r in rows), "Primary outcome requires every item for both models")
    roles = defaultdict(list)
    for row in scored[models[0]]:
        roles[row["analysis_role"]].append(row["item_id"])
    counts = {role: [sum(by_model[m][i]["correct"] for i in ids) for m in models] for role, ids in roles.items()}
    deltas = {role: (v[0] - v[1]) / len(roles[role]) for role, v in counts.items()}
    def winner(role):
        a, b = counts[role]
        return models[0] if a > b else models[1] if b > a else None
    proxy, target = winner("proxy_selection"), winner("target_selection")
    indeterminate = proxy is None or target is None
    confirm = roles["target_confirmation"]
    consequence = (sum(by_model[target][i]["correct"] for i in confirm) - sum(by_model[proxy][i]["correct"] for i in confirm)) / len(confirm) if not indeterminate else None
    return {"status": "indeterminate_tie" if indeterminate else "unique_selections",
            "difference_orientation": models[0] + " minus " + models[1], "paired_accuracy_differences": deltas,
            "proxy_selected_model": proxy, "target_selected_model": target,
            "strict_reversal": None if indeterminate else deltas["proxy_selection"] * deltas["target_selection"] < 0,
            "heldout_target_selected_minus_proxy_selected_accuracy": consequence,
            "holdout_status": "indeterminate_selection_tie" if indeterminate else "positive" if consequence > 0 else "negative" if consequence < 0 else "zero",
            "confirmation_items": len(confirm),
            "interpretation": "Signed realized accuracy difference on the separate ten-item confirmation set; all twenty HANS items are only a secondary aggregate."}


def linear_quantile(values, q):
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def paired_bootstrap(scored, models, outcome, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    """Resample original-label strata jointly across models; never reselect."""
    by_model = {m: {r["item_id"]: r for r in rows} for m, rows in scored.items()}
    strata = defaultdict(list)
    for row in scored[models[0]]:
        strata[(row["analysis_role"], str(row["gold_label"]))].append(row["item_id"])
    require(sorted(len(v) for v in strata.values()) == [5, 5, 5, 5, 10, 10], "Unexpected bootstrap strata")
    require(all(r["valid"] for rows in scored.values() for r in rows), "Cannot bootstrap incomplete paired scores")
    rng = random.Random(seed)
    values = defaultdict(list)
    proxy, target = outcome["proxy_selected_model"], outcome["target_selected_model"]
    for _ in range(draws):
        sampled = defaultdict(list)
        for (role, _gold), ids in sorted(strata.items()):
            sampled[role].extend(rng.choices(ids, k=len(ids)))
        for role, ids in sampled.items():
            values[role + "_model_difference"].append(sum(int(by_model[models[0]][i]["correct"]) - int(by_model[models[1]][i]["correct"]) for i in ids) / len(ids))
        if proxy is not None and target is not None:
            ids = sampled["target_confirmation"]
            values["heldout_target_selected_minus_proxy_selected"].append(sum(int(by_model[target][i]["correct"]) - int(by_model[proxy][i]["correct"]) for i in ids) / len(ids))
    return {"draws": draws, "seed": seed, "confidence_level": 0.95,
            "method": "Equal-tailed percentile at 0.025 and 0.975; linear interpolation, equivalent to NumPy quantile(method='linear').",
            "selection": "Observed winners fixed across every draw; no reselection. Selection ties leave consequence indeterminate.",
            "intervals": {k: {"lower": linear_quantile(v, .025), "upper": linear_quantile(v, .975)} for k, v in sorted(values.items())},
            "limits": "Conditional item-resampling uncertainty only; tiny sample and possible degenerate intervals. Omits model reruns, alternate contexts, article/topic clusters and selection uncertainty. No significance or equivalence claim."}


def analyze(directory, freeze_commit, freeze_time, protocol_sha, gate_sha):
    require(valid_sha(freeze_commit, 40), "A separate consequence freeze commit is required")
    frozen_time = timestamp(freeze_time)
    protocol, gate, items, keys, manifest = frozen_inputs(directory, protocol_sha, gate_sha, frozen_time)
    require(read_json(directory / "gate_activation.json")["source_freeze_commit"] != freeze_commit,
            "Consequence pilot requires a separate freeze commit from the source study")
    aggregate_path = directory / "responses.jsonl"
    records = read_jsonl(aggregate_path) if aggregate_path.is_file() else []
    require(all(isinstance(r, dict) and isinstance(r.get("trial_id"), str) for r in records), "Malformed aggregate record")
    require(len({r["trial_id"] for r in records}) == len(records), "Duplicate aggregate trial id")
    planned = {r["trial_id"] for r in manifest}
    require({r["trial_id"] for r in records} <= planned, "Unexpected aggregate trial id")
    record_map = {r["trial_id"]: r for r in records}
    artifact_dir, journal_dir = directory / "api_artifacts", directory / "stream_journals"
    require({p.stem for p in artifact_dir.glob("*.json")} <= planned, "Unexpected individual artifact")
    require({p.stem for p in journal_dir.glob("*.jsonl")} <= planned, "Unexpected journal")
    metadata_path = directory / "run_metadata.json"
    metadata = read_json(metadata_path) if metadata_path.is_file() else None
    if metadata is not None:
        require(metadata.get("manifest_sha256") == sha_file(directory / "manifest.jsonl"), "Run metadata manifest hash mismatch")
        require(metadata.get("requested") == 24 and metadata.get("recorded") == len(records), "Run metadata count mismatch")
        require(metadata.get("attempts_per_trial") == 1 and metadata.get("retries") == 0 and
                metadata.get("concurrency") == 2 and metadata.get("socket_timeout_seconds") == 120 and
                metadata.get("transport") == "native_sse", "Run metadata deviates from capture plan")
        require(timestamp(metadata.get("completed_capture_utc")) > frozen_time, "Run metadata predates freeze")
        ended = [timestamp(r["ended_utc"]) for r in records if r.get("ended_utc")]
        require(not ended or timestamp(metadata["completed_capture_utc"]) >= max(ended), "Run metadata predates a captured trial")
    audits, predictions = [], {}
    key_map, item_map = {k["id"]: k for k in keys}, {i["item_id"]: i for i in items}
    exported = []
    for row in manifest:
        tid = row["trial_id"]
        audit, parsed = audit_trial(row, record_map.get(tid), artifact_dir / (tid + ".json"), journal_dir / (tid + ".jsonl"), frozen_time)
        audits.append(audit)
        for qid in row["task_ids"]:
            key = key_map[qid]
            item = item_map[key["item_id"]]
            answer = parsed.get(qid)
            if answer is not None:
                predictions[(row["requested_model"], qid)] = answer
            exported.append({"requested_model": row["requested_model"], "returned_model": audit.get("returned_model"),
                             "trial_id": tid, "response_id": audit.get("response_id"), "id": qid, **{k: key[k] for k in ("item_id", "direction")},
                             "suite": item["suite"], "source_id": item["source_id"], "analysis_role": item["analysis_role"],
                             "original_gold_label": item["gold_label"], "valid": answer is not None,
                             "raw_predicted_label": answer["raw_label"] if answer else None,
                             "normalized_predicted_label": answer["label"] if answer else None,
                             "unscorable_reasons": audit["reasons"], "output_text_sha256": audit.get("output_text_sha256")})
    models = protocol["models"]
    scored = item_scores(items, keys, models, predictions)
    per_model = summaries(scored)
    for model in models:
        per_model[model]["ordered_label_coverage"] = {
            "planned": 60, "valid": sum(m == model for m, _q in predictions),
            "by_role": {role: {
                "planned": sum(item_map[k["item_id"]]["analysis_role"] == role for k in keys),
                "valid": sum((model, k["id"]) in predictions for k in keys if item_map[k["item_id"]]["analysis_role"] == role)}
                for role in ("proxy_selection", "target_selection", "target_confirmation")}}
        per_model[model]["valid_three_way_label_counts"] = dict(sorted(Counter(v["label"] for (m, _q), v in predictions.items() if m == model).items()))
    complete = metadata is not None and len(records) == 24 and len(predictions) == 120 and all(a["status"] == "valid_completed_batch" for a in audits)
    results = {"analysis_version": 1, "status": "complete" if complete else "primary_incomplete",
               "freeze": {"commit": freeze_commit, "frozen_utc": freeze_time, "protocol_sha256": protocol_sha,
                          "gate_sha256": gate_sha, "commit_verification": "Caller-supplied frozen Git commit; no remote Git object lookup. Local frozen hashes and post-freeze capture times independently checked."},
               "gate": gate, "coverage": {"planned_client_calls": 24, "aggregate_records": len(records),
                                          "valid_completed_batches": sum(a["status"] == "valid_completed_batch" for a in audits),
                                          "planned_ordered_labels": 120, "valid_ordered_labels": len(predictions),
                                          "run_metadata_present": metadata is not None},
               "per_model": per_model, "trial_audits": audits,
               "item_scores": scored, "primary": None, "bootstrap": None,
               "incomplete_rule": "Available-item scores are secondary descriptive only when any batch, item, label or run metadata is missing/invalid. Missing labels are not semantic errors; no imputation or silent dropping.",
               "annotation_caveat": protocol.get("human_review"),
               "sample_scope": "Exactly twenty PAWS proxy pairs, ten HANS selection items and ten disjoint HANS confirmation items per classifier. HANS strata are independent samples, not matched sentence pairs. Bounded effects concern only these fixed candidates, adapter and sample; no user-adoption, general prevalence or real-world harm claim.",
               "weight_identity_limit": protocol.get("weight_identity_limit")}
    if complete:
        results["primary"] = selection_outcome(scored, models)
        results["bootstrap"] = paired_bootstrap(scored, models, results["primary"])
    inputs = {"protocol.json": protocol_sha, "gate_activation.json": gate_sha, "manifest.jsonl": sha_file(directory / "manifest.jsonl"),
              "analyze_consequence.py": sha_file(Path(__file__))}
    if aggregate_path.is_file():
        inputs["responses.jsonl"] = sha_file(aggregate_path)
    if metadata_path.is_file():
        inputs["run_metadata.json"] = sha_file(metadata_path)
    results["analysis_inputs_sha256"] = inputs
    return results, exported


def write_json_exclusive(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def synthetic_self_test():
    """No local research outputs are read. All answers here are fabricated fixtures."""
    checks = []
    def check(name, ok):
        assert ok, name
        checks.append(name)
    def rejects(name, function, error=(IntegrityError, PredictionError)):
        try:
            function()
        except error:
            checks.append(name)
        else:
            raise AssertionError(name)
    qids = ["S" + str(i) for i in range(5)]
    text = json.dumps({"predictions": [{"id": q, "label": "Entailment"} for q in qids]})
    check("whole JSON and exact raw case retained", parse_predictions(text, qids)[qids[0]] == {"raw_label": "Entailment", "label": "entailment"})
    check("one outer JSON fence", len(parse_predictions("```json\n" + text + "\n```", qids)) == 5)
    rejects("prose prefix rejected", lambda: parse_predictions("Here: " + text, qids))
    rejects("extra root keys rejected", lambda: parse_predictions(text[:-1] + ',"extra":1}', qids))
    rejects("duplicate ids rejected", lambda: parse_predictions(text.replace('"S4"', '"S0"'), qids))
    rejects("missing ids rejected", lambda: parse_predictions(text, qids + ["S5"]))
    rejects("label aliases rejected", lambda: parse_predictions(text.replace("Entailment", "entails"), qids))
    rejects("whitespace label repair rejected", lambda: parse_predictions(text.replace("Entailment", " entailment"), qids))
    rejects("duplicate object keys rejected", lambda: parse_predictions('{"predictions":[],"predictions":[]}', qids))
    freeze = timestamp("2026-01-01T00:00:00Z")
    gate = {"activated": True, "mechanism": "PAWS_TO_DIRECTIONAL_NLI", "qualifying_configuration": "fixture-config",
            "completed_replicates": 3, "same_mechanism_count": 2, "source_trial_ids": ["R1", "R2", "R3"],
            "replicates": [{"trial_id": "R" + str(i), "configuration": "fixture-config", "completed": True,
                            "fresh": True, "original_question": True, "same_mechanism": i < 3} for i in (1, 2, 3)],
            "source_freeze_commit": "a" * 40, "source_summary_sha256": "b" * 64, "generated_utc": "2025-12-31T23:00:00Z"}
    check("external gate receipt accepted", validate_gate(gate, freeze)["same_mechanism_count"] == 2)
    bad = copy.deepcopy(gate); bad["replicates"][0]["configuration"] = "other"
    rejects("pooled gate configurations rejected", lambda: validate_gate(bad, freeze))
    bad = copy.deepcopy(gate); bad["activated"] = False
    rejects("failed gate rejected", lambda: validate_gate(bad, freeze))
    bad = copy.deepcopy(gate); bad["completed_replicates"] = 4
    rejects("posthoc enlarged gate rejected", lambda: validate_gate(bad, freeze))
    with tempfile.TemporaryDirectory(prefix="consequence-synthetic-") as temporary:
        directory = Path(temporary)
        row = {"trial_id": "SYN-1", "requested_model": "synthetic-model", "task_ids": qids,
               "batch_role": "proxy_selection", "request_payload": {"model": "synthetic-model", "stream": True}}
        raw = {"id": "synthetic-response", "model": "synthetic-model", "status": "completed", "output": [
            {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}], "usage": {"output_tokens": 1}}
        data = {"type": "response.completed", "response": raw}
        frames = [{"event": "response.completed", "data": data, "data_text": json.dumps(data), "partial_frame": False,
                   "json_error": False, "captured_utc": "2026-01-01T00:00:02Z"},
                  {"event": "capture_end", "captured_utc": "2026-01-01T00:00:03Z", "http_status": 200,
                   "terminal_event": "response.completed", "transport_error": None}]
        journal, artifact = directory / "SYN-1.jsonl", directory / "SYN-1.json"
        journal.write_text("".join(json.dumps(f) + "\n" for f in frames))
        record = {"trial_id": "SYN-1", "attempt_count": 1, "request_payload": row["request_payload"], "requested_model": "synthetic-model",
                  "request_sha256": sha_bytes(canonical(row["request_payload"])), "started_utc": "2026-01-01T00:00:01Z", "ended_utc": "2026-01-01T00:00:04Z",
                  "output_text": text, "output_text_sha256": sha_bytes(text.encode()), "stream_journal_sha256": sha_file(journal),
                  "stream_frame_count": 1, "stream_json_error_count": 0, "http_status": 200, "terminal_event": "response.completed",
                  "transport_error": None, "raw_response": raw, "terminal_event_seen": True, "response_id": raw["id"], "returned_model": raw["model"],
                  "response_status": "completed", "usage": raw["usage"], "api_error": None, "incomplete_details": None,
                  "text_source": "terminal_message_output_text", "used_delta_fallback": False, "parse_mode": "sse", "response_content_type": "text/event-stream",
                  "stream_format_deviation": False, "stream_incomplete": False, "completed_nonempty": True}
        def save(record_value):
            artifact.write_text(json.dumps(record_value))
        save(record)
        check("terminal SSE artifact fixture accepted", len(audit_trial(row, record, artifact, journal, freeze)[1]) == 5)
        changed = copy.deepcopy(record); changed["output_text"] += "x"; save(changed)
        rejects("tampered text hash rejected", lambda: audit_trial(row, changed, artifact, journal, freeze))
        changed = copy.deepcopy(record); changed["request_payload"]["model"] = "other"; save(changed)
        rejects("changed wire request rejected", lambda: audit_trial(row, changed, artifact, journal, freeze))
        changed = copy.deepcopy(record); changed["started_utc"] = "2025-12-31T23:59:59Z"; save(changed)
        rejects("pre-freeze inference rejected", lambda: audit_trial(row, changed, artifact, journal, freeze))
        save(record)
        journal.write_text(journal.read_text() + "\n")
        rejects("tampered journal hash rejected", lambda: audit_trial(row, record, artifact, journal, freeze))
        journal.write_text("".join(json.dumps(f) + "\n" for f in frames)); save(record)
        check("missing journal unscorable", audit_trial(row, record, artifact, directory / "missing", freeze)[0]["status"] == "unscorable")
        changed = copy.deepcopy(record); changed["stream_incomplete"] = True; save(changed)
        check("incomplete capture not promoted", not audit_trial(row, changed, artifact, journal, freeze)[1])
        changed = copy.deepcopy(record); changed["used_delta_fallback"] = True; save(changed)
        check("delta fallback not promoted", not audit_trial(row, changed, artifact, journal, freeze)[1])
        frames[0]["partial_frame"] = True
        journal.write_text("".join(json.dumps(f) + "\n" for f in frames))
        changed = copy.deepcopy(record); changed["stream_journal_sha256"] = sha_file(journal); save(changed)
        check("partial terminal not promoted", not audit_trial(row, changed, artifact, journal, freeze)[1])
    models = ["synthetic-A", "synthetic-B"]
    items, keys, predictions = [], [], {}
    for suite, role, golds, count in (("paws", "proxy_selection", [0, 1], 10),
                                     ("hans", "target_selection", ["entailment", "non-entailment"], 5),
                                     ("hans", "target_confirmation", ["entailment", "non-entailment"], 5)):
        for gold in golds:
            for number in range(count):
                iid = "S" + str(len(items))
                items.append({"item_id": iid, "suite": suite, "source_id": iid, "analysis_role": role, "gold_label": gold})
                for direction in (["forward", "reverse"] if suite == "paws" else ["forward"]):
                    qid = "Q" + str(len(keys)); keys.append({"id": qid, "item_id": iid, "direction": direction})
                    for model in models:
                        correct = (model == models[0]) if suite == "paws" else (model == models[1])
                        is_entailing = (bool(gold) if suite == "paws" else gold == "entailment") if correct else (not bool(gold) if suite == "paws" else gold != "entailment")
                        label = "entailment" if is_entailing else "neutral"
                        predictions[(model, qid)] = {"label": label, "raw_label": label}
    scored = item_scores(items, keys, models, predictions)
    outcome = selection_outcome(scored, models)
    check("strict opposite ordering detected", outcome["strict_reversal"] is True)
    check("fixed winner heldout signed consequence", outcome["heldout_target_selected_minus_proxy_selected_accuracy"] == 1)
    boot = paired_bootstrap(scored, models, outcome)
    check("10000 fixed-winner paired stratum draws", boot["draws"] == 10000 and boot["intervals"]["heldout_target_selected_minus_proxy_selected"] == {"lower": 1.0, "upper": 1.0})
    tie = copy.deepcopy(scored); tie[models[1]] = copy.deepcopy(tie[models[0]])
    check("ties remain indeterminate", selection_outcome(tie, models)["strict_reversal"] is None)
    neg = copy.deepcopy(scored)
    for model in models:
        for r in neg[model]:
            if r["analysis_role"] == "target_confirmation": r["correct"] = not r["correct"]
    check("negative holdout consequence retained", selection_outcome(neg, models)["heldout_target_selected_minus_proxy_selected_accuracy"] == -1)
    zero = copy.deepcopy(scored)
    for model in models:
        for r in zero[model]:
            if r["analysis_role"] == "target_confirmation": r["correct"] = True
    check("zero holdout consequence retained", selection_outcome(zero, models)["heldout_target_selected_minus_proxy_selected_accuracy"] == 0)
    mixed = copy.deepcopy(scored)
    proxy_ids = [r["item_id"] for r in mixed[models[0]] if r["analysis_role"] == "proxy_selection"]
    for model in models:
        for r in mixed[model]:
            if r["analysis_role"] == "proxy_selection":
                index = proxy_ids.index(r["item_id"])
                r["correct"] = index % 10 < (6 if index < 10 else 5) if model == models[0] else index % 10 >= 5
    mixed_outcome = selection_outcome(mixed, models)
    mixed_boot = paired_bootstrap(mixed, models, mixed_outcome)
    check("bootstrap ranking can cross zero without reselection", mixed_boot["intervals"]["proxy_selection_model_difference"]["lower"] < 0 and
          mixed_boot["intervals"]["proxy_selection_model_difference"]["upper"] > 0 and
          mixed_boot["intervals"]["heldout_target_selected_minus_proxy_selected"] == {"lower": 1.0, "upper": 1.0})
    check("linear percentile interpolation", linear_quantile([0, 10, 20, 30], .25) == 7.5)
    # One non-entailing PAWS direction must prevent a paraphrase prediction.
    probe = copy.deepcopy(predictions)
    iid = next(i["item_id"] for i in items if i["suite"] == "paws" and i["gold_label"] == 1)
    qid = next(k["id"] for k in keys if k["item_id"] == iid and k["direction"] == "reverse")
    probe[(models[0], qid)] = {"label": "contradiction", "raw_label": "contradiction"}
    check("mutual-entailment PAWS adapter", next(r for r in item_scores(items, keys, models, probe)[models[0]] if r["item_id"] == iid)["predicted_label"] == 0)
    del probe[(models[0], qid)]
    missing = item_scores(items, keys, models, probe)
    rejects("missing direction blocks primary", lambda: selection_outcome(missing, models))
    check("missing labels are not incorrect semantics", next(r for r in missing[models[0]] if r["item_id"] == iid)["correct"] is None)
    # End-to-end fixture: synthetic sources, frozen files, 24 terminal journals,
    # 24 individual artifacts and their aggregate. No research captures opened.
    with tempfile.TemporaryDirectory(prefix="consequence-synthetic-full-") as temporary:
        directory = Path(temporary)
        fixture_items = copy.deepcopy(items)
        for item in fixture_items:
            item.update(sentence1="Synthetic premise " + item["item_id"], sentence2="Synthetic hypothesis " + item["item_id"])
        fixture_map = {i["item_id"]: i for i in fixture_items}
        write_json_exclusive(directory / "selected_data.json", {"items": fixture_items})
        write_json_exclusive(directory / "selection_manifest.json", {
            "selected_data_sha256": sha_file(directory / "selected_data.json"),
            "item_selection": [{k: i[k] for k in ("item_id", "suite", "source_id", "analysis_role", "gold_label")} for i in fixture_items]})
        write_json_exclusive(directory / "task_key.json", keys)
        fixture_manifest = []
        for model in models:
            batch_index = 0
            for role in ("proxy_selection", "target_selection", "target_confirmation"):
                role_keys = [k for k in keys if fixture_map[k["item_id"]]["analysis_role"] == role]
                for offset in range(0, len(role_keys), 5):
                    batch_index += 1
                    group = role_keys[offset:offset + 5]
                    questions = []
                    for key in group:
                        item = fixture_map[key["item_id"]]
                        a, b = ("sentence1", "sentence2") if key["direction"] == "forward" else ("sentence2", "sentence1")
                        questions.append({"id": key["id"], "premise": item[a], "hypothesis": item[b]})
                    payload = {"model": model, "instructions": "Synthetic classification fixture only.", "input": json.dumps(questions),
                               "stream": True, "temperature": 0.0, "max_output_tokens": 8192, "tools": [], "tool_choice": "none", "agentic_memory": False, "store": False}
                    fixture_manifest.append({"trial_id": "SYN-" + str(len(fixture_manifest) + 1), "requested_model": model,
                                             "batch_index": batch_index, "batch_role": role, "task_ids": [k["id"] for k in group], "request_payload": payload})
        (directory / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in fixture_manifest))
        (directory / "analyze_consequence.py").write_bytes(Path(__file__).read_bytes())
        (directory / "synthetic_runner.py").write_text("# Synthetic frozen runner identity; never executed.\n")
        fixture_protocol = {"models": models, "uncertainty": {"bootstrap_repeats": BOOTSTRAP_DRAWS, "bootstrap_seed": BOOTSTRAP_SEED, "confidence_level": .95},
                            "artifacts_sha256": {f: sha_file(directory / f) for f in ("selected_data.json", "selection_manifest.json", "task_key.json", "manifest.jsonl", "analyze_consequence.py")},
                            "native_sse_runner": {"path": "synthetic_runner.py", "sha256": sha_file(directory / "synthetic_runner.py"), "stream_true_required": True}}
        write_json_exclusive(directory / "protocol.json", fixture_protocol)
        write_json_exclusive(directory / "gate_activation.json", gate)
        protocol_hash, gate_hash = sha_file(directory / "protocol.json"), sha_file(directory / "gate_activation.json")
        check("full frozen input fixture accepted", len(frozen_inputs(directory, protocol_hash, gate_hash, freeze)[4]) == 24)
        fixture_result, _ = analyze(directory, "c" * 40, freeze.isoformat(), protocol_hash, gate_hash)
        check("no captures produce incomplete rather than invented scores", fixture_result["status"] == "primary_incomplete" and fixture_result["primary"] is None)
        (directory / "api_artifacts").mkdir(); (directory / "stream_journals").mkdir()
        fixture_records = []
        for row in fixture_manifest:
            tid, model = row["trial_id"], row["requested_model"]
            answer = json.dumps({"predictions": [{"id": q, "label": predictions[(model, q)]["raw_label"]} for q in row["task_ids"]]})
            raw = {"id": "response-" + tid, "model": model, "status": "completed", "output": [
                {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": answer}]}], "usage": {"output_tokens": 1}}
            data = {"type": "response.completed", "response": raw}
            frames = [{"event": "response.completed", "data": data, "data_text": json.dumps(data), "partial_frame": False,
                       "json_error": False, "captured_utc": "2026-01-01T00:00:02Z"},
                      {"event": "capture_end", "captured_utc": "2026-01-01T00:00:03Z", "http_status": 200,
                       "terminal_event": "response.completed", "transport_error": None}]
            journal = directory / "stream_journals" / (tid + ".jsonl")
            journal.write_text("".join(json.dumps(f) + "\n" for f in frames))
            fixture_record = copy.deepcopy(record)
            fixture_record.update(trial_id=tid, requested_model=model, request_payload=row["request_payload"],
                                  request_sha256=sha_bytes(canonical(row["request_payload"])), output_text=answer,
                                  output_text_sha256=sha_bytes(answer.encode()), stream_journal_sha256=sha_file(journal),
                                  raw_response=raw, response_id=raw["id"], returned_model=model)
            write_json_exclusive(directory / "api_artifacts" / (tid + ".json"), fixture_record)
            fixture_records.append(fixture_record)
        (directory / "responses.jsonl").write_text("".join(json.dumps(r) + "\n" for r in fixture_records))
        metadata = {"manifest_sha256": sha_file(directory / "manifest.jsonl"), "requested": 24, "recorded": 24, "attempts_per_trial": 1,
                    "retries": 0, "concurrency": 2, "socket_timeout_seconds": 120, "transport": "native_sse", "completed_capture_utc": "2026-01-01T00:00:05Z"}
        write_json_exclusive(directory / "run_metadata.json", metadata)
        fixture_result, fixture_predictions = analyze(directory, "c" * 40, freeze.isoformat(), protocol_hash, gate_hash)
        check("full analysis audits all 120 synthetic labels", fixture_result["status"] == "complete" and len(fixture_predictions) == 120 and fixture_result["coverage"]["valid_ordered_labels"] == 120)
        check("full analysis preserves raw labels and keys", all(r["raw_predicted_label"] in LABELS and r["item_id"] and r["id"] for r in fixture_predictions))
        check("full analysis reproduces known reversal", fixture_result["primary"]["strict_reversal"] is True and fixture_result["primary"]["heldout_target_selected_minus_proxy_selected_accuracy"] == 1)
        changed_record = copy.deepcopy(fixture_records[0]); changed_record["output_text"] = "tamper"
        first_artifact = directory / "api_artifacts" / (fixture_records[0]["trial_id"] + ".json")
        first_artifact.write_text(json.dumps(changed_record))
        rejects("aggregate versus individual mismatch blocks analysis", lambda: analyze(directory, "c" * 40, freeze.isoformat(), protocol_hash, gate_hash))
        first_artifact.write_text(json.dumps(fixture_records[0]))
        (directory / "responses.jsonl").write_text("".join(json.dumps(r) + "\n" for r in fixture_records[:-1]))
        metadata["recorded"] = 23
        (directory / "run_metadata.json").write_text(json.dumps(metadata))
        fixture_result, _ = analyze(directory, "c" * 40, freeze.isoformat(), protocol_hash, gate_hash)
        check("missing batch blocks all primary inference", fixture_result["status"] == "primary_incomplete" and fixture_result["primary"] is None and fixture_result["bootstrap"] is None)
        (directory / "task_key.json").write_text("[]")
        rejects("changed frozen task key blocks analysis", lambda: analyze(directory, "c" * 40, freeze.isoformat(), protocol_hash, gate_hash))
    return {"status": "passed", "kind": "synthetic_offline_verification_only_not_research_results", "checks_passed": len(checks), "checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--freeze-commit")
    parser.add_argument("--freeze-time")
    parser.add_argument("--freeze-protocol-sha256")
    parser.add_argument("--gate-sha256")
    parser.add_argument("--output-directory", type=Path, help="New directory only; defaults to experiment/analysis")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(synthetic_self_test(), indent=2))
        return
    for name in ("freeze_commit", "freeze_time", "freeze_protocol_sha256", "gate_sha256"):
        if not getattr(args, name):
            parser.error("--" + name.replace("_", "-") + " is required for actual analysis")
    directory = args.directory.resolve()
    try:
        result, predictions = analyze(directory, args.freeze_commit, args.freeze_time, args.freeze_protocol_sha256, args.gate_sha256)
    except (IntegrityError, ValueError, KeyError, OSError, TypeError) as exc:
        raise SystemExit("Analysis blocked: " + str(exc)) from exc
    output = args.output_directory or directory / "analysis"
    output.mkdir(parents=True, exist_ok=False)
    write_json_exclusive(output / "results.json", result)
    with (output / "predictions.jsonl").open("x", encoding="utf-8") as handle:
        for row in predictions:
            handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "results": str(output / "results.json"),
                      "predictions": str(output / "predictions.jsonl"), "coverage": result["coverage"], "primary": result["primary"]}, indent=2))


if __name__ == "__main__":
    main()
