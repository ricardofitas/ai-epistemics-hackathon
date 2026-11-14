# Blinded interpretation of released TAPEX-base replies

Two model families independently interpreted each of 100 stratified archival replies and 12 positive/negative controls. Original model identity, the stored answer, the source table, original score and original option order were hidden. A single model generation reached an incomplete terminal. Both Qwen3.8-27B and GLM-5.2 passed all 12 controls and agreed on the other 99 complete study pairs. Checks of the archived provider responses reproduced 224 terminal records, 223 complete responses and a provider-reported cost of 0.147684 credits.

| Original first-choice grading stratum | No identifiable option | Identified correct option | Identified a different, incorrect option | Unknown |
|---|---:|---:|---:|---:|
| Historical evaluator awarded credit (50 sampled) | 40 | 2 | 7 | 1 |
| Historical evaluator withheld credit (50 sampled) | 42 | 3 | 5 | 0 |

There were 443 originally credited and 795 originally uncredited cases among the 1,238 all-zero similarity replies. Weighting the two sampled strata by these counts estimates that the two judges would find no identifiable option in 82.57–83.28% of that pool. Only the one unknown explains that narrow range; it excludes sampling variation and shared judge error. The two models provide evidence about the meaning of the answer text, with controls. Independent human judgments remain outstanding.

The historical reply was produced by TAPEX base. These model judges interpret that archived text, without rerunning TAPEX. A separate private 40-row reader packet contains 16 sampled items per stratum and eight controls. Send readers the blind file and reader instructions only. The deblinding file is for the coordinator. No human responses have been collected. [Adaption run and terminal evidence](https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43626108168).
