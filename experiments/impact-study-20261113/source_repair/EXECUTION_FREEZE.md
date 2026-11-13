# Execution freeze — GSM-Symbolic source repair

Frozen preparation commit: `2e3999a9c9e1e6aa07eee77924100445ea1674df` (2026-11-13 06:44:30 UTC).
This note was recorded before any source-repair inference call. The frozen files at that commit remain the authoritative inputs; a later change to this note or branch head does not change their bytes.

- Manifest SHA256: `a02a82eb6cb83a1063531c3b0d6ecc8441e8a23acb641f81feddf1830b929e85`
- Protocol SHA256: `b2946561e395a6ac751d9d282229a16ab3b1892ca247ba8ad63a56a2135cf97f`
- Runner SHA256: `c280811c5f685cdc5b254d5097946835428cd87de6ea58218de1e2cad537fe5e`
- Independent source check: the primary arXiv v1 GSM-Symbolic paper, Sections 4.1–4.3, supports names/values within templates and P1/P2 one/two added clauses with its exact-step caveat. The patch confines its paraphrase absence claim to the Section 4.2 comparison. The generic paragraph is an active compatibility instruction, so the contrast estimates the supplied context package, not a unique causal effect of source truth.
- Local native-SSE dry run: 36 valid distinct requests, 12 per arm and 3 per model/arm, 294,912 maximum requested output tokens. No API calls were made by the dry run.
- Status at freeze: `prepared_not_executed`. No source-repair response artifacts or human labels exist.

Run the exact frozen manifest once in an environment with an authorized Adaption credential and endpoint access, without client retries or substituted models. Verify the three hashes above before collection. Preserve all 36 attempts, including empty, incomplete and transport-error rows. Score the unchanged primary material-error, five mechanism and secondary useful-plan outcomes per model/arm, showing unknown bounds. Obtain two fresh blinded first judgments before unblinding; human validation remains pending.

```bash
python3 scripts/run_adaption_stream_pilot.py experiments/impact-study-20261113/source_repair --dry-run
python3 scripts/run_adaption_stream_pilot.py experiments/impact-study-20261113/source_repair
```

The current work environment has no `ADAPTION_API_KEY` or authenticated Adaption session. The endpoint is reachable but returns HTTP 401 without a credential. This is a prospective freeze, not a completed 36-call result. Do not pool these selected post-discovery attempts with the historical advice block or claim benchmark-family expansion.
