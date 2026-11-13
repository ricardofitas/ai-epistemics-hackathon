#!/usr/bin/env python3
"""Source-only model preparation and frozen CPU NLI inference.

This is a separate public-model cohort. It never executes the Adaption manifest.
The model sees only premise/hypothesis; gold and split labels remain local to
the analysis files. A failed or interrupted model leaves partial output and is
never silently resumed or replaced.
"""
import argparse
import datetime as dt
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parent
LABELS = {"contradiction", "entailment", "neutral"}
ALLOW = [
    "config.json", "model.safetensors", "tokenizer.json",
    "tokenizer_config.json", "special_tokens_map.json", "spm.model",
    "sentencepiece.bpe.model", "vocab.json", "merges.txt",
    "added_tokens.json", "tokenizer.model",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def verify_sources(protocol):
    for relative, expected in protocol["source_sha256"].items():
        path = (ROOT / relative).resolve()
        if sha(path) != expected:
            raise ValueError(f"Frozen source mismatch: {relative}")
    wsc = load(ROOT / "../wsc/selected_data.json")["items"]
    wkey = load(ROOT / "../wsc/task_key.json")["rows"]
    hans = load(ROOT / "../hans_target/selected_data.json")["items"]
    hkey = load(ROOT / "../hans_target/task_key.json")["rows"]
    if len(wsc) != 72 or len(wkey) != 144 or len(hans) != 80 or len(hkey) != 80:
        raise ValueError("Unexpected source counts")
    if sum(x["analysis_role"] == "selection" for x in wsc) != 35:
        raise ValueError("Unexpected selection count")
    if sum(x["analysis_role"] == "confirmation" for x in wsc) != 37:
        raise ValueError("Unexpected confirmation count")
    by_passage = {x["passage_id"]: x for x in wsc}
    tasks = []
    for row in wkey:
        item = by_passage[row["passage_id"]]
        field = "gold_replacement_hypothesis" if row["variant"] == "gold" else "non_gold_replacement_hypothesis"
        tasks.append((row["task_id"], item["premise"], item[field]))
    by_hans = {x["task_id"]: x for x in hans}
    for row in hkey:
        item = by_hans[row["task_id"]]
        tasks.append((row["task_id"], item["premise"], item["hypothesis"]))
    ids = [x[0] for x in tasks]
    if len(tasks) != 224 or len(ids) != len(set(ids)):
        raise ValueError("Missing or duplicated NLI input")
    return tasks


def prepare_sources(protocol):
    receipt_path = ROOT / "source_receipt.json"
    if receipt_path.exists():
        raise FileExistsError("Source receipt exists; refuse to rewrite an observed source pin")
    models = []
    for spec in protocol["models"]:
        directory = ROOT / "models" / spec["slug"]
        if not directory.exists():
            from huggingface_hub import snapshot_download
            directory.mkdir(parents=True)
            snapshot_download(
                repo_id=spec["id"], revision=spec["revision"],
                local_dir=directory, allow_patterns=ALLOW,
            )
        elif not directory.is_dir():
            raise ValueError("Model path is not a directory: " + str(directory))
        files = []
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or ".cache" in path.parts:
                continue
            metadata = directory / ".cache" / "huggingface" / "download" / (
                str(path.relative_to(directory)) + ".metadata")
            if not metadata.is_file() or metadata.read_text().splitlines()[0] != spec["revision"]:
                raise ValueError("No matching pinned revision download metadata: " + str(path))
            files.append({"path": str(path.relative_to(directory)),
                          "bytes": path.stat().st_size, "sha256": sha(path),
                          "download_metadata_sha256": sha(metadata)})
        names = {x["path"] for x in files}
        if names - set(ALLOW) or len(names) != len(files):
            raise ValueError("Unexpected file in model snapshot: " + spec["slug"])
        if "config.json" not in names or "model.safetensors" not in names:
            raise ValueError("Required pinned model source missing: " + spec["slug"])
        expected_weight = protocol["model_weight_sha256"][spec["slug"]]
        if sha(directory / "model.safetensors") != expected_weight:
            raise ValueError("Weight hash differs from prior pinned download: " + spec["slug"])
        config = load(directory / "config.json")
        labels = {str(x).strip().lower().replace("_", "-")
                  for x in config["id2label"].values()}
        if labels != LABELS:
            raise ValueError(f"Not an exact three-way NLI classifier: {spec['slug']} {labels}")
        models.append({**spec, "files": files, "id2label": config["id2label"],
                       "max_position_embeddings": config.get("max_position_embeddings")})
        print(json.dumps({"prepared": spec["slug"], "files": len(files),
                          "weight_bytes": (directory / "model.safetensors").stat().st_size}), flush=True)
    receipt = {"prepared_utc": now(), "status": "source_only_no_inference",
               "protocol_sha256": sha(ROOT / "protocol.json"),
               "source_sha256": protocol["source_sha256"], "models": models}
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"source_receipt_sha256": sha(receipt_path),
                      "model_count": len(models), "inference_calls": 0}))


