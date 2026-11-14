# Does adding one spurious option change measured answer accuracy?

We crossed two instructions and two option displays on 100 SQuAD v1.1 and 100 TabMWP source questions, for Gemma-4-31B-IT, Qwen3.8-27B, DeepSeek-V4-Flash and GLM-5.2. Every source–model combination was run in four separate conditions. Questions were hash-selected before collection and excluded normalized matches to the earlier project diagnostic pool; model training exposure is unknown. SQuAD exact match and exact numeric TabMWP scoring were fixed before requesting the outputs. Conditions used the same context, temperature and output cap within each source question.

The independent replay validated 3,180 terminal response objects from 3,200 distinct planned requests. There were 3,086 complete answers and 114 responses outside the scoring endpoint. They consist of 94 incomplete terminal responses, 11 missing terminal events and 9 HTTP 504 responses. The provider reported 2.808416 cost units on available usage records. The uncached rate-card estimate from actual input and output tokens is 2.870183 credits. No account invoice or currency conversion enters this report. There were 36 explicit HTTP 429 attempts, recovered as applicable. Effective throughput was 1394 eligible responses/hour.

| Source | Accuracy drop from adding A. None, under choice instruction | Change in this drop when moving from free-response to choice instruction | Observed dummy selections under choice instruction |
|---|---:|---:|---:|
| SQuAD | 50–63 pp | 57.75–73 pp | 284/400 |
| TabMWP | 67.5–79.25 pp | 68–81.25 pp | 280/400 |

Values are equal-weight averages across the four model families. Each range gives the minimum and maximum compatible effects across unavailable response scores on the fixed source set. These ranges describe unknown answers. Additional descriptive sampling uncertainty is recorded in sampling-intervals.json, resampling SQuAD articles and TabMWP questions, with no familywise-confidence claim.

| Model | SQuAD drop, pp | TabMWP drop, pp |
|---|---:|---:|
| gemma-4-31b-it | 80–84 | 91–95 |
| qwen3.8-27b | 44–56 | 81–88 |
| deepseek-v4-flash | 40–57 | 61–70 |
| glm-5.2 | 36–55 | 37–64 |

On the same panel of 100 reading questions, an exploratory SQuAD token-F1 rescore bounded the four-model mean decline at 61.83–74.83 points. It counts partial overlap with any accepted source answer.

## Model-selection test

For each SQuAD condition, retained winners include any model whose best possible score reaches the highest guaranteed score. Regret measures the gap to the best model on the independent, clean TabMWP panel, over unknown answers.

- choice_none: qwen3.8-27b (4–6 pp target regret), deepseek-v4-flash (18–20 pp target regret), glm-5.2 (0–2 pp target regret).
- free_clear: glm-5.2 (0–2 pp target regret).

The admissible winner sets overlap. These outputs do not establish that the formatting change forces a different selection policy.

A separate oracle test gave a correct option and a wrong option on the same 24 future TabMWP questions. The linked research artifacts record the frozen bare-number and exploratory option-aware readings. A third test replays ten published TabMWP baselines and changes scoring alone. These experiments address different mechanisms.
