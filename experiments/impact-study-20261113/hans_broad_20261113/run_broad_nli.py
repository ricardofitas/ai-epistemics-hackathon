#!/usr/bin/env python3
"""Frozen CPU inference for the source-only HANS600 external holdout.

This is a separate cohort. It does not inspect initial WSC predictions or
analysis. The model receives only ordered premise and hypothesis strings.
"""
import argparse
import datetime as dt
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT.parent / "local_nli_20261113"
sys.path.insert(0, str(LOCAL))
from run_local_nli import verify_model_sources, verify_sources  # source-only checks


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def verify_plan():
    plan = read(ROOT / "inference_plan.json")
    broad = read(ROOT / "protocol.json")
    source_path = ROOT / "selected_data.json"
    key_path = ROOT / "task_key.json"
    local_protocol = read(LOCAL / "protocol.json")
    require(sha(ROOT / "protocol.json") == plan["broad_protocol_sha256"],
            "Broad source-only protocol changed")
    require(sha(source_path) == plan["selected_data_sha256"] ==
            broad["selection"]["selected_data_sha256"], "Broad data changed")
    require(sha(key_path) == plan["task_key_sha256"] ==
            broad["selection"]["task_key_sha256"], "Broad key changed")
    require(sha(LOCAL / "protocol.json") == plan["local_protocol_sha256"] ==
            broad["candidate_set"]["source_protocol_sha256"],
            "Original local cohort protocol changed")
    require(sha(LOCAL / "source_receipt.json") == plan["source_receipt_sha256"],
            "Original model source receipt changed")
    require(sha(LOCAL / "analysis" / "summary.json") == plan["wsc_analysis_sha256"],
            "Original WSC selection analysis changed")
    require([x["slug"] for x in local_protocol["models"]] ==
            broad["candidate_set"]["models"] == plan["models"],
            "Candidate set/order changed")
    require(local_protocol["model_weight_sha256"] == plan["model_weight_sha256"],
            "Model weight pins changed")
    verify_sources(local_protocol)
    verify_model_sources(local_protocol)
    items = read(source_path)["items"]
    keys = read(key_path)["rows"]
    require(len(items) == len(keys) == 600, "Expected 600 HANS cases")
    require([x["task_id"] for x in items] == [x["task_id"] for x in keys] and
            len({x["task_id"] for x in items}) == 600, "Task-key mismatch")
    require(all(x["source_pair_id"] == y["source_pair_id"]
                for x, y in zip(items, keys)), "Official pair ID mismatch")
    require(len({x["source_pair_id"] for x in items}) == 600 and
            len({(x["premise"], x["hypothesis"]) for x in items}) == 600,
            "Duplicate HANS cases")
    require(all(x["task_id"] == f"B{i:03d}" for i, x in enumerate(items, 1)),
            "Unexpected task order")
    from collections import Counter
    strata = Counter((x["heuristic"], x["gold_binary"], x["subcase"])
                     for x in items)
    cells = Counter((x["heuristic"], x["gold_binary"]) for x in items)
    require(len(strata) == 30 and set(strata.values()) == {20} and
            len(cells) == 6 and set(cells.values()) == {100},
            "Broad balance/coverage changed")
    prior = read(ROOT.parent / "hans_target" / "selected_data.json")["items"]
    require(sha(ROOT.parent / "hans_target" / "selected_data.json") ==
            broad["source"]["prior_hans80_sha256"], "Prior HANS80 changed")
    require(not ({x["source_pair_id"] for x in items} &
                 {x["source_pair_id"] for x in prior}) and
            not ({(x["premise"], x["hypothesis"]) for x in items} &
                 {(x["premise"], x["hypothesis"]) for x in prior}),
            "HANS600 overlaps HANS80")
    return plan, broad, local_protocol, items


