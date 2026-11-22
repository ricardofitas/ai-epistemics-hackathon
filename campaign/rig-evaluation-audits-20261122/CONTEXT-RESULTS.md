# MadinahQA context-restoration audit

Restoring the documented missing reading passage improved exact-match scores for all 25 auditable configurations on the 602 matched MadinahQA General questions. Mean accuracy across the fixed configurations increased from 64.38% to 76.74%. Individual increases ranged from 6.81 to 16.28 percentage points. Nineteen of 300 model orderings reversed on the whole panel and one became a tie. Fifteen reversals were selected in the first pass. Three recurred directionally on held-out passages. None met the frozen margin and confidence criterion.

| Matched panel | Questions | Passage groups | Unchanged | First model to second | Second model to first | New ties | Resolved ties |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First pass | 286 | 18 | 279 | 8 | 7 | 4 | 2 |
| Held-out assessment | 316 | 18 | 279 | 6 | 13 | 1 | 1 |
| Whole | 602 | 36 | 280 | 9 | 10 | 1 | 0 |

The two direction columns use lexical model ID order. The sample comprises the General subset, one component of HELM Arabic. Of 29 configurations named in the release catalogues, two changed adapter specifications. Two of the remaining 27 lacked their three v1.0.0 run objects, leaving 51 of 351 otherwise eligible pairwise comparisons unavailable. All 50 auditable per-run aggregates reproduced from per-item scores. In each evaluated configuration, 602 of the 612 old and repaired prompts differed only by a passage insertion and all ordered references were unchanged.

The 250 exact-prompt control observations had one score transition and a net increase of one correct answer. HELM marks all 250 v2.0.0 control results and all 15,050 repaired results as cache hits. A cached result can still have originated in a different inference run. The archived request comparison isolates the rendered input change, while a cross-release comparison can include factors such as served-model drift. All 25 gains are consistent with the documented mechanism. A fix-and-rerun experiment at fixed local weights would strengthen the causal comparison. The evidence supports checking that the reference passage appears in rendered requests before commissioning an evaluation. It is insufficient to claim that any particular model pair changes order robustly.

Closest work includes Stanford's own erratum and the original manuscript's WinoGrande sentence intervention. The new result is the size of the score effect and the disparity between descriptive and held-out order changes on this archive. [Stanford's erratum](https://crfm.stanford.edu/2025/12/18/helm-arabic.html#errata-2026-06-03) · [MadinahQA fix](https://github.com/stanford-crfm/helm/pull/4127)

The raw inputs are recoverable from the two fixed releases. The [input manifest](receipts/madinahqa-inputs.json) hashes the 170 available objects and records the six unavailable paths. The [audit receipt](receipts/madinahqa-audit.json) includes every margin and held-out interval used for selection.
