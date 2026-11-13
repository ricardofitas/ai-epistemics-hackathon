# Prospective math benchmark-choice consequence pilot: new 30-family cohort

Status: new source-quality-driven design before any solver inference. The original 32-family protocol failed its source gate: only 30 of all 50 candidate families passed both independent first source reviews. Its SOURCE_GATE_FAILURE.json and unchanged proposal are retained, with zero solver requests. No uncertain or rejected family is promoted by coordinator override. This separate 30-family cohort uses all and only the 30 double-pass families. It follows the completed 36-call source-repair advice study; no solver-performance data from either consequence design have been inspected. The original WSC/HANS confirmation data are not reused.

## Question and bounded decision

Can using the recommended added-clause GSM-Symbolic P1/P2 resource to choose between two fixed assistants select a different assistant from a task-matched numerical-substitution/harmless-rewording evaluation, and does that difference matter on source-family-disjoint confirmation problems?

The primary manipulation is **resource choice with the scoring rule held constant**. Both policies choose a unique highest mean final-answer accuracy on their respective two-variant selection resource. This operational raw-maximum policy is an explicit abstraction of the prior advice. It does not execute every qualification or significance branch of every earlier response, prove an actual user's choice, or identify a unique causal effect of added clauses.

## Source-quality selection and preserved original gate failure

Use public source data only: Apple GSM-Symbolic P1 and P2, instance 0, and GSM-Plus v1 numerical-substitution and problem-understanding variants. A source family is the shared original GSM8K question, linked by the frozen source-only normalization/matching receipt. The data preparation identified 50 candidate families with all four variants. GSM-Plus describes problem understanding as rewording/sentence-structure variation without changing the solution; its category label alone was not accepted as row-level validation.

Two independent first source reviewers checked all 50 candidate families, including the 18 reserves from the original design. The first reviewer passed 31, marked 13 uncertain and rejected six; the second passed 35, marked eight uncertain and rejected seven. Their intersection contains **30 families passed by both**. All four published final gold values and the target perturbation semantics were checked with independent arithmetic evidence. Original source questions and golds remain unchanged. This is agent source review, not external human certification.

The original required minimum of 32 could not be met after exhausting the full source pool. It stopped before inference. This new cohort does not rescue that gate by relabelling uncertainties or by replacing gold answers. It is explicitly a new source-quality-selected study, designed before any solver outcomes. Its changed 30-family count and request geometry must be visible in the protocol, runtime, workflow, report and all denominators.

Preserve the original all-50 priority order: sort by SHA256 of `2026111391|` plus `source_family_id`, breaking ties by family ID. Filter this order to all and only the 30 double-pass families. The first 15 occupy selection and the last 15 confirmation. Keep every rejected/uncertain record, both first review files, arithmetic evidence and the original failed-gate record. There are no further replacements or post-performance family additions. Freeze the final allocation, source revisions/bytes/hashes, review records, task keys and all runtime/analysis files before the first format-admission request or solver request.

The target consists of **two marginal perturbation conditions** per original family: numerical substitution and harmless rewording. It does not test a single item with both changes composed simultaneously. P1/P2 and target variants come from two released resources, so style, quantities and annotation processes can differ in addition to clause structure. The estimated resource-package consequence cannot isolate a pure added-clause effect. Passing source validation also selects cleaner items and is not a prevalence estimate over either full dataset.

All sources are public, and solver pretraining exposure is unknown. This is a conditional evaluation of these archived problems, not an uncontaminated-capability or training-data-absence test. Distinct original question IDs do not prove independent linguistic or computational templates. Human semantic/gold review remains pending and is not claimed.

## Fixed candidates, inputs and budget

Candidates are `gemma-4-31b-it` and `deepseek-v4-flash`. These two requested aliases were chosen before math performance because both completed all nine requests in the prior source-repair study. This is operational selection, not evidence of relative math ability. Provider aliases do not prove immutable weights; retain returned model metadata.

There are 30 families × 4 variants × 2 candidates = **240 main-study classifications**. Each main request contains three unrelated source families of one variant type and one split, giving **80 main requests**, 40 per candidate. Two additional format-admission requests, one per candidate with three trivial non-study questions, make **82 maximum requests** and 246 maximum answer records including admission. Never put related variants from the same family in one request; never mix selection and confirmation. A common three-family block partition within each split is used across all four variant types and both candidates, yielding five co-batch blocks per split. The runtime receipt fixes block membership, task order and request randomization before inference.

Only opaque task IDs and authentic question text are model-facing. Do not send benchmark names, variant labels, split/family metadata, reference solutions, gold answers, selection policies or the study hypothesis. Use the same frozen common instruction and decoding settings for both candidates; exact prompt/payload bytes and their hashes are frozen by the runtime. The planned output cap is 8192 tokens/request, at most **671,744 requested output tokens** including the two admission requests, plus input. Use native SSE, fresh context, no tools/memory/history/storage, concurrency two, one client attempt per row, and no repair/retry calls. Document socket and CI wall-clock timeouts separately. Costs are provider usage receipts, not an invented monetary cap.

