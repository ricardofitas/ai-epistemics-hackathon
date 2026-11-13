# Public NLI WSC→HANS pilot: complete cohort

The separate local-model protocol, runner, analyzer, model-source receipt and README were frozen in Git commit `9a3043a73482b4a4b7571a2835dceea7b40b71f2` at 2026-11-13 10:37:03 UTC, before any forward pass. Four pinned public three-way NLI classifiers each completed all 224 planned classifications: two replacement hypotheses for each of 72 WSC passages, plus 80 HANS examples. The exact predictions, model receipts, passage scores, HANS scores and `analysis/summary.json` accompany this report. The broader HANS600 source-only holdout was frozen separately in commit `d5a3e4ca5230a454be097c6f14d6e9e81c1922a4` before inspection of these results.

## Fixed rule comparison

Each WSC passage scores one only when its gold replacement is predicted *entailment* and its non-gold replacement is predicted *contradiction* under the imposed rule, or predicted *neutral or contradiction* under the repaired rule. The table gives paired successes as counts, with 35 selection passages and 37 source-family-disjoint confirmation passages.

| Model | Selection imposed | Selection repaired | Confirmation imposed | Confirmation repaired | HANS80 binary accuracy |
|---|---:|---:|---:|---:|---:|
| nli-deberta-v3-small | 6/35 | 6/35 | 4/37 | 4/37 | 80/80 |
| nli-distilroberta-base | 0/35 | 0/35 | 0/37 | 0/37 | 40/80 |
| nli-roberta-base | 0/35 | 0/35 | 2/37 | 2/37 | 80/80 |
| nli-deberta-v3-base | 3/35 | 3/35 | 5/37 | 6/37 | 80/80 |

The repaired rule changes **zero** of 140 model-passage scores in selection (35 × 4), and **one** of 148 in confirmation (37 × 4). All six selection pairwise model orderings are unchanged; one pair is tied under both rules. Both rules uniquely select `nli-deberta-v3-small`. The fixed repaired-selected minus imposed-selected contrast is therefore **0/37** on WSC confirmation and **0/80** on HANS80 by identity. The experiment reaches only the mechanical score-distortion level on one confirmation item; it does **not** show a candidate-choice reversal or an independent performance benefit.

An independent audit recomputed the paired counts and verified all four complete 224-row receipts and hashes. `nli-distilroberta-base` predicted entailment for all 224 inputs, explaining its zero paired WSC scores and its 40/80 score on balanced HANS80. The very low WSC paired counts limit this cohort's ability to expose the neutral-versus-contradiction distinction.

HANS80's 80 cases have only three lexical-overlap templates: one supplies all 40 non-entailments and the other two supply all 40 entailments. The apparent 100% scores for three models are narrow and cannot validate a general HANS result; a template-cluster bootstrap with just three clusters is descriptive sensitivity. The prospectively selected HANS600 extension addresses the narrow coverage, but its winner contrast is already zero by identity in this fixed cohort.

## Interpretation and limits

The WSC pairs are a curated coreference-to-NLI recast conditional on the intended referent, not official human-certified three-way NLI gold. Source families are separated between 20 selection and 21 confirmation families, but pretraining exposure and related linguistic patterns remain possible. The four models are related public cross-encoders. The raw-count winner rule is an explicit abstraction of the earlier recommendation and does not implement its significance or macro-F1 branch. No actual user adopted a recommendation. This negative result neither erases the source-verified rule mismatch nor supports a GAMMAF-level consequence claim.

The next decisive test for the original hypothesis remains the separately frozen Adaption cohort using its specified model aliases and full advice policy. A follow-on with other model families would be a new cohort and should be reported as such, with a fresh untouched confirmation set.
