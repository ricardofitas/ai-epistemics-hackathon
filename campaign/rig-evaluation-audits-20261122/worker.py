"""Run a frozen WinoGrande split on a single UUID-pinned GPU."""
import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from freeze import ROOT, source_items


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def command(*args):
    return subprocess.check_output(args, text=True, timeout=10).strip()


def gpu_state(gpu):
    fields = "uuid,pci.bus_id,name,memory.free,utilization.gpu"
    output = command("nvidia-smi", "-i", gpu["uuid"], "--query-gpu=" + fields,
                     "--format=csv,noheader,nounits")
    uuid, pci, name, free, utilization = (value.strip() for value in output.split(","))
    if (uuid, pci, name) != (gpu["uuid"], gpu["pci"], gpu["name"]):
        raise RuntimeError("GPU identity differs from protocol")
    return {"free_mib": int(free), "utilization_percent": int(utilization)}


def boinc_state(gpu):
    host = command("boinccmd", "--host", gpu["boinc_rpc"], "--get_host_info")
    if f'NVIDIA GPU: {gpu["name"]} (' not in host:
        raise RuntimeError("BOINC RPC returned a different GPU")
    status = command("boinccmd", "--host", gpu["boinc_rpc"], "--get_cc_status")
    gpu_status = status.split("GPU status\n", 1)[1].split("Network status", 1)[0].strip()
    tasks = command("boinccmd", "--host", gpu["boinc_rpc"], "--get_tasks")
    return {"gpu_status": gpu_status, "executing_tasks": tasks.count("active_task_state: EXECUTING")}


def prompt(protocol, item, variant):
    sentence = protocol["sentence_line"].format_map(item) if variant == "full" else ""
    return protocol["instruction"] + "\n" + sentence + protocol["options"].format_map(item)


def generate(model, tokenizer, texts, protocol, torch):
    chat = [[{"role": "user", "content": content}] for content in texts]
    inputs = tokenizer.apply_chat_template(chat, add_generation_prompt=True, tokenize=False)
    tokens = tokenizer(inputs, padding=True, add_special_tokens=False, return_tensors="pt").to("cuda")
    with torch.inference_mode():
        output = model.generate(**tokens, do_sample=False, max_new_tokens=protocol["max_new_tokens"],
                                pad_token_id=tokenizer.pad_token_id)
    return tokenizer.batch_decode(output[:, tokens["input_ids"].shape[1]:], skip_special_tokens=True)


def stop(signum, _frame):
    raise InterruptedError(f"Received signal {signum}")


def write_progress(receipt, public, db, expected):
    row_count, dispatch, active = db.execute(
        "SELECT count(*), coalesce(sum(batch_seconds / batch_size), 0), "
        "count(DISTINCT model || ':' || item_id) FROM answers"
    ).fetchone()
    completed_items = db.execute(
        "SELECT count(*) FROM (SELECT item_id FROM answers GROUP BY item_id HAVING count(*) = ?)",
        (expected,),
    ).fetchone()[0]
    receipt.update(completed_items=completed_items, completed_answers=row_count,
                   model_items_with_any_answer=active, inference_seconds=dispatch,
                   answers_per_gpu_hour=round(row_count * 3600 / dispatch, 2) if dispatch else None)
    if receipt.get("started_at"):
        elapsed = (datetime.fromisoformat(receipt.get("finished_at", utc())) -
                   datetime.fromisoformat(receipt["started_at"])).total_seconds()
        receipt["wall_seconds_since_first_start"] = round(elapsed, 3)
        receipt["complete_items_per_wall_hour"] = round(completed_items * 3600 / elapsed, 2) if elapsed else None
    save(public, receipt)


