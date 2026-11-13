# Math consequence pilot: same model choice, exploratory distortion in the performance gap

The frozen primary test did **not** show a model-choice reversal. Both the P1/P2 policy and the policy aligned with numerical substitution and paraphrasing selected `deepseek-v4-flash` over `gemma-4-31b-it`. Their selected-model accuracy difference on the confirmation target is exactly **0 percentage points**, because both policies selected the same model. This remains true under every assignment of the retained unknown scores.

An additional contrast, chosen **after** inspecting the primary results, shows a larger apparent DeepSeek–Gemma performance gap on P1/P2 than on the target-aligned items. This is an exploratory observation about the evaluation packages in this fixed cohort. It is not a successful primary endpoint or a confirmatory finding.

## What was frozen and executed

The original exact-32-family source gate failed before any solver call. Two independent agent reviewers assessed all 50 linked source families and their four variants. Only **30 families passed both first reviews**. A separate 30-family study used all double-pass families in the existing source priority order, without overriding uncertain reviews or editing source questions or answers. Its split was 15 families for selection and 15 for confirmation. The exclusions include construct-fit and wording concerns; **20 exclusions do not mean 20 proven wrong answers**. Three direct arithmetic source contradictions are documented separately in [SOURCE_AUDIT.md](SOURCE_AUDIT.md).

Each family contributes four released variants: a GSM-Plus numerical substitution, a separate GSM-Plus paraphrase, Apple GSM-Symbolic P1 and P2. The target construct is correctness under numerical substitution and paraphrasing, assessed as the mean of those two separate variants. This does not test a composition of both transformations in one item. The alternative policy uses the mean of P1/P2 instead. P1/P2 may be appropriate for another construct; their mismatch here is relative to this declared target.

The models were fixed before mathematical performance was observed, using operational completeness in the previous advice pilot. Each request contained three unrelated families of the same variant and split. Both models received identical blocks. Five co-batch blocks occur in each split. No retries or replacement candidates were allowed.

- Source, cohort, protocol and analysis freeze: [`0408bd25c49f31ab1c7563747d92ac61217692a7`](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/0408bd25c49f31ab1c7563747d92ac61217692a7), 2026-11-13 18:05:24 UTC.
- Execution commit: [`13930853871b890a8e4a599a262b1260fbe83000`](https://github.com/ricardofitas/swarm-adaption-hackathon/commit/13930853871b890a8e4a599a262b1260fbe83000), 18:06:39 UTC.
- Successful [run 43479393991](https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43479393991): **2 format-admission requests + 80 main requests**, each attempted once. The admission gate checked format only, never arithmetic correctness, and passed before all main calls began.
- Original CI artifact: 1,743,620 bytes, SHA256 `03dcd28542fd8edb511e939811ac2a8038f94655c052d0c8d357a8b6e048b344`.

Full identifiers, digests and audit scope are recorded in [EXECUTION_RECEIPT.json](EXECUTION_RECEIPT.json). The frozen [protocol.json](protocol.json) and [prospective_design30.md](prospective_design30.md) remain unchanged.

## Capture and the primary result

All 80 main requests completed their native SSE capture. Of 240 intended item answers, **226 have known correctness: 168 correct and 58 wrong**. Four whole-batch JSON failures leave 12 unknowns; two percentage-formatted answer strings leave two more under the frozen numeric parser. No format repair was applied after seeing results. Every unknown retains correctness in `[0,1]` rather than being counted as wrong.

The following are fixed-cohort accuracy bounds, **not confidence intervals**. Each resource mean covers 30 task answers, or two answers per family.

| Split | Evaluation package | Gemma | DeepSeek |
|---|---|---:|---:|
| Selection | P1/P2 | 23.33–33.33% | 100% |
| Selection | Numerical substitution/paraphrase | 90% | 100% |
| Confirmation | P1/P2 | 10.00–23.33% | 86.67–96.67% |
| Confirmation | Numerical substitution/paraphrase | 50.00–63.33% | 100% |

The P1/P2 selection bounds strictly separate DeepSeek from Gemma; the target-aligned selection has a complete, unique DeepSeek maximum. Both policies therefore make the same robust choice. Their primary confirmation contrast is `[0,0]`, including the registered family and co-batch-block bootstrap summaries. This is a same-model identity, not evidence that the evaluation packages are equivalent. The secondary requirement that both target variants be correct also gives the same selected-model contrast of zero.

## Exploratory contrast selected after the results

Define the gap as DeepSeek accuracy minus Gemma accuracy. Define distortion as the P1/P2 gap minus the numerical-substitution/paraphrase gap. These are comparisons of model differences, not simply the difference in difficulty between resources.

| Split | DeepSeek–Gemma gap on P1/P2 | Gap on target-aligned items | Gap distortion |
|---|---:|---:|---:|
| Selection | 66.67–76.67 pp | 10.00 pp | **56.67–66.67 pp** |
| Confirmation | 63.33–86.67 pp | 36.67–50.00 pp | **13.33–50.00 pp** |

The distortion bounds were independently rederived from family-level task bounds. They are sharp under the registered independent `[0,1]` uncertainty boxes for unknown task correctness. Thus even assigning every unknown in the direction that minimizes distortion leaves a positive descriptive difference in this cohort. This does **not** make the post-hoc metric confirmatory: the confirmation split was protected for the original choice-consequence endpoint, not for an endpoint introduced after inspecting both splits.

The derivation is executable in [analyze_posthoc_gap.py](analyze_posthoc_gap.py), with exact rational outputs in [posthoc_gap_distortion.json](posthoc_gap_distortion.json). It does not alter [analysis/summary.json](analysis/summary.json), the frozen primary analysis.

## Audit, limits and next decision

A separate agent audited 17 source/protocol/implementation blobs against both remote commit trees, all 82 capture journals, admission-before-main timing, exact payload/question correspondence, the rational scoring replay, the source split and both primary and exploratory arithmetic. No discrepancy was found. This is independent agent review, not external human certification.

The 30 families are a restricted, source-screened intersection of public resources, not a random sample of all GSM8K tasks. The solver aliases do not establish immutable weight snapshots, and public pretraining exposure is unknown. Co-batching can create dependence; there are only five blocks per split. The packages differ in wording, values and style as well as added reasoning requirements, so the results do not isolate a causal effect of added clauses. Format uncertainty and source-review error remain possible. No benchmark-wide error prevalence, novelty claim or general model ranking is established.

The useful research direction is now narrower: **a benchmark mismatch can exaggerate the apparent size of a model advantage even when it preserves the winner**. This pilot supplies exploratory evidence for that claim, while its original choice-consequence test is negative. It does not yet justify a GAMMAF-level impact claim.

The next study should freeze gap distortion as its primary endpoint before collecting outputs on new source families, use an independently reviewed cohort with explicit exclusions, preserve missing-score bounds, and then test another model pair and benchmark family. A matched transformation design would be needed to attribute the distortion specifically to extra reasoning clauses. Adding models adaptively to this completed study would be a new exploratory analysis, not a rescue of its primary endpoint.
