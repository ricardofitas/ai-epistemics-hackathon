# Prospective five-option CommonsenseQA evaluation

Take the first 192 eligible questions in SHA-256 order from CommonsenseQA
validation at revision 94630fe30dad47192a8546eb75f094926d47e155. Use unique ID
and normalized stem, five distinct nonempty options, one item per normalized
question concept, and a strict 512-token limit under both models and all
orders. Eligibility uses no official answers or inference outcomes. Freeze
the exact label-free roster and token fixtures before GPU admission.

Reuse the exact Qwen2.5-3B-Instruct and SmolLM3-3B Q4_K_M checkpoints from the
matched 3B four-option study. Preserve its numeric prompt template with
choices 1 through 5, single-token argmax and lowest-index tie breaking.
Use the same RTX 4060 Ti and pinned llama.cpp C ABI with eight isolated
contexts. Qualify the five-label worker with two cold replays of one
synthetic item across all 120 orders per model and require exact choice
agreement. Checkpoints contain eight complete model-item profiles and
are bound to the roster and fixture hashes. A failed dispatch before
inferencing does not count as a scientific attempt. Resume only complete
pinned checkpoints with the same device. Open official answers only after
complete inference and a verified successful queue release.

Evaluate exact paired MSE against the 120-order accuracy-gap reference.
The fixed primary designs use five shared orders per model and question.
The position minimax sampler draws independent uniform option and slot
relabelings of the certified template. The maximum-adjacency sampler uses
the five option-relabeling orbits, uniform inside each orbit, with the
certified real-score upper-bound mixture (82680, 3199, 5472, 3177, 5472)
over total 100000. Its risk upper bound also applies to correctness
contrasts. Its optimality within that class remains open.
Ordinary cyclic and uniform position balance are descriptive controls.

Primary effect is relative panel MSE reduction from maximum adjacency
against position minimax. Report a 95% paired item bootstrap interval
(50000 draws, seed 22112305) and the threshold 5% relative gain. The
five-order design costs 1,920 calls on the 192-item panel across both
models. Reference cost is 46,080 actual model-item-order calls, excluding
qualification. The fixed panel size is an engineering choice for this
exhaustive extension. Interpret uncertainty from the interval and do not
expand or discard the panel based on the result. Check all exact risks
with separate integer enumeration and report all designs.
