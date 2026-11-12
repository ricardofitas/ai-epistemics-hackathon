# TruthfulQA MC2 underflow: direct prior art and implementation status

Checked 2026-11-12. The finite-log-likelihood underflow cause is **specifically documented prior work**, not merely a generally known numerical phenomenon. Our stress test should be described as a reproduction and a possible known-positive case for evaluating recommendation quality.

## Exact matching prior reports and fixes

| Primary source | Date/status when checked | What it establishes |
| --- | --- | --- |
| [EleutherAI harness PR #4108](https://github.com/EleutherAI/lm-evaluation-harness/pull/4108) | Opened 2026-09-06; open, unmerged | Exact same `process_results_mc2` finite-likelihood underflow; direct exponentiation makes all weights zero; common max shift fixes it. The description includes `[-1000,-1001]` and expected 0.7310585786, 16 regression cases, and a native validation workflow. |
| [Evalchemy issue #154](https://github.com/marin-community/evalchemy/issues/154) | Opened and closed 2026-09-20 | Reports three consecutive real `gpt-oss-20b` runs failing during MC2 normalization via vLLM/OpenAI chat serving. Contains internal Iris run paths, no raw per-choice likelihood vectors. This is external reported incidence, not our independently measured incidence. |
| [Evalchemy PR #157](https://github.com/marin-community/evalchemy/pull/157) | Merged 2026-09-20, commit `9b9093c8495a058d83a9dfeeb096a801870c1783` | Exact max-shifted normalization fix, task override retaining prompt/labels/metric/task name, regression tests and task-resolution check. It closes #154. |

The harness PR is authored by `Anormalm`; Evalchemy issue/fix by `penfever`. This provenance is included for attribution, without inferring identities or relationships to the current team.

## Current status at the checked revisions

The GitHub main-branch API returned harness commit `d6de81643928d653435c431bae19945d41d32520`, matching our stress-test pin. Its [scorer](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/truthfulqa/utils.py) still has `probs = np.exp(ll)` followed by division by the sum; file blob `970a7bee2d0ed3c329e624c42537ff40c6f424a8`. Thus the upstream fix was proposed but not integrated at this observed head.

The [current Evalchemy override](https://github.com/marin-community/evalchemy/blob/main/eval/lm_eval_tasks/truthfulqa/utils.py), blob `b14cff92e76c3d58cc772b2d1943832b891b3bc3`, uses float64 max-shifted probabilities. Its YAML metadata is version 3.1. Calling the defect present in all TruthfulQA implementations would therefore be false.

The previously inspected harness issues [#714](https://github.com/EleutherAI/lm-evaluation-harness/issues/714) and [#1340](https://github.com/EleutherAI/lm-evaluation-harness/issues/1340) report NaN symptoms. In particular, #1340 shows NaN model likelihoods/parameters before scoring. Those issues should remain distinguished from the exact finite-input cause now documented by #4108 and #157.

## Practical boundary

MC2 sums continuation token log-probabilities for each candidate answer, then normalizes across the reference choices. Very negative finite sums are contract-compatible. However, one extremely negative *individual* reference is insufficient to show a materially wrong MC2 score. If another candidate has a much larger likelihood, the discarded tiny term may be immaterial. The relevant per-question diagnostic is the **maximum log-likelihood among its reference choices**, together with original-versus-stable score differences.

The constructed `[-745,-746]` example places all reference mass in the float64 subnormal/zero region. It proves implementation failure but does not establish that ordinary evaluated model distributions often reach that region. Actual trace scans should report the minimum across questions of `max(ll)` and counts near the underflow region, rather than only the minimum likelihood across all individual choices.

The exact proposed fix addresses zero-mass vectors from finite likelihoods. It does not make an all-`-inf` distribution mathematically normalizable. Skipping undefined examples or substituting a score could change the benchmark denominator and must be separately disclosed; that is not equivalent to stable normalization for finite inputs.

## Other directly relevant known benchmark defect

[Lighteval PR #1444](https://github.com/huggingface/lighteval/pull/1444), opened 2026-10-20 and still open/unmerged when checked, addresses a **different** TruthfulQA MC2 problem: the adapter stopped counting gold answers at the first gap in gold indexes. Its example labels `[1,0,1]` with probabilities `[.2,.3,.5]` yielded .2 rather than .7; answer reordering could change the score. This is another documented known-positive scenario. It should not be mixed with numeric underflow, nor claimed as new here.

## Search method and limits

I searched GitHub issues and PRs separately for `truthfulqa underflow`, `truthfulqa logsumexp`, `truthfulqa softmax`, and MC2-related fixes in the harness, original TruthfulQA, and globally. Issue-only queries missed the matching upstream PR. I fetched the matching PR metadata/diffs and the closed Evalchemy issue, then verified current implementation files directly. This establishes exact prior art; no exhaustive claim about the earliest discovery is made.
