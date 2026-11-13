# When AI Chooses What Counts

**Can research assistants match evaluations to scientific claims?**

This is a proposed project for the [AI × Epistemics Research Sprint](https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15), 13–15 November 2026, Track 1: Model Epistemics & Decision-Making Evals. The plan is open to revision by the team. Exploratory preparation and first event-day experiments are now documented below; they do not establish a general recommendation-error rate.

## The idea

Researchers increasingly ask AI assistants which benchmarks and metrics to use. A recommendation can look relevant while failing to test the actual claim. We want to investigate whether assistants identify that gap, communicate its limitations, and recommend evaluations that support the intended decision.

For example, an overall accuracy score may identify one model as best, while another performs much better on the worst-performing group. The right measure depends on the research question and decision. We will look for cases where that distinction matters, not assume that either metric is universally wrong.

## Proposed approach

1. Curate a small, source-backed set of research scenarios, candidate benchmarks and metrics, including suitable, partial and unsuitable options.
2. Ask at least two AI assistants for recommendations and limitations. Compare ordinary prompting with a structured compatibility check using the same evidence.
3. Score recommendations against pre-specified criteria, with independent review where feasible. Include cases in which asking for clarification or saying that no supplied option is sufficient is a good answer.
4. For a few cases with published results, calculate how following a recommendation could change a model or method selection.
5. Report both positive and negative findings, uncertainty, limitations and reproducible materials.

The main question concerns whether a recommendation supports a specified claim. We will not infer real-world adoption, causation or harm merely from a model response or a retrospective score comparison.

## Documents

- [Research plan](docs/research-plan.md) — research questions, positioning, outcomes and scope.
- [Experiment protocol](docs/experiment-protocol.md) — case design, prompts, scoring and analysis.
- [Starter cases and literature](docs/starter-cases.md) — concrete public examples and sources to verify.
- [Tasks and sprint plan](docs/tasks.md) — deliverables, dependencies and a minimum viable path.
- [Initial six-case open recommendation study](docs/experiments/open-recommendations-results.md) — 24 answers, frozen prompts and blind/source checks.
- [Model × prompt-form follow-up](docs/experiments/model-prompt-factorial-results.md) — two requested configurations, minimal/scaffolded questions and a verified temporal-fit failure.
- [Targeted replication and independent holdouts](docs/experiments/wmt-targeted-replication-results.md) — 20 fresh WMT answers, four independent-case answers and a source-verification package.
- [Decision-consequence feasibility](docs/experiments/wmt-decision-consequence-feasibility.md) — pinned published scores show no ranking reversal in the inspected three-model pool.
- [Human review worksheet](docs/experiments/WMT_HUMAN_REVIEW.md) — all 28 WMT answers, shuffled, with human judgments pending.

- [Adaption API integration and pilot](docs/experiments/adaption-api-pilot-results.md) — seven granted hosted models, native API runner, retained incomplete/timeout calls and a separate token-budget follow-up.
- [Adaption human review packet](docs/experiments/ADAPTION_HUMAN_REVIEW.md) — all ten API captures, with human judgments pending.

- [Five-family expansion and results](docs/experiments/benchmark-expansion-results.md) — BBQ, BEIR/TREC-COVID, HANS, MMLU and WebArena; 20 attempts, 17 complete answers, retained review disagreements.
- [Coverage target and next steps](docs/experiments/pilot-coverage-and-next-steps.md) — 15 benchmark-centered claim families reached; replication and decision validation next.
- [Expansion human packet](docs/experiments/BENCHMARK_EXPANSION_HUMAN_REVIEW.md) — all 20 new captures with human judgments pending.

## Prior work and contribution

Luo, Kasirzadeh and Shah's [study of autonomous AI scientists](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/) already investigates benchmark selection and metric-related failures. Our proposed extension focuses on matching specific claims to evaluations, testing assistants on sourced cases, and tracing possible consequences for decisions. Any novelty claim must be checked against further related work.

## Current status

**Exploratory preparation and first event-day evidence, 12–13 November 2026.** The initial six-case open study produced 0/24 unsupported recommendations in one inherited configuration. A frozen two-configuration × prompt-form follow-up produced 2/24, both Luna answers on one temporal-fit case: recommending `newstest2019` for late-2019 news, whereas official documentation specifies September–November 2018; `newstest2020` is the matching option.

A separately frozen **20-answer replication** repeated that selected case five times per configuration/package. Both blind agent reviewers agree: Luna memory-only **5/5 unsupported**, Luna source-verification **0/5**, Sol **0/5 in each package**. The source package combines date-check instructions, both official candidate URLs and permitted retrieval, so this is not a browsing-only causal estimate. Two new source-family holdouts (Natural Questions extraction and adult triage evaluation) yielded **0/4 material fit errors**. A separate three-model published-score archive check found **no ranking reversal** between the WMT years; exact historic weight/reference provenance remains incomplete.

The native **Adaption API** is now integrated. The authenticated catalog grants seven hosted model IDs; six configurations produced complete answers across an initial seven-call block and a separately frozen three-call token-budget follow-up. The same selected-case temporal mismatch is observed in Gemma 31B, GLM 5.2, DeepSeek V4 Flash and the higher-cap GLM 5.3 Flash call. Qwen 3.8 27B gives a matching WMT20 answer; Qwen 3.5 397B remains unscorable after an empty capped response and a separate HTTP-504 call. Gemma 26B's date choice matches, while its leakage assurance is conservatively uncertain after a factual scope audit. First blind ratings are preserved alongside that separate coordinator disposition. These are one-off observations on one selected question across different budget/interface settings, not general model error rates. New API human review is separate from the earlier 28-answer packet.

A separately frozen **five-family expansion** adds BBQ/free-text stereotypes, BEIR/TREC-COVID retrieval, first HANS recommendation trials, MMLU confidence calibration and WebArena task completion. Twenty API attempts yield 17 complete answers and 3 retained HTTP504 captures. Coverage is now **15 source-case families** (119 complete answers in 126 captures across heterogeneous cohorts), reaching the preferred pilot-breadth target. Those totals are inventory counts, not a pooled model-error denominator or 15 full benchmark-performance runs. The coordinator synthesis identifies two new material advice examples—PAWS paraphrase scores treated as sufficient for directional NLI, and nonsignificance treated as effectiveness equivalence—plus one unresolved calibration-scope case. Both examples came from one requested DeepSeek configuration and are not yet stochastically replicated. Two initial rating files, their three disagreements, independent scope/factual/mechanism checks and separate adjudication are retained; human validation remains pending. The next phase focuses on repeated selected-case comparisons, primary evidence and measured selection consequences.

These results strengthen a case-specific recommendation finding, not general error prevalence, model ranking, a defect intrinsic to WMT or measured real-world harm. All responses, frozen prompts, source evidence, independent ratings, nulls and limits are retained. Human review is pending; the earlier shuffled packet includes all 28 WMT answers across the three collaboration-agent cohorts. Earlier cohorts remain separate.

Earlier [CivilComments results](https://github.com/ricardofitas/ai-epistemics-hackathon/pull/1) and [TruthfulQA audits/pilot](https://github.com/ricardofitas/ai-epistemics-hackathon/pull/4) remain separate exploratory designs. Known evaluator defects are controls, not new recommendation failures.
