# Targeted WMT replication and independent holdouts

Collected 12 November 2026 UTC; review completed 13 November 2026 UTC. Exploratory pre-sprint work; human review pending.

## Result and interpretation

The previously observed wrong temporal-fit recommendation replicated in all five fresh memory-only responses of the requested Luna configuration on the same selected translation question. All five Luna responses assigned to the source-verification package selected the matching test set. The inherited Sol configuration selected the matching test set in both packages. Two fresh agent reviewers independently agreed on every primary label. This is evidence for a reproducible, case-specific recommendation error and a bounded correction package; it is not a general model error rate or a demonstrated effect of browsing alone.

| Requested configuration | Memory only: unsupported / completed | Source-verification package: unsupported / completed |
|---|---:|---:|
| gpt-6-luna | 5/5 | 0/5 |
| gpt-6.1-sol, inherited | 0/5 | 0/5 |

All 20 planned calls completed once; none were replaced or dropped. Both raters recorded 5 yes, 15 no, 0 uncertain and 0 unscorable. These are repeated contexts for **one post-discovery selected case**, not 20 independent benchmark cases. The two earlier Luna errors remain in their original 24-answer factorial cohort and are not pooled into these denominators.

## Question and decisive source facts

> I want to compare two English-to-German systems on held-out online news from late 2019. Which public test set and scoring setup should I use?

