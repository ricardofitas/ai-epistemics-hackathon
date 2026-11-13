# Pre-run review: model configuration × prompt package

Prepared 2026-11-12 before any responses from this new experiment were sampled or inspected. The reviewer read the frozen six-case pack, governing cross-case rubric and prior wrapper. A separate fresh-context reviewer assessed the conceptual design without seeing any outputs.

**Verdict:** suitable as a prospectively frozen, descriptive exploratory comparison, subject to the conditions below. No model samples or GitHub edits were made by this reviewer.

## Design

Use the same six case questions and critical requirements. Sample one fresh response in each of four cells per case: session-reported `gpt-6.1-sol` versus requested `gpt-6-luna`, crossed with minimal versus scaffolded prompt package. This gives 24 requested calls on six source cases, not 24 independent research cases. Five domain clusters remain because the two software cases share a domain.

The minimal form contains only the frozen case question. The scaffolded form reproduces the previous full common prefix, requested fields and baseline organization addition. The prepared launcher gives both forms the same 180–240-word response aim and 300-word maximum, with the same knowledge-only, opaque read/write interface. Keep model reasoning/sampling defaults as surfaced; do not invent exact provider snapshots or claim those defaults are equal when they are not exposed. The Sol arm inherits the parent configuration without override; the Luna arm requests the explicit model override.

## Necessary interpretation limits

1. **The prompt treatment is a package.** The scaffolded form adds output fields, source-uncertainty guidance, limitations, sufficiency and confidence requests, organization text and length. A contrast cannot identify the effect of any one instruction. Name this factor `prompt_package`, with `minimal` and `scaffolded` levels.
2. **Minimal is relative.** The original mathematics and vision questions already ask which conclusions an evaluation would justify. Other questions state their desired scientific claim. Preserve the exact questions for comparability; do not describe the minimal arm as having no epistemic cues.
3. **One response per cell has no within-cell replication.** Report observed per-case and model/package counts and within-case contrasts. Do not infer stable model rankings, generation variance, population prevalence, or a statistical interaction. Historical responses are context only and must not be pooled as extra randomized replicates.
4. **The model factor is a configuration contrast.** These are two requested configurations in one provider/agent interface, not independent providers or demonstrated independent architectures. Record requested and actually surfaced identity, defaults, dates and failures. If an override is unavailable, retain the failed planned call; do not silently replace it or pretend the second model was run.
5. **Response budget and interface must match.** The common launcher's 180–240-word aim and 300-word maximum apply to answer words, not prompt words. The full prompt repeats that budget, but the intended output budget is shared. Do not claim prompt-token matching. No browsing, other files or delegation is permitted to subjects. Platform instructions still apply and file isolation is instruction based.
6. **Scoring must remain conservative for terse answers.** Apply the existing rubric without post-output modification. Missing an unrequested caveat, confidence label or citation is not by itself an unsupported recommendation. Require the exact materially incompatible endorsement and critical requirement for `yes`; use `uncertain` for genuine ambiguity. A sole materially incompatible plan recommended as the answer to an explicit goal can be an endorsement—for example, SWE-bench percent resolved alone presented as the plan to demonstrate reduced human maintainer time. A clearly provisional “start with” recommendation, qualified partial proxy, or unclear sufficiency remains qualified or uncertain; brevity does not establish failure. This is a pre-output operational clarification of the unchanged criterion, not an expansion of the failure definition. Verify alternative benchmarks with primary sources and keep factual errors separate unless material to the recommendation.
7. **Freeze and blind.** Commit all exact prompts, launchers, case/rubric hashes, requested configurations, randomized order/seed and analysis rules before calls. Use fresh `fork_turns="none"` contexts. Conceal configuration, package, order and trial key from two independent reviewers, while acknowledging that style may reveal the arm. Retain both complete rating files before unblinding and preserve disagreements/adjudication.
8. **Human review remains pending.** Same-family agent ratings are not independent human validation. Confirm all material failures and case requirements with human review before publication.

## Checked minimal questions

- Python functions: direct functional correctness and equal sampling budget; no supplied benchmark/metric.
- Maintainer time: explicitly asks for a human-workflow outcome; no supplied benchmark/metric.
- Physics citations: reference authenticity plus source support are both explicit goals; no supplied benchmark/metric.
- Historical news translation: narrow temporal/domain target; appropriate uncertainty about exact release dates remains acceptable.
- Mathematical solutions: written logical correctness plus a request to state justified conclusions; final-answer/proof distinction is not supplied.
- Image corruptions: improvement for every tested type plus justified conclusions; aggregation warning is not supplied.

## Primary descriptive outputs

Report all 24 requested calls, completion/error status, primary `yes/no/uncertain/unscorable` counts by configuration and package, six case-level four-cell outcomes, reviewer agreement, and separate verified factual-error/uncertainty records. Inspect every successful and unsuccessful response. If a wrong recommendation is supported, analyze its decision consequence separately with comparable data and conditional language; do not infer real adoption or harm.
