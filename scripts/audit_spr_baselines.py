#!/usr/bin/env python3
"""Compare one released AI Scientist SPR report with a public task table.

Inputs are the four original text files from niharshah/AIScientistPitfalls:
SPR Task/BenchmarkIssue/SPR.md,
AgentLaboratory/generated_research/BenchmarkIssue/research_dir/research_dir_0_lab_1/src/run_experiments.py,
the adjacent experiment_output.log, and the lab_1/report.txt.
"""

import argparse
import ast
import json
import re
from pathlib import Path


def supplied_scores(text: str) -> dict[str, float]:
    scores = {
        name: float(value)
        for name, value in re.findall(
            r"^\|\s*\*\*([A-Z]{5})\*\*\s*\|\s*(\d+(?:\.\d+)?)\s*%\s*\|",
            text,
            flags=re.MULTILINE,
        )
    }
    if len(scores) != 20:
        raise ValueError(f"Expected 20 reference scores in task, found {len(scores)}")
    return scores


def coded_scores(text: str) -> dict[str, float]:
    tree = ast.parse(text)
    matches = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "sota_baseline" for target in node.targets)
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one sota_baseline assignment")
    return ast.literal_eval(matches[0])


def logged_scores(text: str) -> dict[str, tuple[float, float]]:
    rows = {
        name: (float(model) * 100, float(baseline) * 100)
        for name, model, baseline in re.findall(
            r"Dataset ([A-Z]{5}):\s*\n\s*- Model Test Accuracy: (\d+\.\d+)\s*\n"
            r"\s*- SOTA Baseline Accuracy: (\d+\.\d+)",
            text,
        )
    }
    if len(rows) != 4:
        raise ValueError(f"Expected four logged benchmark summaries, found {len(rows)}")
    return rows


def reported_scores(text: str) -> dict[str, tuple[float, float]]:
    rows = {
        name: (float(model), float(baseline))
        for name, model, baseline in re.findall(
            r"\\text\{([A-Z]{5})\}\s*&\s*(\d+\.\d+)\s*&\s*(\d+\.\d+)",
            text,
        )
    }
    if len(rows) != 4:
        raise ValueError(f"Expected four reported score-table rows, found {len(rows)}")
    return rows


def audit(task: Path, code: Path, log: Path, report: Path) -> dict:
    source = supplied_scores(task.read_text(encoding="utf-8"))
    hardcoded = coded_scores(code.read_text(encoding="utf-8"))
    run = logged_scores(log.read_text(encoding="utf-8"))
    published = reported_scores(report.read_text(encoding="utf-8"))
    if set(hardcoded) != set(run) or set(run) != set(published):
        raise ValueError("Benchmark names differ between code, log and report")

    rows = []
    for name, (model, logged_baseline) in run.items():
        model_report, baseline_report = published[name]
        baseline_code = 100 * hardcoded[name]
        if abs(model - model_report) > 1e-8 or abs(logged_baseline - baseline_code) > 1e-8:
            raise ValueError(f"Code, log and report disagree on {name}")
        if abs(logged_baseline - baseline_report) > 1e-8:
            raise ValueError(f"Log and report disagree on baseline for {name}")
        supplied = source[name]
        rows.append({
            "benchmark": name,
            "model_accuracy_pct": round(model, 2),
            "reference_supplied_in_task_pct": supplied,
            "baseline_used_by_agent_pct": logged_baseline,
            "model_minus_supplied_reference_pp": round(model - supplied, 2),
            "model_minus_agent_baseline_pp": round(model - logged_baseline, 2),
        })

    return {
        "note": "Conditional cross-file comparison: exact prompt and name-to-score mapping for this run are unverified; task scores are synthetic references, not externally validated SOTA.",
        "rows": rows,
        "changed_reference_values": sum(
            row["reference_supplied_in_task_pct"] != row["baseline_used_by_agent_pct"] for row in rows
        ),
        "positive_differences_with_supplied_references": sum(
            row["model_minus_supplied_reference_pp"] > 0 for row in rows
        ),
        "positive_differences_with_agent_baselines": sum(
            row["model_minus_agent_baseline_pp"] > 0 for row in rows
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("code", type=Path)
    parser.add_argument("log", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.task, args.code, args.log, args.report), indent=2))


if __name__ == "__main__":
    main()
