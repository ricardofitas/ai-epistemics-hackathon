# WMT decision-consequence feasibility: a paired-score null result

The inspected primary archive does **not** demonstrate a change in model selection caused by choosing the wrong WMT year. All three eligible model identifiers retain their BLEU ordering. This is an exploratory feasibility check, not a new benchmark defect or a reproduction of translation inference.

A four-model pool was written to `pool-prior-to-score-inspection.json` before inspecting its English-to-German scores. It contains common public pretrained MT families: Facebook WMT19, M2M100-418M, NLLB-distilled-600M, and mBART50. The archive has paired data for the first three; mBART50's score/info paths returned 404 and it was not replaced. This local timestamped pool definition is not an external preregistration. Earlier exploratory searches had inspected other OPUS model cards, which are excluded from this pool comparison.

| Published model identifier | newstest2019 BLEU | newstest2020 BLEU |
|---|---:|---:|
| facebook/wmt19-en-de | 42.8 | 36.6 |
| facebook/nllb-200-distilled-600M | 36.7 | 27.5 |
| facebook/m2m100_418M | 31.4 | 23.0 |

All three eligible pairs were checked, with **0 strict ranking reversals**. The maximum-score choice is Facebook WMT19 on both archived tests. Different absolute scores across different corpora are not evidence of an evaluation bug. These results do not establish a downstream user adoption, harm, or changed choice.

The six primary `.eval` files are retained locally with commit/blob provenance in `sources.json`. All use the same BLEU signature: one reference, mixed case, 13a tokenization, exponential smoothing, sacreBLEU 2.3.1. The table uses BLEU points on the 0–100 scale. The archive's chrF scores use fractions and also retain this ordering. The plain `newstest2020` entry was used consistently; `newstestB2020` is a separate reference variant and was excluded. Reference token counts agree between models within year (48,746 for 2019; 52,383 for 2020).

The score repository is pinned to `Helsinki-NLP/External-MT-leaderboard` commit `e770bb935e0afbcf006664c5339b358731a8aff1`. This is an author-maintained primary evaluation archive, whose README describes systematic MT model evaluation and provides model scores, metric signatures, raw model outputs and recipes. The underlying OPUS test-set repository was pinned to `ac0f19c0be3cb4e0d9450fcb2d7a9847c4bdd180`, and the exact source/reference blob metadata for both years and the B variant are in `sources.json`.

Two provenance gaps prevent promotion to a definitive fixed-checkpoint experiment:

1. The inspected archive identifies the same Hugging Face model names across years, but does not establish the exact historical evaluated weight revisions. A current model revision would not retrospectively prove which weights were loaded.
2. The inspected single-reference signatures and token counts are consistent, but the OPUS reference bytes have not been compared against the original official WMT release, and raw hypotheses have not been rescored here. Do not describe this as an independent rerun or an already verified checkpoint-level counterfactual.

The standard `Helsinki-NLP/opus-mt-en-de` model card was also checked at HF revision `6183067f769a302e3861815543b9f312c71b0ca4`: its listed tests end at newstest2019, so it cannot itself support a paired WMT19/WMT20 claim. The multilingual `opus-mt-tc-base-gmw-gmw` card has paired scores but was not added post hoc to the fixed pool; a modern big-gmw card lists WMT19 without WMT20. Some guessed bilingual TC model IDs were unavailable (HTTP 401); no authentication or model access was attempted.

The concrete next step is to audit and replay the archived hypotheses for the same predefined pool against pinned official references, retaining every model and both outcomes. Establish fixed-checkpoint identity from original cache/log metadata if available; otherwise explicitly narrow the statement to immutable published output artifacts or run two pinned checkpoints once. A later additional pool requires a separately frozen selection rule, not a search that stops at the first reversal. Even a future reversal would be a consequence illustration linked to a wrong recommendation, not evidence that WMT is intrinsically invalid.

Reproduce the retained archive calculation with `python3 analyze_archived_scores.py`. No inference, paid API calls, external writes or third-party messages were performed.
