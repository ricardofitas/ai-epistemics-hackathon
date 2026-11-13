# Prospective math benchmark-choice consequence pilot

Status: design before any solver inference. This is a new selected-case consequence pilot following the completed 36-call source-repair advice study. Earlier advice outcomes motivate the resource comparison; no solver-performance data from this pilot have been inspected. The original WSC/HANS confirmation data are not reused.

## Question and bounded decision

Can using the recommended added-clause GSM-Symbolic P1/P2 resource to choose between two fixed assistants select a different assistant from a task-matched numerical-substitution/harmless-rewording evaluation, and does that difference matter on source-family-disjoint confirmation problems?

The primary manipulation is **resource choice with the scoring rule held constant**. Both policies choose a unique highest mean final-answer accuracy on their respective two-variant selection resource. This operational raw-maximum policy is an explicit abstraction of the prior advice. It does not execute every qualification or significance branch of every earlier response, prove an actual user's choice, or identify a unique causal effect of added clauses.

## Sources and validity gate

Use public source data only: Apple GSM-Symbolic P1 and P2, instance 0, and GSM-Plus v1 numerical-substitution and problem-understanding variants. A source family is the shared original GSM8K question, linked by the frozen source-only normalization/matching receipt. The parent data preparation identified 50 candidate families with all four variants. GSM-Plus describes problem understanding as rewording/sentence-structure variation without changing the solution; its category label alone is insufficient for row-level validation.

Order all 50 candidate families by SHA256 of `2026111391|` plus `source_family_id`, breaking ties by family ID. Ranks 1–16 occupy selection slots, ranks 17–32 confirmation slots; ranks 33–50 are reserves. Before inference, independently review source texts and published gold values for the first 32 families. Validate that the numerical and rewording variants preserve the intended arithmetic computation structure, that rewording does not add/remove an operative constraint, that the numerical variant's gold corresponds to its changed quantities, and that all four final gold values can be independently derived. Preserve genuine uncertainty.

Reject an invalid or unresolved **whole family** without rewriting its questions or source gold. Replace failed slots in ascending slot order using the next source-valid reserve family in the fixed rank order. Keep rejected source records, first review dispositions, reasons and replacement provenance. Never use model accuracy to exclude or replace data. Freeze the final 32-family allocation, source bytes/revisions/hashes, task keys, validation record and all runtime/analysis files before solver inference. If the reserve pool cannot produce 32 approved families, stop this protocol without inference and prepare an explicitly new design. Human semantic/gold validation remains distinct from first agent review and must not be claimed if not performed.

The target consists of **two marginal perturbation conditions** per original family: numerical substitution and harmless rewording. It does not test a single item with both changes composed simultaneously. P1/P2 and target variants come from two released resources, so style, quantities and annotation processes can differ in addition to clause structure. The estimated resource-package consequence cannot isolate a pure added-clause effect.

All sources are public, and solver pretraining exposure is unknown. This is a conditional evaluation of these archived problems, not an uncontaminated-capability or training-data-absence test. Distinct original question IDs also do not prove independent linguistic or computational templates.

## Fixed candidates, inputs and budget

Candidates are `gemma-4-31b-it` and `deepseek-v4-flash`. These two requested aliases were chosen before math performance because both completed all nine requests in the prior source-repair study. This is operational selection, not evidence of relative math ability. Provider aliases do not prove immutable weights; retain returned model metadata.

There are 32 families × 4 variants × 2 candidates = **256 classifications**. Each request contains four unrelated source families of one variant type and one split, giving **64 requests**, 32 per candidate. Never put related variants from the same family in one request; never mix selection and confirmation. A common four-family block partition within each split is used across all four variant types and both candidates, yielding four co-batch blocks per split. The runtime receipt fixes block membership, task order and request randomization before inference.

Only opaque task IDs and authentic question text are model-facing. Do not send benchmark names, variant labels, split/family metadata, reference solutions, gold answers, selection policies or the study hypothesis. Use the same frozen common instruction and decoding settings for both candidates; exact prompt/payload bytes and their hashes are frozen by the runtime. The planned output cap is 8192 tokens/request, at most **524,288 requested output tokens** plus input. Use native SSE, fresh context, no tools/memory/history/storage, concurrency two, one client attempt per row, and no repair/retry calls. Document socket and CI wall-clock timeouts separately. Costs are provider usage receipts, not an invented monetary cap.

