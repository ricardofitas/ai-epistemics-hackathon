"""Replay the original published GPT-3/PromptPG outputs without generating answers."""
import ast
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
from types import SimpleNamespace
import unicodedata
import urllib.request

HERE = Path(__file__).resolve().parent


def download(item, revision):
    path, expected = item
    url = f"https://raw.githubusercontent.com/lupantech/PromptPG/{revision}/{path}"
    with urllib.request.urlopen(url, timeout=90) as response:
        data = response.read()
    actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if actual != expected:
        raise ValueError(f"Source verification failed for {path}")
    return path, data


def norm(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


class RandomAudit:
    def __init__(self):
        self.calls = 0
        self.rng = random.Random(123)

    def choice(self, choices):
        self.calls += 1
        return self.rng.choice(choices)


def load_functions(source, namespace):
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<pinned author functions>", "exec"), namespace)


def functions(inputs, rl):
    prefix = "run_gpt3_rl" if rl else "run_gpt3"
    rng = RandomAudit()
    ns = dict(re=re, random=rng, np=SimpleNamespace(argmax=lambda values: values.index(max(values))))
    load_functions(inputs[prefix + "/utilities.py"].decode(), ns)
    if not rl:
        tree = ast.parse(inputs[prefix + "/run_gpt3.py"].decode())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "normalize_answer")
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<pinned normalizer>", "exec"), ns)
    return ns, rng


def final_numeric(raw, unit):
    # A full, explicit declaration with a numeric value and only a known unit after it.
    number = r"[-+]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)(?:/[-+]?\d+(?:\.\d+)?)?"
    matches = list(re.finditer(r"(?i)\b(?:final\s+)?answer\s+is\s*(?:[:=]\s*)?(\$?" + number + r")", raw))
    if not matches:
        return None
    match = matches[-1]
    tail = raw[match.end():].strip()
    permitted = re.sub(r"[\s.!$]+$", "", unit or "").strip().casefold()
    tail = re.sub(r"[\s.!]+$", "", tail).strip().casefold()
    if tail not in {"", permitted}:
        return None
    return match[1]


def audit(path, data, source, inputs):
    rows = data["results"]
    assert rows.keys() == source.keys()
    ns, rng = functions(inputs, "/gpt3_rl/" in path)
    normal = ns["normalize_answer"]
    original_similarity = ns["score_string_similarity"]
    stats = Counter()
    per_item = {}
    witnesses = []
    for pid, row in rows.items():
        item = source[pid]
        assert item["answer"] == row["answer"]
        opts, unit, gold = item["choices"], item["unit"], item["answer"]
        def correct(prediction):
            return normal(prediction, unit).lower() == normal(gold, unit).lower()
        stored = row["true_false"]
        assert isinstance(stored, bool)
        replayed_grade = correct(row["prediction"])
        stats["normalizer_flag_mismatches"] += stored != replayed_grade
        stats["stored_correct"] += stored
        logged = []
        def tracking_similarity(a, b):
            score = original_similarity(a, b)
            logged.append((a, b, score))
            return score
        ns["score_string_similarity"] = tracking_similarity
        before = rng.calls
        recovered = ns["extract_prediction"](row["output"], opts, data["args"]["option_inds"])
        random_fallback = rng.calls > before
        stats["random_option_fallbacks"] += random_fallback
        stats["parser_prediction_mismatches"] += recovered != row["prediction"]
        stats["nonrandom_parser_mismatches"] += recovered != row["prediction"] and not random_fallback
        native_zero = bool(logged) and max(x[2] for x in logged) == 0
        stats["choice_rows"] += bool(opts)
        stats["zero_fallback_rows"] += native_zero
        changed = dict(original=stored)
        casefold = row["prediction"]
        if logged:
            transformed = logged[0][1]
            scores = [original_similarity(opt.casefold(), transformed.casefold()) for opt in opts]
            casefold = opts[scores.index(max(scores))]
        changed["casefold_lexical"] = correct(casefold)
        explicit = [option for option in (opts or []) if norm(option) == norm(row["output"])]
        exact_pred = explicit[0] if len(explicit) == 1 else row["prediction"]
        changed["explicit_whole_option"] = correct(exact_pred)
        changed["explicit_then_zero_abstain"] = correct(exact_pred) if len(explicit) == 1 or not native_zero else False
        candidate = final_numeric(row["output"], unit) if not opts else None
        changed["last_declared_numeric"] = correct(candidate) if candidate is not None else stored
        changed["casefold_and_declared_numeric"] = correct(casefold) if opts else changed["last_declared_numeric"]
        for policy, value in changed.items():
            stats[policy + "_correct"] += value
        per_item[pid] = changed
        if any(value != stored for value in changed.values()) or (recovered != row["prediction"] and not random_fallback):
            witnesses.append(dict(archive=path, id=pid, raw=row["output"], source_answer=gold, choices=opts,
                original_prediction=row["prediction"], replayed_prediction=recovered, native_zero_fallback=native_zero,
                casefold_prediction=casefold, declared_numeric=candidate, policy_correctness=changed))
    assert len(rows) == data["count"]
    assert stats["original_correct"] == data["correct"]
    assert abs(data["acc"] - 100 * data["correct"] / data["count"]) < 1e-8
    args = {k: data["args"].get(k) for k in ("seed", "shot_number", "prompt_format", "engine", "temperature", "test_split")}
    return dict(count=len(rows), stored_accuracy=data["acc"], args=args, counts=dict(stats)), per_item, witnesses


def main():
    manifest = json.loads((HERE / "sources.json").read_bytes())
    with ThreadPoolExecutor(4) as pool:
        inputs = dict(pool.map(lambda item: download(item, manifest["source_rev"]), manifest["blobs"].items()))
    source = json.loads(inputs["data/tabmwp/problems_test.json"])
    results, labels, witnesses = {}, {}, []
    for path, raw in sorted(inputs.items()):
        if not path.startswith("results/"):
            continue
        results[path], labels[path], evidence = audit(path, json.loads(raw), source, inputs)
        witnesses.extend(evidence)
    baseline = "results/gpt3/exp4_test_TQ-SA_2_seed_2.json"
    proposed = "results/gpt3_rl/exp1_test_TQ-SA_2_seed_2.json"
    n = len(source)
    policies = list(next(iter(labels[baseline].values())))
    contrasts = {}
    for policy in policies:
        differences = [int(labels[proposed][pid][policy]) - int(labels[baseline][pid][policy]) for pid in source]
        contrasts[policy] = dict(net_correct=sum(differences), gain_pp=100 * sum(differences) / n,
                                proposed_only=sum(x == 1 for x in differences), baseline_only=sum(x == -1 for x in differences))
    out = dict(source_revision=manifest["source_rev"], source_questions=n, files=results,
               seed2_matched_comparison=contrasts, new_model_calls=0, scope="Released files only; inspect actual seed coverage before comparison to a paper mean.")
    (HERE / "summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    (HERE / "changed_items.jsonl").write_text("".join(json.dumps(w, ensure_ascii=False) + "\n" for w in witnesses))
    print("NATURAL_AUDIT " + json.dumps(out, separators=(",", ":")))


if __name__ == "__main__":
    main()
