# Full reproduction of the team's GAMMAF analysis

The complete offline reproduction succeeded in [GitHub run 43616684768](https://github.com/ricardofitas/ai-epistemics-hackathon/actions/runs/43616684768), execution commit `80b5546034be2f854f637575b52016f5066c9262`, based on Antonio's `d4419f1` branch. It made **zero model or judge calls**.

The runner retrieved and authenticated all **28 raw trajectory files, 111,232,152 bytes**, against the fixed public source commit and exact Git blob identities. The previous missing-input blocker is closed. All **38 tests passed**, with no errors, failures or skips. Independent reconciliation of the ZIP, receipts, JUnit, source pins and runner output reproduced **all 27 comparison checks**, including the original inferential statistics.

The terminal audit remains **227 discrepancies among 9,600 detector debates: 156 false credits and 71 missed credits**. The 1,600 controls retain zero discrepancies. All 11,200 debates loaded with raw round grids. These are archived conversations; this reproduction does not add new independent questions or model responses.

The isolated population-accounting correction preserves shadow classifications and all existing coherent per-population/per-cell rates. The corrected detector rate is **217/5,518 = 3.9326%**, control rate **323/1,341 = 24.0865%**, and combined rate **540/6,859 = 7.8729%**. The combined mean is now **1,892/540 = 3.5037 events per affected debate**; the detector mean is **559/217 = 2.5760**. Frozen original results were preserved.

| Archived held-out result | Delivered accuracy |
|---|---:|
| EpistemicGuard-Hard | 85.2995% |
| EpistemicGuard-Soft | 85.5208% |
| Best pooled baseline, XG-Guard | 86.3281% |

The pooled rows use different conversation sets and are descriptive. Matched comparisons within each baseline's conversations reproduce improvements over some baselines, but the strict claim of beating all six methods remains unsupported. The guard performs **offline terminal reaggregation** on conversations produced under the previous methods. Shadow transitions remain observational rather than evidence of causal message transmission.

Earlier YAML and source-pin preflight failures happened before any raw source download or model use; they are engineering attempts, not scientific experiments. A terminal LF added to local text snapshots caused the initial pin mismatch; strict exact Git identities and an EOF-compatible derivative patch resolved it. The final artifact contains `fig_leaderboard.png` despite the `--no-figures` flag, so this is not a zero-figure execution.

The raw cache was authenticated on the pinned runner and is not included in its uploaded artifact. Independent verification here checks retained source receipts and calculations, without downloading those files again or rerunning the experiments. See `FINAL_INDEPENDENT_VERIFICATION.json` for the exact verification boundary.