def inference(args, protocol, panel, items, db, receipt):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, __version__ as transformers_version

    torch.set_num_threads(2)
    gpu = protocol["gpu"]
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("Expected exactly one visible CUDA GPU")
    receipt.update(torch=torch.__version__, transformers=transformers_version)
    predicted = {(m, i, v) for m, i, v in db.execute("SELECT model,item_id,variant FROM answers")}
    expected = len(protocol["models"]) * 2
    for name, revision in protocol["models"].items():
        pending = [(pair, key, variant) for pair, keys in panel.items() for key in keys
                   for variant in ("full", "omitted") if (name, key, variant) not in predicted]
        if not pending:
            continue
        snapshot = args.runtime / "weights" / revision
        tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
        tokenizer.padding_side = "left"
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            snapshot, local_files_only=True, trust_remote_code=False, use_safetensors=True,
            torch_dtype=torch.float16, attn_implementation="eager",
        ).to("cuda").eval()
        for start in range(0, len(pending), protocol["batch_size"]):
            gpu_sample = gpu_state(gpu)
            batch = pending[start:start + protocol["batch_size"]]
            texts = [prompt(protocol, items[key], variant) for _, key, variant in batch]
            dispatched = utc()
            before = time.monotonic()
            outputs = generate(model, tokenizer, texts, protocol, torch)
            seconds = time.monotonic() - before
            assert len(outputs) == len(batch)
            rows = []
            for (pair, key, variant), output in zip(batch, outputs):
                item = items[key]
                answer = output.strip().upper()
                if not re.fullmatch(protocol["answer_pattern"], answer):
                    answer = None
                official = "AB"[int(item["answer"]) - 1]
                rows.append((name, revision, item["qid"], key, pair, variant, official, output, answer,
                             dispatched, seconds, len(batch), gpu_sample["free_mib"],
                             gpu_sample["utilization_percent"]))
            with db:
                db.executemany("INSERT INTO answers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            write_progress(receipt, args.receipt, db, expected)
        del model
        torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime", type=Path)
    parser.add_argument("run_id")
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--split", default="pilot", choices=("pilot", "heldout"))
    args = parser.parse_args()

    os.umask(0o077)
    protocol_file = ROOT / "pilot.json"
    frozen = ROOT / "frozen-items.json"
    protocol = json.loads(protocol_file.read_text())
    gpu = protocol["gpu"]
    archive = args.runtime / "raw" / "winogrande_1.1.zip"
    if sha256(archive) != protocol["dataset_sha256"]:
        raise RuntimeError("WinoGrande source archive hash mismatch")
    panel = json.loads(frozen.read_text())[args.split]
    items, _ = source_items(archive, protocol)

    # Wait outside the lease while dependencies and data files are staged.
    deadline = time.monotonic() + 60 * 60
    asset_names = protocol["snapshot_files"]
    weight_files = [args.runtime / "weights" / rev / name
                    for rev in protocol["models"].values() for name in asset_names]
    while not (all(path.is_file() for path in weight_files)
               and (args.runtime / "packages.ready").is_file()):
        if time.monotonic() > deadline:
            raise RuntimeError("Weights or dependencies were unavailable after one hour")
        time.sleep(5)

    out = args.runtime / "runs" / args.run_id
    out.mkdir(exist_ok=True, parents=True)
    expected = len(protocol["models"]) * 2
    identity = {
        "run_id": args.run_id, "split": args.split, "models": protocol["models"],
        "gpu": gpu, "expected_items": 2 * len(panel), "expected_answers": 2 * len(panel) * expected,
        "protocol_sha256": sha256(protocol_file), "item_manifest_sha256": sha256(frozen),
        "assets_sha256": {str(path.relative_to(args.runtime)): sha256(path) for path in weight_files},
        "boinc_reservation": "none; coexist with executing tasks",
    }
    lock = Path(os.environ["XDG_RUNTIME_DIR"]) / (gpu["uuid"] + ".lock")
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu["uuid"]
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    signal.signal(signal.SIGTERM, stop)

    with lock.open("a") as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        early_gpu = gpu_state(gpu)
        if early_gpu["free_mib"] < gpu["min_free_mib"]:
            raise RuntimeError(f"Insufficient shared GPU memory: {early_gpu}")
        before = boinc_state(gpu)
        receipt = identity.copy()
        if args.receipt.exists():
            previous = json.loads(args.receipt.read_text())
            if any(previous.get(key) != value for key, value in identity.items()):
                raise RuntimeError("Existing receipt does not match the requested run")
            receipt = previous
        receipt.update(status="running", boinc_before=before, gpu_before=early_gpu)
        receipt.pop("finished_at", None)
        receipt.pop("error", None)
        receipt.setdefault("started_at", utc())
        receipt["last_attempt_started_at"] = utc()
        with sqlite3.connect(out / "items.sqlite") as db:
            db.execute("""CREATE TABLE IF NOT EXISTS answers (
                model TEXT, revision TEXT, qid TEXT, item_id TEXT, pair_id TEXT, variant TEXT,
                official TEXT, raw_output TEXT, prediction TEXT, dispatched_at TEXT,
                batch_seconds REAL, batch_size INTEGER, free_mib INTEGER, utilization_percent INTEGER,
                PRIMARY KEY (model, item_id, variant)
            )""")
            write_progress(receipt, args.receipt, db, expected)
            print(f"{args.run_id} started {receipt['last_attempt_started_at']}", flush=True)
            try:
                inference(args, protocol, panel, items, db, receipt)
                receipt["status"] = "complete"
            except BaseException as error:
                receipt.update(status="interrupted", error=f"{type(error).__name__}: {error}")
                raise
            finally:
                receipt["finished_at"] = utc()
                try:
                    receipt["boinc_after"] = boinc_state(gpu)
                    receipt["gpu_after"] = gpu_state(gpu)
                finally:
                    write_progress(receipt, args.receipt, db, expected)


if __name__ == "__main__":
    main()
