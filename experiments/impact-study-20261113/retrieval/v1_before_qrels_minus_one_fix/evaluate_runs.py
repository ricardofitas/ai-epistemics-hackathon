#!/usr/bin/env python3
"""Frozen-input canonical TREC-COVID run audit; no network or model calls."""
import argparse
from collections import Counter
import datetime as dt
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile

SCORER_COMMIT = "f4253652c8efd0d86ddffd0d163cc0a0f813111a"
TOPICS = list(range(1, 51))
METRICS = ("ndcg_cut_10", "P_10")
FLAGS = ["-q", "-c", "-m", "ndcg_cut.10", "-m", "P.10"]
TOLERANCE = 1e-12


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def instant(value):
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "Freeze time must include timezone")
    return result


def validate_freeze(commit, freeze_time, expected_protocol, protocol_path):
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit or "")), "External Git freeze commit required")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", expected_protocol or "")), "External protocol SHA256 required")
    require(digest(protocol_path) == expected_protocol, "Protocol differs from external frozen hash")
    require(dt.datetime.now(dt.timezone.utc) > instant(freeze_time), "Analysis cannot start before freeze")


def qrel_topics(path, expected=TOPICS):
    seen, pairs = set(), set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = line.split()
        require(len(row) == 4, "Qrels must have four columns")
        qid = row[0]
        require(qid in {str(x) for x in expected}, "Unknown qrel topic")
        require((qid, row[2]) not in pairs, "Duplicate topic/document qrel")
        require(row[3] in {"0", "1", "2"}, "Unexpected official relevance level")
        pairs.add((qid, row[2]))
        seen.add(int(qid))
    require(seen == set(expected), "Qrels do not cover the declared topics")
    return sorted(seen)


def run_structure(raw, expected=TOPICS):
    """Check canonical task structure; never join relevance labels here."""
    text = raw.decode("utf-8")
    docs, tags, counts = set(), set(), Counter()
    for line in text.splitlines():
        if not line.strip():
            continue
        row = line.split()
        require(len(row) == 6, "Run must have six columns")
        require(row[0] in {str(x) for x in expected}, "Unknown run topic")
        require(math.isfinite(float(row[4])), "Nonfinite run score")
        key = (row[0], row[2])
        require(key not in docs, "Duplicate topic/document run record")
        docs.add(key)
        tags.add(row[5])
        counts[int(row[0])] += 1
    require(bool(docs), "Wholly empty run is an operationally unusable source")
    require(len(tags) == 1, "Inconsistent encoded run tags")
    # Canonical trec_eval ignores the supplied rank column and sorts scores.
    # Do not exclude zero-based ranks or short/missing topics.
    return {"rows": len(docs), "encoded_run_tag": next(iter(tags)),
            "topic_row_counts": {str(k): v for k, v in sorted(counts.items())},
            "missing_topics": sorted(set(expected) - set(counts)),
            "short_topics": sorted(k for k, v in counts.items() if v < 10)}


def parse_canonical(text, structure, expected=TOPICS):
    values = {m: {} for m in METRICS}
    overall = {}
    for line in text.splitlines():
        fields = line.split()
        require(len(fields) == 3 and fields[0] in METRICS, "Unexpected canonical scorer output")
        measure, qid, value = fields
        score = float(value)
        require(math.isfinite(score) and -1e-9 <= score <= 1 + 1e-9, "Invalid canonical score")
        if qid == "all":
            require(measure not in overall, "Duplicate canonical overall metric")
            overall[measure] = score
        else:
            require(qid in {str(x) for x in expected}, "Unknown scored topic")
            require(int(qid) not in values[measure], "Duplicate per-topic canonical metric")
            values[measure][int(qid)] = score
    require(set(overall) == set(METRICS), "Missing canonical overall result")
    zeros = structure["missing_topics"]
    for measure in METRICS:
        missing = set(expected) - set(values[measure])
        require(missing <= set(zeros), "Scorer omitted a topic with actual run rows")
        for qid in missing:
            values[measure][qid] = 0.0
        require(set(values[measure]) == set(expected), "Incomplete canonical matrix row")
        reconstructed = sum(values[measure].values()) / len(expected)
        require(abs(reconstructed - overall[measure]) <= 0.00011,
                "Canonical -c average differs from complete-topic matrix")
    return {"metrics": {m: [values[m][q] for q in expected] for m in METRICS},
            "canonical_overall": overall, "missing_topic_zeros": zeros,
            "score_resolution": "Canonical per-topic/overall stdout rounded to four decimals"}


