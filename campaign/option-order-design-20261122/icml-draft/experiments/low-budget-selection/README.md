# Selecting an eight-call sampler on a new benchmark

We tested whether a small set of labeled calibration questions could identify the better eight-call sampler for a pair of 3B models on a new benchmark. P balances position and pairwise precedence. W additionally balances directed adjacency and draws two different Williams blocks. Both estimate the mean accuracy gap across all 24 answer orders.

| Benchmark | Calibration / held out | Primary choice | Held-out W gain [95% interval] | Primary policy gain vs. always P |
| --- | ---: | --- | ---: | ---: |
| ARC-Challenge | 64 / 192 | P | -5.54% [-12.22%, +1.38%] | -6.25% |
| OpenBookQA | 64 / 192 | P | -8.27% [-16.11%, -0.54%] | -7.39% |
| Cosmos QA | 64 / 192 | P | -3.02% [-10.68%, +4.34%] | -4.50% |
| RACE | 32 / 96 | P | -8.24% [-19.24%, +2.97%] | -5.86% |

The registered primary pilot and the fixed precedence rule both picked the lower-MSE design on four out of four held-out panels. Across the possible pilot-order assignments, the primary rule repeats the lower-MSE choice with probabilities 49.6%, 56.0%, 52.7% and 63.8%, respectively. Only the panel-specific OpenBookQA interval excludes zero. Every four-panel simultaneous interval includes zero. The full-panel error includes the uncertainty in the calibration-item gap estimates. The primary policy had 4.50–7.39% higher expected MSE than always using P.

A positive held-out W gain indicates lower gap MSE than P. Each interval describes the sensitivity of the fixed-panel comparison to resampling held-out questions. The last column counts the calibration questions in the reported accuracy-gap estimate and charges their eight calls. It averages over pilot randomness on the fixed calibration split. All four benchmarks are reported. [Full numerical results](results.json) · [Prospective protocol](protocol.md)

## What was fixed before scoring

Qwen2.5-3B-Instruct and SmolLM3-3B used Q4_K_M weights and the same numeric-choice prompt and physical RTX 4060 Ti as the preceding study. Each primary panel contributed 64 calibration questions and 192 held-out questions. RACE contributed 32 and 96 because of the two tokenizers' joint passage-length limit. Each distinct passage occurs once in its panel. Question groups and sparse order assignments were made public before the GPU reference run started. The registered choices were published using only the sparse calibration observations before the held-out answers were scored. Four-choice questions with explicit slot-relative answers were screened out. [Registration before inference](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/558cf004b26ccee9599e3be09b1a174f0f6d8d5c) · [Choices before held-out scoring](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/bbf238ebe249338ffe99a25c39000a9027cf9705)

The source audit covers the four validation files. The measurements concern these screened rosters. There were no exact normalized question-stem matches with the three 3B development cohorts. Earlier tests using another model pair shared 252 ARC-Challenge questions and 155 OpenBookQA questions with these rosters. [Admission counts and overlap audit](admission.json)

The primary residual pilot scores eight observed differences in correctness on each calibration question. The score is unbiased for the item MSE of P minus W. Its sign averaged across calibration questions selects W when positive and P otherwise. A second rule evaluates the same contrast from eight orders drawn directly from P. Its results and a 24-order calibration diagnostic are included in the numerical release. Each eight-call rule uses its own observations. The development comparison reports the signed-score variability and calibration-item gap risk on the three previously published 3B panels. [Development-only measurements](development.json)

The physical reference used 43,008 inference calls. One deployed policy would use 14,336 calls across both models on the same 896 questions, including calibration.

## Reproduce

Run these commands from the manuscript directory. The check of the public choices uses only the standard library and the eight revealed responses. The full analysis uses NumPy 2.2.6. It checks the item risks through both block enumeration and feature projection, then reproduces the 50,000 paired item resamples and the 20,000 rerandomizations of the calibration orders. It additionally verifies the primary policy's selection probability by exact convolution of integer ticket counts.

```sh
python3 -B experiments/low-budget-selection/verify_decisions.py
python3 -B certificates/verify_sparse_pilot.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -B experiments/low-budget-selection/analyze.py --check
```

The signed profiles contain the positive and negative correctness masks for model A minus model B. Bit zero is the first lexicographic display order. Question keys are hashes of passages or stems. The registered roles and sparse blocks can be reconstructed without reading a full response profile. Models, source revisions, ordered prediction checksums and research-queue timings are bound by the receipts. The rig staging script uses the original native decoder, tokenization transport and directory structure. Public numerical replay needs only the included files. [Registered assignments](registered-design.json) · [Sparse observations](pilot-observations.json) · [Recorded choices](decisions.json) · [Profile archive](profiles.json.gz) · [Run receipt](run-receipt.json) · [Independent source-to-mask check](join-audit.json) · [Source revisions](source-pins.json)

## Apply the primary rule

Create a JSON file containing a benchmark name and a list of labeled calibration questions identified by distinct IDs. For example, the input for a single question can be written as follows.

```json
{"benchmark":"my-benchmark","items":[{"id":"q-001"}]}
```

The first command returns eight display orders for each question, using zero-based semantic option labels. Run both models on the assigned orders and score their responses against the answer key. Append the eight differences, model A correctness minus model B correctness, in that order to each input item under the key `correctness_differences`. The second command returns the selected deployment sampler and the mean signed item-risk estimate. Use independent blocks from that sampler on the held-out questions. Fix IDs and calibration membership before observing responses.

```sh
python3 experiments/low-budget-selection/select_design.py orders questions.json
python3 experiments/low-budget-selection/select_design.py choose scored-questions.json
```

The fixed baseline uses the precedence sampler on every item. The primary pilot can cost precision on calibration items even though it uses the same number of calls. The registered experiment measures both the correctness of the choice and the effect on the complete benchmark estimate. [Four-option samplers](../../four_option_budgets.py)
