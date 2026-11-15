"""Replay the ScienceQA archives using Python 3's standard library only.

python audit_science.py --fetch --data inputs --out results
"""
import argparse
import csv
import hashlib
import json
import random
import re
import urllib.request
from collections import Counter
from decimal import Decimal
from pathlib import Path


SCI = "2cbf8318e07b9ece895bb2ae605e71e38d623264"
LL = "c121f0432da27facab705978f83c4ada465e46fd"
MM = "ac238a5c329b7132229ad5068e7a3f7a1de01ac9"
SOURCES = {
    "problems.json": ("lupantech/ScienceQA", SCI, "data/scienceqa/problems.json"),
    "splits.json": ("lupantech/ScienceQA", SCI, "data/scienceqa/pid_splits.json"),
    "gpt.json": ("lupantech/ScienceQA", SCI, "results/gpt3/final_test_QCM-ALE_2_seed_3.json"),
    "sqa_readme.md": ("lupantech/ScienceQA", SCI, "README.md"),
    "llava_v0.json": ("haotian-liu/LLaVA", LL, "llava/eval/table/results/test_sqa_llava_13b_v0.json"),
    "llava_v13.json": ("haotian-liu/LLaVA", LL, "llava/eval/table/results/test_sqa_llava_lcs_558k_sqa_12e_vicuna_v1_3_13b.json"),
    "mm_panel.jsonl": ("declare-lab/MM-InstructEval", MM, "multimodal_data/QA/ScienceQA/test.json"),
    "mm_scores.csv": ("declare-lab/MM-InstructEval", MM, "docs/best_performance.csv"),
}
LETTERS = "ABCDE"
NATIVE = re.compile(r"The answer is ([A-Z]).")
LEADING = re.compile(r"^The answer is ([A-E])\.\s*BECAUSE:")
ALIASES = {"llama-adapter-v2": "llama-adapterv2", "multigpt": "multimodal-gpt",
           "llava-13b": "llava-v0-13b", "llava-7b": "llava-v0-7b"}


def get_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def put_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def download(data):
    for filename, (repo, rev, path) in SOURCES.items():
        address = f"https://raw.githubusercontent.com/{repo}/{rev}/{path}"
        with urllib.request.urlopen(address, timeout=90) as response:
            (data / filename).write_bytes(response.read())
    raw = (data / "problems.json").read_bytes()
    assert hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() == "3920b762556abfbfa001f298c9740c36d4e041e1"
    problems = json.loads(raw)
    ids = get_json(data / "splits.json")["test"]
    put_json(data / "test_ids.json", ids)
    put_json(data / "gold_mirror.json", {i: [problems[i]["answer"], len(problems[i]["choices"])] for i in ids})
    put_json(data / "image_mirror.json", {i: bool(problems[i]["image"]) for i in ids})
    mm = [json.loads(line) for line in (data / "mm_panel.jsonl").read_text().splitlines() if line.strip()]
    put_json(data / "mm_ids.json", [[r["index"], r["answer_index"]] for r in mm])


def csv_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def audit_model(name, obj, ids, gold, images):
    assert len(ids) == len(set(ids)) == 4241 and set(obj["results"]) == set(obj["outputs"]) == set(ids)
    counts = Counter()
    records = []
    for qid in ids:
        key, nchoices = gold[qid]
        output = obj["outputs"][qid]
        saved = obj["results"][qid]
        valid = LETTERS[:nchoices]
        hits = NATIVE.findall(output)
        native = hits[0] if len(hits) == 1 else ""
        if name.startswith("llava"):
            if output in LETTERS and len(output) == 1:
                native = output
            elif len(output) >= 3 and output[0] in LETTERS and output[1:3] == ". ":
                native = output[0]
        parsed = valid.find(native) if native else -1
        blank = not output.strip()
        archived_right = int(saved == key)
        accepted = parsed == key
        original_failure = parsed < 0
        lead = LEADING.match(output)
        repair = parsed
        if name == "gpt" and original_failure and lead and lead[1] in valid:
            repair = valid.index(lead[1])
        counts.update({"n": 1, "saved_right": archived_right, "blank": blank,
                       "blank_credits": blank and archived_right, "native_failed": original_failure,
                       "unexpected_valid_parse": not original_failure and parsed != saved,
                       "failed_native_credits": original_failure and archived_right,
                       "native_parse_only_right": int(accepted), "explicit_right": int(repair == key),
                       "nonblank_failed": original_failure and not blank})
        records.append({"id": qid, "gold_index": key, "choice_count": nchoices, "image_panel": int(images[qid]),
                        "saved_index": saved, "native_parse": parsed, "blank": int(blank), "saved_correct": archived_right,
                        "blank_zero_correct": int(not blank and archived_right), "explicit_correct": int(repair == key)})
    counts["file_header_right"] = obj["correct"]
    counts["native_minus_blank_right"] = counts["saved_right"] - counts["blank_credits"]
    counts["finite_low"] = counts["native_parse_only_right"]
    counts["finite_high"] = counts["native_parse_only_right"] + counts["nonblank_failed"]
    return dict(counts), records