Require final JSON covering every expected ID exactly once, with numeric answers or explicit `ABSTAIN`. Normalize numeric equality using an exact rational/decimal parser fixed before outputs; do not use permissive last-number extraction from arbitrary prose. `ABSTAIN` is an observed incorrect answer. Malformed/incomplete captures and unparseable outputs are operational unknowns with [0,1] correctness bounds, not silently wrong answers or substituted candidates. Preserve every raw sanitized artifact, SSE journal, incomplete, failure and format deviation. No model is dropped after a failure.

## Scores, selectors and confirmation

For family f and model m, define the **bad-resource** score as `(correct(P1)+correct(P2))/2`, and the **target-resource** score as `(correct(numerical)+correct(rewording))/2`. Each is in {0, 0.5, 1}; average equally across the 16 selection families. This identical score rule holds metric choice constant while changing the resource.

Each selection policy chooses the unique higher model score. Exact ties remain ties; no arbitrary tie-break. With unknown outputs, declare a winner only if its conservative lower score bound exceeds the other model's upper bound. Overlap means indeterminate selection, not a tie or successful reversal. Report both point scores where fully observed and all conservative bounds. A strict selection reversal requires two determinate, different winners.

The primary confirmation contrast, when both selection winners are determinate, is:

`target accuracy on 16 confirmation families of target-selected model minus target accuracy of bad-resource-selected model`.

Keep the selected winners fixed for confirmation. If they are the same model, the contrast is exactly zero by identity, including under missingness; do not independently extremize the same predictions into a spurious interval. If the winners differ, compute paired family differences and conservative contrast bounds. If either selector is tied/indeterminate, the selected-winner contrast is null; still report all fixed candidate scores and failures.

Secondary endpoints are separate numerical/rewording accuracies and their paired differences; joint correctness of both target variants per family; and selection-score margins. The joint score is 0 when any observed target answer is wrong, 1 when both are observed correct, and [0,1] otherwise. Do not label a model uniformly better on both target capabilities if the category contrasts trade off. The weighted mean measures only the declared equal-weight resource-choice policy.

## Uncertainty and stopping

Report deterministic missingness/format/gold-uncertainty bounds first. Do not impute unknowns as wrong for the primary comparison. For complete fixed-winner confirmation data, use 10,000 paired family bootstrap draws and a separately reported common co-batch-block bootstrap, retaining all model/category outcomes together. With missing outcomes, bootstrap lower and upper paired-difference arrays and report the envelope [2.5th percentile of lower-bound draws, 97.5th percentile of upper-bound draws], alongside the deterministic full-cohort bounds; do not fabricate an unknown-outcome point estimate. The machine protocol fixes the RNG seed before inference.

The family bootstrap has only 16 confirmation families; the co-batch bootstrap has **four blocks** and is fragile. These are conditional descriptive sensitivity intervals, not calibrated population guarantees. Preserve zero, negative, tied and inconclusive results. No independent-family or source-population generalization is established by the grouping rule.

Run all 64 frozen requests once, without success stopping or adaptive candidates/items. A completed run without strict reversal is a null for this choice mechanism. A reversal without positive independent target confirmation is selection instability, not demonstrated benefit/harm. A positive confirmation point contrast with bounds or interval crossing zero is a pilot signal requiring fresh confirmation. A positive result that survives both uncertainty analyses and conservative missingness remains conditional on this selected case, candidates, resources and decoding setup. Any later expansion is a newly named cohort; do not pool it into a retrospective success claim.

## Reporting

Publish exact source/review/allocation pins, every attempted output, parser/capture checks, per-family scores, both selection decisions, fixed-winner confirmation, category tradeoffs, uncertainty, all first/source-review disagreements and nulls. State separately: source mismatch verified; AI advice recurrence observed in the earlier study; operational selection reversal observed or absent here; independent target consequence observed or absent here. The combination does not by itself demonstrate actual adoption, general recommendation-error prevalence, internal model reasoning, training-data absence, or a GAMMAF-level effect.
