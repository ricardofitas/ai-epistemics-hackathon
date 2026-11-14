# Bounded primary-source prior-art check

Research date: 2026-11-14. Scope: deterministic correct-position exposure from benchmark field assembly; native scorer/report metric disagreement. Generic public queries only. No model calls, Git mutations, or manuscript changes.

## Assessment

**The general correct-A mechanism is not new. A near-exact public code-path report exists.** Tinker Cookbook issue #978 (2026-10-17), §6, traces correct-first field assembly to expected A and explicitly states a constant-A policy scores 100%; PR #994 (2026-11-06) adds synthetic environment tests and a proposed shuffle. Sun et al. (2025), §2.6, explicitly recognize frameworks defaulting to correct answer A. Inspect and simple-evals implement shuffle safeguards.

The potentially more specific contribution is an audited, reproducible schema → adapter → rendered prompt → score → report chain in a particular shipped harness, including a content-free constant-A counterexample and disagreement between the metric actually selected for the native report and another metric. This search did **not** establish that combination as globally new. Do not frame ordinary position sensitivity, correct-first storage, missing shuffle, or score-extraction disagreement as first discoveries.

Storage in a dedicated correct-answer field is normal. The failure begins when gold-dependent storage order survives into the prompt and the evaluator interprets that position as the target. A model's learned preference for A is a separate empirical phenomenon; a constant-A oracle can expose the implementation flaw without showing any model preference or training contamination. Option-permutation tests can diagnose both but do not themselves identify the cause.

## Directly relevant sources

### Tinker Cookbook issue #978 / PR #994 — near-exact deployed code-path prior art

- Primary issue: https://github.com/thinking-machines-lab/tinker-cookbook/issues/978
- Title: Fail-open verifier branches and answer-extraction defects across the benchmark suite.
- Author/date: AUTHENSOR; 2026-10-17T17:41:10Z. Read via GitHub connector `fetch({url:...})`; browser direct issue not needed. Open at retrieval.
- Exact location: §6, “GPQA pins the correct answer to option A in the text-answer schema”; audited code commit prefix `df2aff6`, `gpqa.py:89–154` (computation `:96–133`).
- Scope: report traces dedicated correct/incorrect columns, correct-first list construction, target lookup at index zero, no shuffle, and a constant-A policy's 100% score. Synthetic rows with verbatim copied computation verify the path; the reporter explicitly has NOT verified the live dataset layout in that checkout. Thus this is direct prior report of the mechanism and constant-policy consequence, with a stated data-precondition limitation. No native metric-selector disagreement is claimed in §6.
- Follow-up primary PR: https://github.com/thinking-machines-lab/tinker-cookbook/pull/994
- Author/date: zuraiz-anjum; 2026-11-06T18:35:50Z. Title: fix(eval): shuffle GPQA choices so the answer is not always A. Open, unmerged at retrieval.
- PR describes `GPQABenchmarkBuilder.make_envs`, deterministic per-example shuffle and 40 synthetic rows tested through built environments. Reports main test outcome 1 failed/2 passed, proposed branch 3 passed, and does not rerun published real-model scores. Head `1ab89b0023f069b1c89f5334c59f0495612ae12f`; base `7aca914feb309150e2b88b2401b7099cc4b09071`.
- Independently read immutable primary code: https://github.com/thinking-machines-lab/tinker-cookbook/blob/7aca914feb309150e2b88b2401b7099cc4b09071/tinker_cookbook/eval/benchmarks/gpqa.py . `make_envs` confirms gold-first fallback, no permutation, expected letter lookup and prompt rendering; `GPQAMessageEnv.step` gives reward/`correct` by equality with expected. This is source inspection only, not a locally executed reproduction or validation of all live dataset rows. GitHub returned modified date 2026-04-08 for this file, which is metadata rather than a separately audited introduction date.
- Implication: cannot claim first causal correct-field→gold-A trace or first constant-A counterexample. A stronger native CLI, real dataset and native report validation can improve evidence over this public example, without making the general mechanism new. Authorship distinct by public handles; no claim about users' identities or influence.

### Inspect Scout issue #330 — explicit hazard awareness

- Primary: https://github.com/meridianlabs-ai/inspect_scout/issues/330
- Author/date: jiito, 2026-03-10. Exact location: issue description, web text lines154–156; retrieval `turn46view1`.
- Scope: proposes a transcript scanner to catch unshuffled GPQA always A. Hypothetical example rather than documented occurrence, so use as evidence the hazard was already understood.

