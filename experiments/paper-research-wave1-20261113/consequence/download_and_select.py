#!/usr/bin/env python3
"""Download byte-pinned public PAWS/HANS data and reproduce a small frozen sample.
No model calls. Requires pyarrow for the HF parquet mirror; --pyarrow-path is an
optional existing dependency directory. The canonical GCS PAWS URL returned403;
this design uses the stated immutable HF mirror, not unverified tar byte identity.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import random
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
SEED = 2026111311
SOURCES = {
    "paws": {
        "url": "https://huggingface.co/datasets/google-research-datasets/paws/resolve/161ece9501cf0a11f3e48bd356eaa82de46d6a09/labeled_final/test-00000-of-00001.parquet",
        "file": "paws_test.parquet",
        "sha256": "ae342ff12bb84b84b95f468abf5db6cb7c7bd578271299fe9c99be75b8132f4d",
        "max_bytes": 5_000_000,
    },
    "hans": {
        "url": "https://raw.githubusercontent.com/tommccoy1/hans/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/heuristics_evaluation_set.txt",
        "file": "hans.tsv",
        "sha256": "c55b62feef9913070e88f38938dc2492018c945ac81f70139346472494124e79",
        "max_bytes": 20_000_000,
    },
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def download(spec):
    source = ROOT / "source" / spec["file"]
    source.parent.mkdir(exist_ok=True)
    if source.exists():
        raw = source.read_bytes()
    else:
        with urllib.request.urlopen(spec["url"], timeout=90) as response:
            raw = response.read(spec["max_bytes"] + 1)
        if len(raw) > spec["max_bytes"]:
            raise ValueError("Source exceeds declared download cap")
        if digest(raw) != spec["sha256"]:
            raise ValueError("Pinned source bytes changed")
        source.write_bytes(raw)
    if digest(raw) != spec["sha256"]:
        raise ValueError(f"Changed cached source: {source}")
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyarrow-path", type=Path)
    args = parser.parse_args()
    paths = {name: download(spec) for name, spec in SOURCES.items()}
    if args.pyarrow_path:
        sys.path.insert(0, str(args.pyarrow_path))
    import pyarrow.parquet as pq
    paws = pq.read_table(paths["paws"]).to_pylist()
    hans = list(csv.DictReader(io.StringIO(paths["hans"].read_text()), delimiter="\t"))
    assert len(paws) == 8000 and len(hans) == 30000
    rng = random.Random(SEED)
    selected = []
    eligible = {}
    for label in [0, 1]:
        pool = [(i, row) for i, row in enumerate(paws) if row["label"] == label]
        eligible[f"paws_label_{label}"] = len(pool)
        for i, row in rng.sample(pool, 10):
            assert row["sentence1"] and row["sentence2"]
            selected.append({"item_id": f"P-{len(selected)+1:02d}", "suite": "paws",
                             "source_row_index_zero_based": i, "source_id": row["id"],
                             "sentence1": row["sentence1"], "sentence2": row["sentence2"],
                             "gold_label": int(label), "analysis_role": "proxy_selection"})
    for subcase, label in [("ln_subject/object_swap", "non-entailment"), ("le_passive", "entailment")]:
        pool = [(i, row) for i, row in enumerate(hans) if row["subcase"] == subcase and row["gold_label"] == label]
        eligible[f"hans_{subcase}_{label}"] = len(pool)
        assert len(pool) == 1000
        sample = rng.sample(pool, 10)
        rng.shuffle(sample)
        for j, (i, row) in enumerate(sample):
            selected.append({"item_id": f"H-{sum(x['suite']=='hans' for x in selected)+1:02d}",
                             "suite": "hans", "source_row_index_zero_based": i,
                             "source_id": row["pairID"], "sentence1": row["sentence1"],
                             "sentence2": row["sentence2"], "gold_label": label,
                             "subcase": subcase, "template": row["template"],
                             "analysis_role": "target_selection" if j < 5 else "target_confirmation"})
    assert len(selected) == 40
    assert len({(x["suite"], str(x["source_id"])) for x in selected}) == 40
    data = {"selection_seed": SEED, "selection_intent_file": "selection_intent.json",
            "items": selected, "status": "prepared_before_any_model_performance",
            "annotation_caveat": "Original dataset labels retained without manual relabeling. No model-prediction-based filtering; no assertion of perfect labels or training exclusion."}
    write_json(ROOT / "selected_data.json", data)
    selection = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                 "seed": SEED, "generator": "Python random.Random(seed).sample over original source order; paws0,paws1,hansswap,hanspassive; per-HANS-stratum shuffle then first5selection,last5confirmation",
                 "eligible_counts": eligible, "sample_counts": {"paws":20,"hans":20},
                 "paws_balance": {"0":10,"1":10},
                 "hans_split": {"target_selection":{"entailment":5,"non-entailment":5},
                                "target_confirmation":{"entailment":5,"non-entailment":5}},
                 "strata_pairing": "Two independently sampled HANS strata; not matched sentence pairs.",
                 "item_selection": [{k:x[k] for k in ["item_id","suite","source_id","source_row_index_zero_based","gold_label","analysis_role"]} for x in selected],
                 "source_specifications": SOURCES,
                 "selected_data_sha256": digest((ROOT / "selected_data.json").read_bytes()),
                 "no_outcome_selection": True, "model_calls_made": 0}
    write_json(ROOT / "selection_manifest.json", selection)
    # Golds, suite names and source metadata are omitted from model-facing items.
    tasks = []
    for item in selected:
        directions = [("forward", item["sentence1"], item["sentence2"])]
        if item["suite"] == "paws":
            directions.append(("reverse", item["sentence2"], item["sentence1"]))
        for direction, premise, hypothesis in directions:
            tasks.append({"item_id": item["item_id"], "direction": direction,
                          "premise": premise, "hypothesis": hypothesis})
    random.Random(2026111312).shuffle(tasks)
    for i, task in enumerate(tasks, 1):
        task["id"] = f"Q{i:03d}"
    write_json(ROOT / "task_key.json", [{k:t[k] for k in ["id","item_id","direction"]} for t in tasks])
    # Keep all selected rows and opaque QIDs, but isolate model contexts by
    # analysis role. No confirmation input may share a request with selection
    # or proxy inputs. Preserve relative shuffled task order within each role.
    item_roles = {x["item_id"]: x["analysis_role"] for x in selected}
    batches = []
    for role in ["proxy_selection", "target_selection", "target_confirmation"]:
        role_tasks = [t for t in tasks if item_roles[t["item_id"]] == role]
        assert len(role_tasks) % 5 == 0
        for j in range(0, len(role_tasks), 5):
            batches.append((role, [{k:t[k] for k in ["id","premise","hypothesis"]}
                                   for t in role_tasks[j:j+5]]))
    assert len(batches) == 12
    instructions = ("Classify each ordered premise/hypothesis pair. Use entailment when the hypothesis must be true if the premise is true; contradiction when it must be false; neutral otherwise. Use only the given premise, not outside factual knowledge. Return exactly one JSON object with a predictions array, one entry per supplied id, each entry containing only id and label. Valid labels are entailment, contradiction, neutral. Do not include explanations, probabilities or additional text.")
    requests = []
    for model in ["gemma-4-31b-it", "qwen3.8-27b"]:
        for j, (role, batch) in enumerate(batches, 1):
            requests.append({"trial_id": f"DC-{len(requests)+1:02d}", "requested_model": model,
                             "batch_index": j, "batch_role": role,
                             "task_ids": [x["id"] for x in batch],
                             "request_payload": {"model":model,"instructions":instructions,
                                 "input":json.dumps(batch,ensure_ascii=False),"max_output_tokens":8192,
                                 "temperature":0.0,"stream":True,"tools":[],"tool_choice":"none",
                                 "agentic_memory":False,"store":False}})
    random.Random(2026111314).shuffle(requests)
    for i, row in enumerate(requests, 1):
        row["execution_order"] = i
    (ROOT / "manifest.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in requests))
    print(json.dumps({"selected_items":40,"ordered_inputs_per_model":len(tasks),"client_requests":len(requests),
                      "paws_pairs":20,"hans_selection_items":10,"hans_confirmation_items":10,
                      "selected_data_sha256":selection["selected_data_sha256"]}))


if __name__ == "__main__":
    main()
