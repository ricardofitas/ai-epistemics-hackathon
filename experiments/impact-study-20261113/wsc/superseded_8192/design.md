# Q48 WSC recast: scoring consequences on fixed classifier predictions

This is a **new exploratory experiment**, motivated by a source-verified recommendation in prior answer Q48/PR-11. It does not activate or replace the failed PAWS consequence protocol. No classifier performance has been observed during this design. Root source review and a separate prospective Git freeze are required before inference.

## Question and bounded contribution

What changes when the **same immutable three-way NLI predictions** are scored using Q48's rule that every non-gold WSC substitution is contradiction, versus a source-reviewed directional-entailment criterion accepting either neutral or contradiction for a verified non-entailment?

The primary task is a curated WSC recast, conditional on its intended coreference reading. It is not an official three-way NLI benchmark or the full original argument-role tracking target. A separately frozen HANS supplement can test that external target; its result must remain distinct.

A score increase has a mechanical component: a correct positive paired with a neutral negative is accepted by the binary rule and rejected by the imposed-contradiction rule. Stronger candidate-choice evidence needs an observed ordering/selection difference and independent confirmation. No reversal or harmful decision is assumed.

## Data and output-blind validation

The official SuperGLUE v2 release has archive SHA256 `2ed6dfa94556b4a128ff0441efe365b2e883124e7e6aa00fb8d3a6cb1fd520a9`; the exact `WSC/train.jsonl` member SHA256 is `0ffaa3fd8d21e58a0805962565d1619aa4819bc3d034255777f606f801ae5a42`. Release path, S3 version/last-modified metadata and individual JSON-line hashes are recorded.

A mechanical source-only slice contains 81 distinct source passages: one true and one false source coreference candidate, a simple subject pronoun, titlecase-name-pattern candidates, at most 70 whitespace words, and a reproducible exact target offset. These restrictions facilitate exact substitution. They do not produce a random or representative WSC sample.

Two independent first agent semantic judgments were preserved before cross-review merging. Each separately checks the positive replacement under the official intended referent and whether the negative **full sentence** is not entailed. False coreference is not automatically NLI non-entailment, nor automatically contradiction. Valid contradiction negatives are kept alongside neutral negatives.

The conservative final disposition excludes seven unresolved binary recasts: W011, W023, W032, W053, W054, W067 and W069. The previously used discovery witness W074 and its near-identical W001 variant are excluded separately as one previously used source family. Root review approves **72 primary passages**. Three-way C/N disagreements are retained as secondary uncertainty, not forced consensus. No source label is relabelled as official NLI gold. Human validation remains pending.

Original unresolved passages are model-facing. Official coreference gold fixes the analyst's intended-reading convention but is never transmitted. This convention is necessary: arbitrary possible pronoun interpretations do not all entail the same positive replacement. Neutral predictions on genuinely unresolved language cannot be called objective errors beyond the stated convention.

## Fixed cohorts and models

All 81 mechanical source rows are clustered before model predictions: casefold, collapse whitespace, join rows whose maximum forward/reverse `SequenceMatcher` similarity with `autojunk=False` is at least 0.80, then use connected components. The original discovery family is excluded in full. Source-only eligible passages are capped at 80 with a fixed random seed; here all 72 remaining rows are used.

Whole source families are randomly ordered and assigned to the currently smaller passage-count cohort; ties use a fixed seed. The approved disposition yields **41 source families**, **35 selection passages** and **37 confirmation passages**. The clustering rule and memberships are frozen before performance. Similarity grouping is an operational dependency safeguard, not proof of independent linguistic schemas.

The four requested configurations are fixed before performance: `gemma-4-31b-it`, `glm-5.2`, `qwen3.8-27b`, `deepseek-v4-flash`. Aliases do not establish immutable weights. No candidate is added, removed or selected based on observed accuracy.

## Inference and blindness

Each passage generates two exact replacements, giving 144 ordered classification tasks per candidate and 576 classifications overall. A request carries at most four complete passage pairs (eight ordered tasks); selection and confirmation never share a request. The current allocation gives **76 requests**, with the same task memberships across all four candidates and independently shuffled execution order.