### MAS-PromptBench docs — explicit field-to-prompt safeguard

- Primary: https://juyangbai.github.io/MAS-PromptBench/docs/tasks/gpqa/
- Exact location: “Data” §, lines76–78; retrieval `turn46view2`.
- Scope: explains separate correct/incorrect fields and seeded shuffle to avoid always A; output format is A–D and exact letter match. Current documentation, chronology not pinned. Additional supporting implementation documentation; no failure claim.

### Sun et al. 2025 — direct acknowledgment of always-A evaluation

- Title: Evaluation is All You Need: Strategic Overclaiming of LLM Reasoning Capabilities Through Evaluation Design.
- Primary: https://arxiv.org/html/2506.04734v1 ; https://arxiv.org/abs/2506.04734
- Version/date: v1, 2025-06-05.
- Exact location: §2.6 “Option and Answer Bias in GPQA Diamond,” web text lines 190–230; Figure 6. Retrieval refs `turn31view0`, `turn32view1`.
- Short quotation (19 words): “some open-source evaluation frameworks default to placing the correct answer in option A.”
- Scope: always-A control, moved labels/positions, and randomized gold position; reports changes mostly exceeding five percentage points. §2.6 does not name those frameworks or give a schema-to-prompt trace. No constant-A native-report audit located. Avoid translating their interpretation of model stability into proof of training memorization.
- Novelty implication: directly rules out first-general-discovery wording for gold=A evaluation and inflated favorable conditions.

### Inspect Evals GPQA — explicit correct-first storage and shuffle mitigation

- Primary: https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/src/inspect_evals/gpqa/gpqa.py
- Exact locations: `record_to_sample`; `get_gpqa_diamond_dataset` docstring; `gpqa_diamond` parameter docstring. Retrieval refs `turn30view1`, `turn31view2`; web text lines 709–737 and 928–949.
- Short quotation (16 words): “target is always \"A\" in the, dataset, we will shuffle the presentation of options to mitigate this”.
- Scope: maps Correct Answer followed by Incorrect Answer 1/2/3 and target A; loader forwards `shuffle_choices`, defaulting to seed 42 in retrieved main. Documentation explicitly says False preserves raw correct=A order. This is recognized hazard and preventive implementation, not evidence that Inspect's default is leaky. Main is mutable; pin history before claiming chronological priority for any specific comment.

### OpenAI simple-evals GPQA — concrete preprocessing safeguard

- Primary: https://github.com/openai/simple-evals/blob/main/gpqa_eval.py
- Exact locations: `GPQAEval.__init__` and inner `fn` in `__call__`. Retrieval ref `turn37view1`, web text lines 359–394 (source approximately lines 28–44).
- Scope: seeded per-example permutation; correct-first field list; applies permutation before determining target letter and formatting choices. This supports the necessary invariant: gold labels must track displayed permutation. It is not an unshuffled failure example. Main is mutable; no historical-priority claim established.

### Pandey et al. 2025 — GPQA shuffled/unshuffled empirical comparison

- Title: Adaptive Graph of Thoughts: Test-Time Adaptive Reasoning Unifying Chain, Tree, and Graph Structures.
- Primary: https://arxiv.org/html/2502.05078v1
- Exact locations: §5.1.1, §5.1.2, Tables 1–2. Retrieval refs `turn31view1`, `turn32view2`.
- Scope: explicitly compares GPQA Diamond with and without answer shuffling; GPT-4o-mini direct IO 54.6 versus 37.4, AGoT 55.1 versus 49.5. The paper describes position-dependent effects and cites Radha/Goktas 2025. Its text does not establish that every unshuffled answer was A or trace field assembly; therefore use as shuffled/unshuffled precedent, not conclusive constant-A leak evidence.

## Score/extraction/report prior art

### Molfese et al. ACL Findings 2025 — strongest peer-reviewed score-semantic mismatch located

