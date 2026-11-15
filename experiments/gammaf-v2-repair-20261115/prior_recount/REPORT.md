# GAMMAF v2 fixed-population recount

This is an offline reanalysis of the original abbreviated-option live run, not a corrected-stimulus experiment. The source SQLite has Git blob SHA1 `64a01bda49814f1950aa9f9781fbc732dddbd0db` at source commit `94cc84d54df5f8df83a9470d035d94860a05d6cf`.

All 512 paired-arm checkpoints were recovered: 64 questions × 4 graphs × 2 policies. Each policy has exactly 3,584 observed originally honest-agent transition slots (7 agents × 2 transitions × 256 worlds), with no ABSTAIN/missing votes. Round-1 votes match on every paired world. The original published event edge count matches each stored checkpoint individually.

| Outcome (debates) | Terminal filtering | Early intervention | Change, pp | Question-cluster 95% interval, pp |
| --- | ---: | ---: | ---: | --- |
| Published policy-gated switch | 64 | 23 | -16.016 | [-23.828, -8.594] |
| Fixed-population gold-to-target switch | 89 | 65 | -9.375 | [-15.234, -3.906] |
| Same, adjacent original insider held target previously (flags ignored) | 70 | 43 | -10.547 | [-17.188, -4.688] |
| Any originally honest gold-to-wrong switch | 168 | 154 | -5.469 | [-8.984, -2.344] |
| Correct plurality of all seven initially honest agents | 52 | 47 | -1.953 | [-7.813, +3.516] |
| Correct actually delivered answer | 40 | 39 | -0.391 | [-5.078, +4.297] |

Intervals use 20,000 bootstrap resamples of whole question IDs within task, keeping all graphs, rounds, agents and both policies together. The reanalysis and its metrics are post hoc. The selected original question panel is not a representative generalization test.

The reduction in votes switching to the wrong target persists under a fixed originally honest population; it cannot all be explained by policy-dependent event eligibility. The original indicator nevertheless depends strongly on its gates. Holding the complete terminal-filter vote trajectories fixed and applying the paired inline flag schedules reduces counted switch-debates from 64 to 24. Conversely, inline votes count 40 switch-debates under terminal-filter masks and 23 under their own masks. These are counterfactual rescoring diagnostics, not actual interventions or a causal decomposition/mediation estimate; do not describe any percentage of the treatment effect as caused by masking.

The delivered-accuracy interval permits gains and losses; this analysis does not establish equivalence. Contact/co-occurring votes do not identify which message persuaded an agent. Full option text is still missing from the original run, which limits substantive interpretation. The separately frozen repaired-stimulus trial is needed to address that limitation.

Reproduce from the committed source SQLite (read-only):

```sh
python scripts/fixed_population_recount.py --sqlite artifacts/live_adaption_v2.sqlite --population artifacts/repaired_population_source.json --out artifacts/fixed_population_recount
```

Only `numpy` beyond the Python standard library is required. No network/model calls or paid requests occur. Missing observations/rounds/masks and ABSTAIN parsing sentinels remain unknown and receive explicit bounds; no forward fill or zero imputation is used. The original data happen to be complete.