Only opaque IDs, original premises and replacement hypotheses are model-facing. Coreference/NLI gold, source names, family IDs, polarity, split and study hypotheses are withheld. The common instruction allows ordinary English commonsense and asks for one JSON prediction per ID, using `entailment`, `contradiction`, `neutral`.

Common controls: temperature 0; maximum output 8192 tokens; native SSE; no tools, memory, storage or conversation history; concurrency two; 120-second per-socket-operation timeout; exactly one attempt per row. Maximum requested output-token bound is 622,592. Root checks the live pricing/budget before freezing; no USD equivalence or complete-bill claim is made.

## Frozen scores and choice abstraction

For each source passage pair:

- **Imposed-contradiction paired score:** one iff the gold replacement prediction is entailment and the non-gold replacement prediction is contradiction.
- **Repaired-binary paired score:** one iff the gold replacement prediction is entailment and the non-gold replacement prediction is neutral or contradiction.

The original answer called this paired quantity role-swap accuracy. These hypotheses are paired WSC recasts, not literal argument-swapped minimal pairs. Individual accuracy, literal E/C macro-F1 and repaired E/nonE macro-F1 are secondary. Analyst three-way accuracy is an additional predeclared sensitivity only on negatives whose source-only C/N assessment is confident; coverage and unresolved labels remain visible.

**Primary candidate choice is a prospective raw-score abstraction:** choose a unique highest paired score in the selection cohort under each rule. Q48 additionally requested a significantly higher score or an alternative macro-F1 decision. Our raw maximum does not execute that complete inferential/or-metric policy. Do not claim its significance gate was met, or that a user following the full literal advice necessarily would choose that candidate.

Report all six pairwise candidate orderings under both scoring rules, with strict reversals only when both differences are nonzero and have opposite signs. Keep all ties. If both selection winners are unique, compare their repaired paired accuracy on the independent confirmation cohort; report repaired-selected minus imposed-rule-selected performance, including zero and negative values. A tied winner set is not resolved arbitrarily. Full-cohort rankings are descriptive, not independent selection consequences.

## Failures, bounds and uncertainty

The complete-candidate primary analysis requires valid complete predictions for every planned input and all four candidates. Otherwise mark it incomplete. Never drop the failing candidate, retry until success, add easier items, or impute transport failures as semantic errors.

Additionally report conservative score bounds on every fixed cohort. A missing/invalid prediction contributes `[0,1]` at the task level. A pair is `[0,0]` if an observed member already fails that rule, `[1,1]` if both members are known correct, and `[0,1]` otherwise. Declare an ordering only when the conservative score intervals separate. Overlap and ties remain indeterminate.

The paired distortion is coupled: it equals the indicator that the gold prediction is E and the negative prediction is N. Its bounds are zero when either observed requirement fails, one when both are known to hold, and `[0,1]` otherwise. Do not subtract independently extremized score bounds as if the two rules had different predictions.

Only complete, nonempty final assistant captures with HTTP200, event-stream content, a completed terminal event **and** provider completed status, no malformed SSE JSON/transport error/fallback/format deviation can be scored. The entire final JSON must contain every expected ID exactly once and only valid labels; one outer JSON fence and casefolded labels are allowed. No repair calls.

Use 10,000 joint source-family bootstrap draws within each fixed cohort, two-sided 95% percentile intervals with NumPy linear quantiles. For a unique-winner confirmation effect, keep the observed winners fixed during resampling. This is conditional descriptive uncertainty; clustering can miss semantic relations and shared request/provider effects, and it does not establish population prevalence or calibrated generalization.

## Reporting

Preserve every attempted row, original semantic first judgment, final exclusion, raw stream, failure, tie and null. These public source-train items are not proved absent from pretraining. This experiment measures consequences of a declared scoring rule and selection abstraction for fixed candidates; it does not establish actual user adoption, real-world harm, an intrinsic WSC defect, full argument-role capability, or human-validated NLI gold.
