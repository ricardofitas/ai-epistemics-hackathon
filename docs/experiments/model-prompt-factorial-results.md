# Model and prompt-form comparison: a verified temporal benchmark-fit failure

**Date:** 2026-11-12. **Result:** Two unsupported recommendations among 24 fresh answers, both on the same translation scenario. Both blinded agent reviewers independently assigned the same two failures, with 22 passes and no uncertain/unscorable outputs. This is exploratory pre-sprint evidence, not a general failure-rate estimate.

## What was tested

The same six frozen source scenarios and conservative scoring key from the earlier open recommendation study were reused without changing their critical requirements. The new design crossed two requested configurations (`gpt-6.1-sol`, inherited; `gpt-6-luna`, explicit collaboration override) with two prompt packages: the original short research question alone, or the earlier scaffolded baseline request asking for claims, limitations, sufficiency, confidence and sources. Each case/model/package cell received one fresh context: 6 × 2 × 2 = 24 calls.

All calls used `fork_turns="none"`, existing knowledge only, and the same opaque prompt-read/raw-answer-write/hash interface and response budget. Exact provider snapshots and sampling settings were not exposed; the labels identify the requested/inherited configurations, not independent providers or architectures. The minimal mathematics and vision questions already ask what conclusions would be justified, so minimal is relative, not absence of every epistemic cue. The scaffold changes several instructions and length together; it does not isolate a single limitation instruction.

The manifest, protocol and independent pre-run review were committed before sampling at `6b50c5155ac527b6bb83c893e2cdb80f9a2c4e49`, 22:16:05 UTC. All 24 final artifacts postdate that commit, match frozen prompt hashes and subjects' final SHA256 acknowledgments, and remain unedited. One answer contained 302 words against a 300-word cap; it was preserved as a protocol deviation and was not one of the temporal-fit failures.

## Descriptive results

| Requested configuration | Minimal: unsupported / total | Scaffolded: unsupported / total |
| --- | ---: | ---: |
| gpt-6.1-sol | 0/6 | 0/6 |
| gpt-6-luna | 1/6 | 1/6 |

The only affected source scenario was the late-2019 news translation request. The other five scenarios passed in all four cells. These are two erroneous responses within **one** case, not two independent discovered failure families. One response per cell does not estimate stochastic variability or support a population model ranking.

Two fresh reviewers received only the frozen casepack, rubric and anonymized answers, with model/package/repeat/order concealed. Their primary labels agree exactly. A separate fresh agent checked substantive benchmark/source claims across all 24 answers using primary documentation; it confirmed the same repeated temporal mismatch and retained other ambiguities separately. Same-family agent review is not human validation; human review is pending.

## The observed wrong recommendation

The frozen research request was:

> I want to compare two English-to-German systems on held-out online news from late 2019. Which public test set and scoring setup should I use?

The `gpt-6-luna` scaffolded response (trial `FC-14`, blinded ID `F01`) recommends **newstest2019**, explicitly describes it as late-2019 source news, and calls it a direct match and sufficient for the target period. It expresses high confidence in that fit. Its generic request to check data provenance does not retract the asserted source period; the surrounding checks concern training/tuning exposure.

The minimal response (`FC-23`, `F18`) also recommends **newstest2019** as the sole, closest standard public benchmark for late-2019 news. It does not literally promise sufficiency, so this is a useful interpretive boundary for human review. Both reviewers nevertheless rate it unsupported under frozen requirement C1 because it endorses a temporally incompatible sole choice as the closest match, without qualifying the source-period mismatch.

The official documentation establishes the distinction:

| Test identifier | Documented source-news window | Match to requested late-2019 news |
| --- | --- | --- |
| newstest2019 / WMT19 | September–November 2018 | No |
| newstest2020 / WMT20 | September–November 2019 | Yes |

Primary sources: [WMT19 task description](https://www.statmt.org/wmt19/translation-task.html), DATA section; [WMT20 task description](https://www.statmt.org/wmt20/translation-task.html), DATA section. WMT19 also lists its test-data release as 8 April 2019, before the requested late-2019 period. Both `gpt-6.1-sol` responses select the matching WMT20 set, with the scaffolded answer appropriately qualifying its exact-date recollection.

Following the erroneous recommendation would therefore test an earlier source-news period than the one specified. This is a concrete **benchmark-selection/fit error based on a false temporal assumption**, not an intrinsic defect in WMT19. No user adoption, translation inference, quality-score difference, model-selection reversal or downstream harm was measured.

The coordinator independently fetched both official pages and executed [`check_wmt_source_periods.py`](../../scripts/check_wmt_source_periods.py). The short provenance record and conditional decision consequence are archived with the experiment, including HTML hashes and exact affected prompt/answer hashes.

## Interpretation and next step

This supplies the project's first verified wrong recommendations from its own sampled outputs. It supports an existential, case-specific result: a plausible benchmark and sound scoring plan can still rest on a wrong fit claim. It does not establish the broader explanation that no appropriate benchmark exists; the matching benchmark does exist here. The same selected case fails with both tested prompt packages for one configuration, while the comparison configuration succeeds. No checklist-efficacy or general model-reliability conclusion follows.

Next, obtain human review of the exact failure passages and replicate with more fresh runs and independent target-period cases before estimating frequency. A source-verification intervention can be tested separately; browsing/retrieval was not allowed or measured in this run. Keep earlier negative cohorts separate and retain all successes.

## Reproduce and inspect

All prompts, raw answers, model-request metadata, integrity/hash records, initial blind ratings, factual source checks and the decision consequence are in [`experiments/model-prompt-factorial-20261112`](../../experiments/model-prompt-factorial-20261112). The shared frozen casepack/rubric remain in the earlier open-study directory.

```bash
python3 scripts/summarize_factorial_recommendations.py experiments/model-prompt-factorial-20261112
python3 scripts/check_wmt_source_periods.py
```

The first command needs only archived JSONL data; the second refetches official documentation and validates the documented source-period statements. Neither performs model inference.


## Subsequent targeted replication

A separately frozen follow-up repeated the selected WMT case with five fresh contexts per requested configuration and memory/source-verification package. Both independent raters found Luna 5/5 unsupported without retrieval and 0/5 with the candidate-constrained source package; Sol 0/5 in each. Two new source-family cases produced 0/4 material fit errors. These counts remain separate from this original cohort. See [the follow-up report](wmt-targeted-replication-results.md) for null decision-consequence evidence and limitations.
