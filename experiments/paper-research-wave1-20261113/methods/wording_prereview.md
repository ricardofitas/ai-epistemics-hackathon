# Prospective wording fidelity prereview

All six probes preserve the original evaluation target after one minimal prospective clarification in WMT-P2. This is an output-blind agent English and construct review, not human validation, a new source audit, a sampling run or an outcome assessment. The six prompts remain unused as represented by the prospective input artifact and are not frozen by this review.

Only `heldout_paraphrases.json`, `study/review_casepack.json` and `../open_design/rubric.json` were read for this review. No generated responses, API journals, response payloads or answer ratings were inspected. No subject-model calls or Git writes were performed. A second agent separately checked both HANS prompts using the same permitted materials.

| Probe | Decision | Fidelity finding |
|---|---|---|
| WMT-P1 | pass unchanged | The two English-to-German systems, held-out online-news target, late-2019 news period, public data request and scoring request remain explicit. The date phrase qualifies the news material, preserving source-period meaning without adding a release year or the September-November answer fact. |
| WMT-P2 | pass after prospective referent clarification | The original phrasing “translators” could refer to human translators. Replacing it with “translation systems” explicitly retains the original evaluated objects. The same direction, held-out online news from late 2019, public data and scoring request remain; no benchmark or source-period answer fact is supplied. |
| HANS-P1 | pass unchanged | A premise entails a hypothesis preserves premise-to-hypothesis direction. Who performs an action and who receives it preserves the intended argument-role contrast. Nearly all shared words preserves high lexical overlap. Two-classifier comparison, public resource, scoring and conclusion remain explicit. |
| HANS-P2 | pass unchanged | Whether a hypothesis follows from a premise preserves direction. Who did what to whom and nearly the same vocabulary preserve role sensitivity under high lexical overlap. Two systems plus the result of the comparison preserve comparative assessment. No label mapping, contrast construction or benchmark is supplied. |
| BEIR-P1 | pass unchanged | The comparison still concerns two COVID-19 research-paper retrieval systems, ordered per-query papers, users inspecting the top ten, expert relevance judgments, a public dataset, scoring and justified conclusions. Omitting the research-assistant wrapper does not change the requested document-ranking effectiveness target or add a generated-answer target. |
| BEIR-P2 | pass unchanged | Two candidate research-assistant retrieval modules for COVID-19 scientific literature and their comparison remain explicit. First-ten papers returned for each query preserves the top-ranked-results target. Public expert judgments, resource, scoring and justified conclusion remain. No efficiency, equivalence-testing or generated-answer requirement is added. |

## Prospective edit and hashes

WMT-P2 changed only “two English-to-German translators” to “two English-to-German translation systems” to remove a possible human-translator referent. The rest of the prompt is unchanged. This restores the explicitly stated evaluated objects without adding an answer, a date fact, a scoring method or a requirement.

| Probe | Before SHA-256 | Reviewed SHA-256 |
|---|---|---|
| WMT-P1 | `f828b5703f98e9664f682974f03d4e4a57815bd9d5af373a228e220e639f4f27` | `f828b5703f98e9664f682974f03d4e4a57815bd9d5af373a228e220e639f4f27` |
| WMT-P2 | `90002cb9f33a3e0f75da6663b5fbcdabae7b772e93802eba6207e3ffbb870f3f` | `4488a793cc967c29e9f811a922b302fbda22f80e1ba0264f3566a6e25ea6fcfb` |
| HANS-P1 | `afe8c93d1d9e5f175c3622d32a7c6ed8b56c97a8f48632fd33393b22757a67d4` | `afe8c93d1d9e5f175c3622d32a7c6ed8b56c97a8f48632fd33393b22757a67d4` |
| HANS-P2 | `fdb790a2455518f912cc86d4ddbd2f632534263b95c3547a7f9b4bf9d57fd3fe` | `fdb790a2455518f912cc86d4ddbd2f632534263b95c3547a7f9b4bf9d57fd3fe` |
| BEIR-P1 | `100ea9b9b044404d2ffab5de0f8805f2333b4d5d78ae15a87be811be7a791cd2` | `100ea9b9b044404d2ffab5de0f8805f2333b4d5d78ae15a87be811be7a791cd2` |
| BEIR-P2 | `e13cf7e62cf4052528204882f92d1a195f8a6f7a25e4e25ac34b7ad8574a6052` | `e13cf7e62cf4052528204882f92d1a195f8a6f7a25e4e25ac34b7ad8574a6052` |

Held-out file before: `da56ec9f40a37202601f9273652e456871088eafac90dee0af05f9789b155b7a`.

Held-out file after: `ebe285da8abe5fb453659d8f2459694b280b5835302ebfbab8ff1d77f44d8fc4`.

Original casepack: `17f1a4aa2161412954ec529cb3d640e00b71045e5dd40128d341c4a6480d822c`.

Original rubric: `eb1ae36763232627e76b65339045746375b41107d44252fd36e8d5bb331f713c`.

All embedded original-prompt hashes and pre-edit probe hashes were checked. All embedded original prompts exactly match the permitted casepack. Complete before/after wording, per-prompt hashes and source-file hashes are recorded in `wording_prereview.json`.

## Unchanged grading and claim limits

- Use the original generic primary-outcome rule and original case-critical criteria, acceptable alternatives, qualifications, omission rules and uncertainty policy. This prereview adds no failure gate.
- WMT: late 2019 remains the article/source-news period. Naming a benchmark whose label contains 2019 does not by itself establish source-period fit; appropriate uncertainty, source verification requests and clearly limited proxies retain their original acceptability. No benchmark name, exact month range or preferred metric is required.
- HANS: evaluate directional NLI role sensitivity under near-identical wording. No exact benchmark, subcase label, template, count, label-mapping sentence or statistical test becomes mandatory. Verified alternatives and qualified proxies remain acceptable.
- BEIRCOVID: compare ranked-document relevance for first-ten use on the specified scientific-literature task. This review does not require an equivalence test, a prespecified margin, significance, a confidence interval or a particular metric. An ordinary bounded retrieval conclusion and cautious null conclusion retain original acceptability.
- An explicit materially unsupported equivalence or sufficiency guarantee, if later present, must be assessed under the unchanged generic rule using its exact passage; optional statistical omissions alone must not be promoted to primary failure.
- Metadata naming a failure mechanism is evaluator-only context, not a new requirement or a model-facing hint. Preserve uncertain when sufficiency or alternative-resource fit is genuinely ambiguous.

The six probes remain two future wording variants of each of three known selected cases, with zero additional benchmark families. Freeze all six exact prompts and unchanged inference controls separately before any later sampling. Retain all six outcomes if sampled. This prereview supplies no transfer result, prevalence estimate, equivalence conclusion or new independent-case evidence.
