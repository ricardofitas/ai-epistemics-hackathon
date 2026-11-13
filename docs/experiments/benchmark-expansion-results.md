# Five-family benchmark recommendation expansion

Collected 13 November 2026, 03:28:41–03:32:55 UTC. Event-day exploratory work; exact public kickoff hour was not verified. Human review pending.

## Coverage and target

The pilot inventory now contains **15 source-backed benchmark-centered research-claim families**, up from ten. The five additions each have at least three complete assistant answers. The preferred pilot breadth target is 15 families, with 12 well-reviewed families as a minimum. The next priority is replication and correction/decision validation on selected cases.

This unit is a benchmark-centered recommendation case family. It is not a count of fully executed model-performance benchmarks or every resource name appearing in an answer. HumanEval/EvalPlus alternatives share one family; repeated WMT years/calls share one; the earlier adult-triage case contains Semigran/MIMIC recommendations and is not counted as a MedQA recommendation experiment. HANS previously had a source/score audit; this is its first recommendation pilot.

| Added family | Explicit evaluation target | Calls | Complete answers |
|---|---|---:|---:|
| BBQ / free-text stereotyping | Unsupported stereotype assumptions under insufficient evidence | 4 | 3 |
| BEIR / TREC-COVID | Expert-judged relevance of the first ten retrieved papers | 4 | 4 |
| HANS / role-sensitive NLI | Who did what to whom in directional entailment | 4 | 3 |
| MMLU / confidence calibration | Reported answer probabilities versus correctness, with held-out fitting subjects | 4 | 4 |
| WebArena / functional web agents | Actual task completion in hostable/resettable sites | 4 | 3 |

Across all earlier and new cohorts, the archive contains **119 complete recommendation answers in 126 captures**, including seven empty operational captures. These inventory totals span heterogeneous experiments and are not a pooled error-rate denominator. `curation/inventory.json` preserves the pre-block snapshot; `coverage-after.json` records the new inventory.

## Protocol and capture

The five ordinary prompts and 19 case-critical criteria were independently source-checked before sampling. No candidate resource names, source cards, answer facts or hidden criteria were transmitted to subjects. Three cases are clear positive controls; the BBQ and MMLU cases admit valid direct adaptations and qualified proxies. Valid alternatives are accepted rather than forcing the curator's benchmark name.

The [freeze commit](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/2418e52d237ff835e83b1277a6144364b0f944a4) was at 03:28:34 UTC, before every new inference request. Twenty native Adaption calls crossed five cases with one representative each from four previously operational model families: `gemma-4-31b-it`, `glm-5.2`, `qwen3.8-27b`, `deepseek-v4-flash`. Selection was declared before reading these outputs; it is not a random sample of all models.

All requests used the same 8,192 generated-token cap, temperature 0.7, common 180–240-word target/300-word ceiling, no tools, no agentic memory, `store=false`, and no conversation history. Concurrency was two; the 120-second timeout is per socket operation, not a hard wall-clock limit. The common cap includes reasoning tokens. API aliases and returned names do not establish exact immutable weights.

All twenty planned client attempts are retained: **17 HTTP-200 complete final answers and three HTTP-504 empty captures**. All three timeouts occurred in the requested GLM 5.2 configuration; its two other calls completed. No client retry or replacement occurred. No final answer exceeded 300 words. Frozen-payload hashes, final-text hashes, individual raw artifacts versus aggregate, and request-start-after-freeze checks all pass. The reported successful-response usage-cost sum is 0.04240417952; missing timeout cost and final wallet debit are unknown, and no USD conversion or remaining balance is asserted.

## Outcome and review transparency

Two fresh reviewers scored the shuffled packet without model identities, manifest, key, usage or other ratings. Their immutable first results differ:

| First reviewer | Yes | No | Uncertain | Unscorable |
|---|---:|---:|---:|---:|
| A | 1 | 14 | 2 | 3 |
| B | 3 | 14 | 0 | 3 |

