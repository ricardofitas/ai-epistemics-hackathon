#!/usr/bin/env python3
"""Prepare a source-only, output-blind HANS external evaluation slice."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SEED = "hans-broad-20261113-v1"
SOURCE_SHA = "c55b62feef9913070e88f38938dc2492018c945ac81f70139346472494124e79"
OLD_SHA = "08306c3d01da9fa2ddec4ff06532efbe2dc592bee5c7e4e3c8191be658868442"
COMMIT = "7299f6f657089ce06a0f98e7e81f8d0f5b7741ce"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pair(row):
    return (row["sentence1"], row["sentence2"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True,
                    help="Exact official heuristics_evaluation_set.txt at pinned commit")
    ap.add_argument("--output-dir", type=Path, default=HERE,
                    help="Output directory; defaults to this script's directory")
    args = ap.parse_args()
    source_bytes = args.source.read_bytes()
    if sha(source_bytes) != SOURCE_SHA:
        raise ValueError("HANS source SHA mismatch")
    old_path = PARENT / "hans_target" / "selected_data.json"
    if sha(old_path.read_bytes()) != OLD_SHA:
        raise ValueError("HANS80 source SHA mismatch")
    old = json.loads(old_path.read_text())["items"]
    old_ids = {x["source_pair_id"] for x in old}
    old_pairs = {(x["premise"], x["hypothesis"]) for x in old}
    with args.source.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 30000 or len({r["pairID"] for r in rows}) != 30000:
        raise ValueError("Unexpected HANS source row count or duplicate pairID")
    if not all(rows[x["source_row_index_zero_based"]]["pairID"] == x["source_pair_id"]
               and pair(rows[x["source_row_index_zero_based"]]) ==
               (x["premise"], x["hypothesis"]) for x in old):
        raise ValueError("HANS80 does not derive from pinned source")
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[(row["heuristic"], row["gold_label"], row["subcase"])].append((i, row))
    if len(groups) != 30 or any(len(v) != 1000 for v in groups.values()):
        raise ValueError("Unexpected HANS grouping")
    seen = set(old_pairs)
    selected = []
    for stratum in sorted(groups):
        ranked = sorted(groups[stratum], key=lambda ir: (
            sha((SEED + "|" + ir[1]["pairID"]).encode()), ir[1]["pairID"]))
        count = 0
        for i, row in ranked:
            if row["pairID"] in old_ids or pair(row) in seen:
                continue
            selected.append((i, row))
            seen.add(pair(row))
            count += 1
            if count == 20:
                break
        if count != 20:
            raise ValueError("Too few disjoint unique source pairs: " + str(stratum))
    selected.sort(key=lambda ir: (ir[1]["heuristic"], ir[1]["gold_label"],
                                  ir[1]["subcase"], ir[1]["pairID"]))
    items = []
    key = []
    for j, (i, row) in enumerate(selected, 1):
        task_id = f"B{j:03d}"
        items.append({"task_id": task_id, "source_row_index_zero_based": i,
                      "source_pair_id": row["pairID"], "premise": row["sentence1"],
                      "hypothesis": row["sentence2"], "gold_binary": row["gold_label"],
                      "heuristic": row["heuristic"], "subcase": row["subcase"],
                      "template": row["template"]})
        key.append({"task_id": task_id, "source_pair_id": row["pairID"]})
    assert len(items) == len(key) == 600
    assert len({x["source_pair_id"] for x in items}) == 600
    assert len({(x["premise"], x["hypothesis"]) for x in items}) == 600
    assert not {x["source_pair_id"] for x in items} & old_ids
    assert not {(x["premise"], x["hypothesis"]) for x in items} & old_pairs
    assert Counter((x["heuristic"], x["gold_binary"]) for x in items) == {
        (h, g): 100 for h in ("lexical_overlap", "subsequence", "constituent")
        for g in ("entailment", "non-entailment")}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path, obj in ((args.output_dir / "selected_data.json", {"items": items,
                   "official_three_way_gold": False}),
                      (args.output_dir / "task_key.json", {"rows": key})):
        if path.exists():
            raise FileExistsError(path)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"count": len(items), "subcases": len({x["subcase"] for x in items}),
                      "templates": len({x["template"] for x in items}),
                      "heuristic_label": Counter((x["heuristic"], x["gold_binary"])
                      for x in items).__str__(),
                      "selected_sha256": sha((args.output_dir / "selected_data.json").read_bytes()),
                      "key_sha256": sha((args.output_dir / "task_key.json").read_bytes())}))


if __name__ == "__main__":
    main()