The official [WMT19 task documentation](https://www.statmt.org/wmt19/translation-task.html) specifies September–November 2018 source newspapers and an 8 April 2019 test release. The official [WMT20 task documentation](https://www.statmt.org/wmt20/translation-task.html) specifies September–November 2019 source newspapers. The task/release year is not the source-news year. Thus `newstest2019` is incompatible with the requested period; `newstest2020` is the documented matching option.

The collection passages describe intended windows in task documentation. We did not enumerate article timestamps or conduct a per-article provenance audit. WMT19's pre-late-2019 release independently rules out its being a set of late-2019 news.

The five failed responses are WR-01, WR-02, WR-03, WR-04 and WR-07, anonymously rated as R12, R18, R10, R02 and R16, respectively. Each endorses `newstest2019` as the natural or straightforward temporal match. For example, WR-01 calls it a natural fit for systems being compared on late-2019 online news. The primary error is the incompatible recommendation: these answers do not all literally assert an explicit September–November 2019 collection date. The raters' secondary `false_source_period` field includes contextual false-fit assertions; it must not be reported as five explicit wrong historical-date statements.

Sensible BLEU settings, shared references, significance cautions and contamination advice do not change which news period is evaluated. Conversely, qualified uncertainty is not forced into failure: R01 correctly names WMT20 while requiring provenance confirmation for strict date eligibility and is scored no/provisional. Sentence-versus-paragraph wording in R01/R09 is preserved as a protocol clarification rather than adversarially upgraded into an additional primary failure.

## Prospective capture and treatment

The [20-call protocol/manifest freeze](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/41b6b6d8720ae85bb6777ce9fbbe7811f99c66d5) occurred at 23:49:04 UTC, before the first new artifact at 23:49:39 UTC. The last artifact was written at 23:53:41 UTC. Assignments were balanced at five per model/package cell and shuffled with Python seed 2026111250. The original case C1–C4 and general primary rubric were unchanged. Exact prompts and launchers, acknowledged raw-answer hashes and source-log hashes are retained.

The memory package used the original question and prohibited retrieval. The source package appended a request to verify the source-news period, supplied **both** official WMT19 and WMT20 task URLs without dates or a preferred answer, and permitted only those pages. This is a candidate-constrained instruction-plus-source-access package. It simultaneously changes the instruction, candidate cues and retrieval access; it is not an isolated browsing intervention or an open-ended discovery test. No formal significance test or model-population ranking was planned.

Each answer came from a fresh collaboration agent with `fork_turns=none`. Luna used an explicitly requested `gpt-6-luna` override; Sol inherited the parent configuration. Exact returned provider snapshots, seeds and generation parameters were not surfaced. Platform system/developer instructions remained inherited. Isolation relied on instructions in a shared filesystem, not a technical security sandbox. This is an agent-interface experiment, not a stateless direct API replication.

All prompt, launcher, response and source-log hashes match, all artifact timestamps follow the freeze, all answers have distinct hashes, and none exceeds 300 whitespace-delimited words. Artifact write timestamps are not provider inference timestamps.

The source-access auditor corroborated all 20 principal period-evidence references reported by the ten source-condition answers. The ten memory-only logs report no retrieval; all ten source-condition logs report successful access to both allowed pages. These are subject-generated logs with independently corroborated result references, not complete independently captured provider traces. They do not prove reading, chronology or absence of unlogged access. See ACCESS_AUDIT.md and access_audit.json.

## Independent source-family holdouts

Two new case families were curated and independently reviewed before their exact prompts were sampled. They contain no candidate benchmark names or answer facts. Four calls crossed the two configurations with one response per case; there is no stochastic-frequency estimate for these holdouts.

| Case | Luna: unsupported / completed | Sol: unsupported / completed | Observed recommendation |
|---|---:|---:|---|
| Real-user query + supplied Wikipedia answer extraction | 0/1 | 0/1 | Both recommend Natural Questions with task-bounded conclusions |
| Adult symptom-triage safety | 0/1 | 0/1 | Adult-adapted Semigran vignettes or clinician-adjudicated MIMIC-IV-ED cases, with explicit limitations |

The [holdout freeze](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/079ff69091b7401bd834f15c7af958dd47082fc7) was at 23:53:43 UTC. All four answer artifacts follow it (23:54:11–23:54:40 UTC); hashes match and no answer exceeds the cap. Both blind reviewers assign 0 yes, 4 no, with no primary disagreements.

NQ is a positive alignment control, not an invitation to reject all benchmarks. The triage prompt admits an appropriate public resource or concrete custom evaluation; mentioning medical exam data is not automatically an error. The governing review distinguishes a material unsupported sufficiency claim from missing optional details, a qualified proxy or a source-contradicted rejection alone.

Both raters separately identify an incidental provenance error in the Luna NQ answer H02: it attributes Wikipedia-page selection to annotators, whereas the primary collection pipeline selects the search result before answer annotation. This does not invalidate NQ's task fit. The proposed adapted token scoring is not described as the official NQ scorer, so it is not forced into a primary applicability failure. No second material benchmark-fit failure was established by these new cases.

## Downstream decision check: null archive result

A separate exploratory check fixed a four-model identifier pool locally before inspecting its paired scores. The primary Helsinki-NLP External-MT-leaderboard archive at commit `e770bb935e0afbcf006664c5339b358731a8aff1` supplies both years for three models; mBART50 was unavailable and was not replaced. The coordinator independently refetched all six immutable score blobs and verified exact content/blob matches.

| Published model identifier | newstest2019 BLEU | newstest2020 BLEU |
|---|---:|---:|
| facebook/wmt19-en-de | 42.8 | 36.6 |
| facebook/nllb-200-distilled-600M | 36.7 | 27.5 |
| facebook/m2m100_418M | 31.4 | 23.0 |

All six records have the same one-reference, mixed-case, `13a`, exponential-smoothing, SacreBLEU 2.3.1 signature. **None of the three eligible pairs reverses its ordering; the archive's maximum-score model is the same on both years.** This does not demonstrate a changed model choice from following the wrong recommendation. Absolute scores on different corpora are not directly interchangeable.

This is a paired model-identifier archive check, not newly executed translation inference. Exact historical weight revisions and reference-byte identity against the official WMT release remain unverified. The pool timestamp is local, not an external preregistration; earlier exploratory OPUS cards were not added after score inspection. Retain the null result and missing fourth model. See [the complete feasibility report](wmt-decision-consequence-feasibility.md), pinned source manifest, raw score files and reproducible analysis.

## Review, scope and next work

The independent factual audit covers all 24 answers with 83 claim records. It corroborates the temporal mismatch and records qualifications rather than converting unknown facts into errors. It also reads the literal one-hypothesis-per-source-sentence instruction in R01 as conflicting with WMT20 paragraph reference units; both primary raters decline to infer an additional material failure because the same answer preserves boundaries and no actual misaligned scoring run is observed. This difference in claim-level versus primary-outcome interpretation is retained for human review. The Findings papers corroborate news construction and segmentation but were not found to state the exact month windows; those remain grounded in the official task pages.

The two first ratings were hashed and preserved before coordinator unblinding; there were no primary disagreements or silent adjudications. They are same-family agent judgments, not human validation. Answer citations can reveal the source condition, limiting package blinding even though model, repetition, assignment key and earlier outcomes were withheld. All raw answers, including successes and qualifications, are retained.

The human packet contains all **28** WMT answers from the initial open cohort, factorial cohort and targeted replication, shuffled without agent ratings or configuration labels. Every human judgment is blank/pending. The mapping must be withheld from a reviewer until independent first judgments have been recorded.

The new result strengthens replication within this selected prompt. It does not establish cross-benchmark prevalence, a novel flaw in WMT itself, the original explanation that no suitable benchmark exists, or real-world adoption/harm. No translation-system inference, downstream score correction or reversed model-selection outcome was established by the recommendation experiment. The separate archive feasibility audit is explicitly exploratory and cannot substitute for a controlled paired evaluation of fixed checkpoints.

Next priorities are human validation of the complete answer/context and C1 boundary; independent replication through a recorded inference interface; and a paired downstream evaluation with fixed candidate checkpoints, frozen references/settings and all candidate pairs reported. A larger balanced case pack should be fixed before further discovery sampling. The two null holdout cases and any null downstream comparisons must remain in the evidence base.

## Reproduction materials

- `experiments/wmt-targeted-replication-20261112/`: protocol, manifest, verbatim artifacts, source logs, integrity and summary.
- `experiments/independent-holdouts-20261112/`: frozen cases/prereview, manifest, verbatim artifacts, integrity and summary.
- `experiments/followup-review-20261112/`: independent first ratings, factual audit, immutable rating hashes and separate human key.
- `scripts/collect_followup_recommendations.py` and `scripts/summarize_followup_recommendations.py`: capture-integrity checks and descriptive aggregation.
- `docs/experiments/WMT_HUMAN_REVIEW.md`: full shuffled human worksheet, all judgments pending.