- Title: Right Answer, Wrong Score: Uncovering the Inconsistencies of LLM Evaluation in Multiple-Choice Question Answering.
- Primary: https://aclanthology.org/2025.findings-acl.950/ ; https://aclanthology.org/2025.findings-acl.950.pdf
- Exact locations: §3.2 (strategies), §5 RQ1 and Table 1 (human agreement), §6 and Table 3 (adversarial extraction), Appendix A.3/Table 9 (invalid responses). Retrieval refs `turn34view2`, `turn36view4`.
- Scope: compares Logprobs, RegEx, and xFinder extraction with human judgments. §6 shows extractors can answer the original MCQA instead of extracting an absent/invalid model answer; Table 3 gives adversarial rates up to 96.9%. This is concrete scorer task substitution, not a reporter choosing one metric over another. Strongly anticipates broad claims that reported accuracy can credit behavior not present in an evaluated answer.

### EvalEng 2026 — harness-level assessment/reporting framework

- Primary: https://arxiv.org/html/2605.24213v1
- Exact locations: §4.2.4 Assessment, §4.2.5 Reporting, §7.1 “Build oracle-independent verification into scoring pipelines.” Retrieval refs `turn38view0`, `turn39view0`, `turn39view1`.
- Scope: separates scoring/aggregation and reporting and motivates metamorphic/differential testing. §7.1 cites LM Eval LongBench ROUGE-L near 1.0 caused by computation bug (linked primary issue https://github.com/EleutherAI/LMEval/issues/2890). This supports harness-software fault framing but does not by itself establish the specific correct-first leak or metric-selector failure. Article v1 and project website use different issue-count summaries; cite the article version if quoting statistics.

### Public EvalScope release notes — direct auxiliary-score substitution precedent; provenance caution

- Primary: https://github.com/modelscope/evalscope/releases
- Exact location: release entry English “Bug Fixes” containing ProcessBench, web text lines 918–920. Retrieval refs `turn38search4`, `turn39view2`.
- Scope: says incomplete ProcessBench/other metrics could lead to auxiliary-score substitution for unavailable primary metrics, now explicitly reported instead. This is very close to reporting/metric-identity concerns. Release page is mutable; resolve exact release/PR before citing. Author provenance and independence from the present user's earlier work have **not** been checked. Do not call it independent prior art until checked. No inference that it is the current defect.

## Adjacent work that must remain distinct

- Pezeshkpour & Hruschka, 2023, Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions: https://arxiv.org/abs/2308.11483 (`turn42view0`), abstract. Studies model performance changes under reordered choices, not deterministic target revelation from schema order.
- Gupta et al., 2024, Changing Answer Order Can Decrease MMLU Accuracy: https://arxiv.org/abs/2406.19470 (`turn42view1`), abstract. Studies shuffle sensitivity and leaderboard implications; no correct-first-field leak established from abstract.
- Turpin et al., NeurIPS 2023, Language Models Don't Always Say What They Think: https://arxiv.org/abs/2305.04388 (`turn42view2`), abstract and §3 in https://openreview.net/pdf?id=bzs4uPLXvi (`turn29search36`). Deliberately makes few-shot demonstration answers always A to bias predictions and study explanation faithfulness. This is intentional demonstration bias, not a shipped evaluator bug.

## Leads not verified as primary fulltext

- Radha & Goktas, On the Reasoning Capacity of AI Models and How to Quantify It, arXiv:2501.13833 (2025-01-23): primary abstract https://arxiv.org/abs/2501.13833 appeared as `turn35academia30`; HTML unavailable, PDF exceeded browser size. AGoT cites it for positional analysis. Do not quote detailed methods without fulltext.
- Same Outputs, Different Scores: Auditing the Unchecked Graders of Multimodal LLM Benchmarks, arXiv:2611.03377: relevant secondary search leads, but direct arxiv abs/HTML/PDF fetch failed. Excluded from evidentiary conclusions pending primary verification.
- SANE was already known to the parent task; not revisited as direct correct-position prior art because it concerns scorer-specific metamorphic judge testing.

## Safe claim boundary

Defensible: a case study establishes a specific shipped evaluator's gold-position exposure and its effect on selected native report metrics, with dependency-pinned counterexamples and repaired controls. Prior work documents answer-order sensitivity, always-A evaluation conditions, and scorer-dependent scores; this audit adds whatever precise causal/artifact evidence survives comparison.

Not defensible from this check: first answer-position leakage; first demonstration that always A can inflate MCQA; first evaluation-harness scoring bug; first score mismatch; or global novelty of the combined chain. Absence in a bounded search is not evidence of absence.