def verify_model_sources(protocol):
    receipt_path = ROOT / "source_receipt.json"
    receipt = load(receipt_path)
    if receipt["protocol_sha256"] != sha(ROOT / "protocol.json"):
        raise ValueError("Source receipt does not match exact protocol")
    if receipt["source_sha256"] != protocol["source_sha256"]:
        raise ValueError("Source receipt input pins differ")
    if receipt["status"] != "source_only_no_inference":
        raise ValueError("Source receipt status changed")
    if [{k: x[k] for k in ("slug", "id", "revision")} for x in receipt["models"]] != protocol["models"]:
        raise ValueError("Model order, ID or revision changed")
    for spec in receipt["models"]:
        directory = ROOT / "models" / spec["slug"]
        observed = {str(p.relative_to(directory)) for p in directory.rglob("*")
                    if p.is_file() and ".cache" not in p.parts}
        pinned = {entry["path"] for entry in spec["files"]}
        if observed != pinned or observed - set(ALLOW):
            raise ValueError("Unexpected file set in model snapshot: " + spec["slug"])
        if next(x["sha256"] for x in spec["files"] if x["path"] == "model.safetensors") != protocol["model_weight_sha256"][spec["slug"]]:
            raise ValueError("Weight hash does not match protocol: " + spec["slug"])
        for entry in spec["files"]:
            path = directory / entry["path"]
            if path.stat().st_size != entry["bytes"] or sha(path) != entry["sha256"]:
                raise ValueError("Model file differs from pinned source: " + str(path))
            metadata = directory / ".cache" / "huggingface" / "download" / (entry["path"] + ".metadata")
            if sha(metadata) != entry["download_metadata_sha256"] or metadata.read_text().splitlines()[0] != spec["revision"]:
                raise ValueError("Pinned revision metadata changed: " + str(path))
    return receipt_path


def validate_freeze(args, protocol):
    if not re.fullmatch("[0-9a-f]{40}", args.freeze_commit or ""):
        raise ValueError("Real external Git freeze commit required")
    if args.freeze_protocol_sha256 != sha(ROOT / "protocol.json"):
        raise ValueError("Published protocol SHA does not match local bytes")
    if args.freeze_source_sha256 != sha(ROOT / "source_receipt.json"):
        raise ValueError("Published model-source receipt SHA does not match")
    if args.freeze_runner_sha256 != sha(ROOT / "run_local_nli.py"):
        raise ValueError("Published runner SHA does not match")
    instant = dt.datetime.fromisoformat(args.freeze_time.replace("Z", "+00:00"))
    if instant.tzinfo is None or instant > dt.datetime.now(dt.timezone.utc):
        raise ValueError("Freeze time must be in the past")
    verify_sources(protocol)
    verify_model_sources(protocol)


