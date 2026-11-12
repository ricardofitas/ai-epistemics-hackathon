#!/usr/bin/env python3
"""Compare unshifted and stable MC2 on pinned, downloaded public model traces."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np


def audit(root, utils_path):
    source = utils_path.read_text()
    scorer_sha256 = hashlib.sha256(source.encode()).hexdigest()
    if scorer_sha256 != "d3c827d1e2cd442a1e4738b527a18effd48cbb2aed478c12a652311b5ea4dbc8":
        raise ValueError("Scorer source differs from pinned upstream file")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "process_results_mc2")
    namespace = {"np": np}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(utils_path), "exec"), namespace)
    scorer = namespace["process_results_mc2"]
    manifest = json.loads((root / "download_manifest.json").read_text())
    question_hashes = set()
    file_results = []
    material_rows = []
    for entry in manifest["files"]:
        path = root / "data" / entry["path"]
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {path}")
        count = Counter({key: 0 for key in ["rows", "candidate_likelihoods", "finite_input_rows", "nonfinite_input_rows", "nonfinite_upstream_rows", "delta_gt_1e-12", "delta_gt_1e-6"] + [f"max_ll_at_most_{t}" for t in [-700, -708.4, -740, -745.13]]})
        originals, stables, ll_values, per_row_maxes = [], [], [], []
        biggest_delta = 0.0
        biggest_logged_delta = 0.0
        for line in data.splitlines():
            row = json.loads(line)
            count["rows"] += 1
            question_hashes.add(hashlib.sha256(row["doc"]["question"].encode()).hexdigest())
            labels = np.asarray(row["doc"]["mc2_targets"]["labels"])
            ll = np.asarray([x[0] for x in row["filtered_resps"]], dtype=np.float64)
            if ll.ndim != 1 or ll.shape != labels.shape or not len(ll):
                raise ValueError(f"Unexpected row shape {entry['path']}: {row['doc_id']}")
            if not np.all(np.isin(labels, [0, 1])) or not np.any(labels == 1):
                raise ValueError("Unexpected nonbinary or all-false labels")
            count["candidate_likelihoods"] += len(ll)
            if not np.all(np.isfinite(ll)):
                count["nonfinite_input_rows"] += 1
                continue
            count["finite_input_rows"] += 1
            ll_values.extend(ll.tolist())
            row_max = float(np.max(ll))
            per_row_maxes.append(row_max)
            for threshold in [-700, -708.4, -740, -745.13]:
                if row_max <= threshold:
                    count[f"max_ll_at_most_{threshold}"] += 1
            with np.errstate(under="ignore", invalid="ignore"):
                upstream = float(scorer(row["doc"], row["filtered_resps"])["acc"])
                stable_weights = np.exp(ll - np.max(ll))
                stable = float(np.sum(stable_weights[labels == 1]) / stable_weights.sum())
            if not np.isfinite(upstream):
                count["nonfinite_upstream_rows"] += 1
                material_rows.append({"file": entry["path"], "doc_id": row["doc_id"], "upstream": str(upstream), "stable": stable, "log_likelihoods": ll.tolist()})
            else:
                originals.append(upstream)
                stables.append(stable)
                delta = abs(upstream - stable)
                biggest_delta = max(biggest_delta, delta)
                if delta > 1e-12:
                    count["delta_gt_1e-12"] += 1
                    material_rows.append({"file": entry["path"], "doc_id": row["doc_id"], "upstream": upstream, "stable": stable, "log_likelihoods": ll.tolist()})
                if delta > 1e-6:
                    count["delta_gt_1e-6"] += 1
                if isinstance(row.get("acc"), (float, int)):
                    biggest_logged_delta = max(biggest_logged_delta, abs(upstream - row["acc"]))
        file_results.append({
            "path": entry["path"],
            "counts": dict(count),
            "minimum_individual_ll": min(ll_values),
            "minimum_over_rows_of_max_candidate_ll": min(per_row_maxes),
            "maximum_abs_original_stable_score_difference": biggest_delta,
            "maximum_abs_original_logged_score_difference": biggest_logged_delta,
            "mean_original": float(np.mean(originals)),
            "mean_stable": float(np.mean(stables)),
        })
    totals = Counter()
    for f in file_results:
        totals.update(f["counts"])
    return {
        "source_repo": manifest["repo"],
        "revision": manifest["revision"],
        "selection": manifest["selection"],
        "numpy_version": np.__version__,
        "scorer_commit": "d6de81643928d653435c431bae19945d41d32520",
        "scorer_sha256": scorer_sha256,
        "files": len(file_results),
        "distinct_question_texts": len(question_hashes),
        "total_counts": dict(totals),
        "minimum_individual_ll": min(f["minimum_individual_ll"] for f in file_results),
        "minimum_over_rows_of_max_candidate_ll": min(f["minimum_over_rows_of_max_candidate_ll"] for f in file_results),
        "maximum_abs_original_stable_score_difference": max(f["maximum_abs_original_stable_score_difference"] for f in file_results),
        "maximum_abs_original_logged_score_difference": max(f["maximum_abs_original_logged_score_difference"] for f in file_results),
        "aggregate_ordering_unchanged": [f["path"] for f in sorted(file_results, key=lambda f: f["mean_original"])] == [f["path"] for f in sorted(file_results, key=lambda f: f["mean_stable"])],
        "maximum_abs_aggregate_difference": max(abs(f["mean_original"] - f["mean_stable"]) for f in file_results),
        "per_file": file_results,
        "material_rows": material_rows,
        "scope": "Public third-party model traces, 3 related SFT model families x 5 checkpoints on the same English questions; rows are not independent research cases or an unbiased prevalence sample.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("utils_file", type=Path, help="Pinned upstream TruthfulQA utils.py")
    args = parser.parse_args()
    print(json.dumps(audit(args.root, args.utils_file), indent=2))


if __name__ == "__main__":
    main()