def verify_freeze(args):
    require(re.fullmatch(r"[0-9a-f]{40}", args.freeze_commit or "") is not None,
            "Real Git freeze commit required")
    instant = dt.datetime.fromisoformat((args.freeze_time or "").replace("Z", "+00:00"))
    require(instant.tzinfo is not None and instant <= dt.datetime.now(dt.timezone.utc),
            "Freeze time must be real and earlier than inference")
    for path, observed in ((ROOT / "inference_plan.json", args.freeze_plan_sha256),
                           (ROOT / "protocol.json", args.freeze_broad_protocol_sha256),
                           (ROOT / "run_broad_nli.py", args.freeze_runner_sha256)):
        require(sha(path) == observed, "Published freeze hash mismatch: " + path.name)


def run(args, plan, local_protocol, items):
    verify_freeze(args)
    out = ROOT / "broad_predictions"
    require(not out.exists(), "Prediction directory already exists; no overwrite/resume")
    out.mkdir()
    import torch
    import transformers
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    require(torch.__version__ == local_protocol["inference"]["torch_version"] and
            transformers.__version__ == local_protocol["inference"]["transformers_version"],
            "Frozen runtime versions changed")
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(20261113)
    for spec in local_protocol["models"]:
        start = time.monotonic()
        directory = LOCAL / "models" / spec["slug"]
        tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True,
                                                   use_fast=True, trust_remote_code=False)
        model = AutoModelForSequenceClassification.from_pretrained(
            directory, local_files_only=True, use_safetensors=True, trust_remote_code=False)
        model.eval()
        labels = {int(k): str(v).strip().lower().replace("_", "-")
                  for k, v in model.config.id2label.items()}
        require(set(labels.values()) == {"entailment", "contradiction", "neutral"}
                and len(labels) == 3, "Unexpected model labels")
        limit = getattr(model.config, "max_position_embeddings", None)
        partial = out / (spec["slug"] + ".partial.jsonl")
        final = out / (spec["slug"] + ".jsonl")
        with partial.open("x") as stream, torch.inference_mode():
            for offset in range(0, 600, 8):
                batch = items[offset:offset + 8]
                encoded = tokenizer([x["premise"] for x in batch],
                                    [x["hypothesis"] for x in batch],
                                    padding=True, truncation=False, return_tensors="pt")
                require(not limit or encoded["input_ids"].shape[1] <= limit,
                        "Untruncated input exceeds model position limit")
                logits = model(**encoded).logits.float().cpu()
                require(tuple(logits.shape) == (len(batch), 3), "Unexpected logits shape")
                for item, vector in zip(batch, logits.tolist()):
                    index = max(range(3), key=lambda j: vector[j])
                    stream.write(json.dumps({"task_id": item["task_id"],
                                             "label": labels[index], "logits": vector},
                                            allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        partial.rename(final)
        receipt = {"status": "complete", "model_id": spec["id"],
                   "revision": spec["revision"], "slug": spec["slug"],
                   "model_weight_sha256": plan["model_weight_sha256"][spec["slug"]],
                   "rows": 600, "predictions_sha256": sha(final),
                   "plan_sha256": sha(ROOT / "inference_plan.json"),
                   "broad_protocol_sha256": sha(ROOT / "protocol.json"),
                   "source_receipt_sha256": sha(LOCAL / "source_receipt.json"),
                   "freeze_commit": args.freeze_commit,
                   "completed_utc": now(), "elapsed_seconds": round(time.monotonic() - start, 3),
                   "label_map": labels, "device": "cpu", "batch_size": 8,
                   "inference_mode": "eval_no_grad", "input_truncation": False}
        (out / (spec["slug"] + ".receipt.json")).write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"complete": spec["slug"], "rows": 600,
                          "predictions_sha256": receipt["predictions_sha256"]}), flush=True)
        del model, tokenizer
        gc.collect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--freeze-commit")
    parser.add_argument("--freeze-time")
    parser.add_argument("--freeze-plan-sha256")
    parser.add_argument("--freeze-broad-protocol-sha256")
    parser.add_argument("--freeze-runner-sha256")
    args = parser.parse_args()
    require(args.preflight != args.run, "Choose exactly one mode")
    plan, _, local_protocol, items = verify_plan()
    if args.preflight:
        print(json.dumps({"source_pins_verified": True, "items": len(items),
                          "models": len(local_protocol["models"]), "inference_calls": 0}))
    else:
        run(args, plan, local_protocol, items)


if __name__ == "__main__":
    main()