def run(args, protocol, tasks):
    validate_freeze(args, protocol)
    output = ROOT / "predictions"
    if output.exists():
        raise FileExistsError("Prediction directory already exists; no silent resume or overwrite")
    output.mkdir()
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if torch.__version__ != protocol["inference"]["torch_version"]:
        raise ValueError("Unexpected torch version")
    import transformers
    if transformers.__version__ != protocol["inference"]["transformers_version"]:
        raise ValueError("Unexpected transformers version")
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(20261113)
    for spec in protocol["models"]:
        start = time.monotonic()
        directory = ROOT / "models" / spec["slug"]
        tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True, use_fast=True,
                                                   trust_remote_code=False)
        model = AutoModelForSequenceClassification.from_pretrained(
            directory, local_files_only=True, use_safetensors=True, trust_remote_code=False)
        model.eval()
        labels = {int(k): str(v).strip().lower().replace("_", "-")
                  for k, v in model.config.id2label.items()}
        if set(labels.values()) != LABELS or len(labels) != 3:
            raise ValueError("Unusable label map: " + spec["slug"])
        limit = getattr(model.config, "max_position_embeddings", None)
        partial = output / (spec["slug"] + ".partial.jsonl")
        final = output / (spec["slug"] + ".jsonl")
        with partial.open("x") as stream, torch.inference_mode():
            for offset in range(0, len(tasks), 8):
                batch = tasks[offset:offset + 8]
                encoded = tokenizer([x[1] for x in batch], [x[2] for x in batch],
                                    padding=True, truncation=False, return_tensors="pt")
                if limit and encoded["input_ids"].shape[1] > limit:
                    raise ValueError(f"Untruncated input exceeds model limit: {spec['slug']}")
                logits = model(**encoded).logits.float().cpu()
                if tuple(logits.shape) != (len(batch), 3):
                    raise ValueError("Unexpected output shape")
                for task, vector in zip(batch, logits.tolist()):
                    index = int(max(range(3), key=lambda j: vector[j]))
                    row = {"task_id": task[0], "label": labels[index],
                           "logits": vector}
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        partial.rename(final)
        receipt = {"status": "complete", "model_id": spec["id"],
                   "revision": spec["revision"], "slug": spec["slug"], "rows": 224,
                   "predictions_sha256": sha(final),
                   "protocol_sha256": sha(ROOT / "protocol.json"),
                   "source_receipt_sha256": sha(ROOT / "source_receipt.json"),
                   "freeze_commit": args.freeze_commit,
                   "completed_utc": now(), "elapsed_seconds": round(time.monotonic() - start, 3),
                   "label_map": labels, "device": "cpu", "batch_size": 8,
                   "inference_mode": "eval_no_grad_deterministic_algorithms",
                   "input_truncation": False}
        (output / (spec["slug"] + ".receipt.json")).write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"complete": spec["slug"], "rows": 224,
                          "predictions_sha256": receipt["predictions_sha256"]}), flush=True)
        del model, tokenizer
        gc.collect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-sources", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--freeze-commit")
    parser.add_argument("--freeze-time")
    parser.add_argument("--freeze-protocol-sha256")
    parser.add_argument("--freeze-source-sha256")
    parser.add_argument("--freeze-runner-sha256")
    args = parser.parse_args()
    if sum((args.prepare_sources, args.preflight, args.run)) != 1:
        parser.error("Select exactly one mode")
    protocol = load(ROOT / "protocol.json")
    tasks = verify_sources(protocol)
    if args.prepare_sources:
        prepare_sources(protocol)
    elif args.preflight:
        verify_model_sources(protocol)
        print(json.dumps({"source_pins_verified": True, "tasks": len(tasks),
                          "source_receipt_sha256": sha(ROOT / "source_receipt.json"),
                          "inference_calls": 0}))
    else:
        run(args, protocol, tasks)


if __name__ == "__main__":
    main()
