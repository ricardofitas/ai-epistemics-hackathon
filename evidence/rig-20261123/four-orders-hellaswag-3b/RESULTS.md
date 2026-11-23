# Matched three-benchmark Four Orders comparison

HellaSwag used the pinned Qwen2.5-3B-Instruct and SmolLM3-3B Q4_K_M
checkpoints, the standard numeric prompt and the physical RTX 4060 Ti
used for the frozen MMLU and LogiQA panels. HellaSwag context and endings
populate the question and choices fields of the same prompt template.
Each panel contains 992 items. Four shared orders per model and item
define the deployment budgets. All 24 orders per model define the reference.

| Panel | Williams MSE reduction versus precedence minimax | Versus ordinary cyclic |
| --- | ---: | ---: |
| MMLU validation | -3.409% | +12.202% |
| LogiQA 2.0 English test | +2.318% | +20.566% |
| HellaSwag validation | -0.245% | +6.664% |

On HellaSwag the paired bootstrap bounds for the per-item 5% practical
margin are [-1.695, -0.560] in units of 0.001.
The paired bootstrap interval lies below the 5% practical margin. The earlier MMLU and
LogiQA joint decision follows their original protocol. These are
benchmarks as sampled under the fixed setup. The earlier 6,144-item
HellaSwag experiment used different checkpoints and a different prompt. As a descriptive check
by item origin, the precedence-minimax gains were +0.128% on 765
previously unused questions and -1.479% on 227 previously
scored with different models. The primary analysis uses all 992 questions.
The descriptive paired 95% bootstrap interval for the relative Williams
gain against precedence minimax was [-2.93%, +2.39%].

The HellaSwag precedence-minus-Williams contributions, in mean per-item
risk units of 0.001, are +8.726 for adjacency,
-9.479 for residual and +0.701
for their interaction. The sum is -0.053.

Run `icml-confirm-20261123-hellaswag-3b-3` started 2026-11-23T20:08:21.291304+00:00 and released
2026-11-23T20:46:21.920150+00:00. It completed 248
prediction checkpoints and 47,616 reference calls.
Scoring used the independent GPU-release receipt. The frozen run and
source pins are in `public-commitments.json`. Two scoring passes were
byte-identical. With Python 3, run `python3 verify.py` from this
directory to check all five exact MSEs and the reference accuracy gap
from compact correctness masks. This replay requires no internet,
model weights or GPU.
