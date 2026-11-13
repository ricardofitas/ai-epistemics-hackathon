# TREC-COVID Round 5 actual-run diagnostic — 13 November 2026

This is an executed, frozen **offline consequence diagnostic** of the advice error that a nonsignificant difference establishes functional equivalence. It applies that rule to actual archived run outputs; it does **not** show that a user followed the advice or that a benchmark is defective.

## Execution and primary result

The official NIST Round 5 archive supplied all 126 prespecified run files, with matching residual qrels. All 127 source files passed exact byte and decompressed hash checks. The official trec_eval v10.0 source (commit `f4253652c8efd0d86ddffd0d163cc0a0f813111a`) had all 121 tracked blobs verified; its newly pinned local executable passed the official quicktest and 28 synthetic checks. Scoring began at 10:10:27 UTC, after the verified Git freeze `3f0f6eb9285272e954a44c363ae50ffcab57ee73` (10:10:02 UTC). The v3 protocol SHA256 is `b6a893abf4a43b6d356d4b8bdc150beec31b175ab30b6d5a872a9b47ca4586bf`.

Primary metric: canonical nDCG@10 per each of 50 topics. The advice's offered Wilcoxon branch was replayed two-sided at alpha .05 for **all 7,875** unordered candidate pairs, with no discarded weak or duplicate runs. All 126 runs scored completely.

| All-50-topic outcome | Result |
|---|---:|
| Wilcoxon p ≥ .05, which the erroneous advice would call equivalent | 1,931 / 7,875 pairs |
| Of those, distinct 50-topic nDCG@10 vectors | 1,929 |
| Of those, identical 50-topic vectors | 2 |
| Absolute observed mean gap among the 1,931: median / maximum | 0.028166 / 0.151070 |
| Symmetric 95% bootstrap interval frontier among the 1,931: median / maximum | 0.084372 / 0.236068 |
| Sign-flip sensitivity with p ≥ .05 | 1,869 / 7,875 |

The frontier is `max(abs(CI_lower), abs(CI_upper))`, the smallest symmetric margin containing that descriptive 95% interval for a paired mean difference. **No practical-equivalence margin was prespecified or justified**, so neither the nonsignificant pairs nor their confidence intervals demonstrate equivalence or practical inequivalence. The raw 50-topic Wilcoxon null concerns symmetry of paired score differences about zero, not an equivalence claim. Pairwise estimates share systems, teams and topics; 1,931 is a count of dependent pair comparisons, not independent scientific replications or a model error rate.

One post-hoc illustration is `fc3-qrel-hidden` versus `rk_bm25_dfr_lmd_rrf`: the absolute mean nDCG@10 gap is 0.151070 while the Wilcoxon p-value is 0.05411. This is the maximum observed gap within the nonsignificant subset and must not be represented as a typical or prespecified example.

## Secondary topic split

A score-blind 25/25 topic split yielded 2,985 discovery-nonsignificant pairs. Their confirmation absolute gap had median 0.058984 and maximum 0.323088. Exactly one of those pairs had a confirmation Wilcoxon result below .05 after Holm adjustment across all 7,875 pairs. **That pair was already significant in the full 50-topic analysis**, so this secondary result is not a reversal among the 1,931 primary nonsignificant pairs. The sign-flip sensitivity yielded four Holm flags. These comparisons do not constitute future deployment, independent model training, or a selection-regret estimate.

## Provenance and scope

The first frozen launch stopped before scoring because our validator rejected two legitimate `-1` qrels markers. The v2 parser correction and its original files remain preserved. Before this v3 replay, the same official scorer source compiled to a different unstripped binary hash in the current filesystem; the exact new executable was pinned, the original v2 protocol/build receipt archived under `v2_before_runtime_rebuild/`, and all scientific settings retained. See `RUNTIME_REBUILD_AMENDMENT.md`.

The archive of complete pair rows, 126 run records, score matrix, canonical scorer outputs and execution receipts has SHA256 `9eb9f50e2ec38405e2c79f5e5246fc6bda5e9f8a253115c1f3eed5fe9e5254ec`. Its uncompressed `all_pairs.jsonl` SHA256 is `ab299e7fdaeb443be2186554ab9d82365075fe8b5f00e7635358261b1a9a7020`. The public sources can be restored using `fetch_from_pins.py --fetch-missing` and the frozen evaluator; the archive retains the completed output independently.

This quantifies the uncertainty concealed by a *known* inferential mistake in a fixed historical retrieval collection. It does not establish that actual participants used mismatched qrels, actual downstream model-choice changes, latency or cost tradeoffs, causal benefit of an intervention, real-user harm, or GAMMAF-level novelty. The separately frozen 36-call GSM-Symbolic source-repair pilot still needs authenticated Adaption execution and independent response review.
