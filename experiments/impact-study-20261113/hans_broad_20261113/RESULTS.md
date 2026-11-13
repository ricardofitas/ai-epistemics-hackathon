# HANS600 broader external holdout: complete public-model cohort

The source-only HANS600 sample was frozen in Git commit `d5a3e4ca5230a454be097c6f14d6e9e81c1922a4` before inspection of the WSC model results. Its separate inference plan, runner and analyzer were frozen in commit `0d7647fd95b6b61b6d0eebed44657c03ea2c0d40` at 2026-11-13 10:45:35 UTC before any HANS600 forward pass. Each of the same four pinned public NLI models completed all 600 cases; 2,400 raw predictions, receipts and the exact per-case/per-subcase scores accompany this report.

The sample has 20 cases in each of 30 official subcases, 100 in each of the three-heuristic-by-two-label cells, and 58 templates. It has no shared official pair ID or exact text pair with the earlier HANS80. Macro accuracy across the 30 equally sized subcases equals micro accuracy across the 600 cases.

| Model | HANS80 narrow | HANS600 broad | Constituent | Lexical overlap | Subsequence |
|---|---:|---:|---:|---:|---:|
| nli-deberta-v3-small | 100.0% | 70.0% | 59.0% | 98.5% | 52.5% |
| nli-distilroberta-base | 50.0% | 53.3% | 53.5% | 54.5% | 52.0% |
| nli-roberta-base | 100.0% | 68.8% | 57.0% | 90.5% | 59.0% |
| nli-deberta-v3-base | 100.0% | 77.7% | 69.5% | 97.0% | 66.5% |

The original WSC35 selection has the same unique winner under both scoring rules: `nli-deberta-v3-small`. Consequently the predeclared repaired-selected minus imposed-selected HANS600 accuracy is **0.0 percentage points** (paired bootstrap interval `[0, 0]` by identity). This extension supplies no evidence of a correction-induced choice reversal.

The HANS600 source selection and contrast definition were fixed before WSC results were inspected. Its separate inference plan was finalized after the WSC winners were known and before HANS600 predictions. Thus the zero winner contrast was already determined when HANS600 inference began; the informative new observation is the models' performance across the broader subcases.

The broader sample exposes the narrow HANS80 subset's ceiling: its three lexical-overlap templates gave three candidates 100%, while these candidates score 68.8–77.7% on HANS600. Within HANS600, the WSC-selected DeBERTa-small scores 70.0% and DeBERTa-base scores 77.7%, a descriptive **7.7-point** gap. That latter comparison is observed after viewing all four HANS600 accuracies, so it is not a prospectively selected external-performance contrast. Non-entailment is the main weakness outside lexical overlap: for DeBERTa-small, constituent 18% and subsequence 7%; for DeBERTa-base, 39% and 33%.

HANS600 broadens coverage within the *same public HANS source*, not across independently collected benchmarks. Its templates and subcases remain related, model pretraining exposure is unknown, and the WSC pairs lack human-certified NLI gold. The WSC raw-count choice is an abstraction of the original advice, and no user choice was observed. The per-subcase paired bootstrap is a conditional sensitivity to this sampling plan, not a population guarantee or a GAMMAF-level claim.