def canonical_score(binary, qrels, run, expected=TOPICS, capture_prefix=None):
    raw = run.read_bytes()
    structure = run_structure(raw, expected)
    command = [str(binary), *FLAGS, str(qrels), str(run)]
    result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=120)
    if capture_prefix is not None:
        Path(str(capture_prefix) + ".stdout.txt").write_text(result.stdout)
        Path(str(capture_prefix) + ".stderr.txt").write_text(result.stderr)
    record = {"command": command, "exit_code": result.returncode,
              "stdout": result.stdout, "stderr": result.stderr, "structure": structure}
    require(result.returncode == 0, "Canonical scorer returned nonzero: " + result.stderr[:300])
    record.update(parse_canonical(result.stdout, structure, expected))
    return record


def holm_adjust(pvalues):
    import numpy as np
    order = np.argsort(pvalues, kind="stable")
    adjusted = np.empty(len(order), dtype=float)
    ceiling = 0.0
    for rank, pos in enumerate(order):
        ceiling = max(ceiling, min(1.0, float(pvalues[pos]) * (len(order) - rank)))
        adjusted[pos] = ceiling
    return adjusted


def paired_wilcoxon(values, pairs):
    import numpy as np
    import scipy
    from scipy.stats import wilcoxon
    require(scipy.__version__ == "1.17.0", "Frozen SciPy1.17.0 required")
    integers = np.rint(values * 10000).astype(np.int64)
    require(np.max(np.abs(values - integers / 10000)) < 1e-10,
            "Wilcoxon requires canonical four-decimal values")
    pvalues, nonzero, tied = [], [], []
    for a, b in pairs:
        differences = integers[:, a] - integers[:, b]
        n = int(np.count_nonzero(differences))
        p = 1.0 if n == 0 else float(wilcoxon(
            differences, zero_method="wilcox", correction=False,
            alternative="two-sided", method="auto").pvalue)
        require(math.isfinite(p) and 0 <= p <= 1, "Invalid Wilcoxon pvalue")
        pvalues.append(p)
        nonzero.append(n)
        tied.append(len(np.unique(np.abs(differences[differences != 0]))) < n)
    return np.asarray(pvalues), np.asarray(nonzero), np.asarray(tied)


def paired_sign_flip(values, pairs, rng, repeats):
    import numpy as np
    observed = values.mean(axis=0)
    wanted = np.abs(observed[pairs[:, 0]] - observed[pairs[:, 1]])
    counts = np.zeros(len(pairs), dtype=np.int64)
    for offset in range(0, repeats, 2048):
        n = min(2048, repeats - offset)
        signs = rng.integers(0, 2, size=(n, len(values)), dtype=np.int8).astype(float) * 2 - 1
        permuted = signs @ values / len(values)
        for first in range(0, len(pairs), 256):
            last = min(first + 256, len(pairs))
            pair = pairs[first:last]
            delta = np.abs(permuted[:, pair[:, 0]] - permuted[:, pair[:, 1]])
            counts[first:last] += np.count_nonzero(delta >= wanted[first:last] - TOLERANCE, axis=0)
    return (counts + 1) / (repeats + 1)


def paired_bootstrap(values, topics, pairs, rng, repeats):
    import numpy as np
    strata = [[j for j, q in enumerate(topics) if lo <= q <= hi]
              for lo, hi in [(1, 35), (36, 45), (46, 50)]]
    indices = np.concatenate([rng.choice(s, size=(repeats, len(s)), replace=True)
                              for s in strata if s], axis=1)
    sampled = values[indices].mean(axis=1)
    low, high = np.empty(len(pairs)), np.empty(len(pairs))
    for first in range(0, len(pairs), 128):
        last = min(first + 128, len(pairs))
        pair = pairs[first:last]
        differences = sampled[:, pair[:, 0]] - sampled[:, pair[:, 1]]
        quantiles = np.quantile(differences, [0.025, 0.975], axis=0, method="linear")
        low[first:last], high[first:last] = quantiles
    return low, high


