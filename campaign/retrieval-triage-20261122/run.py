"""Frozen CPU BM25 retrieval-triage pilot and gated cross-domain transfer."""
import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

import numpy as np

ARCHIVE_MD5 = {"scifact": "5f7d1de60b170fc8027bb7898e2efca1",
               "arguana": "8ad3e3c2a5867cdced806d6503f29b99"}
TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
FEATURES = ["query_length", "vocabulary_length", "top_score", "gap_2", "gap_10",
            "top10_sd", "mean_idf", "max_idf", "runner_survival", "corpus_survival"]


def tokens(text):
    return TOKEN.findall(text.casefold())


def read_judgments(stream, queries, corpus):
    relevance = defaultdict(set)
    for row in csv.DictReader(stream, delimiter="\t"):
        query, doc = row["query-id"], row["corpus-id"]
        assert query in queries and doc in corpus
        judged = relevance[query]
        if int(row["score"]) > 0:
            judged.add(doc)
    return relevance


def load(path, dataset, splits):
    if path.is_dir():
        import pyarrow.parquet as pq

        manifest = json.loads((path / "manifest.json").read_text())
        expected = {f"{name}-00000-of-00001.parquet" for name in ("corpus", "queries")}
        expected.update(f"{split}.tsv" for split in splits)
        assert set(manifest) == expected
        for name, entry in manifest.items():
            assert hashlib.sha256((path / name).read_bytes()).hexdigest() == entry["sha256"]

        def read_parquet(name):
            rows = pq.read_table(path / f"{name}-00000-of-00001.parquet").to_pylist()
            result = {row["_id"]: row for row in rows}
            assert len(result) == len(rows)
            return result

        corpus, queries = read_parquet("corpus"), read_parquet("queries")
        qrels = {}
        for split in splits:
            with (path / f"{split}.tsv").open(encoding="utf-8") as stream:
                qrels[split] = read_judgments(stream, queries, corpus)
        return corpus, queries, qrels, manifest

    with path.open("rb") as stream:
        assert hashlib.file_digest(stream, "md5").hexdigest() == ARCHIVE_MD5[dataset]
    with ZipFile(path) as archive:
        def read_records(member):
            with archive.open(f"{dataset}/{member}.jsonl") as stream:
                result = {}
                for line in stream:
                    row = json.loads(line)
                    assert row["_id"] not in result
                    result[row["_id"]] = row
                return result

        corpus, queries = read_records("corpus"), read_records("queries")
        qrels = {}
        for split in splits:
            with archive.open(f"{dataset}/qrels/{split}.tsv") as stream:
                qrels[split] = read_judgments(io.TextIOWrapper(stream, encoding="utf-8"), queries, corpus)
    return corpus, queries, qrels, {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


class BM25:
    def __init__(self, docs):
        self.ids = sorted(docs)
        self.index = {doc: idx for idx, doc in enumerate(self.ids)}
        lengths = []
        postings = defaultdict(list)
        for idx, doc in enumerate(self.ids):
            row = docs[doc]
            words = tokens((row.get("title") or "") + " " + row["text"])
            lengths.append(len(words))
            for term, count in Counter(words).items():
                postings[term].append((idx, count))
        lengths = np.array(lengths)
        normalization = 1.2 * (0.25 + 0.75 * lengths / lengths.mean())
        self.postings = {}
        for word, pairs in postings.items():
            ind, freq = np.asarray(pairs).T
            idf = np.log1p((len(docs) - len(ind) + 0.5) / (len(ind) + 0.5))
            self.postings[word] = (ind, idf * 2.2 * freq / (freq + normalization[ind]), idf)

    def measure(self, query_id, text):
        words = tokens(text)
        term_entries = [self.postings[w] for w in sorted(set(words) & self.postings.keys())]
        values = np.zeros(len(self.ids))
        for indices, weights, _ in term_entries:
            values[indices] += weights
        allowed = values.copy()
        out = self.index.get(query_id)
        if out is not None:
            allowed[out] = -np.inf
        top = np.argsort(-allowed.round(12), kind="stable")[:10]
        winner, runner = top[:2]
        scores = allowed[top]
        survivors = [0, 0]
        if len(term_entries) >= 2:
            for indices, weights, _ in term_entries:
                revised = allowed.copy()
                revised[indices] -= weights
                revised = revised.round(12)
                a, b = revised[winner], revised[runner]
                survivors[0] += int(a > b or (a == b and winner < runner))
                survivors[1] += int(revised.argmax() == winner)
        assert survivors[1] <= survivors[0]
        idfs = [term[-1] for term in term_entries] or [0.0]
        features = [np.log1p(len(words)), np.log1p(len(term_entries)), np.log1p(scores[0]),
                    np.log1p(max(0.0, scores[0]-scores[1])), np.log1p(max(0.0, scores[0]-scores[-1])),
                    np.log1p(scores.std()), np.mean(idfs), max(idfs),
                    *(n / max(1,len(term_entries)) for n in survivors)]
        return self.ids[winner], features


def measure(benchmark, queries, labels):
    result = []
    for qid in sorted(labels):
        winner, features = benchmark.measure(qid, queries[qid]["text"])
        result.append({"id": qid, "top_id": winner, "hit": int(winner in labels[qid]), "features": features})
    return result


def fit(x, y):
    loc, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1
    design = np.column_stack((np.ones(len(x)), (x-loc)/scale))
    ridge = np.diag([0.0] + [0.01] * x.shape[1])
    beta = np.zeros(design.shape[1])
    for _ in range(100):
        linear = design @ beta
        p = 1 / (1 + np.exp(-linear.clip(-35, 35)))
        gradient = design.T @ (p-y) / len(y) + ridge @ beta
        if np.max(np.abs(gradient)) < 1e-9:
            return loc, scale, beta
        hessian = design.T @ (design * (p*(1-p))[:,None]) / len(y) + ridge
        beta -= np.linalg.solve(hessian, gradient)
    raise RuntimeError("Logistic fitting did not converge")


def arrays(rows):
    return np.array([r["features"] for r in rows]), np.array([r["hit"] for r in rows])


def predict(x, fitted):
    loc, scale, beta = fitted
    return (x-loc)/scale @ beta[1:] + beta[0]


def assess(rows, fitted):
    x, y = arrays(rows)
    rank_scores = (predict(x[:,:-1], fitted[0]), predict(x, fitted[1]), x[:,4])
    n = len(rows)
    keep = 7*n//10

    def risk(indices, scores):
        order = np.lexsort((indices, -scores[indices]))
        return 1 - y[indices[order[:keep]]].mean()

    original = np.arange(n)
    risk_simple, risk_expanded, risk_gap = [risk(original, score) for score in rank_scores]
    rng = np.random.default_rng(221105)
    contrasts = []
    for _ in range(5000):
        sample = rng.integers(n, size=n)
        contrasts.append(100*(risk(sample, rank_scores[0]) - risk(sample, rank_scores[1])))
    lower, upper = np.quantile(contrasts, [0.025, 0.975])
    estimate = 100*(risk_simple - risk_expanded)
    for row, baseline, expanded in zip(rows, rank_scores[0], rank_scores[1]):
        row.update(baseline_logit=baseline, expanded_logit=expanded)
    return {"queries": n, "accepted": keep, "all_query_hit_rate": y.mean().item(),
            "baseline_miss_rate": risk_simple, "expanded_miss_rate": risk_expanded, "gap10_miss_rate": risk_gap,
            "miss_reduction_pp": estimate, "paired_bootstrap_95_pp": [lower, upper],
            "outside_runner_effect_queries": int(np.sum(x[:,-1] < x[:,-2])),
            "passes": bool(estimate >= 3 and lower > 0)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scifact", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--arguana", type=Path)
    args = p.parse_args()
    corpus, queries, qrels, manifest = load(args.scifact, "scifact", ["train", "test"])
    assert len(qrels["test"]) == 300 and not qrels["train"].keys() & qrels["test"].keys()
    ranker = BM25(corpus)
    x, y = arrays(measure(ranker, queries, qrels["train"]))
    fitted = fit(x[:,:-1], y), fit(x, y)
    pilot_rows = measure(ranker, queries, qrels["test"])
    pilot = assess(pilot_rows, fitted)
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = {"scifact": manifest}
    receipt = {"run_id": "retrieval-triage-20261122-r05", "hardware": "CPU",
               "training_queries": len(y), "feature_names": FEATURES,
               "pilot": pilot, "transfer": "gated" if not pilot["passes"] else "pending"}
    if pilot["passes"] and args.arguana:
        corpus, queries, qrels, manifest = load(args.arguana, "arguana", ["test"])
        assert len(qrels["test"]) == 1406
        transfer = measure(BM25(corpus), queries, qrels["test"])
        receipt["transfer"] = assess(transfer, fitted)
        (args.output/"arguana-items.json").write_text(json.dumps(transfer) + "\n")
        inputs["arguana"] = manifest
    receipt["inputs"] = inputs
    (args.output/"scifact-items.json").write_text(json.dumps(pilot_rows) + "\n")
    (args.output/"receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