They disagree on X02, X08 and X15. An additional reviewer, blind to identities and first judgments, assessed those scopes against the unchanged rubric. A separate independent factual audit checked primary sources and unfamiliar recommendations. The coordinator retains first ratings and explicitly adopts the additional scope dispositions: X02 no, X08 uncertain, X15 yes. The scope decisions were recorded before opening the answer-to-model key. This is agent adjudication, not human validation.

Final coordinator synthesis is **two material unsupported recommendations, fourteen no-primary-failure answers, one unresolved scope case and three unscorable captures**. These are descriptive observations on five curated cases, one answer per configuration/case; they do not estimate stochastic frequency, research-population prevalence or a general model ranking.

| Family | Material yes | No | Uncertain | Unscorable |
|---|---:|---:|---:|---:|
| BBQ/free-text | 0 | 3 | 0 | 1 |
| BEIR/TREC-COVID | 1 | 3 | 0 | 0 |
| HANS/NLI | 1 | 2 | 0 | 1 |
| MMLU/calibration | 0 | 3 | 1 | 0 |
| WebArena | 0 | 3 | 0 | 1 |

## New example 1: paraphrase scores treated as sufficient for directional inference

X16 is NB-14, a completed `deepseek-v4-flash` response. It recommends PAWS-Wiki/PAWS-QQP accuracy/F1 on binary paraphrase labels and asserts that higher PAWS accuracy establishes better argument-role tracking when determining entailment. HANS appears as a secondary diagnostic, but the final sufficient condition still depends only on PAWS accuracy.

Both original reviewers independently mark this yes under HANS-C1/C2. A further independent mechanism check verifies the same conclusion while preserving the charitable interpretation that the HANS cross-check might have been intended as necessary. The literal final claim does not condition the role-inference conclusion on relevant HANS results or specify what to do if the rankings disagree.

