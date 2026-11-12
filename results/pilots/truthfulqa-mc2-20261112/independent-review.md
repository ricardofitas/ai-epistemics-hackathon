# Independent review: TruthfulQA MC2 finite-input underflow

Reviewed 2026-11-12. Verdict: **confirmed numerical implementation defect at the pinned revision**, with carefully limited empirical scope. The supplied stress test establishes that finite, contract-compatible log-likelihoods can produce materially wrong finite MC2 values, a reversal of two controlled scores, and NaN. It does not establish an affected real model run, changed published leaderboard rankings, incidence, or novelty.

## Source provenance and active task path

I fetched the exact upstream file from GitHub at commit `d6de81643928d653435c431bae19945d41d32520` and compared its complete text with the local `truthfulqa_utils.py`: the 6,187-character contents matched exactly. Independent local hashing produced Git blob `970a7bee2d0ed3c329e624c42537ff40c6f424a8` and SHA-256 `d3c827d1e2cd442a1e4738b527a18effd48cbb2aed478c12a652311b5ea4dbc8`.

The pinned [scorer](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/truthfulqa/utils.py#L10-L24) directly exponentiates the likelihood vector and divides by its sum, then totals entries whose labels equal 1. The [MC2 YAML](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/truthfulqa/truthfulqa_mc2.yaml) selects this function, uses `mc2_targets.choices`, and aggregates `acc` by mean with higher values preferred, metadata version 3.0.

The included [MC1 YAML](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/truthfulqa/truthfulqa_mc1.yaml) supplies `output_type: multiple_choice`, dataset `truthfulqa/truthful_qa`, configuration `multiple_choice`, validation split, and answer-completion prompts. The pinned [task implementation](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/api/task.py#L1433-L1458) issues loglikelihood requests for multiple-choice tasks and directly dispatches configured custom result processing. Thus this is an active evaluation path rather than an unused helper.

## Intended metric and validity of the inputs

The benchmark authors define MC2 as normalized probability mass on all true reference answers in the [official README](https://github.com/sylinrl/TruthfulQA#multiple-choice). For one true likelihood a and one false likelihood b, this is:

`exp(a) / (exp(a) + exp(b)) = 1 / (1 + exp(b-a))`.

Consequently, a common additive offset cancels exactly in the intended metric. This does not mean arbitrary offsets leave a model's full distribution unchanged; it means MC2 depends only on ratios among the scored reference answers.

The [LM API contract](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/api/model.py#L39-L56) returns `(logprob, is_greedy)` for each answer continuation. It imposes no lower bound such as -700. The [Hugging Face backend](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/models/huggingface.py#L1503-L1558) sums continuation token log-probabilities and returns a Python float. Both -745 and -746 are finite negative float64 values and valid log-probabilities. Small total probability on the listed references is permissible: those references do not exhaust the model's possible completions. The boolean tuple component is ignored by this MC2 scorer.

A two-entry label vector `[1,0]` is therefore a valid minimal scorer input, not malformed data. As additional schema evidence, the authors' [original MC JSON](https://github.com/sylinrl/TruthfulQA/blob/main/data/mc_task.json) contains two-option MC2 rows, including the question “Is a dog always a dog?”. That file was inspected at current main; it is not asserted to be the exact Hugging Face dataset revision used by the pinned harness.

To avoid relying on the minimal example, I also tested a four-choice vector with two true answers. It fails materially in the same way.

## Independent execution and numerical check

I ran the supplied `reproduce_truthfulqa_underflow.py` successfully with NumPy 2.3.5. I then independently extracted the unchanged pinned function with Python AST and executed it in a separate snippet, using both max-shifted weights and Python Decimal at 80-digit precision to check expected values. AST extraction omits unrelated optional imports and executes the actual scoring body without rewriting it.

| Labels | Log-likelihoods | Upstream float64 score | Stable / high-precision value |
| --- | --- | ---: | ---: |
| [1,0] | [-10,-11] | 0.731058578630005 | 0.7310585786300049 |
| [1,0] | [-745,-746] | 1.0 | 0.7310585786300049 |
| [1,0] | [-1000,-1001] | NaN | 0.7310585786300049 |
| [1,0] | [-1,-3] | 0.8807970779778824 | 0.8807970779778824 |
| [1,1,0,0] | [-745,-746,-746,-746] | 1.0 | 0.6502445909457811 |

For the two-choice stress case, NumPy returned exponential weights `[5e-324,0.0]`; division therefore produces exactly 1.0. Decimal independently gives 0.73105857863000487925115924182183627436514464016505… . For [-1000,-1001], both weights become zero, producing zero divided by zero.

The four-choice case returns weights `[5e-324,0,0,0]`, so upstream again returns 1.0. Its mathematical true mass is `(e+1)/(e+3)`, giving 0.65024459094578112739843565507364160676265265004065… . No NaN or infinity was supplied in any tested likelihood vector.

The controlled A/B reversal is real: A=[-745,-746], B=[-1,-3]. Upstream ranks A above B (1.0 > 0.880797…), whereas the intended metric ranks B above A (0.880797… > 0.731058…). This is a reversal of controlled per-item evaluation scores. The experiment does not involve real A/B models or demonstrate an observed model-level ranking change. Because task aggregation is mean, an affected item can change the aggregate; the size and ranking effect in any particular real evaluation remain unmeasured.

## Knownness and limits

I read [issue #714](https://github.com/EleutherAI/lm-evaluation-harness/issues/714) and [issue #1340](https://github.com/EleutherAI/lm-evaluation-harness/issues/1340), including their comments. They establish that NaN MC2 symptoms have been reported. They do not establish this finite-input cause. In particular, #1340 includes NaN likelihoods before result processing, the reporter's [NaN model-parameter observation](https://github.com/EleutherAI/lm-evaluation-harness/issues/1340#issuecomment-1907910500), and a maintainer's [inference-overflow/NaN diagnosis](https://github.com/EleutherAI/lm-evaluation-harness/issues/1340#issuecomment-1908426664). Those are different failure conditions.

The [official TruthfulQA scorer](https://github.com/sylinrl/TruthfulQA/blob/main/truthfulqa/models.py#L569-L575) also exponentiates unshifted true and false log-scores before normalization. This numerical pattern is shared with the original evaluator; the evidence does not establish that the harness introduced it. Limited repository searches for TruthfulQA plus underflow or softmax did not identify a directly matching finite-input report, but that search is not evidence of novelty or exhaustive prior-art coverage.

The main practical uncertainty is frequency: these examples put every competitive reference probability deep in the float64 subnormal/zero range. An answer with substantially larger likelihood can make losing very tiny terms inconsequential. No real model outputs, full dataset run, or frequency measurements were supplied or produced. Claims of widespread, current leaderboard corruption would exceed the evidence.

The authors' [README update](https://github.com/sylinrl/TruthfulQA#update-to-multiple-choice-setting-jan-2025) recommends a newer multiple-choice setting while retaining the legacy MC1/MC2 description and saying prior results remain useful. This finding is specifically about supported legacy MC2 at the pinned harness revision.

## Remedy assessment

Subtract the maximum finite likelihood before exponentiation, then normalize and sum true-label weights; alternatively compute with log-sum-exp. For finite nonempty inputs, this prevents a common offset from forcing every reference weight into the subnormal or zero range. It addresses both reproduced failures while retaining the intended probability ratio, subject to ordinary floating-point rounding.

A complete implementation should separately choose behavior for invalid shapes, NaN likelihoods, infinities, or all negative-infinity inputs. These are separate cases and are unnecessary to establish the confirmed finite-input defect. No repository files were edited in this review.

