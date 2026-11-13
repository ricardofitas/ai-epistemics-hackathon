# Gradual evidence standards for a paper-oriented recommendation study

Status: prospective methodology proposal, prepared 13 November 2026. No new subject responses were sampled by this curator. Human validation remains pending.

The higher bar applies to **the evidence supporting a stronger research claim**. The original recommendation rubric and case-critical requirements remain unchanged. We must not add output requirements after reading responses, treat optional omissions as errors, or redefine failure in order to find more of it. A rare, well-supported observation stays in the record even if it does not satisfy a later recurrence flag.

## Breadth and the next block

The earlier 15-family target was reached. The user's new instruction expands the future discovery goal to **25 source-backed benchmark-centered claim families**. Add six now, reaching 21 if each receives an interpretable final answer; add another four later if they contribute new construct/data/metric/decision coverage and can be reviewed properly. Choose later families for that coverage, not only because a preliminary answer looks adverse. Keep the older coverage snapshot and nulls unchanged.

A family is a distinct scientific-claim evaluation problem anchored in benchmark resources. WMT years/repetitions, paraphrases and incidental alternative names do not add independent families. This is not a count of complete model-performance benchmark executions.

| Next allocation | Cells | Planned client attempts |
|---|---:|---:|
| Six new families, four configurations, one answer per cell | 6 × 4 × 1 | 24 |
| Three selected original-wording cases, four configurations, three fresh contexts | 3 × 4 × 3 | 36 |
| Total | | **60** |

The selected cases are WMT temporal fit, PAWS/NLI sufficiency, and the TREC-COVID nonsignificance/equivalence conclusion. They were selected after discovery. This block is baseline recommendation sampling only: it does not include a source intervention or the six unused wording probes. Freeze the final exact payload manifest, source keys, controls/transport, ordering, stopping and hashes before sampling. Retain each attempted row once, including timeout/error/incomplete/empty captures; never replace them silently or use them as substantive recommendation errors. The root's final protocol governs the exact backend controls.

## Evidence ladder

These thresholds are **descriptive prioritization heuristics**, not significance tests, universal publication standards, or guarantees of a stable error rate. All numerator/denominator details and all four labels—yes, no, uncertain, unscorable—remain visible.

| Stage | Gradually stronger evidence | Claim permitted |
|---|---|---|
| S0: screened observation | One material unsupported endorsement under a frozen case/rubric, exact answer retained, decisive primary evidence or explicit logical warrant, independent first reviews and transparent scope handling | A recorded configuration/context produced this case-specific advice error |
| S1a: initial replication signal | Three fresh prespecified contexts in a case/configuration cell; at least two yes among three complete/scorable answers | Recurrence under the original wording in this small selected cell |
| S1b: five-context characterization | A separately frozen two-context extension reaches five; a 3/5 complete-answer pattern may be flagged as frequent within that cell | Exact repeated-context counts and variability; not a population failure rate |
| S2a: observed wording transfer | Independently fidelity-reviewed, prospectively unused wording probes; the error appears on original wording and at least one probe in a case/configuration | The mismatch was observed under more than one equivalent wording for this selected case |
| S2b: within-case wording recurrence | A separately frozen repeated-probe block; at least 2/3 complete/scorable yes outcomes for each of two probes in a prespecified cell | Recurrence across those two wordings within the selected case |
| S3: decision consequence tested | Fixed actual candidates or immutable outputs, pinned data/reference/scoring/adapters and selection/tie rules; separate target holdout; every eligible candidate reported | A measured consequence for the stated candidates and target, or an honest null |
| S4: paper-ready claim scope | Human/source review, related-work/novelty check, reproducible complete artifacts and claims limited to stages actually reached | A defensible narrow paper claim, with explicit remaining limitations |

A cell with fewer than three scorable answers cannot receive the S1a three-complete-context flag. A cell with fewer than five cannot receive the S1b five-complete-context flag. Still report whatever occurred: for example, two yes, zero no and one unscorable among three attempted calls. Do not hide those observations or describe a transport failure as model uncertainty. A one-off error or a 1/5 result is retained even if it is not prioritized by the heuristic recurrence threshold.

