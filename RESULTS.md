# Matching the Questions Reverses Four ScienceQA Comparisons

Results accompanying the AI × Epistemics Research Sprint report by Ricardo Fitas, Antonio Galasso, Vittoria Lanzo and Kunal Sharma, 13–15 November 2026. The tables below report the results in the paper. The links identify the records and the evaluation rules used to produce them. Percentage-point differences use the displayed precision unless exact counts are given.

## ScienceQA

The official test split contains 4,241 questions. MM-BigBench used exactly the 2,017 test questions with an image. All item identifiers and all 2,017 answer labels match the source. The archived chain-of-thought GPT-3 choices match 1,360/2,017 image answers and 1,828/2,224 other answers. This reproduces the published 3,188/4,241 (75.17%) and 67.43% on images. The comparator column below is the source study's best accuracy across its ten instructions.

| Comparator | Published comparator score | Comparator lead over full-test GPT-3 | Comparator lead over image-question GPT-3 |
|---|---:|---:|---:|
| LaVIN-7B | 75.11% | −0.06 | +7.68 |
| BLIP-2 | 74.17% | −1.00 | +6.74 |
| InstructBLIP | 73.33% | −1.84 | +5.90 |
| ChatGPT | 69.41% | −5.76 | +1.98 |
| Flan-T5-XXL | 67.43% | −7.74 | 0.00 |

The census covers the entire block of 20 leaderboard rows citing MM-BigBench. Four reverse, one becomes a tie at reported precision and 15 retain their order. LaVIN-7B's published 75.11% is a source aggregate. The audit did not recover a full file of its individual predictions. The MiRA methods and Tables 4–5 are the basis for the separate finding about reusing an image-only result as an overall average.

The authors' GPT-3 script picks an option at random after extraction fails. The original archive contains 243 empty texts, 123 of which were assigned the correct option. Counting empty texts as wrong gives 3,065/4,241 (72.27%). The published direct-answer baseline implies 3,137/4,241 versus 3,188/4,241 with chain-of-thought. A common-policy contrast requires the direct-arm outputs. As a separate check, neither LLaVA archive contained a blank. Under all assignments to unresolved text, v0 scores 3,855–3,856 and v1.3 scores 3,863–3,867.

