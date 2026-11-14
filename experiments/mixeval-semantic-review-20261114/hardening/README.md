# Capture-analysis hardening

This local derivative addresses a reproducible failure in the frozen paired analyzer: a minimal `local_capture_error` receipt contains a trial ID but no request hash, causing an assertion before the record can be retained as unknown. None of the original 80 receipts exhibited that failure.

`analyze_paired_hardened.py` preserves the 80 planned slots and 20 pairs per model. Missing receipts, IDs, request/output hashes, payloads, or incomplete/local-error responses stay unknown. Contradictory hashes/models/IDs, duplicate trial/provider-response identities, unexpected receipt slots and token-cap violations yield a failed integrity report and no score for affected slots. A corrupted manifest/source association is a fatal design error. `integrity_status=PASS` means no contradictory evidence; `association_evidence_complete` separately reports missing proof. The per-slot reason lists retain distinctions.

The pinned official optional RULE scorer is loaded only after verifying its SHA-256. No original scorer or capture is rewritten. Scores are not semantic adjudication and are not the default model-judge mode.

## Validation

- Baseline: all 80 per-slot scores, both model effects, 69 scored / 11 unknown counts, token totals and provider cost-unit total agree with the frozen analysis.
- 20 deliberate fault controls pass, including a minimal local-error receipt, missing metadata, mutated hashes/payloads/models, duplicate identities, unexpected receipts, false completion flags and corrupt design inputs.
- Original input-file tree hashes are unchanged.
- Official parsed-candidate order is produced via `list(set(...))` and varies across Python hash seeds. Candidate contents, all scores and every other judgment field match; verification sorts only these unordered candidates for comparison.

`VERIFICATION.json` records all control outcomes. Run from the conversation workspace:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -W ignore::SyntaxWarning hardening/verify_hardening.py
PYTHONDONTWRITEBYTECODE=1 python3 -W ignore::SyntaxWarning hardening/analyze_paired_hardened.py --input prior/real-generation --output hardening/cli_baseline
```

## Future provenance patch

`native_runner_future.py` is a new copy with the previously reviewed metadata patch applied. It separates `source_record_sha256` and `scorer_source_sha256`, preventing dictionary-key collision. `verify_metadata_patch.py` executes only the exact patched capture-construction statements over 49 stored scorer results and proves all scores and other capture fields unchanged. See `METADATA_PATCH_VERIFICATION.json` and `metadata_reconstructed_captures.json`.

This is metadata-assembly verification, not a new native evaluator/provider run. Frozen original runner/results remain unchanged. There were zero new model calls. Full installed-provider and native-primary-metric integration remains open.
