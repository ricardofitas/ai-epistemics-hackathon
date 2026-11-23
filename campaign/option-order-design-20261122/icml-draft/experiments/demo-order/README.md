# Classification with reordered demonstrations

The GPU evaluated Qwen2.5-3B-Instruct and SmolLM3-3B (Q4_K_M) under the same plain-text classification prompt per task. Each of eight quartets was assigned eight different validation questions. The candidate digit set was 1–2 on SST-2 and 1–4 on AG News. GPU decoding used llama.cpp b12631, temperature zero, and a digit grammar. Each question has 24 predictions per model. Within each released array, the first index is lexicographic demonstration order and the second is query. The included SHA-256 identifiers hash stripped source texts. The task reference is conditional on the selected short texts, prompts and checkpoints.

From the manuscript directory, run the following commands with NumPy installed.

```sh
python experiments/demo-order/analyze.py
python experiments/demo-order/analyze.py --costs
```

The first command replays the two task comparisons from the released class predictions. The second replays the seven retrospective option-order comparisons. Intervals resample entire quartets together with their assigned questions. Uniform equivalents count distinct orders drawn without replacement. The GPU worker uses the environment paths described in its docstring and expects the pinned queue GPU. [Frozen protocol and worker](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/6eb187c570809b3e0d2f3b65db557946adbe5253)

The first worker was excluded before scoring because its training quartets repeated examples. The corrected run verified class balance and disjointness before inference. [Corrected registration](https://github.com/ricardofitas/ai-epistemics-hackathon/commit/432309e80614d4b8f74ec740f3ffde901c29838c)

| Task | Precedence MSE change vs rotations | Quartet 95% interval for MSE change | Uniform calls matching eight precedence calls |
| --- | ---: | ---: | ---: |
| SST-2 | +21.66% | [−2.48%, +53.64%] | 13 |
| AG News | +31.82% | [+11.47%, +62.06%] | 12 |

Positive changes in this table indicate higher MSE for precedence. The numerical release uses the opposite sign to express a gain. [Exact risks and intervals](results.json) · [Response archive](responses.json) · [GPU receipt](receipt.json) · [Seven option-order cost comparisons](option-costs.json)