def compute_diagnostics(matrix, names, split, statistics, output):
    import numpy as np
    values = np.asarray(matrix, dtype=float).T
    pairs = np.asarray(list(itertools.combinations(range(len(names)), 2)), dtype=int)
    require(len(pairs) == len(names) * (len(names) - 1) // 2, "Pair coverage")
    sign_rng = np.random.default_rng(statistics["sign_flip_seed"])
    boot_rng = np.random.default_rng(statistics["bootstrap_seed"])
    blocks = {}
    for label, topics in [("full", TOPICS), ("discovery", split["discovery"]),
                          ("confirmation", split["confirmation"])]:
        sample = values[[q - 1 for q in topics]]
        means = sample.mean(axis=0)
        delta = means[pairs[:, 0]] - means[pairs[:, 1]]
        pvalues = paired_sign_flip(sample, pairs, sign_rng, statistics["sign_flip_repeats"])
        wilcoxon, nonzero, tied = paired_wilcoxon(sample, pairs)
        low, high = paired_bootstrap(sample, topics, pairs, boot_rng, statistics["bootstrap_repeats"])
        blocks[label] = {"delta": delta, "p": pvalues, "wilcoxon": wilcoxon,
                         "nonzero": nonzero, "abs_ties": tied, "low": low, "high": high}
        print(json.dumps({"diagnostic_block_complete": label, "pairs": len(pairs)}), flush=True)
    adjusted = holm_adjust(blocks["confirmation"]["p"])
    wilcoxon_adjusted = holm_adjust(blocks["confirmation"]["wilcoxon"])
    paired_rows = []
    for j, (a, b) in enumerate(pairs):
        row = {"run_a": names[a], "run_b": names[b]}
        for label, block in blocks.items():
            row.update({label + "_mean_difference": float(block["delta"][j]),
                        label + "_raw_sign_flip_p": float(block["p"][j]),
                        label + "_raw_wilcoxon_p": float(block["wilcoxon"][j]),
                        label + "_wilcoxon_nonzero_topic_differences": int(block["nonzero"][j]),
                        label + "_wilcoxon_absolute_difference_ties": bool(block["abs_ties"][j]),
                        label + "_paired_bootstrap95_low": float(block["low"][j]),
                        label + "_paired_bootstrap95_high": float(block["high"][j]),
                        label + "_symmetric95_bound": max(abs(float(block["low"][j])), abs(float(block["high"][j])))})
        row["full_bad_advice_equivalence_replay"] = bool(blocks["full"]["wilcoxon"][j] >= 0.05)
        row["full_sign_flip_sensitivity_equivalence_replay"] = bool(blocks["full"]["p"][j] >= 0.05)
        row["full_metric_vectors_identical"] = bool(np.array_equal(values[:, a], values[:, b]))
        row["discovery_nonsignificant"] = bool(blocks["discovery"]["wilcoxon"][j] >= 0.05)
        row["discovery_sign_flip_nonsignificant_sensitivity"] = bool(blocks["discovery"]["p"][j] >= 0.05)
        row["confirmation_wilcoxon_holm_adjusted_p_all_pairs"] = float(wilcoxon_adjusted[j])
        row["confirmation_sign_flip_holm_adjusted_p_all_pairs"] = float(adjusted[j])
        paired_rows.append(row)
    (output / "all_pairs.jsonl").write_text("".join(json.dumps(r, allow_nan=False) + "\n" for r in paired_rows))
    nonsig = blocks["full"]["wilcoxon"] >= 0.05
    discovery = blocks["discovery"]["wilcoxon"] >= 0.05
    identical = np.asarray([np.array_equal(values[:, a], values[:, b]) for a, b in pairs])
    def distribution(array):
        if not len(array):
            return {"n": 0}
        return {"n": len(array), "min": float(array.min()), "max": float(array.max()),
                "median": float(np.median(array)),
                "quantiles_05_25_50_75_95": [float(x) for x in np.quantile(array, [.05, .25, .5, .75, .95], method="linear")]}
    summary = {"status": "complete_descriptive_margin_free_audit", "pairs": len(pairs),
               "primary_full50_nonsignificant_pairs": int(nonsig.sum()),
               "primary_full50_bad_equivalence_replay": "Wilcoxon raw p>=0.05, an offered-test branch of observed advice; not a valid equivalence assertion",
               "primary_full50_nonsignificant_identical_metric_vectors": int(np.count_nonzero(nonsig & identical)),
               "primary_full50_nonsignificant_distinct_metric_vectors": int(np.count_nonzero(nonsig & ~identical)),
               "sensitivity_full50_sign_flip_nonsignificant_pairs": int(np.count_nonzero(blocks["full"]["p"] >= .05)),
               "full50_nonsignificant_absolute_observed_gaps": distribution(np.abs(blocks["full"]["delta"][nonsig])),
               "full50_nonsignificant_symmetric95_bounds": distribution(np.maximum(np.abs(blocks["full"]["low"][nonsig]), np.abs(blocks["full"]["high"][nonsig]))),
               "secondary_discovery_nonsignificant_pairs": int(discovery.sum()),
               "secondary_confirmation_absolute_gaps_in_discovery_nonsignificant_subset": distribution(np.abs(blocks["confirmation"]["delta"][discovery])),
               "secondary_confirmation_wilcoxon_holm_flags_in_discovery_nonsignificant_subset": int(np.count_nonzero(discovery & (wilcoxon_adjusted < .05))),
               "secondary_confirmation_sign_flip_holm_flags_in_discovery_sign_flip_nonsignificant_subset": int(np.count_nonzero((blocks["discovery"]["p"] >= .05) & (adjusted < .05))),
               "monte_carlo_repeats": statistics["sign_flip_repeats"],
               "minimum_monte_carlo_p": 1 / (statistics["sign_flip_repeats"] + 1),
               "bootstrap_repeats": statistics["bootstrap_repeats"],
               "numerical_comparison_tolerance": TOLERANCE,
               "random_blocks_order": ["full", "discovery", "confirmation"],
               "wilcoxon": {"scipy_version": "1.17.0", "zero_method": "wilcox", "correction": False,
                            "alternative": "two-sided", "method": "auto", "all_zero": "p1",
                            "input": "integer differences from canonical scores x10000",
                            "null": "distribution of paired differences symmetric aboutzero, not mean equivalence",
                            "limits": "Auto may use asymptotic approximation with ties/zeros; small nonzero counts visible per pair"},
               "bootstrap": "Shared topic resamples across all models within block and topic-era stratum; percentile95, linear quantiles",
               "fixed_utility_margin": None,
               "scope": "No practical-equivalence margin, latency/cost ordering, candidate-selection regret, real-user harm or population prevalence is inferred.",
               "small_sample_limit": "Fifty public pooled topics, old-topic judgment feedback, correlated runs/teams and incomplete relevance judgments; split diagnostics are secondary, not literal all50-advice reproduction.",
               "all_pairs_sha256": digest(output / "all_pairs.jsonl")}
    save(output / "diagnostics_summary.json", summary)
    return summary


def run_analysis(args):
    root = args.directory.resolve()
    protocol_path = root / "protocol.json"
    validate_freeze(args.freeze_commit, args.freeze_time, args.freeze_protocol_sha256, protocol_path)
    protocol = load(protocol_path)
    pins = protocol["artifacts_sha256"]
    require({"candidate_registry.json", "source/download_receipt.json", "evaluate_runs.py",
             "trec_eval_upstream.json", "trec_eval_release_tree.json",
             "trec_eval_source_receipt.json", "trec_eval_build_receipt.json"} <= set(pins),
            "Missing required frozen source/scorer pins")
    for relative, expected in pins.items():
        require(digest(root / relative) == expected, "Frozen input hash mismatch: " + relative)
    require("evaluate_runs.py" in pins and digest(Path(__file__)) == pins["evaluate_runs.py"],
            "Executing evaluator is not pinned")
    registry = load(root / "candidate_registry.json")
    candidates = registry["candidates"]
    require(len(candidates) == 126 and len({x["run_tag"] for x in candidates}) == 126, "All126 planned candidates required")
    require(candidates == sorted(candidates, key=lambda x: x["run_tag"]), "Candidate order must be frozen sorted run_tag")
    receipt = load(root / "source/download_receipt.json")
    require(receipt["registry_sha256"] == digest(root / "candidate_registry.json"), "Source receipt registry differs")
    source_rows = receipt["records"]
    records = {r["run_tag"]: r for r in source_rows}
    require(len(records) == len(source_rows) == 127, "Expected126 source records plus matching qrels")
    require(set(records) == {r["run_tag"] for r in candidates} | {"MATCHING_QRELS"}, "Source receipt coverage changed")
    qrecord = records["MATCHING_QRELS"]
    require(not qrecord.get("error_type"), "Matching qrels source unavailable; cannot score")
    require(qrecord["url"] == registry["matching_qrels"] ==
            "https://ir.nist.gov/trec-covid/data/qrels-covid_d5_j4.5-5.txt",
            "Matching residual qrels provenance changed")
    qrels = root / "source" / qrecord["local_file"]
    require(digest(qrels) == qrecord["sha256"], "Qrels bytes differ from frozen receipt")
    qrel_topics(qrels)
    upstream = load(root / "trec_eval_upstream.json")
    require(upstream["commit"] == SCORER_COMMIT, "Wrong canonical scorer commit")
    tree = load(root / "trec_eval_release_tree.json")
    require(tree["sha"] == upstream["tree_sha"], "Wrong scorer source tree")
    for entry in tree["tree"]:
        if entry["type"] != "blob":
            continue
        raw = (root / "scorer_source" / entry["path"]).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == entry["sha"], "Canonical source changed: " + entry["path"])
    binary = root / "scorer_source/trec_eval"
    build = load(root / "trec_eval_build_receipt.json")
    require(digest(binary) == build["binary_sha256"], "Canonical executable changed")
    require(build["canonical_flags"] == FLAGS, "Frozen canonical flags differ")
    import scipy
    import numpy as np
    require(scipy.__version__ == build["scipy_version"] == "1.17.0", "SciPy version differs")
    require(np.__version__ == build["numpy_version"] == "2.3.5", "NumPy version differs")
    import scipy.stats._wilcoxon as wilcoxon_source
    require(digest(Path(wilcoxon_source.__file__)) == build["scipy_wilcoxon_source_sha256"],
            "Installed Wilcoxon implementation differs from recorded bytes")
    split = protocol["topic_split"]
    require(len(split["discovery"]) == len(split["confirmation"]) == 25, "Expected25/25 split")
    require(set(split["discovery"]).isdisjoint(split["confirmation"]) and
            sorted(split["discovery"] + split["confirmation"]) == TOPICS, "Topic partition changed")
    statistics = protocol["statistics"]
    require(statistics["sign_flip_repeats"] == 199999 and statistics["sign_flip_seed"] == 2026111341
            and statistics["bootstrap_repeats"] == 10000 and statistics["bootstrap_seed"] == 2026111342,
            "Frozen statistical settings differ")
    if "numeric_comparison_tolerance" in statistics:
        require(statistics["numeric_comparison_tolerance"] == TOLERANCE, "Numeric tolerance changed")
    output = args.output.resolve() if args.output else root / "analysis"
    require(not output.exists(), "Refusing to replace analysis output")
    output.mkdir(parents=True)
    (output / "canonical").mkdir()
    started = stamp()
    save(output / "analysis_start.json", {"started_utc": started, "freeze_commit": args.freeze_commit,
                                         "freeze_time": args.freeze_time, "protocol_sha256": digest(protocol_path),
                                         "freeze_scope": "Caller externally verifies Git commit/time; this script checks local bytes and ordering",
                                         "planned_candidates": 126, "planned_topics": TOPICS})
    rows, matrix = [], []
    for index, candidate in enumerate(candidates, 1):
        tag = candidate["run_tag"]
        rec = records[tag]
        row = {"run_tag": tag, "team": candidate["team"], "source_url": candidate["url"],
               "source_sha256": rec.get("sha256"), "status": "operational_incomplete",
               "metrics": {m: [None] * 50 for m in METRICS}}
        try:
            require(rec["url"] == candidate["url"], "Run receipt URL differs from frozen registry")
            require(not rec.get("error_type"), "Frozen fetch failure: " + str(rec.get("error")))
            source = root / "source" / rec["local_file"]
            require(digest(source) == rec["sha256"], "Run source hash mismatch")
            raw = gzip.decompress(source.read_bytes())
            require(hashlib.sha256(raw).hexdigest() == rec["uncompressed_sha256"], "Decompressed run hash mismatch")
            with tempfile.TemporaryDirectory(prefix="canonical_run_") as tmp:
                file = Path(tmp) / "run.txt"
                file.write_bytes(raw)
                result = canonical_score(binary, qrels, file,
                                         capture_prefix=output / "canonical" / f"{index:03}")
            result.pop("stdout")
            result.pop("stderr")
            result["command"][-1] = "<exact decompressed frozen run bytes in temporary file>"
            row.update(result)
            row["status"] = "complete"
        except Exception as exc:
            row["error_type"] = type(exc).__name__
            row["error"] = str(exc)
        rows.append(row)
        matrix.append(row["metrics"]["ndcg_cut_10"])
        save(output / "run_records_partial.json", rows)
        print(json.dumps({"scored_source_records": index, "planned": 126, "run_tag": tag, "status": row["status"]}), flush=True)
    save(output / "run_records.json", rows)
    save(output / "score_matrix.json", {"topic_ids": TOPICS, "run_tags": [r["run_tag"] for r in rows],
                                      "ndcg_cut_10": matrix,
                                      "P_10": [r["metrics"]["P_10"] for r in rows],
                                      "missing_source_policy": "nulls; no fabricated zeros",
                                      "missing_topic_policy": "canonical -c zeros only within structurally valid available runs",
                                      "scorer_output_resolution": 0.0001})
    complete = all(r["status"] == "complete" for r in rows)
    summary = {"started_utc": started, "ended_scoring_utc": stamp(), "planned": 126,
               "complete": sum(r["status"] == "complete" for r in rows), "primary_matrix_complete": complete,
               "source_failures": [r["run_tag"] for r in rows if r["status"] != "complete"],
               "canonical_scorer_commit": SCORER_COMMIT, "canonical_flags": FLAGS,
               "score_matrix_sha256": digest(output / "score_matrix.json"),
               "freeze_commit": args.freeze_commit, "freeze_protocol_sha256": args.freeze_protocol_sha256}
    save(output / "scoring_summary.json", summary)
    if complete:
        compute_diagnostics(matrix, [r["run_tag"] for r in rows], split, statistics, output)
    else:
        save(output / "diagnostics_summary.json", {"status": "not_run_primary_matrix_incomplete",
                                                  "planned_candidates": 126,
                                                  "source_failures": summary["source_failures"],
                                                  "comparison_outcomes": None})
    save(output / "analysis_completion.json", {"completed_utc": stamp(), **summary,
                                              "diagnostics_sha256": digest(output / "diagnostics_summary.json")})
    return summary


