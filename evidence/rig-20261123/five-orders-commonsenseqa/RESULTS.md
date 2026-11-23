# Five-option CommonsenseQA evaluation

The 192-question panel used the pinned Qwen2.5-3B-Instruct and SmolLM3-3B
Q4_K_M weights, one physical RTX 4060 Ti and a single-token numeric prompt.
All 120 orders were scored for both models. Each compared estimator uses
five shared orders per model and question and targets the full-order
accuracy gap.

| Design | Exact gap MSE | Relative MSE reduction vs. position minimax | Expected adjacency coverage |
| --- | ---: | ---: | ---: |
| Position minimax | 67337/663552000 | +0.00% | 12.700 |
| Maximum adjacency | 66467387/663552000000 | +1.29% | 15.000 |
| Uniform position balance | 94279/928972800 | -0.01% | 12.679 |
| Ordinary cyclic | 14401/132710400 | -6.93% | 5.000 |

The maximum-adjacency gain was **+1.29%**.
The paired 95% bootstrap interval was **[-0.14%, +2.75%]**.
The upper endpoint falls below the 5% practical margin. The full-order Qwen minus SmolLM3 gap was
+37.118 percentage points. The interval describes
item-composition uncertainty for this screened panel and model pair.

The run `icml-commonsenseqa-five-orders-20261123-1` started 2026-11-23T21:15:20.943056+00:00 and released
2026-11-23T21:35:19.469627+00:00. It completed 48
checkpoints covering 46,080 reference calls.
Each design costs 1,920 deployment calls
across both models and the whole panel. The BOINC mode was restored.

## Verified theory

The position-balanced normalized minimax risk is exactly 9/25 for
real-valued contrasts and differences of binary correctness. Requiring
maximum directed adjacency in every draw means 15 of 20 ordered pairs
and raises the correctness lower bound to 23/55. For real contrasts the
certified interval is [0.47084, 0.47087]. That design supplies the empirical
maximum-adjacency arm and provides a valid upper bound for correctness
contrasts. The four risks above are measured on realized profiles.

The attaining position-minimax template itself has coverage 15.
Across slot relabelings its coverage is 11, 12, 14 or 15 with multiplicities
48, 12, 48 and 12. The position-minimax arm averages 12.7 covered pairs.
The constrained arm achieves 15 in every draw.

## Offline replay

Run `python3 verify_position.py`, `python3 verify_binary_adjacency.py`,
and `python3 verify_real_adjacency.py` to verify the certificates.
Run `python3 verify_commonsenseqa.py` to independently reproduce the exact
empirical MSEs and reference gap from the released correctness masks.
The proofs and this point-estimate replay need no internet, model
weights, GPU or nonstandard Python modules. The rig transport files
record how the token fixtures and native GPU scores were produced.
