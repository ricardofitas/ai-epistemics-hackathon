# Prospective P1 replication meets the fixed-cohort gap-distortion criterion

The prespecified primary criterion was met on **30 new source families**. Using two released P1 instances instead of the numerical-substitution/paraphrase target enlarged the apparent DeepSeek–Gemma accuracy gap by **18.33–48.33 percentage points**. These exact bounds retain all 18 unknown answers. The registered criterion required the lower bound to be at least 10 points; the observed lower bound is `11/60`, above `1/10`.

This is a prospective, source-disjoint replication of the **P1 component** of the earlier exploratory observation. It does not repeat the earlier P1/P2 mixture. The result is identified for this fixed cohort; descriptive resampling envelopes include zero, so generalization across other families remains uncertain. Both evaluation packages still favor DeepSeek. The previous null model-choice result remains unchanged.

## Primary result and what was measured

For each family, the comparison score averages P1 instances 0 and 1. The target score averages two separate released items: numerical substitution and a meaning-preserving paraphrase. The primary endpoint is the comparison DeepSeek-minus-Gemma gap minus the corresponding target gap, with equal family weighting. It measures transformed-item accuracy, rather than an invariance score or a baseline-subtracted robustness drop. The two target transformations are separate items, not a composition in one question.

| Evaluation package | Gemma accuracy | DeepSeek accuracy | DeepSeek–Gemma gap |
|---|---:|---:|---:|
| P1 instances 0 and 1 | 21.67–36.67% | 95.00% | 58.33–73.33 pp |
| Numerical substitution/paraphrase | 58.33–73.33% | 98.33% | 25.00–40.00 pp |

Each package contains 60 task answers per model across 30 families. DeepSeek has 57/60 correct on P1 and 59/60 on the target. Gemma has 13 correct plus nine unknown on P1, and 35 correct plus nine unknown on the target. The unknowns give the exact primary interval `[11/60,29/60]`. Its endpoints assign every unknown in the direction that minimizes or maximizes the signed contrast; missing answers are never imputed as wrong. These are **identification bounds, not confidence intervals**.

Both packages have DeepSeek as a robust unique winner under every unknown assignment. Winner changes were secondary descriptions in this study; there is no independent model-selection consequence test here.

## Prospective registration and source admission

The previous pilot introduced gap distortion after seeing its results. This study fixed the model pair, endpoint, direction, 10-point criterion, source priority and missing-score treatment before any new solver response. The deliberately repeated model pair was informed by the earlier pilot; this is not an unbiased discovery of a model pair.

Released P2 covers only the 50 families already reviewed. P1 covers another 50 linked families, each disjoint from that entire earlier pool, including its rejected families. The source order and admission rule were committed at [`5706a87932ff33786f3c8dbdb69d6566532967ce`](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/5706a87932ff33786f3c8dbdb69d6566532967ce), 18:34:18 UTC, before assigning the two fresh source reviewers. Source pins remain Apple `3b645c25d200bf950fb84e8cdcbfeccd91d6a8af` and GSM-Plus v1 `3b708db57b96a16e8e3368ed2956990c0809440e`.

Two independent first-review streams examined all 50 families and 200 variants. **35 families passed both reviews.** The first 30 in the frozen SHA256 priority order were admitted; five eligible families were unused, while 15 failed the reject-or-uncertain admission rule. No uncertain judgment was overridden and no question, gold or first judgment was edited. Exclusion is not synonymous with a proven wrong gold. The source-only [audit](SOURCE_AUDIT.md) separately documents specific arithmetic and semantic witnesses without a novelty or prevalence claim.

The final cohort, exact prompts, parser, capture and analysis implementation were frozen at [`a88095492bed529454db39893a338857ff7afcca`](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/a88095492bed529454db39893a338857ff7afcca), 18:44:32 UTC. All 120 selected questions and source answers were checked against the pinned raw rows. A separate preflight independently reconstructed source admission, verified all 200 candidate source records, and checked all 46 remote study blobs. The full source and code hashes remain in [protocol.json](protocol.json).

## Execution and retained uncertainty

The study made **two format-only admission calls and 80 main calls**, each attempted once. Requests contained one variant on three unrelated families; ten identical family blocks were used across models and variants. No tools, history, model replacement, retries, format repair or output-dependent stopping were used. Admission checked capture and representation, never arithmetic correctness.

An initial CI launch stopped in its history guard before catalogue access or any provider/model request. Its original ZIP and logs prove zero calls. An explicit infrastructure-only amendment validated the current run through its direct metadata endpoint while retaining prior-run rejection. It used a new one-shot execution identity and changed none of the 19 scientific source/implementation pins. The amendment was committed at [`aed0c26c11eb5fcc77635e320eabef84fa9d8227`](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/aed0c26c11eb5fcc77635e320eabef84fa9d8227), 18:57:54 UTC, before any solver output.

The successful execution commit was [`d0b1c6a6c5f2b5734f08003e897dffd3951f4a79`](https://github.com/ricardofitas/swarm-adaption-hackathon/commit/d0b1c6a6c5f2b5734f08003e897dffd3951f4a79), 18:58:23 UTC; [run 43487746459](https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43487746459) completed successfully. Its original artifact SHA256 is `6d6f23e8bb5def0c3e96cacb328f6c5ccb42d1034a81688660543511f88357d0` (2,109,342 bytes).

All 80 main attempts were recorded. **79 captures were strictly complete, and 74 batches had admissible JSON.** Five completed Gemma batches had invalid JSON; one further Gemma batch was provider-incomplete at the fixed 8192-token cap. Their 18 task answers remain unknown. The other 222 answers comprise 164 correct and 58 wrong. DeepSeek has 116 correct and four wrong; Gemma has 48 correct, 54 wrong and 18 unknown. No global capture-integrity issue was found. Successful workflow completion does not imply every model answer completed.

## Sensitivity, scope and next decision

The registered descriptive resampling retained the unknown bounds in every resample:

| Resampling unit | Units | 95% descriptive bound envelope for distortion |
|---|---:|---:|
| Source families | 30 | −1.67 to 63.33 pp |
| Common three-family blocks | 10 | −15.00 to 68.33 pp |

These envelopes include zero. They are conditional sensitivity summaries, not calibrated population intervals or significance tests. The primary fixed-cohort criterion passes, but the apparent effect varies substantially with which families or blocks are represented. Ten blocks and clustered format failures leave generalization fragile.

The cohort is a source-screened intersection of public resources. The same deliberately chosen model pair was repeated; returned aliases do not establish immutable weights, and public pretraining exposure is unknown. Independent agent reviews can share errors; external human validation remains pending. P1 and target items differ in numerical values, wording and style as well as added reasoning requirements, so this does not isolate a causal effect of added clauses or invalidate P1 for its intended construct.

A fresh independent agent replayed all task scores directly from raw terminal outputs using its own exact numeric logic, checked all 82 journals/artifacts, single attempts, admission-before-main timing, source question identity and the 19 frozen source/code pins. It reproduced `[11/60,29/60]` with no discrepancy. See [INDEPENDENT_AUDIT.json](INDEPENDENT_AUDIT.json). This is independent agent review, not external human certification.

The research claim can now advance from an exploratory observation to **a prospective, source-disjoint finite-cohort replication of gap distortion for this pair**. It still does not establish broad generalization, a model-choice reversal or GAMMAF-level impact. The next study should use a separate model pair and another released transformation family with new source families, and prospectively reduce format losses through individual-item requests. Such a format change must be a new study; it must not replace or repair the unknown outcomes in this completed result.