[Full source-block table](evidence/scienceqa-20261115/results/leaderboard_comparisons.csv) · [GPT-3 item scores](evidence/scienceqa-20261115/results/gpt_records.csv) · [All three model archives and replay scripts](evidence/scienceqa-20261115/README.md) · [Public ScienceQA comparison](https://github.com/lupantech/ScienceQA/blob/2cbf8318e07b9ece895bb2ae605e71e38d623264/README.md) · [MM-BigBench source scores](https://github.com/declare-lab/MM-InstructEval/blob/ac238a5c329b7132229ad5068e7a3f7a1de01ac9/docs/best_performance.csv) · [MiRA](https://doi.org/10.3390/app16010372)

## WinoGrande

The audited One-Eval adapter omits the source sentence and maps both numeric labels to option B. The validation split has 628 official A labels and 639 B labels. A constant-B predictor earns 1,267/1,267 by the adapter and 639/1,267 by the official key. The prospective study selected 64 content-hash-ranked pairs from 136 eligible pairs, covering 128 questions. The original and restored prompts were sent to four models. There were 1,024 planned responses, 949 available and 75 gateway timeouts. Temperature was zero, top-p was one and the output cap was 8,192 tokens.

| Key on identical responses | Correct both, original prompt | Correct both, restored prompt | Gain in percentage points |
|---|---:|---:|---:|
| Official | 13/128 | 98/128 | +66.41 |
| One-Eval adapter | 16/128 | 14/128 | −1.56 |

The table uses the 32 natural pairs with all 16 responses observed. Four models give 128 model–pair outcomes. The difference between gains is 67.96875 points. The 95% complete-pair bootstrap interval is [50.78125, 83.59375], using 20,000 draws. Over all 64 planned pairs the sharp missing-response bounds are [48.828125, 79.296875]. In each model, pair and prompt condition, the same unavailable response has the same hypothetical parsed option under both keys. For Qwen's 57 complete pairs, the adapter understates the joint gain by 68.42 points and overstates the single-question gain by 5.26 points.

| Restored prompt, 128 questions | Responses | Adapter correct | Official correct |
|---|---:|---:|---:|
| Qwen3.8-27B | 126 | 71–73 | 110–112 |
| GLM-5.2 | 125 | 63–66 | 115–118 |

This comparison was exploratory. Qwen leads by 5–10 answers under the adapter. GLM leads by 3–8 using the official key. On the 123 questions answered by both, the adapter tallies are 68/61 and official tallies 108/114 (Qwen/GLM). Among 59 complete natural pairs, the official GLM lead is 4.24 points, with an exploratory 95% pair bootstrap interval of −0.85 to +9.32 points. In an earlier interrupted capture, the two models answered 101 common questions outside the new panel. The respective scores are 50/46 under the adapter and 96/96 under the official key.

[All 1,024 planned scoring records](evidence/paper-20261115/winogrande_scores.csv) · [Adapter and split audit](https://github.com/ricardofitas/ai-epistemics-hackathon/tree/f9fa5228b8ec22c129ba016790bbda46b6f46aac/experiments/winogrande-prompt-impact-20261113) · [Confirmatory protocol, raw responses and analyses](https://github.com/rfitas-lab/rfdl-lab-os/tree/8e874a208f1d921560fd0beb1e844f6c374310a6/experiments/epistemics-masking-confirmatory-20261115/results/wino-final) · [Marginal-score analysis](https://github.com/rfitas-lab/rfdl-lab-os/commit/57c971acdb67393997d937eafb5c72540f24331b) · [Earlier interrupted capture](https://github.com/ricardofitas/swarm-adaption-hackathon/tree/11f476de47ed539988594b0a8c948471f9890294/experiments/epistemics-verifier-native-20261114/offline-paused-wino)

## Model selection on the public Pythia archive

All 2,534 official correctness indicators were reproduced from five-shot Open LLM Leaderboard predictions. The fixed-B key is a counterfactual applied by this audit. The original archive used the correct key.

| Model | Official correct / 1,267 | Constant-B correct / 1,267 |
|---|---:|---:|
| Pythia-160M | 653 | 603 |
| Pythia-12B | 813 | 651 |

The 12B model's lead contracts from 160 to 48. Group exclusion removed 268 questions associated with 234 earlier items. Of the remaining questions, 485 were used for selection and 514 for assessment. Both rules selected 12B, yielding zero held-out loss from choosing by the constant key.

[Per-item predictions, golds and partitions](evidence/scienceqa-20261115/results/wino_records.csv) · [Selection rule](evidence/scienceqa-20261115/wino_split.md) · [Results by partition](evidence/scienceqa-20261115/results/wino_summary.json)

## Social IQa

The EvalScope study fixed 400 questions, four models and two context conditions. Of 3,200 planned answers, 2,920 met the response criteria. The 280 unknowns comprise 265 HTTP 504 responses, 12 truncations and 3 empty final answers. Two independent automated readers labeled the option expressed in each eligible answer. Their initial labels agreed on all 2,920. All 160 prespecified literal controls agreed with the initial labels. There were two false credits and zero missed credits across eligible responses.

| Outcome | 220 questions complete for all models | Bounds on all 400 questions |
|---|---:|---:|
| Native score gain after restoring context | +28.64 points | +17.875 to +35.375 points |
| Gain based on the option expressed | +28.86 points | +18.00 to +35.50 points |
| Expressed-option gain minus native gain | +0.23 points | −17.375 to +17.625 points |

[Final raw outputs, both sets of labels, protocol and analysis](https://github.com/rfitas-lab/rfdl-lab-os/tree/dd3e854a9ba7ee523a79170333bf057bd5d7529e/experiments/epistemics-masking-confirmatory-20261115/results/siqa-final) · [Independent capture verification](https://github.com/ricardofitas/ai-epistemics-hackathon/tree/f9fa5228b8ec22c129ba016790bbda46b6f46aac/experiments/siqa-terminal-independent-20261115)

## Additional experiments in the appendix

- **Released TabMWP scores.** The replay recovers all 76,860 labels from ten baselines on the same 7,686 questions. Recognizing a unique explicit option after normalization changes 557 labels on 432 questions without reversing any of 45 pairwise comparisons. Treating residual all-zero similarity ties as unanswered then reverses two comparisons. Pretrained TAPEX-base moves from 1,209 to 854 correct, UnifiedQA-small from 936 to 923 and UnifiedQA-base from 1,119 to 1,094. [Complete scoring audit and qualified policy](https://github.com/ricardofitas/ai-epistemics-hackathon/tree/74f2aaf31f0f64c61f8d9efff29e995f43c04a59/experiments/tabmwp-archive-audit-20261114)
- **Spurious option in a controlled prompt.** We crossed two instructions with the presence or absence of “A. None” on 100 SQuAD and 100 numerical TabMWP questions across four models. Of 3,200 requests, 3,086 returned scorable answers. Adding the spurious option under a choice instruction lowered accuracy by 50–63 points on SQuAD and 67.50–79.25 points on TabMWP, allowing all missing answers to vary. [Final report, per-model estimates and verified totals](https://github.com/ricardofitas/ai-epistemics-hackathon/tree/ee04dcb55d547275f46fc3c0a8e5486ee24ecfe8/experiments/external-contract-transfer-20261114/results)

The research plan, public benchmarks, archived model predictions and upstream software predate this sprint. The cohort matching, experiments, replay analyses and this synthesis were produced during the sprint.
