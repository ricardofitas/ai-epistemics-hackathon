# Exploratory within-team ambiguity sets — 13 November 2026

This analysis was chosen **after** the 126-run replay and 25/25 topic results had been inspected. It is a descriptive follow-up, not a prospective replication or new holdout result. No new inference calls or benchmark source families were added.

The deterministic rule is: within each NIST submission team, choose the run with the highest mean nDCG@10 on the previously fixed 25 discovery topics (ascending run tag resolves an exact tie). Include that leader and every other submitted run with raw two-sided Wilcoxon p ≥ 0.05 against it on those same topics. Report the complete range of their mean nDCG@10 on the other 25 topics. No score-driven pair or team exclusions are allowed. Teams with one submission remain present with set size one and zero span; the leader's pairwise p is null. All 126 member rows and all 28 team rows are retained.

| Descriptive outcome | Value |
|---|---:|
| Teams with at least two submissions | 24 |
| Such teams with multiple ambiguity-set options | 23 |
| Confirmation span among multi-submission teams: median | 0.015522 nDCG@10 |
| Confirmation span: first / third quartile | 0.006082 / 0.032921 |
| Confirmation span: maximum | 0.179664 |

The largest span is reSearch2vec (5 options), from DoRA_NO_Judgments_6k to DoRAWithJudgments_6k. This maximum was selected after seeing outcomes and is illustrative only.

**Limits:** The leader was chosen on the same discovery scores used for its Wilcoxon comparisons, so p-values used to form the set are not valid post-selection inference. The confirmation data had already been inspected before this analysis was devised. Team membership groups submissions but does not prove a shared architecture or independent team sampling. There is no cost, latency, deployment utility, actual user choice, externally justified equivalence margin or observed regret. The range gives potential option sensitivity under an artificial membership rule; it does not prove that advice caused a model-selection error. The earlier full-pool Wilcoxon and bootstrap results remain the primary executed diagnostic.

Inputs are pinned by SHA256 in `analyze.py` and `summary.json`; all rows are available in `team_rows.jsonl` and `member_rows.jsonl`. Reproduce from the parent retrieval directory with `python3 exploratory_team_20261113/analyze.py --output NEW_EMPTY_DIR`.
