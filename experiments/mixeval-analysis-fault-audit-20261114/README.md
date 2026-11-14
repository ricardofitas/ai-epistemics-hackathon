# Independent fault-path audit of frozen paired generation analysis

Scope: code-level review of launch revision 676f3b618948253a9ff4f01f400e8ab1a2971a13 in private ricardofitas/swarm-adaption-hackathon. No model output or live response artifact was accessed; no generation launched, retried, cancelled or modified. This audit is supplemental and post-launch, not a new pre-launch protocol.

## Confirmed fault-path incompatibility

`execute_paired.py` catches exceptions from transport.run_trial and, when no artifact exists, writes a receipt containing only trial_id, attempt_count=1, local_capture_error, completed_nonempty=False. `analyze_paired.py` then asserts request_sha256 equality unconditionally before classifying completeness. The receipt the executor itself can emit therefore causes AssertionError rather than an unknown row. The frozen analysis protocol says incomplete/unattempted outputs stay in the denominator with bounds. This is a mismatch in fault handling, NOT an observed provider failure and NOT evidence that any live response has been lost.

`python audit_analyzer.py` reproduces three paths on the original analyzer bytes: (1) all 80 responses unattempted -> partial report, zero scored, both models' gain bounds [-1,1]; (2) one exact-shape local-error receipt emitted by the executor -> AssertionError; (3) explicit wrong request hash -> AssertionError, correctly protecting integrity. The fake scoring adapter raises if called; the scorer is never reached. Invented trial IDs/models are only harness inputs, never presented as real answers or benchmark cases. The test writes only temporary directories.

## Required owner follow-up

Preserve the original analyzer, receipts, hashes and generated results. Before final claims, inspect whether any local_capture_error receipt exists and reconcile it against the frozen manifest plus unique attempt_started/attempt_recorded ledger. An absent request hash on an explicitly recorded local-error receipt must remain UNKNOWN with incomplete provenance, not be relabelled a valid response or silently trusted. An explicit mismatching hash must remain an integrity failure. If the owner revises analysis, register the exact post-launch change before rerunning analysis only. No replacement request or extra generation batch is warranted by this audit. This execution has made no such change to active files.

The frozen analyzer also does not implement all checks promised in the analysis protocol's resource_audit: it reads artifact files but never reads CALL_LEDGER.jsonl and does not reconcile attempt_started count/duplicates. This is a static code observation, not an observed resource-limit violation. The final audit should compare ledger, artifacts, manifest and usage separately; errors may have occurred without a completed artifact, so artifact count alone is not a proven call count.

## Identification limits checked without outcomes

For each of the fixed20questions per model, binding score B and typed score T lie in [0,1]. Keep every unknown score as [0,1]. The sum of T_min-B_max divided by20 is a valid lower bound, and T_max-B_min an upper bound. Both endpoints are attainable under unconstrained unknown binary scores, so these are sharp missing-outcome bounds. Dependence across questions does not invalidate these deterministic bounds. Zero completed responses gives [-1,1], as reproduced. A score is an official optional rule-mode assignment, not a default model-judge or population capability estimate.

Both models share the SAME20questions (16TriviaQA,3DROP,1BBH per frozen protocol); they are not40independent questions. Fixed condition/model execution order and changes to instruction/format wording prevent attributing effects solely to the None placeholder or assuming random treatment assignment. These are already documented design limitations, retained here, not new discoveries. No new significance test or favorable criterion is introduced.

## Continuity

At observation the existing sole run43606982014 was in_progress, attempt1, exact launch head676f3b618948253a9ff4f01f400e8ab1a2971a13, created2026-11-14T14:50:47Z. This establishes launch and running status only, not80calls or successful completion. The mutable-receipt fix is present in execute_paired.py via tempfile+os.replace. Primary files and immutable hashes are in AUDIT_PROVENANCE.json. Source state and run status may advance after this observation.

The active owner continues installed-route integration, v1.4 manuscript and the sole generation batch. No duplicate integration, manuscript rewrite or external search was performed here. Canonical state must retain the latest direct owner's results. Earlier checkpoint wording that implied actual division by nominal17/32 is superseded: invalid references are skipped before incrementing the denominator counter; scored_samples=0. Total is a requested policy label, not proof that17/32were used in an executed division.
