# HANS80 independent target supplement

Prepared methods only; no candidate model calls or output inspection occurred during preparation. This is a **new exploratory supplement for the WSC label-conversion consequence study**, not an activation of the earlier failed PAWS protocol. Its no-run status remains unchanged.

The fixed sample contains 80 authentic official HANS examples: 40 subject/object swaps with non-entailment gold and 40 active/passive role-preserving examples with entailment gold. All previously prepared 20 HANS source IDs and exact input pairs are excluded. Source rows are sampled without replacement; exact duplicate inputs are removed prospectively by retaining their first source occurrence. No model-error filtering occurs.

The source commit is `7299f6f657089ce06a0f98e7e81f8d0f5b7741ce`. All 15,462,062 source bytes, SHA256 and Git blob were independently verified. Exact selected texts, original source IDs, labels, subcases and templates are retained. The full source cache is reproducible from the pinned official URL in `official_hans_source_metadata.json`; it need not be committed again.

## Frozen task interface

The same four WSC candidate aliases receive the exact same common three-way NLI instruction. Every model receives ten shared batches of eight items, with only opaque IDs, premise and hypothesis. Source identities, suite names, subcases, gold labels and WSC choice roles are not transmitted. The 40 requests use native SSE, temperature zero, an 8192-token bound, no tools, memory, store or response history, and one attempt per row.

Official HANS gold remains binary. Both neutral and contradiction map to non-entailment. No official three-way gold is invented. Per-model and per-stratum accuracy, all six pairwise differences, missing-data bounds and conditional paired resampling are specified before outputs. Invalid or incomplete output remains unscorable; it is not replaced or silently counted as a semantic error.

## External choice consequence

Candidate aliases must come only from the registered WSC selection paired-score rule. A supplied WSC summary is byte-bound by SHA256 and must establish full WSC candidate completeness plus eligible unique choices. No HANS score can break WSC ties or select a different model.

The signed target effect is repaired-selected minus literal-selected HANS binary accuracy. It may be positive, zero or negative. Same selected candidate gives zero choice effect; ambiguous WSC choice remains indeterminate. Missing selected-candidate target predictions yield bounds rather than an imputed point. This is a diagnostic for two fixed HANS subcases, not all NLI, pretraining independence, real-user harm or a general model ranking. The item bootstrap is conditional on the tiny fixed sample and does not estimate template, batch or provider uncertainty.

## Offline preparation and checks

In the published experiment layout, the existing selected files support analysis without the complete HANS source cache. To reconstruct preparation from the official source:

```bash
python3 prepare_hans_target.py --download-source
python3 ../methods/run_adaption_stream_pilot.py . --dry-run
python3 test_hans_target.py
```

`--source`, `--source-metadata`, `--prior-prepared` and `--wsc-builder` can specify exact local caches. Preparation refuses changes to existing generated artifacts and refuses any rebuild after inference starts. Keep the same frozen WSC builder revision when reproducing its preparation-time provenance hash.

## Analysis after separate freeze and completed collection

The root verifies external Git commit/time and exact frozen protocol/manifest hashes. No API key is needed for analysis.

```bash
python3 analyze_hans_target.py . --freeze-commit COMMIT_SHA --freeze-time UTC_TIME --manifest-sha256 MANIFEST_SHA --protocol-sha256 PROTOCOL_SHA --output-directory analysis
```

Optionally add `--wsc-summary PATH --wsc-summary-sha256 SHA256` to combine the fixed WSC choices. Otherwise all four target results are still reported without choosing a winner. New output directories are required; existing analyses are never overwritten. The 25 software checks in `VERIFICATION.json` use synthetic captures and establish no actual performance finding.