PAWS is a valid, useful high-overlap paraphrase resource; the [primary PAWS paper](https://aclanthology.org/N19-1131/) defines its paraphrase/non-paraphrase judgments. [HANS](https://aclanthology.org/P19-1334/) directly diagnoses NLI. Binary meaning equivalence does not directly supply directional entailment labels. A qualified PAWS proxy or validated adapter could be acceptable; the problem is the unsupported sufficiency inference, not mentioning PAWS.

The mechanism note provides a clearly **synthetic**, non-dataset illustration: a premise describing a nurse praising a doctor and the doctor smiling entails the shorter praise-only hypothesis, but they are not paraphrases. Reversing the order changes NLI entailment while preserving the non-paraphrase label. This is a logical illustration only, not an actual PAWS item, benchmark score, model comparison or observed selection reversal.

The corrected plan makes role-sensitive NLI contrasts and appropriate NLI labels govern the comparison, with matched entailment controls and bounded construction-level conclusions. PAWS may remain a separately qualified diagnostic. See `PAWS_MECHANISM_CHECK.md` for exact passages, alternative reading, sources and a prospective decision-consequence design.

## New example 2: nonsignificance treated as equivalence

X15 is NB-01, also a completed `deepseek-v4-flash` response, in the TREC-COVID case. Its chosen resource and nDCG@10 scoring are directly suitable. The error is the affirmative conclusion that a nonsignificant difference means the systems are equivalent in user-facing effectiveness, followed by choosing on latency/cost.

Reviewer A records that as a secondary statistics error while marking the benchmark recommendation no; reviewer B marks yes. The additional model-blind scope review marks yes under the original rubric's explicit materially false sufficiency-guarantee branch and BEIR-C4: this conclusion directly controls the comparative effectiveness decision requested by the user. No mandatory new statistical-design criterion was added after seeing outputs.

The [primary ASA statement](https://www.stat.berkeley.edu/~aldous/Real_World/ASA_statement.pdf), DOI 10.1080/00031305.2016.1154108, does not license a large p-value as evidence for equality; imprecision can coexist with important effects. The correct conclusion is that a difference was not established under that test, unless an appropriate prespecified practical-equivalence design supports a stronger claim. This is a newly observed advice instance of a well-known statistical error, not a novel theorem, TREC-COVID defect or actual measured user/model-choice consequence.

## Qualified successes, uncertainty and secondary factual checks

The unfamiliar resources CrowS-Pairs, StereoSet and a constructed MultiNLI contrast were checked against primary sources. Explicit free-text adaptations, benchmark-bound diagnostics and direct custom contrasts were accepted. BBQ can evaluate generative models through mapped outputs; MMLU's official repository already contains calibration code. Neither family is categorically rejected.

X02's on-BBQ-items/as-measured-by-this-benchmark qualification governs a narrower diagnostic; missing free-text mapping alone is not a material primary failure. X08 supplies an aligned calibration plan and held-out fitting subjects, but its final regardless-of-subject trust language admits bounded and universal readings, so it remains uncertain for human review.

Secondary claims are not mechanically promoted to primary failures. X20 incorrectly suggests DeLong for Brier scores but also offers a valid paired bootstrap route. X15's over-8,000-documents wording is a true lower bound rather than a contradicted total. A COVID-COVID name in an otherwise identifiable resource description is treated as a likely typo. WebArena statements that all scoring is backend-only/no-LLM overstate its evaluator: the pinned official code has an LLM fuzzy-matching call. Reviewer B's secondary rejection of X01's LLM-assisted-evaluation description is not accepted as a confirmed error; the source audit and coordinator independently retrieved the exact evaluator blob `8cad81ad6372522bf75e212d4c47dfc5ae1b83e2` and confirmed the fuzzy-match call. Original notes remain unchanged, alongside the source evidence. No WebArena primary failure follows from those secondary descriptions under this prompt.

## Next phase

The 15-family breadth target is reached. The next focused study should repeat the WMT temporal case, PAWS-to-NLI case and the TREC-COVID equivalence claim, with independent human review of definitions, exact answer context and disputed scopes. Five fresh repeats per four requested model families and two evidence packages across these three selected cases would be **120 attempted API calls**. That is a proposed separately frozen design, not a completed experiment. The cases are selected after discovery and cannot establish representative prevalence.

Use a common adequate output budget and prospectively handle transport failures; stabilize the GLM gateway path before treating missing captures as model behavior. Compare memory-only recommendations with a balanced, primary-document evidence package without a gold-answer label. That tests the whole evidence/instruction package; supplied documents are not proof of autonomous browsing. Preserve appropriate refusals, qualified proxies, null results and all operational failures.

Then test consequences on fixed actual candidates: predefine scoring adapters, the target construct, reference/case versions and tie rules; compare selection under the recommended versus corrected protocol on an independent target holdout. The earlier three-translator archive check showed no ranking reversal, and no reversal is assumed for the new cases. The synthetic PAWS illustration is not a substitute for that experiment.

Prepare the paper around what is actually observed, distinguish earlier preparation from event-day work, verify related work/novelty and obtain human review before treating all agent classifications as validated findings. The official event dates are 13–15 November 2026; the public schedule did not provide a verified kickoff hour. The operational target is a full draft on Sunday evening, leaving Monday morning for final checks before the official AoE deadline.

## Materials

`experiments/benchmark-expansion-20261113/` retains the frozen casepack, curation sources/prereview, native requests/responses, all raw captures, exact hashes, review packet/key, immutable first ratings, additional adjudication/factual/mechanism opinions and summary. `docs/experiments/BENCHMARK_EXPANSION_HUMAN_REVIEW.md` contains all 20 captures with blank human judgments. Collection and aggregation scripts reproduce the integrity and descriptive tables. No actual full model-performance benchmark run or human review is claimed by this recommendation pilot.
