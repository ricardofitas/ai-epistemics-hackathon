"""Reproduce the post-outcome client-wrapper calculation from retained responses."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--report", type=Path, default=Path(__file__).with_name("POST_OUTCOME_WRAPPER_COUNTERFACTUAL.json"))
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    environment = {"re": re, "Any": object, "List": list, "Dict": dict}
    nodes = []
    for name in ("normalize_text", "compute_exact_match"):
        entry = report["method_source"]["function_sources"][name]
        assert hashlib.sha256(entry["source"].encode()).hexdigest() == entry["sha256"]
        node = ast.parse(entry["source"]).body[0]
        assert isinstance(node, ast.FunctionDef) and node.name == name
        node.decorator_list = []
        nodes.append(node)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 "pinned_native_metric_functions", "exec"), environment)
    sources = {row["source_index"]: row for row in
               json.loads((args.artifact / "selected2.json").read_text())}
    checked = 0
    for expected in report["rows"]:
        directory = args.artifact / "results" / "real" / f"{expected['source_index']}_source_typed"
        result = json.loads((directory / "RESULT.json").read_text())
        trace = json.loads((directory / "HTTP_TRACE.json").read_text())[0]
        raw = json.loads(trace["response_body"])
        message = raw["choices"][0]["message"]
        content = message["content"]
        delivered = result["delivered_row"]["generated_ans"]
        references = sources[expected["source_index"]]["record"]["target"]
        assert raw["id"] == expected["response_id"]
        assert content == expected["raw_content"]
        assert hashlib.sha256(delivered.encode()).hexdigest() == expected["delivered_text_sha256"]
        assert delivered == f"<think>{message['reasoning_content']}</think>\n<answer>{content}</answer>"
        score = environment["compute_exact_match"]
        native = score([delivered], [references])["score"]
        counterfactual = score([content], [references])["score"]
        assert native == result["native_metric_runner"]["primary_metric_result"]["score"]
        assert native == expected["retained_native_delivered_text_score"] == 0
        assert counterfactual == expected["post_outcome_raw_content_counterfactual_score"] == 1
        checked += 1
    assert checked == 2
    print(json.dumps({"status": "PASS", "fixed_responses": checked,
                      "native_delivered_scores": [0, 0],
                      "raw_final_content_counterfactual_scores": [1, 1],
                      "new_calls": 0}))


if __name__ == "__main__":
    main()