The five-context extension must fix two additional requests before seeing their answers; it cannot stop once a desired error count appears. The same principle applies at every stage. Prefer extending all 12 original selected-case/configuration cells by exactly two requests each regardless of their first-three outcomes: **24 additional attempts**, outside the current 60. If a resource-limited extension instead selects cells using earlier outcomes, declare that adaptive rule, retain the original and extension counts separately, and do not treat freezing later payloads as removal of post-selection bias. New criteria or a new target requirement constitute an explicitly versioned amendment, not a harmless paraphrase.

## Wording transfer is a separate later test

`heldout_paraphrases.json` contains **two unused paraphrases for each of the three selected prompts**, six probes in total. They preserve the original scientific target and critical requirements, supply no candidate names or answer facts, and add no explicit equivalence-testing hint to the retrieval prompt. Only each `prompt` string, plus the same common response instruction/controls for its declared arm, is model-facing; the case names, mechanism annotations, original keys and this metadata are evaluator-only.

These are held-out wordings of already selected problems, not three new unseen scientific problems. They add **zero** benchmark families. They have not been sampled or independently fidelity-reviewed yet; freeze the exact texts and obtain that review before a transfer claim.

A one-shot transfer screen across all four configurations would be 3 cases × 2 probes × 4 configurations = **24 additional attempts**, outside the current 60. It can reveal observed transfer, not a stochastic robustness rate. If all probes are subsequently repeated three times, the full block would be **72 additional attempts**. A smaller extension must predefine its selected cells and rationale before new outputs. Retain every probe and never report just the one that failed.

## Sources and consequences

A balanced, verified primary-source card is a distinct evidence/instruction package. It can test whether accessible task/label/scoring facts correct advice. It is not proof of autonomous retrieval, and any effect cannot automatically be attributed to browsing alone. A genuine retrieval arm needs recorded access evidence and a separately specified tool policy. Do not include a gold-answer label or only the preferred candidate in a supposed balanced source package.

For a consequence test, freeze the actual comparison before scoring: candidates/checkpoints or immutable published outputs; label adapter; corpus/reference bytes; target criterion; selection/tie rule; and an independent target holdout. Compare the selected candidates under recommended and corrected protocols, reporting target-score differences and uncertainty. A changed choice must be measured; a synthetic illustration does not qualify. No change is a valid result and must not trigger a search for arbitrary pairs until a reversal appears. Real user adoption/harm requires its own prospective user study.

An actual ranking reversal is necessary for a **ranking-reversal claim**, not for every possible publishable paper. A paper can instead make a narrow, replicated recommendation-audit contribution and report consequence tests that are null or incomplete. Neither a new recommendation error nor a misuse of a valid benchmark proves an intrinsic benchmark defect or first-ever failure mechanism.

## Human and novelty review

Human review should cover case definitions, every material failure used in a paper, disputed scopes, and a prespecified sample of correct/qualified responses. Keep first human judgments separate from automated labels and any later adjudication. One human's review establishes that review scope, not inter-human reliability; describing such reliability requires at least two independent humans on a declared subset. Reversible experiments can continue while human review is pending. Do not convert this requirement into an unnecessary permission stop, or call agent review human validation.

A current primary-source related-work check must distinguish a new observed advice instance, a replicated known misconception, a new method and an actual previously unknown benchmark defect. Claim novelty only at the level the evidence establishes. Record exact available model aliases/settings and missing immutable-checkpoint information, and separate earlier preparation from event-day work.

## Historical results are preserved

- WMT has earlier repeated original-wording evidence for one configuration and native-API observations under another interface; those cohorts are not pooled into one sampling experiment.
- PAWS/NLI currently has one observed API advice instance and source/mechanism checks, with no stochastic replication or measured choice reversal.
- The statistical-equivalence case has one observed advice instance, an original reviewer disagreement and a separate scope disposition; it is not yet repeated.
- The MMLU scope issue remains uncertain, and the three-translator archive comparison remains a null result with provenance gaps.

The ladder does not retroactively regrade any of those answer labels or relabel their exploratory sampling as confirmatory. It sets prospective support levels for future, explicitly scoped claims.
