"""Score the two archived Pythia panels and a disjoint model-selection split."""
import argparse
import csv
import hashlib
import json
import math
import io
import urllib.parse
import urllib.request
from pathlib import Path

MODELS = ["pythia-160m", "pythia-12b"]


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def load_model(data, model):
    rows = json.loads((data / f"EleutherAI__{model}.json").read_text())
    items = {}
    for r in rows:
        source = {k: r[k] for k in ("sentence", "option1", "option2", "answer")}
        source["answer"] = str(source["answer"])
        key = digest(source)
        group = digest(sorted([r["option1"].strip().casefold(), r["option2"].strip().casefold()]))
        scores = r["predictions"]
        assert len(scores) == 2 and all(math.isfinite(v) for v in scores)
        pred = 1 if scores[0] >= scores[1] else 2
        answer = int(r["answer"])
        assert (pred == answer) == bool(r["acc"]) and r["num_asked_few_shots"] == 5
        assert key not in items
        items[key] = (group, answer, pred, scores[0] == scores[1])
    assert len(items) == 1267
    return items


def download(data, manifest):
    import pyarrow.parquet as pq

    for model in MODELS:
        entry = manifest["archives"]["EleutherAI/" + model]
        rows = []
        for source in entry["files"]:
            address = ("https://huggingface.co/datasets/" + entry["dataset"] + "/resolve/" +
                       entry["commit"] + "/" + urllib.parse.quote(source["path"]))
            with urllib.request.urlopen(address, timeout=90) as response:
                raw = response.read()
            assert hashlib.sha256(raw).hexdigest() == source["sha256"]
            rows.extend(pq.read_table(io.BytesIO(raw)).to_pylist())
        assert len(rows) == entry["rows"]
        (data / f"EleutherAI__{model}.json").write_text(json.dumps(rows))


def scores(rows):
    out = {"n": len(rows)}
    for model in MODELS:
        out[model] = {"official_correct": sum(r[model] == r["gold"] for r in rows),
                      "constant_B_correct": sum(r[model] == 2 for r in rows)}
    return out


def choose(result, score):
    a, b = (result[m][score] for m in MODELS)
    return MODELS[0] if a > b else MODELS[1] if b > a else "tie"


def run(data, out, exclusions):
    small, large = [load_model(data, m) for m in MODELS]
    assert set(small) == set(large) and set(exclusions) <= set(small)
    excluded_groups = {small[i][0] for i in exclusions}
    rows = []
    for key, (group, gold, pred, tie) in sorted(small.items()):
        assert (group, gold) == large[key][:2]
        split = "excluded" if group in excluded_groups else ("selection" if int(group[:2],16) % 2 == 0 else "assessment")
        rows.append({"item_sha256": key, "group_sha256": group, "subset": split, "gold": gold,
                     MODELS[0]: pred, MODELS[1]: large[key][2], "tie_small": int(tie), "tie_large": int(large[key][3])})
    panels = {name: scores([r for r in rows if r["subset"] == name]) for name in ("excluded","selection","assessment")}
    panels["full"] = scores(rows)
    for result in panels.values():
        result["winner_official"] = choose(result,"official_correct")
        result["winner_constant_B"] = choose(result,"constant_B_correct")
    judges = panels["selection"]
    heldout = panels["assessment"]
    selected_correct = judges["winner_official"]
    selected_native = judges["winner_constant_B"]
    loss = None
    if "tie" not in (selected_correct, selected_native):
        loss = heldout[selected_correct]["official_correct"] - heldout[selected_native]["official_correct"]
    summary = {"panels": panels, "previous_hashes": len(exclusions), "excluded_option_groups": len(excluded_groups),
               "heldout_loss_of_constant_B_selection": loss, "scored": len(rows)}
    with (out / "wino_records.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out / "wino_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, default=Path("inputs"))
    p.add_argument("--out", type=Path, default=Path("results"))
    p.add_argument("--exclude", type=Path, default=Path("previous_wino_hashes.txt"))
    p.add_argument("--fetch", action="store_true", help="download hash-pinned original Parquet files (requires pyarrow)")
    p.add_argument("--source-manifest", type=Path, default=Path("wino_sources.json"))
    args = p.parse_args()
    args.data.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.fetch:
        download(args.data, json.loads(args.source_manifest.read_text()))
    print(json.dumps(run(args.data, args.out, set(args.exclude.read_text().splitlines())), indent=2))
