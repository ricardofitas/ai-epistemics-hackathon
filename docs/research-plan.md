# Research plan

## Working title

**When AI Chooses What Counts: Can Research Assistants Match Evaluations to Scientific Claims?**

## Motivation

Benchmark scores influence which models, defenses and research directions are selected. Yet a score is evidence for a particular task, data distribution, metric and evaluation protocol; it is not automatically evidence for a broader claim. AI assistants are increasingly involved in choosing evaluation tools, so a plausible but poorly matched recommendation could propagate into the research workflow.

This is a proposed empirical study, not a claim that assistants routinely give incorrect advice or that researchers have acted on it. We distinguish failures of the benchmark implementation, limitations of a valid benchmark used as a proxy, mismatched metrics, unsupported interpretation and lack of information.

## Research questions

1. Given a specific scientific claim and decision, do assistants recommend benchmarks and metrics that can support them, and do they explain what remains unmeasured?
2. How do recommendations change when the objective changes but the candidate information stays the same? Do assistants recognize when no supplied option is sufficient or key information is missing?
3. In selected documented examples, could the recommended evaluation change which method is selected? What is the size and direction of the difference under the decision-relevant measure?
4. Does an explicit compatibility check improve recommendations relative to a baseline with the same source information and output requirements?

## Hypotheses and competing outcomes

- H1: Some recommendations will be insufficiently aligned with the stated claim or will omit a consequential limitation. Alternatives: recommendations are appropriately qualified, or failures are rare in the cases studied.
- H2: In some paired scenarios, changing the research objective will not produce the change in metric or qualification needed to support the new objective. Alternative: assistants adapt appropriately.
- H3: A structured compatibility check will reduce unsupported recommendations. Alternative: it has little effect, increases unnecessary abstention, or worsens some responses.
- H4: In at least one documented example, evaluation choice can change a method selection or its decision-relevant performance. This is to be checked before presenting it as an empirical result of the project.

These are testable expectations, not established results. Report neutral, null and adverse findings as carefully as positive ones.

## Relation to existing work

- Luo et al., [The more you automate, the less you see](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/), PNAS 2026, investigate benchmark choice, metric use and other methodological pitfalls in two autonomous AI scientist systems on a controlled synthetic task. Benchmark choice and workflow auditing are therefore not new by themselves.
- Hutchinson et al., [Evaluation Gaps in Machine Learning Practice](https://facctconference.org/static/pdfs_2022/facct22-3533233.pdf), FAccT 2022, study differences between commonly reported evaluations and application needs.
- Shen et al., [One-Eval](https://arxiv.org/abs/2603.09821), a 2026 preprint, describes automated intent-based benchmark and metric recommendation. Its existence makes the workflow concrete; it does not establish that the system gives bad recommendations.
- [WILDS](https://proceedings.mlr.press/v139/koh21a.html) and [HANS](https://aclanthology.org/P19-1334/) provide documented examples of generalization and evaluation limitations relevant to case construction.

The intended distinction is the combination of claim-specific suitability, paired changes in the objective, calibrated limitations or abstention, and measured decision consequences on sourced examples. Whether this combination is genuinely novel requires a focused literature check before publication.

## Experimental scope

Build approximately 8–12 independently documented cases. Some may be paired variants of a source case; clearly distinguish source cases from prompt variants. A case specifies a research claim, decision, available information, candidate options, critical requirements, evidence links and defensible outcomes. Include:

- clearly suitable recommendations and legitimate alternative choices;
- related but insufficient benchmarks or metrics;
- partial proxies that become acceptable only with accurate qualifications;
- no sufficient option among the supplied candidates;
- insufficient information, where clarification or conditional advice is appropriate;
- paired objectives where a change in requirements should change the evaluation or its interpretation.

For feasibility, target two assistants, two prompting conditions and two independent runs per case. Ten prompts under that design require about 80 model calls. If there are paired variants, count each distinct prompt in that total. Recording failures and annotation time matters more than hitting that number.

## Outcomes

**Primary:** proportion of scorable responses containing a pre-defined unsupported or materially incompatible recommendation, with the denominator and missing responses reported. A partial proxy with an explicit, accurate limitation is not automatically a failure. A qualified recommendation can be appropriate when the task is underspecified.

**Secondary:** critical limitations identified; appropriate versus unnecessary abstention; evidence quality; sensitivity to changes in the stated objective; inter-reviewer disagreement; and, for sourced cases where available, change in the selected method and the decision-relevant score. Analyze the structured-check contrast as paired comparisons on the same cases. Report uncertainty appropriate to the small number of independent source cases.

## Decision consequences

Where published comparable results exist, apply a pre-specified decision rule to the recommended evaluation and compare the selected method with the method favored by the relevant measure. The result is a retrospective, conditional estimate, not evidence that anyone actually followed the recommendation or experienced harm. Do not treat a proxy as ground truth for the real world without independent justification.

## Practical outputs

The minimum deliverable is a curated case set, prompts, recorded responses, ratings and a short report with at least one source-backed worked example. If feasible, add a lightweight checking tool and a blinded second review. Preserve model versions, prompt conditions, evidence snapshots or links, timestamps, failures and analysis code or calculations.

## Boundaries

The study does not estimate the frequency of benchmark misuse throughout research, prove that an assistant caused a published error, or establish that a benchmark is universally bad. Selection and annotation may introduce bias; a small case set supports case-specific, exploratory conclusions. Differences between model runs on the same case are not independent research cases. Declare any reused material and obtain the relevant permission before redistributing private team data.
