# Prospective source-disjoint P1 performance-gap replication

## Question and relation to the preceding pilot

Does using released GSM-Symbolic P1 items instead of the stated target of numerical substitution and meaning-preserving paraphrasing enlarge the apparent accuracy advantage of `deepseek-v4-flash` over `gemma-4-31b-it` by at least 10 percentage points in this new fixed cohort?

The preceding 30-family pilot found no model-choice reversal. Its difference-in-model-gaps contrast was introduced after inspecting results and was exploratory. This study fixes that contrast, its direction, its missing-score treatment and a practical threshold before collecting any new solver output. The model pair is deliberately the same pair that produced the earlier observation. This is a targeted prospective replication, not an unbiased search over model pairs or a general model ranking.

The earlier source pool exhausts the 50 released families with P2 coverage. This study instead uses the **other 50 released Apple P1 families**, each disjoint from all 50 previously reviewed families, and P1 instances 0 and 1. It is a replication of the P1 component on new source families, not a replication of the previous P1/P2 mixture. Two P1 instances vary the released numerical/name realization; they do not constitute two clause levels. P1 and target items differ in other wording and values, so an effect cannot be attributed uniquely to an added reasoning clause.

## Source-only gates, selection and exclusions

The only candidate pool is the intersection of the released GSM-Symbolic/P1 families with GSM-Plus seed questions, excluding every family in the previous 50-family P1/P2 pool. The expected remaining pool is 50 source families. Source files remain pinned to Apple commit `3b645c25d200bf950fb84e8cdcbfeccd91d6a8af` and GSM-Plus revision `3b708db57b96a16e8e3368ed2956990c0809440e`; exact file and row digests must accompany the cohort.

Each candidate contains four unedited released question/gold pairs: GSM-Plus numerical substitution, GSM-Plus problem-understanding paraphrase, Apple P1 instance 0, and Apple P1 instance 1. Numerical substitution and paraphrase are separate items, not a composition of transformations. A source's category label alone is not evidence of semantic validity.

Candidate priority is the ascending hexadecimal SHA256 of UTF-8 `20261113117|SOURCE_FAMILY_ID`, with source-family ID breaking an otherwise equal hash. The candidate order and this admission rule are frozen before source review. Two independent agent reviewers receive source material only, independently derive each answer, and assess construct fit and unambiguous wording. A family passes only if **both first reviews pass all four variants**. Any reject or uncertain judgment excludes the whole family; uncertain judgments are never overridden. Questions, gold answers and first-review judgments are not edited to obtain admission. Agent review is not external human certification.

The cohort is exactly the **first 30 strict double-pass families in the frozen priority order**. If fewer than 30 pass within this finite 50-family pool, the study stops before solver inference. There is no resizing, generated replacement, relaxed review threshold or extension of the pool within this study. Exclusions and reasons remain visible and do not imply that every excluded source contains a proven wrong gold answer. The complete admitted cohort and execution protocol are frozen after source review and before any solver output.

## Fixed execution

All 30 admitted families form a single prospective `replication` cohort. There is no tuning or selection split: neither the models nor the endpoint are chosen from these outputs. Each family has four variants, giving 120 distinct tasks and 240 intended answers across the two fixed models.

The sorted admitted families form 10 fixed blocks of three unrelated families. A request contains one variant for one model on one block; no request contains multiple versions of the same source family. Both models receive identical block membership and item order, and the same blocks are used across all variants. This yields exactly 80 main requests. The common blocks accommodate possible co-batch dependence in descriptive sensitivity analysis.

Before the main requests, one standalone format-admission request per model uses three trivial non-study items. Admission checks exact IDs, complete capture, numeric-string/`ABSTAIN` output and JSON shape, **never mathematical correctness**. If either model fails format admission, no main requests run. Otherwise every planned main request is attempted once; there are no retries, candidate substitutions or output-dependent stops. Main transport or format failures remain unknown scores. A catalogue-availability check is operational and does not supply model performance.

