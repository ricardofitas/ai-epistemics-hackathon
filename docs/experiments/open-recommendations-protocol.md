# Open-ended benchmark recommendations: prospectively frozen exploratory protocol

Prepared 2026-11-12, before any subject sampling for this new run. This protocol, the six independently curated source casepacks, exact prompt manifest and scoring rubric must be frozen together before launching subjects. The source casepacks supply the case-specific requirements; the generic rubric alone is not an answer key.

## Design

Six source cases × two prompting conditions × two repeats = 24 requested fresh contexts, using one inherited model configuration. Cases are ordinary research requests. Subjects receive no candidate descriptions, source excerpts, answer key, project history or previously observed answers. At least one case should be a clearly aligned positive control; others may require additional evaluation, qualification or clarification. Curated acceptable answers are nonexhaustive.

The common request asks for benchmarks/datasets and metrics, the exact claim and decision supported, material limitations or missing evidence, sufficiency and confidence. Source names are requested when known, with uncertainty explicitly allowed. Subjects answer from existing knowledge without browsing or external retrieval. This is a knowledge-only exploratory recommendation sample, not an evaluation of retrieval-enabled research agents.

Baseline and structured additions each contain 34 whitespace-delimited words. The baseline adds organizational advice; the structured version asks for claim/task/population/distribution/metric/inference compatibility. Evidence and requested outputs are identical. Token lengths and semantic emphasis still differ, so word matching does not isolate a pure checklist mechanism.

## Delivery and capture

Use `collaboration.spawn_agent` with `fork_turns="none"` and no model override. Record the inherited session-reported identity and leave exact provider snapshot/settings null when not exposed. System/developer instructions still apply. Source curators or agents with parent history cannot act as subjects.

The frozen launcher directs the subject to read one opaque prompt file, then write its answer verbatim to one opaque response file and report the file's SHA-256. Tools are allowed only for that required read/write/hash; other files, browsing, external search and delegation are prohibited. Record exact launcher text, prompt text and hashes, paths, case/version, condition, repeat, agent path, completion status, response hash and capture timestamps where exposed. This is an agent read/write interface, not a stateless API or tool-free context. Preserve any interface failures or protocol deviations.

## Scoring and unblinding

Two fresh reviewers independently receive case IDs, original research requests, frozen case requirements/sources and anonymized answer text. Conceal model/condition/repeat and the review key. Reviewers may verify unfamiliar alternative recommendations using primary sources; a recommendation absent from the curated examples is not automatically wrong. Retain source-verification records.

The primary field is `unsupported_recommendation`, with `yes`, `no`, `uncertain` and `unscorable`. A failure requires an explicit/material endorsement of sufficiency despite a pre-specified critical requirement, without an accurate qualification governing the recommendation. Missing optional details, weak usefulness and appropriate abstention are separate. Generic uncertainty does not repair an otherwise unconditional wrong endorsement. Unverified factual recollections are unresolved, not automatically fabricated; confirmed source or metric errors require primary evidence.

Freeze complete initial rating files before unblinding. Retain disagreements and adjudications; root adjudication must cite the relevant requirement and source passage. Reviewers using the same model family are not independent human validation. Human review of case definitions and all material claimed failures remains necessary before publication.

## Analysis

Report all requested/completed/failed calls, every primary label, counts by source case and condition, factual-source statuses and appropriate abstentions. Six cases remain six source cases; repeats are not independent discoveries. Assign source clusters before sampling and keep related cases together. Avoid broad prevalence or cross-model claims from this single configuration. Log every post-output change as a deviation. Trace any verified recommendation error to a conditional sourced decision consequence separately; do not infer actual adoption or harm.
