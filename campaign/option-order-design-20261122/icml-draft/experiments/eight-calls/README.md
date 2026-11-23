# Four versus eight shared calls

On each question the two models see the same distinct orders. The target is their accuracy gap averaged over all 24 display orders. The three primary panels hold the checkpoints, numeric prompt and item count fixed. Changing the call budget within a panel reuses the same responses to exactly the same questions.

| Panel | Questions | Adjacency gain at four | Adjacency gain at eight [95% interval] | Residual share |
| --- | ---: | ---: | ---: | ---: |
| HellaSwag 3B | 992 | −0.25% | −7.99% [−11.21%, −4.79%] | 49.09% |
| MMLU 3B | 992 | −3.41% | −9.68% [−13.07%, −6.26%] | 49.85% |
| English LogiQA 2.0 3B | 992 | +2.32% | −1.69% [−5.04%, +1.64%] | 46.22% |
| HellaSwag 1.5B/2B, separate sensitivity | 6,144 | +1.17% | −6.05% [−7.29%, −4.82%] | 48.21% |

Gain is 100 times one minus the full-adjacency MSE divided by the precedence-minimax MSE at the same budget. Positive values favor adjacency. At eight calls, the full design draws two distinct Williams blocks from the six that partition all orders. It improves on the certified precedence design exactly when the residual share is below 5/11 (45.45%), provided the precedence residual is positive. The numerator measures variation among the six Williams block means. The denominator measures the variation left after removing the constant, position and precedence effects. Both are summed over the same items before taking the ratio.

The model pair on the primary panels is Qwen2.5-3B-Instruct and SmolLM3-3B. The larger HellaSwag panel uses Qwen2.5-1.5B-Instruct and Granite-3.3-2B-Instruct, and shares 227 questions with the matched HellaSwag panel. Each point MSE is exact conditional on the observed questions. The intervals use 50,000 paired bootstrap samples of questions with fixed domain or subject counts. They describe item composition separately for each panel. Four-call outcomes were already published when the eight-call comparisons were specified. [Analysis plan](analysis-plan.md) · [Exact rational MSEs, all baselines and paired intervals](results.json)

## Replay

Run these commands from the manuscript directory. The first requires Python 3.10 or later and the standard library. The second also reproduces the stored bootstrap with NumPy 2.2.6 and one BLAS thread.

```sh
python3 -B experiments/eight-calls/replay.py --check
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -B experiments/eight-calls/replay.py --intervals --check
```

The replay integrates the randomization distribution of each sampler. A second computation checks every eight-call balanced item risk with exact position and precedence projections and Williams group means. The profile archive contains counts of positive and negative paired-correctness masks by stratum. Bit positions index the 24 permutations of the displayed option labels in lexicographic order. The inputs contain no question text or source identifiers. The source builder records the original roster, export or checkpoint hashes. Rebuilding the profile archive from upstream inference materials also requires PyArrow. [Profiles](profiles.json.gz) · [Source digests](source-receipts.json) · [Builder arguments](build_profiles.py)

The earlier matched HellaSwag package includes both models' correctness masks and the original per-panel results. The methods and four-call comparators for the other cohorts are in the manuscript. [Matched HellaSwag archive](https://github.com/ricardofitas/ai-epistemics-hackathon/blob/077d34c223c9d6bad32bfeadbbe9972ac77658e0/evidence/rig-20261123/four-orders-hellaswag-3b/RESULTS.md) · [Manuscript](../../paper.pdf)