def self_test(root):
    import numpy as np
    binary = (root / "scorer_source/trec_eval").resolve()
    tests = []
    with tempfile.TemporaryDirectory(prefix="trec_synthetic_") as temp:
        d = Path(temp)
        q = d / "qrels"
        q.write_text("1 0 a 2\n1 0 b 1\n2 0 d 2\n2 0 e 1\n3 0 z 1\n4 0 w 1\n")
        r = d / "run"
        r.write_text("1 Q0 a 1 4 test\n1 Q0 b 2 3 test\n2 Q0 e 1 2 test\n4 Q0 u 1 -1 test\n")
        result = canonical_score(binary, q, r, [1, 2, 3, 4])
        require(result["metrics"]["ndcg_cut_10"] == [1.0, .3801, 0.0, 0.0], "Canonical graded/short/missing fixture")
        require(result["metrics"]["P_10"] == [.2, .1, 0.0, 0.0], "Canonical fixed-cutoff precision fixture")
        require(result["canonical_overall"]["ndcg_cut_10"] == .345, "Canonical -c averaging fixture")
        tests.extend(["graded_linear_gains", "short_ranking_padding", "missing_topic_zero",
                      "complete_query_averaging", "fixed_cutoff_precision", "finite_negative_scores_allowed"])
        bad = b"1 Q0 a 1 2 t\n1 Q0 a 2 1 t\n"
        try:
            run_structure(bad, [1])
        except ValueError:
            tests.append("duplicate_document_rejected")
        else:
            raise ValueError("Duplicate fixture unexpectedly accepted")
        for raw in [b"", b"1 Q0 a 1 nan t\n", b"99 Q0 a 1 2 t\n", b"invalid\n"]:
            try:
                run_structure(raw, [1])
            except ValueError:
                tests.append("invalid_or_missing_source_rejected")
            else:
                raise ValueError("Bad source fixture accepted")
        qtie = d / "qtie"
        qtie.write_text("1 0 a 2\n1 0 b 0\n")
        a, b = d / "tie_a", d / "tie_b"
        a.write_text("1 Q0 a 1 1 t\n1 Q0 b 2 1 t\n")
        b.write_text("1 Q0 b 1 1 t\n1 Q0 a 2 1 t\n")
        require(canonical_score(binary, qtie, a, [1])["metrics"] ==
                canonical_score(binary, qtie, b, [1])["metrics"], "Canonical score-tie invariance")
        tests.append("canonical_score_ties_ignore_input_rank")
    values = np.array([[.1, .1, .2], [.8, .8, .3], [.3, .3, .5], [.6, .6, .4]])
    pairs = np.array([[0, 1], [0, 2], [1, 2]])
    a = paired_sign_flip(values, pairs, np.random.default_rng(42), 199)
    b = paired_sign_flip(values, pairs, np.random.default_rng(42), 199)
    require(np.array_equal(a, b) and a[0] == 1.0, "Shared sign replay")
    require(np.all((a >= 1/200) & (a <= 1)), "MonteCarlo p bounds")
    lo, hi = paired_bootstrap(values, [1, 2, 36, 46], pairs, np.random.default_rng(42), 200)
    require(lo[0] == hi[0] == 0, "Shared paired bootstrap preserves identical candidates")
    require(np.all(lo <= hi), "Percentile order")
    require(np.array_equal(holm_adjust(np.array([.01, .04, .2])), [.03, .08, .2]), "Holm fixture")
    tests.extend(["seeded_sign_draws_replay", "monte_carlo_plus_one_bounds",
                  "paired_bootstrap_same_candidate_identity", "percentile_order", "holm_known_fixture"])
    w, n, ties = paired_wilcoxon(values, pairs)
    require(w[0] == 1 and n[0] == 0, "Allzero Wilcoxon convention")
    known, _, _ = paired_wilcoxon(np.array([[.1, 0.0], [.2, 0.0], [.3, 0.0]]),
                                  np.array([[0, 1]]))
    require(known[0] == .25, "Known exact signedrank fixture")
    tests.extend(["wilcoxon_allzero_p1", "wilcoxon_known_exact_integer_fixture"])
    with tempfile.TemporaryDirectory(prefix="trec_gate_") as tmp:
        protocol = Path(tmp) / "protocol"
        protocol.write_text("{}\n")
        for hash_value, when in [("f"*64, "2000-01-01T00:00:00Z"),
                                 (digest(protocol), "2999-01-01T00:00:00Z")]:
            try:
                validate_freeze("a"*40, when, hash_value, protocol)
            except ValueError:
                tests.append("invalid_hash_or_prefreeze_gate_rejected")
            else:
                raise ValueError("Invalid freeze fixture accepted")
    # End-to-end source ingestion uses only generated fixtures. The expensive
    # statistics block is replaced with a labelled stub; no actual sources or
    # performance outcomes are read by these checks.
    import contextlib
    import io
    import shutil
    with tempfile.TemporaryDirectory(prefix="trec_end_to_end_fixture_") as tmp:
        fixture = Path(tmp)
        source = fixture / "source"
        source.mkdir()
        shutil.copytree(root / "scorer_source", fixture / "scorer_source")
        for name in ["trec_eval_upstream.json", "trec_eval_release_tree.json",
                     "trec_eval_source_receipt.json", "trec_eval_build_receipt.json"]:
            shutil.copyfile(root / name, fixture / name)
        shutil.copyfile(Path(__file__), fixture / "evaluate_runs.py")
        official_qrel_url = "https://ir.nist.gov/trec-covid/data/qrels-covid_d5_j4.5-5.txt"
        qrels = source / "qrels.txt"
        qrels.write_text("".join(f"{q} 0 d{q} 2\n" for q in TOPICS))
        generated = "".join(f"{q} Q0 d{q} 1 1 fixture\n" for q in TOPICS).encode()
        weak = "".join(f"{q} Q0 d{q} 1 1 fixture\n" for q in TOPICS[:-1]).encode()
        candidates, record_list = [], [{"run_tag": "MATCHING_QRELS", "url": official_qrel_url,
                                       "local_file": qrels.name, "sha256": digest(qrels)}]
        for i in range(126):
            tag = f"fixture_{i:03}"
            raw = weak if i == 0 else generated
            file = source / (tag + ".gz")
            file.write_bytes(gzip.compress(raw, mtime=0))
            url = "synthetic-fixture://" + tag
            candidates.append({"run_tag": tag, "team": "synthetic", "url": url})
            record_list.append({"run_tag": tag, "url": url, "local_file": file.name,
                                "sha256": digest(file),
                                "uncompressed_sha256": hashlib.sha256(raw).hexdigest()})
        registry_path = fixture / "candidate_registry.json"
        save(registry_path, {"candidates": candidates, "matching_qrels": official_qrel_url})
        receipt_path = source / "download_receipt.json"
        def write_fixture_protocol():
            save(receipt_path, {"records": record_list, "registry_sha256": digest(registry_path)})
            names = ["candidate_registry.json", "source/download_receipt.json", "evaluate_runs.py",
                     "trec_eval_upstream.json", "trec_eval_release_tree.json",
                     "trec_eval_source_receipt.json", "trec_eval_build_receipt.json"]
            proto = {"artifacts_sha256": {n: digest(fixture / n) for n in names},
                     "topic_split": {"discovery": TOPICS[:25], "confirmation": TOPICS[25:]},
                     "statistics": {"sign_flip_repeats": 199999, "sign_flip_seed": 2026111341,
                                    "bootstrap_repeats": 10000, "bootstrap_seed": 2026111342}}
            save(fixture / "protocol.json", proto)
        write_fixture_protocol()
        original = globals()["compute_diagnostics"]
        def synthetic_stub(matrix, names, split, statistics, output):
            save(output / "diagnostics_summary.json", {"status": "synthetic_fixture_statistics_stub"})
        globals()["compute_diagnostics"] = synthetic_stub
        try:
            args = argparse.Namespace(directory=fixture, freeze_commit="f"*40,
                                      freeze_time="2000-01-01T00:00:00Z",
                                      freeze_protocol_sha256=digest(fixture / "protocol.json"),
                                      output=fixture / "complete_fixture")
            with contextlib.redirect_stdout(io.StringIO()):
                receipt = run_analysis(args)
            require(receipt["complete"] == 126 and receipt["primary_matrix_complete"], "Full126 fixture coverage")
            scored = load(args.output / "score_matrix.json")
            require(scored["ndcg_cut_10"][0][-1] == 0 and
                    load(args.output / "run_records.json")[0]["structure"]["short_topics"] == TOPICS[:-1],
                    "Weak/missing-topic fixture must remain a valid candidate")
            tests.extend(["full126_source_ingestion", "weak_short_and_missing_topics_not_excluded"])
            record_list[1]["error_type"] = "SyntheticMissing"
            record_list[1]["error"] = "deliberate synthetic source absence"
            write_fixture_protocol()
            args.freeze_protocol_sha256 = digest(fixture / "protocol.json")
            args.output = fixture / "incomplete_fixture"
            with contextlib.redirect_stdout(io.StringIO()):
                receipt = run_analysis(args)
            matrix = load(args.output / "score_matrix.json")
            require(receipt["complete"] == 125 and not receipt["primary_matrix_complete"] and
                    matrix["ndcg_cut_10"][0] == [None] * 50, "Source failure cannot become fabricated zeros")
            require(load(args.output / "diagnostics_summary.json")["status"] == "not_run_primary_matrix_incomplete",
                    "Incomplete pool cannot silently run reduced primary comparisons")
            tests.extend(["failed_source_preserved_as_nulls", "incomplete126_pool_blocks_primary_diagnostics"])
        finally:
            globals()["compute_diagnostics"] = original
    return {"synthetic_checks": len(tests), "checks": tests, "no_candidate_scores_read": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--freeze-commit")
    ap.add_argument("--freeze-time")
    ap.add_argument("--freeze-protocol-sha256")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(args.directory)))
        return
    if not (args.freeze_commit and args.freeze_time and args.freeze_protocol_sha256):
        ap.error("Actual scoring requires external freeze commit/time/protocol hash")
    print(json.dumps(run_analysis(args)), flush=True)


if __name__ == "__main__":
    main()
