# Isolated execution of the frozen source-repair cohort

The unchanged source files from `2e3999a9c9e1e6aa07eee77924100445ea1674df` were mirrored as 23 byte-identical Git blobs into the existing private execution repository `ricardofitas/swarm-adaption-hackathon`. The authorized 36-call run uses its existing Adaption CI credential; no credential was copied into this workspace or the research repository.

Execution commit: `9eec2dd5f7610611d0643af11a79f5052e46764e`.
Workflow run: https://github.com/ricardofitas/swarm-adaption-hackathon/actions/runs/43429082614
Branch: `ricardo/epistemics-source-repair-20261113`.

The wrapper verifies the original protocol, manifest, runner and auxiliary hashes; exactly 36 fixed requests; four models and three arms with three contexts each; 8192 output-token cap; concurrency two; 120-second socket timeout; no retries. Existing workflow triggers were checked, and the execution branch starts no other inference campaign. A history guard and run-attempt guard prohibit repeated execution. Sanitized complete and partial captures are retained as a 90-day workflow artifact after a credential-absence scan.

Before reading any new answers, a separate capture validator was written and passed eight offline fixtures. It checks payload and journal hashes, reconstructed SSE frames, HTTP 200, nonempty final text, response.completed event and completed provider status, no transport/JSON/frame/fallback deviations. It produces an anonymous packet with a separately held review key. The original frozen runner is unchanged. Two independent first judgments must be saved and hashed before model/arm unblinding; human validation remains pending.

Status when this note was written: CI capture is running; no new source-repair answers have been inspected or scored. This cohort measures advice compatibility and useful-plan outcomes on one selected case; it does not measure task-performance ranking consequences.