Use the unchanged native-SSE runner, temperature 0, standalone requests without history, no tools, `store=false`, concurrency 2, per-socket timeout 120 seconds and maximum 8192 output tokens per request. The maximum is 82 inference requests and 671,744 requested output tokens, including admission. Returned model aliases do not establish immutable weight snapshots. Freeze the exact payloads, runner, parser, capture helper and analysis implementation before launch.

## Frozen scoring and primary endpoint

Use the strict complete-output parsing and exact rational numeric scoring from the preceding study. An optional single outer code fence may be removed, but extra explanatory text, missing/extra/duplicate IDs or invalid numeric syntax are not repaired after collection. `ABSTAIN` is valid and scores 0. A correct admitted numeric answer scores 1 and an incorrect admitted answer scores 0. Any unscorable answer retains the full correctness interval `[0,1]`; missing is never imputed as wrong. Percentage-formatted strings remain governed by the frozen parser, not retrospective semantic recovery.

For family `f` and model `m`, define:

- `B_fm = (score(P1 instance 0) + score(P1 instance 1)) / 2`.
- `T_fm = (score(numerical substitution) + score(paraphrase)) / 2`.
- `D_f = (B_f,DeepSeek - B_f,Gemma) - (T_f,DeepSeek - T_f,Gemma)`.

The **only primary endpoint** is `D = mean_f D_f` over the 30 admitted families, weighted equally. Positive values mean P1 enlarges DeepSeek's apparent advantage relative to the stated target. This compares differences between models, not merely the absolute difficulty difference between resources.

Report the exact point value if fully identified and the sharp finite-cohort lower and upper bounds under the independent registered correctness boxes for unknown tasks. Compute the bounds with each score's signed coefficient; preserve the coupling when a score appears in more than one derived expression. Here the eight model/variant scores per family are distinct. These are missing-score identification bounds, not confidence intervals or population uncertainty.

The prespecified practical criterion is **meaningful finite-cohort replication if and only if `D_lower >= 1/10`**, equivalent to at least 10 percentage points under every registered unknown-score assignment. Also report whether any positive distortion is identified (`D_lower > 0`) and whether a nonpositive effect is identified (`D_upper <= 0`). A positive but smaller identified effect does not satisfy the meaningful-replication criterion. Bounds crossing zero leave direction unidentified. The effect may be zero or negative; neither a new model nor a changed endpoint can rescue the primary result in this study.

## Secondary descriptions and sensitivity

Report each model's P1 mean, target mean, per-variant accuracy and unknown counts, plus exact gap bounds. Selection/winner differences, if shown, are secondary descriptive metrics only; the study is not a prospective model-selection consequence test. No secondary result changes primary success status.

Use 10,000 conditional bootstrap resamples of the 30 families with seed `20261113118` and 10,000 resamples of the 10 fixed co-batch blocks with seed `20261113119`. Recompute the lower and upper primary bounds in each resample. Report the 2.5th percentile of resampled lower bounds and 97.5th percentile of resampled upper bounds as a descriptive bound envelope; report an ordinary point envelope only if every score required for it is known. Keep fixed block membership and all families in a sampled block together. These sensitivities describe this cohort conditional on the source screening and model pair. Ten blocks are few; neither bootstrap establishes population coverage, a p-value or a significance claim.

## Scope and reporting commitments

Report the source gate and primary endpoint even if they fail. Distinguish a format-admission failure, incomplete main capture, partial score identification, a small/negative distortion and satisfaction of the 10-point criterion. Preserve raw captures, exact payloads, source reviews and all digests. No new solver calls occur after the completed fixed schedule under this study identifier.

The source cohort is a selected intersection of public resources and excludes ambiguous or suspect sources. Public pretraining exposure is unknown. Agent reviewers can share mistakes. Repeating the same models tests a deliberately chosen pair and cannot generalize to all models. P1 instance replication is not new source-family replication within a family. The result concerns evaluation-package effects in these families; it does not prove added-clause causality, dataset-wide error prevalence, novelty, broad benchmark invalidity, a general winner reversal or GAMMAF-level impact. A separate model pair and another released transformation family would require a new prospective study.
