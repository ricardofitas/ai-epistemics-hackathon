#!/usr/bin/env python3
"""Post-hoc descriptive ambiguity sets within NIST Round 5 submission teams.

This is a newly chosen analysis of already inspected outputs. The discovery
leader is selected on the same topics used for the pairwise p-values, so those
p-values are descriptive membership rules, not valid post-selection inference.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics

INPUT_SHA256 = {
    "candidate_registry.json": "355c9d97ef16a78b29aa657edb4668e297833c7a8da1b4c73f851697f838b0cf",
    "protocol.json": "b6a893abf4a43b6d356d4b8bdc150beec31b175ab30b6d5a872a9b47ca4586bf",
    "analysis_v3/score_matrix.json": "8beb8b498e7852be8175f407542582dab65e05ccf84f6d7398de9a90844b6c9a",
    "analysis_v3/all_pairs.jsonl": "ab299e7fdaeb443be2186554ab9d82365075fe8b5f00e7635358261b1a9a7020",
}
ALPHA = 0.05


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def quantile_linear(values, fraction):
    ordered = sorted(values)
    require(bool(ordered), "Empty distribution")
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def run(root, output):
    for name, digest in INPUT_SHA256.items():
        path = root / name
        require(path.is_file() and sha(path) == digest, "Input pin mismatch: " + name)
    registry = json.loads((root / "candidate_registry.json").read_text())
    protocol = json.loads((root / "protocol.json").read_text())
    matrix = json.loads((root / "analysis_v3/score_matrix.json").read_text())
    names = matrix["run_tags"]
    values = matrix["ndcg_cut_10"]
    require(len(names) == len(set(names)) == len(values) == 126, "Expected 126 unique runs")
    require(matrix["topic_ids"] == list(range(1, 51)), "Unexpected topic order")
    require(all(len(row) == 50 for row in values), "Unexpected matrix dimensions")
    split = protocol["topic_split"]
    discovery, confirmation = split["discovery"], split["confirmation"]
    require(len(discovery) == len(confirmation) == 25, "Expected 25/25 split")
    require(set(discovery).isdisjoint(confirmation), "Split overlaps")
    require(set(discovery) | set(confirmation) == set(range(1, 51)), "Split coverage")
    candidates = registry["candidates"]
    require({x["run_tag"] for x in candidates} == set(names), "Registry/matrix mismatch")
    teams = {x["run_tag"]: x["team"] for x in candidates}
    require(all(isinstance(teams[t], str) and teams[t] for t in names), "Missing team")
    scores = dict(zip(names, values))
    def mean(run, topics):
        return statistics.fmean(scores[run][topic - 1] for topic in topics)

    pairs = {}
    with (root / "analysis_v3/all_pairs.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            key = frozenset((row["run_a"], row["run_b"]))
            require(len(key) == 2 and key not in pairs, "Repeated/self pair")
            pairs[key] = row
    require(len(pairs) == 126 * 125 // 2, "Pair count differs from complete pool")
    by_team = defaultdict(list)
    for name in names:
        by_team[teams[name]].append(name)

    team_rows, member_rows = [], []
    for team in sorted(by_team):
        members = sorted(by_team[team])
        # Deterministic within-team rule: highest discovery mean; ascending
        # run tag resolves an exact mean tie. No cost or latency data enter.
        leader = sorted(members, key=lambda t: (-mean(t, discovery), t))[0]
        included = []
        for name in members:
            pair = None if name == leader else pairs[frozenset((leader, name))]
            p = None if pair is None else pair["discovery_raw_wilcoxon_p"]
            # The leader is retained by definition. Every other member is
            # retained under the misinterpreted raw p >= alpha rule.
            selected = name == leader or p >= ALPHA
            row = {
                "team": team, "run_tag": name, "discovery_leader": leader,
                "discovery_mean_ndcg10": mean(name, discovery),
                "confirmation_mean_ndcg10": mean(name, confirmation),
                "discovery_raw_wilcoxon_p_vs_leader": p,
                "discovery_raw_sign_flip_p_vs_leader": None if pair is None else pair["discovery_raw_sign_flip_p"],
                "in_ambiguity_set": selected,
                "pairwise_p_note": "Selected leader on these same topics; p is descriptive, not post-selection inference",
            }
            member_rows.append(row)
            if selected:
                included.append(row)
        lo = min(included, key=lambda x: (x["confirmation_mean_ndcg10"], x["run_tag"]))
        hi = sorted(included, key=lambda x: (-x["confirmation_mean_ndcg10"], x["run_tag"]))[0]
        team_rows.append({
            "team": team, "submitted_runs": len(members), "discovery_leader": leader,
            "leader_discovery_mean_ndcg10": mean(leader, discovery),
            "ambiguity_set_size": len(included),
            "ambiguity_set_run_tags": [x["run_tag"] for x in included],
            "confirmation_low_run": lo["run_tag"],
            "confirmation_high_run": hi["run_tag"],
            "confirmation_low_mean_ndcg10": lo["confirmation_mean_ndcg10"],
            "confirmation_high_mean_ndcg10": hi["confirmation_mean_ndcg10"],
            "confirmation_span_ndcg10": hi["confirmation_mean_ndcg10"] - lo["confirmation_mean_ndcg10"],
            "status": "single_submission" if len(members) == 1 else
                      ("no_ambiguous_alternative" if len(included) == 1 else "multiple_ambiguous_options"),
        })
    require(len(team_rows) == 28 and len(member_rows) == 126, "Unexpected team/member coverage")
    multi = [x for x in team_rows if x["submitted_runs"] >= 2]
    spans = [x["confirmation_span_ndcg10"] for x in multi]
    top = sorted(multi, key=lambda x: (-x["confirmation_span_ndcg10"], x["team"]))
    summary = {
        "status": "executed_post_hoc_exploratory_descriptive",
        "runs": 126, "teams": 28, "multi_submission_teams": len(multi),
        "single_submission_teams": len(team_rows) - len(multi),
        "multi_submission_teams_with_multiple_ambiguous_options": sum(x["ambiguity_set_size"] > 1 for x in multi),
        "rule": "Within team, choose highest discovery mean nDCG@10 (ascending run tag tie); include each other run when raw discovery Wilcoxon p >= 0.05 versus leader; describe min/max confirmation means across set.",
        "discovery_topics": discovery, "confirmation_topics": confirmation,
        "confirmation_span_multi_team_distribution": {
            "n": len(spans), "min": min(spans), "q25": quantile_linear(spans, .25),
            "median": quantile_linear(spans, .5), "q75": quantile_linear(spans, .75),
            "max": max(spans),
        },
        "largest_team_spans": [
            {k: row[k] for k in ("team", "submitted_runs", "ambiguity_set_size",
                                  "confirmation_span_ndcg10", "confirmation_low_run",
                                  "confirmation_high_run")}
            for row in top[:5]
        ],
        "interpretation": "Potential option sensitivity only; not an observed user choice, regret estimate, valid post-selection p-value, or independent confirmatory test.",
        "no_new_source_or_model_calls": True,
        "human_review": "not applicable to canonical score matrix; advice labels separately pending",
        "input_sha256": INPUT_SHA256,
    }
    output.mkdir(exist_ok=True)
    targets = ["team_rows.jsonl", "member_rows.jsonl", "summary.json", "README.md"]
    require(not any((output / name).exists() for name in targets), "Existing output; refusing overwrite")
    (output / "team_rows.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in team_rows))
    (output / "member_rows.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in member_rows))
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    q = summary["confirmation_span_multi_team_distribution"]
    (output / "README.md").write_text(f"""# Exploratory within-team ambiguity sets — 13 November 2026

