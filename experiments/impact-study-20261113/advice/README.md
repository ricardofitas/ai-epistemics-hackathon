# Three-arm scientific-advice follow-up

Prepared methods only; this agent made no inference calls. The current manifest is frozen only when the root publishes and verifies its exact bytes before sampling.

Allocation: two unchanged original questions × four prior requested configurations × three context arms × three fresh requests = **72 attempts**. Each arm has 24 requests. Output-token upper bound: **589,824**, plus input tokens. Model aliases do not establish immutable weights.

The arms are baseline, generic verification caution, and balanced primary-source resource facts. All use the exact previous common answer instruction, temperature 0.7, output cap 8192, native SSE, no tools/history/memory, concurrency 2, and no client retries. Generic and fact contexts are roughly length-matched. Source documents are not autonomous retrieval; interpret an observed difference as the supplied evidence/instruction package.

## Model-facing material

Only each unchanged original question, the common instruction, and the assigned treatment text is sent. `sourcecards.json` and the three standalone text files expose those exact treatment strings. Source snapshots, metadata, adverse historical responses, evaluator criteria, mechanism IDs and item golds are not sent.

## Frozen scoring scope

The original generic rubric and case-critical requirements are unchanged. Primary labels remain yes/no/uncertain/unscorable. Three target mechanisms are separately coded: wrong coreference-to-contradiction conversion; full mixed SVAMP score treated as sufficient for controlled harmless perturbation robustness; finite behavior treated as identifying an internal reasoning process. Retain old PAWS directionality and other material issues separately.

The prospective secondary `actionable_aligned_plan` label is also yes/no/uncertain/unscorable. Accept valid custom/adapted evaluations, qualified proxies and genuine informative essential clarification. Mere refusal or vague caution is not useful advice. This label never adds a new primary failure requirement.

Two fresh first agent reviewers should receive only original questions and ordinary final responses with unchanged definitions/source warrants, with explicit model, arm, repetition, treatment input and usage hidden. Source references inside answers can naturally reveal context, so blinding is incomplete. Preserve first files/hashes before unblinding, then handle factual/scope disagreements separately. Human review remains pending.

## Preparation checks

Five exact official README Git blobs were verified. WSC source metadata binds the authentic official release/archive audited earlier; no item gold is in the source card. SVAMP's primary paper supplies the three-way variation taxonomy; unverified numeric tag mappings and unresolved CSV-to-JSON joins are absent from the treatment.

The preparer refuses to rebuild after a capture directory exists. Native SSE dry-run passed 72 requests with 589,824 maximum generated tokens. `PREPARATION_CHECKS.json` and `PREREVIEW_NOTE.json` are preparation receipts, not independent prereview. Root should obtain source/fidelity review before final freeze.

```bash
python3 paper_research_20261113/run_adaption_stream_pilot.py impact_research_20261113/advice --dry-run
```

Exact manifest/protocol/card hashes are recorded in the files. The root owns collection and analysis. No actual downstream candidate-model scores or ranking reversal are measured by this advice block, and it does not reactivate the earlier failed PAWS consequence protocol.
