"""Execute the unchanged upstream MC2 function on finite valid likelihoods."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("utils_file", type=Path, help="utils.py from the pinned upstream commit")
args = parser.parse_args()
source_path = args.utils_file
source = source_path.read_text()
expected_sha256 = "d3c827d1e2cd442a1e4738b527a18effd48cbb2aed478c12a652311b5ea4dbc8"
if hashlib.sha256(source.encode()).hexdigest() != expected_sha256:
    raise ValueError("Source differs from pinned upstream file; inspect it before changing this audit")
tree = ast.parse(source)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "process_results_mc2")
namespace = {"np": np}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source_path), "exec"), namespace)
upstream = namespace["process_results_mc2"]


def stable(ll, labels):
    values = np.asarray(ll, dtype=np.float64)
    probabilities = np.exp(values - np.max(values))
    return float(probabilities[np.array(labels) == 1].sum() / probabilities.sum())


cases = {
    "ordinary_A": ([-10.0, -11.0], [1, 0]),
    "shifted_A": ([-745.0, -746.0], [1, 0]),
    "further_shifted_A": ([-1000.0, -1001.0], [1, 0]),
    "ordinary_B": ([-1.0, -3.0], [1, 0]),
    "multi_true": ([-745.0, -746.0, -746.0, -746.0], [1, 1, 0, 0]),
}
output = {
    "source_commit": "d6de81643928d653435c431bae19945d41d32520",
    "source_git_blob": "970a7bee2d0ed3c329e624c42537ff40c6f424a8",
    "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
    "numpy_version": np.__version__,
    "cases": {},
}
for name, (ll, labels) in cases.items():
    doc = {"mc2_targets": {"labels": labels}}
    with np.errstate(under="ignore", invalid="ignore"):
        actual = float(upstream(doc, [(value, False) for value in ll])["acc"])
    output["cases"][name] = {
        "log_likelihoods": ll,
        "labels": labels,
        "upstream": actual if np.isfinite(actual) else "NaN",
        "stable_normalized_probability": stable(ll, labels),
    }

a = output["cases"]["shifted_A"]
b = output["cases"]["ordinary_B"]
assert a["upstream"] > b["upstream"]
assert a["stable_normalized_probability"] < b["stable_normalized_probability"]
assert output["cases"]["further_shifted_A"]["upstream"] == "NaN"
assert abs(output["cases"]["ordinary_A"]["stable_normalized_probability"] - a["stable_normalized_probability"]) < 1e-15
output["rank_reversal"] = {"upstream": "A > B", "stable": "B > A"}
print(json.dumps(output, indent=2))