def compatible_counts(value, n):
    candidates = [i for i in range(n + 1) if abs(Decimal(100*i)/n - value) <= Decimal("0.005")]
    return candidates


def sign(a, b):
    return int(a > b) - int(a < b)


def audit(data, out):
    ids = get_json(data / "test_ids.json")
    gold = get_json(data / "gold_mirror.json")
    images = get_json(data / "image_mirror.json")
    mm = get_json(data / "mm_ids.json")
    common = {str(i) for i, _ in mm}
    assert len(mm) == len(common) == 2017 and common == {i for i in ids if images[i]}
    assert all(gold[str(i)][0] == answer for i, answer in mm)
    source_gold = data / "science_gold.json"
    if source_gold.exists():
        official = get_json(source_gold)
        assert set(official) == set(ids)
        assert all(gold[i] == official[i][:2] and images[i] == official[i][5] for i in ids)
    results = {}
    rows = {}
    for name in ("gpt", "llava_v0", "llava_v13"):
        results[name], rows[name] = audit_model(name, get_json(data / f"{name}.json"), ids, gold, images)
        csv_rows(out / f"{name}_records.csv", rows[name])
    g = results["gpt"]
    assert g["saved_right"] == g["file_header_right"] and g["unexpected_valid_parse"] == 0
    reference_run = get_json(data / "gpt.json")
    rng = random.Random(reference_run["args"]["seed"])
    assert reference_run["args"]["shot_qids"] is None
    positions = rng.sample(range(12726), reference_run["args"]["shot_number"])
    failed = [r for r in rows["gpt"] if r["native_parse"] == -1]
    results["uninterrupted_rng_check"] = {"training_positions": positions, "fallback_rows": len(failed),
        "saved_indices_matched": sum(rng.randrange(r["choice_count"]) == r["saved_index"] for r in failed)}
    q = [r for r in rows["gpt"] if r["image_panel"]]
    native_image = sum(r["saved_correct"] for r in q)
    blankzero_image = sum(r["blank_zero_correct"] for r in q)
    full_pct = Decimal(100 * g["saved_right"]) / len(ids)
    mm_scores = {}
    with (data / "mm_scores.csv").open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            model = re.match(r"\[([^\]]+)\]", r["Model"])[1].lower().removesuffix("-hf")
            mm_scores[model] = Decimal(r["ScienceQA"])
    pairs = []
    for line in (data / "sqa_readme.md").read_text().splitlines():
        if not line.startswith("|") or "arxiv.org/abs/2310.09036" not in line:
            continue
        cells = [c.strip().replace("**", "") for c in line.strip("|").split("|")]
        model, displayed = cells[1], Decimal(cells[-1])
        assert displayed == mm_scores[ALIASES.get(model.lower(), model.lower())]
        counts = compatible_counts(displayed, len(common))
        correct = counts[0] if len(counts) == 1 else None
        published_image_pct = (Decimal(native_image * 100) / len(common)).quantize(Decimal("0.01"))
        blankzero_image_pct = (Decimal(blankzero_image * 100) / len(common)).quantize(Decimal("0.01"))
        pairs.append({"published_comparator": model, "reported_pct": str(displayed), "implied_correct": correct,
                      "rank_GPT_as_listed": sign(full_pct, displayed), "rank_GPT_same_ids": sign(published_image_pct, displayed),
                      "rank_GPT_same_ids_GPT_blank_zero": sign(blankzero_image_pct, displayed)})
    assert len(pairs) == 20
    csv_rows(out / "leaderboard_comparisons.csv", pairs)
    results["image_panel"] = {"n": len(q), "native_right": native_image, "blank_zero_right": blankzero_image,
                              "blank": sum(r["blank"] for r in q), "matched_reference_labels": len(mm)}
    results["published_source_block"] = {"n": len(pairs),
          "strict_reversals_same_ids": [r["published_comparator"] for r in pairs if r["rank_GPT_as_listed"] * r["rank_GPT_same_ids"] < 0],
          "new_ties": [r["published_comparator"] for r in pairs if r["rank_GPT_as_listed"] and not r["rank_GPT_same_ids"]]}
    direct, = compatible_counts(Decimal("73.97"), len(ids))
    results["original_CoT_contrast"] = {"published_direct_implied_right": direct,
                                        "published_CoT_lead": g["saved_right"] - direct,
                                        "direct_blank_credits_for_tie": direct - g["native_minus_blank_right"]}
    put_json(out / "summary.json", results)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="fetch version-pinned public sources")
    parser.add_argument("--data", type=Path, default=Path("inputs"))
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.data.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.fetch:
        download(args.data)
    print(json.dumps(audit(args.data, args.out), indent=2))