This analysis was chosen **after** the 126-run replay and 25/25 topic results had been inspected. It is a descriptive follow-up, not a prospective replication or new holdout result. No new inference calls or benchmark source families were added.

The deterministic rule is: within each NIST submission team, choose the run with the highest mean nDCG@10 on the previously fixed 25 discovery topics (ascending run tag resolves an exact tie). Include that leader and every other submitted run with raw two-sided Wilcoxon p ≥ 0.05 against it on those same topics. Report the complete range of their mean nDCG@10 on the other 25 topics. No score-driven pair or team exclusions are allowed. Teams with one submission remain present with set size one and zero span; the leader's pairwise p is null. All 126 member rows and all 28 team rows are retained.

| Descriptive outcome | Value |
|---|---:|
| Teams with at least two submissions | {len(multi)} |
| Such teams with multiple ambiguity-set options | {summary["multi_submission_teams_with_multiple_ambiguous_options"]} |
| Confirmation span among multi-submission teams: median | {q["median"]:.6f} nDCG@10 |
| Confirmation span: first / third quartile | {q["q25"]:.6f} / {q["q75"]:.6f} |
| Confirmation span: maximum | {q["max"]:.6f} |

The largest span is {top[0]["team"]} ({top[0]["ambiguity_set_size"]} options), from {top[0]["confirmation_low_run"]} to {top[0]["confirmation_high_run"]}. This maximum was selected after seeing outcomes and is illustrative only.

**Limits:** The leader was chosen on the same discovery scores used for its Wilcoxon comparisons, so p-values used to form the set are not valid post-selection inference. The confirmation data had already been inspected before this analysis was devised. Team membership groups submissions but does not prove a shared architecture or independent team sampling. There is no cost, latency, deployment utility, actual user choice, externally justified equivalence margin or observed regret. The range gives potential option sensitivity under an artificial membership rule; it does not prove that advice caused a model-selection error. The earlier full-pool Wilcoxon and bootstrap results remain the primary executed diagnostic.

Inputs are pinned by SHA256 in `analyze.py` and `summary.json`; all rows are available in `team_rows.jsonl` and `member_rows.jsonl`. Reproduce from the parent retrieval directory with `python3 exploratory_team_20261113/analyze.py --output NEW_EMPTY_DIR`.
""")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = run(args.root, args.output)
    print(json.dumps({k: result[k] for k in ("teams", "runs", "multi_submission_teams",
                                           "multi_submission_teams_with_multiple_ambiguous_options",
                                           "confirmation_span_multi_team_distribution")}))
