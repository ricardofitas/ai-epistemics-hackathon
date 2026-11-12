# When AI Chooses What Counts

**Can research assistants match evaluations to scientific claims?**

This is a proposed project for the [AI × Epistemics Research Sprint](https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15), 13–15 November 2026, Track 1: Model Epistemics & Decision-Making Evals. The plan is open to revision by the team. Exploratory pre-sprint experiments are now documented below; they do not establish a general recommendation-error rate.

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
- [Completed six-case open recommendation study](docs/experiments/open-recommendations-results.md) — frozen prompts, raw answers, blind ratings and source checks.

## Prior work and contribution

Luo, Kasirzadeh and Shah's [study of autonomous AI scientists](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/) already investigates benchmark selection and metric-related failures. Our proposed extension focuses on matching specific claims to evaluations, testing assistants on sourced cases, and tracing possible consequences for decisions. Any novelty claim must be checked against further related work.

## Current status

**Exploratory pre-sprint evidence.** A six-case, 24-response open recommendation study is complete in one inherited agent configuration. Two blinded agent reviewers found 0/24 unsupported recommendations under the frozen criteria, and a separate bounded source audit found no confirmed factual contradictions. Both conditions explicitly request limitations and sufficiency; human review and broader model/interface testing remain necessary. This does not support a claim of systematic recommendation failure or general reliability.

Earlier [CivilComments pilot results](https://github.com/ricardofitas/ai-epistemics-hackathon/pull/1) and [TruthfulQA audits/pilot](https://github.com/ricardofitas/ai-epistemics-hackathon/pull/4) remain separate exploratory designs. Known evaluator implementation defects are controls, not new recommendation failures.
