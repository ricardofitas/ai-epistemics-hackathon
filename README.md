# When AI Chooses What Counts

**Can research assistants match evaluations to scientific claims?**

This is a proposed project for the [AI × Epistemics Research Sprint](https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15), 13–15 November 2026, Track 1: Model Epistemics & Decision-Making Evals. The plan is open to revision by the team. No experiments or findings are claimed in this repository yet.

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

## Prior work and contribution

Luo, Kasirzadeh and Shah's [study of autonomous AI scientists](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/) already investigates benchmark selection and metric-related failures. Our proposed extension focuses on matching specific claims to evaluations, testing assistants on sourced cases, and tracing possible consequences for decisions. Any novelty claim must be checked against further related work.

## Current status

**Planning.** The protocol, case set, models and division of work are proposed, not final. No model responses, case annotations or experimental results are included yet.