Require final JSON covering every expected ID exactly once, with numeric answers or explicit `ABSTAIN`. Normalize numeric equality using an exact rational/decimal parser fixed before outputs; do not use permissive last-number extraction from arbitrary prose. `ABSTAIN` is an observed incorrect answer. Malformed/incomplete captures and unparseable outputs are operational unknowns with [0,1] correctness bounds, not silently wrong answers or substituted candidates. Preserve every raw sanitized artifact, SSE journal, incomplete, failure and format deviation. No model is dropped after a failure.

## Prospective format admission

Before the 80 main requests, send exactly one format-admission request per fixed candidate. Each contains the same three trivial arithmetic questions that are not drawn from the study, its source families, selection or confirmation. Admission tests only strict native-SSE capture and the exact requested JSON/ID/numeric-or-ABSTAIN format. **Do not use toy-answer correctness as an admission criterion**, choose a model based on those answers, or treat the six admission answers as study performance.

Both admission attempts must satisfy the frozen operational/format rule before any main request is sent. If either fails, stop the main cohort without retries, repair calls, candidate replacement or changes to the frozen input/parser. Preserve both admission outputs and report the failed gate. If both pass, execute all 80 main requests once under the unchanged plan. Admission must not inspect any study answer or tune a semantic scoring rule. The two admission calls use the same 8192-token cap and are included in the maximum 82-call budget.

## Scores, selectors and confirmation

For family f and model m, define the **bad-resource** score as `(correct(P1)+correct(P2))/2`, and the **target-resource** score as `(correct(numerical)+correct(rewording))/2`. Each is in {0, 0.5, 1}; average equally across the 15 selection families. This identical score rule holds metric choice constant while changing the resource.

Each selection policy chooses the unique higher model score. Exact ties remain ties; no arbitrary tie-break. With unknown outputs, declare a winner only if its conservative lower score bound exceeds the other model's upper bound. Overlap means indeterminate selection, not a tie or successful reversal. Report both point scores where fully observed and all conservative bounds. A strict selection reversal requires two determinate, different winners.

The primary confirmation contrast, when both selection winners are determinate, is:

`target accuracy on 15 confirmation families of target-selected model minus target accuracy of bad-resource-selected model`.

Keep the selected winners fixed for confirmation. If they are the same model, the contrast is exactly zero by identity, including under missingness; do not independently extremize the same predictions into a spurious interval. If the winners differ, compute paired family differences and conservative contrast bounds. If either selector is tied/indeterminate, the selected-winner contrast is null; still report all fixed candidate scores and failures.

Secondary endpoints are separate numerical/rewording accuracies and their paired differences; joint correctness of both target variants per family; and selection-score margins. The joint score is 0 when any observed target answer is wrong, 1 when both are observed correct, and [0,1] otherwise. Do not label a model uniformly better on both target capabilities if the category contrasts trade off. The weighted mean measures only the declared equal-weight resource-choice policy.

## Uncertainty and stopping

Report deterministic missingness/format/gold-uncertainty bounds first. Do not impute unknowns as wrong for the primary comparison. For complete fixed-winner confirmation data, use 10,000 paired family bootstrap draws and a separately reported common co-batch-block bootstrap, retaining all model/category outcomes together. With missing outcomes, bootstrap lower and upper paired-difference arrays and report the envelope [2.5th percentile of lower-bound draws, 97.5th percentile of upper-bound draws], alongside the deterministic full-cohort bounds; do not fabricate an unknown-outcome point estimate. The machine protocol fixes the RNG seed before inference.

The family bootstrap has only 15 confirmation families; the co-batch bootstrap has **five blocks** and is fragile. These are conditional descriptive sensitivity intervals, not calibrated population guarantees. Preserve zero, negative, tied and inconclusive results. No independent-family or source-population generalization is established by the grouping rule.

Run exactly two frozen admission requests once; if both pass, run all 80 frozen main requests once, without success stopping or adaptive candidates/items. If admission fails, report the main study as not executed, not as a completed negative performance result. A completed main run without strict reversal is a null for this choice mechanism. A reversal without positive independent target confirmation is selection instability, not demonstrated benefit/harm. A positive confirmation point contrast with bounds or interval crossing zero is a pilot signal requiring fresh confirmation. A positive result that survives both uncertainty analyses and conservative missingness remains conditional on this selected case, candidates, resources and decoding setup. Any later expansion is a newly named cohort; do not pool it into a retrospective success claim.

## Reporting

Publish exact source/review/allocation pins, every attempted output, parser/capture checks, per-family scores, both selection decisions, fixed-winner confirmation, category tradeoffs, uncertainty, all first/source-review disagreements and nulls. State separately: source mismatch verified; AI advice recurrence observed in the earlier study; operational selection reversal observed or absent here; independent target consequence observed or absent here. The combination does not by itself demonstrate actual adoption, general recommendation-error prevalence, internal model reasoning, training-data absence, or a GAMMAF-level effect.
