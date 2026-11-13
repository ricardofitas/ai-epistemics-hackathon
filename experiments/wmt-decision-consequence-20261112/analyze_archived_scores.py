#!/usr/bin/env python3
"""Compare every eligible fixed-pool pair, using pinned archived BLEU records."""
import itertools
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
POOL = json.loads((ROOT / "pool-prior-to-score-inspection.json").read_text())["models"]
SOURCES = json.loads((ROOT / "sources.json").read_text())
records = {r["path"]: r for r in SOURCES["evaluation_records"]}
expected_signature = "BLEU|nrefs:1|case:mixed|eff:no|tok:13a|smooth:exp|version:2.3.1"
rows, missing = [], []
for model in POOL:
    name = model.split("/")[-1]
    vals = {}
    for year in [2019, 2020]:
        path = ROOT / f"{name}_newstest{year}.eng-deu.eval"
        if not path.exists():
            continue
        source_path = f"models/huggingface/{model}/newstest{year}.eng-deu.eval"
        record = records[source_path]
        raw = path.read_bytes()
        blob_hash = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob_hash != record["blob_sha"] or raw.decode() != record["content"]:
            raise ValueError(f"Changed pinned primary score artifact: {path}")
        match = re.search(r"^(BLEU\|[^\n]*tok:13a[^\n]*?) = ([\d.]+) ", path.read_text(), re.M)
        if not match or match[1] != expected_signature:
            raise ValueError(f"Absent or inconsistent scoring signature: {path}")
        vals[str(year)] = float(match[2])
    if len(vals) == 2:
        rows.append({"model_identifier": model, "BLEU": vals})
    else:
        missing.append({"model_identifier": model, "reason": "No complete paired archived records; not replaced"})
pairs = []
for a, b in itertools.combinations(rows, 2):
    differences = {str(y): round(a["BLEU"][str(y)] - b["BLEU"][str(y)], 10) for y in [2019, 2020]}
    pairs.append({"first": a["model_identifier"], "second": b["model_identifier"],
                  "first_minus_second_BLEU": differences,
                  "strict_ranking_reversal": differences["2019"] * differences["2020"] < 0})
result = {"source_commit": SOURCES["evaluation_commit"], "metric_signature": expected_signature,
          "score_unit": "BLEU points on 0–100 scale",
          "eligible": rows, "missing": missing, "all_eligible_pairs": pairs,
          "strict_ranking_reversals": sum(x["strict_ranking_reversal"] for x in pairs),
          "winner_by_archived_score": {str(y): max(rows, key=lambda r: r["BLEU"][str(y)])["model_identifier"] for y in [2019, 2020]},
          "limitation": "Historical exact weight revisions and reference-byte identity are not established; these are paired model-ID archive records, not independently rerun fixed-checkpoint evaluations."}
(ROOT / "paired_results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
