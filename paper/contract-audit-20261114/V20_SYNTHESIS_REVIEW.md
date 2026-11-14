# Scientific synthesis review: final primary 3,200 and pending human review

Restored from the completed read-only review after external workspace deletion. Previously checked authoritative primary summaries at research commit `ee04dcb55d547275f46fc3c0a8e5486ee24ecfe8`, the captured primary protocol, and human-review PROTOCOL.md plus receipt.json through GitHub at `3db521c1831ecd4bb1dd4afa4b44f532d0430405`. No network research was repeated. No workbook rows were inspected or annotated.

## Verified quantities and interpretation

The final primary factorial contains 100 SQuAD v1.1 and 100 TabMWP source questions, four models and four separately generated conditions: free/choice instruction crossed with absence/presence of one spurious “A. None” option. All 3,200 distinct planned requests started. There are 3,086 complete responses and 114 unknown outcomes: 94 terminal incomplete, 11 missing terminal events and nine HTTP 504 outcomes. The 3,180 verified terminal objects include incomplete responses and must not be reported as complete answers. There were 3,236 attempts including 36 explicit HTTP 429 attempts.

The source-paired primary accuracy drop is `choice_clear − choice_none`. Its equal-four-model mean bounds are **50–63 percentage points on SQuAD** and **67.5–79.25 on TabMWP**. The interaction is `(choice_clear − choice_none) − (free_clear − free_none)`, with **positive bounds 57.75–73 and 68–81.25 points**, respectively. Earlier diagnostic prose used a different sign convention; do not carry negative signs across studies. All four means were independently recomputed from the per-model summaries and agree with verified-8-waves.json.

Primary scoring concerns the final answer tag, using the prespecified last-nonempty-line fallback for completed answers: normalized SQuAD exact match and exact rational TabMWP agreement under the declared numeric normalization. These endpoints measure delivered final-answer accuracy, not all factual content in a rationale. The reported ranges assign unavailable answers their full possible correctness range on the fixed panels; **they are not confidence intervals**. Complete-case values are descriptive. The supplementary 5,000-resample analysis clusters SQuAD by its 25 realized articles and resamples TabMWP questions. It reports per-model descriptive envelopes, without simultaneous or universe-wide coverage, and does not supply an equal-four-model mean confidence interval.

Observed dummy selections under choice-plus-option are 284/400 planned model-question outcomes for SQuAD and 280/400 for TabMWP. Unknown outputs are not imputed dummy selections. Repeated models and conditions do not increase the number of independent source questions.

## Conservative model-selection prose

On SQuAD, free response without the dummy option admits only GLM as a possible winner; choice-plus-dummy admits Qwen, DeepSeek and GLM. Their respective regrets on the separate clean TabMWP free_clear panel, relative to the best tested model, are **4–6, 18–20 and 0–2 percentage points**. Winner sets and regrets were independently recomputed and agree with summary.json. The sets overlap at GLM. The manipulation broadens the admissible selections and admits choices with greater target regret; it **does not establish a forced selection-policy change**, an observed deployment decision, or that a practitioner chose DeepSeek.

## Evidence boundaries for manuscript integration

This is a prospective researcher-designed factorial using custom diagnostic prompts. Source selection excluded normalized question matches to the earlier project pool; model training exposure remains unknown. Natural source-contract faults in pinned One-Eval, this prospective intervention and the historical scoring-policy replay of published TabMWP outputs are distinct evidence. The factorial does not show that another group used the faulty One-Eval configuration.

The archive replay establishes baseline sensitivity under declared alternatives: explicit-option recognition changes flags without changing ordering; adding residual-zero abstention produces two inversions. This does not establish a unique semantically correct replacement score or an effect on the PromptPG/GPT-3 headline comparison. The separate 24-question numerical control displays the solution in its correct-option arm: option-aware 96/96 recognition is an interpretation/control result, not a reasoning gain. Keep its frozen bare-number endpoint separate from the later option-aware reading.

Model-reader agreement and control success do not establish independent errors or human truth. Their 99 complete study pairs and 12 controls do not validate all residual-zero archive cases or yield a population error prevalence.

## Pinned human64 protocol and receipt

Human labels remain **pending**. The frozen packet contains **64 records: the original 40 preserved with identifiers, including eight original controls, plus 12 historical discrepancies and 12 numerical replies**. Historical additions comprise six gains and six losses. The supplemental 24 were selected after examining results and are diagnostic; pooling their labels does not estimate archive-wide error prevalence. The original 40 remain separately identifiable to the analyst.

Each reader records initial labels in a separate copy before seeing official answers, other labels or model-judge outputs. The task is to identify the option unambiguously conveyed by the reply, otherwise INDETERMINADA, with an optional transcription of another explicit result; it is not to solve the benchmark anew. Ricardo knows the hypothesis and participated in the study, so his eventual classifications are **author annotations**. A second independently working reader can provide agreement evidence. Packet preparation, or one author review, does not supply independent human gold or human-corrected full-table scores for all 7,686 questions. Preserve initial labels separately from any later resolution.

Receipt checked: cases=64; original_cases=40; additional_historical=12; additional_numeric=12; original_controls=8; reader_fields_blank=true. Original-source SHA256: `2a17d5928a07126b1b7682ff9ed9528e3be9a65724f7a69ccc0f46c18255ad3c`. Blind-packet SHA256: `ad52d7f113bcd499a31a503687efece6b8f58fff9aec1e0f9fc520fde8619e83`.

The final Portuguese aggregate still contains older 40-row human-packet wording. The newer pinned human64 protocol/receipt governs current packet scope. Likewise replace manuscript descriptions of the 3,200-slot primary as unfinished with the verified final counts, while leaving human review pending.

Primary reported usage is 2.808415654416 provider cost units; the uncached token-rate estimate is 2.8701829 credits. Neither is an invoice or currency conversion. Across the primary, model-reader and numerical-control experiments: 3,616 distinct requests, 3,487 complete responses and 3.413513413896 reported usage units. Do not attribute that combined total solely to the primary experiment.

Protocol sources already read:

- https://github.com/ricardofitas/ai-epistemics-hackathon/blob/3db521c1831ecd4bb1dd4afa4b44f532d0430405/experiments/human-review-64-20261114/PROTOCOL.md
- https://github.com/ricardofitas/ai-epistemics-hackathon/blob/3db521c1831ecd4bb1dd4afa4b44f532d0430405/experiments/human-review-64-20261114/receipt.json

No provider/judge calls, contacts, Git mutations or Library writes were performed for this review or its restoration.
